#!/usr/bin/env python3
"""Recompute two sequential target attempts without merging paired metrics."""

import argparse
import hashlib
import json
import re
from pathlib import Path

from audit_dependency_cvss_sources_20261031 import check as check_cvss
from score_dependency_scope_20261031 import evaluate


TARGETS = ("target_none", "target_history", "target_generated_skill", "target_native_skills")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(args):
    initial = json.loads(args.initial.read_text(encoding="utf-8"))
    report = json.loads(args.scanner_report.read_text(encoding="utf-8"))
    old_metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    groups = {key: [] for key in TARGETS}
    for folder in args.runs.iterdir():
        p = folder / "intervention.json"
        if not p.is_file():
            continue
        config = json.loads(p.read_text(encoding="utf-8"))
        condition = config["condition"]
        if condition not in groups:
            continue
        receipt = json.loads((folder / "receipt.json").read_text(encoding="utf-8"))
        if sha(folder / "raw.jsonl") != receipt["raw_sha256"]:
            raise ValueError("raw digest differs: " + folder.name)
        original = initial["cases"][condition]
        for name in ("history_sha256", "skill_sha256"):
            if config.get(name) != original.get(name):
                raise ValueError("condition received a changed history or skill: " + condition)
        score = evaluate(folder / "work/security_audit.csv", report, "cvss_gt_8")
        cvss = check_cvss(folder / "work/security_audit.csv", report)
        test_text = (folder / "verifier.txt").read_text(encoding="utf-8", errors="replace")
        passed = re.search(r"(\d+) passed", test_text)
        failed = re.search(r"(\d+) failed", test_text)
        metadata = []
        for path in sorted((folder / "work").rglob("metadata.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (ValueError, OSError, UnicodeError):
                continue
            if isinstance(data, dict) and {"Version", "UpdatedAt", "DownloadedAt"} <= set(data):
                metadata.append({"path": str(path.relative_to(folder / "work")).replace("\\", "/"),
                                 "same_as_initial": data == old_metadata,
                                 "updated_at": data.get("UpdatedAt"),
                                 "downloaded_at": data.get("DownloadedAt"),
                                 "next_update": data.get("NextUpdate")})
        step_tokens = receipt.get("step_finish_tokens", [])
        calls = receipt["model_http_requests"]
        row = {"round": 1 if folder.name == original["case_name"] else 2,
               "case_name": folder.name, "agent_exit": receipt["agent_exit"],
               "original_verifier_exit": receipt["verifier_exit"],
               "original_tests_passed": int(passed.group(1)) if passed else 0,
               "original_tests_failed": int(failed.group(1)) if failed else 0,
               "scope_check": score, "cvss_source_check": cvss,
               "metadata_copies": metadata, "elapsed_seconds": receipt["elapsed_seconds"],
               "forwarded_post": sum(x.startswith("POST ") for x in calls),
               "denied": [x for x in calls if x.startswith("DENIED")],
               "reported_total_tokens": sum(int(x.get("total") or 0) for x in step_tokens),
               "reported_cache_read": sum(int((x.get("cache") or {}).get("read") or 0) for x in step_tokens),
               "raw_sha256": receipt["raw_sha256"],
               "csv_sha256": sha(folder / "work/security_audit.csv") if (folder / "work/security_audit.csv").is_file() else None}
        groups[condition].append(row)
    for condition, rows in groups.items():
        if sorted(x["round"] for x in rows) != [1, 2]:
            raise ValueError("expected one initial run and one repeat for " + condition)
        rows.sort(key=lambda x: x["round"])
    target_totals = {"forwarded_post": sum(x["forwarded_post"] for rows in groups.values() for x in rows),
                     "denied": sum(len(x["denied"]) for rows in groups.values() for x in rows),
                     "reported_total_tokens": sum(x["reported_total_tokens"] for rows in groups.values() for x in rows),
                     "reported_cache_read": sum(x["reported_cache_read"] for rows in groups.values() for x in rows)}
    return {"status": "POSTHOC_REPEAT_SINGLE_SOURCE_NOT_CONFIRMATION", "groups": groups,
            "target_totals": target_totals,
            "initial_source_and_learning": {k: initial["cases"][k] for k in ("source", "learn")}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--initial", type=Path, required=True)
    parser.add_argument("--scanner-report", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = collect(args)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["target_totals"]))


if __name__ == "__main__":
    main()
