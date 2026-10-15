#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


NORMALIZED_KEYS = [
    "case_id",
    "recipe_id",
    "expected",
    "expected_fail_closed_code",
    "actual",
    "actual_fail_closed_code",
    "target_execution_performed",
    "operation_result_count",
    "passed",
    "pin_source",
    "runtime_tick",
    "registry_substitution",
    "decoy_execution_performed",
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            stat = path.stat()
            rows.append(
                {
                    "relative_path": path.relative_to(root).as_posix(),
                    "bytes": stat.st_size,
                    "sha256": sha256_file(path),
                    "mode": format(stat.st_mode, "o"),
                    "mtime_ns": stat.st_mtime_ns,
                }
            )
    return rows


def verify_manifest(root: Path) -> dict[str, Any]:
    manifest = json.loads((root / "artifacts_manifest.json").read_text(encoding="utf-8"))
    failures = []
    for artifact in manifest["artifacts"]:
        path = root / artifact["relative_path"]
        if not path.is_file():
            failures.append({"relative_path": artifact["relative_path"], "reason": "missing"})
            continue
        actual = {
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "mode": format(path.stat().st_mode, "o"),
        }
        for key in ["bytes", "sha256", "mode"]:
            if actual[key] != artifact[key]:
                failures.append({"relative_path": artifact["relative_path"], "field": key, "expected": artifact[key], "actual": actual[key]})
    expected_paths = {artifact["relative_path"] for artifact in manifest["artifacts"]} | {"artifacts_manifest.json"}
    actual_paths = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    return {
        "declared": manifest["artifact_count"],
        "checked": len(manifest["artifacts"]),
        "failures": failures,
        "missing": sorted(expected_paths - actual_paths),
        "extra": sorted(actual_paths - expected_paths),
        "passed": manifest["artifact_count"] == 45 and len(manifest["artifacts"]) == 45 and not failures and expected_paths == actual_paths,
    }


def run_matrix(root: Path, output: Path) -> tuple[int, list[dict[str, Any]], dict[str, Any]]:
    completed = subprocess.run(
        [
            "python3",
            str(root / "run_probes.py"),
            "--run-root",
            str(root),
            "--definitions",
            str(root / "recipe_fixtures/probe_definitions.json"),
            "--output",
            str(output),
            "--round-id",
            "PASS_1" if output.name.startswith("pass1") else "PASS_2",
        ],
        cwd="/tmp",
        text=True,
        capture_output=True,
        check=False,
    )
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    summary = json.loads(completed.stdout)
    return completed.returncode, rows, summary


def normalized(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: row.get(key) for key in NORMALIZED_KEYS} for row in rows]


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def restore_modes(root: Path) -> list[str]:
    manifest = json.loads((root / "artifacts_manifest.json").read_text(encoding="utf-8"))
    changed = []
    for artifact in manifest["artifacts"]:
        path = root / artifact["relative_path"]
        os.chmod(path, 0o644)
        changed.append(artifact["relative_path"])
    for artifact in manifest["artifacts"]:
        path = root / artifact["relative_path"]
        os.chmod(path, int(artifact["mode"], 8))
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--work-root", required=True)
    args = parser.parse_args()
    run_root = Path(args.run_root).resolve()
    work_root = Path(args.work_root).resolve()
    if work_root == run_root or run_root in work_root.parents:
        raise SystemExit("work root must be outside the delivered run tree")
    if work_root.exists():
        raise SystemExit("refuse to overwrite replay work root")
    work_root.mkdir(parents=True)
    current_dir = work_root / "current_tree"
    fresh_dir = work_root / "fresh_delivery"
    current_dir.mkdir()
    fresh_dir.mkdir()
    before = snapshot(run_root)
    write_json(current_dir / "snapshot_before.json", before)
    manifest_before = verify_manifest(run_root)
    rc1, rows1, summary1 = run_matrix(run_root, current_dir / "pass1_probes.jsonl")
    rc2, rows2, summary2 = run_matrix(run_root, current_dir / "pass2_probes.jsonl")
    manifest_after = verify_manifest(run_root)
    after = snapshot(run_root)
    write_json(current_dir / "snapshot_after.json", after)
    (current_dir / "runner.stdout").write_text(f"PASS_1 rc={rc1} records={len(rows1)}\nPASS_2 rc={rc2} records={len(rows2)}\n", encoding="utf-8", newline="\n")
    write_json(current_dir / "pass1_summary.json", summary1)
    write_json(current_dir / "pass2_summary.json", summary2)
    shutil.copytree(run_root, fresh_dir / "run")
    fresh_root = fresh_dir / "run"
    mode_resets = restore_modes(fresh_root)
    fresh_manifest_before = verify_manifest(fresh_root)
    fresh_before = snapshot(fresh_root)
    write_json(fresh_dir / "snapshot_before.json", fresh_before)
    frc1, frows1, fsummary1 = run_matrix(fresh_root, fresh_dir / "pass1_probes.jsonl")
    frc2, frows2, fsummary2 = run_matrix(fresh_root, fresh_dir / "pass2_probes.jsonl")
    fresh_manifest_after = verify_manifest(fresh_root)
    fresh_after = snapshot(fresh_root)
    write_json(fresh_dir / "snapshot_after.json", fresh_after)
    write_json(fresh_dir / "pass1_summary.json", fsummary1)
    write_json(fresh_dir / "pass2_summary.json", fsummary2)
    matrix_ok = all(rc == 0 and len(rows) == 23 and all(row["passed"] for row in rows) for rc, rows in [(rc1, rows1), (rc2, rows2), (frc1, frows1), (frc2, frows2)])
    outcomes_ok = normalized(rows1) == normalized(rows2) == normalized(frows1) == normalized(frows2)
    result = {
        "schema": "jinrong_t5_replay_evidence_v1",
        "run_id": run_root.name,
        "prerequisites": "NONE",
        "delivery_tree_read_only": True,
        "current_tree": {
            "manifest_before": manifest_before,
            "manifest_after": manifest_after,
            "tree_unchanged": before == after,
            "rounds": [
                {"round_id": "PASS_1", "exit_code": rc1, "summary": summary1, "record_count": len(rows1)},
                {"round_id": "PASS_2", "exit_code": rc2, "summary": summary2, "record_count": len(rows2)},
            ],
        },
        "fresh_delivery": {
            "copy_scope": "Byte/mode copy of the delivered tree; relocation of the absolute watcher binding is generated only in an external runtime directory and no copied manifest path is rewritten.",
            "mode_reset_and_restore_count": len(mode_resets),
            "manifest_before": fresh_manifest_before,
            "manifest_after": fresh_manifest_after,
            "tree_unchanged": fresh_before == fresh_after,
            "rounds": [
                {"round_id": "PASS_1", "exit_code": frc1, "summary": fsummary1, "record_count": len(frows1)},
                {"round_id": "PASS_2", "exit_code": frc2, "summary": fsummary2, "record_count": len(frows2)},
            ],
        },
        "complete_matrix_each_round": matrix_ok,
        "normalized_outcomes_identical_across_four_rounds": outcomes_ok,
        "passed": matrix_ok
        and outcomes_ok
        and before == after
        and fresh_before == fresh_after
        and manifest_before["passed"]
        and manifest_after["passed"]
        and fresh_manifest_before["passed"]
        and fresh_manifest_after["passed"],
    }
    (work_root / "replay_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
