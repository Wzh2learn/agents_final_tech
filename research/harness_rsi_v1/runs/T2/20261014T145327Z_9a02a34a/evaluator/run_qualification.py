#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pass-id", required=True)
    args = parser.parse_args()
    evaluator_dir = Path(__file__).resolve().parent
    run_dir = evaluator_dir.parent
    evaluator = evaluator_dir / "evaluate.py"
    fixture_cases = sorted((evaluator_dir / "fixtures").glob("*.json"))
    t1_cases = sorted((run_dir / "qualification_cases" / "t1").glob("*.json"))
    case_paths = fixture_cases + t1_cases
    results = []
    failures = []
    for case_path in case_paths:
        with case_path.open("r", encoding="utf-8") as handle:
            bundle = json.load(handle)
        command = [
            sys.executable,
            str(evaluator),
            "--case",
            str(case_path),
            "--out",
            "-",
        ]
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError:
            result = {"decision": "INVALID_OUTPUT"}
        expected_decision = bundle.get("expected_category")
        expected_exit = 3 if case_path.parent.name == "fixtures" and case_path.stem.endswith("_failclosed") else 0
        actual_decision = result.get("decision")
        matched = actual_decision == expected_decision and completed.returncode == expected_exit
        record = {
            "case_id": case_path.stem,
            "case_path": str(case_path.relative_to(run_dir)),
            "origin": bundle.get("source", {}).get("origin"),
            "failure_family": bundle.get("failure_family"),
            "expected": expected_decision,
            "actual": actual_decision,
            "expected_exit_code": expected_exit,
            "actual_exit_code": completed.returncode,
            "fail_closed_code": result.get("fail_closed_code"),
            "matched": matched,
        }
        results.append(record)
        if not matched:
            failures.append(record)
    output = {
        "schema": "harness_rsi_t2_qualification_pass_v1",
        "pass_id": args.pass_id,
        "case_count": len(results),
        "fixture_case_count": len(fixture_cases),
        "t1_case_count": len(t1_cases),
        "command_template": "python3 evaluator/evaluate.py --case <bundle.json> --out -",
        "runner_command": f"python3 evaluator/run_qualification.py --pass-id {args.pass_id}",
        "runner_exit_code": 1 if failures else 0,
        "matched_count": len(results) - len(failures),
        "results": results,
        "failures": failures,
        "stderr_empty": all(not item["actual_exit_code"] for item in failures) if failures else True,
    }
    sys.stdout.write(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
