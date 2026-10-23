from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from prepare_stale_retrieval_confirmation_v3 import EXCLUDED_UIDS, select


class RetrievalConfirmationPreparationTests(unittest.TestCase):
    """Validate deterministic unused balanced selection."""

    def test_selection_excludes_seen_uids_and_balances_types(self) -> None:
        data = []
        for index in range(40):
            kind = "T1" if index < 20 else "T2"
            uid = f"uid-{index:02d}"
            data.append({"uid": uid, "type": kind})
        excluded = {row["uid"] for row in data[:12]}
        globals_excluded = set(EXCLUDED_UIDS)
        self.assertTrue(globals_excluded)
        original = EXCLUDED_UIDS
        try:
            import prepare_stale_retrieval_confirmation_v3 as module
            module.EXCLUDED_UIDS = tuple(sorted(excluded))
            chosen = select(data, per_type=4)
        finally:
            module.EXCLUDED_UIDS = original
        self.assertEqual(len(chosen), 8)
        self.assertEqual(sum(item["type"] == "T1" for item in chosen), 4)
        self.assertEqual(sum(item["type"] == "T2" for item in chosen), 4)
        self.assertTrue(excluded.isdisjoint({item["uid"] for item in chosen}))


if __name__ == "__main__":
    unittest.main()
