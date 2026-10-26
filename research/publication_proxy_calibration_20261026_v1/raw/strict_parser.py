"""Strictly parse the frozen actor response schema."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from .calculator import numeric_value


REQUIRED_KEYS = {
    "answer",
    "numeric_value",
    "unit",
    "evidence_refs",
    "unknown",
    "clarification",
}
REFERENCE_PATTERN = re.compile(r"^(?:TABLE:(?:R\d+:)?[A-Z][A-Z0-9]*|P\d+)$")


@dataclass(frozen=True)
class ParsedResponse:
    answer: str | list[str]
    numeric_value: float | None
    unit: str
    evidence_refs: list[str]
    unknown: bool
    clarification: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def unknown_response(
        cls, reason: str = "dry_run_no_model_output"
    ) -> "ParsedResponse":
        return cls(
            answer="UNKNOWN",
            numeric_value=None,
            unit="UNKNOWN",
            evidence_refs=[],
            unknown=True,
            clarification=reason,
        )


def _valid_answer(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value)
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and item for item in value
    )


def parse_response(text: str) -> ParsedResponse:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid_json:{exc.msg}") from exc
    if not isinstance(payload, dict) or set(payload) != REQUIRED_KEYS:
        raise ValueError("schema_keys_mismatch")
    if not _valid_answer(payload["answer"]):
        raise ValueError("invalid_answer")
    if not isinstance(payload["numeric_value"], (int, float, type(None))):
        raise ValueError("invalid_numeric_value_type")
    parsed_numeric = (
        numeric_value(payload["numeric_value"])
        if payload["numeric_value"] is not None
        else numeric_value(payload["answer"])
        if isinstance(payload["answer"], str)
        else None
    )
    if not isinstance(payload["unit"], str) or not payload["unit"]:
        raise ValueError("invalid_unit")
    if not isinstance(payload["evidence_refs"], list) or not all(
        isinstance(item, str) and REFERENCE_PATTERN.fullmatch(item)
        for item in payload["evidence_refs"]
    ):
        raise ValueError("invalid_evidence_refs")
    if not isinstance(payload["unknown"], bool):
        raise ValueError("invalid_unknown")
    if not isinstance(payload["clarification"], str):
        raise ValueError("invalid_clarification")
    unknown = payload["unknown"]
    if unknown and (
        str(payload["answer"]).upper() != "UNKNOWN"
        or payload["numeric_value"] is not None
        or payload["evidence_refs"]
    ):
        raise ValueError("inconsistent_unknown")
    return ParsedResponse(
        answer=payload["answer"],
        numeric_value=parsed_numeric,
        unit=str(payload["unit"]),
        evidence_refs=list(payload["evidence_refs"]),
        unknown=unknown,
        clarification=payload["clarification"],
    )
