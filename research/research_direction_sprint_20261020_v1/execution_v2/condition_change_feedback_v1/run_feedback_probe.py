#!/usr/bin/env python3
"""Run the deterministic baseline and three frozen feedback contracts."""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from fractions import Fraction
from typing import Any

from condition_change_common import (
    ACTOR_TASKS_PATH,
    PACKAGE_DIR,
    EVIDENCE_IDENTITY,
    FACTS_PATH,
    INPUT_MANIFEST_PATH,
    POLICY_PATH,
    PROBE_FIXTURES_PATH,
    PROBE_FREEZE_MANIFEST_PATH,
    PROBE_RUN_MANIFEST_PATH,
    PROBE_RESULTS_PATH,
    PROBE_SUMMARY_PATH,
    REFERENCE_TASKS_PATH,
    REQUEST_ACCOUNTING,
    canonical_json_text,
    load_json,
    sha256_bytes,
    sha256_file,
    validate_against_definition,
    write_json,
)


CONTRACTS = ("exact_match", "sufficiency_only", "composite")
FIXED_DECIMAL_PLACES = 12


def launcher_ids_from_task_prompts() -> dict[str, str]:
    prompt_names = {
        "implementation": "CONDITION_CHANGE_LOOP_A_PROMPT.md",
        "fix": "CONDITION_CHANGE_FIX_A_PROMPT.md",
    }
    launcher_ids = {}
    for key, prompt_name in prompt_names.items():
        prompt_path = PACKAGE_DIR.parent / "gb10_loop_prompts" / prompt_name
        match = re.search(
            r"Task ID: `([^`]+)`",
            prompt_path.read_text(encoding="utf-8"),
        )
        if not match:
            raise ValueError(f"missing Task ID in {prompt_path.name}")
        launcher_ids[key] = match.group(1)
    return launcher_ids


def fixed_decimal(value: Fraction, places: int = FIXED_DECIMAL_PLACES) -> str:
    scaled_numerator = value.numerator * 10**places
    quotient, remainder = divmod(scaled_numerator, value.denominator)
    if remainder * 2 >= value.denominator:
        quotient += 1
    integer_part, fractional_part = divmod(quotient, 10**places)
    return f"{integer_part}.{fractional_part:0{places}d}"


def deterministic_baseline(actor_task: dict[str, Any]) -> dict[str, Any]:
    prior = actor_task["observation"]["prior_experience"]
    return {
        "outcome": prior["baseline_submitted_outcome"],
        "selected_evidence_ids": list(prior["plan_evidence_ids"]),
    }


def contains_sufficient_set(
    selected_evidence_ids: list[str],
    minimal_sufficient_sets: list[list[str]],
) -> bool:
    selected = set(selected_evidence_ids)
    return any(
        set(minimal_set).issubset(selected)
        for minimal_set in minimal_sufficient_sets
    )


def scope_precision_components(
    selected_evidence_ids: list[str],
    reference: dict[str, Any],
) -> tuple[int, int]:
    selected = set(selected_evidence_ids)
    in_scope = set(reference["in_scope_evidence_ids"])
    return len(selected & in_scope), len(selected)


def diagnostic_reason_codes(
    selected_evidence_ids: list[str],
    submitted_outcome: str,
    sufficient: bool,
    reference: dict[str, Any],
) -> list[str]:
    selected = set(selected_evidence_ids)
    in_scope = set(reference["in_scope_evidence_ids"])
    answer_mismatch = submitted_outcome != reference["decision"]["outcome"]
    scope_impurity = not selected.issubset(in_scope)
    in_scope_over_selection = sufficient and any(
        set(minimal_set).issubset(selected) and selected & in_scope != set(minimal_set)
        for minimal_set in reference["minimal_sufficient_sets"]
    )
    reason_codes = []
    if answer_mismatch:
        reason_codes.append("ANSWER_MISMATCH")
    if not sufficient:
        reason_codes.append("INSUFFICIENT_PLAN")
    if scope_impurity:
        reason_codes.append("SCOPE_IMURITY")
    if in_scope_over_selection:
        reason_codes.append("IN_SCOPE_OVER_SELECTION")
    return reason_codes


def feedback_disposition(
    contract: str,
    selected_evidence_ids: list[str],
    submitted_outcome: str,
    reference: dict[str, Any],
) -> dict[str, Any]:
    sufficient = contains_sufficient_set(
        selected_evidence_ids,
        reference["minimal_sufficient_sets"],
    )
    precision_numerator, precision_denominator = scope_precision_components(
        selected_evidence_ids, reference
    )
    precision = Fraction(precision_numerator, precision_denominator)
    answer_covered = submitted_outcome == reference["decision"]["outcome"]
    canonical_match = set(selected_evidence_ids) == set(
        reference["canonical_sufficient_set"]
    )
    if contract == "exact_match":
        accepted = canonical_match and answer_covered
        contract_reason_code = (
            "ANSWER_MISMATCH"
            if not answer_covered
            else "CANONICAL_SET_MISMATCH"
            if not canonical_match
            else "EXACT_MATCH_RETAINED"
        )
    elif contract == "sufficiency_only":
        accepted = sufficient
        contract_reason_code = (
            "SUFFICIENT_SET_RETAINED"
            if accepted
            else "INSUFFICIENT_PLAN"
        )
    elif contract == "composite":
        accepted = sufficient and precision == 1 and answer_covered
        if not sufficient:
            contract_reason_code = "INSUFFICIENT_PLAN"
        elif precision < 1:
            contract_reason_code = "SCOPE_PRECISION_FAILED"
        elif not answer_covered:
            contract_reason_code = "ANSWER_MISMATCH"
        else:
            contract_reason_code = "COMPOSITE_CONTRACT_SATISFIED"
    else:
        raise ValueError(f"unknown feedback contract: {contract}")
    result = {
        "accepted": accepted,
        "answer_coverage": answer_covered,
        "contract": contract,
        "contract_reason_code": contract_reason_code,
        "plan_precision": fixed_decimal(precision),
        "plan_precision_denominator": precision_denominator,
        "plan_precision_numerator": precision_numerator,
        "plan_sufficient": sufficient,
        "reason_codes": diagnostic_reason_codes(
            selected_evidence_ids,
            submitted_outcome,
            sufficient,
            reference,
        ),
    }
    validate_against_definition(result, "feedback_result")
    return result


def _baseline_rows(
    actor_tasks: list[dict[str, Any]],
    references_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for actor_task in actor_tasks:
        reference = references_by_id[actor_task["task_id"]]
        plan = deterministic_baseline(actor_task)
        dispositions = {
            contract: feedback_disposition(
                contract,
                plan["selected_evidence_ids"],
                plan["outcome"],
                reference,
            )
            for contract in CONTRACTS
        }
        composite = dispositions["composite"]
        rows.append(
            {
                "actor_input_only": {
                    "outcome": plan["outcome"],
                    "selected_evidence_ids": plan["selected_evidence_ids"],
                },
                "answer_covered": composite["answer_coverage"],
                "case_id": actor_task["case_id"],
                "composite_accepted": composite["accepted"],
                "plan_precision": composite["plan_precision"],
                "plan_precision_denominator": composite[
                    "plan_precision_denominator"
                ],
                "plan_precision_numerator": composite["plan_precision_numerator"],
                "plan_sufficient": composite["plan_sufficient"],
                "reference_outcome": reference["decision"]["outcome"],
                "source_cluster": actor_task["source_cluster"],
                "stage": actor_task["stage"],
                "task_id": actor_task["task_id"],
            }
        )
    return rows


def _metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(rows)
    sufficient_count = sum(row["plan_sufficient"] for row in rows)
    answer_count = sum(row["answer_covered"] for row in rows)
    accepted_count = sum(row["composite_accepted"] for row in rows)
    precision_sum = sum(
        (
            Fraction(
                row["plan_precision_numerator"],
                row["plan_precision_denominator"],
            )
            for row in rows
        ),
        Fraction(0, 1),
    )
    precision_mean = precision_sum / count
    return {
        "answer_covered_count": answer_count,
        "answer_coverage_rate": answer_count / count,
        "composite_accepted_count": accepted_count,
        "composite_acceptance_rate": accepted_count / count,
        "plan_precision_denominator": precision_mean.denominator,
        "plan_precision_mean": fixed_decimal(precision_mean),
        "plan_precision_numerator": precision_mean.numerator,
        "plan_sufficient_count": sufficient_count,
        "plan_sufficient_rate": sufficient_count / count,
        "tasks": count,
    }


def _contract_probe_rows(
    fixture: dict[str, Any],
    references_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for probe_case in fixture["probe_cases"]:
        reference = references_by_id[probe_case["source_task_id"]]
        dispositions = {
            contract: feedback_disposition(
                contract,
                probe_case["selected_evidence_ids"],
                probe_case["submitted_outcome"],
                reference,
            )
            for contract in CONTRACTS
        }
        rows.append(
            {
                "actor_input_only": {
                    "outcome": probe_case["submitted_outcome"],
                    "selected_evidence_ids": probe_case["selected_evidence_ids"],
                    "source_task_id": probe_case["source_task_id"],
                },
                "contracts": dispositions,
                "derived_reference": {
                    "canonical_sufficient_set": reference["canonical_sufficient_set"],
                    "decision": reference["decision"],
                    "minimal_sufficient_sets": reference["minimal_sufficient_sets"],
                    "out_of_scope_evidence_ids": reference[
                        "out_of_scope_evidence_ids"
                    ],
                },
                "probe_case_id": probe_case["probe_case_id"],
            }
        )
    return rows


def build_probe_result() -> dict[str, Any]:
    manifest = load_json(INPUT_MANIFEST_PATH)
    for entry in manifest["canonical_input_files"]:
        path = INPUT_MANIFEST_PATH.parent / entry["path"]
        if sha256_file(path) != entry["sha256"]:
            raise ValueError(f"frozen input hash mismatch: {entry['path']}")
    policy = load_json(POLICY_PATH)
    actor_tasks = load_json(ACTOR_TASKS_PATH)["tasks"]
    facts = load_json(FACTS_PATH)
    references = load_json(REFERENCE_TASKS_PATH)["references"]
    fixture = load_json(PROBE_FIXTURES_PATH)
    references_by_id = {reference["task_id"]: reference for reference in references}
    if set(actor_task["task_id"] for actor_task in actor_tasks) != set(references_by_id):
        raise ValueError("actor/reference task IDs differ")

    baseline_rows = _baseline_rows(actor_tasks, references_by_id)
    by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in baseline_rows:
        by_stage[row["stage"]].append(row)
    overall_metrics = _metrics(baseline_rows)
    pair_outcomes: dict[str, dict[str, str]] = defaultdict(dict)
    for reference in references:
        pair_outcomes[reference["case_id"]][reference["stage"]] = (
            reference["decision"]["outcome"]
        )
    decision_flips = sum(
        outcomes["pre"] != outcomes["post"]
        for outcomes in pair_outcomes.values()
    )
    references_by_case: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for reference in references:
        references_by_case[reference["case_id"]][reference["stage"]] = reference
    invariant_minimal_set_change_pairs = sum(
        pre["decision"]["outcome"] == post["decision"]["outcome"]
        and pre["minimal_sufficient_sets"] != post["minimal_sufficient_sets"]
        for pre, post in (
            (stage_references["pre"], stage_references["post"])
            for stage_references in references_by_case.values()
        )
    )
    out_of_scope_fact_ids = sorted(
        {
            fact_id
            for reference in references
            for fact_id in reference["out_of_scope_evidence_ids"]
        }
    )
    probe_rows = _contract_probe_rows(fixture, references_by_id)
    headroom = 1.0 - overall_metrics["composite_acceptance_rate"]
    return {
        "baseline": {
            "by_stage": {
                stage: _metrics(stage_rows)
                for stage, stage_rows in sorted(by_stage.items())
            },
            "description": (
                "Frozen historical heuristic: submit approve and retain the "
                "prior plan evidence IDs without reading policy or references."
            ),
            "name": "frozen_historical_prior_plan_v1",
            "overall": overall_metrics,
            "rows": baseline_rows,
        },
        "contract_probe": {
            "contracts": list(CONTRACTS),
            "dispositions_by_case": {
                row["probe_case_id"]: {
                    contract: (
                        "RETAIN"
                        if row["contracts"][contract]["accepted"]
                        else "REVISE"
                    )
                    for contract in CONTRACTS
                }
                for row in probe_rows
            },
            "contract_reason_codes_by_case": {
                row["probe_case_id"]: {
                    contract: row["contracts"][contract]["contract_reason_code"]
                    for contract in CONTRACTS
                }
                for row in probe_rows
            },
            "diagnostic_reason_codes_by_case": {
                row["probe_case_id"]: {
                    contract: row["contracts"][contract]["reason_codes"]
                    for contract in CONTRACTS
                }
                for row in probe_rows
            },
            "rows": probe_rows,
        },
        "evidence_identity": EVIDENCE_IDENTITY,
        "headroom": {
            "baseline_composite_rejections": len(baseline_rows)
            - overall_metrics["composite_accepted_count"],
            "baseline_composite_rejection_rate": headroom,
            "deterministic_nonzero_headroom": 0.0 < headroom < 1.0,
            "real_model_phase_authorized": False,
            "stop_recommendation": "STOP_BEFORE_REAL_MODEL",
        },
        "reference_counts": {
            "actor_tasks": len(actor_tasks),
            "decision_flips": decision_flips,
            "distinct_out_of_scope_fact_ids": len(out_of_scope_fact_ids),
            "evidence_facts": len(facts),
            "invariant_pairs": len(pair_outcomes) - decision_flips,
            "invariant_decision_minimal_set_change_pairs": (
                invariant_minimal_set_change_pairs
            ),
            "paired_cases": len(pair_outcomes),
            "reference_tasks_with_alternative_sets": sum(
                len(reference["minimal_sufficient_sets"]) > 1
                for reference in references
            ),
            "source_clusters": len(
                {actor_task["source_cluster"] for actor_task in actor_tasks}
            ),
        },
        "request_accounting": dict(REQUEST_ACCOUNTING),
        "result_schema": "condition_change_feedback_probe_result_v2",
        "task_id": manifest["task_id"],
    }


def _summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "baseline_by_stage": result["baseline"]["by_stage"],
        "baseline_overall": result["baseline"]["overall"],
        "contract_dispositions": result["contract_probe"][
            "dispositions_by_case"
        ],
        "diagnostic_reason_codes": result["contract_probe"][
            "diagnostic_reason_codes_by_case"
        ],
        "headroom": result["headroom"],
        "reference_counts": result["reference_counts"],
        "request_accounting": result["request_accounting"],
        "summary_schema": "condition_change_feedback_probe_summary_v2",
    }


def freeze_probe() -> dict[str, Any]:
    result = build_probe_result()
    write_json(PROBE_RESULTS_PATH, result)
    summary = _summary(result)
    write_json(PROBE_SUMMARY_PATH, summary)
    manifest = {
        "frozen_files": [
            {"path": path.name, "sha256": sha256_file(path)}
            for path in (PROBE_RESULTS_PATH, PROBE_SUMMARY_PATH)
        ],
        "manifest_schema": "condition_change_probe_freeze_manifest_v2",
        "request_accounting": dict(REQUEST_ACCOUNTING),
        "status": "FROZEN",
    }
    write_json(PROBE_FREEZE_MANIFEST_PATH, manifest)
    return summary


def run_probe() -> dict[str, Any]:
    frozen = load_json(PROBE_RESULTS_PATH)
    recomputed = build_probe_result()
    status = "MATCH" if canonical_json_text(recomputed) == canonical_json_text(frozen) else "MISMATCH"
    if status != "MATCH":
        raise ValueError("recomputed probe result differs from the frozen result")
    run_manifest = {
        "frozen_result_sha256": sha256_file(PROBE_RESULTS_PATH),
        "launcher_ids": launcher_ids_from_task_prompts(),
        "manifest_schema": "condition_change_probe_run_manifest_v2",
        "recomputed_result_sha256": sha256_bytes(
            canonical_json_text(recomputed).encode("utf-8")
        ),
        "request_accounting": dict(REQUEST_ACCOUNTING),
        "status": status,
    }
    write_json(PROBE_RUN_MANIFEST_PATH, run_manifest)
    return run_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--freeze", action="store_true")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args()
    payload = freeze_probe() if args.freeze else run_probe()
    print(canonical_json_text(payload), end="")


if __name__ == "__main__":
    main()
