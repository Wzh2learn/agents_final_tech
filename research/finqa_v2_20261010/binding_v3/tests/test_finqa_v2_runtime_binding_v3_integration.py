from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import research.finqa_independent_observation_scorer_v2 as scorer_module
from research.finqa_v2_20261010.binding_v3.finqa_v2_runtime_binding_v3 import (
    BINDING_DIR,
    IMMUTABLE_IDENTITY_FIELDS,
    QUALIFICATION_ROWS_PATH,
    QUALIFICATION_SUMMARY_PATH,
    RUNTIME_METADATA_FIELDS,
    BindingIntegrityError,
    BindingV3Runner,
    MissingRequiredFieldError,
    RuntimeBindingV3,
    RuntimeMetadataError,
    run_qualification,
    scientific_output_inventory,
    verify_prior_invalid_runs,
)
from research.finqa_v2_20261010.run_finqa_v2_formal_experiment import (
    load_evaluation_rows,
)


INTERFACE_PATH = BINDING_DIR / "finqa_v2_runtime_binding_interface_v3.json"


def load_interface() -> dict:
    return json.loads(INTERFACE_PATH.read_text(encoding="utf-8"))


def first_row() -> dict:
    rows, _ = load_evaluation_rows()
    return copy.deepcopy(rows[0])


def test_runner_forwards_all_four_metadata_fields_to_real_adapter() -> None:
    row = first_row()
    adapter = RuntimeBindingV3.from_paths()
    original_bind = adapter.bind
    observed: dict[str, object] = {}

    def recording_bind(raw_record, identity, **kwargs):
        observed.update(kwargs)
        return original_bind(raw_record, identity, **kwargs)

    adapter.bind = recording_bind
    runner = BindingV3Runner(adapter)
    runner.run([row], expected_count=1)

    assert tuple(observed) == RUNTIME_METADATA_FIELDS
    assert observed == {
        "split_role": row["split_role"],
        "stage": row["stage"],
        "cluster_id": row["cluster_id"],
        "report_cluster": row["report_cluster"],
    }


@pytest.mark.parametrize("missing_field", RUNTIME_METADATA_FIELDS)
def test_missing_runtime_metadata_fails_closed_through_runner(missing_field: str) -> None:
    row = first_row()
    del row[missing_field]
    runner = BindingV3Runner(RuntimeBindingV3.from_paths())

    with pytest.raises((MissingRequiredFieldError, RuntimeMetadataError)) as captured:
        runner.run([row], expected_count=1)

    error = captured.value
    assert error.code == "RUNTIME_METADATA_MISSING"
    assert error.detail["field"] == missing_field


@pytest.mark.parametrize("invalid_value", [None, "", "   "])
@pytest.mark.parametrize("invalid_field", RUNTIME_METADATA_FIELDS)
def test_null_and_empty_runtime_metadata_fail_closed_through_runner(
    invalid_field: str,
    invalid_value: object,
) -> None:
    row = first_row()
    row[invalid_field] = invalid_value
    runner = BindingV3Runner(RuntimeBindingV3.from_paths())

    with pytest.raises(RuntimeMetadataError) as captured:
        runner.run([row], expected_count=1)

    expected_code = (
        "RUNTIME_METADATA_NULL" if invalid_value is None else "RUNTIME_METADATA_EMPTY"
    )
    assert captured.value.code == expected_code
    assert captured.value.detail["field"] == invalid_field


def test_full_raw_normalized_runtime_binding_path_constructs_but_does_not_execute() -> None:
    row = first_row()
    adapter = RuntimeBindingV3.from_paths()
    result = BindingV3Runner(adapter).run([row], expected_count=1)[0]

    assert set(result["immutable_identity"]) == set(IMMUTABLE_IDENTITY_FIELDS)
    assert set(result["runtime_metadata"]) == set(RUNTIME_METADATA_FIELDS)
    assert result["scorer_input"]["construction_status"] == "CONSTRUCTED_NOT_EXECUTED"
    assert result["scorer_input"]["raw_fields"] == [
        "clean",
        "mutant",
        "required_evidence_ids",
    ]
    assert result["validation"]["raw_hash_status"] == "MATCH"
    assert result["validation"]["normalized_hash_status"] == "MATCH"
    assert result["validation"]["trace_rows_expected"] > 0
    assert result["validation"]["trace_rows_mismatched"] == 0
    assert "observation_vector" not in result
    assert not {"V", "D", "O"} & set(result)


def test_complete_89_pair_binding_qualification_with_scorer_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_scorer(*args, **kwargs):
        raise AssertionError("scientific scoring must not be reached")

    monkeypatch.setattr(scorer_module, "score_pair", forbidden_scorer)
    bindings, summary = run_qualification(write_outputs=True)

    assert len(bindings) == 89
    assert sum(row["validation"]["trace_rows_matched"] for row in bindings) == 420
    assert summary["counts"]["runtime_bindings_pass"] == 89
    assert summary["counts"]["evaluation_trace_rows_match"] == 420
    assert summary["counts"]["stage_bindings"] == {"E": 30, "N": 29, "P": 30}
    assert summary["counts"]["stage_report_clusters"] == {"E": 10, "N": 10, "P": 10}
    assert summary["counts"]["report_clusters"] == 30
    assert summary["metadata"]["silent_defaults"] == 0
    assert summary["zero_counters"]["scientific_scoring_calls"] == 0
    persisted_rows = [
        json.loads(line)
        for line in QUALIFICATION_ROWS_PATH.read_text(encoding="utf-8").splitlines()
        if line
    ]
    persisted_summary = json.loads(QUALIFICATION_SUMMARY_PATH.read_text(encoding="utf-8"))
    assert persisted_rows == bindings
    assert persisted_summary == summary


def test_raw_payload_corruption_fails_closed_through_runner() -> None:
    row = first_row()
    row["_score_payload"]["clean"]["steps"][0]["res"] = "999999"
    runner = BindingV3Runner(RuntimeBindingV3.from_paths())

    with pytest.raises(BindingIntegrityError) as captured:
        runner.run([row], expected_count=1)

    assert captured.value.code == "RAW_PAYLOAD_HASH_MISMATCH"


def test_deterministic_replay_is_exact() -> None:
    runner = BindingV3Runner(RuntimeBindingV3.from_paths())
    first = runner.run(expected_count=89)
    second = runner.run(expected_count=89)

    assert first == second


def test_interface_separates_identity_from_runtime_metadata_and_forbids_defaults() -> None:
    interface = load_interface()

    assert interface["immutable_identity"]["fields"] == [
        "source_artifact_id",
        "sample_id",
        "raw_payload_sha256",
        "normalized_payload_sha256",
        "normalization_version",
    ]
    assert tuple(interface["runtime_metadata"]["field_order"]) == RUNTIME_METADATA_FIELDS
    assert set(interface["runtime_metadata"]["fields"]) == set(RUNTIME_METADATA_FIELDS)
    assert interface["runtime_metadata"]["silent_default_policy"].startswith("forbidden")
    assert interface["qualification"]["expected_evaluation_trace_rows"] == 420
    assert interface["qualification"]["binding_rows"] == 89
    source = (BINDING_DIR / "finqa_v2_runtime_binding_v3.py").read_text(encoding="utf-8")
    assert 'record.get("split_role", "")' not in source
    assert 'record.get("stage", "")' not in source
    assert 'record.get("cluster_id", "")' not in source
    assert 'record.get("report_cluster", "")' not in source


def test_trace_map_classification_distinguishes_identity_and_runtime_fields() -> None:
    interface = load_interface()
    classification = interface["trace_map"]["classification"]

    assert "source_artifact_id" in classification["immutable_step_and_artifact_identity"]
    assert "trace_key" in classification["immutable_step_and_artifact_identity"]
    assert tuple(classification["runtime_metadata_cross_check_only"]) == (
        RUNTIME_METADATA_FIELDS
    )
    assert set(classification["immutable_step_and_artifact_identity"]).isdisjoint(
        classification["runtime_metadata_cross_check_only"]
    )


def test_prior_invalid_runs_remain_byte_identical() -> None:
    manifests = verify_prior_invalid_runs()

    assert set(manifests) == {"results", "results_binding_v2_rerun"}
    assert all(item["file_count"] == 12 for item in manifests.values())
    assert all(item["run_status"] == "FORMAL_RUN_INVALID" for item in manifests.values())


def test_binding_v3_namespace_has_zero_scientific_output_files() -> None:
    assert scientific_output_inventory(Path(BINDING_DIR)) == []
