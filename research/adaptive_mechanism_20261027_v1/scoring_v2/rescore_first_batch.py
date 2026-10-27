#!/usr/bin/env python3
"""Rescore exactly the final attempt of every UID x arm in the first 40 calls."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from scorer import ARMS, load_source_records, load_visible_context, score_response


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
HISTORICAL_ROOT = (
    REPOSITORY_ROOT
    / "research"
    / "publication_proxy_calibration_20261026_v1"
)
DEFAULT_RAW = HISTORICAL_ROOT / "raw/runs/compliant_primary/P2_GENERATIONS.raw.jsonl"
DEFAULT_ANNOTATED = HISTORICAL_ROOT / "raw/runs/compliant_primary/P2_GENERATIONS.annotated.jsonl"
DEFAULT_REFERENCE = HISTORICAL_ROOT / "p2_proxy_calibration/receipts/P2_REFERENCE_CHAIN.json"
DEFAULT_SOURCE = Path(
    "/home/testuser/wzh/projects/agents_final_tech/data/research/"
    "tatqa_raw_2026/tatqa_dataset_dev.json"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--annotated", type=Path, default=DEFAULT_ANNOTATED)
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    raw_rows = read_jsonl(args.raw)
    if len(raw_rows) != 40:
        raise SystemExit(f"expected_exactly_40_first_batch_rows:{len(raw_rows)}")
    references_payload = json.loads(args.reference.read_text(encoding="utf-8"))
    references = references_payload["rows"]
    if len(references) != 12:
        raise SystemExit(f"expected_12_reference_rows:{len(references)}")
    source_records = load_source_records(args.source)
    uid_by_hash = {
        hashlib.sha256(row["question_uid"].encode("utf-8")).hexdigest(): row["question_uid"]
        for row in references
    }
    reference_by_uid = {row["question_uid"]: row for row in references}
    annotated_by_call = {
        row["call_id"]: row for row in read_jsonl(args.annotated)
    }

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in raw_rows:
        uid_hash = row["question_uid_sha256"]
        if uid_hash not in uid_by_hash:
            raise SystemExit(f"unknown_question_uid_hash:{uid_hash}")
        grouped[(uid_hash, row["arm"])].append(row)
    if len(grouped) != 36:
        raise SystemExit(f"expected_36_uid_arm_groups:{len(grouped)}")

    selected: list[dict[str, Any]] = []
    for (uid_hash, arm), attempts in sorted(grouped.items()):
        if arm not in ARMS:
            raise SystemExit(f"unknown_arm:{arm}")
        final_attempt = max(attempts, key=lambda item: int(item["call_number"]))
        selected.append({**final_attempt, "question_uid": uid_by_hash[uid_hash]})

    rows: list[dict[str, Any]] = []
    for raw in sorted(selected, key=lambda item: (item["question_uid"], item["arm"])):
        reference = reference_by_uid[raw["question_uid"]]
        visible = load_visible_context(
            source_records[reference["table_uid"]],
            reference,
            raw.get("selected_paragraph_orders", [])
            if "selected_paragraph_orders" in raw
            else annotated_by_call[raw["call_id"]]["selected_paragraph_orders"],
        )
        result = score_response(raw["complete_response"], reference, visible)
        old = annotated_by_call[raw["call_id"]]
        rows.append(
            {
                "schema": "scoring_v2_first_batch_row_v1",
                "question_uid": raw["question_uid"],
                "question_uid_sha256": raw["question_uid_sha256"],
                "arm": raw["arm"],
                "call_id": raw["call_id"],
                "call_number": raw["call_number"],
                "retry_attempt": raw["retry_attempt"],
                "question": reference["question"],
                "answer_type": reference["answer_type"],
                "source_requirement": reference["source_requirement"],
                "visible_paragraph_orders": sorted(visible.raw_orders, key=int),
                "strict_parse_outcome_historical": raw["strict_parse_outcome"],
                "historical_semantic_outcome": old["semantic_outcome"],
                "historical_semantic_reason": old["semantic_reason"],
                "scoring_v2_status": result["status"],
                "scoring_v2_layers": result["layers"],
                "expected_reference_reconstruction": result["expected_reference_reconstruction"],
                "input_tokens": raw["input_tokens"],
                "output_tokens": raw["output_tokens"],
                "cached_tokens": raw["cached_tokens"],
                "wall_seconds": raw["wall_seconds"],
            }
        )

    by_arm: dict[str, dict[str, Any]] = {}
    for arm in ARMS:
        arm_rows = [row for row in rows if row["arm"] == arm]
        by_arm[arm] = {
            "items": len(arm_rows),
            "scoring_v2_outcomes": dict(sorted(Counter(row["scoring_v2_status"] for row in arm_rows).items())),
            "historical_outcomes": dict(sorted(Counter(row["historical_semantic_outcome"] for row in arm_rows).items())),
            "input_tokens_final_attempts": sum(row["input_tokens"] for row in arm_rows),
            "output_tokens_final_attempts": sum(row["output_tokens"] for row in arm_rows),
            "wall_seconds_final_attempts": sum(row["wall_seconds"] for row in arm_rows),
        }
    by_arm["table_top5_minus_table_top3_input_delta"] = (
        by_arm["table_top5"]["input_tokens_final_attempts"]
        - by_arm["table_top3"]["input_tokens_final_attempts"]
    )
    by_arm["table_all_minus_table_top5_input_delta"] = (
        by_arm["table_all"]["input_tokens_final_attempts"]
        - by_arm["table_top5"]["input_tokens_final_attempts"]
    )
    if by_arm["table_top5_minus_table_top3_input_delta"] != 917:
        raise SystemExit("top5_minus_top3_input_delta_not_917")
    if by_arm["table_all_minus_table_top5_input_delta"] != 1604:
        raise SystemExit("all_minus_top5_input_delta_not_1604")

    layer_counts: dict[str, dict[str, Counter[str]]] = {
        layer: {arm: Counter() for arm in ARMS}
        for layer in ("strict", "answer", "numeric_unit", "evidence", "final_delivery")
    }
    for row in rows:
        for layer, counts in layer_counts.items():
            counts[row["arm"]][row["scoring_v2_layers"][layer]["status"]] += 1

    per_uid: list[dict[str, Any]] = []
    grouped_uid: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped_uid[row["question_uid"]][row["arm"]] = row
    for uid in sorted(grouped_uid):
        arm_rows = grouped_uid[uid]
        reference = reference_by_uid[uid]
        per_uid.append(
            {
                "question_uid": uid,
                "question": reference["question"],
                "answer_type": reference["answer_type"],
                "historical_by_arm": {
                    arm: arm_rows[arm]["historical_semantic_outcome"] for arm in ARMS
                },
                "scoring_v2_by_arm": {
                    arm: arm_rows[arm]["scoring_v2_status"] for arm in ARMS
                },
                "scoring_v2_layer_statuses_by_arm": {
                    arm: {
                        layer: arm_rows[arm]["scoring_v2_layers"][layer]["status"]
                        for layer in ("strict", "answer", "numeric_unit", "evidence", "final_delivery")
                    }
                    for arm in ARMS
                },
            }
        )

    payload = {
        "schema": "scoring_v2_first_batch_rescore_v1",
        "status": "COMPLETE_ZERO_MODEL_FIRST_BATCH_36_PRIMARY_FINAL_ATTEMPTS",
        "review_identity": (
            "AI/automatic scoring-v2 development reanalysis; not human gold, "
            "not a preregistered score, and not a complete semantic oracle"
        ),
        "model_calls_in_rescore": 0,
        "generation_records_created": 0,
        "selection_rule": "maximum call_number within each question_uid_sha256 x arm from the immutable first 40-call batch",
        "first_batch_call_count": len(raw_rows),
        "primary_final_attempt_count": len(rows),
        "source_hashes": {
            "raw_jsonl": sha256(args.raw),
            "annotated_jsonl": sha256(args.annotated),
            "reference_chain": sha256(args.reference),
            "tatqa_dev_source": sha256(args.source),
        },
        "historical_score_visible": {
            "table_top3_ACCEPT": 2,
            "table_top5_ACCEPT": 3,
            "table_all_ACCEPT": 3,
            "identity": "historical old scorer; retained without reinterpretation",
        },
        "corrected_final_attempt_input_deltas": {
            "table_top5_minus_table_top3": 917,
            "table_all_minus_table_top5": 1604,
        },
        "per_layer_counts": {
            layer: {arm: dict(sorted(counts.items())) for arm, counts in arm_counts.items()}
            for layer, arm_counts in layer_counts.items()
        },
        "paired_arm_summaries": by_arm,
        "per_uid_outcomes": per_uid,
        "status_semantics": {
            "ACCEPT": "all five layers pass",
            "REJECT": "at least one determinative layer fails",
            "PENDING_ADJUDICATION": "a legal reference, role binding, or visible scale cannot be resolved without inventing evidence",
            "STRICT_FAIL": "JSON/schema/format/output contract fails before semantic acceptance",
            "REASONABLE_UNKNOWN": "required evidence is not visible and the actor correctly declared unknown",
        },
        "claim_boundary": (
            "Development reanalysis of one immutable 12-UID panel; no model, "
            "training, judge, production probe, human-gold claim, or new-source validation."
        ),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output / "FIRST_BATCH_ROWS_V2.jsonl", rows)
    write_json(args.output / "FIRST_BATCH_RESCORE_V2.json", payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "rows": len(rows),
                "model_calls": 0,
                "outcomes": by_arm,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
