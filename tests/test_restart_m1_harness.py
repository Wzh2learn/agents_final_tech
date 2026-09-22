"""Contract tests for the :5050 harness restart SOP.

The script is executed only inside an isolated temporary repository with
stubbed process-control commands.  No real service or port is touched.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "restart_m1_harness.sh"


def _write_executable(path: Path, body: str) -> None:
    path.write_text(f"#!/bin/bash\n{body}\n", encoding="utf-8")
    path.chmod(0o755)


def test_restart_archives_previous_log_before_starting_new_process(tmp_path: Path) -> None:
    """A restart preserves the prior lifecycle log and starts a marked new one."""
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    logs = repo / "logs"
    fake_bin = repo / "fake-bin"
    scripts.mkdir(parents=True)
    logs.mkdir()
    fake_bin.mkdir()
    shutil.copy2(SCRIPT, scripts / SCRIPT.name)

    current_log = logs / "m1_service.log"
    current_log.write_text("previous-instance-failure\n", encoding="utf-8")

    _write_executable(fake_bin / "pkill", "exit 0")
    _write_executable(fake_bin / "sleep", "exit 0")
    _write_executable(fake_bin / "nohup", "printf 'fresh-instance-output\\n'")

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    result = subprocess.run(
        ["bash", str(scripts / SCRIPT.name)],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    archived = list((logs / "archive" / "m1_service").glob("m1_service_*.log"))
    assert len(archived) == 1
    assert archived[0].read_text(encoding="utf-8") == "previous-instance-failure\n"

    new_log = current_log.read_text(encoding="utf-8")
    assert "restart started_at=" in new_log
    assert "fresh-instance-output" in new_log
    assert "previous-instance-failure" not in new_log
