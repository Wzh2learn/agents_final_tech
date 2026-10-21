#!/usr/bin/env python3
"""Freeze the bounded role-history collection protocol and authorization."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
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
    parser.add_argument("--qualified-package", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--window-start-utc", required=True)
    parser.add_argument("--window-end-utc", required=True)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    qualified_path = args.qualified_package.resolve()
    qualified = load_object(qualified_path)
    references = {row["task_id"]: row for row in qualified["hidden_references"]}
    tasks = {row["task_id"]: row for row in qualified["tasks"]}
    excluded_history_clusters = {"cluster_0402", "cluster_1582", "cluster_2174"}

    selected = []
    for task_id, reference in references.items():
        if not task_id.startswith("NR_development_"):
            continue
        if reference["source_cluster_id"] in excluded_history_clusters:
            continue
        if reference["expected_decision"] == "WRONG_ROLE":
            qualification = reference.get("qualification", {})
            if qualification.get("status") != "QUALIFIED_VISIBLE_ROLE_DIFFERENCE":
                raise RuntimeError(f"negative_task_not_visible_qualified:{task_id}")
        selected.append((reference["source_cluster_id"], task_id))

    selected.sort()
    cluster_ids = sorted({cluster_id for cluster_id, _ in selected})
    if len(selected) != 12 or len(cluster_ids) != 6:
        raise RuntimeError(f"selection_count_invalid:{len(selected)}:{len(cluster_ids)}")
    for cluster_id in cluster_ids:
        pair = [task_id for selected_cluster, task_id in selected if selected_cluster == cluster_id]
        if len(pair) != 2 or not any(task_id.endswith("_P1") for task_id in pair) or not any(
            task_id.endswith("_N2") for task_id in pair
        ):
            raise RuntimeError(f"matched_pair_invalid:{cluster_id}")

    task_order = [task_id for _, task_id in selected]
    protocol_path = output_dir / "ROLE_HISTORY_COLLECTION_PROTOCOL_V1.json"
    protocol = {
        "schema": "same_number_role_history_protocol_v1",
        "status": "FROZEN_BEFORE_FIRST_REQUEST",
        "selection_rule": (
            "Six development clusters not used by the earlier same-number history "
            "collection; two visible-reference-valid tasks per cluster; fixed lexical order."
        ),
        "source_cluster_ids": cluster_ids,
        "task_order": task_order,
        "budget": {
            "request_cap": 24,
            "token_cap": 250000,
            "retry_cap": 0,
            "concurrency": 1,
            "attempts_per_task": 2,
        },
        "window_start_utc": args.window_start_utc,
        "window_end_utc": args.window_end_utc,
        "scientific_gate": (
            "At least two wrong-role first decisions with successful plan/tool traces, "
            "role-specific deterministic feedback and changed real follow-up actions "
            "across at least two source clusters."
        ),
    }
    write_json(protocol_path, protocol)

    authorization_path = output_dir / "ROLE_HISTORY_COLLECTION_AUTHORIZATION_V1.json"
    authorization = {
        "schema": "same_number_role_history_authorization_v1",
        "authorization_id": "ROLE-HISTORY-V1-20261019-24REQ",
        "protocol_sha256": digest(protocol_path),
        "runtime_identity_sha256": digest(EXECUTION / "RUNTIME_IDENTITY_SNAPSHOT.json"),
        "window_start_utc": args.window_start_utc,
        "window_end_utc": args.window_end_utc,
        "request_cap": 24,
        "token_cap": 250000,
        "retry_cap": 0,
        "concurrency": 1,
        "allow_model_requests": True,
        "owner_decision_reference": (
            "User authorized execution now after the draft collection gate; "
            "bounded to 24 new requests under the raised cumulative cap."
        ),
        "raw_root": str((output_dir / "raw" / "ROLE-HISTORY-V1-20261019").resolve()),
    }
    write_json(authorization_path, authorization)

    bundle_path = output_dir / "ROLE_HISTORY_COLLECTION_BUNDLE_V1.json"
    bundle = {
        "schema": "role_history_collection_bundle_v1",
        "status": "FROZEN_BEFORE_FIRST_REQUEST",
        "qualified_package_sha256": digest(qualified_path),
        "runtime_identity_sha256": digest(EXECUTION / "RUNTIME_IDENTITY_SNAPSHOT.json"),
        "runner_sha256": digest(PACKAGE / "same_number_role_history_runner.py"),
        "protocol_sha256": digest(protocol_path),
        "authorization_sha256": digest(authorization_path),
        "budget_expansion_sha256": digest(PACKAGE / "EXPLORATORY_BUDGET_EXPANSION_V1.json"),
        "cumulative_before": {
            "requests_used": 292,
            "accounting_tokens_used": 310144,
        },
        "cumulative_cap": {
            "requests": 316,
            "accounting_tokens": 2750000,
        },
        "planned_requests": 24,
    }
    write_json(bundle_path, bundle)
    print(
        json.dumps(
            {
                "tasks": len(task_order),
                "clusters": cluster_ids,
                "planned_requests": 24,
                "protocol_sha256": bundle["protocol_sha256"],
                "authorization_sha256": bundle["authorization_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
