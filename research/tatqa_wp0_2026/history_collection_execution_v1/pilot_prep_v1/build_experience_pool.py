#!/usr/bin/env python3
"""Build real-history experience qualification and U/E context export."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SEED = "experience-context-selection-20261019"


def rank(task_id: str, experience_id: str) -> str:
    return hashlib.sha256(
        f"{SEED}:{task_id}:{experience_id}".encode("utf-8")
    ).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execution-result", required=True, type=Path)
    parser.add_argument("--source-manifest", required=True, type=Path)
    parser.add_argument("--future-manifest", required=True, type=Path)
    parser.add_argument("--pool-output", required=True, type=Path)
    parser.add_argument("--context-output", required=True, type=Path)
    args = parser.parse_args()
    result = json.loads(args.execution_result.read_text(encoding="utf-8"))
    future = json.loads(args.future_manifest.read_text(encoding="utf-8"))
    source_manifest = json.loads(args.source_manifest.read_text(encoding="utf-8"))
    task_meta = {row["task_id"]: row for row in source_manifest["tasks"]}
    grouped = {}
    for row in result["results"]:
        if not row["task_id"].startswith("H"):
            continue
        grouped.setdefault(row["task_id"], []).append(row)
    experiences = []
    for task_id in sorted(grouped):
        attempts = grouped[task_id]
        complete = len(attempts) == 2 and all(
            row["status"] == "COMPLETE"
            and row["plan_request"]["status"] == "OK"
            and row["consume_request"]["status"] == "OK"
            and row["tool_result"]["status"] == "OK"
            and row["consume"]["status"] == "ANSWER"
            and row["feedback_category"] == "SUCCESS"
            for row in attempts
        )
        first = attempts[0]
        followup = attempts[1]
        stable = (
            first["plan"]["params"]["expression"] ==
            followup["plan"]["params"]["expression"]
            and abs(
                float(first["consume"]["delta_target"]) -
                float(followup["consume"]["delta_target"])
            ) <= 1e-9
            and first["consume"]["unit"] == followup["consume"]["unit"]
        )
        target_match = all(
            abs(
                float(row["tool_result"]["returned_value"]) -
                float(row["hidden_reference"]["delta_target"])
            ) <= 1e-9
            and abs(
                float(row["consume"]["delta_target"]) -
                float(row["hidden_reference"]["delta_target"])
            ) <= 1e-9
            and row["consume"]["unit"] == row["hidden_reference"]["target_unit"]
            for row in attempts
        )
        base_eligible = complete and target_match
        evidence_qualified = base_eligible and stable
        context = {
            "experience_id": task_id,
            "lesson": (
                "For a fixed table row and two periods, request the exact calculator "
                "operation late minus early, consume the actual returned value, and "
                "return that value with the stated unit."
            ),
            "actual_tool": "calc",
            "observed_operation_pattern": "late minus early",
            "actual_returned_values": [
                row["tool_result"]["returned_value"] for row in attempts
            ],
            "feedback_categories": [row["feedback_category"] for row in attempts],
            "applicability": "restricted table signed-difference task with explicit unit",
        }
        experiences.append({
            "experience_id": task_id,
            "source_cluster_id": task_meta[task_id]["hidden"]["source_cluster_id"],
            "chain_complete": complete,
            "stable_followup": stable,
            "target_match": target_match,
            "attempts": [
                {
                    "attempt": row["attempt"],
                    "plan": row["plan"],
                    "tool_result": row["tool_result"],
                    "consume": row["consume"],
                    "feedback_category": row["feedback_category"],
                    "hidden_reference": row["hidden_reference"],
                }
                for row in attempts
            ],
            "u_eligible": base_eligible,
            "e_eligible": evidence_qualified,
            "e_reasons": [
                "complete_real_chain",
                "actual_tool_trace",
                "independent_reference_agreement",
                "stable_followup",
                "target_aligned_restricted_table_calculation",
            ] if evidence_qualified else [],
            "context": context,
        })
    u_ids = [row["experience_id"] for row in experiences if row["u_eligible"]]
    e_ids = [row["experience_id"] for row in experiences if row["e_eligible"]]
    contexts = []
    for task in future["tasks"]:
        u_selected = sorted(u_ids, key=lambda eid: rank(task["task_id"], eid))[:2]
        e_selected = sorted(e_ids, key=lambda eid: rank(task["task_id"], eid))[:2]
        contexts.append({
            "task_id": task["task_id"],
            "u_experience_ids": u_selected,
            "e_experience_ids": e_selected,
            "u_e_identical": u_selected == e_selected,
        })
    identical = all(row["u_e_identical"] for row in contexts)
    pool = {
        "schema": "real_history_experience_pool_v1",
        "status": "QUALIFIED_HISTORY_POOL",
        "source_result": str(args.execution_result),
        "experience_count": len(experiences),
        "u_eligible_count": len(u_ids),
        "e_eligible_count": len(e_ids),
        "all_u_e_eligible": sorted(u_ids) == sorted(e_ids),
        "experiences": experiences,
    }
    export = {
        "schema": "experience_context_export_v1",
        "status": "BLOCKED_U_E_IDENTICAL" if identical else "READY_FOR_PILOT_CONTEXTS",
        "selection_seed": SEED,
        "future_task_count": len(contexts),
        "all_u_e_identical": identical,
        "contexts": contexts,
        "stop_rule_triggered": identical,
    }
    with args.pool_output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(pool, ensure_ascii=False, indent=2) + "\n")
    with args.context_output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(export, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "experience_count": len(experiences),
        "u_eligible": len(u_ids),
        "e_eligible": len(e_ids),
        "u_e_identical": identical,
        "pilot_status": export["status"],
    }, sort_keys=True))
    return 2 if identical else 0


if __name__ == "__main__":
    raise SystemExit(main())
