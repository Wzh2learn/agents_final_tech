#!/usr/bin/env python3
"""Requalify the frozen task package without changing frozen source artifacts."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "build_same_number_role_tasks.py"
SPEC = importlib.util.spec_from_file_location("build_same_number_role_tasks", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"module_import_failed:{MODULE_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"object_required:{path}")
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def qualification_for(hidden: dict[str, Any]) -> dict[str, Any]:
    if hidden["expected_decision"] != "WRONG_ROLE":
        return {
            "status": "QUALIFIED_POSITIVE_CONTROL",
            "reason": "Positive control has identical visible target/candidate role.",
            "visible_difference_fields": [],
            "hidden_difference_fields": [],
        }
    kind = "signed_delta" if hidden["case_type"] == "same_delta" else "cell_value"
    return MODULE.qualify_role_pair(
        hidden["target_role"],
        hidden["candidate_role"],
        kind,
        hidden["target_unit"],
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frozen-package", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    frozen = load_json(args.frozen_package.resolve())
    references = []
    for old in frozen["hidden_references"]:
        row = copy.deepcopy(old)
        row["qualification"] = qualification_for(old)
        references.append(row)

    negative_rows = [
        row for row in references if row["expected_decision"] == "WRONG_ROLE"
    ]
    status_counts = Counter(row["qualification"]["status"] for row in negative_rows)
    unscorable_ids = {
        row["task_id"]
        for row in negative_rows
        if row["qualification"]["status"] != "QUALIFIED_VISIBLE_ROLE_DIFFERENCE"
    }
    # Keep only complete positive/negative pairs in the requalified package.
    excluded_pair_ids = set()
    for row in references:
        if row["task_id"] in unscorable_ids:
            excluded_pair_ids.add(row["task_id"])
            pair_suffix = "_P1" if row["task_id"].endswith("_N2") else "_N2"
            excluded_pair_ids.add(row["task_id"][:-3] + pair_suffix)

    task_by_id = {row["task_id"]: row for row in frozen["tasks"]}
    reference_by_id = {row["task_id"]: row for row in references}
    retained_ids = [
        task_id
        for task_id in task_by_id
        if task_id not in excluded_pair_ids
    ]
    package = copy.deepcopy(frozen)
    package["schema"] = "same_number_role_task_package_qualification_v2"
    package["qualification_schema"] = "same_number_role_task_qualification_v2"
    package["status"] = "QUALIFICATION_FIXED_NO_MODEL_REQUEST"
    package["authorization"] = "MODEL_RUN_NOT_AUTHORIZED_YET"
    package["qualification_rule"] = {
        "visible_fields": [
            "row_label",
            "period_label",
            "early_period",
            "late_period",
            "unit",
            "scale",
        ],
        "hidden_coordinates_are_not_sufficient": True,
        "row_index_only_status": "UNSCORABLE_FOR_REFERENCE",
        "no_silent_reference_rewrite": True,
    }
    package["tasks"] = [task_by_id[task_id] for task_id in retained_ids]
    package["hidden_references"] = [
        reference_by_id[task_id] for task_id in retained_ids
    ]
    package["counts"] = {
        **frozen["counts"],
        "total_tasks": len(retained_ids),
        "development_tasks": sum(
            task_id.startswith("NR_development") for task_id in retained_ids
        ),
        "future_tasks": sum(
            task_id.startswith("NR_exploratory_future") for task_id in retained_ids
        ),
        "qualified_negative_pairs": status_counts[
            "QUALIFIED_VISIBLE_ROLE_DIFFERENCE"
        ],
        "unscorable_pairs": status_counts["UNSCORABLE_FOR_REFERENCE"],
        "human_semantic_review_pairs": status_counts[
            "REQUIRES_HUMAN_SEMANTIC_ADJUDICATION"
        ],
        "excluded_pair_count": len(excluded_pair_ids) // 2,
    }
    report = {
        "schema": "same_number_role_qualification_report_v2",
        "status": "QUALIFICATION_FIXED_NO_MODEL_REQUEST",
        "source_package": str(args.frozen_package.resolve()),
        "raw_regeneration_status": "RAW_INPUTS_NOT_PRESENT_IN_WORKSPACE",
        "qualification_rule": package["qualification_rule"],
        "counts": package["counts"],
        "negative_status_counts": dict(status_counts),
        "candidate_pair_qualifications": [
            row["qualification"] | {"task_id": row["task_id"]}
            for row in negative_rows
        ],
        "excluded_from_model_tasks": [
            row["qualification"] | {"task_id": row["task_id"]}
            for row in negative_rows
            if row["task_id"] in unscorable_ids
        ],
        "retained_task_ids": retained_ids,
    }
    write_json(output_dir / "SAME_NUMBER_ROLE_TASKS_QUALIFICATION_V2.json", package)
    write_json(output_dir / "SAME_NUMBER_ROLE_QUALIFICATION_REPORT_V2.json", report)
    print(json.dumps(report["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
