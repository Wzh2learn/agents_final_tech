#!/usr/bin/env python3
"""Inspect period and manager ambiguity in public-task 13F archives.

This is a source qualification, not financial advice, task scoring, or a
comparison to SEC's official archive bytes. Reads ZIP members without unpacking.
"""
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile


MANAGERS = ("renaissance technologies", "bridgewater associates", "berkshire hathaway", "soros fund management")


def rows(archive, basename):
    matches = [name for name in archive.namelist() if name == basename or name.endswith("/" + basename)]
    if len(matches) != 1:
        raise ValueError("expected one " + basename)
    with archive.open(matches[0]) as binary:
        with io.TextIOWrapper(binary, encoding="utf-8-sig", errors="strict", newline="") as text:
            return list(csv.DictReader(text, delimiter="\t"))


def summarize_rows(submissions, covers, target_period):
    accession_to_period = {}
    duplicate_accessions = 0
    for row in submissions:
        accession = row["ACCESSION_NUMBER"]
        if accession in accession_to_period:
            duplicate_accessions += 1
        accession_to_period[accession] = row["PERIODOFREPORT"]
    counts = Counter(row["PERIODOFREPORT"] for row in submissions)
    managers = {}
    for name in MANAGERS:
        matches = [row for row in covers if name in row["FILINGMANAGER_NAME"].casefold()]
        periods = Counter(accession_to_period.get(row["ACCESSION_NUMBER"], "UNJOINED") for row in matches)
        amendments = Counter((row.get("ISAMENDMENT") or "UNKNOWN").strip() for row in matches)
        name_periods = Counter((row["FILINGMANAGER_NAME"], accession_to_period.get(row["ACCESSION_NUMBER"], "UNJOINED")) for row in matches)
        managers[name] = {"substring_matches": len(matches),
                          "target_period_matches": periods.get(target_period, 0),
                          "period_counts": dict(sorted(periods.items())),
                          "amendment_field_counts": dict(sorted(amendments.items())),
                          "name_period_counts": [{"name": key[0], "period": key[1], "filings": value}
                                                 for key, value in sorted(name_periods.items())]}
    return {"submission_rows": len(submissions), "duplicate_submission_accessions": duplicate_accessions,
            "target_period": target_period, "target_period_rows": counts.get(target_period, 0),
            "other_or_missing_period_rows": len(submissions) - counts.get(target_period, 0),
            "period_counts": dict(sorted(counts.items())),
            "cover_rows_without_submission": sum(row["ACCESSION_NUMBER"] not in accession_to_period for row in covers),
            "manager_substring_checks": managers}


def sha_file(path):
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def inspect(path, period):
    with ZipFile(path) as archive:
        data = summarize_rows(rows(archive, "SUBMISSION.tsv"), rows(archive, "COVERPAGE.tsv"), period)
    data["archive_sha256_raw"] = sha_file(path)
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("q2", type=Path)
    ap.add_argument("q3", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    result = {"status": "SOURCE_QUALIFICATION_NOT_TASK_EVALUATION",
              "q2_archive": inspect(args.q2, "30-JUN-2025"),
              "q3_archive": inspect(args.q3, "30-SEP-2025"),
              "limitations": ["source archive bytes not independently matched to SEC",
                              "substring search is not the benchmark fuzzy matcher",
                              "amendment flags and multiple filings require semantic handling",
                              "13F reportable holdings do not establish total AUM"]}
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
