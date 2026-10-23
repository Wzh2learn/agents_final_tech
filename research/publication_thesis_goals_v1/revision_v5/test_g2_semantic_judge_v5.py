from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from g2_semantic_judge_v5 import parse_judge


def verdict() -> dict[str, object]:
    return {
        "primary_category": "GROUNDED_TASK_COMPLETION",
        "historical_fact_status": "SUPPORTED",
        "action_constraints_respected": True,
        "action_reasoning_valid": True,
        "unsupported_detail_status": "NONE",
        "response_contract_status": "VALID",
        "reasonable_abstention": False,
        "unnecessary_refusal": False,
        "fact_correct_action_wrong": False,
        "reason": "Supported.",
        "quote": "supported fact",
    }


class G2SemanticJudgeTests(unittest.TestCase):
    """Validate strict judge verdict objects."""

    def test_valid_single_verdict(self) -> None:
        status, parsed, errors = parse_judge(
            '{"evaluations":{"A":' + __import__("json").dumps(verdict()) + "}}",
            ("A",),
        )
        self.assertEqual(status, "VALID")
        self.assertIsNotNone(parsed)
        self.assertEqual(errors, [])

    def test_string_boolean_is_rejected(self) -> None:
        row = verdict()
        row["action_constraints_respected"] = "Yes"
        status, parsed, errors = parse_judge(
            '{"evaluations":{"A":' + __import__("json").dumps(row) + "}}",
            ("A",),
        )
        self.assertEqual(status, "SCHEMA_INVALID")
        self.assertIsNone(parsed)
        self.assertTrue(any(error.startswith("boolean") for error in errors))


if __name__ == "__main__":
    unittest.main()
