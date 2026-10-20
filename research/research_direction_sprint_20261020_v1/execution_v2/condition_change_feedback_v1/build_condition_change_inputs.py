#!/usr/bin/env python3
"""Freeze declarative inputs, actor views, probe proposals, and references."""

from __future__ import annotations

import argparse
import platform
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from condition_change_common import (
    ACTOR_TASKS_PATH,
    EVIDENCE_IDENTITY,
    FACTS_PATH,
    INPUT_MANIFEST_PATH,
    PACKAGE_NAME,
    POLICY_PATH,
    PROBE_FIXTURES_PATH,
    REVISION_SOURCE_PATH,
    REFERENCE_TASKS_PATH,
    REQUEST_ACCOUNTING,
    SCHEMA_V1_PATH,
    SCHEMA_PATH,
    SOURCE_CASES_V2_PATH,
    SOURCE_CASES_PATH,
    SOURCE_POLICY_V2_PATH,
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


SOURCE_CLUSTERS = {"conference", "meals", "travel", "office", "lodging"}
STAGES = (
    ("pre", "expense_policy_pre_v1"),
    ("post", "expense_policy_post_v1"),
)


def _claim_fact(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "claim": case["claim"],
        "details": case["claim"],
        "fact_id": f"{case['case_id']}:claim",
        "kind": "claim",
        "source_id": f"claim_register:{case['case_id']}",
        "source_cluster": case["source_cluster"],
        "valid": True,
    }


def _case_facts(case: dict[str, Any]) -> list[dict[str, Any]]:
    facts = [_claim_fact(case)]
    for source_fact in case["evidence"]:
        fact = {
            **source_fact,
            "case_id": case["case_id"],
            "source_cluster": case["source_cluster"],
        }
        validate_against_definition(fact, "evidence_fact")
        facts.append(fact)
    validate_against_definition(facts[0], "evidence_fact")
    return facts


def _actor_task(
    policy: dict[str, Any],
    case: dict[str, Any],
    stage: str,
    policy_version_id: str,
) -> dict[str, Any]:
    inventory = [
        {
            "fact_id": fact["fact_id"],
            "kind": fact["kind"],
            "valid": fact["valid"],
        }
        for fact in case["evidence"]
    ]
    task = {
        "actor_input_only": True,
        "case_id": case["case_id"],
        "policy_context": {
            "applicable_policy_text": canonical_json_text(
                {
                    "decision_rules": policy["policy_versions"][policy_version_id][
                        "decision_rules"
                    ],
                    "decision_semantics": policy["decision_semantics"],
                    "in_scope_fact_kinds": policy["in_scope_fact_kinds"],
                }
            ),
            "explicit_policy_delta_text": policy["actor_policy_delta"][
                policy_version_id
            ],
            "policy_version_id": policy_version_id,
        },
        "observation": {
            "claim": case["claim"],
            "evidence_inventory": inventory,
            "prior_experience": {
                "baseline_submitted_outcome": "approve",
                "plan_evidence_ids": case["prior_plan_evidence_ids"],
            },
        },
        "policy_version_id": policy_version_id,
        "source_cluster": case["source_cluster"],
        "stage": stage,
        "task_id": f"{case['case_id']}:{stage}",
    }
    validate_against_definition(task, "actor_task")
    return task


def _validate_source_inputs(policy: dict[str, Any], cases: list[dict[str, Any]]) -> None:
    if policy["evidence_identity"] != EVIDENCE_IDENTITY:
        raise ValueError("policy evidence identity does not match the sprint contract")
    if set(policy["policy_versions"]) != {version_id for _, version_id in STAGES}:
        raise ValueError("policy does not contain the two frozen policy versions")
    if len(cases) != 13:
        raise ValueError("the V2 population must contain exactly 13 paired cases")
    case_ids = [case["case_id"] for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("duplicate source case_id")
    for case in cases:
        if case["source_cluster"] not in SOURCE_CLUSTERS:
            raise ValueError(f"unknown source cluster: {case['source_cluster']}")
        fact_ids = [fact["fact_id"] for fact in case["evidence"]]
        if len(fact_ids) != len(set(fact_ids)):
            raise ValueError(f"duplicate evidence fact_id in {case['case_id']}")
        unknown_prior = set(case["prior_plan_evidence_ids"]) - set(fact_ids)
        if unknown_prior:
            raise ValueError(f"unknown prior-plan fact in {case['case_id']}")


def _apply_v2_revision(
    policy: dict[str, Any], cases: list[dict[str, Any]], revision: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    policy_v2 = deepcopy(policy)
    cases_v2 = deepcopy(cases)
    delta = revision["policy_delta"]
    post_rules = policy_v2["policy_versions"]["expense_policy_post_v1"][
        "decision_rules"
    ]
    insert_index = next(
        index
        for index, rule in enumerate(post_rules)
        if rule["id"] == delta["insert_before_rule_id"]
    )
    post_rules.insert(insert_index, delta["rule"])
    policy_v2["schema_version"] = "condition_change_policy_v2"
    policy_v2["change_description"] = (
        f"{policy_v2['change_description']} {delta['change_text']}"
    )
    policy_v2["actor_policy_delta"] = {
        "expense_policy_pre_v1": (
            "Applicable baseline text; no condition-change delta applies."
        ),
        "expense_policy_post_v1": delta["change_text"],
    }
    cases_v2.append(deepcopy(revision["appended_case"]))
    return policy_v2, cases_v2


def _write_schema_v2() -> None:
    schema = deepcopy(load_json(SCHEMA_V1_PATH))
    schema["$id"] = "condition_change_task_tool_schema_v2"
    schema["properties"]["schema_version"]["const"] = (
        "condition_change_task_tool_schema_v2"
    )
    schema["title"] = "Condition Change Feedback V2 Strict Task and Tool Schema"
    actor = schema["$defs"]["actor_task"]
    for property_name in ("category", "source_cluster"):
        property_schema = actor["properties"]
        if property_name == "category":
            property_schema = property_schema["observation"]["properties"]["claim"][
                "properties"
            ]
        property_schema[property_name]["enum"].append("conference")
        property_schema[property_name]["enum"].sort()
    actor["properties"]["policy_context"] = {
        "additionalProperties": False,
        "properties": {
            "applicable_policy_text": {"minLength": 1, "type": "string"},
            "explicit_policy_delta_text": {"minLength": 1, "type": "string"},
            "policy_version_id": {
                "enum": ["expense_policy_pre_v1", "expense_policy_post_v1"],
                "type": "string",
            },
        },
        "required": [
            "policy_version_id",
            "applicable_policy_text",
            "explicit_policy_delta_text",
        ],
        "type": "object",
    }
    actor["required"].append("policy_context")
    fact = schema["$defs"]["evidence_fact"]
    fact["properties"]["source_cluster"]["enum"].append("conference")
    fact["properties"]["source_cluster"]["enum"].sort()
    feedback = schema["$defs"]["feedback_result"]
    feedback["properties"].pop("reason_code")
    feedback["properties"].update(
        {
            "contract_reason_code": {"type": "string"},
            "plan_precision": {
                "pattern": "^[0-9]+\\.[0-9]{12}$",
                "type": "string",
            },
            "plan_precision_denominator": {"minimum": 1, "type": "integer"},
            "plan_precision_numerator": {"minimum": 0, "type": "integer"},
            "reason_codes": {
                "items": {
                    "enum": [
                        "ANSWER_MISMATCH",
                        "IN_SCOPE_OVER_SELECTION",
                        "INSUFFICIENT_PLAN",
                        "SCOPE_IMURITY",
                    ],
                    "type": "string",
                },
                "maxItems": 4,
                "type": "array",
            },
        }
    )
    feedback["required"].remove("reason_code")
    feedback["required"].extend(
        [
            "contract_reason_code",
            "reason_codes",
            "plan_precision",
            "plan_precision_numerator",
            "plan_precision_denominator",
        ]
    )
    reference = schema["$defs"]["reference_task"]
    reference["properties"]["derivation"]["properties"]["builder"][
        "const"
    ] = "reference_builder_v2"
    write_json(SCHEMA_PATH, schema)


def _probe_fixture(
    actor_tasks: list[dict[str, Any]],
    references: list[dict[str, Any]],
) -> dict[str, Any]:
    references_by_id = {reference["task_id"]: reference for reference in references}
    alternate_candidates: list[
        tuple[str, dict[str, Any], dict[str, Any], list[str]]
    ] = []
    extra_candidates: list[tuple[str, dict[str, Any], dict[str, Any], list[str]]] = []
    for actor_task in actor_tasks:
        reference = references_by_id[actor_task["task_id"]]
        if len(reference["minimal_sufficient_sets"]) > 1:
            noncanonical = next(
                minimal_set
                for minimal_set in reference["minimal_sufficient_sets"]
                if minimal_set != reference["canonical_sufficient_set"]
            )
            alternate_candidates.append(
                (actor_task["task_id"], actor_task, reference, noncanonical)
            )
    for actor_task in actor_tasks:
        reference = references_by_id[actor_task["task_id"]]
        if reference["out_of_scope_evidence_ids"]:
            extra_candidates.append(
                (
                    actor_task["task_id"],
                    actor_task,
                    reference,
                    [reference["out_of_scope_evidence_ids"][0]],
                )
            )
    if not alternate_candidates or not extra_candidates:
        raise ValueError("frozen probes require one alternate and one out-of-scope case")
    alternate = sorted(alternate_candidates)[0]
    extra = sorted(extra_candidates)[0]
    alternate_task_id, _, alternate_reference, alternate_selection = alternate
    extra_task_id, _, extra_reference, extra_out_scope = extra
    minimal_set = extra_reference["minimal_sufficient_sets"][0]
    extra_selection = sorted(set(minimal_set) | set(extra_out_scope))
    clean_selection = sorted(minimal_set)
    if set(extra_selection) - set(clean_selection) != set(extra_out_scope):
        raise ValueError("scope counterfactual differs by more than one fact")

    def proposal(
        task_id: str,
        reference: dict[str, Any],
        selected_evidence_ids: list[str],
        probe_case_id: str,
    ) -> dict[str, Any]:
        return {
            "probe_case_id": probe_case_id,
            "submitted_outcome": reference["decision"]["outcome"],
            "selected_evidence_ids": selected_evidence_ids,
            "source_task_id": task_id,
        }

    alternate_fixture = proposal(
        alternate_task_id,
        alternate_reference,
        alternate_selection,
        "VALID_ALTERNATE_SET",
    )
    extra_fixture = proposal(
        extra_task_id, extra_reference, extra_selection, "OUT_OF_SCOPE_ADDITION"
    )
    clean_fixture = proposal(
        extra_task_id,
        extra_reference,
        clean_selection,
        "OUT_OF_SCOPE_COUNTERFACTUAL",
    )
    clean_fixture["counterfactual_for"] = extra_fixture["probe_case_id"]
    fixture = {
        "fixture_schema": "condition_change_feedback_probe_inputs_v2",
        "note": (
            "Actor proposals only. Dispositions are derived by the feedback "
            "scorer from the frozen policy, evidence facts, and references. "
            "The scope pair differs by exactly one out-of-scope fact."
        ),
        "probe_cases": [alternate_fixture, extra_fixture, clean_fixture],
    }
    write_json(PROBE_FIXTURES_PATH, fixture)
    return fixture


def freeze_inputs() -> dict[str, Any]:
    policy_v1 = load_json(SOURCE_POLICY_PATH)
    cases_v1 = load_json(SOURCE_CASES_PATH)["cases"]
    revision = load_json(REVISION_SOURCE_PATH)
    policy, source_cases = _apply_v2_revision(policy_v1, cases_v1, revision)
    if source_cases[: len(cases_v1)] != cases_v1:
        raise ValueError("V2 case revision changed an existing V1 case")
    write_json(SOURCE_POLICY_V2_PATH, policy)
    write_json(
        SOURCE_CASES_V2_PATH,
        {"cases": source_cases, "schema_version": "condition_change_cases_v2"},
    )
    _validate_source_inputs(policy, source_cases)
    _write_schema_v2()

    facts: list[dict[str, Any]] = []
    actor_tasks: list[dict[str, Any]] = []
    for case in source_cases:
        facts.extend(_case_facts(case))
        for stage, policy_version_id in STAGES:
            actor_tasks.append(
                _actor_task(policy, case, stage, policy_version_id)
            )
    facts.sort(key=lambda fact: fact["fact_id"])
    actor_tasks.sort(key=lambda task: task["task_id"])

    write_json(POLICY_PATH, policy)
    write_json(FACTS_PATH, facts)
    write_json(
        ACTOR_TASKS_PATH,
        {
            "actor_input_only": True,
            "boundary": {
                "contains_adjudication_fields": False,
                "contains_applicable_policy_context": True,
                "contains_gold_answers": False,
                "contains_minimal_sufficient_sets": False,
                "contains_reference_facts": False,
                "contains_reference_labels": False,
            },
            "schema_version": "condition_change_actor_tasks_v2",
            "tasks": actor_tasks,
        },
    )
    references = derive_all_references(POLICY_PATH, FACTS_PATH)
    write_json(REFERENCE_TASKS_PATH, references)
    _probe_fixture(actor_tasks, references["references"])

    receipt_paths = (
        SOURCE_POLICY_PATH,
        SOURCE_CASES_PATH,
        REVISION_SOURCE_PATH,
        SOURCE_POLICY_V2_PATH,
        SOURCE_CASES_V2_PATH,
        SCHEMA_PATH,
        POLICY_PATH,
        FACTS_PATH,
        ACTOR_TASKS_PATH,
        REFERENCE_TASKS_PATH,
        PROBE_FIXTURES_PATH,
    )
    runtime = {
        "executable": sys.executable,
        "implementation": platform.python_implementation(),
        "version": platform.python_version(),
    }
    if runtime["implementation"] != "CPython" or ".".join(
        runtime["version"].split(".")[:2]
    ) not in SUPPORTED_PYTHON_VERSIONS:
        raise ValueError(f"unexpected Python runtime: {runtime}")
    manifest = {
        "actor_tasks": len(actor_tasks),
        "canonical_input_files": [
            {"path": path.name, "sha256": sha256_file(path)}
            for path in receipt_paths
        ],
        "evidence_facts": len(facts),
        "evidence_identity": EVIDENCE_IDENTITY,
        "package": PACKAGE_NAME,
        "paired_cases": len(source_cases),
        "python": runtime,
        "request_accounting": REQUEST_ACCOUNTING,
        "schema_version": "condition_change_frozen_input_manifest_v2",
        "source_clusters": sorted({case["source_cluster"] for case in source_cases}),
        "task_id": TASK_ID,
        "v1_frozen_hashes": {
            path.name: sha256_file(path) for path in V1_FROZEN_FILES
        },
    }
    write_json(INPUT_MANIFEST_PATH, manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", action="store_true", required=True)
    parser.parse_args()
    manifest = freeze_inputs()
    print(
        f"FROZEN paired_cases={manifest['paired_cases']} "
        f"actor_tasks={manifest['actor_tasks']} "
        f"source_clusters={len(manifest['source_clusters'])} model_requests=0"
    )


if __name__ == "__main__":
    main()
