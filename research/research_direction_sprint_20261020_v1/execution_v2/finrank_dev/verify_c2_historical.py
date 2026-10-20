#!/usr/bin/env python3
"""Historical C2 verification with explicit source-snapshot limitation."""

from __future__ import annotations

import json

from finrank_contract import (
    PACKAGE,
    SHARED_LEDGER,
    load_object,
    sha256_file,
    write_json,
)


def check(name: str, condition: bool, observed: object) -> dict:
    return {"name": name, "pass": bool(condition), "observed": observed}


def main() -> int:
    bundle_path = PACKAGE / "BUNDLE_C2_B0_V3.json"
    bundle = load_object(bundle_path)
    fixture = load_object(PACKAGE / "FIXTURE_RECEIPT_C2.json")
    result_path = (
        PACKAGE
        / "results"
        / "B0_V3_EQUAL_VISIBILITY"
        / "B0_RESULT.json"
    )
    result = load_object(result_path)
    raw_root = PACKAGE / "raw" / "B0_V3_EQUAL_VISIBILITY"
    ledger = load_object(SHARED_LEDGER)
    records = ledger.get("request_records", [])
    c2_records = records[:42]
    checks = [
        check(
            "c2_bundle_hash",
            sha256_file(bundle_path)
            == "6b861dcfdbb8efd847b40652ad7abc90fde1cdf17686cc159b27b98d08e02b6e",
            {
                "bundle_sha256": sha256_file(bundle_path),
                "artifact_manifest_entries": len(bundle["artifacts"]),
            },
        ),
        check(
            "c2_fixture",
            fixture["status"] == "PASS"
            and fixture["passed"] == fixture["total"] == 17,
            {"passed": fixture["passed"], "total": fixture["total"]},
        ),
        check(
            "c2_b0_v3_original_result",
            result["success_count"] == 4
            and result["generation_requests"] == 14
            and len(result["results"]) == 7,
            {
                "success": result["success_count"],
                "requests": result["generation_requests"],
                "bundle_sha256": result["bundle_sha256"],
            },
        ),
        check(
            "c2_raw_preserved",
            len(list(raw_root.glob("*/request.json"))) == 14
            and len(list(raw_root.glob("*/response.json"))) == 14
            and not list(raw_root.glob("*/crash.json")),
            {
                "requests": len(list(raw_root.glob("*/request.json"))),
                "responses": len(list(raw_root.glob("*/response.json"))),
                "crashes": len(list(raw_root.glob("*/crash.json"))),
            },
        ),
        check(
            "c2_ledger_slice",
            len(c2_records) == 42
            and sum(item["accounting_tokens"] for item in c2_records)
            == 261902,
            {
                "requests": len(c2_records),
                "accounting_tokens": sum(
                    item["accounting_tokens"] for item in c2_records
                ),
            },
        ),
    ]
    passed = sum(item["pass"] for item in checks)
    output = {
        "schema": "finrank_c2_historical_verification_v1",
        "status": (
            "HISTORICAL_EVIDENCE_VERIFIED_WITH_REPRODUCIBILITY_LIMITATION"
            if passed == len(checks)
            else "FAIL"
        ),
        "passed": passed,
        "total": len(checks),
        "reproducibility_limitation": {
            "source_snapshot": "MISSING",
            "current_source_state": "DRIFTED_INTO_C3",
            "available_frozen_identity": (
                "BUNDLE_C2_B0_V3.json artifact hash manifest only"
            ),
            "claim_boundary": (
                "Historical fixture/result/raw/ledger evidence is verified; "
                "the C2 source tree is not reproducible from current files."
            ),
        },
        "known_blockers": [
            "LITERAL_PERCENT_SCORER_BUG",
            "ARBITRARY_PAIR_DERIVATION_SUPPORT_BUG",
            "ESD_012_OUTPUT_TRUNCATION",
        ],
        "checks": checks,
    }
    write_json(PACKAGE / "C2_VERIFICATION.json", output)
    print(
        json.dumps(
            {
                "status": output["status"],
                "passed": passed,
                "total": len(checks),
            },
            sort_keys=True,
        )
    )
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
