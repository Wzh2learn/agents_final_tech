"""Freeze unused STALE confirmation UIDs and hidden scoring references."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


EXCLUDED_UIDS = (
    "01f694b2-c555-4b6e-8ca0-5f11210e2227",
    "04fea765-0b32-4e8f-b4e9-225901f627b0",
    "009b7c99-b777-465a-bc3a-77f2d88c1318",
    "012f090e-6e02-4751-955d-574745069df3",
    "0683a7ee-1c84-4f83-adb0-c3b04b1ade84",
    "0781e96e-853c-46af-b787-4a64fc248e62",
    "07cc73f3-8a5f-4680-9ad1-8a284389be0d",
    "08c6bbd2-fcf8-43c6-a79f-00a7ddc65c11",
    "05fc9783-f06c-453f-8899-15253d63533a",
    "06071a3e-6ac8-41cc-8138-6db403c7b42d",
    "0a5d90e4-a8c1-4929-81c6-acd553069f50",
    "0c348e44-7f55-4d95-aeb7-137f801985d7",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def select(data: list[dict[str, Any]], per_type: int = 8) -> list[dict[str, Any]]:
    """Select the next unused balanced UID block deterministically."""
    excluded = set(EXCLUDED_UIDS)
    by_type: dict[str, list[dict[str, Any]]] = {"T1": [], "T2": []}
    for item in data:
        kind = str(item.get("type", "")).upper()
        if kind in by_type and item["uid"] not in excluded:
            by_type[kind].append(item)
    if any(len(rows) < per_type for rows in by_type.values()):
        raise ValueError("not enough unused balanced records")
    for rows in by_type.values():
        rows.sort(key=lambda item: item["uid"])
    return by_type["T1"][:per_type] + by_type["T2"][:per_type]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    selected = select(data)
    references = []
    for item in selected:
        relevant = sorted(int(index) for index in item["relevant_session_index"])
        if len(relevant) != 2:
            raise ValueError(f"unexpected relevant index cardinality: {item['uid']}")
        references.append({
            "uid": item["uid"],
            "type": item["type"],
            "old_session_index": relevant[0],
            "new_session_index": relevant[1],
            "M_old": item["M_old"],
            "M_new": item["M_new"],
            "explanation": item["explanation"],
            "dim1_query": item["probing_queries"]["dim1_query"],
        })
    output = {
        "schema": "stale_retrieval_confirmation_reference_v3",
        "date": "2026-10-23",
        "evidence_identity": "HIDDEN_POST_INPUT_SCORING_REFERENCE_NOT_ACTOR_VISIBLE_NOT_HUMAN_GOLD",
        "selection": {
            "sort": "uid_ascending",
            "excluded_uids": list(EXCLUDED_UIDS),
            "per_type": 8,
            "selected_uids": [row["uid"] for row in references],
        },
        "items": references,
        "nonclaims": [
            "M_old/M_new/explanation are scoring references and are never actor inputs.",
            "The explanation is benchmark-authored logic, not independent human gold.",
        ],
    }
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    protocol = {
        "schema": "stale_retrieval_state_confirmation_protocol_v3",
        "date": "2026-10-23",
        "status": "FROZEN_BEFORE_MODEL_GENERATION",
        "query_dimension": "dim1",
        "retrieval": {
            "method": "BM25 over official role/time/session text",
            "top_k": 3,
            "same_selected_sessions_for_all_arms": True,
            "hidden_reference_used_for_actor": False,
        },
        "arms": {
            "direct_answer": {"calls": 1, "max_tokens": [512]},
            "one_call_facts": {"calls": 1, "max_tokens": [512]},
            "two_stage_timeline": {"calls": 2, "max_tokens": [384, 128]},
            "two_stage_state_card": {"calls": 2, "max_tokens": [256, 256]},
        },
        "primary_state_processing_population": "retrieval_category == BOTH_OLD_AND_NEW",
        "end_to_end_population": "all selected uid/query rows",
        "primary_metric": (
            "semantic current-fact success requiring rejection of the old state, "
            "at least two informative tokens shared with M_new/explanation, and "
            "grounding in the retrieved evidence"
        ),
        "secondary_metrics": [
            "retrieval old/new hit category",
            "safe UNKNOWN when new evidence is not retrieved",
            "intermediate current-fact specificity",
            "accounting tokens and completion tokens",
        ],
        "stop_rules": [
            "zero retries and single concurrency",
            "stop on systemic transport failure or identity mismatch",
            "preserve schema/format failures without repair",
        ],
        "reference_path": args.output.name,
        "reference_sha256": sha256_file(args.output),
    }
    args.protocol.write_text(
        json.dumps(protocol, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "selected_uids": protocol and output["selection"]["selected_uids"],
        "reference_sha256": protocol["reference_sha256"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
