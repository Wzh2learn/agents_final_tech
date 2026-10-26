"""Tri-state scoring over the frozen reviewable reference chain."""

from __future__ import annotations

import importlib.util
import math
import sys
from typing import Any

from .calculator import numeric_value
from .contracts import REPOSITORY_ROOT
from .strict_parser import ParsedResponse


FUTURE_MATCHER_PATH = (
    REPOSITORY_ROOT
    / "research"
    / "publication_proxy_calibration_20261026_v1"
    / "p2_proxy_calibration"
    / "FUTURE_EVALUATION_MATCHER.py"
)


def load_future_matcher() -> Any:
    spec = importlib.util.spec_from_file_location(
        "p2_remediation_future_matcher", FUTURE_MATCHER_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("future_matcher_unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules["p2_remediation_future_matcher"] = module
    spec.loader.exec_module(module)
    return module


FUTURE = load_future_matcher()


def expected_refs(program: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(program, dict):
        for key, value in program.items():
            if key == "ref" and isinstance(value, str):
                refs.add(value.upper())
            else:
                refs.update(expected_refs(value))
    elif isinstance(program, list):
        for item in program:
            refs.update(expected_refs(item))
    return refs


def _normalize_candidate_refs(response: ParsedResponse) -> set[str]:
    normalized = set()
    for ref in response.evidence_refs:
        value = ref.upper()
        if value.startswith("TABLE:"):
            coordinate = value[6:]
            if ":" in coordinate:
                row, column = coordinate.split(":", 1)
                normalized.add(f"{row}:{column}")
            else:
                normalized.add(coordinate)
        else:
            normalized.add(value)
    return normalized


def semantic_result(
    response: ParsedResponse,
    reference: dict[str, Any],
    evidence_visible: bool,
) -> dict[str, Any]:
    answer_type = reference["answer_type"]
    reference_value = reference["answer"]
    visible_unit = reference.get("unit") or ""
    ambiguous_visible = not evidence_visible
    lexical_match, lexical_reason = FUTURE.match_full_semantic_answer(
        response.answer,
        reference_value,
        answer_type,
        visible_unit,
        ambiguous_visible,
    )
    if response.unknown:
        outcome = "ACCEPT" if ambiguous_visible else "REJECT"
        reason = "reasonable_unknown" if ambiguous_visible else "unsupported_unknown"
        return {
            "outcome": outcome,
            "reason": reason,
            "lexical_match": lexical_match,
            "lexical_reason": lexical_reason,
        }
    if not lexical_match:
        return {
            "outcome": "REJECT",
            "reason": "reference_mismatch",
            "lexical_match": False,
            "lexical_reason": lexical_reason,
        }
    if answer_type in {"arithmetic", "count"}:
        candidate_number = numeric_value(response.numeric_value)
        reference_number = numeric_value(reference_value)
        if (
            candidate_number is None
            or reference_number is None
            or not math.isclose(
                candidate_number, reference_number, rel_tol=1e-6, abs_tol=1e-6
            )
        ):
            return {
                "outcome": "REJECT",
                "reason": "numeric_mismatch",
                "lexical_match": lexical_match,
                "lexical_reason": lexical_reason,
            }
        expected = expected_refs(reference.get("program"))
        observed = _normalize_candidate_refs(response)
        if expected and expected <= observed:
            return {
                "outcome": "ACCEPT",
                "reason": "numeric_and_reference_role_bound",
                "lexical_match": True,
                "lexical_reason": lexical_reason,
            }
        if observed and expected and not observed & expected:
            return {
                "outcome": "PENDING_ADJUDICATION",
                "reason": "numeric_match_wrong_role_candidate",
                "lexical_match": True,
                "lexical_reason": lexical_reason,
            }
        return {
            "outcome": "PENDING_ADJUDICATION",
            "reason": "numeric_match_without_complete_role_binding",
            "lexical_match": True,
            "lexical_reason": lexical_reason,
        }
    observed = _normalize_candidate_refs(response)
    if observed:
        return {
            "outcome": "ACCEPT",
            "reason": "text_match_with_visible_evidence_ref",
            "lexical_match": True,
            "lexical_reason": lexical_reason,
        }
    return {
        "outcome": "PENDING_ADJUDICATION",
        "reason": "text_match_without_visible_evidence_ref",
        "lexical_match": True,
        "lexical_reason": lexical_reason,
    }
