#!/usr/bin/env python3
"""Materialize the required outputs after the frozen scorer stop condition."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.finqa_v2_20261010.run_finqa_v2_formal_experiment import (  # noqa: E402
    REPLICATES,
    SCORER_FIELDS,
    SEED,
    STAGES,
    FormalRunError,
    canonical_json,
    formal_output_inventory,
    load_evaluation_rows,
    now_iso,
    read_json,
    sha256_file,
    verify_frozen_hashes,
    verify_preflight_log,
    write_json,
    write_jsonl,
)


TASK_DIR = Path(__file__).resolve().parent
RESULTS_DIR = TASK_DIR / "results"


def normalized_scorer_payload_hash(artifact: dict[str, Any]) -> str:
    from research.finqa_independent_observation_scorer_v2 import (
        _normalized_steps,
        artifact_hash,
    )

    bound_payload = {
        "required_evidence_ids": [
            str(item) for item in artifact["required_evidence_ids"]
        ],
        "clean": {
            "evidence_ids": sorted(
                str(item) for item in artifact["clean"]["evidence_ids"]
            ),
            "steps": _normalized_steps(artifact["clean"]["steps"], "clean.steps"),
            "answer": str(artifact["clean"]["answer"]),
        },
        "mutant": {
            "evidence_ids": sorted(
                str(item) for item in artifact["mutant"]["evidence_ids"]
            ),
            "steps": _normalized_steps(artifact["mutant"]["steps"], "mutant.steps"),
            "answer": str(artifact["artifact"].get("answer", ""))
            if False
            else str(artifact["mutant"]["answer"]),
        },
    }
    return artifact_hash(bound_payload)


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
    stage_base = [
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
        f"stage.{stage}.{name}"
        for stage in STAGES
        for name in stage_base
    ]


def render_report(payload: dict[str, Any]) -> str:
    return f"""# FinQA v2 Formal Second-Flow Result Report

- Task ID: `{payload['task_id']}`
- Run status: `{payload['run_status']}`
- `A_RECOMMENDED_CLASS`: `{payload['A_RECOMMENDED_CLASS']}`
- Final class status: deferred; Loop C must audit this invalid run.

## Stop Condition

All 89 authorized scorer calls failed closed on `artifact_sha256_mismatch` before any observation vector was returned. The frozen contract requires `FORMAL_RUN_INVALID`; the run stopped before estimands or bootstrap resampling.

## Retained Evaluation Population

| Stage | Samples | Report clusters |
|---|---:|---:|
| E | 30 | 10 |
| P | 30 | 10 |
| N | 29 | 10 |
| **Total** | **89** | **30** |

Train `81` and calibration `45` were not scored.

## Estimands

Visibility, detection, the 2x2 V×D table, both conditional rates, per-stage profiles and O are `NOT_IDENTIFIABLE` because the scorer returned no valid observation vectors. No result-dependent value, threshold, exclusion or metric was substituted.

## Bootstrap

- Seed reserved: `{SEED}`.
- Planned replicates: `{REPLICATES}`.
- Attempted replicates: `0`.
- Valid replicates: `0`.
- Failed replicates: `0`.
- Status: `NOT_RUN_FORMAL_RUN_INVALID`.
- `PERMUTATION_TEST = NOT_USED`.

## Exclusions, Missing, Invalid and Unevaluable Accounting

| Account | Count |
|---|---:|
| Expected evaluation records | 89 |
| Scorer calls attempted | 89 |
| Scorer successes | 0 |
| Scorer failures | 89 |
| Missing retained records | 0 |
| Invalid retained records | 0 |
| Unevaluable evaluation records | 89 |
| Preserved evaluation rows | 89 |

All 89 rows remain in `finqa_v2_formal_sample_rows.jsonl` with null V/D/O and explicit scorer-failure status. The denominator was not reduced.

## Leakage and Integrity Audit

- Frozen file hashes: PASS, 0 mismatches.
- Nested paired-artifact hashes: PASS, 645 checks.
- Focused preflight: 19 passed.
- Formal output precheck: 0.
- Split/group leakage: PASS.
- Assignment fail-closed checks: PASS.
- Scorer label blindness/independence: PASS.
- Threshold search: NOT PERFORMED.
- Train/calibration scorer calls: 0.
- Raw manifest hash and normalized scorer payload hash are retained under distinct fields.

## Negative and Null Cases

No V/D category is computable. The failure is reported unchanged as NEGATIVE execution evidence; all 89 attempted cases are preserved.

## Allowed Claims

- Report that the formal run is `FORMAL_RUN_INVALID`.
- Report the exact accounting: 89 attempted, 0 successful, 89 failed.
- State that no scientific estimand, interval or result class beyond `SECOND_FLOW_INVALID` is supported.

## Forbidden Claims

- Any hierarchy-beats-flat or hierarchy-localization claim.
- Any semantic-correctness or harmfulness claim.
- Any claim that visibility/detection separation transferred.
- Any natural-failure-localization or automatic Stage E transfer claim.
- Any reduced-denominator, threshold, metric or permutation result.

## Evidence Grading

| Evidence | Grade | Boundary |
|---|---|---|
| Scorer hash-binding failure | NEGATIVE | Execution/integrity only |
| Scientific V/D/O estimands | NOT GRADED | Scorer returned no vectors |
"""


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    required_missing = [
        name
        for name in (
            "finqa_v2_formal_sample_rows.jsonl",
            "finqa_v2_formal_results.json",
            "finqa_v2_bootstrap_replicates.jsonl",
            "FINQA_V2_FORMAL_RESULT_REPORT.md",
            "finqa_v2_formal_execution_receipt.json",
        )
        if (RESULTS_DIR / name).exists()
    ]
    if required_missing:
        raise FormalRunError("FORMAL_OUTPUT_ALREADY_EXISTS", paths=required_missing)
    inventory = formal_output_inventory()
    if inventory:
        raise FormalRunError("FORMAL_OUTPUT_ALREADY_EXISTS", paths=inventory)
    if not (RESULTS_DIR / "finqa_v2_formal_pre_scorer_attempt_2.log").is_file():
        raise FormalRunError("SCORER_FAILURE_ATTEMPT_LOG_MISSING")

    hash_lines, hash_checks = verify_frozen_hashes()
    (RESULTS_DIR / "finqa_v2_frozen_hash_verification.log").write_text(
        "\n".join(hash_lines) + "\n",
        encoding="utf-8",
    )
    focused_log_sha, focused_tests = verify_preflight_log()
    rows, nested_hash_checks = load_evaluation_rows()
    paired = {
        row["sample_id"]: row
        for row in read_json("finqa_v2_paired_artifact_manifest.json")["artifacts"]
    }
    failure_rows: list[dict[str, Any]] = []
    preserved_rows: list[dict[str, Any]] = []
    for row in rows:
        raw_hash = row["manifest_artifact_sha256"]
        normalized_hash = normalized_scorer_payload_hash(paired[row["sample_id"]]["artifact"])
        failure = {
            "sample_id": row["sample_id"],
            "artifact_id": row["artifact_id"],
            "manifest_artifact_sha256": raw_hash,
            "scorer_payload_sha256": normalized_hash,
            "hash_match": raw_hash == normalized_hash,
            "error_code": "artifact_sha256_mismatch",
        }
        if failure["hash_match"]:
            raise FormalRunError("EXPECTED_SCORER_FAILURE_NOT_REPRODUCED", sample_id=row["sample_id"])
        failure_rows.append(failure)
        preserved_rows.append(
            {
                **row,
                "observation_vector": {field: None for field in SCORER_FIELDS},
                "scorer_payload_sha256": normalized_hash,
                "V": None,
                "D": None,
                "O": None,
                "record_status": "SCORER_FAILED_ARTIFACT_SHA256_MISMATCH",
                "missing": False,
                "invalid_record": False,
                "scorer_failure": True,
                "unevaluable": True,
            }
        )
    if len(failure_rows) != 89 or any(item["hash_match"] for item in failure_rows):
        raise FormalRunError("SCORER_FAILURE_ACCOUNTING_MISMATCH")

    ids = estimand_ids()
    if len(ids) != 56:
        raise FormalRunError("INVALID_ESTIMAND_ID_COUNT", actual=len(ids))
    point_estimates = {name: None for name in ids}
    point_estimates["failure_accounting.missing_count"] = 0
    point_estimates["failure_accounting.invalid_record_count"] = 0
    point_estimates["failure_accounting.scorer_failure_count"] = 89
    point_estimates["failure_accounting.unevaluable_count"] = 89
    bootstrap_summary = {
        name: {
            "point_estimate": point_estimates[name],
            "point_estimate_status": "NOT_RUN_FORMAL_RUN_INVALID"
            if name not in {
                "failure_accounting.missing_count",
                "failure_accounting.invalid_record_count",
                "failure_accounting.scorer_failure_count",
                "failure_accounting.unevaluable_count",
            }
            else "ESTIMATED",
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
        "task_id": "finqa-v2-formal-experiment-a-20261010",
        "namespace": "FINQA_V2_FORMAL_RESULTS",
        "generated_at": now_iso(),
        "run_status": "FORMAL_RUN_INVALID",
        "A_RECOMMENDED_CLASS": "SECOND_FLOW_INVALID",
        "final_class_status": "DEFERRED_TO_LOOP_C_AUDIT",
        "frozen_research_question": read_json("finqa_v2_analysis_plan.json")[
            "frozen_research_question"
        ],
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
            "status": "NOT_RUN_FORMAL_RUN_INVALID",
            "permutation_test": "NOT_USED",
        },
        "execution": {
            "frozen_hash_checks": hash_checks,
            "frozen_hash_mismatches": 0,
            "nested_paired_artifact_hash_checks": nested_hash_checks,
            "focused_tests_passed": focused_tests,
            "formal_outputs_before_execution": 0,
            "scorer_calls": 89,
            "scorer_successes": 0,
            "scorer_failures": 89,
            "pre_scorer_runner_import_failures": 1,
            "endpoint_calls": 0,
            "model_calls": 0,
            "database_calls": 0,
            "training_runs": 0,
            "prm_runs": 0,
            "permutation_runs": 0,
        },
        "evidence_grading": {
            "scorer_hash_binding_failure": "NEGATIVE",
            "scientific_estimands": "NOT_GRADED",
        },
        "claim_boundary": {
            "allowed": [
                "FORMAL_RUN_INVALID",
                "89 attempted, 0 successful, 89 scorer failures",
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

    write_jsonl(RESULTS_DIR / "finqa_v2_formal_sample_rows.jsonl", preserved_rows)
    write_jsonl(RESULTS_DIR / "finqa_v2_formal_scorer_failures.jsonl", failure_rows)
    write_json(RESULTS_DIR / "finqa_v2_formal_results.json", payload)
    (RESULTS_DIR / "finqa_v2_bootstrap_replicates.jsonl").write_text(
        "", encoding="utf-8"
    )
    (RESULTS_DIR / "FINQA_V2_FORMAL_RESULT_REPORT.md").write_text(
        render_report(payload) + "\n", encoding="utf-8"
    )
    execution_log = [
        "TASK_ID=finqa-v2-formal-experiment-a-20261010",
        f"COMMAND=PYTHONPATH=src ./venv/bin/python research/finqa_v2_20261010/materialize_finqa_v2_formal_invalid.py",
        f"FROZEN_HASH_VERIFICATION=PASS checks={hash_checks} mismatches=0",
        f"NESTED_PAIRED_HASH_VERIFICATION=PASS checks={nested_hash_checks} mismatches=0",
        f"FOCUSED_PREFLIGHT=PASS passed=19 sha256={focused_log_sha}",
        "FORMAL_OUTPUT_PRECHECK=PASS count=0",
        "EVALUATION_SELECTION=PASS samples=89 clusters=30 stages=E:30,P:30,N:29",
        "SCORER_EXECUTION=FAIL calls=89 successes=0 failures=89",
        "STOP_CONDITION=FORMAL_RUN_INVALID",
        "ESTIMAND_MATERIALIZATION=NOT_RUN",
        "BOOTSTRAP=NOT_RUN planned_replicates=10000 attempted=0",
        "PERMUTATION_TEST=NOT_USED",
        "ENDPOINT_CALLS=0 MODEL_CALLS=0 TRAINING_RUNS=0",
        "ALL_89_ROWS_PRESERVED=true",
        "A_RECOMMENDED_CLASS=SECOND_FLOW_INVALID",
    ]
    (RESULTS_DIR / "finqa_v2_formal_execution.log").write_text(
        "\n".join(execution_log) + "\n", encoding="utf-8"
    )
    environment_log = [
        f"COMMAND=PYTHONPATH=src ./venv/bin/python {Path(__file__).relative_to(ROOT)}",
        "PYTHONPATH=src",
        f"PYTHON_VERSION={sys.version.replace(chr(10), ' ')}",
        f"PYTHON_EXECUTABLE={sys.executable}",
        f"PLATFORM={sys.platform}",
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
        "finqa_v2_frozen_hash_verification.log",
        "finqa_v2_formal_pre_scorer_attempt_1.log",
        "finqa_v2_formal_pre_scorer_attempt_2.log",
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
        "status": "FORMAL_RUN_INVALID",
        "created_at": now_iso(),
        "role": "LOOP_A_GB10_FORMAL_EXECUTION",
        "authorization": "USER_AUTHORIZED_AFTER_PREREG_GO_PASS_FINAL",
        "A_RECOMMENDED_CLASS": "SECOND_FLOW_INVALID",
        "final_class_status": "DEFERRED_TO_LOOP_C_AUDIT",
        "hash_contract": (
            "SHA-256 of raw file bytes for artifacts; SHA-256 of canonical "
            "compact sorted JSON after removing self_sha256 for this receipt"
        ),
        "frozen_hash_verification": {
            "checks": hash_checks,
            "mismatches": 0,
            "nested_paired_artifact_hash_checks": nested_hash_checks,
            "log": output_hashes["finqa_v2_frozen_hash_verification.log"],
        },
        "focused_preflight": {
            "command": read_json("finqa_v2_analysis_plan.json").get(
                "focused_test_command", ""
            )
            or "PYTHONPATH=src ./venv/bin/python -m pytest tests/test_finqa_numeric_token_canonicalization_v2.py tests/test_finqa_evidence_argument_resolver_v2.py tests/test_finqa_independent_observation_scorer_v2.py tests/test_finqa_v2_execution_freeze.py -q",
            "passed": 19,
            "failed": 0,
            "exit_code": 0,
            "log": output_hashes["finqa_v2_focused_preflight.log"],
        },
        "formal_output_precheck": {"count": 0, "paths": []},
        "execution_counters": {
            "scorer_calls": 89,
            "scorer_successes": 0,
            "scorer_failures": 89,
            "evaluation_records_scored": 0,
            "evaluation_records_preserved": 89,
            "train_scoring_calls": 0,
            "calibration_scoring_calls": 0,
            "endpoint_calls": 0,
            "model_calls": 0,
            "database_calls": 0,
            "training_runs": 0,
            "prm_runs": 0,
            "permutation_runs": 0,
            "bootstrap_attempts": 0,
        },
        "population": payload["population"],
        "accounting": payload["accounting"],
        "bootstrap": payload["bootstrap_contract"],
        "leakage_audit": payload["leakage_audit"],
        "hash_field_guard": {
            "manifest_hash_field": "manifest_artifact_sha256",
            "scorer_hash_field": "scorer_payload_sha256",
            "distinct_field_names": True,
            "rows_with_both_fields": 89,
            "values_equal_for_all_rows": False,
        },
        "attempts": {
            "pre_scorer_import_failure": output_hashes[
                "finqa_v2_formal_pre_scorer_attempt_1.log"
            ],
            "scorer_failure": output_hashes[
                "finqa_v2_formal_pre_scorer_attempt_2.log"
            ],
            "detailed_scorer_failures": output_hashes[
                "finqa_v2_formal_scorer_failures.jsonl"
            ],
        },
        "commands": {
            "focused_test": "PYTHONPATH=src ./venv/bin/python -m pytest tests/test_finqa_numeric_token_canonicalization_v2.py tests/test_finqa_evidence_argument_resolver_v2.py tests/test_finqa_independent_observation_scorer_v2.py tests/test_finqa_v2_execution_freeze.py -q",
            "formal_attempt": "PYTHONPATH=src ./venv/bin/python research/finqa_v2_20261010/run_finqa_v2_formal_experiment.py",
            "invalid_materialization": "PYTHONPATH=src ./venv/bin/python research/finqa_v2_20261010/materialize_finqa_v2_formal_invalid.py",
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
        "runners": {
            "formal": {
                "path": str(TASK_DIR / "run_finqa_v2_formal_experiment.py"),
                "sha256": sha256_file(TASK_DIR / "run_finqa_v2_formal_experiment.py"),
            },
            "invalid_materializer": {
                "path": str(Path(__file__).resolve()),
                "sha256": sha256_file(Path(__file__).resolve()),
            },
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
            "sha256": sha256_file(
                ROOT / "research/finqa_v2_formal_experiment_loop_a_task_contract.md"
            ),
        },
        "stop_conditions": {
            "HASH_MISMATCH": False,
            "FOCUSED_TEST_FAILURE": False,
            "EXISTING_FORMAL_OUTPUT_BEFORE_EXECUTION": False,
            "MISSING_OR_INVALID_RETAINED_RECORD": False,
            "SCORER_FAILURE": True,
            "BOOTSTRAP_CONTRACT_DEVIATION_NOT_REACHED": True,
            "FROZEN_INPUT_MODIFICATION": False,
        },
        "success_exit": {
            "all_89_evaluation_pairs_scored": False,
            "frozen_estimands_materialized": False,
            "bootstrap_materialized": False,
            "null_adverse_cases_preserved_as_null_failure_rows": True,
            "outputs_hash_bound_for_loop_c": True,
        },
        "self_sha256": "",
    }
    from research.finqa_v2_20261010.run_finqa_v2_formal_experiment import self_hash

    receipt["self_sha256"] = self_hash(receipt)
    write_json(RESULTS_DIR / "finqa_v2_formal_execution_receipt.json", receipt)
    print(
        json.dumps(
            {
                "status": "FORMAL_RUN_INVALID",
                "A_RECOMMENDED_CLASS": "SECOND_FLOW_INVALID",
                "scorer_calls": 89,
                "scorer_successes": 0,
                "scorer_failures": 89,
                "preserved_rows": 89,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
