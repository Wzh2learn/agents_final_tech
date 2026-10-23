"""Compare fact and action use of the same evidence-derived state bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any


MODEL_DEFAULT = "Qwen3.6-35B-A3B-Q4_K_M.gguf"
ENDPOINT_DEFAULT = "http://127.0.0.1:8004/v1/chat/completions"
MODELS_ENDPOINT_DEFAULT = "http://127.0.0.1:8004/v1/models"
FORBIDDEN = ("M_old", "M_new", "explanation", "relevant_session_index")
REPRESENTATIONS = ("plain_fact_bundle", "evidence_decision_bundle")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def get_json(url: str, timeout: int = 10) -> tuple[dict[str, Any], bytes]:
    request = urllib.request.Request(url, headers={"accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8")), raw


def parse_exact_json(content: Any, required: set[str]) -> tuple[str, dict[str, Any] | None, list[str]]:
    if not isinstance(content, str):
        return "CONTENT_MISSING", None, ["content_not_string"]
    try:
        value = json.loads(content)
    except json.JSONDecodeError as error:
        return "INVALID_JSON", None, [f"{error.msg}:{error.lineno}:{error.colno}"]
    if not isinstance(value, dict) or set(value) != required:
        return "SCHEMA_INVALID", None, [f"field_set:{sorted(value if isinstance(value, dict) else [])}"]
    return "VALID", value, []


def post_model(
    endpoint: str,
    model: str,
    prompt: str,
    max_tokens: int,
    timeout: int,
    required_fields: set[str],
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "top_p": 1,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "chat_template_kwargs": {"enable_thinking": False},
        "stream": False,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={"accept": "application/json", "content-type": "application/json"},
    )
    started = time.perf_counter()
    raw = b""
    parsed_body = None
    error_type = None
    error_message = None
    status = None
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = int(response.status)
            raw = response.read()
        parsed_body = json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as error:
        status = int(error.code)
        raw = error.read()
        error_type = "HTTP_ERROR"
        error_message = str(error)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        error_type = "NETWORK_ERROR"
        error_message = str(error)
    except json.JSONDecodeError as error:
        error_type = "RESPONSE_NOT_JSON"
        error_message = str(error)
    content = None
    usage = {}
    if isinstance(parsed_body, dict):
        raw_usage = parsed_body.get("usage")
        usage = raw_usage if isinstance(raw_usage, dict) else {}
        choices = parsed_body.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
            content = message.get("content") if isinstance(message, dict) else None
    parse_status, parsed, parse_errors = (
        ("NOT_ATTEMPTED", None, [error_type])
        if error_type
        else parse_exact_json(content, required_fields)
    )
    total = usage.get("total_tokens")
    accounting_tokens = (
        int(total)
        if isinstance(total, int) and total >= 0
        else max(1, len(prompt.encode("utf-8")) // 4) + max_tokens
    )
    return {
        "request_payload": payload,
        "_request_body": body,
        "request_body_sha256": sha256_bytes(body),
        "_response_raw": raw,
        "response_body_sha256": sha256_bytes(raw),
        "response_body": parsed_body,
        "content": content,
        "usage": usage,
        "http_status": status,
        "transport_status": "HTTP_OK" if error_type is None else error_type,
        "error_type": error_type,
        "error_message": error_message,
        "latency_seconds": round(time.perf_counter() - started, 6),
        "accounting_attempts": 1,
        "physical_http_calls": 1,
        "accounting_tokens": accounting_tokens,
        "retry_count": 0,
        "parse_status": parse_status,
        "parsed": parsed,
        "parse_errors": parse_errors,
    }


def format_sessions(item: dict[str, Any], selected: list[int]) -> str:
    timestamps = item.get("timestamps", [])
    blocks = []
    for index in selected:
        time_value = timestamps[index] if index < len(timestamps) else "unavailable"
        lines = [f"=== Session {index + 1} [Time: {time_value}] ==="]
        for turn, message in enumerate(item["haystack_session"][index], start=1):
            role = "User" if message.get("role") == "user" else "Assistant"
            lines.append(f"{role} turn {turn}: {message.get('content', '')}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def bm25_select(item: dict[str, Any], query: str, top_k: int = 5) -> list[int]:
    import math
    import re
    from collections import Counter as CounterType

    stopwords = {
        "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "for",
        "from", "has", "have", "in", "is", "it", "its", "of", "on", "or", "the",
        "their", "them", "this", "to", "was", "were", "with", "you", "your",
    }
    query_terms = [
        token for token in re.findall(r"[a-z0-9]+", query.lower())
        if token not in stopwords and len(token) > 2
    ]
    documents = []
    for index in range(len(item["haystack_session"])):
        text = "\n".join(
            f"{message.get('role', '')} {message.get('content', '')}"
            for message in item["haystack_session"][index]
        )
        documents.append([
            token for token in re.findall(r"[a-z0-9]+", text.lower())
            if token not in stopwords and len(token) > 2
        ])
    query_counts = CounterType(query_terms)
    avg_len = sum(map(len, documents)) / len(documents)
    doc_frequency = {
        term: sum(term in set(document) for document in documents)
        for term in set(query_terms)
    }
    scores = []
    for index, document in enumerate(documents):
        frequencies = CounterType(document)
        score = 0.0
        for term, query_frequency in query_counts.items():
            frequency = frequencies.get(term, 0)
            if not frequency:
                continue
            df = doc_frequency[term]
            idf = math.log(1 + (len(documents) - df + 0.5) / (df + 0.5))
            score += (
                query_frequency
                * idf
                * frequency
                * 2.5
                / (frequency + 1.5 * (0.25 + 0.75 * len(document) / avg_len))
            )
        scores.append((score, -index, index))
    return [index for _score, _negative, index in sorted(scores, reverse=True)[:top_k]]


def build_bundle_prompt(kind: str, query: str, evidence: str) -> str:
    if kind == "plain_fact_bundle":
        schema = {
            "current_fact_1": "fact with compact source reference or null",
            "current_fact_2": "fact with compact source reference or null",
            "current_fact_3": "fact with compact source reference or null",
            "conflict_1": "stale or conflicting evidence or null",
            "conflict_2": "stale or conflicting evidence or null",
            "uncertainty_1": "missing evidence or null",
            "uncertainty_2": "missing evidence or null",
            "refs": ["compact source references"],
        }
        instruction = (
            "Extract a plain fact bundle. Separate user facts from assistant "
            "suggestions and past/future statements. Do not decide the action."
        )
    else:
        schema = {
            "confirmed_fact_1": "confirmed current fact or null",
            "confirmed_fact_2": "confirmed current fact or null",
            "invalidated_1": "unsupported assumption or null",
            "invalidated_2": "unsupported assumption or null",
            "uncertain_impact_1": "unresolved consequence or null",
            "uncertain_impact_2": "unresolved consequence or null",
            "constraint_1": "evidence-backed action constraint or null",
            "constraint_2": "evidence-backed action constraint or null",
            "unknown_1": "required clarification or null",
            "refs": ["compact source references"],
        }
        instruction = (
            "Extract an evidence-anchored decision bundle. Distinguish observed "
            "facts from inferred impacts. Add an action constraint only when it "
            "follows from confirmed facts or explicitly recorded uncertainty."
        )
    return f"""{instruction}

Fill only the fixed slots above. Leave unused slots null. Use compact
`Session/turn` references and do not copy unrelated history.

{evidence}

State-recovery query: {query}

Return exactly one JSON object matching this shape:
{json.dumps(schema, ensure_ascii=False, indent=2)}

Do not invent events. Do not answer the fact or action question in this stage."""


def build_answer_prompt(kind: str, question: str, bundle: dict[str, Any]) -> str:
    return f"""Answer the question using only this recovered bundle. Do not add facts.
If the bundle is insufficient, return UNKNOWN. If a short clarification is
required to avoid unsafe advice, return CLARIFY and state the minimum question.

Recovered bundle ({kind}):
{json.dumps(bundle, ensure_ascii=False, indent=2)}

Question: {question}

Return exactly one JSON object:
{{
  "decision": "ANSWER | CLARIFY | UNKNOWN",
  "answer": "specific answer, clarification, or null",
  "basis_refs": ["bundle item references"],
  "constraints_considered": ["constraint names or descriptions"]
}}"""


def write_call_raw(
    raw_dir: Path,
    task_id: str,
    stage: str,
    call: dict[str, Any],
    meta: dict[str, Any],
) -> None:
    target = raw_dir / task_id / stage
    target.mkdir(parents=True, exist_ok=True)
    request_raw = call.pop("_request_body")
    response_raw = call.pop("_response_raw")
    (target / "request.bin").write_bytes(request_raw)
    (target / "response.bin").write_bytes(response_raw)
    write_json(target / "request.json", {"meta": meta, "request": call["request_payload"]})
    write_json(target / "call_receipt.json", {
        key: value for key, value in call.items() if key != "response_body"
    })


def summarize(calls: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_representation = {}
    for representation in REPRESENTATIONS:
        representation_calls = [call for call in calls if call["representation"] == representation]
        representation_rows = [row for row in rows if row["representation"] == representation]
        fact_rows = [row for row in representation_rows if row["question_kind"] == "fact"]
        action_rows = [row for row in representation_rows if row["question_kind"] == "action"]
        by_representation[representation] = {
            "calls": len(representation_calls),
            "accounting_tokens": sum(call["accounting_tokens"] for call in representation_calls),
            "fact_answered": sum(row["answer_record"]["decision"] == "ANSWER" for row in fact_rows),
            "action_answered": sum(row["answer_record"]["decision"] == "ANSWER" for row in action_rows),
            "fact_clarify": sum(row["answer_record"]["decision"] == "CLARIFY" for row in fact_rows),
            "action_clarify": sum(row["answer_record"]["decision"] == "CLARIFY" for row in action_rows),
            "fact_unknown": sum(row["answer_record"]["decision"] == "UNKNOWN" for row in fact_rows),
            "action_unknown": sum(row["answer_record"]["decision"] == "UNKNOWN" for row in action_rows),
        }
    return {
        "overall": {
            "planned_calls": 48,
            "observed_calls": len(calls),
            "accounting_tokens": sum(call["accounting_tokens"] for call in calls),
            "retry_count": 0,
        },
        "by_representation": by_representation,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--endpoint", default=ENDPOINT_DEFAULT)
    parser.add_argument("--models-endpoint", default=MODELS_ENDPOINT_DEFAULT)
    parser.add_argument("--model", default=MODEL_DEFAULT)
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if protocol.get("status") != "FROZEN_BEFORE_MODEL_GENERATION":
        raise ValueError("protocol_not_frozen")
    output_dir = args.output_dir.resolve()
    if (output_dir / "G2_FIXED_STATE_COMPLETE_V5").exists():
        raise RuntimeError("g2_fixed_state_already_complete")
    output_dir.mkdir(parents=True, exist_ok=True)
    data = {item["uid"]: item for item in json.loads(args.data.read_text(encoding="utf-8"))}
    preflight, _raw = get_json(args.models_endpoint)
    model_ids = [row.get("id") for row in preflight.get("data", []) if isinstance(row, dict)]
    if args.model not in model_ids:
        raise RuntimeError(f"model_identity_mismatch:{model_ids}")
    calls = []
    rows = []
    raw_dir = output_dir / "raw"
    stopped = None
    for uid in protocol["uids"]:
        item = data[uid]
        selected = bm25_select(item, item["probing_queries"]["dim1_query"], 5)
        evidence = format_sessions(item, selected)
        for representation in REPRESENTATIONS:
            task_id = f"{uid}__{representation}"
            bundle_call = post_model(
                args.endpoint,
                args.model,
                build_bundle_prompt(
                    representation, item["probing_queries"]["dim1_query"], evidence
                ),
                512,
                args.timeout,
                set(
                    [
                        "current_fact_1", "current_fact_2", "current_fact_3",
                        "conflict_1", "conflict_2", "uncertainty_1",
                        "uncertainty_2", "refs",
                    ]
                    if representation == "plain_fact_bundle"
                    else [
                        "confirmed_fact_1", "confirmed_fact_2", "invalidated_1",
                        "invalidated_2", "uncertain_impact_1", "uncertain_impact_2",
                        "constraint_1", "constraint_2", "unknown_1", "refs",
                    ]
                ),
            )
            bundle_call["representation"] = representation
            write_call_raw(raw_dir, task_id, "recovery", bundle_call, {
                "uid": uid,
                "representation": representation,
                "selected_indices": selected,
                "stage": "recovery",
                "max_tokens": 512,
            })
            calls.append(bundle_call)
            bundle = bundle_call.get("parsed") or {}
            if bundle_call.get("transport_status") != "HTTP_OK":
                stopped = f"transport_failure:{bundle_call.get('http_status')}"
                break
            if bundle_call.get("parse_status") != "VALID":
                stopped = f"parse_failure:{bundle_call.get('parse_status')}"
                break
            for question_kind, query_key in (("fact", "dim1_query"), ("action", "dim3_query")):
                answer_call = post_model(
                    args.endpoint,
                    args.model,
                    build_answer_prompt(representation, item["probing_queries"][query_key], bundle),
                    512,
                    args.timeout,
                    {"decision", "answer", "basis_refs", "constraints_considered"},
                )
                answer_call["representation"] = representation
                write_call_raw(raw_dir, task_id, question_kind, answer_call, {
                    "uid": uid,
                    "representation": representation,
                    "selected_indices": selected,
                    "stage": question_kind,
                    "max_tokens": 512,
                })
                calls.append(answer_call)
                rows.append({
                    "uid": uid,
                    "representation": representation,
                    "question_kind": question_kind,
                    "selected_indices": selected,
                    "bundle": bundle,
                    "answer_record": answer_call.get("parsed") or {},
                    "answer_parse_status": answer_call.get("parse_status"),
                })
                if answer_call.get("transport_status") != "HTTP_OK":
                    stopped = f"transport_failure:{answer_call.get('http_status')}"
                    break
                if answer_call.get("parse_status") != "VALID":
                    stopped = f"parse_failure:{answer_call.get('parse_status')}"
                    break
            if stopped:
                break
        if stopped:
            break
    summary = summarize(calls, rows)
    result = {
        "schema": "g2_fixed_state_transfer_results_v5",
        "date": "2026-10-23",
        "evidence_identity": "DEV_FIXED_EVIDENCE_FIXED_STATE_FACT_ACTION_TRANSFER",
        "protocol_sha256": sha256_bytes(args.protocol.read_bytes()),
        "model_identity_observed": model_ids,
        "summary": summary,
        "rows": rows,
        "stopped_early": stopped,
        "limitations": [
            "These eight UIDs are development cases and several were selected after judge review.",
            "Retrieval is held fixed within each representation but remains BM25 top-5, not oracle evidence.",
            "The two representations are diagnostic variants and are not new memory architectures.",
            "Answer correctness still requires the separate calibrated evaluation contract.",
        ],
    }
    write_json(output_dir / "G2_FIXED_STATE_RESULTS_V5.json", result)
    receipt = {
        "schema": "g2_fixed_state_receipt_v5",
        "status": "COMPLETE_WITH_STOP" if stopped else "COMPLETE",
        "model": args.model,
        "planned_calls": 48,
        "executed_calls": len(calls),
        "accounting_tokens": summary["overall"]["accounting_tokens"],
        "retry_count": 0,
        "results_sha256": sha256_bytes(
            (output_dir / "G2_FIXED_STATE_RESULTS_V5.json").read_bytes()
        ),
        "stopped_early": stopped,
    }
    write_json(output_dir / "G2_FIXED_STATE_RECEIPT_V5.json", receipt)
    (output_dir / "G2_FIXED_STATE_COMPLETE_V5").write_text("COMPLETE\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
