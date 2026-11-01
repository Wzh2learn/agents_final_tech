#!/usr/bin/env python3
"""Run the pinned isolated scope adapter on a selected frozen project."""

import hashlib
import json
from pathlib import Path
import sys


PINNED = "02b3936d6f9139dcaf9f6ebc99d746c27a2ce7500cef6420ca4e9e060bb8a7e1"
CONDITIONS = {"target_none", "target_history", "target_generated_skill", "target_native_skills"}
PROJECTS = {"react", "node"}


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in PROJECTS or sys.argv[2] not in CONDITIONS:
        raise SystemExit("usage: run_cross_project_cvss PROJECT CONDITION [adapter options]")
    project, condition = sys.argv[1:3]
    source = Path(__file__).resolve().parent / "run_dependency_scope_agent_20261031.py"
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != PINNED:
        raise ValueError("scope adapter differs from frozen version")
    text = data.decode("utf-8")
    changes = [
        ("dependency_scope_agent_pilot_20261031/agent_runs",
         "dependency_cross_project_20261101/" + project + "/agent_runs", 1),
        ("len(calls)>=16", "len(calls)>=32", 2),
        ("sum(payload_bytes)+length>900000", "sum(payload_bytes)+length>2400000", 1),
        ("stderr=subprocess.PIPE,timeout=600)", "stderr=subprocess.PIPE,timeout=900)", 1),
        ('"max_forwarded_http": 16', '"max_forwarded_http": 32', 1),
        ('"max_post_bytes": 900000', '"max_post_bytes": 2400000', 1),
        ('"agent_timeout_seconds": 600', '"agent_timeout_seconds": 900', 1),
        ("DEVELOPMENT_NOT_OFFICIAL_HARNESS", "CROSS_PROJECT_DEVELOPMENT", 1),
    ]
    for old, new, count in changes:
        if text.count(old) != count:
            raise ValueError("unexpected adapter fragment: " + old)
        text = text.replace(old, new)
    compile(text, str(source), "exec")
    print(json.dumps({"project": project, "condition": condition,
                      "adapter_sha256": PINNED,
                      "derived_sha256": hashlib.sha256(text.encode()).hexdigest()}), flush=True)
    sys.argv = [str(source), condition] + sys.argv[3:]
    exec(compile(text, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})


if __name__ == "__main__":
    main()
