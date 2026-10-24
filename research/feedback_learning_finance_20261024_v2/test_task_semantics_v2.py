"""Tests for corrected financial task units and denominators."""

from __future__ import annotations

import pytest

from task_semantics_v2 import semantics_for_operator, validate_task_semantics


def test_percent_change_always_uses_percent_output_and_prior_denominator() -> None:
    semantics = semantics_for_operator("percent_change", "reported", "Revenue")
    assert semantics.output_unit == "percent"
    assert semantics.denominator == "prior_value"
    task = {
        "task_id": "t1",
        "task_type": "percent_change",
        "source_unit": "reported",
        "unit": "percent",
        "denominator": "prior_value",
        "row_label": "Revenue",
        "source_column_label": "2020",
        "question": "From 2019 to 2020, what is the percentage change?",
    }
    assert validate_task_semantics(task)["valid"] is True


def test_percentage_point_change_requires_percent_metric() -> None:
    semantics = semantics_for_operator(
        "percentage_point_change",
        "percent",
        "Operating margin %",
    )
    assert semantics.output_unit == "percentage_points"
    with pytest.raises(ValueError):
        semantics_for_operator("percentage_point_change", "reported", "Revenue")

