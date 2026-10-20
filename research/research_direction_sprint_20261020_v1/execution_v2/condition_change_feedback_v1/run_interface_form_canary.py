#!/usr/bin/env python3
"""Frozen eight-request interface form canary for contract v3."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
sys.path.insert(0, str(PACKAGE.parent / "finrank_dev"))

from finrank_contract import (  # noqa: E402
    HttpChatAdapter,
    ImmutableRawStore,
    SharedGenerationLedger,
    load_object,
    parse_chat_response,
    sha256_text,
    write_json,
)


RUN_ID = "INTERFACE_FORM_CANARY_V3_20261020"
REQUEST_CAP = 8
RUN_TOKEN_CAP = 34_816
RUNTIME = (
    PACKAGE.parents[3]
    / "research"
    / "tatqa_wp0_2026"
    / "history_collection_execution_v1"
    / "RUNTIME_IDENTITY_SNAPSHOT.json"
)
LEDGER = PACKAGE.parent.parent / "execution_v1" / "RESEARCH_GENERATION_LEDGER.json"
RAW_ROOT = PACKAGE / "raw" / "FORM_CANARY_V3"
RESULT_PATH = PACKAGE / "FORM_CANARY_RESULT.json"
CONTRACT_PATH = PACKAGE / "INTERFACE_CONTRACT_V3.json"


def expected(task_id: str, wrapper: bool) -> dict:
    value = {
        "task_id": task_id,
        "outcome": "approve",
        "evidence_ids": ["CANARY:fact"],
    }
    return {"submit_reimbursement_decision": value} if wrapper else value


def main() -> int:
    runtime = load_object(RUNTIME)["identity"]
    if runtime["model"]["model_id"] != "Qwen3.6-35B-A3B-Q4_K_M.gguf":
        raise RuntimeError("model_identity_drift")
    if runtime["generation"]["max_tokens"] != 256:
        raise RuntimeError("output_cap_drift")
    ledger = SharedGenerationLedger(LEDGER)
    state = load_object(LEDGER)["new_generation_budget"]
    if state["requests_used"] != 82:
        raise RuntimeError("ledger_start_request_mismatch")
    adapter = HttpChatAdapter("http://127.0.0.1:8004", 120)
    raw = ImmutableRawStore(RAW_ROOT)
    rows = []
    run_tokens = 0
    for wrapper in (False, True):
        representation = "TOOL_WRAPPER" if wrapper else "DIRECT_OBJECT"
        for index in range(1, 5):
            task_id = f"FORM:{representation}:{index}"
            target = expected(task_id, wrapper)
            prompt = (
                "Return exactly this JSON object and nothing else: "
                + json.dumps(target, sort_keys=True, separators=(",", ":"))
            )
            payload = {
                "model": runtime["model"]["model_id"],
                "messages": [{"role": "user", "content": prompt}],
                "chat_template_kwargs": {"enable_thinking": False},
                **runtime["generation"],
            }
            request_key = f"form|{representation}|{index}"
            record_id = ledger.reserve(RUN_ID, request_key, sha256_text(payload))
            request_root = None
            try:
                _, request_root = raw.begin_request(request_key, payload)
                response = adapter.complete(payload)
                raw.persist_response(request_root, response)
                parsed = parse_chat_response(response)
            except Exception as exc:
                ledger.settle(record_id, "FAILED", None, f"{type(exc).__name__}:{exc}")
                if request_root is not None:
                    raw.mark_crash(request_root, f"{type(exc).__name__}:{exc}")
                raise
            usage = parsed["usage"]
            ledger.settle(record_id, "OK", int(usage["total_tokens"]))
            run_tokens += int(usage["total_tokens"])
            try:
                observed = json.loads(parsed["content"])
                valid = observed == target
                error = None
            except json.JSONDecodeError as exc:
                observed = None
                valid = False
                error = str(exc)
            rows.append(
                {
                    "completion_tokens": int(usage["completion_tokens"]),
                    "error": error,
                    "expected": target,
                    "observed": observed,
                    "representation": representation,
                    "task_id": task_id,
                    "valid": valid,
                }
            )
    summary = {}
    for representation in ("DIRECT_OBJECT", "TOOL_WRAPPER"):
        arm = [row for row in rows if row["representation"] == representation]
        summary[representation] = {
            "completion_tokens": sum(row["completion_tokens"] for row in arm),
            "valid": sum(row["valid"] for row in arm),
            "total": len(arm),
        }
    selected = (
        "DIRECT_OBJECT"
        if summary["DIRECT_OBJECT"]["valid"] >= summary["TOOL_WRAPPER"]["valid"]
        else "TOOL_WRAPPER"
    )
    result = {
        "evidence_identity": "ENGINEERING_FORM_CANARY",
        "model_requests": len(rows),
        "rows": rows,
        "run_accounting_tokens": run_tokens,
        "schema": "interface_form_canary_result_v1",
        "selected_representation": selected,
        "status": "COMPLETE",
        "summary": summary,
    }
    write_json(RESULT_PATH, result)
    write_json(
        CONTRACT_PATH,
        {
            "contract_version": "interface_contract_v3",
            "evidence_identity": "ENGINEERING_FORM_CANARY",
            "representation": selected,
            "selection_rule": (
                "strict form-valid count; ties select DIRECT_OBJECT"
            ),
            "source_result_sha256": sha256_text(result),
            "status": "FROZEN_AFTER_FORM_CANARY",
        },
    )
    print(json.dumps({"selected": selected, "summary": summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
