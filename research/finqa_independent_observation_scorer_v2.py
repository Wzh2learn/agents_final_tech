#!/usr/bin/env python3
"""Independent FinQA checkpoint-observation scorer prototype.

Measurement object: paired clean/mutant observation reproduction. This module
does not implement semantic step correctness and does not import the existing
FinQA fault adapter, step scorer, or Stage E aggregation.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any


OBSERVATION_FIELDS = (
    "evidence_required_hit",
    "operator_consistency",
    "argument_consistency",
    "step_result_consistency",
    "answer_consistency",
)
OP_RE = re.compile(r"^([A-Za-z_]+?)(?:\d*)-(?:\d+)$")


class IndependentScorerError(ValueError):
    def __init__(self, code: str, **detail: Any) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def artifact_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def op_family(op: Any) -> str:
    text = str(op or "")
    match = OP_RE.match(text)
    return match.group(1) if match else text


def _require_dict(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise IndependentScorerError("invalid_record_field", field=name)
    return value


def _require_list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise IndependentScorerError("invalid_record_field", field=name)
    return value


def _normalized_steps(value: Any, name: str) -> list[dict[str, str]]:
    steps = _require_list(value, name)
    normalized = []
    for index, step in enumerate(steps):
        item = _require_dict(step, f"{name}[{index}]")
        normalized.append({
            "op_family": op_family(item.get("op")),
            "arg1": str(item.get("arg1", "")),
            "arg2": str(item.get("arg2", "")),
            "res": str(item.get("res", "")),
        })
    return normalized


def score_pair(record: dict[str, Any]) -> dict[str, Any]:
    payload = _require_dict(record, "record")
    required = [str(item) for item in _require_list(payload.get("required_evidence_ids"), "required_evidence_ids")]
    if not required:
        raise IndependentScorerError("missing_required_evidence")
    clean = _require_dict(payload.get("clean"), "clean")
    mutant = _require_dict(payload.get("mutant"), "mutant")
    clean_evidence = {str(item) for item in _require_list(clean.get("evidence_ids"), "clean.evidence_ids")}
    mutant_evidence = {str(item) for item in _require_list(mutant.get("evidence_ids"), "mutant.evidence_ids")}
    clean_steps = _normalized_steps(clean.get("steps"), "clean.steps")
    mutant_steps = _normalized_steps(mutant.get("steps"), "mutant.steps")
    if len(clean_steps) != len(mutant_steps):
        raise IndependentScorerError("step_count_mismatch")

    bound_payload = {
        "required_evidence_ids": required,
        "clean": {
            "evidence_ids": sorted(clean_evidence),
            "steps": clean_steps,
            "answer": str(clean.get("answer", "")),
        },
        "mutant": {
            "evidence_ids": sorted(mutant_evidence),
            "steps": mutant_steps,
            "answer": str(mutant.get("answer", "")),
        },
    }
    observed_hash = artifact_hash(bound_payload)
    if str(payload.get("artifact_sha256", "")) != observed_hash:
        raise IndependentScorerError("artifact_sha256_mismatch", observed=observed_hash)

    required_set = set(required)
    if not required_set.issubset(clean_evidence):
        raise IndependentScorerError("clean_missing_required_evidence")
    evidence_required_hit = int(required_set.issubset(mutant_evidence) is False)

    operator_consistency = int(any(
        before["op_family"] != after["op_family"]
        for before, after in zip(clean_steps, mutant_steps)
    ))
    argument_consistency = int(any(
        (before["arg1"], before["arg2"]) != (after["arg1"], after["arg2"])
        for before, after in zip(clean_steps, mutant_steps)
    ))
    step_result_consistency = int(any(
        before["res"] != after["res"]
        for before, after in zip(clean_steps, mutant_steps)
    ))
    answer_consistency = int(str(clean.get("answer", "")) != str(mutant.get("answer", "")))

    vector = {
        "evidence_required_hit": evidence_required_hit,
        "operator_consistency": operator_consistency,
        "argument_consistency": argument_consistency,
        "step_result_consistency": step_result_consistency,
        "answer_consistency": answer_consistency,
    }
    return {
        "measurement_object": "paired checkpoint observation reproduction",
        "semantic_correctness_claim": False,
        "artifact_sha256": observed_hash,
        "observation_vector": vector,
        "response_signature": [vector[field] for field in OBSERVATION_FIELDS],
        "missing_evidence_count": len(required_set - mutant_evidence),
        "clean_required_evidence_count": len(required_set & clean_evidence),
        "mutant_required_evidence_count": len(required_set & mutant_evidence),
        "provenance": {
            "independent_of_shared_fault_adapter": True,
            "independent_of_hierarchical_aggregation": True,
            "label_blind": True,
            "deterministic": True,
        },
    }
