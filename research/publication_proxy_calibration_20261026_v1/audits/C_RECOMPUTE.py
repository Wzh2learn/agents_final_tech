#!/usr/bin/env python3
"""Loop C independent recompute helpers. Owned by the C joint review.

Read-only with respect to all A artifacts. Reproduces the counts and hashes
reported in TASK_RESULT_C.json so the audit does not have to trust A_RETURN.md.

Usage:
  python3 audits/C_RECOMPUTE.py recompute   # re-run the frozen 24-question regression
  python3 audits/C_RECOMPUTE.py manifest    # check ALL_FILES.sha256 integrity
  python3 audits/C_RECOMPUTE.py p1_identity # numeric vs complete-semantic counts
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[4]
P1 = PKG / "p1_rule_execution"

INSTANCES = Path("/home/testuser/wzh/research_runs/source_disjoint_confirmation_v4/source_disjoint_instances_v4.jsonl")
RESULTS = Path("/home/testuser/wzh/research_runs/source_disjoint_confirmation_v4/source_disjoint_results_v4.jsonl")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cmd_recompute() -> int:
    out = Path("/tmp/C_recompute_24.json")
    proc = subprocess.run(
        [
            sys.executable,
            str(P1 / "run_full_regression.py"),
            "--instances", str(INSTANCES),
            "--results", str(RESULTS),
            "--output", str(out),
        ],
        check=False,
    )
    if proc.returncode != 0:
        print("recompute failed, exit", proc.returncode)
        return proc.returncode
    mine = json.loads(out.read_text(encoding="utf-8"))
    theirs = json.loads((P1 / "full_24_regression.json").read_text(encoding="utf-8"))
    print("summary identical:", mine["summary"] == theirs["summary"])
    print("rows identical:", mine["rows"] == theirs["rows"])
    print("row count:", len(mine["rows"]))
    return 0


def cmd_manifest() -> int:
    man = PKG / "ALL_FILES.sha256"
    missing, mismatched, pyc = [], [], []
    n = 0
    for line in man.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split(None, 1)
        rel = rel.strip()
        n += 1
        path = PKG / rel
        if not path.exists():
            missing.append(rel)
            continue
        if sha256_file(path) != digest:
            mismatched.append(rel)
        if rel.endswith(".pyc"):
            pyc.append(rel)
    print(json.dumps({"entries": n, "missing": missing, "mismatched": mismatched, "pyc_listed": pyc}, indent=2))
    return 0


def cmd_p1_identity() -> int:
    rows = json.loads((P1 / "full_24_regression.json").read_text(encoding="utf-8"))["rows"]
    numeric = sum(1 for r in rows if r["actor_numeric_correct"])
    full = sum(
        1
        for r in rows
        if r["actor_numeric_correct"]
        and r["actor"]["unit"] == r["expected"].get("unit")
        and r["actor"]["evidence_refs"] == r["expected"].get("evidence_refs")
        and r["actor"]["citation_valid"]
    )
    unit_agree = sum(1 for r in rows if r["actor"]["unit"] == r["expected"].get("unit"))
    print("denominator:", len(rows))
    print("numeric program correct:", numeric)
    print("unit agreement:", unit_agree)
    print("complete semantic (value+unit+refs+citation):", full)
    print("baseline correct:", sum(1 for r in rows if r["baseline"]["program_correct"]))
    print("repairs:", sum(1 for r in rows if r["genuine_repair"]))
    print("damage:", sum(1 for r in rows if r["damage"]))
    print("direction conflicts:", sum(1 for r in rows if r["direction_conflict"]))
    return 0


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "p1_identity"
    table = {"recompute": cmd_recompute, "manifest": cmd_manifest, "p1_identity": cmd_p1_identity}
    if mode not in table:
        print(__doc__)
        return 2
    return table[mode]()


if __name__ == "__main__":
    raise SystemExit(main())
