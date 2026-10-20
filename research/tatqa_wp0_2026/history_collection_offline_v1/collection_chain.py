#!/usr/bin/env python3
"""Offline plan -> real tool -> consume chain with independent reference checks."""

from __future__ import annotations

import ast
import operator
from typing import Any


OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def evaluate_expression(expression: str) -> float:
    def evaluate(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
            return float(OPERATORS[type(node.op)](evaluate(node.operand)))
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            return float(OPERATORS[type(node.op)](evaluate(node.left), evaluate(node.right)))
        raise ValueError("unsupported_expression_node")

    tree = ast.parse(expression, mode="eval")
    return evaluate(tree)


def validate_plan(task: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    if task.get("requested_quantity") != "signed_difference":
        return {"tool": None, "params": {}, "plan_status": "INVALID_PLAN", "error": "UNSUPPORTED_REQUESTED_QUANTITY"}
    if plan.get("tool") != "calc":
        return {"tool": None, "params": {}, "plan_status": "INVALID_PLAN", "error": "UNSUPPORTED_TOOL"}
    expression = str(plan.get("params", {}).get("expression", ""))
    if not expression.strip():
        return {"tool": "calc", "params": {"expression": expression}, "plan_status": "INVALID_PLAN", "error": "EMPTY_TOOL_EXPRESSION"}
    try:
        evaluate_expression(expression)
    except Exception as exc:
        return {
            "tool": "calc",
            "params": {"expression": expression},
            "plan_status": "INVALID_PLAN",
            "error": type(exc).__name__,
        }
    return {
        "tool": "calc",
        "params": {"expression": expression},
        "plan_status": "VALID",
    }


def execute_tool(validated_plan: dict[str, Any]) -> dict[str, Any]:
    expression = validated_plan["params"]["expression"]
    try:
        value = evaluate_expression(expression)
    except Exception as exc:
        return {
            "tool": "calc",
            "params": {"expression": expression},
            "returned_value": None,
            "status": "TOOL_ERROR",
            "error": type(exc).__name__,
        }
    return {
        "tool": "calc",
        "params": {"expression": expression},
        "returned_value": value,
        "status": "OK",
        "error": None,
    }


def independent_reference(task: dict[str, Any]) -> dict[str, Any]:
    cells = task.get("cells", {})
    late_value = cells.get("late_value")
    early_value = cells.get("early_value")
    if not isinstance(late_value, (int, float)) or not isinstance(early_value, (int, float)):
        return {"status": "REFERENCE_UNSCORABLE", "reason": "missing_numeric_cells"}
    factor = task.get("source_to_target_factor")
    if not isinstance(factor, (int, float)) or factor <= 0:
        return {"status": "REFERENCE_UNSCORABLE", "reason": "invalid_unit_factor"}
    delta_source = float(late_value) - float(early_value)
    delta_target = delta_source * float(factor)
    return {
        "status": "REFERENCE_RECOMPUTED",
        "delta_source": delta_source,
        "delta_target": delta_target,
        "source_unit": task.get("source_unit"),
        "target_unit": task.get("target_unit"),
    }


def consume_answer(
    task: dict[str, Any],
    tool_result: dict[str, Any],
    actor_answer: dict[str, Any],
) -> dict[str, Any]:
    if tool_result.get("status") != "OK":
        return {"status": "NOT_CONSUMABLE", "reason": "tool_result_not_ok"}
    returned = tool_result.get("returned_value")
    delta_target = actor_answer.get("delta_target")
    if not isinstance(delta_target, (int, float)):
        return {"status": "INVALID_ACTOR_ANSWER", "reason": "missing_numeric_delta_target"}
    if abs(float(delta_target) - float(returned)) > 1e-9:
        return {
            "status": "ANSWER_TOOL_MISMATCH",
            "returned_value": returned,
            "actor_delta_target": delta_target,
        }
    if actor_answer.get("unit") != task.get("target_unit"):
        return {"status": "ANSWER_UNIT_MISMATCH", "expected": task.get("target_unit"), "actual": actor_answer.get("unit")}
    return {
        "status": "ANSWER_CONSUMES_TOOL_RESULT",
        "returned_value": returned,
        "actor_delta_target": delta_target,
        "unit": actor_answer.get("unit"),
    }


def run_offline_episode(
    task: dict[str, Any],
    plan: dict[str, Any],
    actor_answer: dict[str, Any],
) -> dict[str, Any]:
    validated = validate_plan(task, plan)
    if validated.get("plan_status") != "VALID":
        tool_result = {
            "tool": "calc",
            "params": validated.get("params", {}),
            "returned_value": None,
            "status": "TOOL_ERROR",
            "error": "INVALID_PLAN",
            "error_detail": validated.get("error"),
        }
    else:
        tool_result = execute_tool(validated)
    consumption = consume_answer(task, tool_result, actor_answer)
    reference = independent_reference(task)
    return {
        "task_id": task.get("task_id"),
        "plan": validated,
        "tool_result": tool_result,
        "consumption": consumption,
        "reference": reference,
        "model_calls": 0,
        "scientific_result": False,
    }
