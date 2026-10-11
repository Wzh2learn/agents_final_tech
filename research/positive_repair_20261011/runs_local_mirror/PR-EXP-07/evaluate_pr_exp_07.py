#!/usr/bin/env python3
"""Run the frozen PR-EXP-07 extraction, proof, and evaluation pipeline."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from extract_features import extract_all
from extractor import DIRECT_LEAVES, FEATURE_SETS, LEAF_ORDER, NON_DIRECT_LEAVES, extract


CLASSES = ("M", "R", "N")
TIE_LABEL = "__TIE__"
EPS = 1e-12
CHANCE = 1.0 / 3.0
MARGIN = 0.05
SHUFFLED_LABEL_SEED = 2026101108
BOOTSTRAP_SEED = 20261012
BOOTSTRAP_REPLICATES = 10000
EXPECTED_ROWS = 216
EXPECTED_CLUSTERS = 72
FORBIDDEN_EXTRACTOR_TOKENS = (
    "expected_first_stage",
    "target_checkpoint",
    "response_vector",
    "sample_id",
    "namespace",
    "generation_code",
    "gold_outcome",
    "stage_label",
)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def predict_loco(x: np.ndarray, y: np.ndarray, clusters: np.ndarray) -> np.ndarray:
    predictions = np.empty(len(x), dtype=object)
    for cluster in np.unique(clusters):
        train_mask = clusters != cluster
        test_indices = np.flatnonzero(~train_mask)
        centroids = np.vstack(
            [x[train_mask & (y == label)].mean(axis=0) for label in CLASSES]
        )
        test_x = x[test_indices]
        distances = np.sqrt(((test_x[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2))
        for row, global_index in zip(distances, test_indices):
            minimum = float(row.min())
            tied = np.isclose(row, minimum, rtol=0.0, atol=EPS)
            if int(tied.sum()) > 1:
                predictions[global_index] = TIE_LABEL
            else:
                predictions[global_index] = CLASSES[int(np.argmin(row))]
    return predictions


def macro_f1(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    scores = []
    for label in CLASSES:
        tp = int(np.sum((y_true == label) & (y_pred == label)))
        fp = int(np.sum((y_true != label) & (y_pred == label)))
        fn = int(np.sum((y_true == label) & (y_pred != label)))
        denominator = 2 * tp + fp + fn
        scores.append(0.0 if denominator == 0 else (2 * tp) / denominator)
    return float(np.mean(scores))


def metric_payload(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    per_class = {}
    for label in CLASSES:
        tp = int(np.sum((y_true == label) & (y_pred == label)))
        fp = int(np.sum((y_true != label) & (y_pred == label)))
        fn = int(np.sum((y_true == label) & (y_pred != label)))
        numerator = 2 * tp
        denominator = 2 * tp + fp + fn
        per_class[label] = {
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "f1_numerator": numerator,
            "f1_denominator": denominator,
            "f1": 0.0 if denominator == 0 else numerator / denominator,
        }
    correct = int(np.sum(y_true == y_pred))
    return {
        "macro_f1": macro_f1(y_true, y_pred),
        "macro_f1_sum_numerator": sum(item["f1_numerator"] for item in per_class.values()),
        "macro_f1_sum_denominator": sum(item["f1_denominator"] for item in per_class.values()),
        "macro_f1_aggregation": "arithmetic mean of the three per-class F1 fractions",
        "macro_f1_components": per_class,
        "top1_correct": correct,
        "top1_total": len(y_true),
        "top1_accuracy": correct / len(y_true),
        "tie_count": int(np.sum(y_pred == TIE_LABEL)),
        "confusion": {
            true: {
                pred: int(np.sum((y_true == true) & (y_pred == pred)))
                for pred in (*CLASSES, TIE_LABEL)
            }
            for true in CLASSES
        },
    }


def bootstrap_metric(
    y: np.ndarray,
    predictions: np.ndarray,
    clusters: np.ndarray,
    rng: np.random.Generator,
) -> float:
    unique_clusters = np.unique(clusters)
    sampled = rng.choice(unique_clusters, size=len(unique_clusters), replace=True)
    indices = np.concatenate([np.flatnonzero(clusters == cluster) for cluster in sampled])
    return macro_f1(y[indices], predictions[indices])


def classify(full: float, direct: float, non_direct: float, proof_status: str, qualification_status: str) -> tuple[str, str]:
    if qualification_status != "PASS":
        return "NOT_EVALUABLE", qualification_status
    if proof_status != "PASS":
        return "INVALID", "swap-invariance or pairing proof failed"
    if full - direct >= MARGIN and non_direct >= CHANCE + MARGIN:
        return "ROBUST", "both frozen ROBUST margins satisfied"
    if full <= direct:
        return "NULL", "binding full <= direct rule"
    if abs(full - CHANCE) <= MARGIN:
        return "NULL_AT_CHANCE", "full point is within 0.05 of chance"
    if non_direct <= CHANCE + MARGIN:
        return "NULL_DIRECT_CONCENTRATED", "non-direct point does not clear chance plus 0.05"
    return "NOT_EVALUABLE", "frozen taxonomy has no disjoint terminal bucket for this residual region"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--paired", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--formal-result", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--frozen-inputs", type=Path, required=True)
    args = parser.parse_args()

    start_utc = now_utc()
    frozen = json.loads(args.frozen_inputs.read_text(encoding="utf-8"))
    for record in frozen["code_and_definitions"]:
        path = args.work_dir / record["path"]
        if not path.exists() or sha256_file(path) != record["sha256"]:
            raise RuntimeError(f"frozen artifact hash mismatch: {record['path']}")
    for record in frozen["scientific_inputs"]:
        path = Path(record["path"])
        if not path.exists() or sha256_file(path) != record["sha256"]:
            raise RuntimeError(f"scientific input hash mismatch: {record['path']}")
    if sha256_file(args.contract) != frozen["implementation_contract_sha256"]:
        raise RuntimeError("implementation contract hash mismatch")

    feature_path = args.work_dir / "feature_values.jsonl"
    extraction_proof_path = args.work_dir / "extraction_proof.json"
    swap_proof_path = args.work_dir / "swap_invariance_proof.json"
    for path in (feature_path, extraction_proof_path, swap_proof_path):
        if path.exists():
            raise FileExistsError(f"observation output already exists: {path}")

    source_rows = read_jsonl(args.paired)
    feature_records, extraction_proof = extract_all(args.paired)

    with feature_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in feature_records:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")

    extractor_source = (args.work_dir / "extractor.py").read_text(encoding="utf-8").lower()
    pair_source = (args.work_dir / "extract_features.py").read_text(encoding="utf-8").lower()
    forbidden_fields_accessed = sorted(
        {
            token
            for token in FORBIDDEN_EXTRACTOR_TOKENS
            if token in extractor_source or token in pair_source
        }
    )
    extraction_proof.update(
        {
            "status": "PASS" if not forbidden_fields_accessed else "FAIL",
            "forbidden_fields_accessed": forbidden_fields_accessed,
        }
    )
    write_json(extraction_proof_path, extraction_proof)

    swap_failures = []
    for row_index, row in enumerate(source_rows):
        first = extract((row["baseline_scores"], row["injected_scores"]))
        second = extract((row["injected_scores"], row["baseline_scores"]))
        if first != second:
            swap_failures.append({"row_index": row_index, "feature_count": len(first)})
    swap_proof = {
        "status": "PASS" if not swap_failures and len(feature_records) == len(source_rows) else "FAIL",
        "rows_tested": len(source_rows),
        "rows_passed": len(source_rows) - len(swap_failures),
        "rows_failed": len(swap_failures),
        "failures": swap_failures,
        "comparison": "feature(P) == feature(swap(P)) exactly for every row",
    }
    write_json(swap_proof_path, swap_proof)
    if swap_proof["status"] != "PASS":
        raise RuntimeError("swap-invariance proof failed")

    prediction_rows = read_jsonl(args.predictions)
    labels = [row["stage"] for row in source_rows]
    expected_stages = [row["expected_first_affected_stage"] for row in source_rows]
    clusters = [row["cluster_id"] for row in source_rows]
    sample_ids = [row["sample_id"] for row in source_rows]
    original_by_id = {row["sample_id"]: row for row in prediction_rows}

    reasons = {
        "missing_pair_member": 0,
        "nonfinite_feature": 0,
        "feature_row_missing": 0,
        "label_missing": 0,
        "cluster_missing": 0,
        "row_alignment_failure": 0,
        "proof_missing": 0,
    }
    retained = 0
    for index in range(len(source_rows)):
        if index >= len(feature_records):
            reasons["feature_row_missing"] += 1
            continue
        if not labels[index] or labels[index] not in CLASSES:
            reasons["label_missing"] += 1
            continue
        if not clusters[index]:
            reasons["cluster_missing"] += 1
            continue
        if sample_ids[index] not in original_by_id:
            reasons["row_alignment_failure"] += 1
            continue
        if not all(math.isfinite(value) for value in feature_records[index]["features"]):
            reasons["nonfinite_feature"] += 1
            continue
        retained += 1
    attrition = {
        "expected_rows": EXPECTED_ROWS,
        "observed_source_rows": len(source_rows),
        "retained_rows": retained,
        "excluded_rows": len(source_rows) - retained,
        "rows_by_exclusion_reason": reasons,
        "proof_missing_rows": 0,
    }
    write_json(args.work_dir / "attrition.json", attrition)

    qualification_failures = []
    if len(source_rows) != EXPECTED_ROWS:
        qualification_failures.append(f"source rows {len(source_rows)} != {EXPECTED_ROWS}")
    if len({row["cluster_id"] for row in source_rows}) != EXPECTED_CLUSTERS:
        qualification_failures.append(f"clusters != {EXPECTED_CLUSTERS}")
    if retained != EXPECTED_ROWS:
        qualification_failures.append(f"retained rows {retained} != {EXPECTED_ROWS}")
    if labels != expected_stages:
        qualification_failures.append("stage label differs from injection-design expected stage")
    if not (args.contract.exists() and swap_proof_path.exists() and extraction_proof_path.exists()):
        qualification_failures.append("proof artifact missing")
    qualification_status = "PASS" if not qualification_failures else "FAIL"

    y = np.asarray(labels, dtype=object)
    original_y = np.asarray([original_by_id[sample_id]["true_stage"] for sample_id in sample_ids], dtype=object)
    original_pred = np.asarray([original_by_id[sample_id]["predicted_stage"] for sample_id in sample_ids], dtype=object)
    cluster_array = np.asarray(clusters, dtype=object)
    matrix = np.asarray([record["features"] for record in feature_records], dtype=float)

    set_results = {}
    predictions_by_set = {}
    for set_name, indices in FEATURE_SETS.items():
        x = matrix[:, indices]
        predictions = predict_loco(x, y, cluster_array)
        predictions_by_set[set_name] = predictions
        set_results[set_name] = metric_payload(y, predictions)

    unique_clusters = sorted(set(clusters))
    cluster_labels = [next(label for label, cluster in zip(labels, clusters) if cluster == target) for target in unique_clusters]
    shuffled_labels = np.asarray(random.Random(SHUFFLED_LABEL_SEED).sample(cluster_labels, len(cluster_labels)), dtype=object)
    shuffled_by_cluster = dict(zip(unique_clusters, shuffled_labels))
    shuffled_y = np.asarray([shuffled_by_cluster[cluster] for cluster in clusters], dtype=object)
    shuffled_pred = predict_loco(matrix[:, FEATURE_SETS["full"]], shuffled_y, cluster_array)
    shuffled_control = metric_payload(shuffled_y, shuffled_pred)

    rng = random.Random(BOOTSTRAP_SEED)
    unique_cluster_array = np.unique(cluster_array)
    cluster_indices = {cluster: np.flatnonzero(cluster_array == cluster) for cluster in unique_cluster_array}
    bootstrap_full = np.empty(BOOTSTRAP_REPLICATES, dtype=float)
    bootstrap_original = np.empty(BOOTSTRAP_REPLICATES, dtype=float)
    bootstrap_direct = np.empty(BOOTSTRAP_REPLICATES, dtype=float)
    bootstrap_non_direct = np.empty(BOOTSTRAP_REPLICATES, dtype=float)
    bootstrap_shuffled = np.empty(BOOTSTRAP_REPLICATES, dtype=float)
    for replicate in range(BOOTSTRAP_REPLICATES):
        sampled = [unique_cluster_array[rng.randrange(len(unique_cluster_array))] for _ in unique_cluster_array]
        indices = np.concatenate([cluster_indices[cluster] for cluster in sampled])
        bootstrap_full[replicate] = macro_f1(y[indices], predictions_by_set["full"][indices])
        bootstrap_original[replicate] = macro_f1(original_y[indices], original_pred[indices])
        bootstrap_direct[replicate] = macro_f1(y[indices], predictions_by_set["direct_codebook"][indices])
        bootstrap_non_direct[replicate] = macro_f1(y[indices], predictions_by_set["non_direct"][indices])
        bootstrap_shuffled[replicate] = macro_f1(shuffled_y[indices], shuffled_pred[indices])
    bootstrap_delta = bootstrap_full - bootstrap_original

    def ci(values: np.ndarray) -> list[float]:
        return [round(float(np.quantile(values, 0.025)), 6), round(float(np.quantile(values, 0.975)), 6)]

    for name, values in (
        ("full", bootstrap_full),
        ("direct_codebook", bootstrap_direct),
        ("non_direct", bootstrap_non_direct),
        ("shuffled_label_control", bootstrap_shuffled),
    ):
        if name in set_results:
            set_results[name]["macro_f1_ci95"] = ci(values)
        else:
            shuffled_control["macro_f1_ci95"] = ci(values)

    original_frozen = json.loads(args.formal_result.read_text(encoding="utf-8"))
    original_macro = float(original_frozen["primary"]["macro_f1"])
    full_macro = float(set_results["full"]["macro_f1"])
    delta = full_macro - original_macro
    outcome_label, outcome_reason = classify(
        full_macro,
        float(set_results["direct_codebook"]["macro_f1"]),
        float(set_results["non_direct"]["macro_f1"]),
        swap_proof["status"],
        qualification_status,
    )

    claim_lowering_note = None
    if outcome_label.startswith("NULL") or delta < 0:
        claim_lowering_note = (
            "Original multi-leaf claim lowered: the label-blind supporting result is "
            f"{outcome_label}; this run does not support a repair-count increase."
        )

    result = {
        "experiment_id": "PR-EXP-07",
        "role": "ROBUSTNESS_ANTI_TAUTOLOGY_SUPPORTING_ONLY",
        "outcome_label": outcome_label,
        "outcome_reason": outcome_reason,
        "taxonomy_priority": [
            "NOT_EVALUABLE",
            "INVALID",
            "ROBUST",
            "NULL",
            "NULL_AT_CHANCE",
            "NULL_DIRECT_CONCENTRATED"
        ],
        "qualification_status": qualification_status,
        "qualification_failures": qualification_failures,
        "proof_status": {
            "pairing": extraction_proof["status"],
            "swap_invariance": swap_proof["status"],
            "leakage": "PASS" if extraction_proof["forbidden_fields_accessed"] == [] else "FAIL"
        },
        "population": {
            "expected_rows": EXPECTED_ROWS,
            "evaluated_rows": retained,
            "clusters": len(unique_clusters),
            "classes": list(CLASSES),
        },
        "metrics": set_results,
        "chance": {
            "macro_f1": CHANCE,
            "top1_accuracy": CHANCE
        },
        "shuffled_label_control": shuffled_control,
        "original_frozen": {
            "source_path": str(args.formal_result),
            "source_sha256": sha256_file(args.formal_result),
            "macro_f1": original_macro,
            "macro_f1_ci95": original_frozen["primary"]["macro_f1_ci95"],
            "top1_accuracy": original_frozen["primary"]["top1_accuracy"],
            "rows_identical": retained == EXPECTED_ROWS and not reasons["row_alignment_failure"]
        },
        "blind_vs_original_delta": {
            "metric": "macro_f1",
            "formula": "full_labelblind_macroF1 - original_frozen_macroF1",
            "point": delta,
            "ci95": ci(bootstrap_delta),
            "bootstrap_seed": BOOTSTRAP_SEED,
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "claim_comparability": "NON_COMPARABLE_CLAIM_WISE; numeric delta is reported only on identical rows"
        },
        "bootstrap": {
            "seed": BOOTSTRAP_SEED,
            "replicates": BOOTSTRAP_REPLICATES,
            "interval": "cluster percentile 2.5/97.5"
        },
        "shuffled_label_control_seed": SHUFFLED_LABEL_SEED,
        "feature_sets": FEATURE_SETS,
        "feature_set_leaf_order": {
            "full": list(LEAF_ORDER),
            "direct_codebook": list(DIRECT_LEAVES),
            "non_direct": list(NON_DIRECT_LEAVES)
        },
        "attrition": attrition,
        "claim_lowering_note": claim_lowering_note,
        "supporting_only": True,
        "counts_toward_repair_count": False
    }
    result_path = args.work_dir / "result.json"
    write_json(result_path, result)

    contract_hash = sha256_file(args.contract)
    receipt_inputs = {record["path"]: record["sha256"] for record in frozen["scientific_inputs"]}
    receipt_outputs = {}
    for path in sorted(args.work_dir.iterdir()):
        if path.is_file() and path.name != "receipt.json":
            receipt_outputs[path.name] = sha256_file(path)
    receipt = {
        "experiment_id": "PR-EXP-07",
        "status": "COMPLETE"
        if qualification_status == "PASS"
        and swap_proof["status"] == "PASS"
        and extraction_proof["status"] == "PASS"
        else "STOPPED",
        "outcome_label": outcome_label,
        "prereg_sha256": "4724e53ebaf86633384f1955e5182bd7c5b886994603b59a6146c45ce6426d5f",
        "implementation_contract_sha256": contract_hash,
        "start_utc": start_utc,
        "end_utc": now_utc(),
        "input_hashes": receipt_inputs,
        "output_hashes": receipt_outputs,
        "raw_metrics": {
            "full": set_results["full"],
            "direct_codebook": set_results["direct_codebook"],
            "non_direct": set_results["non_direct"],
            "shuffled_label_control": shuffled_control,
            "original_frozen": result["original_frozen"],
            "delta": result["blind_vs_original_delta"]
        },
        "cost": {
            "model_calls": 0,
            "judge_calls": 0,
            "training_runs": 0,
            "service_calls": 0,
            "database_calls": 0,
            "network_requests": 0
        },
        "unverified_items": [],
        "deviations": []
    }
    write_json(args.work_dir / "receipt.json", receipt)
    if receipt["status"] != "COMPLETE":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
