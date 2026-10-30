import unittest

from research.paper_e_publication_route_20261028.recheck_lexical_holm import holm, orient_interval, recheck


class HolmRecheckTest(unittest.TestCase):
    def test_step_down_requires_running_maximum(self):
        result = holm([0.04, 0.01, 0.03])
        self.assertEqual(result, [0.06, 0.03, 0.06])

    def test_rejects_wrong_draw_count(self):
        with self.assertRaises(ValueError):
            recheck({"datasets": []}, {"iterations_per_pair": 2000})

    def test_reversing_system_order_reverses_both_interval_endpoints(self):
        self.assertEqual(orient_interval([0.01, 0.06], True), [0.01, 0.06])
        self.assertEqual(orient_interval([0.01, 0.06], False), [-0.06, -0.01])


if __name__ == "__main__":
    unittest.main()
