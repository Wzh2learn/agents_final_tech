#!/usr/bin/env python3
"""Check per-vulnerability identities against a frozen scanner output.

This is a snapshot-relative identity/scope check, not independent assessment
of vulnerability validity or the correctness of every descriptive field.
"""

import argparse
import collections
import csv
import json
import math
from pathlib import Path


HEADERS = ["Package", "Version", "CVE_ID", "Severity", "CVSS_Score",
           "Fixed_Version", "Title", "Url"]


def scores(record):
    return [value["V3Score"] for value in (record.get("CVSS") or {}).values()
            if isinstance(value, dict) and isinstance(value.get("V3Score"), (int, float))
            and not isinstance(value.get("V3Score"), bool)]


def expected_rows(report, scope):
    rows = [record for result in report.get("Results", [])
            for record in result.get("Vulnerabilities", [])]
    if scope == "high":
        rows = [x for x in rows if x.get("Severity") in ("HIGH", "CRITICAL")]
    elif scope == "cvss_gt_8":
        rows = [x for x in rows if any(score > 8 for score in scores(x))]
    else:
        raise ValueError("unsupported scope")
    return collections.Counter((x["PkgName"], x["InstalledVersion"],
                                x["VulnerabilityID"], x["Severity"]) for x in rows)


def evaluate(csv_path, report, scope):
    expected = expected_rows(report, scope)
    result = {"scope": scope, "expected_records": sum(expected.values()),
              "status": "MISSING_OUTPUT", "exact_identity_and_scope": False}
    if not csv_path.is_file():
        return result
    try:
        with csv_path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            headers = reader.fieldnames
            rows = list(reader)
        if not headers or not set(HEADERS).issubset(headers) or any(None in row for row in rows):
            raise ValueError("required headers absent or malformed CSV")
        observed = collections.Counter(tuple((row.get(k) or "").strip() for k in
            ("Package", "Version", "CVE_ID", "Severity")) for row in rows)
        bad_score = 0
        if scope == "cvss_gt_8":
            for row in rows:
                try:
                    value = float(row.get("CVSS_Score", ""))
                except (TypeError, ValueError):
                    bad_score += 1
                    continue
                if not math.isfinite(value) or not 8 < value <= 10:
                    bad_score += 1
        missing = list((expected - observed).elements())
        extra = list((observed - expected).elements())
        result.update({"status": "SCORED", "observed_records": len(rows),
                       "missing": [list(x) for x in missing],
                       "extra_or_duplicate": [list(x) for x in extra],
                       "invalid_threshold_rows": bad_score,
                       "exact_identity_and_scope": not missing and not extra and bad_score == 0})
        return result
    except (ValueError, OSError, csv.Error, UnicodeError) as exc:
        result.update({"status": "INVALID_OUTPUT", "error_type": type(exc).__name__})
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--scanner-report", type=Path, required=True)
    parser.add_argument("--scope", choices=("high", "cvss_gt_8"), required=True)
    args = parser.parse_args()
    report = json.loads(args.scanner_report.read_text(encoding="utf-8"))
    print(json.dumps(evaluate(args.output_csv, report, args.scope), indent=2))


if __name__ == "__main__":
    main()
