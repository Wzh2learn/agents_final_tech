#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import fmean, median
from typing import Any, Iterable, Mapping, Sequence


ARMS = ("B", "E", "C", "S")
COMPARISONS = (
    ("E", "B"),
    ("E", "C"),
    ("E", "S"),
    ("C", "B"),
)
OUTCOME_CLASSES = {
    "correct",
    "correct_other_form",
    "wrong_unit",
    "wrong_period",
    "wrong",
    "regressed",
    "refused",
    "unknown",
}
CORRECT_OUTCOMES = {"correct", "correct_other_form"}
DEFAULT_SEED = "wp2-analysis-skeleton-20261013"
DEFAULT_BOOTSTRAP_REPLICATES = 10000
NUMERIC_COST_FIELDS = (
    "model_calls",
    "endpoint_calls",
    "transport_retries",
    "prompt_tokens",
    "completion_tokens",
    "context_tokens",
    "experience_tokens",
    "cost_usd",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_json(path: str | Path) -> Any:
    if str(path) == "-":
        return json.load(__import__("sys").stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def canonical_json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def percentile(values: Sequence[float], probability: float) -> float:
    require(values, "percentile requires values")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return (
        ordered[lower] * (1 - fraction)
        + ordered[upper] * fraction
    )


def bootstrap_mean_ci(
    values: Sequence[float], replicates: int, seed: str
) -> list[float] | None:
    if not values:
        return None
    require(
        replicates > 0,
        "bootstrap replicates must be positive",
    )
    rng = random.Random(seed)
    means = []
    for _ in range(replicates):
        sample = [
            values[rng.randrange(len(values))]
            for _ in range(len(values))
        ]
        means.append(fmean(sample))
    return [
        percentile(means, 0.025),
        percentile(means, 0.975),
    ]


def normalize_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, Mapping):
        require(
            "records" in payload,
            "input object must contain a records array",
        )
        raw_records = payload["records"]
    else:
        raw_records = payload
    require(
        isinstance(raw_records, list),
        "input records must be an array",
    )

    normalized = []
    seen_keys = set()
    for index, raw in enumerate(raw_records):
        require(
            isinstance(raw, Mapping),
            f"record {index} must be an object",
        )
        required = {"origin_id", "item_id", "arm", "repeat", "outcome"}
        missing = sorted(required - set(raw))
        require(
            not missing,
            f"record {index} is missing fields: {missing}",
        )
        origin_id = str(raw["origin_id"])
        item_id = str(raw["item_id"])
        arm = str(raw["arm"]).upper()
        repeat = raw["repeat"]
        outcome = str(raw["outcome"])
        require(origin_id, f"record {index} has an empty origin_id")
        require(item_id, f"record {index} has an empty item_id")
        require(arm in ARMS, f"record {index} has an invalid arm: {arm}")
        require(
            isinstance(repeat, int) and not isinstance(repeat, bool),
            f"record {index} repeat must be an integer",
        )
        require(
            repeat >= 1,
            f"record {index} repeat must be >= 1",
        )
        require(
            outcome in OUTCOME_CLASSES,
            f"record {index} has an invalid outcome: {outcome}",
        )
        key = (origin_id, item_id, arm, repeat)
        require(
            key not in seen_keys,
            f"duplicate episode key: {key}",
        )
        seen_keys.add(key)

        record = dict(raw)
        record.update(
            {
                "origin_id": origin_id,
                "item_id": item_id,
                "arm": arm,
                "repeat": repeat,
                "outcome": outcome,
            }
        )
        for field in NUMERIC_COST_FIELDS:
            value = record.get(field, 0)
            require(
                isinstance(value, (int, float))
                and not isinstance(value, bool),
                f"record {index} {field} must be numeric",
            )
            require(
                value >= 0,
                f"record {index} {field} must be non-negative",
            )
            record[field] = value
        for field in (
            "model_calls",
            "endpoint_calls",
            "transport_retries",
        ):
            require(
                isinstance(record[field], int)
                and not isinstance(record[field], bool),
                f"record {index} {field} must be an integer",
            )
        normalized.append(record)
    require(normalized, "input records must not be empty")
    return normalized


def origin_correct_rates(
    records: Iterable[Mapping[str, Any]]
) -> dict[str, float]:
    by_origin: dict[str, list[bool]] = defaultdict(list)
    for record in records:
        by_origin[str(record["origin_id"])].append(
            record["outcome"] in CORRECT_OUTCOMES
        )
    return {
        origin_id: fmean(int(value) for value in values)
        for origin_id, values in by_origin.items()
    }


def aggregate_arm(
    records: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    outcomes = Counter(record["outcome"] for record in records)
    origin_rates = origin_correct_rates(records)
    costs = {
        field: sum(float(record[field]) for record in records)
        for field in NUMERIC_COST_FIELDS
    }
    for field in (
        "model_calls",
        "endpoint_calls",
        "transport_retries",
    ):
        costs[field] = int(costs[field])
    correct_records = sum(
        1 for record in records if record["outcome"] in CORRECT_OUTCOMES
    )
    return {
        "episode_count": len(records),
        "item_count": len({record["item_id"] for record in records}),
        "origin_count": len(origin_rates),
        "outcome_counts": dict(sorted(outcomes.items())),
        "record_correct_rate": correct_records / len(records),
        "origin_mean_correct_rate": fmean(origin_rates.values()),
        "origin_correct_rates": dict(sorted(origin_rates.items())),
        "cost": costs,
    }


def paired_comparison(
    arm_rates: Mapping[str, Mapping[str, float]],
    left: str,
    right: str,
    bootstrap_replicates: int,
    seed: str,
) -> dict[str, Any]:
    common_origins = sorted(
        set(arm_rates[left]) & set(arm_rates[right])
    )
    differences = [
        100
        * (
            arm_rates[left][origin_id]
            - arm_rates[right][origin_id]
        )
        for origin_id in common_origins
    ]
    comparison_seed = hashlib.sha256(
        f"{seed}:{left}-{right}".encode("utf-8")
    ).hexdigest()
    return {
        "comparison": f"{left}-{right}",
        "origin_count": len(common_origins),
        "mean_difference_pp": (
            fmean(differences) if differences else None
        ),
        "median_difference_pp": (
            median(differences) if differences else None
        ),
        "bootstrap_ci_95_pp": bootstrap_mean_ci(
            differences,
            bootstrap_replicates,
            comparison_seed,
        ),
        "bootstrap_replicates": bootstrap_replicates,
        "bootstrap_seed": comparison_seed,
        "origin_differences": [
            {
                "origin_id": origin_id,
                f"{left}_correct_rate": arm_rates[left][origin_id],
                f"{right}_correct_rate": arm_rates[right][origin_id],
                "difference_pp": difference,
            }
            for origin_id, difference in zip(
                common_origins,
                differences,
                strict=True,
            )
        ],
    }


def analyze_records(
    payload: Any,
    *,
    bootstrap_replicates: int = DEFAULT_BOOTSTRAP_REPLICATES,
    seed: str = DEFAULT_SEED,
) -> dict[str, Any]:
    records = normalize_records(payload)
    require(
        bootstrap_replicates > 0,
        "bootstrap replicates must be positive",
    )
    records_by_arm = {
        arm: [record for record in records if record["arm"] == arm]
        for arm in ARMS
    }
    require(
        all(records_by_arm[arm] for arm in ARMS),
        "every arm must contain at least one synthetic record",
    )
    arms = {
        arm: aggregate_arm(records_by_arm[arm])
        for arm in ARMS
    }
    arm_rates = {
        arm: origin_correct_rates(records_by_arm[arm])
        for arm in ARMS
    }
    comparisons = {
        f"{left}-{right}": paired_comparison(
            arm_rates,
            left,
            right,
            bootstrap_replicates,
            seed,
        )
        for left, right in COMPARISONS
    }
    return {
        "schema": "wp2_origin_paired_analysis_v1",
        "status": "ANALYSIS_READY",
        "independent_unit": "origin",
        "correct_outcomes": sorted(CORRECT_OUTCOMES),
        "arms": arms,
        "comparisons": comparisons,
        "cost_by_arm": {
            arm: arms[arm]["cost"] for arm in ARMS
        },
        "input_counts": {
            "records": len(records),
            "origins": len(
                {record["origin_id"] for record in records}
            ),
            "items": len({record["item_id"] for record in records}),
        },
        "analysis_settings": {
            "bootstrap_method": (
                "origin-level nonparametric resampling of paired "
                "origin differences; linear-interpolated percentile CI"
            ),
            "bootstrap_replicates": bootstrap_replicates,
            "bootstrap_seed": seed,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Origin-level paired WP-2 analysis skeleton"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Synthetic or later-frozen episode JSON; '-' reads stdin",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON path",
    )
    parser.add_argument(
        "--bootstrap-replicates",
        type=int,
        default=DEFAULT_BOOTSTRAP_REPLICATES,
    )
    parser.add_argument(
        "--seed",
        default=DEFAULT_SEED,
    )
    args = parser.parse_args()
    payload = load_json(args.input)
    result = analyze_records(
        payload,
        bootstrap_replicates=args.bootstrap_replicates,
        seed=args.seed,
    )
    result["input_sha256"] = hashlib.sha256(
        canonical_json_bytes(payload)
    ).hexdigest()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(result))
    print(
        "WP2_ANALYSIS_SKELETON_PASS "
        f"records={result['input_counts']['records']} "
        f"origins={result['input_counts']['origins']} "
        f"comparisons={len(result['comparisons'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
