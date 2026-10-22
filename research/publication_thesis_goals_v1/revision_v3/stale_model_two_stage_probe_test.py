"""Tests for the deployable two-stage STALE mechanism probe."""

from __future__ import annotations

import unittest

import stale_model_two_stage_probe as probe


class TwoStageProbeTests(unittest.TestCase):
    """Validate visibility boundaries and strict stage schemas."""

    def test_stage1_prompt_excludes_hidden_reference_fields(self) -> None:
        sessions = [[{"role": "user", "content": "The user moved to Austin."}]]
        prompt = probe.build_stage1_prompt("Where does the user live?", sessions)
        for literal in probe.FORBIDDEN_ACTOR_LITERALS:
            self.assertNotIn(literal, prompt)
        self.assertIn("The user moved to Austin.", prompt)
        self.assertIn('"old_state"', prompt)

    def test_stage2_prompt_contains_only_state_card_and_query(self) -> None:
        prompt = probe.build_stage2_prompt(
            "Does the old state remain?",
            '{"old_state":"Seattle","new_state":"Austin","change_type":"CO_REFERENTIAL"}',
        )
        self.assertIn("Seattle", prompt)
        self.assertIn("Does the old state remain?", prompt)
        self.assertNotIn("Selected evidence sessions", prompt)

    def test_state_card_validation_is_strict(self) -> None:
        card = {
            "old_state": "Seattle",
            "new_state": "Austin",
            "change_type": "CO_REFERENTIAL",
        }
        valid, errors = probe.validate_state_card(card)
        self.assertTrue(valid, errors)
        invalid, errors = probe.validate_state_card({**card, "extra": 1})
        self.assertFalse(invalid)
        self.assertTrue(any(error.startswith("field_set:") for error in errors))

    def test_parse_state_card_does_not_repair_json(self) -> None:
        parsed = probe.parse_state_card_content('{"old_state":')
        self.assertEqual(parsed["parse_status"], "INVALID_JSON")
        self.assertIsNone(parsed.get("parsed"))

    def test_summary_keeps_call_and_pair_plans_distinct(self) -> None:
        summary = probe.summarize([])
        self.assertEqual(summary["overall"]["planned_generation_calls"], 8)
        self.assertEqual(summary["overall"]["observed_generation_calls"], 0)
        self.assertEqual(summary["pairs"]["planned"], 4)
        self.assertEqual(summary["pairs"]["observed"], 0)

    def test_summary_tolerates_failed_stage2_parse(self) -> None:
        row = {
            "stage1": {
                "transport_status": "HTTP_OK",
                "parse_status": "VALID",
                "physical_http_calls": 1,
                "accounting_attempts": 1,
                "accounting_tokens": 1,
                "latency_seconds": 0.1,
            },
            "stage2": {
                "transport_status": "HTTP_OK",
                "parse_status": "SCHEMA_INVALID",
                "parsed": None,
                "physical_http_calls": 1,
                "accounting_attempts": 1,
                "accounting_tokens": 1,
                "latency_seconds": 0.1,
            },
            "state_card_parse_status": "VALID",
            "state_card": {"change_type": "UNKNOWN"},
            "state_card_leak_detected": [],
            "answer_polarity": "NO_ANSWER",
            "pair_metric": "PARSE_FAILURE",
        }
        summary = probe.summarize([row])
        self.assertEqual(summary["pairs"]["observed"], 1)
        self.assertEqual(summary["pairs"]["stale_detected_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
