"""Deployment-visible parsing and calculator contract for financial table tasks."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any


REF_PATTERN = re.compile(r"^R(\d+):C(\d+)$")


@dataclass(frozen=True)
class VisibleCell:
    """One actor-visible table cell."""

    ref: str
    row_id: str
    column_id: str
    row_label: str
    column_label: str
    value: float


@dataclass(frozen=True)
class TaskContract:
    """Public task fields reconstructed only from visible question/table text."""

    scope: str
    prior_period: str
    current_period: str
    operator: str
    requested_unit: str


def normalize_label(value: str) -> str:
    """Normalize a visible label for conservative matching."""
    return re.sub(r"\s+", " ", str(value).strip()).casefold()


def parse_number(value: str) -> float | None:
    """Parse one visible numeric table cell."""
    text = value.strip().replace(",", "")
    if not text or text.casefold() in {"n/a", "na", "-", "—"}:
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()").replace("%", "").replace("$", "").replace("£", "")
    text = text.replace("€", "").replace("¥", "")
    if not re.fullmatch(r"-?\d+(?:\.\d+)?", text):
        return None
    parsed = float(text)
    return -parsed if negative else parsed


def parse_visible_table(table_text: str) -> dict[str, VisibleCell]:
    """Parse the rendered actor-visible table without any reference data."""
    lines = table_text.splitlines()
    if not lines:
        return {}
    column_labels = {
        match.group(1): match.group(2).strip()
        for match in re.finditer(r"(C\d+)=([^|]+)", lines[0])
    }
    cells: dict[str, VisibleCell] = {}
    for line in lines[1:]:
        row_match = re.match(r"^(R\d+) \[(.*?)\] (.*)$", line)
        if not row_match:
            continue
        row_id, row_label, value_text = row_match.groups()
        for match in re.finditer(r"(C\d+)=([^|\s]+)", value_text):
            column_id, raw_value = match.groups()
            value = parse_number(raw_value)
            if value is None:
                continue
            ref = f"{row_id}:{column_id}"
            cells[ref] = VisibleCell(
                ref=ref,
                row_id=row_id,
                column_id=column_id,
                row_label=row_label,
                column_label=column_labels.get(column_id, ""),
                value=value,
            )
    return cells


def parse_task_contract(question: str) -> TaskContract:
    """Reconstruct the public task contract from the visible question."""
    scope_match = re.search(r"Scope:\s*(.*?)\.\s+From\s+(.*?)\s+to\s+(.*?),", question)
    if not scope_match:
        raise ValueError("scope_period_contract_not_found")
    if "percentage-point change" in question.casefold():
        operator = "percentage_point_change"
    elif "percentage change" in question.casefold():
        operator = "percent_change"
    elif "numeric change" in question.casefold():
        operator = "difference"
    else:
        raise ValueError("operator_not_found")
    unit_match = re.search(r"Report the answer in\s+(.*?)\s+units\.", question)
    if not unit_match:
        raise ValueError("requested_unit_not_found")
    return TaskContract(
        scope=scope_match.group(1).strip(),
        prior_period=scope_match.group(2).strip(),
        current_period=scope_match.group(3).strip(),
        operator=operator,
        requested_unit=unit_match.group(1).strip(),
    )


def extract_legacy_target(text: str) -> dict[str, Any] | None:
    """Extract a legacy target object for bounded compatibility diagnostics."""
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            value, _ = decoder.raw_decode(text[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "evidence_refs" in value:
            return value
    return None


def parse_candidate(target: dict[str, Any], contract: TaskContract) -> dict[str, Any]:
    """Normalize a legacy or v2 candidate to the common tool contract."""
    refs = target.get("evidence_refs")
    if not isinstance(refs, list) or len(refs) != 2:
        raise ValueError("candidate_requires_two_evidence_refs")
    normalized_refs = [str(ref) for ref in refs]
    operator = str(target.get("operator") or contract.operator)
    return {
        "operator": operator,
        "evidence_refs": normalized_refs,
        "requested_unit": str(target.get("requested_unit") or contract.requested_unit),
    }


def deployable_features(
    question: str,
    table_text: str,
    candidate: dict[str, Any],
) -> dict[str, Any]:
    """Compute policy features without hidden references or gold labels."""
    try:
        contract = parse_task_contract(question)
        parsed = parse_candidate(candidate, contract)
        cells = parse_visible_table(table_text)
        refs = parsed["evidence_refs"]
        refs_unique = len(set(refs)) == len(refs)
        refs_valid = refs_unique and all(REF_PATTERN.fullmatch(ref) and ref in cells for ref in refs)
        referenced = [cells[ref] for ref in refs] if refs_valid else []
        scope_match = bool(referenced) and all(
            normalize_label(cell.row_label) == normalize_label(contract.scope)
            for cell in referenced
        )
        period_labels = {normalize_label(cell.column_label) for cell in referenced}
        expected_periods = {
            normalize_label(contract.prior_period),
            normalize_label(contract.current_period),
        }
        period_match = bool(referenced) and period_labels == expected_periods
        operator_match = parsed["operator"] == contract.operator
        unit_match = normalize_label(parsed["requested_unit"]) == normalize_label(
            contract.requested_unit
        )
        try:
            tool_result = execute_program(question, table_text, parsed)
        except (ValueError, ZeroDivisionError):
            tool_result = None
        features = {
            "contract_parseable": True,
            "candidate_parseable": True,
            "refs_unique": refs_unique,
            "refs_valid": refs_valid,
            "scope_match": scope_match,
            "period_match": period_match,
            "operator_match": operator_match,
            "unit_match": unit_match,
            "tool_executable": tool_result is not None,
        }
    except (ValueError, TypeError, KeyError):
        features = {
            "contract_parseable": False,
            "candidate_parseable": False,
            "refs_unique": False,
            "refs_valid": False,
            "scope_match": False,
            "period_match": False,
            "operator_match": False,
            "unit_match": False,
            "tool_executable": False,
        }
    return features


def execute_program(
    question: str,
    table_text: str,
    candidate: dict[str, Any],
) -> float:
    """Execute refs plus operator against current visible table values."""
    contract = parse_task_contract(question)
    parsed = parse_candidate(candidate, contract)
    cells = parse_visible_table(table_text)
    refs = parsed["evidence_refs"]
    if len(refs) != 2 or any(ref not in cells for ref in refs):
        raise ValueError("invalid_evidence_refs")
    by_period = {
        normalize_label(cells[ref].column_label): cells[ref].value
        for ref in refs
    }
    prior = by_period.get(normalize_label(contract.prior_period))
    current = by_period.get(normalize_label(contract.current_period))
    if prior is None or current is None:
        raise ValueError("period_operands_missing")
    if parsed["operator"] == "difference":
        result = current - prior
    elif parsed["operator"] == "percent_change":
        if prior == 0:
            raise ZeroDivisionError("percent_change_prior_zero")
        result = (current - prior) / prior * 100.0
    elif parsed["operator"] == "percentage_point_change":
        result = current - prior
    else:
        raise ValueError("unsupported_operator")
    if not math.isfinite(result):
        raise ValueError("nonfinite_result")
    return result


def all_deployable_checks_pass(features: dict[str, Any]) -> bool:
    """Apply the transparent strong delivery rule."""
    required = (
        "contract_parseable",
        "candidate_parseable",
        "refs_unique",
        "refs_valid",
        "scope_match",
        "period_match",
        "operator_match",
        "unit_match",
        "tool_executable",
    )
    return all(bool(features.get(name)) for name in required)

