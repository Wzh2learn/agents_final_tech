"""Tests for natural TAT-QA program task construction."""

from __future__ import annotations

from build_natural_tasks_v2 import build_task, natural_rule_candidate
from natural_program_contract_v2 import execute_program, table_cells


def synthetic_record() -> dict[str, object]:
    """Return one TAT-QA-shaped record with a unique arithmetic derivation."""
    return {
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


def test_natural_task_executes_visible_refs() -> None:
    task = build_task(
        synthetic_record(),
        0,
        "train",
        synthetic_record()["questions"][0],
    )
    assert task is not None
    assert task["expected"]["answer"] == 10
    assert task["expected"]["evidence_refs"] == ["R1:C1", "R1:C2"]
    cells = table_cells(synthetic_record()["table"]["table"])
    assert execute_program(task["expected"]["program"], cells) == 10


def test_transparent_question_row_rule_solves_change_template() -> None:
    task = build_task(
        synthetic_record(),
        0,
        "train",
        synthetic_record()["questions"][0],
    )
    candidate = natural_rule_candidate(task)
    assert candidate is not None
    assert candidate["answer"] == 10
