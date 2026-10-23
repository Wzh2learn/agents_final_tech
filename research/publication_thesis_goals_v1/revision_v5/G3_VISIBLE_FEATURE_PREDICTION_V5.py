"""Diagnose whether useful evidence expansion is predictable from visible cues."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier


FEATURES = (
    "query_token_coverage",
    "rank3_to_rank1_score_ratio",
    "has_past_cue",
    "has_update_cue",
    "score_tail",
    "temporal_gap",
)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def cost_matched_threshold(scores: list[float], rate: float) -> float:
    """Return a threshold that expands at most the requested fraction."""
    if not scores:
        return float("inf")
    count = min(len(scores), max(1, int(round(len(scores) * rate))))
    ordered = sorted(scores, reverse=True)
    return ordered[count - 1]


def prediction_metrics(
    useful: list[bool],
    predicted: list[bool],
    costs: list[float],
) -> dict[str, Any]:
    true_positive = sum(bool(u) and bool(p) for u, p in zip(useful, predicted))
    false_positive = sum(not bool(u) and bool(p) for u, p in zip(useful, predicted))
    false_negative = sum(bool(u) and not bool(p) for u, p in zip(useful, predicted))
    expansion_count = sum(bool(p) for p in predicted)
    return {
        "items": len(useful),
        "useful_count": sum(bool(u) for u in useful),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "expansion_count": expansion_count,
        "precision": round(true_positive / expansion_count, 4) if expansion_count else 0.0,
        "recall": round(true_positive / sum(bool(u) for u in useful), 4) if any(useful) else 0.0,
        "predicted_expansion_cost_chars": round(
            sum(cost for cost, pred in zip(costs, predicted) if pred), 2
        ),
    }


def rows_from_results(results: dict[str, Any]) -> list[dict[str, Any]]:
    policy_rows = {
        policy: {
            row["uid"]: row for row in results["rows"] if row["policy"] == policy
        }
        for policy in ("keep_top3", "always_expand_top5", "visible_gap_rule")
    }
    uids = sorted(policy_rows["visible_gap_rule"])
    rows = []
    for uid in uids:
        visible = policy_rows["visible_gap_rule"][uid]
        keep = policy_rows["keep_top3"][uid]
        expand = policy_rows["always_expand_top5"][uid]
        features = visible["diagnostics"]
        rows.append({
            "uid": uid,
            "type": visible["type"],
            "target_useful_expansion": bool(visible["expansion_value"]["useful_expansion"]),
            "features": {feature: features[feature] for feature in FEATURES},
            "incremental_context_chars": float(expand["context_chars"] - keep["context_chars"]),
            "visible_rule_prediction": visible["action"] == "EXPAND",
        })
    return rows


def build_matrices(rows: list[dict[str, Any]]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = np.asarray([
        [float(row["features"][feature]) for feature in FEATURES]
        for row in rows
    ], dtype=float)
    y = np.asarray([row["target_useful_expansion"] for row in rows], dtype=int)
    cost = np.asarray([row["incremental_context_chars"] for row in rows], dtype=float)
    return x, y, cost


def model_factory(name: str) -> Any:
    if name == "logistic_regression":
        return make_pipeline(
            StandardScaler(),
            LogisticRegression(
                class_weight="balanced", max_iter=2000, random_state=0
            ),
        )
    if name == "decision_tree_depth2":
        return DecisionTreeClassifier(
            max_depth=2,
            min_samples_leaf=20,
            class_weight="balanced",
            random_state=0,
        )
    raise ValueError(name)


def repeated_predictions(
    x: np.ndarray,
    y: np.ndarray,
    model_name: str,
    repetitions: int = 5,
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    score_sum = np.zeros(len(y), dtype=float)
    counts = np.zeros(len(y), dtype=int)
    folds = []
    for seed in range(repetitions):
        outer = StratifiedKFold(n_splits=5, shuffle=True, random_state=100 + seed)
        for fold, (train, test) in enumerate(outer.split(x, y)):
            inner = StratifiedKFold(n_splits=3, shuffle=True, random_state=1000 + seed * 10 + fold)
            inner_model = model_factory(model_name)
            inner_scores = cross_val_predict(
                inner_model, x[train], y[train], cv=inner, method="predict_proba"
            )[:, 1]
            threshold = cost_matched_threshold(inner_scores.tolist(), rate=0.10)
            model = model_factory(model_name)
            model.fit(x[train], y[train])
            test_scores = model.predict_proba(x[test])[:, 1]
            score_sum[test] += test_scores
            counts[test] += 1
            folds.append({
                "seed": seed,
                "fold": fold,
                "train_items": len(train),
                "test_items": len(test),
                "threshold": float(threshold),
                "train_useful": int(y[train].sum()),
                "test_useful": int(y[test].sum()),
            })
    return score_sum / np.maximum(counts, 1), folds


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    protocol = load(args.protocol)
    if protocol.get("status") != "FROZEN_BEFORE_OFFLINE_FITTING":
        raise ValueError("protocol_not_frozen")
    rows = rows_from_results(load(args.results))
    x, y, costs = build_matrices(rows)
    useful = y.astype(bool).tolist()
    baselines = {
        "never_expand": prediction_metrics(useful, [False] * len(rows), costs),
        "always_expand_top5": prediction_metrics(useful, [True] * len(rows), costs),
        "visible_gap_rule": prediction_metrics(
            useful, [row["visible_rule_prediction"] for row in rows], costs
        ),
    }
    models = {}
    for model_name in ("logistic_regression", "decision_tree_depth2"):
        scores, folds = repeated_predictions(x, y, model_name)
        threshold = cost_matched_threshold(scores.tolist(), rate=0.10)
        predicted = scores >= threshold
        models[model_name] = {
            "metrics": prediction_metrics(useful, predicted.tolist(), costs),
            "global_cost_matched_threshold": float(threshold),
            "fold_receipts": folds,
            "mean_score_useful": float(scores[y == 1].mean()) if any(y == 1) else None,
            "mean_score_nonuseful": float(scores[y == 0].mean()) if any(y == 0) else None,
        }
    output = {
        "schema": "g3_visible_feature_prediction_results_v5",
        "date": "2026-10-23",
        "evidence_identity": protocol["evidence_identity"],
        "protocol_sha256": __import__("hashlib").sha256(args.protocol.read_bytes()).hexdigest(),
        "summary": {
            "items": len(rows),
            "useful_expansions": int(y.sum()),
            "feature_names": list(FEATURES),
            "baselines": baselines,
            "models": models,
        },
        "rows": rows,
        "nonclaims": protocol["nonclaims"],
    }
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(output["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
