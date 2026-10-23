"""Run a method-blind auxiliary action-alignment judge for STALE dim3."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

from state_processing_comparison_v2 import (
    MODEL_DEFAULT,
    ENDPOINT_DEFAULT,
    MODELS_ENDPOINT_DEFAULT,
    format_sessions,
    get_json,
    post_model,
    sha256_bytes,
    write_call_raw,
    write_json,
)


ACTION_PROMPT = (
    "You are an independent evaluator of downstream actions under changed user state. "
    "Use only the hidden state transition, visible source evidence, question, and "
    "anonymized responses. Ignore method names and self-labels.\n"
    "For each response evaluate:\n"
    "- action_state_aligned: the concrete action/plan follows the new-state consequence.\n"
    "- stale_action_rejected: it does not continue the action basis implied by the old state.\n"
    "- evidence_consistent: details are supported by evidence or cautious inference.\n"
    "- non_generic: the action is specific enough to guide the requested task.\n"
    "- safe_unknown: it uses UNKNOWN/qualification when evidence is insufficient.\n"
    "- pass: true only if action_state_aligned, stale_action_rejected, evidence_consistent, "
    "and non_generic are true.\n"
    "- error_type: CORRECT_ACTION, STALE_ACTION, GENERIC_ACTION, UNSUPPORTED_ACTION, "
    "INVENTED_DETAIL, RETRIEVAL_MISS_SAFE_UNKNOWN, or AMBIGUOUS_QUALIFIED.\n"
    "All boolean fields must be JSON booleans, never Yes/No strings. Return exactly one "
    "JSON object with exactly this outer shape: "
    '{"evaluations": {"A": {...}, "B": {...}}}. The evaluations keys must be exactly '
    "the supplied A/B codes."
)
ERROR_TYPES = {
    "CORRECT_ACTION",
    "STALE_ACTION",
    "GENERIC_ACTION",
    "UNSUPPORTED_ACTION",
    "INVENTED_DETAIL",
    "RETRIEVAL_MISS_SAFE_UNKNOWN",
    "AMBIGUOUS_QUALIFIED",
}


def parse_action_judge(
    content: Any,
    expected_codes: tuple[str, ...] = ("A", "B"),
) -> tuple[str, dict[str, Any] | None, list[str]]:
    if not isinstance(content, str):
        return "CONTENT_MISSING", None, ["content_not_string"]
    try:
        value = json.loads(content)
    except json.JSONDecodeError as error:
        return "INVALID_JSON", None, [f"{error.msg} at line {error.lineno} column {error.colno}"]
    if not isinstance(value, dict) or set(value) != {"evaluations"}:
        return "SCHEMA_INVALID", None, ["root_field_set"]
    evaluations = value["evaluations"]
    if not isinstance(evaluations, dict) or set(evaluations) != set(expected_codes):
        return "SCHEMA_INVALID", None, ["evaluation_field_set"]
    required = {
        "action_state_aligned", "stale_action_rejected", "evidence_consistent",
        "non_generic", "safe_unknown", "pass", "error_type",
    }
    for code, row in evaluations.items():
        if not isinstance(row, dict) or set(row) != required:
            return "SCHEMA_INVALID", None, [f"evaluation_shape:{code}"]
        for field in required - {"error_type"}:
            if not isinstance(row[field], bool):
                return "SCHEMA_INVALID", None, [f"field_not_boolean:{code}:{field}"]
        if row["error_type"] is not None and row["error_type"] not in ERROR_TYPES:
            return "SCHEMA_INVALID", None, [f"error_type:{code}"]
        if row["pass"] and not all(row[field] for field in (
            "action_state_aligned", "stale_action_rejected",
            "evidence_consistent", "non_generic",
        )):
            return "SCHEMA_INVALID", None, [f"pass_inconsistent:{code}"]
    return "VALID", value, []


def build_prompt(
    reference: dict[str, Any],
    question: str,
    evidence: str,
    responses: dict[str, str],
) -> str:
    response_text = "\n\n".join(
        f"Response {code}:\n{text or '[no answer]'}"
        for code, text in sorted(responses.items())
    )
    return f"""{ACTION_PROMPT}

[Hidden reference]
M_old: {reference["M_old"]}
M_new: {reference["M_new"]}
Hidden logic: {reference["explanation"]}

[Visible evidence]
{evidence}

[Action request]
{question}

[Responses]
{response_text}"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--combined", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--endpoint", default=ENDPOINT_DEFAULT)
    parser.add_argument("--models-endpoint", default=MODELS_ENDPOINT_DEFAULT)
    parser.add_argument("--model", default=MODEL_DEFAULT)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    if (output_dir / "STALE_ACTION_JUDGE_COMPLETE_V3").exists():
        raise RuntimeError("action_judge_already_complete")
    output_dir.mkdir(parents=True, exist_ok=True)
    combined = json.loads(args.combined.read_text(encoding="utf-8"))
    data = {item["uid"]: item for item in json.loads(args.data.read_text(encoding="utf-8"))}
    reference_doc = json.loads(args.reference.read_text(encoding="utf-8"))
    references = {row["uid"]: row for row in reference_doc["items"]}
    rows_by_uid: dict[str, dict[str, dict[str, Any]]] = {}
    for row in combined["rows"]:
        rows_by_uid.setdefault(row["uid"], {})[row["arm"]] = row
    prompt_hash = hashlib.sha256(ACTION_PROMPT.encode("utf-8")).hexdigest()
    protocol = {
        "schema": "stale_action_judge_protocol_v3",
        "date": "2026-10-23",
        "status": "FROZEN_BEFORE_JUDGE_GENERATION",
        "identity": "AUXILIARY_METHOD_BLIND_LLM_JUDGE_NOT_HUMAN_GOLD",
        "prompt_sha256": prompt_hash,
        "response_codes": ["A", "B"],
    }
    write_json(args.protocol, protocol)
    preflight, _raw = get_json(args.models_endpoint)
    model_ids = [row.get("id") for row in preflight.get("data", []) if isinstance(row, dict)]
    if args.model not in model_ids:
        raise RuntimeError(f"model_identity_mismatch:{model_ids}")
    calls = []
    rows = []
    stopped = None
    raw_dir = output_dir / "raw"
    for uid in reference_doc["selection"]["selected_uids"]:
        source = rows_by_uid[uid]
        arms = list(source)
        random.Random(uid + "action").shuffle(arms)
        code_to_arm = {code: arm for code, arm in zip(("A", "B"), arms)}
        responses = {
            code: source[arm].get("answer") or ""
            for code, arm in code_to_arm.items()
        }
        selected = source[arms[0]]["selected_indices"]
        question = data[uid]["probing_queries"]["dim3_query"]
        call = post_model(
            args.endpoint,
            args.model,
            build_prompt(
                references[uid], question, format_sessions(data[uid], selected), responses
            ),
            args.max_tokens,
            args.timeout,
            {"evaluations"},
        )
        call["arm"] = "action_judge"
        write_call_raw(raw_dir, uid, "judge", call, {
            "uid": uid,
            "code_to_arm": code_to_arm,
            "prompt_sha256": prompt_hash,
            "max_tokens": args.max_tokens,
        })
        if call.get("parse_status") == "VALID":
            status, parsed, errors = parse_action_judge(
                json.dumps(call.get("parsed") or {}, ensure_ascii=False)
            )
            call["parse_status"] = status
            call["parsed"] = parsed
            call["parse_errors"] = errors
        calls.append(call)
        evaluations = (call.get("parsed") or {}).get("evaluations", {})
        for code, arm in code_to_arm.items():
            rows.append({
                "uid": uid,
                "type": data[uid]["type"],
                "arm": arm,
                "response_code": code,
                "answer": source[arm].get("answer"),
                "retrieval_category": source[arm]["retrieval_category"],
                "judge": evaluations.get(code),
            })
        if call.get("transport_status") != "HTTP_OK":
            stopped = f"transport_failure:{call.get('http_status')}"
            break
        if call.get("parse_status") != "VALID":
            stopped = f"parse_failure:{call.get('parse_status')}"
            break
    by_arm = {}
    for arm in sorted({row["arm"] for row in rows}):
        group = [row for row in rows if row["arm"] == arm]
        valid = [row for row in group if isinstance(row["judge"], dict)]
        primary = [
            row for row in valid if row["retrieval_category"] == "BOTH_OLD_AND_NEW"
        ]
        valid_pass = sum(row["judge"].get("pass") is True for row in valid)
        by_arm[arm] = {
            "rows": len(group),
            "valid_judgments": len(valid),
            "invalid_judgments": len(group) - len(valid),
            "action_pass": valid_pass,
            "action_pass_rate": round(valid_pass / len(valid), 4) if valid else None,
            "primary_rows": len(primary),
            "action_pass_primary": sum(row["judge"].get("pass") is True for row in primary),
            "action_pass_rate_primary": (
                round(
                    sum(row["judge"].get("pass") is True for row in primary) / len(primary),
                    4,
                )
                if primary else None
            ),
            "safe_unknown": sum(row["judge"].get("safe_unknown") is True for row in valid),
            "error_counts": dict(Counter(row["judge"].get("error_type") for row in valid)),
        }
    result = {
        "schema": "stale_action_judge_results_v3",
        "date": "2026-10-23",
        "evidence_identity": "AUXILIARY_METHOD_BLIND_ACTION_JUDGE_NOT_HUMAN_GOLD",
        "protocol_sha256": sha256_bytes(args.protocol.read_bytes()),
        "summary_by_arm": by_arm,
        "rows": rows,
        "stopped_early": stopped,
        "limitations": [
            "The judge uses the same local model family as the actor and is auxiliary only.",
            "Hidden benchmark explanations are not human gold.",
            "Only dim3 is evaluated in this action probe.",
        ],
    }
    write_json(output_dir / "STALE_ACTION_JUDGE_RESULTS_V3.json", result)
    receipt = {
        "schema": "stale_action_judge_receipt_v3",
        "status": "COMPLETE_WITH_STOP" if stopped else "COMPLETE",
        "model": args.model,
        "planned_calls": 16,
        "executed_calls": len(calls),
        "accounting_tokens": sum(call["accounting_tokens"] for call in calls),
        "retry_count": 0,
        "results_sha256": sha256_bytes(
            (output_dir / "STALE_ACTION_JUDGE_RESULTS_V3.json").read_bytes()
        ),
        "stopped_early": stopped,
    }
    write_json(output_dir / "STALE_ACTION_JUDGE_RECEIPT_V3.json", receipt)
    (output_dir / "STALE_ACTION_JUDGE_COMPLETE_V3").write_text(
        "COMPLETE\n", encoding="utf-8"
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
