from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from G3_VISIBLE_FEATURE_PREDICTION_V5 import cost_matched_threshold, prediction_metrics
except ModuleNotFoundError as error:
    if error.name == "sklearn":
        raise unittest.SkipTest("scikit-learn is unavailable in this interpreter")
    raise


class G3VisibleFeaturePredictionTests(unittest.TestCase):
    """Validate cost matching and target metrics."""

    def test_threshold_limits_expansion_rate(self) -> None:
        scores = [0.1, 0.2, 0.3, 0.4]
        threshold = cost_matched_threshold(scores, rate=0.25)
        self.assertEqual(threshold, 0.4)

    def test_metrics_use_hidden_gain_target(self) -> None:
        result = prediction_metrics(
            useful=[True, False, True, False],
            predicted=[True, True, False, False],
            costs=[10, 10, 0, 0],
        )
        self.assertEqual(result["true_positive"], 1)
        self.assertEqual(result["false_positive"], 1)
        self.assertEqual(result["expansion_count"], 2)


if __name__ == "__main__":
    unittest.main()
