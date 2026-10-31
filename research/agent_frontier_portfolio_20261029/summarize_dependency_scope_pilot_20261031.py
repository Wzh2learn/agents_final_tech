#!/usr/bin/env python3
"""Summarize frozen Agent receipts and scanner-relative scope checks."""

import argparse
import hashlib
import json
from pathlib import Path

from score_dependency_scope_20261031 import evaluate


CONDITIONS = ("source", "learn", "target_none", "target_history",
              "target_generated_skill", "target_native_skills")


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def collect(args):
    report = json.loads(args.scanner_report.read_text(encoding="utf-8"))
    initial = json.loads(args.metadata.read_text(encoding="utf-8"))
    cases = {}
    for folder in args.runs.iterdir():
        intervention = folder / "intervention.json"
        if not intervention.is_file():
            continue
        config = json.loads(intervention.read_text(encoding="utf-8"))
        condition = config["condition"]
        if condition not in CONDITIONS or condition in cases:
            raise ValueError("unknown or duplicate condition: " + condition)
        receipt = json.loads((folder / "receipt.json").read_text(encoding="utf-8"))
        if sha(folder / "raw.jsonl") != receipt["raw_sha256"]:
            raise ValueError("raw digest differs: " + condition)
        amounts = receipt.get("step_finish_tokens", [])
        usage = {k: sum(int(item.get(k) or 0) for item in amounts)
                 for k in ("total", "input", "output", "reasoning")}
        usage["cache_read"] = sum(int((item.get("cache") or {}).get("read") or 0) for item in amounts)
        calls = receipt["model_http_requests"]
        metadata_copies = []
        for path in sorted((folder / "work").rglob("metadata.json")):
            try:
                metadata = json.loads(path.read_text(encoding="utf-8"))
            except (ValueError, UnicodeError, OSError):
                continue
            if isinstance(metadata, dict) and {"Version", "UpdatedAt", "DownloadedAt"} <= set(metadata):
                metadata_copies.append({"path": str(path.relative_to(folder / "work")).replace("\\", "/"),
                                        "same_as_initial": metadata == initial,
                                        "updated_at": metadata.get("UpdatedAt"),
                                        "downloaded_at": metadata.get("DownloadedAt"),
                                        "next_update": metadata.get("NextUpdate"),
                                        "sha256": sha(path)})
        item = {"case_name": folder.name, "agent_exit": receipt["agent_exit"],
                "original_verifier_exit": receipt["verifier_exit"],
                "elapsed_seconds": receipt["elapsed_seconds"],
                "forwarded_post": sum(x.startswith("POST ") for x in calls),
                "denied": [x for x in calls if x.startswith("DENIED")],
                "reported_step_tokens": usage, "raw_sha256": receipt["raw_sha256"],
                "history_sha256": config.get("history_sha256"),
                "skill_sha256": config.get("skill_sha256"), "metadata_copies": metadata_copies}
        if condition != "learn":
            scope = "high" if condition == "source" else "cvss_gt_8"
            path = folder / "work/security_audit.csv"
            item["scope_check"] = evaluate(path, report, scope)
            item["output_csv_sha256"] = sha(path) if path.is_file() else None
        else:
            skill = folder / "work/experience.md"
            item["generated_skill_sha256"] = sha(skill) if skill.is_file() else None
            item["generated_skill_characters"] = len(skill.read_text(encoding="utf-8")) if skill.is_file() else 0
        cases[condition] = item
    if set(cases) != set(CONDITIONS):
        raise ValueError("conditions incomplete: " + repr(sorted(set(CONDITIONS) - set(cases))))
    if cases["learn"]["generated_skill_sha256"] != cases["target_generated_skill"]["skill_sha256"]:
        raise ValueError("target used a different skill")
    if cases["learn"]["history_sha256"] != cases["target_history"]["history_sha256"]:
        raise ValueError("learning and history groups saw different source histories")
    totals = {"forwarded_post": sum(x["forwarded_post"] for x in cases.values()),
              "denied": sum(len(x["denied"]) for x in cases.values()),
              "reported_step_tokens": {key: sum(x["reported_step_tokens"][key] for x in cases.values())
                  for key in ("total", "input", "output", "reasoning", "cache_read")}}
    return {"status": "SINGLE_SOURCE_DEVELOPMENT_NOT_GENERALIZATION",
            "scanner_report_sha256": sha(args.scanner_report),
            "original_metadata_sha256": sha(args.metadata), "cases": cases, "totals": totals}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--scanner-report", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = collect(args)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"]))


if __name__ == "__main__":
    main()
