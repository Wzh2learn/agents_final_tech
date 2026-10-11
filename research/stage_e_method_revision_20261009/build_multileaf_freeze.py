#!/usr/bin/env python3
"""Build the outcome-blind M/R/N multi-leaf sample freeze.

The script materializes only deterministic sample contracts and generation
smoke. It does not execute the evaluator, inspect frozen Stage E outcomes, call
models, or run the formal multi-leaf experiment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
DEFAULT_OUT = TASK / "multileaf_freeze.json"

TABLES = ROOT / "data/research/drift_v0/input/tatqa_tables.json"
CHECKPOINT_TREES = ROOT / "config/eval_checkpoint_trees.json"
TATQA_RAW = Path("/home/testuser/wzh/datasets/tat-dqa/raw")
TATQA_FILES = (
    TATQA_RAW / "tatdqa_dataset_train.json",
    TATQA_RAW / "tatdqa_dataset_dev.json",
    TATQA_RAW / "tatdqa_dataset_test_gold.json",
)

SEED = 20261010
CLUSTERS_PER_STAGE = 24
INJECTIONS_PER_CLUSTER = 3
FLOAT_TOLERANCE = 0.01

M_STAGE = "M"
R_STAGE = "R"
N_STAGE = "N"
STAGE_NAMES = {
    M_STAGE: "mapping/schema",
    R_STAGE: "retrieval/grounding",
    N_STAGE: "numeric/reconciliation",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_rank(namespace: str, key: str) -> str:
    return sha256_bytes(f"{SEED}:{namespace}:{key}".encode("utf-8"))


def parse_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(float(value)) else None
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text or text in {"-", "–", "—", "N/A", "n/a"}:
        return None
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]
    text = text.replace(",", "").replace("$", "").replace("¥", "").replace("%", "").strip()
    if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", text):
        return None
    number = float(text)
    return -number if negative else number


def json_hash(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def leaf_ids(tree: dict[str, Any]) -> list[str]:
    leaves: list[str] = []

    def visit(node: dict[str, Any]) -> None:
        children = node.get("children") or []
        if children:
            for child in children:
                visit(child)
        else:
            leaves.append(str(node["id"]))

    for root in tree.get("trees", []):
        visit(root)
    return leaves


def select_m_samples(tables: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[tuple[str, dict[str, Any], list[tuple[int, int, str]]]] = []
    for record in tables:
        table = record.get("table") or []
        if not table or not isinstance(table[0], list):
            continue
        eligible: list[tuple[int, int, str]] = []
        for col, value in enumerate(table[0]):
            if not isinstance(value, str):
                continue
            token = value.strip()
            if len(token) < 2 or parse_number(token) is not None:
                continue
            eligible.append((0, col, token))
        if len(eligible) >= INJECTIONS_PER_CLUSTER:
            uid = str(record["uid"])
            candidates.append((uid, record, eligible))

    candidates.sort(key=lambda item: stable_rank("M-cluster", item[0]))
    selected = candidates[:CLUSTERS_PER_STAGE]
    if len(selected) < CLUSTERS_PER_STAGE:
        raise RuntimeError(f"M stage needs {CLUSTERS_PER_STAGE} clusters, found {len(selected)}")

    samples: list[dict[str, Any]] = []
    for uid, record, eligible in selected:
        ordered_cells = sorted(
            eligible,
            key=lambda item: stable_rank("M-cell", f"{uid}:{item[0]}:{item[1]}:{item[2]}"),
        )[:INJECTIONS_PER_CLUSTER]
        for repeat, (row, col, original) in enumerate(ordered_cells, start=1):
            mutation_token = f"__MUTANT_{stable_rank('M-token', f'{uid}:{row}:{col}')[:8]}__"
            sample_id = f"M-{uid}-r{row}c{col}-{repeat}"
            samples.append({
                "sample_id": sample_id,
                "stage": M_STAGE,
                "stage_name": STAGE_NAMES[M_STAGE],
                "cluster_id": f"M:{uid}",
                "repeat_within_cluster": repeat,
                "source_object": {
                    "path": str(TABLES.relative_to(ROOT)),
                    "uid": uid,
                    "table_sha256": json_hash(record["table"]),
                    "cell": {"row": row, "col": col},
                },
                "injection_operation": "replace_one_header_token_with_out_of_vocabulary_token",
                "injection_location": "table header/canonical mapping input before map_headers",
                "field_before": original,
                "field_after": mutation_token,
                "expected_first_affected_stage": M_STAGE,
                "expected_first_checkpoint": "parse.field.hit_rate",
                "direct_target_leaf": "parse.field.hit_rate",
                "potential_downstream_leaves": ["parse.table.regression", "parse.doc.ok"],
                "deterministic_or_judge": "deterministic",
                "gold_rule": "expected stage is fixed by header-cell injection and pipeline consumption order before scoring",
                "success_condition": "target leaf changes in the preregistered failure direction and the M class is predicted from the full response vector",
                "null_interpretation": "response exists but M/R/N signatures do not separate above baseline",
                "failure_interpretation": "contract violation, missing target response, or fewer than two population-responsive leaves",
                "harmfulness": "NOT_YET_DEFINED_EQUIVALENCE_DEPENDENT",
                "generation_smoke": {
                    "shape_unchanged": True,
                    "token_changed": original != mutation_token,
                },
            })
    return samples


def _records(payload: Any) -> Iterable[dict[str, Any]]:
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                yield item
    elif isinstance(payload, dict):
        for key in ("documents", "data", "examples"):
            if isinstance(payload.get(key), list):
                yield from _records(payload[key])
                return
        yield payload


def _first(record: dict[str, Any], keys: tuple[str, ...], default: Any = None) -> Any:
    for key in keys:
        if key in record:
            return record[key]
    return default


def load_tatqa_questions() -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    split_names = {
        "tatdqa_dataset_train.json": "train",
        "tatdqa_dataset_dev.json": "validation",
        "tatdqa_dataset_test_gold.json": "test",
    }
    for path in TATQA_FILES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        source_split = split_names[path.name]
        for document in _records(payload):
            metadata = document.get("doc") if isinstance(document.get("doc"), dict) else document
            document_id = str(_first(metadata, ("doc_id", "document_id", "uid", "id"), ""))
            for index, question in enumerate(_first(document, ("questions", "qa", "qas"), []) or []):
                if not isinstance(question, dict):
                    continue
                question_id = str(_first(question, ("uid", "question_id", "id", "qid"), f"{document_id}:{index}"))
                block_mapping = question.get("block_mapping")
                if not isinstance(block_mapping, list) or not block_mapping:
                    continue
                expected_blocks = sorted({
                    str(block_id)
                    for mapping in block_mapping
                    if isinstance(mapping, dict)
                    for block_id in mapping
                })
                if not expected_blocks:
                    continue
                questions.append({
                    "document_id": document_id,
                    "source_split": source_split,
                    "question_id": question_id,
                    "question": question.get("question"),
                    "answer": question.get("answer"),
                    "answer_type": question.get("answer_type"),
                    "block_mapping": block_mapping,
                    "expected_block_ids": expected_blocks,
                })
    return questions


def select_r_samples() -> list[dict[str, Any]]:
    by_document: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for question in load_tatqa_questions():
        key = (question["source_split"], question["document_id"])
        by_document.setdefault(key, []).append(question)

    candidates = [
        (key, sorted(rows, key=lambda row: stable_rank("R-question", row["question_id"])))
        for key, rows in by_document.items()
        if len(rows) >= INJECTIONS_PER_CLUSTER
    ]
    candidates.sort(key=lambda item: stable_rank("R-cluster", f"{item[0][0]}:{item[0][1]}"))
    selected = candidates[:CLUSTERS_PER_STAGE]
    if len(selected) < CLUSTERS_PER_STAGE:
        raise RuntimeError(f"R stage needs {CLUSTERS_PER_STAGE} clusters, found {len(selected)}")

    samples: list[dict[str, Any]] = []
    for (source_split, document_id), rows in selected:
        for repeat, question in enumerate(rows[:INJECTIONS_PER_CLUSTER], start=1):
            sample_id = f"R-{document_id}-{question['question_id']}-{repeat}"
            samples.append({
                "sample_id": sample_id,
                "stage": R_STAGE,
                "stage_name": STAGE_NAMES[R_STAGE],
                "cluster_id": f"R:{source_split}:{document_id}",
                "repeat_within_cluster": repeat,
                "source_object": {
                    "paths": [str(path) for path in TATQA_FILES],
                    "source_split": source_split,
                    "document_id": document_id,
                    "question_id": question["question_id"],
                    "question_sha256": json_hash(question["question"]),
                    "answer_sha256": json_hash(question["answer"]),
                    "expected_block_ids": question["expected_block_ids"],
                    "block_mapping": question["block_mapping"],
                },
                "injection_operation": "remove_required_source_blocks_from_retrieval_candidate_bundle",
                "injection_location": "retrieval evidence bundle before answer generation",
                "expected_first_affected_stage": R_STAGE,
                "expected_first_checkpoint": "qa.retrieval.source_required",
                "direct_target_leaf": "qa.retrieval.source_required",
                "potential_downstream_leaves": [
                    "qa.faithfulness.judge",
                    "qa.numeric.number_grounding",
                    "qa.citation.judge",
                ],
                "deterministic_or_judge": "target deterministic; downstream leaves secondary/judge",
                "gold_rule": "expected stage is fixed by required-block removal and pipeline consumption order before scoring",
                "success_condition": "source_required fails on the paired injected bundle while question and answer hashes remain unchanged",
                "null_interpretation": "required evidence is absent but downstream signatures do not separate the R class",
                "failure_interpretation": "missing source bundle, ambiguous required blocks, question/answer change, or semantic mutation outside evidence availability",
                "harmfulness": "NOT_YET_DEFINED_DO_NOT_REUSE_STAGE_E_H_HI_E",
                "leakage_control": {
                    "selection": "stable source-ID hash; retrieval outputs and evaluator scores are not read",
                    "gold": "required block IDs and spans frozen from raw block_mapping before perturbation",
                    "judge": "no LLM or judge in sample generation",
                },
                "generation_smoke": {
                    "question_unchanged": True,
                    "answer_unchanged": True,
                    "required_blocks_removed": question["expected_block_ids"],
                },
            })
    return samples


def _total_like(label: str) -> bool:
    text = label.casefold()
    return any(token in text for token in ("total", "subtotal", "合计", "总计", "小计"))


def find_numeric_identities(table: list[list[Any]]) -> list[dict[str, Any]]:
    identities: list[dict[str, Any]] = []
    if not table:
        return identities

    header_rows = table[:2]
    for col in range(1, max((len(row) for row in header_rows), default=0)):
        headers = [str(row[col]).strip() for row in header_rows if col < len(row) and row[col] not in (None, "")]
        if not any("total" in header.casefold() or "合计" in header or "总计" in header for header in headers):
            continue
        for row_index, row in enumerate(table):
            if col >= len(row):
                continue
            rhs = parse_number(row[col])
            operand_cells: list[dict[str, Any]] = []
            for operand_col in range(1, col):
                if operand_col >= len(row):
                    continue
                value = parse_number(row[operand_col])
                if value is not None:
                    operand_cells.append({"row": row_index, "col": operand_col, "value": value})
            if len(operand_cells) < 2 or rhs is None:
                continue
            lhs = sum(cell["value"] for cell in operand_cells)
            if abs(lhs - rhs) <= FLOAT_TOLERANCE:
                identities.append({
                    "kind": "row_total",
                    "lhs_cells": operand_cells,
                    "rhs_cell": {"row": row_index, "col": col, "value": rhs},
                    "expression": " + ".join(f"r{cell['row']}c{cell['col']}" for cell in operand_cells)
                    + f" = r{row_index}c{col}",
                    "residual": lhs - rhs,
                })

    for col in range(1, max((len(row) for row in table), default=0)):
        for row_index, row in enumerate(table):
            if col >= len(row):
                continue
            label = str(row[0] if row else "")
            rhs = parse_number(row[col])
            if rhs is None or not _total_like(label):
                continue
            operand_cells: list[dict[str, Any]] = []
            for source_row in range(row_index - 1, max(-1, row_index - 9), -1):
                source = table[source_row]
                if col >= len(source):
                    break
                source_label = str(source[0] if source else "")
                if _total_like(source_label):
                    break
                value = parse_number(source[col])
                if value is None:
                    if operand_cells:
                        break
                    continue
                operand_cells.append({"row": source_row, "col": col, "value": value})
            operand_cells.reverse()
            if len(operand_cells) < 2:
                continue
            lhs = sum(cell["value"] for cell in operand_cells)
            if abs(lhs - rhs) <= FLOAT_TOLERANCE:
                identities.append({
                    "kind": "column_total",
                    "lhs_cells": operand_cells,
                    "rhs_cell": {"row": row_index, "col": col, "value": rhs},
                    "expression": " + ".join(f"r{cell['row']}c{cell['col']}" for cell in operand_cells)
                    + f" = r{row_index}c{col}",
                    "residual": lhs - rhs,
                })

    unique: dict[str, dict[str, Any]] = {}
    for identity in identities:
        key = canonical_json(identity)
        unique[sha256_bytes(key.encode("utf-8"))[:16]] = identity
    return list(unique.values())


def mutate_identity_value(value: float, key: str) -> float:
    direction = 1 if int(stable_rank("N-direction", key)[:2], 16) % 2 == 0 else -1
    delta = max(abs(value) * 0.01, 0.02)
    return value + direction * delta


def identity_passes(identity: dict[str, Any], replacements: dict[tuple[int, int], float]) -> bool:
    lhs = 0.0
    for cell in identity["lhs_cells"]:
        key = (int(cell["row"]), int(cell["col"]))
        lhs += replacements.get(key, float(cell["value"]))
    rhs_cell = identity["rhs_cell"]
    rhs = replacements.get((int(rhs_cell["row"]), int(rhs_cell["col"])), float(rhs_cell["value"]))
    return abs(lhs - rhs) <= FLOAT_TOLERANCE


def select_n_samples(tables: list[dict[str, Any]], excluded_uids: set[str]) -> list[dict[str, Any]]:
    candidates: list[tuple[str, dict[str, Any], list[dict[str, Any]], list[tuple[int, int, float, str]]]] = []
    for record in tables:
        uid = str(record["uid"])
        if uid in excluded_uids:
            continue
        identities = find_numeric_identities(record.get("table") or [])
        operands: list[tuple[int, int, float, str]] = []
        for identity in identities:
            identity_key = canonical_json(identity)
            for cell in identity["lhs_cells"]:
                operands.append((
                    int(cell["row"]),
                    int(cell["col"]),
                    float(cell["value"]),
                    identity_key,
                ))
        operands = list({(row, col, value, key): (row, col, value, key) for row, col, value, key in operands}.values())
        if identities and len(operands) >= INJECTIONS_PER_CLUSTER:
            candidates.append((uid, record, identities, operands))

    candidates.sort(key=lambda item: stable_rank("N-cluster", item[0]))
    selected = candidates[:CLUSTERS_PER_STAGE]
    if len(selected) < CLUSTERS_PER_STAGE:
        raise RuntimeError(f"N stage needs {CLUSTERS_PER_STAGE} clusters, found {len(selected)}")

    samples: list[dict[str, Any]] = []
    for uid, record, identities, operands in selected:
        ordered_operands = sorted(
            operands,
            key=lambda item: stable_rank("N-operand", f"{uid}:{item[0]}:{item[1]}:{item[3]}"),
        )[:INJECTIONS_PER_CLUSTER]
        for repeat, (row, col, value, identity_key) in enumerate(ordered_operands, start=1):
            matching = next(identity for identity in identities if canonical_json(identity) == identity_key)
            mutated = mutate_identity_value(value, f"{uid}:{row}:{col}:{repeat}")
            sample_id = f"N-{uid}-r{row}c{col}-{repeat}"
            replacement = {(row, col): mutated}
            samples.append({
                "sample_id": sample_id,
                "stage": N_STAGE,
                "stage_name": STAGE_NAMES[N_STAGE],
                "cluster_id": f"N:{uid}",
                "repeat_within_cluster": repeat,
                "source_object": {
                    "path": str(TABLES.relative_to(ROOT)),
                    "uid": uid,
                    "table_sha256": json_hash(record["table"]),
                    "identity": matching,
                    "mutated_cell": {"row": row, "col": col},
                },
                "injection_operation": "mutate_one_numeric_operand_while_preserving_labels_schema_and_identity_contract",
                "injection_location": "numeric table input before reconciliation",
                "value_before": value,
                "value_after": mutated,
                "expected_first_affected_stage": N_STAGE,
                "expected_first_checkpoint": "parse.reconcile.equations",
                "direct_target_leaf": "parse.reconcile.equations",
                "potential_downstream_leaves": [
                    "qa.numeric.exact",
                    "qa.numeric.number_grounding",
                    "final_output",
                ],
                "deterministic_or_judge": "deterministic",
                "gold_rule": "expected stage is fixed by operand mutation and pipeline consumption order before scoring",
                "success_condition": "the preregistered identity passes before mutation and fails after mutation",
                "null_interpretation": "identity fails but M/R/N signatures do not separate the N class",
                "failure_interpretation": "identity not valid before mutation, mutation fails to break it, schema/labels change, or final semantics cannot be interpreted",
                "final_answer_effect": "may change when the mutated operand is answer-relevant; final-answer change is not the localization gold",
                "harmfulness": "NOT_YET_DEFINED_EQUIVALENCE_AND_QUESTION_DEPENDENT",
                "generation_smoke": {
                    "original_identity_pass": identity_passes(matching, {}),
                    "mutated_identity_pass": identity_passes(matching, replacement),
                    "shape_unchanged": True,
                },
            })
    return samples


def build(out_path: Path) -> dict[str, Any]:
    tables = json.loads(TABLES.read_text(encoding="utf-8"))
    tree = json.loads(CHECKPOINT_TREES.read_text(encoding="utf-8"))
    m_samples = select_m_samples(tables)
    r_samples = select_r_samples()
    n_samples = select_n_samples(tables, {sample["source_object"]["uid"] for sample in m_samples})

    for sample in n_samples:
        smoke = sample["generation_smoke"]
        if not smoke["original_identity_pass"] or smoke["mutated_identity_pass"]:
            raise RuntimeError(f"N generation smoke failed: {sample['sample_id']}")

    counts = {
        stage: {
            "clusters": len({sample["cluster_id"] for sample in samples}),
            "injections": len(samples),
        }
        for stage, samples in ((M_STAGE, m_samples), (R_STAGE, r_samples), (N_STAGE, n_samples))
    }
    ready = all(
        item["clusters"] == CLUSTERS_PER_STAGE and item["injections"] == CLUSTERS_PER_STAGE * INJECTIONS_PER_CLUSTER
        for item in counts.values()
    )

    payload = {
        "namespace": "STAGE_E_MULTILEAF_EXECUTION_FREEZE",
        "status": "MULTILEAF_READY_FOR_EXECUTION" if ready else "MULTILEAF_BLOCKED",
        "formal_experiment_executed": False,
        "selection_seed": SEED,
        "selection_rule": "ascending SHA-256 of seed:namespace:key; no evaluator output or visibility result is read",
        "unit": "stage-namespaced table/document/origin cluster; three injections remain repeated measurements",
        "stage_classes": STAGE_NAMES,
        "clusters_per_stage": CLUSTERS_PER_STAGE,
        "injections_per_cluster": INJECTIONS_PER_CLUSTER,
        "counts": counts,
        "source_hashes": {
            str(TABLES.relative_to(ROOT)): sha256_file(TABLES),
            str(CHECKPOINT_TREES.relative_to(ROOT)): sha256_file(CHECKPOINT_TREES),
            **{str(path): sha256_file(path) for path in TATQA_FILES},
        },
        "generator": {
            "path": str(Path(__file__).resolve().relative_to(ROOT)),
            "sha256": sha256_file(Path(__file__).resolve()),
        },
        "predictor_contract": {
            "input": "all leaves from config/eval_checkpoint_trees.json in frozen tree order; binary paired response vector",
            "classifier": "deterministic nearest-centroid with Euclidean distance on leave-one-cluster-out training folds",
            "classes": [M_STAGE, R_STAGE, N_STAGE],
            "primary_metrics": ["macro-F1", "top-1 stage accuracy"],
            "tie_rule": "a distance tie is scored incorrect; M/R/N lexical order is used only to serialize a deterministic output",
            "chance_top1": 1 / 3,
            "majority_baseline": "predict the first frozen class M; top-1=1/3 and macro-F1=1/6 on the balanced freeze",
            "signature_separability": "leave-one-cluster-out macro-F1 compared with a cluster-label permutation null",
            "permutation_seed": 20261011,
            "permutation_replicates": 10000,
            "bootstrap_seed": 20261012,
            "bootstrap_replicates": 10000,
            "claim_boundary": "checkpoint visibility signatures contain stage-localizing information; hierarchy itself is not claimed to localize",
        },
        "samples": {
            M_STAGE: m_samples,
            R_STAGE: r_samples,
            N_STAGE: n_samples,
        },
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    payload = build(args.out)
    print(json.dumps({
        "status": payload["status"],
        "counts": payload["counts"],
        "output": str(args.out),
        "generator_sha256": payload["generator"]["sha256"],
    }, ensure_ascii=False))
    return 0 if payload["status"] == "MULTILEAF_READY_FOR_EXECUTION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
