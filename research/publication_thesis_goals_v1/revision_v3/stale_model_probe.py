"""Run a bounded STALE model probe without exposing hidden reference metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


MODEL_DEFAULT = "Qwen3.6-35B-A3B-Q4_K_M.gguf"
ENDPOINT_DEFAULT = "http://127.0.0.1:8004/v1/chat/completions"
MODELS_ENDPOINT_DEFAULT = "http://127.0.0.1:8004/v1/models"
MAX_TOKENS_DEFAULT = 256
TOP_K_DEFAULT = 2
FORBIDDEN_ACTOR_LITERALS = ("M_old", "M_new", "explanation", "relevant_session_index")
QUERY_FIELDS = ("dim1_query", "dim2_query", "dim3_query")
ARMS = ("query_only", "lexical_top2", "oracle_relevant_top2")
OUTPUT_FIELDS = {
    "decision",
    "state_resolution",
    "premise_resistance",
    "action_adaptation",
    "answer",
}
DECISIONS = {"ANSWER", "UNKNOWN", "REFUSE"}
STATE_RESOLUTIONS = {
    "STALE_DETECTED",
    "STALE_NOT_DETECTED",
    "UNKNOWN",
    "NOT_APPLICABLE",
}
PREMISE_RESISTANCE = {
    "FALSE_PREMISE_REJECTED",
    "FALSE_PREMISE_ACCEPTED",
    "UNKNOWN",
    "NOT_APPLICABLE",
}
ACTION_ADAPTATION = {
    "CURRENT_STATE_ALIGNED",
    "STALE_STATE_ALIGNED",
    "UNKNOWN",
    "NOT_APPLICABLE",
}


def sha256_bytes(value: bytes) -> str:
    """Return a SHA-256 hex digest."""
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    """Return a SHA-256 hex digest for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    """Write deterministic, UTF-8 JSON."""
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def get_json(url: str, timeout: int = 10) -> tuple[dict[str, Any], bytes]:
    """Read one JSON object and preserve the raw response."""
    request = urllib.request.Request(url, headers={"accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8")), raw


def tokens(text: str) -> set[str]:
    """Return simple lowercase lexical tokens."""
    return {part for part in "".join(
        character.lower() if character.isalnum() else " " for character in text
    ).split() if part}


def session_text(session: list[dict[str, Any]]) -> str:
    """Render session messages without original session indices."""
    return "\n".join(
        f"[{str(message.get('role', 'unknown'))}] {str(message.get('content', ''))}"
        for message in session
    )


def lexical_ranking(query: str, sessions: list[list[dict[str, Any]]]) -> list[int]:
    """Rank sessions by unique-token overlap, breaking ties toward earlier sessions."""
    query_tokens = tokens(query)
    scores = []
    for index, session in enumerate(sessions):
        overlap = len(query_tokens & tokens(session_text(session)))
        scores.append((overlap, -index, index))
    return [index for _overlap, _negative_index, index in sorted(scores, reverse=True)]


def select_instances(data: list[dict[str, Any]], total: int = 4) -> list[dict[str, Any]]:
    """Select a deterministic balanced T1/T2 subset by UID."""
    if total % 2:
        raise ValueError("total must be even")
    by_type: dict[str, list[dict[str, Any]]] = {"T1": [], "T2": []}
    for item in data:
        kind = str(item.get("type", "")).upper()
        if kind in by_type:
            by_type[kind].append(item)
    per_type = total // 2
    if any(len(rows) < per_type for rows in by_type.values()):
        raise ValueError("dataset does not contain the requested balanced subset")
    for rows in by_type.values():
        rows.sort(key=lambda item: str(item["uid"]))
    return by_type["T1"][:per_type] + by_type["T2"][:per_type]


def selected_sessions(
    item: dict[str, Any], arm: str, top_k: int
) -> tuple[list[int], list[list[dict[str, Any]]]]:
    """Select evidence sessions for one arm."""
    sessions = item["haystack_session"]
    relevant = sorted(int(index) for index in item["relevant_session_index"])
    if arm == "query_only":
        indices: list[int] = []
    elif arm == "lexical_top2":
        query = str(item["probe_query"])
        indices = sorted(lexical_ranking(query, sessions)[:top_k])
    elif arm == "oracle_relevant_top2":
        indices = sorted(relevant[:top_k])
    else:
        raise ValueError(f"unknown arm: {arm}")
    return indices, [sessions[index] for index in indices]


def build_actor_prompt(
    query: str, sessions: list[list[dict[str, Any]]]
) -> str:
    """Build the complete actor-visible prompt for one request."""
    if sessions:
        evidence = "\n\n".join(
            f"<evidence_session_{position:02d}>\n{session_text(session)}\n</evidence_session_{position:02d}>"
            for position, session in enumerate(sessions, start=1)
        )
    else:
        evidence = "No evidence session was selected."
    prompt = f"""Answer the user question using only the selected evidence below.
Do not assume facts that are absent from the selected evidence. If the evidence is
insufficient, return UNKNOWN rather than inventing a state or action.

Selected evidence:
{evidence}

User question:
{query}

Return only one JSON object with exactly these five fields:
{{
  "decision": "ANSWER | UNKNOWN | REFUSE",
  "state_resolution": "STALE_DETECTED | STALE_NOT_DETECTED | UNKNOWN | NOT_APPLICABLE",
  "premise_resistance": "FALSE_PREMISE_REJECTED | FALSE_PREMISE_ACCEPTED | UNKNOWN | NOT_APPLICABLE",
  "action_adaptation": "CURRENT_STATE_ALIGNED | STALE_STATE_ALIGNED | UNKNOWN | NOT_APPLICABLE",
  "answer": "brief answer in the question language, or null"
}}

Field requirements:
- decision is ANSWER when the selected evidence supports a direct answer.
- decision is UNKNOWN when evidence is insufficient.
- decision is REFUSE only for a policy refusal.
- state_resolution records whether the selected evidence indicates that an earlier
  state is no longer valid.
- premise_resistance records whether a false premise in the question is rejected.
- action_adaptation records whether the answer or recommendation follows the current
  evidence rather than an outdated state.
- Use UNKNOWN for insufficient evidence and NOT_APPLICABLE only when a dimension is
  unrelated to the question.
- If decision is not ANSWER, answer must be null. If decision is ANSWER, answer must
  be a non-empty string.
- Do not add fields, code fences, or prose outside the JSON object."""
    serialized = json.dumps({"prompt": prompt}, ensure_ascii=False)
    found = [literal for literal in FORBIDDEN_ACTOR_LITERALS if literal in serialized]
    if found:
        raise ValueError(f"actor_prompt_forbidden_literal:{','.join(found)}")
    return prompt


def validate_output(value: Any) -> tuple[bool, list[str]]:
    """Strictly validate the model JSON without coercion."""
    if not isinstance(value, dict):
        return False, ["root_not_object"]
    errors = []
    if set(value) != OUTPUT_FIELDS:
        errors.append(f"field_set:{sorted(value)}")
    decision = value.get("decision")
    if decision not in DECISIONS:
        errors.append(f"decision:{decision}")
    if value.get("state_resolution") not in STATE_RESOLUTIONS:
        errors.append(f"state_resolution:{value.get('state_resolution')}")
    if value.get("premise_resistance") not in PREMISE_RESISTANCE:
        errors.append(f"premise_resistance:{value.get('premise_resistance')}")
    if value.get("action_adaptation") not in ACTION_ADAPTATION:
        errors.append(f"action_adaptation:{value.get('action_adaptation')}")
    answer = value.get("answer")
    if decision == "ANSWER":
        if not isinstance(answer, str) or not answer.strip():
            errors.append("answer_required_for_ANSWER")
    elif answer is not None:
        errors.append("answer_must_be_null_for_non_ANSWER")
    return not errors, errors


def parse_model_content(content: Any) -> dict[str, Any]:
    """Parse one model response strictly; no JSON extraction or retry."""
    if not isinstance(content, str):
        return {"parse_status": "CONTENT_MISSING", "parse_errors": ["content_not_string"]}
    try:
        value = json.loads(content)
    except json.JSONDecodeError as error:
        return {
            "parse_status": "INVALID_JSON",
            "parse_errors": [f"{error.msg} at line {error.lineno} column {error.colno}"],
        }
    valid, errors = validate_output(value)
    return {
        "parse_status": "VALID" if valid else "SCHEMA_INVALID",
        "parse_errors": errors,
        "parsed": value if valid else None,
    }


def estimate_tokens(text: str) -> int:
    """Conservatively estimate tokens when the server omits usage."""
    return max(1, math.ceil(len(text.encode("utf-8")) / 4))


def post_model(
    endpoint: str,
    model: str,
    prompt: str,
    max_tokens: int,
    timeout: int,
) -> dict[str, Any]:
    """Send exactly one model request and preserve transport evidence."""
    request_payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "top_p": 1,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "chat_template_kwargs": {"enable_thinking": False},
        "stream": False,
    }
    body = json.dumps(request_payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={"accept": "application/json", "content-type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    raw = b""
    http_status: int | None = None
    error_type: str | None = None
    error_message: str | None = None
    parsed_body: dict[str, Any] | None = None
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            http_status = int(response.status)
            raw = response.read()
        parsed_body = json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as error:
        http_status = int(error.code)
        raw = error.read()
        error_type = "HTTP_ERROR"
        error_message = str(error)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        error_type = "NETWORK_ERROR"
        error_message = str(error)
    except json.JSONDecodeError as error:
        error_type = "RESPONSE_NOT_JSON"
        error_message = f"{error.msg} at line {error.lineno} column {error.colno}"
    latency = round(time.perf_counter() - started, 6)
    usage = parsed_body.get("usage", {}) if isinstance(parsed_body, dict) else {}
    if not isinstance(usage, dict):
        usage = {}
    reported_total = usage.get("total_tokens")
    accounting_tokens = (
        int(reported_total)
        if isinstance(reported_total, int) and reported_total >= 0
        else estimate_tokens(prompt) + max_tokens
    )
    content: Any = None
    if isinstance(parsed_body, dict):
        choices = parsed_body.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
            content = message.get("content") if isinstance(message, dict) else None
    parse_result = parse_model_content(content) if error_type is None else {
        "parse_status": "NOT_ATTEMPTED",
        "parse_errors": [error_type],
    }
    return {
        "request_payload": request_payload,
        "_request_body": body,
        "request_body_sha256": sha256_bytes(body),
        "_response_raw": raw,
        "response_body_sha256": sha256_bytes(raw),
        "response_bytes": len(raw),
        "response_body": parsed_body,
        "content": content,
        "usage": usage,
        "http_status": http_status,
        "transport_status": "HTTP_OK" if error_type is None else error_type,
        "error_type": error_type,
        "error_message": error_message,
        "latency_seconds": latency,
        "accounting_attempts": 1,
        "physical_http_calls": 1,
        "accounting_tokens": accounting_tokens,
        "accounting_tokens_source": (
            "reported_total_tokens" if isinstance(reported_total, int) and reported_total >= 0
            else "conservative_prompt_estimate_plus_max_tokens"
        ),
        "retry_count": 0,
        **parse_result,
    }


def hidden_reference(
    item: dict[str, Any], selected_indices: list[int], sessions: list[list[dict[str, Any]]]
) -> dict[str, Any]:
    """Describe hidden evidence coverage for post-hoc scoring only."""
    relevant = sorted(int(index) for index in item["relevant_session_index"])
    selected_set = set(selected_indices)
    text = "\n".join(session_text(session) for session in sessions)
    return {
        "relevant_indices": relevant,
        "selected_indices": selected_indices,
        "relevant_hits": sorted(selected_set.intersection(relevant)),
        "relevant_recall": (
            len(selected_set.intersection(relevant)) / len(relevant) if relevant else None
        ),
        "old_reference_text_present": str(item["M_old"]) in text,
        "new_reference_text_present": str(item["M_new"]) in text,
    }


def primary_proxy(dimension: str, parsed: dict[str, Any], reference: dict[str, Any]) -> str:
    """Classify one structured output against hidden reference coverage."""
    if dimension == "dim1":
        observed = parsed["state_resolution"]
        strong = "STALE_DETECTED"
        unsafe = "STALE_NOT_DETECTED"
    elif dimension == "dim2":
        observed = parsed["premise_resistance"]
        strong = "FALSE_PREMISE_REJECTED"
        unsafe = "FALSE_PREMISE_ACCEPTED"
    elif dimension == "dim3":
        observed = parsed["action_adaptation"]
        strong = "CURRENT_STATE_ALIGNED"
        unsafe = "STALE_STATE_ALIGNED"
    else:
        raise ValueError(f"unknown dimension: {dimension}")
    if observed == strong and reference["new_reference_text_present"]:
        return "REFERENCE_MATCH"
    if observed == "UNKNOWN":
        return "SAFE_UNKNOWN"
    if observed == "NOT_APPLICABLE":
        return "UNRESOLVED_NOT_APPLICABLE"
    if observed == unsafe:
        return "UNSUPPORTED_STALE_ACCEPT"
    return "MISMATCH_OR_UNRESOLVED"


def summarize(rows: list[dict[str, Any]], planned_total: int = 36) -> dict[str, Any]:
    """Summarize parsing, grounded proxies, cost, and context by arm/dimension."""
    result: dict[str, Any] = {"overall": {}, "by_arm": {}, "by_dimension": {}}
    for group_name, key, group_count in (
        ("by_arm", "arm", len(ARMS)),
        ("by_dimension", "dimension", len(QUERY_FIELDS)),
    ):
        planned_per_group = planned_total // group_count
        if planned_per_group * group_count != planned_total:
            raise ValueError("planned_total is not divisible across summary groups")
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[str(row[key])].append(row)
        for name, group in sorted(grouped.items()):
            result[group_name][name] = {
                "planned": planned_per_group,
                "observed": len(group),
                "physical_http_calls": sum(int(row["call"]["physical_http_calls"]) for row in group),
                "http_ok": sum(row["call"]["transport_status"] == "HTTP_OK" for row in group),
                "valid_json": sum(row["call"]["parse_status"] == "VALID" for row in group),
                "proxy_counts": dict(Counter(row["primary_proxy"] for row in group)),
                "decision_counts": dict(Counter(
                    row["call"].get("parsed", {}).get("decision", "PARSE_FAILURE")
                    if row["call"].get("parsed") is not None else "PARSE_FAILURE"
                    for row in group
                )),
                "accounting_tokens": sum(int(row["call"]["accounting_tokens"]) for row in group),
                "latency_seconds_sum": round(
                    sum(float(row["call"]["latency_seconds"]) for row in group), 6
                ),
                "mean_context_chars": (
                    sum(int(row["context_chars"]) for row in group) / len(group) if group else 0.0
                ),
            }
    result["overall"] = {
        "planned": planned_total,
        "observed": len(rows),
        "physical_http_calls": sum(int(row["call"]["physical_http_calls"]) for row in rows),
        "http_ok": sum(row["call"]["transport_status"] == "HTTP_OK" for row in rows),
        "valid_json": sum(row["call"]["parse_status"] == "VALID" for row in rows),
        "parse_status_counts": dict(Counter(row["call"]["parse_status"] for row in rows)),
        "proxy_counts": dict(Counter(row["primary_proxy"] for row in rows)),
        "decision_counts": dict(Counter(
            row["call"].get("parsed", {}).get("decision", "PARSE_FAILURE")
            if row["call"].get("parsed") is not None else "PARSE_FAILURE"
            for row in rows
        )),
        "accounting_attempts": sum(int(row["call"]["accounting_attempts"]) for row in rows),
        "accounting_tokens": sum(int(row["call"]["accounting_tokens"]) for row in rows),
        "latency_seconds_sum": round(
            sum(float(row["call"]["latency_seconds"]) for row in rows), 6
        ),
    }
    return result


def build_rows(
    selected: list[dict[str, Any]], endpoint: str, model: str, max_tokens: int,
    timeout: int, raw_dir: Path
) -> tuple[list[dict[str, Any]], bool]:
    """Run all planned rows sequentially and retain each raw request/response."""
    rows: list[dict[str, Any]] = []
    stop_reason: str | None = None
    raw_dir.mkdir(parents=True, exist_ok=True)
    attempt = 0
    for item in selected:
        sessions_all = item["haystack_session"]
        for query_field in QUERY_FIELDS:
            query = str(item["probing_queries"][query_field])
            for arm in ARMS:
                attempt += 1
                indices, sessions = selected_sessions(
                    {**item, "probe_query": query}, arm, TOP_K_DEFAULT
                )
                try:
                    prompt = build_actor_prompt(query, sessions)
                except ValueError as error:
                    rows.append({
                        "attempt": attempt,
                        "uid": item["uid"],
                        "type": item["type"],
                        "dimension": query_field.removesuffix("_query"),
                        "query_field": query_field,
                        "arm": arm,
                        "context_chars": sum(len(session_text(session)) for session in sessions),
                        "hidden_reference": hidden_reference(item, indices, sessions),
                        "call": {
                            "transport_status": "LEAK_BLOCKED_BEFORE_HTTP",
                            "error_type": "ACTOR_INPUT_LEAK",
                            "error_message": str(error),
                            "parse_status": "NOT_ATTEMPTED",
                            "parse_errors": ["ACTOR_INPUT_LEAK"],
                            "accounting_attempts": 0,
                            "physical_http_calls": 0,
                            "accounting_tokens": 0,
                            "latency_seconds": 0.0,
                            "retry_count": 0,
                        },
                        "primary_proxy": "NOT_RUN",
                    })
                    stop_reason = "actor_input_leak"
                    break
                call = post_model(endpoint, model, prompt, max_tokens, timeout)
                request_raw = call.pop("_request_body")
                response_raw = call.pop("_response_raw")
                row = {
                    "attempt": attempt,
                    "uid": item["uid"],
                    "type": item["type"],
                    "dimension": query_field.removesuffix("_query"),
                    "query_field": query_field,
                    "arm": arm,
                    "context_chars": len(prompt),
                    "selected_session_chars": sum(len(session_text(session)) for session in sessions),
                    "selected_session_count": len(sessions),
                    "hidden_reference": hidden_reference(item, indices, sessions),
                    "call": call,
                }
                if call.get("parsed") is not None:
                    row["primary_proxy"] = primary_proxy(
                        str(row["dimension"]), call["parsed"], row["hidden_reference"]
                    )
                else:
                    row["primary_proxy"] = "PARSE_FAILURE"
                attempt_dir = raw_dir / f"attempt_{attempt:03d}"
                attempt_dir.mkdir(parents=True, exist_ok=True)
                write_json(attempt_dir / "request.json", {
                    "meta": {
                        "attempt": attempt,
                        "uid": item["uid"],
                        "type": item["type"],
                        "dimension": row["dimension"],
                        "arm": arm,
                        "selected_session_indices_hidden_from_actor": indices,
                        "retry_count": 0,
                    },
                    "request": call["request_payload"],
                })
                (attempt_dir / "response.bin").write_bytes(
                    response_raw
                )
                (attempt_dir / "request.bin").write_bytes(request_raw)
                write_json(attempt_dir / "call_receipt.json", {
                    key: value for key, value in call.items() if key not in {"request_payload", "response_body"}
                })
                rows.append(row)
                if call["transport_status"] != "HTTP_OK":
                    status = call.get("http_status")
                    stop_reason = (
                        f"systemic_transport_failure:{call['transport_status']}"
                        f":http_status={status}"
                    )
                    break
            if stop_reason:
                break
        if stop_reason:
            break
    return rows, bool(stop_reason)


def main() -> int:
    """Run the bounded probe and write results plus a receipt."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--endpoint", default=ENDPOINT_DEFAULT)
    parser.add_argument("--models-endpoint", default=MODELS_ENDPOINT_DEFAULT)
    parser.add_argument("--model", default=MODEL_DEFAULT)
    parser.add_argument("--max-tokens", type=int, default=MAX_TOKENS_DEFAULT)
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args()
    if args.max_tokens < 1 or args.timeout < 1:
        raise ValueError("max_tokens and timeout must be positive")
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if (output_dir / "STALE_MODEL_COMPLETE_V1").exists():
        raise RuntimeError("stale_model_probe_already_complete")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("dataset root must be a list")
    selected = select_instances(data, total=4)
    preflight, preflight_raw = get_json(args.models_endpoint)
    model_rows = preflight.get("data", []) if isinstance(preflight, dict) else []
    model_ids = [row.get("id") for row in model_rows if isinstance(row, dict)]
    if args.model not in model_ids:
        raise RuntimeError(f"model_identity_mismatch:{model_ids}")
    rows, stopped = build_rows(
        selected,
        args.endpoint,
        args.model,
        args.max_tokens,
        args.timeout,
        output_dir / "stale_model_raw",
    )
    results = {
        "schema": "stale_model_probe_v1",
        "date": "2026-10-23",
        "evidence_identity": "DEV_ONLY_REAL_MODEL_OBSERVATIONS_WITH_STRUCTURED_REFERENCE_PROXIES",
        "scientific_question": (
            "Does query-only, lexical top-2, or hidden-reference top-2 evidence change "
            "grounded stale-state recognition and safe handling of stale premises/actions?"
        ),
        "actor_visibility_contract": {
            "forbidden_metadata": list(FORBIDDEN_ACTOR_LITERALS),
            "allowed_evidence": "only selected raw session messages and the target query",
            "hidden_reference_use": "post-hoc coverage and structured proxy scoring only",
        },
        "data": {
            "path": str(args.data),
            "sha256": sha256_file(args.data),
            "bytes": args.data.stat().st_size,
            "total_items": len(data),
        },
        "selection": {
            "item_count": len(selected),
            "uids": [{"uid": item["uid"], "type": item["type"]} for item in selected],
            "queries_per_item": len(QUERY_FIELDS),
            "arms": list(ARMS),
            "top_k": TOP_K_DEFAULT,
            "planned_generation_calls": len(selected) * len(QUERY_FIELDS) * len(ARMS),
        },
        "model_request_contract": {
            "model_expected": args.model,
            "endpoint": args.endpoint,
            "temperature": 0,
            "top_p": 1,
            "max_tokens": args.max_tokens,
            "response_format": {"type": "json_object"},
            "enable_thinking": False,
            "concurrency": 1,
            "retry_cap": 0,
            "timeout_seconds": args.timeout,
        },
        "model_identity_observed": model_ids,
        "preflight_http_calls": 1,
        "preflight_response_sha256": sha256_bytes(preflight_raw),
        "official_llm_judge": {
            "used": False,
            "role": "AUXILIARY_ONLY_NOT_RUN",
            "note": "The main probe uses strict parsing and hidden-reference proxies; no judge request was issued.",
        },
        "summary": summarize(
            rows,
            planned_total=len(selected) * len(QUERY_FIELDS) * len(ARMS),
        ),
        "rows": rows,
        "stopped_early": stopped,
        "limitations": [
            "The structured proxy is evidence-grounded but is not the official semantic STALE score.",
            "The model sees selected session text only; hidden M_old/M_new/explanation/reference indices are used after generation.",
            "Oracle relevant top-2 is a development upper bound and is not deployable.",
            "Zero retries preserve failures and can leave a run incomplete after a systemic HTTP error.",
        ],
    }
    write_json(output_dir / "STALE_MODEL_RESULTS_V1.json", results)
    receipt = {
        "schema": "stale_model_probe_receipt_v1",
        "status": "COMPLETE_WITH_STOP" if stopped else "COMPLETE",
        "results_path": str(output_dir / "STALE_MODEL_RESULTS_V1.json"),
        "results_sha256": sha256_file(output_dir / "STALE_MODEL_RESULTS_V1.json"),
        "data_sha256": results["data"]["sha256"],
        "model": args.model,
        "planned_generation_calls": results["selection"]["planned_generation_calls"],
        "executed_generation_attempts": results["summary"]["overall"]["accounting_attempts"],
        "physical_http_calls": results["summary"]["overall"]["physical_http_calls"],
        "accounting_tokens": results["summary"]["overall"]["accounting_tokens"],
        "retry_count": 0,
        "official_llm_judge_used": False,
        "stopped_early": stopped,
    }
    write_json(output_dir / "STALE_MODEL_RECEIPT_V1.json", receipt)
    (output_dir / "STALE_MODEL_COMPLETE_V1").write_text("COMPLETE\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
