#!/usr/bin/env python3
"""Build the real exposure/source-cluster audit without model or service calls."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from exposure_classifier import (
    EXPOSURE_UNKNOWN,
    METHOD_DEVELOPMENT_OR_DIAGNOSTIC,
    MODEL_EXPOSURE_PROVENANCE,
    MODEL_OR_FEEDBACK_EXPOSURE,
    PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW,
    STRUCTURAL_SCAN_ONLY,
    build_evidence_sets,
    classify_cluster,
    classify_uid,
)
from offline_core import sha256_file, task_eligibility
from source_cluster_builder import build_clusters, load_raw_records, record_id


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", required=True, type=Path)
    parser.add_argument("--dev", required=True, type=Path)
    parser.add_argument("--task-root", required=True, type=Path)
    parser.add_argument("--candidate-items", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    records = load_raw_records(args.train, args.dev)
    raw_by_id = {record_id(record): record for record in records}
    raw_uids = set(raw_by_id)
    evidence = build_evidence_sets(args.task_root, raw_uids, args.candidate_items)
    cluster_graph = build_clusters(records)

    cluster_rows = []
    exposure_counts = Counter()
    task_total = 0
    for cluster in cluster_graph["clusters"]:
        members = cluster["members"]
        exposure = classify_cluster(members, evidence)
        member_tasks = []
        for uid in members:
            category, sources = classify_uid(uid, evidence)
            exposure_counts[category] += 1
            eligibility = task_eligibility(raw_by_id[uid])
            task_count = len(eligibility.get("usable_rows", []))
            task_total += task_count
            member_tasks.append({
                "uid": uid,
                "category": category,
                "evidence_sources": sources,
                "task_eligible": eligibility["eligible"],
                "contract_task_count": task_count,
                "eligibility": eligibility,
            })
        cluster_rows.append({
            "cluster_id": cluster["cluster_id"],
            "member_count": cluster["member_count"],
            "exposure": exposure,
            "contract_task_count": sum(item["contract_task_count"] for item in member_tasks),
            "task_eligible_record_count": sum(1 for item in member_tasks if item["task_eligible"]),
            "members": member_tasks,
        })

    eligible_clusters = [row for row in cluster_rows if row["contract_task_count"] >= 2]
    immediate_future = [
        row for row in eligible_clusters
        if row["exposure"]["category"] == STRUCTURAL_SCAN_ONLY
    ]
    pending_future = [
        row for row in eligible_clusters
        if row["exposure"]["category"] == PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW
    ]
    excluded_future = [
        row for row in eligible_clusters
        if row["exposure"]["category"] in {
            METHOD_DEVELOPMENT_OR_DIAGNOSTIC,
            MODEL_OR_FEEDBACK_EXPOSURE,
            EXPOSURE_UNKNOWN,
        }
    ]
    future_pool = immediate_future + pending_future
    history_after_future_reservation = max(0, len(eligible_clusters) - len(future_pool))
    history_clusters = [row["cluster_id"] for row in excluded_future]
    if len(immediate_future) >= 8 and history_after_future_reservation >= 12:
        future_status = "PASS_IMMEDIATE"
    elif len(future_pool) >= 8 and history_after_future_reservation >= 12:
        future_status = "CONDITIONAL_PASS_PENDING_PROGRAM_REVIEW"
    else:
        future_status = "INSUFFICIENT"

    cluster_manifest_path = args.output_dir / "SOURCE_CLUSTERS.json"
    write_json(cluster_manifest_path, cluster_graph)
    exposure_register_uids = sorted(
        uid for uid, category in (
            (member["uid"], member["category"])
            for row in cluster_rows
            for member in row["members"]
        )
        if category != STRUCTURAL_SCAN_ONLY
    )
    exposure_register_hash = hashlib.sha256(
        json.dumps(exposure_register_uids, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    tasks_by_category = Counter()
    eligible_clusters_by_category = Counter()
    for row in cluster_rows:
        if row["contract_task_count"] >= 2:
            eligible_clusters_by_category[row["exposure"]["category"]] += 1
        for member in row["members"]:
            tasks_by_category[member["category"]] += member["contract_task_count"]
    audit = {
        "schema": "exposure_and_split_audit_v1",
        "status": "OFFLINE_AUDIT_COMPLETE",
        "scientific_status": "NOT_A_SCIENTIFIC_RESULT",
        "source_identity": {
            "train_path": str(args.train),
            "train_sha256": sha256_file(args.train),
            "dev_path": str(args.dev),
            "dev_sha256": sha256_file(args.dev),
            "candidate_items_path": str(args.candidate_items),
            "candidate_items_sha256": sha256_file(args.candidate_items),
        },
        "normalization_and_association": {
            "thresholds": cluster_graph["thresholds"],
            "normalization": cluster_graph["normalization"],
            "edge_reason_counts": dict(Counter(
                reason["kind"] for edge in cluster_graph["edges"] for reason in edge["reasons"]
            )),
            "report_identity_available": any(
                cluster["report_identity_count"] for cluster in cluster_graph["clusters"]
            ),
        },
        "exposure_model": {
            "principle": "exclusion membership is not exposure evidence",
            "category_counts_by_uid": dict(exposure_counts),
            "model_exposure_provenance": MODEL_EXPOSURE_PROVENANCE,
            "non_structural_exposure_register": {
                "uid_count": len(exposure_register_uids),
                "canonical_sorted_uids_sha256": exposure_register_hash,
                "uids": exposure_register_uids,
            },
            "category_policy": {
                STRUCTURAL_SCAN_ONLY: "eligible_for_developmental_test",
                PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW: "separate_review_required",
                METHOD_DEVELOPMENT_OR_DIAGNOSTIC: "exclude_new_test",
                MODEL_OR_FEEDBACK_EXPOSURE: "exclude_new_test",
                EXPOSURE_UNKNOWN: "exclude_until_resolved",
            },
        },
        "source_clusters": {
            "raw_records": len(records),
            "clusters": len(cluster_rows),
            "eligible_clusters_with_ge2_tasks": len(eligible_clusters),
            "contract_tasks": task_total,
            "immediate_future_clusters": len(immediate_future),
            "pending_program_review_future_clusters": len(pending_future),
            "excluded_future_clusters": len(excluded_future),
            "history_clusters_after_future_reservation": history_after_future_reservation,
            "history_cluster_ids": history_clusters,
            "tasks_by_exposure_category": dict(tasks_by_category),
            "eligible_clusters_by_exposure_category": dict(eligible_clusters_by_category),
            "future_status": future_status,
            "history_requirement": 12,
            "future_requirement": 8,
        },
        "cluster_rows": cluster_rows,
        "unresolved": [
            "raw records have no report ID; clusters are source-association clusters, not report-level independence",
            "program-generated-reference clusters require separate review before future-test use",
        ],
        "outputs": {
            "source_clusters_path": str(cluster_manifest_path),
            "source_clusters_sha256": sha256_file(cluster_manifest_path),
        },
        "cost": {
            "model_calls": 0,
            "endpoint_calls": 0,
            "judge_calls": 0,
            "training_calls": 0,
        },
    }
    audit_path = args.output_dir / "EXPOSURE_AND_SPLIT_AUDIT.json"
    write_json(audit_path, audit)
    print(json.dumps({
        "records": len(records),
        "clusters": len(cluster_rows),
        "eligible_clusters": len(eligible_clusters),
        "immediate_future": len(immediate_future),
        "pending_future": len(pending_future),
        "history_after_future_reservation": history_after_future_reservation,
        "future_status": future_status,
        "audit": str(audit_path),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
