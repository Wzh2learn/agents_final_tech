"""Focused tests for the financial feedback-learning experiment core."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from feedback_learning_core import (
    build_tasks_from_records,
    canonical_target,
    choose_candidate,
    evaluate_prediction,
    formula_result,
    parse_numeric,
)


def synthetic_records() -> list[dict[str, object]]:
    """Return a small real-schema TAT-QA-like record."""
    return [
        {
            "table": {
                "uid": "11111111-2222-3333-4444-555555555555",
                "table": [
                    ["", "2020", "2019"],
                    ["Revenue", "110", "100"],
                    ["Revenue duplicate", "110", "100"],
                    ["Cost", "50", "40"],
                ],
            },
            "paragraphs": [],
            "questions": [],
        }
    ]


def test_parse_numeric_supports_financial_forms() -> None:
    assert parse_numeric("1,234.5") == 1234.5
    assert parse_numeric("(1,234)") == -1234.0
    assert parse_numeric("2.9%") == 2.9
    assert parse_numeric("N/A") is None


def test_formula_result_is_restricted_and_deterministic() -> None:
    assert formula_result("(110 - 100) / 100 * 100") == pytest.approx(10.0)
    assert formula_result(
        "R2:C1 - R2:C2",
        {"R2:C1": 110.0, "R2:C2": 100.0},
    ) == pytest.approx(10.0)
    with pytest.raises(ValueError):
        formula_result("__import__('os')")


def test_task_generation_and_feedback_filters() -> None:
    tasks = build_tasks_from_records(synthetic_records(), "train")
    assert tasks
    task = next(task for task in tasks if task["task_type"] == "difference")
    assert task["expected"]["evidence_refs"]
    assert task["variants"]["relevant_change"]["expected"]["answer"] != task["expected"]["answer"]
    assert task["variants"]["irrelevant_change"]["expected"]["answer"] == task["expected"]["answer"]

    by_id = {candidate["candidate_id"]: candidate for candidate in task["candidates"]}
    assert by_id["correct"]["checks"]["exact_evidence"] is True
    if "answer_correct_evidence_wrong" in by_id:
        candidate = by_id["answer_correct_evidence_wrong"]
        assert candidate["checks"]["calculation"] is True
        assert candidate["checks"]["exact_evidence"] is False
        assert choose_candidate(task, "evidence_dependency")["candidate_id"] == "correct"
        assert choose_candidate(task, "answer_execution")["candidate_id"] in {
            "answer_correct_evidence_wrong",
            "unit_error",
            "correct",
        }


def test_prediction_contract_accepts_correct_target_and_rejects_wrong_answer() -> None:
    tasks = build_tasks_from_records(synthetic_records(), "train")
    task = next(task for task in tasks if task["task_type"] == "difference")
    correct_text = canonical_target(task["expected"])
    scored = evaluate_prediction(
        correct_text,
        task,
        task["expected"],
    )
    assert scored["interface_valid"] is True
    assert scored["answer_correct"] is True
    assert scored["checks"]["exact_evidence"] is True

    wrong = dict(task["expected"])
    wrong["answer"] = float(task["expected"]["answer"]) + 1
    wrong_text = canonical_target(wrong)
    wrong_scored = evaluate_prediction(
        wrong_text,
        task,
        task["expected"],
    )
    assert wrong_scored["interface_valid"] is True
    assert wrong_scored["answer_correct"] is False


    prose_wrapped = "Reasoning first.\n" + correct_text + "\nTrailing explanation"
    diagnostic = evaluate_prediction(
        prose_wrapped,
        task,
        task["expected"],
    )
    assert diagnostic["interface_valid"] is False
    assert diagnostic["embedded_valid"] is True
    assert diagnostic["postprocess_recovered"] is True
    assert diagnostic["answer_correct"] is True
    assert diagnostic["strict_answer_correct"] is False

    symbolic = json.loads(correct_text)
    symbolic_formula = (
        f"{task['expected']['evidence_refs'][1]} - "
        f"{task['expected']['evidence_refs'][0]}"
    )
    symbolic["formula"] = symbolic_formula
    symbolic["answer"] = symbolic_formula
    symbolic_scored = evaluate_prediction(
        json.dumps(symbolic, separators=(",", ":")),
        task,
        task["expected"],
    )
    assert symbolic_scored["embedded_valid"] is True
    assert symbolic_scored["answer_correct"] is True
    assert symbolic_scored["checks"]["calculation"] is True
    assert symbolic_scored["interface_valid"] is False


def test_zero_prior_corrupt_candidate_is_skipped() -> None:
    records = synthetic_records()
    records[0]["table"]["table"] = [
        ["", "2020", "2019"],
        ["Revenue", "110", "100"],
        ["Zero prior", "50", "0"],
    ]
    tasks = build_tasks_from_records(records, "train")
    percent_tasks = [task for task in tasks if task["task_type"] == "percent_change"]
    assert percent_tasks
    assert all(
        candidate["candidate_id"] != "wrong_period"
        or float(candidate["target"]["answer"]) == float(candidate["target"]["answer"])
        for task in percent_tasks
        for candidate in task["candidates"]
    )


def test_protocol_freeze_and_budget_are_machine_readable() -> None:
    protocol_path = Path(__file__).with_name("EXPERIMENT_PROTOCOL.json")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    assert protocol["status"] == "FROZEN_BEFORE_MODEL_GENERATION_AND_TRAINING"
    assert protocol["resource_budget"]["accounting_attempt_cap_for_this_experiment"] == 960
    assert protocol["C3_delivery"]["strong_rule"]
    assert protocol["evaluation"]["statistical_unit"] == "TAT-QA table UID"
