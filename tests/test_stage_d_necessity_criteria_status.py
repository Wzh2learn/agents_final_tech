from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_stage_d_necessity_criteria_status_is_bound_to_authoritative_inputs() -> None:
    status = _load("docs/datasets/2026-10-05_stage_d_necessity_criteria_status_v1.json")
    config = _load("docs/datasets/2026-10-05_stage_d_training_readiness_config_v1.json")
    results = _load("docs/datasets/2026-10-04_b0_b4_exploratory_results_v2.json")
    gate = _load("docs/datasets/2026-10-05_stage_d_necessity_gate_v1.json")

    approved = config["stage_d_necessity_thresholds"]
    criteria = status["criteria"]
    assert status["criteria_status"] == "APPROVED_INITIAL_VALUES"
    assert status["status"] == "PILOT_ONLY"
    assert status["stage_d_necessity"] == "NOT_ESTABLISHED"
    assert status["data_go"] is False
    assert status["rq2_status"] == "NOT_IDENTIFIED"

    assert criteria["minimum_A2_absolute_correct_map_coverage_gain"]["value"] == approved["minimum_A2_absolute_correct_map_coverage_gain"]
    assert criteria["target_exact_noninferiority_margin"]["value"] == approved["target_exact_noninferiority_margin"]
    assert criteria["maximum_single_pair_residual_or_gain_share"]["value"] == approved["maximum_single_pair_gain_share"]
    assert criteria["minimum_A2_absolute_correct_map_coverage_gain"]["current_status"] == "NOT_ESTIMABLE"
    assert criteria["target_exact_noninferiority_margin"]["current_status"] == "NOT_ESTIMABLE"
    assert criteria["A2_minus_B4_coverage_delta_lower_primary_and_pair_invalid"]["current_status"] == "NOT_ESTIMABLE"

    risk = criteria["harmful_map_risk_upper_all_slices"]
    assert risk["value"] == gate["risk_limit"]
    assert risk["primary_upper"] == gate["slices"]["primary"]["B4"]["harmful_map_rate_ci95"][1]
    assert risk["pair_invalid_upper"] == gate["slices"]["pair_invalid"]["B4"]["harmful_map_rate_ci95"][1]
    assert risk["salted_upper"] == gate["slices"]["salted"]["B4"]["harmful_map_rate_ci95"][1]
    assert risk["current_status"] == "FAIL"

    residual = criteria["maximum_single_pair_residual_or_gain_share"]
    assert round(residual["b4_residual_max_pair_count"] / residual["b4_residual_total_count"], 10) == residual["b4_residual_max_pair_share"]
    assert residual["a2_gain_share"] == "NOT_ESTIMABLE"

    coverage = status["risk_constrained_B4_coverage"]
    assert coverage["primary"]["coverage"] == results["primary_quarantine_loo"]["baselines"]["B4"]["correct_map_coverage"]
    assert coverage["pair_invalid"]["coverage"] == results["pair_invalid_loo_sensitivity"]["B4"]["correct_map_coverage"]
    assert coverage["salted"]["coverage"] == results["salted_split_sensitivity"]["B4"]["correct_map_coverage"]
    assert coverage["stable_cross_slice_coverage"] is False
