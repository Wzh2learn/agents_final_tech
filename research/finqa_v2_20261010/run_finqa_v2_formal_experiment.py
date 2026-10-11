#!/usr/bin/env python3
"""Execute the frozen FinQA v2 Loop A formal experiment."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TASK_DIR = Path(__file__).resolve().parent
RESULTS_DIR = TASK_DIR / "results"
SEED = 20261017
REPLICATES = 10_000
STAGES = ("E", "P", "N")
SCORER_FIELDS = (
    "evidence_required_hit",
    "operator_consistency",
    "argument_consistency",
    "step_result_consistency",
    "answer_consistency",
)
FOCUSED_TEST_COMMAND = (
    "PYTHONPATH=src ./venv/bin/python -m pytest "
    "tests/test_finqa_numeric_token_canonicalization_v2.py "
    "tests/test_finqa_evidence_argument_resolver_v2.py "
    "tests/test_finqa_independent_observation_scorer_v2.py "
    "tests/test_finqa_v2_execution_freeze.py -q"
)
REQUIRED_OUTPUTS = (
    "finqa_v2_formal_sample_rows.jsonl",
    "finqa_v2_formal_results.json",
    "finqa_v2_bootstrap_replicates.jsonl",
    "FINQA_V2_FORMAL_RESULT_REPORT.md",
    "finqa_v2_formal_execution_receipt.json",
)
FORBIDDEN_OUTPUT_PATTERNS = (
    "*formal*result*",
    "*evaluator*output*",
    "*prediction*rows*",
    "*scoring*output*",
    "*bootstrap_replicates*",
    "*formal_sample_rows*",
)


class FormalRunError(RuntimeError):
    def __init__(self, code: str, **detail: Any) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def json_hash(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def self_hash(value: dict[str, Any]) -> str:
    return json_hash({key: item for key, item in value.items() if key != "self_sha256"})


def now_iso() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")


def read_json(name: str) -> dict[str, Any]:
    return json.loads((TASK_DIR / name).read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def verify_bound_file(
    record: dict[str, Any],
    label: str,
    lines: list[str],
    counter: dict[str, int],
) -> None:
    path = Path(record["path"])
    if not path.is_file():
        raise FormalRunError("HASH_MISSING", label=label, path=str(path))
    actual = sha256_file(path)
    if actual != record["sha256"]:
        raise FormalRunError(
            "HASH_MISMATCH",
            label=label,
            path=str(path),
            expected=record["sha256"],
            actual=actual,
        )
    if path.stat().st_size != record["bytes"]:
        raise FormalRunError(
            "BYTE_LENGTH_MISMATCH",
            label=label,
            path=str(path),
            expected=record["bytes"],
            actual=path.stat().st_size,
        )
    lines.append(f"HASH_OK {label} {actual} {path}")
    counter["checks"] += 1


def verify_self_hash(
    payload: dict[str, Any],
    expected: str,
    label: str,
    lines: list[str],
    counter: dict[str, int],
) -> None:
    actual = self_hash(payload)
    if actual != expected:
        raise FormalRunError(
            "SELF_HASH_MISMATCH",
            label=label,
            expected=expected,
            actual=actual,
        )
    lines.append(f"HASH_OK {label} {actual}")
    counter["checks"] += 1


def verify_frozen_hashes() -> tuple[list[str], int]:
    lines: list[str] = []
    counter = {"checks": 0}
    analysis_manifest = read_json("finqa_v2_analysis_plan_hash_manifest.json")
    for name, record in analysis_manifest["bound_files"].items():
        if name == "scorer_tests":
            for index, test_record in enumerate(record):
                verify_bound_file(
                    test_record,
                    f"analysis.bound.{name}[{index}]",
                    lines,
                    counter,
                )
        else:
            verify_bound_file(record, f"analysis.bound.{name}", lines, counter)
    verify_self_hash(
        analysis_manifest,
        analysis_manifest["self_sha256"],
        "analysis.manifest.self",
        lines,
        counter,
    )

    analysis_receipt = read_json("finqa_v2_analysis_preresult_freeze_receipt.json")
    for label in ("markdown", "json"):
        verify_bound_file(
            analysis_receipt["analysis_plan"][label],
            f"analysis.receipt.plan.{label}",
            lines,
            counter,
        )
    verify_bound_file(
        analysis_receipt["hash_manifest"],
        "analysis.receipt.hash_manifest.raw",
        lines,
        counter,
    )
    verify_self_hash(
        analysis_manifest,
        analysis_receipt["hash_manifest"]["self_sha256"],
        "analysis.receipt.hash_manifest.self",
        lines,
        counter,
    )
    verify_self_hash(
        analysis_receipt,
        analysis_receipt["self_sha256"],
        "analysis.receipt.self",
        lines,
        counter,
    )

    prior_receipt = read_json("finqa_v2_preresult_freeze_receipt.json")
    for group in ("input_sha256", "output_sha256"):
        for name, record in prior_receipt[group].items():
            verify_bound_file(record, f"prior.{group}.{name}", lines, counter)
    verify_self_hash(
        prior_receipt,
        prior_receipt["self_sha256"],
        "prior.receipt.self",
        lines,
        counter,
    )
    packet = read_json("finqa_v2_execution_freeze_packet.json")
    verify_self_hash(
        packet,
        packet["self_sha256"],
        "prior.packet.self",
        lines,
        counter,
    )
    if packet["self_sha256"] != prior_receipt["packet_self_sha256"]:
        raise FormalRunError("PACKET_SELF_HASH_CROSSBIND_MISMATCH")

    binding = read_json("finqa_v2_scorer_binding_manifest.json")
    for name, record in binding["input_manifests"].items():
        verify_bound_file(record, f"scorer.input.{name}", lines, counter)
    verify_bound_file(binding["source"], "scorer.source", lines, counter)
    for index, record in enumerate(binding["tests"]):
        verify_bound_file(record, f"scorer.test[{index}]", lines, counter)

    paired = read_json("finqa_v2_paired_artifact_manifest.json")
    for index, record in enumerate(paired["source_hashes"]):
        verify_bound_file(record, f"paired.source[{index}]", lines, counter)

    sample_path = TASK_DIR / "finqa_v2_frozen_sample_manifest.json"
    split = read_json("finqa_v2_split_manifest.json")
    if split["source_sample_manifest_sha256"] != sha256_file(sample_path):
        raise FormalRunError("SAMPLE_SPLIT_HASH_CROSSBIND_MISMATCH")
    lines.append(
        f"HASH_OK sample.split.crossbind {split['source_sample_manifest_sha256']}"
    )
    counter["checks"] += 1
    lines.append(f"FROZEN_HASH_PREFLIGHT PASS checks={counter['checks']} mismatches=0")
    return lines, counter["checks"]


def assert_analysis_contract(plan: dict[str, Any]) -> None:
    expected_primary = {
        "visibility_count",
        "visibility_rate",
        "detection_count",
        "detection_rate",
        "visibility_detection_2x2",
        "detection_rate_given_visibility_positive",
        "detection_rate_given_visibility_negative",
    }
    expected_secondary = {
        "per_stage_profiles",
        "terminal_outcome_count",
        "terminal_outcome_rate",
        "missing_invalid_scorer_failure_unevaluable_accounting",
    }
    if {item["id"] for item in plan["estimands"]["primary"]} != expected_primary:
        raise FormalRunError("ANALYSIS_PRIMARY_CONTRACT_MISMATCH")
    if {item["id"] for item in plan["estimands"]["secondary"]} != expected_secondary:
        raise FormalRunError("ANALYSIS_SECONDARY_CONTRACT_MISMATCH")
    if plan["uncertainty"]["seed"] != SEED:
        raise FormalRunError("BOOTSTRAP_SEED_MISMATCH")
    if plan["uncertainty"]["replicate_count"] != REPLICATES:
        raise FormalRunError("BOOTSTRAP_REPLICATE_MISMATCH")
    if plan["uncertainty"]["cluster_unit"] != "report_cluster_id":
        raise FormalRunError("BOOTSTRAP_CLUSTER_UNIT_MISMATCH")
    if plan["uncertainty"]["percentiles"] != [2.5, 97.5]:
        raise FormalRunError("BOOTSTRAP_PERCENTILE_MISMATCH")
    if plan["permutation_contract"]["PERMUTATION_TEST"] != "NOT_USED":
        raise FormalRunError("PERMUTATION_CONTRACT_MISMATCH")
    if plan["population"]["sample_count"] != 89:
        raise FormalRunError("POPULATION_SAMPLE_MISMATCH")
    if plan["population"]["report_cluster_count"] != 30:
        raise FormalRunError("POPULATION_CLUSTER_MISMATCH")


def verify_preflight_log() -> tuple[str, int]:
    path = RESULTS_DIR / "finqa_v2_focused_preflight.log"
    if not path.is_file():
        raise FormalRunError("FOCUSED_PREFLIGHT_LOG_MISSING", path=str(path))
    text = path.read_text(encoding="utf-8")
    if f"COMMAND={FOCUSED_TEST_COMMAND}" not in text:
        raise FormalRunError("FOCUSED_TEST_COMMAND_MISMATCH")
    if "EXIT_CODE=0" not in text or "19 passed" not in text:
        raise FormalRunError("FOCUSED_TEST_FAILURE")
    return sha256_file(path), 19


def formal_output_inventory() -> list[str]:
    hits: set[str] = set()
    for pattern in FORBIDDEN_OUTPUT_PATTERNS:
        hits.update(
            str(path.relative_to(TASK_DIR))
            for path in TASK_DIR.rglob(pattern)
            if path.is_file()
        )
    hits.update(
        name for name in REQUIRED_OUTPUTS if (RESULTS_DIR / name).is_file()
    )
    return sorted(hits)


def safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def base_estimands(rows: list[dict[str, Any]]) -> dict[str, int | float | None]:
    denominator = len(rows)
    values: dict[str, int | float | None] = {}
    visibility_count = sum(row["V"] for row in rows)
    detection_count = sum(row["D"] for row in rows)
    values["visibility_count"] = visibility_count
    values["visibility_rate"] = safe_rate(visibility_count, denominator)
    values["detection_count"] = detection_count
    values["detection_rate"] = safe_rate(detection_count, denominator)
    for visibility in (0, 1):
        for detection in (0, 1):
            count = sum(
                row["V"] == visibility and row["D"] == detection for row in rows
            )
            values[f"visibility_detection_2x2.v{visibility}_d{detection}_count"] = count
            values[
                f"visibility_detection_2x2.v{visibility}_d{detection}_rate"
            ] = safe_rate(count, denominator)
    visibility_positive = [row for row in rows if row["V"] == 1]
    visibility_negative = [row for row in rows if row["V"] == 0]
    values["detection_rate_given_visibility_positive"] = safe_rate(
        sum(row["D"] for row in visibility_positive), len(visibility_positive)
    )
    values["detection_rate_given_visibility_negative"] = safe_rate(
        sum(row["D"] for row in visibility_negative), len(visibility_negative)
    )
    return values


def overall_estimands(rows: list[dict[str, Any]]) -> dict[str, int | float | None]:
    values = base_estimands(rows)
    outcome_count = sum(row["O"] for row in rows)
    values["terminal_outcome_count"] = outcome_count
    values["terminal_outcome_rate"] = safe_rate(outcome_count, len(rows))
    values["failure_accounting.missing_count"] = sum(
        int(row["missing"]) for row in rows
    )
    values["failure_accounting.invalid_record_count"] = sum(
        int(row["invalid_record"]) for row in rows
    )
    values["failure_accounting.scorer_failure_count"] = sum(
        int(row["scorer_failure"]) for row in rows
    )
    values["failure_accounting.unevaluable_count"] = sum(
        int(row["unevaluable"]) for row in rows
    )
    return values


def stage_estimands(
    rows: list[dict[str, Any]], stage: str
) -> dict[str, int | float | None]:
    stage_rows = [row for row in rows if row["stage"] == stage]
    return {
        f"stage.{stage}.{name}": value
        for name, value in base_estimands(stage_rows).items()
        if not name.startswith("detection_rate_given_")
    }


def all_estimands(rows: list[dict[str, Any]]) -> dict[str, int | float | None]:
    values = overall_estimands(rows)
    for stage in STAGES:
        values.update(stage_estimands(rows, stage))
    return values


def load_evaluation_rows() -> tuple[list[dict[str, Any]], int]:
    samples_payload = read_json("finqa_v2_frozen_sample_manifest.json")
    split_payload = read_json("finqa_v2_split_manifest.json")
    paired_payload = read_json("finqa_v2_paired_artifact_manifest.json")
    binding_payload = read_json("finqa_v2_scorer_binding_manifest.json")

    if samples_payload["counts"]["candidate_injections"] != 216:
        raise FormalRunError("CANDIDATE_COUNT_MISMATCH")
    if samples_payload["counts"]["retained_injections"] != 215:
        raise FormalRunError("RETAINED_COUNT_MISMATCH")
    if samples_payload["counts"]["excluded_injections"] != 1:
        raise FormalRunError("EXCLUSION_COUNT_MISMATCH")
    if not split_payload["group_disjointness"]["passed"]:
        raise FormalRunError("SPLIT_GROUP_DISJOINTNESS_FAILED")
    if not split_payload["assignment_checks"]["passed"]:
        raise FormalRunError("ASSIGNMENT_CHECK_FAILED")
    if not split_payload["leakage_fail_closed"]["passed"]:
        raise FormalRunError("SPLIT_LEAKAGE_FAIL_CLOSED_FAILED")
    if not binding_payload["independence"]["passed"]:
        raise FormalRunError("SCORER_INDEPENDENCE_FAILED")
    if binding_payload["semantic_correctness_claim"] is not False:
        raise FormalRunError("SCORER_SEMANTIC_CLAIM_MISMATCH")
    if tuple(binding_payload["observation_surface"]) != SCORER_FIELDS:
        raise FormalRunError("SCORER_OBSERVATION_SURFACE_MISMATCH")
    if binding_payload["formal_evaluator_outputs_materialized"] != 0:
        raise FormalRunError("BINDING_FORMAL_OUTPUT_COUNT_MISMATCH")

    nested_paired_hash_checks = 0
    for artifact in paired_payload["artifacts"]:
        if json_hash(artifact["artifact"]) != artifact["artifact_sha256"]:
            raise FormalRunError(
                "PAIRED_ARTIFACT_HASH_MISMATCH",
                sample_id=artifact["sample_id"],
            )
        if json_hash(artifact["artifact"]["clean"]) != artifact["clean_artifact_sha256"]:
            raise FormalRunError(
                "CLEAN_ARTIFACT_HASH_MISMATCH",
                sample_id=artifact["sample_id"],
            )
        if json_hash(artifact["artifact"]["mutant"]) != artifact["mutant_artifact_sha256"]:
            raise FormalRunError(
                "MUTANT_ARTIFACT_HASH_MISMATCH",
                sample_id=artifact["sample_id"],
            )
        nested_paired_hash_checks += 3

    sample_by_id = {
        row["sample_id"]: row for row in samples_payload["samples"]
    }
    paired_by_id = {row["sample_id"]: row for row in paired_payload["artifacts"]}
    binding_by_id = {row["sample_id"]: row for row in binding_payload["bindings"]}
    expected_roles = Counter(row["split_role"] for row in split_payload["samples"])
    if expected_roles != Counter(train=81, calibration=45, evaluation=89):
        raise FormalRunError("SPLIT_ROLE_COUNT_MISMATCH", actual=dict(expected_roles))

    selected = [
        row for row in split_payload["samples"] if row["split_role"] == "evaluation"
    ]
    if len(selected) != 89:
        raise FormalRunError("EVALUATION_SAMPLE_SELECTION_MISMATCH", count=len(selected))
    if len({row["sample_id"] for row in selected}) != 89:
        raise FormalRunError("EVALUATION_SAMPLE_DUPLICATE")

    rows: list[dict[str, Any]] = []
    for split_row in selected:
        sample_id = split_row["sample_id"]
        if sample_id not in sample_by_id or sample_id not in paired_by_id:
            raise FormalRunError("MISSING_RETAINED_RECORD", sample_id=sample_id)
        sample = sample_by_id[sample_id]
        paired = paired_by_id[sample_id]
        binding = binding_by_id.get(sample_id)
        if binding is None:
            raise FormalRunError("MISSING_SCORER_BINDING", sample_id=sample_id)
        if not sample.get("retained"):
            raise FormalRunError("NONRETAINED_EVALUATION_RECORD", sample_id=sample_id)
        if sample["split_role"] != "evaluation" or paired["split_role"] != "evaluation":
            raise FormalRunError("SPLIT_ROLE_MISMATCH", sample_id=sample_id)
        if binding["status"] != "BOUND_UNSCORED_PENDING_LATER_AUTHORIZED_EXECUTION":
            raise FormalRunError("SCORER_BINDING_STATUS_MISMATCH", sample_id=sample_id)
        hashes = (
            sample["artifact_sha256"],
            paired["artifact_sha256"],
            binding["artifact_sha256"],
        )
        if len(set(hashes)) != 1:
            raise FormalRunError("ARTIFACT_HASH_CROSSBIND_MISMATCH", sample_id=sample_id)
        if sample["artifact_id"] != paired["artifact_id"] or sample["artifact_id"] != binding["artifact_id"]:
            raise FormalRunError("ARTIFACT_ID_CROSSBIND_MISMATCH", sample_id=sample_id)
        if sample["stage"] != paired["stage"] or sample["stage"] != split_row["stage"]:
            raise FormalRunError("STAGE_CROSSBIND_MISMATCH", sample_id=sample_id)
        payload = {**paired["artifact"], "artifact_sha256": paired["artifact_sha256"]}
        rows.append(
            {
                "sample_id": sample_id,
                "artifact_id": sample["artifact_id"],
                "stage": sample["stage"],
                "cluster_id": sample["cluster_id"],
                "report_cluster_id": sample["provenance"]["report_cluster_id"],
                "report_cluster": sample["report_cluster"],
                "record_id": sample["record_id"],
                "record_sha256": sample["record_sha256"],
                "split_role": "evaluation",
                "manifest_artifact_sha256": sample["artifact_sha256"],
                "_score_payload": payload,
                "missing": False,
                "invalid_record": False,
                "scorer_failure": False,
                "unevaluable": False,
            }
        )

    evaluation_ids = {
        row["sample_id"]
        for row in split_payload["samples"]
        if row["split_role"] == "evaluation"
    }
    if evaluation_ids != {row["sample_id"] for row in rows}:
        raise FormalRunError("EVALUATION_SELECTION_CROSSBIND_MISMATCH")
    stage_counts = Counter(row["stage"] for row in rows)
    if stage_counts != Counter(E=30, P=30, N=29):
        raise FormalRunError("STAGE_EVALUATION_COUNT_MISMATCH", actual=dict(stage_counts))
    stage_clusters = {
        stage: len({row["cluster_id"] for row in rows if row["stage"] == stage})
        for stage in STAGES
    }
    if stage_clusters != {stage: 10 for stage in STAGES}:
        raise FormalRunError("STAGE_CLUSTER_COUNT_MISMATCH", actual=stage_clusters)
    if len({row["cluster_id"] for row in rows}) != 30:
        raise FormalRunError("OVERALL_CLUSTER_COUNT_MISMATCH")
    return rows, nested_paired_hash_checks


def score_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    from research.finqa_independent_observation_scorer_v2 import score_pair

    output: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for row in rows:
        try:
            scored = score_pair(row["_score_payload"])
            vector = scored["observation_vector"]
            if set(vector) != set(SCORER_FIELDS):
                raise ValueError("observation_field_mismatch")
            if any(type(vector[field]) is not int or vector[field] not in (0, 1) for field in SCORER_FIELDS):
                raise ValueError("observation_value_invalid")
            if scored["artifact_sha256"] != row["manifest_artifact_sha256"]:
                raise ValueError("normalized_scorer_payload_hash_mismatch")
            visibility = int(any(vector[field] == 1 for field in SCORER_FIELDS))
            detection = int(
                vector["step_result_consistency"] == 1
                or vector["answer_consistency"] == 1
            )
            outcome = int(vector["answer_consistency"] == 1)
            output.append(
                {
                    "sample_id": row["sample_id"],
                    "artifact_id": row["artifact_id"],
                    "stage": row["stage"],
                    "cluster_id": row["cluster_id"],
                    "report_cluster_id": row["report_cluster_id"],
                    "report_cluster": row["report_cluster"],
                    "record_id": row["record_id"],
                    "record_sha256": row["record_sha256"],
                    "split_role": row["split_role"],
                    "manifest_artifact_sha256": row["manifest_artifact_sha256"],
                    "scorer_payload_sha256": scored["artifact_sha256"],
                    "observation_vector": vector,
                    "V": visibility,
                    "D": detection,
                    "O": outcome,
                    "record_status": "VALID",
                    "missing": False,
                    "invalid_record": False,
                    "scorer_failure": False,
                    "unevaluable": False,
                }
            )
        except Exception as error:
            failures.append(
                {
                    "sample_id": row["sample_id"],
                    "error_type": type(error).__name__,
                    "error": str(error),
                }
            )
    if failures or len(output) != 89:
        raise FormalRunError(
            "FORMAL_RUN_INVALID",
            expected=89,
            scored=len(output),
            failures=failures,
        )
    return output, 89


def percentile_interval(values: list[float]) -> tuple[float, float, str]:
    if not values:
        return float("nan"), float("nan"), "NOT_IDENTIFIABLE"
    low, high = np.percentile(
        np.asarray(values, dtype=float),
        [2.5, 97.5],
        method="linear",
    )
    label = "DEGENERATE_EMPIRICAL_INTERVAL" if low == high else "PERCENTILE_95"
    return float(low), float(high), label


def bootstrap(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    cluster_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    stage_clusters: dict[str, list[str]] = {}
    for row in rows:
        cluster_rows[row["cluster_id"]].append(row)
    for stage in STAGES:
        stage_clusters[stage] = sorted(
            {row["cluster_id"] for row in rows if row["stage"] == stage}
        )
    overall_clusters = sorted(cluster_rows)
    if len(overall_clusters) != 30 or any(len(value) != 10 for value in stage_clusters.values()):
        raise FormalRunError("BOOTSTRAP_CLUSTER_BINDING_MISMATCH")

    rng = np.random.default_rng(SEED)
    values: dict[str, list[float]] = defaultdict(list)
    failures: Counter[str] = Counter()
    replicate_rows: list[dict[str, Any]] = []
    expected_ids = set(all_estimands(rows))
    for replicate_index in range(REPLICATES):
        overall_draw = [
            overall_clusters[int(index)]
            for index in rng.integers(0, len(overall_clusters), size=len(overall_clusters))
        ]
        overall_counts = Counter(overall_draw)
        overall_sample = [
            row
            for cluster_id, count in overall_counts.items()
            for row in cluster_rows[cluster_id]
            for _ in range(count)
        ]
        replicate_values = overall_estimands(overall_sample)
        stage_multiplicities: dict[str, dict[str, int]] = {}
        for stage in STAGES:
            clusters = stage_clusters[stage]
            stage_draw = [
                clusters[int(index)]
                for index in rng.integers(0, len(clusters), size=len(clusters))
            ]
            multiplicities = Counter(stage_draw)
            stage_multiplicities[stage] = dict(sorted(multiplicities.items()))
            stage_sample = [
                row
                for cluster_id, count in multiplicities.items()
                for row in cluster_rows[cluster_id]
                for _ in range(count)
            ]
            replicate_values.update(stage_estimands(stage_sample, stage))
        if set(replicate_values) != expected_ids:
            raise FormalRunError("BOOTSTRAP_ESTIMAND_SET_MISMATCH")

        estimates: dict[str, float | None] = {}
        failed_ids: list[str] = []
        for estimand_id in sorted(expected_ids):
            estimate = replicate_values[estimand_id]
            if estimate is None:
                estimates[estimand_id] = None
                failed_ids.append(estimand_id)
                failures[estimand_id] += 1
            else:
                numeric = float(estimate)
                estimates[estimand_id] = numeric
                values[estimand_id].append(numeric)
        replicate_rows.append(
            {
                "replicate_index": replicate_index,
                "seed": SEED,
                "cluster_unit": "report_cluster_id",
                "cluster_multiplicities": {
                    "overall": dict(sorted(overall_counts.items())),
                    "per_stage": stage_multiplicities,
                },
                "estimates": estimates,
                "failed_estimand_ids": failed_ids,
            }
        )

    point_values = all_estimands(rows)
    summary: dict[str, dict[str, Any]] = {}
    for estimand_id in sorted(expected_ids):
        valid = len(values[estimand_id])
        failed = failures[estimand_id]
        if valid == 0:
            interval: Any = "NOT_IDENTIFIABLE"
            interval_label = "NOT_IDENTIFIABLE"
        else:
            low, high, interval_label = percentile_interval(values[estimand_id])
            interval = [low, high]
        point = point_values[estimand_id]
        summary[estimand_id] = {
            "point_estimate": point,
            "point_estimate_status": "NOT_IDENTIFIABLE" if point is None else "ESTIMATED",
            "interval": interval,
            "interval_label": interval_label,
            "seed": SEED,
            "replicate_count": REPLICATES,
            "valid_replicate_count": valid,
            "failed_replicate_count": failed,
            "cluster_unit": "report_cluster_id",
            "ci_method": "PERCENTILE",
            "percentiles": [2.5, 97.5],
            "percentile_interpolation": "linear",
        }
        if valid + failed != REPLICATES:
            raise FormalRunError("BOOTSTRAP_ACCOUNTING_MISMATCH", estimand=estimand_id)
    return replicate_rows, summary


def nested_tables(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def table(stage: str | None = None) -> dict[str, Any]:
        scoped = rows if stage is None else [row for row in rows if row["stage"] == stage]
        denominator = len(scoped)
        cells = {}
        for visibility in (0, 1):
            for detection in (0, 1):
                count = sum(
                    row["V"] == visibility and row["D"] == detection for row in scoped
                )
                cells[f"{visibility}{detection}"] = {
                    "count": count,
                    "rate": safe_rate(count, denominator),
                }
        visibility_count = sum(row["V"] for row in scoped)
        detection_count = sum(row["D"] for row in scoped)
        visibility_positive = [row for row in scoped if row["V"] == 1]
        visibility_negative = [row for row in scoped if row["V"] == 0]
        profile = {
            "sample_denominator": denominator,
            "cluster_denominator": len({row["cluster_id"] for row in scoped}),
            "visibility_count": visibility_count,
            "visibility_rate": safe_rate(visibility_count, denominator),
            "detection_count": detection_count,
            "detection_rate": safe_rate(detection_count, denominator),
            "visibility_detection_2x2": cells,
        }
        if stage is None:
            profile.update(
                {
                    "detection_rate_given_visibility_positive": safe_rate(
                        sum(row["D"] for row in visibility_positive),
                        len(visibility_positive),
                    ),
                    "detection_rate_given_visibility_negative": safe_rate(
                        sum(row["D"] for row in visibility_negative),
                        len(visibility_negative),
                    ),
                    "terminal_outcome_count": sum(row["O"] for row in scoped),
                    "terminal_outcome_rate": safe_rate(
                        sum(row["O"] for row in scoped), denominator
                    ),
                }
            )
        return profile

    return {
        "overall": table(),
        "per_stage": {stage: table(stage) for stage in STAGES},
    }


def case_accounting(rows: list[dict[str, Any]]) -> dict[str, Any]:
    categories = {
        "visibility_without_detection_v1_d0": [
            row["sample_id"] for row in rows if row["V"] == 1 and row["D"] == 0
        ],
        "detection_without_visibility_v0_d1": [
            row["sample_id"] for row in rows if row["V"] == 0 and row["D"] == 1
        ],
        "null_identity_v0_d0": [
            row["sample_id"] for row in rows if row["V"] == 0 and row["D"] == 0
        ],
        "null_identity_v1_d1": [
            row["sample_id"] for row in rows if row["V"] == 1 and row["D"] == 1
        ],
    }
    per_stage = {}
    for stage in STAGES:
        scoped = [row for row in rows if row["stage"] == stage]
        per_stage[stage] = {
            "v1_d0": sum(row["V"] == 1 and row["D"] == 0 for row in scoped),
            "v0_d1": sum(row["V"] == 0 and row["D"] == 1 for row in scoped),
            "v_eq_d": sum(row["V"] == row["D"] for row in scoped),
        }
    return {
        "categories": {name: sorted(ids) for name, ids in categories.items()},
        "counts": {name: len(ids) for name, ids in categories.items()},
        "per_stage": per_stage,
        "all_89_evaluation_rows_preserved": len(rows) == 89,
    }


def recommended_class(rows: list[dict[str, Any]], contract_valid: bool) -> str:
    if not contract_valid:
        return "SECOND_FLOW_INVALID"
    visibility_values = {row["V"] for row in rows}
    detection_values = {row["D"] for row in rows}
    nonidentity = any(row["V"] != row["D"] for row in rows)
    informative = any(row["V"] == 1 and row["D"] == 0 for row in rows)
    if all(row["V"] == row["D"] for row in rows) or not nonidentity:
        return "SECOND_FLOW_NULL"
    if len(visibility_values) > 1 and len(detection_values) > 1 and informative:
        return "SECOND_FLOW_POSITIVE"
    return "SECOND_FLOW_MIXED"


def format_rate(value: int | float | None) -> str:
    if value is None:
        return "NOT_IDENTIFIABLE"
    if isinstance(value, int):
        return str(value)
    return f"{value:.6f}"


def render_report(payload: dict[str, Any]) -> str:
    overall = payload["tables"]["overall"]
    cases = payload["case_accounting"]
    bootstrap = payload["bootstrap_summary"]
    lines = [
        "# FinQA v2 Formal Second-Flow Result Report",
        "",
        f"- Task ID: `{payload['task_id']}`",
        f"- Run status: `{payload['run_status']}`",
        f"- `A_RECOMMENDED_CLASS`: `{payload['A_RECOMMENDED_CLASS']}`",
        "- Final class decision: deferred to Loop D after Loop C audit.",
        "- Window: zero-endpoint, non-training, no permutation test.",
        "",
        "## Frozen Research Question",
        "",
        payload["frozen_research_question"],
        "",
        "## Retained Evaluation Population",
        "",
        "| Stage | Samples | Report clusters |",
        "|---|---:|---:|",
    ]
    for stage in STAGES:
        stage_profile = payload["tables"]["per_stage"][stage]
        lines.append(
            f"| {stage} | {stage_profile['sample_denominator']} | "
            f"{stage_profile['cluster_denominator']} |"
        )
    lines.extend(
        [
            f"| **Total** | **{overall['sample_denominator']}** | "
            f"**{overall['cluster_denominator']}** |",
            "",
            "Train and calibration were not scored for primary analysis: "
            "`81 train`, `45 calibration`.",
            "",
            "## Primary Visibility and Detection",
            "",
            "| Estimand | Count/rate | Denominator |",
            "|---|---:|---:|",
            f"| Visibility | {overall['visibility_count']} / "
            f"{format_rate(overall['visibility_rate'])} | 89 |",
            f"| Detection | {overall['detection_count']} / "
            f"{format_rate(overall['detection_rate'])} | 89 |",
            f"| P(D=1\\|V=1) | {format_rate(overall['detection_rate_given_visibility_positive'])} | "
            f"{overall['visibility_detection_2x2']['10']['count'] + overall['visibility_detection_2x2']['11']['count']} |",
            f"| P(D=1\\|V=0) | {format_rate(overall['detection_rate_given_visibility_negative'])} | "
            f"{overall['visibility_detection_2x2']['00']['count'] + overall['visibility_detection_2x2']['01']['count']} |",
            "",
            "### 2x2 V×D",
            "",
            "| V | D | Count | Rate |",
            "|---:|---:|---:|---:|",
        ]
    )
    for visibility in (0, 1):
        for detection in (0, 1):
            cell = overall["visibility_detection_2x2"][f"{visibility}{detection}"]
            lines.append(
                f"| {visibility} | {detection} | {cell['count']} | "
                f"{format_rate(cell['rate'])} |"
            )
    lines.extend(
        [
            "",
            "## Per-Stage Secondary Profiles",
            "",
            "| Stage | V count/rate | D count/rate | V0D0 | V0D1 | V1D0 | V1D1 |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for stage in STAGES:
        profile = payload["tables"]["per_stage"][stage]
        cells = profile["visibility_detection_2x2"]
        lines.append(
            f"| {stage} | {profile['visibility_count']} / "
            f"{format_rate(profile['visibility_rate'])} | "
            f"{profile['detection_count']} / {format_rate(profile['detection_rate'])} | "
            f"{cells['00']['count']} | {cells['01']['count']} | "
            f"{cells['10']['count']} | {cells['11']['count']} |"
        )
    lines.extend(
        [
            "",
            "## Terminal Outcome Secondary",
            "",
            f"- O count/rate: `{overall['terminal_outcome_count']} / "
            f"{format_rate(overall['terminal_outcome_rate'])}` with denominator `89`.",
            "",
            "## Exclusions, Missing, Invalid and Unevaluable Accounting",
            "",
            "| Account | Count |",
            "|---|---:|",
            "| Candidate injections | 216 |",
            "| Retained paired injections | 215 |",
            "| Excluded before split | 1 ambiguous N join |",
            "| Expected evaluation records | 89 |",
            f"| Successfully scored | {payload['execution']['scorer_calls']} |",
            "| Missing retained records | 0 |",
            "| Invalid retained records | 0 |",
            "| Scorer failures | 0 |",
            "| Unevaluable evaluation records | 0 |",
            "| Preserved evaluation rows | 89 |",
            "",
            "No denominator reduction, result-dependent exclusion, threshold change, "
            "metric addition or adverse-case deletion occurred.",
            "",
            "## Cluster Bootstrap",
            "",
            f"- Seed: `{SEED}`",
            f"- Replicates: `{REPLICATES}`",
            "- Unit: `report_cluster_id`; all paired samples in each selected cluster are retained.",
            "- Interval: 95% percentile, 2.5th/97.5th percentiles, linear interpolation.",
            "- Point estimates remain sample-weighted.",
            "- `PERMUTATION_TEST = NOT_USED`.",
            "",
            "| Estimand | Point | 95% interval | Valid | Failed | Status |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for estimand_id in sorted(bootstrap):
        item = bootstrap[estimand_id]
        interval = item["interval"]
        if isinstance(interval, list):
            interval_text = f"[{interval[0]:.6f}, {interval[1]:.6f}]"
        else:
            interval_text = str(interval)
        lines.append(
            f"| `{estimand_id}` | {format_rate(item['point_estimate'])} | "
            f"{interval_text} | {item['valid_replicate_count']} | "
            f"{item['failed_replicate_count']} | {item['interval_label']} |"
        )
    lines.extend(
        [
            "",
            "## Leakage and Integrity Audit",
            "",
            f"- Frozen hash checks: `{payload['execution']['frozen_hash_checks']}`; "
            "mismatches `0`.",
            f"- Nested paired-artifact hash checks: "
            f"`{payload['execution']['nested_paired_artifact_hash_checks']}`; "
            "mismatches `0`.",
            f"- Focused technical preflight: `{payload['execution']['focused_tests_passed']} passed`.",
            f"- Formal outputs before execution: `{payload['execution']['formal_outputs_before_execution']}`.",
            f"- Split/group leakage: `{payload['leakage_audit']['group_disjointness']}`.",
            f"- Assignment fail-closed checks: `{payload['leakage_audit']['assignment_checks']}`.",
            f"- Scorer label blindness/independence: `{payload['leakage_audit']['scorer_independence']}`.",
            f"- Train/calibration rows scored: `{payload['execution']['non_evaluation_scoring_calls']}`.",
            "- Raw manifest hash and normalized scorer payload hash use distinct row fields.",
            "- Stage labels were used only for the preregistered E/P/N secondary profile.",
            "",
            "## Negative and Null Cases",
            "",
            "| Case | Count |",
            "|---|---:|",
        ]
    )
    for name, count in cases["counts"].items():
        lines.append(f"| `{name}` | {count} |")
    lines.extend(
        [
            "",
            "All 89 evaluation rows are preserved in "
            "`finqa_v2_formal_sample_rows.jsonl`, including null and adverse cases.",
            "",
            "## Allowed Claims",
            "",
            "- Report frozen V, D and O counts, rates, 2x2 cells, conditional rates and cluster-bootstrap intervals exactly as materialized.",
            "- Describe construct distinction only as `A_RECOMMENDED_CLASS`, pending Loop C audit and Loop D decision.",
            "- Label per-stage profiles, O and uncertainty as SECONDARY; label nonidentity/negative cases as NEGATIVE.",
            "",
            "## Forbidden Claims",
            "",
            "- Hierarchy beats flat.",
            "- Hierarchy localizes failures.",
            "- The independent scorer is semantically better or establishes semantic correctness.",
            "- FinQA validates natural-failure localization.",
            "- Harmfulness is established.",
            "- Stage E multi-leaf results transfer automatically.",
            "",
            "## Evidence Grading",
            "",
            "| Evidence | Grade | Boundary |",
            "|---|---|---|",
            "| Overall V/D estimands | CONFIRMATORY | Frozen evaluation role and frozen scorer only |",
            "| Per-stage, O and bootstrap summaries | SECONDARY | Preregistered secondary profiles/uncertainty |",
            "| Adverse and null cases | NEGATIVE | Preserved without deletion or claim redesign |",
            "",
            "No hierarchy/flat comparison, semantic-correctness claim, harmfulness claim, "
            "permutation test, metric search or threshold change is authorized.",
            "",
        ]
    )
    return "\n".join(lines)


def git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> int:
    started_at = now_iso()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    hash_lines, hash_checks = verify_frozen_hashes()
    (RESULTS_DIR / "finqa_v2_frozen_hash_verification.log").write_text(
        "\n".join(hash_lines) + "\n",
        encoding="utf-8",
    )
    plan = read_json("finqa_v2_analysis_plan.json")
    assert_analysis_contract(plan)
    focused_log_sha, focused_tests = verify_preflight_log()
    existing = formal_output_inventory()
    if existing:
        raise FormalRunError("FORMAL_OUTPUT_ALREADY_EXISTS", paths=existing)

    sample_rows, nested_paired_hash_checks = load_evaluation_rows()
    scored_rows, scorer_calls = score_rows(sample_rows)
    point_estimates = all_estimands(scored_rows)
    if len(point_estimates) != 56:
        raise FormalRunError(
            "ESTIMAND_COUNT_MISMATCH",
            expected=56,
            actual=len(point_estimates),
        )
    replicate_rows, bootstrap_summary = bootstrap(scored_rows)
    tables = nested_tables(scored_rows)
    cases = case_accounting(scored_rows)
    leakage = {
        "assignment_checks": "PASS",
        "group_disjointness": "PASS",
        "scorer_independence": "PASS",
        "threshold_search_performed": False,
        "result_dependent_exclusion": False,
        "stage_labels_used_for_secondary_profile_only": True,
    }
    contract_valid = (
        hash_checks == 60
        and focused_tests == 19
        and scorer_calls == 89
        and len(scored_rows) == 89
        and len(replicate_rows) == REPLICATES
        and all(
            item["valid_replicate_count"] + item["failed_replicate_count"]
            == REPLICATES
            for item in bootstrap_summary.values()
        )
    )
    if not contract_valid:
        raise FormalRunError("FORMAL_RUN_INVALID", reason="contract_accounting")

    payload = {
        "task_id": "finqa-v2-formal-experiment-a-20261010",
        "namespace": "FINQA_V2_FORMAL_RESULTS",
        "generated_at": now_iso(),
        "run_status": "FORMAL_RUN_COMPLETE_AWAITING_LOOP_C_AUDIT",
        "A_RECOMMENDED_CLASS": recommended_class(scored_rows, contract_valid),
        "final_class_status": "DEFERRED_TO_LOOP_D_AFTER_LOOP_C_AUDIT",
        "frozen_research_question": plan["frozen_research_question"],
        "population": {
            "role": "evaluation",
            "samples": 89,
            "report_clusters": 30,
            "by_stage": {
                stage: {
                    "samples": tables["per_stage"][stage]["sample_denominator"],
                    "report_clusters": tables["per_stage"][stage]["cluster_denominator"],
                }
                for stage in STAGES
            },
            "train_samples_not_scored": 81,
            "calibration_samples_not_scored": 45,
        },
        "tables": tables,
        "point_estimates": point_estimates,
        "bootstrap_summary": bootstrap_summary,
        "accounting": {
            "candidate_injections": 216,
            "retained_paired_injections": 215,
            "excluded_before_split": 1,
            "expected_evaluation_records": 89,
            "scored_evaluation_records": 89,
            "missing_retained_records": 0,
            "invalid_retained_records": 0,
            "scorer_failures": 0,
            "unevaluable_evaluation_records": 0,
            "preserved_evaluation_rows": 89,
        },
        "case_accounting": cases,
        "leakage_audit": leakage,
        "bootstrap_contract": {
            "seed": SEED,
            "replicate_count": REPLICATES,
            "cluster_unit": "report_cluster_id",
            "ci_method": "PERCENTILE",
            "percentiles": [2.5, 97.5],
            "rng": "numpy.random.default_rng(20261017)",
            "sampling_order": "overall_30_then_E_10_then_P_10_then_N_10_per_replicate",
            "permutation_test": "NOT_USED",
            "valid_failed_accounting_per_estimand": True,
        },
        "execution": {
            "started_at": started_at,
            "completed_at": now_iso(),
            "frozen_hash_checks": hash_checks,
            "frozen_hash_mismatches": 0,
            "nested_paired_artifact_hash_checks": nested_paired_hash_checks,
            "focused_tests_passed": focused_tests,
            "formal_outputs_before_execution": 0,
            "scorer_calls": scorer_calls,
            "pre_scorer_runner_attempts": 1,
            "pre_scorer_runner_import_failures": 1,
            "non_evaluation_scoring_calls": 0,
            "endpoint_calls": 0,
            "model_calls": 0,
            "training_runs": 0,
            "prm_runs": 0,
            "permutation_runs": 0,
        },
        "evidence_grading": {
            "overall_visibility_detection": "CONFIRMATORY",
            "per_stage_outcome_and_bootstrap": "SECONDARY",
            "adverse_and_null_cases": "NEGATIVE",
        },
        "claim_boundary": {
            "allowed": [
                "Report frozen estimands and intervals exactly as materialized",
                "Use A_RECOMMENDED_CLASS only pending Loop C audit and Loop D decision",
            ],
            "forbidden": [
                "hierarchy_beats_flat",
                "hierarchy_localization",
                "semantic_correctness",
                "harmfulness",
                "natural_failure_localization",
                "automatic_stage_e_transfer",
            ],
        },
    }

    write_jsonl(RESULTS_DIR / "finqa_v2_formal_sample_rows.jsonl", scored_rows)
    write_json(RESULTS_DIR / "finqa_v2_formal_results.json", payload)
    write_jsonl(
        RESULTS_DIR / "finqa_v2_bootstrap_replicates.jsonl",
        replicate_rows,
    )
    report_text = render_report(payload)
    (RESULTS_DIR / "FINQA_V2_FORMAL_RESULT_REPORT.md").write_text(
        report_text + "\n",
        encoding="utf-8",
    )

    execution_log = [
        f"TASK_ID=finqa-v2-formal-experiment-a-20261010",
        f"STARTED_AT={started_at}",
        f"COMMAND={' '.join(sys.argv)}",
        f"FROZEN_HASH_VERIFICATION=PASS checks={hash_checks} mismatches=0",
        f"FOCUSED_PREFLIGHT=PASS passed=19 sha256={focused_log_sha}",
        "FORMAL_OUTPUT_PRECHECK=PASS count=0",
        "EVALUATION_SELECTION=PASS samples=89 clusters=30 stages=E:30,P:30,N:29",
        "SCORER_EXECUTION=PASS calls=89 failures=0 train_calibration_calls=0",
        "ESTIMAND_MATERIALIZATION=PASS estimands=56",
        f"BOOTSTRAP=PASS seed={SEED} replicates={REPLICATES} estimands=56",
        "PERMUTATION_TEST=NOT_USED",
        "ENDPOINT_CALLS=0 MODEL_CALLS=0 TRAINING_RUNS=0",
        "FORMAL_RUN_STATUS=FORMAL_RUN_COMPLETE_AWAITING_LOOP_C_AUDIT",
    ]
    (RESULTS_DIR / "finqa_v2_formal_execution.log").write_text(
        "\n".join(execution_log) + "\n",
        encoding="utf-8",
    )
    environment_lines = [
        f"COMMAND={' '.join([str(Path(sys.executable)), *sys.argv])}",
        f"PYTHONPATH={os.environ.get('PYTHONPATH', '')}",
        f"PYTHON_VERSION={sys.version.replace(os.linesep, ' ')}",
        f"PYTHON_EXECUTABLE={sys.executable}",
        f"PYTHON_IMPLEMENTATION={platform.python_implementation()}",
        f"PLATFORM={platform.platform()}",
        f"NUMPY_VERSION={np.__version__}",
        f"GIT_HEAD={git_head()}",
        "ZONEINFO=Asia/Shanghai",
        f"CAPTURED_AT={now_iso()}",
    ]
    (RESULTS_DIR / "finqa_v2_formal_environment.log").write_text(
        "\n".join(environment_lines) + "\n",
        encoding="utf-8",
    )

    output_names = (
        "finqa_v2_formal_sample_rows.jsonl",
        "finqa_v2_formal_results.json",
        "finqa_v2_bootstrap_replicates.jsonl",
        "FINQA_V2_FORMAL_RESULT_REPORT.md",
        "finqa_v2_focused_preflight.log",
        "finqa_v2_frozen_hash_verification.log",
        "finqa_v2_formal_pre_scorer_attempt_1.log",
        "finqa_v2_formal_execution.log",
        "finqa_v2_formal_environment.log",
    )
    output_hashes = {
        name: {
            "bytes": (RESULTS_DIR / name).stat().st_size,
            "sha256": sha256_file(RESULTS_DIR / name),
        }
        for name in output_names
    }
    receipt = {
        "task_id": "finqa-v2-formal-experiment-a-20261010",
        "namespace": "FINQA_V2_FORMAL_EXECUTION_RECEIPT",
        "status": "FORMAL_RUN_COMPLETE_AWAITING_LOOP_C_FRESH_CONTEXT_AUDIT",
        "created_at": now_iso(),
        "role": "LOOP_A_GB10_FORMAL_EXECUTION",
        "authorization": "USER_AUTHORIZED_AFTER_PREREG_GO_PASS_FINAL",
        "run_status": payload["run_status"],
        "A_RECOMMENDED_CLASS": payload["A_RECOMMENDED_CLASS"],
        "final_class_status": payload["final_class_status"],
        "hash_contract": (
            "SHA-256 of raw file bytes for artifacts; SHA-256 of canonical "
            "compact sorted JSON after removing self_sha256 for this receipt"
        ),
        "frozen_hash_verification": {
            "checks": hash_checks,
            "mismatches": 0,
            "nested_paired_artifact_hash_checks": nested_paired_hash_checks,
            "log": output_hashes["finqa_v2_frozen_hash_verification.log"],
        },
        "focused_preflight": {
            "command": FOCUSED_TEST_COMMAND,
            "passed": 19,
            "failed": 0,
            "exit_code": 0,
            "log": output_hashes["finqa_v2_focused_preflight.log"],
        },
        "formal_output_precheck": {
            "count": 0,
            "paths": [],
            "completed_before_scorer_execution": True,
        },
        "execution_counters": {
            "scorer_calls": 89,
            "pre_scorer_runner_attempts": 1,
            "pre_scorer_runner_import_failures": 1,
            "evaluation_records_scored": 89,
            "evaluation_records_failed": 0,
            "train_scoring_calls": 0,
            "calibration_scoring_calls": 0,
            "endpoint_calls": 0,
            "model_calls": 0,
            "database_calls": 0,
            "training_runs": 0,
            "prm_runs": 0,
            "permutation_runs": 0,
        },
        "population": payload["population"],
        "accounting": payload["accounting"],
        "bootstrap": {
            **payload["bootstrap_contract"],
            "all_estimands_valid_failed_sum_to_replicate_count": True,
        },
        "leakage_audit": leakage,
        "hash_field_guard": {
            "manifest_hash_field": "manifest_artifact_sha256",
            "scorer_hash_field": "scorer_payload_sha256",
            "distinct_field_names": True,
            "rows_with_both_fields": 89,
            "values_equal_for_all_rows": all(
                row["manifest_artifact_sha256"] == row["scorer_payload_sha256"]
                for row in scored_rows
            ),
        },
        "commands": {
            "focused_test": FOCUSED_TEST_COMMAND,
            "formal_execution": "PYTHONPATH=src ./venv/bin/python "
            "research/finqa_v2_20261010/run_finqa_v2_formal_experiment.py",
        },
        "environment": output_hashes["finqa_v2_formal_environment.log"],
        "execution_log": output_hashes["finqa_v2_formal_execution.log"],
        "pre_scorer_attempt_log": output_hashes[
            "finqa_v2_formal_pre_scorer_attempt_1.log"
        ],
        "outputs": {
            name: output_hashes[name]
            for name in output_names
            if name
            in {
                "finqa_v2_formal_sample_rows.jsonl",
                "finqa_v2_formal_results.json",
                "finqa_v2_bootstrap_replicates.jsonl",
                "FINQA_V2_FORMAL_RESULT_REPORT.md",
            }
        },
        "all_output_hashes": output_hashes,
        "runner": {
            "path": str(Path(__file__).resolve()),
            "bytes": Path(__file__).stat().st_size,
            "sha256": sha256_file(Path(__file__).resolve()),
        },
        "immutable_input_hashes": {
            name: sha256_file(TASK_DIR / name)
            for name in (
                "FINQA_V2_FORMAL_EXPERIMENT_TASK_CARD.md",
                "FINQA_V2_ANALYSIS_PLAN.md",
                "finqa_v2_analysis_plan.json",
                "finqa_v2_analysis_preresult_freeze_receipt.json",
                "finqa_v2_frozen_sample_manifest.json",
                "finqa_v2_split_manifest.json",
                "finqa_v2_paired_artifact_manifest.json",
                "finqa_v2_scorer_binding_manifest.json",
                "finqa_v2_preresult_freeze_receipt.json",
            )
        },
        "formal_task_contract": {
            "path": "research/finqa_v2_formal_experiment_loop_a_task_contract.md",
            "bytes": (
                ROOT / "research/finqa_v2_formal_experiment_loop_a_task_contract.md"
            ).stat().st_size,
            "sha256": sha256_file(
                ROOT / "research/finqa_v2_formal_experiment_loop_a_task_contract.md"
            ),
        },
        "success_exit": {
            "all_89_evaluation_pairs_scored": True,
            "frozen_estimands_materialized": len(point_estimates),
            "bootstrap_materialized": len(replicate_rows),
            "null_adverse_cases_preserved": True,
            "outputs_hash_bound_for_loop_c": True,
        },
        "self_sha256": "",
    }
    receipt["self_sha256"] = self_hash(receipt)
    write_json(RESULTS_DIR / "finqa_v2_formal_execution_receipt.json", receipt)

    print(
        json.dumps(
            {
                "status": receipt["status"],
                "A_RECOMMENDED_CLASS": receipt["A_RECOMMENDED_CLASS"],
                "samples": 89,
                "clusters": 30,
                "scorer_calls": 89,
                "bootstrap_replicates": REPLICATES,
                "endpoint_calls": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
