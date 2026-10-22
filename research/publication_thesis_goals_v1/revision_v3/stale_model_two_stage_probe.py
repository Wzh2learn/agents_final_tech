"""Run a deployable two-stage state-card mechanism probe on four STALE cases."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from stale_model_probe import (
    ENDPOINT_DEFAULT,
    FORBIDDEN_ACTOR_LITERALS,
    MAX_TOKENS_DEFAULT,
    MODEL_DEFAULT,
    MODELS_ENDPOINT_DEFAULT,
    get_json,
    hidden_reference,
    parse_model_content,
    post_model,
    select_instances,
    session_text,
    sha256_bytes,
    sha256_file,
    write_json,
)


QUERY_FIELD = "dim1_query"
STATE_CARD_FIELDS = {"old_state", "new_state", "change_type"}
CHANGE_TYPES = {"CO_REFERENTIAL", "PROPAGATED", "UNKNOWN"}
EVIDENCE_IDENTITY = "DEV_ONLY_TWO_STAGE_MECHANISM_PROBE"
VISIBILITY = "DEV_ONLY_TWO_STAGE_MECHANISM_PROBE_ORACLE_RETRIEVAL"


def build_stage1_prompt(
    query: str, sessions: list[list[dict[str, Any]]]
) -> str:
    """Build the raw-session state-card extraction prompt."""
    evidence = "\n\n".join(
        f"<evidence_session_{position:02d}>\n{session_text(session)}\n</evidence_session_{position:02d}>"
        for position, session in enumerate(sessions, start=1)
    )
    prompt = f"""Extract a compact state card from the selected raw sessions.
Use only the selected sessions and the query. Do not infer hidden metadata or
add facts outside the evidence.

Selected evidence sessions:
{evidence}

User question:
{query}

Return only one JSON object with exactly these three fields:
{{
  "old_state": "the earlier relevant state supported by the sessions",
  "new_state": "the later relevant state supported by the sessions",
  "change_type": "CO_REFERENTIAL | PROPAGATED | UNKNOWN"
}}

Requirements:
- old_state and new_state must be non-empty strings.
- Use CO_REFERENTIAL when the same attribute changes directly.
- Use PROPAGATED when one observed change indirectly invalidates a related state.
- Use UNKNOWN when the relationship cannot be established from the sessions.
- Do not add fields, code fences, or prose outside the JSON object."""
    serialized = json.dumps({"prompt": prompt}, ensure_ascii=False)
    found = [literal for literal in FORBIDDEN_ACTOR_LITERALS if literal in serialized]
    if found:
        raise ValueError(f"stage1_prompt_forbidden_literal:{','.join(found)}")
    return prompt


def build_stage2_prompt(query: str, state_card_text: str) -> str:
    """Build the state-card-only answer prompt."""
    prompt = f"""Answer the user question using only the state card below.
Do not assume facts beyond the state card. If it is insufficient, return UNKNOWN.

State card:
{state_card_text}

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

Use STALE_DETECTED when new_state invalidates the queried old_state. If decision
is not ANSWER, answer must be null. If decision is ANSWER, answer must be a
non-empty string. Do not add fields, code fences, or prose outside the JSON object."""
    return prompt


def validate_state_card(value: Any) -> tuple[bool, list[str]]:
    """Strictly validate the three-field state card."""
    if not isinstance(value, dict):
        return False, ["root_not_object"]
    errors = []
    if set(value) != STATE_CARD_FIELDS:
        errors.append(f"field_set:{sorted(value)}")
    for field in ("old_state", "new_state"):
        if not isinstance(value.get(field), str) or not str(value.get(field)).strip():
            errors.append(f"{field}_must_be_nonempty_string")
    if value.get("change_type") not in CHANGE_TYPES:
        errors.append(f"change_type:{value.get('change_type')}")
    return not errors, errors


def parse_state_card_content(content: Any) -> dict[str, Any]:
    """Parse one state-card response strictly with no extraction or retry."""
    if not isinstance(content, str):
        return {"parse_status": "CONTENT_MISSING", "parse_errors": ["content_not_string"]}
    try:
        value = json.loads(content)
    except json.JSONDecodeError as error:
        return {
            "parse_status": "INVALID_JSON",
            "parse_errors": [f"{error.msg} at line {error.lineno} column {error.colno}"],
        }
    valid, errors = validate_state_card(value)
    return {
        "parse_status": "VALID" if valid else "SCHEMA_INVALID",
        "parse_errors": errors,
        "parsed": value if valid else None,
    }


def answer_polarity(answer: Any) -> str:
    """Return a conservative lexical answer-polarity proxy."""
    if not isinstance(answer, str) or not answer.strip():
        return "NO_ANSWER"
    first = answer.strip().lower()
    if re.match(r"^(no|no longer|not|isn't|is not|doesn't|does not|cannot|can't)\b", first):
        return "NEGATIVE_OLD_STATE"
    if re.match(r"^(yes|still|indeed|correct)\b", first):
        return "POSITIVE_OLD_STATE"
    return "OTHER"


def call_stage(
    endpoint: str,
    model: str,
    prompt: str,
    max_tokens: int,
    timeout: int,
    stage: str,
) -> tuple[dict[str, Any], bytes, bytes]:
    """Call one stage and return the call receipt plus exact request/response bytes."""
    call = post_model(endpoint, model, prompt, max_tokens, timeout)
    request_raw = call.pop("_request_body")
    response_raw = call.pop("_response_raw")
    if stage == "stage1":
        parsed = parse_state_card_content(call.get("content"))
        call["parse_status"] = parsed["parse_status"]
        call["parse_errors"] = parsed["parse_errors"]
        call["parsed"] = parsed["parsed"]
    return call, request_raw, response_raw


def write_stage_raw(
    raw_dir: Path,
    pair: int,
    stage: str,
    meta: dict[str, Any],
    call: dict[str, Any],
    request_raw: bytes,
    response_raw: bytes,
) -> None:
    """Preserve exact raw evidence and a serializable call receipt."""
    stage_dir = raw_dir / f"pair_{pair:03d}" / stage
    stage_dir.mkdir(parents=True, exist_ok=True)
    write_json(stage_dir / "request.json", {"meta": meta, "request": call["request_payload"]})
    (stage_dir / "request.bin").write_bytes(request_raw)
    (stage_dir / "response.bin").write_bytes(response_raw)
    write_json(stage_dir / "call_receipt.json", {
        key: value for key, value in call.items() if key not in {"request_payload", "response_body"}
    })


def run_pairs(
    selected: list[dict[str, Any]],
    endpoint: str,
    model: str,
    max_tokens: int,
    timeout: int,
    raw_dir: Path,
) -> tuple[list[dict[str, Any]], bool]:
    """Run four extraction/answer pairs sequentially with zero retries."""
    rows: list[dict[str, Any]] = []
    raw_dir.mkdir(parents=True, exist_ok=True)
    stopped = False
    generation_call = 0
    for pair, item in enumerate(selected, start=1):
        query = str(item["probing_queries"][QUERY_FIELD])
        sessions = item["haystack_session"]
        relevant = sorted(int(index) for index in item["relevant_session_index"])
        selected_indices = relevant[:2]
        selected_evidence = [sessions[index] for index in selected_indices]
        stage1_prompt = build_stage1_prompt(query, selected_evidence)
        generation_call += 1
        stage1, request1, response1 = call_stage(
            endpoint, model, stage1_prompt, max_tokens, timeout, "stage1"
        )
        write_stage_raw(
            raw_dir,
            pair,
            "stage1",
            {
                "pair": pair,
                "generation_call": generation_call,
                "uid": item["uid"],
                "type": item["type"],
                "stage": "stage1",
                "selected_session_indices_hidden_from_actor": selected_indices,
                "visibility": VISIBILITY,
                "retry_count": 0,
            },
            stage1,
            request1,
            response1,
        )
        if stage1["transport_status"] != "HTTP_OK":
            rows.append({
                "pair": pair,
                "uid": item["uid"],
                "type": item["type"],
                "query": query,
                "hidden_reference": hidden_reference(item, selected_indices, selected_evidence),
                "stage1": stage1,
                "stage2": None,
                "state_card_text": None,
                "state_card": None,
                "state_card_parse_status": "NOT_RUN",
                "state_card_leak_detected": None,
                "answer_polarity": "NOT_RUN",
                "pair_metric": "NOT_RUN",
            })
            stopped = True
            break
        state_card = stage1.get("parsed")
        state_card_text = (
            json.dumps(state_card, ensure_ascii=False)
            if isinstance(state_card, dict)
            else str(stage1.get("content", ""))
        )
        leak_literals = [
            literal for literal in FORBIDDEN_ACTOR_LITERALS
            if literal in json.dumps({"state_card": state_card_text}, ensure_ascii=False)
        ]
        stage2_prompt = build_stage2_prompt(query, state_card_text)
        generation_call += 1
        stage2, request2, response2 = call_stage(
            endpoint, model, stage2_prompt, max_tokens, timeout, "stage2"
        )
        write_stage_raw(
            raw_dir,
            pair,
            "stage2",
            {
                "pair": pair,
                "generation_call": generation_call,
                "uid": item["uid"],
                "type": item["type"],
                "stage": "stage2",
                "visibility": VISIBILITY,
                "retry_count": 0,
            },
            stage2,
            request2,
            response2,
        )
        answer = (stage2.get("parsed") or {}).get("answer")
        state_resolution = (stage2.get("parsed") or {}).get("state_resolution")
        polarity = answer_polarity(answer)
        pair_metric = (
            "MATCH"
            if polarity == "NEGATIVE_OLD_STATE" and state_resolution == "STALE_DETECTED"
            else "PARTIAL"
            if polarity == "NEGATIVE_OLD_STATE" or state_resolution == "STALE_DETECTED"
            else "NO_MATCH"
            if stage2.get("parsed") is not None
            else "PARSE_FAILURE"
        )
        rows.append({
            "pair": pair,
            "uid": item["uid"],
            "type": item["type"],
            "query": query,
            "hidden_reference": hidden_reference(item, selected_indices, selected_evidence),
            "stage1": stage1,
            "stage2": stage2,
            "state_card_text": state_card_text,
            "state_card": state_card,
            "state_card_parse_status": stage1["parse_status"],
            "state_card_leak_detected": leak_literals,
            "answer_polarity": polarity,
            "pair_metric": pair_metric,
        })
        if stage2["transport_status"] != "HTTP_OK":
            stopped = True
            break
    return rows, stopped


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize the two-stage calls and four paired outcomes."""
    calls = [
        row[stage]
        for row in rows
        for stage in ("stage1", "stage2")
        if row.get(stage) is not None
    ]
    pairs = [row for row in rows if row.get("stage2") is not None]
    by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for stage in ("stage1", "stage2"):
            if row.get(stage) is not None:
                by_stage[stage].append(row[stage])
    return {
        "overall": {
            "planned_generation_calls": 8,
            "observed_generation_calls": len(calls),
            "physical_http_calls": sum(int(call["physical_http_calls"]) for call in calls),
            "http_ok": sum(call["transport_status"] == "HTTP_OK" for call in calls),
            "accounting_attempts": sum(int(call["accounting_attempts"]) for call in calls),
            "accounting_tokens": sum(int(call["accounting_tokens"]) for call in calls),
            "latency_seconds_sum": round(sum(float(call["latency_seconds"]) for call in calls), 6),
            "retry_count": 0,
        },
        "by_stage": {
            stage: {
                "planned": 4,
                "observed": len(group),
                "valid_json": sum(call["parse_status"] == "VALID" for call in group),
                "parse_status_counts": dict(Counter(call["parse_status"] for call in group)),
                "accounting_tokens": sum(int(call["accounting_tokens"]) for call in group),
                "latency_seconds_sum": round(
                    sum(float(call["latency_seconds"]) for call in group), 6
                ),
            }
            for stage, group in sorted(by_stage.items())
        },
        "pairs": {
            "planned": 4,
            "observed": len(pairs),
            "state_card_parse_status_counts": dict(Counter(
                row["state_card_parse_status"] for row in rows
            )),
            "state_card_change_type_counts": dict(Counter(
                (row.get("state_card") or {}).get("change_type", "INVALID_OR_MISSING")
                for row in rows
            )),
            "state_card_output_leak_count": sum(bool(row["state_card_leak_detected"]) for row in rows),
            "answer_polarity_counts": dict(Counter(row["answer_polarity"] for row in rows)),
            "pair_metric_counts": dict(Counter(row["pair_metric"] for row in rows)),
            "stale_detected_rate": (
                sum(
                    ((row.get("stage2") or {}).get("parsed") or {}).get("state_resolution")
                    == "STALE_DETECTED"
                    for row in pairs
                ) / len(pairs) if pairs else None
            ),
            "negative_old_state_rate": (
                sum(row["answer_polarity"] == "NEGATIVE_OLD_STATE" for row in pairs)
                / len(pairs) if pairs else None
            ),
        },
    }


def main() -> int:
    """Run the bounded two-stage probe and preserve each stage's raw evidence."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--endpoint", default=ENDPOINT_DEFAULT)
    parser.add_argument("--models-endpoint", default=MODELS_ENDPOINT_DEFAULT)
    parser.add_argument("--model", default=MODEL_DEFAULT)
    parser.add_argument("--max-tokens", type=int, default=MAX_TOKENS_DEFAULT)
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if (output_dir / "STALE_MODEL_TWO_STAGE_COMPLETE_V1").exists():
        raise RuntimeError("stale_model_two_stage_probe_already_complete")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    selected = select_instances(data, total=4)
    preflight, preflight_raw = get_json(args.models_endpoint)
    model_rows = preflight.get("data", []) if isinstance(preflight, dict) else []
    model_ids = [row.get("id") for row in model_rows if isinstance(row, dict)]
    if args.model not in model_ids:
        raise RuntimeError(f"model_identity_mismatch:{model_ids}")
    rows, stopped = run_pairs(
        selected,
        args.endpoint,
        args.model,
        args.max_tokens,
        args.timeout,
        output_dir / "stale_model_two_stage_raw",
    )
    results = {
        "schema": "stale_model_two_stage_probe_v1",
        "date": "2026-10-23",
        "evidence_identity": EVIDENCE_IDENTITY,
        "visibility": VISIBILITY,
        "scientific_question": (
            "Can a deployable two-stage raw-session-to-state-card representation "
            "recover stale-state detection without hidden benchmark fields?"
        ),
        "stage_contract": {
            "stage1": {
                "input": "oracle relevant raw sessions plus dim1 query",
                "forbidden_input": list(FORBIDDEN_ACTOR_LITERALS),
                "output": ["old_state", "new_state", "change_type"],
            },
            "stage2": {
                "input": "stage1 state-card output plus dim1 query only",
                "output": [
                    "decision",
                    "state_resolution",
                    "premise_resistance",
                    "action_adaptation",
                    "answer",
                ],
            },
            "failure_policy": "preserve stage1 output as-is; no retry or repair",
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
            "query_field": QUERY_FIELD,
            "evidence": "oracle relevant top-2 raw sessions",
            "planned_pairs": 4,
            "planned_generation_calls": 8,
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
        "comparison_context": {
            "one_shot_oracle_raw_sessions": {
                "stale_detected": "1/4",
                "source": "../stale_model_run_20261023_v1/STALE_MODEL_RESULTS_V1.json",
            },
            "hidden_state_values_only": {
                "stale_detected": "4/4",
                "negative_old_state": "4/4",
                "source": "../stale_model_oracle_diag_20261023_v1/STALE_MODEL_ORACLE_DIAGNOSTIC_RESULTS_V1.json",
                "identity": "ORACLE_DIAGNOSTIC_NOT_DEPLOYABLE",
            },
            "two_stage": "computed from this probe",
        },
        "model_identity_observed": model_ids,
        "preflight_http_calls": 1,
        "preflight_response_sha256": sha256_bytes(preflight_raw),
        "official_llm_judge": {
            "used": False,
            "role": "AUXILIARY_ONLY_NOT_RUN",
        },
        "summary": summarize(rows),
        "rows": rows,
        "stopped_early": stopped,
        "limitations": [
            "The state-card text is a model output, not semantic gold.",
            "Oracle relevant raw sessions are provided, so this does not test retrieval.",
            "Four development cases cannot estimate benchmark accuracy.",
            "The answer polarity is a lexical proxy, not the official STALE judge.",
        ],
    }
    write_json(output_dir / "STALE_MODEL_TWO_STAGE_RESULTS_V1.json", results)
    receipt = {
        "schema": "stale_model_two_stage_receipt_v1",
        "status": "COMPLETE_WITH_STOP" if stopped else "COMPLETE",
        "evidence_identity": EVIDENCE_IDENTITY,
        "results_path": str(output_dir / "STALE_MODEL_TWO_STAGE_RESULTS_V1.json"),
        "results_sha256": sha256_file(output_dir / "STALE_MODEL_TWO_STAGE_RESULTS_V1.json"),
        "planned_generation_calls": 8,
        "executed_generation_attempts": results["summary"]["overall"]["observed_generation_calls"],
        "physical_http_calls": results["summary"]["overall"]["physical_http_calls"],
        "accounting_tokens": results["summary"]["overall"]["accounting_tokens"],
        "retry_count": 0,
        "official_llm_judge_used": False,
        "stopped_early": stopped,
    }
    write_json(output_dir / "STALE_MODEL_TWO_STAGE_RECEIPT_V1.json", receipt)
    (output_dir / "STALE_MODEL_TWO_STAGE_COMPLETE_V1").write_text(
        "COMPLETE\n", encoding="utf-8"
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
