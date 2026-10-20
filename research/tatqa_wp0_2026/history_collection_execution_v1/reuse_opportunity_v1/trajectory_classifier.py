#!/usr/bin/env python3
"""Classify trajectory completeness and scientific outcomes independently."""

from __future__ import annotations

import json
from typing import Any


def classify_trajectory(
    result_row: dict[str, Any],
    raw_complete: bool,
    is_fixture: bool = False,
) -> dict[str, Any]:
    plan_request = result_row.get("plan_request") or {}
    consume_request = result_row.get("consume_request") or {}
    plan = result_row.get("plan")
    tool = result_row.get("tool_result") or {}
    consume = result_row.get("consume")
    reference = result_row.get("hidden_reference") or {}

    request_chain_present = all([
        plan_request.get("request_key"),
        consume_request.get("request_key"),
        plan is not None,
        bool(tool),
        consume is not None,
    ])
    trajectory_complete = bool(raw_complete and request_chain_present)

    tool_success = tool.get("status") == "OK"
    tool_match_reference = bool(
        tool_success
        and isinstance(tool.get("returned_value"), (int, float))
        and abs(float(tool["returned_value"]) - float(reference["delta_target"])) <= 1e-9
    )
    answer_reference_match: bool | None = None
    answer_tool_consistency: bool | None = None
    if isinstance(consume, dict) and consume.get("status") == "ANSWER":
        answer_reference_match = (
            abs(float(consume["delta_target"]) - float(reference["delta_target"])) <= 1e-9
            and consume.get("unit") == reference.get("target_unit")
        )
        answer_tool_consistency = bool(
            tool_success
            and abs(float(consume["delta_target"]) - float(tool["returned_value"])) <= 1e-9
        )

    consume_status = consume.get("status") if isinstance(consume, dict) else None
    if not trajectory_complete:
        outcome = "INCOMPLETE_RECORD"
    elif not tool_success:
        outcome = "TOOL_FAILURE"
    elif consume_status == "ANSWER":
        outcome = "SUCCESS" if answer_reference_match else "WRONG_ANSWER"
    elif consume_status == "REFUSE":
        outcome = "REFUSED"
    elif consume_status == "UNKNOWN":
        outcome = "UNKNOWN"
    else:
        outcome = "INVALID_OUTPUT"

    return {
        "task_id": result_row.get("task_id"),
        "attempt": result_row.get("attempt"),
        "is_fixture": is_fixture,
        "trajectory_complete": trajectory_complete,
        "raw_complete": bool(raw_complete),
        "outcome": outcome,
        "tool_execution_success": tool_success,
        "tool_match_reference": tool_match_reference,
        "answer_reference_match": answer_reference_match,
        "answer_tool_consistency": answer_tool_consistency,
        "feedback_category": result_row.get("feedback_category"),
        "post_feedback_action_change": None,
        "scientific_sample_eligible": bool(trajectory_complete and not is_fixture),
    }


def action_change(first: dict[str, Any], followup: dict[str, Any]) -> str:
    first_plan = (first.get("plan") or {}).get("params", {}).get("expression")
    followup_plan = (followup.get("plan") or {}).get("params", {}).get("expression")
    same_action = first_plan == followup_plan
    if same_action:
        return "NO_CHANGE"
    first_failed = first.get("feedback_category") not in {"SUCCESS"}
    second_succeeded = followup.get("feedback_category") == "SUCCESS"
    if first_failed and second_succeeded:
        return "CORRECTIVE_CHANGE"
    return "UNEXPLAINED_CHANGE"


def main() -> int:
    raise SystemExit("use classify_trajectory from the offline diagnostic builder")


if __name__ == "__main__":
    main()
