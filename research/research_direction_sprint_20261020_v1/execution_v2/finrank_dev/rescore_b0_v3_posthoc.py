#!/usr/bin/env python3
"""Zero-request post-hoc rescore of B0 V3 after unit-alias repair."""

from __future__ import annotations

import json

from finrank_contract import (
    PACKAGE,
    classify_result,
    load_object,
    write_json,
)


def main() -> int:
    original = load_object(
        PACKAGE / "results" / "B0_V3_EQUAL_VISIBILITY" / "B0_RESULT.json"
    )
    references_doc = load_object(PACKAGE / "REFERENCES_V2.json")
    references = {
        item["task_id"]: item for item in references_doc["tasks"]
    }
    posthoc_results = []
    changed = []
    for prior in original["results"]:
        task_id = prior["task_id"]
        current = classify_result(
            task_id,
            prior["plan"],
            prior["tool_result"],
            prior["consume"],
            references[task_id],
        )
        task_error = prior.get("task_error")
        if str(task_error).startswith("schema_or_contract:model_json_invalid"):
            current["failure_layer"] = "MODEL_OUTPUT_FORMAT"
        elif current["error_class"] == "SEMANTIC_SELECTION_OR_ANSWER":
            current["failure_layer"] = "SEMANTIC_SELECTION_OR_ANSWER"
        elif current["error_class"] == "ENGINEERING_SCHEMA_OR_TOOL":
            current["failure_layer"] = "ENGINEERING_SCHEMA_OR_TOOL"
        else:
            current["failure_layer"] = None
        current["original_outcome"] = prior["outcome"]
        current["posthoc_outcome"] = current["outcome"]
        current["task_error"] = task_error
        if prior["outcome"] != current["outcome"]:
            changed.append(
                {
                    "task_id": task_id,
                    "from": prior["outcome"],
                    "to": current["outcome"],
                    "reason": "LITERAL_PERCENT_UNIT_ALIAS_SCORER_FIX",
                }
            )
        posthoc_results.append(current)
    posthoc_success = sum(
        item["posthoc_outcome"] == "SUCCESS" for item in posthoc_results
    )
    esd006 = next(
        item for item in posthoc_results if item["task_id"] == "ESD_006"
    )
    esd012 = next(
        item for item in posthoc_results if item["task_id"] == "ESD_012"
    )
    output = {
        "schema": "finrank_b0_v3_posthoc_scorer_v2",
        "status": "POSTHOC_DIAGNOSTIC_NOT_FROZEN_BASELINE",
        "generation_requests": 0,
        "source_result_sha256": __import__("hashlib").sha256(
            (
                PACKAGE
                / "results"
                / "B0_V3_EQUAL_VISIBILITY"
                / "B0_RESULT.json"
            ).read_bytes()
        ).hexdigest(),
        "scorer_change": {
            "scope": "LITERAL_PERCENT_UNIT_ALIAS_ONLY",
            "before": '_unit_matches("%", "percent") == False',
            "after": '_unit_matches("%", "percent") == True',
        },
        "original_frozen": {
            "success_count": original["success_count"],
            "non_success_count": original["non_success_count"],
        },
        "posthoc": {
            "success_count": posthoc_success,
            "non_success_count": len(posthoc_results) - posthoc_success,
        },
        "changed_tasks": changed,
        "preserved_non_successes": {
            "ESD_006": {
                "outcome": esd006["posthoc_outcome"],
                "answer_status": esd006["consume"]["answer_status"],
                "reason": "SUFFICIENT_EVIDENCE_ACTUAL_UNKNOWN_NOT_RESCORED",
            },
            "ESD_012": {
                "outcome": esd012["posthoc_outcome"],
                "failure_layer": esd012["failure_layer"],
                "reason": "TRUNCATED_MODEL_JSON_NOT_REPAIRED",
            },
        },
        "results": posthoc_results,
    }
    if changed != [
        {
            "task_id": "ESD_004",
            "from": "NON_SUCCESS",
            "to": "SUCCESS",
            "reason": "LITERAL_PERCENT_UNIT_ALIAS_SCORER_FIX",
        }
    ]:
        raise RuntimeError(f"unexpected_posthoc_changes:{changed}")
    if esd006["posthoc_outcome"] != "NON_SUCCESS":
        raise RuntimeError("ESD_006_must_remain_non_success")
    if esd012["failure_layer"] != "MODEL_OUTPUT_FORMAT":
        raise RuntimeError("ESD_012_failure_layer_invalid")
    write_json(
        PACKAGE
        / "results"
        / "B0_V3_EQUAL_VISIBILITY"
        / "B0_RESULT_POSTHOC_SCORER_V2.json",
        output,
    )
    print(
        json.dumps(
            {
                "status": output["status"],
                "original_success": original["success_count"],
                "posthoc_success": posthoc_success,
                "changed": changed,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
