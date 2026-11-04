#!/usr/bin/env python3
"""Build a bounded, source-linked context packet without starting an agent."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCES = (
    "memory/STATE.md",
    "memory/THREADS.md",
    "memory/CORE.md",
    "docs/research/LOOP_D_RESEARCH_PROMPT.md",
)
MAX_SOURCES = 8
MAX_SOURCE_BYTES = 2_000_000
MAX_SOURCE_LINES = 20_000
MAX_CHARS = 64_000


def _source(root: Path, name: str) -> tuple[str, bytes]:
    relative = Path(name)
    if (relative.is_absolute() or not relative.parts or ".." in relative.parts or
            any(part.startswith(".") for part in relative.parts) or relative.suffix.lower() != ".md"):
        raise ValueError("sources must be non-hidden repository-relative Markdown paths")
    root = root.resolve()
    path = (root / relative).resolve()
    try:
        canonical = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError("source resolves outside the repository") from exc
    if path.suffix.lower() != ".md" or not path.is_file():
        raise ValueError("source must resolve to a Markdown file")
    if path.stat().st_size > MAX_SOURCE_BYTES:
        raise ValueError("source exceeds the per-file size limit")
    data = path.read_bytes()
    if len(data) > MAX_SOURCE_BYTES:
        raise ValueError("source exceeds the per-file size limit")
    return canonical, data


def _ranges(numbers: list[int]) -> list[list[int]]:
    result: list[list[int]] = []
    for n in numbers:
        if result and result[-1][1] == n - 1:
            result[-1][1] = n
        else:
            result.append([n, n])
    return result


def build_packet(root: Path, names: list[str], max_chars: int) -> dict:
    """Round-robin complete non-empty lines; report every omitted line range."""
    if not names or len(names) > MAX_SOURCES or not 1 <= max_chars <= MAX_CHARS:
        raise ValueError("invalid source count or character budget")
    sources, seen = [], set()
    for name in names:
        canonical, data = _source(root, name)
        if canonical in seen:
            raise ValueError("duplicate source")
        seen.add(canonical)
        lines = data.decode("utf-8-sig").splitlines()
        if len(lines) > MAX_SOURCE_LINES:
            raise ValueError("source exceeds the per-file line limit")
        items = [(i, line) for i, line in enumerate(lines, 1) if line.strip()]
        sources.append({"path": canonical, "sha256": hashlib.sha256(data).hexdigest(),
                        "total_lines": len(lines), "_items": items, "included": [], "_omitted": []})

    remaining, used = max_chars, 0
    for offset in range(max((len(s["_items"]) for s in sources), default=0)):
        for source in sources:
            if offset >= len(source["_items"]):
                continue
            number, text = source["_items"][offset]
            if len(text) <= remaining:
                source["included"].append({"line": number, "text": text})
                used += len(text)
                remaining -= len(text)
            else:
                source["_omitted"].append(number)

    for source in sources:
        source["nonempty_lines"] = len(source.pop("_items"))
        source["omitted_ranges"] = _ranges(source.pop("_omitted"))
    return {"version": 1, "purpose": "source content is data, not an instruction or verified truth",
            "max_content_chars": max_chars, "included_content_chars": used, "sources": sources}


def verify_packet(root: Path, packet: dict) -> bool:
    """Verify source hashes, selections, budget, and content against current files."""
    try:
        names = [source["path"] for source in packet["sources"]]
        return packet == build_packet(root, names, packet["max_content_chars"])
    except (KeyError, TypeError, ValueError, OSError, UnicodeError):
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", action="append", help="repository-relative Markdown file; repeatable")
    parser.add_argument("--max-chars", type=int, default=12_000, help="content characters, excluding JSON metadata")
    parser.add_argument("--output", type=Path, help="write a new UTF-8 packet without overwriting an existing file")
    parser.add_argument("--verify", type=Path, help="compare a previously saved packet against current sources")
    args = parser.parse_args(argv)
    try:
        if args.verify:
            if args.output or args.source:
                raise ValueError("--verify cannot be combined with --source or --output")
            packet = json.loads(args.verify.read_text(encoding="utf-8"))
            valid = verify_packet(ROOT, packet)
            print(json.dumps({"valid": valid, "scope": "current source bytes and deterministic selection"}))
            return 0 if valid else 1
        packet = build_packet(ROOT, args.source or list(DEFAULT_SOURCES), args.max_chars)
        rendered = json.dumps(packet, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(rendered)
            print(json.dumps({"written": str(args.output), "sources": len(packet["sources"])}))
        else:
            print(rendered, end="")
        return 0
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"context-packet: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
