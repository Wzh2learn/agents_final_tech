"""Safe patch application and bounded test evaluation for migration tasks."""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable


DIFF_HEADER = re.compile(r"^diff --git a/(.+) b/(.+)$")


class PatchProtocolError(ValueError):
    """Raised when a patch crosses the task boundary or is malformed."""


def _safe_path(value: str) -> str:
    """Validate one repository-relative patch path."""

    path = Path(value)
    if path.is_absolute() or ".." in path.parts or value.startswith(".git/"):
        raise PatchProtocolError(f"unsafe_patch_path:{value}")
    return path.as_posix()


def validate_patch_paths(patch_text: str, allowed_paths: Iterable[str]) -> list[str]:
    """Reject binary, mode-changing, or out-of-scope patches."""

    allowed = {_safe_path(path) for path in allowed_paths}
    seen: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("GIT binary patch"):
            raise PatchProtocolError("binary_patch")
        if line.startswith("new file mode") or line.startswith("deleted file mode"):
            raise PatchProtocolError("file_creation_or_deletion")
        if line.startswith("rename from") or line.startswith("rename to"):
            raise PatchProtocolError("rename_patch")
        match = DIFF_HEADER.match(line)
        if not match:
            continue
        old_path = _safe_path(match.group(1))
        new_path = _safe_path(match.group(2))
        if old_path != new_path:
            raise PatchProtocolError("patch_path_mismatch")
        if old_path not in allowed:
            raise PatchProtocolError(f"patch_path_out_of_scope:{old_path}")
        seen.append(old_path)
    if not seen:
        raise PatchProtocolError("empty_patch")
    return seen


def apply_patch(repo: Path, patch_text: str, allowed_paths: Iterable[str]) -> dict:
    """Check and apply a unified diff to a disposable checkout."""

    changed = validate_patch_paths(patch_text, allowed_paths)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        suffix=".patch",
        delete=False,
    ) as handle:
        handle.write(patch_text)
        patch_path = Path(handle.name)
    try:
        check = subprocess.run(
            ["git", "apply", "--check", "--whitespace=nowarn", str(patch_path)],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        if check.returncode != 0:
            raise PatchProtocolError(
                f"git_apply_check_failed:{check.stderr.strip()}"
            )
        applied = subprocess.run(
            ["git", "apply", "--whitespace=nowarn", str(patch_path)],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        if applied.returncode != 0:
            raise PatchProtocolError(f"git_apply_failed:{applied.stderr.strip()}")
    finally:
        patch_path.unlink(missing_ok=True)
    return {
        "changed_paths": changed,
        "git_apply_check": check.returncode,
        "git_apply": applied.returncode,
    }


def evaluate_patch(repo: Path, command: list[str], timeout_seconds: int = 180) -> dict:
    """Run one bounded test command and preserve its complete output."""

    completed = subprocess.run(
        command,
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
    )
    return {
        "command": command,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "passed": completed.returncode == 0,
    }
