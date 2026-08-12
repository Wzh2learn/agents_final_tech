#!/usr/bin/env python3
"""Chunk granularity ablation on TAT-DQA validation (in-memory, no DB writes).

 Isolates the effect of chunk granularity on evidence recall by re-indexing the
official parsed blocks under different chunking strategies and running vector
retrieval only (no BM25, no rerank):

  A: original blocks (1 block = 1 chunk; current ingest granularity)
  B: merge 2 adjacent blocks per document into one chunk
  C: merge 3 adjacent blocks per document into one chunk
  D: sliding window +/-1 (each chunk = block + previous + next block)

For every strategy the chunks are embedded with the local Qwen3-Embedding-0.6B
model, the 100 validation questions are embedded once, top-5 chunks are fetched
by cosine similarity, and Evi R@5 / Doc R@5 / MRR are computed. A question is an
evidence hit when any retrieved chunk covers at least one gold block id.

Run inside the retrieval conda env (sentence-transformers + torch):
  conda run -n wzh_retrieval python3 scripts/run_chunk_ablation.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from run_tat_dqa_m2_upper_bound import load_upper_bound_data, stable_hash

MANIFEST = PROJECT_ROOT / "docs" / "datasets" / "tat-dqa-joint-v1-manifest.json"
QA_JSON = Path.home() / "wzh" / "datasets" / "tat-dqa" / "raw" / "tatdqa_dataset_dev.json"
DOCS_ARCHIVE = Path.home() / "wzh" / "datasets" / "tat-dqa" / "raw" / "tatdqa_docs_dev.zip"
OUTPUT_DIR = Path.home() / "wzh" / "datasets" / "tat-dqa" / "derived" / "chunk_ablation"
DEFAULT_EMBEDDING = Path.home() / "wzh" / "models" / "hf" / "qwen3-embedding-0.6b"

STRATEGIES = ("A", "B", "C", "D")
STRATEGY_DESC = {
    "A": "original blocks (1 block = 1 chunk)",
    "B": "2-block merge (adjacent pairs)",
    "C": "3-block merge (adjacent triples)",
    "D": "sliding window +/-1 (block + prev + next)",
}


def build_chunks(documents: list[dict[str, Any]], strategy: str) -> list[dict[str, Any]]:
    """Chunk the per-document block sequence under one strategy."""
    chunks: list[dict[str, Any]] = []
    for document in documents:
        document_id = document["document_id"]
        blocks = document.get("blocks", [])
        if strategy == "A":
            groups = [[block] for block in blocks]
        elif strategy == "B":
            groups = [blocks[i:i + 2] for i in range(0, len(blocks), 2)]
        elif strategy == "C":
            groups = [blocks[i:i + 3] for i in range(0, len(blocks), 3)]
        elif strategy == "D":
            groups = [
                blocks[max(0, i - 1):i + 2] for i in range(len(blocks))
            ]
        else:
            raise ValueError(f"unknown strategy: {strategy}")

        for group in groups:
            if not group:
                continue
            text = "\n".join((block.get("text") or "").strip() for block in group).strip()
            chunks.append(
                {
                    "document_id": document_id,
                    "block_ids": {str(block["block_id"]) for block in group},
                    "text": text or " ",
                }
            )
    return chunks


def evaluate_strategy(
    strategy: str,
    documents: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    embed_model: Any,
    top_k: int,
) -> dict[str, Any]:
    import numpy as np

    started = time.perf_counter()
    chunks = build_chunks(documents, strategy)
    chunk_texts = [chunk["text"] for chunk in chunks]
    chunk_embeddings = embed_model.encode(
        chunk_texts, normalize_embeddings=True, batch_size=64, show_progress_bar=False
    )
    query_embeddings = embed_model.encode(
        [case["question"] for case in cases],
        normalize_embeddings=True,
        batch_size=64,
        show_progress_bar=False,
    )
    chunk_embeddings = np.asarray(chunk_embeddings)
    query_embeddings = np.asarray(query_embeddings)

    evidence_hits = 0
    document_hits = 0
    reciprocal_ranks: list[float] = []
    for case_index, case in enumerate(cases):
        similarities = query_embeddings[case_index] @ chunk_embeddings.T
        k = min(top_k, len(chunks))
        top_indices = np.argpartition(-similarities, kth=k - 1)[:k]
        top_indices = top_indices[np.argsort(-similarities[top_indices])]

        expected_blocks = set(case["expected_block_ids"])
        document_id = case["document_id"]
        first_rank = 0
        evi_hit = False
        doc_hit = False
        for rank, chunk_index in enumerate(top_indices, start=1):
            chunk = chunks[int(chunk_index)]
            if chunk["document_id"] == document_id:
                doc_hit = True
            if chunk["block_ids"] & expected_blocks:
                evi_hit = True
                if first_rank == 0:
                    first_rank = rank
        evidence_hits += int(evi_hit)
        document_hits += int(doc_hit)
        reciprocal_ranks.append(1.0 / first_rank if first_rank else 0.0)

    case_count = len(cases)
    return {
        "strategy": strategy,
        "description": STRATEGY_DESC[strategy],
        "chunk_count": len(chunks),
        "evidence_recall_at_5": round(evidence_hits / case_count, 4),
        "document_recall_at_5": round(document_hits / case_count, 4),
        "evidence_mrr": round(sum(reciprocal_ranks) / case_count, 4),
        "elapsed_sec": round(time.perf_counter() - started, 2),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", default="validation")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--max-cases", type=int)
    parser.add_argument(
        "--strategies", default=",".join(STRATEGIES),
        help="comma-separated subset of A,B,C,D",
    )
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "chunk_ablation.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    strategies = [s.strip().upper() for s in args.strategies.split(",") if s.strip()]
    for strategy in strategies:
        if strategy not in STRATEGIES:
            raise SystemExit(f"unknown strategy {strategy!r}; choose from {STRATEGIES}")

    documents, cases = load_upper_bound_data(MANIFEST, QA_JSON, DOCS_ARCHIVE, args.split)
    if args.max_cases:
        cases = cases[:args.max_cases]
    total_blocks = sum(len(document.get("blocks", [])) for document in documents)

    model_path = os.path.expanduser(
        os.getenv("LOCAL_EMBEDDING_MODEL_PATH", str(DEFAULT_EMBEDDING))
    )
    device = os.getenv("LOCAL_EMBEDDING_DEVICE", "cuda")
    try:
        from sentence_transformers import SentenceTransformer
        embed_model = SentenceTransformer(model_path, device=device)
    except Exception as exc:  # embedding unavailable -> BLOCKED per stop condition
        print(f"BLOCKED: embedding unavailable ({type(exc).__name__}: {exc})")
        return 2

    print(
        f"dataset: {len(documents)} docs, {total_blocks} blocks, "
        f"{len(cases)} questions | embedding: {model_path} ({device})"
    )

    results: list[dict[str, Any]] = []
    for strategy in strategies:
        result = evaluate_strategy(strategy, documents, cases, embed_model, args.top_k)
        results.append(result)
        print(
            f"[{strategy}] {result['description']} | chunks={result['chunk_count']} "
            f"EviR@5={result['evidence_recall_at_5']:.3f} "
            f"DocR@5={result['document_recall_at_5']:.3f} "
            f"MRR={result['evidence_mrr']:.4f} ({result['elapsed_sec']}s)"
        )

    summary = {
        "dataset": "TAT-DQA",
        "split": args.split,
        "top_k": args.top_k,
        "documents": len(documents),
        "blocks": total_blocks,
        "questions": len(cases),
        "embedding_model": model_path,
        "data_contract": {
            "document_ids_sha256": stable_hash(sorted(d["document_id"] for d in documents)),
            "question_ids_sha256": stable_hash(sorted(c["question_id"] for c in cases)),
        },
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\nsummary written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
