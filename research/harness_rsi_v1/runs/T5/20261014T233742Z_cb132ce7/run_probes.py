#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def apply_mutation(call: dict[str, Any], mutation: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(call)
    cursor: Any = result
    for component in mutation["path"][:-1]:
        cursor = cursor[component]
    final = mutation["path"][-1]
    if mutation["operation"] in {"replace", "replace_runtime"}:
        cursor[final] = copy.deepcopy(mutation["value"])
    elif mutation["operation"] == "delete":
        del cursor[final]
    elif mutation["operation"] == "insert":
        cursor[final][mutation["key"]] = copy.deepcopy(mutation["value"])
    else:
        raise ValueError(f"unsupported mutation operation: {mutation['operation']}")
    return result


def runtime_tick(run_root: Path, runtime_root: Path) -> Path:
    source = json.loads((run_root / "recipe_fixtures/dispatch/tick_valid.json").read_text(encoding="utf-8"))
    source["observed_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    source["watcher"] = str((run_root / "recipe_fixtures/dispatch/watcher.sh").resolve())
    destination = runtime_root / "tick_valid.json"
    destination.write_text(json.dumps(source, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return destination


def substituted_registry(run_root: Path, runtime_root: Path) -> Path:
    registry = json.loads((run_root / "registered_operations.json").read_text(encoding="utf-8"))
    decoy = runtime_root / "decoy_operation.sh"
    marker = runtime_root / "decoy_executed.marker"
    decoy.write_text(f"#!/usr/bin/env bash\ntouch {marker}\nexit 0\n", encoding="utf-8", newline="\n")
    os.chmod(decoy, 0o755)
    entry = next(item for item in registry["operations"] if item["op_id"] == "OP-T4-R-DISPATCH-PRECHECK")
    entry["target"]["path"] = str(decoy)
    destination = runtime_root / "operations_substituted.json"
    destination.write_text(json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return destination


def normalize(record: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "case_id",
        "recipe_id",
        "expected",
        "expected_fail_closed_code",
        "actual",
        "actual_fail_closed_code",
        "target_execution_performed",
        "operation_result_count",
        "passed",
        "decoy_execution_performed",
    ]
    return {key: record.get(key) for key in keys}


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--definitions", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--round-id", required=True, choices=["PASS_1", "PASS_2"])
    args = parser.parse_args()
    run_root = Path(args.run_root).resolve()
    definitions_path = Path(args.definitions).resolve()
    definitions = json.loads(definitions_path.read_text(encoding="utf-8"))
    fixture_root = run_root / "recipe_fixtures"
    validator = run_root / "caller_validator.py"
    output = Path(args.output).resolve()
    if output == run_root or run_root in output.parents:
        raise SystemExit("probe output must be outside the delivered run tree")
    if output.exists():
        raise SystemExit("refuse to overwrite probe result")
    output.parent.mkdir(parents=True, exist_ok=True)
    records = []
    with tempfile.TemporaryDirectory(prefix="t5_v3_runtime_", dir=output.parent) as temporary:
        runtime_root = Path(temporary).resolve()
        delivered_tick = json.loads((run_root / "recipe_fixtures/dispatch/tick_valid.json").read_text(encoding="utf-8"))
        delivered_watcher = str((run_root / "recipe_fixtures/dispatch/watcher.sh").resolve())
        relocated_runtime_tick = delivered_tick.get("watcher") != delivered_watcher
        if relocated_runtime_tick:
            relocated = copy.deepcopy(delivered_tick)
            relocated["watcher"] = delivered_watcher
            (runtime_root / "tick_relocated.json").write_text(json.dumps(relocated, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        for definition in definitions["cases"]:
            fixture_path = fixture_root / definition["fixture"]
            call = json.loads(fixture_path.read_text(encoding="utf-8"))
            for mutation in [definition.get("mutation")] if definition.get("mutation") else []:
                call = apply_mutation(call, mutation)
            for mutation in definition.get("mutations", []):
                call = apply_mutation(call, mutation)
            if "pin_source" in definition:
                pin_path = fixture_root / definition["pin_source"]
                pin = pin_path.read_text(encoding="utf-8").strip()
                call.pop("pin_source_reference", None)
                call["caller_context"]["expected_artifact_sha256"] = pin
            if definition.get("runtime_tick"):
                runtime_tick(run_root, runtime_root)
                call["operations"][0]["parameters"]["tick_path"] = "runtime/tick_valid.json"
            elif relocated_runtime_tick and definition["case_id"] == "P01-PRECHECK-VALID":
                call["operations"][0]["parameters"]["tick_path"] = "runtime/tick_relocated.json"
            operations_input = run_root / "registered_operations.json"
            decoy_execution = False
            if definition.get("registry_substitution"):
                operations_input = substituted_registry(run_root, runtime_root)
            started = time.perf_counter()
            completed = subprocess.run(
                [
                    "python3",
                    str(validator),
                    "--interfaces",
                    str(run_root / "recipe_interfaces.json"),
                    "--operations",
                    str(operations_input),
                    "--run-root",
                    str(run_root),
                    "--runtime-root",
                    str(runtime_root),
                    "--call-stdin",
                ],
                input=json.dumps(call, ensure_ascii=False, sort_keys=True),
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
            if definition.get("registry_substitution"):
                decoy_execution = (runtime_root / "decoy_executed.marker").exists()
                passed = passed and not decoy_execution
            record = {
                "schema": "jinrong_t5_probe_result_v3",
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
                "pin_source": definition.get("pin_source"),
                "runtime_tick": bool(definition.get("runtime_tick")),
                "relocated_runtime_tick": relocated_runtime_tick and definition["case_id"] == "P01-PRECHECK-VALID",
                "registry_substitution": bool(definition.get("registry_substitution")),
                "decoy_execution_performed": decoy_execution,
            }
            records.append(record)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    summary = {
        "round_id": args.round_id,
        "probe_count": len(records),
        "passed": sum(record["passed"] for record in records),
        "accepted": sum(record["actual"] == "ACCEPT" for record in records),
        "rejected": sum(record["actual"] == "REJECT" for record in records),
        "normalized": [normalize(record) for record in records],
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if all(record["passed"] for record in records) else 3


if __name__ == "__main__":
    raise SystemExit(main())
