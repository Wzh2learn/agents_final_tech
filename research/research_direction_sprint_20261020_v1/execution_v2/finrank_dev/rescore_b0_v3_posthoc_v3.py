#!/usr/bin/env python3
"""Post-hoc V3 rescore with literal/explicit derived-tool consistency."""

from __future__ import annotations

import json

from finrank_contract import (
    PACKAGE,
    classify_result,
    load_object,
    write_json,
)


def main() -> int:
    result_path = (
        PACKAGE
        / "results"
        / "B0_V3_EQUAL_VISIBILITY"
        / "B0_RESULT.json"
    )
    prior_posthoc_path = (
        PACKAGE
        / "results"
        / "B0_V3_EQUAL_VISIBILITY"
        / "B0_RESULT_POSTHOC_SCORER_V2.json"
    )
    original = load_object(result_path)
    prior_posthoc = load_object(prior_posthoc_path)
    reference_doc = load_object(PACKAGE / "REFERENCES_V3.json")
    references = {
        item["task_id"]: item for item in reference_doc["tasks"]
    }
    prior_results = {
        item["task_id"]: item for item in prior_posthoc["results"]
    }
    results = []
    consistency_changes = []
    outcome_changes_from_prior_posthoc = []
    for prior in original["results"]:
        task_id = prior["task_id"]
        current = classify_result(
            task_id,
            prior["plan"],
            prior["tool_result"],
            prior["consume"],
            references[task_id],
        )
        current["original_outcome"] = prior["outcome"]
        current["unit_fixed_posthoc_outcome"] = prior_results[task_id][
            "posthoc_outcome"
        ]
        current["posthoc_v3_outcome"] = current["outcome"]
        current["original_consistency"] = prior["answer_tool_consistency"]
        current["recomputed_consistency"] = current["answer_tool_consistency"]
        if (
            prior["answer_tool_consistency"]
            != current["answer_tool_consistency"]
        ):
            consistency_changes.append(task_id)
        if (
            prior_results[task_id]["posthoc_outcome"]
            != current["posthoc_v3_outcome"]
        ):
            outcome_changes_from_prior_posthoc.append(task_id)
        results.append(current)
    success = sum(
        item["posthoc_v3_outcome"] == "SUCCESS" for item in results
    )
    esd006 = next(item for item in results if item["task_id"] == "ESD_006")
    esd012 = next(item for item in results if item["task_id"] == "ESD_012")
    output = {
        "schema": "finrank_b0_v3_posthoc_scorer_v3",
        "status": "POSTHOC_DIAGNOSTIC_NOT_FROZEN_BASELINE",
        "generation_requests": 0,
        "source_result_sha256": __import__("hashlib").sha256(
            result_path.read_bytes()
        ).hexdigest(),
        "checker_changes": [
            "LITERAL_PERCENT_UNIT_ALIAS",
            "LITERAL_EVIDENCE_OR_EXPLICIT_REFERENCE_DERIVATION_ONLY",
        ],
        "scores": {
            "original_frozen": original["success_count"],
            "unit_fix_posthoc": prior_posthoc["posthoc"]["success_count"],
            "full_checker_posthoc_v3": success,
        },
        "consistency_changed_tasks": consistency_changes,
        "outcome_changes_from_unit_fix_posthoc": (
            outcome_changes_from_prior_posthoc
        ),
        "preserved_non_successes": {
            "ESD_006": {
                "outcome": esd006["posthoc_v3_outcome"],
                "answer_status": esd006["consume"]["answer_status"],
                "reason": "SUFFICIENT_EVIDENCE_ACTUAL_UNKNOWN",
            },
            "ESD_012": {
                "outcome": esd012["posthoc_v3_outcome"],
                "reason": "TRUNCATED_MODEL_JSON_NOT_REPAIRED",
            },
        },
        "results": results,
    }
    if esd006["posthoc_v3_outcome"] != "NON_SUCCESS":
        raise RuntimeError("ESD_006_must_remain_non_success")
    if esd012["posthoc_v3_outcome"] != "NON_SUCCESS":
        raise RuntimeError("ESD_012_must_remain_non_success")
    write_json(
        PACKAGE
        / "results"
        / "B0_V3_EQUAL_VISIBILITY"
        / "B0_RESULT_POSTHOC_SCORER_V3.json",
        output,
    )
    print(
        json.dumps(
            {
                "status": output["status"],
                "scores": output["scores"],
                "consistency_changed_tasks": consistency_changes,
                "outcome_changes_from_unit_fix_posthoc": (
                    outcome_changes_from_prior_posthoc
                ),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
