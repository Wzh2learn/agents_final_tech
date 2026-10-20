#!/usr/bin/env python3
"""Freeze model-free pilot contexts, experience contract, and request order."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SEED = "history-pilot-five-arm-order-20261019"
ARMS = ("B0", "R", "C", "U", "E")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    future_rows = [row for row in manifest["tasks"] if row["bucket"] == "future_test"]
    rules = (
        "Use only the supplied row and two periods. Compute signed difference as "
        "late minus early. Preserve the stated unit. Use the exact calculator tool "
        "and consume its actual return. Return the frozen JSON contract."
    )
    domain_context = (
        "Financial tables may use parentheses for negatives and may place units in "
        "headers or neighboring cells. A percentage-change column is not an absolute "
        "currency or quantity column. Keep source and target units explicit and do "
        "not substitute values from outside the supplied evidence."
    )
    slots = []
    for task_index, row in enumerate(future_rows):
        rotation = task_index % len(ARMS)
        arm_order = ARMS[rotation:] + ARMS[:rotation]
        for arm in arm_order:
            for stage in ("plan", "consume"):
                slots.append({
                    "request_key": f"{stage}|{row['task_id']}|{arm}",
                    "task_id": row["task_id"],
                    "cluster_id": row["hidden"]["source_cluster_id"],
                    "arm": arm,
                    "stage": stage,
                    "task_position": task_index,
                })
    protocol = {
        "schema": "pilot_protocol_freeze_draft_v1",
        "status": (
            "BLOCKED_UNRESOLVED_F11_F12"
            if manifest["status"] != "QUALIFIED_FOR_PILOT_PREPARATION"
            else "READY_FOR_PILOT_BUNDLE"
        ),
        "measurement_scope": (
            "restricted table calculation: whether real experience improves tool "
            "operation, result consumption, and final answer"
        ),
        "arms": {
            "B0": {"extra_context": None},
            "R": {"extra_context": rules},
            "C": {"extra_context": domain_context},
            "U": {
                "extra_context_source": "two unfiltered qualifying real experiences",
                "must_not_include": ["future answers", "test feedback", "hidden references"],
            },
            "E": {
                "extra_context_source": "two evidence-qualified experiences from the same pool",
                "must_not_include": ["future answers", "test feedback", "hidden references"],
            },
        },
        "context_hashes": {
            "R": sha256_text(rules),
            "C": sha256_text(domain_context),
        },
        "experience_contract": {
            "minimum_chain": [
                "frozen_task",
                "actor_plan",
                "actual_tool_execution",
                "actor_consume",
                "independent_feedback",
                "recorded_followup_or_declared_no_followup",
                "complete_raw",
            ],
            "u_eligibility": [
                "source_and_permissions_valid",
                "raw_request_response_correspondence_valid",
                "actual_tool_trace_present",
                "not_fixture",
            ],
            "e_additional_eligibility": [
                "feedback_supports_the_lesson",
                "lesson_target_matches_the_new_task",
                "applicability_boundary_is_explicit",
                "selection_does_not_use_final_success_or_future_answers",
            ],
            "context_format": {
                "experiences_per_task": 2,
                "same_schema_for_u_e": True,
                "same_order_rule_for_u_e": True,
                "length_match_tolerance_fraction": 0.05,
                "extra_context_token_cap": 2048,
            },
            "stop_if_all_filtered_experiences_make_u_e_identical": True,
        },
        "pilot_budget": {
            "request_cap": 160,
            "token_cap": 1700000,
            "retry_cap": 0,
            "concurrency": 1,
            "tasks": 16,
            "arms": 5,
            "requests_per_task_arm": 2,
        },
        "cumulative_research_budget": {
            "request_cap": 228,
            "token_cap": 2450000,
            "already_used_requests": 14,
            "already_accounted_tokens": 123488,
            "scheduled_collection_request_cap": 54,
            "scheduled_collection_token_cap": 600000,
            "pilot_request_cap": 160,
            "pilot_token_cap": 1700000,
            "failed_requests_remain_in_ledger": True,
            "fixtures_are_not_scientific_samples": True,
        },
        "order_seed": SEED,
        "request_slots": slots,
        "unresolved_task_ids": manifest["period_revision"]["unresolved_task_ids"],
    }
    if len(slots) != 160:
        raise ValueError(f"expected 160 slots, found {len(slots)}")
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(protocol, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "output": str(args.output),
        "status": protocol["status"],
        "slots": len(slots),
        "unresolved": protocol["unresolved_task_ids"],
    }, sort_keys=True))
    return 2 if protocol["unresolved_task_ids"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
