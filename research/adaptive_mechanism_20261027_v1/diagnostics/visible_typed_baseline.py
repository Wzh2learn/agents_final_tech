#!/usr/bin/env python3
"""Visible-only typed reduction baseline for the immutable first batch."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

from research.adaptive_mechanism_20261027_v1.persistent_budget.shared_tools import (
    normalize_answer,
    safe_calculate,
)
from research.adaptive_mechanism_20261027_v1.scoring_v2.scorer import (
    ARMS,
    VisibleContext,
    load_source_records,
    load_visible_context,
    parse_decimal,
    score_response,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = Path(__file__).resolve().parent / "results"
HISTORICAL_ROOT = (
    REPOSITORY_ROOT
    / "research"
    / "publication_proxy_calibration_20261026_v1"
)
DEFAULT_RAW = HISTORICAL_ROOT / "raw/runs/compliant_primary/P2_GENERATIONS.raw.jsonl"
DEFAULT_ANNOTATED = (
    HISTORICAL_ROOT / "raw/runs/compliant_primary/P2_GENERATIONS.annotated.jsonl"
)
DEFAULT_REFERENCE = (
    HISTORICAL_ROOT / "p2_proxy_calibration/receipts/P2_REFERENCE_CHAIN.json"
)
DEFAULT_SOURCE = Path(
    "/home/testuser/wzh/projects/agents_final_tech/data/research/"
    "tatqa_raw_2026/tatqa_dataset_dev.json"
)
QUESTION_STOPWORDS = frozenset(
    """
    a an and are as at be between by did do for from has have how in is its
    many of on or that the their this to was were what within from
    """
    .split()
)
SCALE_MARKERS = {
    "in thousands": "thousands",
    "amounts in thousands": "thousands",
    "$000's": "thousands",
    "000's": "thousands",
    "net sales (in thousands)": "thousands",
    "in millions": "millions",
    "amounts in millions": "millions",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def payload(
    answer: str | list[str],
    numeric_value: int | float | None,
    unit: str,
    evidence_refs: list[str],
) -> str:
    return json.dumps(
        {
            "answer": answer,
            "numeric_value": numeric_value,
            "unit": unit,
            "evidence_refs": evidence_refs,
            "unknown": False,
            "clarification": "",
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def unknown_payload(reason: str) -> str:
    return json.dumps(
        {
            "answer": "UNKNOWN",
            "numeric_value": None,
            "unit": "UNKNOWN",
            "evidence_refs": [],
            "unknown": True,
            "clarification": reason,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def question_words(question: str) -> set[str]:
    return {
        word
        for word in re.findall(r"[a-z0-9.]+", question.casefold())
        if word not in QUESTION_STOPWORDS and len(word) > 1
    }


def find_row(context: VisibleContext, question: str) -> int | None:
    wanted = question_words(question)
    scored: list[tuple[int, int]] = []
    for row_index, label in context.table.row_labels.items():
        numeric_cells = [
            parse_decimal(value)
            for column_index, value in context.table.rows.get(row_index, {}).items()
            if column_index > 0 and value
        ]
        if not any(value is not None for value in numeric_cells):
            continue
        label_words = set(re.findall(r"[a-z0-9.]+", label.casefold()))
        overlap = len(wanted & label_words)
        if overlap:
            scored.append((overlap, row_index))
    if not scored:
        return None
    best = max(score for score, _ in scored)
    candidates = [row_index for score, row_index in scored if score == best]
    return min(candidates)


def column_years(context: VisibleContext) -> dict[int, int]:
    years: dict[int, int] = {}
    values_by_column: dict[int, list[str]] = defaultdict(list)
    for column_index, value in context.table.columns.items():
        values_by_column[column_index].append(value)
    for cells in context.table.rows.values():
        for column_index, value in cells.items():
            values_by_column[column_index].append(value)
    for column_index, values in values_by_column.items():
        matches = [
            int(match.group(0))
            for value in values
            for match in re.finditer(r"\b(?:19|20)\d{2}\b", value)
        ]
        if matches:
            years[column_index] = min(matches)
    return years


def columns_for_question_years(context: VisibleContext, question: str) -> list[int]:
    years = column_years(context)
    requested = [
        int(year)
        for year in re.findall(r"\b(?:19|20)\d{2}\b", question)
    ]
    if not requested:
        return sorted(years)
    return [column for column, year in sorted(years.items()) if year in requested]


def chronological_columns(context: VisibleContext) -> list[int]:
    years = column_years(context)
    return [column for _, column in sorted((year, column) for column, year in years.items())]


def ordered_question_columns(context: VisibleContext, question: str) -> list[int]:
    years = column_years(context)
    requested = [
        int(year)
        for year in re.findall(r"\b(?:19|20)\d{2}\b", question)
    ]
    selected: list[int] = []
    for year in sorted(set(requested)):
        candidates = [
            column for column, candidate_year in years.items() if candidate_year == year
        ]
        closing = [
            column
            for column in candidates
            if "january 1"
            not in " ".join(
                [context.table.columns.get(column, "")]
                + [
                    context.table.rows[row_index].get(column, "")
                    for row_index in sorted(context.table.rows)
                ]
            ).casefold()
        ]
        selected.append((closing or candidates)[0])
    return selected


def visible_haystack(context: VisibleContext) -> str:
    return " ".join(
        [str(value) for value in context.table.columns.values()]
        + [cell for cells in context.table.rows.values() for cell in cells.values()]
        + [item["text"] for item in context.paragraphs.values()]
    ).casefold()


def infer_scale(context: VisibleContext, question: str) -> str | None:
    lowered_question = question.casefold()
    if "percentage" in lowered_question or "percent" in lowered_question:
        return "percent"
    haystack = visible_haystack(context)
    for marker, unit in SCALE_MARKERS.items():
        if marker in haystack:
            return unit
    return None


def format_decimal(value: Decimal) -> str:
    rendered = format(value, "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered


def cell_ref(row_index: int, column_index: int) -> str:
    return f"TABLE:R{row_index}:C{column_index}"


def reduce_mean(context: VisibleContext, question: str) -> str | None:
    row_index = find_row(context, question)
    columns = ordered_question_columns(context, question)
    if row_index is None or len(columns) < 2:
        return None
    operands = [
        parse_decimal(context.table.rows[row_index].get(column_index))
        for column_index in columns[:2]
    ]
    if any(value is None for value in operands):
        return None
    expression = f"({operands[0]}+{operands[1]})/2"
    result = Decimal(str(safe_calculate(expression))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    unit = infer_scale(context, question)
    if unit is None:
        return unknown_payload("required scale is not visible")
    refs = [cell_ref(row_index, column_index) for column_index in columns[:2]]
    return payload(format_decimal(result), float(result), unit, refs)


def reduce_change(context: VisibleContext, question: str) -> str | None:
    row_index = find_row(context, question)
    columns = ordered_question_columns(context, question)
    if row_index is None or len(columns) < 2:
        return None
    earlier = parse_decimal(context.table.rows[row_index].get(columns[0]))
    later = parse_decimal(context.table.rows[row_index].get(columns[1]))
    if earlier is None or later is None or earlier == 0:
        return None
    if "percentage" in question.casefold():
        expression = f"({later}-{earlier})/{earlier}*100"
        unit = "percent"
    else:
        expression = f"({later}-{earlier})"
        unit = infer_scale(context, question) or "unknown"
    result = Decimal(str(safe_calculate(expression))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    refs = [cell_ref(row_index, column_index) for column_index in columns[:2]]
    return payload(format_decimal(result), float(result), unit, refs)


def reduce_paragraph_percentage(context: VisibleContext, question: str) -> str | None:
    for index, item in context.paragraphs.items():
        text = item["text"]
        later_match = re.search(
            r"\$\s*([0-9]+(?:\.[0-9]+)?)\s*million in total",
            text,
            flags=re.IGNORECASE,
        )
        earlier_match = re.search(
            r"\b(20\d{2})\s*\$\s*([0-9]+(?:\.[0-9]+)?)\s*million",
            text,
            flags=re.IGNORECASE,
        )
        if not later_match or not earlier_match:
            continue
        later = Decimal(later_match.group(1))
        earlier = Decimal(earlier_match.group(2))
        expression = f"({later}-{earlier})/{earlier}*100"
        result = Decimal(str(safe_calculate(expression))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return payload(format_decimal(result), float(result), "percent", [f"P{index}"])
    return None


def count_roman_services(context: VisibleContext) -> str | None:
    marker_re = re.compile(r"\((i{1,3}|iv|v|vi{0,3}|ix|x)\)", flags=re.IGNORECASE)
    for index, item in context.paragraphs.items():
        matches = list(marker_re.finditer(item["text"]))
        if len(matches) < 2:
            continue
        count = len(matches)
        return payload(str(count), count, "count", [f"P{index}"])
    return unknown_payload("visible context does not contain the enumerated service list")


def count_table_threshold(context: VisibleContext, question: str) -> str | None:
    row_index = find_row(context, question)
    threshold_match = re.search(r"\$?\s*([0-9]+(?:\.[0-9]+)?)", question)
    if row_index is None or threshold_match is None:
        return None
    threshold = Decimal(threshold_match.group(1))
    section_start = 1
    for candidate in range(1, row_index):
        label = context.table.row_labels.get(candidate, "")
        if re.fullmatch(r"(?:19|20)\d{2}", label.strip()):
            section_start = candidate
    section_end = row_index
    for candidate in range(row_index + 1, max(context.table.rows) + 1):
        label = context.table.row_labels.get(candidate, "")
        if re.fullmatch(r"(?:19|20)\d{2}", label.strip()):
            section_end = candidate
            break
    columns = sorted(
        column
        for column in context.table.columns
        if all(
            column in context.table.rows.get(candidate, {})
            for candidate in range(section_start, section_end)
        )
    )
    selected: list[int] = []
    for column_index in columns:
        value = parse_decimal(context.table.rows[row_index].get(column_index))
        if value is not None and value > threshold:
            selected.append(column_index)
    if not selected:
        return None
    count = len(selected)
    refs = [f"TABLE:C{column_index}" for column_index in selected]
    return payload(str(count), count, "count", refs)


def extract_service_list(text: str) -> list[str] | None:
    marker_re = re.compile(r"\((i{1,3}|iv|v|vi{0,3}|ix|x)\)", flags=re.IGNORECASE)
    matches = list(marker_re.finditer(text))
    if len(matches) < 2:
        return None
    services: list[str] = []
    for position, match in enumerate(matches):
        start = match.end()
        end = matches[position + 1].start() if position + 1 < len(matches) else len(text)
        segment = text[start:end]
        if position + 1 == len(matches):
            segment = re.split(r"\.\s*(?=[A-Z])", segment, maxsplit=1)[0]
        segment = segment.strip().strip(",;")
        segment = re.sub(r"^(?:and|or)\s+", "", segment, flags=re.IGNORECASE)
        segment = re.sub(r"\s+(?:and|or)$", "", segment, flags=re.IGNORECASE)
        segment = segment.strip().strip(",;")
        segment = segment.rstrip(".")
        services.append(segment)
    return services


def extract_paragraph_services(context: VisibleContext) -> str | None:
    for index, item in context.paragraphs.items():
        services = extract_service_list(item["text"])
        if services:
            return payload(services, None, "UNKNOWN", [f"P{index}"])
    return unknown_payload("visible context does not contain the enumerated service list")


def numeric_span(context: VisibleContext, question: str) -> str | None:
    row_index = find_row(context, question)
    years = column_years(context)
    requested = [
        int(year)
        for year in re.findall(r"\b(?:19|20)\d{2}\b", question)
    ]
    columns = [
        column
        for year, column in sorted((year, column) for column, year in years.items())
        if not requested or year in requested
    ]
    if row_index is None or len(columns) != 1:
        return None
    column_index = columns[0]
    raw_value = context.table.rows[row_index].get(column_index)
    value = parse_decimal(raw_value)
    unit = infer_scale(context, question)
    if value is None:
        return None
    if unit is None:
        return unknown_payload("required numeric scale is not visible")
    return payload(
        str(raw_value),
        float(value),
        unit,
        [cell_ref(row_index, column_index)],
    )


def numeric_multi_span(context: VisibleContext, question: str) -> str | None:
    row_index = find_row(context, question)
    columns = columns_for_question_years(context, question)
    if row_index is None or not columns:
        return None
    answers: list[str] = []
    values: list[Decimal] = []
    for column_index in columns:
        raw_value = context.table.rows[row_index].get(column_index)
        value = parse_decimal(raw_value)
        if value is None:
            return None
        answers.append(str(raw_value))
        values.append(value)
    unit = infer_scale(context, question)
    if unit is None:
        return unknown_payload("required numeric scale is not visible")
    return payload(
        answers,
        float(values[0]) if len(values) == 1 else None,
        unit,
        [cell_ref(row_index, column_index) for column_index in columns],
    )


def paragraph_unit(context: VisibleContext, question: str) -> str | None:
    for index, item in context.paragraphs.items():
        match = re.search(r"\((in [a-z]+)\)", item["text"], flags=re.IGNORECASE)
        if match:
            answer = match.group(1)
            return payload(answer, None, answer, [f"P{index}"])
    return unknown_payload("visible context does not state the table unit")


def investment_components(context: VisibleContext) -> str | None:
    rows: list[tuple[int, str]] = []
    final_index: int | None = None
    for row_index, label in context.table.row_labels.items():
        if "at end of the period" in normalize_answer(label):
            final_index = row_index
            break
        cells = context.table.rows.get(row_index, {})
        numeric_cells = [
            parse_decimal(value)
            for column_index, value in cells.items()
            if column_index > 0 and value
        ]
        if numeric_cells and all(value is not None for value in numeric_cells):
            rows.append((row_index, label))
    if final_index is None or not rows:
        return None
    contributing = [(row_index, label) for row_index, label in rows if row_index < final_index]
    if not contributing:
        return None
    return payload(
        [label for _, label in contributing],
        None,
        "UNKNOWN",
        [f"TABLE:R{row_index}:C0" for row_index, _ in contributing],
    )


def answer_from_visible(
    question: str,
    answer_type: str,
    context: VisibleContext,
) -> str:
    lowered = question.casefold()
    if answer_type == "count":
        if "service" in lowered:
            result = count_roman_services(context)
        else:
            result = count_table_threshold(context, question)
    elif answer_type == "multi-span":
        if "service" in lowered:
            result = extract_paragraph_services(context)
        elif "components factored" in lowered:
            result = investment_components(context)
        else:
            result = numeric_multi_span(context, question)
    elif answer_type == "span":
        if "unit" in lowered:
            result = paragraph_unit(context, question)
        else:
            result = numeric_span(context, question)
    elif "percentage change" in lowered or re.search(r"\bchange\b", lowered):
        paragraph_result = reduce_paragraph_percentage(context, question)
        if isinstance(paragraph_result, str) and json.loads(paragraph_result).get("unknown") is False:
            result = paragraph_result
        else:
            result = reduce_change(context, question)
    elif "average" in lowered or "mean" in lowered:
        result = reduce_mean(context, question)
    else:
        result = None
    if result is None:
        return unknown_payload("visible typed reduction is not deterministically reconstructible")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--annotated", type=Path, default=DEFAULT_ANNOTATED)
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()

    raw_rows = read_jsonl(args.raw)
    annotated = {row["call_id"]: row for row in read_jsonl(args.annotated)}
    references_payload = json.loads(args.reference.read_text(encoding="utf-8"))
    references = references_payload["rows"]
    uid_by_hash = {
        hashlib.sha256(row["question_uid"].encode("utf-8")).hexdigest(): row["question_uid"]
        for row in references
    }
    reference_by_uid = {row["question_uid"]: row for row in references}
    source_records = load_source_records(args.source)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in raw_rows:
        grouped[(row["question_uid_sha256"], row["arm"])].append(row)

    rows: list[dict[str, Any]] = []
    for (uid_hash, arm), attempts in sorted(grouped.items()):
        raw = max(attempts, key=lambda item: int(item["call_number"]))
        uid = uid_by_hash[uid_hash]
        reference = reference_by_uid[uid]
        selected_orders = raw.get(
            "selected_paragraph_orders",
            annotated[raw["call_id"]]["selected_paragraph_orders"],
        )
        visible = load_visible_context(
            source_records[reference["table_uid"]],
            reference,
            selected_orders,
        )
        response_text = answer_from_visible(
            reference["question"],
            reference["answer_type"],
            visible,
        )
        score = score_response(response_text, reference, visible)
        rows.append(
            {
                "schema": "visible_typed_baseline_row_v1",
                "question_uid": uid,
                "question": reference["question"],
                "answer_type": reference["answer_type"],
                "arm": arm,
                "call_id": raw["call_id"],
                "call_number": raw["call_number"],
                "visible_paragraph_orders": sorted(visible.raw_orders, key=int),
                "response": json.loads(response_text),
                "score": score,
                "actor_inputs": [
                    "question",
                    "answer_type",
                    "visible selected paragraphs",
                    "visible table",
                ],
                "forbidden_actor_inputs": [
                    "gold answer",
                    "expected evidence",
                    "hidden unit",
                    "UID branch",
                    "expected program",
                ],
            }
        )

    status_counts = Counter(row["score"]["status"] for row in rows)
    per_uid: list[dict[str, Any]] = []
    grouped_uid: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped_uid[row["question_uid"]][row["arm"]] = row
    for uid in sorted(grouped_uid):
        arm_rows = grouped_uid[uid]
        per_uid.append(
            {
                "question_uid": uid,
                "question": arm_rows[ARMS[0]]["question"],
                "answer_type": arm_rows[ARMS[0]]["answer_type"],
                "status_by_arm": {
                    arm: arm_rows[arm]["score"]["status"] for arm in ARMS
                },
                "typed_operation_by_arm": {
                    arm: arm_rows[arm]["score"]["layers"]["answer"].get("reason")
                    for arm in ARMS
                },
                "evidence_by_arm": {
                    arm: arm_rows[arm]["score"]["layers"]["evidence"].get("reason")
                    for arm in ARMS
                },
            }
        )

    payload_out = {
        "schema": "visible_typed_baseline_result_v1",
        "status": "COMPLETE_ZERO_MODEL_FIRST_BATCH_VISIBLE_BASELINE",
        "review_identity": (
            "AI/automatic deterministic baseline evaluation; not human gold, "
            "not a model run, and not new-source validation"
        ),
        "model_calls": 0,
        "training_runs": 0,
        "generation_records_created": 0,
        "baseline_boundary": (
            "The actor function receives only the question, answer type and visible "
            "selected paragraphs/table; reference answers and expected programs are "
            "used only after output for five-layer scoring."
        ),
        "source_hashes": {
            "raw_jsonl": sha256(args.raw),
            "annotated_jsonl": sha256(args.annotated),
            "reference_chain": sha256(args.reference),
            "tatqa_dev_source": sha256(args.source),
        },
        "row_count": len(rows),
        "status_counts": dict(sorted(status_counts.items())),
        "per_uid": per_uid,
        "rows": rows,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(args.output / "VISIBLE_TYPED_BASELINE.json", payload_out)
    (args.output / "VISIBLE_TYPED_BASELINE_ROWS.jsonl").write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": payload_out["status"],
                "rows": len(rows),
                "status_counts": payload_out["status_counts"],
                "model_calls": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
