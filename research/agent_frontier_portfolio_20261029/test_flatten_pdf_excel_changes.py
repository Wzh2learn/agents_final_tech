import unittest

from research.agent_frontier_portfolio_20261029.flatten_pdf_excel_changes import flatten
from research.agent_frontier_portfolio_20261029.score_pdf_excel_transfer import score


class FlattenChangesTest(unittest.TestCase):
    def test_nested_change_converts_without_changing_values(self):
        nested = {"deleted_employees": [], "modified_employees": [{"id": "EMP00001", "changes": [
            {"field": "Salary", "old_value": 2, "new_value": 4}]}]}
        expected = {"deleted_employees": [], "modified_employees": [
            {"id": "EMP00001", "field": "Salary", "old_value": 2, "new_value": 4}]}
        self.assertTrue(score(flatten(nested), expected)["full_contract_pass"])
        self.assertIn("changes", nested["modified_employees"][0])

    def test_extra_nested_fields_are_not_discarded(self):
        nested = {"deleted_employees": [], "modified_employees": [{"id": "EMP00001", "changes": [
            {"field": "Salary", "old_value": 2, "new_value": 4, "note": "unknown"}]}]}
        with self.assertRaises(ValueError):
            flatten(nested)


if __name__ == "__main__":
    unittest.main()
