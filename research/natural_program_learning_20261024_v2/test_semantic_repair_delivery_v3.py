"""Focused tests for bounded structural-denominator repair."""

from __future__ import annotations

from semantic_repair_delivery_v3 import repair_structural_denominator


def test_structural_denominator_is_repaired_to_constant() -> None:
    program = {
        "op": "div",
        "left": {"op": "add", "left": {"ref": "R1:C1"}, "right": {"ref": "R1:C2"}},
        "right": {"ref": "R9:C9"},
    }
    cells = {
        "R1:C1": {"value": 10, "row_label": "Revenue", "column_label": "2019"},
        "R1:C2": {"value": 8, "row_label": "Revenue", "column_label": "2018"},
        "R9:C9": {"value": 2, "row_label": "Other, net", "column_label": ""},
    }
    repaired, repairs = repair_structural_denominator(
        program,
        "What is the average revenue in 2018 and 2019?",
        cells,
    )
    assert repaired["right"] == {"const": 2}
    assert repairs == ["replace_structural_denominator:R9:C9:const:2"]
