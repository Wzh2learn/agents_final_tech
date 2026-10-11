#!/usr/bin/env python3
"""Power and sample-size plans for a three-stage multi-leaf experiment."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from scipy.stats import nct, norm, t

OUT = Path(__file__).resolve().parent / "multileaf_power_analysis.json"
ALPHA = 0.05
POWER_TARGET = 0.80
EFFECT = 0.10
SIGMA = 0.25
SEED = 20261009
N_SIM = 200_000


def exact_power(n_clusters: int, effect: float, sigma: float) -> float:
    df = n_clusters - 1
    critical = t.ppf(1.0 - ALPHA / 2.0, df)
    ncp = effect * math.sqrt(n_clusters) / sigma
    return float(nct.sf(critical, df, ncp) + nct.cdf(-critical, df, ncp))


def normal_power(n_clusters: int, effect: float, sigma: float) -> float:
    z = norm.ppf(1.0 - ALPHA / 2.0)
    ncp = effect * math.sqrt(n_clusters) / sigma
    return float(norm.sf(z - ncp) + norm.cdf(-z - ncp))


def simulation_power(n_clusters: int, effect: float, sigma: float, seed: int) -> float:
    import numpy as np
    rng = np.random.default_rng(seed)
    draws = rng.normal(effect, sigma, size=(N_SIM, n_clusters))
    means = draws.mean(axis=1)
    ses = draws.std(axis=1, ddof=1) / math.sqrt(n_clusters)
    tstat = means / ses
    critical = t.ppf(1.0 - ALPHA / 2.0, n_clusters - 1)
    return float(np.mean(np.abs(tstat) > critical))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    plans = [
        ("MINIMAL", 12, 2),
        ("TARGET", 24, 3),
        ("STRONG", 50, 4),
    ]
    rows = []
    for index, (name, clusters_per_stage, injections_per_cluster_stage) in enumerate(plans):
        total_clusters = clusters_per_stage * 3
        total_injections = clusters_per_stage * injections_per_cluster_stage * 3
        pooled_power_exact = exact_power(total_clusters, EFFECT, SIGMA)
        stage_power_exact = exact_power(clusters_per_stage, EFFECT, SIGMA)
        pooled_power_sim = simulation_power(total_clusters, EFFECT, SIGMA, SEED + index)
        ci_half_width = 1.96 * SIGMA / math.sqrt(total_clusters)
        rows.append({
            "plan": name,
            "independent_table_clusters_per_stage": clusters_per_stage,
            "injections_per_cluster_per_stage": injections_per_cluster_stage,
            "total_independent_clusters": total_clusters,
            "total_injections": total_injections,
            "expected_localization_effect_delta": EFFECT,
            "cluster_difference_sd_assumption": SIGMA,
            "pooled_macro_power_exact": pooled_power_exact,
            "pooled_macro_power_simulated": pooled_power_sim,
            "per_stage_power_exact": stage_power_exact,
            "approx_95pct_ci_half_width": ci_half_width,
            "target_power": POWER_TARGET,
            "gpu_api_cost": "0 GPU / 0 API for deterministic multi-leaf fixture",
            "cpu_cost_note": "bootstrap and deterministic injection checks scale with total_injections; no model or judge call is included",
        })
    sensitivity = []
    for effect in (0.05, 0.10, 0.15):
        for sigma in (0.20, 0.25, 0.35):
            sensitivity.append({
                "effect": effect,
                "sigma": sigma,
                "MINIMAL_pooled_power": exact_power(36, effect, sigma),
                "TARGET_pooled_power": exact_power(72, effect, sigma),
                "STRONG_pooled_power": exact_power(150, effect, sigma),
                "STRONG_per_stage_power": exact_power(50, effect, sigma),
            })
    result = {
        "namespace": "stage_e_multileaf_power_plan_v1",
        "primary_estimand": "macro-average stage-level top-1 localization accuracy difference versus the preregistered non-localization baseline",
        "primary_unit": "independent table/origin cluster",
        "assumptions": {
            "alpha_two_sided": ALPHA,
            "effect_delta": EFFECT,
            "cluster_difference_sd": SIGMA,
            "power_target": POWER_TARGET,
            "seed": SEED,
            "simulation_replicates": N_SIM,
            "effect_status": "DESIGN ASSUMPTION, NOT AN OBSERVED EFFECT",
            "variance_status": "SENSITIVITY ASSUMPTION, NOT ESTIMATED FROM DATA",
        },
        "plans": rows,
        "sensitivity": sensitivity,
        "multiple_comparison_plan": {
            "primary": "one pooled macro top-1 test at alpha=.05",
            "secondary_stage_top1": "Holm correction across Stage M/R/N",
            "exploratory": "top-k, first-visible-stage distance, propagation depth, silent absorption stage remain exploratory until precedent and preregistration are complete",
        },
        "interpretation": {
            "MINIMAL": "feasibility only; pooled power is below 0.80",
            "TARGET": "minimum plan for pooled macro effect under the stated delta/sigma",
            "STRONG": "supports pooled macro effect and approximately 0.80 per-stage power under the stated delta/sigma",
            "caveat": "The same table must not contribute independent power through multiple injections; all injections remain inside their cluster.",
        },
    }
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": str(args.out), "plans": rows}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
