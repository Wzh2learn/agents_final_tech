#!/usr/bin/env python3
"""Run the frozen 24-question visible-rule regression."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot_import:{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def parse_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numeric_value(program: dict[str, Any], cells: dict[str, float], scorer: Any) -> float | None:
    if program is None:
        return None
    try:
        value = scorer.program_value(program, cells)
        return float(value) if math.isfinite(value) else None
    except (KeyError, ValueError, TypeError, ZeroDivisionError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    actor = load_module(Path(__file__).with_name("public_actor.py"), "publication_p1_public_actor")
    scorer_path = ROOT / "research" / "natural_program_learning_20261024_v2" / "run_natural_program_experiment_v2.py"
    scorer = load_module(scorer_path, "publication_p1_frozen_scorer")
    instances = [
        row for row in parse_jsonl(args.instances) if row["variant"] == "original"
    ][:24]
    results = [
        row for row in parse_jsonl(args.results) if row["variant"] == "original"
    ][:24]
    if len(instances) != 24 or len(results) != 24:
        raise ValueError(f"expected_24_ordinary_originals got_instances={len(instances)} got_results={len(results)}")
    if [row["source_task_id"] for row in instances] != [row["source_task_id"] for row in results]:
        raise ValueError("instance_result_order_mismatch")

    rows: list[dict[str, Any]] = []
    for instance, baseline in zip(instances, results):
        question = instance["prompt"].split("\n\nQuestion: ", 1)[1]
        answer = actor.solve(question, instance["table_text"])
        cells = scorer.rendered_values(instance["table_text"])
        value = numeric_value(answer.get("program"), cells, scorer)
        expected = float(instance["expected"]["answer"])
        numeric_correct = value is not None and math.isclose(value, expected, rel_tol=1e-6, abs_tol=1e-6)
        direction_conflict = (
            numeric_correct is False
            and value is not None
            and math.isclose(value, -expected, rel_tol=1e-6, abs_tol=1e-6)
        )
        rows.append(
            {
                "source_task_id": instance["source_task_id"],
                "instance_id": instance["instance_id"],
                "question": question,
                "expected": instance["expected"],
                "baseline": {
                    "program_correct": baseline["program_correct"],
                    "program_executable": baseline["program_executable"],
                    "program_value": baseline.get("program_value"),
                    "failure": baseline.get("failure"),
                },
                "actor": answer,
                "actor_value": value,
                "actor_numeric_correct": numeric_correct,
                "direction_conflict": direction_conflict,
                "genuine_repair": bool(not baseline["program_correct"] and numeric_correct),
                "damage": bool(baseline["program_correct"] and not numeric_correct),
            }
        )

    summary = {
        "denominator": len(rows),
        "baseline_numeric_correct": sum(row["baseline"]["program_correct"] for row in rows),
        "actor_numeric_correct": sum(row["actor_numeric_correct"] for row in rows),
        "genuine_repairs": sum(row["genuine_repair"] for row in rows),
        "damage_to_previously_numeric_correct": sum(row["damage"] for row in rows),
        "direction_conflicts": sum(row["direction_conflict"] for row in rows),
        "actor_outcomes": {
            outcome: sum(row["actor"]["actor_outcome"] == outcome for row in rows)
            for outcome in sorted({row["actor"]["actor_outcome"] for row in rows})
        },
        "actor_program_executable": sum(row["actor_value"] is not None for row in rows),
        "actor_citation_valid": sum(bool(row["actor"]["citation_valid"]) for row in rows),
        "actor_unit_unknown": sum(row["actor"]["unit"] == "UNKNOWN" for row in rows),
        "input_sha256": {
            "instances": sha256_file(args.instances),
            "results": sha256_file(args.results),
            "scorer": sha256_file(scorer_path),
        },
        "notes": [
            "Exposed development regression over the frozen 24 ordinary originals.",
            "The actor is deterministic and receives only question plus complete visible table text.",
            "The frozen numeric scorer is imported and used for program execution.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
