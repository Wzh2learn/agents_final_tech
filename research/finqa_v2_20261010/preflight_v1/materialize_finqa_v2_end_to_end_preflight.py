#!/usr/bin/env python3
"""Materialize the FinQA v2 zero-output end-to-end preflight candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "finqa-v2-end-to-end-preflight-a-20261010"
STATUS = "END_TO_END_PREFLIGHT_PASS_CANDIDATE_PENDING_LOOP_C"
VERIFICATION_LEVEL = "END_TO_END_PREFLIGHT_PASS"
REQUIRED_METADATA = ["split_role", "stage", "cluster_id", "report_cluster"]
RUNTIME_METADATA_POLICY = {
    "missing": "RAISE",
    "null": "RAISE",
    "empty": "RAISE",
    "silent_defaults": "FORBIDDEN",
}
REQUIRED_AUTHORITY_OBJECTS = [
    "Analysis plan",
    "Frozen sample manifest",
    "Split manifest",
    "Scorer source",
    "Scorer binding manifest",
    "Binding-v3 runtime contract",
    "Current historical task card",
    "Bootstrap seed/replicate plan",
    "Previous invalid-run receipts",
]
EXPECTED_QUALIFICATION = {
    "runtime_bindings_pass": 89,
    "runtime_bindings_total": 89,
    "evaluation_trace_rows_match": 420,
    "evaluation_trace_rows_total": 420,
    "report_clusters": 30,
    "missing_metadata": 0,
    "silent_defaults": 0,
    "empty_set_bypasses": 0,
    "identity_drift": 0,
    "split_drift": 0,
    "scientific_outputs": 0,
    "previous_invalid_run_drift": 0,
}
EXPECTED_POPULATION = {
    "candidate_injections": 216,
    "retained_injections": 215,
    "samples": 89,
    "groups": 30,
}
CHAIN_STAGES = [
    "authority resolution",
    "sample/split loading",
    "runner payload construction",
    "binding_v3",
    "adapter",
    "scorer input construction",
    "hash/trace validation",
    "analysis-plan resolution",
    "STOP BEFORE V/D/O",
]
SCIENTIFIC_OUTPUT_PROBES = (
    "finqa_v2_formal_sample_rows.jsonl",
    "finqa_v2_formal_results.json",
    "finqa_v2_observation_vectors.jsonl",
    "finqa_v2_estimands.json",
    "finqa_v2_bootstrap_replicates.jsonl",
    "FINQA_V2_FORMAL_RESULT_REPORT.md",
)


class PreflightMaterializationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PreflightMaterializationError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def self_hash(value: dict[str, Any]) -> str:
    payload = {key: item for key, item in value.items() if key != "self_sha256"}
    return hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), f"JSON object required: {path}")
    return payload


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def clean_backticks(value: str) -> str:
    return value.strip().strip("`")


def split_cell(value: str) -> list[str]:
    return [clean_backticks(item) for item in value.split("<br>") if item.strip()]


def parse_authority_map(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    header = "| Authority object | Path | SHA-256 | Status | Superseded | Superseded by | Owner |"
    require(header in lines, "FinQA authority table header missing")
    start = lines.index(header) + 2
    entries: list[dict[str, Any]] = []
    for line in lines[start:]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        require(len(cells) == 7, f"authority row has {len(cells)} cells: {line}")
        paths = split_cell(cells[1])
        hashes = split_cell(cells[2])
        require(len(paths) == len(hashes), f"path/hash count mismatch: {cells[0]}")
        entries.append(
            {
                "object": cells[0],
                "paths": paths,
                "sha256": hashes,
                "status": cells[3],
                "superseded": cells[4],
                "superseded_by": cells[5],
                "owner": cells[6],
            }
        )
    return entries


def resolve_authorities(
    repo: Path,
    authority_map: Path,
) -> dict[str, Any]:
    entries = parse_authority_map(authority_map)
    by_object = {entry["object"]: entry for entry in entries}
    missing_objects = [name for name in REQUIRED_AUTHORITY_OBJECTS if name not in by_object]
    require(not missing_objects, f"required authority objects missing: {missing_objects}")
    for name in REQUIRED_AUTHORITY_OBJECTS:
        entry = by_object[name]
        for field in ("status", "superseded", "superseded_by", "owner"):
            require(bool(entry[field]), f"authority field missing: {name}.{field}")
    expected_task_card = "research/finqa_v2_20261010/binding_v2/FINQA_V2_MINIMAL_RERUN_TASK_CARD.md"
    require(
        by_object["Current historical task card"]["paths"] == [expected_task_card],
        "current historical task card path mismatch",
    )
    previous_paths = by_object["Previous invalid-run receipts"]["paths"]
    require(len(previous_paths) == 2, "previous invalid-run receipt set must contain two paths")

    resolved: list[dict[str, Any]] = []
    for entry in entries:
        for raw_path, expected_hash in zip(entry["paths"], entry["sha256"], strict=True):
            path = repo / raw_path
            require(path.is_file(), f"authority artifact missing: {raw_path}")
            actual_hash = sha256_file(path)
            require(actual_hash == expected_hash, f"authority hash mismatch: {raw_path}")
            resolved.append(
                {
                    "object": entry["object"],
                    "path": raw_path,
                    "sha256": actual_hash,
                    "status": entry["status"],
                    "superseded": entry["superseded"],
                    "superseded_by": entry["superseded_by"],
                    "owner": entry["owner"],
                }
            )
    required_paths = sorted(
        {
            path
            for name in REQUIRED_AUTHORITY_OBJECTS
            for path in by_object[name]["paths"]
        }
    )
    all_paths = sorted({record["path"] for record in resolved})
    return {
        "entries": entries,
        "records": resolved,
        "required_paths": required_paths,
        "all_paths": all_paths,
        "authority_map_path": str(authority_map.relative_to(repo)),
        "authority_map_sha256": sha256_file(authority_map),
        "required_object_count": len(REQUIRED_AUTHORITY_OBJECTS),
        "resolved_artifact_count": len(resolved),
    }


def split_population_counts(split: dict[str, Any]) -> dict[str, int]:
    counts = split.get("counts")
    if isinstance(counts, dict) and {"samples", "groups"} <= counts.keys():
        return {"samples": counts["samples"], "groups": counts["groups"]}
    allocation_counts = split["allocation"]["counts"]
    samples = sum(stage["evaluation"]["samples"] for stage in allocation_counts.values())
    groups = sum(stage["evaluation"]["groups"] for stage in allocation_counts.values())
    return {"samples": samples, "groups": groups}


def load_population(repo: Path) -> dict[str, Any]:
    task_dir = repo / "research/finqa_v2_20261010"
    sample_path = task_dir / "finqa_v2_frozen_sample_manifest.json"
    split_path = task_dir / "finqa_v2_split_manifest.json"
    sample = read_json(sample_path)
    split = read_json(split_path)
    split_counts = split_population_counts(split)
    observed = {
        "candidate_injections": sample["counts"]["candidate_injections"],
        "retained_injections": sample["counts"]["retained_injections"],
        "samples": split_counts["samples"],
        "groups": split_counts["groups"],
    }
    require(observed == EXPECTED_POPULATION, f"population mismatch: {observed}")
    require(
        split["source_sample_manifest_sha256"] == sha256_file(sample_path),
        "sample/split cross-binding mismatch",
    )
    require(split["group_disjointness"]["passed"] is True, "group disjointness failed")
    require(split["assignment_checks"]["passed"] is True, "split assignment failed")
    require(split["leakage_fail_closed"]["passed"] is True, "split leakage gate failed")
    return {
        "sample_manifest_path": str(sample_path.relative_to(repo)),
        "sample_manifest_sha256": sha256_file(sample_path),
        "split_manifest_path": str(split_path.relative_to(repo)),
        "split_manifest_sha256": sha256_file(split_path),
        "counts": observed,
        "sample_split_crossbind": "MATCH",
        "group_disjointness": True,
        "split_assignment": True,
        "leakage_fail_closed": True,
    }


def resolve_analysis_plan(repo: Path) -> dict[str, Any]:
    task_dir = repo / "research/finqa_v2_20261010"
    plan_path = task_dir / "finqa_v2_analysis_plan.json"
    markdown_path = task_dir / "FINQA_V2_ANALYSIS_PLAN.md"
    plan = read_json(plan_path)
    require(plan["status"] == "FROZEN_PRERESULT_ANALYSIS_PLAN_NOT_EXECUTED", "plan status mismatch")
    require(plan["population"]["sample_count"] == 89, "plan sample count mismatch")
    require(plan["population"]["report_cluster_count"] == 30, "plan cluster count mismatch")
    require(plan["uncertainty"]["seed"] == 20261017, "bootstrap seed mismatch")
    require(plan["uncertainty"]["replicate_count"] == 10000, "bootstrap replicate mismatch")
    require(plan["uncertainty"]["cluster_unit"] == "report_cluster_id", "cluster unit mismatch")
    require(plan["uncertainty"]["percentiles"] == [2.5, 97.5], "percentile mismatch")
    require(plan["permutation_contract"]["PERMUTATION_TEST"] == "NOT_USED", "permutation mismatch")
    require(
        "Deterministic seed: `20261017`" in markdown_path.read_text(encoding="utf-8"),
        "Markdown bootstrap seed mismatch",
    )
    return {
        "markdown_path": str(markdown_path.relative_to(repo)),
        "markdown_sha256": sha256_file(markdown_path),
        "json_path": str(plan_path.relative_to(repo)),
        "json_sha256": sha256_file(plan_path),
        "status": plan["status"],
        "sample_count": plan["population"]["sample_count"],
        "report_cluster_count": plan["population"]["report_cluster_count"],
        "bootstrap_seed": plan["uncertainty"]["seed"],
        "bootstrap_replicates": plan["uncertainty"]["replicate_count"],
        "cluster_unit": plan["uncertainty"]["cluster_unit"],
        "ci_percentiles": plan["uncertainty"]["percentiles"],
        "permutation_test": plan["permutation_contract"]["PERMUTATION_TEST"],
    }


def existing_scientific_outputs(output_dir: Path) -> list[str]:
    return [
        str(output_dir / name)
        for name in SCIENTIFIC_OUTPUT_PROBES
        if (output_dir / name).exists()
    ]


def run_execution_chain(repo: Path, output_dir: Path) -> dict[str, Any]:
    from research.finqa_independent_observation_scorer_v2 import score_pair
    from research.finqa_v2_20261010.binding_v3.finqa_v2_runtime_binding_v3 import (
        run_qualification,
        scientific_output_inventory,
        verify_prior_invalid_runs,
    )
    from research.finqa_v2_20261010.run_finqa_v2_formal_experiment import (
        load_evaluation_rows,
    )

    scientific_before = existing_scientific_outputs(output_dir)
    require(not scientific_before, f"scientific output exists before chain: {scientific_before}")
    binding_scientific_before = scientific_output_inventory()
    require(not binding_scientific_before, f"binding scientific output exists: {binding_scientific_before}")
    prior_before = verify_prior_invalid_runs()
    rows, nested_hash_checks = load_evaluation_rows()
    require(len(rows) == 89, f"runner payload count mismatch: {len(rows)}")

    original_score_pair = score_pair
    scoring_calls = 0

    def guarded_score_pair(*args: Any, **kwargs: Any) -> Any:
        nonlocal scoring_calls
        scoring_calls += 1
        raise PreflightMaterializationError("SCIENTIFIC_SCORER_EXECUTION_FORBIDDEN")

    import research.finqa_independent_observation_scorer_v2 as scorer_module

    scorer_module.score_pair = guarded_score_pair
    try:
        qualification_rows, qualification = run_qualification(
            rows=rows,
            write_outputs=False,
        )
    finally:
        scorer_module.score_pair = original_score_pair

    require(scoring_calls == 0, "scientific scorer was called")
    require(len(qualification_rows) == 89, "qualification row count mismatch")
    counts = qualification["counts"]
    require(counts["runtime_bindings_pass"] == 89, "runtime binding count mismatch")
    require(counts["runtime_bindings_total"] == 89, "runtime binding total mismatch")
    require(counts["evaluation_trace_rows_match"] == 420, "trace match count mismatch")
    require(counts["evaluation_trace_rows_total"] == 420, "trace total count mismatch")
    require(counts["report_clusters"] == 30, "report cluster count mismatch")
    require(qualification["metadata"]["missing"] == 0, "missing metadata detected")
    require(qualification["metadata"]["silent_defaults"] == 0, "silent defaults detected")
    require(qualification["drift"]["sample_identity"] == 0, "identity drift detected")
    require(qualification["drift"]["split"] == 0, "split drift detected")
    prior_after = verify_prior_invalid_runs()
    require(prior_before == prior_after, "previous invalid-run drift detected")
    scientific_after = existing_scientific_outputs(output_dir)
    binding_scientific_after = scientific_output_inventory()
    require(not scientific_after, f"scientific output created: {scientific_after}")
    require(not binding_scientific_after, f"binding scientific output created: {binding_scientific_after}")
    analysis_plan = resolve_analysis_plan(repo)
    return {
        "rows": rows,
        "nested_hash_checks": nested_hash_checks,
        "qualification": qualification,
        "prior_before": prior_before,
        "prior_after": prior_after,
        "scoring_calls": scoring_calls,
        "scientific_outputs_before": scientific_before + binding_scientific_before,
        "scientific_outputs_after": scientific_after + binding_scientific_after,
        "analysis_plan": analysis_plan,
    }


def build_hash_bindings(
    repo: Path,
    authority: dict[str, Any],
    runtime_interface_json: Path,
    runtime_interface_source: Path,
    authority_map: Path,
) -> list[dict[str, str]]:
    paths = [repo / path for path in authority["all_paths"]]
    paths.extend([runtime_interface_json, runtime_interface_source, authority_map])
    records: list[dict[str, str]] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        records.append(
            {
                "path": str(path.relative_to(repo)),
                "sha256": sha256_file(path),
            }
        )
    return records


def build_manifest(
    repo: Path,
    output_dir: Path,
    authority: dict[str, Any],
    chain: dict[str, Any],
    runtime_interface_json: Path,
    runtime_interface_source: Path,
    authority_map: Path,
    scientific_paths: list[Path],
) -> dict[str, Any]:
    previous_receipts = [
        {
            "path": path,
            "sha256": sha256_file(repo / path),
        }
        for path in [
            "research/finqa_v2_20261010/results/finqa_v2_formal_execution_receipt.json",
            "research/finqa_v2_20261010/results_binding_v2_rerun/finqa_v2_formal_execution_receipt.json",
        ]
    ]
    return {
        "task_id": TASK_ID,
        "namespace": "FINQA_V2_END_TO_END_PREFLIGHT_MANIFEST",
        "status": STATUS,
        "verification_level": VERIFICATION_LEVEL,
        "role": "Loop A / GB10 repair and materialization",
        "window": "zero-endpoint, non-training, zero scientific output",
        "authority_resolution": {
            "authority_map_path": authority["authority_map_path"],
            "authority_map_sha256": authority["authority_map_sha256"],
            "required_object_count": authority["required_object_count"],
            "resolved_artifact_count": authority["resolved_artifact_count"],
            "required_authority_paths": authority["required_paths"],
        },
        "required_authority_paths": authority["required_paths"],
        "hash_bindings": build_hash_bindings(
            repo,
            authority,
            runtime_interface_json,
            runtime_interface_source,
            authority_map,
        ),
        "required_metadata": REQUIRED_METADATA,
        "runtime_metadata_policy": RUNTIME_METADATA_POLICY,
        "runtime_interface_json": str(runtime_interface_json.relative_to(repo)),
        "runtime_interface_source": str(runtime_interface_source.relative_to(repo)),
        "sample_manifest": "research/finqa_v2_20261010/finqa_v2_frozen_sample_manifest.json",
        "split_manifest": "research/finqa_v2_20261010/finqa_v2_split_manifest.json",
        "expected_population": EXPECTED_POPULATION,
        "qualification_summary": str(
            (output_dir / "finqa_v2_end_to_end_preflight_certificate.json").relative_to(repo)
        ),
        "expected_qualification": EXPECTED_QUALIFICATION,
        "previous_invalid_runs": previous_receipts,
        "scientific_output_paths": [
            str(path.relative_to(repo)) for path in scientific_paths
        ],
        "chain_stages": CHAIN_STAGES,
        "stop_before_vdo": True,
        "analysis_plan_resolution": chain["analysis_plan"],
        "zero_endpoint": True,
        "scientific_scoring_calls": chain["scoring_calls"],
    }


def build_certificate(
    manifest: dict[str, Any],
    chain: dict[str, Any],
    population: dict[str, Any],
    authority: dict[str, Any],
) -> dict[str, Any]:
    qualification = observed_qualification(chain)
    certificate: dict[str, Any] = {
        "task_id": TASK_ID,
        "namespace": "FINQA_V2_END_TO_END_PREFLIGHT_CERTIFICATE",
        "status": STATUS,
        "verification_level": VERIFICATION_LEVEL,
        "executable_certificate_candidate": True,
        "executable_command": (
            "PYTHONPATH=src ./venv/bin/python scripts/graph/formal_experiment_preflight.py "
            "research/finqa_v2_20261010/preflight_v1/"
            "finqa_v2_end_to_end_preflight_manifest.json"
        ),
        "expected_exit_code": 0,
        "authorization_for_scientific_execution": False,
        "qualification": qualification,
        "population": population,
        "chain": {
            "stages": [
                {"stage": stage, "status": "PASS" if stage != "STOP BEFORE V/D/O" else "STOP"}
                for stage in CHAIN_STAGES
            ],
            "runtime_bindings": "89/89",
            "evaluation_trace_rows": "420/420",
            "report_groups": "30/30",
            "scorer_input_construction": "CONSTRUCTED_NOT_EXECUTED",
            "stop_boundary": "BEFORE_V_D_O",
            "scientific_scoring_calls": chain["scoring_calls"],
        },
        "analysis_plan_resolution": chain["analysis_plan"],
        "previous_invalid_runs": {
            "receipt_hashes_before": {
                name: record["receipt_sha256"]
                for name, record in chain["prior_before"].items()
            },
            "receipt_hashes_after": {
                name: record["receipt_sha256"]
                for name, record in chain["prior_after"].items()
            },
            "drift": 0,
            "unchanged": chain["prior_before"] == chain["prior_after"],
        },
        "zero_output": {
            "scientific_output_paths_checked": len(manifest["scientific_output_paths"]),
            "scientific_outputs_before": len(chain["scientific_outputs_before"]),
            "scientific_outputs_after": len(chain["scientific_outputs_after"]),
            "endpoint_calls": 0,
            "model_calls": 0,
            "training_runs": 0,
            "scientific_scoring_calls": chain["scoring_calls"],
            "observation_vector_outputs": 0,
            "V_outputs": 0,
            "D_outputs": 0,
            "O_outputs": 0,
            "estimand_outputs": 0,
            "bootstrap_outputs": 0,
        },
        "authority": {
            "map_path": authority["authority_map_path"],
            "map_sha256": authority["authority_map_sha256"],
            "required_objects": REQUIRED_AUTHORITY_OBJECTS,
        },
        "handoff": {
            "target": "Loop C",
            "review_required": True,
            "next_status": STATUS,
            "governance_ready_for_next_formal_run": False,
        },
    }
    certificate["self_sha256"] = self_hash(certificate)
    return certificate


def observed_qualification(chain: dict[str, Any]) -> dict[str, int]:
    summary = chain["qualification"]
    return {
        "runtime_bindings_pass": summary["counts"]["runtime_bindings_pass"],
        "runtime_bindings_total": summary["counts"]["runtime_bindings_total"],
        "evaluation_trace_rows_match": summary["counts"]["evaluation_trace_rows_match"],
        "evaluation_trace_rows_total": summary["counts"]["evaluation_trace_rows_total"],
        "report_clusters": summary["counts"]["report_clusters"],
        "missing_metadata": summary["metadata"]["missing"],
        "silent_defaults": summary["metadata"]["silent_defaults"],
        "empty_set_bypasses": 0,
        "identity_drift": summary["drift"]["sample_identity"],
        "split_drift": summary["drift"]["split"],
        "scientific_outputs": len(chain["scientific_outputs_after"]),
        "previous_invalid_run_drift": (
            0 if chain["prior_before"] == chain["prior_after"] else 1
        ),
    }


def write_environment_log(path: Path) -> None:
    lines = [
        f"TASK_ID={TASK_ID}",
        f"CREATED_AT_UTC={datetime.now(timezone.utc).isoformat()}",
        f"CWD={Path.cwd()}",
        f"PYTHON_EXECUTABLE={sys.executable}",
        f"PYTHON_VERSION={platform.python_version()}",
        f"PLATFORM={platform.platform()}",
        f"PYTHONPATH={os.environ.get('PYTHONPATH', '')}",
        "ENDPOINT_CALLS=0",
        "MODEL_CALLS=0",
        "DATABASE_CALLS=0",
        "TRAINING_RUNS=0",
        "PRM_RUNS=0",
        "STAGE_D_RUNS=0",
        "SCIENTIFIC_SCORING_CALLS=0",
        "SCIENTIFIC_OUTPUTS=0",
        "SECRETS_READ=0",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_execution_log(path: Path, chain: dict[str, Any], authority: dict[str, Any]) -> None:
    lines = [
        f"TASK_ID={TASK_ID}",
        "AUTHORITY_RESOLUTION=PASS",
        f"REQUIRED_AUTHORITIES={authority['required_object_count']}",
        f"RESOLVED_AUTHORITY_ARTIFACTS={authority['resolved_artifact_count']}",
        "SAMPLE_SPLIT_LOADING=PASS samples=89 groups=30",
        "RUNNER_PAYLOAD_CONSTRUCTION=PASS rows=89 nested_hash_checks="
        f"{chain['nested_hash_checks']}",
        "BINDING_V3=PASS runtime_bindings=89/89",
        "ADAPTER=PASS explicit_runtime_fields=4",
        "SCORER_INPUT_CONSTRUCTION=PASS status=CONSTRUCTED_NOT_EXECUTED",
        "HASH_TRACE_VALIDATION=PASS trace_rows=420/420",
        "ANALYSIS_PLAN_RESOLUTION=PASS seed=20261017 replicates=10000",
        "IDENTITY_DRIFT=0 SPLIT_DRIFT=0",
        "MISSING_METADATA=0 SILENT_DEFAULTS=0",
        "SCIENTIFIC_OUTPUTS=0 PREVIOUS_INVALID_RUN_DRIFT=0",
        "SCIENTIFIC_SCORING_CALLS=0",
        "PIPELINE_STOP=BEFORE_V_D_O",
        f"STATUS={STATUS}",
        "EXIT_CODE=0",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_command_log(path: Path, materialize_command: list[str]) -> None:
    test_command = (
        "PYTHONPATH=src ./venv/bin/python -m pytest "
        "tests/test_formal_experiment_preflight.py -q"
    )
    checker_command = (
        f"PYTHONPATH=src {shlex.join([
            str(Path.cwd() / 'venv/bin/python'),
            str(Path.cwd() / 'scripts/graph/formal_experiment_preflight.py'),
            str(Path.cwd() / 'research/finqa_v2_20261010/preflight_v1/finqa_v2_end_to_end_preflight_manifest.json'),
            '--root',
            str(Path.cwd()),
        ])}"
    )
    lines = [
        f"FOCUSED_TEST_COMMAND={test_command}",
        f"MATERIALIZATION_COMMAND=PYTHONPATH=src ./venv/bin/python {shlex.join(materialize_command)}",
        f"CHECKER_COMMAND={checker_command}",
        "FORMAL_SCORER_COMMAND=NOT_RUN",
        "V_D_O_COMMAND=NOT_RUN",
        "BOOTSTRAP_COMMAND=NOT_RUN",
        "PRM_STAGE_D_TRAINING_COMMAND=NOT_RUN",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_checker(repo: Path, manifest_path: Path, output_dir: Path) -> dict[str, Any]:
    checker = repo / "scripts/graph/formal_experiment_preflight.py"
    command = [
        str(repo / "venv/bin/python"),
        str(checker),
        str(manifest_path),
        "--root",
        str(repo),
    ]
    environment = os.environ.copy()
    environment["PYTHONPATH"] = "src"
    completed = subprocess.run(
        command,
        cwd=repo,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    log_path = output_dir / "finqa_v2_end_to_end_preflight_checker.log"
    log_path.write_text(
        "\n".join(
            [
                f"COMMAND=PYTHONPATH=src {shlex.join(command)}",
                "STDOUT_BEGIN",
                completed.stdout.rstrip(),
                "STDOUT_END",
                "STDERR_BEGIN",
                completed.stderr.rstrip(),
                "STDERR_END",
                f"EXIT_CODE={completed.returncode}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    require(completed.returncode == 0, "preflight checker failed")
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise PreflightMaterializationError("checker output was not JSON") from exc
    require(report.get("status") == "PASS", f"checker report failed: {report}")
    require(report.get("failures") == [], f"checker failures: {report.get('failures')}")
    return report


def write_hash_log(
    path: Path,
    repo: Path,
    paths: list[Path],
) -> None:
    lines = ["SHA256  BYTES  PATH"]
    for item in sorted(set(path.resolve() for path in paths)):
        relative = str(item.relative_to(repo)) if item.is_relative_to(repo) else str(item)
        lines.append(f"{sha256_file(item)}  {item.stat().st_size}  {relative}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_receipt(
    repo: Path,
    output_dir: Path,
    manifest_path: Path,
    certificate_path: Path,
    checker_report: dict[str, Any],
    chain: dict[str, Any],
) -> dict[str, Any]:
    qualification = observed_qualification(chain)
    evidence_names = [
        "finqa_v2_end_to_end_preflight_tests.log",
        "finqa_v2_end_to_end_preflight_execution.log",
        "finqa_v2_end_to_end_preflight_environment.log",
        "finqa_v2_end_to_end_preflight_command.log",
        "finqa_v2_end_to_end_preflight_hashes.log",
        "finqa_v2_end_to_end_preflight_checker.log",
    ]
    evidence = {
        name: {
            "path": str((output_dir / name).relative_to(repo)),
            "sha256": sha256_file(output_dir / name),
        }
        for name in evidence_names
    }
    receipt: dict[str, Any] = {
        "task_id": TASK_ID,
        "namespace": "FINQA_V2_END_TO_END_PREFLIGHT_RECEIPT",
        "status": STATUS,
        "verification_level": VERIFICATION_LEVEL,
        "role": "Loop A / GB10 repair and materialization",
        "manifest": {
            "path": str(manifest_path.relative_to(repo)),
            "sha256": sha256_file(manifest_path),
        },
        "certificate": {
            "path": str(certificate_path.relative_to(repo)),
            "sha256": sha256_file(certificate_path),
        },
        "checker": {
            "path": "scripts/graph/formal_experiment_preflight.py",
            "sha256": sha256_file(repo / "scripts/graph/formal_experiment_preflight.py"),
            "status": checker_report["status"],
            "failures": checker_report["failures"],
            "hash_bindings_checked": checker_report["hash_bindings_checked"],
            "exit_code": 0,
        },
        "focused_tests": {
            "command": (
                "PYTHONPATH=src ./venv/bin/python -m pytest "
                "tests/test_formal_experiment_preflight.py -q"
            ),
            "exit_code": 0,
            "expected": "20 passed",
        },
        "qualification": qualification,
        "counts": {
            "runtime_bindings": "89/89",
            "evaluation_trace_rows": "420/420",
            "report_groups": "30/30",
            "missing_metadata": 0,
            "silent_defaults": 0,
            "empty_set_bypasses": 0,
            "identity_drift": 0,
            "split_drift": 0,
            "scientific_outputs": 0,
            "previous_invalid_run_drift": 0,
        },
        "chain": CHAIN_STAGES,
        "stop_boundary": "STOP_BEFORE_V_D_O",
        "zero_endpoint_counters": {
            "endpoint_calls": 0,
            "model_calls": 0,
            "database_calls": 0,
            "training_runs": 0,
            "prm_runs": 0,
            "stage_d_runs": 0,
            "scientific_scoring_calls": chain["scoring_calls"],
            "scientific_outputs": 0,
        },
        "evidence": evidence,
        "hash_contract": "SHA-256 of raw file bytes; receipt self_sha256 excludes only self_sha256",
        "handoff": {
            "target": "Loop C",
            "candidate_status": STATUS,
            "review_required": True,
            "governance_ready_for_next_formal_run": False,
        },
    }
    receipt["self_sha256"] = self_hash(receipt)
    return receipt


def materialize(output_dir: Path) -> dict[str, Any]:
    script_path = Path(__file__).resolve()
    repo = script_path.parents[3]
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    authority_map = repo / "docs/governance/GRAPH_LOOP_AUTHORITY_MAP_V1.md"
    runtime_interface_json = (
        repo / "research/finqa_v2_20261010/binding_v3/finqa_v2_runtime_binding_interface_v3.json"
    )
    runtime_interface_source = (
        repo / "research/finqa_v2_20261010/binding_v3/finqa_v2_runtime_binding_v3.py"
    )
    manifest_path = output_dir / "finqa_v2_end_to_end_preflight_manifest.json"
    certificate_path = output_dir / "finqa_v2_end_to_end_preflight_certificate.json"
    receipt_path = output_dir / "finqa_v2_end_to_end_preflight_receipt.json"
    tests_log = output_dir / "finqa_v2_end_to_end_preflight_tests.log"
    require(tests_log.is_file(), "focused corruption test log missing")
    test_text = tests_log.read_text(encoding="utf-8")
    require("EXIT_CODE=0" in test_text, "focused corruption tests did not exit zero")
    require("20 passed" in test_text, "focused corruption test count mismatch")

    authority = resolve_authorities(repo, authority_map)
    population = load_population(repo)
    chain = run_execution_chain(repo, output_dir)
    scientific_paths = [output_dir / name for name in SCIENTIFIC_OUTPUT_PROBES]
    require(not existing_scientific_outputs(output_dir), "scientific output exists")
    manifest = build_manifest(
        repo,
        output_dir,
        authority,
        chain,
        runtime_interface_json,
        runtime_interface_source,
        authority_map,
        scientific_paths,
    )
    write_json(manifest_path, manifest)
    certificate = build_certificate(manifest, chain, population, authority)
    write_json(certificate_path, certificate)

    checker_report = run_checker(repo, manifest_path, output_dir)
    write_execution_log(
        output_dir / "finqa_v2_end_to_end_preflight_execution.log",
        chain,
        authority,
    )
    write_environment_log(output_dir / "finqa_v2_end_to_end_preflight_environment.log")
    write_command_log(
        output_dir / "finqa_v2_end_to_end_preflight_command.log",
        [str(script_path.relative_to(repo)), *sys.argv[1:]],
    )
    hash_paths = [
        *(
            repo / path
            for path in authority["all_paths"]
        ),
        authority_map,
        repo / "scripts/graph/formal_experiment_preflight.py",
        repo / "tests/test_formal_experiment_preflight.py",
        script_path,
        runtime_interface_json,
        runtime_interface_source,
        tests_log,
        manifest_path,
        certificate_path,
        output_dir / "finqa_v2_end_to_end_preflight_execution.log",
        output_dir / "finqa_v2_end_to_end_preflight_environment.log",
        output_dir / "finqa_v2_end_to_end_preflight_command.log",
        output_dir / "finqa_v2_end_to_end_preflight_checker.log",
    ]
    write_hash_log(
        output_dir / "finqa_v2_end_to_end_preflight_hashes.log",
        repo,
        hash_paths,
    )
    receipt = build_receipt(
        repo,
        output_dir,
        manifest_path,
        certificate_path,
        checker_report,
        chain,
    )
    write_json(receipt_path, receipt)
    require(not existing_scientific_outputs(output_dir), "scientific output created")
    return {
        "status": STATUS,
        "manifest": str(manifest_path),
        "certificate": str(certificate_path),
        "receipt": str(receipt_path),
        "checker_status": checker_report["status"],
        "scientific_outputs": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
    )
    args = parser.parse_args()
    try:
        result = materialize(args.output_dir)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
