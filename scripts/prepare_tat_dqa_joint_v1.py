#!/usr/bin/env python3
"""Create the public-ID-only deterministic TAT-DQA joint-v1 manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


SEED = 20260722
TARGET_DOCUMENTS = 100
MAX_QUESTIONS = 500
SPLIT_SIZES = {"train": 60, "validation": 20, "test": 20}
SOURCE_TO_SPLIT = {"train": "train", "dev": "validation", "test_gold": "test"}
TARGET_ANSWER_TYPES = ("span", "spans", "arithmetic", "counting", "comparison")
LICENSE = "CC BY 4.0"


def canonical_answer_type(question: dict[str, Any]) -> str:
    """Map official TAT-DQA labels to the joint-v1 coverage vocabulary."""
    if question.get("req_comparison") is True:
        return "comparison"
    raw = str(_first(question, ("answer_type", "answer_type_gold", "type"), "unknown")).lower()
    return {"multi-span": "spans", "count": "counting"}.get(raw, raw)


def _records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "documents", "dataset"):
            if isinstance(payload.get(key), list):
                return payload[key]
    raise ValueError("unsupported TAT-DQA JSON top level")


def _first(record: dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    for key in keys:
        if key in record and record[key] is not None:
            return record[key]
    return default


def normalize_documents(payloads: Iterable[Any], source_split: str) -> list[dict[str, Any]]:
    """Normalize official split JSON without retaining questions or source text in output."""
    merged: dict[str, dict[str, Any]] = {}
    for payload in payloads:
        for document in _records(payload):
            document_metadata = document.get("doc") if isinstance(document.get("doc"), dict) else document
            document_id = str(_first(document_metadata, ("doc_id", "document_id", "uid", "id"), ""))
            questions = _first(document, ("questions", "qa", "qas"), [])
            if not document_id or not isinstance(questions, list):
                continue
            target = merged.setdefault(
                document_id,
                {"document_id": document_id, "source_split": source_split, "questions": []},
            )
            for index, question in enumerate(questions):
                if not isinstance(question, dict):
                    continue
                answer_type = canonical_answer_type(question)
                question_id = str(_first(question, ("uid", "question_id", "id", "qid"), f"{document_id}:{index}"))
                page_no = _first(
                    question,
                    ("page_no", "page_number", "page", "page_id"),
                    _first(document_metadata, ("page_no", "page_number", "page", "page_id"), None),
                )
                source_blocks = _first(question, ("source_block_ids", "evidence_block_ids"), None)
                if source_blocks is None:
                    gold_inds = question.get("gold_inds")
                    if isinstance(gold_inds, dict):
                        source_blocks = sorted(gold_inds)
                    else:
                        block_mapping = question.get("block_mapping")
                        source_blocks = sorted(
                            block_id
                            for mapping in block_mapping
                            if isinstance(mapping, dict)
                            for block_id in mapping
                        ) if isinstance(block_mapping, list) else []
                if not isinstance(source_blocks, list):
                    source_blocks = [source_blocks]
                target["questions"].append(
                    {
                        "question_id": question_id,
                        "answer_type": answer_type,
                        "page_no": page_no,
                        "source_block_ids": [str(item) for item in source_blocks],
                    }
                )
    return sorted((doc for doc in merged.values() if doc["questions"]), key=lambda item: item["document_id"])


def select_documents(
    documents: list[dict[str, Any]], target_count: int, seed: int = SEED
) -> list[dict[str, Any]]:
    if len(documents) < target_count:
        raise ValueError(f"need at least {target_count} documents, found {len(documents)}")
    rng = random.Random(seed)
    shuffled = documents.copy()
    rng.shuffle(shuffled)
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    candidates_by_type = {
        answer_type: [doc for doc in shuffled if any(q["answer_type"] == answer_type for q in doc["questions"])]
        for answer_type in TARGET_ANSWER_TYPES
    }
    # Counting and comparison are the rarest answer-type families in the official
    # release. Reserve document slots for the two rarest families before filling
    # the sample, so question balancing is not defeated by a purely random draw.
    rare_types = sorted(TARGET_ANSWER_TYPES, key=lambda item: (len(candidates_by_type[item]), item))[:2]
    per_rare_type = target_count // len(rare_types)
    for answer_type in rare_types:
        selected_with_type = 0
        for candidate in candidates_by_type[answer_type]:
            if selected_with_type >= per_rare_type:
                break
            if candidate["document_id"] not in selected_ids:
                selected.append(candidate)
                selected_ids.add(candidate["document_id"])
                selected_with_type += 1
    # Guarantee that every planned answer type occurs in the selected document set.
    for answer_type in TARGET_ANSWER_TYPES:
        candidates = [doc for doc in shuffled if any(q["answer_type"] == answer_type for q in doc["questions"])]
        if not candidates:
            raise ValueError(f"answer type is absent from source data: {answer_type}")
        if len(selected) < target_count and not any(
            any(q["answer_type"] == answer_type for q in doc["questions"]) for doc in selected
        ):
            candidate = candidates[0]
            if candidate["document_id"] not in selected_ids:
                selected.append(candidate)
                selected_ids.add(candidate["document_id"])
    for document in shuffled:
        if len(selected) == target_count:
            break
        if document["document_id"] not in selected_ids:
            selected.append(document)
            selected_ids.add(document["document_id"])
    return selected


def select_questions(documents: list[dict[str, Any]], seed: int = SEED) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for source_split, split in SOURCE_TO_SPLIT.items():
        grouped: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
        for document in documents:
            if document["source_split"] != source_split:
                continue
            for question in document["questions"]:
                grouped[question["answer_type"]].append((document, question))
        for answer_type, values in grouped.items():
            random.Random(f"{seed}:{source_split}:{answer_type}").shuffle(values)

        budget = SPLIT_SIZES[split] * (MAX_QUESTIONS // TARGET_DOCUMENTS)
        positions = {answer_type: 0 for answer_type in TARGET_ANSWER_TYPES}
        answer_types = [answer_type for answer_type in TARGET_ANSWER_TYPES if grouped.get(answer_type)]
        split_selected = 0
        while split_selected < budget:
            added = False
            for answer_type in answer_types:
                position = positions[answer_type]
                if position >= len(grouped[answer_type]) or split_selected >= budget:
                    continue
                document, question = grouped[answer_type][position]
                positions[answer_type] += 1
                selected.append(
                    {
                        "dataset_id": "tat-dqa",
                        "document_id": document["document_id"],
                        "page_no": question["page_no"],
                        "question_id": question["question_id"],
                        "answer_type": question["answer_type"],
                        "source_block_ids": question["source_block_ids"],
                        "source_split": source_split,
                        "split": split,
                        "license": LICENSE,
                    }
                )
                split_selected += 1
                added = True
            if not added:
                break
    return sorted(selected, key=lambda item: (item["split"], item["document_id"], item["question_id"]))


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    documents = manifest["documents"]
    questions = manifest["questions"]
    split_counts = Counter(item["split"] for item in documents)
    if len(documents) != TARGET_DOCUMENTS or dict(split_counts) != SPLIT_SIZES:
        raise ValueError(f"invalid document split counts: {dict(split_counts)}")
    document_splits = {item["document_id"]: item["split"] for item in documents}
    if len(document_splits) != len(documents):
        raise ValueError("duplicate document IDs")
    if len(questions) > MAX_QUESTIONS:
        raise ValueError(f"question limit exceeded: {len(questions)}")
    leakage = [item["document_id"] for item in questions if document_splits.get(item["document_id"]) != item["split"]]
    if leakage:
        raise ValueError(f"document leakage or split mismatch: {sorted(set(leakage))}")
    source_mismatches = [
        item["document_id"]
        for item in documents
        if SOURCE_TO_SPLIT.get(item["source_split"]) != item["split"]
    ]
    if source_mismatches:
        raise ValueError(f"official source split leakage: {sorted(set(source_mismatches))}")
    answer_types = Counter(item["answer_type"] for item in questions)
    missing = [item for item in TARGET_ANSWER_TYPES if not answer_types.get(item)]
    if missing:
        raise ValueError(f"missing required answer types: {missing}")
    return {
        "document_count": len(documents),
        "question_count": len(questions),
        "documents_by_split": dict(sorted(split_counts.items())),
        "documents_by_source_split": dict(
            sorted(Counter(item["source_split"] for item in documents).items())
        ),
        "questions_by_split": dict(sorted(Counter(item["split"] for item in questions).items())),
        "questions_by_answer_type": dict(sorted(answer_types.items())),
        "document_leakage": False,
        "official_split_leakage": False,
    }


def build_manifest(
    split_payloads: dict[str, Iterable[Any]], seed: int = SEED
) -> tuple[dict[str, Any], dict[str, Any]]:
    missing = set(SOURCE_TO_SPLIT) - set(split_payloads)
    if missing:
        raise ValueError(f"missing official source splits: {sorted(missing)}")
    selected_documents: list[dict[str, Any]] = []
    for offset, (source_split, split) in enumerate(SOURCE_TO_SPLIT.items()):
        documents = normalize_documents(split_payloads[source_split], source_split)
        selected_documents.extend(select_documents(documents, SPLIT_SIZES[split], seed + offset))
    questions = select_questions(selected_documents, seed)
    manifest = {
        "manifest_version": "joint-v1",
        "dataset": "TAT-DQA",
        "license": LICENSE,
        "seed": seed,
        "documents": [
            {
                "dataset_id": "tat-dqa",
                "document_id": doc["document_id"],
                "source_split": doc["source_split"],
                "split": SOURCE_TO_SPLIT[doc["source_split"]],
                "license": LICENSE,
            }
            for doc in sorted(selected_documents, key=lambda item: item["document_id"])
        ],
        "questions": questions,
    }
    return manifest, validate_manifest(manifest)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-input", required=True, type=Path)
    parser.add_argument("--validation-input", required=True, type=Path)
    parser.add_argument("--test-input", required=True, type=Path, help="Official test-gold JSON file.")
    parser.add_argument("--manifest-out", required=True, type=Path)
    parser.add_argument("--checks-out", required=True, type=Path)
    args = parser.parse_args()
    split_payloads = {
        "train": [json.loads(args.train_input.read_text(encoding="utf-8"))],
        "dev": [json.loads(args.validation_input.read_text(encoding="utf-8"))],
        "test_gold": [json.loads(args.test_input.read_text(encoding="utf-8"))],
    }
    manifest, checks = build_manifest(split_payloads)
    serialized = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    checks["manifest_sha256"] = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    args.checks_out.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_out.write_text(serialized, encoding="utf-8")
    args.checks_out.write_text(json.dumps(checks, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(checks, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
