import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from research.agent_frontier_portfolio_20261029.summarize_13f_feedback_controls import inspect


class FeedbackControlSummaryTest(unittest.TestCase):
    def test_detects_rejected_counterfactual_and_rejects_wrong_fixture(self):
        audit = {"tasks": {"task": {"expected_q2": 4, "separate_literals_count": 5}}}
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for arm, val, log in (("reference", 4, "2 passed"),
                                  ("separated_literals", 5, "assert 5 == 4\n1 failed, 1 passed")):
                case = root / "task" / arm
                case.mkdir(parents=True)
                (case / "verifier.log").write_text(log)
                (case / "answers.json").write_text(json.dumps({"q2_answer": val}))
            self.assertFalse(inspect(root, audit)["tasks"]["task"]["separated_literals"]["verifier_pass"])
            (root / "task" / "separated_literals" / "answers.json").write_text('{"q2_answer": 4}')
            with self.assertRaises(ValueError):
                inspect(root, audit)


if __name__ == "__main__":
    unittest.main()
