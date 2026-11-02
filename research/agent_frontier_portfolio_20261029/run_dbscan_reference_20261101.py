#!/usr/bin/env python3
"""Run one released DBSCAN task solution and verifier in an offline container."""

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path


SOURCES = {1: "b25dbd168d4dd1a58873abfad38f1fccafab68cbbbf6cf9f79eb6114ab8e475e",
           2: "f17b89148e9db5fabd6eaa7f624df7ee0818634225ea97a106831630b8488981"}
EXPECTED = {1: "6732c58185de4e5f8a8e07db42ca76651185962e0d90b657123384b3a7dfdfb3",
            2: "dab29520a95adb2269818d450f912d40de4bd99cf54f8f80307de29e8361c26b"}
TEST_HASH = "7a652bc3112f01cb7a97fedbc15fc47b81bda442199b4c95b2f367ae0932aaff"
DATA = {"citsci_train.csv": "5a1169e807ceddec822fa676bac29f92562a3a463bd27178b15778c61b642f19",
        "expert_train.csv": "f7402b188f34c0dcf3c843545b15a486167d2e5770aec7cb5773fbb8aa777d92"}
PROJECTED_DATA = {"citsci_train.csv": "c7d14431e5b002691086708c7485e6b9097d4584adcc573bbe5fc1de166a7453",
                  "expert_train.csv": "71fd0da3fd70d2c09cb1b803d1916763f43d1f0adee5a9d889f43746dbc81407"}
IMAGE = "sha256:364db321fcc720859537bc04fab5c06a3be6ad0c87686a380b015a0d36c232ca"


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def execute(command, stdout, stderr, timeout, name):
    started = time.monotonic()
    with stdout.open("wb") as out, stderr.open("wb") as err:
        try:
            completed = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                       timeout=timeout, check=False)
            code = completed.returncode
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "kill", name], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=15, check=False)
            code = 124
    return {"exit_code": code, "elapsed_seconds": round(time.monotonic() - started, 3),
            "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("version", type=int, choices=(1, 2))
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--dependencies", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--data-override", type=Path, help="Use the fixed four-column projection")
    parser.add_argument("--timeout", type=int, default=1200)
    args = parser.parse_args()
    if args.timeout < 1:
        raise ValueError("timeout must be positive")
    task = args.checkout / "tasks/dbscan-parameter-tuning" / ("dbscan-parameter-tuning-" + str(args.version))
    source = task / "solution/solve.py"
    tests, original_data = task / "tests", task / "environment/data"
    data = args.data_override if args.data_override else original_data
    if sha(source) != SOURCES[args.version] or sha(tests / "expected_frontier.csv") != EXPECTED[args.version]:
        raise ValueError("released source or expected reference changed")
    if sha(tests / "test_outputs.py") != TEST_HASH:
        raise ValueError("released verifier changed")
    for name, expected in DATA.items():
        if sha(original_data / name) != expected:
            raise ValueError("input dataset changed: " + name)
    selected_hashes = PROJECTED_DATA if args.data_override else DATA
    for name, expected in selected_hashes.items():
        if sha(data / name) != expected:
            raise ValueError("selected input dataset changed: " + name)
    image_id = subprocess.check_output(["docker", "image", "inspect", "python:3.12-slim", "--format", "{{.Id}}"],
                                       text=True).strip()
    if image_id != IMAGE:
        raise ValueError("container image changed")
    args.output.mkdir(parents=True, exist_ok=False)
    work = args.output / "work"
    (work / "data").mkdir(parents=True)
    (work / "solution.py").touch()
    uid = str(os.getuid()) + ":" + str(os.getgid())
    common = ["docker", "run", "--rm", "--network", "none", "--read-only", "--user", uid,
              "--cpus", "2", "--memory", "3g", "--pids-limit", "128", "--cap-drop", "ALL",
              "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:rw,nosuid,size=256m",
              "-e", "HOME=/tmp", "-e", "PYTHONPATH=/deps", "-e", "OPENBLAS_NUM_THREADS=1",
              "-e", "OMP_NUM_THREADS=1", "-e", "MKL_NUM_THREADS=1", "-e", "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
              "--mount", f"type=bind,src={args.dependencies.resolve()},dst=/deps,readonly"]
    name = "dbscan-reference-" + str(os.getpid())
    # Recent SciPy emits a warning for each distance calculation. Preserve the
    # unsuppressed interrupted run separately, and silence only deprecations in
    # this long solver run; all other warnings and verifier output remain visible.
    solver = common + ["-e", "PYTHONWARNINGS=ignore::DeprecationWarning", "--name", name,
                       "--mount", f"type=bind,src={work.resolve()},dst=/root",
                       "--mount", f"type=bind,src={data.resolve()},dst=/root/data,readonly",
                       "--mount", f"type=bind,src={source.resolve()},dst=/root/solution.py,readonly",
                       "--workdir", "/root", "python:3.12-slim", "python3", "/root/solution.py"]
    run = execute(solver, args.output / "solver.stdout", args.output / "solver.stderr", args.timeout, name)
    verification = None
    if run["exit_code"] == 0:
        test_name = name + "-test"
        verify = common + ["--name", test_name, "--mount", f"type=bind,src={work.resolve()},dst=/root,readonly",
                           "--mount", f"type=bind,src={tests.resolve()},dst=/verifier,readonly",
                           "--workdir", "/root", "python:3.12-slim", "python3", "-m", "pytest", "-q",
                           "-p", "no:cacheprovider", "/verifier/test_outputs.py"]
        verification = execute(verify, args.output / "verifier.stdout", args.output / "verifier.stderr", 300, test_name)
    result_file = work / "pareto_frontier.csv"
    receipt = {"status": "SOURCE_REFERENCE_COMPATIBILITY_NOT_OFFICIAL_ENVIRONMENT", "task": args.version,
               "runner_sha256": sha(Path(__file__).resolve()),
               "source_sha256": SOURCES[args.version], "expected_sha256": EXPECTED[args.version],
               "test_sha256": TEST_HASH,
               "data_source": "four_column_projection" if args.data_override else "original_source",
               "data_sha256": selected_hashes, "original_data_sha256": DATA,
               "image": image_id, "solver": run, "verifier": verification,
               "output_sha256": sha(result_file) if result_file.is_file() else None,
               "timeout_seconds": args.timeout, "model_calls": 0,
               "solver_warning_filter": "ignore::DeprecationWarning",
               "limitation": "Current Python and scientific libraries differ from the published Dockerfile."}
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    main()
