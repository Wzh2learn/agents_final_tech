import unittest

try:
    from .check_prefix_full_trace import compare
except ImportError:
    from check_prefix_full_trace import compare


class FullTraceCheckTest(unittest.TestCase):
    def test_match_and_mismatch(self):
        record = {"idx": 0, "prompt_tokens": 2, "hit_tokens": 1}
        result = {"per_request": [record], "total_requests": 1, "total_prompt_tokens": 2,
                  "total_hit_tokens": 1, "final_cache_blocks": 1, "overall_hit_rate": 0.5}
        self.assertEqual(compare(result, result)["mismatches_by_field"]["hit_tokens"], 0)
        altered = dict(result, per_request=[dict(record, hit_tokens=3)])
        check = compare(altered, result)
        self.assertEqual(check["mismatches_by_field"]["hit_tokens"], 1)
        self.assertEqual(check["hit_outside_prompt_bounds"], 1)

    def test_length_mismatch(self):
        with self.assertRaises(ValueError):
            compare({"per_request": []}, {"per_request": [{}]})


if __name__ == "__main__":
    unittest.main()
