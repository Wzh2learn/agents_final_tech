"""Compare natural-program arms with source-cluster uncertainty."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSONL rows."""
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def task_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compute per-task natural-program outcomes."""
    grouped: dict[tuple[str, str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped[(row["model_arm"], row["slice"], row["source_task_id"])][row["variant"]] = row
    output = []
    for (arm, slice_name, task_id), variants in sorted(grouped.items()):
        if {"original", "relevant_change", "irrelevant_change"} - set(variants):
            continue
        original = variants["original"]
        relevant = variants["relevant_change"]
        irrelevant = variants["irrelevant_change"]
        output.append({
            "model_arm": arm,
            "slice": slice_name,
            "source_task_id": task_id,
            "table_uid": original["table_uid"],
            "original_correct": bool(original["program_correct"]),
            "relevant_correct": bool(relevant["program_correct"]),
            "irrelevant_correct": bool(irrelevant["program_correct"]),
            "relevant_adaptation": bool(original["program_correct"] and relevant["program_correct"]),
            "irrelevant_invariance": bool(original["program_correct"] and irrelevant["program_correct"]),
            "paired_all_three": bool(
                original["program_correct"]
                and relevant["program_correct"]
                and irrelevant["program_correct"]
            ),
        })
    return output


def rate(rows: list[dict[str, Any]], key: str) -> float:
    """Compute task-equal rate."""
    return sum(float(row[key]) for row in rows) / len(rows) if rows else 0.0


def bootstrap_difference(
    left: list[dict[str, Any]],
    right: list[dict[str, Any]],
    key: str,
    repetitions: int = 5000,
) -> dict[str, Any]:
    """Bootstrap arm difference by table UID."""
    left_map = {row["source_task_id"]: row for row in left}
    right_map = {row["source_task_id"]: row for row in right}
    common = sorted(set(left_map) & set(right_map))
    by_cluster: dict[str, list[float]] = defaultdict(list)
    for task_id in common:
        by_cluster[left_map[task_id]["table_uid"]].append(
            float(left_map[task_id][key]) - float(right_map[task_id][key])
        )
    clusters = sorted(by_cluster)
    observed = sum(
        sum(values) / len(values) for values in by_cluster.values()
    ) / len(clusters)
    rng = random.Random(20261024)
    samples = []
    for _ in range(repetitions):
        selected = [rng.choice(clusters) for _ in clusters]
        samples.append(sum(
            sum(by_cluster[cluster]) / len(by_cluster[cluster])
            for cluster in selected
        ) / len(selected))
    samples.sort()
    return {
        "metric": key,
        "left_minus_right": observed,
        "ci95": [samples[int(0.025 * repetitions)], samples[int(0.975 * repetitions)]],
        "table_clusters": len(clusters),
        "paired_tasks": len(common),
    }


def main() -> int:
    """Write source-cluster arm comparison."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = task_rows(load_jsonl(args.results))
    arms = sorted({row["model_arm"] for row in rows})
    metrics: dict[str, Any] = {}
    for arm in arms:
        metrics[arm] = {}
        for slice_name in ("dev", "test", "external"):
            subset = [row for row in rows if row["model_arm"] == arm and row["slice"] == slice_name]
            metrics[arm][slice_name] = {
                "tasks": len(subset),
                "original_correct_rate": rate(subset, "original_correct"),
                "relevant_adaptation_rate": rate(subset, "relevant_adaptation"),
                "irrelevant_invariance_rate": rate(subset, "irrelevant_invariance"),
                "paired_all_three_rate": rate(subset, "paired_all_three"),
            }
    comparisons = {}
    for slice_name in ("test", "external"):
        ordinary = [row for row in rows if row["model_arm"] == "ordinary_answer_execution_sft" and row["slice"] == slice_name]
        visible = [row for row in rows if row["model_arm"] == "visible_program_filter_sft" and row["slice"] == slice_name]
        comparisons[slice_name] = {
            key: bootstrap_difference(ordinary, visible, key)
            for key in ("original_correct", "relevant_adaptation", "irrelevant_invariance", "paired_all_three")
        }
    output = {
        "schema": "natural_program_arm_comparison_v2",
        "date": "2026-10-24",
        "identity": "POST_HOC_SOURCE_CLUSTER_COMPARISON_OF_FROZEN_GENERATIONS",
        "metrics": metrics,
        "ordinary_minus_visible": comparisons,
        "new_model_calls": 0,
    }
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

