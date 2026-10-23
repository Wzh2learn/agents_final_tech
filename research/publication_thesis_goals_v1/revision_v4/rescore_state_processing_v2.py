"""Rescore preserved comparison rows with the corrected text-only criteria."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from stale_semantic_evaluation_v2 import evaluate_answer, match_group
from state_processing_comparison_v2 import current_intermediate_text


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def maybe_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = load(args.results)
    data = {item["uid"]: item for item in load(args.data)}
    references = load(args.reference)["items"]
    rows = []
    for original in result["rows"]:
        uid = original["uid"]
        reference = references[uid]
        parsed_intermediate = maybe_json(original.get("intermediate_text", ""))
        current_text = current_intermediate_text(original["arm"], parsed_intermediate)
        matched = [
            index
            for index, group in enumerate(reference["required_concept_groups"])
            if match_group(group, current_text)
        ]
        lowered = current_text.lower()
        affirms_old = any(
            term.lower() in lowered for term in reference["old_state_concepts"]
        ) and not re.search(
            r"no longer|rather than|instead|old|previous|returned|changed|cleared",
            lowered,
        )
        rows.append({
            **{key: original[key] for key in ("uid", "type", "arm", "selected_indices", "answer")},
            "current_intermediate_text": current_text,
            "intermediate_specificity": {
                "success": bool(matched) and not affirms_old,
                "matched_required_groups": matched,
                "affirms_old_state": affirms_old,
            },
            "semantic": evaluate_answer(
                original.get("answer") or "",
                data[uid],
                reference,
                original.get("selected_indices", []),
            ),
        })
    by_arm = {}
    for arm in sorted({row["arm"] for row in rows}):
        group = [row for row in rows if row["arm"] == arm]
        by_arm[arm] = {
            "count": len(group),
            "semantic_success": sum(row["semantic"]["semantic_success"] for row in group),
            "semantic_rate": round(
                sum(row["semantic"]["semantic_success"] for row in group) / len(group), 4
            ),
            "intermediate_specificity_success": sum(
                row["intermediate_specificity"]["success"] for row in group
            ),
            "relation_counts": dict(Counter(row["semantic"]["relation"] for row in group)),
        }
    output = {
        "schema": "state_processing_comparison_rescored_v2",
        "date": "2026-10-23",
        "evidence_identity": "POST_HOC_CORRECTED_TEXT_AND_EVIDENCE_RESCORE_OF_FROZEN_GENERATIONS",
        "source_results": str(args.results),
        "changes_from_original_scoring": [
            "Intermediate specificity uses current facts/new state only, not preserved past facts.",
            "Completed-return wording is treated as replacement evidence rather than old-state affirmation.",
            "Final semantic success remains answer-text and evidence-grounded and ignores self-labels/cards.",
        ],
        "summary_by_arm": by_arm,
        "rows": rows,
        "nonclaims": [
            "No model request was made by this rescore.",
            "The reference remains AI-assisted development material, not human gold.",
            "The corrected scorer was developed after inspecting failures and is not a frozen confirmatory metric.",
        ],
    }
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(by_arm, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
