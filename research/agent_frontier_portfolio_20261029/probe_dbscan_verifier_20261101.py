#!/usr/bin/env python3
"""White-box controls for one released DBSCAN verifier; no Agent is invoked."""

import argparse
import csv
import json
import os
import subprocess
from decimal import Decimal
from pathlib import Path

from run_dbscan_reference_20261101 import EXPECTED, IMAGE, execute, sha


TEST_HASH = "7a652bc3112f01cb7a97fedbc15fc47b81bda442199b4c95b2f367ae0932aaff"
FIELDS = ("F1", "delta", "min_samples", "epsilon", "shape_weight")
PARAMETERS = ("min_samples", "epsilon", "shape_weight")


def write_rows(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--dependencies", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    tests = args.checkout / "tasks/dbscan-parameter-tuning/dbscan-parameter-tuning-1/tests"
    if sha(tests / "test_outputs.py") != TEST_HASH or sha(tests / "expected_frontier.csv") != EXPECTED[1]:
        raise ValueError("released verifier or expected frontier changed")
    if sha(args.baseline) != EXPECTED[1]:
        raise ValueError("baseline is not the byte-identical reference output")
    image = subprocess.check_output(["docker", "image", "inspect", "python:3.12-slim", "--format", "{{.Id}}"], text=True).strip()
    if image != IMAGE:
        raise ValueError("container image changed")

    with args.baseline.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(FIELDS):
            raise ValueError("unexpected baseline schema")
        rows = list(reader)
    keys = [tuple(row[key] for key in PARAMETERS) for row in rows]
    if not rows or len(set(keys)) != len(keys):
        raise ValueError("expected unique nonempty baseline parameters")
    if min(Decimal(row["F1"]) for row in rows) <= 0 or min(Decimal(row["delta"]) for row in rows) <= 0:
        raise ValueError("constructed outside-frontier control no longer applies")
    invented = dict(rows[0])
    invented["F1"] = "0"
    invented["delta"] = str(min(Decimal(row["delta"]) for row in rows) / 2)
    assert tuple(invented[key] for key in PARAMETERS) == keys[0]
    assert invented["F1"] != rows[0]["F1"] and invented["delta"] != rows[0]["delta"]

    args.output.mkdir(parents=True, exist_ok=False)
    cases = {"baseline": rows, "missing_first": rows[1:], "contradictory_extra": rows + [invented]}
    results = {}
    uid = str(os.getuid()) + ":" + str(os.getgid())
    for case, contents in cases.items():
        case_dir = args.output / case
        case_dir.mkdir()
        result = case_dir / "pareto_frontier.csv"
        write_rows(result, contents)
        name = f"dbscan-verifier-{os.getpid()}-{case.replace('_', '-')}"
        command = ["docker", "run", "--rm", "--network", "none", "--read-only", "--user", uid,
                   "--cpus", "2", "--memory", "3g", "--pids-limit", "128", "--cap-drop", "ALL",
                   "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:rw,nosuid,size=256m",
                   "-e", "HOME=/tmp", "-e", "PYTHONPATH=/deps", "-e", "PYTHONDONTWRITEBYTECODE=1",
                   "-e", "OPENBLAS_NUM_THREADS=1", "-e", "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
                   "--mount", f"type=bind,src={args.dependencies.resolve()},dst=/deps,readonly",
                   "--mount", f"type=bind,src={case_dir.resolve()},dst=/root,readonly",
                   "--mount", f"type=bind,src={tests.resolve()},dst=/verifier,readonly",
                   "--workdir", "/root", "--name", name, "python:3.12-slim", "python3", "-m", "pytest", "-q",
                   "-p", "no:cacheprovider", "/verifier/test_outputs.py"]
        run = execute(command, args.output / (case + ".stdout"), args.output / (case + ".stderr"), 120, name)
        results[case] = {"rows": len(contents), "candidate_sha256": sha(result), **run}
    receipt = {"source_task": 1, "source_test_sha256": TEST_HASH, "expected_sha256": EXPECTED[1],
               "image": image, "baseline_row": rows[0], "invented_row": invented,
               "cases": results, "model_calls": 0,
               "design": "white-box, reference-derived controls; no Agent or human ground truth"}
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    main()
