#!/usr/bin/env python3
"""Fresh verification for the C3 corrections and B0 V4 observation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from finrank_contract import (
    PACKAGE,
    SHARED_LEDGER,
    load_object,
    sha256_file,
    strict_json_object,
    verify_bundle,
    write_json,
)


def check(name: str, condition: bool, observed: Any) -> dict[str, Any]:
    return {"name": name, "pass": bool(condition), "observed": observed}


def raw_counts(root: Path) -> dict[str, int]:
    return {
        "requests": len(list(root.glob("*/request.json"))),
        "responses": len(list(root.glob("*/response.json"))),
        "crashes": len(list(root.glob("*/crash.json"))),
    }


def main() -> int:
    bundle = verify_bundle(PACKAGE / "BUNDLE_C3_B0_V4_FIX1.json")
    fixture = load_object(PACKAGE / "FIXTURE_RECEIPT_C3.json")
    runtime = load_object(PACKAGE / "RUNTIME_QUALIFICATION_C3.json")
    unit_red = load_object(PACKAGE / "C3_UNIT_RED.json")
    unit_green = load_object(PACKAGE / "C3_UNIT_GREEN.json")
    derivation_red = load_object(PACKAGE / "C3_DERIVATION_RED.json")
    derivation_green = load_object(PACKAGE / "C3_DERIVATION_GREEN.json")
    ref_v1 = load_object(PACKAGE / "REFERENCES_V1.json")
    ref_v2 = load_object(PACKAGE / "REFERENCES_V2.json")
    ref_v3 = load_object(PACKAGE / "REFERENCES_V3.json")
    actor_v3 = load_object(PACKAGE / "TASKS_ACTOR_V3.json")
    original_v3 = load_object(
        PACKAGE
        / "results"
        / "B0_V3_EQUAL_VISIBILITY"
        / "B0_RESULT.json"
    )
    posthoc_v2 = load_object(
        PACKAGE
        / "results"
        / "B0_V3_EQUAL_VISIBILITY"
        / "B0_RESULT_POSTHOC_SCORER_V2.json"
    )
    posthoc_v3 = load_object(
        PACKAGE
        / "results"
        / "B0_V3_EQUAL_VISIBILITY"
        / "B0_RESULT_POSTHOC_SCORER_V3.json"
    )
    b0_v4 = load_object(
        PACKAGE
        / "results"
        / "B0_V4_MINIFIED_JSON"
        / "B0_RESULT.json"
    )
    strong = load_object(PACKAGE / "results" / "STRONG_RULE_RESULT_C3.json")
    ledger = load_object(SHARED_LEDGER)
    v4_records = [
        item
        for item in ledger.get("request_records", [])
        if "|B0_V4_MINIFIED_JSON|" in item["request_key"]
    ]
    raw_v1 = raw_counts(PACKAGE / "raw" / "B0_V1")
    raw_v2 = raw_counts(PACKAGE / "raw" / "B0_V2_ENGINEERING_FIX")
    raw_v3 = raw_counts(PACKAGE / "raw" / "B0_V3_EQUAL_VISIBILITY")
    raw_v4 = raw_counts(PACKAGE / "raw" / "B0_V4_MINIFIED_JSON")

    refs_v1 = {item["task_id"]: item for item in ref_v1["tasks"]}
    refs_v2 = {item["task_id"]: item for item in ref_v2["tasks"]}
    refs_v3 = {item["task_id"]: item for item in ref_v3["tasks"]}
    v3_unchanged_scope = all(
        refs_v2[task_id]["answer_atoms"] == refs_v3[task_id]["answer_atoms"]
        and refs_v2[task_id]["operand_facts"]
        == refs_v3[task_id]["operand_facts"]
        and refs_v2[task_id]["canonical_answer"]
        == refs_v3[task_id]["canonical_answer"]
        for task_id in refs_v2
    )
    derivation_contract = (
        len(refs_v3["ESD_006"]["derivations"]) == 2
        and {
            item["target_atom"]
            for item in refs_v3["ESD_006"]["derivations"]
        }
        == {"derived_gross_profit", "derived_gross_margin"}
        and all(
            item["operator"] and item["formula"] and item["operand_atoms"]
            for item in refs_v3["ESD_006"]["derivations"]
        )
    )

    v4_esd012_response = next(
        (PACKAGE / "raw" / "B0_V4_MINIFIED_JSON").glob(
            "consume_B0_V4_MINIFIED_JSON_ESD_012_*/response.json"
        )
    )
    esd012_body = load_object(v4_esd012_response)
    esd012_chat = strict_json_object(esd012_body["body_text"])
    esd012_content = esd012_chat["choices"][0]["message"]["content"]
    try:
        strict_json_object(esd012_content)
        esd012_json_parses = True
    except ValueError:
        esd012_json_parses = False
    esd012_v4_failure = (
        esd012_chat["choices"][0]["finish_reason"] == "length"
        and esd012_chat["usage"]["completion_tokens"] == 256
        and not esd012_json_parses
    )
    v4_plan_requests = sorted(
        (PACKAGE / "raw" / "B0_V4_MINIFIED_JSON").glob(
            "plan_B0_V4_MINIFIED_JSON_*/request.json"
        )
    )
    minified_prompt_seen = True
    for request_path in v4_plan_requests:
        request = load_object(request_path)
        content = request["messages"][1]["content"]
        minified_prompt_seen = minified_prompt_seen and all(
            marker in content
            for marker in (
                "minified JSON",
                "no whitespace outside string values",
                "Do not pretty-print",
                "Markdown fences",
            )
        )

    b0_v4_results = {item["task_id"]: item for item in b0_v4["results"]}
    esd006_real_non_success = (
        b0_v4_results["ESD_006"]["evidence_sufficiency"]["sufficient"]
        and b0_v4_results["ESD_006"]["consume"]["answer_status"] == "UNKNOWN"
        and b0_v4_results["ESD_006"]["outcome"] == "NON_SUCCESS"
    )
    esd004_v4_success = b0_v4_results["ESD_004"]["outcome"] == "SUCCESS"
    frozen_score_split = {
        "original_v3": original_v3["success_count"],
        "posthoc_unit_fix_v2": posthoc_v2["posthoc"]["success_count"],
        "posthoc_full_checker_v3": posthoc_v3["scores"][
            "full_checker_posthoc_v3"
        ],
        "b0_v4_formal": b0_v4["success_count"],
    }

    checks = [
        check(
            "bundle_and_fixtures",
            bundle["schema"] == "finrank_c3_b0_v4_bundle_v2"
            and fixture["status"] == "PASS"
            and fixture["passed"] == fixture["total"] == 21,
            {
                "bundle_sha256": sha256_file(
                    PACKAGE / "BUNDLE_C3_B0_V4_FIX1.json"
                ),
                "fixture": f"{fixture['passed']}/{fixture['total']}",
            },
        ),
        check(
            "unit_red_green",
            unit_red["observed_match"] is False
            and unit_green["observed_match"] is True
            and unit_red["missing_atoms"]
            == ["roe", "roic_adjusted"]
            and not unit_green["missing_atoms"],
            {
                "red": unit_red,
                "green": unit_green,
            },
        ),
        check(
            "derivation_red_green",
            derivation_red["observed"]["false_pair_consistent"] is True
            and derivation_green["observed"]["false_pair_consistent"]
            is False
            and derivation_green["observed"][
                "explicit_derivation_consistent"
            ]
            is True,
            {
                "red": derivation_red["observed"],
                "green": derivation_green["observed"],
            },
        ),
        check(
            "reference_v3_explicit_derivation_only",
            v3_unchanged_scope and derivation_contract,
            {
                "answer_scope_unchanged_from_v2": v3_unchanged_scope,
                "derivations": refs_v3["ESD_006"]["derivations"],
            },
        ),
        check(
            "estimand_limited",
            actor_v3["estimand"]["name"]
            == "COMPLETE_CANDIDATE_SELECTION_AND_CONSUMPTION"
            and "not active evidence acquisition"
            in actor_v3["estimand"]["limit"]
            and "not a V2" in actor_v3["estimand"]["limit"],
            actor_v3["estimand"],
        ),
        check(
            "v3_preserved_and_posthoc_split",
            frozen_score_split
            == {
                "original_v3": 4,
                "posthoc_unit_fix_v2": 5,
                "posthoc_full_checker_v3": 5,
                "b0_v4_formal": 5,
            }
            and posthoc_v3["outcome_changes_from_unit_fix_posthoc"] == [],
            {
                "scores": frozen_score_split,
                "v3_consistency_changed_tasks": posthoc_v3[
                    "consistency_changed_tasks"
                ],
                "v3_outcome_changes_from_unit_fix_posthoc": posthoc_v3[
                    "outcome_changes_from_unit_fix_posthoc"
                ],
            },
        ),
        check(
            "b0_v4_complete_and_clean_execution_chain",
            b0_v4["status"] == "COMPLETE_DEVELOPMENT_OBSERVATION"
            and b0_v4["generation_requests"] == 14
            and b0_v4["error_classes"]["ENGINEERING_SCHEMA_OR_TOOL"] == 1
            and raw_v4
            == {"requests": 14, "responses": 14, "crashes": 0}
            and esd004_v4_success,
            {
                "success": b0_v4["success_count"],
                "non_success": b0_v4["non_success_count"],
                "error_classes": b0_v4["error_classes"],
                "raw_v4": raw_v4,
            },
        ),
        check(
            "known_failures_preserved",
            esd006_real_non_success and esd012_v4_failure,
            {
                "esd006_sufficient_but_unknown": esd006_real_non_success,
                "esd012_finish_reason": esd012_chat["choices"][0][
                    "finish_reason"
                ],
                "esd012_completion_tokens": esd012_chat["usage"][
                    "completion_tokens"
                ],
                "esd012_json_parses": esd012_json_parses,
            },
        ),
        check(
            "minified_constraint_was_sent_but_not_obeyed",
            minified_prompt_seen and esd012_v4_failure,
            {
                "prompt_markers_seen": minified_prompt_seen,
                "esd012_still_pretty_printed_or_truncated": (
                    esd012_v4_failure
                ),
            },
        ),
        check(
            "historical_runs_preserved",
            raw_v1
            == {"requests": 14, "responses": 14, "crashes": 0}
            and raw_v2
            == {"requests": 14, "responses": 14, "crashes": 0}
            and raw_v3
            == {"requests": 14, "responses": 14, "crashes": 0},
            {"raw_v1": raw_v1, "raw_v2": raw_v2, "raw_v3": raw_v3},
        ),
        check(
            "ledger_56_and_forbidden_calls_zero",
            ledger["new_generation_budget"]["requests_used"] == 56
            and ledger["new_generation_budget"]["accounting_tokens_used"]
            == 458650
            and len(v4_records) == 14
            and ledger["new_generation_budget"]["judge_calls"] == 0
            and ledger["new_generation_budget"]["training_calls"] == 0
            and ledger["new_generation_budget"]["production_memory_writes"]
            == 0,
            {
                "requests_used": ledger["new_generation_budget"]["requests_used"],
                "accounting_tokens_used": ledger["new_generation_budget"][
                    "accounting_tokens_used"
                ],
                "v4_requests": len(v4_records),
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
        check(
            "runtime_unchanged",
            runtime["status"] == "QUALIFIED_NON_GENERATIVE"
            and all(runtime["checks"].values()),
            runtime["checks"],
        ),
    ]
    passed = sum(item["pass"] for item in checks)
    output = {
        "schema": "finrank_c3_verification_v1",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed": passed,
        "total": len(checks),
        "scores": frozen_score_split,
        "checks": checks,
    }
    write_json(PACKAGE / "C3_VERIFICATION.json", output)
    print(
        json.dumps(
            {
                "status": output["status"],
                "passed": passed,
                "total": len(checks),
                "scores": frozen_score_split,
            },
            sort_keys=True,
        )
    )
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
