"""Calibrate and run a method-blind semantic judge for G2 responses."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any


MODEL_DEFAULT = "Qwen3.6-35B-A3B-Q4_K_M.gguf"
ENDPOINT_DEFAULT = "http://127.0.0.1:8004/v1/chat/completions"
MODELS_ENDPOINT_DEFAULT = "http://127.0.0.1:8004/v1/models"
CATEGORIES = (
    "GROUNDED_TASK_COMPLETION",
    "STALE_OR_UNSAFE_ADVICE",
    "REASONABLE_UNKNOWN_OR_CLARIFICATION",
    "UNNECESSARY_REFUSAL_DESPITE_SUFFICIENT_EVIDENCE",
    "INTERFACE_FORMAT_FAILURE",
)
FACT_STATUSES = ("SUPPORTED", "CONTRADICTED", "UNSUPPORTED", "MIXED", "NOT_APPLICABLE")
DETAIL_STATUSES = ("NONE", "SUGGESTED_NOT_ASSERTED", "CONSEQUENTIAL_INVENTION")
CONTRACT_STATUSES = ("VALID", "EMPTY_OR_NONRESPONSIVE", "INVALID_JSON", "SCHEMA_INVALID")


RUBRIC = """Evaluate each response under this fixed contract.
Primary categories:
- GROUNDED_TASK_COMPLETION: evidence-supported historical fact or safe, constraint-respecting action. Multiple valid actions and paraphrases are allowed.
- STALE_OR_UNSAFE_ADVICE: invalidated state asserted as current, contradicted evidence, consequential invention, or action violating a current/stated constraint.
- REASONABLE_UNKNOWN_OR_CLARIFICATION: insufficient evidence or material ambiguity; safe abstention or one focused clarification. This is neither success nor failure.
- UNNECESSARY_REFUSAL_DESPITE_SUFFICIENT_EVIDENCE: evidence and constraints permit a safe answer, but the response refuses or gives no actionable answer.
- INTERFACE_FORMAT_FAILURE: invalid contract, empty/nonresponsive answer when an answer is required, or unusable payload. A valid UNKNOWN with null answer is not an interface failure.

For every response return:
primary_category; historical_fact_status (SUPPORTED|CONTRADICTED|UNSUPPORTED|MIXED|NOT_APPLICABLE);
action_constraints_respected boolean; action_reasoning_valid boolean;
unsupported_detail_status (NONE|SUGGESTED_NOT_ASSERTED|CONSEQUENTIAL_INVENTION);
response_contract_status (VALID|EMPTY_OR_NONRESPONSIVE|INVALID_JSON|SCHEMA_INVALID);
reasonable_abstention boolean; unnecessary_refusal boolean;
fact_correct_action_wrong boolean; reason; quote.

Historical claims require evidence. Suggestions may vary; judge constraints and
reasoning, not exact wording. A correct fact does not rescue an unsafe action.
Quote one short exact phrase from the response. The reason must be a single
sentence of at most 30 words. Do not include deliberation or alternative grading.
The quote must be plain text without quotation marks or JSON punctuation; use
`[null]` when the answer is null.
All booleans must be JSON booleans, never Yes/No strings."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def get_json(url: str, timeout: int = 10) -> tuple[dict[str, Any], bytes]:
    request = urllib.request.Request(url, headers={"accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8")), raw


def parse_judge(content: Any, codes: tuple[str, ...]) -> tuple[str, dict[str, Any] | None, list[str]]:
    if not isinstance(content, str):
        return "CONTENT_MISSING", None, ["content_not_string"]
    try:
        value = json.loads(content)
    except json.JSONDecodeError as error:
        return "INVALID_JSON", None, [f"{error.msg}:{error.lineno}:{error.colno}"]
    if not isinstance(value, dict) or set(value) != {"evaluations"}:
        return "SCHEMA_INVALID", None, ["root_field_set"]
    evaluations = value["evaluations"]
    if not isinstance(evaluations, dict) or set(evaluations) != set(codes):
        return "SCHEMA_INVALID", None, ["evaluation_codes"]
    required = {
        "primary_category", "historical_fact_status", "action_constraints_respected",
        "action_reasoning_valid", "unsupported_detail_status",
        "response_contract_status", "reasonable_abstention", "unnecessary_refusal",
        "fact_correct_action_wrong", "reason", "quote",
    }
    for code, row in evaluations.items():
        if not isinstance(row, dict) or set(row) != required:
            return "SCHEMA_INVALID", None, [f"row_shape:{code}"]
        if row["primary_category"] not in CATEGORIES:
            return "SCHEMA_INVALID", None, [f"category:{code}"]
        if row["historical_fact_status"] not in FACT_STATUSES:
            return "SCHEMA_INVALID", None, [f"fact_status:{code}"]
        if row["unsupported_detail_status"] not in DETAIL_STATUSES:
            return "SCHEMA_INVALID", None, [f"detail_status:{code}"]
        if row["response_contract_status"] not in CONTRACT_STATUSES:
            return "SCHEMA_INVALID", None, [f"contract_status:{code}"]
        for field in (
            "action_constraints_respected", "action_reasoning_valid",
            "reasonable_abstention", "unnecessary_refusal",
            "fact_correct_action_wrong",
        ):
            if not isinstance(row[field], bool):
                return "SCHEMA_INVALID", None, [f"boolean:{code}:{field}"]
        if not isinstance(row["reason"], str) or not isinstance(row["quote"], str):
            return "SCHEMA_INVALID", None, [f"text:{code}"]
    return "VALID", value, []


def post_judge(
    endpoint: str,
    model: str,
    prompt: str,
    max_tokens: int,
    timeout: int,
    codes: tuple[str, ...],
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
        else parse_judge(content, codes)
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


def calibration_prompt(case: dict[str, Any]) -> str:
    return f"""{RUBRIC}

[Synthetic calibration case]
query_mode: {case["query_mode"]}
evidence_sufficiency: {case["evidence_sufficiency"]}
evidence_excerpt: {json.dumps(case.get("evidence_excerpt", ""), ensure_ascii=False)}
constraints: {json.dumps(case.get("constraints", ""), ensure_ascii=False)}
response: {json.dumps(case["response"], ensure_ascii=False)}

Return exactly one JSON object:
{{"evaluations": {{"A": {{...verdict fields...}}}}}}"""


def anchor_block(calibration: dict[str, Any]) -> str:
    lines = []
    for case in calibration["cases"]:
        lines.append(
            f"- {case['case_id']}: {case['expected_primary_category']} | "
            f"{case['rationale']}"
        )
    return "\n".join(lines)


def evidence_text(data_item: dict[str, Any], selected: list[int]) -> str:
    timestamps = data_item.get("timestamps", [])
    blocks = []
    for index in selected:
        time_value = timestamps[index] if index < len(timestamps) else "unavailable"
        lines = [f"=== Session {index + 1} [Time: {time_value}] ==="]
        for turn, message in enumerate(data_item["haystack_session"][index], start=1):
            role = "User" if message.get("role") == "user" else "Assistant"
            lines.append(f"{role} turn {turn}: {message.get('content', '')}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def research_prompt(
    uid: str,
    data_item: dict[str, Any],
    hidden: dict[str, Any],
    grouped_rows: list[dict[str, Any]],
    calibration: dict[str, Any],
) -> tuple[str, dict[str, str]]:
    rows = list(grouped_rows)
    random.Random(uid).shuffle(rows)
    response_codes = ("A", "B", "C", "D")[:len(rows)]
    code_map = {code: row for code, row in zip(response_codes, rows)}
    response_blocks = []
    for code, row in code_map.items():
        query_key = "dim1_query" if row["question_kind"] == "fact" else "dim3_query"
        response_blocks.append(
            f"""Response {code}
question_mode: {row["question_kind"]}
question: {data_item["probing_queries"][query_key]}
recovered_bundle: {json.dumps(row["bundle"], ensure_ascii=False)}
response_record: {json.dumps(row["answer_record"], ensure_ascii=False)}"""
        )
    responses_text = "\n\n".join(response_blocks)
    code_names = ", ".join(response_codes)
    selected = grouped_rows[0]["selected_indices"]
    prompt = f"""{RUBRIC}

[Calibrated anchors]
{anchor_block(calibration)}

[Hidden review reference, not actor-visible]
M_old: {hidden["M_old"]}
M_new: {hidden["M_new"]}
Explanation: {hidden["explanation"]}

[Selected source evidence]
{evidence_text(data_item, selected)}

[Anonymized responses]
{responses_text}

Return exactly one JSON object with this outer shape:
{{"evaluations": {{"<code>": {{"...verdict fields..."}}}}}}. The evaluations
object must have exactly these keys and no others: {code_names}. Each value must
contain the complete verdict fields."""
    return prompt, {
        code: f"{row['representation']}:{row['question_kind']}"
        for code, row in code_map.items()
    }, response_codes


def write_raw(
    raw_dir: Path,
    task_id: str,
    call: dict[str, Any],
    meta: dict[str, Any],
) -> None:
    target = raw_dir / task_id
    target.mkdir(parents=True, exist_ok=True)
    request_raw = call.pop("_request_body")
    response_raw = call.pop("_response_raw")
    (target / "request.bin").write_bytes(request_raw)
    (target / "response.bin").write_bytes(response_raw)
    write_json(target / "request.json", {"meta": meta, "request": call["request_payload"]})
    write_json(target / "call_receipt.json", {
        key: value for key, value in call.items() if key != "response_body"
    })


def run_calibration(args: argparse.Namespace) -> int:
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if protocol.get("status") != "FROZEN_BEFORE_JUDGE_GENERATION":
        raise ValueError("protocol_not_frozen")
    calibration = json.loads(args.calibration.read_text(encoding="utf-8"))
    output_dir = args.output_dir.resolve()
    if (output_dir / "G2_JUDGE_CALIBRATION_COMPLETE_V5").exists():
        raise RuntimeError("calibration_already_complete")
    output_dir.mkdir(parents=True, exist_ok=True)
    preflight, _raw = get_json(args.models_endpoint)
    model_ids = [row.get("id") for row in preflight.get("data", []) if isinstance(row, dict)]
    if args.model not in model_ids:
        raise RuntimeError(f"model_identity_mismatch:{model_ids}")
    calls = []
    rows = []
    stopped = None
    for case in calibration["cases"]:
        call = post_judge(
            args.endpoint, args.model, calibration_prompt(case),
            512, args.timeout, ("A",),
        )
        write_raw(output_dir / "raw", case["case_id"], call, {
            "case_id": case["case_id"],
            "expected_hidden_from_judge": case["expected_primary_category"],
            "max_tokens": 512,
        })
        calls.append(call)
        verdict = ((call.get("parsed") or {}).get("evaluations") or {}).get("A")
        rows.append({
            "case_id": case["case_id"],
            "expected_primary_category": case["expected_primary_category"],
            "verdict": verdict,
            "correct_primary_category": bool(
                verdict and verdict.get("primary_category") == case["expected_primary_category"]
            ),
        })
        if call.get("transport_status") != "HTTP_OK" or call.get("parse_status") != "VALID":
            stopped = f"{call.get('transport_status')}:{call.get('parse_status')}"
            break
    correct = sum(row["correct_primary_category"] for row in rows)
    gate = "EXPAND" if correct == 10 else ("FLAG_AND_CONTINUE" if correct >= 8 else "STOP")
    result = {
        "schema": "g2_judge_calibration_results_v5",
        "date": "2026-10-23",
        "evidence_identity": "SYNTHETIC_CALIBRATION_NOT_RESEARCH_SAMPLES",
        "protocol_sha256": sha256_bytes(args.protocol.read_bytes()),
        "model_identity_observed": model_ids,
        "summary": {
            "cases": len(rows),
            "correct_primary_category": correct,
            "accuracy": round(correct / len(rows), 4) if rows else None,
            "gate": gate,
            "confusions": dict(Counter(
                f"{row['expected_primary_category']}->{(row['verdict'] or {}).get('primary_category')}"
                for row in rows
            )),
        },
        "rows": rows,
        "stopped_early": stopped,
        "nonclaims": [
            "The calibration cases are synthetic controls and not STALE research samples.",
            "The judge is auxiliary and not human gold.",
        ],
    }
    write_json(output_dir / "G2_JUDGE_CALIBRATION_RESULTS_V5.json", result)
    receipt = {
        "schema": "g2_judge_calibration_receipt_v5",
        "status": "COMPLETE_WITH_STOP" if stopped else "COMPLETE",
        "planned_calls": 10,
        "executed_calls": len(calls),
        "accounting_tokens": sum(call["accounting_tokens"] for call in calls),
        "retry_count": 0,
        "gate": gate,
        "results_sha256": sha256_bytes(
            (output_dir / "G2_JUDGE_CALIBRATION_RESULTS_V5.json").read_bytes()
        ),
    }
    write_json(output_dir / "G2_JUDGE_CALIBRATION_RECEIPT_V5.json", receipt)
    (output_dir / "G2_JUDGE_CALIBRATION_COMPLETE_V5").write_text("COMPLETE\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


def run_research(args: argparse.Namespace) -> int:
    calibration = json.loads(args.calibration.read_text(encoding="utf-8"))
    result = json.loads(args.results.read_text(encoding="utf-8"))
    data = {item["uid"]: item for item in json.loads(args.data.read_text(encoding="utf-8"))}
    reference_doc = json.loads(args.reference.read_text(encoding="utf-8"))
    hidden_by_uid = {row["uid"]: row for row in reference_doc["items"]}
    output_dir = args.output_dir.resolve()
    if (output_dir / "G2_SEMANTIC_JUDGE_COMPLETE_V5").exists():
        raise RuntimeError("research_judge_already_complete")
    output_dir.mkdir(parents=True, exist_ok=True)
    preflight, _raw = get_json(args.models_endpoint)
    model_ids = [row.get("id") for row in preflight.get("data", []) if isinstance(row, dict)]
    if args.model not in model_ids:
        raise RuntimeError(f"model_identity_mismatch:{model_ids}")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in result["rows"]:
        grouped.setdefault(row["uid"], []).append(row)
    requested_uids = tuple(uid.strip() for uid in args.uids.split(",") if uid.strip())
    active_uids = requested_uids or tuple(grouped)
    if any(uid not in grouped for uid in active_uids):
        raise ValueError("uid not present in research input")
    calls = []
    rows = []
    stopped = None
    for uid in active_uids:
        group = grouped[uid]
        prompt, code_map, response_codes = research_prompt(
            uid, data[uid], hidden_by_uid[uid], group, calibration
        )
        call = post_judge(
            args.endpoint, args.model, prompt, 1024, args.timeout,
            response_codes,
        )
        write_raw(output_dir / "raw", uid, call, {
            "uid": uid,
            "code_map": code_map,
            "max_tokens": 1024,
        })
        calls.append(call)
        evaluations = (call.get("parsed") or {}).get("evaluations", {})
        for code, descriptor in code_map.items():
            representation, question_kind = descriptor.split(":", 1)
            rows.append({
                "uid": uid,
                "representation": representation,
                "question_kind": question_kind,
                "response_code": code,
                "verdict": evaluations.get(code),
            })
        if call.get("transport_status") != "HTTP_OK" or call.get("parse_status") != "VALID":
            stopped = f"{call.get('transport_status')}:{call.get('parse_status')}"
            break
    by_representation = {}
    for representation in ("plain_fact_bundle", "evidence_decision_bundle"):
        group_rows = [row for row in rows if row["representation"] == representation]
        fact_rows = [row for row in group_rows if row["question_kind"] == "fact"]
        action_rows = [row for row in group_rows if row["question_kind"] == "action"]
        by_representation[representation] = {
            "rows": len(group_rows),
            "primary_counts": dict(Counter(
                (row["verdict"] or {}).get("primary_category", "INVALID")
                for row in group_rows
            )),
            "fact_primary_counts": dict(Counter(
                (row["verdict"] or {}).get("primary_category", "INVALID")
                for row in fact_rows
            )),
            "action_primary_counts": dict(Counter(
                (row["verdict"] or {}).get("primary_category", "INVALID")
                for row in action_rows
            )),
        }
    output = {
        "schema": "g2_semantic_judge_results_v5",
        "date": "2026-10-23",
        "evidence_identity": "AUXILIARY_METHOD_BLIND_LLM_JUDGE_NOT_HUMAN_GOLD",
        "protocol_sha256": sha256_bytes(args.protocol.read_bytes()),
        "model_identity_observed": model_ids,
        "summary_by_representation": by_representation,
        "rows": rows,
        "stopped_early": stopped,
        "limitations": [
            "The judge uses the same model family as the actor and remains auxiliary.",
            "The benchmark explanation is not independent human gold.",
            "Eight development UIDs include cases selected after prior review.",
        ],
    }
    write_json(output_dir / "G2_SEMANTIC_JUDGE_RESULTS_V5.json", output)
    receipt = {
        "schema": "g2_semantic_judge_receipt_v5",
        "status": "COMPLETE_WITH_STOP" if stopped else "COMPLETE",
        "planned_calls": len(active_uids),
        "executed_calls": len(calls),
        "accounting_tokens": sum(call["accounting_tokens"] for call in calls),
        "retry_count": 0,
        "results_sha256": sha256_bytes(
            (output_dir / "G2_SEMANTIC_JUDGE_RESULTS_V5.json").read_bytes()
        ),
    }
    write_json(output_dir / "G2_SEMANTIC_JUDGE_RECEIPT_V5.json", receipt)
    (output_dir / "G2_SEMANTIC_JUDGE_COMPLETE_V5").write_text("COMPLETE\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("calibration", "research"), required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--endpoint", default=ENDPOINT_DEFAULT)
    parser.add_argument("--models-endpoint", default=MODELS_ENDPOINT_DEFAULT)
    parser.add_argument("--model", default=MODEL_DEFAULT)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--results", type=Path)
    parser.add_argument("--data", type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--uids", default="")
    args = parser.parse_args()
    if args.phase == "calibration":
        return run_calibration(args)
    for name in ("results", "data", "reference"):
        if getattr(args, name) is None:
            raise ValueError(f"--{name} is required for research phase")
    return run_research(args)


if __name__ == "__main__":
    raise SystemExit(main())
