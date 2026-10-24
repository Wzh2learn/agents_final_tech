"""Explicit semantics for financial difference and percentage tasks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TaskSemantics:
    """Public unit and denominator contract for one derived task."""

    operator: str
    output_unit: str
    denominator: str | None
    rounding_decimals: int


def semantics_for_operator(
    operator: str,
    source_unit: str,
    source_text: str = "",
) -> TaskSemantics:
    """Return the v2 unit/denominator semantics for an operator."""
    normalized = source_text.casefold()
    if operator == "difference":
        return TaskSemantics("difference", source_unit, None, 6)
    if operator == "percent_change":
        return TaskSemantics("percent_change", "percent", "prior_value", 6)
    if operator == "percentage_point_change":
        if "%" not in source_text and not any(
            marker in normalized for marker in ("rate", "margin", "percent")
        ):
            raise ValueError("percentage_point_change_requires_percent_metric")
        return TaskSemantics(
            "percentage_point_change",
            "percentage_points",
            None,
            6,
        )
    raise ValueError(f"unsupported_operator:{operator}")


def validate_task_semantics(task: dict[str, Any]) -> dict[str, Any]:
    """Validate one generated task against its explicit semantics."""
    semantics = semantics_for_operator(
        task["task_type"],
        task.get("source_unit", "reported"),
        f"{task.get('row_label', '')} {task.get('source_column_label', '')}",
    )
    checks = {
        "operator_supported": True,
        "unit_matches_semantics": task.get("unit") == semantics.output_unit,
        "denominator_declared_for_percent_change": (
            task["task_type"] != "percent_change"
            or task.get("denominator") == semantics.denominator
        ),
        "question_names_operator": (
            ("percentage-point change" in task["question"]
             and task["task_type"] == "percentage_point_change")
            or ("percentage change" in task["question"]
                and task["task_type"] == "percent_change")
            or ("numeric change" in task["question"]
                and task["task_type"] == "difference")
        ),
    }
    return {
        "task_id": task.get("task_id"),
        "semantics": semantics.__dict__,
        "checks": checks,
        "valid": all(checks.values()),
    }

