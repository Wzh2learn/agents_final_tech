from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research/stage_e_multileaf_20261010"))

import run_multileaf_formal as formal  # noqa: E402


def _synthetic_localization_arrays() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = []
    y = []
    clusters = []
    patterns = {"M": [1.0, 0.0, 0.0], "R": [0.0, 1.0, 0.0], "N": [0.0, 0.0, 1.0]}
    for stage in formal.CLASSES:
        for cluster_index in range(2):
            cluster = f"{stage}{cluster_index}"
            for _ in range(3):
                x.append(patterns[stage])
                y.append(stage)
                clusters.append(cluster)
    return np.asarray(x), np.asarray(y, dtype=object), np.asarray(clusters, dtype=object)


def test_predict_loco_preserves_row_order_and_separates_frozen_signatures() -> None:
    x, y, clusters = _synthetic_localization_arrays()
    predictions, margins = formal.predict_loco(x, y, clusters)
    assert predictions.shape == y.shape
    assert margins.shape == y.shape
    assert np.array_equal(predictions, y)
    assert bool(np.all(margins >= 0))


def test_distance_tie_is_scored_as_tie_not_rescued_by_class_order() -> None:
    x = np.zeros((9, 3), dtype=float)
    y = np.asarray(["M", "M", "M", "R", "R", "R", "N", "N", "N"], dtype=object)
    clusters = np.asarray([f"c{index // 3}-{index % 3}" for index in range(9)], dtype=object)
    predictions, margins = formal.predict_loco(x, y, clusters)
    assert np.all(predictions == formal.TIE_LABEL)
    assert np.all(margins == 0.0)
    assert formal.accuracy(y, predictions) == 0.0


def test_macro_f1_uses_all_three_classes() -> None:
    y = np.asarray(["M", "R", "N"], dtype=object)
    perfect = np.asarray(["M", "R", "N"], dtype=object)
    all_m = np.asarray(["M", "M", "M"], dtype=object)
    assert formal.macro_f1(y, perfect) == 1.0
    assert abs(formal.macro_f1(y, all_m) - formal.MAJORITY_MACRO_F1) < 1e-12
