#!/usr/bin/env python3
"""Offline, development-only replay of SkillEvolBench's source retry task.

Runs its embedded verifier Python without the shell wrapper's pip-install step.
The upstream task assets are supplied externally and are not copied to this repo.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

from run_dbscan_reference_20261101 import IMAGE, execute, sha


COMMIT = "9e3daa339987c3cfa624121e1be442593a53d43c"
PINNED = {
    "instruction.md": "c18b7eaca12ab129917000dc38d809747fc9676e5d2771065c6ae64df3af8e8a",
    "task-spec.yaml": "ab9efd89f45d17313f6cacf2b9fccee6bc19bdb8c4a6aa14632f71c0f522978c",
    "environment/retry_client.py": "eaba72c96a18d42c8d8d074ceae9a4def738e4b1aed98e0c85d43bbc83a933a2",
    "environment/mock_api.py": "0771ed9a42eaa0342bf76fc62ea27e3810a7a287b3d1990a14971797fe06a8e3",
    "environment/rate_limit_policy.py": "5b8fd5e7fb4babc0206c2520bbf4ddf7adfcac083b8cf2cc7196b3c8f75593f6",
    "environment/request_journal.py": "fc9ab820638e43d1c968b2d1a2c1984a555b236f005ebd79407d59129ed63f4f",
    "solution/solve.sh": "39ffd9826dd52f5ef22fbced9b6e483f23ddda62bb4096c3df0e1e46f338214e",
    "tests/test.sh": "e51f8c82a375e594c8e7e4350be722b56a3d1d159fef137e6405b9c1097181a2",
    "tests/test_outcome.py": "c9d00e2d0c88295601578a26191a17cd37c73427a43f98fb83943de8e27b282b",
    "tests/test_process.py": "fe878a3527d2fe92570e2cdfa6d73b223a5da2097b71d0f2eb95ce126fb8a9c8",
}
MARKER = "\"$PYTHON_BIN\" - <<'PY'\n"


def embedded_verifier(text):
    if text.count(MARKER) != 1:
        raise ValueError("upstream verifier wrapper changed")
    body, ending = text.split(MARKER, 1)[1].split("\nPY\n", 1)
    if "exit 0" not in ending:
        raise ValueError("upstream verifier termination changed")
    compile(body, "upstream_embedded_verifier.py", "exec")
    return body + "\n"


def validate(task, checkout):
    head = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
    if head != COMMIT:
        raise ValueError("source checkout revision changed")
    for name, expected in PINNED.items():
        if sha(task / name) != expected:
            raise ValueError("source asset changed: " + name)
    image = subprocess.check_output(["docker", "image", "inspect", "python:3.12-slim", "--format", "{{.Id}}"],
                                    text=True).strip()
    if image != IMAGE:
        raise ValueError("container image changed")
    return embedded_verifier((task / "tests/test.sh").read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    verifier = validate(args.task, args.checkout)
    if args.check:
        print(json.dumps({"status": "ASSETS_AND_EMBEDDED_VERIFIER_CHECKED", "model_calls": 0}))
        return
    args.output.mkdir(parents=True, exist_ok=False)
    verifier_file = args.output / "embedded_verifier.py"
    verifier_file.write_text(verifier, encoding="utf-8", newline="\n")
    uid = f"{os.getuid()}:{os.getgid()}"
    common = ["docker", "run", "--rm", "--network", "none", "--read-only", "--user", uid,
              "--cpus", "1", "--memory", "1g", "--pids-limit", "128", "--cap-drop", "ALL",
              "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:rw,nosuid,size=256m", "-e", "HOME=/tmp"]
    results = {}
    for variant in ("starter", "released_solution", "empty_result_negative_control"):
        folder = args.output / variant
        folder.mkdir()
        project, logs = folder / "project", folder / "logs"
        shutil.copytree(args.task / "environment", project)
        logs.mkdir()
        # The upstream Dockerfile removes only its own copied Dockerfile.
        (project / "Dockerfile").unlink()
        solver = None
        if variant == "released_solution":
            name = "skillevol-retry-solve-" + str(os.getpid())
            cmd = common + ["--name", name, "-e", "PROJECT_ROOT=/project",
                            "--mount", f"type=bind,src={project.resolve()},dst=/project",
                            "--mount", f"type=bind,src={(args.task / 'solution').resolve()},dst=/oracle,readonly",
                            "python:3.12-slim", "bash", "/oracle/solve.sh"]
            solver = execute(cmd, folder / "solver.stdout", folder / "solver.stderr", 120, name)
        elif variant == "empty_result_negative_control":
            client = project / "retry_client.py"
            with client.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write("\n# Retry-After\ndef fetch_cases(case_ids, api, clock, max_retries=3):\n    return {}\n")
        name = "skillevol-retry-test-" + variant + "-" + str(os.getpid())
        cmd = common + ["--name", name, "-e", "PROJECT_ROOT=/project", "-e", "SCRIPT_DIR=/asset/tests",
                        "-e", "LOG_DIR=/logs", "--mount", f"type=bind,src={project.resolve()},dst=/project,readonly",
                        "--mount", f"type=bind,src={args.task.resolve()},dst=/asset,readonly",
                        "--mount", f"type=bind,src={logs.resolve()},dst=/logs",
                        "--mount", f"type=bind,src={verifier_file.resolve()},dst=/verifier.py,readonly",
                        "python:3.12-slim", "python3", "/verifier.py"]
        verify = execute(cmd, folder / "verifier.stdout", folder / "verifier.stderr", 120, name)
        files = {}
        for filename in ("reward.json", "outcome_report.json", "process_report.json", "score_report.json"):
            path = logs / filename
            if path.is_file():
                files[filename] = {"sha256": sha(path), "content": json.loads(path.read_text(encoding="utf-8"))}
        results[variant] = {"solution": solver, "verification": verify,
                            "client_sha256": sha(project / "retry_client.py"), "reports": files}
    outcome = {"status": "DEVELOPMENT_OFFLINE_EMBEDDED_VERIFIER_NOT_OFFICIAL_HARNESS", "source_commit": COMMIT,
               "pinned_assets": PINNED, "embedded_verifier_sha256": sha(verifier_file), "image": IMAGE,
               "variants": results, "model_calls": 0, "training_runs": 0,
               "limitations": "Python 3.12 slim and extracted verifier body; shell wrapper pip-install and official agent runtime omitted."}
    (args.output / "receipt.json").write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(outcome), flush=True)


if __name__ == "__main__":
    main()
