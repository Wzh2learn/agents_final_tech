#!/usr/bin/env python3
"""Materialize deterministic task/reference and execution-plan manifests."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from execution_core import (
    TASK_SELECT_SEED,
    actor_task,
    independent_reference,
    selection_rank,
    sha256_file,
    source_uid,
    synthetic_fixture_tasks,
    validate_candidate_item,
    write_json_lf,
)


BUCKET_COUNTS = {"history": 1, "future_test": 2, "development": 2}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_cluster_index(split: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for bucket in ("future_test", "development", "history"):
        for row in split[bucket]:
            for uid in row["members"]:
                if uid in index:
                    raise ValueError(f"uid appears in multiple split buckets: {uid}")
                index[uid] = {"bucket": bucket, "cluster_id": row["cluster_id"]}
    return index


def build_manifest(
    candidate_path: Path,
    split_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    candidates = read_json(candidate_path)
    split = read_json(split_path)
    if candidates.get("schema") != "wp2_tatqa_candidate_items_v2":
        raise ValueError("candidate schema mismatch")
    if split.get("schema") != "history_collection_split_proposal_v1":
        raise ValueError("split schema mismatch")
    cluster_index = build_cluster_index(split)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    rejected: list[dict[str, Any]] = []
    for item in candidates["items"]:
        uid = source_uid(item)
        placement = cluster_index.get(uid)
        if placement is None:
            continue
        check = validate_candidate_item(item)
        if not check["valid"]:
            rejected.append({
                "item_id": item.get("item_id"),
                "source_uid": uid,
                "reason": check["reason"],
            })
            continue
        unit = check["unit"]
        reference = independent_reference(item, unit)
        if reference["status"] != "REFERENCE_RECOMPUTED":
            rejected.append({
                "item_id": item.get("item_id"),
                "source_uid": uid,
                "reason": reference["status"],
            })
            continue
        grouped[(placement["bucket"], placement["cluster_id"])].append({
            "item": item,
            "unit": unit,
            "reference": reference,
            "source_uid": uid,
            "placement": placement,
        })

    selected: list[dict[str, Any]] = []
    selection_audit: list[dict[str, Any]] = []
    for bucket in ("history", "future_test", "development"):
        cluster_rows = split[bucket]
        want = BUCKET_COUNTS[bucket]
        for cluster_row in cluster_rows:
            cluster_id = cluster_row["cluster_id"]
            candidates_for_cluster = grouped.get((bucket, cluster_id), [])
            candidates_for_cluster.sort(
                key=lambda row: selection_rank(
                    bucket, cluster_id, row["item"]["item_id"]
                )
            )
            if len(candidates_for_cluster) < want:
                raise ValueError(
                    f"insufficient qualified tasks for {bucket}/{cluster_id}: "
                    f"{len(candidates_for_cluster)} < {want}"
                )
            chosen = candidates_for_cluster[:want]
            selection_audit.append({
                "bucket": bucket,
                "cluster_id": cluster_id,
                "qualified_candidates": len(candidates_for_cluster),
                "selected_item_ids": [row["item"]["item_id"] for row in chosen],
            })
            for item_index, row in enumerate(chosen, start=1):
                item = row["item"]
                task_id = {
                    "history": "H",
                    "future_test": "F",
                    "development": "D",
                }[bucket] + f"{len([x for x in selected if x['bucket'] == bucket]) + 1:02d}"
                unit = row["unit"]
                reference = dict(row["reference"])
                reference["candidate_gold_value"] = item["gold_delta_source_unit"]
                selected.append({
                    "task_id": task_id,
                    "bucket": bucket,
                    "actor_task": actor_task(item, task_id, unit),
                    "hidden": {
                        "source_item_id": item["item_id"],
                        "source_uid": row["source_uid"],
                        "source_cluster_id": cluster_id,
                        "selection_rank": selection_rank(
                            bucket, cluster_id, item["item_id"]
                        ),
                        "selection_position": item_index,
                        "row_index": item["row_index"],
                        "period_early": item["period_early"],
                        "period_late": item["period_late"],
                        "reference": reference,
                    },
                    "qualification": {
                        "contract": "two-period signed difference with explicit unit",
                        "reference_checker": "execution_core.independent_reference",
                        "candidate_gold_agreement": reference["candidate_gold_agreement"],
                        "actor_visibility": "actor_task_only",
                        "future_content_excluded_from_experience_design": True,
                    },
                })

    expected = {"history": 12, "future_test": 16, "development": 4}
    actual = {
        bucket: sum(1 for row in selected if row["bucket"] == bucket)
        for bucket in expected
    }
    if actual != expected:
        raise ValueError(f"selected task counts mismatch: {actual} != {expected}")
    if len({row["task_id"] for row in selected}) != len(selected):
        raise ValueError("task_id collision")
    fixture_rows = synthetic_fixture_tasks()
    manifest = {
        "schema": "task_reference_manifest_v1",
        "status": "QUALIFIED_FOR_EXECUTION_READINESS",
        "task_select_seed": TASK_SELECT_SEED,
        "selection_rule": (
            "filter contract/reference validity, then sha256(seed:bucket:cluster_id:item_id) ascending"
        ),
        "source_identity": {
            "candidate_items_sha256": sha256_file(candidate_path),
            "split_proposal_sha256": sha256_file(split_path),
        },
        "counts": {
            "history": actual["history"],
            "future_test": actual["future_test"],
            "development": actual["development"],
            "qualification_fixtures": len(fixture_rows),
        },
        "selection_audit": selection_audit,
        "rejected_candidates": rejected,
        "tasks": selected,
        "qualification_fixtures": fixture_rows,
        "boundaries": {
            "gold_not_used_for_selection_order": True,
            "reference_is_contract_scoped_not_human_semantic_gold": True,
            "future_reference_hidden_from_actor": True,
            "designated_wp2_clusters_remain_isolated": True,
        },
    }
    slots: list[dict[str, Any]] = []
    for row in selected:
        if row["bucket"] != "history":
            continue
        for attempt in (1, 2):
            role = "initial" if attempt == 1 else "feedback_followup"
            for stage in ("plan", "consume"):
                slots.append({
                    "request_key": f"{stage}|{row['task_id']}|a{attempt}",
                    "task_id": row["task_id"],
                    "bucket": row["bucket"],
                    "attempt": attempt,
                    "attempt_role": role,
                    "stage": stage,
                    "fixture": False,
                })
    for row in fixture_rows:
        for stage in ("plan", "consume"):
            slots.append({
                "request_key": f"{stage}|{row['task_id']}|a1",
                "task_id": row["task_id"],
                "bucket": row["bucket"],
                "attempt": 1,
                "attempt_role": "qualification_fixture",
                "stage": stage,
                "fixture": True,
            })
    if len(slots) != 54:
        raise ValueError(f"execution slot count mismatch: {len(slots)}")
    execution_plan = {
        "schema": "collection_execution_plan_v1",
        "status": "FROZEN_PENDING_AUTHORIZED_COLLECTION_WINDOW",
        "request_cap": 54,
        "token_cap": 600000,
        "per_request_reserve_tokens": 10240,
        "input_token_cap": 8192,
        "output_token_cap": 2048,
        "retry_cap": 0,
        "concurrency": 1,
        "window_minutes_max": 90,
        "request_slots": slots,
    }
    return manifest, execution_plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-items", required=True, type=Path)
    parser.add_argument("--split", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--execution-plan", required=True, type=Path)
    args = parser.parse_args()
    manifest, execution_plan = build_manifest(args.candidate_items, args.split)
    write_json_lf(args.manifest, manifest)
    write_json_lf(args.execution_plan, execution_plan)
    print(json.dumps({
        "manifest": str(args.manifest),
        "execution_plan": str(args.execution_plan),
        "counts": manifest["counts"],
        "request_slots": len(execution_plan["request_slots"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
