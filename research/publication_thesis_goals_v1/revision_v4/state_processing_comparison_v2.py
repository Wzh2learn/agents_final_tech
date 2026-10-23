"""Compare fair one-stage and two-stage state-processing arms on STALE."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

from stale_semantic_evaluation_v2 import evaluate_answer, match_group


MODEL_DEFAULT = "Qwen3.6-35B-A3B-Q4_K_M.gguf"
ENDPOINT_DEFAULT = "http://127.0.0.1:8004/v1/chat/completions"
MODELS_ENDPOINT_DEFAULT = "http://127.0.0.1:8004/v1/models"
DEVELOPMENT_UIDS = (
    "01f694b2-c555-4b6e-8ca0-5f11210e2227",
    "04fea765-0b32-4e8f-b4e9-225901f627b0",
    "009b7c99-b777-465a-bc3a-77f2d88c1318",
    "012f090e-6e02-4751-955d-574745069df3",
)
ARMS = ("direct_answer", "one_call_facts", "two_stage_timeline", "two_stage_state_card")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def get_json(url: str, timeout: int = 10) -> tuple[dict[str, Any], bytes]:
    request = urllib.request.Request(url, headers={"accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8")), raw


def parse_json_object(content: Any, required: set[str]) -> tuple[str, dict[str, Any] | None, list[str]]:
    if not isinstance(content, str):
        return "CONTENT_MISSING", None, ["content_not_string"]
    try:
        value = json.loads(content)
    except json.JSONDecodeError as error:
        return "INVALID_JSON", None, [f"{error.msg} at line {error.lineno} column {error.colno}"]
    if not isinstance(value, dict):
        return "SCHEMA_INVALID", None, ["root_not_object"]
    errors = []
    if set(value) != required:
        errors.append(f"field_set:{sorted(value)}")
    if errors:
        return "SCHEMA_INVALID", None, errors
    return "VALID", value, []


def post_model(
    endpoint: str,
    model: str,
    prompt: str,
    max_tokens: int,
    timeout: int,
    required_fields: set[str],
) -> dict[str, Any]:
    """Send exactly one request and preserve raw transport evidence."""
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
        endpoint, data=body, method="POST",
        headers={"accept": "application/json", "content-type": "application/json"},
    )
    started = time.perf_counter()
    raw = b""
    parsed_body: dict[str, Any] | None = None
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
        error_message = f"{error.msg} at line {error.lineno} column {error.colno}"
    content = None
    usage = {}
    if isinstance(parsed_body, dict):
        usage = parsed_body.get("usage", {}) if isinstance(parsed_body.get("usage"), dict) else {}
        choices = parsed_body.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
            content = message.get("content") if isinstance(message, dict) else None
    parse_status, parsed, parse_errors = (
        ("NOT_ATTEMPTED", None, [error_type])
        if error_type
        else parse_json_object(content, required_fields)
    )
    reported_tokens = usage.get("total_tokens")
    accounting_tokens = (
        int(reported_tokens)
        if isinstance(reported_tokens, int) and reported_tokens >= 0
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
    """Render official-style source roles, order and legal session times."""
    blocks = []
    sessions = item["haystack_session"]
    timestamps = item.get("timestamps", [])
    for source_index in selected:
        session = sessions[source_index]
        time_text = timestamps[source_index] if source_index < len(timestamps) else "unavailable"
        lines = [f"=== Session {source_index + 1} [Time: {time_text}] ==="]
        for turn_index, message in enumerate(session, start=1):
            role = "User" if message.get("role") == "user" else "Assistant"
            lines.append(f"{role} turn {turn_index}: {message.get('content', '')}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def answer_schema_instruction() -> str:
    return """Return exactly one JSON object:
{
  "decision": "ANSWER | UNKNOWN",
  "answer": "specific current-fact answer or null",
  "evidence_refs": ["session/turn references"]
}
If ANSWER, the answer must state the specific current fact, not only Yes or No.
If evidence is insufficient, use UNKNOWN and answer null. Do not invent events."""


def build_direct_prompt(query: str, evidence: str) -> str:
    return f"""Review the source-ordered conversation evidence and answer the question.
Distinguish user facts from assistant suggestions. Treat timestamps as source times,
not as proof that every statement is current.

{evidence}

Question: {query}

{answer_schema_instruction()}"""


def build_one_call_prompt(query: str, evidence: str) -> str:
    return f"""Extract only query-relevant facts and then answer, in one response.
Preserve source role and temporal status. Do not treat assistant suggestions or
future plans as current user facts.

{evidence}

Question: {query}

Return exactly one JSON object:
{{
  "facts": [{{"fact": "...", "source_ref": "...", "source_role": "user|assistant", "temporal_status": "current|past|future|suggestion"}}],
  "decision": "ANSWER | UNKNOWN",
  "answer": "specific current-fact answer or null",
  "evidence_refs": ["..."]
}}
Use at most 3 facts and compact `Session/turn` evidence_refs. If ANSWER, state
the specific current fact or concrete action in at most 80 words, not only Yes or No."""


def build_timeline_prompt(query: str, evidence: str) -> str:
    return f"""Build a query-focused fact timeline from the source evidence.
Preserve source role, source time and whether each statement is observed current
fact, past fact, future plan, or assistant suggestion. Do not decide the final answer.
Keep at most 3 timeline items and at most 2 current facts. Prefer the latest
user-state evidence and omit redundant assistant suggestions.

{evidence}

Question: {query}

Return exactly one JSON object:
{{
  "timeline": [{{"fact": "...", "source_ref": "...", "source_role": "user|assistant", "temporal_status": "current|past|future|suggestion"}}],
  "current_facts": ["..."],
  "unresolved": ["..."]
}}"""


def build_state_card_prompt(query: str, evidence: str) -> str:
    return f"""Extract a query-focused state transition from the source evidence.
Preserve source role and time. Separate observed facts from inferred downstream
effects. Do not answer the question.

{evidence}

Question: {query}

Return exactly one JSON object:
{{
  "old_state": "...",
  "new_state": "...",
  "change_type": "DIRECT | PROPAGATED | UNKNOWN",
  "status": "OBSERVED | INFERRED | UNRESOLVED",
  "evidence_refs": ["..."]
}}
Use at most 3 compact evidence_refs in `Session N, User/Assistant turn M` form.
Do not quote full messages in evidence_refs."""


def build_second_stage_prompt(query: str, intermediate: dict[str, Any]) -> str:
    return f"""Answer using only the extracted intermediate representation and the question.
Do not add events. If the representation is insufficient, return UNKNOWN.

Intermediate representation:
{json.dumps(intermediate, ensure_ascii=False, indent=2)}

Question: {query}

{answer_schema_instruction()}"""


def current_intermediate_text(arm: str, parsed: dict[str, Any]) -> str:
    """Return only current-state content for intermediate specificity checks."""
    if arm == "one_call_facts":
        if isinstance(parsed, list):
            facts = parsed
        elif isinstance(parsed, dict):
            facts = parsed.get("facts", [])
        else:
            facts = []
        return json.dumps(
            [fact for fact in facts if fact.get("temporal_status") == "current"],
            ensure_ascii=False,
        )
    if arm == "two_stage_timeline":
        timeline = parsed.get("timeline", []) if isinstance(parsed, dict) else []
        current_items = [
            item for item in timeline if item.get("temporal_status") == "current"
        ]
        return json.dumps(
            {
                "current_facts": parsed.get("current_facts", []),
                "timeline_current": current_items,
            },
            ensure_ascii=False,
        )
    if arm == "two_stage_state_card":
        return str((parsed or {}).get("new_state", ""))
    return ""


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
    by_arm = {}
    for arm in ARMS:
        group_calls = [call for call in calls if call["arm"] == arm]
        group_rows = [row for row in rows if row["arm"] == arm]
        by_arm[arm] = {
            "planned_calls": len(group_rows) * (2 if arm.startswith("two_stage") else 1),
            "observed_calls": len(group_calls),
            "http_ok": sum(call["transport_status"] == "HTTP_OK" for call in group_calls),
            "valid_json": sum(call["parse_status"] == "VALID" for call in group_calls),
            "semantic_success": sum(row["semantic"]["semantic_success"] for row in group_rows),
            "semantic_count": len(group_rows),
            "intermediate_specificity_success": sum(
                bool(row.get("intermediate_specificity", {}).get("success"))
                for row in group_rows
            ),
            "accounting_tokens": sum(call["accounting_tokens"] for call in group_calls),
            "completion_tokens": sum(
                int(call.get("usage", {}).get("completion_tokens", 0)) for call in group_calls
            ),
            "latency_seconds_sum": round(
                sum(call["latency_seconds"] for call in group_calls), 6
            ),
        }
    return {
        "overall": {
            "planned_calls": sum(row["planned_calls"] for row in by_arm.values()),
            "observed_calls": sum(row["observed_calls"] for row in by_arm.values()),
            "accounting_tokens": sum(row["accounting_tokens"] for row in by_arm.values()),
            "retry_count": 0,
        },
        "by_arm": by_arm,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--endpoint", default=ENDPOINT_DEFAULT)
    parser.add_argument("--models-endpoint", default=MODELS_ENDPOINT_DEFAULT)
    parser.add_argument("--model", default=MODEL_DEFAULT)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--arms", default=",".join(ARMS))
    args = parser.parse_args()
    active_arms = tuple(arm.strip() for arm in args.arms.split(",") if arm.strip())
    if not active_arms or any(arm not in ARMS for arm in active_arms):
        raise ValueError(f"invalid arms: {args.arms}")
    output_dir = args.output_dir.resolve()
    if (output_dir / "STATE_PROCESSING_COMPARISON_COMPLETE_V2").exists():
        raise RuntimeError("state_processing_comparison_already_complete")
    output_dir.mkdir(parents=True, exist_ok=True)
    data = {item["uid"]: item for item in json.loads(args.data.read_text(encoding="utf-8"))}
    references = json.loads(args.reference.read_text(encoding="utf-8"))["items"]
    preflight, preflight_raw = get_json(args.models_endpoint)
    model_ids = [row.get("id") for row in preflight.get("data", []) if isinstance(row, dict)]
    if args.model not in model_ids:
        raise RuntimeError(f"model_identity_mismatch:{model_ids}")
    calls: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    raw_dir = output_dir / "raw"
    stopped = None
    for uid in DEVELOPMENT_UIDS:
        item = data[uid]
        selected = sorted(int(index) for index in item["relevant_session_index"])[:2]
        evidence = format_sessions(item, selected)
        query = item["probing_queries"]["dim1_query"]
        for arm in active_arms:
            task_id = f"{uid}__{arm}"
            if arm == "direct_answer":
                prompt = build_direct_prompt(query, evidence)
                call = post_model(
                    args.endpoint, args.model, prompt, 512, args.timeout,
                    {"decision", "answer", "evidence_refs"},
                )
                call["arm"] = arm
                write_call_raw(raw_dir, task_id, "answer", call, {
                    "uid": uid, "arm": arm, "selected_indices": selected, "max_tokens": 512
                })
                calls.append(call)
                answer = (call.get("parsed") or {}).get("answer")
                intermediate_text = ""
                last_call = call
            elif arm == "one_call_facts":
                prompt = build_one_call_prompt(query, evidence)
                call = post_model(
                    args.endpoint, args.model, prompt, 512, args.timeout,
                    {"facts", "decision", "answer", "evidence_refs"},
                )
                call["arm"] = arm
                write_call_raw(raw_dir, task_id, "facts_and_answer", call, {
                    "uid": uid, "arm": arm, "selected_indices": selected, "max_tokens": 512
                })
                calls.append(call)
                parsed = call.get("parsed") or {}
                answer = parsed.get("answer")
                intermediate_text = current_intermediate_text(arm, parsed)
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
                    args.endpoint, args.model, stage1_prompt, stage1_max, args.timeout, required1
                )
                call1["arm"] = arm
                write_call_raw(raw_dir, task_id, "stage1", call1, {
                    "uid": uid, "arm": arm, "selected_indices": selected, "max_tokens": stage1_max
                })
                calls.append(call1)
                intermediate = call1.get("parsed") or {}
                intermediate_text = current_intermediate_text(arm, intermediate)
                if call1["parse_status"] == "VALID":
                    call2 = post_model(
                        args.endpoint,
                        args.model,
                        build_second_stage_prompt(query, intermediate),
                        stage2_max,
                        args.timeout,
                        {"decision", "answer", "evidence_refs"},
                    )
                    call2["arm"] = arm
                    write_call_raw(raw_dir, task_id, "stage2", call2, {
                        "uid": uid, "arm": arm, "selected_indices": selected, "max_tokens": stage2_max
                    })
                    calls.append(call2)
                    answer = (call2.get("parsed") or {}).get("answer")
                    last_call = call2
                else:
                    answer = None
                    last_call = call1
            reference = references[uid]
            matched = [
                index
                for index, group in enumerate(reference["required_concept_groups"])
                if match_group(group, intermediate_text or answer or "")
            ]
            old_terms = reference["old_state_concepts"]
            intermediate_affirms_old = any(
                term.lower() in intermediate_text.lower() for term in old_terms
            ) and not re.search(r"no longer|rather than|instead|old|previous", intermediate_text.lower())
            semantic = evaluate_answer(answer or "", item, reference, selected)
            rows.append({
                "uid": uid,
                "type": item["type"],
                "arm": arm,
                "selected_indices": selected,
                "answer": answer,
                "intermediate_text": intermediate_text,
                "intermediate_specificity": {
                    "success": bool(matched) and not intermediate_affirms_old,
                    "matched_required_groups": matched,
                    "affirms_old_state": intermediate_affirms_old,
                },
                "semantic": semantic,
            })
            if last_call.get("transport_status") != "HTTP_OK":
                stopped = f"transport_failure:{last_call.get('http_status')}"
                break
            if last_call.get("parse_status") != "VALID":
                stopped = f"parse_failure:{last_call.get('parse_status')}"
                break
        if stopped:
            break
    summary = summarize(calls, rows)
    result = {
        "schema": "state_processing_comparison_v2",
        "date": "2026-10-23",
        "evidence_identity": "DEV_ONLY_FOUR_ARM_FAIR_BUDGET_WITH_ORACLE_RETRIEVAL",
        "question": (
            "Do specific current-fact answers improve from source-preserving direct "
            "reasoning, one-call task decomposition, generic two-stage timeline, or "
            "the state-card representation at comparable generation budgets?"
        ),
        "visibility_contract": {
            "same_evidence": "oracle relevant top-2 raw sessions",
            "source_format": "official-style session index, timestamp, role and turn order",
            "hidden_from_actor": ["M_old", "M_new", "explanation", "relevant_session_index"],
            "semantic_scoring": "answer text plus selected evidence plus fixed semantic reference",
        },
        "budget_contract": {
            "direct_answer": {"calls": 1, "max_tokens": [512]},
            "one_call_facts": {"calls": 1, "max_tokens": [512]},
            "two_stage_timeline": {"calls": 2, "max_tokens": [384, 128]},
            "two_stage_state_card": {"calls": 2, "max_tokens": [256, 256]},
        },
        "development_uids": list(DEVELOPMENT_UIDS),
        "summary": summary,
        "rows": rows,
        "stopped_early": stopped,
        "limitations": [
            "These four UIDs are development objects and cannot estimate benchmark accuracy.",
            "Oracle retrieval isolates state processing but is not deployable retrieval.",
            "The semantic reference is AI-assisted development material, not human gold.",
            "Actual token and latency costs are reported; equal max generation cap is not equal realized compute.",
        ],
    }
    write_json(output_dir / "STATE_PROCESSING_COMPARISON_RESULTS_V2.json", result)
    receipt = {
        "schema": "state_processing_comparison_receipt_v2",
        "status": "COMPLETE_WITH_STOP" if stopped else "COMPLETE",
        "model": args.model,
        "planned_calls": summary["overall"]["planned_calls"],
        "executed_calls": summary["overall"]["observed_calls"],
        "accounting_tokens": summary["overall"]["accounting_tokens"],
        "retry_count": 0,
        "results_sha256": sha256_bytes(
            (output_dir / "STATE_PROCESSING_COMPARISON_RESULTS_V2.json").read_bytes()
        ),
        "stopped_early": stopped,
    }
    write_json(output_dir / "STATE_PROCESSING_COMPARISON_RECEIPT_V2.json", receipt)
    (output_dir / "STATE_PROCESSING_COMPARISON_COMPLETE_V2").write_text(
        "COMPLETE\n", encoding="utf-8"
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
