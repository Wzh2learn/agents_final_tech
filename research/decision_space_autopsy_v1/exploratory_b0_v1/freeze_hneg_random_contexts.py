#!/usr/bin/env python3
"""Freeze failure-only H and irrelevant failure controls."""

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


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def role_state(task):
    return {
        "case_type": "same_number" if task["claim"]["kind"] == "cell_value" else "same_delta",
        "role_match": task["requested_role"] == task["candidate_citation"],
    }


def failure_signature(task, experience):
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
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    tasks_doc = load_object(PARENT / "SAME_NUMBER_ROLE_TASKS_DRAFT.json")
    history = load_object(args.history_result)
    tasks = {row["task_id"]: row for row in tasks_doc["tasks"]}
    histories = []
    for experience in history["experiences"]:
        task = tasks[experience["task_id"]]
        if experience["attempts"][0]["outcome"] == "SUCCESS":
            continue
        histories.append((experience["task_id"], role_state(task), failure_signature(task, experience)))
    if len(histories) < 4:
        raise RuntimeError(f"failed_history_shortfall:{len(histories)}")

    hneg = {}
    random = {}
    for task_id in load_object(PACKAGE / "SAME_NUMBER_ROLE_H_PROTOCOL.json")["task_order"]:
        state = role_state(tasks[task_id])
        matching = sorted(
            [row for row in histories if row[1] == state],
            key=lambda row: row[0],
        )
        nonmatching = sorted(
            [row for row in histories if row[1] != state],
            key=lambda row: row[0],
        )
        if len(matching) < 2:
            raise RuntimeError(f"hneg_candidates_insufficient:{task_id}")
        if len(nonmatching) < 2:
            raise RuntimeError(f"random_candidates_insufficient:{task_id}")
        hneg[task_id] = {
            "failure_signatures": [row[2] for row in matching[:2]],
            "selection_reason": "same visible case type and role-match state; first failed attempt plus feedback only; no final solution",
        }
        random[task_id] = {
            "failure_signatures": [row[2] for row in nonmatching[:2]],
            "selection_reason": "same length failure-only context but mismatched visible case type or role-match state",
        }
    write_json(output_dir / "H_NEG_CONTEXTS.json", {"schema": "same_number_role_hneg_contexts_v1", "status": "FROZEN_BEFORE_RUN", "contexts": hneg})
    write_json(output_dir / "RANDOM_FAILURE_CONTEXTS.json", {"schema": "same_number_role_random_contexts_v1", "status": "FROZEN_BEFORE_RUN", "contexts": random})
    for arm, contexts, raw_name in (("H_NEG", hneg, "SAME-NUMBER-H-NEG-20261019"), ("RANDOM", random, "SAME-NUMBER-RANDOM-20261019")):
        protocol = {
            "schema": "same_number_role_arm_protocol_v1",
            "status": "FROZEN_BEFORE_ARM",
            "arm": arm,
            "task_order": list(contexts),
            "context_by_task": contexts,
            "budget": {"request_cap": 12, "token_cap": 300000, "retry_cap": 0, "concurrency": 1, "per_request_reserve_tokens": 10240},
            "deadline": "2026-10-19T22:00:00+08:00",
        }
        protocol_path = output_dir / f"SAME_NUMBER_ROLE_{arm}_PROTOCOL.json"
        write_json(protocol_path, protocol)
        auth = {
            "schema": "same_number_role_arm_authorization_v1",
            "authorization_id": f"SAME-NUMBER-{arm}-20261019-12REQ",
            "protocol_sha256": digest(protocol_path),
            "runtime_identity_sha256": digest(EXECUTION / "RUNTIME_IDENTITY_SNAPSHOT.json"),
            "window_start_utc": "2026-10-19T13:35:00Z",
            "window_end_utc": "2026-10-19T14:00:00Z",
            "request_cap": 12,
            "token_cap": 300000,
            "retry_cap": 0,
            "concurrency": 1,
            "allow_model_requests": True,
            "owner_decision_reference": "User raised budget and authorized continued exploration on 2026-10-19; this is the final bounded H-negative/random control before 22:00 Beijing.",
            "raw_root": f"/home/testuser/wzh/candidate_b_runs/{raw_name}",
        }
        write_json(output_dir / f"SAME_NUMBER_ROLE_{arm}_AUTHORIZATION.json", auth)
    print(json.dumps({"failed_histories": len(histories), "tasks_per_arm": 6, "planned_requests": 24}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
