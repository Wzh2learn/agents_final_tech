#!/usr/bin/env python3
"""Materialize the fail-closed packet after the binding-v2 scorer stop."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TASK_DIR = Path(__file__).resolve().parent
RESULTS_DIR = TASK_DIR / "results_binding_v2_rerun"
BINDING_DIR = TASK_DIR / "binding_v2"
TASK_ID = "finqa-v2-minimal-rerun-pending-execution-20261010"
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


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def json_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def self_hash(value: dict[str, Any]) -> str:
    return json_hash({key: item for key, item in value.items() if key != "self_sha256"})


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def git_head() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "UNAVAILABLE"


def estimand_ids() -> list[str]:
    overall = [
        "visibility_count",
        "visibility_rate",
        "detection_count",
        "detection_rate",
        "visibility_detection_2x2.v0_d0_count",
        "visibility_detection_2x2.v0_d0_rate",
        "visibility_detection_2x2.v0_d1_count",
        "visibility_detection_2x2.v0_d1_rate",
        "visibility_detection_2x2.v1_d0_count",
        "visibility_detection_2x2.v1_d0_rate",
        "visibility_detection_2x2.v1_d1_count",
        "visibility_detection_2x2.v1_d1_rate",
        "detection_rate_given_visibility_positive",
        "detection_rate_given_visibility_negative",
        "terminal_outcome_count",
        "terminal_outcome_rate",
        "failure_accounting.missing_count",
        "failure_accounting.invalid_record_count",
        "failure_accounting.scorer_failure_count",
        "failure_accounting.unevaluable_count",
    ]
    stage_ids = [
        "visibility_count",
        "visibility_rate",
        "detection_count",
        "detection_rate",
        "visibility_detection_2x2.v0_d0_count",
        "visibility_detection_2x2.v0_d0_rate",
        "visibility_detection_2x2.v0_d1_count",
        "visibility_detection_2x2.v0_d1_rate",
        "visibility_detection_2x2.v1_d0_count",
        "visibility_detection_2x2.v1_d0_rate",
        "visibility_detection_2x2.v1_d1_count",
        "visibility_detection_2x2.v1_d1_rate",
    ]
    return overall + [
        f"stage.{stage}.{name}" for stage in STAGES for name in stage_ids
    ]


def invalid_tables(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def table(stage: str | None) -> dict[str, Any]:
        scoped = rows if stage is None else [row for row in rows if row["stage"] == stage]
        cells = {
            f"{visibility}{detection}": {"count": None, "rate": None}
            for visibility in (0, 1)
            for detection in (0, 1)
        }
        profile = {
            "sample_denominator": len(scoped),
            "cluster_denominator": len({row["cluster_id"] for row in scoped}),
            "visibility_count": None,
            "visibility_rate": None,
            "detection_count": None,
            "detection_rate": None,
            "visibility_detection_2x2": cells,
        }
        if stage is None:
            profile.update(
                {
                    "detection_rate_given_visibility_positive": None,
                    "detection_rate_given_visibility_negative": None,
                    "terminal_outcome_count": None,
                    "terminal_outcome_rate": None,
                }
            )
        return profile

    return {
        "overall": table(None),
        "per_stage": {stage: table(stage) for stage in STAGES},
    }


def materialize() -> dict[str, Any]:
    if not RESULTS_DIR.is_dir():
        raise RuntimeError("RERUN_NAMESPACE_MISSING")
    required_existing = [
        name
        for name in (
            "finqa_v2_formal_sample_rows.jsonl",
            "finqa_v2_formal_results.json",
            "finqa_v2_bootstrap_replicates.jsonl",
            "FINQA_V2_FORMAL_RESULT_REPORT.md",
        )
        if (RESULTS_DIR / name).exists()
    ]
    if required_existing:
        raise RuntimeError(f"FORMAL_OUTPUT_ALREADY_EXISTS:{required_existing}")
    failure_path = RESULTS_DIR / "finqa_v2_formal_scorer_failures.jsonl"
    failures = read_jsonl(failure_path)
    if len(failures) != 89 or len({row["sample_id"] for row in failures}) != 89:
        raise RuntimeError("SCORER_FAILURE_ACCOUNTING_MISMATCH")
    if {row["error_code"] for row in failures} != {"BINDING_TRACE_MISMATCH"}:
        raise RuntimeError("SCORER_FAILURE_CODE_MISMATCH")

    from research.finqa_v2_20261010.binding_v2.finqa_v2_scorer_runtime_binding_v2 import (
        artifact_hash,
        normalized_payload_from_record,
        raw_payload_from_record,
    )
    from research.finqa_v2_20261010.run_finqa_v2_formal_experiment import (
        load_evaluation_rows,
        verify_frozen_hashes,
    )

    hash_lines, hash_checks = verify_frozen_hashes()
    (RESULTS_DIR / "finqa_v2_frozen_hash_verification.log").write_text(
        "\n".join(hash_lines) + "\n", encoding="utf-8"
    )
    rows, nested_hash_checks = load_evaluation_rows()
    failures_by_id = {row["sample_id"]: row for row in failures}
    mapping_rows = read_jsonl(BINDING_DIR / "finqa_v2_raw_normalized_mapping.jsonl")
    trace_count_by_artifact: dict[str, int] = {}
    for row in mapping_rows:
        trace_count_by_artifact[row["artifact_id"]] = (
            trace_count_by_artifact.get(row["artifact_id"], 0) + 1
        )
    preserved_rows: list[dict[str, Any]] = []
    for row in rows:
        raw = raw_payload_from_record(row["_score_payload"])
        raw_hash = json_hash(raw)
        normalized_hash = artifact_hash(normalized_payload_from_record(raw))
        if raw_hash != row["manifest_artifact_sha256"]:
            raise RuntimeError(f"RAW_HASH_MISMATCH:{row['sample_id']}")
        failure = failures_by_id[row["sample_id"]]
        preserved_rows.append(
            {
                **row,
                "raw_payload_sha256": raw_hash,
                "normalized_payload_sha256": normalized_hash,
                "normalization_version": "finqa_v2_scorer_normalization_20261010_v1",
                "trace_key_count": trace_count_by_artifact[row["artifact_id"]],
                "observation_vector": {field: None for field in SCORER_FIELDS},
                "scorer_payload_sha256": normalized_hash,
                "V": None,
                "D": None,
                "O": None,
                "record_status": "SCORER_FAILED_BINDING_TRACE_MISMATCH",
                "missing": False,
                "invalid_record": False,
                "scorer_failure": True,
                "unevaluable": True,
                "failure_error_code": failure["error_code"],
            }
        )
    if len(preserved_rows) != 89:
        raise RuntimeError("PRESERVED_ROW_ACCOUNTING_MISMATCH")

    ids = estimand_ids()
    if len(ids) != 56:
        raise RuntimeError("ESTIMAND_ID_ACCOUNTING_MISMATCH")
    point_estimates = {name: None for name in ids}
    point_estimates["failure_accounting.missing_count"] = 0
    point_estimates["failure_accounting.invalid_record_count"] = 0
    point_estimates["failure_accounting.scorer_failure_count"] = 89
    point_estimates["failure_accounting.unevaluable_count"] = 89
    failure_ids = {
        "failure_accounting.missing_count",
        "failure_accounting.invalid_record_count",
        "failure_accounting.scorer_failure_count",
        "failure_accounting.unevaluable_count",
    }
    bootstrap_summary = {
        name: {
            "point_estimate": point_estimates[name],
            "point_estimate_status": (
                "ESTIMATED" if name in failure_ids else "NOT_RUN_FORMAL_RUN_INVALID"
            ),
            "interval": "NOT_RUN_FORMAL_RUN_INVALID",
            "interval_label": "NOT_RUN_FORMAL_RUN_INVALID",
            "seed": SEED,
            "planned_replicate_count": REPLICATES,
            "replicate_count": 0,
            "valid_replicate_count": 0,
            "failed_replicate_count": 0,
            "not_attempted_replicate_count": REPLICATES,
            "cluster_unit": "report_cluster_id",
            "ci_method": "PERCENTILE",
            "percentiles": [2.5, 97.5],
        }
        for name in ids
    }
    payload = {
        "task_id": TASK_ID,
        "namespace": "FINQA_V2_BINDING_V2_MINIMAL_RERUN_RESULTS",
        "generated_at": now_iso(),
        "run_status": "FORMAL_RUN_INVALID",
        "A_RECOMMENDED_CLASS": "SECOND_FLOW_INVALID",
        "final_class_status": "DEFERRED_TO_LOOP_C_AUDIT",
        "frozen_research_question": read_json(
            TASK_DIR / "finqa_v2_analysis_plan.json"
        )["frozen_research_question"],
        "binding_v2_contract": {
            "contract_sha256": sha256_file(
                BINDING_DIR / "finqa_v2_artifact_binding_contract_v2.json"
            ),
            "runtime_sha256": sha256_file(
                BINDING_DIR / "finqa_v2_scorer_runtime_binding_v2.py"
            ),
            "mapping_sha256": sha256_file(
                BINDING_DIR / "finqa_v2_raw_normalized_mapping.jsonl"
            ),
            "mapping_rows": 994,
            "normalization_version": "finqa_v2_scorer_normalization_20261010_v1",
            "raw_hash_field": "raw_payload_sha256",
            "normalized_hash_field": "normalized_payload_sha256",
            "op_family_is_raw_operator_identity": False,
            "trace_map_retained": True,
        },
        "population": {
            "role": "evaluation",
            "samples": 89,
            "report_clusters": 30,
            "by_stage": {
                "E": {"samples": 30, "report_clusters": 10},
                "P": {"samples": 30, "report_clusters": 10},
                "N": {"samples": 29, "report_clusters": 10},
            },
            "train_samples_not_scored": 81,
            "calibration_samples_not_scored": 45,
        },
        "tables": invalid_tables(preserved_rows),
        "point_estimates": point_estimates,
        "bootstrap_summary": bootstrap_summary,
        "accounting": {
            "candidate_injections": 216,
            "retained_paired_injections": 215,
            "excluded_before_split": 1,
            "expected_evaluation_records": 89,
            "scorer_calls": 89,
            "scorer_successes": 0,
            "scorer_failures": 89,
            "missing_retained_records": 0,
            "invalid_retained_records": 0,
            "unevaluable_evaluation_records": 89,
            "preserved_evaluation_rows": 89,
        },
        "case_accounting": {
            "status": "NOT_COMPUTABLE_SCORER_FAILED",
            "all_89_evaluation_rows_preserved": True,
        },
        "leakage_audit": {
            "assignment_checks": "PASS",
            "group_disjointness": "PASS",
            "scorer_independence": "PASS",
            "threshold_search_performed": False,
            "result_dependent_exclusion": False,
            "stage_labels_used_for_secondary_profile_only": True,
        },
        "bootstrap_contract": {
            "seed": SEED,
            "planned_replicate_count": REPLICATES,
            "attempted_replicate_count": 0,
            "valid_replicate_count": 0,
            "failed_replicate_count": 0,
            "not_attempted_replicate_count": REPLICATES,
            "cluster_unit": "report_cluster_id",
            "ci_method": "PERCENTILE",
            "percentiles": [2.5, 97.5],
            "status": "NOT_RUN_FORMAL_RUN_INVALID",
            "permutation_test": "NOT_USED",
        },
        "execution": {
            "frozen_hash_checks": hash_checks,
            "frozen_hash_mismatches": 0,
            "nested_paired_artifact_hash_checks": nested_hash_checks,
            "focused_tests_passed": 19,
            "binding_v2_tests_passed": 10,
            "formal_outputs_before_execution": 0,
            "pre_scorer_command_failures": 1,
            "scorer_calls": 89,
            "scorer_successes": 0,
            "scorer_failures": 89,
            "endpoint_calls": 0,
            "model_calls": 0,
            "database_calls": 0,
            "training_runs": 0,
            "prm_runs": 0,
            "permutation_runs": 0,
        },
        "evidence_grading": {
            "binding_trace_failure": "NEGATIVE",
            "scientific_estimands": "NOT_GRADED",
        },
        "claim_boundary": {
            "allowed": [
                "FORMAL_RUN_INVALID",
                "89 attempted, 0 successful, 89 binding trace failures",
                "89 preserved rows with null V/D/O",
            ],
            "forbidden": [
                "visibility_detection_transfer_claim",
                "hierarchy_beats_flat",
                "hierarchy_localization",
                "semantic_correctness",
                "harmfulness",
                "natural_failure_localization",
                "automatic_stage_e_transfer",
            ],
        },
    }
    if len(payload["point_estimates"]) != 56:
        raise RuntimeError("POINT_ESTIMAND_ACCOUNTING_MISMATCH")

    write_jsonl(RESULTS_DIR / "finqa_v2_formal_sample_rows.jsonl", preserved_rows)
    write_json(RESULTS_DIR / "finqa_v2_formal_results.json", payload)
    (RESULTS_DIR / "finqa_v2_bootstrap_replicates.jsonl").write_text(
        "", encoding="utf-8"
    )
    report = f"""# FinQA v2 Binding V2 Minimal Rerun Result Report

- Task ID: `{TASK_ID}`
- Run status: `FORMAL_RUN_INVALID`
- `A_RECOMMENDED_CLASS`: `SECOND_FLOW_INVALID`
- Loop C gate: `SCORER_BINDING_GO = PASS`; this packet stops for fresh independent recomputation.

## Stop Condition

All 89 evaluation records failed closed with `BINDING_TRACE_MISMATCH` before the unchanged scorer returned an observation vector. The frozen contract requires `FORMAL_RUN_INVALID`; estimands and bootstrap resampling were not run.

## Binding V2

- Normalization version: `finqa_v2_scorer_normalization_20261010_v1`.
- Raw-to-normalized trace map: `994` rows and retained.
- `raw_payload_sha256` is the provenance hash.
- `normalized_payload_sha256` is the scorer-runtime authoritative hash.
- `op_family` is not reported as raw operator identity.

## Retained Evaluation Population

| Stage | Samples | Report clusters |
|---|---:|---:|
| E | 30 | 10 |
| P | 30 | 10 |
| N | 29 | 10 |
| **Total** | **89** | **30** |

## Estimands and Bootstrap

- All scientific V/D/O estimands: `NOT_IDENTIFIABLE`.
- Failure-accounting estimands: missing `0`, invalid `0`, scorer failures `89`, unevaluable `89`.
- Bootstrap: planned `10000`, attempted `0`, valid `0`, failed `0`, not attempted `10000`.
- `PERMUTATION_TEST = NOT_USED`.

## Accounting

The exact denominator remains `89`; all 89 rows are preserved with null observation vectors and null V/D/O. No adverse or null case was deleted.

## Claim Boundary

No visibility/detection transfer, semantic-correctness, harmfulness, hierarchy, localization, Stage E transfer or reduced-denominator claim is supported.
"""
    (RESULTS_DIR / "FINQA_V2_FORMAL_RESULT_REPORT.md").write_text(
        report + "\n", encoding="utf-8"
    )
    execution_log = [
        f"TASK_ID={TASK_ID}",
        "BINDING_CONTRACT=binding_v2",
        "LOOP_C_SCORER_BINDING_GO=PASS",
        "FROZEN_HASH_VERIFICATION=PASS checks=60 mismatches=0",
        "FOCUSED_PREFLIGHT=PASS passed=19",
        "BINDING_V2_PREFLIGHT=PASS passed=10",
        "FORMAL_OUTPUT_PRECHECK=PASS count=0",
        "EVALUATION_SELECTION=PASS samples=89 clusters=30",
        "SCORER_EXECUTION=FAIL calls=89 successes=0 failures=89",
        "SCORER_FAILURE_CODE=BINDING_TRACE_MISMATCH",
        "STOP_CONDITION=FORMAL_RUN_INVALID",
        "ESTIMAND_MATERIALIZATION=NOT_RUN",
        "BOOTSTRAP=NOT_RUN planned=10000 attempted=0",
        "PERMUTATION_TEST=NOT_USED",
        "ENDPOINT_CALLS=0 MODEL_CALLS=0 TRAINING_RUNS=0 PRM_RUNS=0",
        "A_RECOMMENDED_CLASS=SECOND_FLOW_INVALID",
    ]
    (RESULTS_DIR / "finqa_v2_formal_execution.log").write_text(
        "\n".join(execution_log) + "\n", encoding="utf-8"
    )
    environment_log = [
        "COMMAND=PYTHONPATH=src ./venv/bin/python "
        "research/finqa_v2_20261010/materialize_finqa_v2_binding_v2_rerun_invalid.py",
        "PYTHONPATH=src",
        f"PYTHON_VERSION={sys.version.replace(chr(10), ' ')}",
        f"PYTHON_EXECUTABLE={sys.executable}",
        f"PYTHON_IMPLEMENTATION={platform.python_implementation()}",
        f"PLATFORM={platform.platform()}",
        f"GIT_HEAD={git_head()}",
        f"CAPTURED_AT={now_iso()}",
    ]
    (RESULTS_DIR / "finqa_v2_formal_environment.log").write_text(
        "\n".join(environment_log) + "\n", encoding="utf-8"
    )

    output_names = (
        "finqa_v2_formal_sample_rows.jsonl",
        "finqa_v2_formal_results.json",
        "finqa_v2_bootstrap_replicates.jsonl",
        "FINQA_V2_FORMAL_RESULT_REPORT.md",
        "finqa_v2_formal_scorer_failures.jsonl",
        "finqa_v2_focused_preflight.log",
        "finqa_v2_binding_v2_preflight.log",
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
        "task_id": TASK_ID,
        "namespace": "FINQA_V2_BINDING_V2_MINIMAL_RERUN_EXECUTION_RECEIPT",
        "status": "FORMAL_RUN_INVALID",
        "created_at": now_iso(),
        "role": "MINIMAL_FORMAL_RERUN_BINDING_V2",
        "authorization": {
            "loop_c_audit": "docs/experiments/2026-10-10_loop_c_finqa_v2_binding_v2_audit.md",
            "scorer_binding_go": "PASS",
            "verdict": "PASS",
            "scope": "formal scorer -> frozen estimands -> frozen bootstrap only",
        },
        "A_RECOMMENDED_CLASS": "SECOND_FLOW_INVALID",
        "final_class_status": "DEFERRED_TO_LOOP_C_AUDIT",
        "hash_contract": (
            "SHA-256 of raw file bytes for artifacts; SHA-256 of canonical "
            "compact sorted JSON after removing self_sha256 for this receipt"
        ),
        "binding_v2": payload["binding_v2_contract"],
        "frozen_hash_verification": {
            "checks": hash_checks,
            "mismatches": 0,
            "nested_paired_artifact_hash_checks": nested_hash_checks,
            "log": output_hashes["finqa_v2_frozen_hash_verification.log"],
        },
        "focused_preflight": {
            "command": "PYTHONPATH=src ./venv/bin/python -m pytest "
            "tests/test_finqa_numeric_token_canonicalization_v2.py "
            "tests/test_finqa_evidence_argument_resolver_v2.py "
            "tests/test_finqa_independent_observation_scorer_v2.py "
            "tests/test_finqa_v2_execution_freeze.py -q",
            "passed": 19,
            "failed": 0,
            "exit_code": 0,
            "log": output_hashes["finqa_v2_focused_preflight.log"],
        },
        "binding_v2_preflight": {
            "command": "PYTHONPATH=src ./venv/bin/python -m pytest "
            "tests/test_finqa_v2_scorer_runtime_binding_v2.py -q",
            "passed": 10,
            "failed": 0,
            "exit_code": 0,
            "log": output_hashes["finqa_v2_binding_v2_preflight.log"],
        },
        "formal_output_precheck": {
            "count": 0,
            "paths": [],
            "completed_before_scorer_execution": True,
        },
        "execution_counters": {
            "pre_scorer_command_failures": 1,
            "scorer_calls": 89,
            "scorer_successes": 0,
            "scorer_failures": 89,
            "binding_trace_mismatch_failures": 89,
            "evaluation_records_preserved": 89,
            "estimand_attempts": 0,
            "bootstrap_attempts": 0,
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
        "bootstrap": payload["bootstrap_contract"],
        "hash_field_guard": {
            "raw_hash_field": "raw_payload_sha256",
            "normalized_hash_field": "normalized_payload_sha256",
            "scorer_hash_field": "scorer_payload_sha256",
            "rows_with_raw_and_normalized_hashes": 89,
            "values_are_not_required_to_equal_across_hash_domains": True,
            "op_family_is_raw_operator_identity": False,
        },
        "commands": {
            "focused_test": "PYTHONPATH=src ./venv/bin/python -m pytest "
            "tests/test_finqa_numeric_token_canonicalization_v2.py "
            "tests/test_finqa_evidence_argument_resolver_v2.py "
            "tests/test_finqa_independent_observation_scorer_v2.py "
            "tests/test_finqa_v2_execution_freeze.py -q",
            "binding_v2_test": "PYTHONPATH=src ./venv/bin/python -m pytest "
            "tests/test_finqa_v2_scorer_runtime_binding_v2.py -q",
            "formal_execution": "PYTHONPATH=src ./venv/bin/python "
            "research/finqa_v2_20261010/run_finqa_v2_binding_v2_rerun.py",
            "invalid_materialization": "PYTHONPATH=src ./venv/bin/python "
            "research/finqa_v2_20261010/materialize_finqa_v2_binding_v2_rerun_invalid.py",
        },
        "environment": output_hashes["finqa_v2_formal_environment.log"],
        "execution_log": output_hashes["finqa_v2_formal_execution.log"],
        "outputs": {
            name: output_hashes[name]
            for name in (
                "finqa_v2_formal_sample_rows.jsonl",
                "finqa_v2_formal_results.json",
                "finqa_v2_bootstrap_replicates.jsonl",
                "FINQA_V2_FORMAL_RESULT_REPORT.md",
            )
        },
        "all_output_hashes": output_hashes,
        "runner": {
            "path": str((TASK_DIR / "run_finqa_v2_binding_v2_rerun.py").resolve()),
            "sha256": sha256_file(TASK_DIR / "run_finqa_v2_binding_v2_rerun.py"),
        },
        "invalid_materializer": {
            "path": str(Path(__file__).resolve()),
            "sha256": sha256_file(Path(__file__).resolve()),
        },
        "immutable_input_hashes": {
            "binding_v2/FINQA_V2_MINIMAL_RERUN_TASK_CARD.md": sha256_file(
                BINDING_DIR / "FINQA_V2_MINIMAL_RERUN_TASK_CARD.md"
            ),
            "binding_v2/finqa_v2_artifact_binding_contract_v2.json": sha256_file(
                BINDING_DIR / "finqa_v2_artifact_binding_contract_v2.json"
            ),
            "binding_v2/finqa_v2_raw_normalized_mapping.jsonl": sha256_file(
                BINDING_DIR / "finqa_v2_raw_normalized_mapping.jsonl"
            ),
            "binding_v2/finqa_v2_scorer_runtime_binding_v2.py": sha256_file(
                BINDING_DIR / "finqa_v2_scorer_runtime_binding_v2.py"
            ),
            "loop_c_binding_v2_audit": sha256_file(
                ROOT / "docs/experiments/2026-10-10_loop_c_finqa_v2_binding_v2_audit.md"
            ),
        },
        "stop_conditions": {
            "OLD_RUN_HASH_MISMATCH": False,
            "LOOP_C_SCORER_BINDING_GO_NOT_PASS": False,
            "PRIOR_RERUN_OUTPUT_EXISTS": False,
            "FOCUSED_PREFLIGHT_FAILURE": False,
            "MISSING_OR_INVALID_RETAINED_RECORD": False,
            "SCORER_FAILURE": True,
            "SCORER_FAILURE_CODE": "BINDING_TRACE_MISMATCH",
            "ESTIMAND_COMPUTATION_NOT_REACHED": True,
            "BOOTSTRAP_NOT_REACHED": True,
        },
        "success_exit": {
            "all_89_evaluation_pairs_scored": False,
            "frozen_estimands_materialized": False,
            "bootstrap_materialized": False,
            "null_adverse_cases_preserved_as_null_failure_rows": True,
            "outputs_hash_bound_for_loop_c": True,
            "scientific_class_accepted": False,
        },
        "post_run_requirement": (
            "Loop C must independently recompute scorer rows, V/D/O, all frozen "
            "estimands and bootstrap intervals before scientific acceptance."
        ),
        "self_sha256": "",
    }
    receipt["self_sha256"] = self_hash(receipt)
    write_json(RESULTS_DIR / "finqa_v2_formal_execution_receipt.json", receipt)
    return receipt


if __name__ == "__main__":
    result = materialize()
    print(
        json.dumps(
            {
                "status": result["status"],
                "A_RECOMMENDED_CLASS": result["A_RECOMMENDED_CLASS"],
                "scorer_calls": 89,
                "scorer_failures": 89,
                "preserved_rows": 89,
                "bootstrap_attempts": 0,
                "scientific_class_accepted": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
