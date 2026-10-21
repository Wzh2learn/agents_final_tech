"""Failure-safety contracts for the skill distribution script."""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC = REPO_ROOT / "scripts" / "graph" / "sync_skills.sh"


def _bash() -> str:
    if os.name == "nt":
        git = shutil.which("git")
        if git:
            git_bash = Path(git).resolve().parent.parent / "bin" / "bash.exe"
            if git_bash.is_file():
                return str(git_bash)
    return "bash"


def _run_sync(
    source_root: Path,
    destination_root: Path,
    *,
    fail_after: str | None = None,
):
    env = os.environ.copy()
    env["SKILL_SYNC_SOURCE"] = source_root.as_posix()
    if fail_after == "copy":
        env["SYNC_SKILLS_FAIL_AFTER_COPY"] = "sample"
    elif fail_after == "backup":
        env["SYNC_SKILLS_FAIL_AFTER_BACKUP"] = "sample"
    return subprocess.run(
        [_bash(), SYNC.as_posix(), "--sync-one", "sample", destination_root.as_posix()],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        encoding="utf-8",
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
    env["SKILL_SYNC_SOURCE"] = source_root.as_posix()

    result = subprocess.run(
        [_bash(), SYNC.as_posix(), "--sync-one", "../sample", destination_root.as_posix()],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )

    assert result.returncode == 2
    assert "INVALID skill name" in result.stdout
    assert (destination / "SKILL.md").read_text(encoding="utf-8") == "old\n"


def _check_fixture(tmp_path: Path) -> tuple[Path, Path, Path, str]:
    source_root = tmp_path / "source"
    codex_root = tmp_path / "codex"
    claude_root = tmp_path / "claude"
    lists = re.findall(r"^[AC]_SKILLS=\(([^)]+)\)$", SYNC.read_text(encoding="utf-8"), re.MULTILINE)
    assert len(lists) == 2
    for names, destination_root in zip(lists, (codex_root, claude_root)):
        for name in names.split():
            source = source_root / name
            destination = destination_root / name
            source.mkdir(parents=True, exist_ok=True)
            destination.mkdir(parents=True)
            (source / "SKILL.md").write_bytes(b"# sample\ncontract\n")
            (destination / "SKILL.md").write_bytes(b"# sample\r\ncontract\r\n")
    return source_root, codex_root, claude_root, lists[0].split()[0]


def _run_check(source_root: Path, codex_root: Path, claude_root: Path):
    env = os.environ.copy()
    env.update({
        "SKILL_SYNC_SOURCE": source_root.as_posix(),
        "CODEX_SKILLS_ROOT": codex_root.as_posix(),
        "CLAUDE_SKILLS_ROOT": claude_root.as_posix(),
        "SKILL_SYNC_CHECK_PYTHON": Path(sys.executable).as_posix(),
    })
    return subprocess.run(
        [_bash(), SYNC.as_posix(), "--check"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )


def test_check_accepts_only_line_ending_transport(tmp_path: Path) -> None:
    source_root, codex_root, claude_root, first_name = _check_fixture(tmp_path)
    result = _run_check(source_root, codex_root, claude_root)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS:" in result.stdout
    assert (codex_root / first_name / "SKILL.md").read_bytes() == b"# sample\r\ncontract\r\n"


def test_check_still_rejects_a_real_text_change(tmp_path: Path) -> None:
    source_root, codex_root, claude_root, first_name = _check_fixture(tmp_path)
    (codex_root / first_name / "SKILL.md").write_bytes(b"# sample\r\ncontract changed\r\n")
    result = _run_check(source_root, codex_root, claude_root)
    assert result.returncode == 1
    assert f"DRIFT: content differs: {first_name}" in result.stdout
    assert "file content differs: ./SKILL.md" in result.stdout


def test_eol_only_staging_corruption_is_still_rejected(tmp_path: Path, monkeypatch) -> None:
    source_root, destination_root, destination = _fixture(tmp_path)
    (source_root / "sample" / "SKILL.md").write_bytes(b"new\r\n")
    real_cp = subprocess.check_output([_bash(), "-c", "command -v cp"], text=True).strip()
    shim_dir = tmp_path / "shim"
    shim_dir.mkdir()
    shim = shim_dir / "cp"
    shim.write_bytes((
        "#!/usr/bin/env bash\nset -e\n"
        + shlex.quote(real_cp) + ' "$@"\n'
        + "printf 'new\\n' > \"${@: -1}/SKILL.md\"\n"
    ).encode("utf-8"))
    shim.chmod(0o755)
    if os.name == "nt":
        shell_shim_dir = subprocess.check_output(
            [_bash(), "-c", 'cygpath -u "$1"', "bash", shim_dir.as_posix()],
            text=True,
            encoding="utf-8",
        ).strip()
    else:
        shell_shim_dir = shim_dir.as_posix()
    # Git Bash prepends its system bin directory on startup. Set the shim PATH
    # inside the child shell so this negative control also runs on Windows.
    bash_env = tmp_path / "bash_env"
    bash_env.write_bytes(("export PATH=" + shlex.quote(shell_shim_dir) + ':"$PATH"\n').encode("utf-8"))
    monkeypatch.setenv("BASH_ENV", bash_env.as_posix())

    result = _run_sync(source_root, destination_root)

    assert result.returncode == 1
    assert "FAILED staging validation: sample" in result.stdout
    assert (destination / "SKILL.md").read_text(encoding="utf-8") == "old\n"
    assert (destination / "stale.txt").is_file()
    assert list(destination_root.glob(".skill-sync-*")) == []
