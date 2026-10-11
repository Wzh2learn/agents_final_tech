from __future__ import annotations

import pytest

from research import finqa_evidence_argument_resolver_v2 as resolver_module
from research.finqa_evidence_argument_resolver_v2 import (
    EvidenceArgumentResolverError,
    resolve_numeric_argument,
)
from research.finqa_numeric_token_canonicalization_v2 import (
    canonical_numeric_token,
    numeric_tokens as canonical_numeric_tokens,
)
from research.stage_e_multileaf_20261010 import (
    audit_finqa_v2_causal_join as causal_audit,
)
from research.stage_e_multileaf_20261010 import (
    build_finqa_v2_candidate_manifest as selection,
)


def test_selection_and_causal_paths_share_canonical_token_identity():
    evidence = {"text_1": "the reconciled value is 003.8000"}
    selection_result = selection.resolve_numeric_argument("3.800", evidence)

    assert selection.resolve_numeric_argument is resolve_numeric_argument
    assert resolver_module.canonical_numeric_token is canonical_numeric_token
    assert resolver_module.numeric_tokens is canonical_numeric_tokens
    assert causal_audit.numeric_tokens is canonical_numeric_tokens
    assert selection_result["argument_token"] == canonical_numeric_token("003.800")
    assert causal_audit.literal_arg("3.800") == selection_result["argument_token"]
    assert causal_audit.numeric_tokens(evidence["text_1"]) == {
        selection_result["argument_token"]
    }
    assert f"{float('3.800'):.10f}" != selection_result["argument_token"]


def test_canonically_equal_evidence_remains_ambiguous_and_fails_closed():
    evidence = {
        "text_1": "first amount is 1.10",
        "text_2": "second amount is 1.1000",
    }

    with pytest.raises(EvidenceArgumentResolverError) as exc:
        selection.resolve_numeric_argument("001.100", evidence)

    assert exc.value.code == "unresolved_ambiguous_evidence"
    assert exc.value.detail["matches"] == ["text_1", "text_2"]


def test_shared_adapter_fails_closed_for_no_match_and_nonnumeric_argument():
    with pytest.raises(EvidenceArgumentResolverError) as no_match:
        selection.resolve_numeric_argument("7.25", {"text_1": "unrelated 3"})
    assert no_match.value.code == "unresolved_no_evidence"

    with pytest.raises(EvidenceArgumentResolverError) as nonnumeric:
        selection.resolve_numeric_argument("#0", {"text_1": "value 3"})
    assert nonnumeric.value.code == "argument_not_numeric_literal"
