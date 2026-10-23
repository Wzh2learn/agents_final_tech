"""Run a method-blind auxiliary semantic judge on frozen confirmation answers."""

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


JUDGE_PROMPT = (
    "You are an independent semantic evaluator for long-term state updates. "
    "You will see hidden benchmark reference states, source evidence, a question, "
    "and one or more anonymized responses. Ignore any apparent method or label. Evaluate "
    "each response only against the hidden state transition and visible source evidence.\n\n"
    "For each response return:\n"
    "- current_fact_supported: it states a specific current fact consistent with the "
    "new state or grounded propagated consequence; bare Yes/No is false.\n"
    "- old_state_rejected: it avoids asserting the old state as current.\n"
    "- evidence_consistent: factual details are present in evidence or valid cautious "
    "inferences; penalize invented events and unsupported specificity.\n"
    "- safe_unknown: UNKNOWN or qualification is used when evidence is insufficient "
    "or propagation is genuinely ambiguous.\n"
    "- pass: true only if current_fact_supported and old_state_rejected and "
    "evidence_consistent.\n"
    "- The five boolean fields must be JSON booleans true/false, never strings "
    "such as Yes/No. error_type is a string or null.\n"
    "- error_type: CORRECT_SPECIFIC, STALE_ACCEPT, UNSPECIFIED, "
    "UNSUPPORTED_CURRENT_FACT, INVENTED_DETAIL, RETRIEVAL_MISS_SAFE_UNKNOWN, or "
    "AMBIGUOUS_QUALIFIED.\n\n"
    "Return exactly one JSON object whose evaluations object contains exactly "
    "one entry for every supplied response code and no other keys. Keys must be "
    "exactly A, B, C, or D without a `Response` prefix."
)
ERROR_TYPES = {
    "CORRECT_SPECIFIC",
    "STALE_ACCEPT",
    "UNSPECIFIED",
    "UNSUPPORTED_CURRENT_FACT",
    "INVENTED_DETAIL",
    "RETRIEVAL_MISS_SAFE_UNKNOWN",
    "AMBIGUOUS_QUALIFIED",
}


def judge_prompt(
    reference: dict[str, Any],
    question: str,
    evidence: str,
    responses: dict[str, str],
) -> str:
    response_text = "\n\n".join(
        f"Response {code}:\n{text if text else '[no answer]'}"
        for code, text in sorted(responses.items())
    )
    return f"""{JUDGE_PROMPT}

[Hidden benchmark reference]
M_old: {reference["M_old"]}
M_new: {reference["M_new"]}
Hidden logic: {reference["explanation"]}

[Visible source evidence]
{evidence}

[Question]
{question}

[Anonymized responses]
{response_text}"""


def parse_judge(
    content: Any,
    expected_codes: tuple[str, ...] = ("A", "B", "C", "D"),
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
        "current_fact_supported", "old_state_rejected", "evidence_consistent",
        "safe_unknown", "pass", "error_type",
    }
    for code, row in evaluations.items():
        if not isinstance(row, dict) or set(row) != required:
            return "SCHEMA_INVALID", None, [f"evaluation_shape:{code}"]
        for field in (
            "current_fact_supported", "old_state_rejected",
            "evidence_consistent", "safe_unknown", "pass",
        ):
            if not isinstance(row[field], bool):
                return "SCHEMA_INVALID", None, [f"field_not_boolean:{code}:{field}"]
        error_type = row["error_type"]
        if error_type is not None and error_type not in ERROR_TYPES:
            return "SCHEMA_INVALID", None, [f"error_type:{code}:{error_type}"]
        if row["pass"] and not (
            row["current_fact_supported"]
            and row["old_state_rejected"]
            and row["evidence_consistent"]
        ):
            return "SCHEMA_INVALID", None, [f"pass_inconsistent:{code}"]
    return "VALID", value, []


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
    parser.add_argument("--uids", default="")
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    if (output_dir / "STALE_SEMANTIC_JUDGE_COMPLETE_V3").exists():
        raise RuntimeError("semantic_judge_already_complete")
    output_dir.mkdir(parents=True, exist_ok=True)
    combined = json.loads(args.combined.read_text(encoding="utf-8"))
    data = {item["uid"]: item for item in json.loads(args.data.read_text(encoding="utf-8"))}
    reference_doc = json.loads(args.reference.read_text(encoding="utf-8"))
    references = {row["uid"]: row for row in reference_doc["items"]}
    rows_by_uid: dict[str, dict[str, dict[str, Any]]] = {}
    for row in combined["rows"]:
        rows_by_uid.setdefault(row["uid"], {})[row["arm"]] = row
    prompt_hash = hashlib.sha256(JUDGE_PROMPT.encode("utf-8")).hexdigest()
    protocol = {
        "schema": "stale_semantic_judge_protocol_v3",
        "date": "2026-10-23",
        "status": "FROZEN_BEFORE_JUDGE_GENERATION",
        "judge_model": args.model,
        "prompt_sha256": prompt_hash,
        "input_contract": [
            "hidden M_old/M_new/explanation",
            "retrieved source sessions with role and time",
            "one question and four method-blind responses",
        ],
        "excluded_inputs": [
            "actor self-labels",
            "generated state cards",
            "method names",
            "automatic overlap scores",
        ],
        "identity": "AUXILIARY_LLM_JUDGE_NOT_HUMAN_GOLD",
        "response_count": "dynamic_2_to_4",
    }
    write_json(args.protocol, protocol)
    preflight, _preflight_raw = get_json(args.models_endpoint)
    model_ids = [row.get("id") for row in preflight.get("data", []) if isinstance(row, dict)]
    if args.model not in model_ids:
        raise RuntimeError(f"model_identity_mismatch:{model_ids}")
    rows = []
    calls = []
    raw_dir = output_dir / "raw"
    stopped = None
    requested_uids = tuple(uid.strip() for uid in args.uids.split(",") if uid.strip())
    active_uids = requested_uids or tuple(reference_doc["selection"]["selected_uids"])
    if any(uid not in references for uid in active_uids):
        raise ValueError("uid not present in frozen reference")
    for uid in active_uids:
        reference = references[uid]
        source = rows_by_uid[uid]
        arms = list(source)
        random.Random(uid).shuffle(arms)
        codes = ("A", "B", "C", "D")[:len(arms)]
        code_to_arm = {code: arm for code, arm in zip(codes, arms)}
        responses = {
            code: source[arm].get("answer") or ""
            for code, arm in code_to_arm.items()
        }
        selected = source[arms[0]]["selected_indices"]
        evidence = format_sessions(data[uid], selected)
        call = post_model(
            args.endpoint,
            args.model,
            judge_prompt(reference, reference["dim1_query"], evidence, responses),
            args.max_tokens,
            args.timeout,
            {"evaluations"},
        )
        call["arm"] = "semantic_judge"
        write_call_raw(raw_dir, uid, "judge", call, {
            "uid": uid,
            "code_to_arm": code_to_arm,
            "prompt_sha256": prompt_hash,
            "max_tokens": args.max_tokens,
        })
        if call.get("parse_status") == "VALID":
            strict_status, strict_parsed, strict_errors = parse_judge(
                json.dumps(call.get("parsed") or {}, ensure_ascii=False),
                codes,
            )
            call["parse_status"] = strict_status
            call["parsed"] = strict_parsed
            call["parse_errors"] = strict_errors
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
        primary = [row for row in group if row["retrieval_category"] == "BOTH_OLD_AND_NEW"]
        valid_group = [row for row in group if isinstance(row["judge"], dict)]
        valid_primary = [row for row in primary if isinstance(row["judge"], dict)]
        valid_pass = sum(row["judge"].get("pass") is True for row in valid_group)
        by_arm[arm] = {
            "rows": len(group),
            "valid_judgments": len(valid_group),
            "invalid_judgments": len(group) - len(valid_group),
            "judge_pass": valid_pass,
            "judge_pass_rate": round(
                valid_pass / len(valid_group), 4
            ) if valid_group else None,
            "primary_rows": len(primary),
            "valid_primary_judgments": len(valid_primary),
            "judge_pass_primary": sum(
                row["judge"].get("pass") is True for row in valid_primary
            ),
            "judge_pass_rate_primary": (
                round(
                    sum(row["judge"].get("pass") is True for row in valid_primary)
                    / len(valid_primary),
                    4,
                )
                if valid_primary else None
            ),
            "safe_unknown": sum(
                row["judge"].get("safe_unknown") is True for row in valid_group
            ),
            "error_counts": dict(Counter(
                row["judge"].get("error_type") for row in valid_group
            )),
        }
    result = {
        "schema": "stale_semantic_judge_results_v3",
        "date": "2026-10-23",
        "evidence_identity": "AUXILIARY_METHOD_BLIND_LLM_JUDGE_NOT_HUMAN_GOLD",
        "protocol_sha256": sha256_bytes(args.protocol.read_bytes()),
        "model_identity_observed": model_ids,
        "summary_by_arm": by_arm,
        "rows": rows,
        "stopped_early": stopped,
        "limitations": [
            "The judge uses the same local model family as the actor and is auxiliary only.",
            "Hidden benchmark explanations are not independent human gold.",
            "Method blindness prevents direct self-label leakage but does not remove model bias.",
        ],
    }
    write_json(output_dir / "STALE_SEMANTIC_JUDGE_RESULTS_V3.json", result)
    receipt = {
        "schema": "stale_semantic_judge_receipt_v3",
        "status": "COMPLETE_WITH_STOP" if stopped else "COMPLETE",
        "model": args.model,
        "planned_calls": len(active_uids),
        "executed_calls": len(calls),
        "accounting_tokens": sum(call["accounting_tokens"] for call in calls),
        "retry_count": 0,
        "results_sha256": sha256_bytes(
            (output_dir / "STALE_SEMANTIC_JUDGE_RESULTS_V3.json").read_bytes()
        ),
        "stopped_early": stopped,
    }
    write_json(output_dir / "STALE_SEMANTIC_JUDGE_RECEIPT_V3.json", receipt)
    (output_dir / "STALE_SEMANTIC_JUDGE_COMPLETE_V3").write_text(
        "COMPLETE\n", encoding="utf-8"
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
