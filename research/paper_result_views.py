#!/usr/bin/env python3
"""Build schema-stable paper table/figure views from accepted result shapes.

This module performs no experiment and never promotes an artifact to a paper
result.  It only converts the Phase 2 aggregate report into stable interfaces
for Table 2 and Figure 4.  Publication approval remains an external gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from research.phase2_rule_gate_replay import ARMS, REPORT_VERSION, _stable_bytes


VIEW_VERSION = "paper-result-views-v1"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _metric(metrics: dict[str, object], name: str) -> int | float | None:
    value = metrics.get(name)
    if value is not None and type(value) not in (int, float):
        raise ValueError(f"metric {name} must be numeric or null")
    return value


def build_phase2_views(report: object) -> dict[str, object]:
    if not isinstance(report, dict):
        raise ValueError("Phase 2 report must be an object")
    if set(report) != {"meta", "hashes", "support", "arms"}:
        raise ValueError("Phase 2 report has an unknown or incomplete top-level shape")
    meta = report["meta"]
    arms = report["arms"]
    if not isinstance(meta, dict) or meta.get("contract_version") != REPORT_VERSION:
        raise ValueError("unsupported Phase 2 report contract")
    if meta.get("paper_result") is not False:
        raise ValueError("repository view builder only accepts unpromoted reports")
    if not isinstance(arms, dict) or tuple(arms) != ARMS:
        raise ValueError("Phase 2 report must contain the ordered seven-arm matrix")

    table_rows: list[dict[str, object]] = []
    figure_rows: list[dict[str, object]] = []
    order_hashes: set[object] = set()
    expected_steps: list[int] | None = None
    for arm in ARMS:
        arm_report = arms[arm]
        if not isinstance(arm_report, dict) or set(arm_report) != {
            "events", "metrics", "final_state_sha256", "processed_order_sha256"
        }:
            raise ValueError(f"arm {arm} has an invalid report shape")
        order_hashes.add(arm_report["processed_order_sha256"])
        metrics = arm_report["metrics"]
        events = arm_report["events"]
        if not isinstance(metrics, dict) or not isinstance(events, list):
            raise ValueError(f"arm {arm} metrics/events must be structured")
        steps = [event.get("step") for event in events if isinstance(event, dict)]
        if len(steps) != len(events) or steps != list(range(1, len(events) + 1)):
            raise ValueError(f"arm {arm} has a non-contiguous event sequence")
        if expected_steps is None:
            expected_steps = steps
        elif steps != expected_steps:
            raise ValueError("seven arms do not expose the same candidate sequence length")
        table_rows.append({
            "arm": arm,
            "harmful_accept_rate": _metric(metrics, "harmful_accept_rate"),
            "valid_rule_retention": _metric(metrics, "valid_rule_retention"),
            "gate_coverage": _metric(metrics, "gate_coverage"),
            "gate_accuracy": _metric(metrics, "gate_accuracy"),
            "gate_utility": _metric(metrics, "gate_utility"),
            "worst_family": metrics.get("worst_family"),
            "validation_queries": _metric(metrics, "validation_queries"),
            "rollbacks": _metric(metrics, "rollbacks"),
            "cumulative_cost_proxy": _metric(metrics, "cumulative_cost_proxy"),
        })
        for event in events:
            assert isinstance(event, dict)
            figure_rows.append({
                "arm": arm,
                "step": event["step"],
                "retained_rules": event["retained_rules"],
                "retained_valid_rules": event["retained_valid_rules"],
                "retained_harmful_rules": event["retained_harmful_rules"],
                "cumulative_rollbacks": event["cumulative_rollbacks"],
                "cumulative_cost_proxy": event["cumulative_cost_proxy"],
            })
    if len(order_hashes) != 1 or next(iter(order_hashes)) != report["hashes"].get(
        "candidate_order_sha256"
    ):
        raise ValueError("candidate order hashes are inconsistent")

    source_sha = _sha256_bytes(_stable_bytes(report))
    common = {
        "contract_version": VIEW_VERSION,
        "source_report_sha256": source_sha,
        "paper_result": False,
        "watermark": "NOT_FOR_PAPER_UNTIL_INDEPENDENT_GB10_ACCEPTANCE",
    }
    return {
        "manifest": {
            **common,
            "interfaces": ["table_2_gate_baselines", "figure_4_rule_dynamics"],
        },
        "table_2_gate_baselines": {
            **common,
            "unit": "candidate-level gates; table-level final evaluation",
            "rows": table_rows,
        },
        "figure_4_rule_dynamics": {
            **common,
            "x": "shared_candidate_step",
            "series": figure_rows,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase2-report", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        report = json.loads(args.phase2_report.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("cannot read strict Phase 2 report JSON") from exc
    views = build_phase2_views(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.output.open("xb") as handle:
            handle.write(_stable_bytes(views))
    except FileExistsError as exc:
        raise ValueError("refusing to overwrite existing paper-result views") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
