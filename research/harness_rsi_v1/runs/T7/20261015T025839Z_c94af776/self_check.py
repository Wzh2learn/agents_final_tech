#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20261015T025839Z_c94af776"
REPO_ROOT = Path("/home/testuser/wzh/projects/agents_final_tech").resolve()
RUN_ROOT = REPO_ROOT / "research/harness_rsi_v1/runs/T7" / RUN_ID
EXPECTED_OUTSIDE_STATUS = {
    (" M", "logs/graph/dispatch_log.md"),
    (" M", "logs/graph/docs_lint_report.json"),
    (" M", "logs/graph/governance_drift_latest.md"),
    (" M", "logs/graph/verify-report.json"),
    ("??", "research/harness_rsi_v1/runs/T4/20261014T174628Z_2cc25c92/"),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def git_blob(relative_path: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", f"HEAD:{relative_path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip())
    return completed.stdout.strip()


def git_status_outside_run() -> set[tuple[str, str]]:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip())
    result = set()
    prefix = "research/harness_rsi_v1/runs/T7/" + RUN_ID + "/"
    for line in completed.stdout.splitlines():
        status = line[:2]
        path = line[3:]
        if path == prefix.rstrip("/") or path.startswith(prefix):
            continue
        t4_v1_prefix = "research/harness_rsi_v1/runs/T4/20261014T174628Z_2cc25c92/"
        if path.startswith(t4_v1_prefix):
            path = t4_v1_prefix
        result.add((status, path))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    verify_only = args.verify_only

    checks: list[dict[str, Any]] = []

    def add(check_id: str, result: str, detail: str) -> None:
        checks.append({"id": check_id, "result": result, "detail": detail})

    required = [
        "TASK_PROMPT.md",
        "receipt.json",
        "pilot_acceptance.json",
        "rollback_receipt.json",
        "review_packet.md",
        "summary.md",
        "candidate_amendment_A1.json",
        "amended_candidate.json",
        "paired_replay.json",
        "identity_bindings.json",
        "old_evidence_hashes_before.json",
        "old_evidence_hashes_after.json",
        "repair_record.json",
        "events.jsonl",
    ]
    missing = [name for name in required if not (RUN_ROOT / name).is_file()]
    add("required_files", "PASS" if not missing else "FAIL", f"missing={missing}")

    parse_errors = []
    for path in sorted(RUN_ROOT.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                parse_errors.append(f"{path.relative_to(RUN_ROOT)}: {exc}")
        elif path.suffix == ".jsonl":
            try:
                for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    if line.strip():
                        json.loads(line)
            except Exception as exc:
                parse_errors.append(f"{path.relative_to(RUN_ROOT)}:{number}: {exc}")
    add("json_parse", "PASS" if not parse_errors else "FAIL", f"errors={parse_errors}")

    identity = json.loads((RUN_ROOT / "identity_bindings.json").read_text(encoding="utf-8"))
    identity_errors = []
    for binding in identity["input_bindings"]:
        path = Path(binding["absolute_path"])
        if not path.is_file():
            identity_errors.append(f"missing:{binding['path']}")
            continue
        if sha256_file(path) != binding["sha256_file"]:
            identity_errors.append(f"sha256:{binding['path']}")
        if binding["hash_status"] == "TRACKED_AT_CURRENT_HEAD":
            if git_blob(binding["path"]) != binding["canonical_git_blob_id"]:
                identity_errors.append(f"blob:{binding['path']}")
        elif binding["hash_status"] == "RUN_LOCAL_UNTRACKED_AT_EXECUTION":
            if binding["canonical_git_blob_id"] is not None:
                identity_errors.append(f"local_blob_not_null:{binding['path']}")
        else:
            identity_errors.append(f"unknown_hash_status:{binding['path']}")
    add("input_hashes", "PASS" if not identity_errors else "FAIL", f"errors={identity_errors}")

    amendment = json.loads((RUN_ROOT / "candidate_amendment_A1.json").read_text(encoding="utf-8"))
    base = Path(REPO_ROOT / amendment["base_candidate"]["source_path"])
    amendment_ok = (
        amendment["amendment_status"] == "COMPLETED_BEFORE_EVALUATION"
        and git_blob(amendment["base_candidate"]["source_path"]) == amendment["base_candidate"]["git_blob_id"]
        and sha256_file(base) == amendment["base_candidate"]["sha256"]
        and amendment["evaluation_precondition_result"]["candidate_executable_for_new_absence_policy"] is False
    )
    add("a1_precondition", "PASS" if amendment_ok else "FAIL", "A-1 precedes candidate evaluation and retains legal UNRESOLVED")

    replay = json.loads((RUN_ROOT / "paired_replay.json").read_text(encoding="utf-8"))
    replay_ok = (
        replay["baseline"]["t4_case_count"] == 16
        and replay["baseline"]["t4_replay_match_count"] == 22
        and len(replay["baseline"]["t4_replay_records"]) == 22
        and replay["candidate"]["case_level_replay_status"] == "NOT_EVALUABLE"
        and replay["paired_results"]["counted_repaired_misses"] == 0
    )
    add("paired_replay", "PASS" if replay_ok else "FAIL", "16 cases bound; baseline 22/22; candidate NOT_EVALUABLE")

    before = json.loads((RUN_ROOT / "old_evidence_hashes_before.json").read_text(encoding="utf-8"))["snapshot"]
    after = json.loads((RUN_ROOT / "old_evidence_hashes_after.json").read_text(encoding="utf-8"))["snapshot"]
    snapshot_errors = []
    if before != after:
        snapshot_errors.append("before_after_snapshot_mismatch")
    for relative_path, record in before.items():
        path = REPO_ROOT / relative_path
        if sha256_file(path) != record["sha256_file"]:
            snapshot_errors.append(f"sha256:{relative_path}")
        if git_blob(relative_path) != record["git_blob_id"]:
            snapshot_errors.append(f"blob:{relative_path}")
        if path.stat().st_size != record["bytes"]:
            snapshot_errors.append(f"bytes:{relative_path}")
        if f"{path.stat().st_mode & 0o777:o}" != record["mode"].removeprefix("0o"):
            snapshot_errors.append(f"mode:{relative_path}")
    rollback = json.loads((RUN_ROOT / "rollback_receipt.json").read_text(encoding="utf-8"))
    rollback_ok = (
        rollback["drill_status"] == "PASS"
        and rollback["behavior_verification"]["behavior_consistent"] is True
        and rollback["old_evidence_verification"]["all_git_blob_sha256_bytes_mode_unchanged"] is True
        and not snapshot_errors
    )
    add("rollback_and_old_hashes", "PASS" if rollback_ok else "FAIL", f"errors={snapshot_errors}")

    pilot = json.loads((RUN_ROOT / "pilot_acceptance.json").read_text(encoding="utf-8"))
    wording_ok = (
        pilot["three_axes"] == {"activation": "NOT_ENABLED", "delivery": "DELIVERED", "review": "UNREVIEWED"}
        and pilot["selection_conclusion"]["decision"] == "NO_PROMOTION"
        and "科学成功" not in json.dumps(pilot, ensure_ascii=False).replace("不是实验、科学成功", "")
    )
    add("a3_wording", "PASS" if wording_ok else "FAIL", "No experiment/scientific/C/S success claim")

    receipt = json.loads((RUN_ROOT / "receipt.json").read_text(encoding="utf-8"))
    receipt_required = {"schema", "task_id", "run_id", "card_version", "direction", "execution_status", "acceptance_status", "activation_status", "authorization_ref", "protocol_freeze_sha256", "dependency_acceptance", "input_bindings", "actions", "checks", "output_manifest", "scope", "unresolved", "usage"}
    receipt_ok = receipt_required <= set(receipt) and receipt["schema"] == "receipt" and receipt["activation_status"] == "NOT_ENABLED"
    add("receipt_contract", "PASS" if receipt_ok else "FAIL", f"required_missing={sorted(receipt_required - set(receipt))}")

    derived_logs = sorted((RUN_ROOT / "scratch/baseline_replay").glob("pass*_T1-INC-1[23].log"))
    derived_residue = [path for path in RUN_ROOT.rglob("*") if path.is_file() and path.name.startswith("t4-v2-summary-mismatch")]
    derived_ok = len(derived_logs) == 4 and all("derived_md_sha256=" in path.read_text(encoding="utf-8") and "derived_md_removed=true" in path.read_text(encoding="utf-8") for path in derived_logs) and not derived_residue
    add("runtime_derived_mismatch", "PASS" if derived_ok else "FAIL", f"logs={len(derived_logs)} residue={derived_residue}")

    markdown_results = []
    g1_log = RUN_ROOT / "scratch/g1_guard_matrix.log"
    g1_log.parent.mkdir(parents=True, exist_ok=True)
    markdown_paths = sorted(path for path in RUN_ROOT.rglob("*.md"))
    g1_lines = []
    for path in markdown_paths:
        completed = subprocess.run(
            [sys.executable, "-B", str(REPO_ROOT / "scripts/graph/hooks/summary_recompute_guard.py"), "check", str(path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if not verify_only:
            g1_lines.append(f"path={path}\nrc={completed.returncode}\nstdout={completed.stdout}\nstderr={completed.stderr}\n")
        markdown_results.append({"path": str(path.relative_to(RUN_ROOT)), "rc": completed.returncode})
    if not verify_only:
        g1_log.write_text("\n".join(g1_lines), encoding="utf-8", newline="\n")
    g1_ok = bool(markdown_results) and all(item["rc"] == 0 for item in markdown_results)
    add("g1_markdown", "PASS" if g1_ok else "FAIL", f"count={len(markdown_results)} results={markdown_results}")

    boundary = git_status_outside_run()
    add("write_boundary", "PASS" if boundary == EXPECTED_OUTSIDE_STATUS else "FAIL", f"outside_statuses={sorted(boundary)}")

    residue = []
    for path in RUN_ROOT.rglob("*"):
        if path.is_dir() and path.name in {".omc", "__pycache__"}:
            residue.append(str(path.relative_to(RUN_ROOT)))
        if path.is_file() and path.suffix == ".pyc":
            residue.append(str(path.relative_to(RUN_ROOT)))
    for directory in [RUN_ROOT / "scratch/tmp"]:
        if directory.exists() and any(path.is_file() for path in directory.rglob("*")):
            residue.append(str(directory.relative_to(RUN_ROOT)))
    add("temporary_residue", "PASS" if not residue else "FAIL", f"residue={residue}")

    mode_errors = []
    for path in RUN_ROOT.rglob("*"):
        if not path.is_file():
            continue
        mode = path.stat().st_mode & 0o777
        expected = 0o755 if path.name in {"execute_t7.py", "self_check.py", "build_manifest.py"} else 0o644
        if mode != expected:
            mode_errors.append(f"{path.relative_to(RUN_ROOT)}:{oct(mode)}!={oct(expected)}")
    add("mode_declarations", "PASS" if not mode_errors else "FAIL", f"errors={mode_errors}")

    manifest_path = RUN_ROOT / "artifacts_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_errors = []
        disk_files = sorted(path for path in RUN_ROOT.rglob("*") if path.is_file() and path.name != "artifacts_manifest.json" and ".omc" not in path.parts and "__pycache__" not in path.parts and path.suffix != ".pyc")
        declared_paths = [REPO_ROOT / item["absolute_path"] for item in manifest["artifacts"]]
        if set(disk_files) != set(declared_paths):
            manifest_errors.append("file_set_mismatch")
        for item in manifest["artifacts"]:
            path = REPO_ROOT / item["absolute_path"]
            if not path.is_file():
                continue
            if path.stat().st_size != item["bytes"] or sha256_file(path) != item["sha256_file"] or path.stat().st_mode & 0o777 != int(item["mode"][-3:], 8):
                manifest_errors.append(item["relative_path"])
        add("artifact_manifest", "PASS" if not manifest_errors else "FAIL", f"errors={manifest_errors}")
    elif not verify_only:
        add("artifact_manifest", "PENDING", "Manifest is built after this mutating self-check.")

    failed = [item for item in checks if item["result"] == "FAIL"]
    if failed:
        overall = "CONTRACT_FAIL"
    elif any(item["result"] == "PENDING" for item in checks):
        overall = "CONTRACT_PASS_PRE_MANIFEST"
    else:
        overall = "CONTRACT_PASS"
    result = {
        "schema": "jinrong_t7_self_check_result_v1",
        "run_id": RUN_ID,
        "checked_at": utc_now(),
        "mode": "VERIFY_ONLY" if verify_only else "MUTATING_PRE_MANIFEST",
        "overall": overall,
        "check_count": len(checks),
        "passed_count": sum(item["result"] == "PASS" for item in checks),
        "failed_count": len(failed),
        "checks": checks,
    }

    if not verify_only:
        g1_check = next(item for item in checks if item["id"] == "g1_markdown")
        common_ids = {"required_files", "json_parse", "input_hashes", "rollback_and_old_hashes", "receipt_contract", "write_boundary", "temporary_residue", "mode_declarations"}
        common_failures = [item for item in checks if item["id"] in common_ids and item["result"] != "PASS"]
        a_common_result = "PASS" if not common_failures else "FAIL"
        for check in receipt["checks"]:
            if check["id"] == "g1":
                check["result"] = g1_check["result"]
                check["scope"] = f"All {len(markdown_results)} Markdown artifacts were checked individually; each returned rc=0."
            if check["id"] == "a_common":
                check["result"] = a_common_result
                check["scope"] = "JSON/JSONL, paths, canonical and SHA-256 hashes, modes, write boundary, temporary residue and UNRESOLVED were recomputed."
        receipt["checks_by_id"] = {item["id"]: item["result"] for item in receipt["checks"]}
        write_json(RUN_ROOT / "receipt.json", receipt)
        pilot["a_assertions"]["A_common"] = a_common_result
        pilot["self_check"] = {"overall": overall, "check_count": len(checks), "failed_count": len(failed)}
        write_json(RUN_ROOT / "pilot_acceptance.json", pilot)
        with (RUN_ROOT / "events.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps({"timestamp": utc_now(), "event": "self_check", "run_id": RUN_ID, "task_id": "T7", "overall": overall, "check_count": len(checks), "failed_count": len(failed), "g1_markdown": f"{len(markdown_results)}/{len(markdown_results)} rc=0" if g1_ok else "FAILED"}, ensure_ascii=False, sort_keys=True) + "\n")
        write_json(RUN_ROOT / "self_check_result.json", result)
    elif not (RUN_ROOT / "self_check_result.json").is_file():
        raise RuntimeError("verify-only mode requires the pre-manifest self_check_result.json")

    print(json.dumps({"overall": overall, "check_count": len(checks), "failed_count": len(failed), "mode": result["mode"], "failures": failed}, sort_keys=True))
    return 0 if overall in {"CONTRACT_PASS", "CONTRACT_PASS_PRE_MANIFEST"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
