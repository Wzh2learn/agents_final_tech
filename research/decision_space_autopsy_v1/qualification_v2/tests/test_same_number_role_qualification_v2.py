from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "build_same_number_role_tasks.py"
SPEC = importlib.util.spec_from_file_location("build_same_number_role_tasks", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


UNIT = {"unit": "GBP", "scale": "million"}


class SameNumberRoleQualificationTests(unittest.TestCase):
    def test_row_index_only_difference_is_unscorable(self) -> None:
        target = {
            "row_label": "Adjusted operating costs1",
            "period_label": "2019",
            "row_index": 4,
            "period_index": 1,
        }
        candidate = {
            "row_label": "Adjusted operating costs1",
            "period_label": "2019",
            "row_index": 9,
            "period_index": 1,
        }
        result = MODULE.qualify_role_pair(target, candidate, "cell_value", UNIT)
        self.assertEqual(result["status"], "UNSCORABLE_FOR_REFERENCE")
        self.assertEqual(result["visible_difference_fields"], [])
        self.assertIn("row_index", result["hidden_difference_fields"])

    def test_visible_row_difference_qualifies_wrong_role(self) -> None:
        target = {
            "row_label": "Cash and cash equivalents",
            "period_label": "2019",
            "row_index": 2,
        }
        candidate = {
            "row_label": "Cash including joint ventures",
            "period_label": "2019",
            "row_index": 8,
        }
        result = MODULE.qualify_role_pair(target, candidate, "cell_value", UNIT)
        self.assertEqual(result["status"], "QUALIFIED_VISIBLE_ROLE_DIFFERENCE")
        self.assertEqual(result["visible_difference_fields"], ["row_label"])

    def test_visible_period_difference_qualifies_wrong_role(self) -> None:
        target = {
            "row_label": "Deferred income",
            "period_label": "2018",
            "row_index": 10,
        }
        candidate = {
            "row_label": "Deferred income",
            "period_label": "2019",
            "row_index": 10,
        }
        result = MODULE.qualify_role_pair(target, candidate, "cell_value", UNIT)
        self.assertEqual(result["status"], "QUALIFIED_VISIBLE_ROLE_DIFFERENCE")
        self.assertEqual(result["visible_difference_fields"], ["period_label"])

    def test_visible_unit_difference_qualifies_wrong_role(self) -> None:
        target = {
            "row_label": "Revenue",
            "period_label": "2019",
            "unit": "GBP",
            "scale": "million",
        }
        candidate = {
            "row_label": "Revenue",
            "period_label": "2019",
            "unit": "EUR",
            "scale": "million",
        }
        result = MODULE.qualify_role_pair(
            target,
            candidate,
            "cell_value",
            None,
        )
        self.assertEqual(result["status"], "QUALIFIED_VISIBLE_ROLE_DIFFERENCE")
        self.assertEqual(result["visible_difference_fields"], ["unit"])

    def test_case_selection_skips_row_index_only_case(self) -> None:
        cases = [
            {
                "cluster_id": "cluster_1582",
                "source_uid": "source",
                "normalized_value": "275.7",
                "roles": [
                    {"row_label": "Same row", "period_label": "2019", "row_index": 4},
                    {"row_label": "Same row", "period_label": "2019", "row_index": 9},
                ],
            },
            {
                "cluster_id": "cluster_1582",
                "source_uid": "source",
                "normalized_value": "70.5",
                "roles": [
                    {"row_label": "Same row", "period_label": "2019", "row_index": 6},
                    {"row_label": "Same row", "period_label": "2018", "row_index": 6},
                ],
            },
        ]
        selected, qualifications = MODULE.choose_case(
            cases,
            "cluster_1582",
            lambda _source_uid: UNIT,
        )
        self.assertIsNotNone(selected)
        self.assertEqual(selected["normalized_value"], "70.5")
        self.assertEqual(len(qualifications), 2)
        self.assertEqual(qualifications[0]["status"], "UNSCORABLE_FOR_REFERENCE")
        self.assertEqual(
            qualifications[1]["status"],
            "QUALIFIED_VISIBLE_ROLE_DIFFERENCE",
        )

    def test_make_task_records_visible_qualification(self) -> None:
        class Checker:
            @staticmethod
            def infer_unit_context(_header):
                return UNIT

        case = {
            "cluster_id": "cluster_test",
            "source_uid": "source",
            "normalized_value": "12.0",
            "roles": [
                {"row_label": "Revenue", "period_label": "2019", "row_index": 1},
                {"row_label": "Costs", "period_label": "2019", "row_index": 2},
            ],
        }
        record = {
            "split": "train",
            "index": 0,
            "table": [["$ million", "2019"], ["Revenue", "12"], ["Costs", "12"]],
        }
        actor, hidden = MODULE.make_task(
            case,
            record,
            Checker,
            "development",
            2,
            False,
        )
        self.assertEqual(
            hidden["qualification"]["status"],
            "QUALIFIED_VISIBLE_ROLE_DIFFERENCE",
        )
        self.assertEqual(actor["requested_role"]["unit"], "GBP")
        self.assertEqual(actor["candidate_citation"]["unit"], "GBP")


if __name__ == "__main__":
    unittest.main()
