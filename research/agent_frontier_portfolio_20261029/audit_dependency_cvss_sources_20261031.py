#!/usr/bin/env python3
"""Post-hoc check: do reported CVSS values occur in frozen scanner sources?"""

import argparse
import csv
import json
import math
from pathlib import Path


def check(path, report):
    if not path.is_file():
        return {"status": "MISSING_OUTPUT"}
    records = {}
    for section in report.get("Results", []):
        for item in section.get("Vulnerabilities", []):
            key = (item.get("PkgName"), item.get("InstalledVersion"),
                   item.get("VulnerabilityID"), item.get("Severity"))
            if key in records:
                raise ValueError("duplicate scanner identity: independent adjudication needed")
            records[key] = item
    results = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            key = tuple((row.get(x) or "").strip() for x in ("Package", "Version", "CVE_ID", "Severity"))
            raw = (row.get("CVSS_Score") or "").strip()
            record = records.get(key)
            if record is None:
                results.append({"identity": list(key), "status": "IDENTITY_NOT_IN_SCANNER"})
                continue
            cvss = record.get("CVSS") or {}
            numeric = {source: data.get("V3Score") for source, data in cvss.items()
                       if isinstance(data, dict) and isinstance(data.get("V3Score"), (int, float))
                       and not isinstance(data.get("V3Score"), bool)}
            try:
                value = float(raw)
            except ValueError:
                status = "MISSING_WHEN_AVAILABLE" if numeric else "NO_NUMERIC_SOURCE"
                results.append({"identity": list(key), "reported": raw, "status": status})
                continue
            matching = sorted(source for source, score in numeric.items()
                              if math.isfinite(value) and math.isclose(value, score, abs_tol=1e-9))
            results.append({"identity": list(key), "reported": value if math.isfinite(value) else raw,
                            "status": "MATCHES_SNAPSHOT_SOURCE" if matching else "NO_MATCH",
                            "matching_sources": matching})
    return {"status": "SCORED", "rows": results,
            "limitation": "Matching a source value does not prove which source the Agent used."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--scanner-report", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.output_csv, json.loads(args.scanner_report.read_text(encoding="utf-8"))), indent=2))


if __name__ == "__main__":
    main()
