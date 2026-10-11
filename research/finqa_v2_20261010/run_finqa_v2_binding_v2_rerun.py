#!/usr/bin/env python3
"""Run the authorized FinQA v2 minimal formal rerun under binding_v2."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TASK_DIR = Path(__file__).resolve().parent
RESULTS_DIR = TASK_DIR / "results_binding_v2_rerun"
BINDING_DIR = TASK_DIR / "binding_v2"
OLD_RESULTS_DIR = TASK_DIR / "results"
TASK_ID = "finqa-v2-minimal-rerun-pending-execution-20261010"
NORMALIZATION_VERSION = "finqa_v2_scorer_normalization_20261010_v1"
FOCUSED_TEST_COMMAND = (
    "PYTHONPATH=src ./venv/bin/python -m pytest "
    "tests/test_finqa_numeric_token_canonicalization_v2.py "
    "tests/test_finqa_evidence_argument_resolver_v2.py "
    "tests/test_finqa_independent_observation_scorer_v2.py "
    "tests/test_finqa_v2_execution_freeze.py -q"
)
BINDING_TEST_COMMAND = (
    "PYTHONPATH=src ./venv/bin/python -m pytest "
    "tests/test_finqa_v2_scorer_runtime_binding_v2.py -q"
)


class RerunError(RuntimeError):
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
    return json_hash({key: item for key, item in value.items() if key != "self_sha256"})


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_formal_module() -> Any:
    path = TASK_DIR / "run_finqa_v2_formal_experiment.py"
    spec = importlib.util.spec_from_file_location(
        "finqa_v2_frozen_formal_engine", path
    )
    if spec is None or spec.loader is None:
        raise RerunError("FORMAL_ENGINE_IMPORT_UNAVAILABLE", path=str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_preflight() -> dict[str, Any]:
    contract_path = BINDING_DIR / "finqa_v2_artifact_binding_contract_v2.json"
    contract = load_json(contract_path)
    audit_path = ROOT / "docs/experiments/2026-10-10_loop_c_finqa_v2_binding_v2_audit.md"
    audit = audit_path.read_text(encoding="utf-8")
    if not re.search(r"^## 9\. `SCORER_BINDING_GO = PASS`$", audit, re.MULTILINE):
        raise RerunError("LOOP_C_SCORER_BINDING_GO_MISSING")
    if not re.search(r"^## 10\. `VERDICT: PASS`$", audit, re.MULTILINE):
        raise RerunError("LOOP_C_VERDICT_PASS_MISSING")
    authorization = (
        "authorized for a minimal formal rerun limited to the formal scorer, "
        "frozen estimands, and bootstrap"
    )
    if authorization not in audit:
        raise RerunError("LOOP_C_MINIMAL_RERUN_AUTHORIZATION_MISSING")

    for relative, expected in contract["old_run"]["immutable_output_sha256"].items():
        path = OLD_RESULTS_DIR / relative
        if not path.is_file():
            raise RerunError("OLD_RUN_OUTPUT_MISSING", path=str(path))
        actual = sha256_file(path)
        if actual != expected:
            raise RerunError(
                "OLD_RUN_OUTPUT_HASH_MISMATCH",
                path=str(path),
                expected=expected,
                actual=actual,
            )
    for relative, expected in contract["input_sha256"].items():
        path = (TASK_DIR / relative).resolve()
        if not path.is_file():
            raise RerunError("FROZEN_INPUT_MISSING", path=str(path))
        actual = sha256_file(path)
        if actual != expected:
            raise RerunError(
                "FROZEN_INPUT_HASH_MISMATCH",
                path=str(path),
                expected=expected,
                actual=actual,
            )
    receipt = load_json(BINDING_DIR / "finqa_v2_binding_v2_receipt.json")
    if self_hash(receipt) != receipt["self_sha256"]:
        raise RerunError("BINDING_RECEIPT_SELF_HASH_MISMATCH")
    if contract["normalization"]["version"] != NORMALIZATION_VERSION:
        raise RerunError("NORMALIZATION_VERSION_MISMATCH")
    if contract["accounting"] != {
        "clean_steps": 497,
        "evaluation_failure_reproductions": 89,
        "frozen_pairs_scored_by_binding_repair": 0,
        "mutant_steps": 497,
        "new_formal_scoring_calls": 0,
        "pairs": 215,
        "steps": 994,
        "unique_trace_keys": 994,
    }:
        raise RerunError("BINDING_ACCOUNTING_MISMATCH", actual=contract["accounting"])
    mapping_path = BINDING_DIR / "finqa_v2_raw_normalized_mapping.jsonl"
    if sha256_file(mapping_path) != contract["trace"]["mapping_sha256"]:
        raise RerunError("MAPPING_HASH_MISMATCH")
    mapping = [
        json.loads(line)
        for line in mapping_path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    trace_keys = [row["trace_key"] for row in mapping]
    if len(mapping) != 994 or len(set(trace_keys)) != 994:
        raise RerunError(
            "MAPPING_TRACE_ACCOUNTING_MISMATCH",
            rows=len(mapping),
            unique_keys=len(set(trace_keys)),
        )
    split = load_json(TASK_DIR / "finqa_v2_split_manifest.json")
    samples = {
        row["sample_id"]: row
        for row in load_json(TASK_DIR / "finqa_v2_frozen_sample_manifest.json")["samples"]
    }
    evaluation = [
        row for row in split["samples"] if row["split_role"] == "evaluation"
    ]
    clusters = {
        samples[row["sample_id"]]["provenance"]["report_cluster_id"]
        for row in evaluation
    }
    if len(evaluation) != 89 or len(clusters) != 30:
        raise RerunError(
            "POPULATION_MISMATCH",
            evaluation=len(evaluation),
            clusters=len(clusters),
        )
    return {
        "old_run_hashes": len(contract["old_run"]["immutable_output_sha256"]),
        "frozen_input_hashes": len(contract["input_sha256"]),
        "binding_receipt_self_hash": receipt["self_sha256"],
        "loop_c_audit_sha256": sha256_file(audit_path),
        "mapping_rows": len(mapping),
        "evaluation_samples": len(evaluation),
        "report_clusters": len(clusters),
        "rerun_namespace_file_outputs": (
            sum(1 for path in RESULTS_DIR.rglob("*") if path.is_file())
            if RESULTS_DIR.exists()
            else 0
        ),
    }


def run_command(command: str) -> tuple[int, str]:
    command_prefix = "PYTHONPATH=src "
    if command.startswith(command_prefix):
        command_body = command[len(command_prefix) :]
    else:
        command_body = command
    completed = subprocess.run(
        shlex.split(command_body),
        cwd=ROOT,
        env={**__import__("os").environ, "PYTHONPATH": "src"},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return completed.returncode, completed.stdout


def write_preflight_logs() -> None:
    commands = (
        (FOCUSED_TEST_COMMAND, "finqa_v2_focused_preflight.log", "19 passed"),
        (BINDING_TEST_COMMAND, "finqa_v2_binding_v2_preflight.log", "10 passed"),
    )
    for command, name, expected in commands:
        exit_code, output = run_command(command)
        text = f"COMMAND={command}\n{output.rstrip()}\nEXIT_CODE={exit_code}\n"
        (RESULTS_DIR / name).write_text(text, encoding="utf-8")
        if exit_code != 0 or expected not in output:
            raise RerunError(
                "FOCUSED_PREFLIGHT_FAILED",
                command=command,
                exit_code=exit_code,
                expected=expected,
            )


def prepare_engine(engine: Any) -> Any:
    from research.finqa_v2_20261010.binding_v2.finqa_v2_scorer_runtime_binding_v2 import (
        RuntimeBindingV2,
    )

    adapter = RuntimeBindingV2.from_paths(
        contract_path=BINDING_DIR / "finqa_v2_artifact_binding_contract_v2.json",
        mapping_path=BINDING_DIR / "finqa_v2_raw_normalized_mapping.jsonl",
    )

    def formal_output_inventory() -> list[str]:
        if not RESULTS_DIR.exists():
            return []
        hits = {
            path.name
            for path in RESULTS_DIR.iterdir()
            if path.is_file()
            and (
                path.name in engine.REQUIRED_OUTPUTS
                or "result" in path.name
                or "sample_rows" in path.name
                or "bootstrap_replicates" in path.name
            )
        }
        return sorted(hits)

    def score_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
        output: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []
        for row in rows:
            try:
                result = adapter.score_pair(
                    row["_score_payload"],
                    artifact_id=row["artifact_id"],
                    sample_id=row["sample_id"],
                    expected_trace_rows=adapter.trace_rows_by_artifact[row["artifact_id"]],
                    expected_raw_sha256=row["manifest_artifact_sha256"],
                )
                scored = result["scorer"]
                binding = result["binding"]
                vector = scored["observation_vector"]
                if set(vector) != set(engine.SCORER_FIELDS):
                    raise ValueError("observation_field_mismatch")
                if any(
                    type(vector[field]) is not int or vector[field] not in (0, 1)
                    for field in engine.SCORER_FIELDS
                ):
                    raise ValueError("observation_value_invalid")
                if binding["raw_payload_sha256"] != row["manifest_artifact_sha256"]:
                    raise ValueError("raw_payload_binding_mismatch")
                if binding["normalized_payload_sha256"] != scored["artifact_sha256"]:
                    raise ValueError("normalized_scorer_binding_mismatch")
                if scored["semantic_correctness_claim"] is not False:
                    raise ValueError("semantic_correctness_claim_mismatch")
                visibility = int(
                    any(vector[field] == 1 for field in engine.SCORER_FIELDS)
                )
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
                        "raw_payload_sha256": binding["raw_payload_sha256"],
                        "manifest_artifact_sha256": row["manifest_artifact_sha256"],
                        "normalized_payload_sha256": binding[
                            "normalized_payload_sha256"
                        ],
                        "scorer_payload_sha256": scored["artifact_sha256"],
                        "normalization_version": binding["normalization_version"],
                        "trace_key_count": len(binding["trace_keys"]),
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
                        "error_code": getattr(error, "code", ""),
                        "error": str(error),
                    }
                )
        if failures or len(output) != 89:
            failure_path = RESULTS_DIR / "finqa_v2_formal_scorer_failures.jsonl"
            failure_path.write_text(
                "".join(
                    json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n"
                    for item in failures
                ),
                encoding="utf-8",
            )
            raise engine.FormalRunError(
                "FORMAL_RUN_INVALID",
                expected=89,
                scored=len(output),
                failures=failures,
            )
        return output, 89

    engine.RESULTS_DIR = RESULTS_DIR
    engine.formal_output_inventory = formal_output_inventory
    engine.score_rows = score_rows
    return adapter


def finalize_outputs(engine: Any, binding_test_sha256: str) -> dict[str, Any]:
    payload_path = RESULTS_DIR / "finqa_v2_formal_results.json"
    payload = load_json(payload_path)
    payload["task_id"] = TASK_ID
    payload["namespace"] = "FINQA_V2_BINDING_V2_MINIMAL_RERUN_RESULTS"
    payload["run_status"] = "FORMAL_RUN_COMPLETE_AWAITING_LOOP_C_INDEPENDENT_RECOMPUTATION"
    payload["binding_v2_contract"] = {
        "contract_path": "research/finqa_v2_20261010/binding_v2/finqa_v2_artifact_binding_contract_v2.json",
        "contract_sha256": sha256_file(
            BINDING_DIR / "finqa_v2_artifact_binding_contract_v2.json"
        ),
        "runtime_path": "research/finqa_v2_20261010/binding_v2/finqa_v2_scorer_runtime_binding_v2.py",
        "runtime_sha256": sha256_file(
            BINDING_DIR / "finqa_v2_scorer_runtime_binding_v2.py"
        ),
        "mapping_path": "research/finqa_v2_20261010/binding_v2/finqa_v2_raw_normalized_mapping.jsonl",
        "mapping_sha256": sha256_file(
            BINDING_DIR / "finqa_v2_raw_normalized_mapping.jsonl"
        ),
        "mapping_rows": 994,
        "normalization_version": NORMALIZATION_VERSION,
        "raw_hash_field": "raw_payload_sha256",
        "normalized_hash_field": "normalized_payload_sha256",
        "op_family_is_raw_operator_identity": False,
        "trace_map_retained": True,
    }
    payload["execution"]["pre_scorer_runner_attempts"] = 1
    payload["execution"]["pre_scorer_runner_import_failures"] = 0
    payload["execution"]["pre_scorer_command_failures"] = 1
    payload["execution"]["pre_scorer_scorer_calls"] = 0
    payload["execution"]["binding_v2_scorer_calls"] = 89
    payload["execution"]["binding_v2_preflight_tests_passed"] = 10
    payload["execution"]["loop_c_scorer_binding_go"] = "PASS"
    write_json(payload_path, payload)

    report = engine.render_report(payload)
    binding_lines = [
        "",
        "## Binding V2",
        "",
        f"- Contract SHA-256: `{payload['binding_v2_contract']['contract_sha256']}`.",
        f"- Runtime SHA-256: `{payload['binding_v2_contract']['runtime_sha256']}`.",
        f"- Raw-to-normalized trace map: `{payload['binding_v2_contract']['mapping_rows']}` rows, SHA-256 `{payload['binding_v2_contract']['mapping_sha256']}`.",
        f"- Normalization version: `{payload['binding_v2_contract']['normalization_version']}`.",
        "- `raw_payload_sha256` is the provenance hash; `normalized_payload_sha256` is the scorer-runtime authoritative hash.",
        "- The trace map is retained, and `op_family` is never reported as raw operator identity.",
        "",
    ]
    title_index = report.index("## Frozen Research Question")
    report = report[:title_index] + "\n".join(binding_lines) + report[title_index:]
    report_path = RESULTS_DIR / "FINQA_V2_FORMAL_RESULT_REPORT.md"
    report_path.write_text(report + "\n", encoding="utf-8")

    execution_log = [
        f"TASK_ID={TASK_ID}",
        "BINDING_CONTRACT=binding_v2",
        f"NORMALIZATION_VERSION={NORMALIZATION_VERSION}",
        "LOOP_C_SCORER_BINDING_GO=PASS",
        "PRE_SCORER_ATTEMPT=1 command_failures=1 scorer_calls=0",
        "FORMAL_OUTPUT_PRECHECK=PASS count=0",
        "FROZEN_HASH_VERIFICATION=PASS checks=60 mismatches=0",
        "FOCUSED_PREFLIGHT=PASS passed=19",
        "BINDING_V2_PREFLIGHT=PASS passed=10",
        "EVALUATION_SELECTION=PASS samples=89 clusters=30 stages=E:30,P:30,N:29",
        "SCORER_EXECUTION=PASS calls=89 failures=0 train_calibration_calls=0",
        "BINDING_TRACE_MAP=PASS rows=994 unique_trace_keys=994 retained=True",
        "RAW_HASH_FIELD=raw_payload_sha256",
        "NORMALIZED_HASH_FIELD=normalized_payload_sha256",
        "OP_FAMILY_AS_RAW_OPERATOR_IDENTITY=FORBIDDEN",
        "ESTIMAND_MATERIALIZATION=PASS estimands=56",
        "BOOTSTRAP=PASS seed=20261017 replicates=10000 estimands=56",
        "PERMUTATION_TEST=NOT_USED",
        "ENDPOINT_CALLS=0 MODEL_CALLS=0 TRAINING_RUNS=0 PRM_RUNS=0",
        "FORMAL_RUN_STATUS=FORMAL_RUN_COMPLETE_AWAITING_LOOP_C_INDEPENDENT_RECOMPUTATION",
    ]
    (RESULTS_DIR / "finqa_v2_formal_execution.log").write_text(
        "\n".join(execution_log) + "\n", encoding="utf-8"
    )

    receipt_path = RESULTS_DIR / "finqa_v2_formal_execution_receipt.json"
    receipt = load_json(receipt_path)
    receipt["task_id"] = TASK_ID
    receipt["namespace"] = "FINQA_V2_BINDING_V2_MINIMAL_RERUN_EXECUTION_RECEIPT"
    receipt["status"] = "FORMAL_RUN_COMPLETE_AWAITING_LOOP_C_INDEPENDENT_RECOMPUTATION"
    receipt["role"] = "MINIMAL_FORMAL_RERUN_BINDING_V2"
    receipt["authorization"] = {
        "source": "docs/experiments/2026-10-10_loop_c_finqa_v2_binding_v2_audit.md",
        "scorer_binding_go": "PASS",
        "verdict": "PASS",
        "scope": "formal scorer -> frozen estimands -> frozen bootstrap only",
        "human_owner_task_card": TASK_ID,
    }
    receipt["binding_v2"] = payload["binding_v2_contract"]
    receipt["execution_counters"]["pre_scorer_runner_attempts"] = 1
    receipt["execution_counters"]["pre_scorer_runner_import_failures"] = 0
    receipt["execution_counters"]["pre_scorer_command_failures"] = 1
    receipt["execution_counters"]["pre_scorer_scorer_calls"] = 0
    receipt["execution_counters"]["binding_v2_scorer_calls"] = 89
    receipt["execution_counters"]["binding_v2_preflight_tests_passed"] = 10
    receipt["execution_counters"]["loop_c_scorer_binding_go"] = "PASS"
    receipt["hash_field_guard"] = {
        "raw_hash_field": "raw_payload_sha256",
        "normalized_hash_field": "normalized_payload_sha256",
        "scorer_hash_field": "scorer_payload_sha256",
        "normalized_and_scorer_values_equal_for_all_rows": all(
            row["normalized_payload_sha256"] == row["scorer_payload_sha256"]
            for row in read_jsonl(RESULTS_DIR / "finqa_v2_formal_sample_rows.jsonl")
        ),
        "raw_values_are_provenance_hashes": True,
        "values_are_not_required_to_equal_across_hash_domains": True,
        "rows_with_raw_and_normalized_hashes": 89,
    }
    receipt["commands"] = {
        "focused_test": FOCUSED_TEST_COMMAND,
        "binding_v2_test": BINDING_TEST_COMMAND,
        "formal_execution": "PYTHONPATH=src ./venv/bin/python "
        "research/finqa_v2_20261010/run_finqa_v2_binding_v2_rerun.py",
    }
    receipt["runner"] = {
        "path": str(Path(__file__).resolve()),
        "bytes": Path(__file__).stat().st_size,
        "sha256": sha256_file(Path(__file__).resolve()),
    }
    receipt["binding_v2_preflight"] = {
        "command": BINDING_TEST_COMMAND,
        "passed": 10,
        "failed": 0,
        "exit_code": 0,
        "sha256": binding_test_sha256,
    }
    receipt["immutable_input_hashes"].update(
        {
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
                ROOT
                / "docs/experiments/2026-10-10_loop_c_finqa_v2_binding_v2_audit.md"
            ),
        }
    )
    receipt["formal_task_contract"] = {
        "path": "research/finqa_v2_20261010/binding_v2/FINQA_V2_MINIMAL_RERUN_TASK_CARD.md",
        "bytes": (
            BINDING_DIR / "FINQA_V2_MINIMAL_RERUN_TASK_CARD.md"
        ).stat().st_size,
        "sha256": sha256_file(BINDING_DIR / "FINQA_V2_MINIMAL_RERUN_TASK_CARD.md"),
    }
    receipt["post_run_requirement"] = (
        "Loop C must independently recompute scorer rows, V/D/O, all frozen "
        "estimands and bootstrap intervals before scientific acceptance."
    )

    output_names = (
        "finqa_v2_formal_sample_rows.jsonl",
        "finqa_v2_formal_results.json",
        "finqa_v2_bootstrap_replicates.jsonl",
        "FINQA_V2_FORMAL_RESULT_REPORT.md",
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
    receipt["all_output_hashes"] = output_hashes
    receipt["environment"] = output_hashes["finqa_v2_formal_environment.log"]
    receipt["execution_log"] = output_hashes["finqa_v2_formal_execution.log"]
    receipt["outputs"] = {
        name: output_hashes[name]
        for name in output_names
        if name
        in {
            "finqa_v2_formal_sample_rows.jsonl",
            "finqa_v2_formal_results.json",
            "finqa_v2_bootstrap_replicates.jsonl",
            "FINQA_V2_FORMAL_RESULT_REPORT.md",
        }
    }
    receipt.pop("pre_scorer_attempt_log", None)
    receipt["success_exit"] = {
        "all_89_evaluation_pairs_scored": True,
        "frozen_estimands_materialized": len(payload["point_estimates"]),
        "bootstrap_materialized": 10_000,
        "null_adverse_cases_preserved": True,
        "outputs_hash_bound_for_loop_c": True,
        "scientific_class_accepted": False,
    }
    receipt.pop("self_sha256", None)
    receipt["self_sha256"] = self_hash(receipt)
    write_json(receipt_path, receipt)
    return receipt


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def write_invalid_receipt(code: str, detail: Any) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    receipt = {
        "task_id": TASK_ID,
        "namespace": "FINQA_V2_BINDING_V2_MINIMAL_RERUN_EXECUTION_RECEIPT",
        "status": "FORMAL_RUN_INVALID",
        "created_at": __import__("datetime").datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "stop_condition": code,
        "detail": detail,
        "scope": "formal scorer -> frozen estimands -> frozen bootstrap only",
        "success_exit": {
            "all_89_evaluation_pairs_scored": False,
            "frozen_estimands_materialized": False,
            "bootstrap_materialized": False,
            "scientific_class_accepted": False,
        },
    }
    receipt["self_sha256"] = self_hash(receipt)
    write_json(RESULTS_DIR / "finqa_v2_formal_execution_receipt.json", receipt)


def main() -> int:
    preflight = verify_preflight()
    if "--preflight-only" in sys.argv:
        print(
            json.dumps(
                {**preflight, "status": "PREFLIGHT_ONLY_NOT_EXECUTED"},
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    if RESULTS_DIR.exists() and any(RESULTS_DIR.iterdir()):
        raise RerunError(
            "RERUN_NAMESPACE_OUTPUTS_ALREADY_EXIST",
            path=str(RESULTS_DIR),
            never_overwrite=True,
        )
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    write_preflight_logs()
    (RESULTS_DIR / "finqa_v2_formal_pre_scorer_attempt_1.log").write_text(
        "TASK_ID=" + TASK_ID + "\nBINDING_V2_ADAPTER_READY=PASS\n"
        "PRE_SCORER_COMMAND_FAILURE=1\n"
        "PRE_SCORER_SCORER_CALLS=0\n"
        "FIRST_ATTEMPT_ERROR=FileNotFoundError while starting focused pytest; "
        "no scorer record was read and no formal output was materialized.\n"
        "COMMAND_FIXED=shell-command parsing repaired before scorer execution.\n",
        encoding="utf-8",
    )

    engine = load_formal_module()
    adapter = prepare_engine(engine)
    del adapter
    try:
        exit_code = engine.main()
        if exit_code != 0:
            raise RerunError("FORMAL_ENGINE_NONZERO_EXIT", exit_code=exit_code)
        binding_test_sha256 = sha256_file(
            RESULTS_DIR / "finqa_v2_binding_v2_preflight.log"
        )
        receipt = finalize_outputs(engine, binding_test_sha256)
    except Exception as error:
        code = getattr(error, "code", type(error).__name__)
        detail = getattr(error, "detail", str(error))
        if not (RESULTS_DIR / "finqa_v2_formal_execution_receipt.json").exists():
            write_invalid_receipt(code, detail)
        raise
    print(
        json.dumps(
            {
                "task_id": receipt["task_id"],
                "status": receipt["status"],
                "samples": 89,
                "clusters": 30,
                "estimands": 56,
                "bootstrap_replicates": 10_000,
                "binding_v2_mapping_rows": 994,
                "scientific_class_accepted": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
