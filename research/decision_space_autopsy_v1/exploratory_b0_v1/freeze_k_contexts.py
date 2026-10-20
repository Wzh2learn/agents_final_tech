#!/usr/bin/env python3
"""Create ordinary solved-example K contexts from frozen H contexts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


PACKAGE = Path(__file__).resolve().parent


def load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"object_required:{path}")
    return payload


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--h-contexts", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    h_contexts = load_object(args.h_contexts)
    contexts = {}
    for task_id, entry in h_contexts["contexts"].items():
        examples = []
        for experience in entry["experiences"]:
            attempts = experience["attempts"]
            final_attempt = attempts[-1]
            examples.append(
                {
                    "task": experience["task"],
                    "solution": {
                        "plan": final_attempt["plan"],
                        "tool_result": final_attempt["tool_result"],
                        "consume": final_attempt["consume"],
                    },
                }
            )
        contexts[task_id] = {
            "solved_examples": examples,
            "selection_reason": "same two source examples as H, with history/feedback/correction metadata removed",
        }
    write_json(output_dir / "K_CONTEXTS.json", {"schema": "same_number_role_k_contexts_v1", "status": "FROZEN_BEFORE_K", "contexts": contexts})
    protocol = {
        "schema": "same_number_role_arm_protocol_v1",
        "status": "FROZEN_BEFORE_ARM",
        "arm": "K",
        "task_order": list(contexts),
        "context_by_task": contexts,
        "budget": {"request_cap": 12, "token_cap": 300000, "retry_cap": 0, "concurrency": 1, "per_request_reserve_tokens": 10240},
        "deadline": "2026-10-19T22:00:00+08:00",
    }
    protocol_path = output_dir / "SAME_NUMBER_ROLE_K_PROTOCOL.json"
    write_json(protocol_path, protocol)
    auth = {
        "schema": "same_number_role_arm_authorization_v1",
        "authorization_id": "SAME-NUMBER-K-20261019-12REQ",
        "protocol_sha256": digest(protocol_path),
        "runtime_identity_sha256": digest(PACKAGE.parent.parent / "tatqa_wp0_2026/history_collection_execution_v1/RUNTIME_IDENTITY_SNAPSHOT.json"),
        "window_start_utc": "2026-10-19T12:35:00Z",
        "window_end_utc": "2026-10-19T13:30:00Z",
        "request_cap": 12,
        "token_cap": 300000,
        "retry_cap": 0,
        "concurrency": 1,
        "allow_model_requests": True,
        "owner_decision_reference": "User authorized task-matched history collection and H; K is the required ordinary solved-example control for interpreting H.",
        "raw_root": "/home/testuser/wzh/candidate_b_runs/SAME-NUMBER-K-20261019",
    }
    write_json(output_dir / "SAME_NUMBER_ROLE_K_AUTHORIZATION.json", auth)
    print(json.dumps({"tasks": len(contexts), "planned_requests": 12, "protocol_sha256": auth["protocol_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
