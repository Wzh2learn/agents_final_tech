#!/usr/bin/env python3
"""Deterministic visible-rule FinRank development baseline."""

from __future__ import annotations

import json

from finrank_contract import (
    PACKAGE,
    classify_result,
    deterministic_consume,
    evidence_lookup,
    load_object,
    strong_rule_plan,
    validate_consume,
    validate_consumed_evidence,
    validate_plan,
    verify_bundle,
    write_json,
)


def main() -> int:
    verify_bundle(PACKAGE / "BUNDLE_C3_B0_V4_FIX1.json")
    actor_doc = load_object(PACKAGE / "TASKS_ACTOR_V3.json")
    reference_doc = load_object(PACKAGE / "REFERENCES_V3.json")
    tasks = {item["task_id"]: item for item in actor_doc["tasks"]}
    references = {
        item["task_id"]: item for item in reference_doc["tasks"]
    }
    results = []
    for task_id in actor_doc["task_order"]:
        task = tasks[task_id]
        plan = validate_plan(strong_rule_plan(task))
        tool_result = evidence_lookup(
            task,
            {"candidate_ids": plan["evidence_candidate_ids"]},
            tasks,
        )
        consume = validate_consume(deterministic_consume(task, tool_result))
        validate_consumed_evidence(consume, tool_result)
        results.append(
            classify_result(
                task_id,
                plan,
                tool_result,
                consume,
                references[task_id],
            )
        )
    success = sum(item["outcome"] == "SUCCESS" for item in results)
    output = {
        "schema": "finrank_strong_rule_result_v2",
        "status": "COMPLETE_DETERMINISTIC_DEVELOPMENT_BASELINE",
        "plan_time_visibility": actor_doc["plan_time_visibility"],
        "generation_requests": 0,
        "rule_signals": [
            "visible_target_entity",
            "content_period_not_metadata_only",
            "question_term_overlap",
            "table_metric_presence",
        ],
        "success_count": success,
        "non_success_count": len(results) - success,
        "results": results,
    }
    write_json(PACKAGE / "results" / "STRONG_RULE_RESULT_C3.json", output)
    print(
        json.dumps(
            {
                "status": output["status"],
                "success": success,
                "non_success": output["non_success_count"],
                "generation_requests": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
