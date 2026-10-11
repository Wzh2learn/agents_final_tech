#!/usr/bin/env python3
"""Independent recomputation for the PR-EXP-04 formal result."""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[4]
RUN_DIR = Path(__file__).resolve().parent
RESULT_PATH = RUN_DIR / "result.json"
PREFLIGHT_PATH = RUN_DIR / "preflight_receipt.json"
VALIDATION_PATH = RUN_DIR / "independent_validation.json"
CONTRACT_PATH = RUN_DIR / "implementation_contract.md"
CONTRACT_HASH_PATH = RUN_DIR / "implementation_contract.sha256"
N2_RUN1 = RUN_DIR / "n2_generation_run1.jsonl"
N2_RUN2 = RUN_DIR / "n2_generation_run2.jsonl"
N1_EQUIVALENCE = RUN_DIR / "n1_harness_equivalence.json"

STAGE_E = ROOT / "research/stage_e_multileaf_20261010"
PAIRED = STAGE_E / "results/multileaf_paired_artifacts.jsonl"

CLASSES = ("M", "R", "N")
TIE = "__TIE__"
DIRECT = {
    "M": "parse.field.hit_rate",
    "R": "qa.retrieval.source_required",
    "N": "parse.reconcile.equations",
}
BOOTSTRAP_SEED = 20261012
BOOTSTRAP_REPLICATES = 10_000
EPS = 1e-12
CHANCE = 1.0 / 3.0
MARGIN = 0.05


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def jsonl_bytes(rows: Iterable[dict[str, Any]]) -> bytes:
    return "".join(canonical_json(row) + "\n" for row in rows).encode("utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def close(left: float, right: float, tolerance: float = 1e-12) -> bool:
    return abs(float(left) - float(right)) <= tolerance


def macro(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    per_class: dict[str, Any] = {}
    values: list[float] = []
    for label in CLASSES:
        tp = int(np.sum((y_true == label) & (y_pred == label)))
        fp = int(np.sum((y_true != label) & (y_pred == label)))
        fn = int(np.sum((y_true == label) & (y_pred != label)))
        numerator = 2 * tp
        denominator = 2 * tp + fp + fn
        f1 = 0.0 if denominator == 0 else numerator / denominator
        per_class[label] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "f1_numerator": numerator,
            "f1_denominator": denominator,
            "f1": f1,
        }
        values.append(f1)
    return {
        "per_class": per_class,
        "macro_f1_sum_numerator": sum(values),
        "macro_f1_class_denominator": 3,
        "macro_f1": float(np.mean(values)),
    }


def predict(
    source: list[dict[str, Any]],
    target: list[dict[str, Any]],
    leaves: list[str],
    indices: list[int],
) -> tuple[np.ndarray, int]:
    source_x = np.asarray([[row["response_vector"][leaves[index]] for index in indices] for row in source], dtype=float)
    source_y = np.asarray([row["stage"] for row in source], dtype=object)
    source_group = np.asarray([row["cluster_id"] for row in source], dtype=object)
    target_x = np.asarray([[row["response_vector"][leaves[index]] for index in indices] for row in target], dtype=float)
    target_group = np.asarray([row["cluster_id"] for row in target], dtype=object)
    predictions = np.empty(len(target), dtype=object)
    for position, group in enumerate(target_group):
        train = source_group != group
        if any(not np.any(train & (source_y == label)) for label in CLASSES):
            raise RuntimeError(f"missing class after LOCO for {group}")
        centroids = np.vstack([source_x[train & (source_y == label)].mean(axis=0) for label in CLASSES])
        distances = np.sqrt(((target_x[position][None, :] - centroids) ** 2).sum(axis=1))
        minimum = float(distances.min())
        tied = np.isclose(distances, minimum, rtol=0.0, atol=EPS)
        predictions[position] = TIE if int(tied.sum()) > 1 else CLASSES[int(np.argmin(distances))]
    return predictions, int(np.sum(predictions == TIE))


def bootstrap(
    target: list[dict[str, Any]],
    predictions: np.ndarray,
) -> dict[str, list[float]]:
    y_true = np.asarray([row["stage"] for row in target], dtype=object)
    groups = np.asarray([row["cluster_id"] for row in target], dtype=object)
    unique = np.unique(groups)
    indices = {group: np.flatnonzero(groups == group) for group in unique}
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    macro_values = np.empty(BOOTSTRAP_REPLICATES, dtype=float)
    top_values = np.empty(BOOTSTRAP_REPLICATES, dtype=float)
    for repeat in range(BOOTSTRAP_REPLICATES):
        sampled = rng.choice(unique, size=len(unique), replace=True)
        selected = np.concatenate([indices[group] for group in sampled])
        macro_values[repeat] = macro(y_true[selected], predictions[selected])["macro_f1"]
        top_values[repeat] = float(np.mean(y_true[selected] == predictions[selected]))
    return {
        "macro_f1_ci95_cluster_bootstrap": [
            round(float(np.quantile(macro_values, 0.025)), 6),
            round(float(np.quantile(macro_values, 0.975)), 6),
        ],
        "top1_ci95_cluster_bootstrap": [
            round(float(np.quantile(top_values, 0.025)), 6),
            round(float(np.quantile(top_values, 0.975)), 6),
        ],
    }


def recompute_metric(
    source: list[dict[str, Any]],
    target: list[dict[str, Any]],
    leaves: list[str],
    indices: list[int],
) -> dict[str, Any]:
    predictions, tie_count = predict(source, target, leaves, indices)
    y_true = np.asarray([row["stage"] for row in target], dtype=object)
    components = macro(y_true, predictions)
    correct = int(np.sum(y_true == predictions))
    return {
        "macro_f1": components,
        "top1_accuracy": {
            "correct": correct,
            "denominator": len(target),
            "point": correct / len(target),
        },
        "tie_count": tie_count,
        "confusion": {
            true: {
                pred: int(np.sum((y_true == true) & (predictions == pred)))
                for pred in (*CLASSES, TIE)
            }
            for true in CLASSES
        },
        **bootstrap(target, predictions),
    }


def compare_metric(name: str, expected: dict[str, Any], actual: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for key in ("macro_f1", "top1_accuracy", "confusion", "tie_count",
                "macro_f1_ci95_cluster_bootstrap", "top1_ci95_cluster_bootstrap"):
        checks.append({
            "check": f"{name}.{key}",
            "expected": expected[key],
            "actual": actual[key],
            "pass": expected[key] == actual[key] if key in {"confusion", "tie_count"} else (
                all(close(a, b) for a, b in zip(expected[key], actual[key]))
                if isinstance(expected[key], list)
                else (
                    expected[key]["macro_f1"] == actual[key]["macro_f1"]
                    and expected[key]["per_class"] == actual[key]["per_class"]
                    if key == "macro_f1"
                    else expected[key] == actual[key]
                )
            ),
        })
    return checks


def visibility(rows: list[dict[str, Any]]) -> tuple[int, int, int, int]:
    groups: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        groups[row["group_uid"]].append(int(sum(row["response_vector"].values()) > 0))
    visible = sum(sum(values) for values in groups.values())
    total = sum(len(values) for values in groups.values())
    responding = sum(any(values) for values in groups.values())
    return visible, total, responding, len(groups)


def main() -> int:
    if RECEIPT_EXISTS := (RUN_DIR / "receipt.json").exists():
        raise RuntimeError("receipt must not exist before independent validation")
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    preflight = json.loads(PREFLIGHT_PATH.read_text(encoding="utf-8"))
    contract_hash = CONTRACT_HASH_PATH.read_text(encoding="utf-8").strip().split()[0]
    if sha256_file(CONTRACT_PATH) != contract_hash:
        raise RuntimeError("contract hash mismatch")
    if result["prereg_sha256"] != preflight["prereg_sha256"]:
        raise RuntimeError("prereg hash mismatch")
    if result["implementation_contract_sha256"] != contract_hash:
        raise RuntimeError("implementation contract hash mismatch")
    if result["preflight_verification_level"] != "END_TO_END_PREFLIGHT_PASS":
        raise RuntimeError("preflight level mismatch")

    checks: list[dict[str, Any]] = []
    for record in result["hash_verification"]:
        path = ROOT / record["path"]
        actual = sha256_file(path)
        expected = record["expected"]
        passed = actual == expected if record["identity_rule"] == "raw_sha256" else (
            record.get("revision") == expected and record.get("worktree_blob") == expected
        )
        checks.append({"check": f"input_hash:{record['path']}", "expected": expected, "actual": actual, "pass": passed})

    n2_a = read_jsonl(N2_RUN1)
    n2_b = read_jsonl(N2_RUN2)
    double_bytes = jsonl_bytes(n2_a) == jsonl_bytes(n2_b)
    checks.append({"check": "n2_double_run_byte_identical", "expected": True, "actual": double_bytes, "pass": double_bytes})
    if not double_bytes:
        raise RuntimeError("N2 double-run mismatch")

    equivalence = json.loads(N1_EQUIVALENCE.read_text(encoding="utf-8"))
    equivalence_pass = (
        equivalence["byte_identical_response_vectors"]
        and equivalence["matched_rows"] == 72
        and equivalence["mismatched_rows"] == 0
    )
    checks.append({"check": "n1_harness_equivalence", "expected": True, "actual": equivalence_pass, "pass": equivalence_pass})

    visible, total, responding, group_count = visibility(n2_a)
    gate = result["gates"]["visibility"]
    gate_pass = (
        visible == gate["visible_rows"]
        and total == gate["total_rows"]
        and responding == gate["responding_groups"]
        and group_count == gate["total_groups"]
        and gate["pass"] == (visible >= math.ceil((2.0 / 3.0) * total) and responding >= 6)
    )
    checks.append({"check": "visibility_gate_recomputed", "expected": gate, "actual": {
        "visible_rows": visible, "total_rows": total,
        "responding_groups": responding, "total_groups": group_count,
        "pass": gate_pass,
    }, "pass": gate_pass})

    n1_rows = [dict(row, mechanism="N1") for row in read_jsonl(PAIRED)]
    n2_population = [dict(row, mechanism="N1") for row in n1_rows if row["stage"] in {"M", "R"}] + n2_a
    n1_n = [row for row in n1_rows if row["stage"] == "N"]
    n2_n = [row for row in n2_population if row["stage"] == "N"]
    n1_uids = {row["group_uid"] for row in n1_n}
    n2_uids = {row["group_uid"] for row in n2_n}
    uid_disjoint = not (n1_uids & n2_uids)
    checks.append({
        "check": "n1_n2_uid_disjoint",
        "expected": True,
        "actual": sorted(n1_uids & n2_uids),
        "pass": uid_disjoint,
    })

    counts_n1 = Counter(row["stage"] for row in n1_rows)
    counts_n2 = Counter(row["stage"] for row in n2_population)
    counts_pass = all(counts_n1[label] == counts_n2[label] == 72 for label in CLASSES)
    checks.append({
        "check": "class_counts_72_each",
        "expected": {label: 72 for label in CLASSES},
        "actual": {"n1": dict(counts_n1), "n2": dict(counts_n2)},
        "pass": counts_pass,
    })

    leaves = result["frozen_surface"]["leaves"]
    if len(leaves) != 12:
        raise RuntimeError("leaf surface mismatch")
    all_indices = list(range(12))
    direct_indices = [leaves.index(DIRECT[label]) for label in CLASSES]
    recomputed = {
        "n1_to_n2_full": recompute_metric(n1_rows, n2_population, leaves, all_indices),
        "n1_to_n2_direct": recompute_metric(n1_rows, n2_population, leaves, direct_indices),
        "n2_to_n1_full": recompute_metric(n2_population, n1_rows, leaves, all_indices),
        "n2_to_n1_direct": recompute_metric(n2_population, n1_rows, leaves, direct_indices),
    }
    expected_metrics = {
        "n1_to_n2_full": result["evaluation"]["n1_to_n2"]["full_surface"],
        "n1_to_n2_direct": result["evaluation"]["n1_to_n2"]["direct_codebook"],
        "n2_to_n1_full": result["evaluation"]["n2_to_n1"]["full_surface"],
        "n2_to_n1_direct": result["evaluation"]["n2_to_n1"]["direct_codebook"],
    }
    for name, expected in expected_metrics.items():
        checks.extend(compare_metric(name, expected, recomputed[name]))

    def responsive(rows: list[dict[str, Any]]) -> set[str]:
        return {leaf for leaf in leaves if sum(int(row["response_vector"][leaf]) for row in rows) > 0}
    n1_set = responsive(n1_n)
    n2_set = responsive(n2_n)
    overlap = {
        "intersection": sorted(n1_set & n2_set),
        "union": sorted(n1_set | n2_set),
        "intersection_numerator": len(n1_set & n2_set),
        "union_denominator": len(n1_set | n2_set),
        "jaccard": len(n1_set & n2_set) / len(n1_set | n2_set) if n1_set | n2_set else 1.0,
    }
    recorded_overlap = result["responsive_leaf_overlap"]
    overlap_pass = all(overlap[key] == recorded_overlap[key] for key in overlap)
    checks.append({"check": "responsive_leaf_overlap_recomputed", "expected": recorded_overlap, "actual": overlap, "pass": overlap_pass})

    label_set = {"SUPPORTED", "NULL", "NEGATIVE", "NOT_EVALUABLE", "INVALID"}
    label_pass = result["canonical_outcome_label"] in label_set and result["canonical_outcome_label_satisfied"]
    checks.append({
        "check": "canonical_outcome_label_totality",
        "expected": sorted(label_set),
        "actual": result["canonical_outcome_label"],
        "pass": label_pass,
    })

    if result["controls"]["n1_harness_equivalence"]["byte_identical_response_vectors"] and uid_disjoint and counts_pass:
        if not gate["pass"]:
            expected_label = "NOT_EVALUABLE"
        else:
            points = [recomputed["n1_to_n2_full"]["macro_f1"]["macro_f1"], recomputed["n2_to_n1_full"]["macro_f1"]["macro_f1"]]
            cis = [
                recomputed["n1_to_n2_full"]["macro_f1_ci95_cluster_bootstrap"],
                recomputed["n2_to_n1_full"]["macro_f1_ci95_cluster_bootstrap"],
            ]
            if any(point < CHANCE - MARGIN for point in points):
                expected_label = "NEGATIVE"
            elif all(point >= CHANCE for point in points) and any(ci[0] > CHANCE for ci in cis):
                expected_label = "SUPPORTED"
            else:
                expected_label = "NULL"
    else:
        expected_label = "INVALID"
    checks.append({
        "check": "canonical_outcome_label_recomputed",
        "expected": expected_label,
        "actual": result["canonical_outcome_label"],
        "pass": expected_label == result["canonical_outcome_label"],
    })

    if result["deviations"]:
        checks.append({"check": "deviations_empty", "expected": [], "actual": result["deviations"], "pass": False})
    else:
        checks.append({"check": "deviations_empty", "expected": [], "actual": [], "pass": True})

    status = "PASS" if all(check["pass"] for check in checks) else "FAIL"
    payload = {
        "experiment_id": "PR-EXP-04",
        "verification_level": "FORMAL_RUN_PASS",
        "status": status,
        "checks": checks,
        "check_count": len(checks),
        "failed_checks": [check for check in checks if not check["pass"]],
        "recomputed_metrics": recomputed,
        "recomputed_visibility": {
            "visible_rows": visible,
            "total_rows": total,
            "responding_groups": responding,
            "total_groups": group_count,
        },
        "recomputed_overlap": overlap,
        "recomputed_outcome_label": expected_label,
        "input_result_sha256": sha256_file(RESULT_PATH),
        "preflight_sha256": sha256_file(PREFLIGHT_PATH),
        "implementation_contract_sha256": contract_hash,
    }
    write_json(VALIDATION_PATH, payload)
    print(json.dumps({"status": status, "checks": len(checks), "failed": len(payload["failed_checks"])}, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
