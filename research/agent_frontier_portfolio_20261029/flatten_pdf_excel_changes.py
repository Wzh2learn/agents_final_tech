#!/usr/bin/env python3
"""Post-hoc lossless conversion of nested change records into task schema.

This does not access the expected output and never overwrites the original
agent report. It rejects unknown nested fields rather than discarding them.
"""
import argparse
import json
from pathlib import Path


def flatten(report):
    if not isinstance(report, dict) or not isinstance(report.get("deleted_employees"), list) or not isinstance(report.get("modified_employees"), list):
        raise ValueError("invalid report structure")
    result = dict(report)
    flat = []
    for row in report["modified_employees"]:
        if not isinstance(row, dict):
            raise ValueError("non-object change")
        if set(row) == {"id", "changes"}:
            if not isinstance(row["changes"], list):
                raise ValueError("changes is not a list")
            for change in row["changes"]:
                if not isinstance(change, dict) or set(change) != {"field", "old_value", "new_value"}:
                    raise ValueError("unknown nested change shape")
                flat.append({"id": row["id"], **change})
        elif set(row) == {"id", "field", "old_value", "new_value"}:
            flat.append(row)
        else:
            raise ValueError("unknown change shape")
    result["modified_employees"] = flat
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    if args.input.resolve() == args.output.resolve() or args.output.exists():
        raise ValueError("output must be a new path")
    original = json.loads(args.input.read_text(encoding="utf-8"))
    args.output.write_text(json.dumps(flatten(original), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"input_modified_entries": len(original["modified_employees"]),
                      "output_modified_entries": len(flatten(original)["modified_employees"])}))


if __name__ == "__main__":
    main()
