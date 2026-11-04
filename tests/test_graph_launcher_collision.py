"""Test task identity with a fake tmux; no agent or service is launched."""

import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts/graph/loop_ac_launcher.sh"
pytestmark = pytest.mark.skipif(os.name != "posix" or not shutil.which("bash"), reason="requires POSIX bash")


@pytest.fixture
def launch_env(tmp_path):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    tmux = bindir / "tmux"
    tmux.write_text('#!/bin/sh\n[ "$1" = has-session ] && exit 1\nexit 0\n', encoding="utf-8")
    tmux.chmod(0o755)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("offline test only\n", encoding="utf-8")
    env = {"PATH": str(bindir) + os.pathsep + os.environ.get("PATH", ""),
           "HOME": os.environ["HOME"],
           "PROJECT_DIR": str(ROOT), "LOOP_RUN_ROOT": str(tmp_path / "runs"),
           "JINRONG_AGENT_PATHS_FILE": str(tmp_path / "no-paths.env")}
    return tmp_path / "runs", prompt, env


def launch(prompt, env, role="a", task="example"):
    return subprocess.run(["bash", str(LAUNCHER), "start", role, task, str(prompt), "10"],
                          env=env, text=True, capture_output=True, timeout=10)


def test_existing_role_receipt_is_never_overwritten(launch_env):
    runs, prompt, env = launch_env
    assert launch(prompt, env).returncode == 0
    status = runs / "example/a.status.json"
    original = status.read_bytes()

    result = launch(prompt, env)

    assert result.returncode != 0
    assert status.read_bytes() == original
    assert json.loads(original)["status"] == "running"
    assert launch(prompt, env, role="c").returncode == 0


def test_existing_orphan_log_blocks_restart(launch_env):
    runs, prompt, env = launch_env
    run = runs / "example"
    run.mkdir(parents=True)
    (run / "a.log").write_text("prior evidence\n", encoding="utf-8")

    result = launch(prompt, env)

    assert result.returncode != 0
    assert (run / "a.log").read_text(encoding="utf-8") == "prior evidence\n"
    assert not (run / "a.status.json").exists()


def test_concurrent_same_role_has_exactly_one_winner(launch_env):
    runs, prompt, env = launch_env
    args = ["bash", str(LAUNCHER), "start", "a", "example", str(prompt), "10"]
    first = subprocess.Popen(args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    second = subprocess.Popen(args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    first.communicate(timeout=10)
    second.communicate(timeout=10)

    assert sorted([first.returncode, second.returncode]) == [0, 2]
    assert json.loads((runs / "example/a.status.json").read_text())["status"] == "running"
