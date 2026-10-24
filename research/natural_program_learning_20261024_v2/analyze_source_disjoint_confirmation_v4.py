"""Compute paired task metrics for a source-disjoint confirmation run."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def paired_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped[(row["model_arm"], row["source_task_id"])][row["variant"]] = row
    output = []
    for (arm, task_id), variants in sorted(grouped.items()):
        if {"original", "relevant_change", "irrelevant_change"} - set(variants):
            continue
        output.append({
            "model_arm": arm,
            "source_task_id": task_id,
            "table_uid": variants["original"]["table_uid"],
            "original_correct": bool(variants["original"]["program_correct"]),
            "relevant_adaptation": bool(
                variants["original"]["program_correct"]
                and variants["relevant_change"]["program_correct"]
            ),
            "irrelevant_invariance": bool(
                variants["original"]["program_correct"]
                and variants["irrelevant_change"]["program_correct"]
            ),
            "paired_all_three": bool(all(
                variants[name]["program_correct"]
                for name in ("original", "relevant_change", "irrelevant_change")
            )),
        })
    return output


def bootstrap_difference(
    rows: list[dict[str, Any]],
    left_arm: str,
    right_arm: str,
    key: str,
    repetitions: int = 5000,
) -> dict[str, Any]:
    left = {row["source_task_id"]: row for row in rows if row["model_arm"] == left_arm}
    right = {row["source_task_id"]: row for row in rows if row["model_arm"] == right_arm}
    common = sorted(set(left) & set(right))
    by_cluster: dict[str, list[float]] = defaultdict(list)
    for task_id in common:
        by_cluster[left[task_id]["table_uid"]].append(
            float(left[task_id][key]) - float(right[task_id][key])
        )
    clusters = sorted(by_cluster)
    observed = sum(sum(values) / len(values) for values in by_cluster.values()) / len(clusters)
    rng = random.Random(20261024)
    draws = []
    for _ in range(repetitions):
        selected = [rng.choice(clusters) for _ in clusters]
        draws.append(sum(
            sum(by_cluster[cluster]) / len(by_cluster[cluster])
            for cluster in selected
        ) / len(selected))
    draws.sort()
    return {
        "left": left_arm,
        "right": right_arm,
        "metric": key,
        "difference": observed,
        "ci95": [draws[int(0.025 * repetitions)], draws[int(0.975 * repetitions)]],
        "table_clusters": len(clusters),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = paired_rows(load_jsonl(args.results))
    metrics = {}
    for arm in sorted({row["model_arm"] for row in rows}):
        subset = [row for row in rows if row["model_arm"] == arm]
        metrics[arm] = {
            "tasks": len(subset),
            **{
                f"{key}_rate": sum(float(row[key]) for row in subset) / len(subset)
                for key in ("original_correct", "relevant_adaptation", "irrelevant_invariance", "paired_all_three")
            },
        }
    output = {
        "schema": "source_disjoint_confirmation_analysis_v4",
        "identity": "POST_HOC_TASK_CLUSTER_ANALYSIS_OF_FROZEN_SOURCE_DISJOINT_RESULTS",
        "metrics": metrics,
        "ordinary_minus_visible": {
            key: bootstrap_difference(
                rows,
                "ordinary_answer_execution_sft",
                "visible_program_filter_sft",
                key,
            )
            for key in ("original_correct", "relevant_adaptation", "irrelevant_invariance", "paired_all_three")
        },
        "new_model_calls": 0,
    }
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
