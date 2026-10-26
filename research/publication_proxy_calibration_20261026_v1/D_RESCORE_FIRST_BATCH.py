#!/usr/bin/env python3
"""Build a compliant derived result from the first 40-call raw batch.

This script performs no model calls. It validates that the second batch has the
same scientific payload, then transfers only its derived score fields onto the
first immutable raw batch.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
FIRST_RAW = (
    ROOT
    / "raw"
    / "runs"
    / "failed_attempt_20261026"
    / "P2_GENERATIONS.partial_40.jsonl"
)
SECOND_ANNOTATED = ROOT / "raw" / "runs" / "primary" / "P2_GENERATIONS.jsonl"
SECOND_RESULTS = ROOT / "raw" / "runs" / "primary" / "P2_CALIBRATION_RESULTS.json"
OUT = ROOT / "raw" / "runs" / "compliant_primary"

ORIGINAL_FIELDS = (
    "actor_visibility",
    "arm",
    "cached_tokens",
    "call_id",
    "call_number",
    "complete_response",
    "input_tokens",
    "output_tokens",
    "parse_error",
    "parsed_response",
    "prompt_sha256",
    "question_uid_sha256",
    "retry_attempt",
    "retry_identity",
    "schema",
    "strict_parse_outcome",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> int:
    first = read_jsonl(FIRST_RAW)
    second = read_jsonl(SECOND_ANNOTATED)
    if len(first) != 40 or len(second) != 40:
        raise SystemExit("EXPECTED_40_ROWS_PER_BATCH")

    second_by_call = {row["call_id"]: row for row in second}
    if len(second_by_call) != 40:
        raise SystemExit("DUPLICATE_CALL_ID_IN_SECOND_BATCH")

    wall_changes = 0
    for old in first:
        new = second_by_call.get(old["call_id"])
        if new is None:
            raise SystemExit(f"CALL_ID_MISSING_IN_SECOND_BATCH:{old['call_id']}")
        for field in ORIGINAL_FIELDS:
            if old.get(field) != new.get(field):
                raise SystemExit(
                    f"SCIENTIFIC_PAYLOAD_MISMATCH:{old['call_id']}:{field}"
                )
        if old.get("wall_seconds") != new.get("wall_seconds"):
            wall_changes += 1

    if wall_changes == 0:
        raise SystemExit("EXPECTED_PHYSICAL_REPLAY_WALL_TIME_DIFFERENCE")

    annotated: list[dict[str, Any]] = []
    for old in first:
        new = second_by_call[old["call_id"]]
        row = dict(new)
        row.update({field: old[field] for field in ORIGINAL_FIELDS})
        row["wall_seconds"] = old["wall_seconds"]
        row["source_batch"] = "first_compliant_40"
        row["derived_from_quarantined_replication"] = True
        annotated.append(row)

    OUT.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FIRST_RAW, OUT / "P2_GENERATIONS.raw.jsonl")
    write_jsonl(OUT / "P2_GENERATIONS.annotated.jsonl", annotated)

    results = json.loads(SECOND_RESULTS.read_text(encoding="utf-8"))
    first_input = sum(int(row["input_tokens"]) for row in first)
    first_output = sum(int(row["output_tokens"]) for row in first)
    first_wall = sum(float(row["wall_seconds"]) for row in first)
    second_input = sum(int(row["input_tokens"]) for row in second)
    second_output = sum(int(row["output_tokens"]) for row in second)
    second_wall = sum(float(row["wall_seconds"]) for row in second)

    arm_wall: dict[str, float] = defaultdict(float)
    for row in first:
        arm_wall[row["arm"]] += float(row["wall_seconds"])
    for arm, summary in results["arms"].items():
        summary["wall_seconds_total"] = arm_wall[arm]

    results["raw_response_path"] = (
        "research/publication_proxy_calibration_20261026_v1/raw/runs/"
        "compliant_primary/P2_GENERATIONS.raw.jsonl"
    )
    results["raw_response_sha256"] = sha256(FIRST_RAW)
    results["annotated_derived_path"] = (
        "research/publication_proxy_calibration_20261026_v1/raw/runs/"
        "compliant_primary/P2_GENERATIONS.annotated.jsonl"
    )
    results["status"] = "COMPLETE_12_ITEM_DEVELOPMENT_PANEL_FIRST_BATCH_ONLY"
    results["ledger"].update(
        {
            "input_tokens_total": first_input,
            "output_tokens_total": first_output,
            "total_generation_tokens": first_output,
            "wall_seconds_total": first_wall,
            "compliant_primary_calls": 40,
            "quarantined_replication_calls": 40,
            "actual_physical_generation_calls": 80,
            "hard_generation_call_cap": 48,
            "call_cap_breach": 32,
            "second_batch_input_tokens": second_input,
            "second_batch_output_tokens": second_output,
            "second_batch_wall_seconds": second_wall,
            "accounting_disposition": (
                "FIRST_40_CALLS_ARE_THE_COMPLIANT_PRIMARY; SECOND_40_CALLS_"
                "ARE_A_QUARANTINED_DETERMINISTIC_REPLAY_AND_COUNT_TOWARD_"
                "PHYSICAL_BUDGET"
            ),
        }
    )
    results["derivation_identity"] = {
        "model_calls_in_this_recompute": 0,
        "first_raw_sha256": sha256(FIRST_RAW),
        "second_annotated_sha256": sha256(SECOND_ANNOTATED),
        "scientific_payload_fields_compared": list(ORIGINAL_FIELDS),
        "wall_time_fields_changed": wall_changes,
        "transfer_rule": (
            "Derived score fields are copied by call_id only after all original "
            "scientific payload fields match; first-batch wall_seconds is kept."
        ),
    }
    write_json(OUT / "P2_CALIBRATION_RESULTS.json", results)
    print(
        json.dumps(
            {
                "status": results["status"],
                "first_raw_sha256": sha256(FIRST_RAW),
                "second_annotated_sha256": sha256(SECOND_ANNOTATED),
                "wall_changes": wall_changes,
                "actual_physical_generation_calls": 80,
                "compliant_primary_calls": 40,
                "model_calls_in_recompute": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
