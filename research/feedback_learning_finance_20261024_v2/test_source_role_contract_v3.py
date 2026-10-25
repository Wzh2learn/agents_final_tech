"""Regression tests for source isolation and constant-role classification."""

from __future__ import annotations

import pytest

from source_role_contract_v3 import (
    assert_role_disjoint,
    classify_average_denominator,
    select_source_disjoint_tasks,
)


def make_task(task_id: str, table_uid: str) -> dict[str, object]:
    return {"task_id": task_id, "question_uid": task_id, "table_uid": table_uid}


def test_same_table_different_questions_cannot_cross_roles() -> None:
    one = make_task("q1", "table-1")
    two = make_task("q2", "table-1")
    with pytest.raises(ValueError, match="source_role_overlap"):
        assert_role_disjoint({"train": [one], "confirmation": [two]})


def test_selection_excludes_all_source_keys() -> None:
    tasks = [
        make_task("q1", "table-1"),
        make_task("q2", "table-2"),
        make_task("q3", "table-3"),
    ]
    selected = select_source_disjoint_tasks(
        tasks,
        excluded_task_ids=["q1"],
        excluded_source_keys=[("table_uid", "table-2")],
        count=1,
    )
    assert selected[0]["task_id"] == "q3"


def test_average_count_can_be_structural_not_evidence() -> None:
    label = classify_average_denominator(
        "What is the average revenue in 2018 and 2019?",
        {"ref": "R9:C2"},
        {"value": 2, "row_label": "Other, net", "column_label": ""},
    )
    assert label == "STRUCTURAL_CONSTANT_MISBOUND"


def test_semantically_named_denominator_is_not_forced_constant() -> None:
    label = classify_average_denominator(
        "What is the average estimated fair value of Customer relationships?",
        {"ref": "R4:C2"},
        {"value": 7, "row_label": "Customer relationships", "column_label": "Estimated Useful Life"},
        {"ref": "R4:C1"},
    )
    assert label == "LEGAL_FINANCIAL_DENOMINATOR"


def test_single_year_average_over_two_operands_is_unresolved() -> None:
    label = classify_average_denominator(
        "What is the 2018 average actuarial losses recognised in the SOCI?",
        {"ref": "R2:C2"},
        {"value": 2, "row_label": "Past service costs", "column_label": "2018"},
        {"op": "add", "left": {"ref": "R5:C2"}, "right": {"ref": "R5:C3"}},
    )
    assert label == "UNRESOLVED_REFERENCE_QUESTION_MISMATCH"


def test_non_average_ratio_does_not_convert_denominator() -> None:
    label = classify_average_denominator(
        "What is the ratio of revenue in 2020 to revenue in 2021?",
        {"ref": "R1:C2"},
        {"value": 2, "row_label": "Revenue", "column_label": "2021"},
        {"ref": "R1:C1"},
    )
    assert label == "NON_AVERAGE_DENOMINATOR"


def test_from_to_average_counts_inclusive_years() -> None:
    label = classify_average_denominator(
        "What is the average revenue from 2018 to 2020?",
        {"ref": "R9:C1"},
        {"value": 3, "row_label": "Other", "column_label": ""},
        {"op": "add", "left": {"ref": "R1:C1"}, "right": {"ref": "R1:C2"}},
    )
    assert label == "STRUCTURAL_CONSTANT_MISBOUND"


def test_existing_structural_constant_is_idempotent() -> None:
    label = classify_average_denominator(
        "What is the average revenue in 2018 and 2019?",
        {"const": 2},
        None,
        {"op": "add", "left": {"ref": "R1:C1"}, "right": {"ref": "R1:C2"}},
    )
    assert label == "STRUCTURAL_CONSTANT_ALREADY"
