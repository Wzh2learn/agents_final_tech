#!/usr/bin/env python3
"""Compare every saved task output row with the public task's existing oracle."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

evidence = Path(sys.argv[1])
task = Path(sys.argv[2])
output = Path(sys.argv[3])
oracle_path = task / "verifier/oracle_helpers.py"
spec = importlib.util.spec_from_file_location("skillsbench_oracle", oracle_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

cases = {
    "no_skill": "llm-prefix-cache-replay__no_skill__258386",
    "forced_skill": "llm-prefix-cache-replay__all_skill__263034",
    "optional_docs_8": "llm-prefix-cache-replay__docs_available__267991",
    "optional_docs_12": "llm-prefix-cache-replay__docs_available__278343",
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

results = {}
for name, directory in cases.items():
    case = evidence / directory
    work = case / "work"
    config_path, trace_path, report_path = (work / "config.json", work / "trace.jsonl", work / "report.json")
    receipt_path = case / "receipt.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    trace = module.load_trace(str(trace_path))
    s3 = config["s3fifo"]
    expected = module.simulate(trace, config["block_size"], config["cache_capacity_blocks"], s3["small_ratio"], s3["max_freq"])
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    item = {
        "config_sha256": sha(config_path), "trace_sha256": sha(trace_path),
        "receipt_sha256": sha(receipt_path), "agent_exit": receipt["agent_exit"],
        "verifier_exit": receipt["verifier_exit"],
        "expected_rows": len(expected["per_request"]),
        "report_present": report_path.is_file(),
    }
    if report_path.is_file():
        actual = json.loads(report_path.read_text(encoding="utf-8"))
        expected_rows = expected["per_request"]
        actual_rows = actual.get("per_request", [])
        item["report_sha256"] = sha(report_path)
        item["actual_rows"] = len(actual_rows)
        for key in ("idx", "prompt_tokens", "hit_tokens"):
            item[key + "_mismatches"] = (
                sum(a.get(key) != b.get(key) for a, b in zip(actual_rows, expected_rows))
                + abs(len(actual_rows) - len(expected_rows))
            )
        item["aggregate_matches"] = {
            key: actual.get(key) == expected.get(key)
            for key in ("total_requests", "total_prompt_tokens", "total_hit_tokens", "final_cache_blocks")
        }
    results[name] = item

report = {
    "scope": "post-hoc whole-trace comparison against the same public task verifier oracle; one task per run",
    "oracle_sha256": sha(oracle_path),
    "cases": results,
    "limitations": "Additional rows are correlated within a single episode, not independent tasks; the oracle is not independently validated here. No model was called.",
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2, sort_keys=True))
