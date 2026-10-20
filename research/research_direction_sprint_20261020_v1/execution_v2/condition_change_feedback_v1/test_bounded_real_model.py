"""Offline tests for the Tier 1 submission and scoring contract."""

from __future__ import annotations

import unittest

from run_bounded_real_model import (
    ACTOR_PATH,
    REFERENCE_PATH,
    build_cc013_probe,
    load_object,
    parse_submission,
    validate_submission,
)


class BoundedRealModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.actor_doc = load_object(ACTOR_PATH)
        cls.reference_doc = load_object(REFERENCE_PATH)
        cls.references_by_id = {
            item["task_id"]: item for item in cls.reference_doc["references"]
        }

    def test_valid_submission(self) -> None:
        task = self.actor_doc["tasks"][0]
        value = {
            "task_id": task["task_id"],
            "outcome": "reject",
            "evidence_ids": [
                task["observation"]["evidence_inventory"][0]["fact_id"]
            ],
        }
        self.assertEqual(validate_submission(value, task), value)

    def test_wrong_task_rejected(self) -> None:
        task = self.actor_doc["tasks"][0]
        value = {
            "task_id": "CC013:post",
            "outcome": "reject",
            "evidence_ids": [
                task["observation"]["evidence_inventory"][0]["fact_id"]
            ],
        }
        with self.assertRaisesRegex(ValueError, "task_id_mismatch"):
            validate_submission(value, task)

    def test_unknown_evidence_rejected(self) -> None:
        task = self.actor_doc["tasks"][0]
        value = {
            "task_id": task["task_id"],
            "outcome": "reject",
            "evidence_ids": ["CC013:receipt"],
        }
        with self.assertRaisesRegex(ValueError, "unknown_evidence_id"):
            validate_submission(value, task)

    def test_parse_rejects_wrapper(self) -> None:
        task = self.actor_doc["tasks"][0]
        with self.assertRaisesRegex(ValueError, "keys_invalid"):
            parse_submission(
                '{"submission":{"task_id":"x","outcome":"reject","evidence_ids":["x"]}}',
                task,
            )

    def test_cc013_probe(self) -> None:
        probe = build_cc013_probe(self.references_by_id)
        self.assertEqual(probe["status"], "PASS")
        self.assertEqual(len(probe["rows"]), 2)
        self.assertEqual(
            probe["rows"][1]["observed"],
            {"pre": "sufficient", "post": "insufficient"},
        )


if __name__ == "__main__":
    unittest.main()
