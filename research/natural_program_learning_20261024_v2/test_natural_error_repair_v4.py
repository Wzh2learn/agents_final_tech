"""Focused tests for natural-error repair data construction."""

from __future__ import annotations

from run_natural_error_repair_v4 import corrected_target


def task(unresolved: bool = False) -> dict[str, object]:
    question = (
        "What is the 2018 average actuarial losses recognised in the SOCI?"
        if unresolved
        else "What is the average revenue in 2018 and 2019?"
    )
    return {
        "question": question,
        "table_text": (
            "columns: C0= | C1=2019 | C2=2018\n"
            "R1 [Revenue] C0=Revenue | C1=10 | C2=8\n"
            "R9 [Other, net] C0=Other, net | C1=2 | C2=0"
        ),
        "target": {
            "unit": "million",
            "program": {
                "op": "div",
                "left": {"op": "add", "left": {"ref": "R1:C1"}, "right": {"ref": "R1:C2"}},
                "right": {"ref": "R9:C1"},
            },
            "evidence_refs": ["R1:C1", "R1:C2", "R9:C1"],
        },
    }


def test_structural_denominator_is_corrected_for_training_target() -> None:
    target = corrected_target(task())
    assert target is not None
    assert target["program"]["right"] == {"const": 2.0}
    assert "R9:C1" not in target["evidence_refs"]


def test_reference_question_mismatch_is_excluded() -> None:
    assert corrected_target(task(unresolved=True)) is None
