"""Compare transparent retrieval policies for old and change evidence."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "can",
    "could", "did", "do", "does", "for", "from", "had", "has", "have", "how",
    "i", "if", "in", "into", "is", "it", "its", "me", "my", "of", "on", "or",
    "our", "should", "so", "that", "the", "their", "them", "then", "there",
    "these", "they", "this", "to", "was", "we", "were", "what", "when",
    "where", "which", "who", "why", "will", "with", "would", "you", "your",
}
CHANGE_TERMS = ("current", "currently", "new", "now", "changed", "change", "update", "recent")


def tokenize(text: str) -> list[str]:
    return [
        token for token in re.findall(r"[a-z0-9]+", str(text).lower())
        if token not in STOPWORDS and len(token) > 2
    ]


def session_text(item: dict[str, Any], index: int, user_only: bool = False) -> str:
    messages = item["haystack_session"][index]
    if user_only:
        messages = [message for message in messages if message.get("role") == "user"]
    return "\n".join(str(message.get("content", "")) for message in messages)


def bm25_rank(
    item: dict[str, Any],
    query_terms: list[str],
    top_k: int,
    user_only: bool,
) -> list[int]:
    documents = [
        tokenize(session_text(item, index, user_only=user_only))
        for index in range(len(item["haystack_session"]))
    ]
    query_counts = Counter(query_terms)
    avg_len = sum(len(doc) for doc in documents) / len(documents) if documents else 0.0
    document_frequency = {
        term: sum(term in set(doc) for doc in documents)
        for term in set(query_terms)
    }
    count = len(documents)
    scores: list[tuple[float, int, int]] = []
    k1, b = 1.5, 0.75
    for index, document in enumerate(documents):
        frequencies = Counter(document)
        score = 0.0
        for term, query_frequency in query_counts.items():
            frequency = frequencies.get(term, 0)
            if not frequency:
                continue
            df = document_frequency.get(term, 0)
            idf = math.log(1 + (count - df + 0.5) / (df + 0.5))
            denominator = frequency + k1 * (1 - b + b * len(document) / avg_len)
            score += query_frequency * idf * frequency * (k1 + 1) / denominator
        scores.append((score, -index, index))
    ranked = [index for score, _negative, index in sorted(scores, reverse=True)]
    return ranked[:top_k]


def original_top5(item: dict[str, Any], query: str, top_k: int = 5) -> list[int]:
    return bm25_rank(item, tokenize(query), top_k, user_only=False)


def user_change_top5(item: dict[str, Any], query: str, top_k: int = 5) -> list[int]:
    query_terms = tokenize(query) + list(CHANGE_TERMS)
    return bm25_rank(item, query_terms, top_k, user_only=True)


def document_frequencies(item: dict[str, Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for index in range(len(item["haystack_session"])):
        counts.update(set(tokenize(session_text(item, index, user_only=True))))
    return counts


def attribute_recency_top5(item: dict[str, Any], query: str, top_k: int = 5) -> list[int]:
    query_terms = set(tokenize(query))
    frequencies = document_frequencies(item)
    total = len(item["haystack_session"])
    rare_terms = {
        term for term in query_terms
        if frequencies.get(term, 0) <= max(2, total // 4)
    }
    scored = []
    for index in range(total):
        terms = set(tokenize(session_text(item, index, user_only=True)))
        matches = rare_terms & terms
        change_bonus = bool(set(CHANGE_TERMS) & terms)
        scored.append((len(matches), change_bonus, index))
    scored.sort(reverse=True)
    return [index for _matches, _change, index in scored[:top_k]]


def two_pass_change_top5(item: dict[str, Any], query: str, top_k: int = 5) -> list[int]:
    first_pass = original_top5(item, query, top_k=3)
    query_terms = set(tokenize(query))
    anchor_terms = set()
    for index in first_pass:
        anchor_terms.update(query_terms & set(tokenize(session_text(item, index, user_only=True))))
    second_terms = sorted(anchor_terms) + list(CHANGE_TERMS)
    ranked = bm25_rank(item, second_terms, top_k * 2, user_only=True)
    merged = first_pass + [index for index in ranked if index not in first_pass]
    return merged[:top_k]


POLICIES = {
    "original_bm25_top5": original_top5,
    "user_change_bm25_top5": user_change_top5,
    "attribute_recency_top5": attribute_recency_top5,
    "two_pass_change_top5": two_pass_change_top5,
}


def category(item: dict[str, Any], selected: list[int]) -> str:
    old_index, new_index = sorted(int(index) for index in item["relevant_session_index"])
    has_old = old_index in selected
    has_new = new_index in selected
    if has_old and has_new:
        return "BOTH_OLD_AND_NEW"
    if has_old:
        return "OLD_ONLY"
    if has_new:
        return "NEW_ONLY"
    return "NEITHER"


def evaluate(data: list[dict[str, Any]], dimension: str) -> dict[str, Any]:
    rows = []
    for item in data:
        query = item["probing_queries"][f"{dimension}_query"]
        old_index, new_index = sorted(int(index) for index in item["relevant_session_index"])
        for policy_name, selector in POLICIES.items():
            selected = selector(item, query)
            context_chars = sum(
                len(session_text(item, index, user_only=False))
                for index in selected
            )
            user_chars = sum(
                len(session_text(item, index, user_only=True))
                for index in selected
            )
            rows.append({
                "uid": item["uid"],
                "type": item["type"],
                "policy": policy_name,
                "selected_indices": selected,
                "old_hit": old_index in selected,
                "new_hit": new_index in selected,
                "category": category(item, selected),
                "context_chars": context_chars,
                "user_fact_chars": user_chars,
            })
    summary = {}
    for policy_name in POLICIES:
        group = [row for row in rows if row["policy"] == policy_name]
        categories = Counter(row["category"] for row in group)
        summary[policy_name] = {
            "items": len(group),
            "old_recall": round(sum(row["old_hit"] for row in group) / len(group), 4),
            "new_recall": round(sum(row["new_hit"] for row in group) / len(group), 4),
            "both_rate": round(categories["BOTH_OLD_AND_NEW"] / len(group), 4),
            "category_counts": dict(categories),
            "mean_context_chars": round(
                sum(row["context_chars"] for row in group) / len(group), 2
            ),
            "mean_user_fact_chars": round(
                sum(row["user_fact_chars"] for row in group) / len(group), 2
            ),
        }
    return {"summary": summary, "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    output = {
        "schema": "g2_retrieval_policy_probe_v5",
        "date": "2026-10-23",
        "evidence_identity": "ZERO_MODEL_TRANSPARENT_RETRIEVAL_POLICY_COMPARISON",
        "dim1": evaluate(data, "dim1"),
        "dim3": evaluate(data, "dim3"),
        "nonclaims": [
            "Relevant session indices are hidden structural references and never actor inputs.",
            "Coverage is not answer correctness or action validity.",
            "All policies are transparent baselines, not learned retrieval methods.",
        ],
    }
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "dim1": output["dim1"]["summary"],
        "dim3": output["dim3"]["summary"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
