#!/usr/bin/env python3
"""Independently validate frozen multi-leaf formal result artifacts."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "research/stage_e_multileaf_20261010"
RESULTS = TASK / "results"
PRE_MANIFEST = TASK / "multileaf_preresult_freeze_manifest.json"
PRE_HASH = TASK / "multileaf_preresult_freeze_manifest.sha256"
RUN_RECEIPT = RESULTS / "multileaf_run_receipt.json"
OUT = RESULTS / "independent_validation_receipt.json"

CLASSES = ("M", "R", "N")
TIE = "__TIE__"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def leaf_order(tree: dict[str, Any]) -> list[str]:
    leaves: list[str] = []

    def visit(node: dict[str, Any]) -> None:
        children = node.get("children") or []
        if children:
            for child in children:
                visit(child)
        else:
            leaves.append(str(node["id"]))

    for root in tree.get("trees", []):
        visit(root)
    return leaves


def macro_f1(y_true: list[str], y_pred: list[str]) -> float:
    values = []
    for label in CLASSES:
        tp = sum(true == label and pred == label for true, pred in zip(y_true, y_pred))
        fp = sum(true != label and pred == label for true, pred in zip(y_true, y_pred))
        fn = sum(true == label and pred != label for true, pred in zip(y_true, y_pred))
        denominator = 2 * tp + fp + fn
        values.append(0.0 if denominator == 0 else 2 * tp / denominator)
    return float(np.mean(values))


def close(left: float, right: float, tolerance: float = 1e-12) -> bool:
    return abs(float(left) - float(right)) <= tolerance


def main() -> int:
    errors: list[str] = []
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any = None) -> None:
        checks.append({"check": name, "pass": bool(passed), "detail": detail})
        if not passed:
            errors.append(name)

    result = json.loads((RESULTS / "multileaf_formal_results.json").read_text(encoding="utf-8"))
    predictions = read_jsonl(RESULTS / "multileaf_prediction_rows.jsonl")
    paired = read_jsonl(RESULTS / "multileaf_paired_artifacts.jsonl")
    run_receipt = json.loads(RUN_RECEIPT.read_text(encoding="utf-8"))
    permutation = json.loads((RESULTS / "multileaf_permutation_null.json").read_text(encoding="utf-8"))
    bootstrap = json.loads((RESULTS / "multileaf_bootstrap_intervals.json").read_text(encoding="utf-8"))

    check("row_counts", len(predictions) == 216 and len(paired) == 216, [len(predictions), len(paired)])
    y_true = [row["true_stage"] for row in predictions]
    y_pred = [row["predicted_stage"] for row in predictions]
    observed_macro = macro_f1(y_true, y_pred)
    observed_top1 = sum(true == pred for true, pred in zip(y_true, y_pred)) / len(y_true)
    check("macro_f1_recomputed", close(observed_macro, result["primary"]["macro_f1"]), observed_macro)
    check("top1_recomputed", close(observed_top1, result["primary"]["top1_accuracy"]), observed_top1)
    check("perfect_separation_recomputed", observed_macro == 1.0 and observed_top1 == 1.0)

    confusion = Counter(zip(y_true, y_pred))
    confusion_ok = all(
        result["confusion_matrix"][true][pred] == confusion.get((true, pred), 0)
        for true in CLASSES
        for pred in (*CLASSES, TIE)
    )
    check("confusion_recomputed", confusion_ok)

    contract_ok = all(row["contract_pass"] for row in paired)
    expected_stage_ok = all(row["stage"] == row["expected_first_stage"] for row in paired)
    check("contracts_recomputed", contract_ok)
    check("expected_stage_recomputed", expected_stage_ok)

    tree = json.loads((ROOT / "config/eval_checkpoint_trees.json").read_text(encoding="utf-8"))
    leaves = leaf_order(tree)
    signatures: dict[str, Counter[tuple[int, ...]]] = {stage: Counter() for stage in CLASSES}
    leaf_counts: dict[str, Counter[str]] = {stage: Counter() for stage in CLASSES}
    for row in paired:
        vector = tuple(int(row["response_vector"][leaf]) for leaf in leaves)
        signatures[row["stage"]][vector] += 1
        for leaf, value in row["response_vector"].items():
            if value:
                leaf_counts[row["stage"]][leaf] += 1
    signature_ok = True
    for stage in CLASSES:
        recorded = {tuple(item[0]): item[1] for item in result["response_signatures"][stage]}
        signature_ok = signature_ok and recorded == dict(signatures[stage])
    check("signatures_recomputed", signature_ok)

    p_macro = (1 + sum(value >= observed_macro for value in permutation["macro_f1"])) / (
        len(permutation["macro_f1"]) + 1
    )
    p_top1 = (1 + sum(value >= observed_top1 for value in permutation["top1_accuracy"])) / (
        len(permutation["top1_accuracy"]) + 1
    )
    check("permutation_lengths", len(permutation["macro_f1"]) == 10000 and len(permutation["top1_accuracy"]) == 10000)
    check("permutation_p_macro_recomputed", close(p_macro, result["primary"]["permutation_p_macro_f1"]), p_macro)
    check("permutation_p_top1_recomputed", close(p_top1, result["primary"]["permutation_p_top1"]), p_top1)

    macro_ci = [
        round(float(np.quantile(bootstrap["macro_f1"], 0.025)), 6),
        round(float(np.quantile(bootstrap["macro_f1"], 0.975)), 6),
    ]
    top1_ci = [
        round(float(np.quantile(bootstrap["top1_accuracy"], 0.025)), 6),
        round(float(np.quantile(bootstrap["top1_accuracy"], 0.975)), 6),
    ]
    check("bootstrap_lengths", len(bootstrap["macro_f1"]) == 10000 and len(bootstrap["top1_accuracy"]) == 10000)
    check("bootstrap_macro_ci_recomputed", macro_ci == result["primary"]["macro_f1_ci95"], macro_ci)
    check("bootstrap_top1_ci_recomputed", top1_ci == result["primary"]["top1_ci95"], top1_ci)

    expected_hashes = {
        "result_json_sha256": RESULTS / "multileaf_formal_results.json",
        "result_md_sha256": RESULTS / "multileaf_formal_results.md",
        "paired_artifacts_sha256": RESULTS / "multileaf_paired_artifacts.jsonl",
        "predictions_sha256": RESULTS / "multileaf_prediction_rows.jsonl",
        "formal_runner_sha256": TASK / "run_multileaf_formal.py",
    }
    for key, path in expected_hashes.items():
        check(f"run_receipt_hash:{key}", run_receipt[key] == sha256_file(path), sha256_file(path))

    expected_manifest_hash = PRE_HASH.read_text(encoding="utf-8").strip().split()[0]
    check("pre_result_manifest_hash", expected_manifest_hash == sha256_file(PRE_MANIFEST))
    check("pre_result_hash_recorded_in_results", result["pre_result_manifest_sha256"] == expected_manifest_hash)
    check(
        "claim_boundary",
        result["claim_allowed"].startswith("Checkpoint evidence contains stage-localizing information")
        and result["claim_forbidden"] == "The hierarchy localizes failures.",
    )

    receipt = {
        "status": "PASS" if not errors else "FAIL",
        "checks_passed": sum(item["pass"] for item in checks),
        "checks_total": len(checks),
        "errors": errors,
        "recomputed": {
            "macro_f1": observed_macro,
            "top1_accuracy": observed_top1,
            "permutation_p_macro_f1": p_macro,
            "permutation_p_top1": p_top1,
            "macro_f1_ci95": macro_ci,
            "top1_ci95": top1_ci,
        },
        "checks": checks,
    }
    OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "checks": f"{receipt['checks_passed']}/{receipt['checks_total']}",
        "errors": errors,
        "output": str(OUT),
    }, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
