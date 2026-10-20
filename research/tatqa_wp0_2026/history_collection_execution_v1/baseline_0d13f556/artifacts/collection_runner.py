#!/usr/bin/env python3
"""Authorization-gated two-stage collection runner with immutable raw capture."""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from execution_core import (
    ExecutionBudget,
    ImmutableRawStore,
    canonical_json,
    evaluate_expression,
    sha256_file,
    strict_json_object,
    validate_consume_response,
    validate_plan_response,
    write_json_lf,
)


ALLOWED_AUTHORIZATION_KEYS = {
    "schema", "authorization_id", "mode", "bundle_sha256",
    "window_start_utc", "window_end_utc", "timezone",
    "request_cap", "token_cap", "retry_cap", "concurrency",
    "allow_model_requests", "owner_decision_reference",
}
ALLOWED_CHAT_TOP_KEYS = {
    "id", "object", "created", "model", "choices", "usage", "system_fingerprint"
}
ALLOWED_CHOICE_KEYS = {"index", "finish_reason", "message"}
ALLOWED_MESSAGE_KEYS = {"role", "content"}
ALLOWED_USAGE_KEYS = {
    "prompt_tokens", "completion_tokens", "total_tokens", "prompt_tokens_details"
}


class ChatAdapter(Protocol):
    def complete(self, request_payload: dict[str, Any]) -> dict[str, Any]:
        ...


class HttpChatAdapter:
    def __init__(self, base_url: str, api_path: str, timeout_seconds: int):
        if not base_url.startswith(("http://127.0.0.1:", "http://localhost:")):
            raise ValueError("base_url_must_be_local_bound")
        self.url = base_url.rstrip("/") + api_path
        self.timeout_seconds = timeout_seconds

    def complete(self, request_payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(request_payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self.url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                status = int(response.status)
                content_type = response.headers.get("Content-Type", "")
                raw = response.read(65537)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(f"adapter_request_failed:{type(exc).__name__}") from exc
        elapsed = time.monotonic() - started
        if len(raw) > 65536:
            raise RuntimeError("adapter_response_too_large")
        if not content_type.startswith("application/json"):
            raise RuntimeError("adapter_response_content_type_invalid")
        return {
            "status_code": status,
            "content_type": content_type,
            "body_text": raw.decode("utf-8"),
            "elapsed_s": elapsed,
        }


def parse_chat_response(raw_response: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_response, dict) or raw_response.get("status_code") != 200:
        raise ValueError("chat_http_status_invalid")
    body = strict_json_object(raw_response["body_text"])
    unknown = sorted(set(body) - ALLOWED_CHAT_TOP_KEYS)
    if unknown:
        raise ValueError(f"chat_response_unknown_keys:{unknown}")
    for key in ("choices", "usage"):
        if key not in body:
            raise ValueError(f"chat_response_missing:{key}")
    choices = body["choices"]
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("chat_choices_must_have_one")
    choice = choices[0]
    if not isinstance(choice, dict):
        raise ValueError("chat_choice_must_be_object")
    if not set(choice).issubset(ALLOWED_CHOICE_KEYS) or not {"message"}.issubset(choice):
        raise ValueError("chat_choice_keys_invalid")
    message = choice["message"]
    if not isinstance(message, dict) or set(message) != ALLOWED_MESSAGE_KEYS:
        raise ValueError("chat_message_keys_invalid")
    if message.get("role") != "assistant" or not isinstance(message.get("content"), str):
        raise ValueError("chat_message_shape_invalid")
    usage = body["usage"]
    if not isinstance(usage, dict) or not set(usage).issubset(ALLOWED_USAGE_KEYS):
        raise ValueError("chat_usage_keys_invalid")
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        if isinstance(usage.get(key), bool) or not isinstance(usage.get(key), int) or usage[key] < 0:
            raise ValueError(f"chat_usage_invalid:{key}")
    if usage["prompt_tokens"] + usage["completion_tokens"] != usage["total_tokens"]:
        raise ValueError("chat_usage_total_mismatch")
    return {
        "content": message["content"],
        "usage": dict(usage),
        "finish_reason": choice.get("finish_reason"),
    }


def parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("utc_timestamp_must_end_with_z")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    return parsed.astimezone(timezone.utc)


def validate_authorization(
    authorization: Any,
    bundle_path: Path,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    if not isinstance(authorization, dict) or set(authorization) != ALLOWED_AUTHORIZATION_KEYS:
        raise PermissionError("authorization_schema_invalid")
    if authorization["schema"] != "collection_execution_authorization_v1":
        raise PermissionError("authorization_schema_mismatch")
    if authorization["mode"] != "SINGLE_COLLECTION_RUN":
        raise PermissionError("authorization_mode_invalid")
    if authorization["allow_model_requests"] is not True:
        raise PermissionError("model_requests_not_allowed")
    if authorization["bundle_sha256"] != sha256_file(bundle_path):
        raise PermissionError("authorization_bundle_hash_mismatch")
    expected = {
        "request_cap": 54,
        "token_cap": 600000,
        "retry_cap": 0,
        "concurrency": 1,
        "timezone": "Asia/Shanghai",
    }
    for key, value in expected.items():
        if authorization[key] != value:
            raise PermissionError(f"authorization_{key}_invalid")
    if not isinstance(authorization["authorization_id"], str) or not authorization["authorization_id"]:
        raise PermissionError("authorization_id_invalid")
    if not isinstance(authorization["owner_decision_reference"], str) or not authorization["owner_decision_reference"]:
        raise PermissionError("owner_decision_reference_invalid")
    start = parse_utc(authorization["window_start_utc"])
    end = parse_utc(authorization["window_end_utc"])
    if end <= start or (end - start).total_seconds() > 90 * 60:
        raise PermissionError("authorization_window_invalid")
    now = now_utc or datetime.now(timezone.utc)
    if not (start <= now <= end):
        raise PermissionError("authorization_window_not_active")
    return dict(authorization)


def verify_bundle(bundle_path: Path, root: Path) -> dict[str, Any]:
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    if bundle.get("schema") != "pre_collection_execution_bundle_v1":
        raise ValueError("bundle_schema_invalid")
    if bundle.get("blockers"):
        raise ValueError("bundle_has_blockers")
    if bundle.get("status") != "READY_FOR_SINGLE_COLLECTION_AUTHORIZATION":
        raise ValueError("bundle_not_ready")
    for relative, expected_hash in bundle["artifacts"].items():
        path = root / relative
        if not path.is_file() or sha256_file(path) != expected_hash:
            raise ValueError(f"bundle_artifact_hash_mismatch:{relative}")
    if bundle["budget"] != {
        "request_cap": 54,
        "token_cap": 600000,
        "per_request_reserve_tokens": 10240,
        "retry_cap": 0,
        "concurrency": 1,
    }:
        raise ValueError("bundle_budget_invalid")
    return bundle


def render_prompt(template: dict[str, Any], values: dict[str, str]) -> list[dict[str, str]]:
    user = template["user_template"]
    for key, value in values.items():
        user = user.replace("{{" + key + "}}", value)
    if re.search(r"\{\{[A-Z0-9_]+\}\}", user):
        raise ValueError("prompt_placeholder_unresolved")
    return [
        {"role": "system", "content": template["system"]},
        {"role": "user", "content": user},
    ]


def request_payload(
    runtime_identity: dict[str, Any],
    messages: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "model": runtime_identity["identity"]["model"]["model_id"],
        "messages": messages,
        **runtime_identity["identity"]["generation"],
    }


class CollectionRunner:
    def __init__(
        self,
        root: Path,
        manifest: dict[str, Any],
        execution_plan: dict[str, Any],
        runtime_identity: dict[str, Any],
        plan_prompt: dict[str, Any],
        consume_prompt: dict[str, Any],
        adapter: ChatAdapter,
        raw_root: Path,
    ):
        self.root = root
        self.manifest = manifest
        self.execution_plan = execution_plan
        self.runtime_identity = runtime_identity
        self.plan_prompt = plan_prompt
        self.consume_prompt = consume_prompt
        self.adapter = adapter
        self.raw = ImmutableRawStore(raw_root)
        limits = execution_plan
        self.budget = ExecutionBudget(
            request_cap=limits["request_cap"],
            token_cap=limits["token_cap"],
            per_request_reserve=limits["per_request_reserve_tokens"],
        )
        self.results: list[dict[str, Any]] = []

    def _model_request(
        self,
        logical_id: str,
        payload: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        reservation_id = self.budget.reserve()
        request_id = self.raw.begin_request(logical_id, payload)
        try:
            raw_response = self.adapter.complete(payload)
        except Exception as exc:
            self.raw.mark_crash(request_id, type(exc).__name__)
            raise
        self.raw.persist_response(request_id, raw_response)
        try:
            parsed = parse_chat_response(raw_response)
            actual_tokens = parsed["usage"]["total_tokens"]
        except ValueError as exc:
            self.budget.settle(reservation_id, self.budget.per_request_reserve)
            return {"status": "FORMAT_INVALID", "error": str(exc), "request_id": request_id}, {
                "status": "FORMAT_INVALID", "request_key": logical_id
            }
        self.budget.settle(reservation_id, actual_tokens)
        return parsed, {"status": "OK", "request_id": request_id, "request_key": logical_id}

    def run_attempt(
        self,
        task: dict[str, Any],
        attempt: int,
        correction_context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        task_id = task["task_id"]
        actor_task = task["actor_task"]
        context_json = canonical_json(correction_context or {"mode": "INITIAL_ATTEMPT"})
        plan_messages = render_prompt(self.plan_prompt, {
            "ACTOR_TASK_JSON": canonical_json(actor_task),
            "CORRECTION_CONTEXT_JSON": context_json,
        })
        plan_parsed, plan_request = self._model_request(
            f"plan|{task_id}|a{attempt}",
            request_payload(self.runtime_identity, plan_messages),
        )
        if plan_parsed.get("status") == "FORMAT_INVALID":
            plan = plan_parsed
            tool_result = {
                "tool": "calc",
                "params": {"expression": None},
                "returned_value": None,
                "status": "TOOL_ERROR",
                "error": "INVALID_PLAN",
            }
        else:
            try:
                plan = validate_plan_response(strict_json_object(plan_parsed["content"]))
                tool_result = {
                    "tool": "calc",
                    "params": plan["params"],
                    "returned_value": evaluate_expression(plan["params"]["expression"]),
                    "status": "OK",
                    "error": None,
                }
            except (ValueError, ArithmeticError) as exc:
                plan = {"status": "INVALID_PLAN", "error": str(exc)}
                tool_result = {
                    "tool": "calc",
                    "params": {},
                    "returned_value": None,
                    "status": "TOOL_ERROR",
                    "error": "INVALID_PLAN",
                }
        consume_messages = render_prompt(self.consume_prompt, {
            "ACTOR_TASK_JSON": canonical_json(actor_task),
            "PLAN_JSON": canonical_json(plan),
            "TOOL_RESULT_JSON": canonical_json(tool_result),
            "CORRECTION_CONTEXT_JSON": context_json,
        })
        consume_parsed, consume_request = self._model_request(
            f"consume|{task_id}|a{attempt}",
            request_payload(self.runtime_identity, consume_messages),
        )
        if consume_parsed.get("status") == "FORMAT_INVALID":
            consume = consume_parsed
        else:
            try:
                consume = validate_consume_response(
                    strict_json_object(consume_parsed["content"])
                )
            except ValueError as exc:
                consume = {"status": "FORMAT_INVALID", "error": str(exc)}
        reference = task["hidden"]["reference"]
        if consume.get("status") == "ANSWER":
            value_ok = abs(
                float(consume["delta_target"]) - float(reference["delta_target"])
            ) <= 1e-9
            unit_ok = consume["unit"] == reference["target_unit"]
            feedback_category = (
                "SUCCESS" if value_ok and unit_ok else "ANSWER_REFERENCE_MISMATCH"
            )
        else:
            feedback_category = consume.get("status", "INVALID")
        return {
            "task_id": task_id,
            "attempt": attempt,
            "plan_request": plan_request,
            "plan": plan,
            "tool_result": tool_result,
            "consume_request": consume_request,
            "consume": consume,
            "feedback_category": feedback_category,
            "hidden_reference": reference,
            "scientific_result": False,
        }

    def run(self) -> dict[str, Any]:
        history_tasks = [row for row in self.manifest["tasks"] if row["bucket"] == "history"]
        fixture_tasks = self.manifest["qualification_fixtures"]
        expected_keys = [slot["request_key"] for slot in self.execution_plan["request_slots"]]
        produced_keys: list[str] = []
        for task in history_tasks:
            first = self.run_attempt(task, 1, None)
            self.results.append(first)
            followup_context = {
                "mode": (
                    "SUCCESS_EXECUTION_RECHECK"
                    if first["feedback_category"] == "SUCCESS"
                    else "ACTUAL_FEEDBACK_FOLLOWUP"
                ),
                "actual_first_attempt": {
                    "plan": first["plan"],
                    "tool_result": first["tool_result"],
                    "actor_answer": first["consume"],
                    "feedback_category": first["feedback_category"],
                },
            }
            second = self.run_attempt(task, 2, followup_context)
            self.results.append(second)
            produced_keys.extend([
                first["plan_request"]["request_key"],
                first["consume_request"]["request_key"],
                second["plan_request"]["request_key"],
                second["consume_request"]["request_key"],
            ])
        for task in fixture_tasks:
            result = self.run_attempt(task, 1, {"mode": "QUALIFICATION_FIXTURE"})
            self.results.append(result)
            produced_keys.extend([
                result["plan_request"]["request_key"],
                result["consume_request"]["request_key"],
            ])
        if produced_keys != expected_keys:
            raise RuntimeError("execution_request_order_mismatch")
        return {
            "schema": "collection_execution_result_v1",
            "status": "EXECUTED_WITHOUT_AUTOMATIC_RETRIES",
            "budget": self.budget.snapshot(),
            "results": self.results,
            "scientific_result": False,
        }


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"object required: {path}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "execute"))
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--raw-root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    bundle = verify_bundle(args.bundle.resolve(), root)
    if args.command == "preflight":
        print(json.dumps({
            "status": "PREFLIGHT_PASS_NO_REQUESTS",
            "bundle_status": bundle["status"],
            "artifact_count": len(bundle["artifacts"]),
            "model_calls": 0,
        }, sort_keys=True))
        return 0
    if args.authorization is None or args.raw_root is None:
        raise PermissionError("authorization_and_raw_root_required")
    authorization = validate_authorization(
        load_json(args.authorization.resolve()), args.bundle.resolve()
    )
    runner = CollectionRunner(
        root=root,
        manifest=load_json(root / "TASK_REFERENCE_MANIFEST.json"),
        execution_plan=load_json(root / "EXECUTION_PLAN.json"),
        runtime_identity=load_json(root / "RUNTIME_IDENTITY_SNAPSHOT.json"),
        plan_prompt=load_json(root / "PROMPT_PLAN.json"),
        consume_prompt=load_json(root / "PROMPT_CONSUME.json"),
        adapter=HttpChatAdapter(
            base_url=load_json(root / "RUNTIME_POLICY.json")["base_url"],
            api_path=load_json(root / "RUNTIME_POLICY.json")["api_path"],
            timeout_seconds=load_json(root / "RUNTIME_POLICY.json")["limits"][
                "request_timeout_seconds"
            ],
        ),
        raw_root=args.raw_root.resolve(),
    )
    result = runner.run()
    result["authorization_id"] = authorization["authorization_id"]
    write_json_lf(args.raw_root.resolve() / "EXECUTION_RESULT.json", result)
    print(json.dumps({
        "status": result["status"],
        "requests": result["budget"]["requests"],
        "authorization_id": authorization["authorization_id"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
