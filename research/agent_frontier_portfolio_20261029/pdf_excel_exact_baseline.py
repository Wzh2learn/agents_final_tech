#!/usr/bin/env python3
"""Post-hoc deterministic exact-ID and anchored-field baseline for development.

Uses only the PDF and current workbook visible to the agent. It never opens the
old workbook or benchmark reference; ambiguous old-field reconstructions are
reported as unresolved rather than guessed.
"""
import argparse
import json
from pathlib import Path
import re
import time


FIELDS = ("ID", "First", "Last", "Dept", "Position", "Salary", "Years", "Location", "Score")
ID = re.compile(r"^EMP\d{5}$")


def clean(text):
    return " ".join(str(text).split())


def fmt(field, value):
    if field == "Salary":
        return f"{int(value):,}"
    if field == "Years":
        return str(int(value))
    if field == "Score":
        return f"{float(value):g}"
    return clean(value)


def as_value(field, value):
    if field in ("Salary", "Years"):
        return int(value.replace(",", ""))
    if field == "Score":
        return float(value)
    return value


def candidate_changes(old_line, current):
    """Try replacing one field while requiring the remaining fields to match."""
    formatted = [fmt(field, value) for field, value in zip(FIELDS, current)]
    old = clean(old_line)
    if old == " ".join(formatted):
        return []
    options = []
    for index in range(1, len(FIELDS)):
        prefix = " ".join(formatted[:index]) + " "
        suffix = " " + " ".join(formatted[index + 1:]) if index + 1 < len(FIELDS) else ""
        if not old.startswith(prefix) or (suffix and not old.endswith(suffix)):
            continue
        end = len(old) - len(suffix) if suffix else len(old)
        candidate = old[len(prefix):end].strip()
        if not candidate or candidate == formatted[index]:
            continue
        try:
            old_value = as_value(FIELDS[index], candidate)
        except ValueError:
            continue
        options.append({"id": formatted[0], "field": FIELDS[index],
                        "old_value": old_value, "new_value": current[index]})
    return options


def main():
    from openpyxl import load_workbook
    from pypdf import PdfReader

    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("current", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("diagnostic", type=Path)
    args = ap.parse_args()
    start = time.monotonic()
    old = {}
    for page in PdfReader(str(args.pdf)).pages:
        for line in (page.extract_text() or "").splitlines():
            normalized = clean(line)
            first = normalized.split(" ", 1)[0]
            if ID.fullmatch(first):
                if first in old:
                    raise ValueError("duplicate PDF identifier")
                old[first] = normalized
    rows = load_workbook(args.current, read_only=True, data_only=True).active.iter_rows(values_only=True)
    if tuple(next(rows)) != FIELDS:
        raise ValueError("unexpected workbook fields")
    current = {}
    for row in rows:
        if row[0] in current or not isinstance(row[0], str) or not ID.fullmatch(row[0]):
            raise ValueError("invalid or duplicate current identifier")
        current[row[0]] = row
    deleted = sorted(old.keys() - current.keys())
    changed = []
    unchanged = 0
    unresolved = 0
    for identifier in sorted(old.keys() & current.keys()):
        options = candidate_changes(old[identifier], current[identifier])
        if old[identifier] == " ".join(fmt(field, value) for field, value in zip(FIELDS, current[identifier])):
            unchanged += 1
        elif len(options) == 1:
            changed.append(options[0])
        else:
            unresolved += 1
    report = {"deleted_employees": deleted, "modified_employees": changed}
    diagnostic = {"status": "POST_HOC_DETERMINISTIC_DEVELOPMENT_BASELINE",
                  "pdf_records": len(old), "current_records": len(current),
                  "deleted": len(deleted), "unchanged_lines": unchanged,
                  "single_field_resolved": len(changed), "unresolved_lines": unresolved,
                  "elapsed_seconds": round(time.monotonic() - start, 3),
                  "limitations": "one-field anchored reconstruction; text line comparison is not semantic proof"}
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.diagnostic.write_text(json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(diagnostic))


if __name__ == "__main__":
    main()
