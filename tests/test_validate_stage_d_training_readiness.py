from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.validate_stage_d_training_readiness import ReadinessError, validate

CONFIG = Path(__file__).resolve().parents[1] / "docs" / "datasets" / "2026-10-05_stage_d_training_readiness_config_v1.json"


def _copy_config(tmp_path: Path, mutate) -> Path:
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    mutate(value)
    path = tmp_path / "config.json"
    path.write_text(json.dumps(value), encoding="utf-8", newline="\n")
    return path


def test_readiness_passes_but_training_stays_blocked() -> None:
    report = validate(CONFIG)
    assert report["status"] == "PASS_DRY_RUN_ONLY"
    assert report["training_execution_status"] == "BLOCKED_PENDING_MODEL_GO_DEPENDENCIES_AND_DATA_GATES"
    assert report["training_execution_authorized"] is False
    assert report["paper_result"] is False
    assert report["phase2_status"] == "NOT_RUN"
    assert report["training_status"] == "NOT_RUN"
    assert report["missing_dependencies"] == ["deepspeed", "peft", "trl"]


def test_authorized_training_is_rejected(tmp_path: Path) -> None:
    path = _copy_config(tmp_path, lambda value: value.update(training_execution_authorized=True))
    with pytest.raises(ReadinessError) as exc:
        validate(path)
    assert exc.value.code == "training_must_remain_unauthorized"


def test_changed_seed_list_is_rejected(tmp_path: Path) -> None:
    path = _copy_config(tmp_path, lambda value: value["arms"]["A2"].update(seed_list=[1]))
    with pytest.raises(ReadinessError) as exc:
        validate(path)
    assert exc.value.code == "seed_list_mismatch"


def test_gold_leakage_in_a2_filter_is_rejected(tmp_path: Path) -> None:
    def mutate(value):
        value["arms"]["A2"]["filter_forbidden_inputs"] = ["ground_truth", "source_gold", "final_correctness", "gain", "collateral", "gate_decision", "model_prediction", "gold"]

    path = _copy_config(tmp_path, mutate)
    with pytest.raises(ReadinessError) as exc:
        validate(path)
    assert exc.value.code == "a2_filter_forbidden_set_mismatch"


def test_estimate_must_be_unmeasured(tmp_path: Path) -> None:
    path = _copy_config(tmp_path, lambda value: value["planning_estimates"].update(measurement_status="MEASURED"))
    with pytest.raises(ReadinessError) as exc:
        validate(path)
    assert exc.value.code == "estimate_must_be_unmeasured"

def test_a3_must_not_inherit_a1_a2(tmp_path: Path) -> None:
    path = _copy_config(tmp_path, lambda value: value["arms"]["A3"].update(inherits_from_A1_A2=True))
    with pytest.raises(ReadinessError) as exc:
        validate(path)
    assert exc.value.code == "a3_must_not_inherit_a1_a2"


def test_a3_preference_distribution_gate_is_required(tmp_path: Path) -> None:
    def mutate(value):
        value["arms"]["A3"]["preference_gate"]["max_single_direction_share"] = 0.8

    path = _copy_config(tmp_path, mutate)
    with pytest.raises(ReadinessError) as exc:
        validate(path)
    assert exc.value.code == "a3_preference_gate_mismatch"


def test_phase2_budgets_cannot_change_after_results(tmp_path: Path) -> None:
    path = _copy_config(tmp_path, lambda value: value["phase2_initial_budget"].update(post_result_adjustment_allowed=True))
    with pytest.raises(ReadinessError) as exc:
        validate(path)
    assert exc.value.code == "post_result_adjustment_must_be_false"