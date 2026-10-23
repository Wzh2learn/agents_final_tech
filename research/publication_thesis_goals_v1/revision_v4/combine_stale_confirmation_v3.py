"""Combine complete arm outputs while keeping engineering overhead separate."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


FINAL_ARMS = (
    "direct_answer",
    "one_call_facts",
    "two_stage_timeline",
    "two_stage_state_card",
)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--resume", type=Path, required=True)
    parser.add_argument("--statecard", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base = load(args.base)
    resume = load(args.resume)
    statecard = load(args.statecard)
    rows = [
        row for row in base["rows"] if row["arm"] != "two_stage_state_card"
    ] + list(resume["rows"]) + list(statecard["rows"])
    for arm in FINAL_ARMS:
        arm_rows = [row for row in rows if row["arm"] == arm]
        uids = [row["uid"] for row in arm_rows]
        if len(uids) != 16 or len(set(uids)) != 16:
            raise ValueError(f"incomplete arm {arm}: {len(uids)} rows")
    final_arm_tokens = (
        base["summary"]["by_arm"]["direct_answer"]["accounting_tokens"]
        + base["summary"]["by_arm"]["one_call_facts"]["accounting_tokens"]
        + base["summary"]["by_arm"]["two_stage_timeline"]["accounting_tokens"]
        + resume["summary"]["by_arm"]["direct_answer"]["accounting_tokens"]
        + resume["summary"]["by_arm"]["one_call_facts"]["accounting_tokens"]
        + resume["summary"]["by_arm"]["two_stage_timeline"]["accounting_tokens"]
        + statecard["summary"]["by_arm"]["two_stage_state_card"]["accounting_tokens"]
    )
    total_tokens = (
        base["summary"]["overall"]["accounting_tokens"]
        + resume["summary"]["overall"]["accounting_tokens"]
        + statecard["summary"]["overall"]["accounting_tokens"]
    )
    retrieval_rows = []
    seen = set()
    for row in rows:
        if row["uid"] not in seen:
            seen.add(row["uid"])
            retrieval_rows.append(row)
    retrieval_counts = dict(Counter(row["retrieval_category"] for row in retrieval_rows))
    by_arm = {}
    for arm in FINAL_ARMS:
        group = [row for row in rows if row["arm"] == arm]
        primary = [row for row in group if row["retrieval_category"] == "BOTH_OLD_AND_NEW"]
        by_arm[arm] = {
            "rows": len(group),
            "auto_semantic_success": sum(row["semantic"]["semantic_success"] for row in group),
            "primary_rows": len(primary),
            "auto_semantic_success_primary": sum(
                row["semantic"]["semantic_success"] for row in primary
            ),
            "safe_unknown": sum(row["semantic"]["safe_unknown"] for row in group),
            "intermediate_specificity_success": sum(
                row["intermediate_specificity"]["success"] for row in group
            ),
        }
    output = {
        "schema": "stale_retrieval_state_confirmation_combined_v3",
        "date": "2026-10-23",
        "evidence_identity": "ENGINEERING_REPAIRED_NON_ORACLE_CONFIRMATION_WITH_AUTO_DIAGNOSTIC_ONLY",
        "source_results": {
            "base": str(args.base),
            "resume": str(args.resume),
            "statecard": str(args.statecard),
        },
        "final_comparison": {
            "uids": 16,
            "arms": list(FINAL_ARMS),
            "planned_calls": 96,
            "final_arm_accounting_tokens": final_arm_tokens,
        },
        "execution_accounting": {
            "executed_calls_total": 113,
            "accounting_tokens_total": total_tokens,
            "engineering_overhead_calls": 17,
            "engineering_overhead_tokens": total_tokens - final_arm_tokens,
            "retry_count": 0,
        },
        "retrieval_category_counts": retrieval_counts,
        "auto_diagnostic_summary": by_arm,
        "rows": rows,
        "nonclaims": [
            "Auto overlap is diagnostic and contains known false positives; it is not the final semantic score.",
            "The confirmation required engineering repair after partial output-format failures.",
            "BM25 retrieval and hidden benchmark references are not human gold.",
        ],
    }
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "retrieval_category_counts": retrieval_counts,
        "auto_diagnostic_summary": by_arm,
        "execution_accounting": output["execution_accounting"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
