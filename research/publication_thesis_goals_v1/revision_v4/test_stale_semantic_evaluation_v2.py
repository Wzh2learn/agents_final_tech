from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from stale_semantic_evaluation_v2 import evaluate_answer


REFERENCE = json.loads(
    (Path(__file__).resolve().parent / "STALE_SEMANTIC_REFERENCE_V2.json").read_text(
        encoding="utf-8"
    )
)["items"]["0683a7ee-1c84-4f83-adb0-c3b04b1ade84"]
ITEM = {
    "haystack_session": [
        [{"role": "user", "content": "I’ve been really enjoying my silver hatchback lately."}]
    ]
}


class SemanticEvaluationTests(unittest.TestCase):
    """Check that the semantic scorer rejects the degenerate proxy."""

    def test_fixed_no_fails_without_current_fact(self) -> None:
        result = evaluate_answer("No", ITEM, REFERENCE, [0])
        self.assertEqual(result["relation"], "UNSPECIFIED")
        self.assertFalse(result["semantic_success"])

    def test_specific_current_fact_passes(self) -> None:
        result = evaluate_answer(
            "No, Riley now drives a silver hatchback rather than the old blue sedan.",
            ITEM,
            REFERENCE,
            [0],
        )
        self.assertEqual(result["relation"], "OLD_STATE_INVALID")
        self.assertTrue(result["semantic_success"])

    def test_uncertain_answer_is_not_success_for_direct_conflict(self) -> None:
        result = evaluate_answer(
            "Not sure; I cannot establish the current state.",
            ITEM,
            REFERENCE,
            [0],
        )
        self.assertEqual(result["relation"], "UNKNOWN_CURRENT")
        self.assertFalse(result["semantic_success"])

    def test_evidence_grounding_requires_selected_source(self) -> None:
        result = evaluate_answer(
            "No, Riley now drives a silver hatchback.",
            ITEM,
            REFERENCE,
            [],
        )
        self.assertFalse(result["semantic_success"])

    def test_old_state_with_internal_negation_is_still_an_affirmation(self) -> None:
        reference = json.loads(
            (Path(__file__).resolve().parent / "STALE_SEMANTIC_REFERENCE_V2.json").read_text(
                encoding="utf-8"
            )
        )["items"]["012f090e-6e02-4751-955d-574745069df3"]
        item = {
            "haystack_session": [[
                {"role": "user", "content": "Everything in my portfolio is tied up."}
            ]]
        }
        result = evaluate_answer(
            "Yes, everything in the investment portfolio is tied up and cannot make withdrawals.",
            item,
            reference,
            [0],
        )
        self.assertEqual(result["relation"], "OLD_STATE_VALID")
        self.assertFalse(result["semantic_success"])

    def test_returned_item_is_current_change_not_old_affirmation(self) -> None:
        reference = json.loads(
            (Path(__file__).resolve().parent / "STALE_SEMANTIC_REFERENCE_V2.json").read_text(
                encoding="utf-8"
            )
        )["items"]["04fea765-0b32-4e8f-b4e9-225901f627b0"]
        item = {
            "haystack_session": [[
                {"role": "user", "content": "I did a drop-off run and the garage is clear."}
            ]]
        }
        result = evaluate_answer(
            "User has returned Mike's pressure washer.",
            item,
            reference,
            [0],
        )
        self.assertEqual(result["relation"], "OLD_STATE_INVALID")
        self.assertTrue(result["semantic_success"])


if __name__ == "__main__":
    unittest.main()
