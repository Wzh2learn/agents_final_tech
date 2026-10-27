from __future__ import annotations

import unittest

from research.adaptive_mechanism_20261027_v1.d_integration.question_only_ablation import (
    infer_answer_type_from_question,
)


class QuestionOnlyAblationTests(unittest.TestCase):
    def test_question_text_types(self):
        cases = {
            "How many services have their costs included within the audit fees?": "count",
            "What services have their costs included within the audit fees?": "multi-span",
            "What is the amount of payroll taxes in 2019 and 2018 respectively?": "multi-span",
            "What is the average trade receivables for 2018 and 2019?": "arithmetic",
            "What is the units used for the data in the table?": "span",
        }
        for question, expected in cases.items():
            self.assertEqual(infer_answer_type_from_question(question), expected)

    def test_unknown_is_explicit(self):
        self.assertEqual(infer_answer_type_from_question("Which fact is relevant?"), "unknown")


if __name__ == "__main__":
    unittest.main()
