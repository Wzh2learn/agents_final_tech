#!/usr/bin/env python3
"""Evaluate selective expansion after incremental STALE evidence arrival."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any


MODEL_DEFAULT = "Qwen3.6-35B-A3B-Q4_K_M.gguf"
ENDPOINT_DEFAULT = "http://127.0.0.1:8004/v1/chat/completions"
QUERY_FIELD = "dim1_query"
TOP3 = 3
TOP5 = 5
MAX_TOKENS = 128
MAX_GENERATION_CALLS = 8
FORBIDDEN_ACTOR_FIELDS = (
    "M_old",
    "M_new",
    "explanation",
    "relevant_session_index",
)
PAST_CUES = ("used to", "previously", "before", "last year", "last month")
UPDATE_CUES = (
    "changed",
    "no longer",
    "not anymore",
    "returned",
    "moved",
    "switched",
    "stopped",
    "started",
    "now",
    "current",
    "update",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def session_text(session: list[dict[str, Any]]) -> str:
    lines = []
    for message in session:
        lines.append(f"{message.get('role', '')} {message.get('content', '')}")
    return "\n".join(lines)


def render_session(index: int, session: list[dict[str, Any]], timestamp: str) -> str:
    lines = [f"<session index={index} time={timestamp}>"]
    for message in session:
        lines.append(f"[{message.get('role', '')}] {message.get('content', '')}")
    lines.append("</session>")
    return "\n".join(lines)


def bm25_ranked(item: dict[str, Any], query: str) -> list[tuple[int, float]]:
    query_terms = tokenize(query)
    query_counts = Counter(query_terms)
    timestamps = item.get("timestamps", [])
    documents: list[list[str]] = []
    for index, session in enumerate(item["haystack_session"]):
        prefix = f"session {index + 1} time {timestamps[index] if index < len(timestamps) else ''}"
        documents.append(tokenize(prefix + "\n" + session_text(session)))
    avg_len = sum(len(doc) for doc in documents) / len(documents) if documents else 0.0
    doc_freq = Counter()
    for term in set(query_terms):
        doc_freq[term] = sum(term in set(doc) for doc in documents)
    count = len(documents)
    scored = []
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
        scored.append((index, float(score)))
    return sorted(scored, key=lambda row: (-row[1], row[0]))


def retrieval_category(item: dict[str, Any], selected: list[int]) -> str:
    relevant = {int(index) for index in item["relevant_session_index"]}
    selected_set = set(selected)
    old_index, new_index = sorted(relevant)
    has_old = old_index in selected_set
    has_new = new_index in selected_set
    if has_old and has_new:
        return "BOTH_OLD_AND_NEW"
    if has_old:
        return "OLD_ONLY"
    if has_new:
        return "NEW_ONLY"
    return "NEITHER"


def context_chars(item: dict[str, Any], selected: list[int]) -> int:
    return sum(
        len(session_text(item["haystack_session"][index]))
        for index in selected
    )


def visible_gap_rule(
    query: str,
    item: dict[str, Any],
    top3_indices: list[int],
    ranked: list[tuple[int, float]],
) -> tuple[str, dict[str, Any]]:
    query_terms = set(tokenize(query))
    visible_text = "\n".join(
        session_text(item["haystack_session"][index]) for index in top3_indices
    ).lower()
    visible_terms = set(tokenize(visible_text))
    coverage = len(query_terms & visible_terms) / len(query_terms) if query_terms else 1.0
    has_past = any(cue in visible_text for cue in PAST_CUES)
    has_update = any(cue in visible_text for cue in UPDATE_CUES)
    score_map = dict(ranked)
    rank1 = score_map[top3_indices[0]] if top3_indices else 0.0
    rank3 = score_map[top3_indices[-1]] if top3_indices else 0.0
    score_tail = rank1 > 0 and rank3 / rank1 >= 0.8
    temporal_gap = has_past and not has_update
    expand = coverage < 0.70 or temporal_gap or score_tail
    return ("EXPAND" if expand else "KEEP"), {
        "query_token_coverage": round(coverage, 6),
        "has_past_cue": has_past,
        "has_update_cue": has_update,
        "rank3_to_rank1_score_ratio": round(rank3 / rank1, 6) if rank1 > 0 else None,
        "score_tail": score_tail,
        "temporal_gap": temporal_gap,
    }


def expansion_value(item: dict[str, Any], top3: list[int], top5: list[int]) -> dict[str, Any]:
    relevant = {int(index) for index in item["relevant_session_index"]}
    before = relevant.intersection(top3)
    after = relevant.intersection(top5)
    return {
        "top3_relevant_count": len(before),
        "top5_relevant_count": len(after),
        "added_relevant_count": len(after - before),
        "useful_expansion": bool(after - before),
        "completes_pair": len(before) < 2 and len(after) == 2,
    }


def policy_row(
    item: dict[str, Any],
    policy: str,
    action: str,
    top3: list[int],
    top5: list[int],
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = expansion_value(item, top3, top5)
    if action not in {"KEEP", "EXPAND"}:
        quality = "INVALID_ACTION"
        final_category = "UNRESOLVED"
        selected: list[int] = []
    elif action == "EXPAND":
        quality = "USEFUL_EXPAND" if value["useful_expansion"] else "NO_GAIN_EXPAND"
        final_category = retrieval_category(item, top5)
        selected = top5
    else:
        quality = "MISSED_GAIN" if value["useful_expansion"] else "GOOD_KEEP"
        final_category = retrieval_category(item, top3)
        selected = top3
    return {
        "uid": item["uid"],
        "type": item["type"],
        "policy": policy,
        "action": action,
        "top3_indices": top3,
        "top5_indices": top5,
        "top3_category": retrieval_category(item, top3),
        "top5_category": retrieval_category(item, top5),
        "final_category": final_category,
        "action_quality": quality,
        "selected_indices": selected,
        "context_chars": context_chars(item, selected) if selected else 0,
        "expansion_value": value,
        "diagnostics": diagnostics or {},
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "items": len(rows),
        "expand_count": sum(row["action"] == "EXPAND" for row in rows),
        "keep_count": sum(row["action"] == "KEEP" for row in rows),
        "invalid_count": sum(row["action"] not in {"KEEP", "EXPAND"} for row in rows),
        "final_both_count": sum(
            row["final_category"] == "BOTH_OLD_AND_NEW" for row in rows
        ),
        "final_both_rate": round(
            sum(row["final_category"] == "BOTH_OLD_AND_NEW" for row in rows) / len(rows),
            6,
        ) if rows else None,
        "useful_expand_count": sum(
            row["action"] == "EXPAND" and row["expansion_value"]["useful_expansion"]
            for row in rows
        ),
        "no_gain_expand_count": sum(
            row["action"] == "EXPAND" and not row["expansion_value"]["useful_expansion"]
            for row in rows
        ),
        "missed_gain_count": sum(row["action_quality"] == "MISSED_GAIN" for row in rows),
        "pair_completion_count": sum(
            row["action"] == "EXPAND" and row["expansion_value"]["completes_pair"]
            for row in rows
        ),
        "mean_context_chars": round(
            sum(row["context_chars"] for row in rows) / len(rows), 2
        ) if rows else None,
    }


def evaluate_policies(data: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for item in data:
        query = str(item["probing_queries"][QUERY_FIELD])
        ranked = bm25_ranked(item, query)
        top3 = [index for index, _score in ranked[:TOP3]]
        top5 = [index for index, _score in ranked[:TOP5]]
        value = expansion_value(item, top3, top5)
        keep_rows = [
            policy_row(item, "keep_top3", "KEEP", top3, top5),
            policy_row(item, "always_expand_top5", "EXPAND", top3, top5),
            policy_row(item, "oracle_gain_rule", "EXPAND" if value["useful_expansion"] else "KEEP", top3, top5),
            policy_row(item, "oracle_pair_rule", "EXPAND" if value["completes_pair"] else "KEEP", top3, top5),
        ]
        action, diagnostics = visible_gap_rule(query, item, top3, ranked)
        keep_rows.append(
            policy_row(item, "visible_gap_rule", action, top3, top5, diagnostics)
        )
        rows.extend(keep_rows)
    policies = {}
    for name in (
        "keep_top3",
        "always_expand_top5",
        "visible_gap_rule",
        "oracle_gain_rule",
        "oracle_pair_rule",
    ):
        policies[name] = summarize([row for row in rows if row["policy"] == name])
    return {"summary": policies, "rows": rows}


def recursive_prior_uids(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"uids", "selected_uids", "excluded_uids"} and isinstance(child, list):
                found.update(str(item) for item in child if isinstance(item, str))
            found.update(recursive_prior_uids(child))
    elif isinstance(value, list):
        for child in value:
            found.update(recursive_prior_uids(child))
    return found


def load_prior_uids(paths: list[Path]) -> set[str]:
    found: set[str] = set()
    for path in paths:
        found.update(recursive_prior_uids(json.loads(path.read_text(encoding="utf-8"))))
    return found


def select_model_items(
    data: list[dict[str, Any]],
    prior_uids: set[str],
    per_type: int = 4,
) -> list[dict[str, Any]]:
    by_type: dict[str, list[dict[str, Any]]] = {"T1": [], "T2": []}
    for item in data:
        kind = str(item.get("type", "")).upper()
        if kind in by_type and str(item["uid"]) not in prior_uids:
            by_type[kind].append(item)
    for rows in by_type.values():
        rows.sort(key=lambda item: str(item["uid"]))
    if any(len(rows) < per_type for rows in by_type.values()):
        raise ValueError("not enough unused T1/T2 items")
    return by_type["T1"][:per_type] + by_type["T2"][:per_type]


def build_decision_prompt(item: dict[str, Any], top3: list[int]) -> str:
    query = str(item["probing_queries"][QUERY_FIELD])
    timestamps = item.get("timestamps", [])
    sessions = "\n\n".join(
        render_session(
            index,
            item["haystack_session"][index],
            str(timestamps[index]) if index < len(timestamps) else "",
        )
        for index in top3
    )
    prompt = f"""Decide whether two additional retrieved sessions should be inspected.
This is an evidence-acquisition decision, not a task answer.
Use only the query and the visible sessions. Do not infer hidden metadata.

Query:
{query}

Currently visible sessions:
{sessions}

Return exactly one JSON object:
{{
  "action": "KEEP | EXPAND",
  "confidence": "LOW | MEDIUM | HIGH",
  "evidence_anchors": ["visible phrase or state cue"],
  "missing_information": ["what evidence is still missing"],
  "reason": "short reason"
}}

KEEP means the visible evidence is sufficient and the next two sessions should be
retained as unnecessary. EXPAND means the next two ranked sessions are likely to
add a missing current-state or invalidation fact. Do not answer the user question.
Do not add fields, code fences, or prose outside the JSON object."""
    for literal in FORBIDDEN_ACTOR_FIELDS:
        if literal in prompt:
            raise ValueError(f"forbidden actor field in prompt: {literal}")
    return prompt


def parse_decision(content: Any) -> dict[str, Any]:
    if not isinstance(content, str):
        raise ValueError("model content is not a string")
    text = content.strip()
    if text.startswith("```"):
        raise ValueError("code fence is not allowed")
    value = json.loads(text)
    required = {"action", "confidence", "evidence_anchors", "missing_information", "reason"}
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("decision object keys do not match contract")
    if value["action"] not in {"KEEP", "EXPAND"}:
        raise ValueError("invalid action")
    if value["confidence"] not in {"LOW", "MEDIUM", "HIGH"}:
        raise ValueError("invalid confidence")
    if not isinstance(value["evidence_anchors"], list) or not all(
        isinstance(row, str) for row in value["evidence_anchors"]
    ):
        raise ValueError("invalid evidence_anchors")
    if not isinstance(value["missing_information"], list) or not all(
        isinstance(row, str) for row in value["missing_information"]
    ):
        raise ValueError("invalid missing_information")
    if not isinstance(value["reason"], str):
        raise ValueError("invalid reason")
    return value


def post_model(
    endpoint: str,
    model: str,
    prompt: str,
    timeout: int,
) -> tuple[dict[str, Any], bytes, bytes]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "top_p": 1,
        "max_tokens": MAX_TOKENS,
        "response_format": {"type": "json_object"},
        "chat_template_kwargs": {"enable_thinking": False},
        "stream": False,
    }
    request_raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=request_raw,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_raw = response.read()
            status = response.status
    except urllib.error.HTTPError as error:
        response_raw = error.read()
        status = error.code
    latency = round(time.perf_counter() - started, 6)
    try:
        body = json.loads(response_raw.decode("utf-8"))
    except json.JSONDecodeError as error:
        return {
            "transport_status": "RESPONSE_NOT_JSON",
            "http_status": status,
            "latency_seconds": latency,
            "model_observed": None,
            "finish_reason": None,
            "usage": {},
            "accounting_tokens": 0,
            "content": None,
            "parsed": None,
            "parse_status": "RESPONSE_NOT_JSON",
            "parse_errors": [str(error)],
        }, request_raw, response_raw
    choices = body.get("choices") if isinstance(body, dict) else None
    message = choices[0].get("message", {}) if isinstance(choices, list) and choices else {}
    content = message.get("content") if isinstance(message, dict) else None
    parse_error = None
    try:
        parsed = parse_decision(content)
        parse_status = "VALID"
    except (ValueError, json.JSONDecodeError) as error:
        parsed = None
        parse_status = "INVALID"
        parse_error = str(error)
    usage = body.get("usage", {}) if isinstance(body, dict) else {}
    return {
        "transport_status": "HTTP_OK" if status == 200 else f"HTTP_{status}",
        "http_status": status,
        "latency_seconds": latency,
        "model_observed": body.get("model"),
        "finish_reason": choices[0].get("finish_reason") if isinstance(choices, list) and choices else None,
        "usage": usage,
        "accounting_tokens": int(usage.get("total_tokens", 0)),
        "content": content,
        "parsed": parsed,
        "parse_status": parse_status,
        "parse_errors": [] if parse_error is None else [parse_error],
    }, request_raw, response_raw


def run_model(
    data: list[dict[str, Any]],
    protocol: dict[str, Any],
    endpoint: str,
    model: str,
    timeout: int,
    output: Path,
    receipt: Path,
    raw_dir: Path,
) -> dict[str, Any]:
    if protocol.get("status") != "FROZEN_BEFORE_MODEL_GENERATION":
        raise ValueError("protocol_not_frozen")
    if protocol["model_contract"]["max_generation_calls"] != MAX_GENERATION_CALLS:
        raise ValueError("generation call cap mismatch")
    if protocol["model_contract"]["retry_cap"] != 0:
        raise ValueError("retries are forbidden")
    by_uid = {str(item["uid"]): item for item in data}
    selected_uids = [str(row["uid"]) for row in protocol["selection"]["selected"]]
    if len(selected_uids) != MAX_GENERATION_CALLS:
        raise ValueError("selected UID count mismatch")
    if output.exists() or receipt.exists():
        raise RuntimeError("g3_model_run_already_started")
    if raw_dir.exists() and any(raw_dir.iterdir()):
        raise RuntimeError("g3_model_raw_directory_not_empty")
    raw_dir.mkdir(parents=True, exist_ok=True)
    calls = []
    rows = []
    stopped_early = False
    recovered_failure_path = output.parent / "G3_MODEL_FAILURE_RECEIPT_V1.json"
    start_call = 1
    if recovered_failure_path.exists():
        recovered = json.loads(recovered_failure_path.read_text(encoding="utf-8"))
        if recovered.get("generation_call") != 1:
            raise ValueError("recovered failure must be generation call 1")
        if recovered.get("uid") != selected_uids[0]:
            raise ValueError("recovered failure UID mismatch")
        calls.append(recovered)
        failed_item = by_uid[selected_uids[0]]
        failed_query = str(failed_item["probing_queries"][QUERY_FIELD])
        failed_ranked = bm25_ranked(failed_item, failed_query)
        failed_top3 = [index for index, _score in failed_ranked[:TOP3]]
        failed_top5 = [index for index, _score in failed_ranked[:TOP5]]
        rows.append(policy_row(
            failed_item,
            "model_selective_expansion",
            "INVALID",
            failed_top3,
            failed_top5,
            {"failure_receipt": recovered_failure_path.name},
        ))
        start_call = 2
    for generation_call, uid in enumerate(selected_uids[start_call - 1:], start=start_call):
        item = by_uid[uid]
        query = str(item["probing_queries"][QUERY_FIELD])
        ranked = bm25_ranked(item, query)
        top3 = [index for index, _score in ranked[:TOP3]]
        top5 = [index for index, _score in ranked[:TOP5]]
        prompt = build_decision_prompt(item, top3)
        call, request_raw, response_raw = post_model(endpoint, model, prompt, timeout)
        call_dir = raw_dir / uid
        call_dir.mkdir(parents=True, exist_ok=False)
        request_doc = {
            "generation_call": generation_call,
            "uid": uid,
            "model_expected": model,
            "retry_count": 0,
            "top3_indices_visible_as_session_labels": top3,
            "forbidden_actor_fields": list(FORBIDDEN_ACTOR_FIELDS),
            "request_payload": json.loads(request_raw.decode("utf-8")),
        }
        write_json(call_dir / "request.json", request_doc)
        (call_dir / "request.bin").write_bytes(request_raw)
        (call_dir / "response.bin").write_bytes(response_raw)
        write_json(call_dir / "call_receipt.json", call)
        calls.append({
            "uid": uid,
            "generation_call": generation_call,
            "http_status": call["http_status"],
            "transport_status": call["transport_status"],
            "model_observed": call["model_observed"],
            "finish_reason": call["finish_reason"],
            "usage": call["usage"],
            "accounting_tokens": call["accounting_tokens"],
            "latency_seconds": call["latency_seconds"],
            "retry_count": 0,
            "request_sha256": sha256_bytes(request_raw),
            "response_sha256": sha256_bytes(response_raw),
        })
        action = call["parsed"]["action"] if call["parsed"] is not None else "INVALID"
        rows.append(policy_row(
            item,
            "model_selective_expansion",
            action,
            top3,
            top5,
            {
                "confidence": call["parsed"]["confidence"] if call["parsed"] else None,
                "evidence_anchors": call["parsed"]["evidence_anchors"] if call["parsed"] else [],
                "missing_information": call["parsed"]["missing_information"] if call["parsed"] else [],
                "reason": call["parsed"]["reason"] if call["parsed"] else "; ".join(call["parse_errors"]),
                "prompt_chars": len(prompt),
            },
        ))
        if call["http_status"] != 200 or call["parse_status"] != "VALID":
            stopped_early = True
            break
        if call["model_observed"] != model:
            stopped_early = True
            break
    model_summary = summarize(rows)
    model_summary.update({
        "calls": len(calls),
        "accounting_tokens": sum(row["accounting_tokens"] for row in calls),
        "prompt_tokens": sum(
            int(row.get("usage", {}).get("prompt_tokens", 0) or row.get("prompt_tokens", 0))
            for row in calls
        ),
        "completion_tokens": sum(
            int(row.get("usage", {}).get("completion_tokens", 0) or row.get("completion_tokens", 0))
            for row in calls
        ),
        "latency_seconds_sum": round(
            sum(float(row.get("latency_seconds", row.get("server_total_seconds", 0.0))) for row in calls),
            6,
        ),
        "retry_count": 0,
    })
    result = {
        "schema": "g3_incremental_evidence_model_results_v1",
        "date": "2026-10-23",
        "evidence_identity": "DEV_ONLY_8_CALL_SELECTIVE_EVIDENCE_ACQUISITION_POLICY",
        "question": (
            "Can a model decide from top-3 evidence whether the next two ranked "
            "sessions add missing state/invalidation evidence, without answering the task?"
        ),
        "g2_distinction": (
            "G2 holds recovered state fixed and measures state-to-action transfer. "
            "This G3 probe stops before task answering and measures KEEP versus EXPAND."
        ),
        "protocol_sha256": sha256_file(output.parent / "G3_PROTOCOL_V1.json"),
        "selected_uids": selected_uids,
        "summary": model_summary,
        "rows": rows,
        "calls": calls,
        "stopped_early": stopped_early,
        "nonclaims": [
            "The 8 calls are development policy observations, not learned-policy training.",
            "Hidden relevant_session_index values are used only for post-hoc evaluation.",
            "The model decides evidence acquisition and never answers the STALE question.",
            "This is not independent external confirmation or a full benchmark estimate.",
        ],
    }
    write_json(output, result)
    receipt_payload = {
        "schema": "g3_incremental_evidence_model_receipt_v1",
        "status": "COMPLETE" if not stopped_early else "STOPPED_EARLY",
        "evidence_identity": result["evidence_identity"],
        "model_expected": model,
        "model_observed": sorted({row["model_observed"] for row in calls if row.get("model_observed")}),
        "planned_generation_calls": MAX_GENERATION_CALLS,
        "executed_generation_calls": len(calls),
        "physical_http_calls": len(calls),
        "accounting_tokens": sum(row["accounting_tokens"] for row in calls),
        "prompt_tokens": sum(
            int(row.get("usage", {}).get("prompt_tokens", 0) or row.get("prompt_tokens", 0))
            for row in calls
        ),
        "completion_tokens": sum(
            int(row.get("usage", {}).get("completion_tokens", 0) or row.get("completion_tokens", 0))
            for row in calls
        ),
        "retry_count": 0,
        "stopped_early": stopped_early,
        "results_path": str(output),
        "results_sha256": sha256_file(output),
    }
    write_json(receipt, receipt_payload)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    freeze = subparsers.add_parser("freeze")
    freeze.add_argument("--data", type=Path, required=True)
    freeze.add_argument("--prior-uids", type=Path, action="append", required=True)
    freeze.add_argument("--output", type=Path, required=True)

    offline = subparsers.add_parser("offline")
    offline.add_argument("--data", type=Path, required=True)
    offline.add_argument("--protocol", type=Path, required=True)
    offline.add_argument("--output", type=Path, required=True)

    model = subparsers.add_parser("run-model")
    model.add_argument("--data", type=Path, required=True)
    model.add_argument("--protocol", type=Path, required=True)
    model.add_argument("--output", type=Path, required=True)
    model.add_argument("--receipt", type=Path, required=True)
    model.add_argument("--raw-dir", type=Path, required=True)
    model.add_argument("--endpoint", default=ENDPOINT_DEFAULT)
    model.add_argument("--model", default=MODEL_DEFAULT)
    model.add_argument("--timeout", type=int, default=240)

    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError(f"output already exists: {args.output}")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    if args.command == "freeze":
        prior_uids = load_prior_uids(args.prior_uids)
        selected = select_model_items(data, prior_uids)
        protocol = {
            "schema": "g3_incremental_evidence_protocol_v1",
            "date": "2026-10-23",
            "status": "FROZEN_BEFORE_MODEL_GENERATION",
            "question": (
                "After top-3 retrieval, should the agent retain the current evidence "
                "or selectively inspect the next two ranked sessions?"
            ),
            "g2_distinction": (
                "The model never answers the task or maps a recovered state to action; "
                "it only chooses KEEP or EXPAND for evidence acquisition."
            ),
            "data": {
                "path": str(args.data),
                "sha256": sha256_file(args.data),
                "bytes": args.data.stat().st_size,
                "total_items": len(data),
            },
            "selection": {
                "rule": (
                    "Exclude every UID named in the supplied prior-UID files; sort "
                    "remaining T1 and T2 by UID ascending; select four of each."
                ),
                "prior_uid_count": len(prior_uids),
                "selected": [
                    {"uid": item["uid"], "type": item["type"]}
                    for item in selected
                ],
            },
            "retrieval_contract": {
                "query_field": QUERY_FIELD,
                "initial": "BM25 top-3",
                "increment": "BM25 ranks 4-5",
                "hidden_post_input_fields": ["relevant_session_index"],
                "forbidden_actor_fields": list(FORBIDDEN_ACTOR_FIELDS),
            },
            "model_contract": {
                "model": MODEL_DEFAULT,
                "endpoint": ENDPOINT_DEFAULT,
                "temperature": 0,
                "top_p": 1,
                "max_tokens": MAX_TOKENS,
                "response_format": "json_object",
                "enable_thinking": False,
                "concurrency": 1,
                "retry_cap": 0,
                "max_generation_calls": MAX_GENERATION_CALLS,
            },
            "strong_baselines": [
                "keep_top3",
                "always_expand_top5",
                "visible_gap_rule",
            ],
            "oracle_diagnostics": [
                "oracle_gain_rule",
                "oracle_pair_rule",
            ],
            "primary_metrics": [
                "final BOTH_OLD_AND_NEW coverage",
                "useful-expansion precision and recall",
                "pair-completion count",
                "mean selected context chars",
                "exact accounting tokens",
            ],
            "stop_conditions": [
                "Any generation call fails: stop without retry and preserve raw evidence.",
                "The model is not the expected Qwen3.6 identity: stop before further calls.",
                "Strict JSON/action validation fails: record INVALID and do not repair by retry.",
                "More than 8 generation calls are impossible by protocol.",
            ],
            "nonclaims": [
                "This is a development acquisition-policy probe, not learned-policy training.",
                "The 8 UIDs are unused relative to the supplied prior-UID registry but remain within public STALE.",
                "Oracle policies are hidden-reference diagnostics and are not deployable baselines.",
            ],
        }
        write_json(args.output, protocol)
        print(json.dumps(protocol, ensure_ascii=False, indent=2))
        return 0

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if args.command == "offline":
        if protocol.get("status") != "FROZEN_BEFORE_MODEL_GENERATION":
            raise ValueError("protocol_not_frozen")
        evaluated = evaluate_policies(data)
        output = {
            "schema": "g3_incremental_evidence_offline_results_v1",
            "date": "2026-10-23",
            "evidence_identity": "ZERO_MODEL_ALL_400_DETERMINISTIC_DEVELOPMENT_REPLAY",
            "data_sha256": sha256_file(args.data),
            "protocol_sha256": sha256_file(args.protocol),
            **evaluated,
            "nonclaims": [
                "Relevant indices are hidden structured references, not semantic gold.",
                "Oracle policies use hidden expansion outcomes and are diagnostics only.",
                "The replay measures evidence coverage and context cost, not answer correctness.",
            ],
        }
        write_json(args.output, output)
        print(json.dumps(output["summary"], ensure_ascii=False, indent=2))
        return 0

    result = run_model(
        data=data,
        protocol=protocol,
        endpoint=args.endpoint,
        model=args.model,
        timeout=args.timeout,
        output=args.output,
        receipt=args.receipt,
        raw_dir=args.raw_dir,
    )
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
