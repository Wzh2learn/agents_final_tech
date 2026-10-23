from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from stale_retrieval_policy_probe_v3 import hybrid_select, latest_select


ITEM = {
    "timestamps": ["1", "2", "3", "4"],
    "haystack_session": [
        [{"role": "user", "content": "blue sedan"}],
        [{"role": "user", "content": "coffee"}],
        [{"role": "user", "content": "weather"}],
        [{"role": "user", "content": "silver hatchback"}],
    ],
    "relevant_session_index": [0, 3],
}


class RetrievalPolicyProbeTests(unittest.TestCase):
    """Validate transparent recency and hybrid selection."""

    def test_latest_selects_most_recent_sessions(self) -> None:
        self.assertEqual(latest_select(ITEM, "car", 2), [2, 3])

    def test_hybrid_keeps_latest_and_lexical_matches(self) -> None:
        self.assertEqual(
            hybrid_select(ITEM, "blue sedan silver hatchback", 3),
            [3, 0, 1],
        )


if __name__ == "__main__":
    unittest.main()
