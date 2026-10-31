import unittest

from research.agent_frontier_portfolio_20261029.run_13f_feedback_agent import history_message


class HistoryMessageTest(unittest.TestCase):
    def test_conditions_show_actual_feedback_but_not_target_answer(self):
        h = {"previous_count": 2710, "contract_checker": {"verdict": "accepted", "expected": 2710},
             "upstream_checker": {"verdict": "rejected", "expected": 2451}}
        self.assertEqual(history_message("no_history", h), "")
        self.assertIn("2451", history_message("history_upstream_feedback", h))
        self.assertIn("2710", history_message("history_contract_feedback", h))
        self.assertNotIn("938", history_message("history_conflict_check", h))

    def test_rejects_missing_or_boolean_count(self):
        with self.assertRaises(ValueError):
            history_message("history_only", {"previous_count": True})


if __name__ == "__main__":
    unittest.main()
