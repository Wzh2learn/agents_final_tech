#!/usr/bin/env python3
"""Recompute results from isolated model-free control outputs."""
import argparse
import csv
import json
from pathlib import Path
import re

try:
    from .summarize_codebook_transfer import compare_assignments, inspect_output
except ImportError:
    from summarize_codebook_transfer import compare_assignments, inspect_output


def input_component_opportunities(data):
    keywords = {}
    for path in sorted(data.glob("codebook_*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                product = row["product_id"]
                for kw in row["keywords_examples"].split(","):
                    kw = kw.strip().upper()
                    if re.search(r"[A-Z]+[\d]+", kw):
                        keywords.setdefault(product, set()).add(kw)
    counts = {"records": 0, "records_with_component_regex": 0,
              "records_with_regex_fragment_equal_keyword": 0, "records_with_partial_regex_fragment_candidate": 0}
    with (data / "test_center_logs.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            counts["records"] += 1
            components = set(re.findall(r"[A-Z]+[\d]+", row["raw_reason_text"].upper()))
            options = keywords.get(row["product_id"], set())
            counts["records_with_component_regex"] += bool(components)
            counts["records_with_regex_fragment_equal_keyword"] += bool(components & options)
            counts["records_with_partial_regex_fragment_candidate"] += any(
                c != kw and (c in kw or kw in c) for c in components for kw in options)
    return counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("controls", type=Path)
    parser.add_argument("data", type=Path)
    parser.add_argument("initial_output", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    receipts = json.loads((args.controls / "receipt.json").read_text(encoding="utf-8"))
    results, assignments = {}, {}
    for mode in ("original_replay", "case_substring", "case_exact", "case_signal_exact"):
        case = args.controls / mode
        stats, assignments[mode] = inspect_output(args.data, case / "work/output/solution.json")
        text = (case / "verifier.txt").read_text(encoding="utf-8", errors="replace")
        stats["failed_tests"] = re.findall(r"^FAILED .*?::(test_\w+)", text, re.MULTILINE)
        match = re.search(r"(\d+) failed, (\d+) passed", text)
        stats["tests_failed"] = int(match[1]) if match else None
        stats["tests_passed"] = int(match[2]) if match else None
        stats["run_receipt"] = receipts[mode]
        results[mode] = stats
    initial, _ = inspect_output(args.data, args.initial_output)
    summary = {
        "status": "POST_HOC_DETERMINISTIC_CONTROL_NOT_SEMANTIC_GOLD",
        "original_reproduces_saved_report_sha": initial.get("output_sha256") == results["original_replay"].get("output_sha256"),
        "visible_input_component_opportunities": input_component_opportunities(args.data),
        "results": results,
        "case_repair_vs_original": compare_assignments(assignments["original_replay"], assignments["case_substring"]),
        "exact_vs_substring": compare_assignments(assignments["case_substring"], assignments["case_exact"]),
        "exact_vs_original": compare_assignments(assignments["original_replay"], assignments["case_exact"]),
        "signal_exact_vs_exact": compare_assignments(assignments["case_exact"], assignments["case_signal_exact"]),
    }
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
