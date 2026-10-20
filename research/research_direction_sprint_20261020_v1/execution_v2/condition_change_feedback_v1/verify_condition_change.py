#!/usr/bin/env python3
"""Machine-verify CONDITION_CHANGE_FEEDBACK_V1 without external requests."""

from __future__ import annotations

import platform
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

from condition_change_common import (
    ACTOR_TASKS_PATH,
    EVIDENCE_IDENTITY,
    FACTS_PATH,
    INPUT_MANIFEST_PATH,
    MACHINE_VERIFICATION_PATH,
    PACKAGE_NAME,
    POLICY_PATH,
    PROBE_FIXTURES_PATH,
    PROBE_FREEZE_MANIFEST_PATH,
    PROBE_RESULTS_PATH,
    PROBE_RUN_MANIFEST_PATH,
    REFERENCE_TASKS_PATH,
    REQUEST_ACCOUNTING,
    SCHEMA_PATH,
    SOURCE_CASES_PATH,
    SOURCE_POLICY_PATH,
    SUPPORTED_PYTHON_VERSIONS,
    TASK_ID,
    V1_FROZEN_FILES,
    canonical_json_text,
    load_json,
    sha256_file,
    validate_against_definition,
    write_json,
)
from reference_builder import derive_all_references
from run_feedback_probe import build_probe_result, fixed_decimal


EXACT_COMMANDS = [
    "python3 -B build_condition_change_inputs.py --freeze",
    "python3 -B run_feedback_probe.py --freeze",
    "python3 -B run_feedback_probe.py --run",
    "python3 -B -m unittest -v test_condition_change.py",
    "python3 -B verify_condition_change.py",
]

EXPECTED_DISPOSITIONS = {
    "OUT_OF_SCOPE_COUNTERFACTUAL": {
        "composite": "RETAIN",
        "exact_match": "RETAIN",
        "sufficiency_only": "RETAIN",
    },
    "OUT_OF_SCOPE_ADDITION": {
        "composite": "REVISE",
        "exact_match": "REVISE",
        "sufficiency_only": "RETAIN",
    },
    "VALID_ALTERNATE_SET": {
        "composite": "RETAIN",
        "exact_match": "REVISE",
        "sufficiency_only": "RETAIN",
    },
}


def _zero(value: Any, label: str, errors: list[str]) -> None:
    if value != 0:
        errors.append(f"{label} must be zero, got {value}")


def verify() -> dict[str, Any]:
    errors: list[str] = []
    manifest = load_json(INPUT_MANIFEST_PATH)
    actor_payload = load_json(ACTOR_TASKS_PATH)
    facts = load_json(FACTS_PATH)
    references_payload = load_json(REFERENCE_TASKS_PATH)
    references = references_payload["references"]
    fixture = load_json(PROBE_FIXTURES_PATH)
    result = load_json(PROBE_RESULTS_PATH)
    run_manifest = load_json(PROBE_RUN_MANIFEST_PATH)
    freeze_manifest = load_json(PROBE_FREEZE_MANIFEST_PATH)
    source_policy = load_json(SOURCE_POLICY_PATH)
    source_cases = load_json(SOURCE_CASES_PATH)

    for entry in manifest["canonical_input_files"]:
        path = Path(entry["path"])
        if not path.exists():
            errors.append(f"missing frozen input: {path.name}")
        elif sha256_file(path) != entry["sha256"]:
            errors.append(f"hash mismatch: {path.name}")
    v1_paths = {path.name: path for path in V1_FROZEN_FILES}
    v1_input_manifest = load_json(v1_paths["FROZEN_INPUT_MANIFEST.json"])
    v1_freeze_manifest = load_json(v1_paths["PROBE_FREEZE_MANIFEST.json"])
    v1_run_manifest = load_json(v1_paths["PROBE_RUN_MANIFEST.json"])
    for entry in v1_input_manifest["canonical_input_files"]:
        path = v1_paths[entry["path"]]
        if not path.exists() or sha256_file(path) != entry["sha256"]:
            errors.append(f"V1 input hash changed: {entry['path']}")
    for entry in v1_freeze_manifest["frozen_files"]:
        path = v1_paths[entry["path"]]
        if not path.exists() or sha256_file(path) != entry["sha256"]:
            errors.append(f"V1 frozen result hash changed: {entry['path']}")
    if v1_run_manifest["frozen_result_sha256"] != sha256_file(
        v1_paths["FEEDBACK_PROBE_RESULTS_V1.json"]
    ):
        errors.append("V1 run manifest no longer matches the V1 frozen result")
    for path in V1_FROZEN_FILES:
        if manifest["v1_frozen_hashes"].get(path.name) != sha256_file(path):
            errors.append(f"V2 receipt V1 hash mismatch: {path.name}")
    for entry in freeze_manifest["frozen_files"]:
        path = Path(entry["path"])
        if not path.exists() or sha256_file(path) != entry["sha256"]:
            errors.append(f"probe freeze hash mismatch: {path.name}")

    runtime = {
        "executable": sys.executable,
        "implementation": platform.python_implementation(),
        "version": platform.python_version(),
    }
    if runtime["implementation"] != "CPython" or ".".join(
        runtime["version"].split(".")[:2]
    ) not in SUPPORTED_PYTHON_VERSIONS:
        errors.append(f"Python runtime mismatch: {runtime}")
    if manifest["task_id"] != TASK_ID:
        errors.append("task_id mismatch")
    if result.get("task_id") != TASK_ID:
        errors.append("probe result task_id mismatch")
    for label, payload in (
        ("input_manifest", manifest),
        ("probe_result", result),
        ("probe_freeze", freeze_manifest),
    ):
        if "launcher_ids" in payload:
            errors.append(f"{label} records launcher IDs outside the run manifest")
    if "launcher_ids" not in run_manifest:
        errors.append("run manifest does not record launcher IDs")
    if manifest["evidence_identity"] != EVIDENCE_IDENTITY:
        errors.append("evidence identity mismatch")

    actor_tasks = actor_payload["tasks"]
    expected_task_count = manifest["paired_cases"] * 2
    if len(actor_tasks) != expected_task_count or len(references) != expected_task_count:
        errors.append("actor/reference task count does not match paired cases")
    if len({task["case_id"] for task in actor_tasks}) != manifest["paired_cases"]:
        errors.append("paired case count does not match manifest")
    if manifest["paired_cases"] != 13:
        errors.append("V2 paired case count is not 13")
    if len({task["source_cluster"] for task in actor_tasks}) < 4:
        errors.append("source cluster count is below four")
    for actor_task in actor_tasks:
        try:
            validate_against_definition(actor_task, "actor_task")
        except Exception as error:
            errors.append(f"invalid actor task {actor_task.get('task_id')}: {error}")
        context = actor_task.get("policy_context", {})
        if context.get("policy_version_id") != actor_task["policy_version_id"]:
            errors.append(
                f"actor policy version mismatch: {actor_task.get('task_id')}"
            )
        if not context.get("applicable_policy_text"):
            errors.append(f"actor policy text missing: {actor_task.get('task_id')}")
        if not context.get("explicit_policy_delta_text"):
            errors.append(f"actor policy delta missing: {actor_task.get('task_id')}")
        for prohibited in (
            "decision",
            "minimal_sufficient_sets",
            "canonical_sufficient_set",
            "reference_facts",
            "adjudication",
        ):
            if prohibited in actor_task:
                errors.append(
                    f"actor input contains prohibited field {prohibited}: "
                    f"{actor_task.get('task_id')}"
                )
    for fact in facts:
        try:
            validate_against_definition(fact, "evidence_fact")
        except Exception as error:
            errors.append(f"invalid evidence fact: {error}")
    for reference in references:
        try:
            validate_against_definition(reference, "reference_task")
        except Exception as error:
            errors.append(f"invalid reference {reference.get('task_id')}: {error}")

    recomputed_references = derive_all_references(POLICY_PATH, FACTS_PATH)
    if recomputed_references != references_payload:
        errors.append("reference builder is not reproducible")
    recomputed_result = build_probe_result()
    if recomputed_result != result:
        errors.append("feedback probe result is not reproducible")
    if run_manifest["status"] != "MATCH":
        errors.append("feedback probe run status is not MATCH")
    if run_manifest["frozen_result_sha256"] != run_manifest[
        "recomputed_result_sha256"
    ]:
        errors.append("feedback probe result hashes differ")

    counts = result["reference_counts"]
    required_counts = {
        "actor_tasks": 26,
        "paired_cases": 13,
        "source_clusters": 4,
    }
    for key, expected in required_counts.items():
        if counts[key] < expected:
            errors.append(f"{key} below required minimum")
    for key in (
        "decision_flips",
        "invariant_pairs",
        "reference_tasks_with_alternative_sets",
        "distinct_out_of_scope_fact_ids",
    ):
        if counts[key] < 2:
            errors.append(f"{key} below required minimum")
    if counts["decision_flips"] + counts["invariant_pairs"] != counts[
        "paired_cases"
    ]:
        errors.append("decision flip/invariant accounting does not sum")
    if counts["invariant_decision_minimal_set_change_pairs"] < 1:
        errors.append(
            "no invariant-decision pair changes its minimal sufficient set"
        )

    dispositions = result["contract_probe"]["dispositions_by_case"]
    if dispositions != EXPECTED_DISPOSITIONS:
        errors.append(f"contract dispositions differ: {dispositions}")
    probe_by_id = {
        probe_case["probe_case_id"]: probe_case
        for probe_case in fixture["probe_cases"]
    }
    for probe_case in fixture["probe_cases"]:
        if "decision" in probe_case or "minimal_sufficient_sets" in probe_case:
            errors.append("contract fixture contains reference answer fields")
    extra_probe = probe_by_id.get("OUT_OF_SCOPE_ADDITION", {})
    clean_probe = probe_by_id.get("OUT_OF_SCOPE_COUNTERFACTUAL", {})
    if not extra_probe or not clean_probe:
        errors.append("single-factor scope fixture or counterfactual is missing")
    else:
        extra_selected = set(extra_probe["selected_evidence_ids"])
        clean_selected = set(clean_probe["selected_evidence_ids"])
        removed_fact_ids = extra_selected - clean_selected
        if clean_selected - extra_selected:
            errors.append("scope counterfactual adds facts rather than removing one")
        if len(removed_fact_ids) != 1:
            errors.append("scope fixture is not single-factor")
        extra_reference = next(
            reference
            for reference in references
            if reference["task_id"] == extra_probe["source_task_id"]
        )
        if removed_fact_ids - set(extra_reference["out_of_scope_evidence_ids"]):
            errors.append("scope fixture removes an in-scope fact")
        for probe_case in (extra_probe, clean_probe):
            if probe_case["submitted_outcome"] != extra_reference["decision"]["outcome"]:
                errors.append("scope fixture does not submit the derived outcome")
            if not any(
                set(minimal_set).issubset(probe_case["selected_evidence_ids"])
                for minimal_set in extra_reference["minimal_sufficient_sets"]
            ):
                errors.append("scope fixture selection is insufficient")
    diagnostic_codes = result["contract_probe"][
        "diagnostic_reason_codes_by_case"
    ]
    expected_diagnostic_codes = {
        "OUT_OF_SCOPE_ADDITION": ["SCOPE_IMURITY"],
        "OUT_OF_SCOPE_COUNTERFACTUAL": [],
    }
    for probe_case_id, expected_codes in expected_diagnostic_codes.items():
        actual_codes = diagnostic_codes.get(probe_case_id, {}).get("composite")
        if actual_codes != expected_codes:
            errors.append(
                f"{probe_case_id} diagnostic reason codes differ: {actual_codes}"
            )

    for stage, metrics in result["baseline"]["by_stage"].items():
        for metric in (
            "plan_sufficient_rate",
            "plan_precision_mean",
            "answer_coverage_rate",
            "composite_acceptance_rate",
        ):
            raw_value = metrics[metric]
            value = float(raw_value) if metric == "plan_precision_mean" else raw_value
            if not 0.0 < value < 1.0:
                errors.append(
                    f"baseline {stage} {metric} is terminal: {raw_value}"
                )
        precision_mean = metrics["plan_precision_mean"]
        if not isinstance(precision_mean, str) or len(
            precision_mean.partition(".")[2]
        ) != 12:
            errors.append(f"baseline {stage} precision mean is not fixed-decimal")
        reconstructed = Fraction(
            metrics["plan_precision_numerator"],
            metrics["plan_precision_denominator"],
        )
        if precision_mean != fixed_decimal(reconstructed):
            errors.append(f"baseline {stage} precision mean is not reproducible")
    if not result["headroom"]["deterministic_nonzero_headroom"]:
        errors.append("deterministic headroom is not nonzero")
    if result["headroom"]["stop_recommendation"] != "STOP_BEFORE_REAL_MODEL":
        errors.append("stop recommendation changed")

    accounting_surfaces = {
        "input_manifest": manifest["request_accounting"],
        "probe_result": result["request_accounting"],
        "probe_freeze": freeze_manifest["request_accounting"],
        "probe_run": run_manifest["request_accounting"],
    }
    for surface, accounting in accounting_surfaces.items():
        if accounting != REQUEST_ACCOUNTING:
            errors.append(f"{surface} accounting schema differs")
        for key, value in accounting.items():
            _zero(value, f"{surface}.{key}", errors)

    prohibited_source_keys = {
        "gold",
        "minimal_sufficient_sets",
        "canonical_sufficient_set",
        "reference_decision",
    }

    def contains_key(payload: Any, key: str) -> bool:
        if isinstance(payload, dict):
            return key in payload or any(
                contains_key(value, key) for value in payload.values()
            )
        if isinstance(payload, list):
            return any(contains_key(value, key) for value in payload)
        return False

    for key in prohibited_source_keys:
        if contains_key(source_cases, key):
            errors.append(f"source cases contain per-case key: {key}")
    if contains_key(source_policy, "case_id"):
        errors.append("policy contains per-case identifiers")

    verification = {
        "baseline_by_stage": result["baseline"]["by_stage"],
        "baseline_overall": result["baseline"]["overall"],
        "contract_dispositions": dispositions,
        "counts": counts,
        "evidence_identity": EVIDENCE_IDENTITY,
        "exact_commands": EXACT_COMMANDS,
        "file_hashes": {
            "v1_frozen_inputs_and_results": {
                path.name: sha256_file(path) for path in V1_FROZEN_FILES
            },
            "v2_inputs_and_results": {
                **{
                    entry["path"]: entry["sha256"]
                    for entry in manifest["canonical_input_files"]
                },
                **{
                    entry["path"]: entry["sha256"]
                    for entry in freeze_manifest["frozen_files"]
                },
                INPUT_MANIFEST_PATH.name: sha256_file(INPUT_MANIFEST_PATH),
                PROBE_FREEZE_MANIFEST_PATH.name: sha256_file(
                    PROBE_FREEZE_MANIFEST_PATH
                ),
                PROBE_RUN_MANIFEST_PATH.name: sha256_file(
                    PROBE_RUN_MANIFEST_PATH
                ),
            },
        },
        "headroom": result["headroom"],
        "request_accounting": dict(REQUEST_ACCOUNTING),
        "runtime": runtime,
        "status": "PASS" if not errors else "FAIL",
        "task_id": TASK_ID,
        "provenance": {
            "launcher_ids_recorded_only_in_run_manifest": True,
            "package": PACKAGE_NAME,
        },
        "verification_errors": errors,
        "verification_schema": "condition_change_machine_verification_v2",
    }
    return verification


def main() -> None:
    verification = verify()
    write_json(MACHINE_VERIFICATION_PATH, verification)
    print(canonical_json_text(verification), end="")
    if verification["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
