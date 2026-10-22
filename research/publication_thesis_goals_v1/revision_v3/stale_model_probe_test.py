"""Focused tests for the bounded STALE model probe."""

from __future__ import annotations

import unittest

import stale_model_probe as probe


class StaleModelProbeTests(unittest.TestCase):
    """Validate actor visibility and strict, non-coercing response handling."""

    def test_actor_prompt_excludes_hidden_reference_metadata(self) -> None:
        sessions = [[{"role": "user", "content": "I moved to Austin."}]]
        prompt = probe.build_actor_prompt("Where does the user live?", sessions)
        for literal in probe.FORBIDDEN_ACTOR_LITERALS:
            self.assertNotIn(literal, prompt)
        self.assertIn("Austin", prompt)

    def test_query_only_contains_no_session_text(self) -> None:
        prompt = probe.build_actor_prompt("Where does the user live?", [])
        self.assertIn("No evidence session was selected.", prompt)

    def test_validate_output_rejects_missing_and_extra_fields(self) -> None:
        base = {
            "decision": "UNKNOWN",
            "state_resolution": "UNKNOWN",
            "premise_resistance": "UNKNOWN",
            "action_adaptation": "UNKNOWN",
            "answer": None,
        }
        valid, errors = probe.validate_output(base)
        self.assertTrue(valid, errors)
        invalid, errors = probe.validate_output({**base, "extra": 1})
        self.assertFalse(invalid)
        self.assertTrue(any(error.startswith("field_set:") for error in errors))

    def test_non_answer_must_have_null_answer(self) -> None:
        value = {
            "decision": "UNKNOWN",
            "state_resolution": "UNKNOWN",
            "premise_resistance": "UNKNOWN",
            "action_adaptation": "UNKNOWN",
            "answer": "not null",
        }
        valid, errors = probe.validate_output(value)
        self.assertFalse(valid)
        self.assertIn("answer_must_be_null_for_non_ANSWER", errors)

    def test_parse_is_strict_and_preserves_json_error(self) -> None:
        parsed = probe.parse_model_content('{"decision":')
        self.assertEqual(parsed["parse_status"], "INVALID_JSON")
        self.assertIsNone(parsed.get("parsed"))
        self.assertTrue(parsed["parse_errors"])

    def test_selection_is_balanced_and_deterministic(self) -> None:
        data = [
            {"uid": "b", "type": "T1"},
            {"uid": "a", "type": "T1"},
            {"uid": "d", "type": "T2"},
            {"uid": "c", "type": "T2"},
        ]
        selected = probe.select_instances(data, total=4)
        self.assertEqual(
            [(item["uid"], item["type"]) for item in selected],
            [("a", "T1"), ("b", "T1"), ("c", "T2"), ("d", "T2")],
        )

    def test_summary_keeps_planned_and_observed_distinct(self) -> None:
        rows = [{
            "arm": "query_only",
            "dimension": "dim1",
            "context_chars": 10,
            "primary_proxy": "SAFE_UNKNOWN",
            "hidden_reference": {},
            "call": {
                "physical_http_calls": 1,
                "transport_status": "HTTP_OK",
                "parse_status": "VALID",
                "parsed": {"decision": "UNKNOWN"},
                "accounting_attempts": 1,
                "accounting_tokens": 2,
                "latency_seconds": 0.1,
            },
        }]
        summary = probe.summarize(rows, planned_total=36)
        self.assertEqual(summary["overall"]["planned"], 36)
        self.assertEqual(summary["overall"]["observed"], 1)
        self.assertEqual(summary["by_arm"]["query_only"]["planned"], 12)
        self.assertEqual(summary["by_arm"]["query_only"]["observed"], 1)


if __name__ == "__main__":
    unittest.main()
