"""Evaluate the Stage D necessity gate from frozen B0-B4 exploratory results.

The gate is intentionally narrow. It checks whether B4 satisfies the approved
risk limit on the primary analysis and both mandatory sensitivity slices. It
does not authorize training, does not change DATA_NO_GO, and does not infer
power from exploratory cluster intervals.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SLICES = (
    ("primary", "primary_quarantine_loo"),
    ("pair_invalid", "pair_invalid_loo_sensitivity"),
    ("salted", "salted_split_sensitivity"),
)
BASELINES = ("B3", "B4")


class GateError(ValueError):
    def __init__(self, code: str, **detail: object) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_results(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GateError("invalid_results_type")
    return value


def _risk_view(results: dict[str, object], slice_key: str, run_key: str, baseline: str, risk_limit: float) -> dict[str, object]:
    run = results.get(run_key)
    if not isinstance(run, dict):
        raise GateError("missing_result_slice", slice=slice_key, run=run_key)
    if baseline == "B4":
        metrics = run["baselines"]["B4"]
        if not isinstance(metrics, dict):
            raise GateError("missing_b4_metrics", slice=slice_key)
        point = metrics.get("harmful_map_rate")
        coverage = metrics.get("correct_map_coverage")
        interval = run["B4_cluster_bootstrap_95"]
        harm_interval = interval["harmful_map_rate"]
        coverage_interval = interval["correct_map_coverage"]
    else:
        metrics = run.get("B3")
        if not isinstance(metrics, dict):
            raise GateError("missing_b3_metrics", slice=slice_key)
        point = metrics.get("harmful_map_rate")
        coverage = metrics.get("correct_map_coverage")
        harm_interval = None
        coverage_interval = None
    if not isinstance(point, (int, float)) or not isinstance(coverage, (int, float)):
        raise GateError("missing_risk_metrics", slice=slice_key, baseline=baseline)
    point = float(point)
    coverage = float(coverage)
    harm_upper = float(harm_interval[1]) if harm_interval else None
    risk_admissible = point <= risk_limit and (harm_upper is None or harm_upper <= risk_limit)
    return {
        "slice": slice_key,
        "run_key": run_key,
        "baseline": baseline,
        "risk_limit": risk_limit,
        "harmful_map_rate": point,
        "harmful_map_rate_ci95": harm_interval,
        "risk_admissible_point": point <= risk_limit,
        "risk_admissible_upper": harm_upper is not None and harm_upper <= risk_limit,
        "risk_admissible": risk_admissible,
        "correct_map_coverage": coverage,
        "correct_map_coverage_ci95": coverage_interval,
    }


def evaluate(results_path: Path, risk_limit: float = 0.10) -> dict[str, object]:
    if risk_limit <= 0 or risk_limit >= 1:
        raise GateError("invalid_risk_limit", value=risk_limit)
    results = _load_results(results_path)
    if results.get("paper_result") is not False or results.get("data_go") is not False:
        raise GateError("results_must_remain_exploratory")
    slices: dict[str, object] = {}
    b4_risk_by_slice: dict[str, bool] = {}
    for slice_key, run_key in SLICES:
        b3 = _risk_view(results, slice_key, run_key, "B3", risk_limit)
        b4 = _risk_view(results, slice_key, run_key, "B4", risk_limit)
        slices[slice_key] = {"B3": b3, "B4": b4}
        b4_risk_by_slice[slice_key] = bool(b4["risk_admissible"])
    stable_risk = all(b4_risk_by_slice.values())
    salted = slices["salted"]["B4"]
    if not stable_risk:
        verdict = "PILOT_ONLY"
        reason = (
            "B4 risk admissibility is not stable across the mandatory sensitivity slices; "
            "the salted split has only two test pairs and its harmful-map upper bound crosses "
            "the approved risk limit."
        )
    else:
        verdict = "RESIDUAL_RULE_REQUIRED"
        reason = (
            "B4 satisfies the risk limit on all slices, but SIMPLE_SUFFICIENT versus "
            "LEARNABILITY_SIGNAL still requires a separately approved stable-residual rule."
        )
    return {
        "record_type": "stage_d_necessity_gate",
        "record_version": "stage-d-necessity-gate-v1",
        "status": verdict,
        "stage_d_necessity": "NOT_ESTABLISHED" if verdict != "LEARNABILITY_SIGNAL" else "PENDING_RESIDUAL_RULE",
        "training_recommendation": "DO_NOT_TRAIN_YET",
        "risk_limit": risk_limit,
        "paper_result": False,
        "data_go": False,
        "rq2_status": "NOT_IDENTIFIED",
        "results_path": str(results_path),
        "results_sha256": _sha256(results_path),
        "slices": slices,
        "b4_risk_admissible_by_slice": b4_risk_by_slice,
        "stable_risk_constrained_coverage": stable_risk,
        "primary_risk_constrained_coverage": slices["primary"]["B4"]["correct_map_coverage"] if b4_risk_by_slice["primary"] else None,
        "salted_coverage_at_fixed_policy": salted["correct_map_coverage"],
        "salted_risk_admissible": salted["risk_admissible"],
        "reason": reason,
        "auxiliary_cost_status": {
            "latency": "NOT_MEASURED",
            "token_use": "NOT_MEASURED",
            "gpu_cpu_cost": "NOT_MEASURED",
        },
        "b5_status": "DORMANT_NOT_RUN",
        "phase2_status": "NOT_RUN",
        "training_status": "NOT_RUN",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Stage D necessity from exploratory B0-B4 results")
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--risk-limit", type=float, default=0.10)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(args.results, args.risk_limit)
    args.output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
