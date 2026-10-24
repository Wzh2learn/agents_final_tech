"""Regression tests for corrected metrics and deployment-visible features."""

from __future__ import annotations

from copy import deepcopy

from audit_correction_v2 import pair_metrics
from deployable_tool_contract_v2 import (
    all_deployable_checks_pass,
    deployable_features,
    execute_program,
)
from delivery_policy_v2 import acceptance_metrics, fit_logistic_risk_policy


QUESTION = (
    "Scope: Revenue. From 2019 to 2020, what is the numeric change? "
    "Report the answer in reported units."
)
TABLE = (
    "columns: C0= | C1=2020 | C2=2019\n"
    "R1 [Revenue] C1=110 | C2=100\n"
    "R2 [Cost] C1=50 | C2=40"
)
CANDIDATE = {
    "operator": "difference",
    "evidence_refs": ["R1:C1", "R1:C2"],
    "requested_unit": "reported",
}


def test_tool_result_uses_current_visible_values_not_model_answer() -> None:
    assert execute_program(QUESTION, TABLE, CANDIDATE) == 10.0
    wrong_model_answer = {**CANDIDATE, "answer": 999}
    assert execute_program(QUESTION, TABLE, wrong_model_answer) == 10.0


def test_tool_pair_does_not_require_direct_answer_invariance() -> None:
    rows = []
    for variant, direct, tool in (
        ("original", 1.0, 10.0),
        ("relevant_change", 2.0, 12.0),
        ("irrelevant_change", 3.0, 10.0),
    ):
        rows.append(
            {
                "source_task_id": "task-1",
                "table_uid": "table-1",
                "variant": variant,
                "operator": "difference",
                "direct_value": direct,
                "direct_correct": False,
                "legacy_formula_correct": True,
                "tool_value": tool,
                "tool_result_correct": True,
                "visible_program_correct": True,
            }
        )
    metrics = pair_metrics(rows)
    assert metrics["current_table_tool_pair_count"] == 1
    assert metrics["deployment_contract_pair_count"] == 1
    assert metrics["direct_pair_count"] == 0


def test_hidden_reference_cannot_change_deployable_features() -> None:
    features_a = deployable_features(QUESTION, TABLE, CANDIDATE)
    expected_a = {"answer": 10, "evidence_refs": ["R1:C1", "R1:C2"], "unit": "reported"}
    expected_b = deepcopy(expected_a)
    expected_b["evidence_refs"] = ["R2:C1", "R2:C2"]
    expected_b["answer"] = -999
    features_b = deployable_features(QUESTION, TABLE, CANDIDATE)
    assert features_a == features_b
    assert all_deployable_checks_pass(features_a)
    assert expected_a != expected_b


def test_acceptance_and_retention_are_separate() -> None:
    rows = [
        {"final_correct": True},
        {"final_correct": False},
        {"final_correct": True},
    ]
    metrics = acceptance_metrics(rows, [True, False, False])
    assert metrics["accepted"] == 1
    assert metrics["acceptance_rate"] == 1 / 3
    assert metrics["retention_or_clarification_rate"] == 2 / 3
    assert metrics["conditional_wrong_delivery_rate"] == 0.0
    assert metrics["overall_wrong_delivery_rate"] == 0.0


def test_risk_fit_failure_is_not_gold_fallback() -> None:
    fit = fit_logistic_risk_policy([[0.0], [1.0]], [True, True], [0.5])
    assert fit.available is False
    assert fit.threshold is None
    assert "single_class_outcome" in fit.error

