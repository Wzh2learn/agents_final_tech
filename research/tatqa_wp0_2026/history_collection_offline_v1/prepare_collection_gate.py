#!/usr/bin/env python3
"""Prepare deterministic split and a non-executable collection hash-bundle draft."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SEED = "history-collection-offline-v1-split-20261017"
MODEL_SHA256 = "4ac6a06bce551257267f49ad2226f8671a22519ccc1a4dde9d5b433d1f2a410d"
PROGRAM_REVIEW_LINE = re.compile(
    r"^cluster_id=(?P<cluster_id>[a-z0-9_]+) \| "
    r"group=(?P<group>[a-z_]+) \| "
    r"cluster_contract_tasks=(?P<cluster_tasks>\d+) \| "
    r"uid=(?P<uid>[0-9a-f-]+) \| "
    r"uid_contract_tasks=(?P<uid_tasks>\d+) \| "
    r"category=(?P<category>[A-Z_]+) \| "
    r"evidence=(?P<evidence>.+)$"
)
REVIEW_CATEGORY_RANK = {
    "PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE": 1,
    "EXPOSURE_UNKNOWN": 2,
    "METHOD_DEVELOPMENT_OR_DIAGNOSTIC": 3,
    "MODEL_OR_FEEDBACK_EXPOSURE": 4,
}
CLEAN_REVIEW_CATEGORY = "PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rank_key(scope: str, cluster_id: str) -> str:
    return hashlib.sha256(f"{SEED}:{scope}:{cluster_id}".encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def cluster_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "cluster_id": row["cluster_id"],
        "contract_task_count": row["contract_task_count"],
        "task_eligible_record_count": row["task_eligible_record_count"],
        "exposure_category": row["exposure"]["category"],
        "members": [member["uid"] for member in row["members"]],
    }


def parse_program_exposure_review_text(text: str) -> dict[str, dict[str, Any]]:
    parsed: dict[str, dict[str, Any]] = {}
    for line in text.splitlines():
        if not line.startswith("cluster_id="):
            continue
        match = PROGRAM_REVIEW_LINE.fullmatch(line)
        if not match:
            raise ValueError(f"malformed program exposure review line: {line}")
        row = match.groupdict()
        cluster_id = row["cluster_id"]
        category = row["category"]
        if category not in REVIEW_CATEGORY_RANK:
            raise ValueError(f"unknown review category for {cluster_id}: {category}")
        entry = parsed.setdefault(cluster_id, {
            "cluster_id": cluster_id,
            "category": category,
            "uids": [],
            "evidence": [],
        })
        entry["uids"].append(row["uid"])
        entry["evidence"].append(row["evidence"])
        if REVIEW_CATEGORY_RANK[category] > REVIEW_CATEGORY_RANK[entry["category"]]:
            entry["category"] = category
    if len(parsed) != 165:
        raise ValueError(f"expected 165 reviewed clusters, found {len(parsed)}")
    return parsed


def load_program_exposure_review(path: Path) -> dict[str, dict[str, Any]]:
    return parse_program_exposure_review_text(path.read_text(encoding="utf-8"))


def apply_wp2_designation_boundary(
    review: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    for entry in review.values():
        if any("WP2 dryrun role" in evidence for evidence in entry["evidence"]):
            entry.setdefault("category_before_wp2_boundary", entry["category"])
            entry["category"] = "EXPOSURE_UNKNOWN"
            entry["evidence"].append(
                "LOOP_C_SPLIT_REAUDIT N-1: unresolved WP2 dry-run role "
                "designation applied consistently as EXPOSURE_UNKNOWN"
            )
    return review


def review_category_counts(review: dict[str, dict[str, Any]]) -> dict[str, int]:
    counts = {category: 0 for category in REVIEW_CATEGORY_RANK}
    for entry in review.values():
        counts[entry["category"]] += 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline-root", required=True, type=Path)
    args = parser.parse_args()
    root = args.offline_root
    audit_path = root / "EXPOSURE_AND_SPLIT_AUDIT.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    review = load_program_exposure_review(root / "LOOP_C_PROGRAM_EXPOSURE_REVIEW.md")
    raw_review_counts = review_category_counts(review)
    review = apply_wp2_designation_boundary(review)
    adjusted_review_counts = review_category_counts(review)
    wp2_designated = sorted(
        cluster_id for cluster_id, entry in review.items()
        if any("WP2 dryrun role" in evidence for evidence in entry["evidence"])
    )
    eligible = [
        row for row in audit["cluster_rows"]
        if row["contract_task_count"] >= 2
    ]
    future_pool = [
        row for row in eligible
        if row["exposure"]["category"] == "PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW"
    ]
    history_pool = [
        row for row in eligible
        if row["exposure"]["category"] in {
            "METHOD_DEVELOPMENT_OR_DIAGNOSTIC",
            "MODEL_OR_FEEDBACK_EXPOSURE",
        }
    ]
    future_ranked = sorted(future_pool, key=lambda row: rank_key("future", row["cluster_id"]))
    prior_unfiltered = [cluster_row(row) for row in future_ranked]
    clean_pool = [
        row for row in future_pool
        if review[row["cluster_id"]]["category"] == CLEAN_REVIEW_CATEGORY
    ]
    excluded_pending = [
        row for row in future_pool
        if review[row["cluster_id"]]["category"] != CLEAN_REVIEW_CATEGORY
    ]
    clean_ranked = sorted(clean_pool, key=lambda row: rank_key("future", row["cluster_id"]))
    future = []
    for row in clean_ranked[:8]:
        item = cluster_row(row)
        item["program_exposure_review"] = review[row["cluster_id"]]
        item["effective_exposure_category"] = review[row["cluster_id"]]["category"]
        future.append(item)
    development = []
    for row in clean_ranked[8:10]:
        item = cluster_row(row)
        item["program_exposure_review"] = review[row["cluster_id"]]
        item["effective_exposure_category"] = review[row["cluster_id"]]["category"]
        development.append(item)
    reserve = []
    for row in clean_ranked[10:]:
        item = cluster_row(row)
        item["program_exposure_review"] = review[row["cluster_id"]]
        item["effective_exposure_category"] = review[row["cluster_id"]]["category"]
        reserve.append(item)
    excluded = []
    for row in sorted(excluded_pending, key=lambda row: rank_key("future", row["cluster_id"])):
        item = cluster_row(row)
        item["program_exposure_review"] = review[row["cluster_id"]]
        item["effective_exposure_category"] = review[row["cluster_id"]]["category"]
        excluded.append(item)
    history_ranked = sorted(history_pool, key=lambda row: rank_key("history", row["cluster_id"]))
    history = []
    for row in history_ranked[:12]:
        item = cluster_row(row)
        item["program_exposure_review"] = None
        item["effective_exposure_category"] = row["exposure"]["category"]
        history.append(item)
    if len(future) < 8 or len(development) < 2 or len(history) < 12:
        raise RuntimeError("insufficient clean clusters for deterministic proposal")
    split = {
        "schema": "history_collection_split_proposal_v1",
        "status": "FROZEN_FOR_OWNER_COLLECTION_REVIEW",
        "seed": SEED,
        "selection_rule": (
            "apply LOOP_C_SPLIT_REAUDIT N-1 to WP2 dry-run role designations, "
            "exclude non-clean LOOP_C_PROGRAM_EXPOSURE_REVIEW categories, "
            "then sha256(seed:scope:cluster_id) ascending"
        ),
        "future_test": future,
        "development": development,
        "history": history,
        "reserve": reserve,
        "excluded_pending_review": excluded,
        "revision": {
            "revision": 3,
            "reason": (
                "r1 found 158 clean, 2 EXPOSURE_UNKNOWN, and 5 exposed; "
                "r2 N-1 consistently holds all WP2 dry-run role designations "
                "as EXPOSURE_UNKNOWN, leaving 141 clean, 19 unknown, and 5 exposed"
            ),
            "program_review_raw_category_counts": raw_review_counts,
            "focused_review_wp2_designation_policy":
                "all r1 appendix entries with WP2 dryrun role evidence -> EXPOSURE_UNKNOWN",
            "wp2_designated_cluster_ids": wp2_designated,
            "wp2_category_reclassified_count": sum(
                entry.get("category_before_wp2_boundary") is not None
                and entry["category_before_wp2_boundary"] != entry["category"]
                for entry in review.values()
            ),
            "prior_unfiltered_future_test_ids": [
                row["cluster_id"] for row in prior_unfiltered[:8]
            ],
            "prior_unfiltered_development_ids": [
                row["cluster_id"] for row in prior_unfiltered[8:10]
            ],
            "rejected_from_prior_future_test": [
                {
                    "cluster_id": row["cluster_id"],
                    "category": review[row["cluster_id"]]["category"],
                }
                for row in future_pool
                if row["cluster_id"] in {
                    item["cluster_id"] for item in prior_unfiltered[:8]
                }
                and review[row["cluster_id"]]["category"] != CLEAN_REVIEW_CATEGORY
            ],
            "superseded_revision_2_future_test_ids": [
                "cluster_1340", "cluster_0306", "cluster_0615", "cluster_0978",
                "cluster_1724", "cluster_1628", "cluster_2060", "cluster_2314",
            ],
            "superseded_revision_2_development_ids": [
                "cluster_1642", "cluster_2010",
            ],
            "rejected_from_revision_2_future_test": [
                {
                    "cluster_id": "cluster_2314",
                    "category": "EXPOSURE_UNKNOWN",
                    "reason": "LOOP_C_SPLIT_REAUDIT N-1",
                }
            ],
        },
        "checks": {
            "source_cluster_disjoint": len({
                row["cluster_id"]
                for row in future + development + history + reserve + excluded
            }) == len(future + development + history + reserve + excluded),
            "future_clusters": len(future),
            "development_clusters": len(development),
            "history_clusters": len(history),
            "reserve_clusters": len(reserve),
            "excluded_pending_review_clusters": len(excluded),
            "reviewed_pending_clusters": len(review),
            "clean_pending_clusters": len(clean_pool),
            "raw_review_category_counts": raw_review_counts,
            "adjusted_review_category_counts": adjusted_review_counts,
            "all_selected_have_ge2_tasks": all(
                row["contract_task_count"] >= 2
                for row in future + development + history + reserve + excluded
            ),
            "all_future_clean": all(
                row["program_exposure_review"]["category"] == CLEAN_REVIEW_CATEGORY
                for row in future
            ),
            "future_content_excluded_from_experience_design": True,
        },
    }
    split_path = root / "SPLIT_PROPOSAL.json"
    write_json(split_path, split)

    package_files = [
        "offline_core.py",
        "source_cluster_builder.py",
        "exposure_classifier.py",
        "collection_chain.py",
        "raw_capture.py",
        "build_exposure_and_split_audit.py",
        "run_offline_tests.py",
        "prepare_collection_gate.py",
        "fixtures/synthetic_offline_cases.json",
        "tests/test_offline_v1.py",
    ]
    bundle = {
        "schema": "pre_collection_hash_bundle_draft_v1",
        "status": "NOT_READY_FOR_COLLECTION",
        "owner_review_state": "READY_WITH_UNRESOLVED_ONLINE_GATES",
        "resolved": {
            "source_and_split": {
                "raw_train_sha256": audit["source_identity"]["train_sha256"],
                "raw_dev_sha256": audit["source_identity"]["dev_sha256"],
                "candidate_items_sha256": audit["source_identity"]["candidate_items_sha256"],
                "exposure_audit_sha256": sha256_file(audit_path),
                "source_clusters_sha256": sha256_file(root / "SOURCE_CLUSTERS.json"),
                "split_proposal_sha256": sha256_file(split_path),
                "program_exposure_review_sha256": sha256_file(
                    root / "LOOP_C_PROGRAM_EXPOSURE_REVIEW.md"
                ),
                "split_reaudit_sha256": sha256_file(
                    root / "LOOP_C_SPLIT_REAUDIT.md"
                ),
                "split_delta_reaudit_sha256": sha256_file(
                    root / "LOOP_C_SPLIT_DELTA_REAUDIT.md"
                ),
                "non_structural_exposure_register_uid_count":
                    audit["exposure_model"]["non_structural_exposure_register"]["uid_count"],
                "non_structural_exposure_register_sha256":
                    audit["exposure_model"]["non_structural_exposure_register"]["canonical_sorted_uids_sha256"],
            },
            "implementation": {
                path: sha256_file(root / path) for path in package_files
            },
            "control": {
                "local_test_receipt_sha256": sha256_file(root / "tests" / "TEST_RECEIPT.json"),
                "gb10_test_receipt_sha256": (
                    sha256_file(root / "tests" / "TEST_RECEIPT_GB10.json")
                    if (root / "tests" / "TEST_RECEIPT_GB10.json").exists()
                    else "UNRESOLVED"
                ),
                "collection_request_cap": 54,
                "collection_token_cap": 600000,
                "retry_cap": 0,
                "concurrency": 1,
                "judge_calls": 0,
                "training_calls": 0,
                "generated_json_newline": "LF",
            },
            "independent_review_reports": {
                name: sha256_file(root / name)
                for name in (
                    "LOOP_C_EXPOSURE_AND_SOFTWARE_AUDIT.md",
                    "LOOP_C_REAUDIT.md",
                    "LOOP_C_REAUDIT3.md",
                    "LOOP_C_PROGRAM_EXPOSURE_REVIEW.md",
                    "LOOP_C_SPLIT_REAUDIT.md",
                    "LOOP_C_SPLIT_DELTA_REAUDIT.md",
                )
                if (root / name).exists()
            },
            "model_artifact": {
                "model": "Qwen3.6-35B-A3B-Q4_K_M.gguf",
                "sha256": MODEL_SHA256,
            },
        },
        "unresolved": {
            "loop_c_independent_review": "R3_ACCEPTED_N1_N2_CLOSED",
            "program_generated_reference_review":
                "R1_CONDITIONAL_ADJUSTED_BY_R2_N1_141_CLEAN_19_UNKNOWN_5_EXPOSED",
            "final_future_and_history_split":
                "V3_DELTA_REVIEW_ACCEPTED",
            "focused_split_review_result":
                "R3_DELTA_ACCEPTED_N1_CLOSED",
            "task_and_reference_manifest": "NOT_MATERIALIZED",
            "parse_numeric_accounting_sign_convention":
                "RESOLVED_NEGATIVE_PARENS_NOT_DOUBLE_INVERTED",
            "provenance_comment_citations":
                "RESOLVED_MODEL_EXPOSURE_PROVENANCE_MAP",
            "tokenizer_chat_template_service_binary_generation_parameters": "NOT_BOUND",
            "online_collection_runner_and_prompt_templates": "NOT_IMPLEMENTED_OR_NOT_BOUND",
            "beijing_window": "NOT_AUTHORIZED",
            "independent_software_review_result": "R3_ACCEPTED_N1_N2_CLOSED",
        },
    }
    bundle_path = root / "PRE_COLLECTION_HASH_BUNDLE_DRAFT.json"
    write_json(bundle_path, bundle)
    print(json.dumps({
        "split": str(split_path),
        "future": len(future),
        "development": len(development),
        "history": len(history),
        "reserve": len(reserve),
        "bundle": str(bundle_path),
        "status": bundle["status"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
