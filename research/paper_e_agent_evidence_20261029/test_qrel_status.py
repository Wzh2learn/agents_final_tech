import tempfile
import unittest
from pathlib import Path
from qrel_status import load_qrels, status


class QrelStatusTest(unittest.TestCase):
    def test_positive_zero_negative_and_absent(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'qrels.tsv'
            path.write_text('query-id\tcorpus-id\tscore\nq\tp\t2\nq\tz\t0\nq\tn\t-1\n', encoding='utf-8')
            values = load_qrels(path)
            self.assertEqual(status(values, 'q', 'p'), 'QRELS_POSITIVE')
            self.assertEqual(status(values, 'q', 'z'), 'QRELS_NONPOSITIVE')
            self.assertEqual(status(values, 'q', 'n'), 'QRELS_NONPOSITIVE')
            self.assertEqual(status(values, 'q', 'missing'), 'UNJUDGED')
            self.assertEqual(status(values, 'missing', 'p'), 'UNJUDGED')


if __name__ == '__main__':
    unittest.main()
