from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping


SCALES: dict[str, Decimal] = {
    "unit": Decimal(0),
    "thousand": Decimal(3),
    "million": Decimal(6),
    "billion": Decimal(9),
    "percent": Decimal(0),
}
UNIT_ALIASES: dict[str, str] = {
    "": "unit",
    "unit": "unit",
    "units": "unit",
    "none": "unit",
    "thousand": "thousand",
    "thousands": "thousand",
    "million": "million",
    "millions": "million",
    "billion": "billion",
    "billions": "billion",
    "percent": "percent",
    "%": "percent",
}
REQUIRED_RUNTIME_FIELDS: frozenset[str] = frozenset(
    {
        "table",
        "row_index",
        "period_late",
        "period_early",
        "source_unit",
        "target_unit",
        "requested_quantity",
    }
)
CORRECT_OUTCOMES: frozenset[str] = frozenset({"correct", "correct_other_form"})
NUMERIC_CELL_PATTERN = re.compile(
    r"^\s*\(?\s*[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?\s*%?\s*\)?$"
)
TIMEOUT_TOKENS: frozenset[str] = frozenset(
    {"TIMEOUT", "TIMEOUT_EXCEEDED", "TIMEOUT_ERROR"}
)


@dataclass(frozen=True)
class Gold:
    late_value: Decimal
    early_value: Decimal
    delta_source: Decimal
    delta_target: Decimal
    source_unit: str
    target_unit: str


@dataclass(frozen=True)
class PreparedItem:
    item_id: str
    origin_id: str
    row_label: str
    late_period: str
    early_period: str
    gold: Gold


def normalize_unit(unit: str | None) -> str:
    if unit is None:
        return "unit"
    if not isinstance(unit, str):
        raise ValueError("unit must be a string or null")
    key = unit.strip().lower()
    if key not in UNIT_ALIASES:
        raise ValueError(f"unsupported unit: {unit!r}")
    return UNIT_ALIASES[key]


def parse_numeric_cell(value: str | int | float) -> Decimal:
    if isinstance(value, bool):
        raise ValueError("boolean is not a numeric table cell")
    negative = False
    if isinstance(value, Decimal):
        parsed = value
    elif isinstance(value, int):
        parsed = Decimal(value)
    elif isinstance(value, float):
        parsed = Decimal(str(value))
    elif isinstance(value, str):
        text = value.strip()
        if not NUMERIC_CELL_PATTERN.fullmatch(text):
            raise ValueError(f"invalid numeric table cell: {value!r}")
        negative = text.startswith("(") and text.endswith(")")
        if negative:
            text = text[1:-1].strip()
        if text.endswith("%"):
            text = text[:-1].strip()
        text = text.replace(",", "")
        try:
            parsed = Decimal(text)
        except InvalidOperation as exc:
            raise ValueError(f"invalid numeric table cell: {value!r}") from exc
    else:
        raise ValueError(f"unsupported numeric table cell type: {type(value).__name__}")
    if not parsed.is_finite():
        raise ValueError("numeric table cell must be finite")
    if negative:
        parsed = -parsed
    return parsed


def conversion_factor(source_unit: str, target_unit: str) -> Decimal:
    source_key = normalize_unit(source_unit)
    target_key = normalize_unit(target_unit)
    allowed = source_key == target_key or {
        (source_key, target_key)
    }.issubset(
        {
            ("thousand", "unit"),
            ("million", "thousand"),
            ("billion", "million"),
            ("percent", "percent"),
        }
    )
    if not allowed:
        raise ValueError(
            f"unsupported unit conversion: {source_key!r} -> {target_key!r}"
        )
    exponent = SCALES[source_key] - SCALES[target_key]
    return Decimal(10) ** exponent


def _required_runtime_payload(item: Mapping[str, Any]) -> None:
    missing = sorted(field for field in REQUIRED_RUNTIME_FIELDS if field not in item)
    if missing:
        raise ValueError(f"runtime item is missing fields: {missing}")


def _period_cell(item: Mapping[str, Any], key: str) -> tuple[int, str]:
    period = item[key]
    if not isinstance(period, Mapping):
        raise ValueError(f"{key} must be an object")
    if "col" not in period or "label" not in period:
        raise ValueError(f"{key} must contain col and label")
    col = period["col"]
    label = period["label"]
    if isinstance(col, bool) or not isinstance(col, int) or col < 0:
        raise ValueError(f"{key}.col must be a non-negative integer")
    if not isinstance(label, str):
        raise ValueError(f"{key}.label must be a string")
    return col, label


def recompute_gold(item: Mapping[str, Any]) -> Gold:
    _required_runtime_payload(item)
    table = item["table"]
    if not isinstance(table, list) or not table:
        raise ValueError("table must be a non-empty list")
    row_index = item["row_index"]
    if isinstance(row_index, bool) or not isinstance(row_index, int):
        raise ValueError("row_index must be an integer")
    if row_index < 0 or row_index >= len(table):
        raise ValueError("row_index is out of range")
    row = table[row_index]
    if not isinstance(row, list) or not row:
        raise ValueError("selected table row must be a non-empty list")
    late_col, _ = _period_cell(item, "period_late")
    early_col, _ = _period_cell(item, "period_early")
    if late_col >= len(row) or early_col >= len(row):
        raise ValueError("period column is out of range for the selected row")
    source_unit = normalize_unit(item.get("source_unit"))
    target_unit = normalize_unit(item.get("target_unit", source_unit))
    late_value = parse_numeric_cell(row[late_col])
    early_value = parse_numeric_cell(row[early_col])
    delta_source = late_value - early_value
    delta_target = delta_source * conversion_factor(source_unit, target_unit)
    return Gold(
        late_value=late_value,
        early_value=early_value,
        delta_source=delta_source,
        delta_target=delta_target,
        source_unit=source_unit,
        target_unit=target_unit,
    )


def prepare_item(item: Mapping[str, Any]) -> PreparedItem:
    gold = recompute_gold(item)
    table = item["table"]
    row_index = item["row_index"]
    row_label = table[row_index][0]
    return PreparedItem(
        item_id=str(item.get("item_id", "")),
        origin_id=str(item.get("origin_id", "")),
        row_label=str(row_label),
        late_period=str(item["period_late"]["label"]),
        early_period=str(item["period_early"]["label"]),
        gold=gold,
    )


def _answer_decimal(value: Any, field: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{field} must be numeric")
    try:
        parsed = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field} must be finite")
    return parsed


def parse_answer(answer_text: str) -> dict[str, Any] | None:
    if not isinstance(answer_text, str):
        return None
    token = answer_text.strip().upper()
    if token == "REFUSED":
        return {"answer_class": "refused"}
    if token == "UNKNOWN" or token in TIMEOUT_TOKENS:
        return {"answer_class": "unknown"}
    try:
        parsed = json.loads(answer_text)
    except (json.JSONDecodeError, TypeError):
        return {"answer_class": "unknown"}
    if not isinstance(parsed, dict):
        return {"answer_class": "unknown"}
    required = {"row", "periods", "delta_source", "delta_target", "unit"}
    if set(parsed) != required:
        return {"answer_class": "unknown"}
    if not isinstance(parsed["row"], str):
        return {"answer_class": "unknown"}
    periods = parsed["periods"]
    if (
        not isinstance(periods, list)
        or len(periods) != 2
        or any(not isinstance(period, str) for period in periods)
    ):
        return {"answer_class": "unknown"}
    if not isinstance(parsed["unit"], str):
        return {"answer_class": "unknown"}
    try:
        delta_source = _answer_decimal(parsed["delta_source"], "delta_source")
        delta_target = _answer_decimal(parsed["delta_target"], "delta_target")
    except ValueError:
        return {"answer_class": "unknown"}
    return {
        "answer_class": "parsed",
        "row": parsed["row"],
        "periods": periods,
        "delta_source": delta_source,
        "delta_target": delta_target,
        "unit": normalize_unit(parsed["unit"]),
    }


def score_prepared(prepared: PreparedItem, answer_text: str) -> dict[str, str]:
    answer = parse_answer(answer_text)
    if answer is None:
        return {"outcome": "unknown"}
    if answer["answer_class"] != "parsed":
        return {"outcome": answer["answer_class"]}
    if answer["row"] != prepared.row_label:
        return {"outcome": "wrong"}
    gold = prepared.gold
    if (
        answer["periods"] == [prepared.early_period, prepared.late_period]
        and answer["delta_source"] == -gold.delta_source
        and answer["delta_target"] == -gold.delta_target
    ):
        return {"outcome": "correct_other_form"}
    if answer["periods"] != [prepared.late_period, prepared.early_period]:
        return {"outcome": "wrong_period"}
    source_correct = answer["delta_source"] == gold.delta_source
    target_correct = answer["delta_target"] == gold.delta_target
    if source_correct and not target_correct:
        return {"outcome": "wrong_unit"}
    if source_correct and target_correct and answer["unit"] == gold.target_unit:
        return {"outcome": "correct"}
    return {"outcome": "wrong"}


def score_item(item: Mapping[str, Any], answer_text: str) -> dict[str, str]:
    prepared = prepare_item(item)
    return score_prepared(prepared, answer_text)


def apply_regression(base_outcome: str, arm_outcome: str) -> str:
    if (
        base_outcome in CORRECT_OUTCOMES
        and arm_outcome not in CORRECT_OUTCOMES
        and arm_outcome not in {"refused", "unknown"}
    ):
        return "regressed"
    return arm_outcome


def aggregate_outcomes(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    records_by_arm: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        required = {"origin_id", "item_id", "arm", "outcome"}
        if not required.issubset(record):
            raise ValueError(f"record is missing fields: {sorted(required - set(record))}")
        records_by_arm[str(record["arm"])].append(record)
    arms: dict[str, Any] = {}
    for arm in sorted(records_by_arm):
        arm_records = records_by_arm[arm]
        outcomes = Counter(str(record["outcome"]) for record in arm_records)
        correct_count = sum(outcomes[outcome] for outcome in CORRECT_OUTCOMES)
        total = len(arm_records)
        arms[arm] = {
            "total": total,
            "origin_count": len({str(record["origin_id"]) for record in arm_records}),
            "outcome_counts": dict(sorted(outcomes.items())),
            "correct_count": correct_count,
            "correct_rate": correct_count / total if total else None,
        }
    return {
        "record_count": sum(len(value) for value in records_by_arm.values()),
        "arms": arms,
    }


def _origin_rates(
    records: Iterable[Mapping[str, Any]], arm: str
) -> dict[str, tuple[int, int]]:
    values: dict[str, list[int]] = defaultdict(list)
    for record in records:
        if str(record["arm"]) != arm:
            continue
        is_correct = str(record["outcome"]) in CORRECT_OUTCOMES
        values[str(record["origin_id"])].append(int(is_correct))
    return {
        origin: (sum(observations), len(observations))
        for origin, observations in values.items()
    }


def paired_origin_differences(
    records: Iterable[Mapping[str, Any]],
    left_arm: str,
    right_arm: str,
) -> dict[str, Any]:
    materialized = [dict(record) for record in records]
    left = _origin_rates(materialized, left_arm)
    right = _origin_rates(materialized, right_arm)
    origins = sorted(set(left) | set(right))
    differences: list[dict[str, Any]] = []
    for origin in origins:
        left_count, left_total = left.get(origin, (0, 0))
        right_count, right_total = right.get(origin, (0, 0))
        left_rate = left_count / left_total if left_total else None
        right_rate = right_count / right_total if right_total else None
        delta_pp = (
            (left_rate - right_rate) * 100
            if left_rate is not None and right_rate is not None
            else None
        )
        differences.append(
            {
                "origin_id": origin,
                "left_correct": left_count,
                "left_total": left_total,
                "right_correct": right_count,
                "right_total": right_total,
                "left_rate": left_rate,
                "right_rate": right_rate,
                "delta_pp": delta_pp,
            }
        )
    comparable = [row["delta_pp"] for row in differences if row["delta_pp"] is not None]
    return {
        "left_arm": left_arm,
        "right_arm": right_arm,
        "origin_count": len(origins),
        "origin_differences": differences,
        "mean_delta_pp": (
            sum(comparable) / len(comparable) if comparable else None
        ),
        "net_positive_origins": sum(value > 0 for value in comparable),
        "net_negative_origins": sum(value < 0 for value in comparable),
        "tied_origins": sum(value == 0 for value in comparable),
    }
