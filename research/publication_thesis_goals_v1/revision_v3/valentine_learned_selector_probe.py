"""Nested pair-OOF probe for learned acceptance of B4 map_to predictions."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from scipy.sparse import hstack

from valentine_selective_mapping_probe import (
    apply_threshold,
    load_confidence,
    load_predictions,
    metrics,
    threshold_candidates,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_process_features(path: Path) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            grouped[str(row["sample_id"])].append(row)
    features = {}
    for sample_id, events in grouped.items():
        events.sort(key=lambda row: (int(row["turn"]), int(row["event_index"])))
        final_confidence: float | None = None
        candidate_target: str | None = None
        source_header = ""
        record_count = 0
        revoke_count = 0
        reasoning_present = False
        transformation_present = False
        raw_final_equal = False
        for event in events:
            kind = event.get("event_kind")
            reasoning_present |= bool(event.get("reasoning_present"))
            transformation_present |= bool(event.get("transformation_present"))
            raw_final_equal |= bool(event.get("raw_final_equal"))
            if kind == "record_candidate":
                record_count += 1
                value = event.get("confidence")
                final_confidence = float(value) if isinstance(value, (int, float)) else None
                target = event.get("target_header")
                candidate_target = target if isinstance(target, str) else None
                header = event.get("source_header")
                source_header = header if isinstance(header, str) else source_header
            elif kind == "revoke_candidate":
                revoke_count += 1
                final_confidence = None
                candidate_target = None
        features[sample_id] = {
            "final_confidence": final_confidence,
            "candidate_target": candidate_target,
            "source_header": source_header,
            "record_count": record_count,
            "revoke_count": revoke_count,
            "reasoning_present": reasoning_present,
            "transformation_present": transformation_present,
            "raw_final_equal": raw_final_equal,
        }
    return features


def feature_vector(
    row: dict[str, Any],
    process: dict[str, Any],
) -> list[float]:
    confidence = process.get("final_confidence")
    candidate_target = process.get("candidate_target")
    predicted_target = row.get("predicted_target")
    return [
        1.0 if confidence is None else float(confidence),
        1.0 if confidence is None else 0.0,
        1.0 if candidate_target is not None else 0.0,
        1.0 if candidate_target == predicted_target else 0.0,
        min(int(process.get("record_count", 0)), 5) / 5.0,
        min(int(process.get("revoke_count", 0)), 5) / 5.0,
        1.0 if process.get("reasoning_present") else 0.0,
        1.0 if process.get("transformation_present") else 0.0,
        1.0 if process.get("raw_final_equal") else 0.0,
        min(len(str(predicted_target or "")), 100) / 100.0,
    ]


def semantic_text(row: dict[str, Any], process: dict[str, Any]) -> str:
    return f"{process.get('source_header', '')}\n{process.get('candidate_target', '')}"


def target_label(row: dict[str, Any]) -> int:
    return int(row["gold_action"] == "map_to" and row["predicted_target"] == row["gold_target"])


def fit_predict(
    train: list[dict[str, Any]],
    test: list[dict[str, Any]],
) -> list[float]:
    if not train or not test:
        raise ValueError("empty train or test")
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=1)
    scaler = StandardScaler()
    x_train_text = vectorizer.fit_transform([row["semantic_text"] for row in train])
    x_train_numeric = scaler.fit_transform([row["feature_vector"] for row in train])
    x_train = hstack([x_train_text, x_train_numeric])
    y_train = [target_label(row) for row in train]
    if len(set(y_train)) < 2:
        probability = float(sum(y_train) / len(y_train)) if y_train else 0.0
        return [probability] * len(test)
    model = LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        solver="liblinear",
        random_state=20261023,
    )
    model.fit(x_train, y_train)
    x_test = hstack(
        [
            vectorizer.transform([row["semantic_text"] for row in test]),
            scaler.transform([row["feature_vector"] for row in test]),
        ]
    )
    return [float(value) for value in model.predict_proba(x_test)[:, 1]]


def score_rows(
    source_rows: list[dict[str, Any]],
    process_features: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for row in source_rows:
        sample_id = str(row["sample_id"])
        process = process_features.get(sample_id, {})
        rows.append(
            {
                **row,
                "confidence": process.get("final_confidence"),
                "feature_vector": feature_vector(row, process),
                "semantic_text": semantic_text(row, process),
            }
        )
    return rows


def choose_acceptance_threshold(
    rows: list[dict[str, Any]],
    risk_limit: float,
    target_floor: float,
) -> tuple[float, dict[str, Any]]:
    candidates = threshold_candidates([row["oof_score"] for row in rows])
    eligible = []
    for threshold in candidates:
        evaluated = [
            {
                **row,
                "predicted_action": (
                    "ABSTAIN"
                    if row["predicted_action"] == "map_to" and float(row["oof_score"]) < threshold
                    else row["predicted_action"]
                ),
                "predicted_target": (
                    None
                    if row["predicted_action"] == "map_to" and float(row["oof_score"]) < threshold
                    else row["predicted_target"]
                ),
                "abstained": bool(
                    row["predicted_action"] == "map_to" and float(row["oof_score"]) < threshold
                ),
            }
            for row in rows
        ]
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
        return 1.01, metrics(
            [
                {
                    **row,
                    "predicted_action": "ABSTAIN"
                    if row["predicted_action"] == "map_to"
                    else row["predicted_action"],
                    "predicted_target": None
                    if row["predicted_action"] == "map_to"
                    else row["predicted_target"],
                    "abstained": row["predicted_action"] == "map_to",
                }
                for row in rows
            ]
        )
    _coverage, _negative_threshold, threshold, result = max(eligible)
    return threshold, result


def evaluate_with_scores(
    rows: list[dict[str, Any]],
    score_key: str,
    threshold: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    evaluated = []
    for row in rows:
        accepted = row["predicted_action"] != "map_to" or float(row[score_key]) >= threshold
        evaluated.append(
            {
                **row,
                "predicted_action": row["predicted_action"] if accepted else "ABSTAIN",
                "predicted_target": row["predicted_target"] if accepted else None,
                "abstained": not accepted,
            }
        )
    return evaluated, metrics(evaluated)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary-predictions", type=Path, required=True)
    parser.add_argument("--checkpoint-events", type=Path, required=True)
    parser.add_argument("--risk-limit", type=float, default=0.10)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    primary = load_predictions(args.primary_predictions, "B4")
    process_features = load_process_features(args.checkpoint_events)
    rows = score_rows(list(primary.values()), process_features)
    unfiltered = metrics(
        [
            {**row, "abstained": False}
            for row in rows
        ]
    )
    target_floor = max(0.0, float(unfiltered["target_exact_gold_map_to"] or 0.0) - 0.02)
    pairs = sorted({str(row["pair_id"]) for row in rows})
    outer_rows = []
    outer_thresholds = []
    inner_summaries = []
    for held_out in pairs:
        outer_train = [row for row in rows if row["pair_id"] != held_out]
        inner_scores: dict[str, float] = {}
        for inner_held_out in sorted({str(row["pair_id"]) for row in outer_train}):
            inner_train = [
                row for row in outer_train if row["pair_id"] != inner_held_out
            ]
            inner_test = [
                row for row in outer_train if row["pair_id"] == inner_held_out
            ]
            probabilities = fit_predict(inner_train, inner_test)
            for row, score in zip(inner_test, probabilities, strict=True):
                inner_scores[str(row["sample_id"])] = score
        inner_rows = [{**row, "oof_score": inner_scores[str(row["sample_id"])]} for row in outer_train]
        threshold, train_metrics = choose_acceptance_threshold(
            inner_rows, args.risk_limit, target_floor
        )
        probabilities = fit_predict(
            outer_train,
            [row for row in rows if row["pair_id"] == held_out],
        )
        held_out_rows = [row for row in rows if row["pair_id"] == held_out]
        for row, score in zip(held_out_rows, probabilities, strict=True):
            outer_rows.append({**row, "oof_score": score, "oof_threshold": threshold})
        outer_thresholds.append(threshold)
        inner_summaries.append(
            {
                "held_out": held_out,
                "threshold": threshold,
                "inner_train_metrics": train_metrics,
            }
        )
    learned_evaluated = []
    for row in outer_rows:
        accepted = row["predicted_action"] != "map_to" or float(row["oof_score"]) >= float(
            row["oof_threshold"]
        )
        learned_evaluated.append(
            {
                **row,
                "predicted_action": row["predicted_action"] if accepted else "ABSTAIN",
                "predicted_target": row["predicted_target"] if accepted else None,
                "abstained": not accepted,
            }
        )
    learned_metrics = metrics(learned_evaluated)
    learned_curve = []
    for threshold in threshold_candidates([row["oof_score"] for row in outer_rows]):
        _curve_rows, curve_metrics = evaluate_with_scores(outer_rows, "oof_score", threshold)
        learned_curve.append({"threshold": threshold, "metrics": curve_metrics})
    per_pair_thresholds = []
    for held_out, threshold in zip(pairs, outer_thresholds, strict=True):
        pair_rows = [row for row in outer_rows if row["pair_id"] == held_out]
        _rows, pair_metrics = evaluate_with_scores(pair_rows, "oof_score", threshold)
        per_pair_thresholds.append({"pair_id": held_out, "threshold": threshold, "metrics": pair_metrics})
    payload = {
        "schema": "valentine_learned_selector_probe_v1",
        "date": "2026-10-23",
        "question": (
            "Can a tiny learned selector using only visible process features improve "
            "risk-constrained correct-map coverage over confidence thresholds?"
        ),
        "evidence_identity": "DEV_ONLY_NESTED_PAIR_OOF_LEARNED_ACCEPTANCE",
        "risk_limit": args.risk_limit,
        "target_exact_floor": target_floor,
        "inputs": {
            "primary_predictions_sha256": sha256_file(args.primary_predictions),
            "checkpoint_events_sha256": sha256_file(args.checkpoint_events),
        },
        "feature_contract": [
            "final visible confidence",
            "confidence missing flag",
            "candidate target presence",
            "candidate equals predicted target",
            "record/revoke counts",
            "reasoning/transformation/raw-final-equality flags",
            "predicted target length",
            "source header and candidate target character n-grams",
        ],
        "unfiltered_b4": unfiltered,
        "nested_pair_oof_selector": {
            "metrics": learned_metrics,
            "outer_thresholds": outer_thresholds,
            "per_pair_thresholds": per_pair_thresholds,
            "inner_summaries": inner_summaries,
            "risk_coverage_curve": learned_curve,
        },
        "decision_rule": (
            "Nested pair-OOF logistic acceptance model; each outer threshold is selected "
            "only from inner OOF scores of other pairs under the risk and target-exact floors."
        ),
        "nonclaims": [
            "This is a tiny development selector, not LoRA, a student model or a confirmatory result.",
            "The sealed Q3 labels are development references, not human gold or blind review.",
            "The probe must not use gold fields as input features.",
            "A positive result would justify a later student experiment only after an independent pair/source check.",
        ],
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
