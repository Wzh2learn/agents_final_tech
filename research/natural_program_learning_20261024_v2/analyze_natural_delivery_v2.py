"""Analyze delivery policies over frozen natural-program outputs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "feedback_learning_finance_20261024_v2"),
)

from delivery_policy_v2 import acceptance_metrics, fit_logistic_risk_policy


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSONL rows."""
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def extract_program_shape(text: str) -> str:
    """Extract a program root shape from generated text."""
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            value, _ = decoder.raw_decode(text[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "program" in value:
            program = value["program"]
            return str(program.get("op", "leaf")) if isinstance(program, dict) else "invalid"
    return "missing"


def features(row: dict[str, Any]) -> list[float]:
    """Return deployment-visible policy features."""
    shape = extract_program_shape(row["generated_text"])
    return [
        float(row["interface_valid"]),
        float(row["program_executable"]),
        float(row["refs_valid"]),
        1.0 if shape in {"add", "sub", "mul", "div"} else 0.0,
    ]


def strong_flags(rows: list[dict[str, Any]]) -> list[bool]:
    """Apply the transparent all-applicable-checks rule."""
    return [
        bool(row["interface_valid"] and row["program_executable"] and row["refs_valid"])
        for row in rows
    ]


def choose_threshold(
    rows: list[dict[str, Any]],
    probabilities: list[float],
    thresholds: list[float],
    strong: dict[str, Any],
) -> float | None:
    """Choose a risk threshold under the frozen dev constraint."""
    best_threshold = None
    best_coverage = -1.0
    for threshold in thresholds:
        flags = [value >= threshold for value in probabilities]
        metrics = acceptance_metrics(rows, flags)
        if metrics["accepted"] == 0:
            continue
        wrong = metrics["conditional_wrong_delivery_rate"]
        if wrong is None or wrong <= strong["conditional_wrong_delivery_rate"] + 0.01:
            if metrics["correct_delivery_coverage"] > best_coverage:
                best_threshold = threshold
                best_coverage = metrics["correct_delivery_coverage"]
    return best_threshold


def model_policy_analysis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Fit on dev and analyze held-out slices with no hidden policy features."""
    dev = [row for row in rows if row["slice"] == "dev"]
    strong_dev_flags = strong_flags(dev)
    strong_dev = acceptance_metrics(dev, strong_dev_flags)
    fit = fit_logistic_risk_policy(
        [features(row) for row in dev],
        [bool(row["program_correct"]) for row in dev],
        [0.5, 0.6, 0.7, 0.8, 0.9],
    )
    risk_threshold = None
    risk_fit_error = fit.error
    if fit.available:
        try:
            from sklearn.linear_model import LogisticRegression

            model = LogisticRegression(
                class_weight="balanced",
                max_iter=1000,
                random_state=20261024,
            )
            model.fit([features(row) for row in dev], [bool(row["program_correct"]) for row in dev])
            dev_probabilities = model.predict_proba([features(row) for row in dev])[:, 1]
            risk_threshold = choose_threshold(
                dev,
                list(dev_probabilities),
                [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95],
                strong_dev,
            )
        except Exception as exc:
            risk_fit_error = f"post_fit_failed:{exc!r}"
            model = None
    else:
        model = None
    output: dict[str, Any] = {
        "dev": {
            "strong_rule": strong_dev,
            "risk_fit_error": risk_fit_error,
            "risk_threshold": risk_threshold,
        },
        "held_out": {},
    }
    for slice_name in ("test", "external"):
        subset = [row for row in rows if row["slice"] == slice_name]
        policies = {
            "all_applicable_pass": strong_flags(subset),
            "always_unknown": [False for _ in subset],
        }
        if model is not None and risk_threshold is not None:
            probabilities = model.predict_proba([features(row) for row in subset])[:, 1]
            policies["risk_logistic"] = [value >= risk_threshold for value in probabilities]
        output["held_out"][slice_name] = {
            name: acceptance_metrics(subset, flags)
            for name, flags in policies.items()
        }
    return output


def main() -> int:
    """Write frozen-answer delivery analysis."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = load_jsonl(args.results)
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_model[row["model_arm"]].append(row)
    output = {
        "schema": "natural_program_delivery_analysis_v2",
        "date": "2026-10-24",
        "identity": "FROZEN_ANSWER_DEPLOYMENT_POLICY_REPLAY_WITH_HIDDEN_REFERENCE_FINAL_SCORING_ONLY",
        "models": {
            arm: model_policy_analysis(model_rows)
            for arm, model_rows in sorted(by_model.items())
        },
        "new_model_calls": 0,
        "new_training_runs": 0,
    }
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

