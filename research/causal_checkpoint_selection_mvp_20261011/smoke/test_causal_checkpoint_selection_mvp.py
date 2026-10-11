from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "causal_checkpoint_selection_mvp.py"
SPEC = importlib.util.spec_from_file_location(
    "causal_checkpoint_selection_mvp_under_test", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
mvp = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mvp
SPEC.loader.exec_module(mvp)


def authoritative():
    return mvp.load_authoritative_inputs()


def test_authoritative_matrix_is_exactly_216_by_12_with_frozen_hashes():
    rows, paired_rows, inventory, hashes, shape = authoritative()
    assert len(rows) == 216
    assert len(paired_rows) == 216
    assert len(inventory) == 12
    assert len(rows[0]["response_vector"]) == 12
    assert shape["shape_status"] == "PASS_216_X_12"
    assert hashes == mvp.EXPECTED_INPUT_HASHES
    assert sorted(rows[0]["response_vector"]) == sorted(
        item.checkpoint_id for item in inventory
    )


def test_dev_only_overlay_builds_source_and_downstream_response_paths():
    rows, _, _, _, _ = authoritative()
    augmented = mvp.apply_dev_only_overlay(rows)
    assert all(
        row["dev_only_overlay"]["overlay_label"].startswith("DEV_ONLY")
        for row in augmented
    )
    assert mvp.overlay_counts(augmented) == {
        "rows": 216,
        "source_local_positive_rows": 216,
        "downstream_causal_positive_rows": 72,
        "source_local_positive_cells": 216,
        "downstream_causal_positive_cells": 72,
    }
    m_rows = [row for row in augmented if row["true_stage"] == "M"]
    r_rows = [row for row in augmented if row["true_stage"] == "R"]
    n_rows = [row for row in augmented if row["true_stage"] == "N"]
    assert all(
        row["dev_only_overlay"]["checkpoint_roles"]["parse.table.regression"]
        == "DOWNSTREAM_CAUSAL_RESPONSE"
        for row in m_rows
    )
    assert all(
        not row["dev_only_overlay"]["DOWNSTREAM_CAUSAL_RESPONSE"]
        for row in r_rows + n_rows
    )
    assert all(
        row["dev_only_overlay"]["raw_state_pre_hash"] == "NOT_IDENTIFIABLE"
        for row in augmented
    )


def test_hard_budgets_are_enforced_and_infeasible_all_checkpoints_is_unavailable():
    _, _, inventory, _, _ = authoritative()
    for check_budget, call_budget in mvp.SMOKE_BUDGETS:
        budget = mvp.Budget(check_budget, call_budget)
        assert mvp.all_checkpoints(inventory, budget).status == mvp.TERMINAL_STATUS
        assert mvp.random_k_select(inventory, budget, check_budget).selected_ids
        assert mvp.manual_default_stage_aligned(inventory, budget).selected_ids
    with pytest.raises(mvp.BudgetExceededError):
        mvp.assert_hard_budget(
            [item.checkpoint_id for item in inventory],
            mvp.Budget(4, 0),
            inventory,
        )


def test_all_baselines_have_deterministic_replay_and_fixed_seed():
    rows, paired_rows, inventory, hashes, shape = authoritative()
    first = mvp.build_result(rows, paired_rows, inventory, hashes, shape)
    second = mvp.build_result(rows, paired_rows, inventory, hashes, shape)
    assert first == second
    assert mvp.random_k_select(
        inventory, mvp.Budget(4, 0), 4
    ) == mvp.random_k_select(inventory, mvp.Budget(4, 0), 4)
    assert set(first["budget_results"][0]["baselines"]) == set(mvp.BASELINE_IDS)
    assert set(first["budget_results"][1]["baselines"]) == set(mvp.BASELINE_IDS)


def test_frozen_tie_rule_prefers_calls_then_inventory_order():
    inventory = [
        mvp.Checkpoint("z.checkpoint", "z", 1, 1, None),
        mvp.Checkpoint("a.checkpoint", "a", 1, 0, None),
        mvp.Checkpoint("b.checkpoint", "b", 1, 0, None),
    ]
    roles = {
        item.checkpoint_id: "DOWNSTREAM_CAUSAL_RESPONSE" for item in inventory
    }
    flags = {
        item.checkpoint_id: {
            "REACHED": 1,
            "INFECTED": 0,
            "PROPAGATED": 1,
            "REVEALED": 1,
        }
        for item in inventory
    }
    rows = [
        {
            "response_vector": {item.checkpoint_id: 1 for item in inventory},
            "dev_only_overlay": {
                "checkpoint_roles": roles,
                "ripr_flags": flags,
            },
        }
    ]
    selection = mvp.coverage_only_greedy(inventory, mvp.Budget(3, 1), rows)
    assert selection.selected_ids[0] == "a.checkpoint"
    assert selection.selected_ids[1] == "b.checkpoint"
    assert selection.selected_ids[2] == "z.checkpoint"


def test_nearest_centroid_tie_counts_as_failure():
    flags = {
        "x": {
            "REACHED": 0,
            "INFECTED": 0,
            "PROPAGATED": 0,
            "REVEALED": 0,
        }
    }
    rows = [
        {
            "response_vector": {"x": 0},
            "dev_only_overlay": {"ripr_flags": flags},
            "stage_label": label,
        }
        for label in ("A", "B")
    ]
    predictions = mvp.nearest_centroid_predict(
        rows, rows, ["x"], "stage_label", tie_failure=True
    )
    assert predictions == ["__TIE_FAILURE__", "__TIE_FAILURE__"]
    assert mvp.macro_f1(
        ["A", "B"], predictions, ["A", "B"]
    ) == 0.0


def test_stage_group_split_is_group_disjoint_and_not_available_for_mechanism_holdout():
    rows, _, _, _, _ = authoritative()
    augmented = mvp.apply_dev_only_overlay(rows)
    split = mvp.group_disjoint_split(augmented)
    train_rows, test_rows = mvp.split_rows(augmented, split)
    assert split["label"] == "DEV_ONLY_PSEUDO_FOLD"
    assert split["mechanism_holdout"] == "NOT_AVAILABLE"
    assert split["group_overlap"] == []
    assert not (
        {row["cluster_id"] for row in train_rows}
        & {row["cluster_id"] for row in test_rows}
    )
    assert {row["true_stage"] for row in train_rows} == {"M", "R", "N"}
    assert {row["true_stage"] for row in test_rows} == {"M", "R", "N"}
    assert len(train_rows) + len(test_rows) == 216


def test_result_schema_has_every_required_baseline_budget_count_and_metric():
    rows, paired_rows, inventory, hashes, shape = authoritative()
    result = mvp.build_result(rows, paired_rows, inventory, hashes, shape)
    assert result["required_fields_present"] is True
    assert result["receipt_label"] == "ALGORITHM_SMOKE_DEV_ONLY"
    assert result["scientific_claim"] == "ZERO"
    assert result["formal_experiment"] == "ZERO"
    assert result["mechanism_holdout"] == "NOT_AVAILABLE"
    assert [
        (budget["B_check"], budget["B_call"]) for budget in result["budget_results"]
    ] == [(4, 0), (8, 2)]
    assert result["overlay_counts"]["source_local_positive_rows"] == 216
    assert result["overlay_counts"]["downstream_causal_positive_rows"] == 72
    for budget_result in result["budget_results"]:
        assert set(budget_result["baselines"]) == set(mvp.BASELINE_IDS)
        for baseline in budget_result["baselines"].values():
            assert set(baseline) == set(mvp.REQUIRED_SELECTION_FIELDS)
            assert set(baseline["metrics"]) == set(mvp.METRIC_FIELDS)
            assert baseline["budget_usage"]["within_hard_budgets"] is True
            assert baseline["budget_usage"]["check_count"] <= budget_result["B_check"]
            assert (
                baseline["budget_usage"]["model_or_judge_calls"]
                <= budget_result["B_call"]
            )
            if baseline["availability"]:
                assert all(value is not None for value in baseline["metrics"].values())
        assert (
            budget_result["baselines"]["terminal-only"]["status"]
            == "NOT_AVAILABLE"
        )


def test_generated_manifest_result_and_receipt_are_exact_and_dev_only():
    rows, paired_rows, inventory, hashes, shape = authoritative()
    result = mvp.build_result(rows, paired_rows, inventory, hashes, shape)
    manifest = json.loads((HERE / "dev_smoke_input_manifest.json").read_text())
    generated_result = json.loads((HERE / "dev_smoke_result.json").read_text())
    generated_receipt = json.loads((HERE / "dev_smoke_receipt.json").read_text())
    assert manifest == mvp.input_manifest(hashes, shape, inventory)
    assert generated_result == result
    assert generated_receipt["receipt_label"] == "ALGORITHM_SMOKE_DEV_ONLY"
    assert generated_receipt["scientific_claim"] == "ZERO"
    assert generated_receipt["formal_experiment"] == "ZERO"
    assert generated_receipt["input_hashes"] == mvp.EXPECTED_INPUT_HASHES
    assert generated_receipt["new_scientific_dataset_rows"] == 0
    assert generated_receipt["endpoint_calls"] == 0
