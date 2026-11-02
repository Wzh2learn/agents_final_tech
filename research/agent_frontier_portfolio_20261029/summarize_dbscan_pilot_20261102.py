#!/usr/bin/env python3
"""Recompute compact, non-raw DBSCAN pilot evidence from local receipts."""

import argparse
from collections import Counter
import json
from pathlib import Path

from audit_dbscan_agent_output_20261102 import analyze
from run_dbscan_metric_control_20261102 import SOURCE_HASH
from run_dbscan_reference_20261101 import EXPECTED, sha


def episode(case, reference):
    receipt_path, raw_path = case / "receipt.json", case / "raw.jsonl"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    intervention = json.loads((case / "intervention.json").read_text(encoding="utf-8"))
    if sha(raw_path) != receipt["raw_sha256"]:
        raise ValueError("raw Agent event hash differs")
    events, bad_lines = [], 0
    for line in raw_path.read_text(encoding="utf-8").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            bad_lines += 1
    tools = [item.get("part", {}) for item in events if item.get("type") == "tool_use"]
    tool_counts = dict(Counter(item.get("tool", "unknown") for item in tools))
    reads = Counter()
    for item in tools:
        if item.get("tool") != "read":
            continue
        value = item.get("state", {}).get("input", {}).get("filePath", "")
        for name in ("prior_solution.py", "prior_instructions.txt"):
            if isinstance(value, str) and value.endswith("/" + name):
                reads[name] += 1
    tokens = receipt.get("step_finish_tokens", [])
    def total(name):
        return sum(value.get(name, 0) or 0 for value in tokens)
    def cached(name):
        return sum((value.get("cache") or {}).get(name, 0) or 0 for value in tokens)
    calls = receipt.get("model_http_requests", [])
    return {"case": case.name, "task": receipt.get("task"), "arm": receipt.get("arm"),
            "intervention_condition": intervention.get("condition"),
            "receipt_sha256": sha(receipt_path), "raw_sha256": sha(raw_path),
            "intervention_sha256": sha(case / "intervention.json"),
            "verifier_log_sha256": sha(case / "verifier.txt") if (case / "verifier.txt").is_file() else None,
            "agent_exit": receipt.get("agent_exit"),
            "verifier_exit": receipt.get("verifier_exit"), "elapsed_seconds": receipt.get("elapsed_seconds"),
            "post_requests": sum(value == "POST /v1/chat/completions" for value in calls),
            "other_or_denied_requests": sum(value != "POST /v1/chat/completions" for value in calls),
            "reported_input_tokens": total("input"), "reported_cached_read_tokens": cached("read"),
            "reported_cache_write_tokens": cached("write"), "reported_output_tokens": total("output"),
            "reported_total_tokens": total("total"), "usage_steps": len(tokens),
            "unparsed_raw_lines": bad_lines, "tool_use_counts": tool_counts,
            "explicit_read_tool_calls_for_history": dict(reads),
            "output_audit": analyze(case / "work/pareto_frontier.csv", reference)}


def main():
    parser = argparse.ArgumentParser()
    for name in ("source-case", "target-case", "history-case", "control-case", "source-reference", "target-reference", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if sha(args.source_reference) != EXPECTED[1] or sha(args.target_reference) != EXPECTED[2]:
        raise ValueError("released reference changed")
    if sha(args.source_case / "work/solve.py") != SOURCE_HASH:
        raise ValueError("source program changed")
    control_path = args.control_case / "receipt.json"
    control = json.loads(control_path.read_text(encoding="utf-8"))
    if control.get("agent_calls") != 0 or control.get("source_agent_program_sha256") != SOURCE_HASH:
        raise ValueError("transparent control provenance changed")
    control_result = args.control_case / "work/pareto_frontier.csv"
    current_output_hash = sha(control_result) if control_result.is_file() else None
    if current_output_hash != control.get("audit", {}).get("output_sha256"):
        raise ValueError("transparent control output changed")
    for phase in ("solver", "verifier"):
        if control.get(phase):
            for stream in ("stdout", "stderr"):
                if sha(args.control_case / (phase + "." + stream)) != control[phase][stream + "_sha256"]:
                    raise ValueError("transparent control log changed")
    source = episode(args.source_case, args.source_reference)
    target = episode(args.target_case, args.target_reference)
    history = episode(args.history_case, args.target_reference)
    if ((source["task"], source["arm"], source["intervention_condition"]) != ("dbscan-parameter-tuning-1", "no_skill", "no_history")
            or (target["task"], target["arm"], target["intervention_condition"]) != ("dbscan-parameter-tuning-2", "no_skill", "no_history")
            or (history["task"], history["arm"], history["intervention_condition"]) != ("dbscan-parameter-tuning-2", "prior_source_code", "prior_source_code")):
        raise ValueError("episode conditions do not match the declared comparison")
    result = {"status": "POSTHOC_DEVELOPMENT_SINGLE_SOURCE_FAMILY",
              "source_no_history": source,
              "target_no_history": target,
              "target_prior_source_code": history,
              "stale_source_output_against_target_reference": analyze(args.source_case / "work/pareto_frontier.csv", args.target_reference),
              "transparent_control": {"receipt_sha256": sha(control_path), "solver": control["solver"],
                                      "verifier": control.get("verifier"), "model_calls": 0,
                                      "output_audit": analyze(control_result, args.target_reference)},
              "limits": "One public source family and single runs; cost fields are episode-reported usage, not paid billing."}
    if args.output.exists():
        raise FileExistsError("refusing to overwrite an existing evidence summary")
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary_sha256": sha(args.output), "status": result["status"]}))


if __name__ == "__main__":
    main()
