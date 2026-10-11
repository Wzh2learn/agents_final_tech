#!/usr/bin/env python3
"""Independent lexical evidence-to-numeric-argument resolver for FinQA v2."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from research.finqa_numeric_token_canonicalization_v2 import (
    NumericTokenCanonicalizationError,
    canonical_numeric_token,
    numeric_tokens,
)


class EvidenceArgumentResolverError(ValueError):
    def __init__(self, code: str, **detail: Any) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def resolve_numeric_argument(argument: Any, evidence: dict[str, Any]) -> dict[str, Any]:
    token_text = str(argument or "").strip()
    try:
        token = canonical_numeric_token(token_text)
    except NumericTokenCanonicalizationError:
        raise EvidenceArgumentResolverError("argument_not_numeric_literal", argument=token_text)
    matches = sorted(
        evidence_id
        for evidence_id, text in evidence.items()
        if token in numeric_tokens(text)
    )
    if not matches:
        raise EvidenceArgumentResolverError("unresolved_no_evidence", token=token)
    if len(matches) > 1:
        raise EvidenceArgumentResolverError("unresolved_ambiguous_evidence", token=token, matches=matches)
    return {
        "argument_token": token,
        "evidence_id": matches[0],
        "resolved_value": float(Decimal(token)),
        "join_type": "LEXICAL_UNIQUE_EVIDENCE_TO_ARGUMENT",
    }
