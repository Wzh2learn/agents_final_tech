"""Focused tests for confirmation delivery replay."""

from __future__ import annotations

from analyze_confirmation_delivery_v3 import analyze


def test_confirmation_delivery_uses_all_rows_without_dev_fit() -> None:
    rows = [
        {
            "model_arm": "ordinary",
            "program_correct": True,
            "interface_valid": True,
            "program_executable": True,
            "refs_valid": True,
        },
        {
            "model_arm": "ordinary",
            "program_correct": False,
            "interface_valid": True,
            "program_executable": True,
            "refs_valid": True,
        },
    ]
    output = analyze(rows)
    policy = output["models"]["ordinary"]["policies"]["all_applicable_pass"]
    assert policy["accepted"] == 2
    assert policy["conditional_wrong_delivery_rate"] == 0.5
    assert output["learned_policy"].startswith("NOT_APPLICABLE")
