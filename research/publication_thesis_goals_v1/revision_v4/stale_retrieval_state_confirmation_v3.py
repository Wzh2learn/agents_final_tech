"""Run frozen non-oracle retrieval and state-processing confirmation arms."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from stale_semantic_evaluation_v2 import tokens
from state_processing_comparison_v2 import (
    MODEL_DEFAULT,
    ENDPOINT_DEFAULT,
    MODELS_ENDPOINT_DEFAULT,
    ARMS,
    build_direct_prompt,
    build_one_call_prompt,
    build_second_stage_prompt,
    build_state_card_prompt,
    build_timeline_prompt,
    current_intermediate_text,
    format_sessions,
    get_json,
    post_model,
    sha256_bytes,
    write_call_raw,
    write_json,
)


CONTRAST = (
    "no longer", "rather than", "instead", "used to", "previously", "old",
    "returned", "changed", "cleared", "not the same",
)
UNCERTAIN = (
    "not sure", "unknown", "insufficient", "unable to determine", "not enough",
    "cannot establish", "can't establish", "unclear",
)


def bm25_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def bm25_select(item: dict[str, Any], query: str, top_k: int = 3) -> list[int]:
    """Select sessions with standard BM25 over official role/time text."""
    query_terms = bm25_tokens(query)
    query_counts = Counter(query_terms)
    documents = []
    timestamps = item.get("timestamps", [])
    for index, session in enumerate(item["haystack_session"]):
        lines = [f"session {index + 1} time {timestamps[index] if index < len(timestamps) else ''}"]
        for message in session:
            lines.append(f"{message.get('role', '')} {message.get('content', '')}")
        documents.append(bm25_tokens("\n".join(lines)))
    avg_len = sum(len(doc) for doc in documents) / len(documents) if documents else 0.0
    doc_freq = Counter()
    for term in set(query_terms):
        doc_freq[term] = sum(term in set(doc) for doc in documents)
    count = len(documents)
    scores = []
    k1, b = 1.5, 0.75
    for index, doc in enumerate(documents):
        frequencies = Counter(doc)
        score = 0.0
        for term, query_frequency in query_counts.items():
            if term not in frequencies:
                continue
            df = doc_freq[term]
            idf = math.log(1 + (count - df + 0.5) / (df + 0.5))
            numerator = frequencies[term] * (k1 + 1)
            denominator = frequencies[term] + k1 * (1 - b + b * len(doc) / avg_len)
            score += query_frequency * idf * numerator / denominator
        scores.append((score, -index, index))
    return [index for _score, _negative, index in sorted(scores, reverse=True)[:top_k]]


def retrieval_category(item: dict[str, Any], selected: list[int]) -> str:
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


def semantic_from_hidden_reference(
    answer: str,
    item: dict[str, Any],
    reference: dict[str, Any],
    selected: list[int],
) -> dict[str, Any]:
    """Score current-fact meaning without actor self-labels or generated cards."""
    normalized = re.sub(r"\s+", " ", (answer or "").lower())
    answer_tokens = tokens(answer)
    current_reference_tokens = tokens(f"{reference['M_new']} {reference['explanation']}")
    old_reference_tokens = tokens(reference["M_old"])
    current_overlap = sorted(answer_tokens & current_reference_tokens)
    old_overlap = sorted(answer_tokens & old_reference_tokens)
    uncertain = any(term in normalized for term in UNCERTAIN)
    has_contrast = any(term in normalized for term in CONTRAST)
    affirmative = bool(re.search(r"\b(yes|still|currently|continues|remains|keeps)\b", normalized))
    old_affirmation = len(old_overlap) >= 2 and affirmative and not has_contrast
    selected_tokens = tokens(
        "\n".join(
            str(message.get("content", ""))
            for index in selected
            for message in item["haystack_session"][index]
        )
    )
    grounded_current = sorted(set(current_overlap) & selected_tokens)
    if uncertain and len(current_overlap) < 2:
        relation = "SAFE_UNKNOWN"
    elif old_affirmation:
        relation = "STALE_ACCEPT"
    elif len(current_overlap) >= 2 and not old_affirmation:
        relation = "CURRENT_FACT_SUPPORTED"
    else:
        relation = "UNSPECIFIED"
    success = (
        relation == "CURRENT_FACT_SUPPORTED"
        and len(grounded_current) >= 1
    )
    return {
        "relation": relation,
        "semantic_success": bool(success),
        "current_reference_overlap": current_overlap,
        "old_reference_overlap": old_overlap,
        "grounded_current_tokens": grounded_current,
        "safe_unknown": relation == "SAFE_UNKNOWN",
    }


def summarize(
    rows: list[dict[str, Any]],
    calls: list[dict[str, Any]],
    planned_calls: int,
) -> dict[str, Any]:
    by_arm = {}
    for arm in ARMS:
        group_rows = [row for row in rows if row["arm"] == arm]
        group_calls = [call for call in calls if call["arm"] == arm]
        primary = [
            row for row in group_rows if row["retrieval_category"] == "BOTH_OLD_AND_NEW"
        ]
        by_arm[arm] = {
            "observed_rows": len(group_rows),
            "semantic_success_all": sum(row["semantic"]["semantic_success"] for row in group_rows),
            "semantic_rate_all": (
                round(sum(row["semantic"]["semantic_success"] for row in group_rows) / len(group_rows), 4)
                if group_rows else None
            ),
            "primary_rows": len(primary),
            "semantic_success_primary": sum(row["semantic"]["semantic_success"] for row in primary),
            "semantic_rate_primary": (
                round(sum(row["semantic"]["semantic_success"] for row in primary) / len(primary), 4)
                if primary else None
            ),
            "safe_unknown_all": sum(row["semantic"]["safe_unknown"] for row in group_rows),
            "intermediate_specificity_success": sum(
                row["intermediate_specificity"]["success"] for row in group_rows
            ),
            "calls": len(group_calls),
            "accounting_tokens": sum(call["accounting_tokens"] for call in group_calls),
            "completion_tokens": sum(
                int(call.get("usage", {}).get("completion_tokens", 0)) for call in group_calls
            ),
        }
    retrieval_summary = {}
    retrieval_rows = []
    seen_uids = set()
    for row in rows:
        if row["uid"] not in seen_uids:
            retrieval_rows.append(row)
            seen_uids.add(row["uid"])
    for category in ("BOTH_OLD_AND_NEW", "OLD_ONLY", "NEW_ONLY", "NEITHER"):
        retrieval_summary[category] = sum(
            row["retrieval_category"] == category for row in retrieval_rows
        )
    return {
        "overall": {
            "planned_calls": planned_calls,
            "observed_calls": len(calls),
            "accounting_tokens": sum(call["accounting_tokens"] for call in calls),
            "retry_count": 0,
        },
        "by_arm": by_arm,
        "retrieval_category_counts": retrieval_summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--endpoint", default=ENDPOINT_DEFAULT)
    parser.add_argument("--models-endpoint", default=MODELS_ENDPOINT_DEFAULT)
    parser.add_argument("--model", default=MODEL_DEFAULT)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--uids", default="")
    parser.add_argument("--arms", default=",".join(ARMS))
    parser.add_argument("--retrieval-top-k", type=int, default=3)
    parser.add_argument("--query-dimension", choices=("dim1", "dim2", "dim3"), default="dim1")
    args = parser.parse_args()
    active_arms = tuple(arm.strip() for arm in args.arms.split(",") if arm.strip())
    if not active_arms or any(arm not in ARMS for arm in active_arms):
        raise ValueError(f"invalid arms: {args.arms}")
    requested_uids = tuple(uid.strip() for uid in args.uids.split(",") if uid.strip())
    output_dir = args.output_dir.resolve()
    if (output_dir / "STALE_RETRIEVAL_STATE_CONFIRMATION_COMPLETE_V3").exists():
        raise RuntimeError("confirmation_already_complete")
    output_dir.mkdir(parents=True, exist_ok=True)
    data = {item["uid"]: item for item in json.loads(args.data.read_text(encoding="utf-8"))}
    reference_doc = json.loads(args.reference.read_text(encoding="utf-8"))
    references = {row["uid"]: row for row in reference_doc["items"]}
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if protocol.get("status") != "FROZEN_BEFORE_MODEL_GENERATION":
        raise ValueError("protocol_not_frozen")
    preflight, preflight_raw = get_json(args.models_endpoint)
    model_ids = [row.get("id") for row in preflight.get("data", []) if isinstance(row, dict)]
    if args.model not in model_ids:
        raise RuntimeError(f"model_identity_mismatch:{model_ids}")
    rows: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []
    raw_dir = output_dir / "raw"
    stopped = None
    active_uids = requested_uids or tuple(reference_doc["selection"]["selected_uids"])
    if any(uid not in references for uid in active_uids):
        raise ValueError("uid not present in frozen reference")
    for uid in active_uids:
        item = data[uid]
        reference = references[uid]
        query = data[uid]["probing_queries"][f"{args.query_dimension}_query"]
        selected = bm25_select(item, query, top_k=args.retrieval_top_k)
        category = retrieval_category(item, selected)
        evidence = format_sessions(item, selected)
        for arm in active_arms:
            task_id = f"{uid}__{arm}"
            if arm == "direct_answer":
                call = post_model(
                    args.endpoint, args.model, build_direct_prompt(query, evidence),
                    512, args.timeout, {"decision", "answer", "evidence_refs"},
                )
                call["arm"] = arm
                write_call_raw(raw_dir, task_id, "answer", call, {
                    "uid": uid, "arm": arm, "selected_indices": selected,
                    "retrieval_category": category, "max_tokens": 512,
                })
                calls.append(call)
                parsed = call.get("parsed") or {}
                answer = parsed.get("answer")
                intermediate = {}
                last_call = call
            elif arm == "one_call_facts":
                call = post_model(
                    args.endpoint, args.model, build_one_call_prompt(query, evidence),
                    512, args.timeout, {"facts", "decision", "answer", "evidence_refs"},
                )
                call["arm"] = arm
                write_call_raw(raw_dir, task_id, "facts_and_answer", call, {
                    "uid": uid, "arm": arm, "selected_indices": selected,
                    "retrieval_category": category, "max_tokens": 512,
                })
                calls.append(call)
                parsed = call.get("parsed") or {}
                answer = parsed.get("answer")
                intermediate = parsed
                last_call = call
            else:
                stage1_prompt = (
                    build_timeline_prompt(query, evidence)
                    if arm == "two_stage_timeline"
                    else build_state_card_prompt(query, evidence)
                )
                required1 = (
                    {"timeline", "current_facts", "unresolved"}
                    if arm == "two_stage_timeline"
                    else {"old_state", "new_state", "change_type", "status", "evidence_refs"}
                )
                stage1_max = 384 if arm == "two_stage_timeline" else 256
                stage2_max = 128 if arm == "two_stage_timeline" else 256
                call1 = post_model(
                    args.endpoint, args.model, stage1_prompt, stage1_max,
                    args.timeout, required1,
                )
                call1["arm"] = arm
                write_call_raw(raw_dir, task_id, "stage1", call1, {
                    "uid": uid, "arm": arm, "selected_indices": selected,
                    "retrieval_category": category, "max_tokens": stage1_max,
                })
                calls.append(call1)
                intermediate = call1.get("parsed") or {}
                if call1["parse_status"] != "VALID":
                    answer = None
                    last_call = call1
                else:
                    call2 = post_model(
                        args.endpoint, args.model,
                        build_second_stage_prompt(query, intermediate),
                        stage2_max, args.timeout,
                        {"decision", "answer", "evidence_refs"},
                    )
                    call2["arm"] = arm
                    write_call_raw(raw_dir, task_id, "stage2", call2, {
                        "uid": uid, "arm": arm, "selected_indices": selected,
                        "retrieval_category": category, "max_tokens": stage2_max,
                    })
                    calls.append(call2)
                    answer = (call2.get("parsed") or {}).get("answer")
                    last_call = call2
            current_text = current_intermediate_text(arm, intermediate)
            current_ref_tokens = tokens(f"{reference['M_new']} {reference['explanation']}")
            matched_current = sorted(tokens(current_text) & current_ref_tokens)
            rows.append({
                "uid": uid,
                "type": item["type"],
                "arm": arm,
                "query": query,
                "selected_indices": selected,
                "retrieval_category": category,
                "answer": answer,
                "current_intermediate_text": current_text,
                "intermediate_specificity": {
                    "success": len(matched_current) >= 2,
                    "matched_current_tokens": matched_current,
                },
                "semantic": semantic_from_hidden_reference(
                    answer or "", item, reference, selected
                ),
            })
            if last_call.get("transport_status") != "HTTP_OK":
                stopped = f"transport_failure:{last_call.get('http_status')}"
                break
            if last_call.get("parse_status") != "VALID":
                stopped = f"parse_failure:{last_call.get('parse_status')}"
                break
        if stopped:
            break
    planned_calls = len(active_uids) * sum(
        2 if arm.startswith("two_stage") else 1 for arm in active_arms
    )
    summary = summarize(rows, calls, planned_calls)
    result = {
        "schema": "stale_retrieval_state_confirmation_v3",
        "date": "2026-10-23",
        "evidence_identity": "FROZEN_METRIC_NON_ORACLE_RETRIEVAL_WITH_ENGINEERING_REPAIR_RESUME",
        "active_uids": list(active_uids),
        "active_arms": list(active_arms),
        "retrieval_top_k": args.retrieval_top_k,
        "query_dimension": args.query_dimension,
        "engineering_repair": (
            "State-card evidence_refs restricted to at most three compact "
            "session/turn identifiers after long quotes truncated JSON. "
            "No retrieval, semantic threshold or answer requirement changed."
        ),
        "protocol_sha256": sha256_bytes(args.protocol.read_bytes()),
        "reference_sha256": sha256_bytes(args.reference.read_bytes()),
        "model_identity_observed": model_ids,
        "model_request_contract": {
            "temperature": 0,
            "top_p": 1,
            "enable_thinking": False,
            "concurrency": 1,
            "retry_cap": 0,
        },
        "summary": summary,
        "rows": rows,
        "stopped_early": stopped,
        "limitations": [
            "Only dim1 is used in this confirmation batch.",
            "The semantic reference is hidden benchmark text plus deterministic overlap, not human gold.",
            "BM25 top-3 is one fixed non-oracle retriever, not the best possible retrieval system.",
            "Primary state-processing comparisons condition on retrieval category BOTH_OLD_AND_NEW.",
        ],
    }
    write_json(output_dir / "STALE_RETRIEVAL_STATE_CONFIRMATION_RESULTS_V3.json", result)
    receipt = {
        "schema": "stale_retrieval_state_confirmation_receipt_v3",
        "status": "COMPLETE_WITH_STOP" if stopped else "COMPLETE",
        "model": args.model,
        "planned_calls": planned_calls,
        "executed_calls": summary["overall"]["observed_calls"],
        "accounting_tokens": summary["overall"]["accounting_tokens"],
        "retry_count": 0,
        "results_sha256": sha256_bytes(
            (output_dir / "STALE_RETRIEVAL_STATE_CONFIRMATION_RESULTS_V3.json").read_bytes()
        ),
        "stopped_early": stopped,
    }
    write_json(output_dir / "STALE_RETRIEVAL_STATE_CONFIRMATION_RECEIPT_V3.json", receipt)
    (output_dir / "STALE_RETRIEVAL_STATE_CONFIRMATION_COMPLETE_V3").write_text(
        "COMPLETE\n", encoding="utf-8"
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
