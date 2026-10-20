#!/usr/bin/env python3
"""Freeze C2 equal-visibility actor input, reference V2 and run bundle."""

from __future__ import annotations

import json
from typing import Any

from finrank_contract import (
    ADJUDICATION,
    ALL_SCHEMAS,
    FIRST_SEVEN,
    PACKAGE,
    RUNTIME_SOURCE,
    SOURCE_DRAFT,
    load_object,
    sha256_file,
    write_json,
)


ANSWER_ATOMS: dict[str, list[dict[str, Any]]] = {
    "ESD_001": [
        {
            "name": "largest_component",
            "label_patterns": ["cash and time deposits"],
            "value": 12471,
            "unit": "USD million",
            "period": "2024-12-31",
        },
        {
            "name": "second_component",
            "label_patterns": ["money market funds"],
            "value": 5050,
            "unit": "USD million",
            "period": "2024-12-31",
        },
    ],
    "ESD_002": [
        {
            "name": "net_cash_financing",
            "label_patterns": [
                "cash flows from financing activities",
                "net cash from financing",
                "financing activities",
            ],
            "value": 1938,
            "unit": "USD million",
            "period": "FY2024",
        }
    ],
    "ESD_003": [
        {
            "name": "automotive_debt",
            "label_patterns": ["automotive debt", "debt carrying amount"],
            "value": 15467,
            "unit": "USD million",
            "period": "FY2024",
        },
        {
            "name": "investing_cash_flow",
            "label_patterns": [
                "cash flows from investing activities",
                "net cash from investing",
                "investing activities",
            ],
            "value": -20517,
            "unit": "USD million",
            "period": "FY2024",
        },
    ],
    "ESD_004": [
        {
            "name": "roe",
            "label_patterns": ["return on equity", "roe"],
            "value": 8.7,
            "unit": "percent",
            "period": "FY2024",
            "tolerance": 0.01,
        },
        {
            "name": "roic_adjusted",
            "label_patterns": ["roic adjusted", "adjusted roic", "roic-adjusted"],
            "value": 20.8,
            "unit": "percent",
            "period": "FY2024",
            "tolerance": 0.01,
        },
    ],
    "ESD_006": [
        {
            "name": "automotive_revenue",
            "label_patterns": ["automotive revenue", "revenue"],
            "value": 171606,
            "unit": "USD million",
            "period": "FY2024",
        },
        {
            "name": "automotive_other_cost",
            "label_patterns": [
                "automotive and other cost of sales",
                "cost of sales",
            ],
            "value": 151065,
            "unit": "USD million",
            "period": "FY2024",
        },
        {
            "name": "derived_gross_profit",
            "label_patterns": ["gross profit"],
            "value": 20541,
            "unit": "USD million",
            "period": "FY2024",
        },
        {
            "name": "derived_gross_margin",
            "label_patterns": ["gross margin percentage", "gross margin"],
            "value": 11.97,
            "unit": "percent",
            "period": "FY2024",
            "tolerance": 0.01,
        },
    ],
    "ESD_010": [
        {
            "name": "total_liabilities",
            "label_patterns": ["total liabilities"],
            "value": 48390,
            "unit": "USD million",
            "period": "2024-12-31",
        },
        {
            "name": "other_long_term_liabilities",
            "label_patterns": ["other long-term liabilities", "other long term liabilities"],
            "value": 10495,
            "unit": "USD million",
            "period": "2024-12-31",
        },
    ],
    "ESD_012": [
        {
            "name": "depreciation_method",
            "label_patterns": ["depreciation method", "ppe depreciation method"],
            "value": "generally straight-line",
            "value_synonyms": ["straight-line", "straight line"],
            "unit": "NONE",
            "period": "NONE",
        },
        {
            "name": "ppe_depreciation_2022",
            "label_patterns": ["ppe depreciation", "depreciation"],
            "value": 2.42,
            "unit": "USD billion",
            "period": "2022",
            "tolerance": 0.01,
        },
        {
            "name": "ppe_depreciation_2023",
            "label_patterns": ["ppe depreciation", "depreciation"],
            "value": 3.33,
            "unit": "USD billion",
            "period": "2023",
            "tolerance": 0.01,
        },
        {
            "name": "ppe_depreciation_2024",
            "label_patterns": ["ppe depreciation", "depreciation"],
            "value": 4.12,
            "unit": "USD billion",
            "period": "2024",
            "tolerance": 0.01,
        },
    ],
}


def main() -> int:
    source = load_object(SOURCE_DRAFT)
    adjudication = load_object(ADJUDICATION)
    source_tasks = {item["task_id"]: item for item in source["tasks"]}
    cases = {item["task_id"]: item for item in adjudication["cases"]}
    actor_tasks: list[dict[str, Any]] = []
    references: list[dict[str, Any]] = []
    for task_id in FIRST_SEVEN:
        source_task = source_tasks[task_id]
        case = cases[task_id]
        if case["ruling"] != "KEEP_DEVELOPMENT":
            raise RuntimeError(f"task_not_retained:{task_id}")
        actor_view = source_task["actor_view"]
        actor_tasks.append(
            {
                "task_id": task_id,
                "split": source_task["split"],
                "source_cluster_id": source_task["source_cluster_id"],
                "source_report_key": source_task["source_report_key"],
                "actor_view": {
                    "instruction": actor_view["instruction"],
                    "question": actor_view["question"],
                    "question_scope": actor_view["question_scope"],
                    "candidates": actor_view["candidates"],
                    "experience_context": None,
                },
            }
        )
        references.append(
            {
                "task_id": task_id,
                "source_cluster_id": source_task["source_cluster_id"],
                "minimal_sufficient_sets": case["minimal_sufficient_sets"],
                "optional_redundant": case["optional_redundant"],
                "canonical_answer": case["canonical_answer"],
                "answer_atoms": ANSWER_ATOMS[task_id],
                "adjudication_note": case["note"],
                "evidence_identity": [
                    {
                        "candidate_id": item["candidate_id"],
                        "text_sha256": __import__("hashlib")
                        .sha256(item["text"].encode("utf-8"))
                        .hexdigest(),
                    }
                    for item in actor_view["candidates"]
                ],
            }
        )
    actor_doc = {
        "schema": "finrank_actor_tasks_v2",
        "status": "FROZEN_DEVELOPMENT_INPUT",
        "plan_time_visibility": {
            "policy": "FULL_VISIBLE_CANDIDATES_AT_PLAN",
            "visible_fields": [
                "candidate_id",
                "text",
                "page_number",
                "visible_source_scope",
            ],
            "shared_by": ["B0_ACTOR", "DETERMINISTIC_STRONG_RULE"],
            "evidence_lookup_role": (
                "Return selected original records in request order; consume "
                "may cite only IDs from the actual return."
            ),
        },
        "task_order": list(FIRST_SEVEN),
        "tasks": actor_tasks,
    }
    references_v2: list[dict[str, Any]] = []
    for reference in references:
        updated = dict(reference)
        if reference["task_id"] == "ESD_006":
            updated["answer_atoms"] = reference["answer_atoms"][2:]
            updated["operand_facts"] = reference["answer_atoms"][:2]
            updated["reference_change"] = {
                "version": "V2",
                "reason": (
                    "Question requires gross profit and gross margin; revenue "
                    "and Automotive and other cost of sales are verification "
                    "operands, not additional required answer atoms."
                ),
                "required_answer_atom_names": [
                    "derived_gross_profit",
                    "derived_gross_margin",
                ],
                "verification_operand_names": [
                    "automotive_revenue",
                    "automotive_other_cost",
                ],
            }
        else:
            updated["operand_facts"] = []
            updated["reference_change"] = {
                "version": "UNCHANGED_FROM_V1",
            }
        references_v2.append(updated)
    reference_doc = {
        "schema": "finrank_evaluation_references_v2",
        "status": "AI_ASSISTED_DEVELOPMENT_REFERENCE_NOT_HUMAN_GOLD",
        "human_confirmed": False,
        "source_reference_v1_sha256": sha256_file(
            PACKAGE / "REFERENCES_V1.json"
        ),
        "change_scope": "ESD_006_REQUIRED_ANSWER_ATOMS_ONLY",
        "tasks": references_v2,
    }
    write_json(PACKAGE / "TASKS_ACTOR_V2.json", actor_doc)
    write_json(PACKAGE / "REFERENCES_V2.json", reference_doc)

    runtime_source = load_object(RUNTIME_SOURCE)
    runtime_override = load_object(
        PACKAGE / "RUNTIME_IDENTITY_OVERRIDE_V1.json"
    )

    run_card = {
        "schema": "finrank_c2_run_card_b0_v3_v1",
        "status": "FROZEN_BEFORE_C2_FIXTURES",
        "owner_authorization": (
            "C2 targeted correction delegated by Loop D; B0 V3 limited to 14 "
            "requests after fixtures."
        ),
        "root_cause": "C2_ROOT_CAUSE.md",
        "plan_time_visibility": actor_doc["plan_time_visibility"],
        "reference_version": "REFERENCES_V2.json",
        "reference_change_scope": reference_doc["change_scope"],
        "endpoint_transport_override": "http://127.0.0.1:18004",
        "model_identity_unchanged": True,
        "generation_policy": {
            "model_id": runtime_source["identity"]["model"]["model_id"],
            "model_sha256": runtime_source["identity"]["model"]["sha256"],
            "chat_template_kwargs": {"enable_thinking": False},
            "generation": runtime_source["identity"]["generation"],
            "retry_cap": 0,
            "concurrency": 1,
        },
        "b0": {
            "tasks": list(FIRST_SEVEN),
            "stages_per_task": ["plan", "consume"],
            "planned_generation_requests": 14,
            "generation_request_cap": 14,
            "run_name": "B0_V3_EQUAL_VISIBILITY",
            "expected_prior_requests": 28,
            "expected_total_requests_after": 42,
            "evidence_lookup_is_local_tool_not_model_request": True,
        },
        "strong_rule": {
            "generation_requests": 0,
            "uses_visible_entity_period_header_metric_and_lexical_signals": True,
        },
        "budget": {
            "shared_request_cap": 192,
            "shared_token_cap": 2_000_000,
            "request_token_reserve": 10240,
            "judge_calls": 0,
            "training_calls": 0,
            "production_memory_writes": 0,
            "history_collection_requests": 0,
        },
        "stop_rules": [
            "Stop generation on identity drift or unreadable response.",
            "Stop generation on actor/reference leakage.",
            "Stop generation on raw overwrite or request identity loss.",
            "Do not retry, replace samples or change model parameters.",
            "No history collection or pilot is part of C2.",
        ],
    }
    write_json(PACKAGE / "RUN_CARD_C2_B0_V3.json", run_card)

    source_inputs = {
        "SCOPE_TASK_DRAFT.json": sha256_file(SOURCE_DRAFT),
        "ADJUDICATION.json": sha256_file(ADJUDICATION),
        "RUNTIME_IDENTITY_SNAPSHOT.json": sha256_file(RUNTIME_SOURCE),
        "REFERENCES_V1.json": sha256_file(PACKAGE / "REFERENCES_V1.json"),
        "C2_ROOT_CAUSE.md": sha256_file(PACKAGE / "C2_ROOT_CAUSE.md"),
    }
    artifacts = {}
    for name in (
        "finrank_contract.py",
        "freeze_finrank_inputs.py",
        "qualify_runtime.py",
        "run_fixtures.py",
        "run_b0.py",
        "run_strong_rule.py",
        "TASKS_ACTOR_V2.json",
        "REFERENCES_V2.json",
        "TOOL_SCHEMAS_V1.json",
        "RUNTIME_IDENTITY_OVERRIDE_V1.json",
        "RUN_CARD_C2_B0_V3.json",
    ):
        artifacts[name] = sha256_file(PACKAGE / name)
    bundle = {
        "schema": "finrank_c2_b0_v3_bundle_v1",
        "status": "FROZEN_BEFORE_C2_FIXTURES",
        "source_inputs": source_inputs,
        "artifacts": artifacts,
    }
    write_json(PACKAGE / "BUNDLE_C2_B0_V3.json", bundle)
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "tasks": len(actor_tasks),
                "bundle_sha256": sha256_file(
                    PACKAGE / "BUNDLE_C2_B0_V3.json"
                ),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
