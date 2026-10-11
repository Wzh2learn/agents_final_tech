#!/usr/bin/env python3
"""Label-blind, order-invariant feature extraction for one unordered state pair."""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any


LEAF_ORDER = (
    "parse.doc.ok",
    "parse.doc.throughput",
    "parse.table.regression",
    "parse.field.hit_rate",
    "parse.reconcile.equations",
    "qa.retrieval.source_required",
    "qa.faithfulness.judge",
    "qa.numeric.exact",
    "qa.numeric.number_grounding",
    "qa.citation.judge",
    "qa.refusal.judge",
    "qa.refusal.deterministic",
)

DIRECT_LEAVES = (
    "parse.field.hit_rate",
    "qa.retrieval.source_required",
    "parse.reconcile.equations",
)

NON_DIRECT_LEAVES = tuple(leaf for leaf in LEAF_ORDER if leaf not in DIRECT_LEAVES)

COMPONENTS = (
    "presence_min",
    "presence_max",
    "presence_xor",
    "score_min",
    "score_max",
    "score_abs_diff",
    "score_sum",
)

SCORE_SCALE = 10.0


def _state(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("each pair member must be a mapping")
    unknown = set(value) - set(LEAF_ORDER)
    if unknown:
        raise ValueError(f"unknown observation keys: {sorted(unknown)}")
    return value


def _scaled(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("observation values must be numeric")
    number = float(value) / SCORE_SCALE
    if not math.isfinite(number):
        raise ValueError("observation values must be finite")
    return number


def extract(pair: Sequence[Any]) -> list[float]:
    """Extract a symmetric feature vector from exactly two observation states."""
    if not isinstance(pair, Sequence) or isinstance(pair, (str, bytes)) or len(pair) != 2:
        raise ValueError("pair must contain exactly two observation states")
    first = _state(pair[0])
    second = _state(pair[1])
    features: list[float] = []
    for leaf in LEAF_ORDER:
        first_present = int(leaf in first)
        second_present = int(leaf in second)
        presence_min = min(first_present, second_present)
        presence_max = max(first_present, second_present)
        presence_xor = first_present ^ second_present
        if presence_min:
            first_score = _scaled(first[leaf])
            second_score = _scaled(second[leaf])
            score_min = min(first_score, second_score)
            score_max = max(first_score, second_score)
            score_abs_diff = abs(first_score - second_score)
            score_sum = first_score + second_score
        else:
            score_min = 0.0
            score_max = 0.0
            score_abs_diff = 0.0
            score_sum = 0.0
        features.extend(
            (
                float(presence_min),
                float(presence_max),
                float(presence_xor),
                score_min,
                score_max,
                score_abs_diff,
                score_sum,
            )
        )
    if len(features) != len(LEAF_ORDER) * len(COMPONENTS):
        raise RuntimeError("feature cardinality invariant failed")
    if not all(math.isfinite(value) for value in features):
        raise ValueError("extracted features must be finite")
    return features


def feature_indices(names: tuple[str, ...]) -> list[int]:
    component_width = len(COMPONENTS)
    indices: list[int] = []
    for leaf in LEAF_ORDER:
        if leaf in names:
            start = LEAF_ORDER.index(leaf) * component_width
            indices.extend(range(start, start + component_width))
    return indices


FEATURE_SETS = {
    "full": list(range(len(LEAF_ORDER) * len(COMPONENTS))),
    "direct_codebook": feature_indices(DIRECT_LEAVES),
    "non_direct": feature_indices(NON_DIRECT_LEAVES),
}
