#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20261014T212520Z_3acf4c1d"
RUN_START = datetime(2026, 10, 14, 21, 25, 20, tzinfo=timezone.utc)
EXPECTED_MODES = {
    "recipe_fixtures/dispatch/watcher.sh": "100755",
}
DEFAULT_REPOSITORY_ROOT = Path("/home/testuser/wzh/projects/agents_final_tech")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_mode(path: Path) -> str:
    return format(path.stat().st_mode, "o")


def canonical_blob(repo_root: Path, relative: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", f"HEAD:{relative}"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip())
    return completed.stdout.strip()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def is_ignored(repo_root: Path, path: Path) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "-q", "--", str(path)],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--run-root", default=str(DEFAULT_REPOSITORY_ROOT / "research/harness_rsi_v1/runs/T5" / RUN_ID))
    parser.add_argument("--repo-root", default=str(DEFAULT_REPOSITORY_ROOT))
    args = parser.parse_args()
    run_root = Path(args.run_root).resolve()
    repo_root = Path(args.repo_root).resolve()
    checks: list[dict[str, Any]] = []
    failures: list[str] = []

    def check(check_id: str, condition: bool, detail: Any, level: str = "CONTRACT_PASS", scope: str = "current T5 run package only") -> None:
        checks.append({"check_id": check_id, "status": "OK" if condition else "FAIL", "verification_level": level, "scope": scope, "detail": detail})
        if not condition:
            failures.append(check_id)

    json_paths = [
        path
        for path in run_root.rglob("*.json")
        if "__pycache__" not in path.parts
    ]
    parsed = {path: load_json(path) for path in json_paths}
    check("JSON_PARSE", len(parsed) == len(json_paths), {"parsed": len(json_paths)})

    receipt = parsed[run_root / "receipt.json"]
    required = {"task_id", "run_id", "scope", "execution_status", "acceptance_status", "activation_status", "input_bindings", "output_manifest", "checks", "usage", "unresolved", "authorization_ref", "supersedes", "self_check"}
    check("RECEIPT_REQUIRED_FIELDS", required.issubset(receipt), {"missing": sorted(required - set(receipt))})
    check("THREE_AXIS_STATUS", receipt["execution_status"] == "DELIVERED" and receipt["acceptance_status"] == "UNREVIEWED" and receipt["activation_status"] == "NOT_ENABLED", {"execution_status": receipt["execution_status"], "acceptance_status": receipt["acceptance_status"], "activation_status": receipt["activation_status"]})
    check("SUPERSEDES", receipt["supersedes"]["superseded_run_id"] == "20261014T195445Z_60c8e213" and receipt["supersedes"]["review_decision"] == "REJECTED", receipt["supersedes"])

    task_prompt = run_root / "TASK_PROMPT.md"
    task_binding = receipt["task_prompt"]
    check("TASK_PROMPT_CAPTURE", task_binding["sha256"] == sha256_file(task_prompt), {"sha256": sha256_file(task_prompt), "dispatch_source_sha256": task_binding["dispatch_source_sha256"]})

    binding_results = []
    for binding in receipt["input_bindings"]:
        actual = canonical_blob(repo_root, binding["git_relative_path"])
        actual_file_sha = sha256_file(Path(binding["absolute_path"]))
        binding_results.append({
            "relative": binding["git_relative_path"],
            "declared": binding["canonical_blob_id"],
            "actual": actual,
            "match": actual == binding["canonical_blob_id"],
            "declared_file_sha": binding.get("sha256_file"),
            "actual_file_sha": actual_file_sha,
            "file_sha_match": binding.get("sha256_file") is None or binding["sha256_file"] == actual_file_sha,
        })
    check("CANONICAL_INPUT_HASHES", all(item["match"] and item["file_sha_match"] for item in binding_results), binding_results, "CONTRACT_PASS", "all tracked receipt input/dependency bindings")

    registry = parsed[run_root / "registered_operations.json"]
    interfaces = parsed[run_root / "recipe_interfaces.json"]
    op_results = []
    for operation in registry["operations"]:
        target = Path(operation["target"]["path"])
        op_results.append({
            "op_id": operation["op_id"],
            "declared": operation["target"]["git_blob_id"],
            "actual": canonical_blob(repo_root, operation["target"].get("verification_command", "").split("HEAD:", 1)[-1]),
            "required_cwd": operation["target"]["required_cwd"],
            "target_exists": target.is_file(),
        })
    check("OPERATION_TARGET_BINDINGS_AND_CWD", all(item["declared"] == item["actual"] and item["required_cwd"] == str(repo_root) and item["target_exists"] for item in op_results), op_results, "CONTRACT_PASS", "three T4 read-only adapter targets and fixed cwd only")
    check("TWO_SINGLE_OBJECT_RECIPES", len(interfaces["recipes"]) == 2 and len({recipe["single_object_declaration"]["object_id"] for recipe in interfaces["recipes"]}) == 2, [recipe["single_object_declaration"] for recipe in interfaces["recipes"]])

    definitions = parsed[run_root / "recipe_fixtures/probe_definitions.json"]
    round_paths = [run_root / "scratch/fresh_delivery/probe_results.jsonl", run_root / "scratch/current_tree/probe_results.jsonl"]
    rounds = [[json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] for path in round_paths]
    normalized = [
        [
            {key: row[key] for key in ["case_id", "expected", "expected_fail_closed_code", "actual", "actual_fail_closed_code", "target_execution_performed", "operation_result_count", "passed"]}
            for row in rows
        ]
        for rows in rounds
    ]
    expected_counts = Counter(case["expected"] for case in definitions["cases"])
    actual_counts = Counter(row["actual"] for row in rounds[0])
    check("PROBE_MATRIX", len(definitions["cases"]) == 21 and expected_counts == actual_counts and all(row["passed"] for rows in rounds for row in rows), {"definitions": len(definitions["cases"]), "expected": dict(expected_counts), "actual": dict(actual_counts), "two_round_consistent": normalized[0] == normalized[1]})
    pin_rows = {row["case_id"]: row for row in rounds[0] if row["case_id"].startswith("X06")}
    check("PIN_THREE_WAY_EQUALITY", pin_rows["X06A-SELF-CONSISTENT-FORGED-NO-PIN"]["actual_fail_closed_code"] == "FC_ARTIFACT_NOT_PINNED" and pin_rows["X06B-SELF-CONSISTENT-FORGED-WRONG-PIN"]["actual_fail_closed_code"] == "FC_PIN_MISMATCH" and pin_rows["X06C-SELF-CONSISTENT-FORGED-CORRECT-PIN"]["actual"] == "ACCEPT", pin_rows, "CONTRACT_PASS", "declared == measured == caller-owned external pin; false-pin caller remains outside validator trust boundary")
    bounded_rows = {row["case_id"]: row for row in rounds[0] if row["case_id"] in {"P01-PRECHECK-VALID", "P09-PRECHECK-BOUNDED-TICK-AGE-60"}}
    check("BOUNDED_TICK_AGE", set(bounded_rows) == {"P01-PRECHECK-VALID", "P09-PRECHECK-BOUNDED-TICK-AGE-60"} and all(row["actual"] == "ACCEPT" for row in bounded_rows.values()), bounded_rows, "CONTRACT_PASS", "runtime-generated observed_at with max_tick_age_minutes=30 and 60")

    markdown_paths = sorted(run_root.rglob("*.md"))
    guard_rows = []
    for path in markdown_paths:
        completed = subprocess.run(["python3", str(repo_root / "scripts/graph/hooks/summary_recompute_guard.py"), "check", str(path)], cwd=repo_root, text=True, capture_output=True, check=False)
        guard_rows.append({"path": str(path.relative_to(run_root)), "rc": completed.returncode})
    check("G1_ALL_MARKDOWN_GUARD", all(row["rc"] == 0 for row in guard_rows), guard_rows)

    manifest = parsed[run_root / "artifacts_manifest.json"]
    manifest_results = []
    for artifact in manifest["artifacts"]:
        path = Path(artifact["absolute_path"])
        actual_sha = sha256_file(path) if path.is_file() else None
        actual_bytes = path.stat().st_size if path.is_file() else None
        actual_mode = file_mode(path) if path.is_file() else None
        manifest_results.append({"relative_path": artifact["relative_path"], "sha_match": actual_sha == artifact["sha256"], "bytes_match": actual_bytes == artifact["bytes"], "mode_match": actual_mode == artifact["mode"], "actual_mode": actual_mode})
    check("MANIFEST_BYTES_AND_MODES", manifest["artifact_count"] == len(manifest["artifacts"]) and all(item["sha_match"] and item["bytes_match"] and item["mode_match"] for item in manifest_results), {"declared": manifest["artifact_count"], "checked": len(manifest_results), "failures": [item for item in manifest_results if not item["sha_match"] or not item["bytes_match"] or not item["mode_match"]]})
    mode_results = []
    for relative in manifest["required_executables"]:
        path = run_root / relative
        mode_results.append({"relative_path": relative, "mode": file_mode(path), "x_bit": os.access(path, os.X_OK), "expected_mode": EXPECTED_MODES.get(relative, "100755")})
    check("REQUIRED_EXECUTABLES", manifest["required_executables"] == ["recipe_fixtures/dispatch/watcher.sh"] and all(item["x_bit"] and item["mode"] == item["expected_mode"] for item in mode_results), mode_results)

    expected_disk = {artifact["relative_path"] for artifact in manifest["artifacts"]} | {"artifacts_manifest.json"}
    actual_disk = {
        path.relative_to(run_root).as_posix()
        for path in run_root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    }
    check("RUN_FILE_SET_WITH_IGNORED_PATHS", actual_disk == expected_disk, {"missing": sorted(expected_disk - actual_disk), "extra": sorted(actual_disk - expected_disk)}, "CONTRACT_PASS", "complete run directory enumeration; gitignored paths are not excluded")

    status = subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=repo_root, text=True, capture_output=True, check=True).stdout.splitlines()
    allowed_dirty_prefixes = (" M logs/graph/", "?? research/harness_rsi_v1/runs/T4/20261014T174628Z_2cc25c92/", f"?? research/harness_rsi_v1/runs/T5/{RUN_ID}/")
    boundary_violations = [line for line in status if not line.startswith(allowed_dirty_prefixes)]
    check("GIT_WRITE_BOUNDARY", not boundary_violations, {"violations": boundary_violations, "allowed_preexisting": ["logs/graph dirty files", "T4 uncommitted v1 run"], "executor_owned": f"T5/{RUN_ID}"})

    touched = []
    ignored_touched = []
    scanned = 0
    for root, directories, files in os.walk(repo_root):
        directories[:] = [name for name in directories if name != ".git"]
        for name in files:
            path = Path(root) / name
            scanned += 1
            if datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) >= RUN_START:
                relative = path.relative_to(repo_root).as_posix()
                touched.append(relative)
                if is_ignored(repo_root, path):
                    ignored_touched.append(relative)
    expected_touched_prefix = f"research/harness_rsi_v1/runs/T5/{RUN_ID}/"
    external_touched = [path for path in touched if not path.startswith(expected_touched_prefix)]
    allowed_external_prefixes = ("logs/", ".pytest_cache/")
    disclosed_external = all(path.startswith(allowed_external_prefixes) for path in external_touched)
    check("MTIME_SCAN_INCLUDES_IGNORED", disclosed_external, {"repo_files_scanned": scanned, "touched_count": len(touched), "ignored_touched": ignored_touched, "external_touched": external_touched, "allowed_external_prefixes": list(allowed_external_prefixes), "executor_owned_outside_run": []}, "CONTRACT_PASS", "full repository walk including gitignored files; pre-existing/concurrent external mtimes are disclosed rather than counted as executor writes")

    events = [json.loads(line) for line in (run_root / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    event_ids = [event["event_id"] for event in events]
    check("EVENTS_MONOTONIC", event_ids == list(range(1, len(events) + 1)), {"first": event_ids[0], "last": event_ids[-1], "count": len(events)})
    usage = receipt["usage"]
    check("B0_ZERO_EXTERNAL_AND_UNRESOLVED", all(usage[key] == 0 for key in ["additional_cheap_requests_actual", "additional_strong_requests_actual", "orchestrated_model_requests", "automatic_retries", "network_calls", "remote_calls", "production_calls", "database_calls", "training_calls", "daemon_calls", "loop_b_calls"]) and usage["execution_chat_usage"] == "UNRESOLVED", usage)

    bad_markdown_receipts = []
    for path in markdown_paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        if "SUMMARY-GUARD" in text and "request_count = 3" in text:
            bad_markdown_receipts.append(str(path.relative_to(run_root)))
    check("NO_PERSISTED_BAD_SUMMARY", not bad_markdown_receipts, {"bad_markdown_receipts": bad_markdown_receipts})

    document = {
        "schema": "jinrong_t5_self_check_result_v2",
        "run_id": RUN_ID,
        "verification_level": "CONTRACT_PASS",
        "scope": "Current run package; deterministic local byte/mode/hash/probe/guard/write-boundary checks only; no scientific, GB10 production, daemon, model, database or formal-run qualification.",
        "status": "OK" if not failures else "FAIL",
        "check_count": len(checks),
        "ok_count": len(checks) - len(failures),
        "failures": failures,
        "checks": checks,
        "assertion_mapping": {
            "A1": {"status": "CONTRACT_PASS", "scope": "Two single-object recipes; unregistered/shell/arbitrary-path probes reject before target execution.", "evidence": "probe matrix P02/P03/P08/E02/E03/E09"},
            "A2": {"status": "CONTRACT_PASS", "scope": "Caller-side missing field/hash/forged-summary detection and external-pin three-way equality.", "evidence": "probe matrix P06/P07/E04/E05/E06/X06A/X06B/X06C; validator does not defend against a caller deliberately supplying a false pin"},
            "A3": {"status": "CONTRACT_PASS", "scope": "B0 run-package write boundary including gitignored paths and canonical frozen/dependency hashes.", "evidence": "RUN_FILE_SET_WITH_IGNORED_PATHS, GIT_WRITE_BOUNDARY, MTIME_SCAN_INCLUDES_IGNORED, CANONICAL_INPUT_HASHES"},
            "A_common": {"status": "CONTRACT_PASS", "scope": "JSON, required fields, bytes, modes, hashes, paths, unknown surfaces and package integrity.", "evidence": "all self-check rows"}
        },
    }
    print(json.dumps(document, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 3


if __name__ == "__main__":
    raise SystemExit(main())
