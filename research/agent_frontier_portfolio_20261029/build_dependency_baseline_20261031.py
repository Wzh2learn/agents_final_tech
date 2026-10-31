#!/usr/bin/env python3
"""Format a public Trivy report under a visible task's selection predicate.

The scanner report must come from the same input and frozen database available
to the Agent. This baseline does not read any benchmark verifier reference.
"""

import argparse
import csv
import json
from pathlib import Path

from score_dependency_scope_20261031 import HEADERS, scores


def make_rows(report, scope):
    result = []
    for section in report.get("Results", []):
        for item in section.get("Vulnerabilities", []):
            all_scores = scores(item)
            if scope == "high" and item.get("Severity") not in ("HIGH", "CRITICAL"):
                continue
            if scope == "cvss_gt_8" and not any(s > 8 for s in all_scores):
                continue
            cvss = item.get("CVSS") or {}
            ordered_sources = ["nvd", "ghsa", "redhat"] + sorted(set(cvss) - {"nvd", "ghsa", "redhat"})
            value = next((cvss[src]["V3Score"] for src in ordered_sources
                          if src in cvss and "V3Score" in cvss[src]
                          and (scope != "cvss_gt_8" or cvss[src]["V3Score"] > 8)), "N/A")
            result.append({"Package": item.get("PkgName", ""),
                "Version": item.get("InstalledVersion", ""), "CVE_ID": item.get("VulnerabilityID", ""),
                "Severity": item.get("Severity", ""), "CVSS_Score": value,
                "Fixed_Version": item.get("FixedVersion") or "N/A", "Title": item.get("Title", ""),
                "Url": item.get("PrimaryURL", "")})
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scanner-report", type=Path, required=True)
    parser.add_argument("--scope", choices=("high", "cvss_gt_8"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.scanner_report.read_text(encoding="utf-8"))
    rows = make_rows(report, args.scope)
    with args.output.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=HEADERS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"scope": args.scope, "rows": len(rows)}))


if __name__ == "__main__":
    main()
