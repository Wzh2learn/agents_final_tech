#!/usr/bin/env python3
"""Freeze the C3 scorer/output-contract repair bundle for B0 V4."""

from __future__ import annotations

import json

from finrank_contract import (
    PACKAGE,
    load_object,
    sha256_file,
    write_json,
)


def main() -> int:
    red = load_object(PACKAGE / "C3_UNIT_RED.json")
    green = load_object(PACKAGE / "C3_UNIT_GREEN.json")
    derivation_red = load_object(PACKAGE / "C3_DERIVATION_RED.json")
    derivation_green = load_object(
        PACKAGE / "C3_DERIVATION_GREEN.json"
    )
    posthoc = load_object(
        PACKAGE
        / "results"
        / "B0_V3_EQUAL_VISIBILITY"
        / "B0_RESULT_POSTHOC_SCORER_V2.json"
    )
    if red["phase"] != "red" or red["observed_match"] is not False:
        raise RuntimeError("unit_red_receipt_invalid")
    if green["phase"] != "green" or green["observed_match"] is not True:
        raise RuntimeError("unit_green_receipt_invalid")
    if (
        derivation_red["phase"] != "red"
        or derivation_red["observed"]["false_pair_consistent"] is not True
    ):
        raise RuntimeError("derivation_red_receipt_invalid")
    if (
        derivation_green["phase"] != "green"
        or derivation_green["observed"]["false_pair_consistent"] is not False
        or derivation_green["observed"]["explicit_derivation_consistent"]
        is not True
    ):
        raise RuntimeError("derivation_green_receipt_invalid")
    if posthoc["original_frozen"]["success_count"] != 4:
        raise RuntimeError("v3_original_score_drift")
    if posthoc["posthoc"]["success_count"] != 5:
        raise RuntimeError("v3_posthoc_score_drift")
    if posthoc["preserved_non_successes"]["ESD_006"]["outcome"] != "NON_SUCCESS":
        raise RuntimeError("ESD_006_boundary_drift")

    actor_v2 = load_object(PACKAGE / "TASKS_ACTOR_V2.json")
    actor_v3 = {
        **actor_v2,
        "schema": "finrank_actor_tasks_v3",
        "estimand": {
            "name": "COMPLETE_CANDIDATE_SELECTION_AND_CONSUMPTION",
            "plan_time_visibility": "FULL_VISIBLE_CANDIDATES_AT_PLAN",
            "limit": (
                "Measures selection and consumption from a complete visible "
                "candidate set; not active evidence acquisition and not a V2 "
                "experiment reproduction."
            ),
        },
    }
    write_json(PACKAGE / "TASKS_ACTOR_V3.json", actor_v3)

    ref_v2 = load_object(PACKAGE / "REFERENCES_V2.json")
    ref_v3_tasks = []
    for task in ref_v2["tasks"]:
        updated = dict(task)
        updated["derivations"] = []
        if task["task_id"] == "ESD_006":
            updated["derivations"] = [
                {
                    "target_atom": "derived_gross_profit",
                    "operand_atoms": [
                        "automotive_revenue",
                        "automotive_other_cost",
                    ],
                    "operand_values": {
                        "automotive_revenue": 171606,
                        "automotive_other_cost": 151065,
                    },
                    "operator": "SUBTRACT",
                    "formula": (
                        "automotive_revenue - automotive_other_cost"
                    ),
                },
                {
                    "target_atom": "derived_gross_margin",
                    "operand_atoms": [
                        "automotive_revenue",
                        "automotive_other_cost",
                    ],
                    "operand_values": {
                        "automotive_revenue": 171606,
                        "automotive_other_cost": 151065,
                    },
                    "operator": "MARGIN_PERCENT_FROM_REVENUE_AND_COST",
                    "formula": (
                        "(automotive_revenue - automotive_other_cost) / "
                        "automotive_revenue * 100"
                    ),
                },
            ]
        ref_v3_tasks.append(updated)
    ref_v3 = {
        **ref_v2,
        "schema": "finrank_evaluation_references_v3",
        "source_reference_v2_sha256": sha256_file(
            PACKAGE / "REFERENCES_V2.json"
        ),
        "change_scope": "EXPLICIT_DERIVATION_CHECKS_ONLY",
        "tasks": ref_v3_tasks,
    }
    write_json(PACKAGE / "REFERENCES_V3.json", ref_v3)

    run_card = {
        "schema": "finrank_c3_run_card_b0_v4_v1",
        "status": "FROZEN_BEFORE_C3_FIXTURES",
        "owner_authorization": (
            "C3 targeted scorer and output-contract correction delegated by "
            "Loop D; one complete B0 V4 only."
        ),
        "root_causes": [
            "C2_ROOT_CAUSE.md",
            "C3_CORRECTION_SPEC.md",
        ],
        "plan_time_visibility": {
            "policy": "FULL_VISIBLE_CANDIDATES_AT_PLAN",
            "unchanged_from_c2": True,
        },
        "reference_version": {
            "path": "REFERENCES_V3.json",
            "answer_scope_unchanged_from_v2": True,
            "change_scope": "EXPLICIT_DERIVATION_CHECKS_ONLY",
        },
        "estimand": actor_v3["estimand"],
        "scorer_change": {
            "scope": "LITERAL_PERCENT_UNIT_ALIAS_ONLY",
            "red_receipt": "C3_UNIT_RED.json",
            "green_receipt": "C3_UNIT_GREEN.json",
            "v3_posthoc_rescore": (
                "results/B0_V3_EQUAL_VISIBILITY/"
                "B0_RESULT_POSTHOC_SCORER_V2.json"
            ),
            "derivation_red_receipt": "C3_DERIVATION_RED.json",
            "derivation_green_receipt": "C3_DERIVATION_GREEN.json",
            "derivation_policy": (
                "Literal evidence for ordinary facts; reference V3 explicit "
                "target/operand/operator/formula for derived facts."
            ),
        },
        "output_contract_change": {
            "schema_changed": False,
            "model_changed": False,
            "generation_parameters_changed": False,
            "max_tokens": 256,
            "prompt_constraint": (
                "Minified JSON only, no whitespace outside string values, no "
                "pretty-printing, indentation, Markdown fences, or commentary."
            ),
        },
        "b0": {
            "run_name": "B0_V4_MINIFIED_JSON",
            "tasks": [
                "ESD_001",
                "ESD_002",
                "ESD_003",
                "ESD_004",
                "ESD_006",
                "ESD_010",
                "ESD_012",
            ],
            "task_order_unchanged": True,
            "stages_per_task": ["plan", "consume"],
            "planned_generation_requests": 14,
            "generation_request_cap": 14,
            "retry_cap": 0,
            "concurrency": 1,
            "expected_prior_requests": 42,
            "expected_total_requests_after": 56,
        },
        "boundaries": {
            "history_collection": 0,
            "pilot": 0,
            "judge_calls": 0,
            "training_calls": 0,
            "production_memory_writes": 0,
            "ESD_006_UNKNOWN_must_remain_non_success": True,
            "ESD_012_raw_repair": False,
        },
    }
    write_json(PACKAGE / "RUN_CARD_C3_B0_V4.json", run_card)

    source_inputs = {
        "C2_ROOT_CAUSE.md": sha256_file(PACKAGE / "C2_ROOT_CAUSE.md"),
        "C3_CORRECTION_SPEC.md": sha256_file(
            PACKAGE / "C3_CORRECTION_SPEC.md"
        ),
        "BUNDLE_C2_B0_V3.json": sha256_file(
            PACKAGE / "BUNDLE_C2_B0_V3.json"
        ),
        "B0_V3_RESULT.json": sha256_file(
            PACKAGE
            / "results"
            / "B0_V3_EQUAL_VISIBILITY"
            / "B0_RESULT.json"
        ),
        "B0_V3_POSTHOC_SCORER_V2.json": sha256_file(
            PACKAGE
            / "results"
            / "B0_V3_EQUAL_VISIBILITY"
            / "B0_RESULT_POSTHOC_SCORER_V2.json"
        ),
        "C3_UNIT_RED.json": sha256_file(PACKAGE / "C3_UNIT_RED.json"),
        "C3_UNIT_GREEN.json": sha256_file(PACKAGE / "C3_UNIT_GREEN.json"),
        "C3_DERIVATION_RED.json": sha256_file(
            PACKAGE / "C3_DERIVATION_RED.json"
        ),
        "C3_DERIVATION_GREEN.json": sha256_file(
            PACKAGE / "C3_DERIVATION_GREEN.json"
        ),
        "REFERENCES_V1.json": sha256_file(PACKAGE / "REFERENCES_V1.json"),
        "REFERENCES_V2.json": sha256_file(PACKAGE / "REFERENCES_V2.json"),
    }
    artifacts = {}
    for name in (
        "finrank_contract.py",
        "freeze_c3_bundle.py",
        "qualify_runtime.py",
        "run_fixtures.py",
        "run_b0.py",
        "run_strong_rule.py",
        "rescore_b0_v3_posthoc.py",
        "rescore_b0_v3_posthoc_v3.py",
        "c3_red_green_unit_fixture.py",
        "c3_red_green_derivation_fixture.py",
        "TASKS_ACTOR_V3.json",
        "REFERENCES_V3.json",
        "TOOL_SCHEMAS_V1.json",
        "RUNTIME_IDENTITY_OVERRIDE_V1.json",
        "RUN_CARD_C3_B0_V4.json",
    ):
        artifacts[name] = sha256_file(PACKAGE / name)
    bundle = {
        "schema": "finrank_c3_b0_v4_bundle_v1",
        "status": "FROZEN_BEFORE_C3_FIXTURES",
        "source_inputs": source_inputs,
        "artifacts": artifacts,
    }
    write_json(PACKAGE / "BUNDLE_C3_B0_V4.json", bundle)
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "bundle_sha256": sha256_file(
                    PACKAGE / "BUNDLE_C3_B0_V4.json"
                ),
                "artifacts": len(artifacts),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
