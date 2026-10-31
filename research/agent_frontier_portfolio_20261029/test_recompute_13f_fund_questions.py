import unittest

from research.agent_frontier_portfolio_20261029.recompute_13f_fund_questions import select_unique


class FundQuestionTest(unittest.TestCase):
    def test_selected_manager_requires_matching_period_and_unique_filing(self):
        covers = [{"ACCESSION_NUMBER": "a", "FILINGMANAGER_NAME": "Example Management"},
                  {"ACCESSION_NUMBER": "b", "FILINGMANAGER_NAME": "Example Management"}]
        periods = {"a": "31-MAR-2025", "b": "30-SEP-2025"}
        self.assertEqual(select_unique(covers, periods, "example management")["ACCESSION_NUMBER"], "b")
        periods["a"] = "30-SEP-2025"
        with self.assertRaises(ValueError):
            select_unique(covers, periods, "example management")


if __name__ == "__main__":
    unittest.main()
