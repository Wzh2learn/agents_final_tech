from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


OUTPUT_DIR = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(OUTPUT_DIR))

import candidate_b_reference_checker_v1 as checker


class CandidateBReferenceCheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tasks = json.loads(
            (OUTPUT_DIR / "CANDIDATE_B_TASKS_DRAFT.json").read_text(
                encoding="utf-8"
            )
        )["tasks"]
        cls.hidden = json.loads(
            (OUTPUT_DIR / "HIDDEN_REFERENCE_MANIFEST.json").read_text(
                encoding="utf-8"
            )
        )["references"]
        cls.raw = checker.load_raw_records(ROOT)

    def fixture(self):
        actor_task = copy.deepcopy(self.tasks[0])
        hidden = copy.deepcopy(self.hidden[0])
        table = copy.deepcopy(self.raw[hidden["source_uid"]]["table"])
        submission = checker.correct_submission(hidden)
        return actor_task, hidden, table, submission

    def test_valid_reference_recomputes_deterministically(self) -> None:
        actor_task, hidden, table, submission = self.fixture()
        first = checker.validate_submission(
            actor_task, hidden, submission, table
        )
        second = checker.validate_submission(
            actor_task, hidden, submission, table
        )
        self.assertEqual(first, second)
        self.assertTrue(first["valid"])

    def test_wrong_row_is_rejected(self) -> None:
        actor_task, hidden, table, submission = self.fixture()
        submission["row_index"] += 1
        with self.assertRaisesRegex(
            checker.ReferenceCheckError, "WRONG_ROW"
        ):
            checker.validate_submission(
                actor_task, hidden, submission, table
            )

    def test_wrong_period_is_rejected(self) -> None:
        actor_task, hidden, table, submission = self.fixture()
        submission["late_period_index"] = submission["early_period_index"]
        with self.assertRaisesRegex(
            checker.ReferenceCheckError, "WRONG_PERIOD"
        ):
            checker.validate_submission(
                actor_task, hidden, submission, table
            )

    def test_reversed_sign_is_rejected(self) -> None:
        actor_task, hidden, table, submission = self.fixture()
        submission["sign_convention"] = "early_minus_late"
        submission["answer"] = -submission["answer"]
        submission["tool_result"] = -submission["tool_result"]
        with self.assertRaisesRegex(
            checker.ReferenceCheckError, "REVERSED_SIGN"
        ):
            checker.validate_submission(
                actor_task, hidden, submission, table
            )

    def test_wrong_unit_is_rejected(self) -> None:
        actor_task, hidden, table, submission = self.fixture()
        submission["target_unit"] = (
            "EUR" if submission["target_unit"] != "EUR" else "USD"
        )
        with self.assertRaisesRegex(
            checker.ReferenceCheckError, "WRONG_UNIT_OR_SCALE"
        ):
            checker.validate_submission(
                actor_task, hidden, submission, table
            )

    def test_missing_cell_is_rejected(self) -> None:
        actor_task, hidden, table, submission = self.fixture()
        del submission["selected_values"]["late"]
        with self.assertRaisesRegex(
            checker.ReferenceCheckError, "MISSING_CELLS"
        ):
            checker.validate_submission(
                actor_task, hidden, submission, table
            )

    def test_ambiguous_row_label_is_rejected(self) -> None:
        actor_task, hidden, table, submission = self.fixture()
        row_index = hidden["coordinates"]["row_index"]
        duplicate_index = next(
            index
            for index in range(1, len(table))
            if index != row_index and table[index][0]
        )
        table[duplicate_index][0] = table[row_index][0]
        hidden["frozen_table_sha256"] = checker.sha256_bytes(
            checker.canonical_bytes(table)
        )
        with self.assertRaisesRegex(
            checker.ReferenceCheckError, "AMBIGUOUS_ROW_LABEL"
        ):
            checker.validate_submission(
                actor_task, hidden, submission, table
            )

    def test_hidden_field_leakage_is_rejected(self) -> None:
        actor_task, hidden, table, submission = self.fixture()
        actor_task["hidden_reference"] = hidden
        with self.assertRaisesRegex(
            checker.ReferenceCheckError, "HIDDEN_FIELD_LEAKAGE"
        ):
            checker.validate_submission(
                actor_task, hidden, submission, table
            )

    def test_answer_tool_inconsistency_is_rejected(self) -> None:
        actor_task, hidden, table, submission = self.fixture()
        submission["tool_result"] = submission["answer"] + 1
        with self.assertRaisesRegex(
            checker.ReferenceCheckError, "ANSWER_TOOL_INCONSISTENCY"
        ):
            checker.validate_submission(
                actor_task, hidden, submission, table
            )


if __name__ == "__main__":
    unittest.main()
