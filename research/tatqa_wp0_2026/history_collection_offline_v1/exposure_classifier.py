#!/usr/bin/env python3
"""Classify source exposure by evidence strength, not exclusion-list membership."""

from __future__ import annotations

from pathlib import Path
from typing import Any


STRUCTURAL_SCAN_ONLY = "STRUCTURAL_SCAN_ONLY"
PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW = "PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW"
METHOD_DEVELOPMENT_OR_DIAGNOSTIC = "METHOD_DEVELOPMENT_OR_DIAGNOSTIC"
MODEL_OR_FEEDBACK_EXPOSURE = "MODEL_OR_FEEDBACK_EXPOSURE"
EXPOSURE_UNKNOWN = "EXPOSURE_UNKNOWN"

RANK = {
    EXPOSURE_UNKNOWN: 5,
    MODEL_OR_FEEDBACK_EXPOSURE: 4,
    METHOD_DEVELOPMENT_OR_DIAGNOSTIC: 3,
    PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW: 2,
    STRUCTURAL_SCAN_ONLY: 1,
}

MODEL_EXPOSURE_PROVENANCE = {
    "tq4_natural_selected": {
        "uids_source": "tq4_calibration_v1/panel_v2/natural/SELECTION_LOG.json:selected[].uid",
        "use_evidence": "selected TQ-4 tasks subsequently appeared in TQ-4 model run artifacts",
    },
    "tq5_selected": {
        "uids_source": "tq5_source_validation_v1/panel/SELECTION_LOG.json:selected[].uid",
        "use_evidence": "selected TQ-5 tasks subsequently appeared in run 20261017T072340Z_5d8942bd",
    },
    "tq4_candidate_source_mapping": {
        "uids": {
            "329e3ff5-0cff-4849-8fd0-9b1e5606f6ca": "Q02 exact table/paragraph mapping to a TQ-4 candidate input used in model prompts",
            "d2bba753-0df3-4a39-860b-bde563261fec": "Q03 unique near mapping to a TQ-4 candidate input used in model prompts",
            "44c7c9ef-bb9f-45c9-9ee5-e2bf465c3617": "Q04 exact paragraph mapping to a TQ-4 candidate input used in model prompts",
        },
        "use_evidence": "candidate inputs Q02-Q04 entered TQ-4 B/C prompts; raw source UIDs were recovered by deterministic content mapping",
    },
    "wp2_prompt_exposure": {
        "uids": {
            "3ab739eb-c0d7-44f5-9377-b8a02bafb361": "WP2 opaque origin_fbb782143f9a and history item prompts",
            "97176853-a81e-422a-a8c1-e0542348d051": "WP2 opaque origin_5c4e334806b6 and history item prompts",
        },
        "use_evidence": "WP2 S4B prompt/bridge receipts and candidate_items_v2 opaque-id replay",
    },
}


def load_json(path: Path) -> Any:
    import json

    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_evidence_sets(
    task_root: Path,
    raw_uids: set[str],
    candidate_items_path: Path,
) -> dict[str, set[str]]:
    source_refs = task_root / "tq5_source_validation_v1" / "source_refs"
    coordinator = task_root / "coordinator"
    tq4 = task_root / "tq4_calibration_v1"
    origin_manifest = load_json(source_refs / "origin_manifest.json")
    pool_inventory = load_json(coordinator / "pool_inventory.json")
    case_provenance = load_json(coordinator / "case_provenance.json")
    tq4_natural = load_json(tq4 / "panel_v2" / "natural" / "SELECTION_LOG.json")
    tq5_selection = load_json(
        task_root / "tq5_source_validation_v1" / "panel" / "SELECTION_LOG.json"
    )
    candidate_items = load_json(candidate_items_path)
    items = candidate_items.get("items", candidate_items)

    generated = {
        str(item["uid"]) for item in origin_manifest["origins"]
    } | {
        str(item["origin_id"]).removeprefix("tatqa_") for item in items
    }
    diagnostic = {
        str(item["uid"]) for item in pool_inventory
    } | {
        str(item["uid"]) for item in case_provenance
    }
    literal_model_exposure = {
        str(item["uid"]) for item in tq4_natural["selected"]
    } | {
        str(item["uid"]) for item in tq5_selection["selected"]
    } | {
        "329e3ff5-0cff-4849-8fd0-9b1e5606f6ca",
        "d2bba753-0df3-4a39-860b-bde563261fec",
        "44c7c9ef-bb9f-45c9-9ee5-e2bf465c3617",
        "3ab739eb-c0d7-44f5-9377-b8a02bafb361",
        "97176853-a81e-422a-a8c1-e0542348d051",
    }
    return {
        "structural": set(raw_uids),
        "generated": generated & raw_uids,
        "diagnostic": diagnostic & raw_uids,
        "model": literal_model_exposure & raw_uids,
    }


def classify_uid(uid: str, evidence: dict[str, set[str]]) -> tuple[str, list[str]]:
    sources = []
    if uid in evidence["model"]:
        sources.append("recorded_model_or_feedback_use")
    if uid in evidence["diagnostic"]:
        sources.append("recorded_method_development_or_diagnostic_use")
    if uid in evidence["generated"]:
        sources.append("deterministic_task_or_reference_generation")
    if uid in evidence["structural"]:
        sources.append("full_raw_structural_scan")
    if uid in evidence["model"]:
        category = MODEL_OR_FEEDBACK_EXPOSURE
    elif uid in evidence["diagnostic"]:
        category = METHOD_DEVELOPMENT_OR_DIAGNOSTIC
    elif uid in evidence["generated"]:
        category = PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW
    elif uid in evidence["structural"]:
        category = STRUCTURAL_SCAN_ONLY
    else:
        category = EXPOSURE_UNKNOWN
        sources.append("no_recorded_access_evidence")
    return category, sources


def classify_cluster(members: list[str], evidence: dict[str, set[str]]) -> dict[str, Any]:
    rows = [{"uid": uid, "category": classify_uid(uid, evidence)[0]} for uid in members]
    category = max((row["category"] for row in rows), key=lambda value: RANK[value])
    counts = {
        name: sum(1 for row in rows if row["category"] == name)
        for name in RANK
    }
    return {
        "category": category,
        "category_counts": counts,
        "future_test_state": {
            STRUCTURAL_SCAN_ONLY: "ELIGIBLE_FOR_DEVELOPMENTAL_TEST",
            PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW: "PENDING_SEPARATE_REVIEW",
            METHOD_DEVELOPMENT_OR_DIAGNOSTIC: "EXCLUDE",
            MODEL_OR_FEEDBACK_EXPOSURE: "EXCLUDE",
            EXPOSURE_UNKNOWN: "EXCLUDE",
        }[category],
    }
