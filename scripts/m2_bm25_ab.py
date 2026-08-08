#!/usr/bin/env python3
"""A/B test: hybrid retrieval (vector+BM25) vs vector-only.

Runs the M2 deterministic eval fixture through RAGService.smart_retrieve
in-process (no :5050 needed) with M2_ENABLE_BM25 off/on and compares
hit@max_results against each question's expected sample_id.

Usage: python scripts/m2_bm25_ab.py [--top-k 5]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

FIXTURE = os.path.join(os.path.dirname(__file__), "..",
                       "tests", "fixtures", "m2_eval_questions.json")


def load_questions() -> list[dict]:
    with open(FIXTURE, encoding="utf-8") as fh:
        d = json.load(fh)
    return d if isinstance(d, list) else d.get("questions", [])


def expected_sample(q: dict) -> str:
    for c in q.get("checks", []):
        if c.get("type") == "source_required" and c.get("sample_id_contains"):
            return c["sample_id_contains"]
    return ""


def doc_matches(doc: dict, expected: str) -> bool:
    if not expected:
        return False
    text = doc.get("content") or doc.get("text") or doc.get("page_content") or ""
    if expected in text:
        return True
    meta = doc.get("metadata") or {}
    for key in ("document_id", "sample_id", "source"):
        if expected in str(meta.get(key, "")):
            return True
    return False


def run_once(rag, questions: list[dict], flag: bool, max_results: int):
    os.environ["M2_ENABLE_BM25"] = "true" if flag else "false"
    out = []
    for q in questions:
        exp = expected_sample(q)
        qtext = q.get("question") or " ".join(q.get("turns", []))
        t0 = time.time()
        docs = rag.smart_retrieve(qtext, max_results=max_results)
        dt = time.time() - t0
        hit_rank = None
        for i, d in enumerate(docs):
            if doc_matches(d, exp):
                hit_rank = i + 1
                break
        out.append({"id": q["id"], "expected": exp,
                    "hit_rank": hit_rank, "n_docs": len(docs),
                    "latency_s": round(dt, 2)})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-results", type=int, default=10)
    args = ap.parse_args()

    questions = load_questions()
    scripts_dir = os.path.abspath(os.path.dirname(__file__))
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import m1_rag_ingest as rag_mod  # sets local-embedding/PG env vars
    rag = rag_mod.RAGService(collection_name=rag_mod.COLLECTION)

    print(f"[ab] {len(questions)} questions, max_results={args.max_results}")
    print("[ab] run 1/2: M2_ENABLE_BM25=false (vector only)")
    off = run_once(rag, questions, False, args.max_results)
    print("[ab] run 2/2: M2_ENABLE_BM25=true (vector + BM25)")
    on = run_once(rag, questions, True, args.max_results)

    print(f"{'question':<28} {'off':>6} {'on':>6}  delta")
    improved = regressed = 0
    for a, b in zip(off, on):
        ra, rb = a["hit_rank"], b["hit_rank"]
        sa = str(ra) if ra else "MISS"
        sb = str(rb) if rb else "MISS"
        note = ""
        if ra is None and rb is not None:
            note, improved = "GAIN", improved + 1
        elif ra is not None and rb is None:
            note, regressed = "LOSS", regressed + 1
        elif ra and rb and rb < ra:
            note, improved = "RANK-UP", improved + 1
        elif ra and rb and rb > ra:
            note, regressed = "RANK-DOWN", regressed + 1
        print(f"{a['id']:<28} {sa:>6} {sb:>6}  {note}")
    hit_off = sum(1 for x in off if x["hit_rank"])
    hit_on = sum(1 for x in on if x["hit_rank"])
    lat_off = sum(x["latency_s"] for x in off) / len(off)
    lat_on = sum(x["latency_s"] for x in on) / len(on)
    print(f"\n[ab] hit@{args.max_results}: off={hit_off}/{len(off)} on={hit_on}/{len(on)}")
    print(f"[ab] avg latency: off={lat_off:.2f}s on={lat_on:.2f}s")
    print(f"[ab] improved={improved} regressed={regressed}")
    report = {"max_results": args.max_results, "hit_off": hit_off, "hit_on": hit_on,
              "avg_latency_off": round(lat_off, 2), "avg_latency_on": round(lat_on, 2),
              "improved": improved, "regressed": regressed,
              "off": off, "on": on}
    os.makedirs("logs/graph/eval", exist_ok=True)
    with open("logs/graph/eval/bm25_ab_report.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("[ab] report: logs/graph/eval/bm25_ab_report.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
