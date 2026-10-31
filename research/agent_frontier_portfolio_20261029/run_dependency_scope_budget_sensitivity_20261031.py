#!/usr/bin/env python3
"""Run the pinned scope pilot under a separately recorded larger budget."""

import hashlib
import json
from pathlib import Path
import sys


PINNED = "02b3936d6f9139dcaf9f6ebc99d746c27a2ce7500cef6420ca4e9e060bb8a7e1"
ALLOWED = {"target_none", "target_history", "target_generated_skill", "target_native_skills"}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ALLOWED:
        raise SystemExit("only target conditions are permitted")
    source = Path(__file__).resolve().parent / "run_dependency_scope_agent_20261031.py"
    data = source.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual != PINNED:
        raise ValueError("base scope adapter differs from frozen version")
    text = data.decode("utf-8")
    changes = [
        ("dependency_scope_agent_pilot_20261031/agent_runs",
         "dependency_scope_budget_sensitivity_20261031/agent_runs", 1),
        ("len(calls)>=16", "len(calls)>=32", 2),
        ("sum(payload_bytes)+length>900000", "sum(payload_bytes)+length>2400000", 1),
        ("stderr=subprocess.PIPE,timeout=600)", "stderr=subprocess.PIPE,timeout=900)", 1),
        ('"max_forwarded_http": 16', '"max_forwarded_http": 32', 1),
        ('"max_post_bytes": 900000', '"max_post_bytes": 2400000', 1),
        ('"agent_timeout_seconds": 600', '"agent_timeout_seconds": 900', 1),
        ("DEVELOPMENT_NOT_OFFICIAL_HARNESS", "POSTHOC_BUDGET_SENSITIVITY", 1),
    ]
    for before, after, expected in changes:
        if text.count(before) != expected:
            raise ValueError("unexpected adapter fragment: " + before)
        text = text.replace(before, after)
    compile(text, str(source), "exec")
    print(json.dumps({"status": "POSTHOC_BUDGET_SENSITIVITY",
                      "adapter_sha256": actual,
                      "budget_adapter_sha256": hashlib.sha256(text.encode()).hexdigest()}), flush=True)
    namespace = {"__name__": "__main__", "__file__": str(source)}
    exec(compile(text, str(source), "exec"), namespace)


if __name__ == "__main__":
    main()
