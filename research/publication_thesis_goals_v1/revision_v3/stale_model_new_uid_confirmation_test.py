"""Tests for the frozen new-UID paired confirmation."""

from __future__ import annotations

import unittest

import stale_model_new_uid_confirmation as confirmation


class NewUidConfirmationTests(unittest.TestCase):
    """Validate frozen selection, prompts, metric, and planned accounting."""

    def test_selection_excludes_current_uids_and_balances_types(self) -> None:
        data = []
        for index in range(12):
            kind = "T1" if index < 6 else "T2"
            uid = f"uid-{index:02d}"
            data.append({"uid": uid, "type": kind})
        excluded = {"uid-00", "uid-01", "uid-06", "uid-07"}
        selected = confirmation.select_new_uid_confirmation(data, excluded, per_type=2)
        self.assertEqual(
            [(item["uid"], item["type"]) for item in selected],
            [
                ("uid-02", "T1"),
                ("uid-03", "T1"),
                ("uid-08", "T2"),
                ("uid-09", "T2"),
            ],
        )

    def test_frozen_prompts_exclude_hidden_metadata(self) -> None:
        sessions = [[{"role": "user", "content": "The user moved."}]]
        one_shot = confirmation.build_actor_prompt("Is the state stale?", sessions)
        stage1 = confirmation.build_stage1_prompt("Is the state stale?", sessions)
        stage2 = confirmation.build_stage2_prompt(
            "Is the state stale?",
            '{"old_state":"before","new_state":"after","change_type":"UNKNOWN"}',
        )
        for prompt in (one_shot, stage1):
            for literal in confirmation.FORBIDDEN_ACTOR_LITERALS:
                self.assertNotIn(literal, prompt)
        self.assertNotIn("Selected evidence sessions", stage2)

    def test_pair_success_requires_both_metrics(self) -> None:
        parsed = {
            "decision": "ANSWER",
            "state_resolution": "STALE_DETECTED",
            "premise_resistance": "NOT_APPLICABLE",
            "action_adaptation": "CURRENT_STATE_ALIGNED",
            "answer": "No",
        }
        self.assertTrue(confirmation.pair_success(parsed, "NEGATIVE_OLD_STATE"))
        self.assertFalse(confirmation.pair_success(parsed, "POSITIVE_OLD_STATE"))
        self.assertFalse(
            confirmation.pair_success(
                {**parsed, "state_resolution": "STALE_NOT_DETECTED"},
                "NEGATIVE_OLD_STATE",
            )
        )

    def test_summary_reports_planned_twenty_four(self) -> None:
        summary = confirmation.paired_summary([])
        self.assertEqual(summary["cost"]["planned_generation_calls"], 24)
        self.assertEqual(summary["cost"]["observed_generation_calls"], 0)
        self.assertEqual(summary["overall"]["uids"], 0)


if __name__ == "__main__":
    unittest.main()
