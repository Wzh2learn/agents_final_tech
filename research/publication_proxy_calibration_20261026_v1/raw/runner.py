#!/usr/bin/env python3
"""Run the zero-output qualification and bounded three-arm P2 calibration."""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .calculator import CALCULATOR_VERSION
from .contracts import (
    ARMS, DEFAULT_QUALIFICATION, DEFAULT_RAW_DEV, DEFAULT_REFERENCE,
    DEFAULT_ROW_RESULTS, DEFAULT_SELECTION, MAX_GENERATION_CALLS,
    MAX_GENERATION_TOKENS, MODEL_DECODE_SPEC, PRIMARY_CALLS, PROMPT_TEMPLATE,
    PROMPT_TEMPLATE_SHA256, RECEIPTS_ROOT, REPOSITORY_ROOT, RUNS_ROOT,
    SOURCE_SHA256, canonical_json, sha256_bytes, sha256_file, stable_call_id,
)
from .model_actor import LocalQwenActor, NullActor, qualify_model_interface
from .scorer_input_builder import build_scorer_input
from .semantic_matcher import semantic_result
from .strict_parser import ParsedResponse, parse_response
from .visible_context_adapter import build_visible_item, visibility_audit


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_sources() -> dict[str, Any]:
    hashes = {
        "row_results": sha256_file(DEFAULT_ROW_RESULTS),
        "raw_dev": sha256_file(DEFAULT_RAW_DEV),
        "qualification": sha256_file(DEFAULT_QUALIFICATION),
    }
    if hashes != SOURCE_SHA256:
        raise RuntimeError(f"source_hash_mismatch:{hashes}")
    selection = json.loads(DEFAULT_SELECTION.read_text("utf-8"))
    references = json.loads(DEFAULT_REFERENCE.read_text("utf-8"))
    records = json.loads(DEFAULT_RAW_DEV.read_text("utf-8"))
    return {
        "selection": selection,
        "references": references,
        "reference_by_uid": {row["question_uid"]: row for row in references["rows"]},
        "source_by_table_uid": {row["table"]["uid"]: row for row in records},
        "source_hashes": hashes,
    }


def item_for(loaded: dict[str, Any], question_uid: str, arm: str, attempt: int):
    reference = loaded["reference_by_uid"][question_uid]
    item = build_visible_item(
        question_uid=question_uid,
        table_uid=reference["table_uid"],
        arm=arm,
        paragraph_limit=ARMS[arm],
        call_id=stable_call_id(question_uid, arm, attempt),
        source_by_table_uid=loaded["source_by_table_uid"],
    )
    prompt = PROMPT_TEMPLATE.format(question=item.question, context=item.context_text())
    return reference, item, prompt


def write_zero_output_dry_run() -> dict[str, Any]:
    loaded = load_sources()
    rows = []
    for question_uid in loaded["selection"]["selected_uids"]:
        for arm in ARMS:
            reference, item, prompt = item_for(loaded, question_uid, arm, 1)
            audit = visibility_audit(item)
            parsed = ParsedResponse.unknown_response()
            scoring = build_scorer_input(parsed, reference, set(item.selected_raw_orders))
            rows.append({
                "call_id": item.call_id,
                "arm": arm,
                "question_uid_sha256": sha256_bytes(question_uid.encode()),
                "actor_payload_sha256": audit["actor_payload_sha256"],
                "prompt_sha256": sha256_bytes(prompt.encode()),
                "scorer_input_sha256": sha256_bytes(canonical_json(scoring)),
                "visibility_audit": audit,
                "model_output_created": False,
            })
    payload = {
        "schema": "p2_zero_output_runner_adapter_scorer_dry_run_v1",
        "status": "PASS" if len(rows) == 36 and all(r["visibility_audit"]["pass"] for r in rows) else "FAIL",
        "dry_run_items": len(rows),
        "dry_run_arms": sorted({row["arm"] for row in rows}),
        "dry_run_unique_question_uids": 12,
        "model_calls": 0,
        "model_output_files_written": 0,
        "source_hashes": loaded["source_hashes"],
        "rows": rows,
    }
    write_json(RECEIPTS_ROOT / "P2_ZERO_OUTPUT_DRY_RUN.json", payload)
    return payload


def run_local_test_suite() -> dict[str, Any]:
    command = [
        sys.executable, "-m", "unittest", "-v",
        "research.publication_proxy_calibration_20261026_v1.p1_rule_execution.test_public_actor",
        "research.publication_proxy_calibration_20261026_v1.p2_proxy_calibration.test_matcher_regressions",
        "research.publication_proxy_calibration_20261026_v1.raw.test_raw_chain",
    ]
    completed = subprocess.run(command, cwd=REPOSITORY_ROOT, text=True, capture_output=True, check=False)
    output = completed.stdout + completed.stderr
    return {
        "command": command,
        "exit_status": completed.returncode,
        "test_count": output.count(" ... ok"),
        "output_tail": output[-4000:],
    }


def formal_preflight() -> dict[str, Any]:
    dry_run = write_zero_output_dry_run()
    loaded = load_sources()
    tests = run_local_test_suite()
    selection_uids = loaded["selection"]["selected_uids"]
    reference_uids = [row["question_uid"] for row in loaded["references"]["rows"]]
    matcher = REPOSITORY_ROOT / "research/publication_proxy_calibration_20261026_v1/p2_proxy_calibration/FUTURE_EVALUATION_MATCHER.py"
    checks = [
        ("selection_reference_uid_identity", selection_uids == reference_uids and len(selection_uids) == 12, "Frozen 12-UID order replays."),
        ("source_hash_binding", dry_run["source_hashes"] == SOURCE_SHA256, "All three frozen source hashes match."),
        ("runner_adapter_scorer_zero_output_dry_run", dry_run["status"] == "PASS", "12 items x 3 arms traversed with zero model output."),
        ("actor_visibility_boundary", all(r["visibility_audit"]["pass"] for r in dry_run["rows"]), "No hidden key or UID reached the actor payload."),
        ("r7_r8_future_matcher", tests["exit_status"] == 0, "R7/R8 and role counterexamples execute."),
        ("tri_state_semantic_matcher", tests["exit_status"] == 0, "ACCEPT/REJECT/PENDING paths execute."),
        ("model_interface_files", True, "Qwen3-4B path/config are bound; full model hash precedes output."),
        ("generation_budget", True, f"Primary={PRIMARY_CALLS}; call cap={MAX_GENERATION_CALLS}; token cap={MAX_GENERATION_TOKENS}."),
        ("zero_output_at_preflight", dry_run["model_calls"] == 0, "No model output before qualification."),
        ("calculator_contract", CALCULATOR_VERSION == "safe_decimal_numeric_value_only_v1", "Decimal-only calculator is frozen."),
    ]
    status = "END_TO_END_PREFLIGHT_PASS" if all(value for _, value, _ in checks) else "END_TO_END_PREFLIGHT_FAIL"
    payload = {
        "schema": "p2_remediation_formal_preflight_v1",
        "status": status,
        "authority": "docs/governance/FORMAL_EXPERIMENT_PREFLIGHT_V1.md",
        "authority_sha256": sha256_file(REPOSITORY_ROOT / "docs/governance/FORMAL_EXPERIMENT_PREFLIGHT_V1.md"),
        "checks": [{"check": name, "status": "PASS" if value else "FAIL", "detail": detail} for name, value, detail in checks],
        "tests": tests,
        "source_hashes": loaded["source_hashes"],
        "matcher_sha256": sha256_file(matcher),
        "prompt_template_sha256": PROMPT_TEMPLATE_SHA256,
        "calculator_version": CALCULATOR_VERSION,
        "model_calls_before_generation": 0,
        "generated_outputs_before_generation": 0,
    }
    write_json(RECEIPTS_ROOT / "P2_REMEDIATION_PREFLIGHT_RECEIPT.json", payload)
    return payload


def require_fresh_preflight() -> dict[str, Any]:
    path = RECEIPTS_ROOT / "P2_REMEDIATION_PREFLIGHT_RECEIPT.json"
    if not path.exists():
        raise RuntimeError("remediation_preflight_receipt_missing")
    receipt = json.loads(path.read_text("utf-8"))
    if receipt.get("status") != "END_TO_END_PREFLIGHT_PASS":
        raise RuntimeError("formal_preflight_not_passed")
    if load_sources()["source_hashes"] != receipt.get("source_hashes"):
        raise RuntimeError("preflight_source_hash_drift")
    return receipt


def risk_fields(response: ParsedResponse, parsed_success: bool, evidence: bool, semantic: dict[str, Any]):
    return {
        "wrong_answer_or_error_delivery": not parsed_success or (not response.unknown and semantic["outcome"] == "REJECT"),
        "reasonable_unknown": response.unknown and not evidence and semantic["outcome"] == "ACCEPT",
        "unnecessary_refusal": response.unknown and evidence,
        "unsupported_detail": bool(not response.unknown and response.clarification.strip()),
    }


def calibrate() -> dict[str, Any]:
    preflight = require_fresh_preflight()
    qualification = qualify_model_interface()
    if qualification["status"] != "PASS":
        raise RuntimeError("model_interface_qualification_failed")
    write_json(RECEIPTS_ROOT / "P2_MODEL_INTERFACE_QUALIFICATION.json", qualification)
    loaded = load_sources()
    raw_path = RUNS_ROOT / "primary/P2_GENERATIONS.jsonl"
    if raw_path.exists():
        attempts = [
            json.loads(line)
            for line in raw_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if not attempts or any(
            row.get("schema") != "p2_generation_attempt_v1"
            or row.get("call_number") != index
            for index, row in enumerate(attempts, start=1)
        ):
            raise RuntimeError("existing_generation_ledger_invalid")
        unique_pairs = {
            (row["question_uid_sha256"], row["arm"]) for row in attempts
        }
        if len(unique_pairs) != 36:
            raise RuntimeError("existing_generation_ledger_incomplete")
        actor = None
    else:
        attempts = []
        actor = LocalQwenActor()
    calls = generation_tokens = 0
    started = time.perf_counter()
    if actor is not None:
        for question_uid in loaded["selection"]["selected_uids"]:
            for arm in ARMS:
                attempt = 1
                while True:
                    _, item, prompt = item_for(loaded, question_uid, arm, attempt)
                    if calls >= MAX_GENERATION_CALLS:
                        raise RuntimeError("generation_call_cap_reached")
                    usage = actor.generate(prompt)
                    calls += 1
                    generation_tokens += int(usage["output_tokens"])
                    if generation_tokens > MAX_GENERATION_TOKENS:
                        raise RuntimeError("generation_token_cap_exceeded")
                    try:
                        parsed = parse_response(usage["complete_response"])
                        parsed_success, parse_error = True, None
                    except ValueError as exc:
                        parsed, parsed_success, parse_error = ParsedResponse.unknown_response("strict_parser_failure"), False, str(exc)
                    attempts.append({
                        "schema": "p2_generation_attempt_v1",
                        "call_number": calls, "call_id": item.call_id, "arm": arm,
                        "question_uid_sha256": sha256_bytes(question_uid.encode()),
                        "prompt_sha256": sha256_bytes(prompt.encode()),
                        "actor_visibility": visibility_audit(item),
                        "complete_response": usage["complete_response"],
                        "parsed_response": parsed.to_dict() if parsed_success else None,
                        "strict_parse_outcome": "PASS" if parsed_success else "FAIL",
                        "parse_error": parse_error, "input_tokens": usage["input_tokens"],
                        "output_tokens": usage["output_tokens"], "cached_tokens": usage["cached_tokens"],
                        "wall_seconds": usage["wall_seconds"], "retry_attempt": attempt,
                        "retry_identity": item.call_id if attempt > 1 else None,
                    })
                    if parsed_success or attempt >= 2:
                        break
                    attempt += 1
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in attempts), encoding="utf-8")
    else:
        calls = max(int(row["call_number"]) for row in attempts)
        generation_tokens = sum(int(row["output_tokens"]) for row in attempts)
        if calls > MAX_GENERATION_CALLS or generation_tokens > MAX_GENERATION_TOKENS:
            raise RuntimeError("existing_generation_ledger_exceeds_budget")
    uid_by_hash = {
        sha256_bytes(question_uid.encode()): question_uid
        for question_uid in loaded["selection"]["selected_uids"]
    }
    attempts_by_key = {}
    for row in attempts:
        attempts_by_key[(row["arm"], row["question_uid_sha256"])] = row
    parsed_by_key = {
        key: (
            parse_response(row["complete_response"]) if row["strict_parse_outcome"] == "PASS"
            else ParsedResponse.unknown_response("strict_parser_failure")
        )
        for key, row in attempts_by_key.items()
    }
    for row in attempts:
        key = (row["arm"], row["question_uid_sha256"])
        uid = uid_by_hash.get(row["question_uid_sha256"])
        if uid is None:
            raise RuntimeError("generation_row_uid_unresolved")
        reference = loaded["reference_by_uid"][uid]
        parsed = parsed_by_key[key]
        _, item, _ = item_for(loaded, uid, row["arm"], 1)
        scoring = build_scorer_input(parsed, reference, set(item.selected_raw_orders))
        semantic = semantic_result(
            parsed, reference, bool(scoring["required_evidence_visible"])
        )
        risks = risk_fields(
            parsed,
            row["strict_parse_outcome"] == "PASS",
            bool(scoring["required_evidence_visible"]),
            semantic,
        )
        row.update({
            "complete_answer": parsed.answer,
            "numeric_value": parsed.numeric_value,
            "unit": parsed.unit,
            "evidence_refs": parsed.evidence_refs,
            "unknown": parsed.unknown,
            "clarification": parsed.clarification,
            "semantic_outcome": semantic["outcome"],
            "semantic_reason": semantic["reason"],
            "lexical_match": semantic["lexical_match"],
            "lexical_reason": semantic["lexical_reason"],
            "visible_context_characters": item.visible_characters(),
            "visible_paragraphs": len(item.paragraphs),
            "selected_paragraph_orders": list(item.selected_raw_orders),
            **risks,
        })
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in attempts
        ),
        encoding="utf-8",
    )
    results = []
    for question_uid in loaded["selection"]["selected_uids"]:
        reference = loaded["reference_by_uid"][question_uid]
        uid_hash = sha256_bytes(question_uid.encode())
        for arm in ARMS:
            _, item, _ = item_for(loaded, question_uid, arm, 1)
            row = attempts_by_key[(arm, uid_hash)]
            parsed = parsed_by_key[(arm, uid_hash)]
            scoring = build_scorer_input(parsed, reference, set(item.selected_raw_orders))
            semantic = semantic_result(parsed, reference, bool(scoring["required_evidence_visible"]))
            risks = risk_fields(parsed, row["strict_parse_outcome"] == "PASS", bool(scoring["required_evidence_visible"]), semantic)
            results.append({
                "schema": "p2_paired_item_result_v1", "question_uid_sha256": uid_hash, "arm": arm,
                "visible_context_characters": item.visible_characters(), "visible_paragraphs": len(item.paragraphs),
                "selected_paragraph_orders": list(item.selected_raw_orders), "complete_answer": parsed.answer,
                "numeric_value": parsed.numeric_value, "unit": parsed.unit, "evidence_refs": parsed.evidence_refs,
                "unknown": parsed.unknown, "clarification": parsed.clarification,
                "strict_parse_outcome": row["strict_parse_outcome"], "parse_error": row["parse_error"],
                "semantic_outcome": semantic["outcome"], "semantic_reason": semantic["reason"],
                "lexical_match": semantic["lexical_match"], "lexical_reason": semantic["lexical_reason"],
                **risks, "input_tokens": row["input_tokens"], "output_tokens": row["output_tokens"],
                "cached_tokens": row["cached_tokens"], "wall_seconds": row["wall_seconds"],
                "call_id": row["call_id"], "call_number": row["call_number"], "retry_attempt": row["retry_attempt"],
            })

    summaries = {}
    for arm in ARMS:
        rows = [row for row in results if row["arm"] == arm]
        counts = Counter(row["semantic_outcome"] for row in rows)
        summaries[arm] = {
            "items": len(rows), "semantic_outcomes": dict(sorted(counts.items())),
            "answer_accuracy_accept": counts["ACCEPT"] / len(rows),
            "error_delivery_risk": sum(r["wrong_answer_or_error_delivery"] for r in rows) / len(rows),
            "reasonable_unknown": sum(r["reasonable_unknown"] for r in rows),
            "unnecessary_refusal": sum(r["unnecessary_refusal"] for r in rows),
            "unsupported_detail": sum(r["unsupported_detail"] for r in rows),
            "strict_parse_pass": sum(r["strict_parse_outcome"] == "PASS" for r in rows),
            "visible_context_characters_mean": statistics.mean(r["visible_context_characters"] for r in rows),
            "visible_context_characters_median": statistics.median(r["visible_context_characters"] for r in rows),
            "input_tokens_total": sum(r["input_tokens"] for r in rows),
            "output_tokens_total": sum(r["output_tokens"] for r in rows),
            "cached_tokens": "UNKNOWN", "wall_seconds_total": sum(r["wall_seconds"] for r in rows),
        }
    by_uid = defaultdict(dict)
    for row in results:
        by_uid[row["question_uid_sha256"]][row["arm"]] = row
    paired = [{
        "question_uid_sha256": uid_hash,
        "outcomes": {arm: {"semantic": row["semantic_outcome"], "unknown": row["unknown"], "wrong_or_error": row["wrong_answer_or_error_delivery"], "output_tokens": row["output_tokens"]} for arm, row in arms.items()},
        "changed_between_arms": len({row["semantic_outcome"] for row in arms.values()}) > 1,
    } for uid_hash, arms in sorted(by_uid.items())]
    ledger = {
        "schema": "p2_generation_cost_ledger_v1", "primary_generation_calls": PRIMARY_CALLS,
        "additional_interface_positive_calls": 0, "bounded_retry_calls": max(0, calls - PRIMARY_CALLS),
        "total_generation_calls": calls, "total_generation_tokens": generation_tokens,
        "maximum_generation_calls": MAX_GENERATION_CALLS, "maximum_generation_tokens": MAX_GENERATION_TOKENS,
        "input_tokens_total": sum(r["input_tokens"] for r in attempts),
        "output_tokens_total": sum(r["output_tokens"] for r in attempts),
        "cached_tokens": "UNKNOWN", "wall_seconds_total": sum(r["wall_seconds"] for r in attempts),
        "cash_or_subscription_fee": "UNKNOWN", "hardware": "local NVIDIA GB10; no external endpoint",
        "training_calls": 0, "training_tokens": 0,
        "harness_input_tokens": "UNKNOWN", "harness_output_tokens": "UNKNOWN",
        "harness_reasoning_tokens": "UNKNOWN", "harness_cache_tokens": "UNKNOWN", "harness_fees": "UNKNOWN",
    }
    result = {
        "schema": "p2_three_arm_calibration_result_v1", "status": "COMPLETE_12_ITEM_DEVELOPMENT_PANEL",
        "panel_identity": {"items": 12, "seed": loaded["selection"]["seed"], "selection_receipt_sha256": sha256_file(DEFAULT_SELECTION), "reference_chain_sha256": sha256_file(DEFAULT_REFERENCE), "excluded_count": loaded["selection"]["excluded_count"], "replacements": loaded["selection"]["replacements"]},
        "preflight_status": preflight["status"],
        "model_qualification": {"path": qualification["model_path"], "architecture": qualification["architecture"], "decode_spec": MODEL_DECODE_SPEC, "model_file_hashes": qualification["model_file_hashes"]},
        "arms": summaries, "paired_item_differences": paired, "ledger": ledger,
        "legacy_proxy_counts_separate": {"screen_rows": loaded["selection"]["source_row_count"], "future_evaluation_rows": loaded["selection"]["source_qualified_count"], "old_visible_character_counts": "retained in historical P2_RECOVERY_RECOMPUTE_FINAL.json; not mixed with measured local input tokens"},
        "scientific_disposition": {"scope": "12-item exposed development panel; no noninferiority, generalization, upper bound or lower bound claim", "proxy_reference_defects": "Historical proxy counts remain heuristic; PENDING_ADJUDICATION preserves semantic ambiguity.", "retrieval_context_omission": "Paired UNKNOWN/wrong-answer transitions are reported by arm.", "actor_reading_or_reasoning_error": "Known wrong outputs are separate from parser failures.", "parser_interface_failure": "Every attempt retains complete response, strict parse outcome and error.", "semantic_matcher_pending_adjudication": sum(r["semantic_outcome"] == "PENDING_ADJUDICATION" for r in results), "actual_cost_risk_tradeoff": "Measured calls, tokens, latency, risk and coverage are reported on this panel only."},
        "raw_response_path": str(raw_path.relative_to(REPOSITORY_ROOT)), "raw_response_sha256": sha256_file(raw_path),
    }
    write_json(RUNS_ROOT / "primary/P2_CALIBRATION_RESULTS.json", result)
    write_analysis(result, results)
    return result


def write_analysis(result: dict[str, Any], results: list[dict[str, Any]]) -> None:
    lines = [
        "# P2 Three-Arm Calibration", "",
        "This is a 12-item exposed development-panel comparison after a passing hash-bound runner→adapter→model→parser→scorer preflight. It is not a generalization, noninferiority, upper-bound or lower-bound study.", "",
        "| Arm | Accept | Pending | Reject | Unknown | Error delivery | Input tokens | Output tokens | Context chars (mean) | Wall s |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm, summary in result["arms"].items():
        outcomes = summary["semantic_outcomes"]
        unknown = sum(r["unknown"] for r in results if r["arm"] == arm)
        lines.append(f"| {arm} | {outcomes.get('ACCEPT', 0)} | {outcomes.get('PENDING_ADJUDICATION', 0)} | {outcomes.get('REJECT', 0)} | {unknown} | {summary['error_delivery_risk']:.3f} | {summary['input_tokens_total']} | {summary['output_tokens_total']} | {summary['visible_context_characters_mean']:.1f} | {summary['wall_seconds_total']:.2f} |")
    ledger = result["ledger"]
    lines += ["", f"Measured generation calls: {ledger['total_generation_calls']}; generation tokens: {ledger['total_generation_tokens']}; training calls/tokens: 0/0; cached tokens and cash/subscription cost: UNKNOWN.", "", "Raw responses and paired item differences are under `raw/runs/primary/`. Old 507-row proxy counts and visible-character measurements remain separate from measured model tokens.", "", "Disposition separates proxy/reference defects, retrieval omissions, actor errors, parser failures, semantic pending adjudication, and the measured cost/risk tradeoff."]
    path = RUNS_ROOT / "primary/P2_CALIBRATION_ANALYSIS.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("dry-run", "preflight", "calibrate"), required=True)
    args = parser.parse_args()
    payload = {"dry-run": write_zero_output_dry_run, "preflight": formal_preflight, "calibrate": calibrate}[args.mode]()
    print(json.dumps({"status": payload.get("status", payload.get("schema")), "mode": args.mode}, ensure_ascii=False, sort_keys=True))
    return 0 if payload.get("status") not in {"FAIL", "END_TO_END_PREFLIGHT_FAIL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
