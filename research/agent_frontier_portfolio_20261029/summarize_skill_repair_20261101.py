#!/usr/bin/env python3
"""Compare manual skill-repair runs with frozen earlier developer runs."""

import argparse
import hashlib
import json
from pathlib import Path

from prepare_cross_project_cvss_20261031 import PROJECTS
from score_cross_project_cvss_20261031 import evaluate, metadata_audit


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--react-report", type=Path, required=True)
    parser.add_argument("--node-report", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((args.root / "repair_v1/manifest.json").read_text(encoding="utf-8"))
    if sha(args.root / "repair_v1/experience_verified_v1.md") != manifest["repaired_skill_sha256"]:
        raise ValueError("repaired skill differs from its frozen manifest")
    previous = json.loads(args.previous.read_text(encoding="utf-8"))
    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    result = {"status": "POSTHOC_MANUAL_REPAIR_DEVELOPMENT", "projects": {}}
    for project in ("react", "node"):
        report_path = getattr(args, project + "_report")
        if sha(report_path) != PROJECTS[project]["report"]:
            raise ValueError("frozen scanner report changed")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        folders = [p for p in (args.root / project / "agent_runs").iterdir() if p.is_dir()]
        if len(folders) != 1:
            raise ValueError("expected one repair run per project")
        folder = folders[0]
        config = json.loads((folder / "intervention.json").read_text(encoding="utf-8"))
        if config["condition"] != "target_generated_skill" or config["skill_sha256"] != manifest["repaired_skill_sha256"]:
            raise ValueError("wrong condition or repaired skill")
        receipt = json.loads((folder / "receipt.json").read_text(encoding="utf-8"))
        if receipt["raw_sha256"] != sha(folder / "raw.jsonl"):
            raise ValueError("raw output differs from receipt")
        work = folder / "work"
        calls = receipt["model_http_requests"]
        tokens = receipt.get("step_finish_tokens", [])
        repaired = {"case_name": folder.name, "agent_exit": receipt["agent_exit"],
                    "format_verifier_exit": receipt["verifier_exit"],
                    "lock_unchanged": sha(work / "package-lock.json") == PROJECTS[project]["lock"],
                    "snapshot_scoring": evaluate(work / "security_audit.csv", report),
                    "metadata_audit": metadata_audit(work, metadata),
                    "forwarded_post": sum(c.startswith("POST ") for c in calls),
                    "denied": [c for c in calls if c.startswith("DENIED")],
                    "elapsed_seconds": receipt["elapsed_seconds"],
                    "reported_total_tokens": sum(int(t.get("total") or 0) for t in tokens),
                    "reported_cache_read": sum(int((t.get("cache") or {}).get("read") or 0) for t in tokens),
                    "raw_sha256": receipt["raw_sha256"]}
        result["projects"][project] = {
            "original_skill": previous["projects"][project]["cases"]["target_generated_skill"],
            "manual_repair": repaired,
            "baseline": previous["projects"][project]["baseline"]}
        if "target_history" in previous["projects"][project]["cases"]:
            result["projects"][project]["ordinary_history"] = previous["projects"][project]["cases"]["target_history"]
    runs = [item["manual_repair"] for item in result["projects"].values()]
    result["totals"] = {"forwarded_post": sum(r["forwarded_post"] for r in runs),
                        "denied": sum(len(r["denied"]) for r in runs),
                        "reported_total_tokens": sum(r["reported_total_tokens"] for r in runs),
                        "reported_cache_read": sum(r["reported_cache_read"] for r in runs)}
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"]))


if __name__ == "__main__":
    main()
