#!/usr/bin/env python3
"""Request-accounted B0 plan -> evidence_lookup -> consume runner."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from finrank_contract import (
    HttpChatAdapter,
    ImmutableRawStore,
    PACKAGE,
    REQUEST_CAP,
    SHARED_LEDGER,
    SharedGenerationLedger,
    TOKEN_CAP,
    classify_result,
    evidence_lookup,
    load_object,
    parse_chat_response,
    render_messages,
    request_payload,
    sha256_text,
    strict_json_object,
    utc_now,
    validate_consume,
    validate_consumed_evidence,
    validate_plan,
    validate_reference_separation,
    verify_bundle,
    write_json,
)


def settled_failure(
    ledger: SharedGenerationLedger,
    record_id: str,
    raw: ImmutableRawStore,
    request_root: Path | None,
    error: str,
) -> None:
    ledger.settle(record_id, "FAILED", None, error)
    if request_root is not None:
        raw.mark_crash(request_root, error)


def execute(run_name: str, expected_prior_requests: int) -> int:
    verify_bundle(PACKAGE / "BUNDLE_C3_B0_V4_FIX1.json")
    fixture = load_object(PACKAGE / "FIXTURE_RECEIPT_C3.json")
    if fixture.get("status") != "PASS":
        raise RuntimeError("fixture_gate_not_passed")
    runtime = load_object(PACKAGE / "RUNTIME_IDENTITY_OVERRIDE_V1.json")
    actor_doc = load_object(PACKAGE / "TASKS_ACTOR_V3.json")
    reference_doc = load_object(PACKAGE / "REFERENCES_V3.json")
    tasks = {item["task_id"]: item for item in actor_doc["tasks"]}
    references = {
        item["task_id"]: item for item in reference_doc["tasks"]
    }
    runtime_identity = runtime
    adapter = HttpChatAdapter(
        runtime_identity["identity"]["base_url"],
        runtime_identity["identity"]["limits"]["request_timeout_seconds"],
    )
    ledger = SharedGenerationLedger(SHARED_LEDGER)
    current = load_object(SHARED_LEDGER)["new_generation_budget"]
    if current["requests_used"] != expected_prior_requests:
        raise RuntimeError("shared_ledger_prior_request_count_mismatch")
    if current["requests_used"] + 14 > REQUEST_CAP:
        raise RuntimeError("c2_request_cap_invalid")
    if current["accounting_tokens_used"] + 14 * 10240 > TOKEN_CAP:
        raise RuntimeError("c2_token_cap_invalid")
    raw = ImmutableRawStore(PACKAGE / "raw" / run_name)
    results: list[dict[str, Any]] = []
    produced: list[str] = []
    stop_reason: str | None = None
    run_id = f"FINRANK_C3_{run_name}_{utc_now().replace(':', '').replace('-', '')}"
    for task_id in actor_doc["task_order"]:
        task = tasks[task_id]
        reference = references[task_id]
        stage_values: dict[str, Any] = {}
        task_error: str | None = None
        for stage in ("plan", "consume"):
            tool_result = stage_values.get("tool_result")
            messages = render_messages(stage, task, tool_result)
            validate_reference_separation(task, messages)
            payload = request_payload(runtime_identity, messages)
            logical_id = f"{stage}|{run_name}|{task_id}"
            record_id = ledger.reserve(
                run_id,
                logical_id,
                sha256_text(payload),
            )
            produced.append(logical_id)
            request_root: Path | None = None
            try:
                _, request_root = raw.begin_request(logical_id, payload)
                raw_response = adapter.complete(payload)
                raw.persist_response(request_root, raw_response)
                parsed = parse_chat_response(raw_response)
                ledger.settle(
                    record_id,
                    "OK",
                    int(parsed["usage"]["total_tokens"]),
                )
            except Exception as exc:
                error = f"{type(exc).__name__}:{exc}"
                settled_failure(ledger, record_id, raw, request_root, error)
                stop_reason = f"{stage.upper()}_REQUEST_FAILED"
                task_error = error
                break
            try:
                model_json = strict_json_object(parsed["content"])
                if stage == "plan":
                    plan = validate_plan(model_json)
                    tool_result = evidence_lookup(task, {
                        "candidate_ids": plan["evidence_candidate_ids"]
                    }, tasks)
                    stage_values["plan"] = plan
                    stage_values["tool_result"] = tool_result
                else:
                    consume = validate_consume(model_json)
                    validate_consumed_evidence(
                        consume,
                        stage_values["tool_result"],
                    )
                    stage_values["consume"] = consume
            except ValueError as exc:
                task_error = f"schema_or_contract:{exc}"
                if stage == "plan":
                    stage_values["plan"] = {
                        "error": task_error,
                    }
                    stage_values["tool_result"] = {
                        "tool_status": "INVALID_ARGUMENT",
                        "evidence": [],
                        "error": "invalid_plan",
                    }
                else:
                    stage_values["consume"] = {
                        "error": task_error,
                        "answer_status": "FORMAT_INVALID",
                        "facts": [],
                        "used_candidate_ids": [],
                    }
        if "consume" not in stage_values:
            break
        result = classify_result(
            task_id,
            stage_values["plan"],
            stage_values["tool_result"],
            stage_values["consume"],
            reference,
        )
        if task_error and result["error_class"] is None:
            result["error_class"] = "ENGINEERING_SCHEMA_OR_TOOL"
            result["outcome"] = "NON_SUCCESS"
        result["task_error"] = task_error
        results.append(result)
        write_json(
            PACKAGE / "results" / run_name / "B0_PARTIAL_RESULT.json",
            {
                "schema": "finrank_b0_partial_v2",
                "run_id": run_id,
                "results": results,
                "produced": produced,
            },
        )
        if stop_reason:
            break
    success = sum(item["outcome"] == "SUCCESS" for item in results)
    output = {
        "schema": "finrank_b0_result_v2",
        "status": (
            "COMPLETE_DEVELOPMENT_OBSERVATION"
            if len(results) == 7 and not stop_reason
            else "STOPPED_PARTIAL"
        ),
        "scientific_scope": (
            "Seven retained development tasks only; not statistical confirmation."
        ),
        "run_id": run_id,
        "run_name": run_name,
        "bundle_sha256": __import__("hashlib").sha256(
            (PACKAGE / "BUNDLE_C3_B0_V4_FIX1.json").read_bytes()
        ).hexdigest(),
        "stop_reason": stop_reason,
        "generation_requests": len(produced),
        "success_count": success,
        "non_success_count": len(results) - success,
        "error_classes": {
            "ENGINEERING_SCHEMA_OR_TOOL": sum(
                item["error_class"] == "ENGINEERING_SCHEMA_OR_TOOL"
                for item in results
            ),
            "SEMANTIC_SELECTION_OR_ANSWER": sum(
                item["error_class"] == "SEMANTIC_SELECTION_OR_ANSWER"
                for item in results
            ),
        },
        "produced_request_keys": produced,
        "results": results,
    }
    write_json(PACKAGE / "results" / run_name / "B0_RESULT.json", output)
    print(
        json.dumps(
            {
                "status": output["status"],
                "requests": output["generation_requests"],
                "success": success,
                "non_success": output["non_success_count"],
                "stop_reason": stop_reason,
            },
            sort_keys=True,
        )
    )
    return 0 if output["status"] == "COMPLETE_DEVELOPMENT_OBSERVATION" else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ledger",
        type=Path,
        default=SHARED_LEDGER,
        help="Shared research generation ledger; path is recorded but authority is fixed.",
    )
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument(
        "--run-name",
        default="B0_V4_MINIFIED_JSON",
        choices=("B0_V4_MINIFIED_JSON",),
    )
    parser.add_argument("--expected-prior-requests", type=int, default=42)
    args = parser.parse_args()
    if args.ledger.resolve() != SHARED_LEDGER.resolve():
        raise SystemExit("ledger_path_mismatch")
    if args.preflight:
        verify_bundle(PACKAGE / "BUNDLE_C3_B0_V4_FIX1.json")
        fixture = load_object(PACKAGE / "FIXTURE_RECEIPT_C3.json")
        if fixture.get("status") != "PASS":
            raise SystemExit("fixture_gate_not_passed")
        print(
            json.dumps(
                {
                    "status": "PREFLIGHT_PASS_NO_REQUESTS",
                    "planned_generation_requests": 14,
                    "run_name": args.run_name,
                    "expected_prior_requests": args.expected_prior_requests,
                }
            )
        )
        return 0
    return execute(args.run_name, args.expected_prior_requests)


if __name__ == "__main__":
    raise SystemExit(main())
