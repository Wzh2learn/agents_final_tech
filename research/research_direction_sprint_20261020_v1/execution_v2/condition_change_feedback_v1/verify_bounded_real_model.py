#!/usr/bin/env python3
"""Verify the completed Tier 1 model run."""

from __future__ import annotations

import json
from pathlib import Path

from run_bounded_real_model import (
    CC013_PROBE_PATH,
    PARTIAL_PATH,
    RAW_ROOT,
    REFERENCE_PATH,
    RESULT_PATH,
    RUN_MANIFEST_PATH,
    RUNTIME_QUALIFICATION_PATH,
    SHARED_LEDGER,
    load_object,
    metrics,
    pair_metrics,
    sha256_file,
    write_json,
)


def main() -> int:
    manifest = load_object(RUN_MANIFEST_PATH)
    result = load_object(RESULT_PATH)
    references_by_id = {
        item["task_id"]: item
        for item in load_object(REFERENCE_PATH)["references"]
    }
    ledger = load_object(SHARED_LEDGER)
    checks = []

    def check(name: str, passed: bool, observed: object) -> None:
        checks.append({"name": name, "pass": bool(passed), "observed": observed})

    check(
        "manifest",
        manifest["status"] == "FROZEN_BEFORE_REQUESTS"
        and manifest["run_id"] == result["run_id"],
        manifest["status"],
    )
    check(
        "hashes",
        sha256_file(RUNTIME_QUALIFICATION_PATH)
        == manifest["runtime_qualification_sha256"]
        and sha256_file(CC013_PROBE_PATH) == manifest["cc013_probe_sha256"],
        {
            "runtime": sha256_file(RUNTIME_QUALIFICATION_PATH),
            "probe": sha256_file(CC013_PROBE_PATH),
        },
    )
    cc013 = load_object(CC013_PROBE_PATH)
    check(
        "cc013",
        cc013["status"] == "PASS"
        and cc013["rows"][1]["observed"]
        == {"pre": "sufficient", "post": "insufficient"},
        cc013["rows"],
    )
    check(
        "raw",
        len(list(RAW_ROOT.rglob("request.json"))) == 26
        and len(list(RAW_ROOT.rglob("response.json"))) == 26
        and not list(RAW_ROOT.rglob("crash.json")),
        {
            "requests": len(list(RAW_ROOT.rglob("request.json"))),
            "responses": len(list(RAW_ROOT.rglob("response.json"))),
        },
    )
    records = [
        item
        for item in ledger["request_records"]
        if item["run_id"] == "CONDITION_CHANGE_TIER1_20261020"
    ]
    check(
        "ledger",
        len(records) == 26
        and all(item["status"] == "OK" for item in records)
        and sum(item["usage_total_tokens"] for item in records)
        == result["run_accounting_tokens"],
        len(records),
    )
    budget = ledger["new_generation_budget"]
    check(
        "budget",
        budget["requests_used"] == 82
        and budget["accounting_tokens_used"] == 504_701
        and budget["judge_calls"] == 0
        and budget["training_calls"] == 0
        and budget["production_memory_writes"] == 0,
        budget,
    )
    check(
        "result",
        result["status"] == "COMPLETE_TIER1"
        and result["generation_requests"] == 26
        and result["stop_reason"] is None,
        result["status"],
    )
    check(
        "metrics",
        metrics(result["results"]) == result["overall"],
        result["overall"],
    )
    invalid = [
        row for row in result["results"] if row["submission_status"] != "VALID"
    ]
    check(
        "invalid_unrepaired",
        len(invalid) == 8
        and all(row["submission"] is None for row in invalid)
        and all(
            row["error"].startswith("submission_keys_invalid") for row in invalid
        ),
        [row["task_id"] for row in invalid],
    )
    valid = [
        row for row in result["results"] if row["submission_status"] == "VALID"
    ]
    valid_metrics = metrics(valid)
    valid_pairs = pair_metrics(valid, references_by_id)
    check(
        "valid_diagnostic",
        len(valid) == 18
        and valid_metrics["answer_covered_count"] == 17
        and valid_metrics["plan_sufficient_count"] == 18
        and valid_metrics["composite_accepted_count"] == 16
        and valid_pairs["decision_flip_revision_rate"] == 1.0
        and valid_pairs["invariant_preservation_rate"] == 1.0,
        {"metrics": valid_metrics, "pairs": valid_pairs},
    )
    partial = load_object(PARTIAL_PATH)
    check(
        "partial",
        partial["run_tokens"] == result["run_accounting_tokens"]
        and len(partial["results"]) == 26,
        partial["run_tokens"],
    )
    passed = sum(item["pass"] for item in checks)
    output = {
        "checks": checks,
        "file_hashes": {
            "BOUNDED_REAL_MODEL_RESULT.json": sha256_file(RESULT_PATH),
            "BOUNDED_REAL_MODEL_RUN_MANIFEST.json": sha256_file(
                RUN_MANIFEST_PATH
            ),
            "CC013_ALTERNATE_PATH_PROBE.json": sha256_file(CC013_PROBE_PATH),
        },
        "passed": passed,
        "runtime": {
            "judge_calls": 0,
            "model_requests": 26,
            "production_memory_writes": 0,
            "training_calls": 0,
        },
        "schema": "condition_change_real_model_verification_v1",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "total": len(checks),
        "valid_only_diagnostic": {
            "metrics": valid_metrics,
            "pair_behavior": valid_pairs,
        },
    }
    write_json(
        Path(__file__).resolve().parent
        / "CONDITION_CHANGE_REAL_MODEL_VERIFICATION.json",
        output,
    )
    print(json.dumps({"passed": passed, "total": len(checks)}, sort_keys=True))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
