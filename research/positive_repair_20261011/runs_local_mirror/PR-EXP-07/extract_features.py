#!/usr/bin/env python3
"""Materialize label-blind features without loading labels into extractor calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

from extractor import extract


PAIR_ORDER_SEED = 2026101107


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_all(source: Path) -> tuple[list[dict], dict]:
    records = []
    order_rng = random.Random(PAIR_ORDER_SEED)
    order_counts = {"baseline_first": 0, "injected_first": 0}
    with source.open("r", encoding="utf-8") as handle:
        for row_index, line in enumerate(handle):
            if not line.strip():
                continue
            row = json.loads(line)
            first = row["baseline_scores"]
            second = row["injected_scores"]
            reverse = bool(order_rng.getrandbits(1))
            pair = (second, first) if reverse else (first, second)
            features = extract(pair)
            order_label = "injected_first" if reverse else "baseline_first"
            order_counts[order_label] += 1
            records.append(
                {
                    "row_index": row_index,
                    "pair_order": order_label,
                    "features": features,
                }
            )
    proof = {
        "pair_order_seed": PAIR_ORDER_SEED,
        "row_count": len(records),
        "order_counts": order_counts,
        "source_sha256": sha256_file(source),
        "extractor_sha256": sha256_file(Path(__file__).with_name("extractor.py")),
        "extractor_input_contract": "exactly one unordered pair of observation-state mappings",
        "forbidden_fields_accessed": [],
    }
    return records, proof


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--proof", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.proof.exists():
        raise FileExistsError("feature outputs must not pre-exist")
    records, proof = extract_all(args.source)
    write_jsonl(args.output, records)
    args.proof.write_text(
        json.dumps(proof, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
