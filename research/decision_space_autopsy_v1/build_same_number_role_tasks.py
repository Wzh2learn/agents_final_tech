#!/usr/bin/env python3
"""Build exploratory same-number/same-delta role-binding tasks."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
AUTOPSY_DIR = Path(__file__).resolve().parent
QUALIFICATION = ROOT / "research/tatqa_candidate_b_qualification_v1"
RAW_DIR = ROOT / "data/research/tatqa_raw_2026"


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


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module_import_failed:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalized(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).strip())


def visible_text_key(value: Any) -> str:
    """Canonicalize visible labels conservatively for substantive comparison."""
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    text = re.sub(r"[\W_]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def claim_kind(case: dict[str, Any]) -> str:
    return "signed_delta" if "normalized_delta" in case else "cell_value"


def visible_role_fields(
    role: dict[str, Any],
    kind: str,
    unit: dict[str, Any] | None = None,
) -> dict[str, str]:
    fields = {
        "row_label": role.get("row_label", ""),
    }
    if kind == "signed_delta":
        fields["early_period"] = role.get("early_period", "")
        fields["late_period"] = role.get("late_period", "")
    else:
        fields["period_label"] = role.get("period_label", "")
    if unit is not None or "unit" in role or "scale" in role:
        fields["unit"] = role.get("unit", unit.get("unit", "") if unit else "")
        fields["scale"] = role.get("scale", unit.get("scale", "") if unit else "")
    return {key: visible_text_key(value) for key, value in fields.items()}


def hidden_role_difference(
    target: dict[str, Any], candidate: dict[str, Any]
) -> list[str]:
    fields = ("row_index", "period_index", "year", "value", "delta")
    return [
        key
        for key in fields
        if key in target or key in candidate
        if target.get(key) != candidate.get(key)
    ]


def qualify_role_pair(
    target: dict[str, Any],
    candidate: dict[str, Any],
    kind: str,
    unit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify a negative pair using only fields visible to the actor."""
    target_visible = visible_role_fields(target, kind, unit)
    candidate_visible = visible_role_fields(candidate, kind, unit)
    visible_difference_fields = [
        key
        for key in target_visible
        if target_visible[key] != candidate_visible[key]
    ]
    hidden_difference_fields = hidden_role_difference(target, candidate)
    if visible_difference_fields:
        status = "QUALIFIED_VISIBLE_ROLE_DIFFERENCE"
        reason = (
            "WRONG_ROLE is decidable from visible row_label/period/unit role "
            "differences."
        )
    elif hidden_difference_fields:
        status = "UNSCORABLE_FOR_REFERENCE"
        reason = (
            "The roles differ only in hidden coordinates or values; actor-visible "
            "row_label/period/unit fields cannot establish WRONG_ROLE."
        )
    else:
        status = "REQUIRES_HUMAN_SEMANTIC_ADJUDICATION"
        reason = "No visible or hidden field difference establishes a distinct role."
    return {
        "status": status,
        "reason": reason,
        "visible_difference_fields": visible_difference_fields,
        "hidden_difference_fields": hidden_difference_fields,
        "target_visible_role": target_visible,
        "candidate_visible_role": candidate_visible,
    }


def raw_records() -> dict[str, dict[str, Any]]:
    records = {}
    for split in ("train", "dev"):
        for index, item in enumerate(
            json.loads((RAW_DIR / f"tatqa_dataset_{split}.json").read_text(encoding="utf-8"))
        ):
            records[item["table"]["uid"]] = {
                "split": split,
                "index": index,
                "uid": item["table"]["uid"],
                "table": item["table"]["table"],
            }
    return records


def choose_case(
    cases: list[dict[str, Any]],
    cluster_id: str,
    unit_lookup: Any,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    cluster_cases = [case for case in cases if case["cluster_id"] == cluster_id]
    qualifications = []
    for case in cluster_cases:
        if len(case["roles"]) < 2:
            continue
        unit = unit_lookup(case["source_uid"])
        qualification = qualify_role_pair(
            case["roles"][0],
            case["roles"][1],
            claim_kind(case),
            unit,
        )
        qualification.update(
            {
                "cluster_id": case["cluster_id"],
                "source_uid": case["source_uid"],
                "case_type": claim_kind(case),
                "normalized_value": case.get("normalized_value"),
                "normalized_delta": case.get("normalized_delta"),
            }
        )
        qualifications.append(qualification)
        if qualification["status"] == "QUALIFIED_VISIBLE_ROLE_DIFFERENCE":
            return case, qualifications
    return None, qualifications


def make_task(
    case: dict[str, Any],
    record: dict[str, Any],
    checker: Any,
    scope: str,
    task_index: int,
    positive: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    roles = case["roles"]
    target = roles[0]
    candidate = roles[0] if positive else roles[1]
    table = record["table"]
    header = table[0]
    unit = checker.infer_unit_context(header[0])
    if unit is None:
        raise ValueError(f"unit_context_missing:{case['source_uid']}")
    if "normalized_delta" in case:
        claim_type = "signed_delta"
        claim_value = float(case["normalized_delta"])
        early_value = checker.parse_decimal(table[target["row_index"]][
            next(i for i, h in enumerate(header) if normalized(h) == normalized(target["early_period"]))
        ])
        late_value = checker.parse_decimal(table[target["row_index"]][
            next(i for i, h in enumerate(header) if normalized(h) == normalized(target["late_period"]))
        ])
        if early_value is None or late_value is None:
            raise ValueError(f"delta_operand_missing:{case['source_uid']}")
        expected_expression = f"{late_value} - {early_value}"
        requested_role = {
            "row_label": target["row_label"],
            "early_period": target["early_period"],
            "late_period": target["late_period"],
            "unit": unit["unit"],
            "scale": unit["scale"],
        }
        candidate_citation = {
            "row_label": candidate["row_label"],
            "early_period": candidate["early_period"],
            "late_period": candidate["late_period"],
            "unit": unit["unit"],
            "scale": unit["scale"],
        }
    else:
        claim_type = "cell_value"
        claim_value = float(case["normalized_value"])
        expected_expression = str(claim_value)
        requested_role = {
            "row_label": target["row_label"],
            "period": target["period_label"],
            "unit": unit["unit"],
            "scale": unit["scale"],
        }
        candidate_citation = {
            "row_label": candidate["row_label"],
            "period": candidate["period_label"],
            "unit": unit["unit"],
            "scale": unit["scale"],
        }

    cluster_id = case["cluster_id"]
    task_id = f"NR_{scope}_{cluster_id.replace('cluster_', '')}_{'P' if positive else 'N'}{task_index}"
    actor_task = {
        "schema": "same_number_role_actor_task_v1",
        "task_id": task_id,
        "instructions": (
            "Bind the candidate citation to the requested role, execute the candidate "
            "value or signed difference with calc, and decide whether the evidence role "
            "supports the claim. Numeric agreement alone is insufficient."
        ),
        "question": (
            "Does the candidate evidence support the requested role and claimed "
            f"{claim_type.replace('_', ' ')}?"
        ),
        "table": table,
        "claim": {
            "kind": claim_type,
            "value": claim_value,
            "unit": unit["unit"],
            "scale": unit["scale"],
        },
        "requested_role": requested_role,
        "candidate_citation": candidate_citation,
    }
    hidden = {
        "schema": "same_number_role_hidden_reference_v1",
        "task_id": task_id,
        "partition": scope,
        "source_cluster_id": cluster_id,
        "source_uid": case["source_uid"],
        "raw_split": record["split"],
        "raw_index": record["index"],
        "case_type": "same_delta" if "normalized_delta" in case else "same_number",
        "target_role": target,
        "candidate_role": candidate,
        "expected_decision": "SUPPORTED" if positive else "WRONG_ROLE",
        "expected_calculator_expression": expected_expression,
        "expected_value": claim_value,
        "target_unit": unit,
        "role_match": positive,
        "qualification": (
            {
                "status": "QUALIFIED_POSITIVE_CONTROL",
                "reason": "Positive control has identical visible target/candidate role.",
                "visible_difference_fields": [],
                "hidden_difference_fields": [],
            }
            if positive
            else qualify_role_pair(target, candidate, claim_kind(case), unit)
        ),
    }
    return actor_task, hidden


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--artifact-name",
        default="SAME_NUMBER_ROLE_TASKS_DRAFT.json",
        help="Task package filename; use a new name for versioned qualification artifacts.",
    )
    parser.add_argument(
        "--qualification-report-name",
        default="SAME_NUMBER_ROLE_QUALIFICATION_REPORT.json",
        help="Qualification report filename written beside the task package.",
    )
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    autopsy = load_json(AUTOPSY_DIR / "DECISION_SPACE_AUTOPSY.json")
    source_exposure = load_json(QUALIFICATION / "SOURCE_EXPOSURE_QUALIFICATION.json")
    checker = load_module(
        QUALIFICATION / "candidate_b_reference_checker_v1.py",
        "candidate_b_reference_checker",
    )
    records = raw_records()

    def unit_for(source_uid: str) -> dict[str, Any]:
        record = records[source_uid]
        unit = checker.infer_unit_context(record["table"][0][0])
        if unit is None:
            raise ValueError(f"unit_context_missing:{source_uid}")
        return unit

    reserve_cases = (
        autopsy["same_number_role_scan"]["same_number_role_examples"]
        + autopsy["same_number_role_scan"]["same_delta_role_examples"]
    )
    development_cases = (
        autopsy["candidate_b_development_collision_scan"]["same_number_role_examples"]
        + autopsy["candidate_b_development_collision_scan"]["same_delta_role_examples"]
    )
    future_cases = (
        autopsy["candidate_b_future_collision_scan"]["same_number_role_examples"]
        + autopsy["candidate_b_future_collision_scan"]["same_delta_role_examples"]
    )
    dev_clusters = sorted({case["cluster_id"] for case in reserve_cases + development_cases})
    future_clusters = sorted({case["cluster_id"] for case in future_cases})
    if len(dev_clusters) < 5 or len(future_clusters) < 3:
        raise RuntimeError(f"exploratory_cluster_shortfall:{len(dev_clusters)}:{len(future_clusters)}")

    tasks = []
    references = []
    qualification_rows = []
    selected_pairs = []
    for scope, cases, clusters in (
        ("development", reserve_cases + development_cases, dev_clusters),
        ("exploratory_future", future_cases, future_clusters),
    ):
        for cluster_id in clusters:
            case, cluster_qualifications = choose_case(
                cases, cluster_id, unit_for
            )
            qualification_rows.extend(cluster_qualifications)
            if case is None:
                continue
            record = records[case["source_uid"]]
            for task_index, positive in ((1, True), (2, False)):
                actor_task, hidden = make_task(
                    case, record, checker, scope, task_index, positive
                )
                tasks.append(actor_task)
                references.append(hidden)
                selected_pairs.append(hidden["qualification"])

    source_rows = {}
    for cluster in source_exposure["clusters"]:
        source_rows[cluster["cluster_id"]] = {
            "cluster_id": cluster["cluster_id"],
            "effective_exposure_category": cluster["effective_exposure_category"],
            "evidence_class": cluster["evidence_class"],
            "existing_role": cluster["existing_role"],
        }
    qualified_pairs = [
        row for row in qualification_rows
        if row["status"] == "QUALIFIED_VISIBLE_ROLE_DIFFERENCE"
    ]
    unscorable_pairs = [
        row for row in qualification_rows
        if row["status"] == "UNSCORABLE_FOR_REFERENCE"
    ]
    human_review_pairs = [
        row for row in qualification_rows
        if row["status"] == "REQUIRES_HUMAN_SEMANTIC_ADJUDICATION"
    ]
    output = {
        "schema": "same_number_role_task_package_v1",
        "qualification_schema": "same_number_role_task_qualification_v2",
        "status": "EXPLORATORY_DEVELOPMENT_PACKAGE",
        "authorization": "MODEL_RUN_NOT_AUTHORIZED_YET",
        "qualification_rule": {
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
        },
        "development_cluster_ids": dev_clusters,
        "exploratory_future_cluster_ids": future_clusters,
        "counts": {
            "development_clusters": len(dev_clusters),
            "future_clusters": len(future_clusters),
            "development_tasks": sum(task["task_id"].startswith("NR_development") for task in tasks),
            "future_tasks": sum(task["task_id"].startswith("NR_exploratory_future") for task in tasks),
            "total_tasks": len(tasks),
            "qualified_negative_pairs": len(qualified_pairs),
            "unscorable_pairs": len(unscorable_pairs),
            "human_semantic_review_pairs": len(human_review_pairs),
        },
        "source_rows": source_rows,
        "tasks": tasks,
        "hidden_references": references,
        "selected_pair_qualifications": selected_pairs,
    }
    report = {
        "schema": "same_number_role_qualification_report_v2",
        "status": "QUALIFICATION_FIXED_NO_MODEL_REQUEST",
        "qualification_rule": output["qualification_rule"],
        "counts": output["counts"],
        "candidate_pair_qualifications": qualification_rows,
        "selected_pair_qualifications": selected_pairs,
        "excluded_from_model_tasks": unscorable_pairs + human_review_pairs,
    }
    write_json(output_dir / args.artifact_name, output)
    write_json(output_dir / args.qualification_report_name, report)
    print(json.dumps(output["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
