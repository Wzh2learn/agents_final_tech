#!/usr/bin/env python3
"""Generate the frozen Candidate B B0 protocol, bundle and authorization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
QUALIFICATION = PACKAGE.parent
EXECUTION = ROOT / "research/tatqa_wp0_2026/history_collection_execution_v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    tasks = json.loads((QUALIFICATION / "CANDIDATE_B_TASKS_DRAFT.json").read_text(encoding="utf-8"))
    hidden = json.loads((QUALIFICATION / "HIDDEN_REFERENCE_MANIFEST.json").read_text(encoding="utf-8"))
    development_ids = {
        row["task_id"]
        for row in hidden["references"]
        if row["partition"] == "development"
    }
    order = [row["task_id"] for row in tasks["tasks"] if row["task_id"] in development_ids]
    if len(order) != 16:
        raise RuntimeError(f"development_order_count_invalid:{len(order)}")
    slots = []
    for task_id in order:
        slots.append({"request_key": f"plan|B0|{task_id}", "task_id": task_id, "stage": "plan", "arm": "B0"})
        slots.append({"request_key": f"consume|B0|{task_id}", "task_id": task_id, "stage": "consume", "arm": "B0"})
    protocol = {
        "schema": "candidate_b_b0_protocol_v1",
        "status": "FROZEN_BEFORE_B0",
        "measurement_question": "Does the fixed model correctly bind row, periods, sign and unit before executing a signed-difference calculation on the Candidate B development panel?",
        "partition": "development",
        "task_order": order,
        "request_slots": slots,
        "budget": {
            "request_cap": 32,
            "token_cap": 600000,
            "retry_cap": 0,
            "concurrency": 1,
            "per_request_reserve_tokens": 10240,
        },
        "branch_gates": {
            "all_16_success": "CEILING_ON_THIS_PANEL",
            "fewer_than_2_nonsuccess_or_single_cluster": "LIMITED_HEADROOM",
            "at_least_2_clusters_with_nonsuccess": "CONTINUE_TO_ARM_DESIGN",
            "technical_or_window_failure": "TECHNICAL_OR_WINDOW_STOP",
        },
        "deadline": "2026-10-19T22:00:00+08:00",
    }
    write_json(PACKAGE / "CANDIDATE_B_B0_PROTOCOL.json", protocol)

    artifacts = {
        "candidate_b_b0_runner.py": digest(PACKAGE / "candidate_b_b0_runner.py"),
        "build_candidate_b_b0_config.py": digest(PACKAGE / "build_candidate_b_b0_config.py"),
        "CANDIDATE_B_B0_PROTOCOL.json": digest(PACKAGE / "CANDIDATE_B_B0_PROTOCOL.json"),
        "qualification/CANDIDATE_B_TASKS_DRAFT.json": digest(QUALIFICATION / "CANDIDATE_B_TASKS_DRAFT.json"),
        "qualification/HIDDEN_REFERENCE_MANIFEST.json": digest(QUALIFICATION / "HIDDEN_REFERENCE_MANIFEST.json"),
        "qualification/candidate_b_qualification_receipt.json": digest(QUALIFICATION / "candidate_b_qualification_receipt.json"),
        "execution/reuse_opportunity_v1/DIAGNOSTIC_PLAN_PROMPT.json": digest(EXECUTION / "reuse_opportunity_v1/DIAGNOSTIC_PLAN_PROMPT.json"),
        "execution/reuse_opportunity_v1/DIAGNOSTIC_CONSUME_PROMPT.json": digest(EXECUTION / "reuse_opportunity_v1/DIAGNOSTIC_CONSUME_PROMPT.json"),
        "execution/OUTPUT_SCHEMAS.json": digest(EXECUTION / "OUTPUT_SCHEMAS.json"),
        "execution/RUNTIME_IDENTITY_SNAPSHOT.json": digest(EXECUTION / "RUNTIME_IDENTITY_SNAPSHOT.json"),
        "execution/RUNTIME_POLICY.json": digest(EXECUTION / "RUNTIME_POLICY.json"),
    }
    bundle = {
        "schema": "candidate_b_b0_bundle_v1",
        "status": "FROZEN_BEFORE_B0",
        "artifact_hashes": artifacts,
        "task_count": 16,
        "planned_requests": 32,
        "authorization": "USER_AUTHORIZED_2026-10-19",
    }
    write_json(PACKAGE / "CANDIDATE_B_B0_BUNDLE.json", bundle)

    authorization = {
        "schema": "candidate_b_b0_authorization_v1",
        "authorization_id": "CANDIDATE-B-B0-20261019-0820-32REQ",
        "bundle_sha256": digest(PACKAGE / "CANDIDATE_B_B0_BUNDLE.json"),
        "runtime_identity_sha256": digest(EXECUTION / "RUNTIME_IDENTITY_SNAPSHOT.json"),
        "protocol_sha256": digest(PACKAGE / "CANDIDATE_B_B0_PROTOCOL.json"),
        "window_start_utc": "2026-10-19T08:20:00Z",
        "window_end_utc": "2026-10-19T13:30:00Z",
        "request_cap": 32,
        "token_cap": 600000,
        "retry_cap": 0,
        "concurrency": 1,
        "allow_model_requests": True,
        "owner_decision_reference": "User authorized Candidate B development B0 in current thread on 2026-10-19; 32 requests only.",
        "raw_root": "/home/testuser/wzh/candidate_b_runs/CANDIDATE-B-B0-20261019-0820-32REQ",
    }
    write_json(PACKAGE / "CANDIDATE_B_B0_AUTHORIZATION.json", authorization)


if __name__ == "__main__":
    main()
