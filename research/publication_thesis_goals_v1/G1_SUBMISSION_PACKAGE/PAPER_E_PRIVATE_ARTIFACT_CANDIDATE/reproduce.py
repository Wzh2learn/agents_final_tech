#!/usr/bin/env python3
"""Recompute the compact Paper E tables with the Python standard library."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def recompute_stage(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["rows"]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["uid"]].append(row)
    detected = sum(bool(row["E1.2_detected"]) for row in rows)
    uid_equal = sum(
        sum(bool(row["E1.2_detected"]) for row in group) / len(group)
        for group in grouped.values()
    ) / len(grouped)
    run_weighted = detected / len(rows)
    rng = random.Random(20261021)
    uids = sorted(grouped)
    run_rates: list[float] = []
    uid_rates: list[float] = []
    for _ in range(20_000):
        sampled = rng.choices(uids, k=len(uids))
        sampled_rows = [row for uid in sampled for row in grouped[uid]]
        run_rates.append(sum(bool(row["E1.2_detected"]) for row in sampled_rows) / len(sampled_rows))
        uid_rates.append(
            sum(
                sum(bool(row["E1.2_detected"]) for row in grouped[uid]) / len(grouped[uid])
                for uid in sampled
            )
            / len(sampled)
        )
    overlap = Counter(len({int(row["seed"]) for row in group}) for group in grouped.values())
    expected = payload["pooled_protocols"]["E1.2_flat"]
    result = {
        "table_runs": len(rows),
        "detected_table_runs": detected,
        "unique_source_table_uids": len(grouped),
        "run_weighted_rate": round(run_weighted, 6),
        "uid_equal_rate": round(uid_equal, 6),
        "run_weighted_rate_ci95": [round(percentile(run_rates, 0.025), 6), round(percentile(run_rates, 0.975), 6)],
        "uid_equal_rate_ci95": [round(percentile(uid_rates, 0.025), 6), round(percentile(uid_rates, 0.975), 6)],
        "uid_seed_overlap_counts": {f"seen_in_{key}_seed(s)": overlap[key] for key in sorted(overlap)},
    }
    assert result["table_runs"] == expected["table_runs"] == 282
    assert result["detected_table_runs"] == expected["detected_table_runs"] == 219
    assert result["unique_source_table_uids"] == expected["unique_source_table_uids"] == 119
    assert result["run_weighted_rate"] == expected["run_weighted_rate"]
    assert result["uid_equal_rate"] == expected["uid_equal_rate"]
    assert result["run_weighted_rate_ci95"] == [0.711744, 0.836364]
    assert result["uid_equal_rate_ci95"] == [0.683473, 0.820728]
    return result


def recompute_finrank(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["rows"]
    gaps = [round(row["random"] - row["hard"], 3) for row in rows]
    assert gaps == payload["expected_gaps"]
    for model in ("TF-IDF", "BM25"):
        model_rows = [row for row in rows if row["model"] == model]
        by_policy = {row["tie_policy"]: row for row in model_rows}
        positive = by_policy["ties-positive"]["random"] - by_policy["ties-positive"]["hard"]
        strict = by_policy["strict-win"]["random"] - by_policy["strict-win"]["hard"]
        assert positive > 0 and strict > 0
        assert abs((positive - strict) - (0.359 if model == "TF-IDF" else 0.343)) < 0.0001
    return {"rows": len(rows), "gaps": gaps, "hard_vs_random_direction": "positive_for_all_tested_tie_policies"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-receipt", type=Path)
    args = parser.parse_args()
    stage_path = ROOT / "data/G1_SEED_REANALYSIS.json"
    finrank_path = ROOT / "FINRANK_COMPACT_ROWS.json"
    result = {
        "schema": "paper_e_private_artifact_reproduction_receipt_v1",
        "status": "PASS",
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
        },
        "inputs": {
            str(stage_path.relative_to(ROOT)): sha256_file(stage_path),
            str(finrank_path.relative_to(ROOT)): sha256_file(finrank_path),
        },
        "stage_uid_cluster": recompute_stage(stage_path),
        "finrank_compact_table": recompute_finrank(finrank_path),
        "nonclaims": [
            "The row-level staged analysis is a post-hoc reanalysis of frozen results.",
            "The compact FinRank table verifies arithmetic and direction, not the full historical application.",
            "No model or judge call is made by this reproduction.",
        ],
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.write_receipt:
        args.write_receipt.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
