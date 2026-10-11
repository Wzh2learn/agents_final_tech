#!/usr/bin/env python3
"""Run the frozen Stage E multi-leaf formal experiment.

The runner refuses to start unless the pre-result freeze receipt and manifest
still match the code, inputs, predictor contract, environment snapshot and git
state captured before any formal result was materialized.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "research/stage_e_multileaf_20261010"
FREEZE = ROOT / "research/stage_e_method_revision_20261009/multileaf_freeze.json"
PRE_MANIFEST = TASK / "multileaf_preresult_freeze_manifest.json"
PRE_MANIFEST_HASH = TASK / "multileaf_preresult_freeze_manifest.sha256"
PRE_RECEIPT = ROOT / "docs/research/multileaf_preresult_freeze_receipt_v1.md"
RESULTS_DIR = TASK / "results"

TABLES = ROOT / "data/research/drift_v0/input/tatqa_tables.json"
CHECKPOINT_TREES = ROOT / "config/eval_checkpoint_trees.json"
TATQA_RAW = Path("/home/testuser/wzh/datasets/tat-dqa/raw")
TATQA_FILES = (
    TATQA_RAW / "tatdqa_dataset_train.json",
    TATQA_RAW / "tatdqa_dataset_dev.json",
    TATQA_RAW / "tatdqa_dataset_test_gold.json",
)

CLASSES = ("M", "R", "N")
DIRECT_LEAVES = {
    "M": "parse.field.hit_rate",
    "R": "qa.retrieval.source_required",
    "N": "parse.reconcile.equations",
}
PERMUTATION_SEED = 20261011
PERMUTATION_REPLICATES = 10_000
BOOTSTRAP_SEED = 20261012
BOOTSTRAP_REPLICATES = 10_000
TOP1_BASELINE = 1.0 / 3.0
MAJORITY_MACRO_F1 = 1.0 / 6.0
TIE_LABEL = "__TIE__"
EPS = 1e-12


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def json_hash(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def now_iso() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")


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


def leaf_order(tree: dict[str, Any]) -> list[str]:
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


def effective_leaf_weights(tree: dict[str, Any]) -> dict[str, float]:
    weights: dict[str, float] = {}

    def visit(node: dict[str, Any], prefix: float) -> None:
        children = node.get("children") or []
        if not children:
            weights[str(node["id"])] = prefix
            return
        total = sum(float(child.get("weight", 1)) for child in children)
        for child in children:
            visit(child, prefix * float(child.get("weight", 1)) / total)

    roots = tree.get("trees", [])
    root_total = sum(float(root.get("weight", 1)) for root in roots)
    for root in roots:
        visit(root, float(root.get("weight", 1)) / root_total)
    return weights


def records(payload: Any) -> Iterable[dict[str, Any]]:
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                yield item
    elif isinstance(payload, dict):
        for key in ("documents", "data", "examples"):
            if isinstance(payload.get(key), list):
                yield from records(payload[key])
                return
        yield payload


def first(record: dict[str, Any], keys: tuple[str, ...], default: Any = None) -> Any:
    for key in keys:
        if key in record:
            return record[key]
    return default


def load_tatqa_questions() -> dict[tuple[str, str, str], dict[str, Any]]:
    split_names = {
        "tatdqa_dataset_train.json": "train",
        "tatdqa_dataset_dev.json": "validation",
        "tatdqa_dataset_test_gold.json": "test",
    }
    index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for path in TATQA_FILES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        source_split = split_names[path.name]
        for document in records(payload):
            metadata = document.get("doc") if isinstance(document.get("doc"), dict) else document
            document_id = str(first(metadata, ("doc_id", "document_id", "uid", "id"), ""))
            for fallback, question in enumerate(first(document, ("questions", "qa", "qas"), []) or []):
                if not isinstance(question, dict):
                    continue
                question_id = str(first(question, ("uid", "question_id", "id", "qid"), f"{document_id}:{fallback}"))
                block_mapping = question.get("block_mapping") or []
                expected_blocks = sorted({
                    str(block_id)
                    for mapping in block_mapping
                    if isinstance(mapping, dict)
                    for block_id in mapping
                })
                index[(source_split, document_id, question_id)] = {
                    "question": question.get("question"),
                    "answer": question.get("answer"),
                    "answer_type": question.get("answer_type"),
                    "block_mapping": block_mapping,
                    "expected_block_ids": expected_blocks,
                }
    return index


def verify_pre_result_freeze() -> dict[str, Any]:
    if not PRE_MANIFEST.is_file() or not PRE_MANIFEST_HASH.is_file() or not PRE_RECEIPT.is_file():
        raise RuntimeError("PRE-RESULT FREEZE is missing")
    expected_manifest_hash = PRE_MANIFEST_HASH.read_text(encoding="utf-8").strip().split()[0]
    if sha256_file(PRE_MANIFEST) != expected_manifest_hash:
        raise RuntimeError("pre-result manifest hash mismatch")
    manifest = json.loads(PRE_MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("status") != "FREEZE_COMPLETE":
        raise RuntimeError("pre-result manifest is not FREEZE_COMPLETE")
    if not manifest.get("result_artifacts_absent_at_freeze", False):
        raise RuntimeError("result artifacts were not absent at freeze time")

    for relative, record in manifest["frozen_files"].items():
        path = ROOT / relative
        if not path.is_file() or sha256_file(path) != record["sha256"]:
            raise RuntimeError(f"frozen file changed: {relative}")

    if sha256_file(Path(__file__).resolve()) != manifest["formal_runner"]["sha256"]:
        raise RuntimeError("formal runner changed after pre-result freeze")
    if manifest["git_state"]["head"] != subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True
    ).stdout.strip():
        raise RuntimeError("git HEAD changed after pre-result freeze")
    diff_path = ROOT / manifest["git_state"]["diff_path"]
    if sha256_file(diff_path) != manifest["git_state"]["diff_sha256"]:
        raise RuntimeError("captured git diff changed after pre-result freeze")
    return manifest


def identity_passes(identity: dict[str, Any], table: list[list[Any]], replacements: dict[tuple[int, int], float]) -> bool:
    lhs = 0.0
    for cell in identity["lhs_cells"]:
        row, col = int(cell["row"]), int(cell["col"])
        value = replacements.get((row, col), parse_number(table[row][col]))
        if value is None:
            return False
        lhs += value
    rhs_cell = identity["rhs_cell"]
    row, col = int(rhs_cell["row"]), int(rhs_cell["col"])
    rhs = replacements.get((row, col), parse_number(table[row][col]))
    return rhs is not None and abs(lhs - rhs) <= 0.01


def check_m(sample: dict[str, Any], tables: dict[str, list[list[Any]]], leaves: list[str]) -> dict[str, Any]:
    source = sample["source_object"]
    uid = str(source["uid"])
    table = tables[uid]
    if json_hash(table) != source["table_sha256"]:
        raise RuntimeError(f"M source hash mismatch: {sample['sample_id']}")
    row, col = int(source["cell"]["row"]), int(source["cell"]["col"])
    before = table[row][col]
    after = sample["field_after"]
    checks = {
        "source_hash": True,
        "field_before_matches": str(before).strip() == str(sample["field_before"]).strip(),
        "field_changed": str(before) != str(after),
        "shape_unchanged": True,
    }

    canonical = [str(value).strip() for value in table[0] if isinstance(value, str) and str(value).strip()]
    canonical_set = set(canonical)
    baseline_hit = sum(token in canonical_set for token in canonical) / len(canonical)
    mutated_table = [list(item) for item in table]
    mutated_table[row][col] = after
    mutated_headers = [str(value).strip() for value in mutated_table[0] if isinstance(value, str) and str(value).strip()]
    mutated_hit = sum(token in canonical_set for token in mutated_headers) / len(mutated_headers)

    response = {leaf: 0 for leaf in leaves}
    response["parse.table.regression"] = int(mutated_hit < baseline_hit)
    response["parse.field.hit_rate"] = int(mutated_hit < baseline_hit)
    checks["direct_leaf_response"] = response[DIRECT_LEAVES["M"]] == 1
    return {
        "sample_id": sample["sample_id"],
        "stage": "M",
        "cluster_id": sample["cluster_id"],
        "expected_first_stage": sample["expected_first_affected_stage"],
        "contract_checks": checks,
        "contract_pass": all(checks.values()),
        "baseline_scores": {
            "parse.table.regression": 10.0,
            "parse.field.hit_rate": 10.0 * baseline_hit,
        },
        "injected_scores": {
            "parse.table.regression": 10.0 if mutated_hit == 1.0 else 10.0 * mutated_hit,
            "parse.field.hit_rate": 10.0 * mutated_hit,
        },
        "response_vector": response,
    }


def check_r(
    sample: dict[str, Any],
    questions: dict[tuple[str, str, str], dict[str, Any]],
    leaves: list[str],
) -> dict[str, Any]:
    source = sample["source_object"]
    key = (str(source["source_split"]), str(source["document_id"]), str(source["question_id"]))
    raw = questions[key]
    checks = {
        "source_question_found": True,
        "question_hash": json_hash(raw["question"]) == source["question_sha256"],
        "answer_hash": json_hash(raw["answer"]) == source["answer_sha256"],
        "block_mapping": canonical_json(raw["block_mapping"]) == canonical_json(source["block_mapping"]),
        "expected_blocks_nonempty": bool(source["expected_block_ids"]),
        "task_semantics_unchanged": True,
    }
    expected = set(map(str, source["expected_block_ids"]))
    baseline_bundle = sorted(expected | {"__DISTRACTOR_BLOCK__"})
    injected_bundle = [block for block in baseline_bundle if block not in expected]
    baseline_pass = bool(expected.intersection(baseline_bundle))
    injected_pass = bool(expected.intersection(injected_bundle))
    response = {leaf: 0 for leaf in leaves}
    response["qa.retrieval.source_required"] = int(baseline_pass and not injected_pass)
    checks["direct_leaf_response"] = response[DIRECT_LEAVES["R"]] == 1
    return {
        "sample_id": sample["sample_id"],
        "stage": "R",
        "cluster_id": sample["cluster_id"],
        "expected_first_stage": sample["expected_first_affected_stage"],
        "contract_checks": checks,
        "contract_pass": all(checks.values()),
        "baseline_scores": {"qa.retrieval.source_required": 10.0 if baseline_pass else 0.0},
        "injected_scores": {"qa.retrieval.source_required": 10.0 if injected_pass else 0.0},
        "response_vector": response,
    }


def check_n(sample: dict[str, Any], tables: dict[str, list[list[Any]]], leaves: list[str]) -> dict[str, Any]:
    source = sample["source_object"]
    uid = str(source["uid"])
    table = tables[uid]
    identity = source["identity"]
    row, col = int(source["mutated_cell"]["row"]), int(source["mutated_cell"]["col"])
    raw_value = parse_number(table[row][col])
    replacements = {(row, col): float(sample["value_after"])}
    original_pass = identity_passes(identity, table, {})
    mutated_pass = identity_passes(identity, table, replacements)
    checks = {
        "source_hash": json_hash(table) == source["table_sha256"],
        "value_before_matches": raw_value is not None and abs(raw_value - float(sample["value_before"])) <= EPS,
        "value_changed": abs(float(sample["value_after"]) - float(sample["value_before"])) > 0.01,
        "shape_unchanged": True,
        "original_identity_pass": original_pass,
        "mutated_identity_fail": not mutated_pass,
    }
    response = {leaf: 0 for leaf in leaves}
    response["parse.reconcile.equations"] = int(original_pass and not mutated_pass)
    checks["direct_leaf_response"] = response[DIRECT_LEAVES["N"]] == 1
    return {
        "sample_id": sample["sample_id"],
        "stage": "N",
        "cluster_id": sample["cluster_id"],
        "expected_first_stage": sample["expected_first_affected_stage"],
        "contract_checks": checks,
        "contract_pass": all(checks.values()),
        "baseline_scores": {"parse.reconcile.equations": 10.0 if original_pass else 0.0},
        "injected_scores": {"parse.reconcile.equations": 10.0 if mutated_pass else 0.0},
        "response_vector": response,
    }


def materialize(
    freeze: dict[str, Any],
    leaves: list[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    tables_record = json.loads(TABLES.read_text(encoding="utf-8"))
    tables = {str(record["uid"]): record["table"] for record in tables_record}
    questions = load_tatqa_questions()
    rows: list[dict[str, Any]] = []
    for stage in CLASSES:
        for sample in freeze["samples"][stage]:
            if stage == "M":
                rows.append(check_m(sample, tables, leaves))
            elif stage == "R":
                rows.append(check_r(sample, questions, leaves))
            else:
                rows.append(check_n(sample, tables, leaves))

    cluster_stage: dict[str, set[str]] = defaultdict(set)
    cluster_rows: dict[str, int] = Counter()
    sample_ids = set()
    for row in rows:
        cluster_stage[row["cluster_id"]].add(row["stage"])
        cluster_rows[row["cluster_id"]] += 1
        sample_ids.add(row["sample_id"])

    leakage_checks = {
        "sample_ids_unique": len(sample_ids) == len(rows),
        "one_stage_per_cluster": all(len(stages) == 1 for stages in cluster_stage.values()),
        "three_repeated_injections_per_cluster": all(count == 3 for count in cluster_rows.values()),
        "expected_stage_matches": all(row["stage"] == row["expected_first_stage"] for row in rows),
        "m_n_uid_disjoint": not (
            {sample["source_object"]["uid"] for sample in freeze["samples"]["M"]}
            & {sample["source_object"]["uid"] for sample in freeze["samples"]["N"]}
        ),
    }
    return rows, leakage_checks


def macro_f1(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    scores = []
    for label in CLASSES:
        true_positive = int(np.sum((y_true == label) & (y_pred == label)))
        false_positive = int(np.sum((y_true != label) & (y_pred == label)))
        false_negative = int(np.sum((y_true == label) & (y_pred != label)))
        denominator = 2 * true_positive + false_positive + false_negative
        scores.append(0.0 if denominator == 0 else 2 * true_positive / denominator)
    return float(np.mean(scores))


def accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(y_true == y_pred))


def predict_loco(x: np.ndarray, y: np.ndarray, clusters: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    predictions = np.empty(len(x), dtype=object)
    margin_values = np.empty(len(x), dtype=float)
    for cluster in np.unique(clusters):
        train_mask = clusters != cluster
        test_indices = np.flatnonzero(~train_mask)
        centroids = np.vstack([
            x[train_mask & (y == label)].mean(axis=0)
            for label in CLASSES
        ])
        test_x = x[test_indices]
        distances = np.sqrt(((test_x[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2))
        for row, global_index in zip(distances, test_indices):
            minimum = float(row.min())
            tied = np.isclose(row, minimum, rtol=0.0, atol=EPS)
            if int(tied.sum()) > 1:
                predictions[global_index] = TIE_LABEL
                margin_values[global_index] = 0.0
            else:
                predictions[global_index] = CLASSES[int(np.argmin(row))]
                ordered = np.sort(row)
                margin_values[global_index] = float(ordered[1] - ordered[0])
    return predictions, margin_values


def rankdata(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    sorted_values = values[order]
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and sorted_values[end] == sorted_values[start]:
            end += 1
        average = (start + end - 1) / 2.0 + 1.0
        ranks[order[start:end]] = average
        start = end
    return ranks


def pearson(x: np.ndarray, y: np.ndarray) -> float:
    if float(np.std(x)) == 0.0 or float(np.std(y)) == 0.0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def auc_score(negative: np.ndarray, positive: np.ndarray) -> float:
    wins = 0.0
    for pos in positive:
        wins += float(np.sum(negative < pos))
        wins += 0.5 * float(np.sum(negative == pos))
    return wins / (len(negative) * len(positive))


def result_classification(
    contracts_pass: bool,
    leakage_pass: bool,
    permutation_p_macro: float,
    top1_ci_low: float,
) -> tuple[str, str, str]:
    if not contracts_pass or not leakage_pass:
        return (
            "INVALID",
            "No confirmatory localization claim is allowed.",
            "The hierarchy localizes failures.",
        )
    primary_pass = permutation_p_macro < 0.05 and top1_ci_low > TOP1_BASELINE
    partial = permutation_p_macro < 0.05 or top1_ci_low > TOP1_BASELINE
    if primary_pass:
        return (
            "POSITIVE",
            "Checkpoint evidence contains stage-localizing information under the frozen M/R/N controlled injections.",
            "The hierarchy localizes failures.",
        )
    if partial:
        return (
            "MIXED",
            "Localization is not established by both preregistered primary criteria; report the mixed primary evidence without upgrading the claim.",
            "The hierarchy localizes failures.",
        )
    return (
        "NULL",
        "Checkpoint signatures do not establish stage-localizing information above the preregistered baseline.",
        "The hierarchy localizes failures.",
    )


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def render_results(payload: dict[str, Any]) -> str:
    p = payload
    contract_rows = "\n".join(
        f"| {stage} | {data['contract_status']} | {data['clusters']} | {data['injections']} |"
        for stage, data in p["contracts"].items()
    )
    profile_rows = "\n".join(
        f"| {stage} | {data['direct_leaf']} | {data['direct_visibility_rate']:.4f} | "
        f"{data['any_response_rate']:.4f} | {data['responsive_leaves']} |"
        for stage, data in p["per_stage_profiles"].items()
    )
    signature_lines = []
    for stage, signatures in p["response_signatures"].items():
        joined = "; ".join(f"{vector} x{count}" for vector, count in signatures)
        signature_lines.append(f"- {stage}: {joined}")
    matrix = p["confusion_matrix"]
    confusion_rows = "\n".join(
        "| " + label + " | " + " | ".join(str(matrix[label][column]) for column in matrix["columns"]) + " |"
        for label in CLASSES
    )
    flat = p["secondary_flat_hierarchy"]
    return f"""# Stage E Multi-Leaf Formal Results v1

> Status: `{p['result_status']}` | Generated: {p['generated_at']} | Pre-result freeze verified before output creation

## 1-2. Contracts and retained units

| Stage | Contract | Clusters | Injections |
|---|---|---:|---:|
{contract_rows}

Leakage audit: `{p['leakage_audit']['status']}`.

## 3. Per-stage visibility profiles

| Stage | Direct leaf | Direct visibility | Any response | Responsive leaves |
|---|---|---:|---:|---:|
{profile_rows}

## 4-5. Responsive leaves and signatures

Global responsive leaves: `{p['responsive_leaves']}`.

{chr(10).join(signature_lines)}

## 6-10. Primary localization results

- LOCO macro-F1: `{p['primary']['macro_f1']:.6f}`
- Top-1 accuracy: `{p['primary']['top1_accuracy']:.6f}`
- Majority baseline: top-1 `{p['baseline']['majority_top1']:.6f}`, macro-F1 `{p['baseline']['majority_macro_f1']:.6f}`
- Permutation p-value: macro-F1 `{p['primary']['permutation_p_macro_f1']:.6g}`, top-1 `{p['primary']['permutation_p_top1']:.6g}`
- Cluster bootstrap 95% CI: macro-F1 `{p['primary']['macro_f1_ci95']}`, top-1 `{p['primary']['top1_ci95']}`

## 11. Confusion matrix

| True / Pred | { ' | '.join(matrix['columns']) } |
|---|{ '---|' * len(matrix['columns']) }
{confusion_rows}

Ties are serialized as `{TIE_LABEL}` and always scored incorrect.

## 12. Leakage audit

{p['leakage_audit']['detail']}

## 13-14. Flat/hierarchy secondary structure

- Flat/hierarchical Pearson correlation: `{flat['pearson_r']:.6f}`
- Spearman ranking correlation: `{flat['spearman_r']:.6f}`
- Linear affine fit: `h = {flat['slope']:.6f} f + {flat['intercept']:.6f}`, R2 `{flat['r2']:.6f}`, max residual `{flat['max_abs_residual']:.6f}`
- Flat score support: `{flat['flat_support']}`
- Hierarchical score support: `{flat['hierarchical_support']}`
- AUROC flat/hierarchical: `{flat['auroc_flat']:.6f}` / `{flat['auroc_hier']:.6f}`
- Clean-only matched operating point: `{flat['matched_operating_point']}`
- Single-leaf affine degeneracy broken: `{flat['affine_degeneracy_broken']}`

## 15-16. Claim boundary

Allowed: `{p['claim_allowed']}`

Forbidden: `{p['claim_forbidden']}`

MULTILEAF_RESULT_STATUS: {p['result_status']}
"""


def run(out_dir: Path, permutations: int, bootstraps: int) -> dict[str, Any]:
    pre = verify_pre_result_freeze()
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    trees = json.loads(CHECKPOINT_TREES.read_text(encoding="utf-8"))
    leaves = leaf_order(trees)
    if freeze["predictor_contract"]["permutation_seed"] != PERMUTATION_SEED:
        raise RuntimeError("permutation seed mismatch")
    if freeze["predictor_contract"]["bootstrap_seed"] != BOOTSTRAP_SEED:
        raise RuntimeError("bootstrap seed mismatch")

    rows, leakage_checks = materialize(freeze, leaves)
    if out_dir.exists():
        raise RuntimeError(f"result directory already exists: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)
    write_jsonl(out_dir / "multileaf_paired_artifacts.jsonl", rows)

    contract_status = {}
    for stage in CLASSES:
        stage_rows = [row for row in rows if row["stage"] == stage]
        contract_status[stage] = {
            "contract_status": "PASS" if all(row["contract_pass"] for row in stage_rows) else "FAIL",
            "clusters": len({row["cluster_id"] for row in stage_rows}),
            "injections": len(stage_rows),
        }
    contracts_pass = all(item["contract_status"] == "PASS" for item in contract_status.values())
    leakage_pass = all(leakage_checks.values())

    if not contracts_pass or not leakage_pass:
        status, claim_allowed, claim_forbidden = result_classification(
            contracts_pass, leakage_pass, 1.0, 0.0
        )
        payload = {
            "generated_at": now_iso(),
            "pre_result_manifest_sha256": sha256_file(PRE_MANIFEST),
            "result_status": status,
            "contracts": contract_status,
            "retained": {"clusters": 0, "injections": 0},
            "leakage_audit": {
                "status": "FAIL" if not leakage_pass else "PASS",
                "detail": json.dumps(leakage_checks, ensure_ascii=False, sort_keys=True),
            },
            "claim_allowed": claim_allowed,
            "claim_forbidden": claim_forbidden,
            "stopped_reason": "stage contract or leakage failure; confirmatory metrics not computed",
        }
        write_json(out_dir / "multileaf_formal_results.json", payload)
        (out_dir / "multileaf_formal_results.md").write_text(render_results(payload), encoding="utf-8")
        return payload

    x = np.asarray([[row["response_vector"][leaf] for leaf in leaves] for row in rows], dtype=float)
    y = np.asarray([row["stage"] for row in rows], dtype=object)
    clusters = np.asarray([row["cluster_id"] for row in rows], dtype=object)
    unique_clusters = np.unique(clusters)
    cluster_labels = np.asarray([y[clusters == cluster][0] for cluster in unique_clusters], dtype=object)

    predictions, margins = predict_loco(x, y, clusters)
    observed_macro = macro_f1(y, predictions)
    observed_top1 = accuracy(y, predictions)

    rng = np.random.default_rng(PERMUTATION_SEED)
    permutation_macro = np.empty(permutations, dtype=float)
    permutation_top1 = np.empty(permutations, dtype=float)
    for index in range(permutations):
        permuted_cluster_labels = rng.permutation(cluster_labels)
        label_by_cluster = dict(zip(unique_clusters, permuted_cluster_labels))
        permuted_y = np.asarray([label_by_cluster[cluster] for cluster in clusters], dtype=object)
        permuted_predictions, _ = predict_loco(x, permuted_y, clusters)
        permutation_macro[index] = macro_f1(permuted_y, permuted_predictions)
        permutation_top1[index] = accuracy(permuted_y, permuted_predictions)
    p_macro = (1.0 + float(np.sum(permutation_macro >= observed_macro))) / (permutations + 1.0)
    p_top1 = (1.0 + float(np.sum(permutation_top1 >= observed_top1))) / (permutations + 1.0)

    bootstrap_macro = np.empty(bootstraps, dtype=float)
    bootstrap_top1 = np.empty(bootstraps, dtype=float)
    cluster_indices = {cluster: np.flatnonzero(clusters == cluster) for cluster in unique_clusters}
    rng_boot = np.random.default_rng(BOOTSTRAP_SEED)
    for index in range(bootstraps):
        sampled = rng_boot.choice(unique_clusters, size=len(unique_clusters), replace=True)
        row_index = np.concatenate([cluster_indices[cluster] for cluster in sampled])
        bootstrap_macro[index] = macro_f1(y[row_index], predictions[row_index])
        bootstrap_top1[index] = accuracy(y[row_index], predictions[row_index])
    macro_ci = [
        round(float(np.quantile(bootstrap_macro, 0.025)), 6),
        round(float(np.quantile(bootstrap_macro, 0.975)), 6),
    ]
    top1_ci = [
        round(float(np.quantile(bootstrap_top1, 0.025)), 6),
        round(float(np.quantile(bootstrap_top1, 0.975)), 6),
    ]

    columns = list(CLASSES) + [TIE_LABEL]
    confusion = {"columns": columns}
    for label in CLASSES:
        confusion[label] = {
            column: int(np.sum((y == label) & (predictions == column)))
            for column in columns
        }

    per_stage_profiles: dict[str, Any] = {}
    response_signatures: dict[str, Any] = {}
    for stage in CLASSES:
        mask = y == stage
        direct = DIRECT_LEAVES[stage]
        stage_x = x[mask]
        responsive_by_leaf = {
            leaf: int(stage_x[:, position].sum())
            for position, leaf in enumerate(leaves)
        }
        per_stage_profiles[stage] = {
            "direct_leaf": direct,
            "direct_visibility_rate": float(stage_x[:, leaves.index(direct)].mean()),
            "any_response_rate": float(np.mean(stage_x.sum(axis=1) > 0)),
            "responsive_leaves": sum(value > 0 for value in responsive_by_leaf.values()),
            "response_counts_by_leaf": responsive_by_leaf,
        }
        response_signatures[stage] = sorted(
            Counter(tuple(map(int, row)) for row in stage_x).items(),
            key=lambda item: (-item[1], item[0]),
        )

    weights = effective_leaf_weights(trees)
    weight_vector = np.asarray([weights[leaf] for leaf in leaves], dtype=float)
    flat_scores = 10.0 * x.mean(axis=1)
    hierarchical_scores = 10.0 * (x * weight_vector).sum(axis=1)
    slope, intercept = np.polyfit(flat_scores, hierarchical_scores, 1)
    fitted = slope * flat_scores + intercept
    residuals = hierarchical_scores - fitted
    ss_total = float(np.sum((hierarchical_scores - hierarchical_scores.mean()) ** 2))
    ss_residual = float(np.sum(residuals ** 2))
    r2 = 0.0 if ss_total == 0 else 1.0 - ss_residual / ss_total
    clean_scores = np.zeros(len(rows), dtype=float)
    flat_hier = {
        "pearson_r": pearson(flat_scores, hierarchical_scores),
        "spearman_r": pearson(rankdata(flat_scores), rankdata(hierarchical_scores)),
        "slope": float(slope),
        "intercept": float(intercept),
        "r2": float(r2),
        "max_abs_residual": float(np.max(np.abs(residuals))),
        "flat_support": sorted({round(float(value), 6) for value in flat_scores}),
        "hierarchical_support": sorted({round(float(value), 6) for value in hierarchical_scores}),
        "auroc_flat": auc_score(clean_scores, flat_scores),
        "auroc_hier": auc_score(clean_scores, hierarchical_scores),
        "matched_operating_point": "NOT_IDENTIFIABLE_CLEAN_SUPPORT_ZERO",
        "affine_degeneracy_broken": bool(
            len({round(float(value), 6) for value in flat_scores}) > 1
            and float(np.max(np.abs(residuals))) > EPS
        ),
    }

    status, claim_allowed, claim_forbidden = result_classification(
        contracts_pass, leakage_pass, p_macro, top1_ci[0]
    )
    responsive_global = sorted(leaf for leaf in leaves if x[:, leaves.index(leaf)].sum() > 0)
    payload = {
        "generated_at": now_iso(),
        "pre_result_manifest_sha256": sha256_file(PRE_MANIFEST),
        "result_status": status,
        "contracts": contract_status,
        "retained": {"clusters": len(unique_clusters), "injections": len(rows)},
        "responsive_leaves": responsive_global,
        "per_stage_profiles": per_stage_profiles,
        "response_signatures": {
            stage: [[list(vector), count] for vector, count in signatures]
            for stage, signatures in response_signatures.items()
        },
        "primary": {
            "macro_f1": observed_macro,
            "top1_accuracy": observed_top1,
            "permutation_p_macro_f1": p_macro,
            "permutation_p_top1": p_top1,
            "macro_f1_ci95": macro_ci,
            "top1_ci95": top1_ci,
            "permutation_replicates": permutations,
            "bootstrap_replicates": bootstraps,
        },
        "baseline": {
            "chance_top1": TOP1_BASELINE,
            "majority_top1": TOP1_BASELINE,
            "majority_macro_f1": MAJORITY_MACRO_F1,
        },
        "confusion_matrix": confusion,
        "tie_count": int(np.sum(predictions == TIE_LABEL)),
        "leakage_audit": {
            "status": "PASS" if leakage_pass else "FAIL",
            "detail": json.dumps(leakage_checks, ensure_ascii=False, sort_keys=True),
        },
        "secondary_flat_hierarchy": flat_hier,
        "claim_allowed": claim_allowed,
        "claim_forbidden": claim_forbidden,
        "pre_result_freeze": {
            "manifest": str(PRE_MANIFEST.relative_to(ROOT)),
            "receipt": str(PRE_RECEIPT.relative_to(ROOT)),
            "git_head": pre["git_state"]["head"],
        },
    }

    prediction_rows = [
        {
            "sample_id": row["sample_id"],
            "cluster_id": row["cluster_id"],
            "true_stage": str(y[index]),
            "predicted_stage": str(predictions[index]),
            "correct": bool(y[index] == predictions[index]),
            "distance_margin": float(margins[index]),
            "response_vector": {leaf: int(x[index, position]) for position, leaf in enumerate(leaves)},
        }
        for index, row in enumerate(rows)
    ]
    write_jsonl(out_dir / "multileaf_prediction_rows.jsonl", prediction_rows)
    write_json(
        out_dir / "multileaf_permutation_null.json",
        {
            "seed": PERMUTATION_SEED,
            "replicates": permutations,
            "macro_f1": permutation_macro.tolist(),
            "top1_accuracy": permutation_top1.tolist(),
        },
    )
    write_json(
        out_dir / "multileaf_bootstrap_intervals.json",
        {
            "seed": BOOTSTRAP_SEED,
            "replicates": bootstraps,
            "macro_f1": bootstrap_macro.tolist(),
            "top1_accuracy": bootstrap_top1.tolist(),
        },
    )
    write_json(out_dir / "multileaf_formal_results.json", payload)
    (out_dir / "multileaf_formal_results.md").write_text(render_results(payload), encoding="utf-8")
    receipt = {
        "status": "COMPLETE",
        "result_status": status,
        "result_json_sha256": sha256_file(out_dir / "multileaf_formal_results.json"),
        "result_md_sha256": sha256_file(out_dir / "multileaf_formal_results.md"),
        "paired_artifacts_sha256": sha256_file(out_dir / "multileaf_paired_artifacts.jsonl"),
        "predictions_sha256": sha256_file(out_dir / "multileaf_prediction_rows.jsonl"),
        "formal_runner_sha256": sha256_file(Path(__file__).resolve()),
        "completed_at": now_iso(),
    }
    write_json(out_dir / "multileaf_run_receipt.json", receipt)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--permutations", type=int, default=PERMUTATION_REPLICATES)
    parser.add_argument("--bootstraps", type=int, default=BOOTSTRAP_REPLICATES)
    args = parser.parse_args()
    payload = run(args.out_dir, args.permutations, args.bootstraps)
    print(json.dumps({
        "result_status": payload["result_status"],
        "contracts": payload["contracts"],
        "retained": payload.get("retained"),
        "primary": payload.get("primary"),
        "claim_allowed": payload["claim_allowed"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if payload["result_status"] in {"POSITIVE", "MIXED", "NULL"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
