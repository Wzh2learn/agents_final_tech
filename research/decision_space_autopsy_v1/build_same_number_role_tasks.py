#!/usr/bin/env python3
"""Build exploratory same-number/same-delta role-binding tasks."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
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
        newline="\n",
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


def choose_case(cases: list[dict[str, Any]], cluster_id: str) -> dict[str, Any] | None:
    cluster_cases = [case for case in cases if case["cluster_id"] == cluster_id]
    for case in cluster_cases:
        roles = case["roles"]
        if len(roles) >= 2 and normalized(roles[0].get("row_label")) != normalized(roles[1].get("row_label")):
            return case
    return cluster_cases[0] if cluster_cases else None


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
        claim_kind = "signed_delta"
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
        }
        candidate_citation = {
            "row_label": candidate["row_label"],
            "early_period": candidate["early_period"],
            "late_period": candidate["late_period"],
        }
    else:
        claim_kind = "cell_value"
        claim_value = float(case["normalized_value"])
        expected_expression = str(claim_value)
        requested_role = {
            "row_label": target["row_label"],
            "period": target["period_label"],
        }
        candidate_citation = {
            "row_label": candidate["row_label"],
            "period": candidate["period_label"],
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
            f"{claim_kind.replace('_', ' ')}?"
        ),
        "table": table,
        "claim": {
            "kind": claim_kind,
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
    }
    return actor_task, hidden


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
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
    for scope, cases, clusters in (
        ("development", reserve_cases + development_cases, dev_clusters),
        ("exploratory_future", future_cases, future_clusters),
    ):
        for cluster_id in clusters:
            case = choose_case(cases, cluster_id)
            if case is None:
                raise RuntimeError(f"collision_case_missing:{cluster_id}")
            record = records[case["source_uid"]]
            for task_index, positive in ((1, True), (2, False)):
                actor_task, hidden = make_task(
                    case, record, checker, scope, task_index, positive
                )
                tasks.append(actor_task)
                references.append(hidden)

    source_rows = {}
    for cluster in source_exposure["clusters"]:
        source_rows[cluster["cluster_id"]] = {
            "cluster_id": cluster["cluster_id"],
            "effective_exposure_category": cluster["effective_exposure_category"],
            "evidence_class": cluster["evidence_class"],
            "existing_role": cluster["existing_role"],
        }
    output = {
        "schema": "same_number_role_task_package_v1",
        "status": "EXPLORATORY_DEVELOPMENT_PACKAGE",
        "authorization": "MODEL_RUN_NOT_AUTHORIZED_YET",
        "development_cluster_ids": dev_clusters,
        "exploratory_future_cluster_ids": future_clusters,
        "counts": {
            "development_clusters": len(dev_clusters),
            "future_clusters": len(future_clusters),
            "development_tasks": sum(task["task_id"].startswith("NR_development") for task in tasks),
            "future_tasks": sum(task["task_id"].startswith("NR_exploratory_future") for task in tasks),
            "total_tasks": len(tasks),
        },
        "source_rows": source_rows,
        "tasks": tasks,
        "hidden_references": references,
    }
    write_json(output_dir / "SAME_NUMBER_ROLE_TASKS_DRAFT.json", output)
    print(json.dumps(output["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
