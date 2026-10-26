#!/usr/bin/env python3
"""Recompute deterministic retrieval coverage on TAT-QA text-only questions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    records = json.loads(args.input.read_text(encoding="utf-8"))
    rows: list[dict[str, object]] = []
    for record_index, record in enumerate(records):
        paragraphs = sorted(record["paragraphs"], key=lambda item: item["order"])
        if not paragraphs:
            continue
        orders = [str(item["order"]) for item in paragraphs]
        vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2))
        matrix = vectorizer.fit_transform([item["text"] for item in paragraphs])
        for question_index, question in enumerate(record["questions"]):
            if question.get("answer_from") != "text":
                continue
            gold = {str(item) for item in question.get("rel_paragraphs", [])}
            similarities = cosine_similarity(
                vectorizer.transform([question["question"]]), matrix
            )[0]
            ranked_indices = sorted(
                range(len(paragraphs)),
                key=lambda index: (-similarities[index], int(paragraphs[index]["order"])),
            )
            top3 = {orders[index] for index in ranked_indices[:3]}
            top5 = {orders[index] for index in ranked_indices[:5]}
            top10 = {orders[index] for index in ranked_indices[:10]}
            top1_neighbor = set(top3)
            first = ranked_indices[0]
            for neighbor in (first - 1, first + 1):
                if 0 <= neighbor < len(paragraphs):
                    top1_neighbor.add(orders[neighbor])
            rows.append(
                {
                    "record_index": record_index,
                    "question_index": question_index,
                    "uid": question["uid"],
                    "question": question["question"],
                    "answer": question["answer"],
                    "gold_paragraphs": sorted(gold, key=int),
                    "coverage": {
                        "top3": gold <= top3,
                        "top5": gold <= top5,
                        "top3_top1_neighbor": gold <= top1_neighbor,
                        "top10": gold <= top10,
                    },
                    "context_paragraph_counts": {
                        "top3": len(top3),
                        "top5": len(top5),
                        "top3_top1_neighbor": len(top1_neighbor),
                        "top10": len(top10),
                        "all": len(paragraphs),
                    },
                }
            )

    methods = ["top3", "top5", "top3_top1_neighbor", "top10"]
    summary = {
        method: {
            "gold_covered": sum(row["coverage"][method] for row in rows),
            "denominator": len(rows),
            "average_context_paragraphs": sum(
                row["context_paragraph_counts"][method] for row in rows
            )
            / len(rows),
        }
        for method in methods
    }
    output = {
        "schema": "tatqa_text_only_retrieval_screen_v1",
        "evidence_identity": "DETERMINISTIC_DEV_QUALIFICATION_SCREEN_NO_MODEL",
        "input_path": str(args.input),
        "input_sha256": sha256_file(args.input),
        "method": "Per-record TF-IDF(1,2), cosine ranking, paragraph-order tie break",
        "summary": summary,
        "top3_miss_examples": [
            row for row in rows if not row["coverage"]["top3"]
        ][:10],
        "nonclaims": [
            "Development screening only; selected examples are exposed.",
            "Coverage is not full semantic answer accuracy.",
            "No model, judge, training, production or confirmation call occurred.",
        ],
    }
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
