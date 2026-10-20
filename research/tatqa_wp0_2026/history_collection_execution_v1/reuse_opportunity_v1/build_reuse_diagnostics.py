#!/usr/bin/env python3
"""Build trajectory classification and invented-lesson-free history contexts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from trajectory_classifier import action_change, classify_trajectory


FIXTURE_TASK_IDS = {"X01", "X02", "X03"}


def has_key(value: Any, names: set[str]) -> bool:
    if isinstance(value, dict):
        return any(
            key in names or has_key(child, names)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(has_key(child, names) for child in value)
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execution-result", required=True, type=Path)
    parser.add_argument("--source-manifest", required=True, type=Path)
    parser.add_argument("--classification-output", required=True, type=Path)
    parser.add_argument("--context-output", required=True, type=Path)
    args = parser.parse_args()
    result = json.loads(args.execution_result.read_text(encoding="utf-8"))
    source = json.loads(args.source_manifest.read_text(encoding="utf-8"))
    task_meta = {row["task_id"]: row for row in source["tasks"]}
    by_task = {}
    for row in result["results"]:
        by_task.setdefault(row["task_id"], []).append(row)
    classified = []
    contexts = []
    for task_id in sorted(by_task):
        attempts = by_task[task_id]
        rows = [
            classify_trajectory(
                attempt,
                raw_complete=attempt["status"] == "COMPLETE",
                is_fixture=task_id in FIXTURE_TASK_IDS,
            )
            for attempt in attempts
        ]
        classified.extend(rows)
        if task_id.startswith("H") and task_id in task_meta:
            meta = task_meta[task_id]
            change = (
                action_change(attempts[0], attempts[1])
                if len(attempts) == 2
                else "NO_FOLLOWUP"
            )
            for row in rows:
                row["post_feedback_action_change"] = change
            contexts.append({
                "experience_id": task_id,
                "task": meta["actor_task"],
                "actual_attempts": [
                    {
                        "attempt": attempt["attempt"],
                        "operation": attempt["plan"],
                        "tool_return": attempt["tool_result"],
                        "actual_answer": attempt["consume"],
                        "feedback": attempt["feedback_category"],
                    }
                    for attempt in attempts
                ],
                "post_feedback_action_change": change,
                "raw_complete": all(row["raw_complete"] for row in rows),
            })
    classification = {
        "schema": "trajectory_classification_v1",
        "counts": {
            "results": len(classified),
            "complete": sum(row["trajectory_complete"] for row in classified),
            "reference_match": sum(row["answer_reference_match"] is True for row in classified),
            "tool_success": sum(row["tool_execution_success"] for row in classified),
            "answer_tool_consistent": sum(row["answer_tool_consistency"] is True for row in classified),
        },
        "rows": classified,
    }
    context_pool = {
        "schema": "reuse_history_context_pool_v1",
        "status": "HISTORY_CONTEXTS_WITHOUT_INVENTED_LESSONS",
        "experience_count": len(contexts),
        "contains_hardcoded_lesson": has_key(contexts, {"lesson"}),
        "contains_hidden_reference": has_key(contexts, {"hidden_reference"}),
        "contains_future_answer": has_key(contexts, {"future", "expected_answer", "ground_truth", "gold"}),
        "contains_fabricated_correction": has_key(contexts, {"correction", "fabricated_correction"}),
        "experiences": contexts,
    }
    with args.classification_output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(classification, ensure_ascii=False, indent=2) + "\n")
    with args.context_output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(context_pool, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "classified": len(classified),
        "contexts": len(contexts),
        "contains_hardcoded_lesson": context_pool["contains_hardcoded_lesson"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
