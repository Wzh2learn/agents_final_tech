#!/usr/bin/env python3
"""Compare a public synthetic spreadsheet task's reference with its source files.

The original spreadsheet and benchmark expected answer are evaluation-only;
never mount either in an agent container. Output contains aggregate counts and
file hashes, not employee records. This is a development qualification, not an
independent real-world or human-labelled gold standard.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table_map(headers, rows):
    if not headers or headers[0] != "ID" or len(headers) != len(set(headers)):
        raise ValueError("unexpected or repeated spreadsheet headers")
    result = {}
    for values in rows:
        if len(values) != len(headers) or not isinstance(values[0], str):
            raise ValueError("invalid row or ID")
        if values[0] in result:
            raise ValueError("duplicate ID")
        result[values[0]] = dict(zip(headers[1:], values[1:]))
    return result


def values_equal(left, right):
    if isinstance(left, (int, float)) and not isinstance(left, bool) and isinstance(right, (int, float)) and not isinstance(right, bool):
        return abs(left - right) < 0.01
    return left == right


def compare_tables(original, current):
    deleted = set(original) - set(current)
    added = set(current) - set(original)
    changes = {}
    for identifier in original.keys() & current.keys():
        old, new = original[identifier], current[identifier]
        if old.keys() != new.keys():
            raise ValueError("spreadsheet field mismatch")
        for field in old:
            if not values_equal(old[field], new[field]):
                changes[(identifier, field)] = (old[field], new[field])
    return deleted, added, changes


def compare_reference(deleted, changes, expected):
    reported_deleted = expected["deleted_employees"]
    modifications = expected["modified_employees"]
    expected_changes = {}
    for row in modifications:
        key = (row["id"], row["field"])
        if key in expected_changes:
            raise ValueError("duplicate expected change")
        expected_changes[key] = (row["old_value"], row["new_value"])
    shared = changes.keys() & expected_changes.keys()
    return {
        "expected_deleted_total": len(reported_deleted),
        "duplicate_expected_deleted": len(reported_deleted) - len(set(reported_deleted)),
        "deleted_missing_in_reference": len(deleted - set(reported_deleted)),
        "deleted_extra_in_reference": len(set(reported_deleted) - deleted),
        "expected_changes_total": len(expected_changes),
        "change_keys_missing_in_reference": len(changes.keys() - expected_changes.keys()),
        "change_keys_extra_in_reference": len(expected_changes.keys() - changes.keys()),
        "change_value_mismatches": sum(not (values_equal(changes[key][0], expected_changes[key][0]) and values_equal(changes[key][1], expected_changes[key][1])) for key in shared),
    }


def read_workbook(path):
    import openpyxl
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = book.active
    values = sheet.iter_rows(values_only=True)
    headers = next(values)
    return headers, table_map(headers, values)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("original", type=Path)
    parser.add_argument("current", type=Path)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("expected", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    old_headers, old = read_workbook(args.original)
    new_headers, new = read_workbook(args.current)
    if old_headers != new_headers:
        raise ValueError("spreadsheet headers differ")
    deleted, added, changes = compare_tables(old, new)
    expected = json.loads(args.expected.read_text(encoding="utf-8"))
    result = compare_reference(deleted, changes, expected)
    pdf = subprocess.run(["pdftotext", "-layout", str(args.pdf), "-"], check=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pdf_ids = re.findall(r"\bEMP\d{5}\b", pdf.stdout.decode("utf-8", errors="replace"))
    result.update({"original_records": len(old), "current_records": len(new),
                   "computed_deleted": len(deleted), "computed_added": len(added),
                   "computed_field_changes": len(changes),
                   "pdf_id_occurrences": len(pdf_ids), "pdf_unique_ids": len(set(pdf_ids)),
                   "pdf_original_missing_ids": len(set(old) - set(pdf_ids)),
                   "pdf_extra_ids": len(set(pdf_ids) - set(old)),
                   "input_sha256_raw": {name: digest(path) for name, path in (("original_xlsx", args.original), ("current_xlsx", args.current), ("backup_pdf", args.pdf), ("benchmark_expected", args.expected))},
                   "limitations": ["synthetic source, not independently human-labelled", "same-source spreadsheet reference, not independently collected data", "PDF check compares identifiers only, not all field values", "model pretraining exposure unknown"]})
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
