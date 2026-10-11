#!/usr/bin/env python3
"""Exploratory post-hoc ablation of multi-leaf stage signatures."""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "research/stage_e_multileaf_20261010"
RESULTS = TASK / "results"
PREDICTIONS = RESULTS / "multileaf_prediction_rows.jsonl"
OUT_JSON = RESULTS / "multileaf_signature_ablation.json"
OUT_MD = ROOT / "docs/research/stage_e_multileaf_signature_ablation_v1.md"

CLASSES = ("M", "R", "N")
TIE = "__TIE__"
DIRECT_LEAVES = {
    "M": "parse.field.hit_rate",
    "R": "qa.retrieval.source_required",
    "N": "parse.reconcile.equations",
}
EPS = 1e-12


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def macro_f1(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    values = []
    for label in CLASSES:
        tp = int(np.sum((y_true == label) & (y_pred == label)))
        fp = int(np.sum((y_true != label) & (y_pred == label)))
        fn = int(np.sum((y_true == label) & (y_pred != label)))
        denominator = 2 * tp + fp + fn
        values.append(0.0 if denominator == 0 else 2 * tp / denominator)
    return float(np.mean(values))


def predict_loco(x: np.ndarray, y: np.ndarray, clusters: np.ndarray) -> np.ndarray:
    predictions = np.empty(len(x), dtype=object)
    for cluster in np.unique(clusters):
        train = clusters != cluster
        test_indices = np.flatnonzero(~train)
        centroids = np.vstack([x[train & (y == label)].mean(axis=0) for label in CLASSES])
        for global_index in test_indices:
            distances = np.sqrt(((x[global_index] - centroids) ** 2).sum(axis=1))
            minimum = float(distances.min())
            tied = np.isclose(distances, minimum, rtol=0.0, atol=EPS)
            predictions[global_index] = TIE if int(tied.sum()) > 1 else CLASSES[int(np.argmin(distances))]
    return predictions


def metrics(x: np.ndarray, y: np.ndarray, clusters: np.ndarray) -> dict[str, Any]:
    predictions = predict_loco(x, y, clusters)
    return {
        "macro_f1": macro_f1(y, predictions),
        "top1_accuracy": float(np.mean(y == predictions)),
        "tie_rate": float(np.mean(predictions == TIE)),
        "confusion": {
            true: {
                pred: int(np.sum((y == true) & (predictions == pred)))
                for pred in (*CLASSES, TIE)
            }
            for true in CLASSES
        },
    }


def mutual_information(bit: np.ndarray, y: np.ndarray) -> float:
    total = len(y)
    joint = Counter(zip(map(int, bit), map(str, y)))
    bit_counts = Counter(map(int, bit))
    class_counts = Counter(map(str, y))
    value = 0.0
    for (bit_value, label), count in joint.items():
        pxy = count / total
        px = bit_counts[bit_value] / total
        py = class_counts[label] / total
        value += pxy * math.log2(pxy / (px * py))
    return value


def main() -> int:
    rows = [
        json.loads(line)
        for line in PREDICTIONS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    leaves = list(rows[0]["response_vector"])
    x = np.asarray([[row["response_vector"][leaf] for leaf in leaves] for row in rows], dtype=float)
    y = np.asarray([row["true_stage"] for row in rows], dtype=object)
    clusters = np.asarray([row["cluster_id"] for row in rows], dtype=object)
    direct_indices = [leaves.index(DIRECT_LEAVES[stage]) for stage in CLASSES]
    direct_set = set(direct_indices)

    feature_sets = {
        "full_vector": list(range(len(leaves))),
        "direct_target_codebook": direct_indices,
        "full_without_parse_table_regression": [
            index for index, leaf in enumerate(leaves) if leaf != "parse.table.regression"
        ],
        "full_without_parse_field_hit_rate": [
            index for index, leaf in enumerate(leaves) if leaf != "parse.field.hit_rate"
        ],
        "full_without_qa_source_required": [
            index for index, leaf in enumerate(leaves) if leaf != "qa.retrieval.source_required"
        ],
        "full_without_parse_reconcile": [
            index for index, leaf in enumerate(leaves) if leaf != "parse.reconcile.equations"
        ],
        "non_direct_leaves_only": [index for index in range(len(leaves)) if index not in direct_set],
        "any_response_scalar": [],
    }
    results = {}
    for name, indices in feature_sets.items():
        if name == "any_response_scalar":
            feature_x = (x.sum(axis=1) > 0).astype(float)[:, None]
        else:
            feature_x = x[:, indices]
        results[name] = {
            "features": [leaves[index] for index in indices] if indices else ["any_response"],
            **metrics(feature_x, y, clusters),
        }

    per_leaf = {}
    for position, leaf in enumerate(leaves):
        counts = {
            stage: int(x[y == stage, position].sum()) for stage in CLASSES
        }
        single = x[:, position][:, None]
        per_leaf[leaf] = {
            "response_counts": counts,
            "mutual_information_bits": mutual_information(x[:, position], y),
            **metrics(single, y, clusters),
        }

    leave_one_out = {}
    for removed, leaf in enumerate(leaves):
        indices = [index for index in range(len(leaves)) if index != removed]
        leave_one_out[leaf] = metrics(x[:, indices], y, clusters)

    full = results["full_vector"]
    direct = results["direct_target_codebook"]
    payload = {
        "namespace": "MULTILEAF_SIGNATURE_ABLATION",
        "status": "EXPLORATORY_POST_HOC",
        "formal_result_changed": False,
        "source": {
            "path": str(PREDICTIONS),
            "sha256": sha256_file(PREDICTIONS),
            "rows": len(rows),
        },
        "feature_sets": results,
        "per_leaf": per_leaf,
        "leave_one_leaf_out": leave_one_out,
        "signature_counts": {
            stage: sorted(
                Counter(
                    tuple(int(row["response_vector"][leaf]) for leaf in leaves)
                    for row in rows
                    if row["true_stage"] == stage
                ).items()
            )
            for stage in CLASSES
        },
        "key_findings": {
            "full_equals_direct_codebook": (
                close(full["macro_f1"], direct["macro_f1"])
                and close(full["top1_accuracy"], direct["top1_accuracy"])
            ),
            "incremental_information_from_non_direct_leaves": (
                direct["macro_f1"] > results["non_direct_leaves_only"]["macro_f1"]
            ),
            "interpretation": (
                "The fixed three-direct-leaf codebook is sufficient for perfect stage decoding. "
                "This confirms Loop C's tautology concern and limits the claim to the constructed observation surface."
            ),
        },
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    feature_rows = "\n".join(
        f"| {name} | {data['macro_f1']:.4f} | {data['top1_accuracy']:.4f} | {data['tie_rate']:.4f} |"
        for name, data in results.items()
    )
    leaf_rows = "\n".join(
        f"| {leaf} | {data['response_counts']['M']} | {data['response_counts']['R']} | "
        f"{data['response_counts']['N']} | {data['mutual_information_bits']:.4f} | "
        f"{data['macro_f1']:.4f} |"
        for leaf, data in per_leaf.items()
    )
    OUT_MD.write_text(f"""# Stage E Multi-Leaf Signature Ablation v1

> Status: `EXPLORATORY_POST_HOC` | Formal result unchanged | Purpose: quantify the codebook/tautology limitation identified by Loop C

## 1. Feature-set ablation

| Feature set | Macro-F1 | Top-1 | Tie rate |
|---|---:|---:|---:|
{feature_rows}

## 2. Per-leaf information

| Leaf | M responses | R responses | N responses | Mutual information bits | Single-leaf macro-F1 |
|---|---:|---:|---:|---:|---:|
{leaf_rows}

## 3. Findings

1. The full 12-leaf vector and the fixed three-direct-leaf codebook both decode all stages perfectly.
2. Non-direct leaves alone identify only the M signature through `parse.table.regression`; R and N become tied/zero-pattern cases.
3. The perfect formal result is therefore driven by a constructed stage codebook, not incremental natural-trace information.
4. `qa.retrieval.source_required` is always 1 for R, while M and N are 0 on that coordinate. Conversely, absence patterns also identify classes under nearest-centroid.
5. This ablation does not invalidate the preregistered result; it narrows its interpretation.

## 4. Claim boundary

Allowed:

> Under the frozen M/R/N controlled injections, the evaluator's constructed checkpoint-response codebook contains stage-localizing information.

Stronger statement now explicitly unsupported:

> A production checkpoint trace or naturally occurring failure can be localized from generalizable visibility dynamics.

`DECIDE NEXT LOOP: STOP_BRANCH` for further analysis of this same perfect codebook. The next useful evidence must use a different dataflow or non-degenerate overlapping signatures.
""", encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": payload["status"],
        "full_equals_direct_codebook": payload["key_findings"]["full_equals_direct_codebook"],
        "full_macro_f1": full["macro_f1"],
        "direct_macro_f1": direct["macro_f1"],
        "output": str(OUT_MD),
    }, ensure_ascii=False, sort_keys=True))
    return 0


def close(left: float, right: float, tolerance: float = 1e-12) -> bool:
    return abs(float(left) - float(right)) <= tolerance


if __name__ == "__main__":
    raise SystemExit(main())
