from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from valentine_selective_mapping_probe import apply_threshold, metrics


def test_low_or_missing_confidence_abstains_only_map_to() -> None:
    row = {
        "sample_id": "s1",
        "pair_id": "p1",
        "gold_action": "map_to",
        "gold_target": "t",
        "predicted_action": "map_to",
        "predicted_target": "t",
    }
    assert apply_threshold(row, 0.5, 0.8)["predicted_action"] == "ABSTAIN"
    assert apply_threshold(row, None, 0.8)["predicted_action"] == "ABSTAIN"
    assert apply_threshold(row, 0.9, 0.8)["predicted_action"] == "map_to"
    non_map = {**row, "predicted_action": "hold", "predicted_target": None}
    assert apply_threshold(non_map, None, 0.8)["predicted_action"] == "hold"


def test_metrics_separate_map_risk_from_row_coverage() -> None:
    rows = [
        {
            "sample_id": "correct",
            "pair_id": "p",
            "gold_action": "map_to",
            "gold_target": "t",
            "predicted_action": "map_to",
            "predicted_target": "t",
            "abstained": False,
        },
        {
            "sample_id": "harm",
            "pair_id": "p",
            "gold_action": "hold",
            "gold_target": None,
            "predicted_action": "map_to",
            "predicted_target": "wrong",
            "abstained": False,
        },
        {
            "sample_id": "abstain",
            "pair_id": "p",
            "gold_action": "map_to",
            "gold_target": "t",
            "predicted_action": "ABSTAIN",
            "predicted_target": None,
            "abstained": True,
        },
    ]
    result = metrics(rows)
    assert result["map_to_risk"] == 0.5
    assert result["correct_map_coverage_all_rows"] == 1 / 3
    assert result["target_exact_gold_map_to"] == 0.5
