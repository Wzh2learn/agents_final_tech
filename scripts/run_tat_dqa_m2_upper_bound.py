#!/usr/bin/env python3
"""Run a parsed-JSON TAT-DQA retrieval and answer upper-bound baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import statistics
import sys
import time
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from biz.rag_service import get_rag_service_sync
from storage.database.db import get_session
from storage.database.document_manager import DocumentManager


SOURCE_SPLIT = {"validation": "dev", "test": "test_gold"}
ARCHIVE_PREFIX = {"validation": "dev", "test": "test"}


def load_upper_bound_data(
    manifest_path: Path,
    qa_path: Path,
    archive_path: Path,
    split: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Join the public manifest with official QA labels and converted blocks."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_source = SOURCE_SPLIT[split]
    selected_documents = {
        item["document_id"]
        for item in manifest["documents"]
        if item["split"] == split and item["source_split"] == expected_source
    }
    selected_questions = {
        item["question_id"]
        for item in manifest["questions"]
        if item["split"] == split and item["source_split"] == expected_source
    }
    qa_documents = {
        item["doc"]["uid"]: item
        for item in json.loads(qa_path.read_text(encoding="utf-8"))
        if item.get("doc", {}).get("uid") in selected_documents
    }
    if set(qa_documents) != selected_documents:
        missing = sorted(selected_documents - set(qa_documents))
        raise ValueError(f"official QA JSON is missing selected documents: {missing}")

    documents: list[dict[str, Any]] = []
    cases: list[dict[str, Any]] = []
    with zipfile.ZipFile(archive_path) as archive:
        for document_id in sorted(selected_documents):
            qa_document = qa_documents[document_id]
            member = f"{ARCHIVE_PREFIX[split]}/{document_id}.json"
            converted = json.loads(archive.read(member).decode("utf-8"))
            blocks = [
                {
                    "block_id": block["uuid"],
                    "text": block.get("text", ""),
                    "page": page_index + 1,
                    "bbox": block.get("bbox"),
                    "order": block.get("order"),
                }
                for page_index, page in enumerate(converted.get("pages", []))
                for block in page.get("blocks", [])
                if isinstance(block, dict) and block.get("uuid")
            ]
            documents.append(
                {
                    "document_id": document_id,
                    "source": qa_document["doc"].get("source") or f"{document_id}.pdf",
                    "blocks": blocks,
                }
            )
            for question in qa_document.get("questions", []):
                question_id = str(question.get("uid", ""))
                if question_id not in selected_questions:
                    continue
                block_ids = sorted(
                    str(block_id)
                    for mapping in question.get("block_mapping", [])
                    if isinstance(mapping, dict)
                    for block_id in mapping
                )
                cases.append(
                    {
                        "question_id": question_id,
                        "document_id": document_id,
                        "question": question["question"],
                        "answer": question.get("answer"),
                        "answer_type": question.get("answer_type"),
                        "scale": question.get("scale"),
                        "expected_block_ids": block_ids,
                    }
                )

    if len(documents) != 20 or len(cases) != 100:
        raise ValueError(
            f"{split} contract requires 20 documents and 100 questions; "
            f"found {len(documents)} and {len(cases)}"
        )
    return documents, sorted(cases, key=lambda item: item["question_id"])


def collection_document_ids(collection_name: str) -> set[str]:
    db = get_session()
    try:
        documents = DocumentManager().get_documents(
            db,
            limit=1000,
            collection_name=collection_name,
        )
        return {str(document["id"]) for document in documents}
    finally:
        db.close()


def ingest_documents(
    documents: list[dict[str, Any]],
    collection_name: str,
    split: str,
) -> dict[str, int]:
    expected_ids = {document["document_id"] for document in documents}
    existing_ids = collection_document_ids(collection_name)
    unexpected = existing_ids - expected_ids
    if unexpected:
        raise ValueError(
            f"collection {collection_name!r} contains unexpected documents: "
            f"{sorted(unexpected)}"
        )

    service = get_rag_service_sync()
    chunks = 0
    for document in documents:
        if document["document_id"] in existing_ids:
            continue
        result = service.ingest_parsed_blocks(
            document["document_id"],
            document["blocks"],
            metadata={
                "source": document["document_id"],
                "original_source": document["source"],
                "dataset": "TAT-DQA",
                "split": split,
            },
            collection_name=collection_name,
        )
        chunks += result["chunks"]
    return {
        "documents": len(documents),
        "chunks_added": chunks,
        "documents_reused": len(existing_ids),
    }


def stable_hash(value: Any) -> str:
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def normalized_answer(value: Any) -> str:
    if isinstance(value, list):
        return "|".join(sorted(normalized_answer(item) for item in value))
    text = str(value if value is not None else "").lower().strip()
    text = text.replace(",", "").replace("$", "").replace("£", "").replace("€", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .")


def answer_exact_match(prediction: Any, expected: Any) -> bool:
    predicted = normalized_answer(prediction)
    target = normalized_answer(expected)
    try:
        return math.isclose(
            float(predicted.rstrip("%")),
            float(target.rstrip("%")),
            rel_tol=1e-4,
            abs_tol=1e-4,
        )
    except ValueError:
        return predicted == target


def call_answer_model(
    base_url: str,
    model: str,
    question: str,
    evidence: list[dict[str, Any]],
    timeout: int,
) -> dict[str, Any]:
    safe_evidence = [
        {
            "block_id": item.get("metadata", {}).get("block_id"),
            "text": item.get("content", ""),
        }
        for item in evidence
    ]
    prompt = (
        "Answer the financial question using only the evidence blocks. "
        "Return strict JSON with keys answer and evidence_block_ids. "
        "For arithmetic questions, compute the result. Do not add prose.\n"
        f"Evidence: {json.dumps(safe_evidence, ensure_ascii=False)}\n"
        f"Question: {question}"
    )
    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": 256,
        "chat_template_kwargs": {"enable_thinking": False},
        "messages": [{"role": "user", "content": prompt}],
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer local-dev"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    content = body["choices"][0]["message"].get("content", "")
    match = re.search(r"\{.*\}", content, flags=re.DOTALL)
    if not match:
        raise ValueError("answer model did not return a JSON object")
    parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict) or "answer" not in parsed:
        raise ValueError("answer model JSON must contain answer")
    return parsed


def evaluate(
    cases: list[dict[str, Any]],
    split: str,
    collection_name: str,
    base_url: str,
    model: str,
    timeout: int,
    max_cases: int | None,
    with_answers: bool,
) -> dict[str, Any]:
    service = get_rag_service_sync()
    selected_cases = cases[:max_cases] if max_cases else cases
    records: list[dict[str, Any]] = []
    for case in selected_cases:
        started = time.perf_counter()
        evidence = service.smart_retrieve(
            case["question"],
            collection_names=[collection_name],
            top_k=5,
            max_results=5,
            use_rerank=False,
        )
        retrieved_blocks = [
            str(item.get("metadata", {}).get("block_id", ""))
            for item in evidence
        ]
        retrieved_documents = [
            str(item.get("metadata", {}).get("document_id", ""))
            for item in evidence
        ]
        expected_blocks = set(case["expected_block_ids"])
        ranks = [
            index + 1
            for index, block_id in enumerate(retrieved_blocks)
            if block_id in expected_blocks
        ]
        answer_payload = None
        answer_ok = None
        cited_ok = None
        error_type = None
        if with_answers:
            try:
                answer_payload = call_answer_model(
                    base_url,
                    model,
                    case["question"],
                    evidence,
                    timeout,
                )
                answer_ok = answer_exact_match(answer_payload["answer"], case["answer"])
                cited_ok = bool(
                    set(map(str, answer_payload.get("evidence_block_ids", [])))
                    & expected_blocks
                )
            except Exception as exc:
                error_type = type(exc).__name__
        records.append(
            {
                "question_id": case["question_id"],
                "answer_type": case["answer_type"],
                "document_hit_at_5": case["document_id"] in retrieved_documents,
                "evidence_hit_at_5": bool(ranks),
                "evidence_reciprocal_rank": 1.0 / min(ranks) if ranks else 0.0,
                "answer_exact_match": answer_ok,
                "answer_evidence_hit": cited_ok,
                "latency_sec": round(time.perf_counter() - started, 3),
                "retrieved_block_hash": stable_hash(retrieved_blocks),
                "answer_hash": stable_hash(answer_payload) if answer_payload else None,
                "error_type": error_type,
            }
        )

    def rate(key: str) -> float | None:
        values = [record[key] for record in records if record[key] is not None]
        return round(sum(bool(value) for value in values) / len(values), 4) if values else None

    latencies = [record["latency_sec"] for record in records]
    return {
        "sanitized": True,
        "dataset": "TAT-DQA",
        "split": split,
        "collection": collection_name,
        "case_count": len(records),
        "metrics": {
            "document_recall_at_5": rate("document_hit_at_5"),
            "evidence_recall_at_5": rate("evidence_hit_at_5"),
            "evidence_mrr": round(
                statistics.mean(record["evidence_reciprocal_rank"] for record in records),
                4,
            ),
            "answer_exact_match": rate("answer_exact_match"),
            "answer_evidence_hit_rate": rate("answer_evidence_hit"),
            "latency_mean_sec": round(statistics.mean(latencies), 3),
            "answer_errors": dict(
                sorted(Counter(record["error_type"] for record in records if record["error_type"]).items())
            ),
        },
        "records": records,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--qa-json", type=Path, required=True)
    parser.add_argument("--docs-archive", type=Path, required=True)
    parser.add_argument("--split", choices=tuple(SOURCE_SPLIT), default="validation")
    parser.add_argument("--collection", default="tat-dqa-joint-v1-validation")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ingest", action="store_true")
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--with-answers", action="store_true")
    parser.add_argument("--max-cases", type=int)
    parser.add_argument("--base-url", default="http://127.0.0.1:8004/v1")
    parser.add_argument("--model", default="Qwen3-14B-Q4_K_M.gguf")
    parser.add_argument("--timeout", type=int, default=180)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.split == "test" and args.with_answers:
        raise SystemExit("test answers stay sealed until the validation protocol is frozen")
    documents, cases = load_upper_bound_data(
        args.manifest,
        args.qa_json,
        args.docs_archive,
        args.split,
    )
    summary: dict[str, Any] = {
        "data_contract": {
            "split": args.split,
            "documents": len(documents),
            "questions": len(cases),
            "document_ids_sha256": stable_hash(sorted(item["document_id"] for item in documents)),
            "question_ids_sha256": stable_hash(sorted(item["question_id"] for item in cases)),
        }
    }
    if args.ingest:
        summary["ingestion"] = ingest_documents(documents, args.collection, args.split)
    if args.evaluate:
        summary["evaluation"] = evaluate(
            cases,
            args.split,
            args.collection,
            args.base_url,
            args.model,
            args.timeout,
            args.max_cases,
            args.with_answers,
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    printable = {
        "data_contract": summary["data_contract"],
        "ingestion": summary.get("ingestion"),
        "metrics": summary.get("evaluation", {}).get("metrics"),
    }
    print(json.dumps(printable, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
