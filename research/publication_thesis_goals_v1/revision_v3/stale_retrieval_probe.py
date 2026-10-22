"""Deterministic STALE retrieval qualification over hidden relevant sessions."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"[a-z0-9]+")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def session_text(session: list[dict[str, Any]]) -> str:
    return "\n".join(str(message.get("content", "")) for message in session)


def lexical_ranking(query: str, sessions: list[list[dict[str, Any]]]) -> list[int]:
    query_tokens = tokens(query)
    scores = []
    for index, session in enumerate(sessions):
        overlap = len(query_tokens & tokens(session_text(session)))
        scores.append((overlap, -index, index))
    return [index for _overlap, _negative_index, index in sorted(scores, reverse=True)]


def evaluate_arm(
    name: str,
    selected_indices: list[int],
    relevant: set[int],
    sessions: list[list[dict[str, Any]]],
) -> dict[str, Any]:
    selected_text_chars = sum(
        len(session_text(sessions[index])) for index in selected_indices
    )
    selected_tokens = sum(
        len(tokens(session_text(sessions[index]))) for index in selected_indices
    )
    hits = sorted(relevant.intersection(selected_indices))
    return {
        "arm": name,
        "selected_indices": selected_indices,
        "relevant_indices": sorted(relevant),
        "hit_indices": hits,
        "recall": len(hits) / len(relevant) if relevant else None,
        "precision": len(hits) / len(selected_indices) if selected_indices else 0.0,
        "context_chars": selected_text_chars,
        "context_unique_tokens": selected_tokens,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--item-count", type=int, default=12)
    parser.add_argument("--top-k", type=int, default=2)
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    by_type: dict[str, list[dict[str, Any]]] = {"T1": [], "T2": []}
    for item in data:
        kind = str(item.get("type", "")).upper()
        if kind in by_type:
            by_type[kind].append(item)
    for rows in by_type.values():
        rows.sort(key=lambda item: str(item["uid"]))
    per_type = max(1, args.item_count // 2)
    selected = by_type["T1"][:per_type] + by_type["T2"][:per_type]
    rows = []
    for item in selected:
        sessions = item["haystack_session"]
        relevant = {int(index) for index in item["relevant_session_index"]}
        for query_label, query in sorted(item["probing_queries"].items()):
            lexical = lexical_ranking(str(query), sessions)[: args.top_k]
            recent = list(range(max(0, len(sessions) - args.top_k), len(sessions)))
            rows.append(
                {
                    "uid": item["uid"],
                    "type": item["type"],
                    "query_label": query_label,
                    "arms": {
                        "query_only": evaluate_arm("query_only", [], relevant, sessions),
                        "lexical_top_k": evaluate_arm("lexical_top_k", lexical, relevant, sessions),
                        "recent_top_k": evaluate_arm("recent_top_k", recent, relevant, sessions),
                        "oracle_relevant_top_k": evaluate_arm(
                            "oracle_relevant_top_k", sorted(relevant)[: args.top_k], relevant, sessions
                        ),
                    },
                }
            )
    summary = {}
    for arm in ("query_only", "lexical_top_k", "recent_top_k", "oracle_relevant_top_k"):
        arm_rows = [row["arms"][arm] for row in rows]
        summary[arm] = {
            "query_count": len(arm_rows),
            "mean_recall": sum(float(row["recall"] or 0.0) for row in arm_rows) / len(arm_rows),
            "perfect_recall_rate": sum(float(row["recall"] or 0.0) == 1.0 for row in arm_rows) / len(arm_rows),
            "mean_context_chars": sum(int(row["context_chars"]) for row in arm_rows) / len(arm_rows),
            "mean_context_unique_tokens": sum(int(row["context_unique_tokens"]) for row in arm_rows) / len(arm_rows),
        }
    payload = {
        "schema": "stale_retrieval_probe_v1",
        "date": "2026-10-23",
        "question": (
            "Do simple query-retrieval policies find the sessions needed for "
            "implicit state invalidation, or is a stronger memory mechanism necessary?"
        ),
        "evidence_identity": "DEV_ONLY_DETERMINISTIC_RETRIEVAL_ON_PUBLIC_STALE_DATA",
        "data": {
            "path": str(args.data),
            "sha256": sha256_file(args.data),
            "bytes": args.data.stat().st_size,
            "total_items": len(data),
        },
        "selection": {
            "item_count": len(selected),
            "per_type": per_type,
            "uids": [item["uid"] for item in selected],
            "top_k": args.top_k,
        },
        "summary": summary,
        "rows": rows,
        "nonclaims": [
            "Relevant session indices are independent structured references but not semantic answer gold.",
            "This is a retrieval qualification probe, not a model or CUPMem performance result.",
            "Oracle relevant selection is a development upper bound and is not deployable.",
        ],
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
