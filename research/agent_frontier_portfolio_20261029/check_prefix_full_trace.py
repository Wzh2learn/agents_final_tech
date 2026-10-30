#!/usr/bin/env python3
"""After an episode, compare all saved rows to the task's existing oracle.

This expands coverage beyond five sampled rows; it is not an independent
implementation or proof that the task oracle is correct.
"""
import importlib.util
import json
import sys
from pathlib import Path


def compare(actual, expected):
    ar, er = actual["per_request"], expected["per_request"]
    if len(ar) != len(er):
        raise ValueError("per-request length mismatch")
    keys = ("idx", "prompt_tokens", "hit_tokens")
    mismatches = {k: sum(a.get(k) != e.get(k) for a, e in zip(ar, er)) for k in keys}
    bounds = sum(not (0 <= a["hit_tokens"] <= a["prompt_tokens"]) for a in ar)
    aggregates = {k: actual[k] == expected[k] for k in
                  ("total_requests", "total_prompt_tokens", "total_hit_tokens", "final_cache_blocks")}
    aggregates["overall_hit_rate_within_1e-6"] = abs(actual["overall_hit_rate"] - expected["overall_hit_rate"]) < 1e-6
    return {"rows": len(ar), "mismatches_by_field": mismatches,
            "hit_outside_prompt_bounds": bounds, "aggregate_matches": aggregates}


def main(work, verifier):
    work, verifier = Path(work), Path(verifier)
    spec = importlib.util.spec_from_file_location("prefix_oracle_helpers", verifier / "oracle_helpers.py")
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    config = json.loads((work / "config.json").read_text(encoding="utf8"))
    trace = oracle.load_trace(str(work / "trace.jsonl"))
    s3 = config["s3fifo"]
    expected = oracle.simulate(trace, config["block_size"], config["cache_capacity_blocks"],
                               s3["small_ratio"], s3["max_freq"])
    actual = json.loads((work / "report.json").read_text(encoding="utf8"))
    print(json.dumps(compare(actual, expected), sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: check_prefix_full_trace.py work verifier-dir")
    main(*sys.argv[1:])
