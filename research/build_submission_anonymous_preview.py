"""Build an anonymous submission-source preview from the internal paper draft.

The generator performs deterministic redactions only. It does not edit the source
manuscript and does not create a venue-specific camera-ready file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPO / "paper" / "teacher_review_draft_v1.md"

INTERNAL_HEADER = (
    "> Evaluation-track evidence draft for internal teacher review, 2026-09-22. "
    "This document covers the evaluation stage only; the current three-stage paper "
    "direction is documented separately. Author and affiliation are to be filled in. "
    "Do not distribute, submit, upload to arXiv, or publish code before the patent-status "
    "gate is cleared."
)
ANONYMOUS_HEADER = (
    "> Anonymous submission-source preview. Author and affiliation are omitted; "
    "venue-specific formatting and final submission authorization remain pending."
)

REDACTIONS: list[tuple[str, str, str]] = [
    (INTERNAL_HEADER, ANONYMOUS_HEADER, "internal_status_header"),
    (
        r"\.\./docs/experiments/figures_paper/fig_checkpoint_trees_v2\.svg",
        "figures/fig_checkpoint_trees_v2.svg",
        "figure_1_path",
    ),
    (
        r"\.\./docs/experiments/figures_paper/fig_visibility_spectrum\.png",
        "figures/fig_visibility_spectrum.png",
        "figure_2_path",
    ),
    (
        r"config/eval_checkpoint_trees\.json v0\.1\.0",
        "the frozen checkpoint configuration",
        "checkpoint_config_versioned",
    ),
    (
        r"source tag m2_judge in config/eval_checkpoint_trees\.json",
        "the frozen semantic-judge configuration",
        "semantic_judge_config",
    ),
    (
        r"config/eval_checkpoint_trees\.json",
        "the frozen checkpoint configuration",
        "checkpoint_config",
    ),
    (
        r"data/research/drift_v0/input/tatqa_tables\.json, sha256 [0-9a-f]+",
        "the frozen source-table artifact",
        "source_artifact",
    ),
    (
        r"data/research/drift_v0/output/injection_map\.json, sha256 [0-9a-f]+",
        "the frozen perturbation artifact",
        "injection_artifact",
    ),
    (
        r"scripts/m1_statement_parser\.py, map_headers",
        "the deterministic header matcher",
        "matcher_implementation",
    ),
    (
        r"Qwen3\.6-35B-A3B \(Q4_K_M GGUF\) served at 127\.0\.0\.1:8004",
        "a fixed semantic-judge model",
        "judge_model_endpoint",
    ),
    (
        r"frozen artifact t2_visibility_sensitivity\.json; path in the evidence ledger",
        "the frozen sensitivity artifact",
        "sensitivity_artifact",
    ),
    (
        r"production greedy header matcher",
        "greedy header matcher",
        "production_wording",
    ),
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def anonymize(source_text: str) -> tuple[str, dict[str, object]]:
    output = source_text
    applied: list[dict[str, object]] = []
    for pattern, replacement, label in REDACTIONS:
        if label == "internal_status_header":
            count = output.count(pattern)
            output = output.replace(pattern, replacement)
        else:
            output, count = re.subn(pattern, replacement, output)
        applied.append({"label": label, "count": count, "replacement": replacement})
    return output, {
        "schema_version": 1,
        "generator": "submission-anonymous-preview-v1",
        "redactions": applied,
    }


def build(source: Path, output: Path, map_output: Path) -> dict[str, object]:
    source_text = source.read_text(encoding="utf-8")
    source_hash = _sha256(source)
    anonymous_text, redaction_map = anonymize(source_text)
    redaction_map.update({
        "source_path": _display_path(source),
        "source_sha256": source_hash,
        "output_path": _display_path(output),
    })
    output.write_text(anonymous_text, encoding="utf-8", newline="\n")
    map_output.write_text(
        json.dumps(redaction_map, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return {
        "source_sha256": source_hash,
        "output_sha256": _sha256(output),
        "map_sha256": _sha256(map_output),
        "redaction_count": sum(int(item["count"]) for item in redaction_map["redactions"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--map-output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.source, args.output, args.map_output)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
