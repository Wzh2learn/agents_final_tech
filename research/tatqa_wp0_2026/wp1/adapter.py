from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping


ARMS: frozenset[str] = frozenset({"B", "E", "C", "S"})
CONTEXT_HOOK_TYPES: Mapping[str, str] = {
    "B": "none",
    "E": "experience",
    "C": "matched_experience",
    "S": "static_rules",
}
ANSWER_FORMAT = (
    '{row: <label>, periods: [<late>, <early>], '
    "delta_source: <number>, delta_target: <number>, unit: <target unit>}"
)
TOKEN_PATTERN = re.compile(r"\S+")


@dataclass(frozen=True)
class ContextHook:
    arm: str
    hook_type: str
    text: str


@dataclass(frozen=True)
class Projection:
    row_label: str
    period_late: str
    period_early: str
    source_unit: str
    target_unit: str
    requested_quantity: str
    table: list[list[str]]


def _normalize_cell(cell: Any) -> str:
    if cell is None:
        return ""
    return str(cell)


def _normalize_table(table: Any) -> list[list[str]]:
    if not isinstance(table, list) or not table:
        raise ValueError("table must be a non-empty list")
    normalized: list[list[str]] = []
    width: int | None = None
    for row in table:
        if not isinstance(row, list):
            raise ValueError("each table row must be a list")
        if width is None:
            width = len(row)
        if len(row) != width:
            raise ValueError("all table rows must have the same width")
        normalized.append([_normalize_cell(cell) for cell in row])
    return normalized


def _require_period(item: Mapping[str, Any], key: str) -> tuple[int, str]:
    period = item.get(key)
    if not isinstance(period, Mapping):
        raise ValueError(f"{key} must be an object")
    if set(period) != {"col", "label"}:
        raise ValueError(f"{key} must contain exactly col and label")
    col = period["col"]
    label = period["label"]
    if isinstance(col, bool) or not isinstance(col, int) or col < 0:
        raise ValueError(f"{key}.col must be a non-negative integer")
    if not isinstance(label, str):
        raise ValueError(f"{key}.label must be a string")
    return col, label


def _candidate_projection_fields(
    item: Mapping[str, Any]
) -> tuple[list[list[str]], str, str, str, str, str]:
    required = {
        "table",
        "row_index",
        "period_late",
        "period_early",
        "source_unit",
        "requested_quantity",
    }
    missing = sorted(field for field in required if field not in item)
    if missing:
        raise ValueError(f"candidate item is missing fields: {missing}")
    table = _normalize_table(item["table"])
    row_index = item["row_index"]
    if isinstance(row_index, bool) or not isinstance(row_index, int):
        raise ValueError("row_index must be an integer")
    if row_index < 0 or row_index >= len(table):
        raise ValueError("row_index is out of range")
    if not table[row_index]:
        raise ValueError("selected row is empty")
    late_col, late_label = _require_period(item, "period_late")
    early_col, early_label = _require_period(item, "period_early")
    if late_col >= len(table[row_index]) or early_col >= len(table[row_index]):
        raise ValueError("period column is out of range")
    source_unit = item.get("source_unit") or "unit"
    target_unit = item.get("target_unit") or source_unit
    requested_quantity = item.get("requested_quantity")
    if not isinstance(source_unit, str) or not isinstance(target_unit, str):
        raise ValueError("source_unit and target_unit must be strings")
    if not isinstance(requested_quantity, str):
        raise ValueError("requested_quantity must be a string")
    return (
        table,
        str(table[row_index][0]),
        late_label,
        early_label,
        source_unit,
        target_unit,
        requested_quantity,
    )


def runtime_payload_from_candidate(item: Mapping[str, Any]) -> dict[str, Any]:
    (
        table,
        _row_label,
        late_label,
        early_label,
        source_unit,
        target_unit,
        requested_quantity,
    ) = _candidate_projection_fields(item)
    return {
        "table": table,
        "row_index": item["row_index"],
        "period_late": {"col": item["period_late"]["col"], "label": late_label},
        "period_early": {
            "col": item["period_early"]["col"],
            "label": early_label,
        },
        "source_unit": source_unit,
        "target_unit": target_unit,
        "requested_quantity": requested_quantity,
    }


def projection_from_candidate(item: Mapping[str, Any]) -> Projection:
    (
        table,
        row_label,
        late_label,
        early_label,
        source_unit,
        target_unit,
        requested_quantity,
    ) = _candidate_projection_fields(item)
    return Projection(
        row_label=row_label,
        period_late=late_label,
        period_early=early_label,
        source_unit=source_unit,
        target_unit=target_unit,
        requested_quantity=requested_quantity,
        table=table,
    )


def validate_context_hook(hook: ContextHook) -> None:
    if hook.arm not in ARMS:
        raise ValueError(f"unsupported arm: {hook.arm!r}")
    expected = CONTEXT_HOOK_TYPES[hook.arm]
    if hook.hook_type != expected:
        raise ValueError(
            f"arm {hook.arm} requires context hook type {expected!r}"
        )
    if not isinstance(hook.text, str):
        raise ValueError("context hook text must be a string")
    if hook.arm == "B" and hook.text != "":
        raise ValueError("B arm context must be empty")
    if hook.arm != "B" and not hook.text.strip():
        raise ValueError("E/C/S context hook text must be non-empty")


def build_prompt(item: Mapping[str, Any], hook: ContextHook) -> str:
    validate_context_hook(hook)
    projection = projection_from_candidate(item)
    payload = {
        "arm": hook.arm,
        "arm_context": {
            "content": hook.text,
            "type": hook.hook_type,
        },
        "evidence": {
            "period_early": projection.period_early,
            "period_late": projection.period_late,
            "requested_quantity": projection.requested_quantity,
            "row_label": projection.row_label,
            "source_unit": projection.source_unit,
            "table": projection.table,
            "target_unit": projection.target_unit,
        },
        "final_answer_format": ANSWER_FORMAT,
        "tool": "calc(expression) -> number",
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ) + "\n"


def count_context_tokens(text: str) -> int:
    if not isinstance(text, str):
        raise ValueError("context text must be a string")
    return len(TOKEN_PATTERN.findall(text))


def context_token_delta(
    e_text: str,
    c_text: str,
    relative_limit: Decimal = Decimal("0.05"),
) -> dict[str, Any]:
    if relative_limit < 0:
        raise ValueError("relative_limit must be non-negative")
    e_tokens = count_context_tokens(e_text)
    c_tokens = count_context_tokens(c_text)
    absolute_delta = abs(e_tokens - c_tokens)
    relative_delta = (
        Decimal(absolute_delta) / Decimal(e_tokens)
        if e_tokens
        else Decimal(1) if absolute_delta else Decimal(0)
    )
    return {
        "e_tokens": e_tokens,
        "c_tokens": c_tokens,
        "absolute_delta": absolute_delta,
        "relative_delta": float(relative_delta),
        "relative_limit": float(relative_limit),
        "within_limit": relative_delta <= relative_limit,
    }
