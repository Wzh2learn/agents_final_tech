"""Zero-training risk-coverage qualification for selective map_to decisions."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_predictions(path: Path, baseline: str) -> dict[str, dict[str, Any]]:
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("baseline") != baseline:
            continue
        sample_id = str(row["sample_id"])
        if sample_id in rows:
            raise ValueError(f"duplicate_prediction:{sample_id}")
        rows[sample_id] = row
    return rows


def load_confidence(path: Path) -> dict[str, float | None]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        grouped[str(row["sample_id"])].append(row)
    confidence = {}
    for sample_id, events in grouped.items():
        events.sort(key=lambda row: (int(row["turn"]), int(row["event_index"])))
        state: float | None = None
        for event in events:
            kind = event.get("event_kind")
            if kind == "record_candidate":
                value = event.get("confidence")
                state = float(value) if isinstance(value, (int, float)) else None
            elif kind == "revoke_candidate":
                state = None
        confidence[sample_id] = state
    return confidence


def apply_threshold(
    row: dict[str, Any],
    confidence: float | None,
    threshold: float,
) -> dict[str, Any]:
    predicted_action = str(row["predicted_action"])
    if predicted_action == "map_to" and (confidence is None or confidence < threshold):
        return {
            "sample_id": row["sample_id"],
            "pair_id": row["pair_id"],
            "gold_action": row["gold_action"],
            "gold_target": row["gold_target"],
            "predicted_action": "ABSTAIN",
            "predicted_target": None,
            "confidence": confidence,
            "abstained": True,
        }
    return {
        "sample_id": row["sample_id"],
        "pair_id": row["pair_id"],
        "gold_action": row["gold_action"],
        "gold_target": row["gold_target"],
        "predicted_action": predicted_action,
        "predicted_target": row["predicted_target"],
        "confidence": confidence,
        "abstained": False,
    }


def metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [row for row in rows if not row["abstained"]]
    accepted_maps = [row for row in scored if row["predicted_action"] == "map_to"]
    correct_maps = [
        row
        for row in accepted_maps
        if row["gold_action"] == "map_to" and row["predicted_target"] == row["gold_target"]
    ]
    harmful_maps = [
        row
        for row in accepted_maps
        if row["gold_action"] != "map_to" or row["predicted_target"] != row["gold_target"]
    ]
    gold_maps = [row for row in rows if row["gold_action"] == "map_to"]
    return {
        "row_count": len(rows),
        "scored_row_count": len(scored),
        "abstained_row_count": len(rows) - len(scored),
        "accepted_map_count": len(accepted_maps),
        "correct_map_count": len(correct_maps),
        "harmful_map_count": len(harmful_maps),
        "map_to_risk": len(harmful_maps) / len(accepted_maps) if accepted_maps else None,
        "harmful_map_rate_all_scored": len(harmful_maps) / len(scored) if scored else None,
        "correct_map_coverage_all_rows": len(correct_maps) / len(rows) if rows else None,
        "target_exact_gold_map_to": len(correct_maps) / len(gold_maps) if gold_maps else None,
        "target_exact_accepted_map_to": len(correct_maps) / len(accepted_maps) if accepted_maps else None,
    }


def threshold_candidates(values: list[float | None]) -> list[float]:
    finite = sorted({float(value) for value in values if value is not None})
    return [0.0, *finite, 1.01]


def choose_threshold(
    rows: list[dict[str, Any]],
    risk_limit: float,
    target_floor: float,
) -> tuple[float, dict[str, Any]]:
    candidates = threshold_candidates([row["confidence"] for row in rows])
    eligible = []
    for threshold in candidates:
        evaluated = [apply_threshold(row, row["confidence"], threshold) for row in rows]
        result = metrics(evaluated)
        if (
            result["map_to_risk"] is not None
            and result["map_to_risk"] <= risk_limit
            and result["target_exact_gold_map_to"] is not None
            and result["target_exact_gold_map_to"] >= target_floor
        ):
            eligible.append(
                (
                    float(result["correct_map_coverage_all_rows"] or 0.0),
                    -threshold,
                    threshold,
                    result,
                )
            )
    if not eligible:
        return 1.01, metrics([apply_threshold(row, row["confidence"], 1.01) for row in rows])
    _coverage, _negative_threshold, threshold, result = max(eligible)
    return threshold, result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary-predictions", type=Path, required=True)
    parser.add_argument("--salted-predictions", type=Path, required=True)
    parser.add_argument("--checkpoint-events", type=Path, required=True)
    parser.add_argument("--risk-limit", type=float, default=0.10)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    primary_rows = load_predictions(args.primary_predictions, "B4")
    salted_rows = load_predictions(args.salted_predictions, "B4")
    confidence = load_confidence(args.checkpoint_events)
    primary_pairs = sorted({row["pair_id"] for row in primary_rows.values()})
    primary_list = list(primary_rows.values())
    unfiltered = metrics(
        [apply_threshold(row, confidence.get(str(row["sample_id"]), None), 0.0) for row in primary_list]
    )
    target_floor = max(
        0.0,
        float(unfiltered["target_exact_gold_map_to"] or 0.0) - 0.02,
    )
    oof_rows = []
    selected_thresholds = []
    inner_train_metrics = []
    for held_out in primary_pairs:
        train = [
            {**row, "confidence": confidence.get(str(row["sample_id"]))}
            for row in primary_list
            if row["pair_id"] != held_out
        ]
        threshold, train_result = choose_threshold(
            train, args.risk_limit, target_floor
        )
        selected_thresholds.append(threshold)
        inner_train_metrics.append({"held_out": held_out, "threshold": threshold, "metrics": train_result})
        for row in primary_list:
            if row["pair_id"] == held_out:
                oof_rows.append(
                    apply_threshold(
                        row,
                        confidence.get(str(row["sample_id"]), None),
                        threshold,
                    )
                )
    oof_metrics = metrics(oof_rows)
    median_threshold = sorted(selected_thresholds)[len(selected_thresholds) // 2]
    salted_evaluated = [
        apply_threshold(row, confidence.get(str(row["sample_id"]), None), median_threshold)
        for row in salted_rows.values()
    ]
    salted_metrics = metrics(salted_evaluated)
    curve = []
    for threshold in threshold_candidates(list(confidence.values())):
        evaluated = [
            apply_threshold(row, confidence.get(str(row["sample_id"]), None), threshold)
            for row in primary_list
        ]
        curve.append({"threshold": threshold, "metrics": metrics(evaluated)})
    payload = {
        "schema": "valentine_selective_mapping_probe_v1",
        "date": "2026-10-23",
        "question": (
            "Can visible process confidence gate B4 map_to decisions to improve "
            "correct-map coverage under a harmful-map risk limit without training?"
        ),
        "evidence_identity": "DEV_ONLY_OOF_SELECTIVE_MAPPING_WITH_SEALED_Q3_REFERENCE",
        "risk_limit": args.risk_limit,
        "target_exact_floor": target_floor,
        "inputs": {
            "primary_predictions": {
                "path": str(args.primary_predictions),
                "sha256": sha256_file(args.primary_predictions),
            },
            "salted_predictions": {
                "path": str(args.salted_predictions),
                "sha256": sha256_file(args.salted_predictions),
            },
            "checkpoint_events": {
                "path": str(args.checkpoint_events),
                "sha256": sha256_file(args.checkpoint_events),
            },
        },
        "unfiltered_b4": unfiltered,
        "oof_confidence_gated_b4": {
            "metrics": oof_metrics,
            "selected_thresholds": selected_thresholds,
            "inner_train_metrics": inner_train_metrics,
        },
        "salted_sensitivity": {
            "median_threshold_from_primary_oof": median_threshold,
            "metrics": salted_metrics,
        },
        "primary_risk_coverage_curve": curve,
        "decision_rule": (
            "For each held-out pair, select the threshold on all other pairs that "
            "maximizes correct-map coverage subject to empirical map_to_risk <= limit "
            "and target_exact_gold_map_to >= unfiltered B4 minus 0.02; ties use the "
            "higher threshold. Missing confidence forces abstention for map_to."
        ),
        "nonclaims": [
            "This is a development risk-coverage probe over 10 pairs, not a confirmatory estimate.",
            "The Q3 labels are sealed expert-adjudicated development references, not human gold or blind review.",
            "Confidence gating tests a transparent selective rule; it does not train or justify a student model.",
            "The salted slice contains only two test pairs and is a sensitivity check.",
        ],
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
