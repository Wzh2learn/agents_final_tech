#!/usr/bin/env python3
"""Validate an offline research snapshot; never run or approve research.

Usage: python scripts/graph/research_evidence_graph.py --root WORKDIR SNAPSHOT.json

Version 1 has arrays `candidates`, `evidence`, `trials`, and `reviews`.
Candidates contain id, parent (id or null), hypothesis, baseline, source and
conclusion. Evidence contains id, relative path and SHA-256. Trials contain id,
candidate, phase, outcome, status, evidence IDs, cost (number or null), and
cost_unit. Trial statuses are success, failure, engineering_failure, unknown,
or inconclusive. Reviews
contain id, candidate, reviewer, conclusion and evidence IDs. Free text is
recorded context, not a verified claim. Null cost means unknown; zero means zero.

Minimal draft snapshot (use actual IDs, claims and files for real work)::

  {"version": 1,
   "candidates": [{"id": "idea-1", "parent": null,
     "hypothesis": "feedback helps", "baseline": "ordinary history",
     "source": "paper or trace", "conclusion": "not yet tested"}],
   "evidence": [], "trials": [], "reviews": []}

For a completed trial, add its evidence file relative to --root with its
SHA-256, then reference that evidence ID. Unknown/inconclusive trials can omit
evidence but must still explicitly record a numeric cost or null and its unit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


def _path(root: Path, name: Any) -> Path:
    if not isinstance(name, str) or not name:
        raise ValueError("path must be a nonempty relative string")
    rel = Path(name)
    if rel.is_absolute() or rel.drive or ".." in rel.parts:
        raise ValueError("absolute and parent paths are forbidden")
    path = (root / rel).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("path resolves outside root") from exc
    if not path.is_file():
        raise ValueError("file missing or not a regular file")
    return path


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _unique_object(pairs):
    """Reject duplicate keys at every object depth when decoding snapshots."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def validate(root: Path, snapshot: Any) -> dict:
    """Check schema, links, ancestry and evidence bytes within a single root."""
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("root must be a directory")
    errors = []
    if not isinstance(snapshot, dict) or type(snapshot.get("version")) is not int or snapshot.get("version") != 1:
        return {"valid": False, "errors": ["snapshot version must be 1"]}

    sections = {}
    ids = set()
    for name in ("candidates", "evidence", "trials", "reviews"):
        rows = snapshot.get(name)
        if not isinstance(rows, list):
            errors.append(name + " must be an array")
            rows = []
        index = {}
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"].strip():
                errors.append(name + " has invalid id")
                continue
            ident = row["id"]
            if ident in ids:
                errors.append("duplicate id: " + ident)
            ids.add(ident)
            index[ident] = row
        sections[name] = index

    def text(row, key, context):
        if not isinstance(row.get(key), str) or not row[key].strip():
            errors.append(context + " missing " + key)

    candidates = sections["candidates"]
    if not candidates:
        errors.append("at least one candidate is required")
    for ident, row in candidates.items():
        for key in ("hypothesis", "baseline", "source", "conclusion"):
            text(row, key, ident)
        parent = row.get("parent")
        if "parent" not in row or (parent is not None and (not isinstance(parent, str) or parent not in candidates)):
            errors.append(ident + " has missing parent")

    for ident in candidates:
        seen = set()
        current = ident
        while isinstance(current, str) and current in candidates:
            if current in seen:
                errors.append("candidate ancestry cycle: " + ident)
                break
            seen.add(current)
            current = candidates[current].get("parent")

    checked = 0
    for ident, row in sections["evidence"].items():
        digest = row.get("sha256")
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            errors.append(ident + " has invalid sha256")
            continue
        try:
            if _digest(_path(root, row.get("path"))) != digest:
                errors.append(ident + " hash mismatch")
            else:
                checked += 1
        except (OSError, ValueError) as exc:
            errors.append(ident + " evidence: " + str(exc))

    for section in ("trials", "reviews"):
        for ident, row in sections[section].items():
            if not isinstance(row.get("candidate"), str) or row["candidate"] not in candidates:
                errors.append(ident + " has missing candidate")
            references = row.get("evidence")
            if not isinstance(references, list) or any(not isinstance(ref, str) or ref not in sections["evidence"] for ref in references):
                errors.append(ident + " has invalid evidence references")
            elif section == "trials" and row.get("status") in ("success", "failure", "engineering_failure") and not references:
                errors.append(ident + " requires evidence for a completed outcome")
            for key in (("phase", "outcome") if section == "trials" else ("reviewer", "conclusion")):
                text(row, key, ident)
            if section == "trials":
                if row.get("status") not in ("success", "failure", "engineering_failure", "unknown", "inconclusive"):
                    errors.append(ident + " has invalid trial status")
                text(row, "cost_unit", ident)
                cost = row.get("cost")
                if "cost" not in row or (cost is not None and (isinstance(cost, bool) or not isinstance(cost, (int, float)) or not 0 <= cost < float("inf"))):
                    errors.append(ident + " cost must be nonnegative or null")

    return {"valid": not errors, "errors": errors,
            "counts": {name: len(rows) for name, rows in sections.items()},
            "evidence_hashes_checked": checked,
            "evidence_binding_status": ("no_evidence_supplied" if not sections["evidence"] else
                                        "bindings_verified" if checked == len(sections["evidence"]) else
                                        "binding_errors"),
            "scope": "structure, ancestry and cited file bytes only; no claim, independence, review or authorization verification"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("snapshot", help="JSON file relative to root")
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve(strict=True)
        data = json.loads(_path(root, args.snapshot).read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
        report = validate(root, data)
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        report = {"valid": False, "errors": [str(exc)]}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
