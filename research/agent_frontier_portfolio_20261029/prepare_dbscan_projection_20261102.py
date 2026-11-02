#!/usr/bin/env python3
"""Project the public DBSCAN input to task-relevant, non-identifier columns."""

import argparse
import csv
import itertools
import json
from pathlib import Path

from run_dbscan_reference_20261101 import DATA, sha


FIELDS = ("file_rad", "x", "y", "frame_file")


def project(source, target):
    with source.open(encoding="utf-8", newline="") as inp, target.open("w", encoding="utf-8", newline="") as out:
        reader = csv.DictReader(inp)
        if not reader.fieldnames or any(reader.fieldnames.count(x) != 1 for x in FIELDS):
            raise ValueError("required columns missing or duplicated")
        writer = csv.DictWriter(out, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        count = 0
        for row in reader:
            writer.writerow({key: row[key] for key in FIELDS})
            count += 1
        source_columns = len(reader.fieldnames)
    target.chmod(0o644)  # The parent directory remains private; sandbox drops DAC privileges.
    with source.open(encoding="utf-8", newline="") as inp, target.open(encoding="utf-8", newline="") as out:
        original, projected = csv.DictReader(inp), csv.DictReader(out)
        if projected.fieldnames != list(FIELDS):
            raise ValueError("unexpected projected schema")
        compared = 0
        for before, after in itertools.zip_longest(original, projected):
            if before is None or after is None or any(before[k] != after[k] for k in FIELDS):
                raise ValueError("projection differs from source")
            compared += 1
        if compared != count:
            raise ValueError("projection row count differs")
    return {"source_sha256": sha(source), "projection_sha256": sha(target),
            "rows": count, "source_columns": source_columns, "projected_columns": list(FIELDS),
            "row_order_and_selected_values_equal": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for name, expected in DATA.items():
        if sha(args.source / name) != expected:
            raise ValueError("source input changed: " + name)
    args.output.mkdir(parents=True, exist_ok=False)
    args.output.chmod(0o700)
    data_dir = args.output / "data"
    data_dir.mkdir(mode=0o755)
    data_dir.chmod(0o755)
    files = {name: project(args.source / name, data_dir / name) for name in DATA}
    receipt = {"source_task": 1, "script_sha256": sha(Path(__file__).resolve()),
               "fields": list(FIELDS), "files": files,
               "model_calls": 0, "training_runs": 0,
               "limitation": "Projection equality does not determine the original dataset licence."}
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    (args.output / "receipt.json").chmod(0o600)
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    main()
