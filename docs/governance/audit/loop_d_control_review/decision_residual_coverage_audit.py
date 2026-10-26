"""Audit an exposed TAT-QA retrieval screen; no model generation or training."""
from __future__ import annotations
import argparse, collections, hashlib, json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def audit(source: Path) -> dict:
    records = json.loads(source.read_text(encoding="utf-8"))
    counts = collections.Counter()
    rows = []
    for record in records:
        paragraphs = sorted(record.get("paragraphs", []), key=lambda x: x["order"])
        if not paragraphs:
            continue
        texts = [p["text"] for p in paragraphs]
        orders = [str(p["order"]) for p in paragraphs]
        vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2))
        matrix = vectorizer.fit_transform(texts)
        for question in record["questions"]:
            counts[question.get("answer_from", "MISSING")] += 1
            if question.get("answer_from") != "text":
                continue
            gold = set(map(str, question.get("rel_paragraphs", [])))
            scores = cosine_similarity(vectorizer.transform([question["question"]]), matrix)[0]
            ranking = sorted(range(len(texts)), key=lambda j: (-scores[j], int(orders[j])))
            sets = {f"top{k}": set(ranking[:k]) for k in [1, 2, 3, 5, 10]}
            neighbor = set(ranking[:3])
            first = ranking[0]
            neighbor.update(j for j in [first - 1, first + 1] if 0 <= j < len(texts))
            sets["top3_neighbor"] = neighbor
            sets["all"] = set(range(len(texts)))
            rows.append({
                "paragraph_count": len(texts), "empty_gold": not gold,
                "coverage": {k: gold <= {orders[j] for j in selected} for k, selected in sets.items()},
                "chars": {k: sum(len(texts[j]) for j in selected) for k, selected in sets.items()},
                "context_count": {k: len(selected) for k, selected in sets.items()},
            })
    if not rows:
        raise ValueError("No text-only rows; refusing an empty-denominator pass")
    summary = {
        k: {
            "covered": sum(r["coverage"][k] for r in rows),
            "equals_all": sum(r["context_count"][k] == r["paragraph_count"] for r in rows),
            "total_chars": sum(r["chars"][k] for r in rows),
            "total_paragraphs": sum(r["context_count"][k] for r in rows),
        } for k in rows[0]["coverage"]
    }
    return {
        "schema": "decision_residual_post_return_audit_v1",
        "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "record_count": len(records), "answer_from_counts": dict(counts),
        "text_only_count": len(rows),
        "empty_gold_count": sum(r["empty_gold"] for r in rows),
        "paragraph_histogram_by_text_question": dict(sorted(collections.Counter(r["paragraph_count"] for r in rows).items())),
        "summary": summary,
        "neighbor_vs_top5": {
            "equal_annotated_evidence_coverage": summary["top3_neighbor"]["covered"] == summary["top5"]["covered"],
            "chars_reduction_fraction": 1 - summary["top3_neighbor"]["total_chars"] / summary["top5"]["total_chars"],
        },
        "scientific_generation_attempts": 0, "training_runs": 0,
        "limits": [
            "Exposed development screen; labels are not a new confirmation reference.",
            "Characters proxy context volume, not measured tokens, latency, answer correctness, or deployable policy gain.",
            "Retrieval is inside each preselected record; not full-report or corpus retrieval.",
            "The 507 table-text questions were counted, not evaluated or certified."
        ],
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.input), ensure_ascii=False, sort_keys=True))
