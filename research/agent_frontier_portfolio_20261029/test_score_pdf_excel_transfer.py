import unittest

from research.agent_frontier_portfolio_20261029.score_pdf_excel_transfer import score


class PdfExcelScoreTest(unittest.TestCase):
    def setUp(self):
        self.expected = {"deleted_employees": ["EMP00002"], "modified_employees": [
            {"id": "EMP00001", "field": "Salary", "old_value": 2, "new_value": 4}]}

    def test_identical_reference_passes_complete_contract(self):
        result = score(self.expected, self.expected)
        self.assertTrue(result["full_contract_pass"])
        self.assertEqual(result["change_expected_unique_ids"], 1)

    def test_duplicate_or_string_numeric_does_not_pass(self):
        report = {"deleted_employees": ["EMP00002", "EMP00002"], "modified_employees": [
            {"id": "EMP00001", "field": "Salary", "old_value": "2", "new_value": 4}]}
        result = score(report, self.expected)
        self.assertFalse(result["full_contract_pass"])
        self.assertEqual((result["duplicate_entries"], result["invalid_value_types"]), (1, 1))

    def test_matching_ids_do_not_hide_wrong_change_values(self):
        report = {"deleted_employees": ["EMP00002"], "modified_employees": [
            {"id": "EMP00001", "field": "Salary", "old_value": 2, "new_value": 5}]}
        result = score(report, self.expected)
        self.assertEqual((result["change_key_true_positive"], result["change_values_and_types_correct"]), (1, 0))
        self.assertFalse(result["full_contract_pass"])

    def test_invalid_modified_entry_preserves_valid_deletion_results(self):
        report = {"deleted_employees": ["EMP00002"], "modified_employees": [{"bad": "entry"}]}
        result = score(report, self.expected)
        self.assertEqual(result["status"], "SCORED_WITH_INVALID_ENTRIES")
        self.assertEqual((result["deleted_true_positive"], result["invalid_modified_entries"]), (1, 1))
        self.assertFalse(result["full_contract_pass"])


if __name__ == "__main__":
    unittest.main()
