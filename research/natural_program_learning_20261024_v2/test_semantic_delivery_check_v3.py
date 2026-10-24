"""Focused tests for visible semantic delivery checks."""

from __future__ import annotations

from semantic_delivery_check_v3 import policy_metrics, semantic_check


def cells() -> dict[str, dict[str, object]]:
    return {
        "R1:C1": {"row_label": "Revenue", "column_label": "2019", "value": 10},
        "R1:C2": {"row_label": "Revenue", "column_label": "2018", "value": 8},
        "R9:C9": {"row_label": "Other, net", "column_label": "", "value": 2},
    }


def test_structural_average_denominator_is_visible_invalid() -> None:
    program = {
        "op": "div",
        "left": {"op": "add", "left": {"ref": "R1:C1"}, "right": {"ref": "R1:C2"}},
        "right": {"ref": "R9:C9"},
    }
    decision, reasons = semantic_check(
        "What is the average revenue in 2018 and 2019?",
        program,
        cells(),
    )
    assert decision == "INVALID"
    assert "structural_average_denominator_misbound" in reasons


def test_semantic_rule_retains_unresolved_and_wrong_answers() -> None:
    rows = [
        {
            "program_correct": True,
            "interface_valid": True,
            "program_executable": True,
            "refs_valid": True,
            "semantic_decision": "VALID",
        },
        {
            "program_correct": False,
            "interface_valid": True,
            "program_executable": True,
            "refs_valid": True,
            "semantic_decision": "INVALID",
        },
    ]
    accepted = policy_metrics(rows, "always_accept")
    semantic = policy_metrics(rows, "semantic_rule")
    assert accepted["accepted"] == 2
    assert semantic["accepted"] == 1
    assert semantic["wrong_delivery_count"] == 0
