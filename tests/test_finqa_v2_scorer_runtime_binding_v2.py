from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from research.finqa_independent_observation_scorer_v2 import artifact_hash
from research.finqa_v2_20261010.binding_v2.finqa_v2_scorer_runtime_binding_v2 import (
    NORMALIZATION_FUNCTION,
    NORMALIZATION_VERSION,
    RuntimeBindingV2,
    TRACE_FIELDS,
    build_trace_rows,
    normalized_payload_from_record,
    raw_payload_from_record,
    sha256_json,
    sha256_text,
)


TASK_DIR = Path("research/finqa_v2_20261010")
BINDING_DIR = TASK_DIR / "binding_v2"
RESULTS_DIR = TASK_DIR / "results"
CONTRACT_PATH = BINDING_DIR / "finqa_v2_artifact_binding_contract_v2.json"
MAPPING_PATH = BINDING_DIR / "finqa_v2_raw_normalized_mapping.jsonl"
AUDIT_PATH = BINDING_DIR / "finqa_v2_normalization_audit.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def synthetic_record() -> dict:
    return {
        "required_evidence_ids": ["E1"],
        "clean": {
            "answer": "1",
            "evidence_ids": ["E1"],
            "steps": [
                {"op": "add1-1", "arg1": "1", "arg2": "2", "res": "3"},
                {"op": "add2-1", "arg1": "3", "arg2": "4", "res": "7"},
            ],
        },
        "mutant": {
            "answer": "2",
            "evidence_ids": ["E1"],
            "steps": [
                {"op": "add1-1", "arg1": "1", "arg2": "2", "res": "4"},
                {"op": "add2-1", "arg1": "3", "arg2": "4", "res": "8"},
            ],
        },
    }


def synthetic_trace_rows(record: dict) -> tuple[str, list[dict]]:
    raw_hash = sha256_json(record)
    normalized_hash = artifact_hash(normalized_payload_from_record(record))
    rows = build_trace_rows(
        record,
        artifact_id="SYNTH-ART",
        sample_id="SYNTH-SAMPLE",
        split_role="",
        stage="",
        cluster_id="",
        report_cluster="",
        raw_payload_sha256=raw_hash,
        normalized_payload_sha256=normalized_hash,
    )
    return raw_hash, rows


def synthetic_adapter() -> RuntimeBindingV2:
    return RuntimeBindingV2(
        {
            "normalization_function": NORMALIZATION_FUNCTION,
            "normalization_version": NORMALIZATION_VERSION,
            "fail_closed": True,
        },
        {},
    )


def test_deterministic_normalization_replay_raw_preservation_and_scorer_hash() -> None:
    record = synthetic_record()
    original = copy.deepcopy(record)
    raw_hash, trace_rows = synthetic_trace_rows(record)
    runtime_record = {**record, "artifact_sha256": raw_hash}
    first = synthetic_adapter().score_pair(
        runtime_record,
        artifact_id="SYNTH-ART",
        sample_id="SYNTH-SAMPLE",
        expected_trace_rows=trace_rows,
        expected_raw_sha256=raw_hash,
    )
    second = synthetic_adapter().score_pair(
        runtime_record,
        artifact_id="SYNTH-ART",
        sample_id="SYNTH-SAMPLE",
        expected_trace_rows=trace_rows,
        expected_raw_sha256=raw_hash,
    )
    expected_normalized_hash = artifact_hash(normalized_payload_from_record(record))

    assert record == original
    assert first == second
    assert first["binding"]["raw_payload_sha256"] == raw_hash
    assert first["binding"]["normalized_payload_sha256"] == expected_normalized_hash
    assert first["scorer"]["artifact_sha256"] == expected_normalized_hash
    assert first["binding"]["raw_payload_sha256"] != (
        first["binding"]["normalized_payload_sha256"]
    )


def test_positive_control_corruption_fails_closed() -> None:
    record = synthetic_record()
    raw_hash, trace_rows = synthetic_trace_rows(record)
    corrupted = copy.deepcopy(record)
    corrupted["clean"]["steps"][0]["res"] = "999"
    with pytest.raises(Exception) as captured:
        synthetic_adapter().score_pair(
            {**corrupted, "artifact_sha256": raw_hash},
            artifact_id="SYNTH-ART",
            sample_id="SYNTH-SAMPLE",
            expected_trace_rows=trace_rows,
            expected_raw_sha256=raw_hash,
        )
    assert getattr(captured.value, "code", "") == "RAW_PAYLOAD_HASH_MISMATCH"


def test_missing_trace_key_fails_closed() -> None:
    record = synthetic_record()
    raw_hash, trace_rows = synthetic_trace_rows(record)
    incomplete_rows = trace_rows[:-1]
    with pytest.raises(Exception) as captured:
        synthetic_adapter().score_pair(
            {**record, "artifact_sha256": raw_hash},
            artifact_id="SYNTH-ART",
            sample_id="SYNTH-SAMPLE",
            expected_trace_rows=incomplete_rows,
            expected_raw_sha256=raw_hash,
        )
    error = captured.value
    assert getattr(error, "code", "") == "BINDING_TRACE_MISSING"
    assert error.detail["trace_key"] == trace_rows[-1]["trace_key"]


def test_extra_label_field_is_not_a_hash_input_and_fails_closed() -> None:
    audit = read_json(AUDIT_PATH)
    hash_fields = set(audit["leakage_audit"]["hash_input_field_paths"])
    forbidden = {
        "label",
        "labels",
        "outcome",
        "outcomes",
        "stage",
        "V",
        "D",
        "O",
        "record_status",
        "result",
        "results",
        "split_role",
        "cluster_id",
        "report_cluster",
        "sample_id",
        "artifact_id",
    }
    assert not (hash_fields & forbidden)
    assert audit["leakage_audit"]["forbidden_hash_fields_present"] == []
    normalized = normalized_payload_from_record(synthetic_record())
    assert set(normalized) == {"required_evidence_ids", "clean", "mutant"}
    with pytest.raises(Exception) as captured:
        raw_payload_from_record({**synthetic_record(), "label": "E"})
    assert getattr(captured.value, "code", "") == "RAW_PAYLOAD_FIELD_MISMATCH"


def test_exact_215_pair_994_step_mapping_accounting() -> None:
    mapping = read_jsonl(MAPPING_PATH)
    audit = read_json(AUDIT_PATH)
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in mapping:
        groups[row["artifact_id"]].append(row)
    side_counts = Counter(row["step_side"] for row in mapping)

    assert len(mapping) == 994
    assert len(groups) == 215
    assert len({row["trace_key"] for row in mapping}) == 994
    assert all(set(row) == set(TRACE_FIELDS) for row in mapping)
    assert side_counts == {"clean": 497, "mutant": 497}
    for rows in groups.values():
        pair_side_counts = Counter(row["step_side"] for row in rows)
        assert set(pair_side_counts) == {"clean", "mutant"}
        clean_indexes = sorted(
            row["step_index"]
            for row in rows
            if row["step_side"] == "clean"
        )
        mutant_indexes = sorted(
            row["step_index"]
            for row in rows
            if row["step_side"] == "mutant"
        )
        assert clean_indexes == list(range(len(clean_indexes)))
        assert mutant_indexes == list(range(len(mutant_indexes)))
        assert len(clean_indexes) == len(mutant_indexes)
    assert audit["accounting"]["pairs"] == 215
    assert audit["accounting"]["steps"] == 994
    assert audit["decision_flags"] == {
        "BIJECTIVE_OR_TRACEABLE": True,
        "DETERMINISTIC": True,
        "NO_LEAKAGE": True,
        "NO_SAMPLE_ID_CHANGE": True,
        "SEMANTICS_PRESERVING": True,
    }


def test_frozen_mapping_replays_normalization_without_scoring() -> None:
    paired = read_json(TASK_DIR / "finqa_v2_paired_artifact_manifest.json")["artifacts"]
    sample_doc = read_json(TASK_DIR / "finqa_v2_frozen_sample_manifest.json")
    samples_by_id = {row["sample_id"]: row for row in sample_doc["samples"]}
    mapping = read_jsonl(MAPPING_PATH)
    mapping_by_artifact: dict[str, list[dict]] = defaultdict(list)
    for row in mapping:
        mapping_by_artifact[row["artifact_id"]].append(row)

    for artifact in paired:
        raw = artifact["artifact"]
        sample_row = samples_by_id[artifact["sample_id"]]
        normalized_hash = artifact_hash(normalized_payload_from_record(raw))
        raw_hash = sha256_json(raw)
        expected_rows = build_trace_rows(
            raw,
            artifact_id=artifact["artifact_id"],
            sample_id=artifact["sample_id"],
            split_role=artifact["split_role"],
            stage=artifact["stage"],
            cluster_id=sample_row["cluster_id"],
            report_cluster=sample_row["report_cluster"],
            raw_payload_sha256=raw_hash,
            normalized_payload_sha256=normalized_hash,
        )
        assert raw_hash == artifact["artifact_sha256"]
        assert mapping_by_artifact[artifact["artifact_id"]] == expected_rows


def test_sample_id_and_group_membership_are_invariant() -> None:
    paired = read_json(TASK_DIR / "finqa_v2_paired_artifact_manifest.json")["artifacts"]
    sample_doc = read_json(TASK_DIR / "finqa_v2_frozen_sample_manifest.json")
    split_doc = read_json(TASK_DIR / "finqa_v2_split_manifest.json")
    binding_doc = read_json(TASK_DIR / "finqa_v2_scorer_binding_manifest.json")
    retained = [row for row in sample_doc["samples"] if row.get("retained")]
    samples_by_id = {row["sample_id"]: row for row in retained}
    split_by_id = {row["sample_id"]: row for row in split_doc["samples"]}
    binding_by_id = {row["sample_id"]: row for row in binding_doc["bindings"]}
    paired_ids = {row["sample_id"] for row in paired}

    assert paired_ids == set(samples_by_id) == set(split_by_id) == set(binding_by_id)
    for artifact in paired:
        sample = samples_by_id[artifact["sample_id"]]
        split = split_by_id[artifact["sample_id"]]
        binding = binding_by_id[artifact["sample_id"]]
        assert artifact["artifact_id"] == sample["artifact_id"] == binding["artifact_id"]
        assert artifact["split_role"] == sample["split_role"] == split["split_role"]
        assert artifact["stage"] == sample["stage"] == split["stage"]
        assert sample["cluster_id"]
        assert sample["report_cluster"]


def test_all_89_old_failure_hashes_reproduce_exactly() -> None:
    paired = {
        row["sample_id"]: row
        for row in read_json(TASK_DIR / "finqa_v2_paired_artifact_manifest.json")[
            "artifacts"
        ]
    }
    failures = read_jsonl(RESULTS_DIR / "finqa_v2_formal_scorer_failures.jsonl")
    assert len(failures) == 89
    for failure in failures:
        artifact = paired[failure["sample_id"]]
        raw_hash = sha256_json(artifact["artifact"])
        normalized_hash = artifact_hash(
            normalized_payload_from_record(artifact["artifact"])
        )
        assert failure["error_code"] == "artifact_sha256_mismatch"
        assert failure["hash_match"] is False
        assert failure["manifest_artifact_sha256"] == raw_hash
        assert failure["scorer_payload_sha256"] == normalized_hash
        assert raw_hash != normalized_hash


def test_old_invalid_run_hashes_remain_unchanged() -> None:
    audit = read_json(AUDIT_PATH)
    immutable = audit["old_invalid_run"]["immutable_output_sha256"]
    results = read_json(RESULTS_DIR / "finqa_v2_formal_results.json")
    receipt = read_json(RESULTS_DIR / "finqa_v2_formal_execution_receipt.json")

    for name, expected in immutable.items():
        observed = hashlib.sha256((RESULTS_DIR / name).read_bytes()).hexdigest()
        assert observed == expected
    assert results["run_status"] == "FORMAL_RUN_INVALID"
    assert receipt["status"] == "FORMAL_RUN_INVALID"
    assert audit["old_invalid_run"]["scientific_status"] == "SECOND_FLOW_INVALID"
    assert audit["old_invalid_run"]["superseded_scientifically"] is False


def test_contract_and_mapping_load_fail_closed_with_exact_accounting() -> None:
    contract = read_json(CONTRACT_PATH)
    assert contract["hash_domains"]["raw_payload_sha256"]["role"].startswith(
        "provenance hash"
    )
    assert contract["hash_domains"]["normalized_payload_sha256"]["role"] == (
        "scorer-runtime authoritative hash"
    )
    assert contract["normalization"]["function"] == NORMALIZATION_FUNCTION
    assert contract["normalization"]["version"] == NORMALIZATION_VERSION
    assert contract["normalization"]["scorer_modified"] is False
    assert contract["trace"]["fail_closed"] is True
    assert contract["accounting"] == {
        "clean_steps": 497,
        "evaluation_failure_reproductions": 89,
        "frozen_pairs_scored_by_binding_repair": 0,
        "mutant_steps": 497,
        "new_formal_scoring_calls": 0,
        "pairs": 215,
        "steps": 994,
        "unique_trace_keys": 994,
    }
    assert contract["trace"]["mapping_sha256"] == sha256_text(
        MAPPING_PATH.read_text(encoding="utf-8")
    )
    adapter = RuntimeBindingV2.from_paths(CONTRACT_PATH)
    assert len(adapter.trace_rows_by_artifact) == 215
    assert sum(len(rows) for rows in adapter.trace_rows_by_artifact.values()) == 994
