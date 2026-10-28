"""Preserve the first interface reservation as an explicit pre-model fault."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.adaptive_mechanism_20261027_v1.persistent_budget.ledger import (
    PersistentLedger,
)


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
LEDGER_PATH = Path(
    "/home/testuser/wzh/research_runs/persistent_budget/"
    "word_new_family_20261027/ledger.jsonl"
)
OUTPUT_PATH = ROOT / "generation" / "INTERFACE_FAULT_RECEIPT.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ledger = PersistentLedger(LEDGER_PATH)
    snapshot = ledger.snapshot_now()
    if not snapshot.uncertain_reservations:
        raise RuntimeError(
            "expected_at_least_one_uncertain_reservation"
        )
    faults = [
        {
            "logical_call_id": reservation["logical_call_id"],
            "physical_attempt_id": reservation["physical_attempt_id"],
            "reservation_event_sha256": reservation["event_sha256"],
            "failure": (
                "transformers_chat_template_returned_batch_encoding_without_tensor_shape"
                if index == 0
                else (
                    "reservation_upper_bound_used_as_tokenized_input_length"
                    if index == 1
                    else "model_stopped_without_complete_json_discarded_before_raw_append"
                )
            ),
            "failed_stage": (
                "tokenized_input_validation_before_model_weight_load"
                if index < 2
                else "loader_exception_after_model_generation_before_raw_append"
            ),
            "model_weights_loaded": index >= 2,
            "real_model_generate_calls": 1 if index >= 2 else 0,
            "actual_usage": None if index >= 2 else {
                "input_tokens": reservation["reserved_input_tokens"],
                "output_tokens": None,
            },
            "actual_usage_known": index < 2,
            "raw_response_persisted": False,
            "uncertain_reservation_consumed": True,
            "reserved_input_tokens": reservation["reserved_input_tokens"],
            "reserved_output_tokens": reservation["reserved_output_tokens"],
            "consumed_token_upper_bound": (
                reservation["reserved_input_tokens"]
                + reservation["reserved_output_tokens"]
            ),
        }
        for index, reservation in enumerate(snapshot.uncertain_reservations)
    ]
    receipt = {
        "schema": "word_new_family_interface_fault_receipt_v1",
        "status": "PRESERVED_INTERFACE_AND_MODEL_FAILURES",
        "run_id": "word-new-family-20261027-a",
        "fault_count": len(faults),
        "faults": faults,
        "model_weights_loaded": True,
        "real_model_generate_calls": sum(
            fault["real_model_generate_calls"] for fault in faults
        ),
        "raw_response_persisted": False,
        "uncertain_reservation_consumed": True,
        "consumed_token_upper_bound": sum(
            fault["consumed_token_upper_bound"] for fault in faults
        ),
        "repair": (
            "Use return_dict=True, reserve the exact input length plus 512, "
            "return every model response before scoring even when strict JSON "
            "is incomplete, and consume bounded retries with new logical_call_ids."
        ),
        "ledger_path": str(LEDGER_PATH),
        "ledger_sha256": sha256(LEDGER_PATH),
        "training_runs": 0,
    }
    OUTPUT_PATH.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
