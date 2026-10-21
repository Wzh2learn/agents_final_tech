#!/usr/bin/env python3
"""Recover a bounded role-history collection without replaying crashed calls."""

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


def feedback_for(result):
    if result["outcome"] == "SUCCESS":
        category = "SUCCESS"
        message = "The first attempt was correct. Preserve the same evidence-role decision."
    elif not result["plan_valid"] or not result["tool_execution_success"]:
        category = "PLAN_OR_TOOL_ERROR"
        message = "The calculator plan or tool execution failed. Emit one valid calc expression."
    elif not result["consume_contract_valid"]:
        category = "FORMAT_INVALID"
        message = "The consume response violated the output contract. Use SUPPORTED/WRONG_ROLE with numeric calc_value and unit."
    elif not result["decision_match"]:
        category = "ROLE_DECISION_ERROR"
        message = f"The evidence-role decision was incorrect; the correct decision is {result['expected_decision']}."
    else:
        category = "NUMERIC_ERROR"
        message = "The role decision was correct but the calculator value did not match."
    return {"category": category, "message": message}


def run_attempt(
    base_runner,
    adapter,
    raw,
    budget,
    window,
    runtime_identity,
    task,
    hidden,
    plan_prompt,
    consume_prompt,
    output_schemas,
    attempt,
    context,
):
    plan_messages = render_prompt(plan_prompt, task, context, None, None, output_schemas)
    window.check_request_allowed()
    reservation = budget.reserve()
    plan_key = f"plan|HCOLLECT|{task['task_id']}|a{attempt}"
    plan_request_id = raw.begin_request(plan_key, request_payload(runtime_identity, plan_messages))
    try:
        plan_raw = adapter.complete(request_payload(runtime_identity, plan_messages))
        raw.persist_response(plan_request_id, plan_raw)
    except Exception as exc:
        raw.mark_crash(plan_request_id, type(exc).__name__)
        raise
    parsed_plan = parse_chat_response(plan_raw)
    budget.settle(reservation, parsed_plan["usage"]["total_tokens"])
    try:
        plan = validate_plan_response(strict_json_object(parsed_plan["content"]))
        tool_result = {"tool": "calc", "params": plan["params"], "returned_value": evaluate_expression(plan["params"]["expression"]), "status": "OK", "error": None}
    except (ValueError, ArithmeticError) as exc:
        plan = {"status": "INVALID_PLAN", "error": str(exc)}
        tool_result = {"tool": "calc", "params": {}, "returned_value": None, "status": "TOOL_ERROR", "error": "INVALID_PLAN"}
    consume_messages = render_prompt(consume_prompt, task, context, plan, tool_result, output_schemas)
    window.check_request_allowed()
    reservation = budget.reserve()
    consume_key = f"consume|HCOLLECT|{task['task_id']}|a{attempt}"
    consume_request_id = raw.begin_request(consume_key, request_payload(runtime_identity, consume_messages))
    try:
        consume_raw = adapter.complete(request_payload(runtime_identity, consume_messages))
        raw.persist_response(consume_request_id, consume_raw)
    except Exception as exc:
        raw.mark_crash(consume_request_id, type(exc).__name__)
        raise
    parsed_consume = parse_chat_response(consume_raw)
    budget.settle(reservation, parsed_consume["usage"]["total_tokens"])
    try:
        consume = base_runner.validate_role_consume(strict_json_object(parsed_consume["content"]))
    except ValueError as exc:
        consume = {"decision": "FORMAT_INVALID", "calc_value": None, "unit": None, "error": str(exc)}
    result = base_runner.classify(task["task_id"], hidden["source_cluster_id"], plan, tool_result, consume, hidden)
    result["attempt"] = attempt
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "collect"))
    parser.add_argument("--package-root", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--authorization", required=True, type=Path)
    parser.add_argument("--runtime-identity", required=True, type=Path)
    args = parser.parse_args()
    base_runner = load_runner()
    protocol = load_object(args.protocol)
    authorization = load_object(args.authorization)
    if authorization.get("schema") != "same_number_role_history_authorization_v1":
        raise PermissionError("authorization_schema_invalid")
    expected_requests = 2 * len(protocol["task_order"])
    if authorization.get("request_cap") != expected_requests or authorization.get("retry_cap") != 0:
        raise PermissionError("authorization_budget_invalid")
    runtime_identity = load_object(args.runtime_identity)
    if sha256_file(args.protocol) != authorization["protocol_sha256"]:
        raise PermissionError("protocol_hash_mismatch")
    if sha256_file(args.runtime_identity) != authorization["runtime_identity_sha256"]:
        raise PermissionError("runtime_identity_hash_mismatch")
    tasks_doc = load_object(PARENT / "SAME_NUMBER_ROLE_TASKS_DRAFT.json")
    if args.command == "preflight":
        print(json.dumps({"status": "PREFLIGHT_PASS_NO_REQUESTS", "tasks": len(protocol["task_order"]), "planned_requests": expected_requests, "model_calls": 0}, sort_keys=True))
        return 0
    tasks = {row["task_id"]: row for row in tasks_doc["tasks"]}
    hidden = {row["task_id"]: row for row in tasks_doc["hidden_references"]}
    adapter = HttpChatAdapter(runtime_identity["identity"]["base_url"], runtime_identity["identity"]["api_path"], runtime_identity["identity"]["limits"]["request_timeout_seconds"])
    budget = ExecutionBudget(request_cap=authorization["request_cap"], token_cap=authorization["token_cap"], per_request_reserve=runtime_identity["identity"]["limits"]["per_request_reserve_tokens"])
    window = RequestWindow.from_authorization(authorization, runtime_identity["identity"]["limits"]["request_timeout_seconds"])
    raw = ImmutableRawStore(Path(authorization["raw_root"]).resolve())
    experiences = []
    for task_id in protocol["task_order"]:
        task = tasks[task_id]
        reference = hidden[task_id]
        first = run_attempt(base_runner, adapter, raw, budget, window, runtime_identity, task, reference, load_object(PACKAGE / "SAME_NUMBER_ROLE_ARM_PLAN_PROMPT.json"), load_object(PACKAGE / "SAME_NUMBER_ROLE_ARM_CONSUME_PROMPT.json"), load_object(PACKAGE / "SAME_NUMBER_ROLE_OUTPUT_SCHEMAS.json"), 1, None)
        feedback = feedback_for(first)
        second_context = {"actual_first_attempt": first, "feedback": feedback}
        second = run_attempt(base_runner, adapter, raw, budget, window, runtime_identity, task, reference, load_object(PACKAGE / "SAME_NUMBER_ROLE_ARM_PLAN_PROMPT.json"), load_object(PACKAGE / "SAME_NUMBER_ROLE_ARM_CONSUME_PROMPT.json"), load_object(PACKAGE / "SAME_NUMBER_ROLE_OUTPUT_SCHEMAS.json"), 2, second_context)
        experiences.append({"task_id": task_id, "source_cluster_id": reference["source_cluster_id"], "case_type": reference["case_type"], "target_role": reference["target_role"], "candidate_role": reference["candidate_role"], "attempts": [first, second], "feedback": feedback})
        write_json_lf(raw.root / "HISTORY_PARTIAL_RESULT.json", {"schema": "same_number_role_history_partial_v1", "experiences": experiences, "budget": budget.snapshot()})
    write_json_lf(raw.root / "HISTORY_COLLECTION_RESULT.json", {"schema": "same_number_role_history_result_v1", "authorization_id": authorization["authorization_id"], "experiences": experiences, "budget": budget.snapshot()})
    print(json.dumps({"tasks": len(experiences), "requests": budget.snapshot()["requests"], "corrections": sum(1 for row in experiences if row["attempts"][0]["outcome"] != "SUCCESS" and row["attempts"][1]["outcome"] == "SUCCESS")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
