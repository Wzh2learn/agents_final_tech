"""Run a bounded new-UID paired confirmation for STALE state-card extraction."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from stale_model_probe import (
    ENDPOINT_DEFAULT,
    FORBIDDEN_ACTOR_LITERALS,
    MAX_TOKENS_DEFAULT,
    MODEL_DEFAULT,
    MODELS_ENDPOINT_DEFAULT,
    build_actor_prompt,
    get_json,
    hidden_reference,
    post_model,
    select_instances,
    session_text,
    sha256_bytes,
    sha256_file,
    write_json,
)
from stale_model_oracle_diagnostic import answer_polarity
from stale_model_two_stage_probe import (
    VISIBILITY as TWO_STAGE_VISIBILITY,
    build_stage1_prompt,
    build_stage2_prompt,
    call_stage,
    parse_state_card_content,
)


EVIDENCE_IDENTITY = "BOUNDED_NEW_UID_CONFIRMATION_WITHIN_PUBLIC_STALE"
QUERY_FIELD = "dim1_query"
CURRENT_UIDS = {
    "01f694b2-c555-4b6e-8ca0-5f11210e2227",
    "04fea765-0b32-4e8f-b4e9-225901f627b0",
    "009b7c99-b777-465a-bc3a-77f2d88c1318",
    "012f090e-6e02-4751-955d-574745069df3",
}


def select_new_uid_confirmation(
    data: list[dict[str, Any]],
    excluded_uids: set[str],
    per_type: int = 4,
) -> list[dict[str, Any]]:
    """Select the next UID-sorted T1/T2 cases after the frozen exclusions."""
    by_type: dict[str, list[dict[str, Any]]] = {"T1": [], "T2": []}
    for item in data:
        kind = str(item.get("type", "")).upper()
        uid = str(item.get("uid", ""))
        if kind in by_type and uid not in excluded_uids:
            by_type[kind].append(item)
    if any(len(rows) < per_type for rows in by_type.values()):
        raise ValueError("dataset lacks the requested new UID confirmation subset")
    for rows in by_type.values():
        rows.sort(key=lambda item: str(item["uid"]))
    return by_type["T1"][:per_type] + by_type["T2"][:per_type]


def pair_success(
    parsed: dict[str, Any] | None, polarity: str
) -> bool:
    """Apply the frozen paired success criterion."""
    return bool(
        isinstance(parsed, dict)
        and parsed.get("state_resolution") == "STALE_DETECTED"
        and polarity == "NEGATIVE_OLD_STATE"
    )


def write_call_raw(
    raw_dir: Path,
    uid: str,
    call_id: str,
    meta: dict[str, Any],
    call: dict[str, Any],
    request_raw: bytes,
    response_raw: bytes,
) -> None:
    """Preserve one exact model request/response and its receipt."""
    call_dir = raw_dir / uid / call_id
    call_dir.mkdir(parents=True, exist_ok=True)
    write_json(call_dir / "request.json", {"meta": meta, "request": call["request_payload"]})
    (call_dir / "request.bin").write_bytes(request_raw)
    (call_dir / "response.bin").write_bytes(response_raw)
    write_json(call_dir / "call_receipt.json", {
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
    """Run A one-shot then B extraction/answer for each UID sequentially."""
    rows: list[dict[str, Any]] = []
    raw_dir.mkdir(parents=True, exist_ok=True)
    stopped = False
    generation_call = 0
    for item in selected:
        uid = str(item["uid"])
        query = str(item["probing_queries"][QUERY_FIELD])
        sessions = item["haystack_session"]
        relevant = sorted(int(index) for index in item["relevant_session_index"])
        selected_indices = relevant[:2]
        selected_evidence = [sessions[index] for index in selected_indices]
        row: dict[str, Any] = {
            "uid": uid,
            "type": item["type"],
            "query": query,
            "hidden_reference": hidden_reference(item, selected_indices, selected_evidence),
            "selected_session_indices_hidden_from_actor": selected_indices,
        }

        one_shot_prompt = build_actor_prompt(query, selected_evidence)
        generation_call += 1
        one_shot = post_model(endpoint, model, one_shot_prompt, max_tokens, timeout)
        request_raw = one_shot.pop("_request_body")
        response_raw = one_shot.pop("_response_raw")
        write_call_raw(
            raw_dir,
            uid,
            "A_one_shot",
            {
                "generation_call": generation_call,
                "uid": uid,
                "type": item["type"],
                "arm": "A_one_shot",
                "selected_session_indices_hidden_from_actor": selected_indices,
                "visibility": "ORACLE_RAW_SESSIONS_NO_HIDDEN_METADATA",
                "retry_count": 0,
            },
            one_shot,
            request_raw,
            response_raw,
        )
        one_parsed = one_shot.get("parsed")
        one_polarity = answer_polarity(
            one_parsed.get("answer") if isinstance(one_parsed, dict) else None
        )
        row.update({
            "one_shot": one_shot,
            "one_shot_answer_polarity": one_polarity,
            "one_shot_success": pair_success(one_parsed, one_polarity),
            "one_shot_context_chars": len(one_shot_prompt),
        })
        if one_shot["transport_status"] != "HTTP_OK":
            rows.append(row)
            stopped = True
            break

        stage1_prompt = build_stage1_prompt(query, selected_evidence)
        generation_call += 1
        stage1, request1, response1 = call_stage(
            endpoint, model, stage1_prompt, max_tokens, timeout, "stage1"
        )
        write_call_raw(
            raw_dir,
            uid,
            "B_stage1_state_card",
            {
                "generation_call": generation_call,
                "uid": uid,
                "type": item["type"],
                "arm": "B_two_stage",
                "stage": "stage1",
                "selected_session_indices_hidden_from_actor": selected_indices,
                "visibility": TWO_STAGE_VISIBILITY,
                "retry_count": 0,
            },
            stage1,
            request1,
            response1,
        )
        state_card = stage1.get("parsed")
        state_card_text = (
            json.dumps(state_card, ensure_ascii=False)
            if isinstance(state_card, dict)
            else str(stage1.get("content", ""))
        )
        stage1_leaks = [
            literal for literal in FORBIDDEN_ACTOR_LITERALS
            if literal in json.dumps({"state_card": state_card_text}, ensure_ascii=False)
        ]
        row.update({
            "stage1": stage1,
            "state_card": state_card,
            "state_card_text": state_card_text,
            "state_card_leak_detected": stage1_leaks,
            "stage1_context_chars": len(stage1_prompt),
        })
        if stage1["transport_status"] != "HTTP_OK":
            row.update({
                "stage2": None,
                "two_stage_answer_polarity": "NOT_RUN",
                "two_stage_success": False,
                "two_stage_context_chars": 0,
            })
            rows.append(row)
            stopped = True
            break

        stage2_prompt = build_stage2_prompt(query, state_card_text)
        generation_call += 1
        stage2, request2, response2 = call_stage(
            endpoint, model, stage2_prompt, max_tokens, timeout, "stage2"
        )
        write_call_raw(
            raw_dir,
            uid,
            "B_stage2_answer",
            {
                "generation_call": generation_call,
                "uid": uid,
                "type": item["type"],
                "arm": "B_two_stage",
                "stage": "stage2",
                "visibility": TWO_STAGE_VISIBILITY,
                "retry_count": 0,
            },
            stage2,
            request2,
            response2,
        )
        stage2_parsed = stage2.get("parsed")
        stage2_polarity = answer_polarity(
            stage2_parsed.get("answer") if isinstance(stage2_parsed, dict) else None
        )
        row.update({
            "stage2": stage2,
            "two_stage_answer_polarity": stage2_polarity,
            "two_stage_success": pair_success(stage2_parsed, stage2_polarity),
            "two_stage_context_chars": len(stage2_prompt),
        })
        rows.append(row)
        if stage2["transport_status"] != "HTTP_OK":
            stopped = True
            break
    return rows, stopped


def paired_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize paired success and cost overall and by conflict type."""
    def summarize_group(group: list[dict[str, Any]]) -> dict[str, Any]:
        count = len(group)
        one = sum(bool(row.get("one_shot_success")) for row in group)
        two = sum(bool(row.get("two_stage_success")) for row in group)
        return {
            "uids": count,
            "one_shot_success": one,
            "one_shot_rate": one / count if count else None,
            "two_stage_success": two,
            "two_stage_rate": two / count if count else None,
            "paired_difference_two_minus_one": (two - one) / count if count else None,
            "both_success": sum(
                bool(row.get("one_shot_success")) and bool(row.get("two_stage_success"))
                for row in group
            ),
            "one_only": sum(
                bool(row.get("one_shot_success")) and not bool(row.get("two_stage_success"))
                for row in group
            ),
            "two_only": sum(
                not bool(row.get("one_shot_success")) and bool(row.get("two_stage_success"))
                for row in group
            ),
            "neither_success": sum(
                not bool(row.get("one_shot_success")) and not bool(row.get("two_stage_success"))
                for row in group
            ),
        }

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["type"])].append(row)
    calls = [
        row[key]
        for row in rows
        for key in ("one_shot", "stage1", "stage2")
        if row.get(key) is not None
    ]
    return {
        "overall": summarize_group(rows),
        "by_type": {kind: summarize_group(group) for kind, group in sorted(grouped.items())},
        "unknown_and_format": {
            "one_shot_parse_failure": sum(
                row.get("one_shot", {}).get("parse_status") != "VALID" for row in rows
            ),
            "one_shot_decision_unknown": sum(
                ((row.get("one_shot") or {}).get("parsed") or {}).get("decision") == "UNKNOWN"
                for row in rows
            ),
            "one_shot_state_unknown": sum(
                ((row.get("one_shot") or {}).get("parsed") or {}).get("state_resolution")
                == "UNKNOWN"
                for row in rows
            ),
            "stage1_parse_failure": sum(
                row.get("stage1", {}).get("parse_status") != "VALID" for row in rows
            ),
            "stage2_parse_failure": sum(
                row.get("stage2", {}).get("parse_status") != "VALID" for row in rows
            ),
            "stage2_decision_unknown": sum(
                ((row.get("stage2") or {}).get("parsed") or {}).get("decision") == "UNKNOWN"
                for row in rows
            ),
            "stage2_state_unknown": sum(
                ((row.get("stage2") or {}).get("parsed") or {}).get("state_resolution")
                == "UNKNOWN"
                for row in rows
            ),
            "state_card_output_leaks": sum(
                bool(row.get("state_card_leak_detected")) for row in rows
            ),
        },
        "cost": {
            "planned_generation_calls": 24,
            "observed_generation_calls": len(calls),
            "physical_http_calls": sum(int(call["physical_http_calls"]) for call in calls),
            "http_ok": sum(call["transport_status"] == "HTTP_OK" for call in calls),
            "accounting_attempts": sum(int(call["accounting_attempts"]) for call in calls),
            "accounting_tokens": sum(int(call["accounting_tokens"]) for call in calls),
            "one_shot_tokens": sum(
                int((row.get("one_shot") or {}).get("accounting_tokens", 0)) for row in rows
            ),
            "stage1_tokens": sum(
                int((row.get("stage1") or {}).get("accounting_tokens", 0)) for row in rows
            ),
            "stage2_tokens": sum(
                int((row.get("stage2") or {}).get("accounting_tokens", 0)) for row in rows
            ),
            "one_shot_context_chars": sum(int(row.get("one_shot_context_chars", 0)) for row in rows),
            "stage1_context_chars": sum(int(row.get("stage1_context_chars", 0)) for row in rows),
            "stage2_context_chars": sum(int(row.get("two_stage_context_chars", 0)) for row in rows),
            "latency_seconds_sum": round(
                sum(float(call["latency_seconds"]) for call in calls), 6
            ),
        },
    }


def main() -> int:
    """Run the bounded new-UID paired confirmation."""
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
    if (output_dir / "STALE_MODEL_NEW_UID_CONFIRMATION_COMPLETE_V1").exists():
        raise RuntimeError("stale_model_new_uid_confirmation_already_complete")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    selected = select_new_uid_confirmation(data, CURRENT_UIDS, per_type=4)
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
        output_dir / "stale_model_new_uid_confirmation_raw",
    )
    results = {
        "schema": "stale_model_new_uid_confirmation_v1",
        "date": "2026-10-23",
        "evidence_identity": EVIDENCE_IDENTITY,
        "not_independent_external_confirmation": True,
        "frozen_selection": {
            "sort": "uid_ascending",
            "excluded_uids": sorted(CURRENT_UIDS),
            "per_type": 4,
            "selected": [{"uid": item["uid"], "type": item["type"]} for item in selected],
            "query_field": QUERY_FIELD,
            "evidence": "oracle relevant top-2 raw sessions",
        },
        "frozen_comparison": {
            "A_one_shot": "existing five-field raw-session prompt",
            "B_two_stage": "existing state-card extraction and state-card answer prompts",
            "primary_pair_success": (
                "state_resolution == STALE_DETECTED and "
                "answer_polarity == NEGATIVE_OLD_STATE"
            ),
            "temperature": 0,
            "max_tokens": args.max_tokens,
            "retry_cap": 0,
            "concurrency": 1,
        },
        "actor_visibility": {
            "forbidden": list(FORBIDDEN_ACTOR_LITERALS),
            "oracle_relevant_selection_is_post_input": True,
            "hidden_reference_use": "post-hoc scoring only",
        },
        "data": {
            "path": str(args.data),
            "sha256": sha256_file(args.data),
            "bytes": args.data.stat().st_size,
            "total_items": len(data),
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
        "official_llm_judge": {"used": False, "role": "AUXILIARY_ONLY_NOT_RUN"},
        "summary": paired_summary(rows),
        "rows": rows,
        "stopped_early": stopped,
        "limitations": [
            "This is bounded confirmation within public STALE, not independent external confirmation.",
            "Oracle relevant raw sessions are fixed; retrieval quality is not evaluated.",
            "State cards are model output and are not semantic gold.",
            "Answer polarity is a lexical proxy, not the official STALE judge.",
        ],
    }
    write_json(output_dir / "STALE_MODEL_NEW_UID_CONFIRMATION_RESULTS_V1.json", results)
    receipt = {
        "schema": "stale_model_new_uid_confirmation_receipt_v1",
        "status": "COMPLETE_WITH_STOP" if stopped else "COMPLETE",
        "evidence_identity": EVIDENCE_IDENTITY,
        "results_path": str(output_dir / "STALE_MODEL_NEW_UID_CONFIRMATION_RESULTS_V1.json"),
        "results_sha256": sha256_file(
            output_dir / "STALE_MODEL_NEW_UID_CONFIRMATION_RESULTS_V1.json"
        ),
        "planned_generation_calls": 24,
        "executed_generation_attempts": results["summary"]["cost"]["observed_generation_calls"],
        "physical_http_calls": results["summary"]["cost"]["physical_http_calls"],
        "accounting_tokens": results["summary"]["cost"]["accounting_tokens"],
        "retry_count": 0,
        "official_llm_judge_used": False,
        "stopped_early": stopped,
    }
    write_json(output_dir / "STALE_MODEL_NEW_UID_CONFIRMATION_RECEIPT_V1.json", receipt)
    (output_dir / "STALE_MODEL_NEW_UID_CONFIRMATION_COMPLETE_V1").write_text(
        "COMPLETE\n", encoding="utf-8"
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
