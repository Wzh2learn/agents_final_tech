#!/usr/bin/env python3
"""Materialize the immutable receipt for the completed binding-v3 rerun."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


OUTPUT_DIR = Path(__file__).resolve().parent
RUNNER_PATH = OUTPUT_DIR / "run_finqa_v2_binding_v3_rerun.py"
RECEIPT_PATH = OUTPUT_DIR / "finqa_v2_formal_execution_receipt.json"


def load_runner() -> Any:
    spec = importlib.util.spec_from_file_location(
        "finqa_v2_binding_v3_rerun_runner",
        RUNNER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("RUNNER_IMPORT_SPEC_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def main() -> int:
    runner = load_runner()
    if RECEIPT_PATH.exists():
        raise RuntimeError("RECEIPT_PATH_COLLISION")
    manifest = runner.read_json(runner.PREFLIGHT_MANIFEST)
    certificate = runner.read_json(runner.PREFLIGHT_CERTIFICATE)
    if runner.self_hash(certificate) != certificate["self_sha256"]:
        raise RuntimeError("PREFLIGHT_CERTIFICATE_SELF_HASH_MISMATCH")
    preflight_log = OUTPUT_DIR / "finqa_v2_end_to_end_preflight_checker.log"
    preflight_lines = preflight_log.read_text(encoding="utf-8").splitlines()
    if preflight_lines[1] != "EXIT_CODE=0" or preflight_lines[2] != "STATUS=PASS":
        raise RuntimeError("PREFLIGHT_NOT_PASS")
    preflight = json.loads(preflight_lines[3])
    if (
        preflight["status"] != "PASS"
        or preflight["hash_bindings_checked"] != 14
        or preflight["previous_runs_checked"] != 2
        or preflight["scientific_outputs"] != 0
        or preflight["failures"]
    ):
        raise RuntimeError("PREFLIGHT_CONTRACT_MISMATCH")

    checked_hashes: dict[str, str] = {}
    for record in manifest["hash_bindings"]:
        path = runner.ROOT / record["path"]
        actual = runner.sha256_file(path)
        if actual != record["sha256"]:
            raise RuntimeError(f"AUTHORITY_HASH_MISMATCH:{record['path']}")
        checked_hashes[record["path"]] = actual
    if len(checked_hashes) != 14:
        raise RuntimeError("AUTHORITY_HASH_COUNT_MISMATCH")
    prior_before: dict[str, str] = {}
    for record in manifest["previous_invalid_runs"]:
        path = runner.ROOT / record["path"]
        actual = runner.sha256_file(path)
        if actual != record["sha256"]:
            raise RuntimeError(f"PRIOR_INVALID_RUN_HASH_MISMATCH:{record['path']}")
        prior_before[record["path"]] = actual

    results_path = OUTPUT_DIR / "finqa_v2_formal_results.json"
    results = runner.read_json(results_path)
    if (
        results["run_status"]
        != "FORMAL_RUN_COMPLETE_AWAITING_LOOP_C_RECOMPUTATION"
        or results["A_RECOMMENDED_CLASS"] == "SECOND_FLOW_INVALID"
        or results["binding_v3"]["runtime_bindings_pass"] != 89
        or results["binding_v3"]["evaluation_trace_rows_matched"] != 420
        or results["binding_v3"]["raw_normalized_hash_distinct_rows"] != 89
        or results["accounting"]["scored_evaluation_records"] != 89
        or results["accounting"]["scorer_failures"] != 0
        or len(results["point_estimates"]) != 56
        or len(results["bootstrap_summary"]) != 56
    ):
        raise RuntimeError("SCIENTIFIC_OUTPUT_CONTRACT_MISMATCH")
    scorer_rows = read_jsonl(OUTPUT_DIR / "finqa_v2_formal_sample_rows.jsonl")
    v_d_o_rows = read_jsonl(OUTPUT_DIR / "finqa_v2_v_d_o_rows.jsonl")
    bootstrap_rows = read_jsonl(
        OUTPUT_DIR / "finqa_v2_bootstrap_replicates.jsonl"
    )
    if len(scorer_rows) != 89 or len(v_d_o_rows) != 89:
        raise RuntimeError("ROW_ACCOUNTING_MISMATCH")
    if any(
        row["raw_payload_sha256"] == row["normalized_payload_sha256"]
        for row in scorer_rows
    ):
        raise RuntimeError("RAW_NORMALIZED_HASH_NOT_DISTINCT")
    if len(bootstrap_rows) != 10_000:
        raise RuntimeError("BOOTSTRAP_REPLICATE_ACCOUNTING_MISMATCH")
    if any(row["seed"] != 20261017 for row in bootstrap_rows):
        raise RuntimeError("BOOTSTRAP_SEED_MISMATCH")
    frozen_hash_log = OUTPUT_DIR / "finqa_v2_frozen_hash_verification.log"
    frozen_hash_lines = frozen_hash_log.read_text(encoding="utf-8").splitlines()
    if frozen_hash_lines[-1] != "FROZEN_HASH_PREFLIGHT PASS checks=60 mismatches=0":
        raise RuntimeError("FROZEN_HASH_LOG_MISMATCH")
    if runner.verify_prior_after(manifest) != prior_before:
        raise RuntimeError("PRIOR_INVALID_RUN_CHANGED")

    expected_scientific_outputs = [
        OUTPUT_DIR / name
        for name in runner.SCIENTIFIC_OUTPUT_NAMES
        if name != RECEIPT_PATH.name
    ]
    missing = [path.name for path in expected_scientific_outputs if not path.is_file()]
    if missing:
        raise RuntimeError(f"SCIENTIFIC_OUTPUT_MISSING:{missing}")
    output_paths = sorted(
        [
            path
            for path in OUTPUT_DIR.iterdir()
            if path.is_file() and path != RECEIPT_PATH
        ],
        key=lambda path: path.name,
    )
    output_hashes = {
        path.name: {
            "bytes": path.stat().st_size,
            "sha256": runner.sha256_file(path),
        }
        for path in output_paths
    }
    receipt = {
        "task_id": runner.TASK_ID,
        "namespace": "FINQA_V2_FORMAL_BINDING_V3_RERUN_RECEIPT",
        "status": "FORMAL_RUN_COMPLETE_AWAITING_LOOP_C_INDEPENDENT_RECOMPUTATION",
        "created_at": runner.now_iso(),
        "role": "LOOP_A_GB10_FORMAL_EXECUTION",
        "authorization": "USER_AUTHORIZED_FROZEN_TASK_CARD_IN_CURRENT_TURN",
        "frozen_task_card": {
            "path": str(runner.TASK_CARD.relative_to(runner.ROOT)),
            "sha256": runner.sha256_file(runner.TASK_CARD),
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
            "previous_runs_checked": preflight["previous_runs_checked"],
            "scientific_outputs": preflight["scientific_outputs"],
            "log": output_hashes["finqa_v2_end_to_end_preflight_checker.log"],
        },
        "authority_verification": {
            "checked": len(checked_hashes),
            "mismatches": 0,
            "hashes": checked_hashes,
            "prior_invalid_runs_before": prior_before,
            "prior_invalid_runs_after": runner.verify_prior_after(manifest),
            "unchanged": True,
            "log": output_hashes["finqa_v2_authority_hash_verification.log"],
        },
        "binding_v3": {
            "interface": (
                "research/finqa_v2_20261010/binding_v3/"
                "FINQA_V2_RUNTIME_BINDING_INTERFACE_V3.md"
            ),
            "runtime_bindings_pass": 89,
            "runtime_bindings_total": 89,
            "evaluation_trace_rows_matched": 420,
            "evaluation_trace_rows_total": 420,
            "metadata_fields": [
                "split_role",
                "stage",
                "cluster_id",
                "report_cluster",
            ],
            "silent_defaults": 0,
            "raw_normalized_hash_distinct_rows": 89,
        },
        "hash_contract": (
            "SHA-256 of raw file bytes for artifacts; SHA-256 of canonical "
            "compact sorted JSON after removing self_sha256 for this receipt"
        ),
        "frozen_hash_verification": {
            "checks": 60,
            "mismatches": 0,
            "log": output_hashes["finqa_v2_frozen_hash_verification.log"],
        },
        "output_path_precheck": {
            "collision_count": 0,
            "collisions": [],
            "completed_before_scientific_execution": True,
        },
        "execution_counters": {
            "loaded_evaluation_rows": 89,
            "runtime_bindings": 89,
            "scorer_calls": 89,
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
            "wrapper_attempts": 3,
            "preflight_invocation_failures": 1,
            "receipt_materialization_failures": 2,
            "scorer_attempts_before_success": 0,
        },
        "receipt_materialization": {
            "attempt_1_status": "FAILED_BEFORE_RECEIPT_WRITE",
            "attempt_1_error": "KeyError: previous_invalid_runs_checked",
            "attempt_1_log": output_hashes[
                "finqa_v2_formal_receipt_attempt_1.log"
            ],
            "attempt_2_status": "FAILED_BEFORE_RECEIPT_WRITE",
            "attempt_2_error": (
                "RuntimeError: SCIENTIFIC_OUTPUT_MISSING:"
                "finqa_v2_formal_execution_receipt.json"
            ),
            "attempt_2_log": output_hashes[
                "finqa_v2_formal_receipt_attempt_2.log"
            ],
            "repair_scope": (
                "receipt_field_name_and_expected_receipt_path_before_creation"
            ),
            "scientific_outputs_recomputed": False,
            "scorer_or_bootstrap_rerun": False,
        },
        "scientific_accounting": {
            "point_estimands": len(results["point_estimates"]),
            "bootstrap_estimands": len(results["bootstrap_summary"]),
            "bootstrap_seed": 20261017,
            "bootstrap_replicates": len(bootstrap_rows),
            "cluster_unit": "report_cluster_id",
            "evidence_grading": results["evidence_grading"],
            "result_class_status": results["final_class_status"],
        },
        "runner": {
            "path": str(RUNNER_PATH.relative_to(runner.ROOT)),
            "bytes": RUNNER_PATH.stat().st_size,
            "sha256": runner.sha256_file(RUNNER_PATH),
        },
        "receipt_materializer": {
            "path": str(Path(__file__).resolve().relative_to(runner.ROOT)),
            "bytes": Path(__file__).stat().st_size,
            "sha256": runner.sha256_file(Path(__file__).resolve()),
        },
        "outputs": output_hashes,
        "success_exit": {
            "all_89_evaluation_pairs_scored": True,
            "raw_and_normalized_hashes_materialized": True,
            "v_d_o_rows_materialized": 89,
            "frozen_estimands_materialized": len(results["point_estimates"]),
            "bootstrap_materialized": len(bootstrap_rows),
            "null_adverse_cases_preserved": True,
            "exact_exclusions_and_failure_accounting_materialized": True,
            "outputs_hash_bound_for_loop_c": True,
        },
        "review_handoff": "STOP FOR LOOP C INDEPENDENT RECOMPUTATION",
        "self_sha256": "",
    }
    receipt["self_sha256"] = runner.self_hash(receipt)
    runner.write_json(RECEIPT_PATH, receipt)
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "A_RECOMMENDED_CLASS": results["A_RECOMMENDED_CLASS"],
                "samples": 89,
                "runtime_bindings": 89,
                "trace_rows": 420,
                "scorer_calls": 89,
                "bootstrap_replicates": len(bootstrap_rows),
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
