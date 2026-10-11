#!/usr/bin/env python3
"""Binding-only FinQA v2 runtime interface v3 qualification implementation."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from research.finqa_independent_observation_scorer_v2 import (
    _normalized_steps,
    artifact_hash,
    canonical_json,
)


TASK_DIR = Path(__file__).resolve().parents[1]
BINDING_DIR = Path(__file__).resolve().parent
ROOT = TASK_DIR.parents[1]
V2_BINDING_DIR = TASK_DIR / "binding_v2"
V2_CONTRACT_PATH = V2_BINDING_DIR / "finqa_v2_artifact_binding_contract_v2.json"
V2_MAPPING_PATH = V2_BINDING_DIR / "finqa_v2_raw_normalized_mapping.jsonl"
INTERFACE_PATH = BINDING_DIR / "finqa_v2_runtime_binding_interface_v3.json"
IMPLEMENTATION_PATH = BINDING_DIR / "finqa_v2_runtime_binding_v3.py"
TEST_PATH = BINDING_DIR / "tests/test_finqa_v2_runtime_binding_v3_integration.py"
QUALIFICATION_ROWS_PATH = BINDING_DIR / "finqa_v2_binding_v3_qualification_rows.jsonl"
QUALIFICATION_SUMMARY_PATH = BINDING_DIR / "finqa_v2_binding_v3_qualification_summary.json"
QUALIFICATION_LOG_PATH = BINDING_DIR / "finqa_v2_binding_v3_qualification.log"
INTEGRATION_LOG_PATH = BINDING_DIR / "finqa_v2_binding_v3_integration_tests.log"
RECEIPT_PATH = BINDING_DIR / "finqa_v2_binding_v3_qualification_receipt.json"
INTERFACE_MD_PATH = BINDING_DIR / "FINQA_V2_RUNTIME_BINDING_INTERFACE_V3.md"

TASK_ID = "finqa-v2-binding-v3-qualification-a-20261010"
NAMESPACE = "FINQA_V2_RUNTIME_BINDING_INTERFACE_V3"
NORMALIZATION_FUNCTION = (
    "finqa_independent_observation_scorer_v2.py::_normalized_steps + artifact_hash"
)
NORMALIZATION_VERSION = "finqa_v2_scorer_normalization_20261010_v1"
RAW_PAYLOAD_FIELDS = {"required_evidence_ids", "clean", "mutant"}
RAW_SIDE_FIELDS = {"evidence_ids", "steps", "answer"}
RUNTIME_METADATA_FIELDS = (
    "split_role",
    "stage",
    "cluster_id",
    "report_cluster",
)
IMMUTABLE_IDENTITY_FIELDS = (
    "source_artifact_id",
    "sample_id",
    "raw_payload_sha256",
    "normalized_payload_sha256",
    "normalization_version",
)
TRACE_FIELDS = (
    "artifact_id",
    "sample_id",
    "split_role",
    "stage",
    "cluster_id",
    "report_cluster",
    "step_side",
    "step_index",
    "trace_key",
    "raw_step_payload_sha256",
    "normalized_step_payload_sha256",
    "raw_step_identity",
    "normalized_step_identity",
    "raw_payload_sha256",
    "normalized_payload_sha256",
    "normalization_function",
    "normalization_version",
)
IMMUTABLE_TRACE_FIELDS = (
    "source_artifact_id",
    "sample_id",
    "raw_payload_sha256",
    "normalized_payload_sha256",
    "normalization_version",
    "trace_key",
    "step_side",
    "step_index",
    "raw_step_identity",
    "normalized_step_identity",
    "raw_step_payload_sha256",
    "normalized_step_payload_sha256",
)
RUNTIME_TRACE_FIELDS = RUNTIME_METADATA_FIELDS
PRIOR_INVALID_RUN_BASELINES = {
    "results": {
        "files": 12,
        "manifest_sha256": "a14b595df597c2d3a3e4df2dc9875049288d4158f8c9226de1e87588bc5b9078",
        "receipt_sha256": "2d94d30003f9de563402c71b34b58dc492e8e545682278ffb6f1c40d3d87320f",
        "status": "FORMAL_RUN_INVALID",
    },
    "results_binding_v2_rerun": {
        "files": 12,
        "manifest_sha256": "824f34bce5da3d59d48effa434e32549ffc5a633286bf74a8161f0d67ab72f8a",
        "receipt_sha256": "8a0017e1ae5f065fe73a01bb1af1a0f5033199fbe25369263d4184c27d8eb071",
        "status": "FORMAL_RUN_INVALID",
    },
}
_REQUIRED = object()


class BindingV3Error(RuntimeError):
    """Base fail-closed error for binding interface v3."""

    def __init__(self, code: str, **detail: Any) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


class MissingRequiredFieldError(BindingV3Error):
    """A required identity or runtime field was absent."""


class RuntimeMetadataError(BindingV3Error):
    """Runtime metadata was absent, null, empty, or otherwise invalid."""


class ImmutableIdentityError(BindingV3Error):
    """Immutable identity was absent, malformed, or inconsistent."""


class BindingIntegrityError(BindingV3Error):
    """A hash, trace, identity, group, split, or leakage check failed."""


class QualificationError(BindingV3Error):
    """Qualification accounting or output boundary failed."""


@dataclass(frozen=True)
class ImmutableIdentity:
    source_artifact_id: str
    sample_id: str
    raw_payload_sha256: str
    normalized_payload_sha256: str
    normalization_version: str


@dataclass(frozen=True)
class RuntimeMetadata:
    split_role: str
    stage: str
    cluster_id: str
    report_cluster: str


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def json_hash(value: Any) -> str:
    return sha256_json(value)


def canonical(value: Any) -> str:
    return canonical_json(value)


def self_hash(value: dict[str, Any]) -> str:
    return json_hash({key: item for key, item in value.items() if key != "self_sha256"})


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _require_nonempty(
    value: Any,
    *,
    field: str,
    error_type: type[BindingV3Error],
    missing_code: str,
) -> str:
    if value is _REQUIRED:
        code = (
            missing_code
            if missing_code.endswith("_MISSING")
            else f"{missing_code}_MISSING"
        )
        raise error_type(code, field=field)
    if value is None:
        raise error_type(f"{missing_code}_NULL", field=field)
    if not isinstance(value, str):
        raise error_type(f"{missing_code}_INVALID_TYPE", field=field, actual_type=type(value).__name__)
    if value == "" or value.strip() == "":
        raise error_type(f"{missing_code}_EMPTY", field=field)
    return value


def extract_runtime_metadata(row: dict[str, Any]) -> RuntimeMetadata:
    if not isinstance(row, dict):
        raise RuntimeMetadataError("RUNTIME_ROW_INVALID")
    values: dict[str, str] = {}
    for field in RUNTIME_METADATA_FIELDS:
        if field not in row:
            raise MissingRequiredFieldError("RUNTIME_METADATA_MISSING", field=field)
        values[field] = _require_nonempty(
            row[field],
            field=field,
            error_type=RuntimeMetadataError,
            missing_code="RUNTIME_METADATA",
        )
    return RuntimeMetadata(**values)


def validate_runtime_metadata(
    metadata: RuntimeMetadata,
) -> RuntimeMetadata:
    values: dict[str, str] = {}
    for field in RUNTIME_METADATA_FIELDS:
        values[field] = _require_nonempty(
            getattr(metadata, field),
            field=field,
            error_type=RuntimeMetadataError,
            missing_code="RUNTIME_METADATA",
        )
    return RuntimeMetadata(**values)


def raw_payload_from_record(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise BindingIntegrityError("RAW_RECORD_INVALID")
    allowed = RAW_PAYLOAD_FIELDS | {"artifact_sha256"}
    supplied = set(record)
    missing = RAW_PAYLOAD_FIELDS - supplied
    unexpected = supplied - allowed
    if missing or unexpected:
        raise BindingIntegrityError(
            "RAW_PAYLOAD_FIELD_MISMATCH",
            missing=sorted(missing),
            unexpected=sorted(unexpected),
        )
    return {key: record[key] for key in sorted(RAW_PAYLOAD_FIELDS)}


def normalized_payload_from_record(record: dict[str, Any]) -> dict[str, Any]:
    raw = raw_payload_from_record(record)
    clean = raw["clean"]
    mutant = raw["mutant"]
    if set(clean) != RAW_SIDE_FIELDS or set(mutant) != RAW_SIDE_FIELDS:
        raise BindingIntegrityError("RAW_SIDE_FIELD_MISMATCH")
    required = [str(item) for item in raw["required_evidence_ids"]]
    return {
        "required_evidence_ids": required,
        "clean": {
            "evidence_ids": sorted({str(item) for item in clean["evidence_ids"]}),
            "steps": _normalized_steps(clean["steps"], "clean.steps"),
            "answer": str(clean["answer"]),
        },
        "mutant": {
            "evidence_ids": sorted({str(item) for item in mutant["evidence_ids"]}),
            "steps": _normalized_steps(mutant["steps"], "mutant.steps"),
            "answer": str(mutant["answer"]),
        },
    }


def construct_scorer_input(
    raw_record: dict[str, Any],
    *,
    normalized_payload_sha256: str,
) -> dict[str, Any]:
    raw = raw_payload_from_record(raw_record)
    normalized_payload_sha256 = _require_nonempty(
        normalized_payload_sha256,
        field="normalized_payload_sha256",
        error_type=ImmutableIdentityError,
        missing_code="IMMUTABLE_IDENTITY",
    )
    return {**raw, "artifact_sha256": normalized_payload_sha256}


def trace_key(source_artifact_id: str, step_side: str, step_index: int) -> str:
    return f"{source_artifact_id}::{step_side}::{step_index:04d}"


def build_trace_rows(
    raw_record: dict[str, Any],
    *,
    identity: ImmutableIdentity,
    metadata: RuntimeMetadata,
) -> list[dict[str, Any]]:
    raw = raw_payload_from_record(raw_record)
    normalized = normalized_payload_from_record(raw_record)
    rows: list[dict[str, Any]] = []
    for step_side in ("clean", "mutant"):
        raw_steps = raw[step_side]["steps"]
        normalized_steps = normalized[step_side]["steps"]
        if len(raw_steps) != len(normalized_steps):
            raise BindingIntegrityError("TRACE_STEP_COUNT_MISMATCH", step_side=step_side)
        for step_index, (raw_step, normalized_step) in enumerate(
            zip(raw_steps, normalized_steps, strict=True)
        ):
            rows.append(
                {
                    "artifact_id": identity.source_artifact_id,
                    "sample_id": identity.sample_id,
                    "split_role": metadata.split_role,
                    "stage": metadata.stage,
                    "cluster_id": metadata.cluster_id,
                    "report_cluster": metadata.report_cluster,
                    "step_side": step_side,
                    "step_index": step_index,
                    "trace_key": trace_key(
                        identity.source_artifact_id,
                        step_side,
                        step_index,
                    ),
                    "raw_step_payload_sha256": sha256_json(raw_step),
                    "normalized_step_payload_sha256": sha256_json(normalized_step),
                    "raw_step_identity": raw_step,
                    "normalized_step_identity": normalized_step,
                    "raw_payload_sha256": identity.raw_payload_sha256,
                    "normalized_payload_sha256": identity.normalized_payload_sha256,
                    "normalization_function": NORMALIZATION_FUNCTION,
                    "normalization_version": identity.normalization_version,
                }
            )
    return rows


def partition_trace_row(row: dict[str, Any]) -> dict[str, dict[str, Any]]:
    artifact_row = {
        "source_artifact_id": row["artifact_id"],
        "sample_id": row["sample_id"],
        "raw_payload_sha256": row["raw_payload_sha256"],
        "normalized_payload_sha256": row["normalized_payload_sha256"],
        "normalization_version": row["normalization_version"],
        "trace_key": row["trace_key"],
        "step_side": row["step_side"],
        "step_index": row["step_index"],
        "raw_step_identity": row["raw_step_identity"],
        "normalized_step_identity": row["normalized_step_identity"],
        "raw_step_payload_sha256": row["raw_step_payload_sha256"],
        "normalized_step_payload_sha256": row["normalized_step_payload_sha256"],
    }
    runtime = {field: row[field] for field in RUNTIME_TRACE_FIELDS}
    return {
        "immutable_step_and_artifact_identity": artifact_row,
        "runtime_metadata_cross_check_only": runtime,
    }


def prior_invalid_run_manifest(directory: Path) -> dict[str, Any]:
    if not directory.is_dir():
        raise QualificationError("PRIOR_INVALID_RUN_MISSING", directory=str(directory))
    files: dict[str, str] = {}
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or ".omc" in path.parts:
            continue
        files[str(path.relative_to(directory))] = sha256_file(path)
    manifest_sha256 = json_hash(files)
    baseline = PRIOR_INVALID_RUN_BASELINES[directory.name]
    if len(files) != baseline["files"] or manifest_sha256 != baseline["manifest_sha256"]:
        raise QualificationError(
            "PRIOR_INVALID_RUN_HASH_MISMATCH",
            directory=str(directory),
            expected_files=baseline["files"],
            actual_files=len(files),
            expected_manifest_sha256=baseline["manifest_sha256"],
            actual_manifest_sha256=manifest_sha256,
        )
    receipt_path = directory / "finqa_v2_formal_execution_receipt.json"
    receipt_sha256 = sha256_file(receipt_path)
    receipt = read_json(receipt_path)
    if receipt_sha256 != baseline["receipt_sha256"]:
        raise QualificationError(
            "PRIOR_INVALID_RECEIPT_HASH_MISMATCH",
            directory=str(directory),
            expected=baseline["receipt_sha256"],
            actual=receipt_sha256,
        )
    if receipt.get("status") != baseline["status"]:
        raise QualificationError(
            "PRIOR_INVALID_STATUS_MISMATCH",
            directory=str(directory),
            expected=baseline["status"],
            actual=receipt.get("status"),
        )
    return {
        "directory": str(directory.relative_to(TASK_DIR)),
        "file_count": len(files),
        "files": files,
        "manifest_sha256": manifest_sha256,
        "receipt_sha256": receipt_sha256,
        "run_status": receipt.get("status"),
    }


def verify_prior_invalid_runs() -> dict[str, Any]:
    manifests = {
        name: prior_invalid_run_manifest(TASK_DIR / name)
        for name in PRIOR_INVALID_RUN_BASELINES
    }
    if any(manifest["run_status"] != "FORMAL_RUN_INVALID" for manifest in manifests.values()):
        raise QualificationError("PRIOR_INVALID_RUN_STATUS_MISMATCH")
    return manifests


class RuntimeBindingV3:
    def __init__(
        self,
        interface: dict[str, Any],
        contract: dict[str, Any],
        trace_rows_by_artifact: dict[str, list[dict[str, Any]]],
    ) -> None:
        if interface.get("namespace") != NAMESPACE:
            raise BindingIntegrityError("INTERFACE_NAMESPACE_MISMATCH")
        if interface.get("contract_version") != "finqa-v2-runtime-binding-interface-v3":
            raise BindingIntegrityError("INTERFACE_VERSION_MISMATCH")
        if interface["immutable_identity"]["fields"] != list(IMMUTABLE_IDENTITY_FIELDS):
            raise BindingIntegrityError("IMMUTABLE_IDENTITY_SCHEMA_MISMATCH")
        if tuple(interface["runtime_metadata"]["field_order"]) != RUNTIME_METADATA_FIELDS:
            raise BindingIntegrityError("RUNTIME_METADATA_SCHEMA_MISMATCH")
        if tuple(interface["trace_map"]["classification"]["runtime_metadata_cross_check_only"]) != RUNTIME_TRACE_FIELDS:
            raise BindingIntegrityError("TRACE_RUNTIME_SCHEMA_MISMATCH")
        if interface["scope"]["window"] != "zero-endpoint, non-training, zero scientific scoring":
            raise BindingIntegrityError("SCOPE_WINDOW_MISMATCH")
        if contract["normalization"]["version"] != NORMALIZATION_VERSION:
            raise BindingIntegrityError("NORMALIZATION_VERSION_MISMATCH")
        if contract["normalization"]["function"] != NORMALIZATION_FUNCTION:
            raise BindingIntegrityError("NORMALIZATION_FUNCTION_MISMATCH")
        self.interface = interface
        self.contract = contract
        self.trace_rows_by_artifact = trace_rows_by_artifact

    @classmethod
    def from_paths(
        cls,
        *,
        interface_path: Path = INTERFACE_PATH,
        contract_path: Path = V2_CONTRACT_PATH,
        mapping_path: Path = V2_MAPPING_PATH,
    ) -> RuntimeBindingV3:
        interface = read_json(interface_path)
        contract = read_json(contract_path)
        expected_mapping_hash = interface["trace_map"]["frozen_mapping_sha256"]
        actual_mapping_hash = sha256_file(mapping_path)
        if actual_mapping_hash != expected_mapping_hash:
            raise BindingIntegrityError(
                "FROZEN_MAPPING_HASH_MISMATCH",
                expected=expected_mapping_hash,
                actual=actual_mapping_hash,
            )
        if contract["trace"]["mapping_sha256"] != actual_mapping_hash:
            raise BindingIntegrityError("V2_CONTRACT_MAPPING_HASH_MISMATCH")
        mapping = [
            json.loads(line)
            for line in mapping_path.read_text(encoding="utf-8").splitlines()
            if line
        ]
        if any(set(row) != set(TRACE_FIELDS) for row in mapping):
            raise BindingIntegrityError("MAPPING_ROW_SCHEMA_MISMATCH")
        trace_keys = [row["trace_key"] for row in mapping]
        if len(trace_keys) != len(set(trace_keys)):
            raise BindingIntegrityError("MAPPING_TRACE_KEY_DUPLICATE")
        by_artifact: dict[str, list[dict[str, Any]]] = {}
        for row in mapping:
            validate_runtime_metadata(
                RuntimeMetadata(
                    split_role=row["split_role"],
                    stage=row["stage"],
                    cluster_id=row["cluster_id"],
                    report_cluster=row["report_cluster"],
                )
            )
            by_artifact.setdefault(row["artifact_id"], []).append(row)
        if len(by_artifact) != 215 or len(mapping) != 994:
            raise BindingIntegrityError(
                "MAPPING_ACCOUNTING_MISMATCH",
                pairs=len(by_artifact),
                rows=len(mapping),
            )
        return cls(interface, contract, by_artifact)

    def immutable_identity_for(
        self,
        row: dict[str, Any],
    ) -> ImmutableIdentity:
        if not isinstance(row, dict):
            raise ImmutableIdentityError("IDENTITY_ROW_INVALID")
        for field in ("artifact_id", "sample_id", "manifest_artifact_sha256"):
            if field not in row:
                raise MissingRequiredFieldError("IMMUTABLE_IDENTITY_MISSING", field=field)
        source_artifact_id = _require_nonempty(
            row["artifact_id"],
            field="source_artifact_id",
            error_type=ImmutableIdentityError,
            missing_code="IMMUTABLE_IDENTITY",
        )
        sample_id = _require_nonempty(
            row["sample_id"],
            field="sample_id",
            error_type=ImmutableIdentityError,
            missing_code="IMMUTABLE_IDENTITY",
        )
        raw_payload_sha256 = _require_nonempty(
            row["manifest_artifact_sha256"],
            field="raw_payload_sha256",
            error_type=ImmutableIdentityError,
            missing_code="IMMUTABLE_IDENTITY",
        )
        expected_rows = self.trace_rows_by_artifact.get(source_artifact_id)
        if not expected_rows:
            raise BindingIntegrityError(
                "BINDING_TRACE_MISSING",
                source_artifact_id=source_artifact_id,
            )
        expected_raw = {item["raw_payload_sha256"] for item in expected_rows}
        expected_normalized = {item["normalized_payload_sha256"] for item in expected_rows}
        expected_samples = {item["sample_id"] for item in expected_rows}
        expected_versions = {item["normalization_version"] for item in expected_rows}
        if expected_raw != {raw_payload_sha256}:
            raise BindingIntegrityError("IDENTITY_RAW_HASH_CROSSBIND_MISMATCH")
        if len(expected_normalized) != 1 or len(expected_samples) != 1 or len(expected_versions) != 1:
            raise BindingIntegrityError("IDENTITY_TRACE_INCONSISTENT")
        if expected_samples != {sample_id}:
            raise BindingIntegrityError("IDENTITY_SAMPLE_DRIFT")
        return ImmutableIdentity(
            source_artifact_id=source_artifact_id,
            sample_id=sample_id,
            raw_payload_sha256=raw_payload_sha256,
            normalized_payload_sha256=next(iter(expected_normalized)),
            normalization_version=next(iter(expected_versions)),
        )

    def bind(
        self,
        raw_record: dict[str, Any],
        identity: ImmutableIdentity,
        *,
        split_role: Any = _REQUIRED,
        stage: Any = _REQUIRED,
        cluster_id: Any = _REQUIRED,
        report_cluster: Any = _REQUIRED,
    ) -> dict[str, Any]:
        metadata = RuntimeMetadata(
            split_role=_require_nonempty(
                split_role,
                field="split_role",
                error_type=RuntimeMetadataError,
                missing_code="RUNTIME_METADATA",
            ),
            stage=_require_nonempty(
                stage,
                field="stage",
                error_type=RuntimeMetadataError,
                missing_code="RUNTIME_METADATA",
            ),
            cluster_id=_require_nonempty(
                cluster_id,
                field="cluster_id",
                error_type=RuntimeMetadataError,
                missing_code="RUNTIME_METADATA",
            ),
            report_cluster=_require_nonempty(
                report_cluster,
                field="report_cluster",
                error_type=RuntimeMetadataError,
                missing_code="RUNTIME_METADATA",
            ),
        )
        for field in IMMUTABLE_IDENTITY_FIELDS:
            if not getattr(identity, field):
                raise ImmutableIdentityError("IMMUTABLE_IDENTITY_EMPTY", field=field)
        if identity.normalization_version != NORMALIZATION_VERSION:
            raise ImmutableIdentityError("NORMALIZATION_VERSION_MISMATCH")
        raw = raw_payload_from_record(raw_record)
        raw_payload_sha256 = sha256_json(raw)
        if raw_payload_sha256 != identity.raw_payload_sha256:
            raise BindingIntegrityError(
                "RAW_PAYLOAD_HASH_MISMATCH",
                expected=identity.raw_payload_sha256,
                actual=raw_payload_sha256,
            )
        normalized = normalized_payload_from_record(raw_record)
        normalized_payload_sha256 = artifact_hash(normalized)
        if normalized_payload_sha256 != identity.normalized_payload_sha256:
            raise BindingIntegrityError(
                "NORMALIZED_PAYLOAD_HASH_MISMATCH",
                expected=identity.normalized_payload_sha256,
                actual=normalized_payload_sha256,
            )
        scorer_input = construct_scorer_input(
            raw_record,
            normalized_payload_sha256=normalized_payload_sha256,
        )
        if scorer_input["artifact_sha256"] != normalized_payload_sha256:
            raise BindingIntegrityError("SCORER_INPUT_HASH_BINDING_MISMATCH")
        expected_rows = self.trace_rows_by_artifact.get(identity.source_artifact_id)
        if not expected_rows:
            raise BindingIntegrityError(
                "BINDING_TRACE_MISSING",
                source_artifact_id=identity.source_artifact_id,
            )
        for expected in expected_rows:
            expected_metadata = RuntimeMetadata(
                split_role=expected["split_role"],
                stage=expected["stage"],
                cluster_id=expected["cluster_id"],
                report_cluster=expected["report_cluster"],
            )
            if expected_metadata != metadata:
                raise BindingIntegrityError(
                    "RUNTIME_METADATA_TRACE_MISMATCH",
                    trace_key=expected["trace_key"],
                )
        computed_rows = build_trace_rows(
            raw_record,
            identity=identity,
            metadata=metadata,
        )
        computed_by_key = {row["trace_key"]: row for row in computed_rows}
        expected_by_key = {row["trace_key"]: row for row in expected_rows}
        if len(computed_by_key) != len(computed_rows):
            raise BindingIntegrityError("COMPUTED_TRACE_KEY_DUPLICATE")
        if set(computed_by_key) != set(expected_by_key):
            raise BindingIntegrityError(
                "BINDING_TRACE_KEY_SET_MISMATCH",
                missing=sorted(set(computed_by_key) - set(expected_by_key)),
                unexpected=sorted(set(expected_by_key) - set(computed_by_key)),
            )
        matched = 0
        for key in sorted(computed_by_key):
            if computed_by_key[key] != expected_by_key[key]:
                raise BindingIntegrityError("BINDING_TRACE_MISMATCH", trace_key=key)
            matched += 1
        trace_classification = {
            key: partition_trace_row(row) for key, row in sorted(computed_by_key.items())
        }
        return {
            "immutable_identity": asdict(identity),
            "runtime_metadata": asdict(metadata),
            "scorer_input": {
                "artifact_sha256_field": scorer_input["artifact_sha256"],
                "raw_fields": sorted(raw),
                "scorer_input_sha256": sha256_json(scorer_input),
                "construction_status": "CONSTRUCTED_NOT_EXECUTED",
            },
            "validation": {
                "binding_status": "PASS",
                "corruption_detected": False,
                "group_drift": False,
                "identity_drift": False,
                "leakage": False,
                "metadata_present": True,
                "metadata_consistent": True,
                "raw_hash_status": "MATCH",
                "normalized_hash_status": "MATCH",
                "split_drift": False,
                "silent_default_count": 0,
                "trace_rows_expected": len(expected_rows),
                "trace_rows_matched": matched,
                "trace_rows_mismatched": 0,
            },
            "trace_map": trace_classification,
        }


class BindingV3Runner:
    """Real runner-to-adapter seam; never invokes scientific scoring."""

    def __init__(self, adapter: RuntimeBindingV3) -> None:
        self.adapter = adapter

    def run(
        self,
        rows: Sequence[dict[str, Any]] | None = None,
        *,
        expected_count: int = 89,
    ) -> list[dict[str, Any]]:
        if rows is None:
            from research.finqa_v2_20261010.run_finqa_v2_formal_experiment import (
                load_evaluation_rows,
            )

            loaded, _ = load_evaluation_rows()
            rows = loaded
        output: list[dict[str, Any]] = []
        for index, row in enumerate(rows):
            metadata = extract_runtime_metadata(row)
            identity = self.adapter.immutable_identity_for(row)
            result = self.adapter.bind(
                row["_score_payload"],
                identity,
                split_role=metadata.split_role,
                stage=metadata.stage,
                cluster_id=metadata.cluster_id,
                report_cluster=metadata.report_cluster,
            )
            output.append(
                {
                    "binding_index": index,
                    "immutable_identity": result["immutable_identity"],
                    "runtime_metadata": result["runtime_metadata"],
                    "scorer_input": result["scorer_input"],
                    "validation": result["validation"],
                    "trace_map": result["trace_map"],
                }
            )
        if len(output) != expected_count:
            raise QualificationError(
                "RUNTIME_BINDING_COUNT_MISMATCH",
                expected=expected_count,
                actual=len(output),
            )
        return output


def _split_flags() -> dict[str, bool]:
    split = read_json(TASK_DIR / "finqa_v2_split_manifest.json")
    flags = {
        "group_disjointness": bool(split["group_disjointness"]["passed"]),
        "assignment_checks": bool(split["assignment_checks"]["passed"]),
        "leakage_fail_closed": bool(split["leakage_fail_closed"]["passed"]),
    }
    if not all(flags.values()):
        raise QualificationError("SPLIT_OR_LEAKAGE_GATE_FAILED", flags=flags)
    return flags


def _missing_metadata_controls(
    runner: BindingV3Runner,
    representative: dict[str, Any],
) -> dict[str, Any]:
    controls: dict[str, Any] = {}
    for field in RUNTIME_METADATA_FIELDS:
        candidate = copy.deepcopy(representative)
        del candidate[field]
        try:
            runner.run([candidate], expected_count=1)
        except (MissingRequiredFieldError, RuntimeMetadataError) as error:
            if error.code != "RUNTIME_METADATA_MISSING" or error.detail.get("field") != field:
                raise QualificationError(
                    "MISSING_METADATA_CONTROL_ERROR_MISMATCH",
                    field=field,
                    code=error.code,
                    detail=error.detail,
                ) from error
            controls[field] = {
                "control": "PASS",
                "error_type": type(error).__name__,
                "error_code": error.code,
                "field": error.detail["field"],
            }
        else:
            raise QualificationError("MISSING_METADATA_CONTROL_DID_NOT_FAIL", field=field)
    return controls


def _corruption_control(
    runner: BindingV3Runner,
    representative: dict[str, Any],
) -> dict[str, Any]:
    candidate = copy.deepcopy(representative)
    candidate["_score_payload"]["clean"]["steps"][0]["res"] = "999999"
    try:
        runner.run([candidate], expected_count=1)
    except BindingIntegrityError as error:
        if error.code != "RAW_PAYLOAD_HASH_MISMATCH":
            raise QualificationError(
                "CORRUPTION_CONTROL_ERROR_MISMATCH",
                code=error.code,
            ) from error
        return {
            "control": "PASS",
            "error_type": type(error).__name__,
            "error_code": error.code,
        }
    raise QualificationError("CORRUPTION_CONTROL_DID_NOT_FAIL")


def scientific_output_inventory(directory: Path = BINDING_DIR) -> list[str]:
    forbidden_names = (
        "observation_vector",
        "bootstrap_replicates",
        "estimand",
        "formal_result",
        "scientific_result",
        "score_pair_output",
    )
    return sorted(
        str(path.relative_to(directory))
        for path in directory.rglob("*")
        if path.is_file() and any(token in path.name for token in forbidden_names)
    )


def run_qualification(
    *,
    rows: Sequence[dict[str, Any]] | None = None,
    output_dir: Path | None = None,
    write_outputs: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    prior_before = verify_prior_invalid_runs()
    flags = _split_flags()
    adapter = RuntimeBindingV3.from_paths()
    runner = BindingV3Runner(adapter)
    first = runner.run(rows)
    second = runner.run(rows)
    if first != second:
        raise QualificationError("DETERMINISTIC_REPLAY_MISMATCH")
    representative = copy.deepcopy(rows[0] if rows is not None else _load_one_row())
    missing_controls = _missing_metadata_controls(runner, representative)
    corruption = _corruption_control(runner, representative)
    prior_after = verify_prior_invalid_runs()
    if prior_before != prior_after:
        raise QualificationError("PRIOR_INVALID_RUN_CHANGED_DURING_QUALIFICATION")
    trace_total = sum(item["validation"]["trace_rows_matched"] for item in first)
    if trace_total != 420:
        raise QualificationError("EVALUATION_TRACE_COUNT_MISMATCH", actual=trace_total, expected=420)
    if any(item["validation"]["binding_status"] != "PASS" for item in first):
        raise QualificationError("BINDING_FAILURE_REMAINS")
    metadata_fields_present = Counter()
    for item in first:
        for field in RUNTIME_METADATA_FIELDS:
            value = item["runtime_metadata"][field]
            if not isinstance(value, str) or value.strip() == "":
                raise QualificationError("QUALIFICATION_METADATA_EMPTY", field=field)
            metadata_fields_present[field] += 1
    stage_counts = Counter(item["runtime_metadata"]["stage"] for item in first)
    if stage_counts != Counter({"E": 30, "P": 30, "N": 29}):
        raise QualificationError("STAGE_BINDING_COUNT_MISMATCH", actual=dict(stage_counts))
    report_clusters = {
        item["runtime_metadata"]["cluster_id"]: item["runtime_metadata"]["report_cluster"]
        for item in first
    }
    if len(report_clusters) != 30 or len(set(report_clusters.values())) != 30:
        raise QualificationError(
            "REPORT_CLUSTER_COUNT_MISMATCH",
            cluster_ids=len(report_clusters),
            report_clusters=len(set(report_clusters.values())),
        )
    stage_report_clusters = {
        stage: len(
            {
                item["runtime_metadata"]["cluster_id"]
                for item in first
                if item["runtime_metadata"]["stage"] == stage
            }
        )
        for stage in ("E", "N", "P")
    }
    if stage_report_clusters != {"E": 10, "N": 10, "P": 10}:
        raise QualificationError(
            "STAGE_REPORT_CLUSTER_COUNT_MISMATCH",
            actual=stage_report_clusters,
        )
    scientific_outputs = scientific_output_inventory()
    if scientific_outputs:
        raise QualificationError(
            "SCIENTIFIC_OUTPUT_IN_BINDING_NAMESPACE",
            paths=scientific_outputs,
        )
    summary = {
        "namespace": "FINQA_V2_BINDING_V3_QUALIFICATION_SUMMARY",
        "task_id": TASK_ID,
        "status": "QUALIFICATION_PASS_PENDING_LOOP_C_INDEPENDENT_REVIEW",
        "interface": {
            "contract_version": "finqa-v2-runtime-binding-interface-v3",
            "immutable_identity_fields": list(IMMUTABLE_IDENTITY_FIELDS),
            "runtime_metadata_fields": list(RUNTIME_METADATA_FIELDS),
        },
        "counts": {
            "runtime_bindings_pass": len(first),
            "runtime_bindings_total": len(first),
            "evaluation_trace_rows_match": trace_total,
            "evaluation_trace_rows_total": 420,
            "report_clusters": len(report_clusters),
            "stage_bindings": dict(sorted(stage_counts.items())),
            "stage_report_clusters": stage_report_clusters,
        },
        "metadata": {
            "field_presence": dict(sorted(metadata_fields_present.items())),
            "field_consistency": {field: len(first) for field in RUNTIME_METADATA_FIELDS},
            "missing": 0,
            "null": 0,
            "empty": 0,
            "silent_defaults": 0,
        },
        "drift": {
            "sample_identity": 0,
            "group": 0,
            "split": 0,
            "leakage": 0,
        },
        "controls": {
            "missing_metadata": missing_controls,
            "corruption": corruption,
            "deterministic_replay": {
                "control": "PASS",
                "equal_rows": len(first),
            },
        },
        "pipeline": {
            "runner_to_adapter_explicit_fields": True,
            "scorer_input_construction_status": "CONSTRUCTED_NOT_EXECUTED",
            "raw_hash_validation": "89/89 MATCH",
            "normalized_hash_validation": "89/89 MATCH",
            "trace_validation": "420/420 MATCH",
            "stop_boundary": "BEFORE_SCIENTIFIC_SCORING",
        },
        "gates": {
            "group_disjointness": flags["group_disjointness"],
            "split_assignment": flags["assignment_checks"],
            "leakage_fail_closed": flags["leakage_fail_closed"],
        },
        "zero_counters": {
            "endpoint_calls": 0,
            "model_calls": 0,
            "training_runs": 0,
            "scientific_scoring_calls": 0,
            "observation_vector_outputs": 0,
            "V_outputs": 0,
            "D_outputs": 0,
            "O_outputs": 0,
            "estimand_outputs": 0,
            "bootstrap_outputs": 0,
            "scientific_output_files": len(scientific_outputs),
            "silent_defaults": 0,
            "identity_drift": 0,
            "group_drift": 0,
            "split_drift": 0,
            "leakage": 0,
        },
        "prior_invalid_runs": {
            name: {
                "file_count": manifest["file_count"],
                "manifest_sha256": manifest["manifest_sha256"],
                "receipt_sha256": manifest["receipt_sha256"],
                "status": manifest["run_status"],
                "unchanged": True,
            }
            for name, manifest in prior_after.items()
        },
        "receipt_required": "generated only after exact integration-test and qualification logs are final",
    }
    if write_outputs:
        target = output_dir if output_dir is not None else BINDING_DIR
        target.mkdir(parents=True, exist_ok=True)
        rows_path = target / QUALIFICATION_ROWS_PATH.name
        summary_path = target / QUALIFICATION_SUMMARY_PATH.name
        rows_path.write_text(
            "".join(
                json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n"
                for item in first
            ),
            encoding="utf-8",
        )
        write_json(summary_path, summary)
    return first, summary


def _load_one_row() -> dict[str, Any]:
    from research.finqa_v2_20261010.run_finqa_v2_formal_experiment import (
        load_evaluation_rows,
    )

    rows, _ = load_evaluation_rows()
    return copy.deepcopy(rows[0])


def _required_qualification_files() -> list[Path]:
    return [
        INTERFACE_MD_PATH,
        INTERFACE_PATH,
        IMPLEMENTATION_PATH,
        TEST_PATH,
        QUALIFICATION_ROWS_PATH,
        QUALIFICATION_SUMMARY_PATH,
        QUALIFICATION_LOG_PATH,
        INTEGRATION_LOG_PATH,
    ]


def build_receipt() -> dict[str, Any]:
    missing = [str(path) for path in _required_qualification_files() if not path.is_file()]
    if missing:
        raise QualificationError("QUALIFICATION_ARTIFACT_MISSING", paths=missing)
    integration_log = INTEGRATION_LOG_PATH.read_text(encoding="utf-8")
    qualification_log = QUALIFICATION_LOG_PATH.read_text(encoding="utf-8")
    if "EXIT_CODE=0" not in integration_log:
        raise QualificationError("INTEGRATION_LOG_EXIT_ZERO_MISSING")
    if "EXIT_CODE=0" not in qualification_log:
        raise QualificationError("QUALIFICATION_LOG_EXIT_ZERO_MISSING")
    summary = read_json(QUALIFICATION_SUMMARY_PATH)
    if summary["counts"]["runtime_bindings_pass"] != 89:
        raise QualificationError("RECEIPT_BINDING_COUNT_MISMATCH")
    if summary["counts"]["evaluation_trace_rows_match"] != 420:
        raise QualificationError("RECEIPT_TRACE_COUNT_MISMATCH")
    if summary["zero_counters"]["silent_defaults"] != 0:
        raise QualificationError("RECEIPT_SILENT_DEFAULT_PRESENT")
    prior = verify_prior_invalid_runs()
    interface = read_json(INTERFACE_PATH)
    artifact_hashes = {
        path.name: sha256_file(path) for path in _required_qualification_files()
    }
    frozen_hashes = dict(interface["unchanged_surfaces"]["frozen_input_sha256"])
    frozen_hashes.update(
        {
            "binding_v2/finqa_v2_artifact_binding_contract_v2.json": sha256_file(
                V2_CONTRACT_PATH
            ),
            "binding_v2/finqa_v2_raw_normalized_mapping.jsonl": sha256_file(
                V2_MAPPING_PATH
            ),
        }
    )
    receipt = {
        "namespace": "FINQA_V2_BINDING_V3_QUALIFICATION_RECEIPT",
        "task_id": TASK_ID,
        "status": "BINDING_V3_QUALIFICATION_COMPLETE_PENDING_LOOP_C_REVIEW",
        "interface_contract_version": interface["contract_version"],
        "artifact_hashes": artifact_hashes,
        "frozen_input_hashes": frozen_hashes,
        "prior_invalid_runs": prior,
        "qualification": {
            "runtime_bindings_pass": "89/89",
            "evaluation_trace_rows_match": "420/420",
            "metadata_fields": list(RUNTIME_METADATA_FIELDS),
            "silent_defaults": 0,
            "identity_drift": 0,
            "group_drift": 0,
            "split_drift": 0,
            "leakage": 0,
            "scientific_output_files": 0,
            "stop_boundary": "BEFORE_SCIENTIFIC_SCORING",
        },
        "zero_endpoint_counters": {
            "endpoint_calls": 0,
            "model_calls": 0,
            "training_runs": 0,
            "scientific_scoring_calls": 0,
            "new_formal_scientific_runs": 0,
        },
        "hash_definition": "sha256 of file bytes for artifacts; sha256 of canonical compact sorted JSON excluding self_sha256 for this receipt",
        "review_handoff": "STOP FOR LOOP C INDEPENDENT REVIEW",
    }
    receipt["self_sha256"] = self_hash(receipt)
    return receipt


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("qualify", help="run binding-only qualification")
    subparsers.add_parser("receipt", help="build the hash-complete receipt")
    args = parser.parse_args(argv)
    if args.command == "qualify":
        rows, summary = run_qualification()
        print("TASK_ID=" + TASK_ID)
        print("INTERFACE_V3=PASS")
        print(f"RUNTIME_BINDINGS=PASS count={len(rows)} total={len(rows)}")
        print("EVALUATION_TRACE_ROWS=PASS count=420 total=420")
        print("METADATA_FIELDS=PASS fields=split_role,stage,cluster_id,report_cluster")
        print("MISSING_METADATA_CONTROLS=PASS count=4")
        print("CORRUPTION_CONTROL=PASS")
        print("DETERMINISTIC_REPLAY=PASS")
        print("SILENT_DEFAULTS=0")
        print("IDENTITY_DRIFT=0 GROUP_DRIFT=0 SPLIT_DRIFT=0 LEAKAGE=0")
        print("SCIENTIFIC_OUTPUTS=0")
        print("SCORE_PAIR_CALLS=0 OBSERVATION_VECTOR_OUTPUTS=0")
        print("V_D_O_OUTPUTS=0 ESTIMAND_OUTPUTS=0 BOOTSTRAP_OUTPUTS=0")
        print("PRIOR_INVALID_RUN_HASHES=UNCHANGED")
        print("PIPELINE_STOP=BEFORE_SCIENTIFIC_SCORING")
        print(f"SUMMARY_STATUS={summary['status']}")
        return 0
    if args.command == "receipt":
        receipt = build_receipt()
        write_json(RECEIPT_PATH, receipt)
        print("RECEIPT=" + str(RECEIPT_PATH))
        print("RECEIPT_SELF_SHA256=" + receipt["self_sha256"])
        print("REVIEW_HANDOFF=STOP FOR LOOP C INDEPENDENT REVIEW")
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
