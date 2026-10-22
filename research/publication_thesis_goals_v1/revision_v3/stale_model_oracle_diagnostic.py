"""Run an oracle-only STALE diagnostic for explicit state values versus explanations."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from stale_model_probe import (
    ARMS,
    ENDPOINT_DEFAULT,
    MAX_TOKENS_DEFAULT,
    MODEL_DEFAULT,
    MODELS_ENDPOINT_DEFAULT,
    OUTPUT_FIELDS,
    get_json,
    hidden_reference,
    post_model,
    select_instances,
    session_text,
    sha256_bytes,
    sha256_file,
    write_json,
)


QUERY_FIELD = "dim1_query"
ARMS_DIAGNOSTIC = ("state_values_only", "state_values_plus_explanation")
FORBIDDEN_ACTOR_LITERALS = ("relevant_session_index",)


def build_diagnostic_prompt(
    query: str,
    sessions: list[list[dict[str, Any]]],
    old_state: str,
    new_state: str,
    explanation: str | None,
) -> str:
    """Build an explicitly oracle-only development prompt."""
    evidence = "\n\n".join(
        f"<evidence_session_{position:02d}>\n{session_text(session)}\n</evidence_session_{position:02d}>"
        for position, session in enumerate(sessions, start=1)
    )
    explanation_block = (
        f"\nDevelopment-only explanation:\n{explanation}\n"
        if explanation is not None
        else ""
    )
    prompt = f"""ORACLE_DIAGNOSTIC_NOT_DEPLOYABLE
This is a development-only diagnostic. The actor is intentionally given hidden
state values to distinguish explicit state visibility from causal explanation.
This input must never be used as a deployable task condition or main-arm result.

Selected evidence sessions:
{evidence}

Hidden development state values:
M_old: {old_state}
M_new: {new_state}
{explanation_block}
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

Use STALE_DETECTED when M_new invalidates the state queried from M_old. If
decision is not ANSWER, answer must be null. Do not add fields, code fences, or
prose outside the JSON object."""
    serialized = json.dumps({"prompt": prompt}, ensure_ascii=False)
    found = [literal for literal in FORBIDDEN_ACTOR_LITERALS if literal in serialized]
    if found:
        raise ValueError(f"actor_prompt_forbidden_literal:{','.join(found)}")
    return prompt


def answer_polarity(answer: Any) -> str:
    """Return a conservative lexical polarity proxy for the answer text."""
    if not isinstance(answer, str) or not answer.strip():
        return "NO_ANSWER"
    first = answer.strip().lower()
    if re.match(r"^(no|no longer|not|isn't|is not|doesn't|does not|cannot|can't)\b", first):
        return "NEGATIVE_OLD_STATE"
    if re.match(r"^(yes|still|indeed|correct)\b", first):
        return "POSITIVE_OLD_STATE"
    return "OTHER"


def run_rows(
    selected: list[dict[str, Any]],
    endpoint: str,
    model: str,
    max_tokens: int,
    timeout: int,
    raw_dir: Path,
) -> tuple[list[dict[str, Any]], bool]:
    """Run the eight diagnostic requests sequentially with zero retries."""
    rows: list[dict[str, Any]] = []
    raw_dir.mkdir(parents=True, exist_ok=True)
    stopped = False
    attempt = 0
    for item in selected:
        query = str(item["probing_queries"][QUERY_FIELD])
        sessions = item["haystack_session"]
        relevant = sorted(int(index) for index in item["relevant_session_index"])
        selected_indices = relevant[:2]
        selected_evidence = [sessions[index] for index in selected_indices]
        for arm in ARMS_DIAGNOSTIC:
            attempt += 1
            prompt = build_diagnostic_prompt(
                query,
                selected_evidence,
                str(item["M_old"]),
                str(item["M_new"]),
                str(item["explanation"]) if arm.endswith("explanation") else None,
            )
            call = post_model(endpoint, model, prompt, max_tokens, timeout)
            request_raw = call.pop("_request_body")
            response_raw = call.pop("_response_raw")
            parsed = call.get("parsed")
            row = {
                "attempt": attempt,
                "uid": item["uid"],
                "type": item["type"],
                "dimension": "dim1",
                "arm": arm,
                "query": query,
                "context_chars": len(prompt),
                "hidden_reference": hidden_reference(item, selected_indices, selected_evidence),
                "call": call,
                "answer_polarity": answer_polarity(
                    parsed.get("answer") if isinstance(parsed, dict) else None
                ),
            }
            attempt_dir = raw_dir / f"attempt_{attempt:03d}"
            attempt_dir.mkdir(parents=True, exist_ok=True)
            write_json(attempt_dir / "request.json", {
                "meta": {
                    "attempt": attempt,
                    "uid": item["uid"],
                    "type": item["type"],
                    "dimension": "dim1",
                    "arm": arm,
                    "selected_session_indices_hidden_from_actor": selected_indices,
                    "retry_count": 0,
                    "diagnostic_visibility": "ORACLE_DIAGNOSTIC_NOT_DEPLOYABLE",
                },
                "request": call["request_payload"],
            })
            (attempt_dir / "request.bin").write_bytes(request_raw)
            (attempt_dir / "response.bin").write_bytes(response_raw)
            write_json(attempt_dir / "call_receipt.json", {
                key: value for key, value in call.items() if key not in {"request_payload", "response_body"}
            })
            rows.append(row)
            if call["transport_status"] != "HTTP_OK":
                stopped = True
                break
        if stopped:
            break
    return rows, stopped


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize the two oracle diagnostic arms."""
    result: dict[str, Any] = {
        "overall": {
            "planned": 8,
            "observed": len(rows),
            "physical_http_calls": sum(int(row["call"]["physical_http_calls"]) for row in rows),
            "http_ok": sum(row["call"]["transport_status"] == "HTTP_OK" for row in rows),
            "valid_json": sum(row["call"]["parse_status"] == "VALID" for row in rows),
            "accounting_attempts": sum(int(row["call"]["accounting_attempts"]) for row in rows),
            "accounting_tokens": sum(int(row["call"]["accounting_tokens"]) for row in rows),
            "latency_seconds_sum": round(sum(float(row["call"]["latency_seconds"]) for row in rows), 6),
            "state_resolution_counts": dict(Counter(
                row["call"].get("parsed", {}).get("state_resolution", "PARSE_FAILURE")
                if row["call"].get("parsed") is not None else "PARSE_FAILURE"
                for row in rows
            )),
            "answer_polarity_counts": dict(Counter(row["answer_polarity"] for row in rows)),
        },
        "by_arm": {},
    }
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["arm"])].append(row)
    for arm in ARMS_DIAGNOSTIC:
        group = grouped.get(arm, [])
        result["by_arm"][arm] = {
            "planned": 4,
            "observed": len(group),
            "state_resolution_counts": dict(Counter(
                row["call"].get("parsed", {}).get("state_resolution", "PARSE_FAILURE")
                if row["call"].get("parsed") is not None else "PARSE_FAILURE"
                for row in group
            )),
            "stale_detected_rate": (
                sum(
                    (row["call"].get("parsed") or {}).get("state_resolution") == "STALE_DETECTED"
                    for row in group
                ) / len(group) if group else None
            ),
            "answer_polarity_counts": dict(Counter(row["answer_polarity"] for row in group)),
            "negative_old_state_rate": (
                sum(row["answer_polarity"] == "NEGATIVE_OLD_STATE" for row in group) / len(group)
                if group else None
            ),
            "accounting_tokens": sum(int(row["call"]["accounting_tokens"]) for row in group),
            "latency_seconds_sum": round(sum(float(row["call"]["latency_seconds"]) for row in group), 6),
            "mean_context_chars": (
                sum(int(row["context_chars"]) for row in group) / len(group) if group else 0.0
            ),
        }
    return result


def load_rows_from_raw(
    selected: list[dict[str, Any]], raw_dir: Path
) -> list[dict[str, Any]]:
    """Reconstruct result rows from preserved raw calls without network access."""
    item_by_uid = {str(item["uid"]): item for item in selected}
    rows: list[dict[str, Any]] = []
    attempt_dirs = sorted(raw_dir.glob("attempt_*"))
    if len(attempt_dirs) != 8:
        raise RuntimeError(f"raw_attempt_count_mismatch:{len(attempt_dirs)}")
    for expected_attempt, attempt_dir in enumerate(attempt_dirs, start=1):
        request_record = json.loads((attempt_dir / "request.json").read_text(encoding="utf-8"))
        call = json.loads((attempt_dir / "call_receipt.json").read_text(encoding="utf-8"))
        meta = request_record["meta"]
        if int(meta["attempt"]) != expected_attempt:
            raise RuntimeError(f"raw_attempt_order_mismatch:{attempt_dir}")
        item = item_by_uid[str(meta["uid"])]
        request_body = json.loads((attempt_dir / "request.bin").read_text(encoding="utf-8"))
        observed_model = request_body.get("model")
        prompt = request_body["messages"][0]["content"]
        selected_indices = [int(index) for index in meta["selected_session_indices_hidden_from_actor"]]
        selected_evidence = [item["haystack_session"][index] for index in selected_indices]
        parsed = call.get("parsed")
        rows.append({
            "attempt": expected_attempt,
            "uid": item["uid"],
            "type": item["type"],
            "dimension": "dim1",
            "arm": meta["arm"],
            "query": str(item["probing_queries"][QUERY_FIELD]),
            "context_chars": len(prompt),
            "hidden_reference": hidden_reference(item, selected_indices, selected_evidence),
            "call": call,
            "answer_polarity": answer_polarity(
                parsed.get("answer") if isinstance(parsed, dict) else None
            ),
            "recovery_observed_model": observed_model,
        })
    return rows


def main() -> int:
    """Run the bounded oracle diagnostic and preserve all evidence."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--endpoint", default=ENDPOINT_DEFAULT)
    parser.add_argument("--models-endpoint", default=MODELS_ENDPOINT_DEFAULT)
    parser.add_argument("--model", default=MODEL_DEFAULT)
    parser.add_argument("--max-tokens", type=int, default=MAX_TOKENS_DEFAULT)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--recover-existing", action="store_true")
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if (output_dir / "STALE_MODEL_ORACLE_DIAGNOSTIC_COMPLETE_V1").exists():
        raise RuntimeError("stale_model_oracle_diagnostic_already_complete")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    selected = select_instances(data, total=4)
    raw_dir = output_dir / "stale_model_oracle_diagnostic_raw"
    recovered = False
    recovery_reason = None
    model_ids: list[Any] = []
    preflight_response_sha256 = None
    if args.recover_existing:
        rows = load_rows_from_raw(selected, raw_dir)
        stopped = any(row["call"]["transport_status"] != "HTTP_OK" for row in rows)
        recovered = True
        recovery_reason = (
            "Result assembly raised NameError after all eight preserved calls; "
            "recovery reads raw evidence and performs zero generation requests."
        )
        recovered_models = sorted({
            str(row.get("recovery_observed_model")) for row in rows
        })
        if recovered_models != [args.model]:
            raise RuntimeError(f"raw_model_identity_mismatch:{recovered_models}")
        model_ids = recovered_models
        for row in rows:
            row.pop("recovery_observed_model", None)
    else:
        preflight, preflight_raw = get_json(args.models_endpoint)
        preflight_response_sha256 = sha256_bytes(preflight_raw)
        model_rows = preflight.get("data", []) if isinstance(preflight, dict) else []
        model_ids = [row.get("id") for row in model_rows if isinstance(row, dict)]
        if args.model not in model_ids:
            raise RuntimeError(f"model_identity_mismatch:{model_ids}")
        rows, stopped = run_rows(
            selected,
            args.endpoint,
            args.model,
            args.max_tokens,
            args.timeout,
            raw_dir,
        )
    results = {
        "schema": "stale_model_oracle_diagnostic_v1",
        "date": "2026-10-23",
        "evidence_identity": "ORACLE_DIAGNOSTIC_NOT_DEPLOYABLE",
        "purpose": (
            "Distinguish whether explicit M_old/M_new state values are sufficient "
            "for stale-state detection, or whether the explanation of causal "
            "propagation changes the answer."
        ),
        "main_arm_exclusion": (
            "These calls intentionally expose hidden development fields and are "
            "not part of the deployable/main STALE arms."
        ),
        "data": {
            "path": str(args.data),
            "sha256": sha256_file(args.data),
            "bytes": args.data.stat().st_size,
            "total_items": len(data),
        },
        "selection": {
            "item_count": len(selected),
            "uids": [{"uid": item["uid"], "type": item["type"]} for item in selected],
            "arms": list(ARMS_DIAGNOSTIC),
            "query_field": QUERY_FIELD,
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
        "model_identity_observed": model_ids,
        "preflight_http_calls": 0 if recovered else 1,
        "preflight_response_sha256": preflight_response_sha256,
        "recovered_from_existing_raw": recovered,
        "generation_calls_reexecuted": False if recovered else None,
        "recovery_reason": recovery_reason,
        "official_llm_judge": {
            "used": False,
            "role": "AUXILIARY_ONLY_NOT_RUN",
        },
        "summary": summarize(rows),
        "rows": rows,
        "stopped_early": stopped,
        "limitations": [
            "This is an oracle diagnostic and cannot be compared as a deployable arm.",
            "The answer polarity is a lexical proxy, not an official STALE judge.",
            "The four instances are development observations, not an accuracy estimate.",
        ],
    }
    write_json(output_dir / "STALE_MODEL_ORACLE_DIAGNOSTIC_RESULTS_V1.json", results)
    receipt = {
        "schema": "stale_model_oracle_diagnostic_receipt_v1",
        "status": "COMPLETE_WITH_STOP" if stopped else "COMPLETE",
        "evidence_identity": "ORACLE_DIAGNOSTIC_NOT_DEPLOYABLE",
        "results_path": str(output_dir / "STALE_MODEL_ORACLE_DIAGNOSTIC_RESULTS_V1.json"),
        "results_sha256": sha256_file(output_dir / "STALE_MODEL_ORACLE_DIAGNOSTIC_RESULTS_V1.json"),
        "planned_generation_calls": 8,
        "executed_generation_attempts": len(rows),
        "physical_http_calls": sum(int(row["call"]["physical_http_calls"]) for row in rows),
        "accounting_tokens": sum(int(row["call"]["accounting_tokens"]) for row in rows),
        "retry_count": 0,
        "official_llm_judge_used": False,
        "stopped_early": stopped,
        "recovered_from_existing_raw": recovered,
        "generation_calls_reexecuted": False if recovered else None,
        "recovery_reason": recovery_reason,
    }
    write_json(output_dir / "STALE_MODEL_ORACLE_DIAGNOSTIC_RECEIPT_V1.json", receipt)
    (output_dir / "STALE_MODEL_ORACLE_DIAGNOSTIC_COMPLETE_V1").write_text(
        "COMPLETE\n", encoding="utf-8"
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
