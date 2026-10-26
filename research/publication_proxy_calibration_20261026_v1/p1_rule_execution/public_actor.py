#!/usr/bin/env python3
"""Deterministic public actor for the frozen P1 visible-rule regression.

Runtime visibility is deliberately limited to ``question`` and the complete
rendered ``table_text``. No expected answer, program, evidence reference,
task identity, hidden scale, ledger, or per-case branch is accepted.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any, Iterable


VISIBLE_RULES = (
    "1_visible_completeness",
    "2_explicit_period_binding",
    "3_change_direction",
    "4_inclusive_range",
    "5_label_scope",
    "6_numeric_reference_validation",
)

TEMPORAL_WORDS = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "between",
    "by",
    "change",
    "company",
    "difference",
    "for",
    "from",
    "in",
    "increase",
    "decrease",
    "nominal",
    "of",
    "on",
    "paid",
    "reported",
    "the",
    "to",
    "total",
    "was",
    "were",
    "what",
    "with",
}

SECTION_HEADING_RE = re.compile(r"[A-Z][A-Za-z0-9 &/()'’-]+:\s*$")
ROW_RE = re.compile(r"^(R\d+) \[(.*?)\] (.*)$")
COLUMN_RE = re.compile(r"(C\d+)=(.*?)(?=(?:\s*\|\s*)C\d+=|\s*$)")
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
DATE_RE = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{1,2},\s+(?:19|20)\d{2}\b",
    re.IGNORECASE,
)
QUARTER_RE = re.compile(
    r"\b(?:first|second|third|fourth)\s+quarter\b", re.IGNORECASE
)


@dataclass(frozen=True)
class Cell:
    ref: str
    row_id: str
    row_label: str
    column_id: str
    raw: str
    value: float | None


@dataclass(frozen=True)
class TableRow:
    row_id: str
    label: str
    cells: dict[str, Cell]


@dataclass(frozen=True)
class ParsedTable:
    column_context: dict[str, str]
    rows: list[TableRow]
    cells: dict[str, Cell]


def _split_cells(body: str) -> list[tuple[str, str]]:
    return [(column, raw.strip()) for column, raw in COLUMN_RE.findall(body)]


def parse_numeric(raw: Any) -> float | None:
    text = str(raw).strip()
    if text in {"", "-", "–", "—", "n/a", "N/A"}:
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("() ")
    text = re.sub(r"(?<=\d),(?=\d)", "", text)
    text = re.sub(r"[$€£¥₹]", "", text)
    text = text.replace("−", "-").replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", "", text)
    if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", text):
        return None
    value = float(text)
    return -abs(value) if negative else value


def parse_table(table_text: str) -> ParsedTable:
    lines = table_text.splitlines()
    if not lines or not lines[0].startswith("columns: "):
        raise ValueError("missing_complete_visible_table")
    column_context = {
        column: value.strip()
        for column, value in _split_cells(lines[0].removeprefix("columns: "))
    }
    if "C0" not in column_context:
        raise ValueError("missing_visible_axis")
    for column_id, context in list(column_context.items()):
        if not context or _all_periods_in_context(context):
            continue
        for offset in range(1, len(column_context)):
            following_id = f"C{int(column_id.removeprefix('C')) + offset}"
            following = column_context.get(following_id)
            if following is None:
                break
            if following:
                break
            column_context[following_id] = context

    rows: list[TableRow] = []
    cells: dict[str, Cell] = {}
    for line in lines[1:]:
        match = ROW_RE.match(line)
        if not match:
            continue
        row_id, row_label, body = match.groups()
        row_cells: dict[str, Cell] = {}
        for column_id, raw in _split_cells(body):
            cell = Cell(
                ref=f"{row_id}:{column_id}",
                row_id=row_id,
                row_label=row_label.strip(),
                column_id=column_id,
                raw=raw.strip(),
                value=parse_numeric(raw),
            )
            row_cells[column_id] = cell
            cells[cell.ref] = cell
        rows.append(TableRow(row_id=row_id, label=row_label.strip(), cells=row_cells))
    if not rows or not any(cell.value is not None for cell in cells.values()):
        raise ValueError("missing_visible_numeric_cells")
    for row in rows:
        header_like = not row.label.strip() or bool(
            re.search(
                r"^(?:years? ended|fiscal year ended|year ended|at\s+\d+\s+march)",
                row.label.strip(),
                re.IGNORECASE,
            )
        )
        if not header_like:
            continue
        for column_id, cell in row.cells.items():
            if cell.value is not None and not re.fullmatch(
                r"(?:19|20)\d{2}", re.sub(r"\s+", "", cell.raw)
            ):
                continue
            column_context[column_id] = " ".join(
                part for part in (column_context.get(column_id, ""), cell.raw) if part
            ).strip()
        row_periods = []
        for cell in row.cells.values():
            row_periods.extend(_all_periods_in_context(cell.raw))
        row_periods = list(dict.fromkeys(row_periods))
        row_years = list(dict.fromkeys(YEAR_RE.findall(" ".join(row_periods))))
        if len(row_periods) == 1 or len(row_years) == 1:
            period = row_years[0] if row_years else row_periods[0]
            for column_id in column_context:
                if not _context_contains(column_context[column_id], period):
                    column_context[column_id] = " ".join(
                        part for part in (column_context[column_id], period) if part
                    ).strip()
        if header_like:
            for index, cell in enumerate(row.cells.values()):
                if index == 0 or cell.raw.strip() or cell.column_id == "C0":
                    continue
                previous_column_number = int(cell.column_id.removeprefix("C")) - 1
                previous = row.cells.get(f"C{previous_column_number}")
                if previous is None or not previous.raw.strip():
                    continue
                previous_periods = _all_periods_in_context(previous.raw)
                if len(previous_periods) <= 1:
                    column_context[cell.column_id] = " ".join(
                        part
                        for part in (column_context.get(cell.column_id, ""), previous.raw)
                        if part
                    ).strip()
    for row in rows:
        for index, cell in enumerate(row.cells.values()):
            if cell.value is not None or not cell.raw.strip():
                continue
            next_cell = row.cells.get(f"C{index + 1}")
            if next_cell is None or next_cell.value is None:
                continue
            if not re.fullmatch(r"(?:19|20)\d{2}", re.sub(r"\s+", "", next_cell.raw)):
                continue
            for offset in range(1, len(row.cells)):
                following = row.cells.get(f"C{index + offset}")
                if following is None or following.value is None:
                    continue
                if not re.fullmatch(r"(?:19|20)\d{2}", re.sub(r"\s+", "", following.raw)):
                    break
                column_context[following.column_id] = " ".join(
                    part
                    for part in (column_context.get(following.column_id, ""), cell.raw)
                    if part
                ).strip()
            break
    return ParsedTable(column_context=column_context, rows=rows, cells=cells)


def _tokens(value: str) -> set[str]:
    text = value.casefold().replace("’", "'")
    text = re.sub(r"\b(?:19|20)\d{2}\b", " ", text)
    text = re.sub(r"\((?:\d+)\)", " ", text)
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text)
        if len(token) >= 2 and token not in STOPWORDS
    }


def _strip_footnote(value: str) -> str:
    return re.sub(r"\(\d+\)", " ", value)


def _strip_periods(value: str) -> str:
    value = DATE_RE.sub(" ", value)
    value = QUARTER_RE.sub(" ", value)
    value = YEAR_RE.sub(" ", value)
    value = re.sub(r"\b12/\d{1,2}/\d{4}\b", " ", value)
    return value


def _question_target(question: str) -> str:
    value = question.split("?", 1)[0]
    value = re.sub(
        r"^(?:what\s+(?:was|is)|what)\s+(?:was|is)\s+", "", value, flags=re.I
    )
    value = re.sub(r"^(?:what|which)\s+", "", value, flags=re.I)
    value = re.sub(
        r"\b(?:change|difference|increase|decrease|amount|value)\s+(?:in|of|to)?\s*",
        " ",
        value,
        flags=re.I,
    )
    value = re.sub(
        r"\b(?:nominal|total|number|gross|net|as reported)\b",
        " ",
        value,
        flags=re.I,
    )
    value = _strip_periods(value)
    value = re.sub(
        r"\b(?:between|from|in|to|at|under|after|of|for|and)\b",
        " ",
        value,
        flags=re.I,
    )
    return re.sub(r"\s+", " ", value).strip(" .,:;/-")


def _explicit_periods(question: str) -> list[str]:
    periods = [match.group(0) for match in DATE_RE.finditer(question)]
    periods.extend(match.group(0) for match in QUARTER_RE.finditer(question))
    periods.extend(match.group(0) for match in YEAR_RE.finditer(question))
    quarter_group = re.search(
        r"\b(first|second|third|fourth)\b(?:\s+and\s+(first|second|third|fourth))?\s+quarter",
        question,
        re.IGNORECASE,
    )
    if quarter_group:
        for group in quarter_group.groups():
            if group:
                periods.append(f"{group} quarter")
    deduplicated: list[str] = []
    for period in periods:
        if period not in deduplicated:
            deduplicated.append(period)
    return deduplicated


def _period_order(period: str) -> tuple[int, int, int, int]:
    date = DATE_RE.fullmatch(period)
    if date:
        month_name = date.group(0).split()[0]
        months = {
            name: index
            for index, name in enumerate(
                [
                    "January",
                    "February",
                    "March",
                    "April",
                    "May",
                    "June",
                    "July",
                    "August",
                    "September",
                    "October",
                    "November",
                    "December",
                ],
                start=1,
            )
        }
        pieces = re.findall(r"[A-Za-z]+|\d+", date.group(0))
        return (3, int(pieces[-1]), months[month_name.casefold().capitalize()], int(pieces[-2]))
    quarter = QUARTER_RE.fullmatch(period)
    if quarter:
        return (2, 0, TEMPORAL_WORDS[quarter.group(0).split()[0].casefold()], 0)
    return (1, int(period), 0, 0)


def _normalize_period(period: str) -> str:
    return re.sub(r"\s+", " ", period).strip().casefold()


def _context_contains(context: str, period: str) -> bool:
    return _normalize_period(period) in _normalize_period(context)


def _row_score(question_target: str, row_label: str) -> int:
    question_tokens = _tokens(question_target)
    row_tokens = _tokens(_strip_footnote(row_label))
    if not question_tokens:
        return 0
    return len(question_tokens & row_tokens)


def _matching_rows(table: ParsedTable, question_target: str) -> list[TableRow]:
    scored = [(_row_score(question_target, row.label), row) for row in table.rows]
    best = max((score for score, _ in scored), default=0)
    if best == 0:
        return []
    selected = [row for score, row in scored if score == best]
    target_tokens = _tokens(question_target)
    if {"domestic", "state"} <= target_tokens:
        scoped = [
            row
            for row in table.rows
            if {"domestic", "state"} <= _tokens(_strip_footnote(row.label))
        ]
        if scoped:
            return scoped[:1]
    named_tokens = target_tokens - {
        "amount",
        "assets",
        "balance",
        "cash",
        "expense",
        "income",
        "number",
        "profit",
        "revenue",
        "risks",
        "shares",
        "tax",
        "value",
    }
    if named_tokens:
        scope_rows = [
            row
            for row in selected
            if named_tokens <= _tokens(_strip_footnote(row.label))
        ]
        if scope_rows:
            selected = scope_rows
    if len({row.label.strip().casefold() for row in selected}) == 1:
        return selected[:1]
    return selected


def _column_matches(table: ParsedTable, period: str) -> list[str]:
    matches = [
        column_id
        for column_id, context in table.column_context.items()
        if _context_contains(context, period)
    ]
    exact = [
        column_id
        for column_id in matches
        if {
            _normalize_period(value)
            for value in _all_periods_in_context(table.column_context[column_id])
        }
        == {_normalize_period(period)}
    ]
    return exact or matches


def _all_periods_in_context(text: str) -> list[str]:
    values = [match.group(0) for match in DATE_RE.finditer(text)]
    values.extend(match.group(0) for match in QUARTER_RE.finditer(text))
    values.extend(match.group(0) for match in YEAR_RE.finditer(text))
    deduplicated: list[str] = []
    for value in values:
        if value not in deduplicated:
            deduplicated.append(value)
    return deduplicated


def _visible_unit(table_text: str) -> str:
    lowered = table_text.casefold()
    if re.search(
        r"\bin\s+(?:thousands?|millions?)\b|"
        r"\(dollars? in (?:thousands?|millions?)|"
        r"\b(?:€|eur)\s+thousands?\b|"
        r"\b(?:dollars?|usd)\s+in\s+(?:thousands?|millions?)\b",
        lowered,
    ):
        if "thousand" in lowered:
            return "thousand"
        return "million"
    if re.search(r"(?<!\w)\$m\b|(?<!\w)£m\b|\$ million|\bmillions?\b", lowered):
        return "million"
    if re.search(r"(?<!\w)£k\b|(?<!\w)\$k\b|\bthousands?\b", lowered):
        return "thousand"
    if re.search(r"[$€£¥₹]", table_text):
        return "UNKNOWN"
    return "UNKNOWN"


def _build_program(refs: Iterable[str], operator: str) -> dict[str, Any]:
    programs = [{"ref": ref} for ref in refs]
    if not programs:
        raise ValueError("missing_program_refs")
    program = programs[0]
    for right in programs[1:]:
        program = {"left": program, "op": operator, "right": right}
    return program


def _answer(
    program: dict[str, Any],
    evidence_refs: list[str],
    unit: str,
    rules: list[str],
    citations: dict[str, bool],
    outcome: str,
) -> dict[str, Any]:
    return {
        "evidence_refs": evidence_refs,
        "program": program,
        "unit": unit,
        "policy_id": "VISIBLE_AXIS_SCOPE_POLICY_V1",
        "policy_rules": rules,
        "citation_valid": all(citations.get(ref, False) for ref in evidence_refs),
        "actor_outcome": outcome,
    }


def _unknown(reason: str, rules: list[str]) -> dict[str, Any]:
    return {
        "evidence_refs": [],
        "program": None,
        "unit": "UNKNOWN",
        "policy_id": "VISIBLE_AXIS_SCOPE_POLICY_V1",
        "policy_rules": rules,
        "citation_valid": False,
        "actor_outcome": reason,
    }


def _choose_cell(
    table: ParsedTable,
    rows: list[TableRow],
    period: str,
    question_target: str,
    column_keywords: set[str] | None = None,
) -> Cell | None:
    candidates: list[tuple[int, Cell]] = []
    for row in rows:
        row_periods = _all_periods_in_context(row.label)
        row_matches_period = _context_contains(row.label, period)
        for column_id, cell in row.cells.items():
            if cell.value is None:
                continue
            column_matches_period = column_id in _column_matches(table, period)
            if not row_matches_period and not column_matches_period:
                continue
            if row_matches_period and column_matches_period:
                continue
            context = f"{row.label} {table.column_context.get(column_id, '')}"
            context_periods = set(_all_periods_in_context(context))
            if _normalize_period(period) not in {
                _normalize_period(value) for value in context_periods
            }:
                continue
            score = _row_score(question_target, row.label)
            if column_keywords:
                column_tokens = _tokens(context)
                score += 2 * len(column_keywords & column_tokens)
            candidates.append((score, cell))
    if not candidates:
        return None
    best = max(score for score, _ in candidates)
    selected = [cell for score, cell in candidates if score == best]
    refs = sorted({cell.ref for cell in selected})
    if len(refs) != 1:
        return None
    return selected[0]


def _row_period_cells(
    table: ParsedTable,
    rows: list[TableRow],
    periods: list[str],
    question_target: str,
    question: str,
    column_keywords: set[str] | None = None,
) -> list[Cell] | None:
    question_tokens = _tokens(_strip_periods(question))
    cells: list[Cell] = []
    for period in periods:
        selected: list[Cell] = []
        period_columns = set(_column_matches(table, period))
        for row in rows:
            for cell in row.cells.values():
                if cell.value is None:
                    continue
                if period_columns and cell.column_id not in period_columns:
                    continue
                context = f"{row.label} {table.column_context.get(cell.column_id, '')}"
                if _context_contains(context, period):
                    selected.append(cell)
        if not selected:
            return None
        scored: list[tuple[int, Cell]] = []
        for cell in selected:
            context = f"{cell.row_label} {table.column_context.get(cell.column_id, '')}"
            score = _row_score(question_target, context)
            score += 2 * len(question_tokens & _tokens(context))
            if column_keywords:
                score += 3 * len(column_keywords & _tokens(table.column_context.get(cell.column_id, "")))
            scored.append((score, cell))
        best = max(score for score, _ in scored)
        finalists = [cell for score, cell in scored if score == best]
        refs = sorted({cell.ref for cell in finalists})
        if len(refs) != 1:
            return None
        cells.append(finalists[0])
    return cells


def _change_program(
    table: ParsedTable,
    question: str,
    question_target: str,
) -> dict[str, Any] | None:
    rows = _matching_rows(table, question_target)
    if not rows:
        return None
    explicit = _explicit_periods(question)
    if len(explicit) == 1:
        visible_periods: list[str] = []
        for row in rows:
            visible_periods.extend(_all_periods_in_context(row.label))
        for column_context in table.column_context.values():
            visible_periods.extend(_all_periods_in_context(column_context))
        deduplicated: list[str] = []
        for period in visible_periods:
            if period not in deduplicated:
                deduplicated.append(period)
        periods = deduplicated if len(deduplicated) >= 2 else explicit
    elif explicit:
        periods = explicit
    else:
        visible_periods: list[str] = []
        for row in rows:
            for cell in row.cells.values():
                visible_periods.extend(_all_periods_in_context(cell.raw))
        for column_context in table.column_context.values():
            visible_periods.extend(_all_periods_in_context(column_context))
        periods = list(dict.fromkeys(visible_periods))
        if len(periods) != 2:
            return None
    if len(periods) < 2:
        return None
    periods = sorted(periods, key=_period_order)
    earlier, later = periods[0], periods[-1]
    question_tokens = _tokens(_strip_periods(question))
    selected = _row_period_cells(
        table, rows, [earlier, later], question_target, question,
        _tokens(_strip_periods(question)),
    )
    if selected is None:
        selected = [
            _choose_cell(table, rows, earlier, question_target, question_tokens),
            _choose_cell(table, rows, later, question_target, question_tokens),
        ]
        if any(cell is None for cell in selected):
            return None
    earlier_cell, later_cell = selected
    return {
        "evidence_refs": [later_cell.ref, earlier_cell.ref],
        "program": {"left": {"ref": later_cell.ref}, "op": "sub", "right": {"ref": earlier_cell.ref}},
        "rules": ["2_explicit_period_binding", "3_change_direction"],
    }


def _inclusive_range_program(
    table: ParsedTable,
    question: str,
    question_target: str,
) -> dict[str, Any] | None:
    if not re.search(r"\bbetween\b|\bfrom\b|\bto\b", question, re.I):
        return None
    periods = sorted(_explicit_periods(question), key=_period_order)
    if len(periods) < 2:
        return None
    earlier, later = periods[0], periods[-1]
    ordered_all = sorted(_all_periods_in_context(" ".join(table.column_context.values())), key=_period_order)
    ordered_all = [
        period
        for period in ordered_all
        if _period_order(earlier) <= _period_order(period) <= _period_order(later)
    ]
    selected = _row_period_cells(
        table, _matching_rows(table, question_target), ordered_all, question_target, question,
        _tokens(_strip_periods(question)),
    )
    if not selected:
        return None
    refs = [cell.ref for cell in selected]
    return {
        "evidence_refs": refs,
        "program": _build_program(refs, "add"),
        "rules": ["2_explicit_period_binding", "4_inclusive_range", "5_label_scope"],
    }


def _total_people_program(
    table: ParsedTable,
    question: str,
    question_target: str,
) -> dict[str, Any] | None:
    if not re.search(r"\btotal\b|\bsum\b", question, re.I):
        return None
    target_tokens = _tokens(question_target)
    rows = [
        row
        for row in table.rows
        if row.label
        and not SECTION_HEADING_RE.search(row.label)
        and any(token in _tokens(_strip_footnote(row.label)) for token in target_tokens)
    ]
    if len(rows) < 1:
        return None
    row = rows[0]
    section_rows = [row]
    if re.search(r"after\s+change\s+of\s+control", question, re.I):
        active = False
        section_rows = []
        for candidate in table.rows:
            if SECTION_HEADING_RE.search(candidate.label):
                active = _context_contains(candidate.label, "Termination after Change of Control")
                continue
            if active:
                if candidate.label.casefold() in {"total", "total:"}:
                    break
                section_rows.append(candidate)
        if not section_rows:
            return None
        section_matches = [
            item
            for item in section_rows
            if _row_score(question_target, item.label)
            == max(_row_score(question_target, candidate.label) for candidate in section_rows)
        ]
        if len(section_matches) != 1:
            return None
        row = section_matches[0]
    elif len(rows) != 1:
        return None

    question_tokens = _tokens(_strip_periods(question))
    selected = [
        cell
        for column_id, cell in row.cells.items()
        if cell.value is not None and column_id != "C0"
    ]
    refs = [cell.ref for cell in selected]
    if len(refs) < 2:
        return None
    return {
        "evidence_refs": refs,
        "program": _build_program(refs, "add"),
        "rules": ["5_label_scope", "6_numeric_reference_validation"],
    }


def _multi_row_total_program(
    table: ParsedTable,
    question: str,
    question_target: str,
) -> dict[str, Any] | None:
    if not re.search(r"\btotal\b|\bsum\b", question, re.I):
        return None
    rows = [
        row
        for row in table.rows
        if row.label
        and _row_score(question_target, row.label) >= 1
        and any(cell.value is not None for cell in row.cells.values())
    ]
    if len(rows) < 2:
        return None
    best_row_score = max(_row_score(question_target, row.label) for row in rows)
    rows = [row for row in rows if _row_score(question_target, row.label) == best_row_score]
    periods = _explicit_periods(question)
    if not periods:
        return None
    column_ids = [
        column_id
        for period in periods
        for column_id in _column_matches(table, period)
    ]
    column_ids = list(dict.fromkeys(column_ids))
    question_tokens = _tokens(_strip_periods(question))
    scored_columns: list[tuple[int, str]] = []
    for column_id in column_ids:
        context = table.column_context.get(column_id, "")
        score = len(question_tokens & _tokens(context))
        if score:
            scored_columns.append((score, column_id))
    if not scored_columns:
        return None
    best = max(score for score, _ in scored_columns)
    column_id = next(column_id for score, column_id in scored_columns if score == best)
    cells = [row.cells[column_id] for row in rows if row.cells[column_id].value is not None]
    if len(cells) != len(rows):
        return None
    refs = [cell.ref for cell in cells]
    return {
        "evidence_refs": refs,
        "program": _build_program(refs, "add"),
        "rules": ["4_inclusive_range", "5_label_scope", "6_numeric_reference_validation"],
    }


def _total_range_program(
    table: ParsedTable,
    question: str,
    question_target: str,
) -> dict[str, Any] | None:
    if not re.search(r"\btotal\b|\bsum\b", question, re.I):
        return None
    periods = _explicit_periods(question)
    if len(periods) < 2:
        return None
    rows = _matching_rows(table, question_target)
    if len(rows) != 1:
        return None
    row = rows[0]
    ordered = sorted(_all_periods_in_context(" ".join(table.column_context.values())), key=_period_order)
    start, end = _period_order(min(periods, key=_period_order)), _period_order(max(periods, key=_period_order))
    selected = []
    for column_id, cell in row.cells.items():
        if cell.value is None:
            continue
        context = table.column_context.get(column_id, "")
        cell_periods = _all_periods_in_context(context)
        if any(start <= _period_order(period) <= end for period in cell_periods):
            selected.append(cell)
    refs = [cell.ref for cell in selected]
    if len(refs) < 2:
        return None
    return {
        "evidence_refs": refs,
        "program": _build_program(refs, "add"),
        "rules": ["2_explicit_period_binding", "4_inclusive_range", "5_label_scope"],
    }


def _gross_profit_program(
    table: ParsedTable,
    question: str,
) -> dict[str, Any] | None:
    if not re.search(r"\bgross\s+profit\b", question, re.I):
        return None
    if any("gross profit" in row.label.casefold() for row in table.rows):
        return None
    revenue_rows = [row for row in table.rows if row.label.casefold().startswith("revenue")]
    cost_rows = [
        row
        for row in table.rows
        if "cost of goods sold" in row.label.casefold()
        or "cost of sales" in row.label.casefold()
    ]
    if len(revenue_rows) != 1 or len(cost_rows) != 1:
        return None
    periods = _explicit_periods(question)
    if periods:
        if re.search(r"\bas\s+reported\b", question, re.I):
            reported = [
                column_id
                for column_id, context in table.column_context.items()
                if "as reported" in context.casefold()
            ]
            if len(reported) != 1:
                return None
            column_id = reported[0]
            if not any(
                _context_contains(table.column_context[column_id], period)
                for period in periods
            ):
                return None
        else:
            column_ids: list[str] = []
            for period in periods:
                matches = _column_matches(table, period)
                if len(matches) != 1:
                    return None
                column_ids.append(matches[0])
            if len(set(column_ids)) != 1:
                return None
            column_id = column_ids[0]
    else:
        return None
    if re.search(r"\bas\s+reported\b", question, re.I):
        reported = [
            candidate
            for candidate, context in table.column_context.items()
            if "as reported" in context.casefold()
        ]
        if column_id not in reported:
            return None
    revenue = revenue_rows[0].cells[column_id]
    cost = cost_rows[0].cells[column_id]
    if revenue.value is None or cost.value is None:
        return None
    return {
        "evidence_refs": [revenue.ref, cost.ref],
        "program": {"left": {"ref": revenue.ref}, "op": "sub", "right": {"ref": cost.ref}},
        "rules": ["2_explicit_period_binding", "5_label_scope", "6_numeric_reference_validation"],
    }


def solve(question: str, table_text: str) -> dict[str, Any]:
    """Return one structured answer from visible question and table only."""
    if not question.strip() or not table_text.strip():
        return _unknown("missing_input", ["1_visible_completeness"])
    try:
        table = parse_table(table_text)
    except (ValueError, TypeError):
        return _unknown("unmatched", ["1_visible_completeness"])
    question_target = _question_target(question)
    if not question_target:
        return _unknown("ambiguous", ["5_label_scope"])

    candidate: dict[str, Any] | None = None
    change_query = bool(
        re.search(r"\bchange\b|\bdifference\b|\bincrease\b|\bdecrease\b", question, re.I)
        and "change of control" not in question.casefold()
    )
    if change_query:
        candidate = _change_program(table, question, question_target)
        if candidate is None:
            candidate = _inclusive_range_program(table, question, question_target)
    elif "gross profit" in question.casefold():
        candidate = _gross_profit_program(table, question)
    else:
        candidate = _total_people_program(table, question, question_target)
        if candidate is None:
            candidate = _total_range_program(table, question, question_target)
        if candidate is None:
            candidate = _multi_row_total_program(table, question, question_target)

    if candidate is None:
        return _unknown("unmatched", ["1_visible_completeness", "5_label_scope"])
    refs = candidate["evidence_refs"]
    if not refs or any(ref not in table.cells or table.cells[ref].value is None for ref in refs):
        return _unknown("UNKNOWN", ["6_numeric_reference_validation"])
    if any(not math.isfinite(table.cells[ref].value) for ref in refs):
        return _unknown("UNKNOWN", ["6_numeric_reference_validation"])
    unit = _visible_unit(table_text)
    outcome = "numeric"
    if unit == "UNKNOWN":
        outcome = "numeric_unit_unknown"
    return _answer(
        candidate["program"],
        refs,
        unit,
        candidate["rules"],
        {ref: True for ref in refs},
        outcome,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", required=True)
    parser.add_argument("--table-text", required=True)
    args = parser.parse_args()
    print(json.dumps(solve(args.question, args.table_text), ensure_ascii=False, sort_keys=True))
