#!/usr/bin/env python3
"""Summarize the separate four-arm budget-sensitivity run."""

import argparse
import hashlib
import json
import re
from pathlib import Path

from audit_dependency_cvss_sources_20261031 import check as check_cvss
from score_dependency_scope_20261031 import evaluate


TARGETS = {"target_none", "target_history", "target_generated_skill", "target_native_skills"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--scanner-report", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--initial", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    initial = json.loads(args.initial.read_text(encoding="utf-8"))["cases"]
    report = json.loads(args.scanner_report.read_text(encoding="utf-8"))
    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    cases = {}
    for folder in args.runs.iterdir():
        config = json.loads((folder / "intervention.json").read_text(encoding="utf-8"))
        condition = config["condition"]
        if condition not in TARGETS or condition in cases:
            raise ValueError("invalid or duplicate condition")
        if config["status"] != "POSTHOC_BUDGET_SENSITIVITY" or config["max_forwarded_http"] != 32:
            raise ValueError("wrong budget profile")
        for key in ("history_sha256", "skill_sha256"):
            if config.get(key) != initial[condition].get(key):
                raise ValueError("history or skill changed")
        receipt = json.loads((folder / "receipt.json").read_text(encoding="utf-8"))
        if sha(folder / "raw.jsonl") != receipt["raw_sha256"]:
            raise ValueError("raw hash mismatch")
        output = folder / "work/security_audit.csv"
        test_text = (folder / "verifier.txt").read_text(encoding="utf-8", errors="replace")
        passed, failed = re.search(r"(\d+) passed", test_text), re.search(r"(\d+) failed", test_text)
        metadata_copies = []
        for p in sorted((folder / "work").rglob("metadata.json")):
            try:
                item = json.loads(p.read_text(encoding="utf-8"))
            except (ValueError, OSError, UnicodeError):
                continue
            if isinstance(item, dict) and {"Version", "UpdatedAt", "DownloadedAt"} <= set(item):
                metadata_copies.append({"path": str(p.relative_to(folder / "work")).replace("\\", "/"),
                                        "same_as_initial": item == metadata,
                                        "updated_at": item.get("UpdatedAt"),
                                        "downloaded_at": item.get("DownloadedAt"),
                                        "next_update": item.get("NextUpdate")})
        calls = receipt["model_http_requests"]
        tokens = receipt.get("step_finish_tokens", [])
        cases[condition] = {"case_name": folder.name, "agent_exit": receipt["agent_exit"],
                            "original_verifier_exit": receipt["verifier_exit"],
                            "original_tests_passed": int(passed.group(1)) if passed else 0,
                            "original_tests_failed": int(failed.group(1)) if failed else 0,
                            "scope_check": evaluate(output, report, "cvss_gt_8"),
                            "cvss_source_check": check_cvss(output, report),
                            "metadata_copies": metadata_copies,
                            "forwarded_post": sum(x.startswith("POST ") for x in calls),
                            "denied": [x for x in calls if x.startswith("DENIED")],
                            "elapsed_seconds": receipt["elapsed_seconds"],
                            "reported_total_tokens": sum(int(x.get("total") or 0) for x in tokens),
                            "reported_cache_read": sum(int((x.get("cache") or {}).get("read") or 0) for x in tokens),
                            "raw_sha256": receipt["raw_sha256"],
                            "csv_sha256": sha(output) if output.is_file() else None}
    if set(cases) != TARGETS:
        raise ValueError("incomplete budget-sensitivity conditions")
    totals = {"forwarded_post": sum(v["forwarded_post"] for v in cases.values()),
              "denied": sum(len(v["denied"]) for v in cases.values()),
              "reported_total_tokens": sum(v["reported_total_tokens"] for v in cases.values()),
              "reported_cache_read": sum(v["reported_cache_read"] for v in cases.values())}
    result = {"status": "POSTHOC_BUDGET_SENSITIVITY_SINGLE_SOURCE", "cases": cases, "totals": totals}
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(totals))


if __name__ == "__main__":
    main()
