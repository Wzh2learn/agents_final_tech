from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from reuse_exact_cache_baseline_v2 import classify


class ReuseExactCacheBaselineTests(unittest.TestCase):
    """Validate decision classification without rerunning modules."""

    def test_unresolved_is_abstain(self) -> None:
        self.assertEqual(classify("UNRESOLVED", "PASS"), "ABSTAIN")

    def test_pass_and_fail_outcomes_are_separate(self) -> None:
        self.assertEqual(classify("PASS", "PASS"), "CORRECT")
        self.assertEqual(classify("PASS", "FAIL"), "FALSE_ACCEPT")
        self.assertEqual(classify("FAIL", "PASS"), "FALSE_REJECT")


if __name__ == "__main__":
    unittest.main()
