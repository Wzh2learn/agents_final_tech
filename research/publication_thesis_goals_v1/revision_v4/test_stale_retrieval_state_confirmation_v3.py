from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from stale_retrieval_state_confirmation_v3 import (
    bm25_select,
    retrieval_category,
    semantic_from_hidden_reference,
)


ITEM = {
    "timestamps": ["2025-01-01 00:00", "2025-02-01 00:00"],
    "haystack_session": [
        [{"role": "user", "content": "I drive a blue sedan."}],
        [{"role": "user", "content": "I am enjoying my silver hatchback."}],
    ],
    "relevant_session_index": [0, 1],
}
REFERENCE = {
    "M_old": "I drive a blue sedan.",
    "M_new": "I am enjoying my silver hatchback.",
    "explanation": "The current car changed to a silver hatchback.",
}


class RetrievalStateConfirmationTests(unittest.TestCase):
    """Validate retrieval and hidden-reference semantic screens."""

    def test_bm25_prefers_matching_session(self) -> None:
        selected = bm25_select(ITEM, "silver hatchback", top_k=1)
        self.assertEqual(selected, [1])

    def test_retrieval_categories_are_explicit(self) -> None:
        self.assertEqual(retrieval_category(ITEM, [0, 1]), "BOTH_OLD_AND_NEW")
        self.assertEqual(retrieval_category(ITEM, [0]), "OLD_ONLY")
        self.assertEqual(retrieval_category(ITEM, [1]), "NEW_ONLY")
        self.assertEqual(retrieval_category(ITEM, []), "NEITHER")

    def test_fixed_no_does_not_pass_hidden_reference_semantics(self) -> None:
        result = semantic_from_hidden_reference("No", ITEM, REFERENCE, [0, 1])
        self.assertFalse(result["semantic_success"])

    def test_specific_current_fact_passes(self) -> None:
        result = semantic_from_hidden_reference(
            "No, the current car is a silver hatchback.", ITEM, REFERENCE, [0, 1]
        )
        self.assertTrue(result["semantic_success"])

    def test_old_fact_acceptance_fails(self) -> None:
        result = semantic_from_hidden_reference(
            "Yes, the user still drives a blue sedan.", ITEM, REFERENCE, [0, 1]
        )
        self.assertEqual(result["relation"], "STALE_ACCEPT")
        self.assertFalse(result["semantic_success"])


if __name__ == "__main__":
    unittest.main()
