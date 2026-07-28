#!/usr/bin/env python3
"""Cross-encoder rerank evaluation on TAT-DQA validation.

Retrieves top-k candidates via hybrid search, reranks with
bge-reranker-v2-m3 cross-encoder, then evaluates answer quality.

Experiments:
  G: hybrid top_k=10 -> rerank -> top-5
  H: hybrid top_k=5  -> rerank -> top-5
  I: hybrid top_k=10 -> rerank -> top-3
"""

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
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from run_tat_dqa_m2_upper_bound import (
    answer_exact_match,
    call_answer_model,
    load_upper_bound_data,
    stable_hash,
)

RERANKER_MODEL_PATH = Path.home() / "wzh" / "models" / "hf" / "bge-reranker-v2-m3"
MANIFEST = PROJECT_ROOT / "docs" / "datasets" / "tat-dqa-joint-v1-manifest.json"
QA_JSON = Path.home() / "wzh" / "datasets" / "tat-dqa" / "raw" / "tatdqa_dataset_dev.json"
DOCS_ARCHIVE = Path.home() / "wzh" / "datasets" / "tat-dqa" / "raw" / "tatdqa_docs_dev.zip"
OUTPUT_DIR = Path.home() / "wzh" / "datasets" / "tat-dqa" / "derived" / "rerank"
COLLECTION = "tat-dqa-joint-v1-validation"
EXPERIMENT_TIMEOUT_SEC = 300

EXPERIMENTS = [
    # (name, retrieve_top_k, rerank_top_n)
    ("G_top10_rerank5", 10, 5),
    ("H_top5_rerank5", 5, 5),
    ("I_top10_rerank3", 10, 3),
]


def rerank_evidence(
    cross_encoder: Any,
    query: str,
    evidence: list[dict[str, Any]],
    top_n: int,
) -> list[dict[str, Any]]:
    """Rerank evidence using cross-encoder scores, return top_n."""
    if not evidence:
        return evidence
    pairs = [(query, item.get("content", "")) for item in evidence]
    scores = cross_encoder.predict(pairs)
    scored = sorted(
        zip(evidence, scores), key=lambda pair: pair[1], reverse=True
    )
    return [item for item, _score in scored[:top_n]]


def evaluate_with_rerank(
    cases: list[dict[str, Any]],
    collection_name: str,
    cross_encoder: Any,
    retrieve_top_k: int,
    rerank_top_n: int,
    base_url: str,
    model: str,
    answer_timeout: int,
    with_answers: bool,
    max_cases: int | None = None,
) -> dict[str, Any]:
    """Run evaluation with cross-encoder reranking."""
    from biz.rag_service import get_rag_service_sync

    service = get_rag_service_sync()
    selected_cases = cases[:max_cases] if max_cases else cases
    records: list[dict[str, Any]] = []
    rerank_latencies: list[float] = []

    for case_index, case in enumerate(selected_cases):
        started = time.perf_counter()

        evidence = service.smart_retrieve(
            case["question"],
            collection_names=[collection_name],
            top_k=retrieve_top_k,
            max_results=retrieve_top_k,
            use_rerank=False,
        )

        rerank_started = time.perf_counter()
        reranked = rerank_evidence(
            cross_encoder, case["question"], evidence, rerank_top_n
        )
        rerank_elapsed = time.perf_counter() - rerank_started
        rerank_latencies.append(rerank_elapsed)

        retrieved_blocks = [
            str(item.get("metadata", {}).get("block_id", ""))
            for item in reranked
        ]
        retrieved_documents = [
            str(item.get("metadata", {}).get("document_id", ""))
            for item in reranked
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
                    base_url, model, case["question"], reranked, answer_timeout
                )
                answer_ok = answer_exact_match(
                    answer_payload["answer"], case["answer"]
                )
                cited_ok = bool(
                    set(map(str, answer_payload.get("evidence_block_ids", [])))
                    & expected_blocks
                )
            except Exception as exc:
                error_type = type(exc).__name__

        total_elapsed = time.perf_counter() - started
        records.append(
            {
                "question_id": case["question_id"],
                "answer_type": case["answer_type"],
                "document_hit_at_5": case["document_id"] in retrieved_documents,
                "evidence_hit_at_5": bool(ranks),
                "evidence_reciprocal_rank": (
                    1.0 / min(ranks) if ranks else 0.0
                ),
                "answer_exact_match": answer_ok,
                "answer_evidence_hit": cited_ok,
                "latency_sec": round(total_elapsed, 3),
                "rerank_latency_sec": round(rerank_elapsed, 3),
                "retrieved_block_ids": retrieved_blocks,
                "error_type": error_type,
            }
        )
        if (case_index + 1) % 20 == 0:
            print(f"  [{case_index + 1}/{len(selected_cases)}] "
                  f"avg latency {statistics.mean(r['latency_sec'] for r in records):.2f}s")

    def rate(key: str) -> float | None:
        values = [r[key] for r in records if r[key] is not None]
        return (
            round(sum(bool(v) for v in values) / len(values), 4)
            if values
            else None
        )

    latencies = [r["latency_sec"] for r in records]
    return {
        "experiment": {
            "retrieve_top_k": retrieve_top_k,
            "rerank_top_n": rerank_top_n,
            "reranker": "bge-reranker-v2-m3",
            "collection": collection_name,
        },
        "case_count": len(records),
        "metrics": {
            "document_recall_at_5": rate("document_hit_at_5"),
            "evidence_recall_at_5": rate("evidence_hit_at_5"),
            "evidence_mrr": round(
                statistics.mean(
                    r["evidence_reciprocal_rank"] for r in records
                ),
                4,
            ),
            "answer_exact_match": rate("answer_exact_match"),
            "answer_evidence_hit_rate": rate("answer_evidence_hit"),
            "latency_mean_sec": round(statistics.mean(latencies), 3),
            "rerank_latency_mean_sec": round(
                statistics.mean(rerank_latencies), 3
            ),
            "answer_errors": dict(
                sorted(
                    Counter(
                        r["error_type"] for r in records if r["error_type"]
                    ).items()
                )
            ),
        },
        "records": records,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url", default="http://127.0.0.1:8004/v1"
    )
    parser.add_argument(
        "--model", default="Qwen3-14B-Q4_K_M.gguf"
    )
    parser.add_argument("--answer-timeout", type=int, default=180)
    parser.add_argument("--max-cases", type=int)
    parser.add_argument(
        "--experiments",
        nargs="*",
        default=None,
        help="Subset of experiment names to run (default: all)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading validation data...")
    documents, cases = load_upper_bound_data(
        MANIFEST, QA_JSON, DOCS_ARCHIVE, "validation"
    )
    print(f"Loaded {len(documents)} docs, {len(cases)} questions")

    print("Loading cross-encoder reranker...")
    from sentence_transformers import CrossEncoder

    load_started = time.time()
    cross_encoder = CrossEncoder(str(RERANKER_MODEL_PATH))
    print(f"Reranker loaded in {time.time() - load_started:.1f}s "
          f"(device: {cross_encoder.model.device})")

    selected_experiments = EXPERIMENTS
    if args.experiments:
        selected_experiments = [
            exp for exp in EXPERIMENTS if exp[0] in args.experiments
        ]
        if not selected_experiments:
            print(f"No matching experiments for: {args.experiments}")
            return 1

    all_results: dict[str, Any] = {}

    for name, retrieve_top_k, rerank_top_n in selected_experiments:
        print(f"\n{'=' * 60}")
        print(f"EXPERIMENT: {name} "
              f"(top_k={retrieve_top_k} -> rerank -> top_{rerank_top_n})")
        print(f"{'=' * 60}")

        experiment_started = time.time()
        try:
            result = evaluate_with_rerank(
                cases=cases,
                collection_name=COLLECTION,
                cross_encoder=cross_encoder,
                retrieve_top_k=retrieve_top_k,
                rerank_top_n=rerank_top_n,
                base_url=args.base_url,
                model=args.model,
                answer_timeout=args.answer_timeout,
                with_answers=True,
                max_cases=args.max_cases,
            )
            elapsed = time.time() - experiment_started
            result["wall_time_sec"] = round(elapsed, 1)
            all_results[name] = result

            metrics = result["metrics"]
            print(f"\n[{name}] Completed in {elapsed:.1f}s")
            print(f"  Doc R@5:  {metrics['document_recall_at_5']}")
            print(f"  Evi R@5:  {metrics['evidence_recall_at_5']}")
            print(f"  MRR:      {metrics['evidence_mrr']}")
            print(f"  EM:       {metrics['answer_exact_match']}")
            print(f"  Cite:     {metrics['answer_evidence_hit_rate']}")
            print(f"  Latency:  {metrics['latency_mean_sec']}s")
            print(f"  Rerank:   {metrics['rerank_latency_mean_sec']}s")

            output_file = OUTPUT_DIR / f"{name}.json"
            output_file.write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"  Saved: {output_file}")

        except Exception as exc:
            elapsed = time.time() - experiment_started
            print(f"\n[{name}] FAILED after {elapsed:.1f}s: {exc}")
            all_results[name] = {"error": str(exc), "wall_time_sec": round(elapsed, 1)}

        if time.time() - experiment_started > EXPERIMENT_TIMEOUT_SEC:
            print(f"[{name}] WARNING: exceeded {EXPERIMENT_TIMEOUT_SEC}s timeout")

    summary_path = OUTPUT_DIR / "rerank_summary.json"
    summary_data = {
        name: {
            "metrics": result.get("metrics"),
            "experiment": result.get("experiment"),
            "wall_time_sec": result.get("wall_time_sec"),
            "error": result.get("error"),
        }
        for name, result in all_results.items()
    }
    summary_path.write_text(
        json.dumps(summary_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    header = (f"{'Experiment':<22} {'DocR@5':>7} {'EviR@5':>7} {'MRR':>8} "
              f"{'EM':>7} {'Cite':>7} {'Lat(s)':>7} {'Rerank':>7}")
    print(header)
    print("-" * len(header))
    for name, result in all_results.items():
        metrics = result.get("metrics")
        if metrics:
            print(f"{name:<22} "
                  f"{metrics.get('document_recall_at_5', 0):>7.3f} "
                  f"{metrics.get('evidence_recall_at_5', 0):>7.3f} "
                  f"{metrics.get('evidence_mrr', 0):>8.4f} "
                  f"{metrics.get('answer_exact_match', 0):>7.3f} "
                  f"{metrics.get('answer_evidence_hit_rate', 0):>7.3f} "
                  f"{metrics.get('latency_mean_sec', 0):>7.3f} "
                  f"{metrics.get('rerank_latency_mean_sec', 0):>7.3f}")
        else:
            error = result.get("error", "unknown")
            print(f"{name:<22} ERROR: {error}")

    print(f"\nSummary saved: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
