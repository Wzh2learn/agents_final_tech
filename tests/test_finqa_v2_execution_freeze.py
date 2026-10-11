from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from research.finqa_independent_observation_scorer_v2 import artifact_hash
from research.finqa_numeric_token_canonicalization_v2 import canonical_numeric_token
from research.finqa_v2_20261010.build_finqa_v2_execution_freeze import (
    FreezeError,
    PATHS,
    STAGES,
    assign_split,
    assignment_source_checks,
    scorer_independence_checks,
)
from research.stage_e_multileaf_20261010 import (
    audit_finqa_v2_causal_join as causal_audit,
    audit_finqa_v2_overlap_feasibility as overlap_audit,
    build_finqa_v2_candidate_manifest as selection,
)

OUT_DIR = Path("research/finqa_v2_20261010")


def _load(name: str) -> dict:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def test_premise_identity_counts_and_source_hashes_are_exact():
    candidate = json.loads(PATHS["candidate_manifest"].read_text(encoding="utf-8"))
    sample_ids = [
        sample["sample_id"]
        for stage in STAGES
        for sample in candidate["samples"][stage]
    ]
    assert len(sample_ids) == 216
    assert len(set(sample_ids)) == 216
    assert {stage: len(candidate["samples"][stage]) for stage in STAGES} == {"E": 72, "P": 72, "N": 72}
    for raw_path, expected in candidate["source_files"].items():
        path = Path(raw_path)
        assert path.stat().st_size == expected["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected["sha256"]


def test_split_is_deterministic_group_disjoint_and_exact_by_stage_role():
    first = _load("finqa_v2_split_manifest.json")
    normalized = [
        {
            "sample_id": row["sample_id"],
            "stage": row["stage"],
            "report_cluster": row["provenance"]["report_cluster_id"],
            "record_sha256": row["record_sha256"],
            "record_id": row["record_id"],
            "source_identity": row["provenance"]["normalized_source_identity"],
        }
        for row in _load("finqa_v2_frozen_sample_manifest.json")["samples"]
        if row.get("retained", True)
    ]
    assignments, allocation = assign_split(normalized)
    assert [(row["canonical_group_id"], row["role"], row["order_key"]) for row in assignments] == [
        (row["canonical_group_id"], row["role"], row["order_key"])
        for row in first["assignments"]
    ]
    assert allocation["counts"] == first["counts_by_stage_and_role"]
    assert first["group_disjointness"] == {
        "cross_stage_components": 0,
        "sample_in_multiple_roles": 0,
        "passed": True,
    }
    for stage in STAGES:
        assert {role: allocation["counts"][stage][role]["groups"] for role in ("train", "calibration", "evaluation")} == {
            "train": 9,
            "calibration": 5,
            "evaluation": 10,
        }


def test_split_fails_closed_on_unexpected_fields_and_cross_stage_component():
    sample = {
        "sample_id": "synthetic",
        "stage": "E",
        "report_cluster": "A/2020",
        "record_sha256": "a" * 64,
        "record_id": "A/2020/page_1.pdf-1",
        "source_identity": "b" * 64,
    }
    with pytest.raises(FreezeError) as unexpected:
        assign_split([{**sample, "terminal_correctness": 1}])
    assert unexpected.value.code == "SPLIT_INPUT_NOT_WHITELISTED"

    other = {**sample, "sample_id": "synthetic-other", "stage": "P"}
    with pytest.raises(FreezeError) as collision:
        assign_split([sample, other])
    assert collision.value.code == "SPLIT_GROUP_COLLISION"


def test_every_retained_sample_has_exact_hash_bound_pair():
    samples = _load("finqa_v2_frozen_sample_manifest.json")
    artifacts = _load("finqa_v2_paired_artifact_manifest.json")
    retained = {row["sample_id"] for row in samples["samples"] if row.get("retained", True)}
    entries = {row["sample_id"]: row for row in artifacts["artifacts"]}
    assert retained == set(entries)
    assert len(entries) == 215
    for entry in entries.values():
        assert artifact_hash(entry["artifact"]) == entry["artifact_sha256"]
        assert entry["stage"] in STAGES
        assert entry["split_role"] in {"train", "calibration", "evaluation"}


def test_ambiguous_join_is_excluded_before_split_and_counted():
    samples = _load("finqa_v2_frozen_sample_manifest.json")
    split = _load("finqa_v2_split_manifest.json")
    excluded = samples["exclusions"]
    assert len(excluded) == 1
    assert excluded[0]["stage"] == "N"
    assert excluded[0]["exclusion_reason"] == "JOIN_AMBIGUOUS"
    excluded_ids = {row["sample_id"] for row in excluded}
    assigned_ids = {sample_id for row in split["assignments"] for sample_id in row["sample_ids"]}
    assert excluded_ids.isdisjoint(assigned_ids)
    assert samples["counts"] == {
        "candidate_injections": 216,
        "retained_injections": 215,
        "excluded_injections": 1,
        "retained_groups": 72,
        "by_stage": {
            "E": {"candidate": 72, "retained": 72, "excluded": 0, "groups": 24},
            "P": {"candidate": 72, "retained": 72, "excluded": 0, "groups": 24},
            "N": {"candidate": 72, "retained": 71, "excluded": 1, "groups": 24},
        },
    }


def test_unique_e_joins_and_deterministic_removal_are_frozen():
    samples = _load("finqa_v2_frozen_sample_manifest.json")
    assert samples["join"]["join_status_by_stage"]["E"] == {"UNIQUE": 72}
    assert samples["join"]["removal_response_by_stage"]["E"] == {"unresolved_no_evidence": 72}
    assert samples["join"]["join_status_by_stage"]["N"] == {"AMBIGUOUS": 1, "UNIQUE": 71}
    assert samples["join"]["join_status_by_stage"]["P"] == {"NOT_APPLICABLE_OPERATOR_MUTATION": 72}
    e_rows = [row for row in samples["samples"] if row["stage"] == "E"]
    assert all(row["provenance"]["evidence_text_sha256"] for row in e_rows)
    assert all(row["provenance"]["argument_token"] == row["provenance"]["canonical_token"] for row in e_rows)
    assert all(row["provenance"]["resolver_version"]["contract_version"] == "finqa-evidence-argument-resolver-v2" for row in e_rows)
    assert all(len(row["provenance"]["resolver_version"]["source_sha256"]) == 64 for row in e_rows)


def test_scorer_binding_is_independent_label_blind_and_unexecuted():
    binding = _load("finqa_v2_scorer_binding_manifest.json")
    checks = scorer_independence_checks(PATHS["scorer"])
    assert checks["passed"]
    assert checks["forbidden_import_hits"] == []
    assert binding["measurement_object"] == "paired_checkpoint_observation_reproduction"
    assert binding["semantic_correctness_claim"] is False
    assert binding["observation_surface"] == [
        "evidence_required_hit",
        "operator_consistency",
        "argument_consistency",
        "step_result_consistency",
        "answer_consistency",
    ]
    assert binding["unevaluable_denominators"] == {
        "bound_artifacts": 215,
        "formal_scoring_calls": 0,
        "unevaluable_before_later_authorized_execution": 215,
    }
    assert binding["formal_evaluator_outputs_materialized"] == 0
    assert all(row["status"] == "BOUND_UNSCORED_PENDING_LATER_AUTHORIZED_EXECUTION" for row in binding["bindings"])


def test_live_numeric_identity_paths_and_assignment_gate_share_contracts():
    assert selection.numeric_literal("003.800")
    assert not selection.numeric_literal("#0")
    assert overlap_audit.numeric_tokens("003.800") == {canonical_numeric_token("3.800")}
    assert causal_audit.numeric_tokens("003.800") == {canonical_numeric_token("3.800")}
    assert causal_audit.literal_arg("003.800") == canonical_numeric_token("3.800")
    checks = assignment_source_checks()
    assert checks["passed"]
    assert checks["forbidden_identifier_hits"] == []
    assert checks["allowed_input_fields"] == [
        "record_id",
        "record_sha256",
        "report_cluster",
        "sample_id",
        "source_identity",
        "stage",
    ]
