#!/usr/bin/env python3
"""Post-hoc behavior checks for the retry acquisition task, without model calls."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from run_dbscan_reference_20261101 import IMAGE, sha


QUALIFICATION_HASH = "022c731ee609d60989e433653ebe0b0c35b180018868b41259e535afd8879f06"
SOURCE_RAW_HASH = "14dbba560ff536baa4ed5af1bd7456ef40cff966dcd42adeac9ab6c41d6a7c4c"


def regular_case(fetch, api_class, clock_class, delay):
    api, clock = api_class({"probe": delay}), clock_class()
    try:
        result = fetch(["probe"], api, clock, max_retries=3)
        correct = result == {"probe": {"case_id": "probe", "value": "payload-probe"}}
        wait_ok = delay == 0 or bool(clock.sleep_calls) and clock.sleep_calls[0] >= delay
        return {"delay": delay, "passed": bool(correct and wait_ok),
                "calls": len(api.trace), "waits": clock.sleep_calls}
    except Exception as exc:
        return {"delay": delay, "passed": False, "error_type": type(exc).__name__}


def bounded_case(fetch, clock_class, limit):
    class AlwaysLimited:
        def __init__(self):
            self.calls = 0

        def get_resource(self, case_id, clock):
            self.calls += 1
            return {"status": 429, "headers": {"Retry-After": "1"}, "body": {}}

    api, clock = AlwaysLimited(), clock_class()
    try:
        fetch(["probe"], api, clock, max_retries=limit)
        return {"max_retries": limit, "passed": False, "reason": "returned_without_success"}
    except RuntimeError:
        return {"max_retries": limit, "passed": api.calls == limit + 1 and len(clock.sleep_calls) == limit,
                "calls": api.calls, "waits": len(clock.sleep_calls)}
    except Exception as exc:
        return {"max_retries": limit, "passed": False, "error_type": type(exc).__name__}


def inside():
    sys.path.insert(0, "/project")
    from mock_api import FakeClock, RateLimitAPI
    from retry_client import fetch_cases
    regular = [regular_case(fetch_cases, RateLimitAPI, FakeClock, delay) for delay in (0, 1, 2, 5, 9, 17)]
    bounded = [bounded_case(fetch_cases, FakeClock, limit) for limit in (0, 1, 3)]
    print(json.dumps({"regular": regular, "bounded": bounded,
                      "passed": sum(row["passed"] for row in regular + bounded),
                      "total": len(regular) + len(bounded)}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inside", action="store_true")
    parser.add_argument("--qualification", type=Path)
    parser.add_argument("--agent-case", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.inside:
        inside()
        return
    if not all((args.qualification, args.agent_case, args.output)):
        parser.error("qualification, agent-case and output are required")
    if sha(args.qualification / "receipt.json") != QUALIFICATION_HASH:
        raise ValueError("qualification receipt changed")
    agent_receipt = json.loads((args.agent_case / "receipt.json").read_text(encoding="utf-8"))
    if (agent_receipt.get("raw_sha256") != SOURCE_RAW_HASH
            or sha(args.agent_case / "raw.jsonl") != SOURCE_RAW_HASH
            or agent_receipt.get("task") != "429-with-retry-after-header"):
        raise ValueError("source Agent trace changed")
    if args.output.exists():
        raise FileExistsError("refusing to overwrite an existing behavior probe")
    image = subprocess.check_output(["docker", "image", "inspect", "python:3.12-slim", "--format", "{{.Id}}"],
                                    text=True).strip()
    if image != IMAGE:
        raise ValueError("container image changed")
    uid = f"{os.getuid()}:{os.getgid()}"
    projects = {"starter": args.qualification / "starter/project",
                "released_solution": args.qualification / "released_solution/project",
                "agent_solution": args.agent_case / "work/task"}
    results = {}
    script = Path(__file__).resolve()
    # The probe itself imports only stdlib in the container. Mount the project's
    # hash helper read-only because its top-level import defines sha/IMAGE.
    helper = script.parent / "run_dbscan_reference_20261101.py"
    for label, project in projects.items():
        command = ["docker", "run", "--rm", "--network", "none", "--read-only", "--user", uid,
                   "--cpus", "1", "--memory", "512m", "--pids-limit", "64", "--cap-drop", "ALL",
                   "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:rw,nosuid,size=32m",
                   "-e", "PYTHONDONTWRITEBYTECODE=1", "--mount", f"type=bind,src={project.resolve()},dst=/project,readonly",
                   "--mount", f"type=bind,src={script},dst=/probe.py,readonly",
                   "--mount", f"type=bind,src={helper},dst=/run_dbscan_reference_20261101.py,readonly",
                   "python:3.12-slim", "python3", "/probe.py", "--inside"]
        result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=60, check=False)
        results[label] = {"exit_code": result.returncode,
                          "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
                          "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
                          "checks": json.loads(result.stdout) if result.returncode == 0 else None,
                          "retry_client_sha256": sha(project / "retry_client.py"),
                          "policy_sha256": sha(project / "rate_limit_policy.py")}
    output = {"status": "POSTHOC_DEVELOPMENT_BEHAVIOR_PROBE", "source_agent_raw_sha256": SOURCE_RAW_HASH,
              "qualification_sha256": QUALIFICATION_HASH, "probe_sha256": sha(script),
              "model_calls": 0, "cases": results,
              "limitation": "One task, a finite mock-input suite, and checks designed after observing the verifier failure."}
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"receipt_sha256": sha(args.output), "results": {k: v["checks"] for k, v in results.items()}}))


if __name__ == "__main__":
    main()
