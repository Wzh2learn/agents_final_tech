"""Generate the frozen 24-call D/T/M batch through the persistent guard."""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

from research.adaptive_mechanism_20261027_v1.persistent_budget.ledger import (
    PersistentLedger,
)
from research.adaptive_mechanism_20261027_v1.persistent_budget.runner import (
    GenerationSpec,
    generate_once,
)
from research.word_scoring_new_family_20261027_v1.generation.local_loader import (
    load_and_generate,
    raw_persisted_scorer,
)


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
LEDGER_PATH = Path(
    "/home/testuser/wzh/research_runs/persistent_budget/"
    "word_new_family_20261027/ledger.jsonl"
)
PLANNED_PATH = ROOT / "mechanism" / "PLANNED_PROMPTS.jsonl"
FREEZE_PATH = ROOT / "mechanism" / "MECHANISM_FREEZE.json"
FAULT_RECEIPT_PATH = ROOT / "budget" / "BUDGET_FAULT_TEST_RECEIPT.json"
TOKEN_RECEIPT_PATH = ROOT / "generation" / "TOKEN_QUALIFICATION.json"
INTERFACE_FAULT_PATH = ROOT / "generation" / "INTERFACE_FAULT_RECEIPT.json"
PRE_RECEIPT_PATH = ROOT / "generation" / "PRE_GENERATION_RECEIPT.json"
RUN_RECEIPT_PATH = ROOT / "generation" / "GENERATION_RECEIPT.json"
RECEIPTS_DIR = ROOT / "generation" / "receipts"
MAX_NEW_TOKENS = 512
PLANNED_ATTEMPTS = 24


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_planned() -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in PLANNED_PATH.read_text(encoding="utf-8").splitlines()
        if line
    ]


def ensure_pre_generation_receipt() -> dict[str, object]:
    values = {
        "schema": "word_new_family_pre_generation_receipt_v1",
        "status": "READY_FOR_LOCAL_GENERATION",
        "run_id": "word-new-family-20261027-a",
        "ledger_path": str(LEDGER_PATH),
        "freeze_path": str(FREEZE_PATH.relative_to(REPO)),
        "freeze_sha256": sha256(FREEZE_PATH),
        "planned_prompts_path": str(PLANNED_PATH.relative_to(REPO)),
        "planned_prompts_sha256": sha256(PLANNED_PATH),
        "fault_test_status": json.loads(FAULT_RECEIPT_PATH.read_text())["status"],
        "fault_test_sha256": sha256(FAULT_RECEIPT_PATH),
        "token_qualification_status": json.loads(
            TOKEN_RECEIPT_PATH.read_text()
        )["status"],
        "token_qualification_sha256": sha256(TOKEN_RECEIPT_PATH),
        "actual_model_loaded": False,
        "new_model_outputs": 0,
        "training_runs": 0,
        "generated_outputs_seen_by_freeze": False,
    }
    if PRE_RECEIPT_PATH.exists():
        current = json.loads(PRE_RECEIPT_PATH.read_text(encoding="utf-8"))
        if current != values:
            raise RuntimeError("pre_generation_receipt_changed")
        return current
    write_json(PRE_RECEIPT_PATH, values)
    return values


def main() -> int:
    if (
        json.loads(FAULT_RECEIPT_PATH.read_text(encoding="utf-8"))["status"]
        != "PASS"
    ):
        raise RuntimeError("budget_fault_tests_not_passed")
    token_receipt = json.loads(TOKEN_RECEIPT_PATH.read_text(encoding="utf-8"))
    if token_receipt["status"] != "QUALIFIED_PRE_GENERATION":
        raise RuntimeError("token_qualification_failed")
    ensure_pre_generation_receipt()
    planned = load_planned()
    if len(planned) != PLANNED_ATTEMPTS:
        raise RuntimeError(f"planned_attempt_count:{len(planned)}")
    token_rows = {
        row["logical_call_id"]: row for row in token_receipt["rows"]
    }
    ledger = PersistentLedger(LEDGER_PATH)
    existing = ledger.snapshot_now()
    if existing.uncertain_reservations:
        print(
            json.dumps(
                {
                    "uncertain_reservations_preserved": len(
                        existing.uncertain_reservations
                    ),
                    "action": "use_preregistered_bounded_retry_ids",
                },
                sort_keys=True,
            ),
            flush=True,
        )
    raw_by_logical = {
        row["logical_call_id"] for row in existing.raw_responses
    }
    uncertain_logical = {
        row["logical_call_id"] for row in existing.uncertain_reservations
    }
    started_at = time.time()
    generated = 0
    skipped_existing = 0
    for row in planned:
        planned_logical_call_id = str(row["logical_call_id"])
        candidates = [planned_logical_call_id] + [
            f"{planned_logical_call_id}:retry-{index}"
            for index in range(1, 13)
        ]
        if any(candidate in raw_by_logical for candidate in candidates):
            skipped_existing += 1
            continue
        logical_call_id = next(
            candidate
            for candidate in candidates
            if candidate not in uncertain_logical
        )
        attempt_suffix = (
            logical_call_id.removeprefix(planned_logical_call_id)
            if logical_call_id != planned_logical_call_id
            else ""
        )
        token_row = token_rows[planned_logical_call_id]
        input_tokens = int(token_row["reservation_upper_bound"])
        output_dir = (
            ROOT
            / "generation"
            / "raw"
            / str(row["arm"])
            / str(row["question_uid"])
            / ("retry-1" if attempt_suffix else "primary")
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        spec = GenerationSpec(
            logical_call_id=logical_call_id,
            arm=str(row["arm"]),
            payload={"messages": row["messages"]},
            input_tokens_upper_bound=input_tokens,
            max_new_tokens=MAX_NEW_TOKENS,
            output_dir=output_dir,
        )
        receipt = generate_once(
            ledger,
            spec,
            model_loader=load_and_generate,
            scorer=raw_persisted_scorer,
            score_output=RECEIPTS_DIR / f"{row['arm']}:{row['question_uid']}.json",
        )
        generated += 1
        print(
            json.dumps(
                {
                    "logical_call_id": logical_call_id,
                    "physical_attempt_id": receipt["physical_attempt_id"],
                    "generated": generated,
                    "skipped_existing": skipped_existing,
                },
                sort_keys=True,
            ),
            flush=True,
        )
    snapshot = ledger.snapshot_now()
    completed = len(snapshot.raw_responses)
    receipt = {
        "schema": "word_new_family_generation_receipt_v1",
        "status": "COMPLETE" if completed == PLANNED_ATTEMPTS else "INCOMPLETE",
        "run_id": "word-new-family-20261027-a",
        "ledger_path": str(LEDGER_PATH),
        "ledger_sha256": sha256(LEDGER_PATH),
        "planned_attempts": PLANNED_ATTEMPTS,
        "primary_attempts_completed": completed,
        "new_attempts_this_process": generated,
        "skipped_existing_attempts": skipped_existing,
        "preserved_failed_reservations": len(existing.uncertain_reservations),
        "bounded_retries": sum(
            ":retry-" in str(row["logical_call_id"])
            for row in snapshot.raw_responses
        ),
        "reserve_attempts_used": max(
            0, snapshot.physical_attempts - PLANNED_ATTEMPTS
        ),
        "reserve_attempts_available": 12
        - max(0, snapshot.physical_attempts - PLANNED_ATTEMPTS),
        "physical_attempt_cap": 36,
        "consumed_input_tokens": snapshot.consumed_input_tokens,
        "consumed_output_tokens": snapshot.consumed_output_tokens,
        "consumed_tokens": snapshot.consumed_tokens,
        "token_cap": 240000,
        "uncertain_reservations": len(snapshot.uncertain_reservations),
        "retries": 0,
        "wall_seconds_this_process": time.time() - started_at,
        "model_loader": "local transformers Qwen3-4B on CUDA GB10",
        "service_or_endpoint_calls": 0,
        "external_harness_calls": 0,
        "judge_calls": 0,
        "paid_api_calls": 0,
        "production_calls": 0,
        "training_runs": 0,
        "adapters_loaded": 0,
        "os_getpid": os.getpid(),
        "source_hashes": {
            str(PLANNED_PATH.relative_to(REPO)): sha256(PLANNED_PATH),
            str(FREEZE_PATH.relative_to(REPO)): sha256(FREEZE_PATH),
            str(PRE_RECEIPT_PATH.relative_to(REPO)): sha256(PRE_RECEIPT_PATH),
            str(FAULT_RECEIPT_PATH.relative_to(REPO)): sha256(FAULT_RECEIPT_PATH),
            str(TOKEN_RECEIPT_PATH.relative_to(REPO)): sha256(TOKEN_RECEIPT_PATH),
            str(INTERFACE_FAULT_PATH.relative_to(REPO)): sha256(
                INTERFACE_FAULT_PATH
            ),
            "research/word_scoring_new_family_20261027_v1/generation/local_loader.py": sha256(
                Path(__file__).with_name("local_loader.py")
            ),
        },
    }
    write_json(RUN_RECEIPT_PATH, receipt)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0 if receipt["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
