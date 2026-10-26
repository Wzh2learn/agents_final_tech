from pathlib import Path
import sys

MODULE_PATH = Path(__file__).with_name("FUTURE_EVALUATION_MATCHER.py")
sys.path.insert(0, str(MODULE_PATH.parent))
import FUTURE_EVALUATION_MATCHER as MATCHER


def test_r7_thousands_separator_is_digit_adjacent_only():
    assert MATCHER.match_full_semantic_answer("1,496", 1496, "arithmetic", "", False)[0]
    assert not MATCHER.match_full_semantic_answer("1, 496", 1496, "arithmetic", "", False)[0]


def test_r8_count_rejects_negative_integers():
    assert not MATCHER.match_full_semantic_answer("-5", -5, "count", "", False)[0]
    assert not MATCHER.match_full_semantic_answer("(5)", -5, "count", "", False)[0]
    assert MATCHER.match_full_semantic_answer("5", 5, "count", "", False)[0]


def test_classifier_counterexamples_require_visible_role_context():
    assert not MATCHER.numeric_role_match(
        "How many units were shipped?", "table quantity: 42", 17
    )
    assert not MATCHER.numeric_role_match(
        "How many units were shipped?", "table row: 42", 42
    )
    assert MATCHER.numeric_role_match(
        "How many units were shipped?", "paragraph: units shipped: 42", 42
    )
