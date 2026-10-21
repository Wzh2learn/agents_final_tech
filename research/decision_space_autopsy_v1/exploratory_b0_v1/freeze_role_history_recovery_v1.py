#!/usr/bin/env python3
"""Freeze a no-replay recovery after one connection-refused request attempt."""

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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-protocol", required=True, type=Path)
    parser.add_argument("--source-authorization", required=True, type=Path)
    parser.add_argument("--qualified-package", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--window-start-utc", required=True)
    parser.add_argument("--window-end-utc", required=True)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()

    source_protocol = load_object(args.source_protocol.resolve())
    source_authorization = load_object(args.source_authorization.resolve())
    qualified = load_object(args.qualified_package.resolve())
    references = {row["task_id"]: row for row in qualified["hidden_references"]}

    crashed_cluster = "cluster_0424"
    recovery_order = [
        task_id
        for task_id in source_protocol["task_order"]
        if references[task_id]["source_cluster_id"] != crashed_cluster
    ]
    recovery_clusters = sorted({references[task_id]["source_cluster_id"] for task_id in recovery_order})
    if len(recovery_order) != 10 or len(recovery_clusters) != 5:
        raise RuntimeError(f"recovery_selection_invalid:{len(recovery_order)}:{len(recovery_clusters)}")

    protocol_path = output_dir / "ROLE_HISTORY_RECOVERY_PROTOCOL_V1.json"
    protocol = {
        "schema": "same_number_role_history_protocol_v1",
        "status": "FROZEN_BEFORE_RECOVERY_REQUESTS",
        "recovery_of": {
            "authorization_id": source_authorization["authorization_id"],
            "protocol_sha256": digest(args.source_protocol.resolve()),
            "crashed_logical_id": "plan|HCOLLECT|NR_development_0424_N2|a1",
            "excluded_cluster": crashed_cluster,
            "reason": "CONNECTION_REFUSED_BEFORE_MODEL_RESPONSE",
        },
        "selection_rule": (
            "Remove the complete source cluster containing the crashed request; "
            "retain the other five preselected matched pairs in frozen order. "
            "Do not replay the crashed logical request."
        ),
        "source_cluster_ids": recovery_clusters,
        "task_order": recovery_order,
        "budget": {
            "request_cap": 20,
            "token_cap": 220000,
            "retry_cap": 0,
            "concurrency": 1,
            "attempts_per_task": 2,
        },
        "window_start_utc": args.window_start_utc,
        "window_end_utc": args.window_end_utc,
    }
    write_json(protocol_path, protocol)

    authorization_path = output_dir / "ROLE_HISTORY_RECOVERY_AUTHORIZATION_V1.json"
    authorization = {
        "schema": "same_number_role_history_authorization_v1",
        "authorization_id": "ROLE-HISTORY-RECOVERY-V1-20261019-20REQ",
        "protocol_sha256": digest(protocol_path),
        "runtime_identity_sha256": digest(EXECUTION / "RUNTIME_IDENTITY_SNAPSHOT.json"),
        "window_start_utc": args.window_start_utc,
        "window_end_utc": args.window_end_utc,
        "request_cap": 20,
        "token_cap": 220000,
        "retry_cap": 0,
        "concurrency": 1,
        "allow_model_requests": True,
        "owner_decision_reference": (
            "User authorized execution now. This recovery preserves the crashed "
            "request record, excludes its complete source pair and does not replay it."
        ),
        "raw_root": source_authorization["raw_root"],
    }
    write_json(authorization_path, authorization)

    bundle_path = output_dir / "ROLE_HISTORY_RECOVERY_BUNDLE_V1.json"
    bundle = {
        "schema": "role_history_recovery_bundle_v1",
        "status": "FROZEN_BEFORE_RECOVERY_REQUESTS",
        "source_protocol_sha256": digest(args.source_protocol.resolve()),
        "source_authorization_sha256": digest(args.source_authorization.resolve()),
        "recovery_protocol_sha256": digest(protocol_path),
        "recovery_authorization_sha256": digest(authorization_path),
        "recovery_runner_sha256": digest(PACKAGE / "same_number_role_history_recovery_runner.py"),
        "runtime_identity_sha256": digest(EXECUTION / "RUNTIME_IDENTITY_SNAPSHOT.json"),
        "qualified_package_sha256": digest(args.qualified_package.resolve()),
        "raw_root": source_authorization["raw_root"],
        "accounting": {
            "before_recovery_requests_used": 293,
            "before_recovery_actual_tokens": 310144,
            "crashed_attempt_requests": 1,
            "crashed_attempt_actual_tokens": 0,
            "recovery_planned_requests": 20,
            "cumulative_request_cap": 316,
            "cumulative_token_cap": 2750000,
        },
    }
    write_json(bundle_path, bundle)
    print(
        json.dumps(
            {
                "tasks": len(recovery_order),
                "clusters": recovery_clusters,
                "planned_requests": 20,
                "crashed_replayed": False,
                "protocol_sha256": bundle["recovery_protocol_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
