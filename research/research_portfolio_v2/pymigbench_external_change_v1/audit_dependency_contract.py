"""Audit whether real migration commits update dependency manifests."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Iterable


MANIFEST_NAMES = {
    "setup.py",
    "setup.cfg",
    "pyproject.toml",
    "requirements.txt",
    "requirements.in",
    "pipfile",
    "pipfile.lock",
    "tox.ini",
    "environment.yml",
    "environment.yaml",
}


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def is_manifest(path: str) -> bool:
    name = Path(path).name.lower()
    return (
        name in MANIFEST_NAMES
        or name.startswith("requirements")
        or name.startswith("environment")
    )


def audit_row(row: dict[str, Any]) -> dict[str, Any]:
    fetch = row.get("fetch") or {}
    repo_dir = fetch.get("repo_dir")
    commit = row.get("commit")
    if not repo_dir or not commit or fetch.get("status") != "FETCHED":
        return {
            "repo": row.get("repo"),
            "commit": commit,
            "status": "NOT_AUDITED_FETCH_UNAVAILABLE",
        }
    repo = Path(repo_dir)
    changed = [
        path
        for path in git(
            repo, "diff-tree", "--no-commit-id", "--name-only", "-r", commit
        ).splitlines()
        if path
    ]
    manifests = [path for path in changed if is_manifest(path)]
    manifest_diff = ""
    if manifests:
        manifest_diff = git(
            repo,
            "show",
            "--format=",
            "--unified=0",
            commit,
            "--",
            *manifests,
        )
    source = str(row.get("source", "")).lower()
    target = str(row.get("target", "")).lower()
    source_declared = source and source in manifest_diff.lower()
    target_declared = target and target in manifest_diff.lower()
    return {
        "repo": row.get("repo"),
        "commit": commit,
        "source": row.get("source"),
        "target": row.get("target"),
        "status": "AUDITED",
        "changed_paths": changed,
        "manifest_paths": manifests,
        "manifest_changed": bool(manifests),
        "source_name_in_manifest_diff": bool(source_declared),
        "target_name_in_manifest_diff": bool(target_declared),
        "classification": (
            "TARGET_DECLARED"
            if target_declared
            else "MANIFEST_CHANGED_TARGET_NAME_NOT_FOUND"
            if manifests
            else "CODE_ONLY_NO_MANIFEST_CONTRACT"
        ),
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    receipt = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    rows = [audit_row(row) for row in receipt.get("candidate_attempts", [])]
    audited = [row for row in rows if row.get("status") == "AUDITED"]
    summary = {
        "attempted_rows": len(rows),
        "audited_rows": len(audited),
        "manifest_changed": sum(row["manifest_changed"] for row in audited),
        "code_only_no_manifest_contract": sum(
            row["classification"] == "CODE_ONLY_NO_MANIFEST_CONTRACT"
            for row in audited
        ),
        "target_declared": sum(
            row["classification"] == "TARGET_DECLARED" for row in audited
        ),
    }
    payload = {
        "schema": "pymigbench_dependency_contract_audit_v1",
        "status": "COMPLETE",
        "summary": summary,
        "rows": rows,
        "interpretation": (
            "A code-only migration can preserve tests while leaving installation "
            "contract stale; behavioral task builders must freeze and expose the "
            "target dependency contract separately."
        ),
    }
    Path(args.output).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
