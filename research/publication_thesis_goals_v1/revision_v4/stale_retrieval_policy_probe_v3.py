"""Compare non-oracle session retrieval policies on STALE dim1."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from stale_retrieval_state_confirmation_v3 import bm25_select, retrieval_category


def latest_select(_item: dict[str, Any], _query: str, top_k: int = 3) -> list[int]:
    count = len(_item["haystack_session"])
    return list(range(max(0, count - top_k), count))


def hybrid_select(item: dict[str, Any], query: str, top_k: int = 3) -> list[int]:
    latest = latest_select(item, query, 1)
    bm25 = [index for index in bm25_select(item, query, top_k=top_k) if index not in latest]
    return (latest + bm25)[:top_k]


POLICIES = {
    "bm25_top3": lambda item, query: bm25_select(item, query, 3),
    "bm25_top5": lambda item, query: bm25_select(item, query, 5),
    "latest3": latest_select,
    "hybrid_latest1_bm25_2": hybrid_select,
}


def evaluate(data: list[dict[str, Any]], uids: set[str] | None = None) -> dict[str, Any]:
    rows = []
    for item in data:
        if uids is not None and item["uid"] not in uids:
            continue
        query = item["probing_queries"]["dim1_query"]
        old_index, new_index = sorted(int(index) for index in item["relevant_session_index"])
        for name, selector in POLICIES.items():
            selected = selector(item, query)
            category = retrieval_category(item, selected)
            context_chars = sum(
                len(str(message.get("content", "")))
                for index in selected
                for message in item["haystack_session"][index]
            )
            rows.append({
                "uid": item["uid"],
                "type": item["type"],
                "policy": name,
                "selected_indices": selected,
                "old_hit": old_index in selected,
                "new_hit": new_index in selected,
                "category": category,
                "context_chars": context_chars,
            })
    summary = {}
    for name in POLICIES:
        group = [row for row in rows if row["policy"] == name]
        summary[name] = {
            "items": len(group),
            "old_recall": round(sum(row["old_hit"] for row in group) / len(group), 4),
            "new_recall": round(sum(row["new_hit"] for row in group) / len(group), 4),
            "both_rate": round(
                sum(row["category"] == "BOTH_OLD_AND_NEW" for row in group) / len(group), 4
            ),
            "category_counts": dict(Counter(row["category"] for row in group)),
            "mean_context_chars": round(
                sum(row["context_chars"] for row in group) / len(group), 2
            ),
        }
    by_type = defaultdict(dict)
    for kind in ("T1", "T2"):
        for name in POLICIES:
            group = [
                row for row in rows if row["policy"] == name and row["type"] == kind
            ]
            by_type[kind][name] = {
                "items": len(group),
                "old_recall": round(sum(row["old_hit"] for row in group) / len(group), 4),
                "new_recall": round(sum(row["new_hit"] for row in group) / len(group), 4),
                "both_rate": round(
                    sum(row["category"] == "BOTH_OLD_AND_NEW" for row in group)
                    / len(group),
                    4,
                ),
            }
    return {"summary": summary, "by_type": dict(by_type), "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    frozen_uids = {
        row["uid"]
        for row in json.loads(args.reference.read_text(encoding="utf-8"))["items"]
    }
    all_result = evaluate(data)
    frozen_result = evaluate(data, frozen_uids)
    output = {
        "schema": "stale_retrieval_policy_probe_v3",
        "date": "2026-10-23",
        "evidence_identity": "ZERO_MODEL_NON_ORACLE_RETRIEVAL_POLICY_COMPARISON",
        "all_400_dim1": {
            "summary": all_result["summary"],
            "by_type": all_result["by_type"],
        },
        "frozen_16_dim1": {
            "summary": frozen_result["summary"],
            "by_type": frozen_result["by_type"],
        },
        "rows": frozen_result["rows"],
        "nonclaims": [
            "Relevant session indices are hidden structural references, not actor inputs.",
            "This probe measures retrieval coverage only, not answer correctness.",
            "The hybrid policy uses source recency and is not a learned retriever.",
        ],
    }
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "all_400_dim1": output["all_400_dim1"]["summary"],
        "frozen_16_dim1": output["frozen_16_dim1"]["summary"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
