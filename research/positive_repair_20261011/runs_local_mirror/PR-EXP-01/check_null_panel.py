#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = next(path for path in Path(__file__).resolve().parents if (path / "src").is_dir())
GENERATOR_NAME = "generate_null_panel"
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


def digest(value) -> str:
    blob = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def stringify(row: list) -> list[str]:
    return [str(value) if value is not None else "" for value in row]


def transform(header: list[str], index: int, rule: str) -> list[str] | None:
    output = list(header)
    value = output[index]
    if rule == RULES[0]:
        changed = " " + value
    elif rule == RULES[1]:
        changed = value + " "
    elif rule == RULES[2]:
        if " " not in value:
            return None
        changed = value.replace(" ", "", 1)
    elif rule == RULES[3]:
        changed = value.swapcase()
    else:
        raise AssertionError(rule)
    if changed == value:
        return None
    output[index] = changed
    return output


def downstream(header: list[str], mp, d3) -> dict:
    canonical = d3.unique_canonical(header, mp)
    schema_fields = [mp.SchemaField(name, [name]) for name in canonical]
    schema = mp.SchemaTable(
        table_name="pr_exp_01_independent_check",
        layout="grid",
        header_region_keywords=[],
        fields=schema_fields,
    )
    mapped, unmapped = mp.map_headers(header, schema)
    ordered_targets = [mapped.get(value) for value in header]
    absent = Counter(mp.normalize_header(value) for value in unmapped)
    return {
        "canonical_normalized_keys": [mp.normalize_header(value) for value in canonical],
        "canonical_count": len(canonical),
        "mapped_standard_values_in_header_order": ordered_targets,
        "unmapped_normalized_counts": [list(item) for item in sorted(absent.items())],
    }


def own_ast_independence(path: Path) -> dict:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    generator_imports = sorted({name for name in imports if GENERATOR_NAME in name})
    return {"imports": sorted(imports), "generator_imports": generator_imports, "passes": not generator_imports}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", required=True)
    parser.add_argument("--generator", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    self_path = Path(__file__).resolve()
    generator_path = Path(args.generator).resolve()
    ast_check = own_ast_independence(self_path)
    sys.path.insert(0, str(ROOT / "src"))
    import biz.m1_statement_parser as mp

    d3 = load_module("pr_exp01_checker_d3", ROOT / "research/paper_d3_matched_fpr_stage_a.py")
    tables = json.loads((ROOT / "data/research/drift_v0/input/tatqa_tables.json").read_text(encoding="utf-8"))
    mapping = json.loads((ROOT / "data/research/drift_v0/output/injection_map.json").read_text(encoding="utf-8"))["mapping"]
    injected = {row["uid"] for row in mapping}
    ordered_uids = sorted({row["uid"] for row in tables})
    folds = {uid: position % 5 for position, uid in enumerate(ordered_uids)}
    by_uid = {row["uid"]: row for row in tables}

    expected = []
    failures = []
    candidate_count = 0
    for uid in ordered_uids:
        if uid in injected:
            continue
        header = stringify(by_uid[uid]["table"][0])
        if not d3.unique_canonical(header, mp):
            continue
        source_truth = downstream(header, mp, d3)
        source_truth_hash = digest(source_truth)
        source_raw_hash = digest(header)
        for index in range(len(header)):
            for rule in RULES:
                candidate_count += 1
                edited = transform(header, index, rule)
                if edited is None:
                    continue
                edited_raw_hash = digest(edited)
                if edited_raw_hash == source_raw_hash:
                    failures.append({"kind": "raw_identity", "uid": uid, "index": index, "rule": rule})
                    continue
                edited_truth = downstream(edited, mp, d3)
                edited_truth_hash = digest(edited_truth)
                if edited_truth_hash != source_truth_hash:
                    failures.append({"kind": "truth_mismatch", "uid": uid, "index": index, "rule": rule})
                    continue
                identity = sha_input = f"{uid}\x1f{index}\x1f{rule}".encode("utf-8")
                expected.append(
                    {
                        "candidate_id": hashlib.sha256(sha_input).hexdigest(),
                        "uid": uid,
                        "fold": folds[uid],
                        "cell_index": index,
                        "rule": rule,
                        "source_header_sha256": source_raw_hash,
                        "edited_header_sha256": edited_raw_hash,
                        "source_task_truth_sha256": source_truth_hash,
                        "task_truth_sha256": edited_truth_hash,
                        "scored_surface_nonidentity": True,
                        "task_truth_identity": True,
                    }
                )

    actual = [json.loads(line) for line in Path(args.panel).read_text(encoding="utf-8").splitlines() if line.strip()]
    expected.sort(key=lambda row: (row["uid"], row["cell_index"], RULES.index(row["rule"]), row["candidate_id"]))
    duplicate_ids = len(actual) - len({row.get("candidate_id") for row in actual})
    exact_match = actual == expected
    status = "PASS" if ast_check["passes"] and not failures and duplicate_ids == 0 and exact_match and expected else "FAIL"
    payload = {
        "namespace": "PR-EXP-01_independent_panel_checker_v1",
        "status": status,
        "ast_independence": ast_check,
        "generator_path": str(generator_path.relative_to(ROOT)),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "checker_path": str(self_path.relative_to(ROOT)),
        "checker_sha256": hashlib.sha256(self_path.read_bytes()).hexdigest(),
        "separate_file_hash_lineage": generator_path != self_path,
        "candidate_count_recomputed": candidate_count,
        "admitted_count_recomputed": len(expected),
        "admitted_count_observed": len(actual),
        "duplicate_candidate_ids": duplicate_ids,
        "panel_exact_complete_match": exact_match,
        "admission_failures": failures[:100],
        "admission_failure_count": len(failures),
        "empty_admission": not expected,
        "unverifiable_identity": bool(failures) or not ast_check["passes"],
    }
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "admitted": len(expected), "failures": len(failures)}, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
