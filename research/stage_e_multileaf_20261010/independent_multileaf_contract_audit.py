#!/usr/bin/env python3
"""Independently recompute M/R/N deterministic contracts without importing the runner."""
from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "research/stage_e_multileaf_20261010"
FREEZE = ROOT / "research/stage_e_method_revision_20261009/multileaf_freeze.json"
RESULTS = TASK / "results"
TABLES = ROOT / "data/research/drift_v0/input/tatqa_tables.json"
OUT = RESULTS / "independent_contract_audit.json"
TATQA_FILES = (
    Path("/home/testuser/wzh/datasets/tat-dqa/raw/tatdqa_dataset_train.json"),
    Path("/home/testuser/wzh/datasets/tat-dqa/raw/tatdqa_dataset_dev.json"),
    Path("/home/testuser/wzh/datasets/tat-dqa/raw/tatdqa_dataset_test_gold.json"),
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def json_hash(value: Any) -> str:
    return sha256_text(canonical_json(value))


def decimal_number(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return Decimal(str(value))
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
    try:
        number = Decimal(text)
    except InvalidOperation:
        return None
    return -number if negative else number


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


def load_questions() -> dict[tuple[str, str, str], dict[str, Any]]:
    split_names = {
        "tatdqa_dataset_train.json": "train",
        "tatdqa_dataset_dev.json": "validation",
        "tatdqa_dataset_test_gold.json": "test",
    }
    index = {}
    for path in TATQA_FILES:
        source_split = split_names[path.name]
        for document in records(json.loads(path.read_text(encoding="utf-8"))):
            metadata = document.get("doc") if isinstance(document.get("doc"), dict) else document
            document_id = str(first(metadata, ("doc_id", "document_id", "uid", "id"), ""))
            for fallback, question in enumerate(first(document, ("questions", "qa", "qas"), []) or []):
                question_id = str(first(question, ("uid", "question_id", "id", "qid"), f"{document_id}:{fallback}"))
                block_mapping = question.get("block_mapping") or []
                expected = sorted({
                    str(block_id)
                    for mapping in block_mapping
                    if isinstance(mapping, dict)
                    for block_id in mapping
                })
                index[(source_split, document_id, question_id)] = {
                    "question": question.get("question"),
                    "answer": question.get("answer"),
                    "block_mapping": block_mapping,
                    "expected": expected,
                }
    return index


def identity_status(identity: dict[str, Any], table: list[list[Any]], replacements: dict[tuple[int, int], Decimal]) -> bool:
    total = Decimal("0")
    for cell in identity["lhs_cells"]:
        row, col = int(cell["row"]), int(cell["col"])
        value = replacements.get((row, col), decimal_number(table[row][col]))
        if value is None:
            return False
        total += value
    rhs_cell = identity["rhs_cell"]
    row, col = int(rhs_cell["row"]), int(rhs_cell["col"])
    rhs = replacements.get((row, col), decimal_number(table[row][col]))
    return rhs is not None and abs(total - rhs) <= Decimal("0.01")


def main() -> int:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    paired = {
        row["sample_id"]: row
        for row in (
            json.loads(line)
            for line in (RESULTS / "multileaf_paired_artifacts.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }
    tables = {
        str(record["uid"]): record["table"]
        for record in json.loads(TABLES.read_text(encoding="utf-8"))
    }
    questions = load_questions()
    errors = []
    details = []

    for stage in ("M", "R", "N"):
        for sample in freeze["samples"][stage]:
            sample_id = sample["sample_id"]
            observed = paired[sample_id]
            source = sample["source_object"]
            if stage == "M":
                table = tables[str(source["uid"])]
                row, col = int(source["cell"]["row"]), int(source["cell"]["col"])
                expected_vector = {leaf: 0 for leaf in observed["response_vector"]}
                expected_vector["parse.table.regression"] = 1
                expected_vector["parse.field.hit_rate"] = 1
                checks = {
                    "source_hash": json_hash(table) == source["table_sha256"],
                    "field_before": str(table[row][col]).strip() == str(sample["field_before"]).strip(),
                    "field_after": sample["field_after"] != sample["field_before"],
                }
            elif stage == "R":
                key = (str(source["source_split"]), str(source["document_id"]), str(source["question_id"]))
                raw = questions[key]
                expected_vector = {leaf: 0 for leaf in observed["response_vector"]}
                expected_vector["qa.retrieval.source_required"] = 1
                checks = {
                    "question_hash": json_hash(raw["question"]) == source["question_sha256"],
                    "answer_hash": json_hash(raw["answer"]) == source["answer_sha256"],
                    "removal_contract_declared": sample["injection_operation"] == "remove_required_source_blocks_from_retrieval_candidate_bundle",
                    "expected_blocks_nonempty": bool(raw["expected"]),
                    "gold_unchanged": raw["expected"] == list(source["expected_block_ids"]),
                }
            else:
                table = tables[str(source["uid"])]
                row, col = int(source["mutated_cell"]["row"]), int(source["mutated_cell"]["col"])
                expected_vector = {leaf: 0 for leaf in observed["response_vector"]}
                expected_vector["parse.reconcile.equations"] = 1
                replacements = {(row, col): decimal_number(sample["value_after"])}
                assert replacements[(row, col)] is not None
                checks = {
                    "source_hash": json_hash(table) == source["table_sha256"],
                    "original_identity": identity_status(source["identity"], table, {}),
                    "mutated_identity_fails": not identity_status(
                        source["identity"], table, replacements  # type: ignore[arg-type]
                    ),
                    "value_changed": decimal_number(sample["value_after"]) != decimal_number(sample["value_before"]),
                }

            vector_match = all(
                int(observed["response_vector"][leaf]) == int(expected_vector[leaf])
                for leaf in expected_vector
            )
            passed = all(checks.values()) and vector_match
            details.append({
                "sample_id": sample_id,
                "stage": stage,
                "pass": passed,
                "checks": checks,
                "vector_match": vector_match,
            })
            if not passed:
                errors.append(sample_id)

    receipt = {
        "status": "PASS" if not errors else "FAIL",
        "independent_implementation": True,
        "imports_formal_runner": False,
        "numeric_implementation": "decimal.Decimal",
        "samples_checked": len(details),
        "samples_passed": len(details) - len(errors),
        "errors": errors,
        "details": details,
    }
    OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "samples": receipt["samples_checked"],
        "passed": receipt["samples_passed"],
        "errors": errors[:10],
        "output": str(OUT),
    }, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
