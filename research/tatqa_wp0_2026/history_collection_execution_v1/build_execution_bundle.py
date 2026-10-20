#!/usr/bin/env python3
"""Build the complete non-generative execution bundle and blocker register."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from execution_core import sha256_file, write_json_lf


REQUIRED_COUNTS = {"history": 12, "future_test": 16, "development": 4}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object required: {path}")
    return value


def review_verdict(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"(?:\*\*Verdict:|## Verdict:)\s*`([A-Z_]+)`", text)
    return match.group(1) if match else "UNRESOLVED"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--review-report", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = read_json(root / "TASK_REFERENCE_MANIFEST.json")
    execution_plan = read_json(root / "EXECUTION_PLAN.json")
    runtime = read_json(root / "RUNTIME_IDENTITY_SNAPSHOT.json")
    window = read_json(root / "COLLECTION_WINDOW_PROPOSAL.json")

    blockers: list[str] = []
    counts = manifest.get("counts", {})
    if any(counts.get(key) != value for key, value in REQUIRED_COUNTS.items()):
        blockers.append("task_manifest_counts_invalid")
    if counts.get("qualification_fixtures") != 3:
        blockers.append("qualification_fixture_count_invalid")
    if execution_plan.get("request_cap") != 54 or len(execution_plan.get("request_slots", [])) != 54:
        blockers.append("execution_plan_request_cap_invalid")
    if execution_plan.get("token_cap") != 600000 or execution_plan.get("retry_cap") != 0:
        blockers.append("execution_plan_budget_invalid")
    if runtime.get("status") != "BOUND_NON_GENERATIVE_IDENTITY" or runtime.get("blockers"):
        blockers.append("runtime_identity_not_bound")
    if window.get("status") != "PROPOSED_NOT_AUTHORIZED" or window.get("duration_minutes") != 90:
        blockers.append("window_proposal_invalid")
    review_status = "PENDING"
    if args.review_report is not None:
        review_status = review_verdict(args.review_report)
        if review_status != "ACCEPTED":
            blockers.append("incremental_review_not_accepted")
    else:
        blockers.append("incremental_review_missing")

    artifact_paths = [
        "PROMPT.md",
        "IMPLEMENTATION_PLAN.md",
        "IMPLEMENTATION_DELTA.md",
        "execution_core.py",
        "build_task_manifest.py",
        "build_runtime_identity.py",
        "collection_runner.py",
        "run_execution_tests.py",
        "build_execution_bundle.py",
        "TASK_REFERENCE_MANIFEST.json",
        "EXECUTION_PLAN.json",
        "RUNTIME_IDENTITY_SNAPSHOT.json",
        "RUNTIME_POLICY.json",
        "PROMPT_PLAN.json",
        "PROMPT_CONSUME.json",
        "OUTPUT_SCHEMAS.json",
        "COLLECTION_WINDOW_PROPOSAL.json",
        "EXECUTION_AUTHORIZATION_SCHEMA.json",
        "INCREMENTAL_REVIEW_PROMPT.md",
        "TARGETED_REAUDIT_PROMPT.md",
        "LOOP_C_INCREMENTAL_REVIEW.md",
        "TARGETED_INCREMENT_REAUDIT_PROMPT.md",
        "MANIFEST_COMPARISON.json",
        "CHANGE_RECORD.md",
        "RETRY_FIX_CHANGE_RECORD.md",
        "RETRY_FIX_REAUDIT_PROMPT.md",
        "authorized_run_v1/PROMPT.md",
        "authorized_run_v1/IMPLEMENTATION_PLAN.md",
        "baseline_0d13f556/PRE_COLLECTION_EXECUTION_BUNDLE.json",
        "failed_run_5a389f0e/PRE_COLLECTION_EXECUTION_BUNDLE.json",
        "failed_run_5a389f0e/COLLECTION_RETURN.md",
        "failed_run_21e83312/PRE_COLLECTION_EXECUTION_BUNDLE.json",
        "failed_run_21e83312/COLLECTION_RETURN.md",
        "failed_run_8819c732/PRE_COLLECTION_EXECUTION_BUNDLE.json",
        "failed_run_8819c732/COLLECTION_RETURN.md",
        "tests/test_execution_v1.py",
        "tests/TEST_RECEIPT_LOCAL.json",
        "tests/TEST_RECEIPT_GB10.json",
    ]
    if args.review_report is not None:
        artifact_paths.append(args.review_report.name)
    artifacts = {}
    for relative in artifact_paths:
        path = root / relative
        if not path.is_file():
            blockers.append(f"missing_artifact:{relative}")
        else:
            artifacts[relative] = sha256_file(path)
    if args.output.name in artifacts:
        blockers.append("bundle_must_not_hash_itself")
    bundle = {
        "schema": "pre_collection_execution_bundle_v1",
        "status": (
            "READY_FOR_SINGLE_COLLECTION_AUTHORIZATION"
            if not blockers
            else "NOT_READY_FOR_COLLECTION"
        ),
        "owner_review_state": (
            "READY_WITH_ZERO_BLOCKERS"
            if not blockers
            else "BLOCKERS_RECORDED"
        ),
        "review": {
            "incremental_review_report": "LOOP_C_INCREMENTAL_REVIEW.md",
            "targeted_reaudit_report": (
                args.review_report.name if args.review_report is not None else None
            ),
            "verdict": review_status,
        },
        "task_reference_qualification": {
            "status": manifest["status"],
            "counts": counts,
            "references_recomputed": all(
                row["hidden"]["reference"]["status"] == "REFERENCE_RECOMPUTED"
                for row in manifest["tasks"]
            ),
            "candidate_gold_agreement": all(
                row["qualification"]["candidate_gold_agreement"] is True
                for row in manifest["tasks"]
            ),
        },
        "budget": {
            "request_cap": execution_plan["request_cap"],
            "token_cap": execution_plan["token_cap"],
            "per_request_reserve_tokens": execution_plan["per_request_reserve_tokens"],
            "retry_cap": execution_plan["retry_cap"],
            "concurrency": execution_plan["concurrency"],
        },
        "window_proposal": window,
        "runtime_identity": {
            "status": runtime["status"],
            "blockers": runtime["blockers"],
        },
        "artifacts": artifacts,
        "blockers": blockers,
        "cost": {
            "model_calls": 0,
            "endpoint_calls": 0,
            "judge_calls": 0,
            "training_calls": 0,
            "collection_calls": 0,
            "pilot_calls": 0,
            "service_starts": 0,
        },
    }
    write_json_lf(args.output, bundle)
    print(json.dumps({
        "output": str(args.output),
        "status": bundle["status"],
        "blockers": blockers,
        "artifact_count": len(artifacts),
    }, sort_keys=True))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
