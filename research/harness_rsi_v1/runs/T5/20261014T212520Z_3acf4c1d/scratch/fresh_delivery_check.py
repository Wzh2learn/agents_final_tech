#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from collections import Counter
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--source-run", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--probe-output", required=True)
    parser.add_argument("--summary-output", required=True)
    args = parser.parse_args()
    source_run = Path(args.source_run).resolve()
    destination = Path(args.destination).resolve()
    probe_output = Path(args.probe_output).resolve()
    summary_output = Path(args.summary_output).resolve()
    if destination.exists():
        raise SystemExit("refuse to overwrite fresh-delivery destination")
    if probe_output.exists() or summary_output.exists():
        raise SystemExit("refuse to overwrite fresh-delivery evidence")
    def ignore_destination(directory: str, names: list[str]) -> set[str]:
        if Path(directory).name == Path(source_run).name:
            return {".fresh_delivery_copy"}
        return set()

    shutil.copytree(source_run, destination, ignore=ignore_destination)
    chmod_rows = []
    for path in sorted(destination.rglob("*")):
        if path.is_file():
            os.chmod(path, 0o644)
            chmod_rows.append({"relative_path": path.relative_to(destination).as_posix(), "after_chmod_x": format(path.stat().st_mode, "o")})
    manifest_path = destination / "artifacts_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    restore_rows = []
    for artifact in manifest["artifacts"]:
        path = destination / artifact["relative_path"]
        os.chmod(path, int(artifact["mode"], 8))
        restore_rows.append({"relative_path": artifact["relative_path"], "declared_mode": artifact["mode"], "restored_mode": format(path.stat().st_mode, "o")})
    prepare = subprocess.run(
        ["python3", str(destination / "scratch/prepare_runtime_fixtures.py"), "--run-root", str(destination)],
        cwd="/tmp",
        text=True,
        capture_output=True,
        check=False,
    )
    if prepare.returncode != 0:
        raise SystemExit(prepare.stderr)
    probes = subprocess.run(
        [
            "python3",
            str(destination / "run_probes.py"),
            "--run-root",
            str(destination),
            "--definitions",
            str(destination / "recipe_fixtures/probe_definitions.json"),
            "--output",
            str(probe_output),
            "--round-id",
            "PASS_1",
        ],
        cwd="/tmp",
        text=True,
        capture_output=True,
        check=False,
    )
    rows = [json.loads(line) for line in probe_output.read_text(encoding="utf-8").splitlines()]
    required = manifest["required_executables"]
    executable_rows = [{"relative_path": relative, "restored_mode": format((destination / relative).stat().st_mode, "o"), "x_bit": os.access(destination / relative, os.X_OK)} for relative in required]
    normalized = [{key: row[key] for key in ["case_id", "expected", "actual", "actual_fail_closed_code", "target_execution_performed", "operation_result_count", "passed"]} for row in rows]
    summary = {
        "schema": "jinrong_t5_fresh_delivery_simulation_v1",
        "helper_attempts": 4,
        "manual_repair_evidence": [
            "attempt1_failure.json",
            "attempt2_failure.json",
        ],
        "source_run": str(source_run),
        "destination": str(destination),
        "copy_complete": True,
        "all_files_chmod_x_removed": len(chmod_rows) > 0 and all(row["after_chmod_x"] == "100644" for row in chmod_rows),
        "mode_restoration": restore_rows,
        "required_executables": executable_rows,
        "runtime_fixture_prepare": {"exit_code": prepare.returncode, "stdout": prepare.stdout, "stderr": prepare.stderr},
        "probe_exit_code": probes.returncode,
        "probe_count": len(rows),
        "expected_counts": dict(Counter(row["expected"] for row in rows)),
        "actual_counts": dict(Counter(row["actual"] for row in rows)),
        "all_passed": all(row["passed"] for row in rows),
        "normalized_outcomes": normalized,
        "probe_stdout": probes.stdout,
        "probe_stderr": probes.stderr,
    }
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    with summary_output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    return 0 if probes.returncode == 0 and summary["all_passed"] and all(row["x_bit"] for row in executable_rows) else 3


if __name__ == "__main__":
    raise SystemExit(main())
