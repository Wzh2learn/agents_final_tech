from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from revision_operator_diagnostic_v1 import (
    TERMINAL_INSTRUCTION,
    diff_target,
    minimal_edit_instruction,
    normalize_generated_text,
    strict_target,
    standardized_prompt,
)


class RevisionOperatorDiagnosticTests(unittest.TestCase):
    def test_minimal_edit_only_reports_one_reference_change(self) -> None:
        candidate = {"program": {"ref": "R1:C1"}, "evidence_refs": ["R1:C1"], "unit": "million"}
        expected = {"program": {"ref": "R2:C1"}, "evidence_refs": ["R2:C1"], "unit": "million"}
        differences = diff_target(candidate, expected)
        self.assertEqual(len(differences), 2)
        edit = minimal_edit_instruction(differences)
        self.assertIsNotNone(edit)
        self.assertIn("replace evidence reference", edit)

    def test_standardized_prompt_has_one_terminal_instruction(self) -> None:
        instance = {
            "prompt": "Question: What was the change?",
            "expected": {"answer": 1, "program": {}, "evidence_refs": [], "unit": "million"},
        }
        prompt = standardized_prompt(
            instance,
            '{"program":{"const":1},"evidence_refs":[],"unit":"million"}',
            {
                "status": "control",
                "finding": "No targeted finding.",
                "edit": "Return the candidate unchanged.",
            },
        )
        self.assertEqual(prompt.count(TERMINAL_INSTRUCTION), 1)
        self.assertGreater(prompt.index(TERMINAL_INSTRUCTION), prompt.index("Previous candidate:"))
        self.assertNotIn("oracle-assisted", prompt.casefold())

    def test_syntax_adapter_only_removes_unmatched_tail_parenthesis(self) -> None:
        raw = '{"program":{"const":1},"evidence_refs":[],"unit":"thousand")}'
        normalized, applied, actions = normalize_generated_text(raw)
        self.assertTrue(applied)
        self.assertEqual(actions, ["replace_quote_close_paren_brace_tail"])
        self.assertEqual(
            normalized,
            '{"program":{"const":1},"evidence_refs":[],"unit":"thousand"}',
        )

    def test_syntax_adapter_does_not_repair_internal_numeric_corruption(self) -> None:
        raw = '{"program":{"const":1)0},"evidence_refs":[],"unit":"million"}'
        normalized, applied, actions = normalize_generated_text(raw)
        self.assertFalse(applied)
        self.assertEqual(actions, [])
        self.assertEqual(normalized, raw)
        self.assertIsNone(strict_target(normalized))

    def test_strict_target_rejects_embedded_json(self) -> None:
        embedded = 'prefix\n{"program":{"const":1},"evidence_refs":[],"unit":"million"}'
        self.assertIsNone(strict_target(embedded))


if __name__ == "__main__":
    unittest.main()
