from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from g2_fixed_state_transfer_probe_v5 import (
    build_answer_prompt,
    build_bundle_prompt,
    format_sessions,
    parse_exact_json,
)


ITEM = {
    "timestamps": ["2025-01-01 00:00"],
    "haystack_session": [[
        {"role": "user", "content": "I drive a blue sedan."},
        {"role": "assistant", "content": "Consider a hatchback."},
    ]],
}


class G2FixedStateTransferTests(unittest.TestCase):
    """Validate fixed evidence visibility and strict answer contracts."""

    def test_session_format_preserves_roles_and_time(self) -> None:
        text = format_sessions(ITEM, [0])
        self.assertIn("Session 1 [Time: 2025-01-01 00:00]", text)
        self.assertIn("User turn 1", text)
        self.assertIn("Assistant turn 2", text)

    def test_prompts_exclude_hidden_reference_fields(self) -> None:
        evidence = format_sessions(ITEM, [0])
        prompts = [
            build_bundle_prompt("plain_fact_bundle", "state?", evidence),
            build_bundle_prompt("evidence_decision_bundle", "state?", evidence),
            build_answer_prompt("plain_fact_bundle", "act?", {"current_facts": []}),
        ]
        for prompt in prompts:
            for field in ("M_old", "M_new", "explanation", "relevant_session_index"):
                self.assertNotIn(field, prompt)

    def test_parse_is_exact(self) -> None:
        required = {"decision", "answer", "basis_refs", "constraints_considered"}
        status, _parsed, errors = parse_exact_json(
            '{"decision":"UNKNOWN","answer":null,"basis_refs":[],"constraints_considered":[],"extra":1}',
            required,
        )
        self.assertEqual(status, "SCHEMA_INVALID")
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
