"""Skill drift checks ignore transport EOL only, never substantive differences."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pytest


HELPER = Path(__file__).resolve().parents[1] / "scripts" / "graph" / "skill_tree_compare.py"
spec = importlib.util.spec_from_file_location("skill_tree_compare", HELPER)
comparator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparator)


def _trees(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    installed = tmp_path / "installed"
    source.mkdir()
    installed.mkdir()
    return source, installed


def test_utf8_crlf_transport_is_equal_without_mutating_files(tmp_path: Path) -> None:
    source, installed = _trees(tmp_path)
    for root in (source, installed):
        (root / "nested").mkdir()
    left = "说明\nkeep trailing space \nlast line\n".encode("utf-8")
    right = left.replace(b"\n", b"\r\n")
    (source / "nested" / "SKILL.md").write_bytes(left)
    (installed / "nested" / "SKILL.md").write_bytes(right)

    assert comparator.compare_trees(source, installed) == []
    assert (source / "nested" / "SKILL.md").read_bytes() == left
    assert (installed / "nested" / "SKILL.md").read_bytes() == right


@pytest.mark.parametrize("payload", [b"plain\n", b"\xff\x00\r\n", b"\xef\xbb\xbftext\r\n"])
def test_identical_files_are_equal_including_binary_and_bom(tmp_path: Path, payload: bytes) -> None:
    source, installed = _trees(tmp_path)
    for root in (source, installed):
        (root / "asset").write_bytes(payload)
    assert comparator.compare_trees(source, installed) == []


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (b"value\r\n", b"other\n"),
        (b"value\r\n", b"value \n"),
        (b"value\r\n", b"value\t\n"),
        (b"value\r\n", b"\xef\xbb\xbfvalue\n"),
        (b"value\r", b"value\n"),
        (b"value\r\n", b"value"),
        (b"\xffvalue\r\n", b"\xffvalue\n"),
        (b"\0value\r\n", b"\0value\n"),
    ],
)
def test_substantive_or_binary_differences_are_rejected(tmp_path: Path, left: bytes, right: bytes) -> None:
    source, installed = _trees(tmp_path)
    (source / "asset").write_bytes(left)
    (installed / "asset").write_bytes(right)
    assert comparator.compare_trees(source, installed) == ["file content differs: ./asset"]


@pytest.mark.parametrize("extra_side", ["source", "installed"])
@pytest.mark.parametrize("entry_kind", ["file", "empty_directory"])
def test_missing_extra_entries_are_rejected(tmp_path: Path, extra_side: str, entry_kind: str) -> None:
    source, installed = _trees(tmp_path)
    extra_root = source if extra_side == "source" else installed
    entry = extra_root / ".hidden-extra"
    if entry_kind == "file":
        entry.write_bytes(b"")
    else:
        entry.mkdir()
    differences = comparator.compare_trees(source, installed)
    assert len(differences) == 1 and ".hidden-extra" in differences[0]


def test_file_directory_mismatch_is_rejected(tmp_path: Path) -> None:
    source, installed = _trees(tmp_path)
    (source / "asset").write_bytes(b"")
    (installed / "asset").mkdir()
    assert comparator.compare_trees(source, installed) == ["entry type differs: ./asset"]


def _symlink(target: str, link: Path, *, directory: bool = False) -> None:
    try:
        link.symlink_to(target, target_is_directory=directory)
    except OSError as exc:
        if os.name == "nt" and getattr(exc, "winerror", None) == 1314:
            pytest.skip("Windows account lacks symlink privilege")
        raise


def test_identical_dangling_symlinks_are_compared_without_following(tmp_path: Path) -> None:
    source, installed = _trees(tmp_path)
    _symlink("missing-target", source / "link")
    _symlink("missing-target", installed / "link")
    assert comparator.compare_trees(source, installed) == []


def test_different_symlink_targets_are_rejected(tmp_path: Path) -> None:
    source, installed = _trees(tmp_path)
    _symlink("first-target", source / "link")
    _symlink("second-target", installed / "link")
    assert comparator.compare_trees(source, installed) == ["symlink target differs: ./link"]


def test_directory_symlink_is_not_treated_as_a_regular_directory(tmp_path: Path) -> None:
    source, installed = _trees(tmp_path)
    _symlink("missing-directory", source / "link", directory=True)
    (installed / "link").mkdir()
    assert comparator.compare_trees(source, installed) == ["entry type differs: ./link"]


def test_cli_distinguishes_match_drift_and_read_error(tmp_path: Path) -> None:
    source, installed = _trees(tmp_path)
    assert subprocess.run([sys.executable, str(HELPER), str(source), str(installed)], capture_output=True).returncode == 0
    (installed / "extra").write_bytes(b"")
    drift = subprocess.run([sys.executable, str(HELPER), str(source), str(installed)], capture_output=True, text=True)
    assert drift.returncode == 1 and "extra installed entry" in drift.stdout
    error = subprocess.run([sys.executable, str(HELPER), str(source / "missing"), str(installed)], capture_output=True, text=True)
    assert error.returncode == 2 and "comparison error" in error.stderr
