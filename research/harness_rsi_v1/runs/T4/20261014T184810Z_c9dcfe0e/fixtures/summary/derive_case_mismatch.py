#!/usr/bin/env python3
"""Derive a mismatching SUMMARY-GUARD Markdown body only in a temporary path."""

from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: derive_case_mismatch.py MATCHING_BASE_MD DERIVED_MD")
    source = Path(sys.argv[1])
    destination = Path(sys.argv[2])
    text = source.read_text(encoding="utf-8")
    needle = "  request_count = 4\n"
    replacement = "  request_count = 3\n"
    if text.count(needle) != 1:
        raise SystemExit("matching base must contain exactly one request_count = 4 claim")
    destination.write_text(text.replace(needle, replacement), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
