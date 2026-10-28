from __future__ import annotations

import json
import unittest

from research.word_scoring_new_family_20261027_v1.scoring_v3 import (
    diagnostic_rescore as diagnostic,
)


class DiagnosticInterfaceControls(unittest.TestCase):
    def reference(self) -> dict[str, object]:
        return {
            "question": "What is the difference?",
            "answer": 2.41,
            "answer_type": "arithmetic",
            "unit": "UNKNOWN",
            "program": "8.40-5.99",
            "source_requirement": "table",
            "table_text": (
                "columns: C0= | C1=low | C2=high\n"
                "R1 [First Quarter] C0=First Quarter | C1=5.99 | C2=8.40"
            ),
            "paragraphs": [],
            "required_evidence": [
                {
                    "binding_mode": "role_period",
                    "citation": "TABLE:R1:C2",
                    "operand_id": "operand_1",
                }
            ],
        }

    def visible(self) -> object:
        return diagnostic.visible_context(self.reference())

    def test_extract_json_ignores_reasoning_prefix(self) -> None:
        text = "reasoning\n" + json.dumps(
            {
                "answer": "2.41",
                "numeric_value": 2.41,
                "unit": "UNKNOWN",
                "evidence_refs": ["TABLE:R1:C1", "TABLE:R1:C2"],
                "unknown": False,
                "clarification": "",
            }
        )
        objects = diagnostic.extract_json_objects(text)
        self.assertEqual(len(objects), 1)
        self.assertEqual(set(objects[0]), diagnostic.FINAL_KEYS)

    def test_typed_numeric_program_uses_shared_calculator(self) -> None:
        payload = {
            "answer_type": "arithmetic",
            "answer": "2.41",
            "operands": [],
            "program": "8.40-5.99",
            "operation": "subtract",
            "unit": "UNKNOWN",
            "evidence_refs": ["TABLE:R1:C1", "TABLE:R1:C2"],
            "unknown": False,
            "clarification": "",
        }
        final, receipt = diagnostic.normalize_typed(
            payload, "T", self.reference(), self.visible()
        )
        self.assertEqual(receipt["status"], "PASS")
        self.assertTrue(receipt["calculator_executed"])
        self.assertAlmostEqual(final["numeric_value"], 2.41, places=6)

    def test_m_binding_row_mismatch_fails_before_execution(self) -> None:
        payload = {
            "answer_type": "arithmetic",
            "answer": "2.41",
            "operands": [],
            "program": "8.40-5.99",
            "operation": "subtract",
            "unit": "UNKNOWN",
            "evidence_refs": ["TABLE:R1:C2"],
            "unknown": False,
            "clarification": "",
            "bindings": [
                {
                    "evidence_ref": "TABLE:R1:C2",
                    "row": 9,
                    "period": "First Quarter",
                    "role": "high",
                    "unit": None,
                }
            ],
        }
        final, receipt = diagnostic.normalize_typed(
            payload, "M", self.reference(), self.visible()
        )
        self.assertIsNone(final)
        self.assertEqual(receipt["reason"], "binding_row_mismatch")

    def test_m_visible_binding_passes(self) -> None:
        payload = {
            "answer_type": "arithmetic",
            "answer": "2.41",
            "operands": [],
            "program": "8.40-5.99",
            "operation": "subtract",
            "unit": "UNKNOWN",
            "evidence_refs": ["TABLE:R1:C2"],
            "unknown": False,
            "clarification": "",
            "bindings": [
                {
                    "evidence_ref": "TABLE:R1:C2",
                    "row": 1,
                    "period": "First Quarter",
                    "role": "high",
                    "unit": None,
                }
            ],
        }
        final, receipt = diagnostic.normalize_typed(
            payload, "M", self.reference(), self.visible()
        )
        self.assertIsNotNone(final)
        self.assertEqual(receipt["status"], "PASS")

    def test_formula_canonicalization_ignores_numeric_literals(self) -> None:
        self.assertEqual(
            diagnostic.canonical_formula("8.40-5.99"),
            diagnostic.canonical_formula("10.40-7.99"),
        )


if __name__ == "__main__":
    unittest.main()
