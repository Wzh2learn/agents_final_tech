"""Run owned no-model budget fault tests and write a completion receipt."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import unittest
from pathlib import Path

from research.word_scoring_new_family_20261027_v1.budget import (
    test_word_new_family_faults as owned_tests,
)
from research.word_scoring_new_family_20261027_v1.budget.test_word_new_family_faults import (
    FAULT_ROOT,
)
from research.adaptive_mechanism_20261027_v1.persistent_budget import (
    ledger,
    runner,
    test_persistent_budget as base_tests,
)


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
RECEIPT_PATH = ROOT / "budget" / "BUDGET_FAULT_TEST_RECEIPT.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def iter_tests(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iter_tests(item)
        else:
            yield item


def main() -> int:
    if FAULT_ROOT.exists():
        shutil.rmtree(FAULT_ROOT)
    FAULT_ROOT.mkdir(parents=True, exist_ok=True)
    suite = unittest.TestSuite(
        [
            unittest.defaultTestLoader.loadTestsFromModule(base_tests),
            unittest.defaultTestLoader.loadTestsFromModule(owned_tests),
        ]
    )
    test_ids = sorted(test.id() for test in iter_tests(suite))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    shutil.rmtree(FAULT_ROOT, ignore_errors=True)
    if FAULT_ROOT.parent.exists() and not any(FAULT_ROOT.parent.iterdir()):
        FAULT_ROOT.parent.rmdir()
    receipt = {
        "schema": "word_new_family_budget_fault_test_receipt_v1",
        "status": "PASS" if result.wasSuccessful() else "FAIL",
        "commands": [
            (
                "PYTHONPATH=src:. python3.12 "
                "research/word_scoring_new_family_20261027_v1/budget/run_fault_tests.py"
            )
        ],
        "python": sys.version.split()[0],
        "test_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "tests": test_ids,
        "real_model_calls": 0,
        "real_generation_attempts": 0,
        "training_runs": 0,
        "actual_local_model_loaded": False,
        "fault_root": str(FAULT_ROOT),
        "fault_root_owned_by_task": True,
        "uses_stub_loaders_only": True,
        "source_hashes": {
            str(path.relative_to(REPO)): sha256(path)
            for path in [
                base_tests.__file__ and Path(base_tests.__file__),
                Path(owned_tests.__file__),
                Path(ledger.__file__),
                Path(runner.__file__),
            ]
        },
    }
    RECEIPT_PATH.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
