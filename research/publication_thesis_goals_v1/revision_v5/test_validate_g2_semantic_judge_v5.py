from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_g2_semantic_judge_v5 import corrected_category


class ValidateG2SemanticJudgeTests(unittest.TestCase):
    """Validate the contract-level category corrections."""

    def test_clarify_is_reasonable_not_completion(self) -> None:
        row = {"answer_record": {"decision": "CLARIFY", "answer": "Which plan?"}}
        verdict = {
            "primary_category": "GROUNDED_TASK_COMPLETION",
            "response_contract_status": "VALID",
        }
        category, reasons = corrected_category(row, verdict)
        self.assertEqual(category, "REASONABLE_UNKNOWN_OR_CLARIFICATION")
        self.assertIn("CLARIFY_IS_NOT_TASK_COMPLETION", reasons)

    def test_answer_without_text_is_interface_failure(self) -> None:
        row = {"answer_record": {"decision": "ANSWER", "answer": None}}
        verdict = {
            "primary_category": "GROUNDED_TASK_COMPLETION",
            "response_contract_status": "VALID",
        }
        category, reasons = corrected_category(row, verdict)
        self.assertEqual(category, "INTERFACE_FORMAT_FAILURE")
        self.assertIn("ANSWER_DECISION_WITHOUT_ANSWER", reasons)

    def test_unnecessary_refusal_is_not_overwritten(self) -> None:
        row = {"answer_record": {"decision": "UNKNOWN", "answer": None}}
        verdict = {
            "primary_category": "UNNECESSARY_REFUSAL_DESPITE_SUFFICIENT_EVIDENCE",
            "response_contract_status": "VALID",
        }
        category, reasons = corrected_category(row, verdict)
        self.assertEqual(category, "UNNECESSARY_REFUSAL_DESPITE_SUFFICIENT_EVIDENCE")
        self.assertEqual(reasons, [])


if __name__ == "__main__":
    unittest.main()
