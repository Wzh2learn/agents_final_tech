import unittest

from . import FUTURE_EVALUATION_MATCHER as MATCHER


class FutureMatcherRegressionTests(unittest.TestCase):
    def test_r7_thousands_separator_is_digit_adjacent_only(self):
        self.assertTrue(
            MATCHER.match_full_semantic_answer("1,496", 1496, "arithmetic", "", False)[0]
        )
        for candidate in ("1, 496", "1 496", "1 ,496"):
            with self.subTest(candidate=candidate):
                self.assertFalse(
                    MATCHER.match_full_semantic_answer(
                        candidate, 1496, "arithmetic", "", False
                    )[0]
                )


    def test_r8_count_rejects_negative_integers(self):
        self.assertFalse(
            MATCHER.match_full_semantic_answer("-5", -5, "count", "", False)[0]
        )
        self.assertFalse(
            MATCHER.match_full_semantic_answer("(5)", -5, "count", "", False)[0]
        )
        self.assertTrue(MATCHER.match_full_semantic_answer("5", 5, "count", "", False)[0])


    def test_classifier_counterexamples_require_visible_role_context(self):
        self.assertFalse(
            MATCHER.numeric_role_match(
                "How many units were shipped?", "table quantity: 42", 17
            )
        )
        self.assertFalse(
            MATCHER.numeric_role_match(
                "How many units were shipped?", "table row: 42", 42
            )
        )
        self.assertTrue(
            MATCHER.numeric_role_match(
                "How many units were shipped?", "paragraph: units shipped: 42", 42
            )
        )


if __name__ == "__main__":
    unittest.main()
