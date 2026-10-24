"""Rescore frozen natural-program generations without new model calls."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from natural_variant_measurement_v3 import rescore_generation


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["model_arm"], row["slice"], row["variant"])].append(row)
    output = {}
    for (arm, slice_name, variant), subset in sorted(grouped.items()):
        output.setdefault(arm, {}).setdefault(slice_name, {})[variant] = {
            "instances": len(subset),
            "program_correct": sum(bool(row["program_correct"]) for row in subset),
            "program_correct_v2": sum(bool(row["program_correct_v2"]) for row in subset),
            "measurement_flips": sum(bool(row["measurement_flip"]) for row in subset),
            "failures": dict(Counter(row["failure"] for row in subset)),
            "failures_v2": dict(Counter(row["failure_v2"] for row in subset)),
        }
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output-results", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    args = parser.parse_args()
    instances = {row["instance_id"]: row for row in load_jsonl(args.instances)}
    original_results = load_jsonl(args.results)
    corrected = []
    missing = []
    for result in original_results:
        instance = instances.get(result.get("instance_id"))
        if instance is None:
            missing.append(result.get("instance_id"))
            continue
        corrected.append(rescore_generation(result, instance))
    write_jsonl(args.output_results, corrected)
    summary = {
        "schema": "natural_program_variant_rescore_v3",
        "date": "2026-10-24",
        "identity": "POST_HOC_RESCORE_OF_FROZEN_GENERATIONS_ON_PROMPT_VISIBLE_VARIANT_TABLES",
        "inputs": {
            "instances_sha256": sha256_file(args.instances),
            "results_sha256": sha256_file(args.results),
        },
        "instances": len(original_results),
        "rescored": len(corrected),
        "missing_instances": missing,
        "measurement_flips": sum(bool(row["measurement_flip"]) for row in corrected),
        "corrections": dict(Counter(row["measurement_correction"] for row in corrected)),
        "summary": summarize(corrected),
        "new_model_calls": 0,
        "interpretation_boundary": "This repairs variant-table scoring only; it does not create new generations or prospective evidence.",
    }
    write_json(args.output_summary, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
