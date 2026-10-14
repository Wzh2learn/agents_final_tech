#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def apply_mutation(call: dict[str, Any], mutation: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(call)
    path = mutation["path"]
    cursor: Any = result
    for component in path[:-1]:
        cursor = cursor[component]
    final = path[-1]
    if mutation["operation"] == "replace":
        cursor[final] = copy.deepcopy(mutation["value"])
    elif mutation["operation"] == "replace_runtime":
        cursor[final] = copy.deepcopy(mutation["value"])
    elif mutation["operation"] == "delete":
        del cursor[final]
    elif mutation["operation"] == "insert":
        cursor[final][mutation["key"]] = copy.deepcopy(mutation["value"])
    else:
        raise ValueError(f"unsupported mutation operation: {mutation['operation']}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--definitions", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--round-id", required=True, choices=["PASS_1", "PASS_2"])
    args = parser.parse_args()
    run_root = Path(args.run_root).resolve()
    definitions = json.loads(Path(args.definitions).read_text(encoding="utf-8"))
    fixture_root = run_root / "recipe_fixtures"
    validator = run_root / "caller_validator.py"
    output = Path(args.output)
    if output.exists():
        raise SystemExit("refuse to overwrite probe result")
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        for definition in definitions["cases"]:
            fixture_path = fixture_root / definition["fixture"]
            call = json.loads(fixture_path.read_text(encoding="utf-8"))
            if "mutation" in definition:
                call = apply_mutation(call, definition["mutation"])
            if "mutations" in definition:
                for mutation in definition["mutations"]:
                    call = apply_mutation(call, mutation)
            call_text = json.dumps(call, ensure_ascii=False, sort_keys=True)
            started = time.perf_counter()
            completed = subprocess.run(
                [
                    "python3",
                    str(validator),
                    "--interfaces",
                    str(run_root / "recipe_interfaces.json"),
                    "--operations",
                    str(run_root / "registered_operations.json"),
                    "--run-root",
                    str(run_root),
                    "--call-stdin",
                ],
                input=call_text,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=20,
                check=False,
            )
            duration_ms = round((time.perf_counter() - started) * 1000, 3)
            try:
                result = json.loads(completed.stdout)
            except json.JSONDecodeError:
                result = {"validation_status": "MALFORMED_RESULT", "fail_closed_code": "FC_INTERNAL"}
            expected = definition["expected"]
            actual = "ACCEPT" if completed.returncode == 0 and result.get("validation_status") == "ACCEPTED_WITHIN_SCOPE" else "REJECT"
            passed = (
                actual == expected
                and result.get("fail_closed_code") == definition["expected_fail_closed_code"]
                and (actual == "ACCEPT") == bool(result.get("target_execution_performed"))
            )
            record = {
                "schema": "jinrong_t5_probe_result_v2",
                "round_id": args.round_id,
                "case_id": definition["case_id"],
                "recipe_id": definition["recipe_id"],
                "expected": expected,
                "expected_fail_closed_code": definition["expected_fail_closed_code"],
                "actual": actual,
                "actual_fail_closed_code": result.get("fail_closed_code"),
                "caller_exit_code": completed.returncode,
                "target_execution_performed": result.get("target_execution_performed", False),
                "operation_result_count": len(result.get("operation_results", [])),
                "duration_ms": duration_ms,
                "passed": passed,
                "caller_stdout": completed.stdout,
                "caller_stderr": completed.stderr,
            }
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            stream.flush()
            if not passed:
                return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
