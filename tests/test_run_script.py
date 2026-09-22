"""Contract tests for the documented local development launcher.

The launcher runs only inside a temporary repository with process, network, and
container commands stubbed.  No real service, port, or Docker daemon is touched.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "run.sh"


def _write_executable(path: Path, body: str) -> None:
    path.write_text(f"#!/bin/bash\n{body}\n", encoding="utf-8")
    path.chmod(0o755)


def _isolated_launcher(tmp_path: Path, *, port_occupied: bool) -> tuple[Path, dict[str, str], Path]:
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    fake_bin = repo / "fake-bin"
    venv_bin = repo / "venv" / "bin"
    scripts.mkdir(parents=True)
    fake_bin.mkdir()
    venv_bin.mkdir(parents=True)
    shutil.copy2(SCRIPT, scripts / SCRIPT.name)
    (venv_bin / "activate").write_text("", encoding="utf-8")

    marker = repo / "uvicorn-invoked"
    _write_executable(fake_bin / "docker", "[ \"${1:-}\" = ps ] && echo pgvector")
    _write_executable(fake_bin / "curl", "exit 1")
    _write_executable(fake_bin / "sleep", "exit 0")
    _write_executable(fake_bin / "pkill", "exit 0")
    _write_executable(fake_bin / "nohup", "exit 0")
    _write_executable(
        fake_bin / "python",
        """
if [ "${1:-}" = "-c" ]; then
    if [[ "${2:-}" == *dotenv_values* ]]; then
        awk -F= -v key="${3:-}" '$1 == key {sub(/^[^=]*=/, ""); print; exit}' .env
        exit 0
    fi
    [ "${FAKE_PORT_OCCUPIED:-0}" = "1" ] && exit 0
    exit 1
fi
printf '%s\\n' "$*" > "$FAKE_UVICORN_MARKER"
exit 0
""".strip(),
    )

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["FAKE_PORT_OCCUPIED"] = "1" if port_occupied else "0"
    env["FAKE_UVICORN_MARKER"] = str(marker)
    return repo, env, marker


def test_launcher_refuses_to_replace_process_on_occupied_port(tmp_path: Path) -> None:
    repo, env, marker = _isolated_launcher(tmp_path, port_occupied=True)

    result = subprocess.run(
        ["bash", "scripts/run.sh"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "port 5050 is already in use" in (result.stdout + result.stderr).lower()
    assert not marker.exists(), "occupied-port path must not invoke Uvicorn"


def test_launcher_uses_foreground_exec_without_implicit_kill() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert "pkill" not in source
    assert "nohup" not in source
    assert "exec python -m uvicorn" in source


def test_launcher_honors_runtime_values_from_dotenv(tmp_path: Path) -> None:
    repo, env, marker = _isolated_launcher(tmp_path, port_occupied=False)
    (repo / ".env").write_text(
        "PGDATABASE_URL=postgresql://user:pass@127.0.0.1:15432/vector_db\n"
        "M1_PORT=15050\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["bash", "scripts/run.sh"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert marker.read_text(encoding="utf-8").endswith("--port 15050 --workers 2\n")
