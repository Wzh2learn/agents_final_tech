#!/usr/bin/env python3
"""Run offline unit tests and emit a deterministic receipt."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
import unittest
import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host-label", default="LOCAL_UNSPECIFIED")
    parser.add_argument("--receipt-name", default="TEST_RECEIPT.json")
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    receipt = {
        "schema": "history_collection_offline_test_receipt_v1",
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "status": "PASS" if result.wasSuccessful() else "FAIL",
        "fixture_sha256": sha256_file(ROOT / "fixtures" / "synthetic_offline_cases.json"),
        "implementation_hashes": {
            path.name: sha256_file(path)
            for path in sorted(ROOT.glob("*.py"))
        },
        "test_hashes": {
            path.name: sha256_file(path)
            for path in sorted((ROOT / "tests").glob("*.py"))
        },
        "host_label": args.host_label,
        "platform": platform.platform(),
        "python_version": sys.version,
        "cost": {
            "model_calls": 0,
            "endpoint_calls": 0,
            "judge_calls": 0,
            "training_calls": 0,
        },
    }
    output = ROOT / "tests" / Path(args.receipt_name).name
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
