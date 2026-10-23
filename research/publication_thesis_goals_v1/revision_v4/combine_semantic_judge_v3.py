"""Combine recovered and resumed strict semantic-judge rows."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from stale_semantic_judge_v3 import parse_judge


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def recover_rows(
    raw_root: Path,
    uids: list[str],
    source_by_key: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for uid in uids:
        request = load(raw_root / uid / "judge" / "request.json")
        receipt = load(raw_root / uid / "judge" / "call_receipt.json")
        status, parsed, errors = parse_judge(receipt["content"])
        if status != "VALID":
            raise ValueError(f"raw judge invalid for {uid}: {errors}")
        code_to_arm = request["meta"]["code_to_arm"]
        evaluations = parsed["evaluations"]
        for code, arm in code_to_arm.items():
            source = source_by_key[(uid, arm)]
            rows.append({
                "uid": uid,
                "type": source["type"],
                "arm": arm,
                "response_code": code,
                "answer": source["answer"],
                "judge": evaluations[code],
                "retrieval_category": source["retrieval_category"],
            })
    return rows


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_arm = {}
    for arm in sorted({row["arm"] for row in rows}):
        group = [row for row in rows if row["arm"] == arm]
        primary = [
            row for row in group if row.get("retrieval_category") == "BOTH_OLD_AND_NEW"
        ]
        by_arm[arm] = {
            "rows": len(group),
            "judge_pass": sum(row["judge"].get("pass") is True for row in group),
            "judge_pass_rate": round(
                sum(row["judge"].get("pass") is True for row in group) / len(group), 4
            ),
            "primary_rows": len(primary),
            "judge_pass_primary": sum(
                row["judge"].get("pass") is True for row in primary
            ),
            "judge_pass_rate_primary": (
                round(
                    sum(row["judge"].get("pass") is True for row in primary)
                    / len(primary),
                    4,
                )
                if primary else None
            ),
            "safe_unknown": sum(
                row["judge"].get("safe_unknown") is True for row in group
            ),
            "error_counts": dict(Counter(row["judge"].get("error_type") for row in group)),
        }
    return by_arm


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-prefix", type=Path, required=True)
    parser.add_argument("--resume", type=Path, required=True)
    parser.add_argument("--combined", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    combined = load(args.combined)
    source_by_key = {
        (row["uid"], row["arm"]): row
        for row in combined["rows"]
    }
    recovered = recover_rows(
        args.raw_prefix,
        ["09949c3c-0abe-42fb-9012-efb34b298947", "0af76ce2-d242-4deb-bd5c-a853338150bc"],
        source_by_key,
    )
    resume = load(args.resume)
    rows = recovered + list(resume["rows"])
    for arm in {row["arm"] for row in rows}:
        uids = [row["uid"] for row in rows if row["arm"] == arm]
        if len(uids) != 16 or len(set(uids)) != 16:
            raise ValueError(f"incomplete judge arm {arm}: {len(uids)}")
    output = {
        "schema": "stale_semantic_judge_combined_v3",
        "date": "2026-10-23",
        "evidence_identity": "AUXILIARY_METHOD_BLIND_LLM_JUDGE_NOT_HUMAN_GOLD",
        "summary_by_arm": summarize(rows),
        "execution_accounting": {
            "final_judge_calls": 16,
            "final_judge_tokens": 145979,
            "judge_engineering_overhead_calls": 17,
            "judge_engineering_overhead_tokens": 153017,
            "total_judge_calls": 33,
            "total_judge_tokens": 298996,
            "retry_count": 0,
        },
        "rows": rows,
        "nonclaims": [
            "The final judge is method-blind but uses the same local model family as the actor.",
            "The loose judge and failed strict response are engineering overhead, not evidence.",
            "Hidden benchmark explanations are not human gold.",
        ],
    }
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "summary_by_arm": output["summary_by_arm"],
        "execution_accounting": output["execution_accounting"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
