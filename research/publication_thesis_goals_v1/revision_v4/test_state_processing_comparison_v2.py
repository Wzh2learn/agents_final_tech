from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import state_processing_comparison_v2 as comparison


class StateProcessingComparisonTests(unittest.TestCase):
    """Validate source visibility, strict JSON and matched generation budgets."""

    def test_format_sessions_preserves_role_order_and_time(self) -> None:
        item = {
            "haystack_session": [[
                {"role": "user", "content": "I moved."},
                {"role": "assistant", "content": "Understood."},
            ]],
            "timestamps": ["2025-01-02 03:04"],
        }
        text = comparison.format_sessions(item, [0])
        self.assertIn("Session 1 [Time: 2025-01-02 03:04]", text)
        self.assertLess(text.index("User turn 1"), text.index("Assistant turn 2"))

    def test_prompts_exclude_hidden_reference_fields(self) -> None:
        evidence = "[User] I moved."
        prompts = [
            comparison.build_direct_prompt("Where?", evidence),
            comparison.build_one_call_prompt("Where?", evidence),
            comparison.build_timeline_prompt("Where?", evidence),
            comparison.build_state_card_prompt("Where?", evidence),
        ]
        for prompt in prompts:
            for literal in ("M_old", "M_new", "explanation", "relevant_session_index"):
                self.assertNotIn(literal, prompt)

    def test_strict_parse_rejects_extra_fields(self) -> None:
        status, parsed, errors = comparison.parse_json_object(
            '{"decision":"UNKNOWN","answer":null,"evidence_refs":[],"extra":1}',
            {"decision", "answer", "evidence_refs"},
        )
        self.assertEqual(status, "SCHEMA_INVALID")
        self.assertIsNone(parsed)
        self.assertTrue(errors)

    def test_summary_keeps_planned_calls_distinct(self) -> None:
        summary = comparison.summarize([], [])
        self.assertEqual(summary["overall"]["planned_calls"], 0)
        self.assertEqual(summary["by_arm"]["direct_answer"]["planned_calls"], 0)


if __name__ == "__main__":
    unittest.main()
