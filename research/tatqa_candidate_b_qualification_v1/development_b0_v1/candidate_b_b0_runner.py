#!/usr/bin/env python3
"""Run the authorized Candidate B development B0 with immutable raw capture."""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXECUTION_ROOT = ROOT / "research/tatqa_wp0_2026/history_collection_execution_v1"
sys.path.insert(0, str(EXECUTION_ROOT))

from collection_runner import (  # noqa: E402
    HttpChatAdapter,
    RequestWindow,
    parse_chat_response,
    request_payload,
    schema_rules,
)
from execution_core import (  # noqa: E402
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


REQUIRED_AUTHORIZATION_KEYS = {
    "schema",
    "authorization_id",
    "bundle_sha256",
    "runtime_identity_sha256",
    "protocol_sha256",
    "window_start_utc",
    "window_end_utc",
    "request_cap",
    "token_cap",
    "retry_cap",
    "concurrency",
    "allow_model_requests",
    "owner_decision_reference",
    "raw_root",
}


def load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"object_required:{path}")
    return payload


def render_prompt(
    template: dict[str, Any],
    actor_task: dict[str, Any],
    plan: Any,
    tool_result: Any,
    output_schemas: dict[str, Any],
) -> list[dict[str, str]]:
    schema = output_schemas[template["output_schema_key"]]
    values = {
        "ACTOR_TASK_JSON": canonical_json(actor_task),
        "EXTRA_CONTEXT_JSON": canonical_json(None),
        "PLAN_JSON": canonical_json(plan),
        "TOOL_RESULT_JSON": canonical_json(tool_result),
        "OUTPUT_SCHEMA_JSON": canonical_json(schema),
        "OUTPUT_RULES": schema_rules(schema),
    }
    user = template["user_template"]
    for key, value in values.items():
        user = user.replace("{{" + key + "}}", value)
    return [
        {"role": "system", "content": template["system"]},
        {"role": "user", "content": user},
    ]


def validate_authorization(payload: dict[str, Any]) -> dict[str, Any]:
    if set(payload) != REQUIRED_AUTHORIZATION_KEYS:
        raise PermissionError("authorization_keys_invalid")
    if payload["schema"] != "candidate_b_b0_authorization_v1":
        raise PermissionError("authorization_schema_invalid")
    if payload["request_cap"] != 32 or payload["token_cap"] != 600000:
        raise PermissionError("authorization_budget_invalid")
    if payload["retry_cap"] != 0 or payload["concurrency"] != 1:
        raise PermissionError("authorization_execution_policy_invalid")
    if payload["allow_model_requests"] is not True:
        raise PermissionError("model_requests_not_allowed")
    return payload


def verify_bundle(
    bundle: dict[str, Any],
    package_root: Path,
    execution_root: Path,
    qualification_root: Path,
) -> None:
    if bundle.get("schema") != "candidate_b_b0_bundle_v1":
        raise PermissionError("bundle_schema_invalid")
    if bundle.get("status") != "FROZEN_BEFORE_B0":
        raise PermissionError("bundle_status_invalid")
    for relative, expected in bundle["artifact_hashes"].items():
        if relative.startswith("execution/"):
            path = execution_root / relative.removeprefix("execution/")
        elif relative.startswith("qualification/"):
            path = qualification_root / relative.removeprefix("qualification/")
        else:
            path = package_root / relative
        if not path.is_file() or sha256_file(path) != expected:
            raise PermissionError(f"bundle_artifact_mismatch:{relative}")


def approx_equal(left: Any, right: Any) -> bool:
    try:
        return math.isclose(float(left), float(right), rel_tol=1e-9, abs_tol=1e-9)
    except (TypeError, ValueError):
        return False


def classify_result(
    task_id: str,
    cluster_id: str,
    plan: dict[str, Any],
    tool_result: dict[str, Any],
    consume: dict[str, Any],
    reference: dict[str, Any],
) -> dict[str, Any]:
    plan_valid = plan.get("status") != "INVALID_PLAN" and plan.get("tool") == "calc"
    tool_success = tool_result.get("status") == "OK"
    consume_valid = consume.get("status") in {"ANSWER", "UNKNOWN", "REFUSE"}
    expected = reference["deterministic_reference"]
    if consume.get("status") == "ANSWER":
        reference_match = approx_equal(consume.get("delta_target"), expected["late_minus_early"])
        answer_tool_consistency = approx_equal(
            consume.get("delta_target"), tool_result.get("returned_value")
        )
        unit_match = consume.get("unit") == expected["unit"]
    else:
        reference_match = False
        answer_tool_consistency = False
        unit_match = consume.get("delta_target") is None and consume.get("unit") is None

    trajectory_complete = plan_valid and tool_success and consume_valid
    success = (
        trajectory_complete
        and reference_match
        and answer_tool_consistency
        and unit_match
    )
    return {
        "task_id": task_id,
        "source_cluster_id": cluster_id,
        "arm": "B0",
        "attempt": 1,
        "trajectory_complete": trajectory_complete,
        "plan_valid": plan_valid,
        "tool_execution_success": tool_success,
        "consume_contract_valid": consume_valid,
        "reference_match": reference_match,
        "answer_tool_consistency": answer_tool_consistency,
        "unit_match": unit_match,
        "outcome": "SUCCESS" if success else "NON_SUCCESS",
        "plan": plan,
        "tool_result": tool_result,
        "consume": consume,
    }


def run_b0(
    package_root: Path,
    protocol: dict[str, Any],
    authorization: dict[str, Any],
    runtime_identity: dict[str, Any],
    plan_prompt: dict[str, Any],
    consume_prompt: dict[str, Any],
    output_schemas: dict[str, Any],
    tasks_doc: dict[str, Any],
    hidden_doc: dict[str, Any],
) -> dict[str, Any]:
    expected_order = protocol["task_order"]
    all_tasks = {row["task_id"]: row for row in tasks_doc["tasks"]}
    all_references = {row["task_id"]: row for row in hidden_doc["references"]}
    tasks = {task_id: all_tasks[task_id] for task_id in expected_order}
    references = {task_id: all_references[task_id] for task_id in expected_order}
    if len(tasks) != 16 or len(references) != 16:
        raise RuntimeError("task_reference_set_mismatch")

    adapter = HttpChatAdapter(
        runtime_identity["identity"]["base_url"],
        runtime_identity["identity"]["api_path"],
        runtime_identity["identity"]["limits"]["request_timeout_seconds"],
    )
    budget = ExecutionBudget(
        request_cap=authorization["request_cap"],
        token_cap=authorization["token_cap"],
        per_request_reserve=runtime_identity["identity"]["limits"][
            "per_request_reserve_tokens"
        ],
    )
    window = RequestWindow.from_authorization(
        authorization,
        runtime_identity["identity"]["limits"]["request_timeout_seconds"],
    )
    raw = ImmutableRawStore(Path(authorization["raw_root"]).resolve())
    results: list[dict[str, Any]] = []
    produced: list[str] = []
    stop_reason = None

    for task_id in expected_order:
        task = tasks[task_id]
        reference = references[task_id]
        plan_messages = render_prompt(
            plan_prompt, task, None, None, output_schemas
        )
        try:
            window.check_request_allowed()
        except Exception:
            stop_reason = "WINDOW_EXPIRED_BEFORE_PLAN"
            break
        reservation = budget.reserve()
        plan_request_id = raw.begin_request(
            f"plan|B0|{task_id}",
            request_payload(runtime_identity, plan_messages),
        )
        produced.append(f"plan|B0|{task_id}")
        try:
            plan_raw = adapter.complete(request_payload(runtime_identity, plan_messages))
            raw.persist_response(plan_request_id, plan_raw)
        except Exception as exc:
            raw.mark_crash(plan_request_id, type(exc).__name__)
            stop_reason = "PLAN_REQUEST_FAILED"
            break
        parsed_plan = parse_chat_response(plan_raw)
        budget.settle(reservation, parsed_plan["usage"]["total_tokens"])
        try:
            plan = validate_plan_response(strict_json_object(parsed_plan["content"]))
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

        consume_messages = render_prompt(
            consume_prompt, task, plan, tool_result, output_schemas
        )
        try:
            window.check_request_allowed()
        except Exception:
            stop_reason = "WINDOW_EXPIRED_BEFORE_CONSUME"
            break
        reservation = budget.reserve()
        consume_request_id = raw.begin_request(
            f"consume|B0|{task_id}",
            request_payload(runtime_identity, consume_messages),
        )
        produced.append(f"consume|B0|{task_id}")
        try:
            consume_raw = adapter.complete(
                request_payload(runtime_identity, consume_messages)
            )
            raw.persist_response(consume_request_id, consume_raw)
        except Exception as exc:
            raw.mark_crash(consume_request_id, type(exc).__name__)
            stop_reason = "CONSUME_REQUEST_FAILED"
            break
        parsed_consume = parse_chat_response(consume_raw)
        budget.settle(reservation, parsed_consume["usage"]["total_tokens"])
        try:
            consume = validate_consume_response(
                strict_json_object(parsed_consume["content"])
            )
        except ValueError as exc:
            consume = {"status": "FORMAT_INVALID", "error": str(exc)}

        result = classify_result(
            task_id,
            reference["source_cluster_id"],
            plan,
            tool_result,
            consume,
            reference,
        )
        results.append(result)
        write_json_lf(
            raw.root / "B0_PARTIAL_RESULT.json",
            {
                "schema": "candidate_b_b0_partial_result_v1",
                "authorization_id": authorization["authorization_id"],
                "completed_tasks": len(results),
                "results": results,
                "budget": budget.snapshot(),
            },
        )

    success = sum(row["outcome"] == "SUCCESS" for row in results)
    non_success_clusters = sorted(
        {
            row["source_cluster_id"]
            for row in results
            if row["outcome"] != "SUCCESS"
        }
    )
    if stop_reason:
        decision = "TECHNICAL_OR_WINDOW_STOP"
    elif success == 16:
        decision = "CEILING_ON_THIS_PANEL"
    elif (
        sum(row["outcome"] != "SUCCESS" for row in results) < 2
        or len(non_success_clusters) <= 1
    ):
        decision = "LIMITED_HEADROOM"
    else:
        decision = "CONTINUE_TO_ARM_DESIGN"

    output = {
        "schema": "candidate_b_b0_result_v1",
        "authorization_id": authorization["authorization_id"],
        "decision": decision,
        "stop_reason": stop_reason,
        "success_count": success,
        "non_success_count": len(results) - success,
        "non_success_clusters": non_success_clusters,
        "budget": budget.snapshot(),
        "produced_request_keys": produced,
        "results": results,
    }
    write_json_lf(raw.root / "B0_RESULT.json", output)
    return output


def preflight(
    package_root: Path,
    protocol: dict[str, Any],
    authorization: dict[str, Any],
    runtime_identity: dict[str, Any],
    tasks_doc: dict[str, Any],
    hidden_doc: dict[str, Any],
) -> dict[str, Any]:
    validate_authorization(authorization)
    if protocol.get("status") != "FROZEN_BEFORE_B0":
        raise PermissionError("protocol_not_frozen")
    task_ids = {row["task_id"] for row in tasks_doc["tasks"]}
    reference_ids = {row["task_id"] for row in hidden_doc["references"]}
    if len(protocol["task_order"]) != 16 or not set(protocol["task_order"]).issubset(task_ids):
        raise RuntimeError("development_task_count_invalid")
    if not set(protocol["task_order"]).issubset(reference_ids):
        raise RuntimeError("development_reference_count_invalid")
    if protocol["budget"]["request_cap"] != 32 or protocol["budget"]["retry_cap"] != 0:
        raise RuntimeError("protocol_budget_invalid")
    generation = runtime_identity["identity"]["generation"]
    if generation["max_tokens"] != 256:
        raise RuntimeError("max_tokens_drift")
    if runtime_identity["identity"]["chat_template_kwargs"] != {"enable_thinking": False}:
        raise RuntimeError("thinking_switch_drift")
    return {
        "status": "PREFLIGHT_PASS_NO_REQUESTS",
        "tasks": 16,
        "planned_requests": 32,
        "model_calls": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "b0"))
    parser.add_argument("--package-root", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--authorization", required=True, type=Path)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--runtime-identity", required=True, type=Path)
    args = parser.parse_args()

    package_root = args.package_root.resolve()
    qualification_root = package_root.parent
    execution_root = ROOT / "research/tatqa_wp0_2026/history_collection_execution_v1"
    protocol = load_object(args.protocol)
    authorization = validate_authorization(load_object(args.authorization))
    runtime_identity = load_object(args.runtime_identity)
    bundle = load_object(args.bundle)
    verify_bundle(bundle, package_root, execution_root, qualification_root)
    if sha256_file(args.protocol) != authorization["protocol_sha256"]:
        raise PermissionError("protocol_hash_mismatch")
    if sha256_file(args.runtime_identity) != authorization["runtime_identity_sha256"]:
        raise PermissionError("runtime_identity_hash_mismatch")
    if sha256_file(args.bundle) != authorization["bundle_sha256"]:
        raise PermissionError("bundle_hash_mismatch")

    tasks_doc = load_object(qualification_root / "CANDIDATE_B_TASKS_DRAFT.json")
    hidden_doc = load_object(qualification_root / "HIDDEN_REFERENCE_MANIFEST.json")
    if args.command == "preflight":
        print(
            json.dumps(
                preflight(
                    package_root,
                    protocol,
                    authorization,
                    runtime_identity,
                    tasks_doc,
                    hidden_doc,
                ),
                sort_keys=True,
            )
        )
        return 0

    output = run_b0(
        package_root,
        protocol,
        authorization,
        runtime_identity,
        load_object(execution_root / "reuse_opportunity_v1/DIAGNOSTIC_PLAN_PROMPT.json"),
        load_object(execution_root / "reuse_opportunity_v1/DIAGNOSTIC_CONSUME_PROMPT.json"),
        load_object(execution_root / "OUTPUT_SCHEMAS.json"),
        tasks_doc,
        hidden_doc,
    )
    print(
        json.dumps(
            {
                "decision": output["decision"],
                "success": output["success_count"],
                "non_success": output["non_success_count"],
                "requests": output["budget"]["requests"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
