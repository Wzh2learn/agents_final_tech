import unittest

from research.agent_frontier_portfolio_20261029.qualify_13f_periods import summarize_rows


class Form13fPeriodsTest(unittest.TestCase):
    def test_reports_out_of_period_and_unjoined_matches(self):
        submissions = [{"ACCESSION_NUMBER": "a", "PERIODOFREPORT": "30-JUN-2025"},
                       {"ACCESSION_NUMBER": "b", "PERIODOFREPORT": "31-MAR-2025"}]
        covers = [{"ACCESSION_NUMBER": "a", "FILINGMANAGER_NAME": "Bridgewater Associates", "ISAMENDMENT": "N"},
                  {"ACCESSION_NUMBER": "b", "FILINGMANAGER_NAME": "Bridgewater Associates", "ISAMENDMENT": "Y"},
                  {"ACCESSION_NUMBER": "missing", "FILINGMANAGER_NAME": "Bridgewater Associates", "ISAMENDMENT": ""}]
        result = summarize_rows(submissions, covers, "30-JUN-2025")
        self.assertEqual((result["target_period_rows"], result["other_or_missing_period_rows"]), (1, 1))
        manager = result["manager_substring_checks"]["bridgewater associates"]
        self.assertEqual((manager["substring_matches"], manager["target_period_matches"]), (3, 1))
        self.assertEqual(len(manager["name_period_counts"]), 3)
        self.assertEqual(result["cover_rows_without_submission"], 1)


if __name__ == "__main__":
    unittest.main()
