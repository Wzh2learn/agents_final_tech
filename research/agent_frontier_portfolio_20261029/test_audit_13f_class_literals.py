import unittest

from research.agent_frontier_portfolio_20261029.audit_13f_class_literals import class_literals


class AdjacentLiteralAuditTest(unittest.TestCase):
    def test_adjacent_literals_compile_to_one_runtime_value(self):
        source = "cat > /tmp/solver.py << 'PYTHON_SCRIPT'\ntitle_class_of_stocks = ['com', 'adr' 'cl a']\nPYTHON_SCRIPT\n"
        runtime, separated = class_literals(source)
        self.assertEqual(runtime, ["com", "adrcl a"])
        self.assertEqual(separated, ["com", "adr", "cl a"])

    def test_missing_heredoc_is_rejected(self):
        with self.assertRaises(ValueError):
            class_literals("title_class_of_stocks = []")


if __name__ == "__main__":
    unittest.main()
