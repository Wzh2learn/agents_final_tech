import unittest

from research.agent_frontier_portfolio_20261029.pdf_excel_exact_baseline import candidate_changes


class ExactAnchorBaselineTest(unittest.TestCase):
    def test_unchanged_full_row_produces_no_edit(self):
        row = ("EMP00001", "Jo", "Li", "QA", "QA Manager", 112000, 7, "San Diego", 4.3)
        self.assertEqual(candidate_changes("EMP00001 Jo Li QA QA Manager 112,000 7 San Diego 4.3", row), [])

    def test_single_changed_multiword_field_preserves_old_and_new(self):
        row = ("EMP00001", "Jo", "Li", "QA", "Test Engineer", 112000, 7, "San Diego", 4.3)
        result = candidate_changes("EMP00001 Jo Li QA QA Manager 112,000 7 San Diego 4.3", row)
        self.assertEqual(result, [{"id": "EMP00001", "field": "Position", "old_value": "QA Manager", "new_value": "Test Engineer"}])

    def test_changed_salary_is_numeric(self):
        row = ("EMP00001", "Jo", "Li", "QA", "QA Manager", 112000, 7, "San Diego", 4.3)
        result = candidate_changes("EMP00001 Jo Li QA QA Manager 99,000 7 San Diego 4.3", row)
        self.assertEqual(result, [{"id": "EMP00001", "field": "Salary", "old_value": 99000, "new_value": 112000}])


if __name__ == "__main__":
    unittest.main()
