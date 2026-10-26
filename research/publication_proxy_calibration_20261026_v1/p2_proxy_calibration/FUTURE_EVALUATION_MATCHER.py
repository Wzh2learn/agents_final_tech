"""Gold-free future-path matcher for P2 answer scoring.

The frozen historical matcher remains unchanged. This module preserves its
span/unit/UNKNOWN behavior while correcting R7/R8 only for future evaluation.
It accepts no hidden table identifiers or per-case branches.
"""

from __future__ import annotations

import importlib.util
import math
import re
import sys
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
HISTORICAL_PATH = (
    REPOSITORY_ROOT
    / "research"
    / "natural_error_evidence_cost_20261026_v1"
    / "a_closeout"
    / "P2_RECOVERY_RECOMPUTE_FINAL.py"
)


def _load_historical() -> Any:
    spec = importlib.util.spec_from_file_location("p2_historical_matcher", HISTORICAL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("historical_matcher_unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules["p2_historical_matcher"] = module
    spec.loader.exec_module(module)
    return module


HISTORICAL = _load_historical()


def _parse_number_fixed(candidate: Any) -> float | None:
    if isinstance(candidate, bool):
        return None
    if isinstance(candidate, (int, float)):
        return float(candidate)
    text = HISTORICAL.normalize_text(candidate)
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("() ")
    text = re.sub(r"\$|\b(?:usd|dollars?)\b", " ", text)
    text = re.sub(
        r"\b(?:percent(?:age)?|trillions?|tn|billions?|bn|millions?|mn|thousands?|k)\b",
        " ",
        text,
    )
    text = text.replace("%", " ")
    if re.search(r"(?<=\d)\s+(?=\d|,)", text) or re.search(r"(?<=\d)\s+(?=,)", text):
        return None
    text = re.sub(r"(?<=\d),(?=\d)", "", text)
    text = re.sub(r"\s+", "", text)
    if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", text):
        return None
    value = float(text)
    return -abs(value) if negative else value


def match_full_semantic_answer(
    candidate: Any,
    reference: Any,
    answer_type: str,
    reference_scale: str,
    ambiguous_visible: bool,
) -> tuple[bool, str]:
    normalized_candidate = HISTORICAL.normalize_text(candidate)
    unknown = normalized_candidate in {
        "unknown",
        "unanswerable",
        "insufficient visible evidence",
    }
    if unknown:
        return (
            ambiguous_visible,
            "reasonable_unknown" if ambiguous_visible else "unsupported_unknown",
        )
    if answer_type in {"arithmetic", "count"}:
        if HISTORICAL._explicit_unit_conflict(candidate, reference, reference_scale):
            return False, "explicit_unit_conflict"
        if answer_type == "count" and HISTORICAL._visible_numeric_scale(candidate) is not None:
            return False, "count_explicit_scale_rejected"
        candidate_number = _parse_number_fixed(candidate)
        reference_number = _parse_number_fixed(reference)
        if candidate_number is None or reference_number is None:
            return False, "numeric_parse_failure"
        if answer_type == "count":
            if not candidate_number.is_integer() or not reference_number.is_integer():
                return False, "non_integer_count"
            if candidate_number < 0 or reference_number < 0:
                return False, "negative_count_rejected"
            return candidate_number == reference_number, "count_integer_equality"
        return (
            math.isclose(candidate_number, reference_number, rel_tol=1e-6, abs_tol=1e-6),
            "numeric_isclose",
        )
    return HISTORICAL.match_full_semantic_answer(
        candidate, reference, answer_type, reference_scale, ambiguous_visible
    )


def numeric_role_match(question: str, source_text: str, expected_value: float) -> bool:
    """Reject numeric substring hits without visible semantic role support."""
    question_tokens = set(HISTORICAL.tokenize(question))
    source_tokens = set(HISTORICAL.tokenize(source_text))
    if not question_tokens or not question_tokens & source_tokens:
        return False
    expected = _parse_number_fixed(expected_value)
    if expected is None:
        return False
    literals = [float(item.replace(",", "")) for item in HISTORICAL._numeric_literals(source_text)]
    return any(math.isclose(value, expected, rel_tol=1e-6, abs_tol=1e-6) for value in literals)
