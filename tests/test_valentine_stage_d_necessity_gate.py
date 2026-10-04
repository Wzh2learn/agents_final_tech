from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.valentine_stage_d_necessity_gate import GateError, evaluate


def _slice(harm: float, harm_upper: float, coverage: float) -> dict:
    return {
        "baselines": {
            "B3": {
                "harmful_map_rate": 0.18,
                "correct_map_coverage": 0.33,
            },
            "B4": {
                "harmful_map_rate": harm,
                "correct_map_coverage": coverage,
            },
        },
        "B3": {
            "harmful_map_rate": 0.18,
            "correct_map_coverage": 0.33,
        },
        "B4_cluster_bootstrap_95": {
            "harmful_map_rate": [0.03, harm_upper],
            "correct_map_coverage": [coverage - 0.05, coverage + 0.05],
        },
    }


def _write_results(path: Path, salted_harm: float, salted_upper: float) -> None:
    value = {
        "paper_result": False,
        "data_go": False,
        "primary_quarantine_loo": _slice(0.06, 0.09, 0.26),
        "pair_invalid_loo_sensitivity": {
            "B3": {"harmful_map_rate": 0.18, "correct_map_coverage": 0.34},
            "B4": {"harmful_map_rate": 0.06, "correct_map_coverage": 0.25},
            "B4_cluster_bootstrap_95": {
                "harmful_map_rate": [0.03, 0.09],
                "correct_map_coverage": [0.20, 0.30],
            },
        },
        "salted_split_sensitivity": {
            "B3": {"harmful_map_rate": 0.16, "correct_map_coverage": 0.37},
            "B4": {"harmful_map_rate": salted_harm, "correct_map_coverage": 0.32},
            "B4_cluster_bootstrap_95": {
                "harmful_map_rate": [0.09, salted_upper],
                "correct_map_coverage": [0.27, 0.38],
            },
        },
    }
    path.write_text(json.dumps(value), encoding="utf-8", newline="\n")


def test_unstable_sensitivity_is_pilot_only(tmp_path: Path) -> None:
    results = tmp_path / "results.json"
    _write_results(results, salted_harm=0.105, salted_upper=0.125)
    report = evaluate(results, 0.10)
    assert report["status"] == "PILOT_ONLY"
    assert report["stage_d_necessity"] == "NOT_ESTABLISHED"
    assert report["training_recommendation"] == "DO_NOT_TRAIN_YET"
    assert report["b4_risk_admissible_by_slice"] == {
        "primary": True,
        "pair_invalid": True,
        "salted": False,
    }


def test_stable_risk_still_requires_residual_rule(tmp_path: Path) -> None:
    results = tmp_path / "results.json"
    _write_results(results, salted_harm=0.08, salted_upper=0.09)
    report = evaluate(results, 0.10)
    assert report["status"] == "RESIDUAL_RULE_REQUIRED"
    assert report["training_recommendation"] == "DO_NOT_TRAIN_YET"


def test_non_exploratory_results_are_rejected(tmp_path: Path) -> None:
    results = tmp_path / "results.json"
    _write_results(results, salted_harm=0.08, salted_upper=0.09)
    value = json.loads(results.read_text())
    value["paper_result"] = True
    results.write_text(json.dumps(value), encoding="utf-8", newline="\n")
    with pytest.raises(GateError) as exc:
        evaluate(results, 0.10)
    assert exc.value.code == "results_must_remain_exploratory"
