#!/usr/bin/env python3
"""Filter a saved real scanner report without model calls or hidden answers."""

import argparse
import csv
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    fields = ["Package", "Version", "CVE_ID", "Severity", "CVSS_Score", "Fixed_Version", "Title", "Url"]
    count = 0
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for result in report.get("Results", []):
            for item in result.get("Vulnerabilities", []):
                score = None
                for provider in ("nvd", "ghsa", "redhat"):
                    candidate = (item.get("CVSS", {}).get(provider, {}) or {}).get("V3Score")
                    if isinstance(candidate, (int, float)) and not isinstance(candidate, bool) and 0 <= candidate <= 10:
                        score = candidate
                        break
                if score is None or score <= 8:
                    continue
                writer.writerow({"Package": item["PkgName"], "Version": item["InstalledVersion"],
                                 "CVE_ID": item["VulnerabilityID"], "Severity": item["Severity"],
                                 "CVSS_Score": score, "Fixed_Version": item.get("FixedVersion") or "N/A",
                                 "Title": item.get("Title") or "N/A", "Url": item.get("PrimaryURL") or "N/A"})
                count += 1
    print(json.dumps({"records": count, "model_calls": 0, "input": "saved scanner report"}))


if __name__ == "__main__":
    main()
