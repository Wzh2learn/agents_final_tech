"""Evaluate deployment checks on the frozen unseen-family confirmation outputs."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "feedback_learning_finance_20261024_v2"),
)

from delivery_policy_v2 import acceptance_metrics


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def strong_flags(rows: list[dict[str, Any]]) -> list[bool]:
    return [
        bool(row["interface_valid"] and row["program_executable"] and row["refs_valid"])
        for row in rows
    ]


def analyze(rows: list[dict[str, Any]]) -> dict[str, Any]:
    normalized = [
        {**row, "final_correct": bool(row["program_correct"])}
        for row in rows
    ]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in normalized:
        grouped[row["model_arm"]].append(row)
    models = {}
    for arm, subset in sorted(grouped.items()):
        policies = {
            "all_applicable_pass": strong_flags(subset),
            "always_accept": [True for _ in subset],
            "always_unknown": [False for _ in subset],
        }
        models[arm] = {
            "items": len(subset),
            "policies": {
                name: acceptance_metrics(subset, flags)
                for name, flags in policies.items()
            },
        }
    return {
        "schema": "natural_tatqa_confirmation_delivery_v3",
        "identity": "FROZEN_CONFIRMATION_DEPLOYMENT_CHECK_REPLAY_NO_POLICY_FIT",
        "models": models,
        "learned_policy": "NOT_APPLICABLE_NO_CONFIRMATION_DEV_CALIBRATION",
        "new_model_calls": 0,
        "new_training_runs": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = analyze(load_jsonl(args.results))
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
