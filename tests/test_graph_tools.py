"""Pytest entry points for the mechanical Graph guard shell suites."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
BASH_AVAILABLE = shutil.which("bash") is not None


@pytest.mark.skipif(not BASH_AVAILABLE, reason="bash unavailable")
@pytest.mark.parametrize(
    "script",
    (
        "tests/graph_tools/test_git_commit_guard.sh",
        "tests/graph_tools/test_secret_scan.sh",
    ),
)
def test_graph_guard_shell_suite(script: str) -> None:
    result = subprocess.run(
        ["bash", script],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
