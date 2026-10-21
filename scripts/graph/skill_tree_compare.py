#!/usr/bin/env python3
"""Read-only skill-tree check; tolerate only UTF-8 CRLF/LF transport changes.

Names, entry types and literal symlink targets must match. Regular files remain
byte-exact unless both are valid UTF-8 without NUL bytes; only CRLF pairs may
then be compared as LF. BOMs, whitespace, lone CRs and other content stay exact.
This helper is for installation drift checks, not staged-copy activation.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import stat
import sys


def _file_contents_match(left: Path, right: Path) -> bool:
    left_bytes = left.read_bytes()
    right_bytes = right.read_bytes()
    if left_bytes == right_bytes:
        return True
    if b"\0" in left_bytes or b"\0" in right_bytes:
        return False
    try:
        left_bytes.decode("utf-8", errors="strict")
        right_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return False
    return left_bytes.replace(b"\r\n", b"\n") == right_bytes.replace(b"\r\n", b"\n")


def compare_trees(left: Path, right: Path) -> list[str]:
    """Return differences without following symlinks or changing either tree."""
    differences: list[str] = []

    def compare_entry(left_path: Path, right_path: Path, relative: str) -> None:
        left_kind = stat.S_IFMT(left_path.lstat().st_mode)
        right_kind = stat.S_IFMT(right_path.lstat().st_mode)
        if left_kind != right_kind:
            differences.append(f"entry type differs: {relative}")
        elif left_kind == stat.S_IFLNK:
            if os.readlink(left_path) != os.readlink(right_path):
                differences.append(f"symlink target differs: {relative}")
        elif left_kind == stat.S_IFREG:
            if not _file_contents_match(left_path, right_path):
                differences.append(f"file content differs: {relative}")
        elif left_kind == stat.S_IFDIR:
            with os.scandir(left_path) as entries:
                left_names = {entry.name for entry in entries}
            with os.scandir(right_path) as entries:
                right_names = {entry.name for entry in entries}
            for name in sorted(left_names - right_names):
                differences.append(f"missing installed entry: {relative}/{name}")
            for name in sorted(right_names - left_names):
                differences.append(f"extra installed entry: {relative}/{name}")
            for name in sorted(left_names & right_names):
                compare_entry(left_path / name, right_path / name, f"{relative}/{name}")
        else:
            differences.append(f"unsupported entry type: {relative}")

    compare_entry(Path(left), Path(right), ".")
    return differences


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("installed", type=Path)
    args = parser.parse_args()
    try:
        differences = compare_trees(args.source, args.installed)
    except OSError as exc:
        print(f"skill-tree comparison error: {exc}", file=sys.stderr)
        return 2
    for difference in differences:
        print(difference)
    return 1 if differences else 0


if __name__ == "__main__":
    raise SystemExit(main())
