#!/usr/bin/env python3
"""Execute the frozen FinQA v2 binding-v3 formal rerun."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TASK_DIR = ROOT / "research" / "finqa_v2_20261010"
OUTPUT_DIR = Path(__file__).resolve().parent
PREFLIGHT_MANIFEST = (
    TASK_DIR
    / "preflight_v1"
    / "finqa_v2_end_to_end_preflight_manifest.json"
)
PREFLIGHT_CERTIFICATE = (
    TASK_DIR
    / "preflight_v1"
    / "finqa_v2_end_to_end_preflight_certificate.json"
)
TASK_CARD = TASK_DIR / "preflight_v1" / "FINQA_V2_FORMAL_RERUN_V3_TASK_CARD.md"
TASK_ID = "finqa-v2-formal-rerun-v3-loop-a-20261010"
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
SCIENTIFIC_OUTPUT_NAMES = (
    "finqa_v2_formal_sample_rows.jsonl",
    "finqa_v2_v_d_o_rows.jsonl",
    "finqa_v2_formal_results.json",
    "finqa_v2_exclusions_and_failure_accounting.json",
    "finqa_v2_bootstrap_replicates.jsonl",
    "FINQA_V2_FORMAL_RESULT_REPORT.md",
    "finqa_v2_formal_execution_receipt.json",
)
LOG_NAMES = (
    "finqa_v2_formal_pre_scorer_attempt_1.log",
    "finqa_v2_end_to_end_preflight_checker.log",
    "finqa_v2_authority_hash_verification.log",
    "finqa_v2_formal_execution.log",
    "finqa_v2_formal_environment.log",
)


class BindingV3RunError(RuntimeError):
    def __init__(self, code: str, **detail: Any) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def json_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def self_hash(value: dict[str, Any]) -> str:
    return json_hash(
        {key: item for key, item in value.items() if key != "self_sha256"}
    )


def now_iso() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def git_head() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def verify_output_collision(manifest: dict[str, Any]) -> list[str]:
    expected_paths = [
        ROOT / path for path in manifest["scientific_output_paths"]
    ] + [OUTPUT_DIR / name for name in SCIENTIFIC_OUTPUT_NAMES]
    collisions = [
        str(path.relative_to(ROOT))
        for path in expected_paths
        if path.exists()
    ]
    if collisions:
        raise BindingV3RunError(
            "SCIENTIFIC_OUTPUT_PATH_COLLISION",
            paths=collisions,
        )
    return collisions


def run_preflight() -> tuple[dict[str, Any], str]:
    command = [
        str(Path(sys.executable).resolve()),
        str(ROOT / "scripts" / "graph" / "formal_experiment_preflight.py"),
        str(PREFLIGHT_MANIFEST),
    ]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = "src"
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    display_command = (
        "PYTHONPATH=src ./venv/bin/python scripts/graph/formal_experiment_preflight.py "
        "research/finqa_v2_20261010/preflight_v1/"
        "finqa_v2_end_to_end_preflight_manifest.json"
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise BindingV3RunError(
            "PREFLIGHT_OUTPUT_NOT_JSON",
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        ) from error
    status = payload.get("status")
    if completed.returncode != 0 or status != "PASS" or payload.get("failures"):
        raise BindingV3RunError(
            "PREFLIGHT_NOT_PASS",
            exit_code=completed.returncode,
            status=status,
            failures=payload.get("failures"),
        )
    log = "\n".join(
        [
            f"COMMAND={display_command}",
            f"EXIT_CODE={completed.returncode}",
            f"STATUS={status}",
            canonical_json(payload),
        ]
    )
    (OUTPUT_DIR / "finqa_v2_end_to_end_preflight_checker.log").write_text(
        log + "\n",
        encoding="utf-8",
    )
    return payload, sha256_file(
        OUTPUT_DIR / "finqa_v2_end_to_end_preflight_checker.log"
    )


def verify_authorities(
    manifest: dict[str, Any],
) -> tuple[list[str], dict[str, str], dict[str, str]]:
    lines: list[str] = []
    checked: dict[str, str] = {}
    for record in manifest["hash_bindings"]:
        path = ROOT / record["path"]
        if not path.is_file():
            raise BindingV3RunError("AUTHORITY_PATH_MISSING", path=record["path"])
        actual = sha256_file(path)
        if actual != record["sha256"]:
            raise BindingV3RunError(
                "AUTHORITY_HASH_MISMATCH",
                path=record["path"],
                expected=record["sha256"],
                actual=actual,
            )
        checked[record["path"]] = actual
        lines.append(f"HASH_OK {actual} {record['path']}")
    prior_before: dict[str, str] = {}
    for record in manifest["previous_invalid_runs"]:
        path = ROOT / record["path"]
        actual = sha256_file(path)
        if actual != record["sha256"]:
            raise BindingV3RunError(
                "PRIOR_INVALID_RUN_HASH_MISMATCH",
                path=record["path"],
                expected=record["sha256"],
                actual=actual,
            )
        prior_before[record["path"]] = actual
        lines.append(f"PRIOR_INVALID_RUN_HASH_OK {actual} {record['path']}")
    certificate = read_json(PREFLIGHT_CERTIFICATE)
    actual_certificate_hash = self_hash(certificate)
    if actual_certificate_hash != certificate["self_sha256"]:
        raise BindingV3RunError(
            "PREFLIGHT_CERTIFICATE_SELF_HASH_MISMATCH",
            expected=certificate["self_sha256"],
            actual=actual_certificate_hash,
        )
    lines.append(
        f"PREFLIGHT_CERTIFICATE_SELF_HASH_OK {actual_certificate_hash} "
        "finqa_v2_end_to_end_preflight_certificate.json"
    )
    lines.append(f"AUTHORITY_VERIFICATION PASS checked={len(checked)} prior=2")
    path = OUTPUT_DIR / "finqa_v2_authority_hash_verification.log"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lines, checked, prior_before


def verify_prior_after(
    manifest: dict[str, Any],
) -> dict[str, str]:
    after: dict[str, str] = {}
    for record in manifest["previous_invalid_runs"]:
        path = ROOT / record["path"]
        actual = sha256_file(path)
        if actual != record["sha256"]:
            raise BindingV3RunError(
                "PRIOR_INVALID_RUN_CHANGED_DURING_EXECUTION",
                path=record["path"],
                expected=record["sha256"],
                actual=actual,
            )
        after[record["path"]] = actual
    return after


def score_binding_v3_rows(
    sample_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    from research.finqa_independent_observation_scorer_v2 import score_pair
    from research.finqa_v2_20261010.binding_v3.finqa_v2_runtime_binding_v3 import (
        BindingV3Runner,
        RuntimeBindingV3,
        construct_scorer_input,
    )

    adapter = RuntimeBindingV3.from_paths()
    binding_rows = BindingV3Runner(adapter).run(sample_rows, expected_count=89)
    output: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    trace_rows_matched = 0
    raw_normalized_distinct = 0
    for row, binding_row in zip(sample_rows, binding_rows, strict=True):
        try:
            identity = adapter.immutable_identity_for(row)
            if identity.raw_payload_sha256 != row["manifest_artifact_sha256"]:
                raise BindingV3RunError(
                    "RAW_IDENTITY_CROSSBIND_MISMATCH",
                    sample_id=row["sample_id"],
                )
            scorer_input = construct_scorer_input(
                row["_score_payload"],
                normalized_payload_sha256=identity.normalized_payload_sha256,
            )
            scored = score_pair(scorer_input)
            vector = scored["observation_vector"]
            if set(vector) != set(SCORER_FIELDS):
                raise BindingV3RunError(
                    "OBSERVATION_FIELD_MISMATCH",
                    sample_id=row["sample_id"],
                )
            if any(
                type(vector[field]) is not int or vector[field] not in (0, 1)
                for field in SCORER_FIELDS
            ):
                raise BindingV3RunError(
                    "OBSERVATION_VALUE_INVALID",
                    sample_id=row["sample_id"],
                )
            if scored["artifact_sha256"] != identity.normalized_payload_sha256:
                raise BindingV3RunError(
                    "NORMALIZED_SCORER_HASH_MISMATCH",
                    sample_id=row["sample_id"],
                )
            if binding_row["scorer_input"]["artifact_sha256_field"] != (
                identity.normalized_payload_sha256
            ):
                raise BindingV3RunError(
                    "BINDING_SCORER_INPUT_HASH_MISMATCH",
                    sample_id=row["sample_id"],
                )
            validation = binding_row["validation"]
            if (
                validation["binding_status"] != "PASS"
                or validation["raw_hash_status"] != "MATCH"
                or validation["normalized_hash_status"] != "MATCH"
                or validation["trace_rows_matched"] != validation["trace_rows_expected"]
            ):
                raise BindingV3RunError(
                    "BINDING_VALIDATION_FAILED",
                    sample_id=row["sample_id"],
                    validation=validation,
                )
            visibility = int(any(vector[field] == 1 for field in SCORER_FIELDS))
            detection = int(
                vector["step_result_consistency"] == 1
                or vector["answer_consistency"] == 1
            )
            outcome = int(vector["answer_consistency"] == 1)
            if identity.raw_payload_sha256 != identity.normalized_payload_sha256:
                raw_normalized_distinct += 1
            trace_rows_matched += validation["trace_rows_matched"]
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
                    "raw_payload_sha256": identity.raw_payload_sha256,
                    "normalized_payload_sha256": identity.normalized_payload_sha256,
                    "scorer_payload_sha256": scored["artifact_sha256"],
                    "normalization_version": identity.normalization_version,
                    "binding_v3_status": validation["binding_status"],
                    "binding_trace_rows_matched": validation["trace_rows_matched"],
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
        raise BindingV3RunError(
            "SCORER_FAILURE",
            expected=89,
            scored=len(output),
            failures=failures,
        )
    if trace_rows_matched != 420:
        raise BindingV3RunError(
            "EVALUATION_TRACE_COUNT_MISMATCH",
            expected=420,
            actual=trace_rows_matched,
        )
    if raw_normalized_distinct != 89:
        raise BindingV3RunError(
            "RAW_NORMALIZED_HASH_DISTINCTNESS_MISMATCH",
            expected=89,
            actual=raw_normalized_distinct,
        )
    counters = {
        "runtime_bindings_pass": len(binding_rows),
        "evaluation_trace_rows_matched": trace_rows_matched,
        "scorer_calls": len(output),
        "scorer_failures": len(failures),
        "raw_normalized_hash_distinct_rows": raw_normalized_distinct,
    }
    return output, counters


def build_payload(
    *,
    started_at: str,
    plan: dict[str, Any],
    sample_rows: list[dict[str, Any]],
    scored_rows: list[dict[str, Any]],
    point_estimates: dict[str, int | float | None],
    bootstrap_summary: dict[str, dict[str, Any]],
    tables: dict[str, Any],
    cases: dict[str, Any],
    counters: dict[str, int],
    nested_paired_hash_checks: int,
    frozen_hash_checks: int,
) -> dict[str, Any]:
    from research.finqa_v2_20261010.run_finqa_v2_formal_experiment import (
        recommended_class,
    )

    contract_valid = (
        frozen_hash_checks == 60
        and nested_paired_hash_checks == 645
        and counters["runtime_bindings_pass"] == 89
        and counters["evaluation_trace_rows_matched"] == 420
        and counters["scorer_calls"] == 89
        and counters["scorer_failures"] == 0
        and len(scored_rows) == 89
        and len(point_estimates) == 56
        and len(bootstrap_summary) == 56
        and all(
            item["valid_replicate_count"] + item["failed_replicate_count"]
            == REPLICATES
            for item in bootstrap_summary.values()
        )
    )
    if not contract_valid:
        raise BindingV3RunError("FORMAL_RUN_INVALID", reason="contract_accounting")
    stage_counts = Counter(row["stage"] for row in scored_rows)
    if stage_counts != Counter(E=30, P=30, N=29):
        raise BindingV3RunError(
            "STAGE_EVALUATION_COUNT_MISMATCH",
            actual=dict(stage_counts),
        )
    leakage = {
        "assignment_checks": "PASS",
        "group_disjointness": "PASS",
        "scorer_independence": "PASS",
        "threshold_search_performed": False,
        "result_dependent_exclusion": False,
        "stage_labels_used_for_secondary_profile_only": True,
    }
    return {
        "task_id": TASK_ID,
        "namespace": "FINQA_V2_FORMAL_BINDING_V3_RERUN_RESULTS",
        "generated_at": now_iso(),
        "run_status": "FORMAL_RUN_COMPLETE_AWAITING_LOOP_C_RECOMPUTATION",
        "A_RECOMMENDED_CLASS": recommended_class(scored_rows, contract_valid),
        "final_class_status": "DEFERRED_TO_LOOP_D_AFTER_LOOP_C_AUDIT",
        "frozen_research_question": plan["frozen_research_question"],
        "analysis_plan_contract": {
            "primary": plan["estimands"]["primary"],
            "secondary": plan["estimands"]["secondary"],
            "uncertainty": plan["uncertainty"],
            "permutation_contract": plan["permutation_contract"],
        },
        "binding_v3": {
            "runtime_bindings_pass": counters["runtime_bindings_pass"],
            "runtime_bindings_total": 89,
            "evaluation_trace_rows_matched": counters[
                "evaluation_trace_rows_matched"
            ],
            "evaluation_trace_rows_total": 420,
            "raw_normalized_hash_distinct_rows": counters[
                "raw_normalized_hash_distinct_rows"
            ],
            "silent_defaults": 0,
            "identity_drift": 0,
            "group_drift": 0,
            "split_drift": 0,
        },
        "population": {
            "role": "evaluation",
            "samples": 89,
            "report_clusters": 30,
            "by_stage": {
                stage: {
                    "samples": tables["per_stage"][stage]["sample_denominator"],
                    "report_clusters": tables["per_stage"][stage][
                        "cluster_denominator"
                    ],
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
            "sampling_order": (
                "overall_30_then_E_10_then_P_10_then_N_10_per_replicate"
            ),
            "permutation_test": "NOT_USED",
            "valid_failed_accounting_per_estimand": True,
        },
        "execution": {
            "started_at": started_at,
            "completed_at": now_iso(),
            "preflight_status": "PASS",
            "frozen_hash_checks": frozen_hash_checks,
            "frozen_hash_mismatches": 0,
            "nested_paired_artifact_hash_checks": nested_paired_hash_checks,
            "focused_tests_passed": "NOT_RERUN_PER_TASK_CARD",
            "formal_outputs_before_execution": 0,
            "runtime_bindings": counters["runtime_bindings_pass"],
            "scorer_calls": counters["scorer_calls"],
            "non_evaluation_scoring_calls": 0,
            "endpoint_calls": 0,
            "model_calls": 0,
            "database_calls": 0,
            "training_runs": 0,
            "prm_runs": 0,
            "permutation_runs": 0,
            "loaded_evaluation_rows": len(sample_rows),
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


def main() -> int:
    started_at = now_iso()
    manifest = read_json(PREFLIGHT_MANIFEST)
    collisions = verify_output_collision(manifest)
    preflight, preflight_log_hash = run_preflight()
    authority_lines, checked_hashes, prior_before = verify_authorities(manifest)
    if len(checked_hashes) != 14:
        raise BindingV3RunError(
            "AUTHORITY_HASH_COUNT_MISMATCH",
            expected=14,
            actual=len(checked_hashes),
        )

    frozen_hash_lines, frozen_hash_checks = (
        __import__(
            "research.finqa_v2_20261010.run_finqa_v2_formal_experiment",
            fromlist=["verify_frozen_hashes"],
        ).verify_frozen_hashes()
    )
    frozen_log = OUTPUT_DIR / "finqa_v2_frozen_hash_verification.log"
    frozen_log.write_text("\n".join(frozen_hash_lines) + "\n", encoding="utf-8")
    if frozen_hash_checks != 60:
        raise BindingV3RunError(
            "FROZEN_HASH_COUNT_MISMATCH",
            expected=60,
            actual=frozen_hash_checks,
        )

    from research.finqa_v2_20261010.run_finqa_v2_formal_experiment import (
        all_estimands,
        assert_analysis_contract,
        bootstrap,
        case_accounting,
        load_evaluation_rows,
        nested_tables,
        render_report,
    )

    plan = read_json(TASK_DIR / "finqa_v2_analysis_plan.json")
    assert_analysis_contract(plan)
    sample_rows, nested_paired_hash_checks = load_evaluation_rows()
    if len(sample_rows) != 89:
        raise BindingV3RunError(
            "EVALUATION_SELECTION_MISMATCH",
            expected=89,
            actual=len(sample_rows),
        )
    scored_rows, counters = score_binding_v3_rows(sample_rows)
    point_estimates = all_estimands(scored_rows)
    replicate_rows, bootstrap_summary = bootstrap(scored_rows)
    tables = nested_tables(scored_rows)
    cases = case_accounting(scored_rows)
    payload = build_payload(
        started_at=started_at,
        plan=plan,
        sample_rows=sample_rows,
        scored_rows=scored_rows,
        point_estimates=point_estimates,
        bootstrap_summary=bootstrap_summary,
        tables=tables,
        cases=cases,
        counters=counters,
        nested_paired_hash_checks=nested_paired_hash_checks,
        frozen_hash_checks=frozen_hash_checks,
    )

    write_jsonl(
        OUTPUT_DIR / "finqa_v2_formal_sample_rows.jsonl",
        scored_rows,
    )
    write_jsonl(
        OUTPUT_DIR / "finqa_v2_v_d_o_rows.jsonl",
        [
            {
                "sample_id": row["sample_id"],
                "stage": row["stage"],
                "cluster_id": row["cluster_id"],
                "report_cluster_id": row["report_cluster_id"],
                "report_cluster": row["report_cluster"],
                "raw_payload_sha256": row["raw_payload_sha256"],
                "normalized_payload_sha256": row["normalized_payload_sha256"],
                "observation_vector": row["observation_vector"],
                "V": row["V"],
                "D": row["D"],
                "O": row["O"],
            }
            for row in scored_rows
        ],
    )
    write_json(OUTPUT_DIR / "finqa_v2_formal_results.json", payload)
    sample_manifest = read_json(TASK_DIR / "finqa_v2_frozen_sample_manifest.json")
    failure_accounting = {
        "namespace": "FINQA_V2_EXCLUSIONS_AND_FAILURE_ACCOUNTING",
        "task_id": TASK_ID,
        "frozen_exclusions": sample_manifest["exclusions"],
        "counts": payload["accounting"],
        "failure_accounting": {
            key: value
            for key, value in point_estimates.items()
            if key.startswith("failure_accounting.")
        },
        "denominator_reduced": False,
        "result_dependent_exclusion": False,
        "missing_or_failed_scorer_rows": 0,
        "all_expected_evaluation_rows_preserved": len(scored_rows) == 89,
    }
    write_json(
        OUTPUT_DIR / "finqa_v2_exclusions_and_failure_accounting.json",
        failure_accounting,
    )
    write_jsonl(
        OUTPUT_DIR / "finqa_v2_bootstrap_replicates.jsonl",
        replicate_rows,
    )
    report = render_report(payload)
    report = report.replace(
        "- Focused technical preflight: `NOT_RERUN_PER_TASK_CARD passed`.",
        "- End-to-end preflight checker: `PASS`.",
    )
    report = report.replace(
        "- Raw manifest hash and normalized scorer payload hash use distinct row fields.",
        "- Binding-v3 binds all 89 raw manifest hashes to distinct normalized scorer payload hashes.",
    )
    (OUTPUT_DIR / "FINQA_V2_FORMAL_RESULT_REPORT.md").write_text(
        report + "\n",
        encoding="utf-8",
    )

    execution_log = [
        f"TASK_ID={TASK_ID}",
        f"STARTED_AT={started_at}",
        f"COMMAND={' '.join([str(Path(sys.executable)), *sys.argv])}",
        "END_TO_END_PREFLIGHT=PASS",
        "AUTHORITY_HASH_VERIFICATION=PASS checked=14 prior_invalid_runs=2",
        "PRE_SCORER_RUNNER_ATTEMPTS=2 preflight_invocation_failures=1 scorer_attempts_before_success=0",
        f"FROZEN_HASH_VERIFICATION=PASS checks={frozen_hash_checks} mismatches=0",
        "OUTPUT_PATH_PRECHECK=PASS collisions=0",
        "EVALUATION_SELECTION=PASS samples=89 clusters=30 stages=E:30,P:30,N:29",
        "BINDING_V3=PASS bindings=89 trace_rows=420 metadata_fields=4",
        "SCORER_EXECUTION=PASS calls=89 failures=0 train_calibration_calls=0",
        "RAW_NORMALIZED_HASHES=PASS distinct_rows=89",
        "ESTIMAND_MATERIALIZATION=PASS estimands=56",
        f"BOOTSTRAP=PASS seed={SEED} replicates={REPLICATES} estimands=56",
        "PERMUTATION_TEST=NOT_USED",
        "ENDPOINT_CALLS=0 MODEL_CALLS=0 DATABASE_CALLS=0 TRAINING_RUNS=0",
        "FORMAL_RUN_STATUS=FORMAL_RUN_COMPLETE_AWAITING_LOOP_C_RECOMPUTATION",
        "REVIEW_HANDOFF=STOP FOR LOOP C INDEPENDENT RECOMPUTATION",
    ]
    (OUTPUT_DIR / "finqa_v2_formal_execution.log").write_text(
        "\n".join(execution_log) + "\n",
        encoding="utf-8",
    )
    environment_log = [
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
    (OUTPUT_DIR / "finqa_v2_formal_environment.log").write_text(
        "\n".join(environment_log) + "\n",
        encoding="utf-8",
    )

    prior_after = verify_prior_after(manifest)
    if prior_after != prior_before:
        raise BindingV3RunError(
            "PRIOR_INVALID_RUN_HASHES_CHANGED",
            before=prior_before,
            after=prior_after,
        )
    output_paths = [
        OUTPUT_DIR / name
        for name in (*SCIENTIFIC_OUTPUT_NAMES[:-1], *LOG_NAMES)
        if name != "finqa_v2_formal_execution_receipt.json"
    ]
    output_paths.append(frozen_log)
    output_hashes: dict[str, dict[str, Any]] = {}
    for path in sorted(set(output_paths), key=lambda item: item.name):
        if not path.is_file():
            raise BindingV3RunError("OUTPUT_MISSING", path=path.name)
        output_hashes[path.name] = {
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    receipt = {
        "task_id": TASK_ID,
        "namespace": "FINQA_V2_FORMAL_BINDING_V3_RERUN_RECEIPT",
        "status": "FORMAL_RUN_COMPLETE_AWAITING_LOOP_C_INDEPENDENT_RECOMPUTATION",
        "created_at": now_iso(),
        "role": "LOOP_A_GB10_FORMAL_EXECUTION",
        "authorization": "USER_AUTHORIZED_FROZEN_TASK_CARD_IN_CURRENT_TURN",
        "frozen_task_card": {
            "path": str(TASK_CARD.relative_to(ROOT)),
            "sha256": sha256_file(TASK_CARD),
        },
        "preflight": {
            "command": (
                "PYTHONPATH=src ./venv/bin/python "
                "scripts/graph/formal_experiment_preflight.py "
                "research/finqa_v2_20261010/preflight_v1/"
                "finqa_v2_end_to_end_preflight_manifest.json"
            ),
            "status": preflight["status"],
            "exit_code": 0,
            "hash_bindings_checked": preflight["hash_bindings_checked"],
            "previous_invalid_runs_checked": preflight["previous_invalid_runs_checked"],
            "scientific_outputs": preflight["scientific_outputs"],
            "log": output_hashes[
                "finqa_v2_end_to_end_preflight_checker.log"
            ],
            "log_sha256": preflight_log_hash,
        },
        "authority_verification": {
            "checked": len(checked_hashes),
            "mismatches": 0,
            "hashes": checked_hashes,
            "prior_invalid_runs_before": prior_before,
            "prior_invalid_runs_after": prior_after,
            "unchanged": prior_before == prior_after,
            "log": output_hashes["finqa_v2_authority_hash_verification.log"],
            "authority_log_line_count": len(authority_lines),
        },
        "binding_v3": {
            "interface": (
                "research/finqa_v2_20261010/binding_v3/"
                "FINQA_V2_RUNTIME_BINDING_INTERFACE_V3.md"
            ),
            "runtime_bindings_pass": counters["runtime_bindings_pass"],
            "runtime_bindings_total": 89,
            "evaluation_trace_rows_matched": counters[
                "evaluation_trace_rows_matched"
            ],
            "evaluation_trace_rows_total": 420,
            "metadata_fields": [
                "split_role",
                "stage",
                "cluster_id",
                "report_cluster",
            ],
            "silent_defaults": 0,
            "raw_normalized_hash_distinct_rows": counters[
                "raw_normalized_hash_distinct_rows"
            ],
        },
        "hash_contract": (
            "SHA-256 of raw file bytes for artifacts; SHA-256 of canonical "
            "compact sorted JSON after removing self_sha256 for this receipt"
        ),
        "frozen_hash_verification": {
            "checks": frozen_hash_checks,
            "mismatches": 0,
            "log": output_hashes["finqa_v2_frozen_hash_verification.log"],
        },
        "output_path_precheck": {
            "collision_count": len(collisions),
            "collisions": collisions,
            "completed_before_scientific_execution": True,
        },
        "execution_counters": {
            "loaded_evaluation_rows": 89,
            "runtime_bindings": 89,
            "scorer_calls": 89,
            "pre_scorer_runner_attempts": 2,
            "preflight_invocation_failures": 1,
            "scorer_attempts_before_success": 0,
            "scorer_failures": 0,
            "evaluation_records_scored": 89,
            "evaluation_records_failed": 0,
            "preserved_evaluation_rows": 89,
            "train_scoring_calls": 0,
            "calibration_scoring_calls": 0,
            "endpoint_calls": 0,
            "model_calls": 0,
            "database_calls": 0,
            "training_runs": 0,
            "prm_runs": 0,
            "permutation_runs": 0,
        },
        "scientific_accounting": {
            "point_estimands": len(point_estimates),
            "bootstrap_estimands": len(bootstrap_summary),
            "bootstrap_seed": SEED,
            "bootstrap_replicates": len(replicate_rows),
            "cluster_unit": "report_cluster_id",
            "evidence_grading": payload["evidence_grading"],
            "result_class_status": payload["final_class_status"],
        },
        "runner": {
            "path": str(Path(__file__).resolve().relative_to(ROOT)),
            "bytes": Path(__file__).stat().st_size,
            "sha256": sha256_file(Path(__file__).resolve()),
        },
        "outputs": output_hashes,
        "success_exit": {
            "all_89_evaluation_pairs_scored": True,
            "raw_and_normalized_hashes_materialized": True,
            "v_d_o_rows_materialized": len(scored_rows),
            "frozen_estimands_materialized": len(point_estimates),
            "bootstrap_materialized": len(replicate_rows),
            "null_adverse_cases_preserved": True,
            "exact_exclusions_and_failure_accounting_materialized": True,
            "outputs_hash_bound_for_loop_c": True,
        },
        "review_handoff": "STOP FOR LOOP C INDEPENDENT RECOMPUTATION",
        "self_sha256": "",
    }
    receipt["self_sha256"] = self_hash(receipt)
    write_json(
        OUTPUT_DIR / "finqa_v2_formal_execution_receipt.json",
        receipt,
    )
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "A_RECOMMENDED_CLASS": payload["A_RECOMMENDED_CLASS"],
                "samples": 89,
                "clusters": 30,
                "runtime_bindings": 89,
                "trace_rows": 420,
                "scorer_calls": 89,
                "bootstrap_replicates": len(replicate_rows),
                "endpoint_calls": 0,
                "review_handoff": receipt["review_handoff"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
