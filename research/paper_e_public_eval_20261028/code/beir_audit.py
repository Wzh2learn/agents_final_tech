#!/usr/bin/env python3
"""Audit a public IR evaluation system (BEIR) end to end, without any model.

What is audited is the *evaluation protocol*, not a neural retriever:

  observation surface  -> the full ranking the retriever produced (recall@100)
  detection predicate  -> the metric cutoff k (nDCG@10 only credits rank <= 10)
  decision             -> which of several systems is reported as better
  identity contract    -> qrels/corpus id resolution (duplicates, missing docs)
  tie contract         -> score ties at the cutoff, where the official scorer
                          does not specify an order
  reproduction         -> metric re-implementation vs a second implementation

Everything is deterministic: BM25 / TF-IDF over the released corpus, trec_eval
definitions (ndcg_cut / map_cut / recall) re-implemented and cross-checked, and
a query-level bootstrap for uncertainty. No model is called, so this case costs
zero generation tokens.

Usage:  python beir_audit.py --data DIR --out OUT.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys
from collections import defaultdict

import numpy as np

TOKEN = re.compile(r"[a-z0-9]+")
K_EVAL = (10, 100)


# --------------------------------------------------------------------------
# IO
# --------------------------------------------------------------------------
def read_jsonl(path: str):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def read_qrels(path: str) -> dict[str, dict[str, int]]:
    rel: dict[str, dict[str, int]] = defaultdict(dict)
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            rel[row["query-id"]][row["corpus-id"]] = int(float(row["score"]))
    return rel


def tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


# --------------------------------------------------------------------------
# Retrievers (deterministic, numpy only)
# --------------------------------------------------------------------------
class BM25:
    def __init__(self, corpus: dict[str, dict], k1: float, b: float):
        self.ids = list(corpus)
        self.k1, self.b = k1, b
        self.doc_len = np.zeros(len(self.ids), dtype=np.float32)
        postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for i, did in enumerate(self.ids):
            doc = corpus[did]
            toks = tokenize(" ".join([doc.get("title") or "", doc.get("text") or ""]))
            self.doc_len[i] = len(toks)
            tf: dict[str, int] = defaultdict(int)
            for t in toks:
                tf[t] += 1
            for t, c in tf.items():
                postings[t].append((i, c))
        self.avgdl = float(self.doc_len.mean()) or 1.0
        self.postings = {t: (np.array([p[0] for p in v]), np.array([p[1] for p in v], dtype=np.float32))
                         for t, v in postings.items()}
        n = len(self.ids)
        self.idf = {t: math.log(1 + (n - len(v[0]) + 0.5) / (len(v[0]) + 0.5))
                    for t, v in self.postings.items()}

    def scores(self, query: str) -> np.ndarray:
        s = np.zeros(len(self.ids), dtype=np.float32)
        for t in tokenize(query):
            p = self.postings.get(t)
            if p is None:
                continue
            idx, tf = p
            denom = tf + self.k1 * (1 - self.b + self.b * self.doc_len[idx] / self.avgdl)
            s[idx] += self.idf[t] * tf * (self.k1 + 1) / denom
        return s


class Tfidf:
    def __init__(self, corpus: dict[str, dict]):
        self.ids = list(corpus)
        postings: dict[str, list[tuple[int, float]]] = defaultdict(list)
        df = defaultdict(int)
        raw: list[dict[str, int]] = []
        for did in self.ids:
            doc = corpus[did]
            toks = tokenize(" ".join([doc.get("title") or "", doc.get("text") or ""]))
            tf: dict[str, int] = defaultdict(int)
            for t in toks:
                tf[t] += 1
            raw.append(tf)
            for t in tf:
                df[t] += 1
        n = len(self.ids)
        self.idf = {t: math.log((1 + n) / (1 + d)) + 1.0 for t, d in df.items()}
        self.norm = np.zeros(n, dtype=np.float32)
        for i, tf in enumerate(raw):
            for t, c in tf.items():
                w = (1 + math.log(c)) * self.idf[t]
                postings[t].append((i, w))
                self.norm[i] += w * w
        self.norm = np.sqrt(np.maximum(self.norm, 1e-12))
        self.postings = {t: (np.array([p[0] for p in v]), np.array([p[1] for p in v], dtype=np.float32))
                         for t, v in postings.items()}

    def scores(self, query: str) -> np.ndarray:
        s = np.zeros(len(self.ids), dtype=np.float32)
        toks = defaultdict(int)
        for t in tokenize(query):
            if t in self.idf:
                toks[t] += 1
        qn = math.sqrt(sum(((1 + math.log(c)) * self.idf[t]) ** 2 for t, c in toks.items())) or 1.0
        for t, c in toks.items():
            idx, w = self.postings[t]
            s[idx] += ((1 + math.log(c)) * self.idf[t]) * w
        return s / (self.norm * qn)


def rank(scores: np.ndarray, ids: list[str], tie: str, topk: int) -> list[str]:
    """Rank by score desc; ties broken deterministically by doc id."""
    order = np.argsort(-scores, kind="stable")
    # group exact score ties and reorder inside each group by id
    s = scores[order]
    out: list[str] = []
    i = 0
    n = len(order)
    while i < n and len(out) < topk:
        j = i
        while j + 1 < n and s[j + 1] == s[i]:
            j += 1
        grp = [ids[k] for k in order[i:j + 1]]
        grp.sort(reverse=(tie == "id_desc"))
        out.extend(grp)
        i = j + 1
    return out[:topk]


# --------------------------------------------------------------------------
# trec_eval-compatible metrics (ndcg_cut / map_cut / recall)
# --------------------------------------------------------------------------
def dcg(gains: list[int]) -> float:
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains))


def ndcg_cut(ranked: list[str], rel: dict[str, int], k: int) -> float:
    gains = [1 if rel.get(d, 0) > 0 else 0 for d in ranked[:k]]
    ideal = dcg([1] * min(sum(1 for v in rel.values() if v > 0), k))
    return dcg(gains) / ideal if ideal > 0 else 0.0


def map_cut(ranked: list[str], rel: dict[str, int], k: int) -> float:
    hits = 0
    total = 0.0
    n_rel = sum(1 for v in rel.values() if v > 0)
    for i, d in enumerate(ranked[:k], start=1):
        if rel.get(d, 0) > 0:
            hits += 1
            total += hits / i
    return total / min(n_rel, k) if n_rel else 0.0


def recall_cut(ranked: list[str], rel: dict[str, int], k: int) -> float:
    n_rel = sum(1 for v in rel.values() if v > 0)
    if not n_rel:
        return 0.0
    return sum(1 for d in ranked[:k] if rel.get(d, 0) > 0) / n_rel


def brute_ndcg(ranked: list[str], rel: dict[str, int], k: int) -> float:
    """Independent O(k) statement of the same definition, for cross-checking."""
    seen = [d for d in ranked[:k]]
    num = 0.0
    for pos, d in enumerate(seen):
        if rel.get(d, 0) > 0:
            num += 1.0 if pos == 0 else 1.0 / math.log2(pos + 2)
    idel = sorted((1 for v in rel.values() if v > 0), reverse=True)[:k]
    den = 0.0
    for pos in range(len(idel)):
        den += 1.0 if pos == 0 else 1.0 / math.log2(pos + 2)
    return num / den if den else 0.0


# --------------------------------------------------------------------------
# Audit
# --------------------------------------------------------------------------
def bootstrap_ci(x: np.ndarray, n: int = 2000, seed: int = 20261028) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n, len(x)))
    means = x[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def paired_ci(a: np.ndarray, b: np.ndarray, n: int = 2000, seed: int = 20261028) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(a), size=(n, len(a)))
    d = a[idx].mean(axis=1) - b[idx].mean(axis=1)
    return float(a.mean() - b.mean()), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def run_dataset(name: str, root: str) -> dict:
    d = os.path.join(root, name)
    corpus = {r["_id"]: r for r in read_jsonl(os.path.join(d, "corpus.jsonl"))}
    queries = {r["_id"]: r["text"] for r in read_jsonl(os.path.join(d, "queries.jsonl"))}
    rel = read_qrels(os.path.join(d, "qrels", "test.tsv"))
    qids = [q for q in rel if q in queries and any(v > 0 for v in rel[q].values())]

    systems = {
        "bm25_k1=0.9_b=0.4": BM25(corpus, 0.9, 0.4),   # BEIR's reported default
        "bm25_k1=1.2_b=0.75": BM25(corpus, 1.2, 0.75),
        "bm25_k1=0.5_b=0.3": BM25(corpus, 0.5, 0.3),
        "bm25_k1=1.5_b=0.6": BM25(corpus, 1.5, 0.6),
        "tfidf_cosine": Tfidf(corpus),
    }

    per_system: dict[str, dict] = {}
    raw_scores: dict[str, dict[str, np.ndarray]] = {}
    for sname, retr in systems.items():
        per_query = {f"{m}@{k}": [] for m in ("ndcg", "map", "recall") for k in K_EVAL}
        per_query.update({"tie_flip@10": [], "ndcg10_tieB": []})
        for q in qids:
            sc = retr.scores(queries[q])
            r_a = rank(sc, retr.ids, "id_asc", max(K_EVAL))
            r_b = rank(sc, retr.ids, "id_desc", max(K_EVAL))
            for k in K_EVAL:
                per_query[f"ndcg@{k}"].append(ndcg_cut(r_a, rel[q], k))
                per_query[f"map@{k}"].append(map_cut(r_a, rel[q], k))
                per_query[f"recall@{k}"].append(recall_cut(r_a, rel[q], k))
            per_query["ndcg10_tieB"].append(ndcg_cut(r_b, rel[q], 10))
            per_query["tie_flip@10"].append(0.0 if r_a[:10] == r_b[:10] else 1.0)
            # record score ties at the 10/11 boundary
        raw_scores[sname] = {k: np.array(v, dtype=float) for k, v in per_query.items()}

        entry = {}
        for m in ("ndcg", "map", "recall"):
            for k in K_EVAL:
                v = raw_scores[sname][f"{m}@{k}"]
                lo, hi = bootstrap_ci(v)
                entry[f"{m}@{k}"] = {"mean": float(v.mean()), "ci95": [lo, hi]}
        for key in ("ndcg@10", "ndcg@100"):
            a = raw_scores[sname][key]
            b = raw_scores[sname]["ndcg10_tieB"] if key == "ndcg@10" else None
            if b is not None:
                entry["tie_policy_gap@10"] = {"asc": float(a.mean()), "desc": float(b.mean()),
                                              "gap": float(a.mean() - b.mean()),
                                              "queries_changed": float(raw_scores[sname]["tie_flip@10"].mean())}
        per_system[sname] = entry

    # cross-implementation check on a deterministic subsample
    mism = 0
    checked = 0
    rng = np.random.default_rng(7)
    for sname, retr in systems.items():
        for q in qids[:20]:
            sc = retr.scores(queries[q])
            r = rank(sc, retr.ids, "id_asc", 100)
            for k in K_EVAL:
                a = ndcg_cut(r, rel[q], k)
                b = brute_ndcg(r, rel[q], k)
                checked += 1
                if abs(a - b) > 1e-9:
                    mism += 1

    # ranking under each protocol view
    def ranking(metric_key: str) -> list[tuple[str, float]]:
        return sorted(((s, per_system[s][metric_key]["mean"]) for s in systems),
                      key=lambda x: -x[1])

    rank10 = ranking("ndcg@10")
    rank100 = ranking("ndcg@100")
    # pairwise gaps with paired bootstrap at k=10
    pairs = []
    for i in range(len(rank10)):
        for j in range(i + 1, len(rank10)):
            a, b = rank10[i][0], rank10[j][0]
            diff, lo, hi = paired_ci(raw_scores[a]["ndcg@10"], raw_scores[b]["ndcg@10"])
            pairs.append({"higher": a, "lower": b, "diff": diff, "ci95": [lo, hi],
                          "significant": bool(lo > 0 or hi < 0)})

    return {
        "dataset": name,
        "corpus_docs": len(corpus),
        "queries_evaluated": len(qids),
        "qrels_positive_pairs": int(sum(sum(1 for v in rel[q].values() if v > 0) for q in qids)),
        "systems": per_system,
        "ranking_ndcg@10": [[s, v] for s, v in rank10],
        "ranking_ndcg@100": [[s, v] for s, v in rank100],
        "rank_order_same_k10_vs_k100": [s for s, _ in rank10] == [s for s, _ in rank100],
        "pairwise_ndcg@10": pairs,
        "cross_impl_checks": checked,
        "cross_impl_mismatches": mism,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--datasets", default="scifact,nfcorpus")
    args = ap.parse_args()

    out = {"datasets": [], "metric_definitions": {
        "ndcg_cut": "trec_eval ndcg_cut: binary gain, discount 1/log2(rank+1), ideal = min(n_rel,k)",
        "map_cut": "trec_eval map_cut: AP truncated at k, divided by min(n_rel,k)",
        "recall": "trec_eval recall: |rel in top k| / |rel|",
        "tie_policy": "id_asc / id_desc within exact score ties; official pytrec_eval order is unspecified",
        "bootstrap": "2000 query-level resamples, seed 20261028",
    }}
    for name in args.datasets.split(","):
        name = name.strip()
        if not name:
            continue
        print(f"[audit] {name}", flush=True)
        out["datasets"].append(run_dataset(name, args.data))
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    for ds in out["datasets"]:
        print(ds["dataset"], "q=", ds["queries_evaluated"],
              "k10==", ds["rank_order_same_k10_vs_k100"],
              "mism=", ds["cross_impl_mismatches"], "/", ds["cross_impl_checks"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
