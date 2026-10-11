from __future__ import annotations

import copy

import pytest

from research.finqa_independent_observation_scorer_v2 import (
    IndependentScorerError,
    artifact_hash,
    op_family,
    score_pair,
)


def _normalized(steps: list[dict]) -> list[dict]:
    return [{
        "op_family": op_family(step["op"]),
        "arg1": str(step.get("arg1", "")),
        "arg2": str(step.get("arg2", "")),
        "res": str(step.get("res", "")),
    } for step in steps]


def _hash_payload(required, clean, mutant):
    return artifact_hash({
        "required_evidence_ids": required,
        "clean": {
            "evidence_ids": sorted(clean["evidence_ids"]),
            "steps": _normalized(clean["steps"]),
            "answer": clean["answer"],
        },
        "mutant": {
            "evidence_ids": sorted(mutant["evidence_ids"]),
            "steps": _normalized(mutant["steps"]),
            "answer": mutant["answer"],
        },
    })


def _record(**mutant_changes):
    clean = {
        "evidence_ids": ["e1", "e2"],
        "steps": [
            {"op": "add1-1", "arg1": "1", "arg2": "2", "res": "3"},
            {"op": "minus1-2", "arg1": "#0", "arg2": "1", "res": "2"},
        ],
        "answer": "2",
    }
    mutant = copy.deepcopy(clean)
    for key, value in mutant_changes.items():
        mutant[key] = value
    required = ["e1"]
    return {
        "required_evidence_ids": required,
        "clean": clean,
        "mutant": mutant,
        "artifact_sha256": _hash_payload(required, clean, mutant),
    }


def test_measurement_object_is_observation_not_semantic_correctness():
    result = score_pair(_record())
    assert result["measurement_object"] == "paired checkpoint observation reproduction"
    assert result["semantic_correctness_claim"] is False
    assert result["response_signature"] == [0, 0, 0, 0, 0]
    assert result["provenance"]["label_blind"] is True


def test_evidence_operator_argument_result_and_answer_are_separate():
    assert score_pair(_record(evidence_ids=["e2"]))["response_signature"] == [1, 0, 0, 0, 0]
    assert score_pair(_record(steps=[
        {"op": "multiply1-1", "arg1": "1", "arg2": "2", "res": "3"},
        {"op": "minus1-2", "arg1": "#0", "arg2": "1", "res": "2"},
    ]))["response_signature"] == [0, 1, 0, 0, 0]
    assert score_pair(_record(steps=[
        {"op": "add1-1", "arg1": "9", "arg2": "2", "res": "3"},
        {"op": "minus1-2", "arg1": "#0", "arg2": "1", "res": "2"},
    ]))["response_signature"] == [0, 0, 1, 0, 0]
    assert score_pair(_record(steps=[
        {"op": "add1-1", "arg1": "1", "arg2": "2", "res": "3"},
        {"op": "minus1-2", "arg1": "#0", "arg2": "1", "res": "99"},
    ]))["response_signature"] == [0, 0, 0, 1, 0]
    assert score_pair(_record(answer="99"))["response_signature"] == [0, 0, 0, 0, 1]


def test_stage_label_cannot_change_output():
    plain = score_pair(_record())
    labelled = score_pair({**_record(), "stage_label": "N", "fault_family": "operator"})
    assert labelled["observation_vector"] == plain["observation_vector"]
    assert labelled["response_signature"] == plain["response_signature"]


def test_hash_binding_and_missing_fields_fail_closed():
    record = _record()
    record["artifact_sha256"] = "0" * 64
    with pytest.raises(IndependentScorerError) as exc:
        score_pair(record)
    assert exc.value.code == "artifact_sha256_mismatch"

    missing = _record()
    del missing["mutant"]
    with pytest.raises(IndependentScorerError) as exc:
        score_pair(missing)
    assert exc.value.code == "invalid_record_field"


def test_clean_cannot_be_missing_required_evidence():
    record = _record()
    record["clean"]["evidence_ids"] = ["e2"]
    record["artifact_sha256"] = _hash_payload(
        record["required_evidence_ids"], record["clean"], record["mutant"]
    )
    with pytest.raises(IndependentScorerError) as exc:
        score_pair(record)
    assert exc.value.code == "clean_missing_required_evidence"
