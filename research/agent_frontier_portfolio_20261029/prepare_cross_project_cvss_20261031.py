#!/usr/bin/env python3
"""Freeze visible target tasks without mounting reference reports to the Agent."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


PROJECTS = {
    "react": {
        "lock": "28bca44deafc6c8857880abb6884a6adcf96041dcc2a2d6efe0ad4a20c9f72b0",
        "report": "96df76a3e02bb5ec721a842384bc6e9e131fef5a591121befbc6f11c025b05f7",
        "license": "1fb3d499dec33f0e777f81fd9f8806fc1066e4553dc904665bbd3f9ee5b67572",
    },
    "node": {
        "lock": "89c48d839f9881836f45fac42fae824e4163c75ccb542ee3baee0831a494602b",
        "report": "891fc275e9e8b0c2b71970aa07900b522c36c5b2763779833c003b85586654f7",
        "license": "fcfb904481fbbd1e0c86f0865324102b63e10552187c90471c92c074d930fc32",
    },
}

TASK = """---
schema_version: '1.0'
---
Audit the dependencies in `/root/package-lock.json` with the offline `trivy`
executable. The frozen database is at `/root/trivy-cache`. It is an old
snapshot; report results relative to this snapshot and do not access the
network or update the database. Do not alter database or metadata timestamps,
including copies. Use a scanner invocation that preserves the snapshot.

For each vulnerability, select the first numeric CVSS V3 score in the closed
range 0 to 10 using this source order: `nvd`, then `ghsa`, then `redhat`.
If none is available, omit the vulnerability. Include a record only when the
selected score is strictly greater than 8.0. Do not combine different CVEs for
the same package and version. Use the scanner's severity for each record.

Write `/root/security_audit.csv` with exactly these columns and this order:
`Package,Version,CVE_ID,Severity,CVSS_Score,Fixed_Version,Title,Url`.
Include the header even if no record matches. Use the available scanner values
for the remaining fields, and N/A where a field is unavailable. Avoid printing
entire large input files or scanner reports into the conversation.
"""

VERIFIER = '''import csv
from pathlib import Path

FIELDS = ["Package", "Version", "CVE_ID", "Severity", "CVSS_Score",
          "Fixed_Version", "Title", "Url"]

def test_output_exists():
    assert Path("/root/security_audit.csv").is_file()

def test_header():
    with Path("/root/security_audit.csv").open(encoding="utf-8-sig", newline="") as stream:
        assert csv.DictReader(stream).fieldnames == FIELDS
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project", choices=PROJECTS)
    parser.add_argument("--previous-pilot", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--license", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for name in ("lock", "report", "license"):
        if sha(getattr(args, name)) != PROJECTS[args.project][name]:
            raise ValueError("source differs from frozen project: " + name)
    old = json.loads((args.previous_pilot / "manifest.json").read_text(encoding="utf-8"))
    old_tasks = args.previous_pilot / "tasks"
    skills_rel = Path("dependency-scope-target/environment/skills")
    for path in (old_tasks / skills_rel).rglob("*"):
        if path.is_file():
            rel = path.relative_to(old_tasks).as_posix()
            if old["tasks"].get(rel) != sha(path):
                raise ValueError("native skill changed: " + rel)
    args.output.mkdir(parents=True, exist_ok=False)
    target = args.output / "tasks/dependency-scope-target"
    (target / "verifier").mkdir(parents=True)
    (target / "task.md").write_text(TASK, encoding="utf-8")
    (target / "verifier/test_outputs.py").write_text(VERIFIER, encoding="utf-8")
    shutil.copytree(old_tasks / skills_rel, args.output / "tasks" / skills_rel)
    assets = dict(old["assets_sha256"])
    assets["lock"] = PROJECTS[args.project]["lock"]
    assets["scan"] = PROJECTS[args.project]["report"]
    manifest = {"status": "POSTHOC_PROJECT_SELECTION_DEVELOPMENT", "project": args.project,
                "assets_sha256": assets, "source_license_sha256": PROJECTS[args.project]["license"],
                "tasks": {}}
    for path in sorted((args.output / "tasks").rglob("*")):
        if path.is_file():
            manifest["tasks"][path.relative_to(args.output / "tasks").as_posix()] = sha(path)
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"project": args.project, "frozen_files": len(manifest["tasks"]),
                      "manifest_sha256": sha(args.output / "manifest.json")}))


if __name__ == "__main__":
    main()
