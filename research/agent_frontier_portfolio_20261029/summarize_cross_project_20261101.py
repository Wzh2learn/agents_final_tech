#!/usr/bin/env python3
"""Recompute the six frozen cross-project runs from raw, receipts and snapshots."""

import argparse
import hashlib
import json
from pathlib import Path

from prepare_cross_project_cvss_20261031 import PROJECTS
from score_cross_project_cvss_20261031 import evaluate, metadata_audit


EXPECTED = {"react": {"target_none", "target_history", "target_generated_skill", "target_native_skills"},
            "node": {"target_none", "target_generated_skill"}}
HISTORY = "002832098228f5e982c726b58ec0142bc2bb08a29e8f69d9625c99bfd8a613e9"
SKILL = "92f13d4cb7abbf334d4a837049222bea28638fd8d815a2f70fd590877d9900b9"


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--react-report", type=Path, required=True)
    parser.add_argument("--node-report", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    result = {"status": "POSTHOC_CROSS_PROJECT_DEVELOPMENT", "projects": {}}
    for project, required in EXPECTED.items():
        report_path = getattr(args, project + "_report")
        if sha(report_path) != PROJECTS[project]["report"]:
            raise ValueError("frozen report changed")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        root = args.root / project
        manifest_path = root / "frozen/manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["project"] != project or manifest["assets_sha256"]["lock"] != PROJECTS[project]["lock"]:
            raise ValueError("wrong project manifest")
        for name, value in manifest["tasks"].items():
            if sha(root / "frozen/tasks" / name) != value:
                raise ValueError("frozen task or skill differs")
        cases = {}
        for folder in (root / "agent_runs").iterdir():
            if not folder.is_dir():
                continue
            config = json.loads((folder / "intervention.json").read_text(encoding="utf-8"))
            condition = config["condition"]
            if condition not in required or condition in cases:
                raise ValueError("unexpected or duplicate condition")
            if config["status"] != "CROSS_PROJECT_DEVELOPMENT" or config["max_forwarded_http"] != 32:
                raise ValueError("unexpected execution contract")
            if config.get("history_sha256") != (HISTORY if condition == "target_history" else None):
                raise ValueError("history changed")
            if config.get("skill_sha256") != (SKILL if condition == "target_generated_skill" else None):
                raise ValueError("generated skill changed")
            receipt = json.loads((folder / "receipt.json").read_text(encoding="utf-8"))
            if sha(folder / "raw.jsonl") != receipt["raw_sha256"]:
                raise ValueError("raw hash mismatch")
            work = folder / "work"
            calls = receipt["model_http_requests"]
            tokens = receipt.get("step_finish_tokens", [])
            cases[condition] = {"case_name": folder.name, "agent_exit": receipt["agent_exit"],
                                "format_verifier_exit": receipt["verifier_exit"],
                                "lock_unchanged": sha(work / "package-lock.json") == PROJECTS[project]["lock"],
                                "snapshot_scoring": evaluate(work / "security_audit.csv", report),
                                "metadata_audit": metadata_audit(work, metadata),
                                "forwarded_post": sum(x.startswith("POST ") for x in calls),
                                "denied": [x for x in calls if x.startswith("DENIED")],
                                "elapsed_seconds": receipt["elapsed_seconds"],
                                "reported_total_tokens": sum(int(t.get("total") or 0) for t in tokens),
                                "reported_cache_read": sum(int((t.get("cache") or {}).get("read") or 0) for t in tokens),
                                "raw_sha256": receipt["raw_sha256"]}
        if set(cases) != required:
            raise ValueError("missing project conditions")
        baseline = evaluate(root / "baseline/security_audit.csv", report)
        result["projects"][project] = {"manifest_sha256": sha(manifest_path),
                                       "snapshot_report_sha256": sha(report_path),
                                       "baseline": baseline, "cases": cases}
    cases = [v for project in result["projects"].values() for v in project["cases"].values()]
    result["totals"] = {"forwarded_post": sum(v["forwarded_post"] for v in cases),
                        "denied": sum(len(v["denied"]) for v in cases),
                        "reported_total_tokens": sum(v["reported_total_tokens"] for v in cases),
                        "reported_cache_read": sum(v["reported_cache_read"] for v in cases)}
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"]))


if __name__ == "__main__":
    main()
