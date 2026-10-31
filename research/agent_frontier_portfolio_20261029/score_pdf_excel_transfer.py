#!/usr/bin/env python3
"""Aggregate a saved agent report against a separately mounted reference."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

try:
    from .qualify_pdf_excel_reference import values_equal
except ImportError:  # Running the checked-in script directly on GB10.
    from qualify_pdf_excel_reference import values_equal


ID = re.compile(r"^EMP\d{5}$")
NUMERIC = {"Salary", "Years", "Score"}


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def score(report, expected):
    if not isinstance(report, dict) or not isinstance(report.get("deleted_employees"), list) or not isinstance(report.get("modified_employees"), list):
        return {"status": "INVALID_STRUCTURE"}
    raw_deleted = report["deleted_employees"]
    raw_changed = report["modified_employees"]
    deleted = [x for x in raw_deleted if isinstance(x, str) and ID.fullmatch(x)]
    changed = [row for row in raw_changed if isinstance(row, dict)
               and isinstance(row.get("id"), str) and ID.fullmatch(row["id"])
               and isinstance(row.get("field"), str)
               and "old_value" in row and "new_value" in row]
    invalid_deleted = len(raw_deleted) - len(deleted)
    invalid_changed = len(raw_changed) - len(changed)
    dcounts = Counter(deleted)
    keys = [(row["id"], row["field"]) for row in changed]
    ccounts = Counter(keys)
    reference = {(r["id"], r["field"]): r for r in expected["modified_employees"]}
    deleted_reference = set(expected["deleted_employees"])
    type_errors = 0
    value_matches = set()
    for row in changed:
        key = (row["id"], row["field"])
        values = (row["old_value"], row["new_value"])
        valid_type = all(is_number(v) for v in values) if row["field"] in NUMERIC else all(isinstance(v, str) for v in values)
        if not valid_type:
            type_errors += 1
        target = reference.get(key)
        if target is not None and valid_type and all(values_equal(v, target[k]) for v, k in zip(values, ("old_value", "new_value"))):
            value_matches.add(key)
    detected_deleted = set(deleted)
    detected_keys = set(keys)
    extra_duplicates = sum(n - 1 for n in dcounts.values()) + sum(n - 1 for n in ccounts.values())
    result = {
        "status": "SCORED_WITH_INVALID_ENTRIES" if invalid_deleted or invalid_changed else "SCORED",
        "deleted_expected": len(deleted_reference),
        "deleted_returned": len(raw_deleted), "invalid_deleted_entries": invalid_deleted,
        "deleted_true_positive": len(detected_deleted & deleted_reference),
        "deleted_false_positive_unique": len(detected_deleted - deleted_reference),
        "deleted_false_negative": len(deleted_reference - detected_deleted),
        "change_expected": len(reference), "change_returned": len(raw_changed),
        "change_expected_unique_ids": len({key[0] for key in reference}),
        "change_reported_unique_ids": len({key[0] for key in keys}),
        "invalid_modified_entries": invalid_changed,
        "change_key_true_positive": len(detected_keys & reference.keys()),
        "change_key_false_positive_unique": len(detected_keys - reference.keys()),
        "change_key_false_negative": len(reference.keys() - detected_keys),
        "change_values_and_types_correct": len(value_matches),
        "invalid_value_types": type_errors, "duplicate_entries": extra_duplicates,
        "deleted_sorted": not invalid_deleted and deleted == sorted(deleted),
        "changes_sorted_by_id": not invalid_changed and [row["id"] for row in changed] == sorted(row["id"] for row in changed),
    }
    result["full_contract_pass"] = (result["deleted_true_positive"] == len(deleted_reference)
        and not result["deleted_false_positive_unique"] and not result["deleted_false_negative"]
        and result["change_key_true_positive"] == len(reference)
        and not result["change_key_false_positive_unique"] and not result["change_key_false_negative"]
        and result["change_values_and_types_correct"] == len(reference)
        and not type_errors and not extra_duplicates and not invalid_deleted and not invalid_changed
        and result["deleted_sorted"] and result["changes_sorted_by_id"])
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report", type=Path)
    ap.add_argument("expected", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    if not args.report.exists():
        result = {"status": "NO_OUTPUT"}
    else:
        try:
            report = json.loads(args.report.read_text(encoding="utf-8"))
            result = score(report, json.loads(args.expected.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, UnicodeDecodeError):
            result = {"status": "INVALID_JSON"}
        result["report_sha256"] = hashlib.sha256(args.report.read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
