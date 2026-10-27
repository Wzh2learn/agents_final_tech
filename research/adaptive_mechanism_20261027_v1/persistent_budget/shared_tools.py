"""One normalization/calculator implementation shared by every eligible arm."""

from __future__ import annotations

import ast
import operator
import re
from decimal import Decimal
from typing import Any


_BINARY = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def normalize_answer(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    normalized = re.sub(r"\s+", " ", value.strip().casefold())
    return normalized.rstrip(".")


def safe_calculate(expression: str) -> Decimal:
    if not isinstance(expression, str) or len(expression) > 200:
        raise ValueError("invalid_expression")
    tree = ast.parse(expression, mode="eval")

    def evaluate(node: ast.AST) -> Decimal:
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in {int, float, Decimal}:
            return Decimal(str(node.value))
        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
            left = evaluate(node.left)
            right = evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError("power_limit")
            return Decimal(str(_BINARY[type(node.op)](left, right)))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            return Decimal(str(_UNARY[type(node.op)](evaluate(node.operand))))
        raise ValueError("unsupported_expression_node")

    return evaluate(tree)
