"""Five-layer, zero-model scoring contract for the immutable first batch."""

from __future__ import annotations

import json
import math
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


ARMS = ("table_top3", "table_top5", "table_all")
TEXT_KEYS = frozenset(
    {"answer", "numeric_value", "unit", "evidence_refs", "unknown", "clarification"}
)
NUMBER_RE = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?")
POSITIVE_NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
REFERENCE_RE = re.compile(r"^(?:P[1-9]\d*|TABLE:C\d+|TABLE:R\d+:C\d+)$")
STOPWORDS = frozenset(
    "what is the of for in and to how many did have their costs included within from between".split()
)


@dataclass(frozen=True)
class Table:
    columns: dict[int, str]
    rows: dict[int, dict[int, str]]
    row_labels: dict[int, str]


@dataclass(frozen=True)
class VisibleContext:
    paragraphs: dict[int, dict[str, str]]
    raw_orders: set[str]
    table: Table


def parse_decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        if not math.isfinite(float(value)):
            return None
        return Decimal(str(value))
    if not isinstance(value, str):
        return None
    text = value.strip().replace(",", "")
    text = re.sub(r"^[ $£€]+", "", text)
    text = text.strip()
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]
    match = re.fullmatch(r"[-+]?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        number = Decimal(text)
    except InvalidOperation:
        return None
    return -number if negative and number > 0 else number


def numeric_close(left: Any, right: Any, tolerance: Decimal = Decimal("0.000001")) -> bool:
    left_number = parse_decimal(left)
    right_number = parse_decimal(right)
    if left_number is None or right_number is None:
        return False
    return abs(left_number - right_number) <= tolerance * max(
        Decimal(1), abs(left_number), abs(right_number)
    )


def normalize_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.rstrip(".")


def answer_tokens(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return list(value)
    return []


def extract_numbers(value: Any) -> list[Decimal]:
    numbers: list[Decimal] = []
    for token in answer_tokens(value):
        for match in NUMBER_RE.finditer(token):
            number = parse_decimal(match.group(0))
            if number is not None:
                numbers.append(number)
    return numbers


def parse_table(text: str) -> Table:
    lines = [line for line in text.splitlines() if line.strip()]
    columns: dict[int, str] = {}
    if lines:
        for match in re.finditer(r"C(\d+)=(.*?)(?= \| C\d+=|$)", lines[0]):
            columns[int(match.group(1))] = match.group(2).strip()
    rows: dict[int, dict[int, str]] = {}
    row_labels: dict[int, str] = {}
    for line in lines[1:]:
        row_match = re.match(r"R(\d+)\s+\[(.*?)\]\s+(.*)$", line)
        if not row_match:
            continue
        row_index = int(row_match.group(1))
        row_labels[row_index] = row_match.group(2).strip()
        cells: dict[int, str] = {}
        body = row_match.group(3)
        for match in re.finditer(r"C(\d+)=(.*?)(?= \| C\d+=|$)", body):
            cells[int(match.group(1))] = match.group(2).strip()
        rows[row_index] = cells
    return Table(columns=columns, rows=rows, row_labels=row_labels)


def load_visible_context(
    source_record: dict[str, Any],
    reference: dict[str, Any],
    selected_raw_orders: list[str],
) -> VisibleContext:
    selected = set(str(item) for item in selected_raw_orders)
    paragraphs = sorted(
        (item for item in source_record["paragraphs"] if str(item["order"]) in selected),
        key=lambda item: int(item["order"]),
    )
    mapped = {
        index: {
            "raw_order": str(item["order"]),
            "text": str(item["text"]),
            "uid": str(item["uid"]),
        }
        for index, item in enumerate(paragraphs, start=1)
    }
    return VisibleContext(
        paragraphs=mapped,
        raw_orders=selected,
        table=parse_table(reference["table_text"]),
    )


def strict_layer(response_text: str, reference: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError as exc:
        return {
            "status": "STRICT_FAIL",
            "reason": f"invalid_json:{exc.msg}",
            "parsed": None,
        }
    if not isinstance(payload, dict) or set(payload) != TEXT_KEYS:
        return {
            "status": "STRICT_FAIL",
            "reason": "schema_keys_mismatch",
            "parsed": None,
        }
    answer = payload["answer"]
    numeric_value = payload["numeric_value"]
    unit = payload["unit"]
    refs = payload["evidence_refs"]
    unknown = payload["unknown"]
    clarification = payload["clarification"]
    errors: list[str] = []
    if not (
        isinstance(answer, str)
        or (isinstance(answer, list) and bool(answer) and all(isinstance(x, str) and x for x in answer))
    ):
        errors.append("invalid_answer")
    if numeric_value is not None and (
        isinstance(numeric_value, bool)
        or not isinstance(numeric_value, (int, float))
        or not math.isfinite(float(numeric_value))
    ):
        errors.append("invalid_numeric_value_type")
    if not isinstance(unit, str) or not unit:
        errors.append("invalid_unit")
    if not isinstance(refs, list) or not all(isinstance(item, str) for item in refs):
        errors.append("invalid_evidence_refs_type")
    if not isinstance(unknown, bool):
        errors.append("invalid_unknown_type")
    if not isinstance(clarification, str):
        errors.append("invalid_clarification_type")
    if unknown:
        if not (isinstance(answer, str) and answer == "UNKNOWN"):
            errors.append("unknown_answer_contract")
        if numeric_value is not None:
            errors.append("unknown_numeric_contract")
        if refs:
            errors.append("unknown_reference_contract")
        if unit != "UNKNOWN":
            errors.append("unknown_unit_contract")
        if not clarification:
            errors.append("unknown_clarification_required")
    else:
        if not refs:
            errors.append("evidence_refs_required")
        if any(not REFERENCE_RE.fullmatch(item) for item in refs):
            errors.append("invalid_evidence_reference_syntax")
        if numeric_value is not None and not isinstance(numeric_value, (int, float)):
            errors.append("numeric_array_contract")
    answer_type = reference["answer_type"]
    reference_is_singular_numeric = (
        answer_type in {"arithmetic", "count"}
        or (answer_type == "span" and parse_decimal(reference["answer"]) is not None)
    )
    if not unknown and reference_is_singular_numeric and numeric_value is None:
        errors.append("numeric_value_required")
    if answer_type == "count" and not unknown:
        count_value = parse_decimal(numeric_value)
        if count_value is None or count_value != count_value.to_integral_value() or count_value < 0:
            errors.append("count_must_be_nonnegative_integer")
    if errors:
        return {
            "status": "STRICT_FAIL",
            "reason": ";".join(sorted(set(errors))),
            "parsed": payload,
        }
    return {"status": "PASS", "reason": "strict_contract_satisfied", "parsed": payload}


def _reference_supports(expected: str, observed: str) -> str:
    if expected == observed:
        return "exact"
    if expected.startswith("TABLE:R") and observed.startswith("TABLE:C"):
        expected_column = expected.rsplit(":", 1)[-1]
        observed_column = observed.rsplit(":", 1)[-1]
        if expected_column == observed_column:
            return "broad"
    return "none"


def _find_numeric_cells(table: Table, numbers: list[Decimal]) -> set[str]:
    refs, _ = _find_numeric_cells_report(table, numbers, allow_partial=False)
    return refs


def _find_numeric_cells_report(
    table: Table,
    numbers: list[Decimal],
    allow_partial: bool,
) -> tuple[set[str], set[Decimal]]:
    refs: set[str] = set()
    found_numbers: set[Decimal] = set()
    for number in numbers:
        found = False
        for row_index, cells in table.rows.items():
            for column_index, cell in cells.items():
                if numeric_close(cell, number):
                    refs.add(f"TABLE:R{row_index}:C{column_index}")
                    found = True
        if not found:
            for column_index, cell in table.columns.items():
                if numeric_close(cell, number):
                    refs.add(f"TABLE:C{column_index}")
                    found = True
        if not found:
            if not allow_partial:
                return set(), set()
            continue
        found_numbers.add(number)
    return refs, found_numbers


def _find_text_cells(table: Table, expected: list[str]) -> set[str]:
    refs: set[str] = set()
    for item in expected:
        normalized = normalize_text(item)
        found = False
        for row_index, cells in table.rows.items():
            for column_index, cell in cells.items():
                if normalized and normalized in normalize_text(cell):
                    refs.add(f"TABLE:R{row_index}:C{column_index}")
                    found = True
        if not found:
            return set()
    return refs


def _count_header_refs(table: Table, program_items: list[str]) -> set[str]:
    refs: set[str] = set()
    for item in program_items:
        normalized = normalize_text(item)
        matches = [
            column_index
            for column_index, value in table.columns.items()
            if normalized == normalize_text(value)
        ]
        if len(matches) != 1:
            return set()
        refs.add(f"TABLE:C{matches[0]}")
    return refs


def _count_value_refs(
    reference: dict[str, Any],
    table: Table,
    program_items: list[str],
) -> set[str]:
    question_words = {
        word
        for word in re.findall(r"[a-z0-9.]+", reference["question"].casefold())
        if word not in STOPWORDS and len(word) > 2
    }
    scored_rows: list[tuple[int, int]] = []
    for row_index, label in table.row_labels.items():
        label_words = set(re.findall(r"[a-z0-9.]+", label.casefold()))
        overlap = len(question_words & label_words)
        if overlap:
            scored_rows.append((overlap, row_index))
    if not scored_rows:
        return set()
    best_overlap = max(score for score, _ in scored_rows)
    candidate_rows = [row for score, row in scored_rows if score == best_overlap]
    if len(candidate_rows) != 1:
        return set()
    row_index = candidate_rows[0]
    refs: set[str] = set()
    for item in program_items:
        normalized = normalize_text(item)
        columns = [
            column_index
            for column_index, value in table.columns.items()
            if normalized == normalize_text(value)
        ]
        if len(columns) != 1 or columns[0] not in table.rows[row_index]:
            return set()
        refs.add(f"TABLE:R{row_index}:C{columns[0]}")
    return refs


def reconstruct_expected_refs(
    reference: dict[str, Any],
    visible: VisibleContext,
) -> dict[str, Any]:
    answer_type = reference["answer_type"]
    source_requirement = reference["source_requirement"]
    required_raw_orders = {str(item["order"]) for item in reference.get("paragraphs", [])}
    if source_requirement in {"paragraph", "both"}:
        missing = required_raw_orders - visible.raw_orders
        if missing:
            return {
                "refs": set(),
                "reconstructible": False,
                "reason": "required_paragraph_not_visible",
                "missing_raw_orders": sorted(missing),
            }
        visible_indexes = [
            index
            for index, item in visible.paragraphs.items()
            if item["raw_order"] in required_raw_orders
        ]
        if not visible_indexes:
            return {
                "refs": set(),
                "reconstructible": False,
                "reason": "visible_paragraph_mapping_unavailable",
                "missing_raw_orders": sorted(required_raw_orders),
            }
        if source_requirement == "paragraph":
            return {
                "refs": {f"P{index}" for index in visible_indexes},
                "reconstructible": True,
                "reason": "required_visible_paragraph",
                "missing_raw_orders": [],
            }

    program = str(reference.get("program") or "")
    expected_values = reference["answer"]
    if answer_type == "count" and program:
        program_items = [item.strip() for item in program.split("##") if item.strip()]
        if source_requirement == "paragraph":
            refs = {f"P{index}" for index in visible_indexes}
        else:
            header_refs = _count_header_refs(visible.table, program_items)
            value_refs = _count_value_refs(reference, visible.table, program_items)
            refs = value_refs or header_refs
        return {
            "refs": refs,
            "reconstructible": bool(refs),
            "reason": "count_members_reconstructed",
            "missing_raw_orders": sorted(required_raw_orders - visible.raw_orders),
        }

    if answer_type in {"arithmetic", "count"} or (
        answer_type == "span" and parse_decimal(expected_values) is not None
    ):
        numbers = (
            extract_numbers(program)
            if answer_type == "arithmetic" and program
            else [parse_decimal(expected_values)]
        )
        if answer_type == "arithmetic":
            numbers = [number for number in numbers if number is not None]
        if not numbers:
            return {
                "refs": set(),
                "reconstructible": False,
                "reason": "numeric_reference_unavailable",
                "missing_raw_orders": sorted(required_raw_orders),
            }
        if source_requirement == "paragraph":
            refs = {f"P{index}" for index in visible_indexes}
            return {
                "refs": refs,
                "reconstructible": bool(refs),
                "reason": "arithmetic_operands_in_visible_paragraph",
                "missing_raw_orders": [],
            }
        refs, found_numbers = _find_numeric_cells_report(
            visible.table,
            numbers,
            allow_partial=answer_type == "arithmetic",
        )
        if answer_type == "arithmetic" and len(found_numbers) < min(2, len(numbers)):
            return {
                "refs": set(),
                "reconstructible": False,
                "reason": "numeric_reference_unavailable",
                "missing_raw_orders": sorted(required_raw_orders - visible.raw_orders),
            }
        return {
            "refs": refs,
            "reconstructible": bool(refs),
            "reason": "numeric_cells_reconstructed",
            "missing_raw_orders": sorted(required_raw_orders - visible.raw_orders),
        }

    expected_list = expected_values if isinstance(expected_values, list) else [expected_values]
    expected_text = [item for item in expected_list if isinstance(item, str)]
    if source_requirement == "paragraph" and expected_text:
        normalized_visible = " ".join(
            normalize_text(item["text"]) for item in visible.paragraphs.values()
        )
        if all(normalize_text(item) in normalized_visible for item in expected_text):
            refs = {
                f"P{index}"
                for index, item in visible.paragraphs.items()
                if any(normalize_text(value) in normalize_text(item["text"]) for value in expected_text)
            }
            return {
                "refs": refs,
                "reconstructible": bool(refs),
                "reason": "text_found_in_visible_paragraph",
                "missing_raw_orders": [],
            }
    numeric_values = [value for value in expected_list if parse_decimal(value) is not None]
    if numeric_values and len(numeric_values) == len(expected_list):
        refs = _find_numeric_cells(visible.table, numeric_values)
        return {
            "refs": refs,
            "reconstructible": bool(refs),
            "reason": "multi_span_numeric_cells_reconstructed",
            "missing_raw_orders": [],
        }
    refs = _find_text_cells(visible.table, expected_text)
    if not refs and source_requirement in {"paragraph", "both"} and expected_text:
        paragraph_matches = {
            f"P{index}"
            for index, item in visible.paragraphs.items()
            if all(normalize_text(value) in normalize_text(item["text"]) for value in expected_text)
        }
        refs = paragraph_matches
    return {
        "refs": refs,
        "reconstructible": bool(refs),
        "reason": "answer_spans_reconstructed",
        "missing_raw_orders": [],
    }


def answer_layer(payload: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    answer_type = reference["answer_type"]
    answer = payload["answer"]
    if payload.get("unknown"):
        return {"status": "PASS", "reason": "reasonable_unknown_declared"}
    expected = reference["answer"]
    if answer_type in {"arithmetic", "count"} or (
        answer_type == "span" and parse_decimal(expected) is not None
    ):
        numbers = extract_numbers(answer)
        expected_number = parse_decimal(expected)
        non_year_numbers = [
            number
            for number in numbers
            if not (Decimal(1900) <= number <= Decimal(2100) and number == number.to_integral_value())
        ]
        if expected_number is None or len(non_year_numbers) != 1:
            return {
                "status": "FAIL",
                "reason": "numeric_answer_not_complete_or_reduced",
                "observed": answer,
            }
        if not numeric_close(non_year_numbers[0], expected_number):
            return {
                "status": "FAIL",
                "reason": "numeric_answer_mismatch",
                "observed": answer,
            }
        return {"status": "PASS", "reason": "numeric_answer_complete"}

    expected_items = expected if isinstance(expected, list) else [expected]
    observed_items = answer if isinstance(answer, list) else [answer]
    expected_numbers = [parse_decimal(item) for item in expected_items]
    if expected_numbers and all(item is not None for item in expected_numbers):
        observed_numbers = extract_numbers(observed_items)
        if len(observed_numbers) != len(expected_numbers):
            return {
                "status": "FAIL",
                "reason": "multi_span_numeric_set_incomplete",
                "observed": answer,
            }
        if sorted(observed_numbers) != sorted(expected_numbers):
            return {
                "status": "FAIL",
                "reason": "multi_span_numeric_set_mismatch",
                "observed": answer,
            }
        return {"status": "PASS", "reason": "exact_numeric_set"}

    expected_set = {normalize_text(item) for item in expected_items}
    observed_set = {normalize_text(item) for item in observed_items}
    if observed_set != expected_set or len(observed_items) != len(expected_items):
        missing = sorted(expected_set - observed_set)
        extra = sorted(observed_set - expected_set)
        return {
            "status": "FAIL",
            "reason": "exact_text_set_mismatch",
            "missing": missing,
            "extra": extra,
            "observed": answer,
        }
    return {"status": "PASS", "reason": "exact_text_set"}


def _normalize_unit(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    normalized = normalize_text(value)
    aliases = {
        "$": "currency",
        "usd": "currency",
        "dollars": "currency",
        "percentage": "percent",
        "%": "percent",
        "pct": "percent",
        "thousands": "thousand",
        "thousand": "thousand",
        "$000": "thousand",
        "in thousands": "thousand",
        "unknown": "unknown",
        "": "unknown",
    }
    return aliases.get(normalized, normalized)


def _visible_unit_is_reconstructible(
    reference: dict[str, Any],
    visible: VisibleContext,
) -> bool:
    expected = _normalize_unit(reference.get("unit") or "")
    if expected in {"", "unknown"}:
        return True
    haystack = " ".join(
        [reference["table_text"]]
        + [item["text"] for item in visible.paragraphs.values()]
        + [reference["question"]]
    ).casefold()
    if expected == "percent":
        return "%" in haystack or "percent" in haystack or "percentage" in haystack
    if expected == "thousand":
        return any(
            marker in haystack
            for marker in ("in thousands", "$000", "000's", "amounts in thousands")
        )
    return expected in _normalize_unit(haystack)


def unit_layer(payload: dict[str, Any], reference: dict[str, Any], visible: VisibleContext) -> dict[str, Any]:
    if payload.get("unknown"):
        if not _visible_unit_is_reconstructible(reference, visible):
            return {"status": "REASONABLE_UNKNOWN", "reason": "required_scale_not_visible"}
        return {"status": "FAIL", "reason": "unsupported_unknown"}
    expected_unit = _normalize_unit(reference.get("unit") or "")
    observed_unit = _normalize_unit(payload["unit"])
    if expected_unit in {"", "unknown"}:
        if reference["answer_type"] in {"count", "multi-span"} or observed_unit in {"unknown", "currency", "thousand"}:
            return {"status": "PASS", "reason": "non_scale_unit_contract"}
        return {"status": "PASS", "reason": "dimensionless_reference"}
    if observed_unit == expected_unit:
        return {"status": "PASS", "reason": "unit_and_scale_match"}
    if not _visible_unit_is_reconstructible(reference, visible):
        return {
            "status": "PENDING_ADJUDICATION",
            "reason": "expected_scale_not_reconstructible_from_visible_evidence",
            "observed": payload["unit"],
            "expected": reference.get("unit") or "",
        }
    return {
        "status": "FAIL",
        "reason": "unit_or_scale_mismatch",
        "observed": payload["unit"],
        "expected": reference.get("unit") or "",
    }


def evidence_layer(
    payload: dict[str, Any],
    reference: dict[str, Any],
    visible: VisibleContext,
    reconstruction: dict[str, Any],
) -> dict[str, Any]:
    if payload.get("unknown"):
        if not reconstruction["reconstructible"]:
            return {"status": "REASONABLE_UNKNOWN", "reason": reconstruction["reason"]}
        return {"status": "FAIL", "reason": "unsupported_unknown_visible_evidence"}

    observed_refs = list(payload["evidence_refs"])
    for ref in observed_refs:
        if not REFERENCE_RE.fullmatch(ref):
            return {"status": "FAIL", "reason": "invalid_reference", "observed": ref}
        if ref.startswith("P"):
            index = int(ref[1:])
            if index not in visible.paragraphs:
                return {"status": "FAIL", "reason": "out_of_range_reference", "observed": ref}
        elif ":R" in ref:
            row_match = re.fullmatch(r"TABLE:R(\d+):C(\d+)", ref)
            assert row_match
            row_index, column_index = map(int, row_match.groups())
            if row_index not in visible.table.rows or column_index not in visible.table.rows[row_index]:
                return {"status": "FAIL", "reason": "nonexistent_reference", "observed": ref}
        else:
            column_index = int(ref.split(":C", 1)[1])
            if column_index not in visible.table.columns:
                return {"status": "FAIL", "reason": "nonexistent_reference", "observed": ref}

    if not reconstruction["reconstructible"]:
        if not observed_refs:
            return {"status": "FAIL", "reason": "evidence_refs_missing"}
        return {
            "status": "PENDING_ADJUDICATION",
            "reason": "legal_semantic_reference_not_reconstructible",
            "observed": observed_refs,
        }

    expected_refs = reconstruction["refs"]
    if not expected_refs:
        if reference["source_requirement"] in {"paragraph", "both"} and reconstruction.get(
            "missing_raw_orders"
        ):
            return {
                "status": "PENDING_ADJUDICATION",
                "reason": "required_scale_context_not_visible",
                "missing_raw_orders": reconstruction["missing_raw_orders"],
            }
        return {"status": "PENDING_ADJUDICATION", "reason": "semantic_reference_unavailable"}

    support: dict[str, str] = {}
    for expected in expected_refs:
        statuses = [_reference_supports(expected, observed) for observed in observed_refs]
        if "exact" in statuses:
            support[expected] = "exact"
        elif "broad" in statuses:
            support[expected] = "broad"
        else:
            support[expected] = "none"
    if any(status == "none" for status in support.values()):
        return {
            "status": "FAIL",
            "reason": "semantic_reference_mismatch",
            "expected": sorted(expected_refs),
            "observed": observed_refs,
            "support": support,
        }
    if all(status == "broad" for status in support.values()):
        return {
            "status": "PENDING_ADJUDICATION",
            "reason": "broad_reference_not_role_bound",
            "expected": sorted(expected_refs),
            "observed": observed_refs,
            "support": support,
        }
    return {
        "status": "PASS",
        "reason": "visible_reference_semantically_supports_answer",
        "expected": sorted(expected_refs),
        "observed": observed_refs,
        "support": support,
    }


def final_status(layers: dict[str, dict[str, Any]], payload: dict[str, Any], visible: VisibleContext, reconstruction: dict[str, Any]) -> dict[str, Any]:
    if layers["strict"]["status"] == "STRICT_FAIL":
        return {"status": "STRICT_FAIL", "reason": layers["strict"]["reason"]}
    if payload.get("unknown"):
        required_missing = bool(reconstruction.get("missing_raw_orders"))
        if required_missing or not reconstruction["reconstructible"]:
            return {"status": "REASONABLE_UNKNOWN", "reason": "required_evidence_not_visible"}
        return {"status": "REJECT", "reason": "unsupported_unknown"}
    if any(layers[name]["status"] == "FAIL" for name in ("answer", "numeric_unit", "evidence")):
        failed = [
            name
            for name in ("answer", "numeric_unit", "evidence")
            if layers[name]["status"] == "FAIL"
        ]
        return {"status": "REJECT", "reason": ";".join(f"{name}:{layers[name]['reason']}" for name in failed)}
    if any(layers[name]["status"] in {"PENDING_ADJUDICATION", "REASONABLE_UNKNOWN"} for name in layers):
        pending = [
            name
            for name, layer in layers.items()
            if layer["status"] in {"PENDING_ADJUDICATION", "REASONABLE_UNKNOWN"}
        ]
        return {
            "status": "PENDING_ADJUDICATION",
            "reason": ";".join(f"{name}:{layers[name]['reason']}" for name in pending),
        }
    return {"status": "ACCEPT", "reason": "all_five_layers_pass"}


def score_response(
    response_text: str,
    reference: dict[str, Any],
    visible: VisibleContext,
) -> dict[str, Any]:
    strict = strict_layer(response_text, reference)
    if strict["parsed"] is None:
        layers = {
            "strict": strict,
            "answer": {"status": "STRICT_FAIL", "reason": "unavailable_after_strict_failure"},
            "numeric_unit": {"status": "STRICT_FAIL", "reason": "unavailable_after_strict_failure"},
            "evidence": {"status": "STRICT_FAIL", "reason": "unavailable_after_strict_failure"},
            "final_delivery": {"status": "STRICT_FAIL", "reason": "unavailable_after_strict_failure"},
        }
        return {
            "status": "STRICT_FAIL",
            "layers": layers,
            "expected_reference_reconstruction": None,
        }
    payload = strict["parsed"]
    reconstruction = reconstruct_expected_refs(reference, visible)
    answer = answer_layer(payload, reference)
    unit_result = unit_layer(payload, reference, visible)
    singular_numeric_expected = (
        reference["answer_type"] in {"arithmetic", "count"}
        or (
            reference["answer_type"] == "span"
            and parse_decimal(reference["answer"]) is not None
        )
    )
    numeric_result: dict[str, Any] = {"status": "PASS", "reason": "numeric_value_not_applicable"}
    if singular_numeric_expected:
        expected_number = parse_decimal(reference["answer"])
        observed_number = parse_decimal(payload["numeric_value"])
        if expected_number is None or observed_number is None:
            numeric_result = {
                "status": "FAIL",
                "reason": "numeric_value_missing_or_non_numeric",
                "observed": payload["numeric_value"],
                "expected": reference["answer"],
            }
        elif numeric_close(observed_number, expected_number):
            numeric_result = {
                "status": "PASS",
                "reason": "signed_numeric_value_matches",
                "observed": payload["numeric_value"],
                "expected": reference["answer"],
            }
        else:
            numeric_result = {
                "status": "FAIL",
                "reason": "numeric_value_mismatch_or_direction",
                "observed": payload["numeric_value"],
                "expected": reference["answer"],
            }
    if numeric_result["status"] == "FAIL" or unit_result["status"] == "FAIL":
        numeric_unit = {
            "status": "FAIL",
            "reason": ";".join(
                item["reason"]
                for item in (numeric_result, unit_result)
                if item["status"] == "FAIL"
            ),
            "numeric": numeric_result,
            "unit": unit_result,
        }
    elif unit_result["status"] == "PENDING_ADJUDICATION":
        numeric_unit = {
            "status": "PENDING_ADJUDICATION",
            "reason": unit_result["reason"],
            "numeric": numeric_result,
            "unit": unit_result,
        }
    else:
        numeric_unit = {
            "status": "PASS",
            "reason": ";".join(
                item["reason"] for item in (numeric_result, unit_result)
            ),
            "numeric": numeric_result,
            "unit": unit_result,
        }
    evidence = evidence_layer(payload, reference, visible, reconstruction)
    layers = {
        "strict": strict,
        "answer": answer,
        "numeric_unit": numeric_unit,
        "evidence": evidence,
    }
    final = final_status(layers, payload, visible, reconstruction)
    layers["final_delivery"] = final
    return {
        "status": final["status"],
        "layers": layers,
        "expected_reference_reconstruction": {
            **reconstruction,
            "refs": sorted(reconstruction["refs"]) if isinstance(reconstruction.get("refs"), set) else reconstruction.get("refs"),
        },
    }


def load_source_records(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records: dict[str, dict[str, Any]] = {}
    for record in payload:
        table_uid = str(record["table"]["uid"])
        records[table_uid] = record
    return records
