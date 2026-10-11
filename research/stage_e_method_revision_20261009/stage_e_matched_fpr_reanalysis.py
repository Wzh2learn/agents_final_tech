#!/usr/bin/env python3
"""Clean-only structural reanalysis for flat versus hierarchical scores."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "matched_fpr_reanalysis.json"
ALPHA = 0.05
N_FOLDS = 5
SENSITIVITY_GRID = [0.1, 0.2, 0.5, 1.0, 1.428571, 2.0]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = rank
        i = j + 1
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    out_path = Path(args.out)

    sys.path.insert(0, str(ROOT / "scripts"))
    import m1_statement_parser as mp

    d3 = load_module("d3_reanalysis_base", ROOT / "research/paper_d3_matched_fpr_stage_a.py")
    tb = load_module("tree_agg_reanalysis", ROOT / "research/paper_t1_eval_baselines.py")
    corpus = d3.load_corpus()
    g1 = d3.g1_reproduce(corpus, mp, tb)

    clean = []
    for table in corpus["src"]:
        if table["uid"] in corpus["inj_uids"]:
            continue
        header = d3.header_of(table["table"][0])
        canonical = d3.unique_canonical(header, mp)
        if not canonical:
            continue
        h, _ = d3.hit_rate(header, canonical, mp)
        h_repeat = d3.hit_rate(header, canonical, mp)[0]
        flat = round((h - h_repeat) * 10.0, 6)
        root = d3.root_of(tb, h)
        layered = round(root - d3.root_of(tb, h_repeat), 6)
        clean.append({"uid": table["uid"], "flat": flat, "layered": layered})

    harmful = [
        row for row in g1["per_inj"]
        if row["class"] in {"H", "HI"}
    ]
    equivalent = [row for row in g1["per_inj"] if row["class"] == "E"]

    clean_flat = [row["flat"] for row in clean]
    clean_layered = [row["layered"] for row in clean]
    positive_clean_flat = sum(value > 0 for value in clean_flat)
    positive_clean_layered = sum(value > 0 for value in clean_layered)
    threshold_identifiable = positive_clean_flat > 0 and positive_clean_layered > 0

    fold = {uid: i % N_FOLDS for i, uid in enumerate(sorted({row["uid"] for row in clean} | {row["uid"] for row in harmful}))}
    clean_by_fold = defaultdict(list)
    harmful_by_fold = defaultdict(list)
    for row in clean:
        clean_by_fold[fold[row["uid"]]].append(row)
    for row in harmful:
        harmful_by_fold[fold[row["uid"]]].append(row)

    folds = []
    for held_out in range(N_FOLDS):
        calibration = [row for f, rows in clean_by_fold.items() if f != held_out for row in rows]
        evaluation = harmful_by_fold[held_out]
        calibration_positive = {
            "flat": sum(row["flat"] > 0 for row in calibration),
            "layered": sum(row["layered"] > 0 for row in calibration),
        }
        sensitivity = []
        for theta_flat in SENSITIVITY_GRID:
            theta_layered = 0.375 * theta_flat
            flat_detected = sum(row["dH10"] > theta_flat for row in evaluation)
            layered_detected = sum(row["layer_drop"] > theta_layered for row in evaluation)
            sensitivity.append({
                "theta_flat_drop10": theta_flat,
                "theta_layered_root_drop": theta_layered,
                "flat_detected": flat_detected,
                "layered_detected": layered_detected,
                "difference": flat_detected - layered_detected,
            })
        folds.append({
            "fold": held_out,
            "n_clean_calibration": len(calibration),
            "n_harmful_evaluation": len(evaluation),
            "clean_positive_support": calibration_positive,
            "clean_only_threshold_identifiable": all(v > 0 for v in calibration_positive.values()),
            "threshold_status": "UNIDENTIFIED_ZERO_CLEAN_SUPPORT",
            "fixed_affine_grid_sensitivity": sensitivity,
        })

    positive_pairs = [
        row for row in harmful
        if row["dH10"] > 0
    ]
    slopes = [row["layer_drop"] / row["dH10"] for row in positive_pairs]
    flat_scores = [row["dH10"] for row in harmful]
    layered_scores = [row["layer_drop"] for row in harmful]
    spearman = statistics.correlation(ranks(flat_scores), ranks(layered_scores))
    max_slope_deviation = max(abs(value - 0.375) for value in slopes)

    payload = {
        "namespace": "stage_e_matched_fpr_reanalysis_v1",
        "status": "BLOCKER_CLEAN_THRESHOLD_NOT_IDENTIFIABLE",
        "alpha_target": ALPHA,
        "clean_only_contract": {
            "calibration_inputs": "clean-table flat/layered contrastive scores only",
            "prohibited_inputs": ["injected scores", "H/HI labels", "evaluation-fold TPR"],
            "fold_assignment": "sorted(table uid) index modulo 5",
            "replicate_recalibration": "required for future confirmatory analysis; impossible here because clean support has no positive scores",
        },
        "data": {
            "n_clean_usable": len(clean),
            "n_harmful_H_union_HI": len(harmful),
            "n_equivalent_excluded": len(equivalent),
            "clean_flat_support": sorted(set(clean_flat)),
            "clean_layered_support": sorted(set(clean_layered)),
            "positive_clean_flat": positive_clean_flat,
            "positive_clean_layered": positive_clean_layered,
        },
        "identification": {
            "threshold_identifiable": threshold_identifiable,
            "score_construction_note": "The second hit-rate observation repeats the same computation on the unmodified row, so the current contrastive score is zero by construction.",
            "reason": "No unmodified clean panel can produce nonzero support under this exact score definition; any positive threshold has FPR 0 and cannot be selected uniquely without harmful outcomes.",
            "required_missing_evidence": "A revised score definition with nonzero clean support or a separately preregistered pseudo-injection/null-mutation panel. More clean rows under the same zero-by-construction score do not resolve identification.",
        },
        "cross_fit": folds,
        "structural_equivalence": {
            "positive_harmful_pairs": len(positive_pairs),
            "slope_layered_over_flat": sorted(set(round(value, 10) for value in slopes)),
            "max_abs_slope_deviation_from_0.375": max_slope_deviation,
            "spearman_rank_correlation": spearman,
            "ranking_equivalent": math.isclose(spearman, 1.0, abs_tol=1e-12),
            "roc_equivalent": math.isclose(spearman, 1.0, abs_tol=1e-12) and max_slope_deviation < 1e-6,
            "reason": "The hierarchical score is a positive affine transform of the flat score on the current single-responsive-leaf construction.",
        },
        "claims": {
            "claim_a_structural_affine_equivalence": "SUPPORTED",
            "claim_b_empirical_clean_matched_fpr_equality": "NOT_IDENTIFIABLE",
            "old_90_111_comparison": "SUPPORTING_SENSITIVITY_ONLY",
        },
        "frozen_inputs": {
            "d3_matched_fpr_stage_a": sha256(ROOT / "logs/graph/eval/d3_matched_fpr_stage_a.json"),
            "d1_mutant_validity_audit": sha256(ROOT / "logs/graph/eval/d1_mutant_validity_audit.json"),
        },
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "threshold_identifiable": threshold_identifiable,
        "ranking_equivalent": payload["structural_equivalence"]["ranking_equivalent"],
        "max_slope_deviation": max_slope_deviation,
        "output": str(out_path),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
