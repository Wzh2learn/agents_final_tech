from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from g2_retrieval_policy_probe_v5 import (
    attribute_recency_top5,
    category,
    user_change_top5,
)


ITEM = {
    "relevant_session_index": [0, 3],
    "haystack_session": [
        [{"role": "user", "content": "I drive the blue sedan every day."}],
        [{"role": "user", "content": "The weather is rainy."}],
        [{"role": "assistant", "content": "You could consider driving a hatchback."}],
        [{"role": "user", "content": "I am enjoying the silver hatchback now."}],
    ],
}


class G2RetrievalPolicyTests(unittest.TestCase):
    """Validate transparent retrieval behavior and category labels."""

    def test_categories_distinguish_old_and_new_hits(self) -> None:
        self.assertEqual(category(ITEM, [0, 3]), "BOTH_OLD_AND_NEW")
        self.assertEqual(category(ITEM, [0]), "OLD_ONLY")
        self.assertEqual(category(ITEM, [3]), "NEW_ONLY")
        self.assertEqual(category(ITEM, [1]), "NEITHER")

    def test_user_change_policy_prefers_user_evidence(self) -> None:
        selected = user_change_top5(ITEM, "blue sedan silver hatchback", top_k=2)
        self.assertNotEqual(selected, [2])
        self.assertTrue(set(selected).issubset({0, 1, 3}))

    def test_attribute_recency_prefers_late_matching_user_session(self) -> None:
        selected = attribute_recency_top5(ITEM, "blue sedan", top_k=1)
        self.assertEqual(selected, [0])


if __name__ == "__main__":
    unittest.main()
