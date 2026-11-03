#!/usr/bin/env python3
"""Recheck saved BEIR query comparisons with SciPy and statsmodels.

This is a post-hoc numerical cross-check, not independent data or a check of
the statistical assumptions. The saved six-system result is supplied by path
and stays outside Git. Results do not replace the original audit artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import platform
import time
from pathlib import Path

import numpy as np
import scipy
from scipy.stats import permutation_test
import statsmodels
from statsmodels.stats.multitest import multipletests


EXPECTED_SOURCE_SHA256 = "b4596b01db7557570f644fcecf0325af6a18261637e47b6c9e112480fb87acdc"
LEXICAL = {"BM25_09_04", "BM25_12_075", "BM25_05_03", "BM25_15_06", "TFIDF"}


def statistic(x, y, axis=-1):
    """Absolute paired mean difference: one-sided tail of |difference|."""
    return np.abs(np.mean(x - y, axis=axis))


def positive_controls():
    x = np.ones(3)
    zero = np.zeros(3)
    common = dict(permutation_type="samples", vectorized=True,
                  n_resamples=np.inf, alternative="greater")
    exact = permutation_test((x, zero), statistic, **common)
    duplicate = permutation_test((x, x), statistic, **common)
    corrected = multipletests([0.01, 0.02, 0.04], method="holm")[1]
    if (len(exact.null_distribution) != 8 or not np.isclose(exact.pvalue, 0.25)
            or not np.isclose(duplicate.pvalue, 1.0)
            or not np.allclose(corrected, [0.03, 0.04, 0.04])):
        raise AssertionError("exhaustive sign-flip or Holm control failed")


def review(source, previous, draws, seed):
    if draws < 1000:
        raise ValueError("at least 1,000 Monte Carlo draws are required")
    positive_controls()
    source_bytes = source.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    if source_hash != EXPECTED_SOURCE_SHA256:
        raise ValueError("saved six-system source SHA-256 does not match")
    saved = json.loads(source_bytes)
    old = json.loads(previous.read_text(encoding="utf-8"))
    if old["iterations_per_pair"] != 200000:
        raise ValueError("unexpected prior Monte Carlo count")
    rng = np.random.default_rng(seed)
    result = {
        "status": "POST_HOC_CROSS_IMPLEMENTATION_NUMERICAL_REVIEW",
        "scope": ("same saved per-query scores, not independent data; paired sign-flip "
                  "inference still assumes an appropriate null and query independence"),
        "source_sha256": source_hash,
        "previous_lf_sha256": hashlib.sha256(
            previous.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "random_seed": seed,
        "draws_per_pair": draws,
        "implementation": {"python": platform.python_version(), "numpy": np.__version__,
                           "scipy": scipy.__version__, "statsmodels": statsmodels.__version__},
        "controls": {"three_pairs_exact_p": 0.25, "identical_p": 1.0,
                     "holm_001_002_004": [0.03, 0.04, 0.04]},
        "datasets": {},
    }
    for name, data in saved["datasets"].items():
        qids = data["per_query"]["qids"]
        scores = data["per_query"]["scores"]
        if (len(qids) != data["queries"] or len(set(qids)) != len(qids)
                or set(scores) != LEXICAL | {"BGE"}
                or old["datasets"][name]["queries"] != len(qids)):
            raise ValueError(f"unexpected query or system identities: {name}")
        for system, metrics in scores.items():
            arr = np.asarray(metrics["graded_10"], dtype=np.float64)
            if (arr.shape != (len(qids),) or not np.isfinite(arr).all()
                    or (arr < -1e-12).any() or (arr > 1 + 1e-12).any()):
                raise ValueError(f"invalid query values: {name}/{system}")
        prior = {frozenset((r["a"], r["b"])): r
                 for r in old["datasets"][name]["pairs"]}
        if len(prior) != 15:
            raise ValueError(f"unexpected prior pairs: {name}")
        rows = []
        for a, b in itertools.combinations(scores, 2):
            x = np.asarray(scores[a]["graded_10"], dtype=np.float64)
            y = np.asarray(scores[b]["graded_10"], dtype=np.float64)
            old_row = prior[frozenset((a, b))]
            effect = float(np.mean(x - y))
            expected_effect = old_row["difference"] if old_row["a"] == a else -old_row["difference"]
            if not np.isclose(effect, expected_effect, rtol=0, atol=1e-12):
                raise ValueError(f"pair effect differs from prior data: {name}/{a}/{b}")
            trial = permutation_test((x, y), statistic, permutation_type="samples",
                                     vectorized=True, n_resamples=draws, batch=500,
                                     alternative="greater", random_state=rng)
            pvalue = float(trial.pvalue)
            previous_p = float(old_row["p"])
            # Independent random draws fluctuate; this describes simulation error,
            # not a confidence interval for the scientific effect.
            mc_se = math.sqrt(pvalue * (1 - pvalue) / draws
                              + previous_p * (1 - previous_p) / 200000)
            rows.append({"a": a, "b": b, "difference_a_minus_b": effect,
                         "p_scipy": pvalue, "p_previous": previous_p,
                         "p_difference": pvalue - previous_p,
                         "combined_mc_se_approx": mc_se})
        six_adjusted = multipletests([row["p_scipy"] for row in rows], method="holm")[1]
        previous_six_adjusted = multipletests([row["p_previous"] for row in rows], method="holm")[1]
        lexical_indices = [i for i, row in enumerate(rows) if row["a"] in LEXICAL and row["b"] in LEXICAL]
        if len(lexical_indices) != 10:
            raise AssertionError("expected ten lexical pairs")
        lexical_adjusted = multipletests([rows[i]["p_scipy"] for i in lexical_indices],
                                        method="holm")[1]
        previous_lexical_adjusted = multipletests([rows[i]["p_previous"] for i in lexical_indices],
                                                 method="holm")[1]
        for row, adjusted, prior_adjusted in zip(rows, six_adjusted, previous_six_adjusted):
            row["p_holm_six"] = float(adjusted)
            row["p_previous_holm_six"] = float(prior_adjusted)
            old_row = prior[frozenset((row["a"], row["b"]))]
            if not np.isclose(prior_adjusted, old_row["p_holm"], rtol=0, atol=1e-12):
                raise ValueError(f"prior six-system Holm differs: {name}")
        for index, adjusted, prior_adjusted in zip(lexical_indices, lexical_adjusted,
                                                    previous_lexical_adjusted):
            rows[index]["p_holm_lexical"] = float(adjusted)
            rows[index]["p_previous_holm_lexical"] = float(prior_adjusted)
        result["datasets"][name] = {
            "queries": len(qids),
            "six_system_supported": sum(row["p_holm_six"] < 0.05 for row in rows),
            "lexical_supported": sum(rows[i]["p_holm_lexical"] < 0.05 for i in lexical_indices),
            "six_system_decisions_changed_vs_previous": sum(
                (row["p_holm_six"] < 0.05) != (row["p_previous_holm_six"] < 0.05)
                for row in rows),
            "lexical_decisions_changed_vs_previous": sum(
                (rows[i]["p_holm_lexical"] < 0.05) != (rows[i]["p_previous_holm_lexical"] < 0.05)
                for i in lexical_indices),
            "pairs": rows,
        }
        print(f"{name}: checked {len(rows)} pairs / {len(qids)} queries", flush=True)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("previous", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--draws", type=int, default=200000)
    parser.add_argument("--seed", type=int, default=20261103)
    args = parser.parse_args()
    started = time.perf_counter()
    result = review(args.source, args.previous, args.draws, args.seed)
    result["wall_seconds"] = time.perf_counter() - started
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise FileExistsError("refusing to overwrite a prior review")
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {args.output}", flush=True)


if __name__ == "__main__":
    main()
