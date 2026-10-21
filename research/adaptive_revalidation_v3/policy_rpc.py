"""Strict spawned-process RPC boundary for actor-safe policy execution.

The policy client has no transport attribute. Tool calls use a control channel
that can carry only ``tool_call`` messages; final worker results use a separate
result channel. Canonical JSON bytes cross both channels.
"""
from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
import inspect
import json
import multiprocessing
from multiprocessing.connection import wait as wait_for_connections
import os
import sys
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

from .actor import (
    ActorInput,
    Evidence,
    PolicyDecision,
    PolicySpec,
    actor_input_from_dict,
    canonical_json,
    evidence_from_dict,
    policy_decision_from_dict,
    policy_spec_from_dict,
)
from .policies import PUBLIC_TOOL_NAMES, make_policy


ToolHandler = Callable[[int, str, str], Any]
_CONTROL_CHANNEL: ContextVar[Any] = ContextVar(
    "adaptive_v3_control_channel",
    default=None,
)
_EPISODE_INDEX: ContextVar[int] = ContextVar(
    "adaptive_v3_episode_index",
    default=-1,
)


class RpcToolError(RuntimeError):
    """Raised when the evaluator rejects or fails one public tool call."""


class RpcProtocolError(RuntimeError):
    """Raised when the policy process violates the channel protocol."""


@dataclass(frozen=True)
class PolicyProcessInfo:
    """Deterministic boundary metadata; PIDs are excluded from receipts."""

    evaluator_pid: int
    policy_pid: int
    public_tools: Tuple[str, ...]

    def as_dict(self) -> Dict[str, Any]:
        """Return the boundary metadata used by runtime assertions."""
        return {
            "evaluator_pid": self.evaluator_pid,
            "policy_pid": self.policy_pid,
            "public_tools": list(self.public_tools),
        }


def _invoke_tool(tool: str, target: str) -> Evidence:
    connection = _CONTROL_CHANNEL.get()
    if connection is None:
        raise RpcProtocolError("TOOL_CHANNEL_NOT_BOUND")
    message = {
        "episode_index": _EPISODE_INDEX.get(),
        "target": str(target),
        "tool": tool,
        "type": "tool_call",
    }
    connection.send_bytes(canonical_json(message).encode("utf-8"))
    raw = json.loads(connection.recv_bytes().decode("utf-8"))
    if raw.get("type") == "tool_error":
        raise RpcToolError(str(raw.get("error", "TOOL_CALL_FAILED")))
    if raw.get("type") != "tool_result" or not isinstance(raw.get("payload"), dict):
        raise RpcProtocolError("TOOL_RESULT_PROTOCOL_MISMATCH")
    return evidence_from_dict(raw["payload"])


class RpcPublicTools:
    """Connection-free actor client with exactly three public call methods."""

    __slots__ = ()

    def __dir__(self) -> list[str]:
        """Expose only the complete public call surface."""
        return list(PUBLIC_TOOL_NAMES)

    def __repr__(self) -> str:
        """Return a stable capability description without private state."""
        return "<RpcPublicTools inspect_dependency inspect_change run_target_test>"

    def inspect_dependency(self, node_id: str) -> Evidence:
        """Inspect one actor-visible dependency record."""
        return _invoke_tool("inspect_dependency", node_id)

    def inspect_change(self, change_id: str) -> Evidence:
        """Inspect one actor-visible source change."""
        return _invoke_tool("inspect_change", change_id)

    def run_target_test(self, output_id: str) -> Evidence:
        """Run one actor-visible target test."""
        return _invoke_tool("run_target_test", output_id)


def _send(connection: Any, payload: Mapping[str, Any]) -> None:
    connection.send_bytes(canonical_json(payload).encode("utf-8"))


def _receive(connection: Any) -> Mapping[str, Any]:
    try:
        raw = json.loads(connection.recv_bytes().decode("utf-8"))
    except EOFError:
        raise
    except BaseException as exc:
        raise RpcProtocolError("INVALID_RPC_JSON") from exc
    if not isinstance(raw, dict):
        raise RpcProtocolError("RPC_MESSAGE_NOT_OBJECT")
    return raw


def _policy_worker_entry(
    control_channel: Any,
    result_channel: Any,
    actor_payloads: Sequence[str],
    spec_payloads: Sequence[str],
) -> None:
    """Run policy episodes without exposing either channel through the client."""
    control_token = _CONTROL_CHANNEL.set(control_channel)
    episode_token = _EPISODE_INDEX.set(-1)
    try:
        if len(actor_payloads) != len(spec_payloads):
            raise RpcProtocolError("POLICY_BATCH_SIZE_MISMATCH")
        results = []
        for index, (actor_payload, spec_payload) in enumerate(
            zip(actor_payloads, spec_payloads)
        ):
            actor_input = actor_input_from_dict(json.loads(actor_payload))
            spec = policy_spec_from_dict(json.loads(spec_payload))
            _EPISODE_INDEX.set(index)
            decision = make_policy(spec).run(actor_input, RpcPublicTools())
            results.append(decision.as_dict())
        _send(
            result_channel,
            {
                "policy_pid": os.getpid(),
                "results": results,
                "type": "batch_result",
            },
        )
    except BaseException as exc:
        _send(
            result_channel,
            {
                "error": f"{type(exc).__name__}: {exc}",
                "type": "worker_error",
            },
        )
    finally:
        _CONTROL_CHANNEL.reset(control_token)
        _EPISODE_INDEX.reset(episode_token)
        control_channel.close()
        result_channel.close()


def _probe_worker_entry(control_channel: Any, result_channel: Any) -> None:
    """Adversarially inspect the connection-free client from policy code."""
    try:
        client = RpcPublicTools()
        public_names = [
            name
            for name in dir(client)
            if not name.startswith("_") and callable(getattr(client, name))
        ]
        private_attributes = sorted(
            name
            for name in vars(type(client))
            if name.startswith("_") and not name.startswith("__")
        )
        connection_error = None
        try:
            object.__getattribute__(client, "_connection")
        except AttributeError as exc:
            connection_error = type(exc).__name__
        vars_error = None
        try:
            vars_payload = vars(client)
        except TypeError as exc:
            vars_payload = None
            vars_error = type(exc).__name__
        global_names = set()
        for name in PUBLIC_TOOL_NAMES:
            global_names.update(getattr(type(client), name).__globals__.keys())
        loaded_modules = sorted(
            name
            for name in sys.modules
            if name.startswith("research.adaptive_revalidation_v3.")
        )
        probe = {
            "client_class_module": type(client).__module__,
            "client_connection_attribute_error": connection_error,
            "client_private_attributes": private_attributes,
            "client_repr": repr(client),
            "client_slots": list(getattr(type(client), "__slots__", ())),
            "client_vars": vars_payload,
            "client_vars_error": vars_error,
            "loaded_modules": loaded_modules,
            "method_global_names": sorted(global_names),
            "public_names": public_names,
        }
        _send(
            result_channel,
            {
                "policy_pid": os.getpid(),
                "probe": probe,
                "type": "probe_result",
            },
        )
    except BaseException as exc:
        _send(
            result_channel,
            {
                "error": f"{type(exc).__name__}: {exc}",
                "type": "worker_error",
            },
        )
    finally:
        control_channel.close()
        result_channel.close()


def _spawn_context() -> Any:
    return multiprocessing.get_context("spawn")


def _validate_tool_call(message: Mapping[str, Any]) -> Tuple[int, str, str]:
    if set(message) != {"episode_index", "target", "tool", "type"}:
        raise RpcProtocolError("TOOL_CALL_FIELDS_MISMATCH")
    index = message["episode_index"]
    if isinstance(index, bool) or not isinstance(index, int) or index < 0:
        raise RpcProtocolError("TOOL_CALL_INDEX_INVALID")
    tool = message["tool"]
    target = message["target"]
    if tool not in PUBLIC_TOOL_NAMES or not isinstance(tool, str):
        raise RpcProtocolError("NON_PUBLIC_TOOL")
    if not isinstance(target, str) or not target:
        raise RpcProtocolError("TOOL_CALL_TARGET_INVALID")
    return index, tool, target


def _run_protocol(
    target: Callable[..., None],
    args: Tuple[Any, ...],
    tool_handler: Optional[ToolHandler] = None,
) -> Tuple[Mapping[str, Any], PolicyProcessInfo]:
    context = _spawn_context()
    evaluator_pid = os.getpid()
    control_parent, control_child = context.Pipe(duplex=True)
    result_parent, result_child = context.Pipe(duplex=True)
    process = context.Process(
        target=target,
        args=(control_child, result_child) + args,
    )
    process.start()
    control_child.close()
    result_child.close()
    result_message: Optional[Mapping[str, Any]] = None
    failure: Optional[BaseException] = None
    try:
        while result_message is None:
            ready = wait_for_connections(
                [control_parent, result_parent],
                timeout=30,
            )
            if not ready:
                raise RpcProtocolError("POLICY_PROTOCOL_TIMEOUT")
            messages = []
            for connection in ready:
                try:
                    messages.append((connection, _receive(connection)))
                except EOFError:
                    continue
            for connection, message in messages:
                message_type = message.get("type")
                if connection is result_parent:
                    if message_type not in {"batch_result", "probe_result", "worker_error"}:
                        raise RpcProtocolError("UNEXPECTED_RESULT_MESSAGE")
                    if message_type == "worker_error":
                        raise RpcProtocolError(str(message.get("error", "WORKER_ERROR")))
                    result_message = message
                    break
                if message_type != "tool_call":
                    raise RpcProtocolError("UNEXPECTED_CONTROL_MESSAGE")
                if tool_handler is None:
                    raise RpcProtocolError("TOOL_CALL_WITHOUT_HANDLER")
                try:
                    index, tool, tool_target = _validate_tool_call(message)
                    result = tool_handler(index, tool, tool_target)
                    payload = (
                        result.as_dict() if hasattr(result, "as_dict") else dict(result)
                    )
                    _send(control_parent, {"payload": payload, "type": "tool_result"})
                except BaseException as exc:
                    _send(
                        control_parent,
                        {
                            "error": f"{type(exc).__name__}: {exc}",
                            "type": "tool_error",
                        },
                    )
    except BaseException as exc:
        failure = exc
    finally:
        control_parent.close()
        result_parent.close()
        process.join(timeout=30)
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)

    if failure is not None:
        raise failure
    if result_message is None:
        raise RpcProtocolError("POLICY_RESULT_MISSING")
    if process.exitcode != 0:
        raise RpcProtocolError("POLICY_PROCESS_EXIT_NONZERO")
    policy_pid = int(result_message.get("policy_pid", process.pid or -1))
    info = PolicyProcessInfo(
        evaluator_pid=evaluator_pid,
        policy_pid=policy_pid,
        public_tools=PUBLIC_TOOL_NAMES,
    )
    return result_message, info


def execute_policy_batch(
    items: Sequence[Tuple[ActorInput, PolicySpec]],
    tool_handler: ToolHandler,
) -> Tuple[Tuple[PolicyDecision, ...], PolicyProcessInfo]:
    """Execute serialized policy inputs in a separate process over strict RPC."""
    actor_payloads = tuple(canonical_json(actor.as_dict()) for actor, _ in items)
    spec_payloads = tuple(canonical_json(spec.as_dict()) for _, spec in items)
    message, info = _run_protocol(
        _policy_worker_entry,
        (actor_payloads, spec_payloads),
        tool_handler,
    )
    raw_results = message.get("results")
    if not isinstance(raw_results, list) or len(raw_results) != len(items):
        raise RpcProtocolError("POLICY_RESULT_COUNT_MISMATCH")
    decisions = tuple(policy_decision_from_dict(raw) for raw in raw_results)
    for (expected_actor, _), decision in zip(items, decisions):
        if decision.evidence.actor_input != expected_actor:
            raise RpcProtocolError("POLICY_ACTOR_INPUT_TAMPERED")
    return decisions, info


def run_introspection_probe() -> Tuple[Mapping[str, Any], PolicyProcessInfo]:
    """Run adversarial client introspection in the policy process."""
    message, info = _run_protocol(_probe_worker_entry, ())
    probe = message.get("probe")
    if not isinstance(probe, dict):
        raise RpcProtocolError("PROBE_RESULT_MISSING")
    return probe, info
