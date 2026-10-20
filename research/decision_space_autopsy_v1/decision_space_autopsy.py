#!/usr/bin/env python3
"""Quantify prompt-disclosed decision space and same-number role collisions."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data/research/tatqa_raw_2026"
OLD_MANIFEST = (
    ROOT
    / "research/tatqa_wp0_2026/history_collection_execution_v1/pilot_prep_v1/"
    "PILOT_TASK_REFERENCE_MANIFEST_V2.json"
)
QUALIFICATION = ROOT / "research/tatqa_candidate_b_qualification_v1"


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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).strip()).casefold()


def load_checker():
    path = QUALIFICATION / "candidate_b_reference_checker_v1.py"
    spec = importlib.util.spec_from_file_location("candidate_b_checker", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("checker_import_failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_raw_records() -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for split in ("train", "dev"):
        path = RAW_DIR / f"tatqa_dataset_{split}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"raw_list_required:{path}")
        for index, item in enumerate(data):
            uid = item["table"]["uid"]
            if uid in records:
                raise ValueError(f"duplicate_raw_uid:{uid}")
            records[uid] = {
                "split": split,
                "index": index,
                "uid": uid,
                "table": item["table"]["table"],
            }
    return records


def year_columns(header: list[Any]) -> list[tuple[int, int]]:
    output = []
    for index, value in enumerate(header[1:], start=1):
        match = re.search(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)", str(value))
        if match:
            output.append((index, int(match.group(1))))
    return output


def old_panel_metrics(old_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in old_manifest["tasks"]:
        if item.get("bucket") != "future_test":
            continue
        task = item["actor_task"]["task"]
        table = item["actor_task"]["evidence"]["table_projection"]
        row_options = max(0, len(table) - 1)
        period_options = max(0, len(table[0]) - 1)
        rows.append(
            {
                "task_id": item["task_id"],
                "panel": "old_fixed_calculation",
                "target_row_supplied": True,
                "both_periods_supplied": True,
                "operation_supplied": task.get("requested_quantity") == "signed_difference",
                "unit_and_scale_supplied": all(
                    task.get(key) is not None
                    for key in ("source_unit", "target_unit", "scale_rule")
                ),
                "table_body_rows": row_options,
                "period_columns": period_options,
                "raw_row_period_column_choice_count": max(
                    1, row_options * period_options
                ),
                "raw_row_period_pair_choice_count": max(
                    1,
                    row_options
                    * (math.comb(period_options, 2) if period_options >= 2 else 1),
                ),
                "post_prompt_choice_count": 1,
                "post_prompt_choice_bits": 0.0,
            }
        )
    return rows


def candidate_b_metrics(
    tasks_doc: dict[str, Any],
    hidden_doc: dict[str, Any],
    checker: Any,
) -> list[dict[str, Any]]:
    references = {row["task_id"]: row for row in hidden_doc["references"]}
    rows = []
    for task in tasks_doc["tasks"]:
        reference = references[task["task_id"]]
        if reference["partition"] != "development":
            continue
        table = task["table"]
        header = table[0]
        body_labels = [normalized(row[0]) for row in table[1:]]
        target_row = normalized(reference["canonical_labels"]["row"])
        early = normalized(reference["canonical_labels"]["early_period"])
        late = normalized(reference["canonical_labels"]["late_period"])
        question = normalized(task["question"] + " " + task["instructions"])
        row_matches = sum(label == target_row for label in body_labels)
        period_columns = len(reference["distractors"]["period_indices"])
        raw_period_pairs = math.comb(period_columns, 2) if period_columns >= 2 else 1
        raw_choice_count = max(1, len(body_labels) * raw_period_pairs)
        row_disclosed = target_row in question
        periods_disclosed = early in question and late in question
        operation_disclosed = "calculate the change" in question or "how did" in question
        unit_context = checker.infer_unit_context(header[0])
        unit_unique = unit_context is not None
        post_choice_count = (
            1
            if row_disclosed
            and periods_disclosed
            and operation_disclosed
            and unit_unique
            else raw_choice_count
        )
        rows.append(
            {
                "task_id": task["task_id"],
                "panel": "candidate_b_evidence_binding",
                "partition": reference["partition"],
                "target_row_supplied": row_disclosed,
                "both_periods_supplied": periods_disclosed,
                "operation_supplied": operation_disclosed,
                "unit_and_scale_supplied": unit_unique,
                "target_row_exact_matches": row_matches,
                "table_body_rows": len(body_labels),
                "period_columns": period_columns,
                "raw_row_period_column_choice_count": max(
                    1, len(body_labels) * period_columns
                ),
                "raw_row_period_pair_choice_count": raw_choice_count,
                "post_prompt_choice_count": post_choice_count,
                "post_prompt_choice_bits": math.log2(post_choice_count),
            }
        )
    return rows


def same_number_role_scan(
    raw_records: dict[str, dict[str, Any]],
    source_exposure: dict[str, Any],
    selected_clusters: set[str],
    checker: Any,
    allowed_clusters: set[str] | None = None,
) -> dict[str, Any]:
    uid_to_cluster = {}
    eligible_clusters = {}
    for cluster in source_exposure["clusters"]:
        if allowed_clusters is not None and cluster["cluster_id"] not in allowed_clusters:
            continue
        if cluster["cluster_id"] in selected_clusters:
            continue
        if allowed_clusters is None and not cluster["eligible_new_candidate_pool"]:
            continue
        if cluster["evidence_class"] not in {"ID_SCAN_ONLY", "PROGRAMMATIC_ONLY"}:
            continue
        eligible_clusters[cluster["cluster_id"]] = cluster
        for uid in cluster["members"]:
            uid_to_cluster[uid] = cluster["cluster_id"]

    value_cases = []
    delta_cases = []
    eligible_records = 0
    for uid, cluster_id in uid_to_cluster.items():
        record = raw_records.get(uid)
        if record is None:
            continue
        table = record["table"]
        if len(table) < 3 or len(table[0]) < 3:
            continue
        header = table[0]
        if checker.infer_unit_context(header[0]) is None:
            continue
        eligible_records += 1
        period_columns = year_columns(header)
        values_by_number: dict[Decimal, list[dict[str, Any]]] = defaultdict(list)
        row_values: dict[int, dict[int, Decimal]] = defaultdict(dict)
        for row_index, row in enumerate(table[1:], start=1):
            row_label = normalized(row[0])
            if not row_label:
                continue
            for col_index, year in period_columns:
                value = checker.parse_decimal(row[col_index])
                if value is None:
                    continue
                role = {
                    "row_label": row[0],
                    "row_index": row_index,
                    "period_label": header[col_index],
                    "period_index": col_index,
                    "year": year,
                    "value": str(value),
                }
                values_by_number[value].append(role)
                row_values[row_index][col_index] = value

        for value, roles in values_by_number.items():
            distinct_roles = {
                (role["row_index"], role["period_index"]) for role in roles
            }
            distinct_rows = {role["row_index"] for role in roles}
            distinct_periods = {role["period_index"] for role in roles}
            if len(distinct_roles) >= 2 and (len(distinct_rows) >= 2 or len(distinct_periods) >= 2):
                value_cases.append(
                    {
                        "cluster_id": cluster_id,
                        "source_uid": uid,
                        "raw_split": record["split"],
                        "raw_index": record["index"],
                        "normalized_value": str(value),
                        "roles": roles,
                    }
                )

        all_delta_roles: dict[Decimal, list[dict[str, Any]]] = defaultdict(list)
        for left in range(len(period_columns)):
            for right in range(left + 1, len(period_columns)):
                early_col, early_year = period_columns[left]
                late_col, late_year = period_columns[right]
                for row_index, values in row_values.items():
                    if early_col not in values or late_col not in values:
                        continue
                    delta = values[late_col] - values[early_col]
                    row = table[row_index]
                    all_delta_roles[delta].append(
                        {
                            "row_label": row[0],
                            "row_index": row_index,
                            "early_period": header[early_col],
                            "late_period": header[late_col],
                            "delta": str(delta),
                        }
                    )
        for delta, roles in all_delta_roles.items():
            distinct_roles = {
                (
                    role["row_index"],
                    role["early_period"],
                    role["late_period"],
                )
                for role in roles
            }
            if len(distinct_roles) >= 2:
                delta_cases.append(
                    {
                        "cluster_id": cluster_id,
                        "source_uid": uid,
                        "raw_split": record["split"],
                        "raw_index": record["index"],
                        "normalized_delta": str(delta),
                        "roles": roles,
                    }
                )

    return {
        "eligible_cluster_count": len(eligible_clusters),
        "eligible_record_count": eligible_records,
        "same_number_role_case_count": len(value_cases),
        "same_number_role_cluster_count": len({row["cluster_id"] for row in value_cases}),
        "same_delta_role_case_count": len(delta_cases),
        "same_delta_role_cluster_count": len({row["cluster_id"] for row in delta_cases}),
        "same_number_role_examples": value_cases[:20],
        "same_delta_role_examples": delta_cases[:20],
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "tasks": len(rows),
        "target_row_supplied": sum(row["target_row_supplied"] for row in rows),
        "both_periods_supplied": sum(row["both_periods_supplied"] for row in rows),
        "operation_supplied": sum(row["operation_supplied"] for row in rows),
        "unit_and_scale_supplied": sum(row["unit_and_scale_supplied"] for row in rows),
        "single_choice_after_prompt": sum(
            row["post_prompt_choice_count"] == 1 for row in rows
        ),
        "mean_raw_row_period_column_choice_count": round(
            sum(row["raw_row_period_column_choice_count"] for row in rows) / len(rows),
            3,
        ),
        "mean_raw_row_period_pair_choice_count": round(
            sum(row["raw_row_period_pair_choice_count"] for row in rows) / len(rows),
            3,
        ),
        "mean_post_prompt_choice_count": round(
            sum(row["post_prompt_choice_count"] for row in rows) / len(rows), 3
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    checker = load_checker()
    raw_records = load_raw_records()
    old_manifest = load_json(OLD_MANIFEST)
    tasks_doc = load_json(QUALIFICATION / "CANDIDATE_B_TASKS_DRAFT.json")
    hidden_doc = load_json(QUALIFICATION / "HIDDEN_REFERENCE_MANIFEST.json")
    source_exposure = load_json(QUALIFICATION / "SOURCE_EXPOSURE_QUALIFICATION.json")

    old_rows = old_panel_metrics(old_manifest)
    candidate_rows = candidate_b_metrics(tasks_doc, hidden_doc, checker)
    selected_clusters = set(
        source_exposure["selection"]["development_cluster_ids"]
        + source_exposure["selection"]["future_validation_cluster_ids"]
    )
    collision_scan = same_number_role_scan(
        raw_records,
        source_exposure,
        selected_clusters,
        checker,
    )
    future_collision_scan = same_number_role_scan(
        raw_records,
        source_exposure,
        set(),
        checker,
        allowed_clusters=set(
            source_exposure["selection"]["future_validation_cluster_ids"]
        ),
    )
    development_collision_scan = same_number_role_scan(
        raw_records,
        source_exposure,
        set(),
        checker,
        allowed_clusters=set(
            source_exposure["selection"]["development_cluster_ids"]
        ),
    )
    history_collision_scan = same_number_role_scan(
        raw_records,
        source_exposure,
        set(),
        checker,
        allowed_clusters={
            cluster["cluster_id"]
            for cluster in source_exposure["clusters"]
            if cluster["existing_role"] == "history"
        },
    )

    result = {
        "schema": "decision_space_autopsy_v1",
        "status": "COMPLETE_NO_MODEL_REQUESTS",
        "model_or_judge_calls": 0,
        "input_hashes": {
            "old_manifest_sha256": sha256(OLD_MANIFEST),
            "candidate_tasks_sha256": sha256(QUALIFICATION / "CANDIDATE_B_TASKS_DRAFT.json"),
            "hidden_references_sha256": sha256(QUALIFICATION / "HIDDEN_REFERENCE_MANIFEST.json"),
            "source_exposure_sha256": sha256(QUALIFICATION / "SOURCE_EXPOSURE_QUALIFICATION.json"),
        },
        "old_panel": {
            "aggregate": aggregate(old_rows),
            "tasks": old_rows,
        },
        "candidate_b_panel": {
            "aggregate": aggregate(candidate_rows),
            "tasks": candidate_rows,
        },
        "same_number_role_scan": collision_scan,
        "candidate_b_future_collision_scan": future_collision_scan,
        "candidate_b_development_collision_scan": development_collision_scan,
        "history_collision_scan": history_collision_scan,
    }
    write_json(output_dir / "DECISION_SPACE_AUTOPSY.json", result)
    print(
        json.dumps(
            {
                "old_single_choice": result["old_panel"]["aggregate"][
                    "single_choice_after_prompt"
                ],
                "candidate_single_choice": result["candidate_b_panel"]["aggregate"][
                    "single_choice_after_prompt"
                ],
                "same_delta_clusters": collision_scan["same_delta_role_cluster_count"],
                "same_number_clusters": collision_scan[
                    "same_number_role_cluster_count"
                ],
                "future_same_delta_clusters": future_collision_scan[
                    "same_delta_role_cluster_count"
                ],
                "future_same_number_clusters": future_collision_scan[
                    "same_number_role_cluster_count"
                ],
                "development_same_delta_clusters": development_collision_scan[
                    "same_delta_role_cluster_count"
                ],
                "development_same_number_clusters": development_collision_scan[
                    "same_number_role_cluster_count"
                ],
                "history_same_delta_clusters": history_collision_scan[
                    "same_delta_role_cluster_count"
                ],
                "history_same_number_clusters": history_collision_scan[
                    "same_number_role_cluster_count"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
