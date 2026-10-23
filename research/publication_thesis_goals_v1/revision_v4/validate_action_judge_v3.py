"""Apply deterministic non-degeneracy gates to the auxiliary action judge."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(row: dict[str, Any]) -> dict[str, Any]:
    judge = row["judge"] or {}
    answer = str(row.get("answer") or "").strip()
    reasons = []
    if not answer:
        reasons.append("EMPTY_ANSWER_CANNOT_BE_ACTION_SUCCESS")
    if judge.get("safe_unknown") is True:
        reasons.append("SAFE_UNKNOWN_IS_NOT_A_CONCRETE_ACTION_SUCCESS")
    for field in (
        "action_state_aligned", "stale_action_rejected",
        "evidence_consistent", "non_generic",
    ):
        if judge.get(field) is not True:
            reasons.append(f"JUDGE_CONDITION_FALSE:{field}")
    return {
        "raw_judge_pass": judge.get("pass") is True,
        "validated_action_pass": not reasons,
        "validation_reasons": reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = load(args.results)
    rows = [{**row, "validated": validate(row)} for row in source["rows"]]
    by_arm = {}
    for arm in sorted({row["arm"] for row in rows}):
        group = [row for row in rows if row["arm"] == arm]
        primary = [row for row in group if row["retrieval_category"] == "BOTH_OLD_AND_NEW"]
        by_arm[arm] = {
            "rows": len(group),
            "raw_judge_pass": sum(row["validated"]["raw_judge_pass"] for row in group),
            "validated_action_pass": sum(
                row["validated"]["validated_action_pass"] for row in group
            ),
            "validated_action_rate": round(
                sum(row["validated"]["validated_action_pass"] for row in group) / len(group), 4
            ),
            "primary_rows": len(primary),
            "validated_action_pass_primary": sum(
                row["validated"]["validated_action_pass"] for row in primary
            ),
            "validated_action_rate_primary": (
                round(
                    sum(row["validated"]["validated_action_pass"] for row in primary)
                    / len(primary),
                    4,
                )
                if primary else None
            ),
            "validation_removals": dict(Counter(
                reason
                for row in group
                for reason in row["validated"]["validation_reasons"]
            )),
        }
    output = {
        "schema": "stale_action_judge_validated_v3",
        "date": "2026-10-23",
        "evidence_identity": "DETERMINISTIC_NONDEGENERACY_GATE_OVER_AUXILIARY_LLM_JUDGE",
        "validation_rule": (
            "non-empty answer AND action_state_aligned AND stale_action_rejected "
            "AND evidence_consistent AND non_generic AND NOT safe_unknown"
        ),
        "summary_by_arm": by_arm,
        "rows": rows,
        "nonclaims": [
            "This gate removes judge contradictions but is not human gold.",
            "The underlying action judge remains auxiliary and model-based.",
        ],
    }
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(by_arm, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
