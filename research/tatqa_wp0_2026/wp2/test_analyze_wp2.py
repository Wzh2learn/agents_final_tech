#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from analyze_wp2 import analyze_records


FIXTURE_PATH = Path(__file__).resolve().parent / (
    "fixtures/synthetic_wp2_analysis.json"
)


class AnalyzeWp2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_origin_level_paired_comparisons_and_costs(self) -> None:
        result = analyze_records(
            copy.deepcopy(self.payload),
            bootstrap_replicates=200,
            seed="synthetic-test",
        )
        self.assertEqual(result["input_counts"], {
            "records": 16,
            "origins": 2,
            "items": 2,
        })
        self.assertEqual(
            result["arms"]["B"]["outcome_counts"]["unknown"], 1
        )
        self.assertEqual(
            result["arms"]["E"]["outcome_counts"]["regressed"], 1
        )
        self.assertAlmostEqual(
            result["comparisons"]["E-B"]["mean_difference_pp"],
            0.0,
        )
        self.assertAlmostEqual(
            result["comparisons"]["E-C"]["mean_difference_pp"],
            0.0,
        )
        self.assertAlmostEqual(
            result["comparisons"]["E-S"]["mean_difference_pp"],
            0.0,
        )
        self.assertAlmostEqual(
            result["comparisons"]["C-B"]["mean_difference_pp"],
            0.0,
        )
        self.assertEqual(
            len(
                result["comparisons"]["E-B"][
                    "origin_differences"
                ]
            ),
            2,
        )
        self.assertEqual(result["cost_by_arm"]["B"]["model_calls"], 4)
        self.assertEqual(result["cost_by_arm"]["E"]["model_calls"], 4)
        self.assertEqual(
            result["cost_by_arm"]["E"]["prompt_tokens"], 620
        )

    def test_analysis_is_deterministic(self) -> None:
        kwargs = {
            "bootstrap_replicates": 200,
            "seed": "deterministic-test",
        }
        first = analyze_records(copy.deepcopy(self.payload), **kwargs)
        second = analyze_records(copy.deepcopy(self.payload), **kwargs)
        self.assertEqual(
            json.dumps(first, sort_keys=True),
            json.dumps(second, sort_keys=True),
        )

    def test_duplicate_episode_is_rejected(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["records"].append(copy.deepcopy(payload["records"][0]))
        with self.assertRaisesRegex(
            ValueError, "duplicate episode key"
        ):
            analyze_records(payload)

    def test_fractional_call_count_is_rejected(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["records"][0]["model_calls"] = 1.5
        with self.assertRaisesRegex(
            ValueError, "model_calls must be an integer"
        ):
            analyze_records(payload)


if __name__ == "__main__":
    unittest.main()
