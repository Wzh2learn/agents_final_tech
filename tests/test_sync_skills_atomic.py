"""Failure-safety contracts for the skill distribution script."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC = REPO_ROOT / "scripts" / "graph" / "sync_skills.sh"


def _run_sync(
    source_root: Path,
    destination_root: Path,
    *,
    fail_after: str | None = None,
):
    env = os.environ.copy()
    env["SKILL_SYNC_SOURCE"] = str(source_root)
    if fail_after == "copy":
        env["SYNC_SKILLS_FAIL_AFTER_COPY"] = "sample"
    elif fail_after == "backup":
        env["SYNC_SKILLS_FAIL_AFTER_BACKUP"] = "sample"
    return subprocess.run(
        ["bash", str(SYNC), "--sync-one", "sample", str(destination_root)],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
    )


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    source_root = tmp_path / "source"
    destination_root = tmp_path / "installed"
    source = source_root / "sample"
    destination = destination_root / "sample"
    source.mkdir(parents=True)
    destination.mkdir(parents=True)
    (source / "SKILL.md").write_text("new\n", encoding="utf-8")
    (source / "asset.txt").write_text("new asset\n", encoding="utf-8")
    (destination / "SKILL.md").write_text("old\n", encoding="utf-8")
    (destination / "stale.txt").write_text("stale\n", encoding="utf-8")
    return source_root, destination_root, destination


def test_sync_replaces_only_after_validated_copy(tmp_path: Path) -> None:
    source_root, destination_root, destination = _fixture(tmp_path)

    result = _run_sync(source_root, destination_root)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (destination / "SKILL.md").read_text(encoding="utf-8") == "new\n"
    assert (destination / "asset.txt").is_file()
    assert not (destination / "stale.txt").exists()
    assert list(destination_root.glob(".skill-sync-*")) == []


def test_injected_copy_failure_preserves_existing_install(tmp_path: Path) -> None:
    source_root, destination_root, destination = _fixture(tmp_path)

    result = _run_sync(source_root, destination_root, fail_after="copy")

    assert result.returncode != 0
    assert "injected failure" in result.stdout
    assert (destination / "SKILL.md").read_text(encoding="utf-8") == "old\n"
    assert (destination / "stale.txt").is_file()
    assert list(destination_root.glob(".skill-sync-*")) == []


def test_activation_failure_rolls_back_existing_install(tmp_path: Path) -> None:
    source_root, destination_root, destination = _fixture(tmp_path)

    result = _run_sync(source_root, destination_root, fail_after="backup")

    assert result.returncode != 0
    assert "injected failure after backup" in result.stdout
    assert (destination / "SKILL.md").read_text(encoding="utf-8") == "old\n"
    assert (destination / "stale.txt").is_file()
    assert list(destination_root.glob(".skill-sync-*")) == []


def test_missing_source_never_touches_existing_install(tmp_path: Path) -> None:
    source_root, destination_root, destination = _fixture(tmp_path)
    (source_root / "sample" / "SKILL.md").unlink()

    result = _run_sync(source_root, destination_root)

    assert result.returncode != 0
    assert "MISSING source: sample" in result.stdout
    assert (destination / "SKILL.md").read_text(encoding="utf-8") == "old\n"
    assert (destination / "stale.txt").is_file()


def test_sync_rejects_path_traversal_in_skill_name(tmp_path: Path) -> None:
    source_root, destination_root, destination = _fixture(tmp_path)
    env = os.environ.copy()
    env["SKILL_SYNC_SOURCE"] = str(source_root)

    result = subprocess.run(
        ["bash", str(SYNC), "--sync-one", "../sample", str(destination_root)],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 2
    assert "INVALID skill name" in result.stdout
    assert (destination / "SKILL.md").read_text(encoding="utf-8") == "old\n"
