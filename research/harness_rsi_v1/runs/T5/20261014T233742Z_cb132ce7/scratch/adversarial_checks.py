#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_validator(run_root: Path):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("t5_caller_validator", run_root / "caller_validator.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load caller validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_root = Path(args.run_root).resolve()
    output = Path(args.output).resolve()
    if output == run_root or run_root in output.parents:
        raise SystemExit("output must be outside the delivered run tree")
    if output.exists():
        raise SystemExit("refuse to overwrite adversarial evidence")
    output.parent.mkdir(parents=True, exist_ok=True)
    validator = load_validator(run_root)
    identity = {
        "interfaces_sha256_match": sha256_file(run_root / "recipe_interfaces.json") == validator.INTERFACES_SHA256,
        "operations_sha256_match": sha256_file(run_root / "registered_operations.json") == validator.OPERATIONS_SHA256,
    }
    registry = json.loads((run_root / "registered_operations.json").read_text(encoding="utf-8"))
    entry = copy.deepcopy(next(item for item in registry["operations"] if item["op_id"] == "OP-T4-R-SUMMARY-GUARD-CHECK"))
    entry["target"]["git_blob_id"] = "0" * 40
    target_rejection = None
    try:
        validator.execute_operation("OP-T4-R-SUMMARY-GUARD-CHECK", {"markdown_path": run_root / "recipe_fixtures/summary/good_summary.md"}, entry)
    except validator.ContractError as exc:
        target_rejection = {"code": exc.code, "detail": exc.detail}
    with tempfile.TemporaryDirectory(prefix="t5_v3_adversarial_") as temporary:
        temporary_root = Path(temporary)
        definitions = json.loads((run_root / "recipe_fixtures/probe_definitions.json").read_text(encoding="utf-8"))
        failing = copy.deepcopy(definitions)
        failing["cases"][0]["expected"] = "REJECT"
        failing_path = temporary_root / "failing_definitions.json"
        failing_path.write_text(json.dumps(failing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        output_path = temporary_root / "full_failure_matrix.jsonl"
        completed = subprocess.run(
            [
                "python3",
                str(run_root / "run_probes.py"),
                "--run-root",
                str(run_root),
                "--definitions",
                str(failing_path),
                "--output",
                str(output_path),
                "--round-id",
                "PASS_1",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    result = {
        "schema": "jinrong_t5_adversarial_checks_v1",
        "new1_input_identity": identity,
        "new1_target_identity": {
            "expected_code": "FC_OPERATION_TARGET_IDENTITY_MISMATCH",
            "actual": target_rejection,
            "passed": target_rejection is not None and target_rejection["code"] == "FC_OPERATION_TARGET_IDENTITY_MISMATCH",
        },
        "new2_full_matrix_on_failure": {
            "exit_code": completed.returncode,
            "record_count": len(rows),
            "first_case_failed": bool(rows and not rows[0]["passed"]),
            "last_case_present": bool(rows and rows[-1]["case_id"] == "Z01-IDENTITY-VERIFIED-REGISTRY-SUBSTITUTION"),
            "passed": completed.returncode == 3 and len(rows) == 23 and not rows[0]["passed"] and rows[-1]["case_id"] == "Z01-IDENTITY-VERIFIED-REGISTRY-SUBSTITUTION",
        },
    }
    result["passed"] = all(identity.values()) and result["new1_target_identity"]["passed"] and result["new2_full_matrix_on_failure"]["passed"]
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
