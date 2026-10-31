#!/usr/bin/env python3
"""Make privileged verifier controls differing only in one computed answer.

These are not Agent outputs. They deliberately use the benchmark's expected
answers for all unchanged fields to isolate its q2 predicate.
"""
import argparse
import json
from pathlib import Path


def prepare(reference, alternative):
    expected = dict(reference)
    counterfactual = dict(reference)
    if "q2_answer" not in reference or alternative == reference["q2_answer"]:
        raise ValueError("q2 reference missing or counterfactual unchanged")
    counterfactual["q2_answer"] = alternative
    return expected, counterfactual


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task_root", type=Path)
    ap.add_argument("literal_audit", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    audit = json.loads(args.literal_audit.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=False)
    for task, value in audit["tasks"].items():
        reference = json.loads((args.task_root / task / "tests/expected_output.json").read_text(encoding="utf-8"))
        original, alternative = prepare(reference, value["separate_literals_count"])
        for arm, answer in (("reference", original), ("separated_literals", alternative)):
            dest = args.output / task / arm
            dest.mkdir(parents=True)
            (dest / "answers.json").write_text(json.dumps(answer, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PRIVILEGED_VERIFIER_CONTROLS_NOT_AGENT_OUTPUTS", "tasks": list(audit["tasks"])}))


if __name__ == "__main__":
    main()
