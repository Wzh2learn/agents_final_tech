import unittest

from research.agent_frontier_portfolio_20261029.prepare_13f_feedback_controls import prepare


class FeedbackControlsTest(unittest.TestCase):
    def test_only_target_answer_changes(self):
        source = {"q1_answer": 3, "q2_answer": 7, "q3_answer": ["A"], "q4_answer": ["B"]}
        original, alternative = prepare(source, 8)
        self.assertEqual(original, source)
        self.assertEqual(alternative["q2_answer"], 8)
        self.assertEqual(alternative["q3_answer"], source["q3_answer"])
        self.assertEqual(source["q2_answer"], 7)

    def test_rejects_no_difference(self):
        with self.assertRaises(ValueError):
            prepare({"q2_answer": 1}, 1)


if __name__ == "__main__":
    unittest.main()
