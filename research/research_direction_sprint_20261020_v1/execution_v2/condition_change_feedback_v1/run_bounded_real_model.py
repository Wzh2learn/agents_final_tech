#!/usr/bin/env python3
"""Execute the frozen Tier 1 condition-change model observation."""

from __future__ import annotations

import argparse
import json
import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import Any


PACKAGE = Path(__file__).resolve().parent
EXECUTION_V2 = PACKAGE.parent
SPRINT_ROOT = EXECUTION_V2.parent
PROJECT_ROOT = SPRINT_ROOT.parent.parent
FINRANK_PACKAGE = EXECUTION_V2 / "finrank_dev"
sys.path.insert(0, str(FINRANK_PACKAGE))

from finrank_contract import (  # noqa: E402
    HttpChatAdapter,
    ImmutableRawStore,
    SharedGenerationLedger,
    load_object,
    parse_chat_response,
    sha256_file,
    sha256_text,
    strict_json_object,
    utc_now,
    write_json,
)
from run_feedback_probe import feedback_disposition, fixed_decimal  # noqa: E402


PREREG_PATH = PACKAGE / "BOUNDED_REAL_MODEL_V1_PREREGISTRATION.md"
ACTOR_PATH = PACKAGE / "ACTOR_TASKS_V2.json"
REFERENCE_PATH = PACKAGE / "REFERENCE_TASKS_V2.json"
SCHEMA_PATH = PACKAGE / "TASK_TOOL_SCHEMA_V2.json"
INPUT_MANIFEST_PATH = PACKAGE / "FROZEN_INPUT_MANIFEST_V2.json"
RUNTIME_SNAPSHOT_PATH = (
    PROJECT_ROOT
    / "research"
    / "tatqa_wp0_2026"
    / "history_collection_execution_v1"
    / "RUNTIME_IDENTITY_SNAPSHOT.json"
)
SHARED_LEDGER = SPRINT_ROOT / "execution_v1" / "RESEARCH_GENERATION_LEDGER.json"
RUN_MANIFEST_PATH = PACKAGE / "BOUNDED_REAL_MODEL_RUN_MANIFEST.json"
RUNTIME_QUALIFICATION_PATH = PACKAGE / "RUNTIME_QUALIFICATION_TIER1.json"
CC013_PROBE_PATH = PACKAGE / "CC013_ALTERNATE_PATH_PROBE.json"
RESULT_PATH = PACKAGE / "BOUNDED_REAL_MODEL_RESULT.json"
PARTIAL_PATH = PACKAGE / "BOUNDED_REAL_MODEL_PARTIAL.json"
RAW_ROOT = PACKAGE / "raw" / "BOUNDED_REAL_MODEL_V1"

RUN_ID = "CONDITION_CHANGE_TIER1_20261020"
REQUEST_CAP = 26
RUN_TOKEN_CAP = 113_152
REQUEST_INPUT_CAP = 4_096
REQUEST_OUTPUT_CAP = 256
CONTRACTS = ("exact_match", "sufficiency_only", "composite")


def require_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise ValueError(
            f"{label}_keys_invalid missing={sorted(expected - set(value))} "
            f"unknown={sorted(set(value) - expected)}"
        )


def validate_submission(
    value: dict[str, Any],
    actor_task: dict[str, Any],
) -> dict[str, Any]:
    require_keys(value, {"task_id", "outcome", "evidence_ids"}, "submission")
    if value["task_id"] != actor_task["task_id"]:
        raise ValueError("submission_task_id_mismatch")
    if value["outcome"] not in {"approve", "reject"}:
        raise ValueError("submission_outcome_invalid")
    evidence_ids = value["evidence_ids"]
    if not isinstance(evidence_ids, list) or not 1 <= len(evidence_ids) <= 4:
        raise ValueError("submission_evidence_count_invalid")
    if any(not isinstance(item, str) or not item for item in evidence_ids):
        raise ValueError("submission_evidence_id_invalid")
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError("submission_duplicate_evidence_id")
    allowed = {
        item["fact_id"]
        for item in actor_task["observation"]["evidence_inventory"]
    }
    unknown = sorted(set(evidence_ids) - allowed)
    if unknown:
        raise ValueError(f"submission_unknown_evidence_id:{unknown}")
    return {
        "task_id": value["task_id"],
        "outcome": value["outcome"],
        "evidence_ids": list(evidence_ids),
    }


def parse_submission(
    content: str,
    actor_task: dict[str, Any],
) -> dict[str, Any]:
    return validate_submission(strict_json_object(content), actor_task)


def submission_tool_from_schema(schema_doc: dict[str, Any]) -> dict[str, Any]:
    definition = schema_doc["$defs"]["submission_tool"]
    return {
        "input_schema": definition["properties"]["input_schema"],
        "name": definition["properties"]["name"]["const"],
    }


def verify_frozen_inputs() -> dict[str, Any]:
    manifest = load_object(INPUT_MANIFEST_PATH)
    checked = []
    for entry in manifest["canonical_input_files"]:
        path = PACKAGE / entry["path"]
        actual = sha256_file(path)
        if actual != entry["sha256"]:
            raise ValueError(f"frozen_input_hash_mismatch:{entry['path']}")
        checked.append({"path": entry["path"], "sha256": actual})
    return {
        "count": len(checked),
        "files": checked,
        "input_manifest_sha256": sha256_file(INPUT_MANIFEST_PATH),
        "preregistration_sha256": sha256_file(PREREG_PATH),
    }


def port_8004_listening() -> bool:
    for path in (Path("/proc/net/tcp"), Path("/proc/net/tcp6")):
        if not path.exists():
            continue
        for line in path.read_text(encoding="ascii").splitlines()[1:]:
            fields = line.split()
            if len(fields) >= 4 and fields[1].endswith(":1F44") and fields[3] == "0A":
                return True
    return False


def llama_server_processes() -> list[str]:
    matches = []
    for cmdline_path in Path("/proc").glob("[0-9]*/cmdline"):
        try:
            cmdline = cmdline_path.read_bytes().replace(b"\0", b" ").decode(
                "utf-8", errors="replace"
            )
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if "llama-server" in cmdline:
            matches.append(cmdline.strip())
    return sorted(matches)


def qualify_runtime() -> dict[str, Any]:
    snapshot = load_object(RUNTIME_SNAPSHOT_PATH)
    identity = snapshot["identity"]
    if identity["model"]["model_id"] != "Qwen3.6-35B-A3B-Q4_K_M.gguf":
        raise ValueError("runtime_model_id_drift")
    if identity["generation"]["temperature"] != 0:
        raise ValueError("runtime_temperature_drift")
    if identity["generation"]["max_tokens"] != REQUEST_OUTPUT_CAP:
        raise ValueError("runtime_output_cap_drift")
    if identity["chat_template_kwargs"] != {"enable_thinking": False}:
        raise ValueError("runtime_thinking_switch_drift")
    if identity["generation"]["response_format"] != {"type": "json_object"}:
        raise ValueError("runtime_response_format_drift")
    model_path = Path(identity["model"]["path"])
    server_path = Path(identity["server_binary"]["path"])
    if not model_path.is_file() or not server_path.is_file():
        raise ValueError("runtime_artifact_missing")
    if model_path.stat().st_size != identity["model"]["bytes"]:
        raise ValueError("runtime_model_size_drift")
    model_sha = sha256_file(model_path)
    server_sha = sha256_file(server_path)
    if model_sha != identity["model"]["sha256"]:
        raise ValueError("runtime_model_hash_drift")
    if server_sha != identity["server_binary"]["sha256"]:
        raise ValueError("runtime_server_hash_drift")
    listening = port_8004_listening()
    processes = llama_server_processes()
    if not listening or not processes:
        raise ValueError("runtime_local_service_not_observed")
    return {
        "status": "QUALIFIED_LOCAL_FILES_AND_PROCESS_PORT",
        "checked_at_utc": utc_now(),
        "model_id": identity["model"]["model_id"],
        "model_sha256": model_sha,
        "server_sha256": server_sha,
        "chat_template_sha256_snapshot": identity["chat_template"]["sha256"],
        "chat_template_current_rehash": "NOT_PERFORMED_NO_PROPS_ENDPOINT_CALL",
        "generation": identity["generation"],
        "chat_template_kwargs": identity["chat_template_kwargs"],
        "base_url": "http://127.0.0.1:8004",
        "port_8004_listening": listening,
        "llama_server_process_count": len(processes),
        "network_calls_during_qualification": 0,
    }


def feedback_results(
    selected_evidence_ids: list[str],
    submitted_outcome: str,
    reference: dict[str, Any],
) -> dict[str, Any]:
    return {
        contract: feedback_disposition(
            contract,
            selected_evidence_ids,
            submitted_outcome,
            reference,
        )
        for contract in CONTRACTS
    }


def build_cc013_probe(references_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    cases = [
        {
            "probe": "clean_canonical",
            "outcome": "approve",
            "selected_evidence_ids": [
                "CC013:manager_approval",
                "CC013:receipt",
            ],
            "expected": {"pre": "sufficient", "post": "sufficient"},
        },
        {
            "probe": "alternate_path",
            "outcome": "approve",
            "selected_evidence_ids": [
                "CC013:card_statement",
                "CC013:manager_approval",
                "CC013:merchant_invoice",
            ],
            "expected": {"pre": "sufficient", "post": "insufficient"},
        },
    ]
    rows = []
    for case in cases:
        stage_results = {}
        for stage in ("pre", "post"):
            reference = references_by_id[f"CC013:{stage}"]
            dispositions = feedback_results(
                case["selected_evidence_ids"],
                case["outcome"],
                reference,
            )
            stage_results[stage] = {
                "decision_outcome": reference["decision"]["outcome"],
                "plan_sufficient": dispositions["composite"]["plan_sufficient"],
                "composite_accepted": dispositions["composite"]["accepted"],
                "contract_reason_code": dispositions["composite"][
                    "contract_reason_code"
                ],
            }
        observed = {
            stage: "sufficient" if result["plan_sufficient"] else "insufficient"
            for stage, result in stage_results.items()
        }
        if observed != case["expected"]:
            raise ValueError(f"cc013_probe_mismatch:{case['probe']}:{observed}")
        rows.append(
            {
                "probe": case["probe"],
                "outcome": case["outcome"],
                "selected_evidence_ids": case["selected_evidence_ids"],
                "expected": case["expected"],
                "observed": observed,
                "stages": stage_results,
            }
        )
    return {
        "schema": "cc013_alternate_path_probe_v1",
        "status": "PASS",
        "generation_requests": 0,
        "rows": rows,
    }


def fixed_fraction(value: Fraction) -> dict[str, Any]:
    return {
        "denominator": value.denominator,
        "mean": fixed_decimal(value),
        "numerator": value.numerator,
    }


def metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(rows)
    if count == 0:
        raise ValueError("metric_rows_empty")
    precision_sum = sum(
        (
            Fraction(
                row["plan_precision_numerator"],
                row["plan_precision_denominator"],
            )
            for row in rows
        ),
        Fraction(0, 1),
    )
    micro_precision = Fraction(
        sum(row["plan_precision_numerator"] for row in rows),
        sum(row["plan_precision_denominator"] for row in rows),
    )
    exact_count = sum(row["contract_acceptance"]["exact_match"] for row in rows)
    sufficiency_count = sum(
        row["contract_acceptance"]["sufficiency_only"] for row in rows
    )
    composite_count = sum(
        row["contract_acceptance"]["composite"] for row in rows
    )
    answer_count = sum(row["answer_covered"] for row in rows)
    sufficient_count = sum(row["plan_sufficient"] for row in rows)
    return {
        "answer_covered_count": answer_count,
        "answer_coverage_rate": answer_count / count,
        "composite_accepted_count": composite_count,
        "composite_acceptance_rate": composite_count / count,
        "exact_match_accepted_count": exact_count,
        "exact_match_acceptance_rate": exact_count / count,
        "invalid_submission_count": sum(
            row["submission_status"] != "VALID" for row in rows
        ),
        "plan_precision_macro": fixed_fraction(precision_sum / count),
        "plan_precision_micro": fixed_fraction(micro_precision),
        "plan_sufficient_count": sufficient_count,
        "plan_sufficient_rate": sufficient_count / count,
        "sufficiency_only_accepted_count": sufficiency_count,
        "sufficiency_only_acceptance_rate": sufficiency_count / count,
        "tasks": count,
    }


def pair_metrics(
    rows: list[dict[str, Any]],
    references_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    by_case: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_case.setdefault(row["case_id"], {})[row["stage"]] = row
    flip_total = 0
    flip_revised = 0
    invariant_total = 0
    invariant_preserved = 0
    details = []
    for case_id, stages in sorted(by_case.items()):
        if set(stages) != {"pre", "post"}:
            continue
        pre_ref = references_by_id[f"{case_id}:pre"]
        post_ref = references_by_id[f"{case_id}:post"]
        flip = pre_ref["decision"]["outcome"] != post_ref["decision"]["outcome"]
        pre = stages["pre"]
        post = stages["post"]
        both_correct = pre["answer_covered"] and post["answer_covered"]
        changed = pre["submitted_outcome"] != post["submitted_outcome"]
        if flip:
            flip_total += 1
            if both_correct and changed:
                flip_revised += 1
        else:
            invariant_total += 1
            if both_correct and not changed:
                invariant_preserved += 1
        details.append(
            {
                "both_outcomes_correct": both_correct,
                "case_id": case_id,
                "changed": changed,
                "class": "decision_flip" if flip else "invariant",
            }
        )
    return {
        "decision_flip_count": flip_total,
        "decision_flip_revision_count": flip_revised,
        "decision_flip_revision_rate": flip_revised / flip_total
        if flip_total
        else None,
        "invariant_count": invariant_total,
        "invariant_preserved_count": invariant_preserved,
        "invariant_preservation_rate": invariant_preserved / invariant_total
        if invariant_total
        else None,
        "pairs": details,
    }


def freeze_run_manifest() -> dict[str, Any]:
    frozen = verify_frozen_inputs()
    runtime = qualify_runtime()
    actor_doc = load_object(ACTOR_PATH)
    reference_doc = load_object(REFERENCE_PATH)
    schema_doc = load_object(SCHEMA_PATH)
    references_by_id = {
        item["task_id"]: item for item in reference_doc["references"]
    }
    tasks = actor_doc["tasks"]
    expected_order = [
        f"CC{index:03d}:{stage}"
        for index in range(1, 14)
        for stage in ("post", "pre")
    ]
    if len(tasks) != REQUEST_CAP:
        raise ValueError("actor_task_count_invalid")
    if [item["task_id"] for item in tasks] != expected_order:
        raise ValueError("actor_task_order_invalid")
    if set(references_by_id) != {item["task_id"] for item in tasks}:
        raise ValueError("actor_reference_ids_invalid")
    submission_tool = submission_tool_from_schema(schema_doc)
    if submission_tool["name"] != "submit_reimbursement_decision":
        raise ValueError("submission_tool_name_invalid")
    cc013 = build_cc013_probe(references_by_id)
    write_json(CC013_PROBE_PATH, cc013)
    write_json(RUNTIME_QUALIFICATION_PATH, runtime)
    manifest = {
        "schema": "bounded_real_model_run_manifest_v1",
        "status": "FROZEN_BEFORE_REQUESTS",
        "run_id": RUN_ID,
        "created_at_utc": utc_now(),
        "frozen_inputs": frozen,
        "runtime_qualification_sha256": sha256_file(RUNTIME_QUALIFICATION_PATH),
        "cc013_probe_sha256": sha256_file(CC013_PROBE_PATH),
        "actor_task_sha256": sha256_file(ACTOR_PATH),
        "reference_sha256": sha256_file(REFERENCE_PATH),
        "schema_sha256": sha256_file(SCHEMA_PATH),
        "task_order": [item["task_id"] for item in tasks],
        "request_cap": REQUEST_CAP,
        "retry_cap": 0,
        "run_token_cap": RUN_TOKEN_CAP,
        "request_input_cap": REQUEST_INPUT_CAP,
        "request_output_cap": REQUEST_OUTPUT_CAP,
        "contracts": list(CONTRACTS),
    }
    write_json(RUN_MANIFEST_PATH, manifest)
    return manifest


def invalid_result(
    actor_task: dict[str, Any],
    submission_status: str,
    error: str,
) -> dict[str, Any]:
    return {
        "answer_covered": False,
        "case_id": actor_task["case_id"],
        "contract_acceptance": {contract: False for contract in CONTRACTS},
        "contracts": {},
        "error": error,
        "plan_precision_denominator": 1,
        "plan_precision_numerator": 0,
        "plan_sufficient": False,
        "stage": actor_task["stage"],
        "submission": None,
        "submission_status": submission_status,
        "submitted_outcome": None,
        "task_id": actor_task["task_id"],
    }


def valid_result(
    actor_task: dict[str, Any],
    reference: dict[str, Any],
    submission: dict[str, Any],
) -> dict[str, Any]:
    contracts = feedback_results(
        submission["evidence_ids"],
        submission["outcome"],
        reference,
    )
    composite = contracts["composite"]
    return {
        "answer_covered": composite["answer_coverage"],
        "case_id": actor_task["case_id"],
        "contract_acceptance": {
            contract: contracts[contract]["accepted"]
            for contract in CONTRACTS
        },
        "contracts": contracts,
        "error": None,
        "plan_precision_denominator": composite["plan_precision_denominator"],
        "plan_precision_numerator": composite["plan_precision_numerator"],
        "plan_sufficient": composite["plan_sufficient"],
        "stage": actor_task["stage"],
        "submission": submission,
        "submission_status": "VALID",
        "submitted_outcome": submission["outcome"],
        "task_id": actor_task["task_id"],
    }


def build_messages(
    actor_task: dict[str, Any],
    submission_tool: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "Return exactly one JSON object matching the submission tool "
                "input schema. No Markdown, commentary, or extra keys."
            ),
        },
        {
            "role": "user",
            "content": (
                f"ACTOR_TASK={json.dumps(actor_task, ensure_ascii=False, sort_keys=True)}\n"
                f"SUBMISSION_TOOL={json.dumps(submission_tool, ensure_ascii=False, sort_keys=True)}\n"
                "Submit the reimbursement decision now."
            ),
        },
    ]


def execute_run() -> dict[str, Any]:
    if not RUN_MANIFEST_PATH.is_file():
        raise RuntimeError("run_manifest_missing")
    manifest = load_object(RUN_MANIFEST_PATH)
    if manifest["status"] != "FROZEN_BEFORE_REQUESTS":
        raise RuntimeError("run_manifest_not_frozen")
    if manifest["run_id"] != RUN_ID:
        raise RuntimeError("run_id_mismatch")
    verify_frozen_inputs()
    if sha256_file(RUNTIME_QUALIFICATION_PATH) != manifest[
        "runtime_qualification_sha256"
    ]:
        raise RuntimeError("runtime_qualification_hash_mismatch")
    if sha256_file(CC013_PROBE_PATH) != manifest["cc013_probe_sha256"]:
        raise RuntimeError("cc013_probe_hash_mismatch")
    actor_doc = load_object(ACTOR_PATH)
    reference_doc = load_object(REFERENCE_PATH)
    schema_doc = load_object(SCHEMA_PATH)
    tasks = actor_doc["tasks"]
    references_by_id = {
        item["task_id"]: item for item in reference_doc["references"]
    }
    submission_tool = submission_tool_from_schema(schema_doc)
    ledger = SharedGenerationLedger(SHARED_LEDGER)
    ledger_state = load_object(SHARED_LEDGER)["new_generation_budget"]
    if ledger_state["requests_used"] != 56:
        raise RuntimeError("shared_ledger_start_count_mismatch")
    if ledger_state["accounting_tokens_used"] != 458_650:
        raise RuntimeError("shared_ledger_start_token_mismatch")
    runtime = load_object(RUNTIME_SNAPSHOT_PATH)["identity"]
    adapter = HttpChatAdapter("http://127.0.0.1:8004", 120)
    raw = ImmutableRawStore(RAW_ROOT)
    results: list[dict[str, Any]] = []
    request_records = []
    run_tokens = 0
    stop_reason = None
    started = time.monotonic()
    for actor_task in tasks:
        reference = references_by_id[actor_task["task_id"]]
        messages = build_messages(actor_task, submission_tool)
        payload = {
            "model": runtime["model"]["model_id"],
            "messages": messages,
            "chat_template_kwargs": {"enable_thinking": False},
            **runtime["generation"],
        }
        estimated_tokens = len(
            json.dumps(payload, ensure_ascii=False, sort_keys=True)
        ) / 2.5
        if estimated_tokens > REQUEST_INPUT_CAP:
            stop_reason = "INPUT_ESTIMATE_EXCEEDED_BEFORE_REQUEST"
            results.append(invalid_result(actor_task, "NOT_SENT", stop_reason))
            break
        request_key = f"submission|{actor_task['task_id']}"
        record_id = ledger.reserve(
            RUN_ID,
            request_key,
            sha256_text(payload),
        )
        request_root = None
        try:
            _, request_root = raw.begin_request(request_key, payload)
            raw_response = adapter.complete(payload)
            raw.persist_response(request_root, raw_response)
            parsed = parse_chat_response(raw_response)
        except Exception as exc:
            error = f"{type(exc).__name__}:{exc}"
            ledger.settle(record_id, "FAILED", None, error)
            if request_root is not None:
                raw.mark_crash(request_root, error)
            results.append(invalid_result(actor_task, "TRANSPORT_FAILURE", error))
            stop_reason = "TRANSPORT_FAILURE"
            break
        usage = parsed["usage"]
        usage_total = int(usage["total_tokens"])
        prompt_tokens = int(usage.get("prompt_tokens", 0))
        completion_tokens = int(usage.get("completion_tokens", 0))
        ledger.settle(record_id, "OK", usage_total)
        run_tokens += usage_total
        request_records.append(
            {
                "completion_tokens": completion_tokens,
                "prompt_tokens": prompt_tokens,
                "record_id": record_id,
                "request_key": request_key,
                "task_id": actor_task["task_id"],
                "total_tokens": usage_total,
            }
        )
        if prompt_tokens > REQUEST_INPUT_CAP:
            results.append(
                invalid_result(
                    actor_task,
                    "INPUT_CAP_EXCEEDED",
                    f"prompt_tokens:{prompt_tokens}",
                )
            )
            stop_reason = "INPUT_CAP_EXCEEDED"
            break
        if completion_tokens > REQUEST_OUTPUT_CAP:
            results.append(
                invalid_result(
                    actor_task,
                    "OUTPUT_CAP_EXCEEDED",
                    f"completion_tokens:{completion_tokens}",
                )
            )
            stop_reason = "OUTPUT_CAP_EXCEEDED"
            break
        try:
            submission = parse_submission(parsed["content"], actor_task)
            result = valid_result(actor_task, reference, submission)
        except ValueError as exc:
            result = invalid_result(
                actor_task,
                "INVALID_SUBMISSION",
                str(exc),
            )
        results.append(result)
        write_json(
            PARTIAL_PATH,
            {
                "request_records": request_records,
                "results": results,
                "run_id": RUN_ID,
                "run_tokens": run_tokens,
                "stop_reason": stop_reason,
            },
        )
        if run_tokens > RUN_TOKEN_CAP:
            stop_reason = "RUN_TOKEN_CAP_EXCEEDED"
            break
    by_stage = {
        stage: metrics([row for row in results if row["stage"] == stage])
        for stage in ("pre", "post")
        if any(row["stage"] == stage for row in results)
    }
    output = {
        "schema": "bounded_real_model_result_v1",
        "status": (
            "COMPLETE_TIER1"
            if len(results) == REQUEST_CAP and stop_reason is None
            else "STOPPED_PARTIAL"
        ),
        "run_id": RUN_ID,
        "started_at_utc": manifest["created_at_utc"],
        "elapsed_seconds": time.monotonic() - started,
        "generation_requests": len(request_records),
        "run_accounting_tokens": run_tokens,
        "stop_reason": stop_reason,
        "raw_root": str(RAW_ROOT),
        "by_stage": by_stage,
        "overall": metrics(results) if results else None,
        "pair_behavior": pair_metrics(results, references_by_id)
        if results
        else None,
        "request_records": request_records,
        "results": results,
        "explicit_non_claims": [
            "no feedback was shown to the model",
            "no learning or adaptation effect",
            "no public generalization",
            "no human gold",
        ],
    }
    write_json(RESULT_PATH, output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "execute"))
    args = parser.parse_args()
    if args.mode == "preflight":
        manifest = freeze_run_manifest()
        print(
            json.dumps(
                {
                    "run_id": manifest["run_id"],
                    "status": manifest["status"],
                    "tasks": len(manifest["task_order"]),
                },
                sort_keys=True,
            )
        )
        return 0
    output = execute_run()
    print(
        json.dumps(
            {
                "generation_requests": output["generation_requests"],
                "run_accounting_tokens": output["run_accounting_tokens"],
                "status": output["status"],
                "stop_reason": output["stop_reason"],
            },
            sort_keys=True,
        )
    )
    return 0 if output["status"] == "COMPLETE_TIER1" else 1


if __name__ == "__main__":
    raise SystemExit(main())
