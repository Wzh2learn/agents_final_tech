from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from research.agent_frontier_portfolio_20261029.prepare_13f_agent_history import read_count, upstream_verdict


class ActualFeedbackHistoryTest(unittest.TestCase):
    def test_upstream_log_must_show_the_specific_conflict(self):
        log = "assert 2710 == 2451\n1 failed, 1 passed"
        self.assertEqual(upstream_verdict(log, 2710, 2451), "rejected")
        with self.assertRaises(ValueError):
            upstream_verdict("1 failed, 1 passed", 2710, 2451)

    def test_source_count_must_be_strict_integer(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "count.json"
            path.write_text('{"count": true}')
            with self.assertRaises(ValueError):
                read_count(path)


if __name__ == "__main__":
    unittest.main()
