#!/usr/bin/env python3
"""Reproduce privileged, isolated controls against public benchmark tests.

This is a retrospective verifier qualification, not a prospective Agent
evaluation.  Reference answers are copied solely to isolate each predicate.
"""

import argparse
import hashlib
import json
import re
import runpy
import subprocess
import sys
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args):
    args.output.mkdir(parents=True, exist_ok=False)
    image_id = subprocess.check_output(
        ["docker", "image", "inspect", args.image, "--format", "{{.Id}}"], text=True
    ).strip()
    records = []
    for task in sorted(args.tasks.glob("enterprise-information-search-*")):
        test = task / "tests/test_outputs.py"
        question = task / "environment/question.txt"
        data = task / "environment/DATA"
        question_text = question.read_text(encoding="utf-8")
        question_keys = re.findall(r'^\s*"(q\d+)"\s*:', question_text, re.M)
        context = runpy.run_path(str(test))
        expected = context["EXPECTED_ANSWERS"]
        if "q2" not in question_keys or "q2" in expected or not expected:
            raise ValueError(f"Unexpected reference/question contract for {task.name}")
        exact = {key: {"answer": list(value), "tokens": 1} for key, value in expected.items()}
        with_placeholder = dict(exact, q2={"answer": [], "tokens": 1})
        omitted = dict(exact)
        extra = {key: {"answer": list(value) + ["__NOT_AN_EMPLOYEE_ID_OR_URL__"],
                       "tokens": 1} for key, value in expected.items()}
        bad_tokens = {key: {"answer": list(value), "tokens": -123} for key, value in expected.items()}
        missing = {key: {"answer": list(value), "tokens": 1} for key, value in expected.items()}
        first = next(key for key, value in expected.items() if value)
        missing[first]["answer"].pop()
        cases = {"placeholder_q2": with_placeholder, "omitted_q2": omitted,
                 "extra_impossible_item": extra, "negative_token_count": bad_tokens,
                 "missing_required_item": missing}
        for label, answer in cases.items():
            folder = args.output / task.name / label
            folder.mkdir(parents=True)
            answer_path = folder / "answer.json"
            answer_path.write_text(json.dumps(answer, indent=2) + "\n", encoding="utf-8")
            command = [
                "docker", "run", "--rm", "--network", "none", "--read-only", "--user", "0:0",
                "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
                "-e", "PYTHONPATH=/deps", "-e", "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
                "-e", "PYTHONDONTWRITEBYTECODE=1",
                "-v", f"{args.site_packages.resolve()}:/deps:ro",
                "-v", f"{test.resolve()}:/tests/test_outputs.py:ro",
                "-v", f"{data.resolve()}:/root/DATA:ro",
                "-v", f"{question.resolve()}:/root/question.txt:ro",
                "-v", f"{answer_path.resolve()}:/root/answer.json:ro",
                args.image, "python", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                "/tests/test_outputs.py",
            ]
            process = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, timeout=60)
            log = folder / "verifier.log"
            log.write_text(process.stdout, encoding="utf-8")
            records.append({"task": task.name, "case": label, "exit_code": process.returncode,
                            "question_keys": question_keys, "expected_keys": list(expected),
                            "question_sha256": digest(question), "test_sha256": digest(test),
                            "fixture_sha256": digest(answer_path), "log_sha256": digest(log)})
    if not records:
        raise ValueError("No enterprise task found")
    summary = {"status": "POSTHOC_PRIVILEGED_TEST_CONTROLS_NOT_AGENT_OUTPUTS",
               "benchmark_commit": "726e1f79b96b0cb3d729d0e55a1c847e0b5353ae",
               "image_id": image_id, "pytest": "9.0.1 via mounted research venv",
               "source_sha256": digest(Path(__file__)), "records": records}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(records), "exit_codes": {
        case: [r["exit_code"] for r in records if r["case"] == case]
        for case in sorted({r["case"] for r in records})}}, ensure_ascii=False))
    if any(r["exit_code"] != 0 for r in records if r["case"] == "placeholder_q2"):
        sys.exit("Infrastructure/control failure: baseline must pass; inspect retained logs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--site-packages", type=Path, required=True)
    parser.add_argument("--image", default="python-sandbox:latest")
    run(parser.parse_args())
