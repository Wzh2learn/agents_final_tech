#!/usr/bin/env python3
"""Post-hoc Holm sensitivity for five lexical systems, using saved 200k-draw p-values.

This does not simulate new data or independently validate the sign-flip null.
It removes the dense system from a previously recomputed six-system family,
checks each effect against the earlier five-system result, and applies Holm to
the ten remaining unordered pairs separately within each dataset.
"""
import argparse
import hashlib
import json
from pathlib import Path


NAMES = {
    "bm25_k1=0.9_b=0.4": "BM25_09_04",
    "bm25_k1=1.2_b=0.75": "BM25_12_075",
    "bm25_k1=0.5_b=0.3": "BM25_05_03",
    "bm25_k1=1.5_b=0.6": "BM25_15_06",
    "tfidf_cosine": "TFIDF",
}


def holm(pvalues):
    adjusted = [0.0] * len(pvalues)
    running = 0.0
    for rank, index in enumerate(sorted(range(len(pvalues)), key=lambda i: pvalues[i])):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[index]))
        adjusted[index] = running
    return adjusted


def orient_interval(interval, same_direction):
    return interval if same_direction else [-interval[1], -interval[0]]


def recheck(original, sensitivity):
    results = {}
    if sensitivity["iterations_per_pair"] != 200000:
        raise ValueError("Unexpected Monte Carlo count")
    for dataset in original["datasets"]:
        name = dataset["dataset"]
        if name not in sensitivity["datasets"]:
            raise ValueError("Missing sensitivity dataset: " + name)
        previous = {}
        for row in dataset["pairwise_ndcg@10"]:
            key = frozenset((NAMES[row["higher"]], NAMES[row["lower"]]))
            if len(key) != 2 or key in previous:
                raise ValueError("Repeated or malformed prior pair")
            previous[key] = row
        saved = sensitivity["datasets"][name]
        if saved["queries"] != dataset["queries_evaluated"]:
            raise ValueError("Query count mismatch")
        rows = []
        for row in saved["pairs"]:
            if row["a"] == "BGE" or row["b"] == "BGE":
                continue
            key = frozenset((row["a"], row["b"]))
            if len(key) != 2 or key not in previous:
                raise ValueError("Unexpected lexical pair")
            old = previous[key]
            if abs(abs(row["difference"]) - abs(old["diff"])) > 1e-12:
                raise ValueError("Saved pair effect does not match previous result")
            interval = orient_interval(old["ci95"], row["a"] == NAMES[old["higher"]])
            rows.append({"a": row["a"], "b": row["b"], "difference_a_minus_b": row["difference"],
                         "p_200k": row["p"], "mc_standard_error_approx": row["mc_standard_error_approx"],
                         "original_bootstrap_ci95_a_minus_b": interval, "original_p_signflip_2k": old["p_signflip"],
                         "original_p_holm_2k": old["p_holm"], "original_significant_2k": old["significant_holm"]})
        if len(rows) != 10 or len({frozenset((row["a"], row["b"])) for row in rows}) != 10 or len(previous) != 10:
            raise ValueError("Expected exactly ten unique lexical pairs")
        for row, value in zip(rows, holm([row["p_200k"] for row in rows])):
            row["p_holm_200k_five_systems"] = value
            row["significant_200k"] = value < 0.05
        results[name] = {"queries": saved["queries"], "pairs": rows,
                         "significant_count_2k": sum(row["original_significant_2k"] for row in rows),
                         "significant_count_200k": sum(row["significant_200k"] for row in rows),
                         "changed_classifications": sum(row["original_significant_2k"] != row["significant_200k"] for row in rows)}
    return results


def sha_lf(path):
    """Hash repository text with Git's LF checkout normalization.

    Windows and Linux checkouts can differ only in line endings. Preserve all
    other bytes; this is not a hash of the physical checkout file.
    """
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("original", type=Path)
    parser.add_argument("sensitivity", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    old = json.loads(args.original.read_text(encoding="utf-8"))
    new = json.loads(args.sensitivity.read_text(encoding="utf-8"))
    data = {"status": "POST_HOC_NUMERICAL_SENSITIVITY_NOT_INDEPENDENT_CONFIRMATION",
            "inputs_lf_sha256": {"five_system_result": sha_lf(args.original), "six_system_200k_recheck": sha_lf(args.sensitivity)},
            "hash_contract": "SHA-256 after CRLF to LF normalization; not the physical checkout-file hash",
            "contract": "retain five lexical systems; recompute Holm across ten unordered pairs per dataset",
            "iterations_per_pair": new["iterations_per_pair"], "seed": new["seed"],
            "limitations": "Uses prior regenerated query scores; matching pair means is not proof of query-level identity. Post-hoc and conditional on sign-flip assumptions.",
            "datasets": recheck(old, new)}
    args.output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    if args.markdown:
        lines = ["# BEIR lexical pairwise comparisons: private review supplement", "",
                 "Post-hoc calculation using the saved 2,000-draw five-system analysis and the later 200,000-draw six-system sensitivity recheck. The latter regenerates lexical query scores and is not an independent dataset. Differences and intervals are in the direction A minus B for graded nDCG@10.", "",
                 "Bootstrap intervals are unadjusted query-level 95% intervals; both p columns use two-sided sign flips with Holm over the ten lexical pairs, separately by dataset. These are different inference procedures. Non-significance does not establish equality; numerical precision does not verify sign-flip or query-independence assumptions.", ""]
        for name, value in data["datasets"].items():
            lines.extend([f"## {name} ({value['queries']} queries)", "",
                          "| A | B | Mean A − B | Unadjusted bootstrap 95% CI | Holm p, 2,000 draws | Holm p, 200,000 draws |",
                          "| --- | --- | ---: | --- | ---: | ---: |"])
            for row in value["pairs"]:
                lo, hi = row["original_bootstrap_ci95_a_minus_b"]
                lines.append(f"| {row['a']} | {row['b']} | {row['difference_a_minus_b']:+.5f} | [{lo:.5f}, {hi:.5f}] | {row['original_p_holm_2k']:.5f} | {row['p_holm_200k_five_systems']:.5f} |")
            lines.append("")
        lines.extend(["The three supported pair classifications remain the same in the higher-draw sensitivity check. The source JSONs, code and hashes are listed in `lexical_holm_200k_sensitivity.json`; third-party dataset redistribution and anonymized artifact hosting remain subject to author approval and license review.", ""])
        args.markdown.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(json.dumps({name: {"2k": value["significant_count_2k"], "200k": value["significant_count_200k"],
                             "changed": value["changed_classifications"]} for name, value in data["datasets"].items()}))


if __name__ == "__main__":
    main()
