"""Frozen numeric parser/calculator surface used by the strict response parser."""

from __future__ import annotations

import ast
import math
import operator
from decimal import Decimal, InvalidOperation
from typing import Any


CALCULATOR_VERSION = "safe_decimal_numeric_value_only_v1"

_BINARY = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _evaluate(node: ast.AST) -> Decimal:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return Decimal(str(node.value))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_evaluate(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
        left = _evaluate(node.left)
        right = _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(float(right)) > 12:
            raise ValueError("exponent_out_of_bounds")
        return _BINARY[type(node.op)](left, right)
    raise ValueError("unsupported_expression_node")


def numeric_value(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        result = float(value)
        return result if math.isfinite(result) else None
    text = str(value).strip()
    if not text:
        return None
    normalized = text.replace(",", "")
    try:
        parsed = ast.parse(normalized, mode="eval")
        result = float(_evaluate(parsed))
    except (SyntaxError, TypeError, ValueError, InvalidOperation, ZeroDivisionError):
        try:
            result = float(normalized)
        except ValueError:
            return None
    return result if math.isfinite(result) else None
