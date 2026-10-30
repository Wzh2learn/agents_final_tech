import unittest

from research.agent_frontier_portfolio_20261029.qualify_pdf_excel_reference import (
    compare_reference, compare_tables, table_map,
)


class PdfExcelQualificationTest(unittest.TestCase):
    def test_duplicate_ids_are_not_silently_overwritten(self):
        with self.assertRaises(ValueError):
            table_map(("ID", "Salary"), [("EMP00001", 1), ("EMP00001", 2)])

    def test_reference_checks_deleted_and_field_values(self):
        old = {"EMP00001": {"Salary": 2, "Dept": "A"}, "EMP00002": {"Salary": 3, "Dept": "B"}}
        new = {"EMP00001": {"Salary": 4, "Dept": "A"}}
        deleted, added, changes = compare_tables(old, new)
        self.assertEqual(added, set())
        expected = {"deleted_employees": ["EMP00002"], "modified_employees": [
            {"id": "EMP00001", "field": "Salary", "old_value": 2, "new_value": 5}]}
        result = compare_reference(deleted, changes, expected)
        self.assertEqual(result["deleted_missing_in_reference"], 0)
        self.assertEqual(result["change_value_mismatches"], 1)

    def test_duplicate_changes_in_reference_are_rejected(self):
        row = {"id": "EMP00001", "field": "Salary", "old_value": 2, "new_value": 4}
        with self.assertRaises(ValueError):
            compare_reference(set(), {}, {"deleted_employees": [], "modified_employees": [row, row]})


if __name__ == "__main__":
    unittest.main()
