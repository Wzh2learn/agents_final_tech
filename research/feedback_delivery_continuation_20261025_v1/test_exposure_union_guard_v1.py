from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from exposure_union_guard_v1 import (
    ExposureOverlapError,
    assert_unexposed_for_confirmation,
    check_exposure,
)


class ExposureUnionGuardTests(unittest.TestCase):
    def test_confirmation_blocks_overlap_before_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "seen.jsonl"
            source.write_text(
                json.dumps({"task_id": "T1", "table_uid": "TABLE1"}) + "\n",
                encoding="utf-8",
            )
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps({"sources": [{"path": str(source), "role": "seen"}]}),
                encoding="utf-8",
            )
            with self.assertRaises(ExposureOverlapError):
                assert_unexposed_for_confirmation(["T1"], [], manifest)
            receipt = check_exposure(["T2"], ["TABLE2"], manifest, allow_development_exposure=False)
            self.assertEqual(receipt["overlap_count"], 0)

    def test_development_replay_can_record_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "seen.jsonl"
            source.write_text(json.dumps({"source_task_id": "T1"}) + "\n", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps({"sources": [{"path": str(source), "role": "seen"}]}),
                encoding="utf-8",
            )
            receipt = check_exposure(["T1::original"], [], manifest, allow_development_exposure=True)
            self.assertEqual(receipt["overlap_count"], 1)


if __name__ == "__main__":
    unittest.main()
