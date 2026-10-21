#!/usr/bin/env python3
"""Freeze failure-only matched and mismatched contexts without index-only cases."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


PACKAGE = Path(__file__).resolve().parent
PARENT = PACKAGE.parent
EXECUTION = PARENT.parent / "tatqa_wp0_2026/history_collection_execution_v1"


def load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"object_required:{path}")
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def visible_role(role: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        str(role.get(key, ""))
        for key in ("row_label", "period", "period_label", "early_period", "late_period", "unit", "scale")
    )


def visible_roles_match(task: dict[str, Any]) -> bool:
    return visible_role(task["requested_role"]) == visible_role(task["candidate_citation"])


def determinable_wrong_role(task: dict[str, Any]) -> bool:
    return not visible_roles_match(task)


def failure_signature(task: dict[str, Any], experience: dict[str, Any]) -> dict[str, Any]:
    first = experience["attempts"][0]
    return {
        "task": task,
        "failed_attempt": {
            "plan": first["plan"],
            "tool_result": first["tool_result"],
            "consume": first["consume"],
        },
        "feedback": experience["feedback"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history-result", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--window-start-utc", required=True)
    parser.add_argument("--window-end-utc", required=True)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    tasks_doc = load_object(PARENT / "SAME_NUMBER_ROLE_TASKS_DRAFT.json")
    history = load_object(args.history_result)
    tasks = {row["task_id"]: row for row in tasks_doc["tasks"]}
    references = {row["task_id"]: row for row in tasks_doc["hidden_references"]}

    failed_histories = []
    excluded = []
    for experience in history["experiences"]:
        task = tasks[experience["task_id"]]
        reference = references[experience["task_id"]]
        if experience["attempts"][0]["outcome"] == "SUCCESS":
            continue
        if reference["expected_decision"] == "WRONG_ROLE" and not determinable_wrong_role(task):
            excluded.append(
                {
                    "task_id": experience["task_id"],
                    "reason": "UNSCORABLE_FOR_REFERENCE_VISIBLE_ROLE_IDENTICAL",
                }
            )
            continue
        failed_histories.append(
            {
                "task_id": experience["task_id"],
                "role_match": bool(reference["role_match"]),
                "case_type": reference["case_type"],
                "signature": failure_signature(task, experience),
            }
        )

    by_state = {
        state: sorted(
            [row for row in failed_histories if row["role_match"] == state],
            key=lambda row: row["task_id"],
        )
        for state in (True, False)
    }
    if not by_state[True] or not by_state[False]:
        raise RuntimeError(
            f"failed_history_state_shortfall:match={len(by_state[True])}:mismatch={len(by_state[False])}"
        )

    hneg = {}
    random = {}
    for task_id in load_object(PACKAGE / "SAME_NUMBER_ROLE_H_PROTOCOL.json")["task_order"]:
        state = bool(references[task_id]["role_match"])
        matched = by_state[state][0]
        mismatched = by_state[not state][0]
        hneg[task_id] = {
            "failure_signatures": [matched["signature"]],
            "selection_reason": (
                "one visible-role-state-matched failed history; first failed attempt and "
                "deterministic feedback only; final solution withheld"
            ),
        }
        random[task_id] = {
            "failure_signatures": [mismatched["signature"]],
            "selection_reason": (
                "one visible-role-state-mismatched failed history; length and schema matched "
                "to H-negative; final solution withheld"
            ),
        }

    hneg_path = output_dir / "H_NEG_CONTEXTS_V2.json"
    random_path = output_dir / "RANDOM_FAILURE_CONTEXTS_V2.json"
    write_json(
        hneg_path,
        {
            "schema": "same_number_role_hneg_contexts_v2",
            "status": "FROZEN_BEFORE_RUN",
            "excluded_history": excluded,
            "eligible_failed_history_count": len(failed_histories),
            "contexts": hneg,
        },
    )
    write_json(
        random_path,
        {
            "schema": "same_number_role_random_contexts_v2",
            "status": "FROZEN_BEFORE_RUN",
            "excluded_history": excluded,
            "eligible_failed_history_count": len(failed_histories),
            "contexts": random,
        },
    )

    for arm, context_path, raw_name in (
        ("H_NEG", hneg_path, "SAME-NUMBER-H-NEG-V2-20261019"),
        ("RANDOM", random_path, "SAME-NUMBER-RANDOM-V2-20261019"),
    ):
        contexts = load_object(context_path)["contexts"]
        protocol = {
            "schema": "same_number_role_arm_protocol_v1",
            "status": "FROZEN_BEFORE_RUN",
            "arm": arm,
            "task_order": list(contexts),
            "context_by_task": contexts,
            "budget": {
                "request_cap": 12,
                "token_cap": 150000,
                "retry_cap": 0,
                "concurrency": 1,
                "per_request_reserve_tokens": 10240,
            },
            "deadline": "2026-10-19T22:00:00+08:00",
            "scientific_scope": (
                "EXPLORATORY_POST_HOC_FAILURE_SOURCE_COMPARISON; not independent confirmation"
            ),
        }
        protocol_path = output_dir / f"SAME_NUMBER_ROLE_{arm}_PROTOCOL_V2.json"
        write_json(protocol_path, protocol)
        authorization = {
            "schema": "same_number_role_arm_authorization_v1",
            "authorization_id": f"SAME-NUMBER-{arm}-V2-20261019-12REQ",
            "protocol_sha256": digest(protocol_path),
            "runtime_identity_sha256": digest(EXECUTION / "RUNTIME_IDENTITY_SNAPSHOT.json"),
            "window_start_utc": args.window_start_utc,
            "window_end_utc": args.window_end_utc,
            "request_cap": 12,
            "token_cap": 150000,
            "retry_cap": 0,
            "concurrency": 1,
            "allow_model_requests": True,
            "owner_decision_reference": (
                "User raised budget and authorized continued exploratory research; "
                "bounded to the final failure-source comparison before the fixed deadline."
            ),
            "raw_root": str((output_dir / "raw" / raw_name).resolve()),
        }
        write_json(output_dir / f"SAME_NUMBER_ROLE_{arm}_AUTHORIZATION_V2.json", authorization)

    budget = {
        "schema": "exploratory_budget_expansion_v1",
        "status": "AUTHORIZED_BY_USER_BUDGET_INCREASE",
        "owner_instruction": "提高预算，继续探索",
        "baseline_cumulative": {
            "requests_used": 292,
            "request_cap": 292,
            "accounting_tokens_used": 310144,
            "token_cap": 2450000,
        },
        "increase": {
            "requests": 24,
            "accounting_tokens_reserved": 300000,
        },
        "new_cumulative_cap": {
            "requests": 316,
            "accounting_tokens": 2750000,
        },
        "planned_use": {
            "H_NEG": 12,
            "RANDOM": 12,
            "fixtures_or_retries": 0,
        },
        "scientific_scope": (
            "One exploratory H-negative versus random-failure comparison. "
            "No independent validation, training, judge or production-memory write."
        ),
    }
    write_json(output_dir / "EXPLORATORY_BUDGET_EXPANSION_V1.json", budget)
    print(
        json.dumps(
            {
                "eligible_failed_histories": len(failed_histories),
                "excluded_history": excluded,
                "match_candidates": len(by_state[True]),
                "mismatch_candidates": len(by_state[False]),
                "planned_requests": 24,
                "new_request_cap": 316,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
