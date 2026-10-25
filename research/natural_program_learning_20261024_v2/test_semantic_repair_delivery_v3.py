"""Focused tests for bounded structural-denominator repair."""

from __future__ import annotations

from semantic_repair_delivery_v3 import evaluate, repair_structural_denominator


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


def test_policy_scoring_uses_each_policys_own_candidate() -> None:
    rows = [
        {
            "program_correct": False,
            "correct_after_repair": True,
            "interface_valid": True,
            "program_executable": True,
            "refs_valid": True,
            "semantic_decision": "INVALID",
            "repair_valid": True,
            "policy_outcomes": {
                "always_accept": {"accepted": True, "correct": False, "repair_actions": 0},
                "executable_rule": {"accepted": True, "correct": False, "repair_actions": 0},
                "semantic_rule": {"accepted": False, "correct": False, "repair_actions": 0},
                "semantic_repair_rule": {"accepted": True, "correct": True, "repair_actions": 1},
            },
        }
    ]
    assert evaluate(rows, "always_accept")["correct_delivery_count"] == 0
    assert evaluate(rows, "semantic_repair_rule")["correct_delivery_count"] == 1
    assert evaluate(rows, "semantic_repair_rule")["repair_actions"] == 1
