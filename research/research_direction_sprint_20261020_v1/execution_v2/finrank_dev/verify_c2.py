#!/usr/bin/env python3
"""Deterministic C2 verification over frozen artifacts and raw outputs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from finrank_contract import (
    PACKAGE,
    SHARED_LEDGER,
    load_object,
    plan_visible_candidates,
    sha256_file,
    strict_json_object,
    verify_bundle,
    write_json,
)


def check(name: str, condition: bool, observed: Any) -> dict[str, Any]:
    return {"name": name, "pass": bool(condition), "observed": observed}


def plan_sufficient(result: dict[str, Any], reference: dict[str, Any]) -> bool:
    selected = set(result["plan"].get("evidence_candidate_ids", []))
    return any(
        set(minimal) <= selected
        for minimal in reference["minimal_sufficient_sets"]
    )


def raw_counts(root: Path) -> dict[str, int]:
    return {
        "requests": len(list(root.glob("*/request.json"))),
        "responses": len(list(root.glob("*/response.json"))),
        "crashes": len(list(root.glob("*/crash.json"))),
    }


def main() -> int:
    bundle = verify_bundle(PACKAGE / "BUNDLE_C2_B0_V3.json")
    fixture = load_object(PACKAGE / "FIXTURE_RECEIPT_C2.json")
    runtime = load_object(PACKAGE / "RUNTIME_QUALIFICATION_C2.json")
    actor_doc = load_object(PACKAGE / "TASKS_ACTOR_V2.json")
    ref_v1_doc = load_object(PACKAGE / "REFERENCES_V1.json")
    ref_v2_doc = load_object(PACKAGE / "REFERENCES_V2.json")
    b0_v1 = load_object(PACKAGE / "results" / "b0_v1" / "B0_RESULT.json")
    b0_v2 = load_object(
        PACKAGE / "results" / "B0_V2_ENGINEERING_FIX" / "B0_RESULT.json"
    )
    b0_v3 = load_object(
        PACKAGE / "results" / "B0_V3_EQUAL_VISIBILITY" / "B0_RESULT.json"
    )
    strong = load_object(PACKAGE / "results" / "STRONG_RULE_RESULT_C2.json")
    ledger = load_object(SHARED_LEDGER)
    tasks = {item["task_id"]: item for item in actor_doc["tasks"]}
    refs_v1 = {item["task_id"]: item for item in ref_v1_doc["tasks"]}
    refs_v2 = {item["task_id"]: item for item in ref_v2_doc["tasks"]}
    results_v3 = {item["task_id"]: item for item in b0_v3["results"]}
    strong_results = {item["task_id"]: item for item in strong["results"]}

    unchanged_refs = []
    esd006_reference_change = (
        refs_v1["ESD_006"]["canonical_answer"]
        == refs_v2["ESD_006"]["canonical_answer"]
        and refs_v1["ESD_006"]["minimal_sufficient_sets"]
        == refs_v2["ESD_006"]["minimal_sufficient_sets"]
        and [
            item["name"] for item in refs_v2["ESD_006"]["answer_atoms"]
        ]
        == ["derived_gross_profit", "derived_gross_margin"]
        and [
            item["name"] for item in refs_v2["ESD_006"]["operand_facts"]
        ]
        == ["automotive_revenue", "automotive_other_cost"]
    )
    for task_id in refs_v1:
        if task_id == "ESD_006":
            continue
        unchanged_refs.append(
            all(
                refs_v1[task_id][key] == refs_v2[task_id][key]
                for key in (
                    "minimal_sufficient_sets",
                    "optional_redundant",
                    "canonical_answer",
                    "answer_atoms",
                    "adjudication_note",
                    "evidence_identity",
                )
            )
        )

    plan_visibility_checks = []
    for request_path in sorted(
        (PACKAGE / "raw" / "B0_V3_EQUAL_VISIBILITY").glob(
            "plan_B0_V3_EQUAL_VISIBILITY_*/request.json"
        )
    ):
        payload = load_object(request_path)
        content = payload["messages"][1]["content"]
        match = re.search(
            r"TASK_AND_VISIBLE_EVIDENCE=(.*?)\nChoose candidate IDs",
            content,
            re.DOTALL,
        )
        task_payload = json.loads(match.group(1)) if match else {}
        task_id = task_payload.get("task_id")
        expected = (
            plan_visible_candidates(tasks[task_id]) if task_id in tasks else []
        )
        plan_visibility_checks.append(
            task_payload.get("plan_time_visibility")
            == "FULL_VISIBLE_CANDIDATES_AT_PLAN"
            and task_payload.get("candidates") == expected
            and all(item["text"] for item in expected)
        )

    b0_plan_sufficient = sum(
        plan_sufficient(item, refs_v2[item["task_id"]])
        for item in b0_v3["results"]
    )
    strong_plan_sufficient = sum(
        plan_sufficient(item, refs_v2[item["task_id"]])
        for item in strong["results"]
    )
    b0_consume_sufficient = sum(
        item["evidence_sufficiency"]["sufficient"]
        for item in b0_v3["results"]
    )
    frozen_answer_matches = sum(
        item["answer_reference_match"]["match"]
        for item in b0_v3["results"]
    )
    model_format_failures = sum(
        str(item.get("task_error", "")).startswith(
            "schema_or_contract:model_json_invalid"
        )
        for item in b0_v3["results"]
    )
    raw_v1 = raw_counts(PACKAGE / "raw" / "B0_V1")
    raw_v2 = raw_counts(PACKAGE / "raw" / "B0_V2_ENGINEERING_FIX")
    raw_v3 = raw_counts(PACKAGE / "raw" / "B0_V3_EQUAL_VISIBILITY")
    request_records = ledger.get("request_records", [])
    v3_records = [
        item
        for item in request_records
        if "|B0_V3_EQUAL_VISIBILITY|" in item["request_key"]
    ]

    esd004 = results_v3["ESD_004"]
    esd004_checker_limitation = (
        esd004["answer_reference_match"]["match"] is False
        and set(esd004["answer_reference_match"]["missing_atoms"])
        == {"roe", "roic_adjusted"}
        and {
            fact["value"] for fact in esd004["consume"]["facts"]
        }
        == {8.7, 20.8}
        and all(fact["unit"] == "%" for fact in esd004["consume"]["facts"])
    )

    esd012_response_path = next(
        (
            PACKAGE / "raw" / "B0_V3_EQUAL_VISIBILITY"
        ).glob(
            "consume_B0_V3_EQUAL_VISIBILITY_ESD_012_*/response.json"
        )
    )
    esd012_response = load_object(esd012_response_path)
    esd012_body = strict_json_object(esd012_response["body_text"])
    esd012_content = esd012_body["choices"][0]["message"]["content"]
    try:
        strict_json_object(esd012_content)
        esd012_json_parses = True
    except ValueError:
        esd012_json_parses = False
    esd012_length_failure = (
        esd012_body["choices"][0]["finish_reason"] == "length"
        and not esd012_json_parses
    )

    esd006_abstention = (
        results_v3["ESD_006"]["evidence_sufficiency"]["sufficient"]
        and results_v3["ESD_006"]["consume"]["answer_status"] == "UNKNOWN"
    )

    checks = [
        check(
            "bundle_and_fixture",
            bundle["schema"] == "finrank_c2_b0_v3_bundle_v1"
            and fixture["status"] == "PASS"
            and fixture["passed"] == fixture["total"] == 17,
            {
                "bundle_sha256": sha256_file(
                    PACKAGE / "BUNDLE_C2_B0_V3.json"
                ),
                "fixture": f"{fixture['passed']}/{fixture['total']}",
            },
        ),
        check(
            "runtime_unchanged",
            runtime["status"] == "QUALIFIED_NON_GENERATIVE"
            and all(runtime["checks"].values()),
            runtime["checks"],
        ),
        check(
            "reference_v2_only_esd006_changed",
            esd006_reference_change and all(unchanged_refs),
            {
                "source_v1_sha256": ref_v2_doc["source_reference_v1_sha256"],
                "current_v1_sha256": sha256_file(
                    PACKAGE / "REFERENCES_V1.json"
                ),
                "unchanged_other_tasks": all(unchanged_refs),
                "esd006_required": [
                    item["name"]
                    for item in refs_v2["ESD_006"]["answer_atoms"]
                ],
                "esd006_operands": [
                    item["name"]
                    for item in refs_v2["ESD_006"]["operand_facts"]
                ],
            },
        ),
        check(
            "equal_plan_time_visibility_in_actual_requests",
            len(plan_visibility_checks) == 7 and all(plan_visibility_checks),
            {
                "requests_checked": len(plan_visibility_checks),
                "policy": actor_doc["plan_time_visibility"]["policy"],
            },
        ),
        check(
            "prior_runs_preserved",
            b0_v1["generation_requests"] == 14
            and b0_v2["generation_requests"] == 14
            and raw_v1 == {
                "requests": 14,
                "responses": 14,
                "crashes": 0,
            }
            and raw_v2 == {
                "requests": 14,
                "responses": 14,
                "crashes": 0,
            },
            {"b0_v1_raw": raw_v1, "b0_v2_raw": raw_v2},
        ),
        check(
            "b0_v3_complete",
            b0_v3["status"] == "COMPLETE_DEVELOPMENT_OBSERVATION"
            and b0_v3["generation_requests"] == 14
            and len(b0_v3["results"]) == 7
            and raw_v3 == {
                "requests": 14,
                "responses": 14,
                "crashes": 0,
            },
            {
                "frozen_success": b0_v3["success_count"],
                "frozen_non_success": b0_v3["non_success_count"],
                "raw": raw_v3,
            },
        ),
        check(
            "decision_layers_recomputed",
            b0_plan_sufficient == 7
            and b0_consume_sufficient == 6
            and frozen_answer_matches == 4
            and strong_plan_sufficient == 7
            and model_format_failures == 1,
            {
                "b0_plan_sufficient": b0_plan_sufficient,
                "b0_consume_sufficient": b0_consume_sufficient,
                "frozen_answer_matches": frozen_answer_matches,
                "strong_plan_sufficient": strong_plan_sufficient,
                "model_format_failures": model_format_failures,
            },
        ),
        check(
            "known_limitations_not_silently_rescored",
            esd004_checker_limitation
            and esd012_length_failure
            and esd006_abstention,
            {
                "esd004_percent_unit_checker_limitation": (
                    esd004_checker_limitation
                ),
                "esd012_finish_reason": esd012_body["choices"][0][
                    "finish_reason"
                ],
                "esd012_json_parses": esd012_json_parses,
                "esd006_sufficient_but_unknown": esd006_abstention,
            },
        ),
        check(
            "ledger_42_and_forbidden_calls_zero",
            ledger["new_generation_budget"]["requests_used"] == 42
            and ledger["new_generation_budget"]["accounting_tokens_used"]
            == 261902
            and len(v3_records) == 14
            and ledger["new_generation_budget"]["judge_calls"] == 0
            and ledger["new_generation_budget"]["training_calls"] == 0
            and ledger["new_generation_budget"]["production_memory_writes"] == 0,
            {
                "requests_used": ledger["new_generation_budget"]["requests_used"],
                "accounting_tokens_used": ledger["new_generation_budget"][
                    "accounting_tokens_used"
                ],
                "v3_requests": len(v3_records),
                "judge_calls": ledger["new_generation_budget"]["judge_calls"],
                "training_calls": ledger["new_generation_budget"][
                    "training_calls"
                ],
                "production_memory_writes": ledger["new_generation_budget"][
                    "production_memory_writes"
                ],
            },
        ),
        check(
            "strong_rule_zero_generation",
            strong["generation_requests"] == 0
            and strong["plan_time_visibility"]["policy"]
            == "FULL_VISIBLE_CANDIDATES_AT_PLAN",
            {
                "generation_requests": strong["generation_requests"],
                "policy": strong["plan_time_visibility"]["policy"],
            },
        ),
    ]
    passed = sum(item["pass"] for item in checks)
    output = {
        "schema": "finrank_c2_verification_v1",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed": passed,
        "total": len(checks),
        "checks": checks,
    }
    write_json(PACKAGE / "C2_VERIFICATION.json", output)
    print(
        json.dumps(
            {
                "status": output["status"],
                "passed": passed,
                "total": len(checks),
            },
            sort_keys=True,
        )
    )
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
