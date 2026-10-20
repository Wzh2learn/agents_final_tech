#!/usr/bin/env python3
"""Audit and minimally correct future-task period order without model calls."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from execution_core import unit_tokens, write_json_lf  # noqa: E402


DATE_FORMATS = ("%d/%m/%Y", "%b %d, %Y", "%B %d, %Y")
CANDIDATE_ITEMS_SHA256 = "5f61f2a476c220f4ed4c159030490c6dfaabcea9778820abc89d3bed859738aa"
PERIOD_REPAIRS = {
    "F11": {
        "early": {"col": 1, "label": "Actual Fiscal 2018 (1) $", "value": "1,007"},
        "late": {
            "col": 3,
            "label": "Actual Fiscal 2019 (constant currency) (3) $",
            "value": "1,092",
        },
        "reference": 85.0,
        "reason": "replace mismatched percent column with same-table 2019 dollar column",
    },
    "F12": {
        "early": {"col": 1, "label": "Actual Fiscal 2018 (1) $", "value": "2,147"},
        "late": {
            "col": 3,
            "label": "Actual Fiscal 2019 (constant currency) (3) $",
            "value": "2,294",
        },
        "reference": 147.0,
        "reason": "replace mismatched percent column with same-table 2019 dollar column",
    },
}


def period_key(label: str) -> tuple[datetime | None, str | None]:
    text = " ".join(label.split())
    fiscal = re.search(r"Fiscal\s+((?:19|20)\d{2})", text, re.IGNORECASE)
    if fiscal:
        return datetime(int(fiscal.group(1)), 6, 30), None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt), None
        except ValueError:
            pass
    year = re.search(r"(?:19|20)\d{2}", text)
    if year:
        return datetime(int(year.group(0)), 6, 30), None
    return None, "period_date_unresolved"


def unit_compatibility(task: dict) -> tuple[bool, dict]:
    late = unit_tokens(task["period_late"])
    early = unit_tokens(task["period_early"])
    if not late or not early:
        return True, {
            "late_label_units": sorted(late),
            "early_label_units": sorted(early),
            "rule": "missing label units inherit explicit task unit",
        }
    intersection = late & early
    return bool(intersection), {
        "late_label_units": sorted(late),
        "early_label_units": sorted(early),
        "intersection": sorted(intersection),
    }


def corrected_task(row: dict) -> dict:
    output = copy.deepcopy(row)
    task = output["actor_task"]["task"]
    projection = output["actor_task"]["evidence"]["table_projection"]
    old_reference = float(output["hidden"]["reference"]["delta_target"])
    task["period_late"], task["period_early"] = task["period_early"], task["period_late"]
    projection[0][1], projection[0][2] = projection[0][2], projection[0][1]
    projection[1][1], projection[1][2] = projection[1][2], projection[1][1]
    output["hidden"]["period_late"], output["hidden"]["period_early"] = (
        output["hidden"]["period_early"],
        output["hidden"]["period_late"],
    )
    reference = output["hidden"]["reference"]
    reference["delta_source"] = -float(reference["delta_source"])
    reference["delta_target"] = -old_reference
    reference["previous_candidate_gold_value"] = reference.pop("candidate_gold_value")
    reference["candidate_gold_agreement"] = None
    reference["reference_revision"] = "chronological_period_swap"
    output["qualification"]["candidate_gold_agreement"] = (
        "NOT_APPLICABLE_AFTER_PERIOD_CORRECTION"
    )
    output["revision"] = {
        "old_period_late": row["actor_task"]["task"]["period_late"],
        "old_period_early": row["actor_task"]["task"]["period_early"],
        "old_reference": old_reference,
        "new_reference": -old_reference,
    }
    return output


def corrected_task_from_repair(row: dict, repair: dict) -> dict:
    output = copy.deepcopy(row)
    task = output["actor_task"]["task"]
    projection = output["actor_task"]["evidence"]["table_projection"]
    old_reference = float(output["hidden"]["reference"]["delta_target"])
    task["period_early"] = repair["early"]["label"]
    task["period_late"] = repair["late"]["label"]
    projection[0] = ["row", repair["early"]["label"], repair["late"]["label"]]
    projection[1] = [
        projection[1][0],
        repair["early"]["value"],
        repair["late"]["value"],
    ]
    output["hidden"]["period_early"] = {
        "col": repair["early"]["col"], "label": repair["early"]["label"]
    }
    output["hidden"]["period_late"] = {
        "col": repair["late"]["col"], "label": repair["late"]["label"]
    }
    reference = output["hidden"]["reference"]
    reference["delta_source"] = repair["reference"]
    reference["delta_target"] = repair["reference"]
    reference["previous_candidate_gold_value"] = reference.pop("candidate_gold_value")
    reference["candidate_gold_agreement"] = None
    reference["reference_revision"] = "same_unit_period_column_repair"
    output["qualification"]["candidate_gold_agreement"] = (
        "NOT_APPLICABLE_AFTER_PERIOD_CORRECTION"
    )
    output["revision"] = {
        "old_period_late": row["actor_task"]["task"]["period_late"],
        "old_period_early": row["actor_task"]["task"]["period_early"],
        "old_reference": old_reference,
        "new_period_late": repair["late"]["label"],
        "new_period_early": repair["early"]["label"],
        "new_reference": repair["reference"],
        "reason": repair["reason"],
    }
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--output-manifest", required=True, type=Path)
    args = parser.parse_args()
    source = json.loads(args.manifest.read_text(encoding="utf-8"))
    future_rows = [row for row in source["tasks"] if row["bucket"] == "future_test"]
    audit_rows = []
    output_rows = []
    for row in future_rows:
        task = row["actor_task"]["task"]
        late_key, late_error = period_key(task["period_late"])
        early_key, early_error = period_key(task["period_early"])
        units_ok, unit_evidence = unit_compatibility(task)
        inverted = bool(
            late_key is not None
            and early_key is not None
            and early_key > late_key
        )
        repair = PERIOD_REPAIRS.get(row["task_id"])
        if repair:
            status = "CORRECTED_ALTERNATE_SAME_UNIT_PERIOD"
            corrected = corrected_task_from_repair(row, repair)
            corrected["pilot_status"] = "QUALIFIED"
            units_ok = True
            unit_evidence = {
                "repair": repair,
                "source_item_id": row["hidden"]["source_item_id"],
            }
        elif not units_ok:
            status = "UNRESOLVED_PERIOD_UNIT_MISMATCH"
            corrected = copy.deepcopy(row)
            corrected["pilot_status"] = status
        elif late_error or early_error:
            status = "UNRESOLVED_PERIOD_DATE"
            corrected = copy.deepcopy(row)
            corrected["pilot_status"] = status
        elif inverted:
            status = "CORRECTED_INVERSION"
            corrected = corrected_task(row)
            corrected["pilot_status"] = "QUALIFIED"
        else:
            status = "PASS"
            corrected = copy.deepcopy(row)
            corrected["pilot_status"] = "QUALIFIED"
        audit_rows.append({
            "task_id": row["task_id"],
            "source_cluster_id": row["hidden"]["source_cluster_id"],
            "old_period_late": task["period_late"],
            "old_period_early": task["period_early"],
            "late_key": late_key.isoformat() if late_key else None,
            "early_key": early_key.isoformat() if early_key else None,
            "chronologically_inverted": inverted,
            "units_compatible": units_ok,
            "unit_evidence": unit_evidence,
            "status": status,
        })
        output_rows.append(corrected)
    qualified = [row for row in output_rows if row.get("pilot_status") == "QUALIFIED"]
    unresolved = [
        row for row in output_rows if row.get("pilot_status") != "QUALIFIED"
    ]
    audit = {
        "schema": "pilot_period_audit_v1",
        "status": "PILOT_BLOCKED" if unresolved else "PASS",
        "source_identity": {
            "candidate_items_v2_sha256": CANDIDATE_ITEMS_SHA256,
            "collection_manifest_sha256": (
                "5be130d7d6c3514862ad44149ec61b95ba68c8d83178e259aa7da90904633db6"
            ),
        },
        "task_count": len(audit_rows),
        "qualified_count": len(qualified),
        "unresolved_count": len(unresolved),
        "unresolved_task_ids": [row["task_id"] for row in unresolved],
        "rows": audit_rows,
    }
    output = copy.deepcopy(source)
    output["schema"] = "task_reference_manifest_pilot_v2"
    output["status"] = (
        "BLOCKED_UNRESOLVED_PERIOD_UNIT"
        if unresolved
        else "QUALIFIED_FOR_PILOT_PREPARATION"
    )
    output["tasks"] = output_rows
    output["period_revision"] = {
        "corrected_task_ids": [
            row["task_id"] for row in audit_rows
            if row["status"] == "CORRECTED_INVERSION"
        ],
        "unresolved_task_ids": [row["task_id"] for row in unresolved],
        "reserve_substitution_allowed": False,
        "source_candidate_items_sha256": CANDIDATE_ITEMS_SHA256,
    }
    write_json_lf(args.audit, audit)
    write_json_lf(args.output_manifest, output)
    print(json.dumps({
        "audit": str(args.audit),
        "manifest": str(args.output_manifest),
        "qualified": len(qualified),
        "unresolved": [row["task_id"] for row in unresolved],
    }, sort_keys=True))
    return 0 if not unresolved else 2


if __name__ == "__main__":
    raise SystemExit(main())
