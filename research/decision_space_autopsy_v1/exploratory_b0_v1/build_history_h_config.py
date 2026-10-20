#!/usr/bin/env python3
"""Freeze history-collection and H/control protocols for the role-binding study."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
PARENT = PACKAGE.parent
EXECUTION = ROOT / "research/tatqa_wp0_2026/history_collection_execution_v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    tasks_doc = json.loads((PARENT / "SAME_NUMBER_ROLE_TASKS_DRAFT.json").read_text(encoding="utf-8"))
    hidden = {row["task_id"]: row for row in tasks_doc["hidden_references"]}
    history_clusters = {"cluster_0402", "cluster_1582", "cluster_2174"}
    future_clusters = {"cluster_1604", "cluster_1792", "cluster_2442"}
    history_order = sorted(task_id for task_id, row in hidden.items() if row["source_cluster_id"] in history_clusters)
    future_order = sorted(task_id for task_id, row in hidden.items() if row["source_cluster_id"] in future_clusters)
    residual_order = sorted(task_id for task_id in future_order if hidden[task_id]["source_cluster_id"] != "cluster_2442")
    if len(history_order) != 6 or len(future_order) != 6 or len(residual_order) != 4:
        raise RuntimeError(f"partition_count_invalid:{len(history_order)}:{len(future_order)}:{len(residual_order)}")
    history_protocol = {
        "schema": "same_number_role_history_protocol_v1",
        "status": "FROZEN_BEFORE_COLLECTION",
        "task_order": history_order,
        "budget": {"request_cap": 24, "token_cap": 300000, "retry_cap": 0, "concurrency": 1, "per_request_reserve_tokens": 10240},
        "history_clusters": sorted(history_clusters),
        "feedback_rule": "attempt 1 receives actual plan/tool/consume classification; attempt 2 receives the same task plus actual first attempt and deterministic feedback",
    }
    write_json(PACKAGE / "SAME_NUMBER_ROLE_HISTORY_PROTOCOL.json", history_protocol)
    history_auth = {
        "schema": "same_number_role_history_authorization_v1",
        "authorization_id": "SAME-NUMBER-HISTORY-20261019-24REQ",
        "protocol_sha256": digest(PACKAGE / "SAME_NUMBER_ROLE_HISTORY_PROTOCOL.json"),
        "runtime_identity_sha256": digest(EXECUTION / "RUNTIME_IDENTITY_SNAPSHOT.json"),
        "window_start_utc": "2026-10-19T11:15:00Z",
        "window_end_utc": "2026-10-19T13:30:00Z",
        "request_cap": 24,
        "token_cap": 300000,
        "retry_cap": 0,
        "concurrency": 1,
        "allow_model_requests": True,
        "owner_decision_reference": "User authorized one task-matched history collection and H arm on 2026-10-19.",
        "raw_root": "/home/testuser/wzh/candidate_b_runs/SAME-NUMBER-HISTORY-20261019-24REQ",
    }
    write_json(PACKAGE / "SAME_NUMBER_ROLE_HISTORY_AUTHORIZATION.json", history_auth)
    contexts = {
        "R_RESIDUAL": {"guidance": "Before accepting a claim, compare the requested role tuple with the candidate citation row and periods. Numeric agreement is insufficient. If the roles differ, return WRONG_ROLE and include the executed numeric value and unit."},
        "C_RESIDUAL": {"guidance": "Financial tables often repeat identical values across rows, periods, entities and accounting roles. Evidence relevance depends on the requested role and source context, not numeric equality alone."},
        "H": {"experiences": "FROZEN_AFTER_HISTORY_COLLECTION_FROM_SAME_NUMBER_ROLE_HISTORY_PROTOCOL"},
    }
    for arm, order, request_cap in (("R_RESIDUAL", residual_order, 8), ("C_RESIDUAL", residual_order, 8), ("H", future_order, 12)):
        protocol = {
            "schema": "same_number_role_arm_protocol_v1",
            "status": "FROZEN_BEFORE_ARM",
            "arm": arm,
            "task_order": order,
            "context": contexts[arm],
            "budget": {"request_cap": request_cap, "token_cap": 300000, "retry_cap": 0, "concurrency": 1, "per_request_reserve_tokens": 10240},
            "deadline": "2026-10-19T22:00:00+08:00",
        }
        protocol_path = PACKAGE / f"SAME_NUMBER_ROLE_{arm}_PROTOCOL.json"
        write_json(protocol_path, protocol)
        auth = {
            "schema": "same_number_role_arm_authorization_v1",
            "authorization_id": f"SAME-NUMBER-{arm}-20261019",
            "protocol_sha256": digest(protocol_path),
            "runtime_identity_sha256": digest(EXECUTION / "RUNTIME_IDENTITY_SNAPSHOT.json"),
            "window_start_utc": "2026-10-19T11:15:00Z",
            "window_end_utc": "2026-10-19T13:30:00Z",
            "request_cap": request_cap,
            "token_cap": 300000,
            "retry_cap": 0,
            "concurrency": 1,
            "allow_model_requests": True,
            "owner_decision_reference": "User authorized one task-matched history collection and H arm; R/C residual controls complete the frozen comparison.",
            "raw_root": f"/home/testuser/wzh/candidate_b_runs/SAME-NUMBER-{arm}-20261019",
        }
        write_json(PACKAGE / f"SAME_NUMBER_ROLE_{arm}_AUTHORIZATION.json", auth)
    write_json(PACKAGE / "H_SELECTION_RULE.json", {
        "schema": "same_number_role_h_selection_rule_v1",
        "status": "FROZEN_BEFORE_HISTORY_COLLECTION",
        "rule": "Select two history trajectories from the six task-matched histories with the same case_type and expected_decision pattern as the evaluation task where available; otherwise use the first two corrected successful trajectories ordered by task_id. Never inspect H evaluation outputs.",
        "history_task_ids": history_order,
        "evaluation_task_ids": future_order,
    })


if __name__ == "__main__":
    main()
