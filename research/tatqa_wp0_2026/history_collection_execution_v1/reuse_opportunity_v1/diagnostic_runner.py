#!/usr/bin/env python3
"""Run the frozen B0-first reuse diagnostic without changing scientific contracts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

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
    strict_json_object,
    sha256_file,
    validate_consume_response,
    validate_plan_response,
    write_json_lf,
)
from trajectory_classifier import classify_trajectory  # noqa: E402


def render_diagnostic_prompt(
    template: dict[str, Any],
    actor_task: dict[str, Any],
    extra_context: Any,
    plan: Any,
    tool_result: Any,
    output_schemas: dict[str, Any],
) -> list[dict[str, str]]:
    schema = output_schemas[template["output_schema_key"]]
    values = {
        "ACTOR_TASK_JSON": canonical_json(actor_task),
        "EXTRA_CONTEXT_JSON": canonical_json(extra_context),
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


def validate_reuse_authorization(payload: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schema", "authorization_id", "protocol_sha256", "runtime_identity_sha256",
        "bundle_sha256",
        "window_start_utc", "window_end_utc", "new_request_cap", "new_token_cap",
        "allow_model_requests", "owner_decision_reference",
    }
    if set(payload) != required:
        raise PermissionError("reuse_authorization_keys_invalid")
    if payload["schema"] != "reuse_diagnostic_authorization_v1":
        raise PermissionError("reuse_authorization_schema_invalid")
    if payload["new_request_cap"] != 128 or payload["new_token_cap"] != 1700000:
        raise PermissionError("reuse_budget_invalid")
    if payload["allow_model_requests"] is not True:
        raise PermissionError("reuse_model_requests_not_allowed")
    return payload


def b0_decision(results: list[dict[str, Any]]) -> tuple[str, set[str]]:
    if any(not row["trajectory_complete"] for row in results):
        return "TECHNICAL_INVALID_STOP", set()
    success = sum(row["outcome"] == "SUCCESS" for row in results)
    nonsuccess_clusters = {
        row["source_cluster_id"] for row in results if row["outcome"] != "SUCCESS"
    }
    if success == 16:
        return "CEILING_ON_THIS_PANEL", set()
    if sum(row["outcome"] != "SUCCESS" for row in results) < 2 or len(nonsuccess_clusters) <= 1:
        return "LIMITED_HEADROOM", nonsuccess_clusters
    return "CONTINUE_STAGE_THREE", nonsuccess_clusters


def run_task(
    task: dict[str, Any],
    arm: str,
    extra_context: Any,
    protocol: dict[str, Any],
    runtime_identity: dict[str, Any],
    plan_prompt: dict[str, Any],
    consume_prompt: dict[str, Any],
    output_schemas: dict[str, Any],
    adapter: Any,
    budget: ExecutionBudget,
    raw: ImmutableRawStore,
    request_window: RequestWindow,
) -> dict[str, Any]:
    plan_messages = render_diagnostic_prompt(
        plan_prompt, task["actor_task"], extra_context, None, None, output_schemas
    )
    reservation = budget.reserve()
    request_window.check_request_allowed()
    request_id = raw.begin_request(
        f"plan|{arm}|{task['task_id']}",
        request_payload(runtime_identity, plan_messages),
    )
    plan_raw = adapter.complete(request_payload(runtime_identity, plan_messages))
    raw.persist_response(request_id, plan_raw)
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
            "tool": "calc", "params": {}, "returned_value": None,
            "status": "TOOL_ERROR", "error": "INVALID_PLAN",
        }

    consume_messages = render_diagnostic_prompt(
        consume_prompt,
        task["actor_task"],
        extra_context,
        plan,
        tool_result,
        output_schemas,
    )
    reservation = budget.reserve()
    request_window.check_request_allowed()
    request_id = raw.begin_request(
        f"consume|{arm}|{task['task_id']}",
        request_payload(runtime_identity, consume_messages),
    )
    consume_raw = adapter.complete(request_payload(runtime_identity, consume_messages))
    raw.persist_response(request_id, consume_raw)
    parsed_consume = parse_chat_response(consume_raw)
    budget.settle(reservation, parsed_consume["usage"]["total_tokens"])
    try:
        consume = validate_consume_response(strict_json_object(parsed_consume["content"]))
    except ValueError as exc:
        consume = {"status": "FORMAT_INVALID", "error": str(exc)}
    result = {
        "task_id": task["task_id"],
        "attempt": 1,
        "status": "COMPLETE",
        "plan_request": {"request_key": f"plan|{arm}|{task['task_id']}", "status": "OK"},
        "plan": plan,
        "tool_result": tool_result,
        "consume_request": {"request_key": f"consume|{arm}|{task['task_id']}", "status": "OK"},
        "consume": consume,
        "hidden_reference": task["hidden"]["reference"],
        "feedback_category": "NOT_USED_IN_DIAGNOSTIC",
    }
    classified = classify_trajectory(result, raw_complete=True, is_fixture=False)
    classified["source_cluster_id"] = task["hidden"]["source_cluster_id"]
    classified["arm"] = arm
    return classified


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("b0",))
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--runtime-identity", required=True, type=Path)
    parser.add_argument("--output-schemas", required=True, type=Path)
    parser.add_argument("--authorization", required=True, type=Path)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--raw-root", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    runtime_identity = json.loads(args.runtime_identity.read_text(encoding="utf-8"))
    output_schemas = json.loads(args.output_schemas.read_text(encoding="utf-8"))
    authorization = validate_reuse_authorization(
        json.loads(args.authorization.read_text(encoding="utf-8"))
    )
    if sha256_file(args.protocol) != authorization["protocol_sha256"]:
        raise PermissionError("protocol_hash_mismatch")
    if sha256_file(args.runtime_identity) != authorization["runtime_identity_sha256"]:
        raise PermissionError("runtime_identity_hash_mismatch")
    if sha256_file(args.bundle) != authorization["bundle_sha256"]:
        raise PermissionError("bundle_hash_mismatch")
    manifest = json.loads(
        (root.parent / "pilot_prep_v1" / "PILOT_TASK_REFERENCE_MANIFEST_V2.json")
        .read_text(encoding="utf-8")
    )
    tasks = {row["task_id"]: row for row in manifest["tasks"]}
    adapter = HttpChatAdapter(
        runtime_identity["identity"]["base_url"],
        runtime_identity["identity"]["api_path"],
        runtime_identity["identity"]["limits"]["request_timeout_seconds"],
    )
    budget = ExecutionBudget(
        request_cap=authorization["new_request_cap"],
        token_cap=authorization["new_token_cap"],
        per_request_reserve=12288,
    )
    request_window = RequestWindow.from_authorization(
        authorization,
        runtime_identity["identity"]["limits"]["request_timeout_seconds"],
    )
    raw = ImmutableRawStore(args.raw_root.resolve())
    plan_prompt = json.loads((args.root / "DIAGNOSTIC_PLAN_PROMPT.json").read_text(encoding="utf-8"))
    consume_prompt = json.loads((args.root / "DIAGNOSTIC_CONSUME_PROMPT.json").read_text(encoding="utf-8"))
    results = []
    for slot in protocol["b0_request_slots"]:
        if slot["stage"] != "plan":
            continue
        task = tasks[slot["task_id"]]
        results.append(run_task(
            task,
            "B0",
            None,
            protocol,
            runtime_identity,
            plan_prompt,
            consume_prompt,
            output_schemas,
            adapter,
            budget,
            raw,
            request_window,
        ))
    decision, nonsuccess_clusters = b0_decision(results)
    success = sum(row["outcome"] == "SUCCESS" for row in results)
    output = {
        "schema": "reuse_b0_result_v1",
        "authorization_id": authorization["authorization_id"],
        "decision": decision,
        "success_count": success,
        "non_success_count": 16 - success,
        "non_success_clusters": sorted(nonsuccess_clusters),
        "budget": budget.snapshot(),
        "results": results,
    }
    write_json_lf(args.raw_root.resolve() / "B0_RESULT.json", output)
    print(json.dumps({
        "decision": decision,
        "success": success,
        "non_success": 16 - success,
        "clusters": sorted(nonsuccess_clusters),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
