#!/usr/bin/env python3
"""Deterministic utilities for history-collection qualification."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from typing import Any, Iterable


YEAR_PATTERN = re.compile(r"(19|20)\d{2}")
UNIT_PATTERN = re.compile(
    r"(%|\$|¥|£|€|EUR|USD|RMB|CNY|million|thousand|billion)",
    re.IGNORECASE,
)
SCALES = (("billion", 1e9), ("million", 1e6), ("thousand", 1e3), ("%", 1.0))


def normalize_text(value: Any) -> str:
    """Normalize whitespace while preserving signs, decimals, and punctuation."""
    text = unicodedata.normalize("NFKC", str(value))
    return " ".join(text.split())


def text_ngrams(value: Any, size: int = 5) -> set[str]:
    text = normalize_text(value).lower()
    if not text:
        return set()
    if len(text) < size:
        return {text}
    return {text[index:index + size] for index in range(len(text) - size + 1)}


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Any) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_numeric(value: Any) -> float | None:
    text = normalize_text(value).replace(",", "")
    text = re.sub(r"[−–—－]", "-", text)
    negative_parentheses = text.startswith("(") and text.endswith(")")
    text = text[1:-1] if negative_parentheses else text
    if not re.fullmatch(r"-?\d+(\.\d+)?", text):
        return None
    number = float(text)
    if negative_parentheses and number > 0:
        return -number
    return number


def header_scale(header: str) -> str | None:
    for name, _ in SCALES:
        if re.search(name, header, re.IGNORECASE):
            return name
    if re.search(r"[$¥£€]", header):
        return "currency"
    return None


def table_rows(table: list[list[Any]]) -> list[list[Any]]:
    return [row if isinstance(row, list) else [row] for row in table]


def record_vectors(record: dict[str, Any]) -> tuple[set[str], set[str]]:
    rows = table_rows(record["table"]["table"])
    cells = [cell for row in rows for cell in row]
    paragraphs = [
        item.get("text", "") if isinstance(item, dict) else str(item)
        for item in record.get("paragraphs", [])
    ]
    table_grams: set[str] = set()
    paragraph_grams: set[str] = set()
    for cell in cells:
        table_grams.update(text_ngrams(cell))
    for paragraph in paragraphs:
        paragraph_grams.update(text_ngrams(paragraph))
    return table_grams, paragraph_grams


def task_eligibility(record: dict[str, Any]) -> dict[str, Any]:
    table = record["table"]["table"]
    if not isinstance(table, list) or len(table) < 2:
        return {"eligible": False, "reason": "table_too_short"}
    rows = table_rows(table)
    headers = [str(cell) for cell in rows[0]]
    periods = [(index, value) for index, value in enumerate(headers) if YEAR_PATTERN.search(value)]
    if len(periods) < 2:
        return {"eligible": False, "reason": "fewer_than_two_periods"}
    unit_columns = [index for index, value in enumerate(headers) if UNIT_PATTERN.search(value)]
    if not unit_columns:
        return {"eligible": False, "reason": "no_unit_marker"}
    usable_rows = []
    for row_index, row in enumerate(rows[1:], start=1):
        values = []
        for column_index, _ in periods:
            value = parse_numeric(row[column_index]) if column_index < len(row) else None
            if value is not None:
                values.append({"column": column_index, "value": value})
        if len(values) >= 2:
            usable_rows.append({"row_index": row_index, "period_values": values})
    if not usable_rows:
        return {"eligible": False, "reason": "no_two_parseable_period_values"}
    return {
        "eligible": True,
        "period_columns": [index for index, _ in periods],
        "period_labels": [label for _, label in periods],
        "unit_columns": unit_columns,
        "usable_rows": usable_rows,
    }


def cosine_proxy(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    intersection = len(left & right)
    return intersection / math.sqrt(len(left) * len(right))


def unique_preserving_order(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))
