import unittest

from research.agent_frontier_portfolio_20261029.build_13f_conflict_tasks import make_instruction


class ControlledTaskTest(unittest.TestCase):
    def test_task_specifies_period_identity_row_and_output_contract(self):
        text = make_instruction("Example Manager", ["com", "adr"])
        for required in ("Example Manager", "30-SEP-2025", "TITLEOFCLASS.lower()", '"com", "adr"', '"count"'):
            if required == '"count"':
                self.assertIn("`count`", text)
            else:
                self.assertIn(required, text)
        self.assertNotIn("2710", text)


if __name__ == "__main__":
    unittest.main()
