#!/usr/bin/env python3
"""Visible-input-only, no-model baseline for the controlled 13F task."""
import argparse
import csv
import io
import json
from pathlib import Path
import re
import time
from zipfile import ZipFile


def policy_from_task(text):
    labels = re.search(r"allowed TITLEOFCLASS values are (\[[^\n]*\])\.", text)
    manager = re.search(r"FILINGMANAGER_NAME equals `([^`]+)` ignoring case", text)
    period = re.search(r"PERIODOFREPORT is `([^`]+)`", text)
    if not labels or not manager or not period:
        raise ValueError("task does not contain the explicit machine-readable contract")
    classes = json.loads(labels.group(1))
    if not isinstance(classes, list) or not classes or any(not isinstance(v, str) for v in classes):
        raise ValueError("invalid class list")
    return classes, manager.group(1), period.group(1)


def rows(archive, basename):
    paths = [path for path in archive.namelist() if path == basename or path.endswith("/" + basename)]
    if len(paths) != 1:
        raise ValueError("table member is not unique: " + basename)
    with archive.open(paths[0]) as source:
        with io.TextIOWrapper(source, encoding="utf-8-sig", errors="strict", newline="") as text:
            yield from csv.DictReader(text, delimiter="\t")


def count_archive(path, classes, manager, target_period):
    with ZipFile(path) as archive:
        periods = {row["ACCESSION_NUMBER"]: row["PERIODOFREPORT"] for row in rows(archive, "SUBMISSION.tsv")}
        candidates = [row["ACCESSION_NUMBER"] for row in rows(archive, "COVERPAGE.tsv")
                      if row["FILINGMANAGER_NAME"].casefold() == manager.casefold()
                      and periods.get(row["ACCESSION_NUMBER"]) == target_period]
        if len(candidates) != 1:
            raise ValueError("manager and period do not identify one filing")
        allowed = set(classes)
        return sum(1 for row in rows(archive, "INFOTABLE.tsv")
                   if row["ACCESSION_NUMBER"] == candidates[0] and row["TITLEOFCLASS"].lower() in allowed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archive", type=Path)
    ap.add_argument("task", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("diagnostic", type=Path)
    args = ap.parse_args()
    started = time.monotonic()
    labels, manager, period = policy_from_task(args.task.read_text(encoding="utf-8"))
    count = count_archive(args.archive, labels, manager, period)
    args.output.write_text(json.dumps({"count": count}) + "\n", encoding="utf-8")
    summary = {"status": "VISIBLE_INPUT_DETERMINISTIC_BASELINE", "count": count,
               "elapsed_seconds": round(time.monotonic() - started, 3), "model_calls": 0}
    args.diagnostic.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
