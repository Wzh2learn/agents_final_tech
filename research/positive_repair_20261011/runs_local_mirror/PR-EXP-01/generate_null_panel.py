#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = next(path for path in Path(__file__).resolve().parents if (path / "src").is_dir())
SOURCE_TABLES = ROOT / "data/research/drift_v0/input/tatqa_tables.json"
INJECTION_MAP = ROOT / "data/research/drift_v0/output/injection_map.json"
RULES = (
    "edge_space_prefix",
    "edge_space_suffix",
    "internal_single_space_removed",
    "case_swap",
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json_bytes(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def raw_header(row: list) -> list[str]:
    return [str(cell) if cell is not None else "" for cell in row]


def apply_rule(header: list[str], cell_index: int, rule: str) -> list[str] | None:
    edited = list(header)
    text = edited[cell_index]
    if rule == "edge_space_prefix":
        replacement = " " + text
    elif rule == "edge_space_suffix":
        replacement = text + " "
    elif rule == "internal_single_space_removed":
        if " " not in text:
            return None
        replacement = text.replace(" ", "", 1)
    elif rule == "case_swap":
        replacement = text.swapcase()
    else:
        raise ValueError(rule)
    if replacement == text:
        return None
    edited[cell_index] = replacement
    return edited


def task_truth_artifact(header: list[str], mp, d3) -> dict:
    canonical_raw = d3.unique_canonical(header, mp)
    fields = [mp.SchemaField(std, [std]) for std in canonical_raw]
    schema_table = mp.SchemaTable(
        table_name="pr_exp_01_task_truth",
        layout="grid",
        header_region_keywords=[],
        fields=fields,
    )
    mapping, unmapped = mp.map_headers(header, schema_table)
    mapped_standard_values = [mapping.get(cell) for cell in header]
    unmapped_counts = sorted(Counter(mp.normalize_header(cell) for cell in unmapped).items())
    return {
        "canonical_normalized_keys": [mp.normalize_header(cell) for cell in canonical_raw],
        "canonical_count": len(canonical_raw),
        "mapped_standard_values_in_header_order": mapped_standard_values,
        "unmapped_normalized_counts": [list(item) for item in unmapped_counts],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT / "src"))
    import biz.m1_statement_parser as mp

    d3 = load_module("pr_exp01_frozen_d3", ROOT / "research/paper_d3_matched_fpr_stage_a.py")
    source_tables = json.loads(SOURCE_TABLES.read_text(encoding="utf-8"))
    injection_map = json.loads(INJECTION_MAP.read_text(encoding="utf-8"))["mapping"]
    injected_uids = {row["uid"] for row in injection_map}
    sorted_uids = sorted({row["uid"] for row in source_tables})
    folds = {uid: index % 5 for index, uid in enumerate(sorted_uids)}

    records = []
    counters = Counter()
    for table in source_tables:
        uid = table["uid"]
        counters["source_tables"] += 1
        if uid in injected_uids:
            counters["excluded_injected_uid"] += 1
            continue
        source_header = raw_header(table["table"][0])
        source_canonical = d3.unique_canonical(source_header, mp)
        if not source_canonical:
            counters["excluded_no_canonical"] += 1
            continue
        counters["clean_usable_tables"] += 1
        source_truth = task_truth_artifact(source_header, mp, d3)
        source_truth_sha = sha256_bytes(canonical_json_bytes(source_truth))
        source_raw_sha = sha256_bytes(canonical_json_bytes(source_header))
        for cell_index in range(len(source_header)):
            for rule in RULES:
                counters["candidate_applications"] += 1
                edited_header = apply_rule(source_header, cell_index, rule)
                if edited_header is None:
                    counters["candidate_identity_at_rule"] += 1
                    continue
                edited_raw_sha = sha256_bytes(canonical_json_bytes(edited_header))
                if edited_raw_sha == source_raw_sha:
                    counters["rejected_scored_surface_identity"] += 1
                    continue
                edited_truth = task_truth_artifact(edited_header, mp, d3)
                edited_truth_sha = sha256_bytes(canonical_json_bytes(edited_truth))
                if edited_truth_sha != source_truth_sha:
                    counters["rejected_task_truth_mismatch"] += 1
                    continue
                candidate_key = f"{uid}\x1f{cell_index}\x1f{rule}"
                records.append(
                    {
                        "candidate_id": sha256_bytes(candidate_key.encode("utf-8")),
                        "uid": uid,
                        "fold": folds[uid],
                        "cell_index": cell_index,
                        "rule": rule,
                        "source_header_sha256": source_raw_sha,
                        "edited_header_sha256": edited_raw_sha,
                        "source_task_truth_sha256": source_truth_sha,
                        "task_truth_sha256": edited_truth_sha,
                        "scored_surface_nonidentity": True,
                        "task_truth_identity": True,
                    }
                )
                counters["admitted"] += 1

    records.sort(key=lambda row: (row["uid"], row["cell_index"], RULES.index(row["rule"]), row["candidate_id"]))
    out_path = Path(args.out)
    summary_path = Path(args.summary)
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    tmp_path.replace(out_path)
    summary = {
        "namespace": "PR-EXP-01_null_panel_generator_v1",
        "source_tables_sha256": hashlib.sha256(SOURCE_TABLES.read_bytes()).hexdigest(),
        "injection_map_sha256": hashlib.sha256(INJECTION_MAP.read_bytes()).hexdigest(),
        "edit_dsl_rules": list(RULES),
        "panel_completeness": "all and only candidate applications satisfying raw nonidentity and task-truth hash identity; no sampling",
        "candidate_scope": "every cell of every usable non-injected source table × every DSL rule",
        "counts": dict(sorted(counters.items())),
        "admitted_count": len(records),
        "panel_sha256": hashlib.sha256(out_path.read_bytes()).hexdigest(),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"admitted": len(records), "panel": str(out_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
