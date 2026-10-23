from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from stale_semantic_judge_v3 import judge_prompt, parse_judge


class SemanticJudgeTests(unittest.TestCase):
    """Validate method blindness and strict judge output parsing."""

    def test_prompt_contains_hidden_reference_but_no_method_names(self) -> None:
        prompt = judge_prompt(
            {"M_old": "old", "M_new": "new", "explanation": "change"},
            "question",
            "[User] evidence",
            {"A": "answer a", "B": "answer b", "C": "answer c", "D": "answer d"},
        )
        self.assertIn("M_new: new", prompt)
        for arm in ("direct_answer", "one_call_facts", "state_card", "timeline"):
            self.assertNotIn(arm, prompt)

    def test_parse_rejects_missing_response_code(self) -> None:
        value = '{"evaluations":{"A":{},"B":{},"C":{}}}'
        status, parsed, errors = parse_judge(value)
        self.assertEqual(status, "SCHEMA_INVALID")
        self.assertIsNone(parsed)
        self.assertTrue(errors)

    def test_parse_rejects_string_booleans(self) -> None:
        row = {
            "current_fact_supported": "Yes",
            "old_state_rejected": "Yes",
            "evidence_consistent": "Yes",
            "safe_unknown": "No",
            "pass": True,
            "error_type": None,
        }
        value = {"evaluations": {code: dict(row) for code in "ABCD"}}
        status, parsed, errors = parse_judge(json.dumps(value))
        self.assertEqual(status, "SCHEMA_INVALID")
        self.assertIsNone(parsed)
        self.assertTrue(any(error.startswith("field_not_boolean") for error in errors))

    def test_parse_accepts_dynamic_three_code_contract(self) -> None:
        row = {
            "current_fact_supported": True,
            "old_state_rejected": True,
            "evidence_consistent": True,
            "safe_unknown": False,
            "pass": True,
            "error_type": None,
        }
        value = {"evaluations": {code: dict(row) for code in "ABC"}}
        status, parsed, errors = parse_judge(json.dumps(value), ("A", "B", "C"))
        self.assertEqual(status, "VALID")
        self.assertIsNotNone(parsed)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
