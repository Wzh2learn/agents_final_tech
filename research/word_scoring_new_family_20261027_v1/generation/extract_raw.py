"""Extract persisted D/T/M raw responses without loading a model."""

from __future__ import annotations

import hashlib
import json
import re
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
PLANNED_PATH = ROOT / "mechanism" / "PLANNED_PROMPTS.jsonl"
OUTPUT_PATH = ROOT / "generation" / "results" / "RAW_RESPONSES.jsonl"
RECEIPT_PATH = ROOT / "generation" / "results" / "RAW_EXTRACTION_RECEIPT.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    planned = {
        json.loads(line)["logical_call_id"]: json.loads(line)
        for line in PLANNED_PATH.read_text(encoding="utf-8").splitlines()
        if line
    }
    snapshot = PersistentLedger(LEDGER_PATH).snapshot_now()
    rows = []
    for raw in sorted(snapshot.raw_responses, key=lambda item: item["seq"]):
        logical = raw["logical_call_id"]
        match = re.fullmatch(r"(.*):retry-(\d+)", logical)
        prefix = match.group(1) if match else logical
        suffix = f":retry-{match.group(2)}" if match else ""
        planned_row = planned[prefix]
        rows.append(
            {
                "schema": "word_new_family_raw_response_row_v1",
                "physical_attempt_id": raw["physical_attempt_id"],
                "logical_call_id": logical,
                "base_logical_call_id": prefix,
                "retry_suffix": suffix,
                "arm": planned_row["arm"],
                "family_id": planned_row["family_id"],
                "question_uid": planned_row["question_uid"],
                "response_text": raw["response_text"],
                "response_sha256": raw["response_sha256"],
                "raw_event_sha256": raw["event_sha256"],
                "usage": raw["usage"],
                "persisted_at_unix": raw["persisted_at_unix"],
                "fsync_before_scoring": raw["fsync_before_scoring"],
            }
        )
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    receipt = {
        "schema": "word_new_family_raw_extraction_receipt_v1",
        "status": "COMPLETE" if len(rows) == 24 else "INCOMPLETE",
        "model_loaded": False,
        "raw_rows": len(rows),
        "arm_counts": {
            arm: sum(row["arm"] == arm for row in rows)
            for arm in ("D", "T", "M")
        },
        "actual_input_tokens": sum(row["usage"]["input_tokens"] for row in rows),
        "actual_output_tokens": sum(row["usage"]["output_tokens"] for row in rows),
        "actual_input_plus_output_tokens": sum(
            row["usage"]["input_tokens"] + row["usage"]["output_tokens"]
            for row in rows
        ),
        "ledger_path": str(LEDGER_PATH),
        "ledger_sha256": sha256(LEDGER_PATH),
        "output_path": str(OUTPUT_PATH.relative_to(REPO)),
        "output_sha256": sha256(OUTPUT_PATH),
        "training_runs": 0,
    }
    RECEIPT_PATH.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0 if receipt["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
