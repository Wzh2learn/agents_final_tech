#!/usr/bin/env python3
"""Check a DBSCAN output against the released reference after an episode ends.

Extra parameter keys are unresolved: the reference frontier is not an
independent recomputation of every additional claim made by an Agent.
"""

import argparse
import csv
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path

from run_dbscan_reference_20261101 import EXPECTED, sha


FIELDS = ("F1", "delta", "min_samples", "epsilon", "shape_weight")


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or any(reader.fieldnames.count(field) != 1 for field in FIELDS):
            raise ValueError("required fields are missing or duplicated")
        rows = []
        for row in reader:
            try:
                values = tuple(Decimal(row[field]) for field in FIELDS)
            except (KeyError, TypeError, InvalidOperation):
                raise ValueError("non-numeric or missing value") from None
            if not all(value.is_finite() for value in values):
                raise ValueError("non-finite value")
            rows.append(values)
        return rows


def key(row):
    return row[2], row[3], row[4]


def valid(row):
    f1, delta, minimum, epsilon, weight = row
    return (Decimal("0.5") < f1 <= 1 and delta > 0 and minimum == int(minimum)
            and 3 <= minimum <= 9 and epsilon == int(epsilon) and 4 <= epsilon <= 24
            and int(epsilon) % 2 == 0 and Decimal("0.9") <= weight <= Decimal("1.9")
            and weight * 10 == int(weight * 10))


def objectives_match(a, b):
    return abs(a[0] - b[0]) <= Decimal("0.0001") and abs(a[1] - b[1]) <= Decimal("0.001")


def analyze(output, reference):
    ref_rows = read_rows(reference)
    refs = {key(row): row for row in ref_rows}
    if len(refs) != len(ref_rows) or any(not valid(row) for row in ref_rows):
        raise ValueError("reference violates the expected unique-parameter contract")
    result = {"reference_sha256": sha(reference), "reference_rows": len(ref_rows),
              "output_exists": output.is_file(), "output_sha256": sha(output) if output.is_file() else None}
    if not output.is_file():
        return {**result, "classification": "NO_OUTPUT"}
    try:
        rows = read_rows(output)
    except (ValueError, UnicodeError, csv.Error) as exc:
        return {**result, "classification": "INVALID_OUTPUT", "reason": str(exc)}
    invalid = [row for row in rows if not valid(row)]
    by_key = {}
    for row in rows:
        by_key.setdefault(key(row), []).append(row)
    duplicate_keys = [group for group in by_key.values() if len(group) > 1]
    conflict_keys = [group for group in duplicate_keys
                     if any(not objectives_match(group[0], row) for row in group[1:])]
    matched = {k for k, group in by_key.items() if k in refs
               and any(valid(row) and objectives_match(row, refs[k]) for row in group)}
    known_mismatch_rows = sum(k in refs and not objectives_match(row, refs[k])
                              for k, group in by_key.items() for row in group)
    extra_rows = sum(k not in refs for k, group in by_key.items() for row in group)
    missing = len(refs) - len(matched)
    if not rows:
        classification = "EMPTY_OUTPUT"
    elif invalid or conflict_keys or known_mismatch_rows or missing:
        classification = "CONTRACT_OR_REFERENCE_MISMATCH"
    elif extra_rows or duplicate_keys:
        classification = "UNRESOLVED_ADDITIONAL_OR_DUPLICATE_ROWS"
    else:
        classification = "MATCHES_RELEASED_REFERENCE_WITHIN_TOLERANCES"
    return {**result, "classification": classification, "output_rows": len(rows),
            "invalid_rows": len(invalid), "matched_reference_keys": len(matched),
            "missing_reference_keys": missing, "known_reference_mismatch_rows": known_mismatch_rows,
            "extra_parameter_rows_unresolved": extra_rows, "duplicate_parameter_keys": len(duplicate_keys),
            "conflicting_duplicate_parameter_keys": len(conflict_keys),
            "limits": "Comparison with the released reference; extra parameter rows are not independently recomputed."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=int, choices=(1, 2), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args()
    if sha(args.reference) != EXPECTED[args.task]:
        raise ValueError("released reference hash differs")
    print(json.dumps({"task": args.task, **analyze(args.output, args.reference)}, indent=2))


if __name__ == "__main__":
    main()
