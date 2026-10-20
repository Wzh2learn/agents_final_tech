#!/usr/bin/env python3
"""Select and freeze H contexts from task-matched history trajectories."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


PACKAGE = Path(__file__).resolve().parent
PARENT = PACKAGE.parent


def load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"object_required:{path}")
    return payload


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def visible_role_match(task: dict[str, Any]) -> bool:
    return task["requested_role"] == task["candidate_citation"]


def context_item(task: dict[str, Any], experience: dict[str, Any]) -> dict[str, Any]:
    attempts = []
    for attempt in experience["attempts"]:
        attempts.append(
            {
                "attempt": attempt["attempt"],
                "plan": attempt["plan"],
                "tool_result": attempt["tool_result"],
                "consume": attempt["consume"],
            }
        )
    return {
        "task": task,
        "attempts": attempts,
        "feedback": experience["feedback"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history-result", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--authorization", required=True, type=Path)
    args = parser.parse_args()

    history = load_object(args.history_result)
    tasks_doc = load_object(PARENT / "SAME_NUMBER_ROLE_TASKS_DRAFT.json")
    tasks = {row["task_id"]: row for row in tasks_doc["tasks"]}
    experiences = history["experiences"]
    contexts = {}
    for task_id in load_object(args.protocol)["task_order"]:
        task = tasks[task_id]
        target_match = visible_role_match(task)
        target_case = "same_number" if task["claim"]["kind"] == "cell_value" else "same_delta"
        candidates = []
        for experience in experiences:
            history_task = tasks[experience["task_id"]]
            history_match = visible_role_match(history_task)
            history_case = "same_number" if history_task["claim"]["kind"] == "cell_value" else "same_delta"
            if history_case == target_case and history_match == target_match:
                corrected = experience["attempts"][1]["outcome"] == "SUCCESS"
                candidates.append((0 if corrected else 1, experience["task_id"], experience))
        candidates.sort(key=lambda row: (row[0], row[1]))
        if len(candidates) < 2:
            raise RuntimeError(f"h_context_candidates_insufficient:{task_id}")
        contexts[task_id] = {
            "experiences": [context_item(tasks[row[1]], row[2]) for row in candidates[:2]],
            "selection_reason": {
                "case_type": target_case,
                "visible_role_match": target_match,
                "rule": "same case type and visible role-match state; corrected successful histories first; task_id order; no future outputs",
            },
        }
    write_json(PACKAGE / "H_CONTEXTS.json", {"schema": "same_number_role_h_contexts_v1", "status": "FROZEN_BEFORE_H", "contexts": contexts})
    protocol = load_object(args.protocol)
    protocol["context_by_task"] = contexts
    protocol["status"] = "FROZEN_BEFORE_H_WITH_CONTEXTS"
    write_json(args.protocol, protocol)
    authorization = load_object(args.authorization)
    authorization["protocol_sha256"] = digest(args.protocol)
    write_json(args.authorization, authorization)
    print(json.dumps({"tasks": len(contexts), "history_experiences": len(experiences), "protocol_sha256": authorization["protocol_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
