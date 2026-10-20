#!/usr/bin/env python3
"""Run one frozen R or C arm on the same-number role failure pairs."""

from __future__ import annotations

import argparse
import importlib.util
import json
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


def load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"object_required:{path}")
    return payload


def load_runner():
    path = PACKAGE / "same_number_role_b0_runner.py"
    spec = importlib.util.spec_from_file_location("role_b0_runner", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("runner_import_failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render_prompt(template, actor_task, context, plan, tool_result, output_schemas):
    schema = output_schemas[template["output_schema_key"]]
    values = {
        "ACTOR_TASK_JSON": canonical_json(actor_task),
        "EXTRA_CONTEXT_JSON": canonical_json(context),
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


def run_arm(protocol, authorization, runtime_identity, tasks_doc, plan_prompt, consume_prompt, output_schemas):
    base_runner = load_runner()
    tasks = {row["task_id"]: row for row in tasks_doc["tasks"]}
    hidden = {row["task_id"]: row for row in tasks_doc["hidden_references"]}
    order = protocol["task_order"]
    expected_count = len(order)
    if expected_count < 2 or len(set(order)) != expected_count:
        raise RuntimeError("arm_task_order_invalid")
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
    default_context = protocol.get("context")
    context_by_task = protocol.get("context_by_task", {})
    arm = protocol["arm"]
    results = []
    produced = []
    stop_reason = None
    for task_id in order:
        task = tasks[task_id]
        reference = hidden[task_id]
        context = context_by_task.get(task_id, default_context)
        plan_messages = render_prompt(plan_prompt, task, context, None, None, output_schemas)
        try:
            window.check_request_allowed()
        except Exception:
            stop_reason = "WINDOW_EXPIRED_BEFORE_PLAN"
            break
        reservation = budget.reserve()
        plan_key = f"plan|{arm}|{task_id}"
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
            tool_result = {"tool": "calc", "params": plan["params"], "returned_value": evaluate_expression(plan["params"]["expression"]), "status": "OK", "error": None}
        except (ValueError, ArithmeticError) as exc:
            plan = {"status": "INVALID_PLAN", "error": str(exc)}
            tool_result = {"tool": "calc", "params": {}, "returned_value": None, "status": "TOOL_ERROR", "error": "INVALID_PLAN"}
        consume_messages = render_prompt(consume_prompt, task, context, plan, tool_result, output_schemas)
        try:
            window.check_request_allowed()
        except Exception:
            stop_reason = "WINDOW_EXPIRED_BEFORE_CONSUME"
            break
        reservation = budget.reserve()
        consume_key = f"consume|{arm}|{task_id}"
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
            consume = base_runner.validate_role_consume(strict_json_object(parsed_consume["content"]))
        except ValueError as exc:
            consume = {"decision": "FORMAT_INVALID", "calc_value": None, "unit": None, "error": str(exc)}
        result = base_runner.classify(task_id, reference["source_cluster_id"], plan, tool_result, consume, reference)
        result["arm"] = arm
        results.append(result)
        write_json_lf(raw.root / "ARM_PARTIAL_RESULT.json", {"schema": "same_number_role_arm_partial_v1", "arm": arm, "results": results, "budget": budget.snapshot()})
    success = sum(row["outcome"] == "SUCCESS" for row in results)
    non_success_clusters = sorted({row["source_cluster_id"] for row in results if row["outcome"] != "SUCCESS"})
    if stop_reason:
        decision = "TECHNICAL_OR_WINDOW_STOP"
    elif success == expected_count:
        decision = f"{arm}_EXPLAINS_HEADROOM_STOP"
    elif expected_count - success < 2 or len(non_success_clusters) <= 1:
        decision = f"{arm}_LIMITED_RESIDUAL"
    else:
        if arm == "R":
            decision = "RUN_NEXT_ARM"
        elif arm == "C":
            decision = "HISTORY_COLLECTION_REQUIRED"
        else:
            decision = "H_INSUFFICIENT"
    output = {
        "schema": "same_number_role_arm_result_v1",
        "authorization_id": authorization["authorization_id"],
        "arm": arm,
        "decision": decision,
        "stop_reason": stop_reason,
        "success_count": success,
        "non_success_count": len(results) - success,
        "non_success_clusters": non_success_clusters,
        "budget": budget.snapshot(),
        "produced_request_keys": produced,
        "results": results,
    }
    write_json_lf(raw.root / "ARM_RESULT.json", output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "run"))
    parser.add_argument("--package-root", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--authorization", required=True, type=Path)
    parser.add_argument("--runtime-identity", required=True, type=Path)
    args = parser.parse_args()
    package_root = args.package_root.resolve()
    protocol = load_object(args.protocol)
    authorization = load_object(args.authorization)
    if authorization["schema"] != "same_number_role_arm_authorization_v1":
        raise PermissionError("authorization_schema_invalid")
    if (
        authorization["request_cap"] != 2 * len(protocol["task_order"])
        or authorization["retry_cap"] != 0
        or authorization["concurrency"] != 1
    ):
        raise PermissionError("authorization_budget_invalid")
    if authorization["allow_model_requests"] is not True:
        raise PermissionError("model_requests_not_allowed")
    runtime_identity = load_object(args.runtime_identity)
    if sha256_file(args.protocol) != authorization["protocol_sha256"]:
        raise PermissionError("protocol_hash_mismatch")
    if sha256_file(args.runtime_identity) != authorization["runtime_identity_sha256"]:
        raise PermissionError("runtime_identity_hash_mismatch")
    tasks_doc = load_object(PARENT / "SAME_NUMBER_ROLE_TASKS_DRAFT.json")
    if args.command == "preflight":
        if protocol["arm"] not in {"R", "C", "H", "K", "R_RESIDUAL", "C_RESIDUAL"} or len(protocol["task_order"]) < 2:
            raise RuntimeError("arm_protocol_invalid")
        print(json.dumps({"status": "PREFLIGHT_PASS_NO_REQUESTS", "arm": protocol["arm"], "tasks": len(protocol["task_order"]), "planned_requests": 2 * len(protocol["task_order"]), "model_calls": 0}, sort_keys=True))
        return 0
    output = run_arm(
        protocol,
        authorization,
        runtime_identity,
        tasks_doc,
        load_object(PACKAGE / "SAME_NUMBER_ROLE_ARM_PLAN_PROMPT.json"),
        load_object(PACKAGE / "SAME_NUMBER_ROLE_ARM_CONSUME_PROMPT.json"),
        load_object(PACKAGE / "SAME_NUMBER_ROLE_OUTPUT_SCHEMAS.json"),
    )
    print(json.dumps({"arm": output["arm"], "decision": output["decision"], "success": output["success_count"], "non_success": output["non_success_count"], "requests": output["budget"]["requests"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
