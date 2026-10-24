"""Focused tests for natural program candidate feedback and variants."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "feedback_learning_finance_20261024_v2"),
)

from build_natural_tasks_v2 import build_task
from run_natural_program_experiment_v2 import (
    candidate_pool,
    make_variants,
    rendered_values,
    visible_filter,
)


def natural_task() -> dict[str, object]:
    """Build one deterministic natural task fixture."""
    record = {
        "table": {
            "uid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "table": [
                ["", "2020", "2019"],
                ["Revenue", "110", "100"],
                ["Cost", "50", "40"],
            ],
        },
        "paragraphs": [],
        "questions": [
            {
                "uid": "11111111-2222-3333-4444-555555555555",
                "question": "What is the change in Revenue between 2019 and 2020?",
                "answer": [10],
                "derivation": "110 - 100",
                "answer_type": "arithmetic",
                "answer_from": "table",
                "rel_paragraphs": [],
                "scale": "",
            }
        ],
    }
    return build_task(record, 0, "train", record["questions"][0])


def test_visible_filter_uses_program_shape_not_hidden_answer() -> None:
    task = natural_task()
    candidates = {candidate["candidate_id"]: candidate for candidate in candidate_pool(task)}
    assert candidates["gold"]["hidden_answer_pass"] is True
    assert visible_filter(task, candidates["gold"]["target"]) is True
    wrong_op = candidates["wrong_operator"]["target"]
    assert visible_filter(task, wrong_op) is False


def test_relevant_and_irrelevant_variants_keep_the_same_program() -> None:
    task = natural_task()
    variants = {variant["variant"]: variant for variant in make_variants(task)}
    assert set(variants) == {"original", "relevant_change", "irrelevant_change"}
    assert variants["irrelevant_change"]["expected"]["answer"] == task["expected"]["answer"]
    assert variants["relevant_change"]["expected"]["answer"] != task["expected"]["answer"]
    assert variants["relevant_change"]["expected"]["program"] == task["expected"]["program"]


def test_rendered_values_accept_percent_and_parentheses() -> None:
    table = (
        "columns: C0= | C1=2020 | C2=2019\n"
        "R1 [Margin] C1=25.0% | C2=(20.0)%\n"
        "R2 [Revenue] C1=1,110 | C2=1,000"
    )
    values = rendered_values(table)
    assert values["R1:C1"] == 25.0
    assert values["R1:C2"] == -20.0
    assert values["R2:C1"] == 1110.0
