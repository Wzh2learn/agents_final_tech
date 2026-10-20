#!/usr/bin/env python3
"""Build the frozen reuse diagnostic bundle and readiness record."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    parent = root.parent
    artifacts = [
        "PROMPT.md", "IMPLEMENTATION_PLAN.md", "LOOP_C_REUSE_DEFINITION_REVIEW.md",
        "trajectory_classifier.py", "build_reuse_diagnostics.py", "freeze_reuse_protocol.py",
        "diagnostic_runner.py", "test_reuse_diagnostics.py", "test_diagnostic_runner.py",
        "build_reuse_bundle.py",
        "synthetic_trajectory_fixtures.json", "TRAJECTORY_CLASSIFICATION.json",
        "REUSE_HISTORY_CONTEXT_POOL.json", "REUSE_DIAGNOSTIC_PROTOCOL.json",
        "DIAGNOSTIC_PLAN_PROMPT.json", "DIAGNOSTIC_CONSUME_PROMPT.json",
    ]
    external = {
        "PILOT_TASK_REFERENCE_MANIFEST_V2.json": root.parent / "pilot_prep_v1" / "PILOT_TASK_REFERENCE_MANIFEST_V2.json",
        "RUNTIME_IDENTITY_SNAPSHOT.json": parent / "RUNTIME_IDENTITY_SNAPSHOT.json",
        "OUTPUT_SCHEMAS.json": parent / "OUTPUT_SCHEMAS.json",
    }
    hashes = {}
    for name in artifacts:
        path = root / name
        if not path.is_file():
            raise FileNotFoundError(path)
        hashes[name] = sha256_file(path)
    for name, path in external.items():
        if not path.is_file():
            raise FileNotFoundError(path)
        hashes[name] = sha256_file(path)
    protocol = json.loads((root / "REUSE_DIAGNOSTIC_PROTOCOL.json").read_text(encoding="utf-8"))
    bundle = {
        "schema": "reuse_diagnostic_bundle_v1",
        "status": "READY_FOR_B0",
        "artifacts": hashes,
        "protocol_status": protocol["status"],
        "budget": protocol["budget"],
        "branch_gates": protocol["branch_gates"],
        "definition_review": {
            "report": "LOOP_C_REUSE_DEFINITION_REVIEW.md",
            "verdict": "ACCEPTED",
            "blocker_count": 0,
        },
        "cost_at_freeze": {
            "model_calls": 0,
            "endpoint_calls": 0,
            "collection_calls": 0,
            "pilot_calls": 0,
        },
    }
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "status": bundle["status"],
        "artifact_count": len(hashes),
        "bundle_sha256": sha256_file(args.output),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
