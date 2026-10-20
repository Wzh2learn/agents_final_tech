#!/usr/bin/env python3
"""Exploratory B0 runner for same-number role-binding tasks."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
PARENT = PACKAGE.parent
EXECUTION_ROOT = ROOT / "research/tatqa_wp0_2026/history_collection_execution_v1"
sys.path.insert(0, str(EXECUTION_ROOT))

from collection_runner import (
    HttpChatAdapter,
    RequestWindow,
    parse_chat_response,
    request_payload,
    schema_rules,
)
from execution_core import (
    ExecutionBudget,
    ImmutableRawStore,
    canonical_json,
    evaluate_expression,
    sha256_file,
    strict_json_object,
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


def validate_authorization(payload: dict[str, Any]) -> dict[str, Any]:
    if set(payload) != REQUIRED_AUTHORIZATION_KEYS:
        raise PermissionError("authorization_keys_invalid")
    if payload["schema"] != "same_number_role_b0_authorization_v1":
        raise PermissionError("authorization_schema_invalid")
    if payload["request_cap"] != 48 or payload["token_cap"] != 600000:
        raise PermissionError("authorization_budget_invalid")
    if payload["retry_cap"] != 0 or payload["concurrency"] != 1:
        raise PermissionError("authorization_execution_policy_invalid")
    if payload["allow_model_requests"] is not True:
        raise PermissionError("model_requests_not_allowed")
    return payload


def render_prompt(template, actor_task, plan, tool_result, output_schemas):
    schema = output_schemas[template["output_schema_key"]]
    values = {
        "ACTOR_TASK_JSON": canonical_json(actor_task),
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


def approx_equal(left, right):
    try:
        return math.isclose(float(left), float(right), rel_tol=1e-9, abs_tol=1e-9)
    except (TypeError, ValueError):
        return False


def validate_role_consume(payload):
    if set(payload) != {"decision", "calc_value", "unit"}:
        raise ValueError("consume_keys_invalid")
    decision = payload["decision"]
    if decision not in {"SUPPORTED", "WRONG_ROLE", "UNKNOWN", "REFUSE"}:
        raise ValueError("consume_decision_invalid")
    if decision in {"SUPPORTED", "WRONG_ROLE"}:
        if isinstance(payload["calc_value"], bool) or not isinstance(payload["calc_value"], (int, float)):
            raise ValueError("role_decision_requires_numeric_calc_value")
        if not isinstance(payload["unit"], str) or not payload["unit"].strip():
            raise ValueError("role_decision_requires_unit")
    elif payload["calc_value"] is not None or payload["unit"] is not None:
        raise ValueError("non_answer_requires_null_fields")
    return payload


def classify(task_id, cluster_id, plan, tool_result, consume, hidden):
    plan_valid = plan.get("tool") == "calc"
    tool_success = tool_result.get("status") == "OK"
    consume_valid = consume.get("decision") in {"SUPPORTED", "WRONG_ROLE", "UNKNOWN", "REFUSE"}
    numeric_match = approx_equal(consume.get("calc_value"), tool_result.get("returned_value"))
    decision_match = consume.get("decision") == hidden["expected_decision"]
    success = plan_valid and tool_success and consume_valid and numeric_match and decision_match
    return {
        "task_id": task_id,
        "source_cluster_id": cluster_id,
        "scope": hidden["partition"],
        "case_type": hidden["case_type"],
        "plan_valid": plan_valid,
        "tool_execution_success": tool_success,
        "consume_contract_valid": consume_valid,
        "numeric_match": numeric_match,
        "decision_match": decision_match,
        "expected_decision": hidden["expected_decision"],
        "actual_decision": consume.get("decision"),
        "outcome": "SUCCESS" if success else "NON_SUCCESS",
        "plan": plan,
        "tool_result": tool_result,
        "consume": consume,
    }


def run_b0(protocol, authorization, runtime_identity, tasks_doc, plan_prompt, consume_prompt, output_schemas):
    tasks = {row["task_id"]: row for row in tasks_doc["tasks"]}
    hidden = {row["task_id"]: row for row in tasks_doc["hidden_references"]}
    order = protocol["task_order"]
    if len(order) != 24 or set(order) != set(tasks):
        raise RuntimeError("task_order_mismatch")
    adapter = HttpChatAdapter(
        runtime_identity["identity"]["base_url"],
        runtime_identity["identity"]["api_path"],
        runtime_identity["identity"]["limits"]["request_timeout_seconds"],
    )
    budget = ExecutionBudget(
        request_cap=authorization["request_cap"],
        token_cap=authorization["token_cap"],
        per_request_reserve=runtime_identity["identity"]["limits"]["per_request_reserve_tokens"],
    )
    window = RequestWindow.from_authorization(
        authorization,
        runtime_identity["identity"]["limits"]["request_timeout_seconds"],
    )
    raw = ImmutableRawStore(Path(authorization["raw_root"]).resolve())
    results = []
    produced = []
    stop_reason = None
    for task_id in order:
        task = tasks[task_id]
        reference = hidden[task_id]
        plan_messages = render_prompt(plan_prompt, task, None, None, output_schemas)
        try:
            window.check_request_allowed()
        except Exception:
            stop_reason = "WINDOW_EXPIRED_BEFORE_PLAN"
            break
        reservation = budget.reserve()
        plan_key = f"plan|B0|{task_id}"
        plan_request_id = raw.begin_request(plan_key, request_payload(runtime_identity, plan_messages))
        produced.append(plan_key)
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
            tool_result = {"tool": "calc", "params": {}, "returned_value": None, "status": "TOOL_ERROR", "error": "INVALID_PLAN"}
        consume_messages = render_prompt(consume_prompt, task, plan, tool_result, output_schemas)
        try:
            window.check_request_allowed()
        except Exception:
            stop_reason = "WINDOW_EXPIRED_BEFORE_CONSUME"
            break
        reservation = budget.reserve()
        consume_key = f"consume|B0|{task_id}"
        consume_request_id = raw.begin_request(consume_key, request_payload(runtime_identity, consume_messages))
        produced.append(consume_key)
        try:
            consume_raw = adapter.complete(request_payload(runtime_identity, consume_messages))
            raw.persist_response(consume_request_id, consume_raw)
        except Exception as exc:
            raw.mark_crash(consume_request_id, type(exc).__name__)
            stop_reason = "CONSUME_REQUEST_FAILED"
            break
        parsed_consume = parse_chat_response(consume_raw)
        budget.settle(reservation, parsed_consume["usage"]["total_tokens"])
        try:
            consume = validate_role_consume(strict_json_object(parsed_consume["content"]))
        except ValueError as exc:
            consume = {"decision": "FORMAT_INVALID", "calc_value": None, "unit": None, "error": str(exc)}
        results.append(classify(task_id, reference["source_cluster_id"], plan, tool_result, consume, reference))
        write_json_lf(raw.root / "B0_PARTIAL_RESULT.json", {"schema": "same_number_role_b0_partial_v1", "results": results, "budget": budget.snapshot()})
    success = sum(row["outcome"] == "SUCCESS" for row in results)
    non_success_clusters = sorted({row["source_cluster_id"] for row in results if row["outcome"] != "SUCCESS"})
    if stop_reason:
        decision = "TECHNICAL_OR_WINDOW_STOP"
    elif success == 24:
        decision = "CEILING_ON_THIS_PANEL"
    elif sum(row["outcome"] != "SUCCESS" for row in results) < 2 or len(non_success_clusters) <= 1:
        decision = "LIMITED_HEADROOM"
    else:
        decision = "CONTINUE_TO_ARM_DESIGN"
    output = {
        "schema": "same_number_role_b0_result_v1",
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


def preflight(protocol, authorization, runtime_identity, tasks_doc):
    if len(tasks_doc["tasks"]) != 24 or len(tasks_doc["hidden_references"]) != 24:
        raise RuntimeError("exploratory_task_count_invalid")
    if protocol["budget"]["request_cap"] != 48 or protocol["budget"]["retry_cap"] != 0:
        raise RuntimeError("protocol_budget_invalid")
    if runtime_identity["identity"]["generation"]["max_tokens"] != 256:
        raise RuntimeError("max_tokens_drift")
    if runtime_identity["identity"]["chat_template_kwargs"] != {"enable_thinking": False}:
        raise RuntimeError("thinking_switch_drift")
    return {"status": "PREFLIGHT_PASS_NO_REQUESTS", "tasks": 24, "planned_requests": 48, "model_calls": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "b0"))
    parser.add_argument("--package-root", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--authorization", required=True, type=Path)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--runtime-identity", required=True, type=Path)
    args = parser.parse_args()
    package_root = args.package_root.resolve()
    protocol = load_object(args.protocol)
    authorization = validate_authorization(load_object(args.authorization))
    runtime_identity = load_object(args.runtime_identity)
    bundle = load_object(args.bundle)
    if bundle.get("schema") != "same_number_role_b0_bundle_v1" or bundle.get("status") != "FROZEN_BEFORE_B0":
        raise PermissionError("bundle_invalid")
    for relative, expected in bundle["artifact_hashes"].items():
        if relative.startswith("runtime/"):
            path = EXECUTION_ROOT / relative.removeprefix("runtime/")
        elif relative.startswith("tasks/"):
            path = PARENT / relative.removeprefix("tasks/")
        else:
            path = PACKAGE / relative
        if not path.is_file() or sha256_file(path) != expected:
            raise PermissionError(f"bundle_artifact_mismatch:{relative}")
    if sha256_file(args.protocol) != authorization["protocol_sha256"]:
        raise PermissionError("protocol_hash_mismatch")
    if sha256_file(args.runtime_identity) != authorization["runtime_identity_sha256"]:
        raise PermissionError("runtime_identity_hash_mismatch")
    if sha256_file(args.bundle) != authorization["bundle_sha256"]:
        raise PermissionError("bundle_hash_mismatch")
    tasks_doc = load_object(PARENT / "SAME_NUMBER_ROLE_TASKS_DRAFT.json")
    if args.command == "preflight":
        print(json.dumps(preflight(protocol, authorization, runtime_identity, tasks_doc), sort_keys=True))
        return 0
    output = run_b0(
        protocol,
        authorization,
        runtime_identity,
        tasks_doc,
        load_object(PACKAGE / "SAME_NUMBER_ROLE_PLAN_PROMPT.json"),
        load_object(PACKAGE / "SAME_NUMBER_ROLE_CONSUME_PROMPT.json"),
        load_object(PACKAGE / "SAME_NUMBER_ROLE_OUTPUT_SCHEMAS.json"),
    )
    print(json.dumps({"decision": output["decision"], "success": output["success_count"], "non_success": output["non_success_count"], "requests": output["budget"]["requests"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
