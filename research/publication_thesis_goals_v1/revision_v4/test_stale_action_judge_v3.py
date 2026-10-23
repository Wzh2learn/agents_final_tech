from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from stale_action_judge_v3 import parse_action_judge


class ActionJudgeTests(unittest.TestCase):
    """Validate the action-specific strict judge contract."""

    def test_valid_two_response_contract(self) -> None:
        row = {
            "action_state_aligned": True,
            "stale_action_rejected": True,
            "evidence_consistent": True,
            "non_generic": True,
            "safe_unknown": False,
            "pass": True,
            "error_type": None,
        }
        status, parsed, errors = parse_action_judge(
            json.dumps({"evaluations": {"A": row, "B": row}})
        )
        self.assertEqual(status, "VALID")
        self.assertIsNotNone(parsed)
        self.assertEqual(errors, [])

    def test_pass_requires_action_alignment(self) -> None:
        row = {
            "action_state_aligned": False,
            "stale_action_rejected": True,
            "evidence_consistent": True,
            "non_generic": True,
            "safe_unknown": False,
            "pass": True,
            "error_type": None,
        }
        status, _parsed, errors = parse_action_judge(
            json.dumps({"evaluations": {"A": row, "B": row}})
        )
        self.assertEqual(status, "SCHEMA_INVALID")
        self.assertTrue(any(error.startswith("pass_inconsistent") for error in errors))


if __name__ == "__main__":
    unittest.main()
