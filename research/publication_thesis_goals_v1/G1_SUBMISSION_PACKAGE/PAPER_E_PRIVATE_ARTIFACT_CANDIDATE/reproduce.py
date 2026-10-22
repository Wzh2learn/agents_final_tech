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


def verify_manifest(root: Path) -> dict[str, Any]:
    manifest_path = root / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = {entry["path"] for entry in manifest["files"]}
    actual = {
        str(path.relative_to(root)).replace("\\", "/")
        for path in root.rglob("*")
        if path.is_file() and path.name not in {"MANIFEST.json", "REPRODUCTION_RECEIPT.json"}
    }
    assert actual == expected, {
        "missing": sorted(expected - actual),
        "extra": sorted(actual - expected),
    }
    for entry in manifest["files"]:
        path = root / entry["path"]
        assert path.is_file(), entry["path"]
        assert path.stat().st_size == entry["bytes"], entry["path"]
        assert sha256_file(path) == entry["sha256"], entry["path"]
    return {
        "entries": len(expected),
        "all_entries_exist_size_and_hash_match": True,
        "extra_files": [],
    }


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


def recompute_finrank(full_path: Path, compact_path: Path) -> dict[str, Any]:
    full_payload = json.loads(full_path.read_text(encoding="utf-8"))
    compact_payload = json.loads(compact_path.read_text(encoding="utf-8"))
    rows = full_payload["rows"]
    compact = {
        (row["model"], row["tie_policy"]): row
        for row in compact_payload["rows"]
    }
    raw_gaps = []
    display_gaps = []
    display_rows = []
    for row in rows:
        raw_gap = row["random"] - row["hard"]
        source_gap = full_payload["source_gap_fields"][row["model"]][row["tie_policy"]]
        assert math.isclose(raw_gap, source_gap, rel_tol=0.0, abs_tol=1e-12)
        raw_gaps.append(raw_gap)
        display_gaps.append(round(raw_gap, 3))
        displayed = compact[(row["model"], row["tie_policy"])]
        assert displayed["hard"] == round(row["hard"], 3)
        assert displayed["random"] == round(row["random"], 3)
        display_rows.append(
            {
                "model": row["model"],
                "tie_policy": row["tie_policy"],
                "hard": round(row["hard"], 3),
                "random": round(row["random"], 3),
                "gap": round(raw_gap, 3),
            }
        )
    assert display_gaps == compact_payload["expected_gaps"]
    for model in ("TF-IDF", "BM25"):
        model_rows = [row for row in rows if row["model"] == model]
        by_policy = {row["tie_policy"]: row for row in model_rows}
        positive = (
            by_policy["ties-positive"]["random"]
            - by_policy["ties-positive"]["hard"]
        )
        strict = (
            by_policy["strict-win"]["random"]
            - by_policy["strict-win"]["hard"]
        )
        assert positive > 0 and strict > 0
        assert round(positive - strict, 3) == (0.359 if model == "TF-IDF" else 0.343)
    tfidf_strict = next(
        row for row in rows
        if row["model"] == "TF-IDF" and row["tie_policy"] == "strict-win"
    )
    raw_strict_gap = tfidf_strict["random"] - tfidf_strict["hard"]
    rounded_cell_gap = round(tfidf_strict["random"], 3) - round(tfidf_strict["hard"], 3)
    assert f"{raw_strict_gap:.3f}" == "13.821"
    assert f"{rounded_cell_gap:.3f}" == "13.820"
    return {
        "rows": len(rows),
        "raw_gaps": raw_gaps,
        "display_gaps": display_gaps,
        "display_rows": display_rows,
        "tfidf_strict_precision_check": {
            "raw_gap": raw_strict_gap,
            "raw_gap_display": f"{raw_strict_gap:.3f}",
            "rounded_cell_gap": rounded_cell_gap,
            "rounded_cell_gap_display": f"{rounded_cell_gap:.3f}",
            "rule": "compute at full precision and format only at the end",
        },
        "hard_vs_random_direction": "positive_for_all_tested_tie_policies",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-receipt", type=Path)
    args = parser.parse_args()
    stage_path = ROOT / "inputs/G1_SEED_REANALYSIS.json"
    finrank_full_path = ROOT / "inputs/FINRANK_FULL_PRECISION_ROWS.json"
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
            str(finrank_full_path.relative_to(ROOT)): sha256_file(finrank_full_path),
            str(finrank_path.relative_to(ROOT)): sha256_file(finrank_path),
        },
        "manifest": verify_manifest(ROOT),
        "stage_uid_cluster": recompute_stage(stage_path),
        "finrank_compact_table": recompute_finrank(finrank_full_path, finrank_path),
        "nonclaims": [
            "The row-level staged analysis is a post-hoc reanalysis of frozen results.",
            "The FinRank extract verifies full-precision arithmetic, display rounding and direction, not the full historical application.",
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
