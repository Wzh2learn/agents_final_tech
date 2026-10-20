#!/usr/bin/env python3
"""Fresh deterministic verification for the C1 deliverables."""

from __future__ import annotations

import json
from typing import Any

from finrank_contract import (
    PACKAGE,
    SHARED_LEDGER,
    load_object,
    sha256_file,
    verify_bundle,
    write_json,
)


def check(name: str, condition: bool, observed: Any) -> dict[str, Any]:
    return {"name": name, "pass": bool(condition), "observed": observed}


def main() -> int:
    bundle = verify_bundle(PACKAGE / "BUNDLE_B0_FIX_V2.json")
    fixture = load_object(PACKAGE / "FIXTURE_RECEIPT.json")
    runtime = load_object(PACKAGE / "RUNTIME_QUALIFICATION.json")
    actor_doc = load_object(PACKAGE / "TASKS_ACTOR_V1.json")
    reference_doc = load_object(PACKAGE / "REFERENCES_V1.json")
    b0_v1 = load_object(
        PACKAGE / "results" / "b0_v1" / "B0_RESULT.json"
    )
    b0_v2 = load_object(
        PACKAGE / "results" / "B0_V2_ENGINEERING_FIX" / "B0_RESULT.json"
    )
    strong = load_object(PACKAGE / "results" / "STRONG_RULE_RESULT.json")
    ledger = load_object(SHARED_LEDGER)
    request_records = ledger.get("request_records", [])
    v1_records = [
        item for item in request_records if "|B0|" in item["request_key"]
    ]
    v2_records = [
        item
        for item in request_records
        if "|B0_V2_ENGINEERING_FIX|" in item["request_key"]
    ]
    raw_v2 = PACKAGE / "raw" / "B0_V2_ENGINEERING_FIX"
    raw_v1 = PACKAGE / "raw" / "B0_V1"
    request_files = list(raw_v2.glob("*/request.json"))
    response_files = list(raw_v2.glob("*/response.json"))
    crash_files = list(raw_v2.glob("*/crash.json"))
    v1_request_files = list(raw_v1.glob("*/request.json"))
    v1_response_files = list(raw_v1.glob("*/response.json"))
    v1_crash_files = list(raw_v1.glob("*/crash.json"))
    references = {
        item["task_id"]: item for item in reference_doc["tasks"]
    }

    def plan_is_sufficient(result: dict[str, Any]) -> bool:
        selected = set(result["plan"].get("evidence_candidate_ids", []))
        return any(
            set(minimal) <= selected
            for minimal in references[result["task_id"]][
                "minimal_sufficient_sets"
            ]
        )

    b0_plan_sufficient = sum(plan_is_sufficient(item) for item in b0_v2["results"])
    strong_plan_sufficient = sum(
        plan_is_sufficient(item) for item in strong["results"]
    )
    actor_banned = {
        "reference",
        "canonical_answer",
        "answer_atoms",
        "minimal_sufficient_sets",
        "optional_redundant",
        "anchors",
        "adjudication_note",
        "source_passage_ids",
    }

    def has_banned(value: Any) -> bool:
        if isinstance(value, dict):
            return bool(actor_banned & set(value)) or any(
                has_banned(item) for item in value.values()
            )
        if isinstance(value, list):
            return any(has_banned(item) for item in value)
        return False

    checks = [
        check(
            "bundle_current",
            bundle["schema"] == "finrank_c1_b0_fix_bundle_v2",
            {
                "schema": bundle["schema"],
                "sha256": sha256_file(PACKAGE / "BUNDLE_B0_FIX_V2.json"),
            },
        ),
        check(
            "fixtures",
            fixture["status"] == "PASS" and fixture["passed"] == fixture["total"],
            {"passed": fixture["passed"], "total": fixture["total"]},
        ),
        check(
            "runtime_non_generative",
            runtime["status"] == "QUALIFIED_NON_GENERATIVE"
            and all(runtime["checks"].values()),
            runtime["checks"],
        ),
        check(
            "actor_reference_separated",
            len(actor_doc["tasks"]) == 7
            and len(reference_doc["tasks"]) == 7
            and not has_banned(actor_doc),
            {
                "actor_tasks": len(actor_doc["tasks"]),
                "references": len(reference_doc["tasks"]),
                "human_confirmed": reference_doc["human_confirmed"],
            },
        ),
        check(
            "v1_preserved_as_engineering_failure",
            b0_v1["generation_requests"] == 14
            and b0_v1["error_classes"]["ENGINEERING_SCHEMA_OR_TOOL"] == 7,
            {
                "requests": b0_v1["generation_requests"],
                "engineering": b0_v1["error_classes"][
                    "ENGINEERING_SCHEMA_OR_TOOL"
                ],
            },
        ),
        check(
            "v2_complete_and_engineering_clean",
            b0_v2["status"] == "COMPLETE_DEVELOPMENT_OBSERVATION"
            and b0_v2["generation_requests"] == 14
            and b0_v2["error_classes"]["ENGINEERING_SCHEMA_OR_TOOL"] == 0
            and len(b0_v2["results"]) == 7,
            {
                "requests": b0_v2["generation_requests"],
                "engineering": b0_v2["error_classes"][
                    "ENGINEERING_SCHEMA_OR_TOOL"
                ],
                "semantic": b0_v2["error_classes"][
                    "SEMANTIC_SELECTION_OR_ANSWER"
                ],
                "results": len(b0_v2["results"]),
            },
        ),
        check(
            "raw_all_immutable_complete",
            len(request_files) == 14
            and len(response_files) == 14
            and not crash_files
            and len(v1_request_files) == 14
            and len(v1_response_files) == 14
            and not v1_crash_files,
            {
                "v1_request_files": len(v1_request_files),
                "v1_response_files": len(v1_response_files),
                "v1_crash_files": len(v1_crash_files),
                "v2_request_files": len(request_files),
                "v2_response_files": len(response_files),
                "v2_crash_files": len(crash_files),
            },
        ),
        check(
            "plan_sufficiency_recomputed",
            b0_plan_sufficient == 3 and strong_plan_sufficient == 7,
            {
                "b0_v2_plan_sufficient": b0_plan_sufficient,
                "strong_rule_plan_sufficient": strong_plan_sufficient,
                "tasks": 7,
            },
        ),
        check(
            "shared_ledger_complete",
            ledger["new_generation_budget"]["requests_used"] == 28
            and ledger["new_generation_budget"]["accounting_tokens_used"] == 65864
            and len(v1_records) == 14
            and len(v2_records) == 14,
            {
                "requests_used": ledger["new_generation_budget"]["requests_used"],
                "accounting_tokens_used": ledger["new_generation_budget"][
                    "accounting_tokens_used"
                ],
                "v1_requests": len(v1_records),
                "v2_requests": len(v2_records),
            },
        ),
        check(
            "zero_forbidden_research_calls",
            ledger["new_generation_budget"]["judge_calls"] == 0
            and ledger["new_generation_budget"]["training_calls"] == 0
            and ledger["new_generation_budget"]["production_memory_writes"] == 0,
            {
                "judge_calls": ledger["new_generation_budget"]["judge_calls"],
                "training_calls": ledger["new_generation_budget"]["training_calls"],
                "production_memory_writes": ledger["new_generation_budget"][
                    "production_memory_writes"
                ],
            },
        ),
        check(
            "strong_rule_zero_generation",
            strong["generation_requests"] == 0
            and len(strong["results"]) == 7,
            {
                "generation_requests": strong["generation_requests"],
                "results": len(strong["results"]),
            },
        ),
    ]
    passed = sum(item["pass"] for item in checks)
    output = {
        "schema": "finrank_c1_verification_v1",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed": passed,
        "total": len(checks),
        "checks": checks,
    }
    write_json(PACKAGE / "C1_VERIFICATION.json", output)
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
