#!/usr/bin/env python3
"""Derive decisions and minimal sufficient sets from policy and evidence facts."""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any

from condition_change_common import (
    FACTS_PATH,
    POLICY_PATH,
    load_json,
    sorted_unique,
    validate_against_definition,
)


def match_value(value: Any, predicate: dict[str, Any]) -> bool:
    operator = predicate["op"]
    expected = predicate["value"]
    if operator == "eq":
        return value == expected
    if operator == "neq":
        return value != expected
    if operator == "gt":
        return value > expected
    if operator == "gte":
        return value >= expected
    if operator == "lt":
        return value < expected
    if operator == "lte":
        return value <= expected
    raise ValueError(f"unsupported predicate operator: {operator}")


def match_predicate(record: dict[str, Any], predicate: dict[str, Any]) -> bool:
    if not predicate:
        return True
    if "all" in predicate:
        return all(match_predicate(record, child) for child in predicate["all"])
    if "any" in predicate:
        return any(match_predicate(record, child) for child in predicate["any"])
    if "not" in predicate:
        return not match_predicate(record, predicate["not"])
    field = predicate.get("field")
    if field is None or "op" not in predicate or "value" not in predicate:
        raise ValueError(f"invalid predicate: {predicate}")
    return match_value(record.get(field), predicate)


def _matching_fact_ids(
    facts: list[dict[str, Any]], predicate: dict[str, Any]
) -> list[str]:
    return sorted(
        fact["fact_id"] for fact in facts if match_predicate(fact, predicate)
    )


def _requirement_sets(
    facts: list[dict[str, Any]],
    claim: dict[str, Any],
    requirement: dict[str, Any],
) -> list[list[str]]:
    if "when" in requirement and not match_predicate(claim, requirement["when"]):
        return [[]]
    alternatives: list[list[str]] = []
    for alternative in requirement["alternatives"]:
        alternative_sets = [[]]
        for predicate in alternative:
            matched = _matching_fact_ids(facts, predicate)
            alternative_sets = [
                sorted_unique(existing + [fact_id])
                for existing in alternative_sets
                for fact_id in matched
            ]
        alternatives.extend(alternative_sets)
    return ordered_unique_sets(alternatives)


def ordered_unique_sets(sets: list[list[str]]) -> list[list[str]]:
    seen: set[tuple[str, ...]] = set()
    ordered: list[list[str]] = []
    for item_set in sets:
        normalized = sorted_unique(item_set)
        key = tuple(normalized)
        if key not in seen:
            seen.add(key)
            ordered.append(normalized)
    return ordered


def sorted_unique_sets(sets: list[list[str]]) -> list[list[str]]:
    deduplicated = {tuple(sorted(set(item_set))) for item_set in sets}
    return [list(item_set) for item_set in sorted(deduplicated)]


def policy_scope_fact_kinds(policy: dict[str, Any]) -> set[str]:
    return set(policy["in_scope_fact_kinds"])


def _matching_rule(
    policy: dict[str, Any], policy_version_id: str, claim: dict[str, Any]
) -> dict[str, Any]:
    if policy["decision_semantics"] != "first_match_in_declared_order":
        raise ValueError("unsupported decision semantics")
    rules = policy["policy_versions"][policy_version_id]["decision_rules"]
    matched = [rule for rule in rules if match_predicate(claim, rule["applies_when"])]
    if not matched:
        raise ValueError("claim matched no decision rules")
    return matched[0]


def derive_reference(
    policy: dict[str, Any],
    task_fields: dict[str, Any],
    facts: list[dict[str, Any]],
) -> dict[str, Any]:
    claim_facts = [fact for fact in facts if fact["kind"] == "claim"]
    if len(claim_facts) != 1:
        raise ValueError(f"{task_fields['task_id']} must have exactly one claim fact")
    claim = claim_facts[0]["claim"]
    evidence_facts = [fact for fact in facts if fact["kind"] != "claim"]
    rule = _matching_rule(policy, task_fields["policy_version_id"], claim)
    requirement_sets = [
        _requirement_sets(evidence_facts, claim, requirement)
        for requirement in rule["requires"]
    ]
    if any(not sets for sets in requirement_sets):
        raise ValueError(f"{task_fields['task_id']} has an unsatisfiable requirement")
    sufficient_sets = ordered_unique_sets(
        [
            sorted_unique(list(itertools.chain.from_iterable(selection)))
            for selection in itertools.product(*requirement_sets)
        ]
    )
    if not sufficient_sets:
        raise ValueError(f"{task_fields['task_id']} has no sufficient evidence set")
    scope_kinds = policy_scope_fact_kinds(policy)
    in_scope_ids = sorted(
        fact["fact_id"] for fact in evidence_facts if fact["kind"] in scope_kinds
    )
    out_of_scope_ids = sorted(
        fact["fact_id"] for fact in evidence_facts if fact["kind"] not in scope_kinds
    )
    reference = {
        **task_fields,
        "canonical_sufficient_set": sufficient_sets[0],
        "decision": {
            "outcome": rule["outcome"],
            "reason_code": rule["reason_code"],
            "rule_id": rule["id"],
        },
        "derivation": {
            "builder": "reference_builder_v2",
            "gold_source": "declarative_policy_and_evidence_facts",
            "minimal_set_count": len(sufficient_sets),
        },
        "in_scope_evidence_ids": in_scope_ids,
        "minimal_sufficient_sets": sufficient_sets,
        "out_of_scope_evidence_ids": out_of_scope_ids,
    }
    validate_against_definition(reference, "reference_task")
    return reference


def derive_all_references(
    policy_path: Path = POLICY_PATH,
    facts_path: Path = FACTS_PATH,
) -> dict[str, Any]:
    policy = load_json(policy_path)
    facts = load_json(facts_path)
    facts_by_case: dict[str, list[dict[str, Any]]] = {}
    for fact in facts:
        validate_against_definition(fact, "evidence_fact")
        facts_by_case.setdefault(fact["case_id"], []).append(fact)
    references: list[dict[str, Any]] = []
    for case_id in sorted(facts_by_case):
        for stage, policy_version_id in (
            ("pre", "expense_policy_pre_v1"),
            ("post", "expense_policy_post_v1"),
        ):
            task_fields = {
                "case_id": case_id,
                "policy_version_id": policy_version_id,
                "stage": stage,
                "task_id": f"{case_id}:{stage}",
            }
            references.append(
                derive_reference(policy, task_fields, facts_by_case[case_id])
            )
    references.sort(key=lambda reference: reference["task_id"])
    result = {
        "builder_version": "reference_builder_v2",
        "policy_id": policy["policy_id"],
        "references": references,
        "schema_version": "condition_change_references_v2",
    }
    return result


if __name__ == "__main__":
    result = derive_all_references()
    print(
        f"DERIVED {len(result['references'])} references from policy and evidence facts"
    )
