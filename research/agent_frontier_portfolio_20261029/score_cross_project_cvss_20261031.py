#!/usr/bin/env python3
"""Score visible CVSS rules against a fixed Trivy snapshot, not real-world truth."""

import argparse
import collections
import csv
import hashlib
import json
import math
from pathlib import Path


SOURCES = ("nvd", "ghsa", "redhat")
FIELDS = ("Package", "Version", "CVE_ID", "Severity", "CVSS_Score",
          "Fixed_Version", "Title", "Url")
IDENTITY = FIELDS[:4]


def selected_score(record):
    for source in SOURCES:
        value = ((record.get("CVSS") or {}).get(source) or {}).get("V3Score")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if math.isfinite(value) and 0 <= value <= 10:
                return source, float(value)
    return None


def reference(report):
    result = {}
    for section in report.get("Results", []):
        for record in section.get("Vulnerabilities", []):
            selected = selected_score(record)
            if selected is None or selected[1] <= 8:
                continue
            identity = tuple(record[k] for k in ("PkgName", "InstalledVersion",
                                                  "VulnerabilityID", "Severity"))
            if identity in result:
                raise ValueError("duplicate reference identity requires adjudication")
            result[identity] = selected
    return result


def evaluate(output, report):
    expected = reference(report)
    verdict = {"status": "MISSING_OUTPUT", "expected_records": len(expected),
               "identity_exact": False, "identity_and_score_exact": False}
    if not output.is_file():
        return verdict
    try:
        with output.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != list(FIELDS):
                raise ValueError("header differs from requested columns")
            rows = list(reader)
        if any(None in row for row in rows):
            raise ValueError("malformed CSV row")
        identities = [tuple((row.get(k) or "").strip() for k in IDENTITY) for row in rows]
        observed = collections.Counter(identities)
        wanted = collections.Counter(expected.keys())
        missing = list((wanted - observed).elements())
        extra = list((observed - wanted).elements())
        score_errors = []
        for key, row in zip(identities, rows):
            try:
                number = float(row.get("CVSS_Score", ""))
            except (ValueError, TypeError):
                number = float("nan")
            if key in expected and (not math.isfinite(number) or
                                    not math.isclose(number, expected[key][1], abs_tol=1e-9)):
                score_errors.append(list(key))
        verdict.update({"status": "SCORED", "observed_records": len(rows),
                        "missing": [list(x) for x in missing],
                        "extra_or_duplicate": [list(x) for x in extra],
                        "wrong_scores": score_errors,
                        "identity_exact": not missing and not extra,
                        "identity_and_score_exact": not missing and not extra and not score_errors})
    except (ValueError, OSError, csv.Error, UnicodeError) as exc:
        verdict.update({"status": "INVALID_OUTPUT", "error_type": type(exc).__name__})
    return verdict


def metadata_audit(work, original):
    items = []
    for path in sorted(work.rglob("metadata.json")):
        relative = path.relative_to(work).as_posix()
        likely_database_metadata = path.parent.name == "db"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeError):
            if likely_database_metadata:
                items.append({"path": relative, "unchanged": None, "status": "UNREADABLE"})
            continue
        if isinstance(data, dict) and {"Version", "UpdatedAt", "DownloadedAt"} <= set(data):
            items.append({"path": relative, "unchanged": data == original, "status": "SCORED",
                          "updated_at": data.get("UpdatedAt"),
                          "downloaded_at": data.get("DownloadedAt"),
                          "next_update": data.get("NextUpdate")})
        elif likely_database_metadata:
            items.append({"path": relative, "unchanged": None, "status": "UNEXPECTED_STRUCTURE"})
    return {"observed_copies": items,
            "original_location_present": (work / "trivy-cache/db/metadata.json").is_file(),
            "changed_copies": sum(item["unchanged"] is False for item in items),
            "unresolved_copies": sum(item["unchanged"] is None for item in items),
            "limitation": "Deleted copies and which metadata the scanner used are not established."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report_bytes = args.report.read_bytes()
    report = json.loads(report_bytes)
    original = json.loads(args.metadata.read_text(encoding="utf-8"))
    result = {"report_sha256": hashlib.sha256(report_bytes).hexdigest(),
              "snapshot_scoring": evaluate(args.work / "security_audit.csv", report),
              "metadata_audit": metadata_audit(args.work, original),
              "limitation": "Snapshot-relative; URL, title, fixed-version truth and real-world security not assessed."}
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
