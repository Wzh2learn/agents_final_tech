#!/usr/bin/env python3
"""Fail-closed raw/normalized binding adapter for the unchanged FinQA v2 scorer."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from research.finqa_independent_observation_scorer_v2 import (
    _normalized_steps,
    artifact_hash,
    canonical_json,
    score_pair,
)


DEFAULT_CONTRACT_PATH = Path(__file__).with_name(
    "finqa_v2_artifact_binding_contract_v2.json"
)
NORMALIZATION_FUNCTION = (
    "finqa_independent_observation_scorer_v2.py::_normalized_steps + artifact_hash"
)
NORMALIZATION_VERSION = "finqa_v2_scorer_normalization_20261010_v1"
RAW_PAYLOAD_FIELDS = {"required_evidence_ids", "clean", "mutant"}
RAW_SIDE_FIELDS = {"evidence_ids", "steps", "answer"}
RAW_RUNTIME_METADATA_FIELDS = {
    "artifact_id",
    "sample_id",
    "split_role",
    "stage",
    "cluster_id",
    "report_cluster",
}
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


class BindingV2Error(RuntimeError):
    def __init__(self, code: str, **detail: Any) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_text(canonical_json(value))


def raw_payload_from_record(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise BindingV2Error("INVALID_RUNTIME_RECORD")
    supplied_fields = set(record)
    unexpected = (
        supplied_fields
        - RAW_PAYLOAD_FIELDS
        - {"artifact_sha256"}
        - RAW_RUNTIME_METADATA_FIELDS
    )
    missing = RAW_PAYLOAD_FIELDS - supplied_fields
    if unexpected or missing:
        raise BindingV2Error(
            "RAW_PAYLOAD_FIELD_MISMATCH",
            unexpected=sorted(unexpected),
            missing=sorted(missing),
        )
    return {key: record[key] for key in sorted(RAW_PAYLOAD_FIELDS)}


def normalized_payload_from_record(record: dict[str, Any]) -> dict[str, Any]:
    raw = raw_payload_from_record(record)
    required = [str(item) for item in raw["required_evidence_ids"]]
    clean = raw["clean"]
    mutant = raw["mutant"]
    if set(clean) != RAW_SIDE_FIELDS or set(mutant) != RAW_SIDE_FIELDS:
        raise BindingV2Error("RAW_SIDE_FIELD_MISMATCH")
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


def trace_key(artifact_id: str, step_side: str, step_index: int) -> str:
    return f"{artifact_id}::{step_side}::{step_index:04d}"


def build_trace_rows(
    record: dict[str, Any],
    *,
    artifact_id: str,
    sample_id: str,
    split_role: str,
    stage: str,
    cluster_id: str,
    report_cluster: str,
    raw_payload_sha256: str,
    normalized_payload_sha256: str,
) -> list[dict[str, Any]]:
    raw = raw_payload_from_record(record)
    normalized = normalized_payload_from_record(record)
    rows: list[dict[str, Any]] = []
    for step_side in ("clean", "mutant"):
        raw_steps = raw[step_side]["steps"]
        normalized_steps = normalized[step_side]["steps"]
        if len(raw_steps) != len(normalized_steps):
            raise BindingV2Error("TRACE_STEP_COUNT_MISMATCH", step_side=step_side)
        for step_index, (raw_step, normalized_step) in enumerate(
            zip(raw_steps, normalized_steps)
        ):
            rows.append(
                {
                    "artifact_id": artifact_id,
                    "sample_id": sample_id,
                    "split_role": split_role,
                    "stage": stage,
                    "cluster_id": cluster_id,
                    "report_cluster": report_cluster,
                    "step_side": step_side,
                    "step_index": step_index,
                    "trace_key": trace_key(artifact_id, step_side, step_index),
                    "raw_step_payload_sha256": sha256_json(raw_step),
                    "normalized_step_payload_sha256": sha256_json(normalized_step),
                    "raw_step_identity": raw_step,
                    "normalized_step_identity": normalized_step,
                    "raw_payload_sha256": raw_payload_sha256,
                    "normalized_payload_sha256": normalized_payload_sha256,
                    "normalization_function": NORMALIZATION_FUNCTION,
                    "normalization_version": NORMALIZATION_VERSION,
                }
            )
    return rows


class RuntimeBindingV2:
    def __init__(
        self,
        contract: dict[str, Any],
        trace_rows_by_artifact: dict[str, list[dict[str, Any]]],
    ) -> None:
        normalization = contract.get("normalization", {})
        trace = contract.get("trace", {})
        normalization_function = contract.get(
            "normalization_function", normalization.get("function")
        )
        normalization_version = contract.get(
            "normalization_version", normalization.get("version")
        )
        fail_closed = contract.get("fail_closed", trace.get("fail_closed"))
        if normalization_function != NORMALIZATION_FUNCTION:
            raise BindingV2Error("NORMALIZATION_FUNCTION_CONTRACT_MISMATCH")
        if normalization_version != NORMALIZATION_VERSION:
            raise BindingV2Error("NORMALIZATION_VERSION_CONTRACT_MISMATCH")
        if fail_closed is not True:
            raise BindingV2Error("FAIL_CLOSED_CONTRACT_REQUIRED")
        self.contract = contract
        self.trace_rows_by_artifact = trace_rows_by_artifact

    @classmethod
    def from_paths(
        cls,
        contract_path: Path = DEFAULT_CONTRACT_PATH,
        mapping_path: Path | None = None,
    ) -> RuntimeBindingV2:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        actual_mapping_path = (
            mapping_path
            if mapping_path is not None
            else contract_path.parent / contract["trace"]["mapping_path"]
        )
        mapping_bytes = actual_mapping_path.read_bytes()
        if sha256_text(mapping_bytes.decode("utf-8")) != contract["trace"]["mapping_sha256"]:
            raise BindingV2Error("MAPPING_FILE_HASH_MISMATCH")
        rows = [
            json.loads(line)
            for line in mapping_bytes.decode("utf-8").splitlines()
            if line
        ]
        if any(set(row) != set(TRACE_FIELDS) for row in rows):
            raise BindingV2Error("MAPPING_ROW_SCHEMA_MISMATCH")
        trace_keys = [row["trace_key"] for row in rows]
        if len(trace_keys) != len(set(trace_keys)):
            raise BindingV2Error("MAPPING_TRACE_KEY_DUPLICATE")
        by_artifact: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            by_artifact.setdefault(row["artifact_id"], []).append(row)
        expected_pairs = contract["accounting"]["pairs"]
        expected_steps = contract["accounting"]["steps"]
        expected_trace_keys = contract["accounting"]["unique_trace_keys"]
        if (
            len(by_artifact) != expected_pairs
            or len(rows) != expected_steps
            or len(trace_keys) != expected_trace_keys
        ):
            raise BindingV2Error(
                "MAPPING_ACCOUNTING_MISMATCH",
                pairs=len(by_artifact),
                steps=len(rows),
                trace_keys=len(trace_keys),
                expected_pairs=expected_pairs,
                expected_steps=expected_steps,
                expected_trace_keys=expected_trace_keys,
            )
        return cls(contract, by_artifact)

    def score_pair(
        self,
        record: dict[str, Any],
        *,
        artifact_id: str,
        sample_id: str,
        expected_trace_rows: Iterable[dict[str, Any]],
        expected_raw_sha256: str,
    ) -> dict[str, Any]:
        if not expected_raw_sha256:
            raise BindingV2Error("EXPECTED_RAW_HASH_REQUIRED")
        raw = raw_payload_from_record(record)
        raw_payload_sha256 = sha256_json(raw)
        if raw_payload_sha256 != expected_raw_sha256:
            raise BindingV2Error(
                "RAW_PAYLOAD_HASH_MISMATCH",
                expected=expected_raw_sha256,
                observed=raw_payload_sha256,
            )
        normalized = normalized_payload_from_record(raw)
        normalized_payload_sha256 = artifact_hash(normalized)
        if normalized_payload_sha256 != sha256_json(normalized):
            raise BindingV2Error("NORMALIZED_HASH_IMPLEMENTATION_MISMATCH")
        computed_rows = build_trace_rows(
            raw,
            artifact_id=artifact_id,
            sample_id=sample_id,
            split_role=record.get("split_role", ""),
            stage=record.get("stage", ""),
            cluster_id=record.get("cluster_id", ""),
            report_cluster=record.get("report_cluster", ""),
            raw_payload_sha256=raw_payload_sha256,
            normalized_payload_sha256=normalized_payload_sha256,
        )
        computed_by_key = {row["trace_key"]: row for row in computed_rows}
        if len(computed_by_key) != len(computed_rows):
            raise BindingV2Error("COMPUTED_TRACE_KEY_DUPLICATE")
        expected_by_key: dict[str, dict[str, Any]] = {}
        for row in expected_trace_rows:
            key = row.get("trace_key")
            if not key:
                raise BindingV2Error("EXPECTED_TRACE_KEY_MISSING")
            if key in expected_by_key:
                raise BindingV2Error("EXPECTED_TRACE_KEY_DUPLICATE", trace_key=key)
            expected_by_key[key] = row
        missing_keys = sorted(set(computed_by_key) - set(expected_by_key))
        if missing_keys:
            raise BindingV2Error(
                "BINDING_TRACE_MISSING",
                trace_key=missing_keys[0],
                missing_count=len(missing_keys),
            )
        extra_keys = sorted(set(expected_by_key) - set(computed_by_key))
        if extra_keys:
            raise BindingV2Error(
                "BINDING_TRACE_UNEXPECTED",
                trace_key=extra_keys[0],
                unexpected_count=len(extra_keys),
            )
        for key in sorted(computed_by_key):
            if expected_by_key[key] != computed_by_key[key]:
                raise BindingV2Error(
                    "BINDING_TRACE_MISMATCH",
                    trace_key=key,
                )
        runtime_record = {**raw, "artifact_sha256": normalized_payload_sha256}
        scored = score_pair(runtime_record)
        if scored.get("artifact_sha256") != normalized_payload_sha256:
            raise BindingV2Error("SCORER_NORMALIZED_HASH_MISMATCH")
        return {
            "scorer": scored,
            "binding": {
                "artifact_id": artifact_id,
                "sample_id": sample_id,
                "raw_payload_sha256": raw_payload_sha256,
                "normalized_payload_sha256": normalized_payload_sha256,
                "scorer_artifact_sha256": scored["artifact_sha256"],
                "normalization_function": NORMALIZATION_FUNCTION,
                "normalization_version": NORMALIZATION_VERSION,
                "trace_keys": sorted(computed_by_key),
                "raw_hash_field": "artifact_sha256(raw stored payload)",
                "normalized_hash_field": "artifact_sha256(score_pair runtime payload)",
            },
        }

    def score_stored_pair(self, record: dict[str, Any]) -> dict[str, Any]:
        raw = raw_payload_from_record(record)
        raw_hash = record.get("artifact_sha256")
        if not isinstance(raw_hash, str) or not raw_hash:
            raise BindingV2Error("STORED_RAW_HASH_REQUIRED")
        artifact_id = record.get("artifact_id")
        sample_id = record.get("sample_id")
        if not isinstance(artifact_id, str) or not artifact_id:
            raise BindingV2Error("STORED_ARTIFACT_ID_REQUIRED")
        if not isinstance(sample_id, str) or not sample_id:
            raise BindingV2Error("STORED_SAMPLE_ID_REQUIRED")
        expected_rows = self.trace_rows_by_artifact.get(artifact_id)
        if expected_rows is None:
            raise BindingV2Error(
                "BINDING_TRACE_MISSING",
                trace_key=f"{artifact_id}::clean::0000",
            )
        runtime_metadata = {
            key: record.get(key, "")
            for key in ("split_role", "stage", "cluster_id", "report_cluster")
        }
        runtime_record = {**raw, "artifact_sha256": raw_hash, **runtime_metadata}
        return self.score_pair(
            runtime_record,
            artifact_id=artifact_id,
            sample_id=sample_id,
            expected_trace_rows=expected_rows,
            expected_raw_sha256=raw_hash,
        )
