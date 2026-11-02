#!/usr/bin/env python3
"""Adapt the actual source Agent program using the visible target metric.

This is a case-specific transparent control, not a learned Agent method.
The target verifier is mounted only after the adapted program has finished.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess

from audit_dbscan_agent_output_20261102 import analyze
from run_dbscan_agent_pilot_20261102 import verify_projection
from run_dbscan_reference_20261101 import EXPECTED, IMAGE, TEST_HASH, execute, sha


SOURCE_HASH = "00b252c6664870b8f9c7d503ef45f021dd15e1cb88ea026bc46028772c3b32f0"
ORIGINAL = "dbscan = DBSCAN(eps=epsilon, min_samples=min_samples)"
REPLACEMENT = "dbscan = DBSCAN(eps=epsilon, min_samples=min_samples, metric='chebyshev')"
OLD_COMMENT = "# Standard Euclidean in transformed space = custom metric in original space"
NEW_COMMENT = "# Standard Chebyshev in transformed space = custom metric in original space"


def adapt(text):
    if text.count(ORIGINAL) != 1 or text.count(OLD_COMMENT) != 1:
        raise ValueError("source program no longer matches the frozen control")
    return text.replace(ORIGINAL, REPLACEMENT).replace(OLD_COMMENT, NEW_COMMENT)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-receipt", type=Path, required=True)
    parser.add_argument("--projection", type=Path, required=True)
    parser.add_argument("--proof-root", type=Path, required=True)
    parser.add_argument("--dependencies", type=Path, required=True)
    parser.add_argument("--tests", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    receipt = json.loads(args.source_receipt.read_text(encoding="utf-8"))
    if (sha(args.source) != SOURCE_HASH or receipt.get("task") != "dbscan-parameter-tuning-1"
            or receipt.get("arm") != "no_skill" or receipt.get("agent_exit") != 0
            or receipt.get("verifier_exit") != 0):
        raise ValueError("actual successful source Agent program or receipt changed")
    proofs = verify_projection(args.projection, args.proof_root)
    if sha(args.tests / "expected_frontier.csv") != EXPECTED[2] or sha(args.tests / "test_outputs.py") != TEST_HASH:
        raise ValueError("target reference or verifier changed")
    image = subprocess.check_output(["docker", "image", "inspect", "python:3.12-slim", "--format", "{{.Id}}"],
                                    text=True).strip()
    if image != IMAGE:
        raise ValueError("container image changed")
    adapted = adapt(args.source.read_text(encoding="utf-8"))
    compile(adapted, "adapted_source_agent_program.py", "exec")
    provenance = {"status": "CASE_SPECIFIC_VISIBLE_RULE_CONTROL", "source_agent_program_sha256": SOURCE_HASH,
                  "source_agent_receipt_sha256": sha(args.source_receipt), "projection_proofs": proofs,
                  "agent_calls": 0, "training_runs": 0, "change": "DBSCAN metric: euclidean -> chebyshev"}
    if args.check:
        print(json.dumps(provenance))
        return
    args.output.mkdir(parents=True, exist_ok=False)
    work = args.output / "work"
    (work / "data").mkdir(parents=True)
    code = work / "adapted_source_agent_program.py"
    code.write_text(adapted, encoding="utf-8", newline="\n")
    uid = f"{os.getuid()}:{os.getgid()}"
    common = ["docker", "run", "--rm", "--network", "none", "--read-only", "--user", uid,
              "--cpus", "2", "--memory", "3g", "--pids-limit", "128", "--cap-drop", "ALL",
              "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:rw,nosuid,size=256m",
              "-e", "HOME=/tmp", "-e", "PYTHONPATH=/deps", "-e", "OPENBLAS_NUM_THREADS=1",
              "-e", "OMP_NUM_THREADS=1", "-e", "PYTHONWARNINGS=ignore::DeprecationWarning",
              "-e", "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
              "--mount", f"type=bind,src={args.dependencies.resolve()},dst=/deps,readonly"]
    name = "dbscan-metric-control-" + str(os.getpid())
    solver = common + ["--name", name, "--mount", f"type=bind,src={work.resolve()},dst=/root",
                       "--mount", f"type=bind,src={args.projection.resolve()},dst=/root/data,readonly",
                       "--workdir", "/root", "python:3.12-slim", "python3", "/root/" + code.name]
    run = execute(solver, args.output / "solver.stdout", args.output / "solver.stderr", 1200, name)
    verification = None
    if run["exit_code"] == 0:
        verify_name = name + "-test"
        verify = common + ["--name", verify_name, "--mount", f"type=bind,src={work.resolve()},dst=/root,readonly",
                           "--mount", f"type=bind,src={args.tests.resolve()},dst=/verifier,readonly",
                           "--workdir", "/root", "python:3.12-slim", "python3", "-m", "pytest", "-q",
                           "-p", "no:cacheprovider", "/verifier/test_outputs.py"]
        verification = execute(verify, args.output / "verifier.stdout", args.output / "verifier.stderr", 300, verify_name)
    result = work / "pareto_frontier.csv"
    outcome = {**provenance, "adapted_program_sha256": sha(code), "solver": run, "verifier": verification,
               "audit": analyze(result, args.tests / "expected_frontier.csv")}
    (args.output / "receipt.json").write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(outcome), flush=True)


if __name__ == "__main__":
    main()
