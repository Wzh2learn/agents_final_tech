#!/usr/bin/env python3

from __future__ import annotations

import json
import unittest
from pathlib import Path

from trajectory_classifier import action_change, classify_trajectory


ROOT = Path(__file__).resolve().parent


class ReuseDiagnosticsTests(unittest.TestCase):
    def test_synthetic_success_failure_refusal_and_missing(self) -> None:
        fixtures = json.loads(
            (ROOT / "synthetic_trajectory_fixtures.json").read_text(encoding="utf-8")
        )
        self.assertFalse(fixtures["scientific_sample"])
        for case in fixtures["cases"]:
            actual = classify_trajectory(
                case["result"],
                raw_complete=case["raw_complete"],
                is_fixture=True,
            )
            for key, expected in case["expected"].items():
                self.assertEqual(actual[key], expected, f"{case['name']}:{key}")
            self.assertFalse(actual["scientific_sample_eligible"])

    def test_failed_followup_is_complete_and_corrective(self) -> None:
        first = {
            "plan": {"params": {"expression": "2 - 1"}},
            "consume": {"status": "UNKNOWN", "delta_target": None, "unit": None},
            "feedback_category": "TOOL_FAILURE",
        }
        followup = {
            "plan": {"params": {"expression": "2 - 1.0"}},
            "consume": {"status": "ANSWER", "delta_target": 1.0, "unit": "%"},
            "feedback_category": "SUCCESS",
        }
        self.assertEqual(action_change(first, followup), "CORRECTIVE_CHANGE")
        complete_first = dict(first, status="COMPLETE", plan_request={"request_key": "p"}, consume_request={"request_key": "c"}, tool_result={"status": "TOOL_ERROR"}, hidden_reference={"delta_target": 1.0, "target_unit": "%"})
        classified = classify_trajectory(complete_first, raw_complete=True)
        self.assertTrue(classified["trajectory_complete"])
        self.assertFalse(classified["tool_execution_success"])
        self.assertIsNone(classified["post_feedback_action_change"])

    def test_numeric_tail_drift_is_not_action_change(self) -> None:
        first = {
            "plan": {"params": {"expression": "138.3 - 130.0"}},
            "consume": {"status": "ANSWER", "delta_target": 8.3, "unit": "currency"},
            "feedback_category": "SUCCESS",
        }
        followup = {
            "plan": {"params": {"expression": "138.3 - 130.0"}},
            "consume": {"status": "ANSWER", "delta_target": 8.300000000000011, "unit": "currency"},
            "feedback_category": "SUCCESS",
        }
        self.assertEqual(action_change(first, followup), "NO_CHANGE")

    def test_synthetic_wrong_answer_and_unknown_are_complete(self) -> None:
        fixtures = json.loads(
            (ROOT / "synthetic_trajectory_fixtures.json").read_text(encoding="utf-8")
        )
        for case in fixtures["cases"]:
            actual = classify_trajectory(
                case["result"], raw_complete=case["raw_complete"], is_fixture=True
            )
            for key, expected in case["expected"].items():
                self.assertEqual(actual[key], expected, f"{case['name']}:{key}")

    def test_real_contexts_have_no_invented_lesson(self) -> None:
        pool = json.loads((ROOT / "REUSE_HISTORY_CONTEXT_POOL.json").read_text(encoding="utf-8"))
        self.assertFalse(pool["contains_hardcoded_lesson"])
        for row in pool["experiences"]:
            self.assertNotIn("lesson", row)
            self.assertIn("task", row)
            self.assertIn("actual_attempts", row)
            self.assertIn("post_feedback_action_change", row)
        self.assertFalse(pool["contains_hidden_reference"])
        self.assertFalse(pool["contains_future_answer"])
        self.assertFalse(pool["contains_fabricated_correction"])


if __name__ == "__main__":
    unittest.main()
