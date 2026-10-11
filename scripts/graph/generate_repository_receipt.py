#!/usr/bin/env python3
"""Generate a deterministic repository/test receipt for cross-host verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AUTHORITATIVE_PATHS = (
    "docs/handoff/repository_governance_commit_manifest_2026-10-11.json",
    "docs/handoff/repository_asset_classification_2026-10-11.json",
    "docs/handoff/repository_governance_and_sync_2026-10-11.md",
    "docs/research/finqa_v2_asset_lineage_v1.md",
    "docs/experiments/2026-10-11_loop_c_repository_governance_final_audit.md",
)

INVALID_RUN_PATHS = (
    "research/finqa_v2_20261010/results/finqa_v2_formal_execution_receipt.json",
    "research/finqa_v2_20261010/results_binding_v2_rerun/finqa_v2_formal_execution_receipt.json",
)

SCIENTIFIC_TOKENS = (
    "PRIMARY_ROUTE=A",
    "B_QUALIFICATION=NO / STOP_BRANCH",
    "SECOND_FLOW_MIXED",
    "MEASUREMENT_OBJECT_MISMATCH",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def run_git(repo: Path, *args: str, binary: bool = False) -> Any:
    command = ["git", "-c", "core.quotepath=false", *args]
    result = subprocess.run(
        command,
        cwd=repo,
        check=True,
        capture_output=True,
        text=not binary,
        encoding=None if binary else "utf-8",
        errors=None if binary else "replace",
    )
    return result.stdout


def parse_status(raw: bytes) -> tuple[list[dict[str, Any]], str]:
    records: list[dict[str, Any]] = []
    parts = raw.split(b"\0")
    index = 0
    while index < len(parts):
        item = parts[index]
        if not item:
            index += 1
            continue
        text = item.decode("utf-8", errors="replace")
        xy = text[:2]
        path = text[3:]
        original_path = None
        if xy[0] in "RC" or xy[1] in "RC":
            index += 1
            if index >= len(parts):
                raise ValueError("malformed rename entry in git status output")
            original_path = parts[index].decode("utf-8", errors="replace")
        records.append({"xy": xy, "path": path, "original_path": original_path})
        index += 1
    return records, hashlib.sha256(raw).hexdigest()


def json_payload(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def repo_relative(repo: Path, path: Path) -> str:
    return path.resolve().relative_to(repo.resolve()).as_posix()


def build_receipt(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path(args.repo).resolve()
    output = Path(args.output).resolve()
    pytest_log = Path(args.pytest_log).resolve()
    pytest_exit_file = Path(args.pytest_exit_code_file).resolve()
    claims_path = Path(args.claims_json).resolve()
    submission_path = Path(args.submission_json).resolve()
    docs_path = Path(args.docs_json).resolve()

    status_raw = run_git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all", binary=True)
    if isinstance(status_raw, str):
        status_raw = status_raw.encode("utf-8")
    status_records, status_sha256 = parse_status(status_raw)

    head = run_git(repo, "rev-parse", "HEAD").strip()
    branch = run_git(repo, "branch", "--show-current").strip()
    top_level = run_git(repo, "rev-parse", "--show-toplevel").strip()
    try:
        upstream = run_git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}").strip()
        ahead, behind = run_git(repo, "rev-list", "--left-right", "--count", f"{upstream}...HEAD").split()
    except subprocess.CalledProcessError:
        upstream = None
        ahead, behind = None, None

    commit_manifest_path = repo / AUTHORITATIVE_PATHS[0]
    commit_manifest = json_payload(commit_manifest_path)
    entries = commit_manifest.get("entries", [])
    entry_paths = [item.get("path") for item in entries]
    archive_paths = sorted(
        item.get("path") for item in entries if item.get("action") == "ARCHIVE_MOVE_DELETE_OLD_PATH"
    )

    pytest_exit_code = int(pytest_exit_file.read_text(encoding="ascii").strip())
    pytest_text = pytest_log.read_text(encoding="utf-8", errors="replace")
    summary_lines = [
        line.strip()
        for line in pytest_text.splitlines()
        if re.search(r"\d+ passed", line) and " in " in line
    ]
    claims = json_payload(claims_path)
    submission = json_payload(submission_path)
    docs = json_payload(docs_path)

    state_text = (repo / "memory/STATE.md").read_text(encoding="utf-8")
    lineage_text = (repo / "docs/research/finqa_v2_asset_lineage_v1.md").read_text(encoding="utf-8")

    identity: dict[str, Any] = {
        "schema_version": 1,
        "verification_mode": "RECEIPT_VERIFIED",
        "generation_mode": "DETERMINISTIC_CROSS_HOST_RECEIPT",
        "host_id": args.host_id,
        "repo_identity": {
            "absolute_path": str(repo),
            "git_top_level": top_level,
        },
        "git": {
            "branch": branch,
            "head_sha": head,
            "upstream": upstream,
            "ahead": ahead,
            "behind": behind,
            "diff_stat": run_git(repo, "diff", "--stat"),
        },
        "git_status": {
            "porcelain_v1_z_sha256": status_sha256,
            "records": status_records,
            "staged_paths": sorted(
                item["path"] for item in status_records if item["xy"][0] not in " ?"
            ),
            "unstaged_paths": sorted(
                item["path"] for item in status_records if item["xy"][1] not in " ?"
            ),
            "untracked_paths": sorted(
                item["path"] for item in status_records if item["xy"] == "??"
            ),
        },
        "commit_manifest": {
            "path": AUTHORITATIVE_PATHS[0],
            "sha256": sha256_file(commit_manifest_path),
            "covered_paths": commit_manifest.get("reconciliation", {}).get("covered_paths"),
            "entry_count": len(entries),
            "entry_paths_sha256": hashlib.sha256(canonical_json(entry_paths).encode("ascii")).hexdigest(),
            "unique_entry_paths": len(set(entry_paths)) == len(entry_paths),
            "archive_move_paths": archive_paths,
        },
        "authoritative_assets": {
            path: sha256_file(repo / path) for path in AUTHORITATIVE_PATHS
        },
        "test_receipts": {
            "pytest": {
                "command": args.pytest_command,
                "exit_code": pytest_exit_code,
                "summary_lines": summary_lines,
                "log_path": repo_relative(repo, pytest_log),
                "log_sha256": sha256_file(pytest_log),
                "exit_code_path": repo_relative(repo, pytest_exit_file),
                "exit_code_sha256": sha256_file(pytest_exit_file),
            },
            "claims": {
                "status": claims.get("status"),
                "claims": claims.get("claims"),
                "checks_total": claims.get("checks_total"),
                "checks_passed": claims.get("checks_passed"),
                "errors": claims.get("errors"),
                "path": repo_relative(repo, claims_path),
                "sha256": sha256_file(claims_path),
            },
            "submission": {
                "checks_passed": submission.get("checks_passed"),
                "checks_total": submission.get("checks_total"),
                "mechanical_status": submission.get("mechanical_status"),
                "submission_status": submission.get("submission_status"),
                "path": repo_relative(repo, submission_path),
                "sha256": sha256_file(submission_path),
            },
            "docs_lint": {
                "overall": docs.get("overall"),
                "fail_count": len(docs.get("fails", [])),
                "warn_count": len(docs.get("warns", [])),
                "path": repo_relative(repo, docs_path),
                "sha256": sha256_file(docs_path),
            },
        },
        "scientific_authority": {
            "state_tokens_present": {token: token in state_text for token in SCIENTIFIC_TOKENS},
            "lineage_invalid_hashes_present": {
                path: sha256_file(repo / path) in lineage_text for path in INVALID_RUN_PATHS
            },
        },
        "invalid_runs": {
            path: {
                "sha256": sha256_file(repo / path),
                "expected_sha256": expected,
                "match": sha256_file(repo / path) == expected,
            }
            for path, expected in zip(
                INVALID_RUN_PATHS,
                (
                    "2d94d30003f9de563402c71b34b58dc492e8e545682278ffb6f1c40d3d87320f",
                    "8a0017e1ae5f065fe73a01bb1af1a0f5033199fbe25369263d4184c27d8eb071",
                ),
            )
        },
        "identity_policy": {
            "timestamp_is_metadata_not_identity": True,
            "tracked_source_identity": "git_blob_or_normalized_content",
            "raw_byte_identity_required_only_for_frozen_scientific_artifacts": True,
        },
    }

    identity_hash = hashlib.sha256(canonical_json(identity).encode("ascii")).hexdigest()
    receipt = dict(identity)
    receipt["generated_at"] = datetime.now(timezone.utc).isoformat()
    receipt["identity_payload_sha256"] = identity_hash

    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(receipt, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    output.write_text(payload, encoding="utf-8")
    receipt_sha256 = sha256_file(output)
    output.with_name(output.name + ".sha256").write_text(
        f"{receipt_sha256}  {output.name}\n", encoding="ascii"
    )
    return {
        "output": str(output),
        "identity_payload_sha256": identity_hash,
        "receipt_sha256": receipt_sha256,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--host-id", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--pytest-log", required=True)
    parser.add_argument("--pytest-exit-code-file", required=True)
    parser.add_argument("--pytest-command", required=True)
    parser.add_argument("--claims-json", required=True)
    parser.add_argument("--submission-json", required=True)
    parser.add_argument("--docs-json", required=True)
    args = parser.parse_args()
    print(json.dumps(build_receipt(args), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()