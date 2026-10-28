#!/usr/bin/env python3
"""Pure, zero-model Scoring V3 rescore of immutable saved actor outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY_ROOT))

from research.adaptive_mechanism_20261027_v1.scoring_v2 import scorer as v2
from research.word_scoring_new_family_20261027_v1.scoring_v3.scorer import (
    score_response,
)


ROOT = REPOSITORY_ROOT
RAW = (
    ROOT
    / "research/publication_proxy_calibration_20261026_v1/raw/runs/"
    "compliant_primary/P2_GENERATIONS.raw.jsonl"
)
ANNOTATED = (
    ROOT
    / "research/publication_proxy_calibration_20261026_v1/raw/runs/"
    "compliant_primary/P2_GENERATIONS.annotated.jsonl"
)
REFERENCE = (
    ROOT
    / "research/publication_proxy_calibration_20261026_v1/"
    "p2_proxy_calibration/receipts/P2_REFERENCE_CHAIN.json"
)
SOURCE = Path(
    "/home/testuser/wzh/projects/agents_final_tech/data/research/"
    "tatqa_raw_2026/tatqa_dataset_dev.json"
)
V2_ROWS = (
    ROOT
    / "research/adaptive_mechanism_20261027_v1/scoring_v2/"
    "results/FIRST_BATCH_ROWS_V2.jsonl"
)
ABLATION_ROOT = ROOT / "research/adaptive_mechanism_20261027_v1/d_integration/results"
VARIANTS = {
    "first_batch_final": V2_ROWS,
    "oracle": ABLATION_ROOT / "ORACLE_ROWS.jsonl",
    "blank_type": ABLATION_ROOT / "ANSWER_TYPE_FREE_ROWS.jsonl",
    "question_only": ABLATION_ROOT / "QUESTION_ONLY_ROWS.jsonl",
}
LAYERS = ("strict", "answer", "numeric_unit", "evidence", "final_delivery")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def build_cases() -> dict[tuple[str, str], dict[str, Any]]:
    raw_rows = read_jsonl(RAW)
    if len(raw_rows) != 40:
        raise SystemExit(f"expected_40_first_batch_rows:{len(raw_rows)}")
    annotated = {row["call_id"]: row for row in read_jsonl(ANNOTATED)}
    references = json.loads(REFERENCE.read_text(encoding="utf-8"))["rows"]
    uid_by_hash = {
        hashlib.sha256(row["question_uid"].encode("utf-8")).hexdigest(): row[
            "question_uid"
        ]
        for row in references
    }
    reference_by_uid = {row["question_uid"]: row for row in references}
    sources = v2.load_source_records(SOURCE)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in raw_rows:
        grouped[(row["question_uid_sha256"], row["arm"])].append(row)
    if len(grouped) != 36:
        raise SystemExit(f"expected_36_final_attempt_groups:{len(grouped)}")

    cases: dict[tuple[str, str], dict[str, Any]] = {}
    for (uid_hash, arm), attempts in sorted(grouped.items()):
        raw = max(attempts, key=lambda item: int(item["call_number"]))
        uid = uid_by_hash[uid_hash]
        reference = reference_by_uid[uid]
        selected_orders = raw.get(
            "selected_paragraph_orders",
            annotated[raw["call_id"]]["selected_paragraph_orders"],
        )
        visible = v2.load_visible_context(
            sources[reference["table_uid"]], reference, selected_orders
        )
        cases[(uid, arm)] = {
            "raw": raw,
            "reference": reference,
            "visible": visible,
        }
    return cases


def response_text(
    row: dict[str, Any], first_batch: bool, case: dict[str, Any]
) -> str:
    if first_batch:
        return str(case["raw"]["complete_response"])
    return json.dumps(row["response"], ensure_ascii=False, sort_keys=True)


def v2_layers(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("scoring_v2_layers") or row["score_layers"]


def axis_report(v2_layers_by_name: dict[str, Any], v3_layers: dict[str, Any]) -> dict[str, Any]:
    strict_v2 = v2_layers_by_name["strict"]
    strict_v3 = v3_layers["strict"]
    answer_v2 = v2_layers_by_name["answer"]
    answer_v3 = v3_layers["answer"]
    numeric_v2 = v2_layers_by_name["numeric_unit"]
    numeric_v3 = v3_layers["numeric_unit"]
    evidence_v2 = v2_layers_by_name["evidence"]
    evidence_v3 = v3_layers["evidence"]
    return {
        "semantic_equivalence": {
            "v2": answer_v2["status"],
            "v3": answer_v3["status"],
            "changed": answer_v2 != answer_v3,
        },
        "exact_set_completeness": {
            "v2_reason": answer_v2.get("reason"),
            "v3_reason": answer_v3.get("reason"),
            "changed": answer_v2.get("reason") != answer_v3.get("reason"),
        },
        "unit_direction": {
            "v2_status": numeric_v2["status"],
            "v3_status": numeric_v3["status"],
            "v2_numeric": numeric_v2.get("numeric"),
            "v3_numeric": numeric_v3.get("numeric"),
            "v2_unit": numeric_v2.get("unit"),
            "v3_unit": numeric_v3.get("unit"),
            "changed": numeric_v2 != numeric_v3,
        },
        "evidence_support": {
            "v2_status": evidence_v2["status"],
            "v3_status": evidence_v3["status"],
            "v2_reason": evidence_v2.get("reason"),
            "v3_reason": evidence_v3.get("reason"),
            "v2_support": evidence_v2.get("support"),
            "v3_support": evidence_v3.get("support"),
            "changed": evidence_v2 != evidence_v3,
        },
        "strict_format": {
            "v2_status": strict_v2["status"],
            "v3_status": strict_v3["status"],
            "v2_reason": strict_v2.get("reason"),
            "v3_reason": strict_v3.get("reason"),
            "changed": strict_v2 != strict_v3,
        },
        "unknown_pending": {
            "v2_final": v2_layers_by_name["final_delivery"]["status"],
            "v3_final": v3_layers["final_delivery"]["status"],
            "v2_reason": v2_layers_by_name["final_delivery"].get("reason"),
            "v3_reason": v3_layers["final_delivery"].get("reason"),
            "changed": v2_layers_by_name["final_delivery"]
            != v3_layers["final_delivery"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "results",
    )
    args = parser.parse_args()
    cases = build_cases()
    rows: list[dict[str, Any]] = []
    summaries: dict[str, Any] = {}
    differences: list[dict[str, Any]] = []

    for variant, source_path in VARIANTS.items():
        source_rows = read_jsonl(source_path)
        if len(source_rows) != 36:
            raise SystemExit(f"expected_36_{variant}_rows:{len(source_rows)}")
        variant_rows: list[dict[str, Any]] = []
        status_counts = Counter()
        v2_status_counts = Counter()
        layer_counts: dict[str, Counter[str]] = {layer: Counter() for layer in LAYERS}
        changed_layers = Counter()
        for old in sorted(source_rows, key=lambda row: (row["question_uid"], row["arm"])):
            key = (old["question_uid"], old["arm"])
            if key not in cases:
                raise SystemExit(f"missing_case:{variant}:{key}")
            case = cases[key]
            v3 = score_response(
                response_text(old, variant == "first_batch_final", case),
                case["reference"],
                case["visible"],
            )
            old_layers = v2_layers(old)
            old_status = old.get("scoring_v2_status") or old["score_status"]
            axes = axis_report(old_layers, v3["layers"])
            layer_changes = {
                layer: {"v2": old_layers[layer]["status"], "v3": v3["layers"][layer]["status"]}
                for layer in LAYERS
                if old_layers[layer] != v3["layers"][layer]
            }
            row = {
                "schema": "scoring_v3_pure_rescore_row_v1",
                "variant": variant,
                "question_uid": old["question_uid"],
                "arm": old["arm"],
                "question": case["reference"]["question"],
                "answer_type": case["reference"]["answer_type"],
                "source_requirement": case["reference"]["source_requirement"],
                "response": json.loads(
                    response_text(old, variant == "first_batch_final", case)
                ),
                "scoring_v2_status": old_status,
                "scoring_v3_status": v3["status"],
                "scoring_v2_layers": old_layers,
                "scoring_v3_layers": v3["layers"],
                "version_axis_report": axes,
            }
            variant_rows.append(row)
            rows.append(row)
            status_counts[v3["status"]] += 1
            v2_status_counts[old_status] += 1
            for layer in LAYERS:
                layer_counts[layer][v3["layers"][layer]["status"]] += 1
            if layer_changes:
                changed_layers.update(layer_changes.keys())
                differences.append(
                    {
                        "variant": variant,
                        "question_uid": old["question_uid"],
                        "arm": old["arm"],
                        "question": case["reference"]["question"],
                        "layer_changes": layer_changes,
                        "status_change": {
                            "v2": old_status,
                            "v3": v3["status"],
                        },
                        "axes": axes,
                    }
                )
        summaries[variant] = {
            "rows": len(variant_rows),
            "v2_status_counts": dict(sorted(v2_status_counts.items())),
            "v3_status_counts": dict(sorted(status_counts.items())),
            "v3_layer_status_counts": {
                layer: dict(sorted(counts.items()))
                for layer, counts in layer_counts.items()
            },
            "changed_layer_status_counts": dict(sorted(changed_layers.items())),
        }

    per_uid: dict[str, dict[str, Any]] = {}
    for row in rows:
        per_uid.setdefault(row["question_uid"], {"question_uid": row["question_uid"], "variants": {}})
        per_uid[row["question_uid"]]["variants"][row["variant"]] = {
            "arm": row["arm"],
            "question": row["question"],
            "answer_type": row["answer_type"],
            "v2_status": row["scoring_v2_status"],
            "v3_status": row["scoring_v3_status"],
            "layer_changes": {
                layer: {
                    "v2": row["scoring_v2_layers"][layer]["status"],
                    "v3": row["scoring_v3_layers"][layer]["status"],
                }
                for layer in LAYERS
                if row["scoring_v2_layers"][layer] != row["scoring_v3_layers"][layer]
            },
        }

    payload = {
        "schema": "scoring_v3_pure_rescore_v1",
        "status": "COMPLETE_ZERO_MODEL_PURE_RESCORE",
        "model_calls": 0,
        "training_runs": 0,
        "judge_calls": 0,
        "generation_records_created": 0,
        "selection_rule": "immutable first 40-call raw batch; maximum call_number per UID x arm yields 36 final attempts",
        "datasets": {
            "first_batch_final": 36,
            "oracle": 36,
            "blank_type": 36,
            "question_only": 36,
        },
        "source_hashes": {
            "raw_jsonl": sha256(RAW),
            "annotated_jsonl": sha256(ANNOTATED),
            "reference_chain": sha256(REFERENCE),
            "tatqa_dev_source": sha256(SOURCE),
            "v2_first_batch_rows": sha256(V2_ROWS),
            **{
                f"saved_{name}": sha256(path)
                for name, path in VARIANTS.items()
                if name != "first_batch_final"
            },
        },
        "historical_immutables": {
            "old_first_batch_score": {"table_top3": 2, "table_top5": 3, "table_all": 3},
            "oracle_counts": {"ACCEPT": 31, "REASONABLE_UNKNOWN": 5},
            "blank_type_counts": {
                "ACCEPT": 12,
                "REJECT": 19,
                "REASONABLE_UNKNOWN": 5,
            },
            "question_only_counts": {"ACCEPT": 31, "REASONABLE_UNKNOWN": 5},
            "corrected_final_attempt_input_deltas": {
                "table_top5_minus_table_top3": 917,
                "table_all_minus_table_top5": 1604,
            },
            "identity": "recorded from unchanged historical manifests; not recomputed or rewritten",
        },
        "v3_version_boundaries": {
            "role_only_equal_values": "independent required evidence binding; no gold numeric-value scan",
            "required_evidence_support": "each operand separately; any broad support is PENDING, not automatic PASS",
            "single_element_numeric_span": "answer list element and numeric_value must agree",
            "pending_boundary": "unresolved legal reference or role binding remains PENDING",
            "unknown_boundary": "reasonable missing-evidence UNKNOWN remains distinct from PENDING",
        },
        "summaries_by_variant": summaries,
        "difference_count": len(differences),
        "per_uid": [per_uid[uid] for uid in sorted(per_uid)],
        "claim_boundary": (
            "Development pure rescore of saved outputs. Synthetic and mutated "
            "paired controls are not natural model error rates; no human-gold "
            "or new-source accuracy claim."
        ),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output / "V3_PURE_RESCORE_ROWS.jsonl", rows)
    write_jsonl(args.output / "V2_V3_LAYER_UID_DIFFERENCES.jsonl", differences)
    write_json(args.output / "V3_PURE_RESCORE_SUMMARY.json", payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "rows": len(rows),
                "differences": len(differences),
                "summaries": summaries,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
