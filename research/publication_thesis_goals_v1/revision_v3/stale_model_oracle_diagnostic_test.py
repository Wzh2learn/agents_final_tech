"""Tests for the oracle-only STALE diagnostic."""

from __future__ import annotations

import unittest
from pathlib import Path
import tempfile
import json

import stale_model_oracle_diagnostic as diagnostic


class OracleDiagnosticTests(unittest.TestCase):
    """Validate the development-only visibility contract and scoring proxies."""

    def test_state_values_arm_excludes_explanation(self) -> None:
        sessions = [[{"role": "user", "content": "I moved to Austin."}]]
        prompt = diagnostic.build_diagnostic_prompt(
            "Where does the user live?", sessions, "Seattle", "Austin", None
        )
        self.assertIn("M_old: Seattle", prompt)
        self.assertIn("M_new: Austin", prompt)
        self.assertNotIn("Development-only explanation", prompt)
        self.assertIn("ORACLE_DIAGNOSTIC_NOT_DEPLOYABLE", prompt)
        self.assertNotIn("relevant_session_index", prompt)

    def test_explanation_arm_adds_explanation(self) -> None:
        sessions = [[{"role": "user", "content": "I moved to Austin."}]]
        prompt = diagnostic.build_diagnostic_prompt(
            "Where does the user live?", sessions, "Seattle", "Austin", "Location changed."
        )
        self.assertIn("Development-only explanation:\nLocation changed.", prompt)
        self.assertIn("ORACLE_DIAGNOSTIC_NOT_DEPLOYABLE", prompt)

    def test_answer_polarity_is_lexical_and_neutral(self) -> None:
        self.assertEqual(diagnostic.answer_polarity("No, the state changed."), "NEGATIVE_OLD_STATE")
        self.assertEqual(diagnostic.answer_polarity("Yes, the old state remains."), "POSITIVE_OLD_STATE")
        self.assertEqual(diagnostic.answer_polarity("The evidence is ambiguous."), "OTHER")
        self.assertEqual(diagnostic.answer_polarity(None), "NO_ANSWER")

    def test_summary_keeps_planned_eight(self) -> None:
        summary = diagnostic.summarize([])
        self.assertEqual(summary["overall"]["planned"], 8)
        self.assertEqual(summary["overall"]["observed"], 0)
        self.assertEqual(summary["by_arm"]["state_values_only"]["planned"], 4)

    def test_raw_recovery_is_order_and_identity_checked(self) -> None:
        selected = []
        for index in range(4):
            selected.append({
                "uid": f"uid-{index}",
                "type": "T1" if index < 2 else "T2",
                "M_old": "old",
                "M_new": "new",
                "explanation": "why",
                "relevant_session_index": [0, 1],
                "haystack_session": [
                    [{"role": "user", "content": "old"}],
                    [{"role": "user", "content": "new"}],
                ],
                "probing_queries": {"dim1_query": "Is the state stale?"},
            })
        with tempfile.TemporaryDirectory() as directory:
            raw_dir = Path(directory)
            for attempt, item in enumerate(
                [selected[0], selected[0], selected[1], selected[1],
                 selected[2], selected[2], selected[3], selected[3]],
                start=1,
            ):
                arm = (
                    diagnostic.ARMS_DIAGNOSTIC[0]
                    if attempt % 2 else diagnostic.ARMS_DIAGNOSTIC[1]
                )
                attempt_dir = raw_dir / f"attempt_{attempt:03d}"
                attempt_dir.mkdir()
                prompt = diagnostic.build_diagnostic_prompt(
                    "Is the state stale?",
                    item["haystack_session"],
                    item["M_old"],
                    item["M_new"],
                    item["explanation"] if arm.endswith("explanation") else None,
                )
                (attempt_dir / "request.bin").write_text(json.dumps({
                    "model": "model-x",
                    "messages": [{"role": "user", "content": prompt}],
                }), encoding="utf-8")
                (attempt_dir / "request.json").write_text(json.dumps({
                    "meta": {
                        "attempt": attempt,
                        "uid": item["uid"],
                        "arm": arm,
                        "selected_session_indices_hidden_from_actor": [0, 1],
                    }
                }), encoding="utf-8")
                (attempt_dir / "call_receipt.json").write_text(json.dumps({
                    "transport_status": "HTTP_OK",
                    "parsed": {
                        "decision": "ANSWER",
                        "state_resolution": "STALE_DETECTED",
                        "premise_resistance": "NOT_APPLICABLE",
                        "action_adaptation": "CURRENT_STATE_ALIGNED",
                        "answer": "No, the state changed.",
                    },
                }), encoding="utf-8")
            rows = diagnostic.load_rows_from_raw(selected, raw_dir)
            self.assertEqual(len(rows), 8)
            self.assertTrue(all(row["answer_polarity"] == "NEGATIVE_OLD_STATE" for row in rows))


if __name__ == "__main__":
    unittest.main()
