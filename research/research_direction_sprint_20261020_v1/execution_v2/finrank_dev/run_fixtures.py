#!/usr/bin/env python3
"""Offline fixtures for the FinRank plan/lookup/consume contract."""

from __future__ import annotations

import json
import re
from typing import Any

from finrank_contract import (
    PACKAGE,
    answer_reference_match,
    answer_tool_consistency,
    candidate_visibility_sha256,
    classify_result,
    evidence_lookup,
    evidence_sufficiency,
    load_object,
    plan_visible_candidates,
    render_messages,
    strict_json_object,
    validate_consume,
    validate_consumed_evidence,
    validate_plan,
    validate_reference_separation,
    verify_bundle,
    write_json,
)


def expect_error(function, expected: str) -> dict[str, Any]:
    try:
        function()
    except ValueError as exc:
        return {
            "pass": expected in str(exc),
            "expected": expected,
            "actual": str(exc),
        }
    return {
        "pass": False,
        "expected": expected,
        "actual": "NO_ERROR",
    }


def main() -> int:
    verify_bundle(PACKAGE / "BUNDLE_C3_B0_V4_FIX1.json")
    actor_doc = load_object(PACKAGE / "TASKS_ACTOR_V2.json")
    reference_v2_doc = load_object(PACKAGE / "REFERENCES_V2.json")
    reference_doc = load_object(PACKAGE / "REFERENCES_V3.json")
    reference_v1_doc = load_object(PACKAGE / "REFERENCES_V1.json")
    tasks = {item["task_id"]: item for item in actor_doc["tasks"]}
    references = {
        item["task_id"]: item for item in reference_doc["tasks"]
    }
    references_v1 = {
        item["task_id"]: item for item in reference_v1_doc["tasks"]
    }
    references_v2 = {
        item["task_id"]: item for item in reference_v2_doc["tasks"]
    }
    cases: list[dict[str, Any]] = []

    legal = evidence_lookup(
        tasks["ESD_003"],
        {"candidate_ids": ["cand_007", "cand_006"]},
        tasks,
    )
    cases.append(
        {
            "name": "legal_lookup_request_order",
            "pass": legal["tool_status"] == "OK"
            and [item["candidate_id"] for item in legal["evidence"]]
            == ["cand_007", "cand_006"],
            "observed": legal,
        }
    )
    invalid = evidence_lookup(
        tasks["ESD_001"],
        {"candidate_ids": []},
        tasks,
    )
    cases.append(
        {
            "name": "invalid_empty_lookup",
            "pass": invalid["tool_status"] == "INVALID_ARGUMENT"
            and invalid["error"] == "lookup_count_out_of_range",
            "observed": invalid,
        }
    )
    cross = evidence_lookup(
        tasks["ESD_001"],
        {"candidate_ids": ["cand_007"]},
        tasks,
    )
    cases.append(
        {
            "name": "cross_task_id_rejected",
            "pass": cross["error"] == "cross_task_candidate_id",
            "observed": cross,
        }
    )
    duplicate = evidence_lookup(
        tasks["ESD_001"],
        {"candidate_ids": ["cand_001", "cand_001"]},
        tasks,
    )
    cases.append(
        {
            "name": "duplicate_id_rejected",
            "pass": duplicate["error"] == "lookup_duplicate_candidate_id",
            "observed": duplicate,
        }
    )
    extra = evidence_lookup(
        tasks["ESD_001"],
        {"candidate_ids": ["cand_001"], "gold": True},
        tasks,
    )
    cases.append(
        {
            "name": "extra_key_rejected",
            "pass": extra["error"].startswith("lookup_input_keys_invalid"),
            "observed": extra,
        }
    )
    out_of_range = evidence_lookup(
        tasks["ESD_001"],
        {"candidate_ids": [f"cand_{index:03d}" for index in range(1, 10)]},
        tasks,
    )
    cases.append(
        {
            "name": "out_of_range_lookup_count",
            "pass": out_of_range["error"] == "lookup_count_out_of_range",
            "observed": out_of_range,
        }
    )

    esd002 = tasks["ESD_002"]
    cand004_years = set(
        __import__("re").findall(
            r"\b20\d{2}\b",
            next(
                item["text"]
                for item in esd002["actor_view"]["candidates"]
                if item["candidate_id"] == "cand_004"
            ),
        )
    )
    strong_ids = __import__("finrank_contract", fromlist=["strong_rule_plan"]).strong_rule_plan(
        esd002
    )["evidence_candidate_ids"]
    cases.append(
        {
            "name": "same_form_different_content_period",
            "pass": not {"2024"} <= cand004_years
            and "cand_004" not in strong_ids
            and "cand_001" in strong_ids,
            "observed": {
                "cand_004_content_years": sorted(cand004_years),
                "strong_rule_ids": strong_ids,
            },
        }
    )

    esd010 = references["ESD_010"]
    subset_only = evidence_sufficiency(["cand_003"], esd010)
    subset_plus_optional = evidence_sufficiency(
        ["cand_003", "cand_007"],
        esd010,
    )
    cases.append(
        {
            "name": "ESD_010_sufficient_subset",
            "pass": subset_only["sufficient"]
            and subset_only["scope_precision"]
            and subset_plus_optional["sufficient"]
            and subset_plus_optional["optional_redundant_used"] == ["cand_007"],
            "observed": {
                "subset_only": subset_only,
                "subset_plus_optional": subset_plus_optional,
            },
        }
    )

    task = tasks["ESD_001"]
    messages = render_messages("plan", task, None)
    actor_view = {
        "task_id": task["task_id"],
        **task["actor_view"],
    }
    try:
        validate_reference_separation(actor_view, messages)
        leak_pass = True
        leak_error = None
    except ValueError as exc:
        leak_pass = False
        leak_error = str(exc)
    complete_schema_visible = all(
        token in messages[1]["content"]
        for token in (
            '"plan"',
            '"evidence_lookup_input"',
            '"evidence_lookup_output"',
            '"consume"',
            '"candidate_id"',
            '"visible_source_scope"',
        )
    )
    cases.append(
        {
            "name": "full_schema_visible_no_reference_leak",
            "pass": leak_pass and complete_schema_visible,
            "observed": {
                "leak_error": leak_error,
                "complete_schema_visible": complete_schema_visible,
            },
        }
    )

    tool_result = {
        "tool_status": "OK",
        "evidence": [
            {
                "candidate_id": "cand_001",
                "text": "Cash and time deposits $12,471 million",
                "page_number": "67",
                "visible_source_scope": {},
            }
        ],
    }
    consume = {
        "answer_status": "ANSWER",
        "facts": [
            {
                "label": "cash and time deposits",
                "value": 12471,
                "unit": "USD million",
                "period": "2024-12-31",
            }
        ],
        "used_candidate_ids": ["cand_002"],
    }
    cases.append(
        {
            "name": "consume_cannot_cite_absent_evidence",
            "pass": bool(
                expect_error(
                    lambda: validate_consumed_evidence(consume, tool_result),
                    "consume_cites_absent_evidence",
                )["pass"]
            ),
        }
    )
    non_answer = {
        "answer_status": "UNKNOWN",
        "facts": [
            {
                "label": "x",
                "value": 1,
                "unit": None,
                "period": None,
            }
        ],
        "used_candidate_ids": ["cand_001"],
    }
    cases.append(
        {
            "name": "unknown_rejects_numeric_facts",
            "pass": bool(
                expect_error(
                    lambda: validate_consume(non_answer),
                    "non_answer_facts_must_be_empty",
                )["pass"]
            ),
        }
    )

    valid_plan = validate_plan(
        {"experience_actions": [], "evidence_candidate_ids": ["cand_001"]}
    )
    valid_consume = validate_consume(
        {
            "answer_status": "UNKNOWN",
            "facts": [],
            "used_candidate_ids": ["cand_001"],
        }
    )
    validate_consumed_evidence(valid_consume, tool_result)
    cases.append(
        {
            "name": "valid_plan_and_nonanswer_consume",
            "pass": valid_plan["evidence_candidate_ids"] == ["cand_001"]
            and valid_consume["answer_status"] == "UNKNOWN",
        }
    )
    direct_plan = {
        "experience_actions": [],
        "evidence_candidate_ids": ["cand_001"],
    }
    wrapped_plan_error = expect_error(
        lambda: validate_plan({"plan": direct_plan}),
        "plan_keys_invalid",
    )
    cases.append(
        {
            "name": "plan_direct_positive_wrapper_negative",
            "pass": validate_plan(direct_plan) == direct_plan
            and wrapped_plan_error["pass"],
            "observed": {
                "direct_valid": True,
                "wrapper_error": wrapped_plan_error,
            },
        }
    )
    direct_consume = {
        "answer_status": "UNKNOWN",
        "facts": [],
        "used_candidate_ids": [],
    }
    wrapped_consume_error = expect_error(
        lambda: validate_consume({"consume": direct_consume}),
        "consume_keys_invalid",
    )
    cases.append(
        {
            "name": "consume_direct_positive_wrapper_negative",
            "pass": validate_consume(direct_consume) == direct_consume
            and wrapped_consume_error["pass"],
            "observed": {
                "direct_valid": True,
                "wrapper_error": wrapped_consume_error,
            },
        }
    )
    plan_message = render_messages(
        "plan",
        tasks["ESD_001"],
        None,
    )[1]["content"]
    consume_message = render_messages(
        "consume",
        tasks["ESD_001"],
        tool_result,
    )[1]["content"]
    cases.append(
        {
            "name": "prompt_forbids_stage_wrappers",
            "pass": "without a `plan` wrapper" in plan_message
            and "without a `consume` wrapper" in consume_message,
            "observed": {
                "plan_instruction_present": "without a `plan` wrapper"
                in plan_message,
                "consume_instruction_present": "without a `consume` wrapper"
                in consume_message,
            },
        }
    )
    task_payload_match = re.search(
        r"TASK_AND_VISIBLE_EVIDENCE=(.*?)\nChoose candidate IDs",
        plan_message,
        re.DOTALL,
    )
    task_payload = (
        json.loads(task_payload_match.group(1))
        if task_payload_match is not None
        else {}
    )
    expected_visible = plan_visible_candidates(task)
    source_visible = [
        {
            "candidate_id": item["candidate_id"],
            "text": item["text"],
            "page_number": item["page_number"],
            "visible_source_scope": item["visible_source_scope"],
        }
        for item in task["actor_view"]["candidates"]
    ]
    cases.append(
        {
            "name": "equal_plan_time_candidate_visibility",
            "pass": actor_doc["plan_time_visibility"]["policy"]
            == "FULL_VISIBLE_CANDIDATES_AT_PLAN"
            and task_payload.get("candidates") == expected_visible
            and expected_visible == source_visible
            and task_payload.get("candidate_visibility_sha256")
            == candidate_visibility_sha256(task)
            and all(item["text"] for item in expected_visible),
            "observed": {
                "policy": actor_doc["plan_time_visibility"]["policy"],
                "candidate_count": len(expected_visible),
                "candidate_text_chars": sum(
                    len(item["text"]) for item in expected_visible
                ),
                "prompt_matches_strong_rule_input": task_payload.get("candidates")
                == expected_visible,
                "visibility_sha256": candidate_visibility_sha256(task),
            },
        }
    )
    esd006_consume = validate_consume(
        {
            "answer_status": "ANSWER",
            "facts": [
                {
                    "label": "GM Automotive Gross Profit (2024)",
                    "value": 20541,
                    "unit": "million USD",
                    "period": "2024",
                },
                {
                    "label": "GM Automotive Gross Margin Percentage (2024)",
                    "value": 11.97,
                    "unit": "percent",
                    "period": "2024",
                },
            ],
            "used_candidate_ids": ["cand_005"],
        }
    )
    esd006_v1_match = answer_reference_match(
        esd006_consume,
        references_v1["ESD_006"],
    )
    esd006_v2_match = answer_reference_match(
        esd006_consume,
        references_v2["ESD_006"],
    )
    cases.append(
        {
            "name": "ESD_006_v1_v2_answer_scope_difference",
            "pass": not esd006_v1_match["match"]
            and set(esd006_v1_match["missing_atoms"])
            == {"automotive_revenue", "automotive_other_cost"}
            and esd006_v2_match["match"]
            and [
                item["name"]
                for item in references["ESD_006"]["answer_atoms"]
            ]
            == ["derived_gross_profit", "derived_gross_margin"]
            and [
                item["name"]
                for item in references["ESD_006"]["operand_facts"]
            ]
            == ["automotive_revenue", "automotive_other_cost"],
            "observed": {
                "v1_match": esd006_v1_match,
                "v2_match": esd006_v2_match,
                "v2_required": [
                    item["name"]
                    for item in references["ESD_006"]["answer_atoms"]
                ],
                "v2_operand_facts": [
                    item["name"]
                    for item in references["ESD_006"]["operand_facts"]
                ],
            },
        }
    )
    esd004_consume = validate_consume(
        {
            "answer_status": "ANSWER",
            "facts": [
                {
                    "label": "ROE 2024",
                    "value": 8.7,
                    "unit": "%",
                    "period": "2024",
                },
                {
                    "label": "ROIC-adjusted 2024",
                    "value": 20.8,
                    "unit": "%",
                    "period": "2024",
                },
            ],
            "used_candidate_ids": ["cand_005", "cand_003"],
        }
    )
    esd004_match = answer_reference_match(
        esd004_consume,
        references["ESD_004"],
    )
    cases.append(
        {
            "name": "literal_percent_matches_percent",
            "pass": esd004_match["match"]
            and not esd004_match["missing_atoms"],
            "observed": esd004_match,
        }
    )
    margin_fact = {
        "answer_status": "ANSWER",
        "facts": [
            {
                "label": "GM Automotive Gross Margin Percentage (2024)",
                "value": 11.97,
                "unit": "percent",
                "period": "2024",
            }
        ],
        "used_candidate_ids": ["cand_005"],
    }
    false_pair_consistency = answer_tool_consistency(
        margin_fact,
        {
            "tool_status": "OK",
            "evidence": [
                {
                    "candidate_id": "cand_005",
                    "text": "Unrelated values 10127 and 846",
                    "page_number": "54-55",
                    "visible_source_scope": {},
                }
            ],
        },
        references["ESD_006"],
    )
    explicit_derivation_consistency = answer_tool_consistency(
        margin_fact,
        {
            "tool_status": "OK",
            "evidence": [
                {
                    "candidate_id": "cand_005",
                    "text": (
                        "Automotive revenue 171606 cost of sales 151065"
                    ),
                    "page_number": "54-55",
                    "visible_source_scope": {},
                }
            ],
        },
        references["ESD_006"],
    )
    cases.append(
        {
            "name": "explicit_derivation_rejects_false_pair_support",
            "pass": not false_pair_consistency["consistent"]
            and explicit_derivation_consistency["consistent"],
            "observed": {
                "false_pair": false_pair_consistency,
                "explicit_derivation": explicit_derivation_consistency,
            },
        }
    )
    minified_markers = (
        "minified JSON",
        "no whitespace outside string values",
        "Do not pretty-print",
        "Markdown fences",
    )
    cases.append(
        {
            "name": "plan_and_consume_require_minified_json",
            "pass": all(
                marker in plan_message for marker in minified_markers
            )
            and all(
                marker in consume_message for marker in minified_markers
            ),
            "observed": {
                "plan_markers": {
                    marker: marker in plan_message
                    for marker in minified_markers
                },
                "consume_markers": {
                    marker: marker in consume_message
                    for marker in minified_markers
                },
            },
        }
    )
    esd006_unknown = validate_consume(
        {
            "answer_status": "UNKNOWN",
            "facts": [],
            "used_candidate_ids": ["cand_005"],
        }
    )
    esd006_unknown_match = answer_reference_match(
        esd006_unknown,
        references["ESD_006"],
    )
    cases.append(
        {
            "name": "ESD_006_UNKNOWN_remains_non_success",
            "pass": not esd006_unknown_match["match"]
            and set(esd006_unknown_match["missing_atoms"])
            == {"derived_gross_profit", "derived_gross_margin"},
            "observed": esd006_unknown_match,
        }
    )
    passed = sum(bool(item["pass"]) for item in cases)
    output = {
        "schema": "finrank_c3_fixture_receipt_v1",
        "status": "PASS" if passed == len(cases) else "FAIL",
        "generation_requests": 0,
        "passed": passed,
        "total": len(cases),
        "cases": cases,
    }
    write_json(PACKAGE / "FIXTURE_RECEIPT_C3.json", output)
    print(json.dumps({"status": output["status"], "passed": passed, "total": len(cases)}))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
