#!/usr/bin/env python3
"""Check persisted verifier controls without publishing answer fixtures."""
import argparse
import hashlib
import json
from pathlib import Path


def inspect(root, audit):
    result = {}
    for task, numbers in audit["tasks"].items():
        arms = {}
        for arm in ("reference", "separated_literals"):
            case = root / task / arm
            log = (case / "verifier.log").read_bytes()
            text = log.decode("utf-8", errors="replace")
            answer_path = case / "answers.json"
            answer = json.loads(answer_path.read_text(encoding="utf-8"))
            expected_value = numbers["expected_q2"] if arm == "reference" else numbers["separate_literals_count"]
            if answer.get("q2_answer") != expected_value:
                raise ValueError("fixture does not match audit")
            passed = "2 passed" in text and "failed" not in text.lower()
            rejected_q2 = ("1 failed, 1 passed" in text and
                           f"assert {numbers['separate_literals_count']} == {numbers['expected_q2']}" in text)
            if (arm == "reference" and not passed) or (arm != "reference" and not rejected_q2):
                raise ValueError("verifier output differs from expected control")
            arms[arm] = {"verifier_pass": passed, "q2_value": expected_value,
                         "verifier_log_sha256": hashlib.sha256(log).hexdigest(),
                         "fixture_sha256": hashlib.sha256(answer_path.read_bytes()).hexdigest()}
        result[task] = arms
    return {"status": "PRIVILEGED_VERIFIER_CONTROLS_NOT_AGENT_OUTPUTS", "tasks": result,
            "limitations": ["q1/q3/q4 copied from expected answers to isolate q2",
                            "runs original pytest assertions in an adapted offline container, not upstream test.sh",
                            "separate literals are not independently certified financial gold"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("audit", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    result = inspect(args.root, json.loads(args.audit.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
