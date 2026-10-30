#!/usr/bin/env python3
"""Apply a visible exact-before-fuzzy policy to one frozen development program."""
from pathlib import Path
import hashlib
import json
import shutil
import sys


def main(source, target):
    source, target = Path(source), Path(target)
    target.mkdir(parents=True, exist_ok=False)
    for name in ("invoices.pdf", "vendors.xlsx", "purchase_orders.csv"):
        shutil.copyfile(source / name, target / name)
    original = (source / "analyze_fraud.py").read_text(encoding="utf8")
    before = "    if best_score < 80:\n"
    after = "    if vendor_name in vendors:\n        matched_name, best_score = vendor_name, 100\n\n" + before
    if original.count(before) != 1:
        raise ValueError("unexpected source version")
    code = original.replace(before, after)
    (target / "analyze_fraud.py").write_text(code, encoding="utf8")
    print(json.dumps({"original_sha256": hashlib.sha256(original.encode()).hexdigest(),
                      "control_sha256": hashlib.sha256(code.encode()).hexdigest(),
                      "scope": "exact vendor match takes priority over existing fuzzy matching"}))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: prepare_invoice_exact_match_control.py source-work new-work")
    main(*sys.argv[1:])
