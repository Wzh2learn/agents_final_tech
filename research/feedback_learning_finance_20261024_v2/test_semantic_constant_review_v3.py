"""Focused tests for average-denominator review."""

from __future__ import annotations

from semantic_constant_review_v3 import iter_denominator_nodes


def test_denominator_node_is_found_only_in_division_position() -> None:
    program = {
        "op": "div",
        "left": {"op": "add", "left": {"ref": "R1:C1"}, "right": {"ref": "R1:C2"}},
        "right": {"ref": "R9:C2"},
    }
    assert list(iter_denominator_nodes(program, "R9:C2")) == [{"ref": "R9:C2"}]
    assert list(iter_denominator_nodes(program, "R1:C1")) == []
