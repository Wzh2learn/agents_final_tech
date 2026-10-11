from __future__ import annotations

import pytest

from research.finqa_evidence_argument_resolver_v2 import (
    EvidenceArgumentResolverError,
    resolve_numeric_argument,
)


EVIDENCE = {
    "text_1": "the value is 3.8 million",
    "text_2": "the prior year is 2.5",
}


def test_unique_numeric_evidence_resolves_and_removal_fails():
    result = resolve_numeric_argument("3.8", EVIDENCE)
    assert result["evidence_id"] == "text_1"
    assert result["resolved_value"] == 3.8
    assert result["join_type"] == "LEXICAL_UNIQUE_EVIDENCE_TO_ARGUMENT"

    with pytest.raises(EvidenceArgumentResolverError) as exc:
        resolve_numeric_argument("3.8", {"text_2": EVIDENCE["text_2"]})
    assert exc.value.code == "unresolved_no_evidence"


def test_ambiguous_and_nonnumeric_arguments_fail_closed():
    ambiguous = {
        "a": "amount 10",
        "b": "total 10",
    }
    with pytest.raises(EvidenceArgumentResolverError) as exc:
        resolve_numeric_argument("10", ambiguous)
    assert exc.value.code == "unresolved_ambiguous_evidence"

    with pytest.raises(EvidenceArgumentResolverError) as exc:
        resolve_numeric_argument("#0", EVIDENCE)
    assert exc.value.code == "argument_not_numeric_literal"


def test_numeric_formatting_is_canonicalized():
    result = resolve_numeric_argument("3.800", EVIDENCE)
    assert result["argument_token"] == "3.8"
    assert result["evidence_id"] == "text_1"
