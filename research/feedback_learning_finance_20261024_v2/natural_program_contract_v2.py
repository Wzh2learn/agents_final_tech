"""Structured evidence programs for natural TAT-QA arithmetic questions."""

from __future__ import annotations

import ast
import math
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProgramCell:
    """One raw table cell with visible row/column identity."""

    ref: str
    row_label: str
    column_label: str
    value: float


def parse_numeric(value: Any) -> float | None:
    """Parse a conservative TAT-QA numeric cell."""
    text = str(value).strip().replace(",", "")
    if not text or text.casefold() in {"n/a", "na", "-", "—"}:
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()").replace("%", "").replace("$", "").replace("£", "")
    text = text.replace("€", "").replace("¥", "")
    if not re.fullmatch(r"-?\d+(?:\.\d+)?", text):
        return None
    result = float(text)
    return -result if negative else result


def table_cells(table: list[list[Any]]) -> dict[str, ProgramCell]:
    """Index visible numeric cells using stable row/column IDs."""
    if not table:
        return {}
    header = table[0]
    cells: dict[str, ProgramCell] = {}
    for row_index, row in enumerate(table[1:], start=1):
        row_label = str(row[0]).strip() if row else ""
        for column_index in range(1, min(len(row), len(header))):
            value = parse_numeric(row[column_index])
            if value is None:
                continue
            ref = f"R{row_index}:C{column_index}"
            cells[ref] = ProgramCell(
                ref=ref,
                row_label=row_label,
                column_label=str(header[column_index]).strip(),
                value=value,
            )
    return cells


def normalize_derivation(derivation: str) -> str:
    """Normalize the restricted arithmetic subset of TAT-QA derivations."""
    text = derivation.strip().replace(",", "")
    text = text.replace("−", "-").replace("×", "*").replace("÷", "/")
    text = re.sub(r"(?<=\d)\s*%", "", text)
    if "=" in text:
        text = text.split("=", 1)[1]
    return text.strip()


def parse_derivation_ast(derivation: str) -> ast.Expression:
    """Parse a derivation containing only numeric arithmetic."""
    return ast.parse(normalize_derivation(derivation), mode="eval")


def literal_values(tree: ast.Expression) -> list[float]:
    """Return numeric constants in source order."""
    values: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            values.append(float(node.value))
    return values


def unique_literal_refs(
    tree: ast.Expression,
    cells: dict[str, ProgramCell],
    ignored_literals: set[float] | None = None,
) -> tuple[dict[float, str], list[str]]:
    """Map each nontrivial numeric literal to exactly one visible table cell."""
    ignored = ignored_literals or {1.0}
    mapping: dict[float, str] = {}
    exclusions: list[str] = []
    for value in literal_values(tree):
        if value in ignored or value in mapping:
            continue
        matches = [
            cell for cell in cells.values()
            if math.isclose(cell.value, value, rel_tol=0, abs_tol=1e-9)
        ]
        if len(matches) == 1:
            mapping[value] = matches[0].ref
        elif len(matches) == 0:
            exclusions.append(f"literal_not_in_table:{value}")
        else:
            exclusions.append(f"literal_ambiguous:{value}:{len(matches)}")
    return mapping, exclusions


def ast_to_program(
    node: ast.AST,
    literal_refs: dict[float, str],
) -> dict[str, Any]:
    """Convert restricted arithmetic AST to a structured evidence program."""
    if isinstance(node, ast.Expression):
        return ast_to_program(node.body, literal_refs)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        value = float(node.value)
        ref = literal_refs.get(value)
        return {"ref": ref} if ref else {"const": value}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        operand = ast_to_program(node.operand, literal_refs)
        return operand if isinstance(node.op, ast.UAdd) else {
            "op": "sub",
            "left": {"const": 0.0},
            "right": operand,
        }
    if isinstance(node, ast.BinOp):
        op_names = {
            ast.Add: "add",
            ast.Sub: "sub",
            ast.Mult: "mul",
            ast.Div: "div",
        }
        op_name = next((name for cls, name in op_names.items() if isinstance(node.op, cls)), None)
        if op_name:
            return {
                "op": op_name,
                "left": ast_to_program(node.left, literal_refs),
                "right": ast_to_program(node.right, literal_refs),
            }
    raise ValueError("unsupported_derivation_node")


def restore_top_level_scale(
    program: dict[str, Any],
    scale_ref: str | None,
) -> dict[str, Any]:
    """Restore a top-level multiplier 100 as a constant, not a table operand."""
    if not scale_ref or program.get("op") != "mul":
        return program
    updated = dict(program)
    if updated.get("right") == {"ref": scale_ref}:
        updated["right"] = {"const": 100.0}
    if updated.get("left") == {"ref": scale_ref}:
        updated["left"] = {"const": 100.0}
    return updated


def program_refs(program: dict[str, Any]) -> list[str]:
    """Return unique evidence references in structured program order."""
    refs: list[str] = []
    if "ref" in program:
        refs.append(str(program["ref"]))
    elif "op" in program:
        refs.extend(program_refs(program["left"]))
        refs.extend(program_refs(program["right"]))
    return list(dict.fromkeys(refs))


def execute_program(program: dict[str, Any], cells: dict[str, ProgramCell]) -> float:
    """Execute a structured evidence program against raw visible cells."""
    if "ref" in program:
        ref = str(program["ref"])
        if ref not in cells:
            raise ValueError(f"missing_ref:{ref}")
        return cells[ref].value
    if "const" in program:
        return float(program["const"])
    if "op" not in program:
        raise ValueError("invalid_program_node")
    left = execute_program(program["left"], cells)
    right = execute_program(program["right"], cells)
    if program["op"] == "add":
        return left + right
    if program["op"] == "sub":
        return left - right
    if program["op"] == "mul":
        return left * right
    if program["op"] == "div":
        if right == 0:
            raise ZeroDivisionError("program_division_by_zero")
        return left / right
    raise ValueError(f"unsupported_program_op:{program['op']}")

