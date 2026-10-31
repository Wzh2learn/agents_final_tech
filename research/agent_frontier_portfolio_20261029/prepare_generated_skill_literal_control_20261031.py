#!/usr/bin/env python3
"""Prepare, without executing, one generated code block and scanner control."""

import argparse
import hashlib
import json
import re
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", type=Path, required=True)
    parser.add_argument("--scanner-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    blocks = re.findall(r"```python\s*\n(.*?)```", args.skill.read_text(encoding="utf-8"), flags=re.S)
    if len(blocks) != 1:
        raise ValueError("expected exactly one Python sample")
    report = json.loads(args.scanner_report.read_text(encoding="utf-8"))
    for section in report.get("Results", []):
        if "Vulnerabilities" in section:
            section["Vulnerabilities"] = [x for x in section["Vulnerabilities"]
                                           if x.get("Severity") in ("HIGH", "CRITICAL")]
    args.output.mkdir(parents=True, exist_ok=False)
    code = args.output / "generated_code.py"
    data = args.output / "source_high_report.json"
    code.write_text(blocks[0], encoding="utf-8")
    data.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    manifest = {"status": "POSTHOC_LITERAL_CODE_CONTROL_NOT_AGENT_OUTPUT",
                "skill_sha256": sha(args.skill), "original_report_sha256": sha(args.scanner_report),
                "code_sha256": sha(code), "filtered_report_sha256": sha(data),
                "filter": "Severity in HIGH or CRITICAL, as in generated skill"}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
