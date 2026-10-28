#!/usr/bin/env python3
"""Audit a public IR evaluation protocol (BEIR) end to end, without any model.

Revision 2 — corrected scoring contract
---------------------------------------
The first version binarised relevance and divided MAP by ``min(n_rel, K)``.
Both are wrong relative to the scoring path BEIR actually calls:

* BEIR's ``EvaluateRetrieval`` delegates to ``pytrec_eval`` with
  ``ndcg_cut`` / ``map_cut`` / ``recall``, and trec_eval uses the **raw qrels
  grade as the gain**.  Binarising relevance changes the metric whenever the
  qrels are graded.
* trec_eval's ``map_cut.K`` divides the truncated average precision by the
  **total number of relevant documents**, not by ``min(n_rel, K)``.

Both corrections are pinned by counter-examples that fail loudly if the
implementation regresses (``self_test``).

``pytrec_eval`` is not installed on this machine, so the claim here is
"matches the published trec_eval definition, checked against hand-computed
counter-examples and a second independent implementation", **not** "verified
against the official binary".

No model is called; this case costs zero generation tokens.

Usage:
    python beir_audit.py --data DIR --out OUT.json [--datasets scifact,nfcorpus]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

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
        self.postings = {t: (np.array([p[0] for p in v]),
                             np.array([p[1] for p in v], dtype=np.float32))
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
        df: dict[str, int] = defaultdict(int)
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
        self.postings = {t: (np.array([p[0] for p in v]),
                             np.array([p[1] for p in v], dtype=np.float32))
                         for t, v in postings.items()}

    def scores(self, query: str) -> np.ndarray:
        s = np.zeros(len(self.ids), dtype=np.float32)
        toks: dict[str, int] = defaultdict(int)
        for t in tokenize(query):
            if t in self.idf:
                toks[t] += 1
        qn = math.sqrt(sum(((1 + math.log(c)) * self.idf[t]) ** 2
                           for t, c in toks.items())) or 1.0
        for t, c in toks.items():
            idx, w = self.postings[t]
            s[idx] += ((1 + math.log(c)) * self.idf[t]) * w
        return s / (self.norm * qn)


def rank(scores: np.ndarray, ids: list[str], tie: str, topk: int) -> list[str]:
    """Rank by score desc; ties broken deterministically by doc id."""
    order = np.argsort(-scores, kind="stable")
    s = scores[order]
    out: list[str] = []
    i, n = 0, len(order)
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
# trec_eval-compatible metrics
# --------------------------------------------------------------------------
def _discount(rank1: int) -> float:
    """trec_eval ndcg_cut discount: 1 at rank 1, 1/log2(r+1) beyond."""
    return 1.0 if rank1 == 1 else 1.0 / math.log2(rank1 + 1)


def dcg(gains: list[float]) -> float:
    return sum(g * _discount(i + 1) for i, g in enumerate(gains))


def ndcg_cut(ranked: list[str], rel: dict[str, int], k: int, graded: bool = True) -> float:
    """trec_eval ndcg_cut: gain is the raw qrels grade (graded=True) or {0,1}."""
    gains = []
    for d in ranked[:k]:
        r = rel.get(d, 0)
        gains.append(float(r if graded else (1.0 if r > 0 else 0.0)))
    ideal_grades = sorted((float(v if graded else (1.0 if v > 0 else 0.0))
                           for v in rel.values() if v > 0), reverse=True)[:k]
    ideal = dcg(ideal_grades)
    return dcg(gains) / ideal if ideal > 0 else 0.0


def map_cut(ranked: list[str], rel: dict[str, int], k: int) -> float:
    """trec_eval map_cut.K: sum of precision at each relevant hit / n_rel."""
    n_rel = sum(1 for v in rel.values() if v > 0)
    if n_rel == 0:
        return 0.0
    hits, total = 0, 0.0
    for i, d in enumerate(ranked[:k], start=1):
        if rel.get(d, 0) > 0:
            hits += 1
            total += hits / i
    return total / n_rel


def recall_cut(ranked: list[str], rel: dict[str, int], k: int) -> float:
    n_rel = sum(1 for v in rel.values() if v > 0)
    if not n_rel:
        return 0.0
    return sum(1 for d in ranked[:k] if rel.get(d, 0) > 0) / n_rel


def ndcg_cut_ref(ranked: list[str], rel: dict[str, int], k: int, graded: bool = True) -> float:
    """Second, independent statement of the same definition (no shared helpers)."""
    num = 0.0
    for pos, d in enumerate(ranked[:k]):
        r = rel.get(d, 0)
        g = float(r if graded else (1.0 if r > 0 else 0.0))
        num += g if pos == 0 else g / math.log2(pos + 2)
    pool = sorted((float(v if graded else (1.0 if v > 0 else 0.0))
                   for v in rel.values() if v > 0), reverse=True)[:k]
    den = 0.0
    for pos in range(len(pool)):
        den += pool[pos] if pos == 0 else pool[pos] / math.log2(pos + 2)
    return num / den if den else 0.0


def self_test() -> list[dict]:
    """Counter-examples that pin the two definitions that were previously wrong."""
    cases = []

    def check(name, got, want, tol=1e-6):
        ok = abs(got - want) <= tol
        cases.append({"case": name, "got": round(got, 10), "want": round(want, 10), "ok": ok})
        if not ok:
            raise SystemExit(f"metric self-test failed: {name} got {got} want {want}")

    check("ndcg_graded_[1,2]", ndcg_cut(["a", "b"], {"a": 1, "b": 2}, 2), 0.8597188160)
    check("ndcg_graded_[2,1]", ndcg_cut(["b", "a"], {"a": 1, "b": 2}, 2), 1.0)
    check("ndcg_binary_[1,2]", ndcg_cut(["a", "b"], {"a": 1, "b": 2}, 2, graded=False), 1.0)
    check("ndcg_ref_agrees", ndcg_cut_ref(["a", "b"], {"a": 1, "b": 2}, 2), 0.8597188160)
    check("map_k1_two_rel", map_cut(["a", "b"], {"a": 1, "b": 1}, 1), 0.5)
    check("map_k2_both_hit", map_cut(["a", "b"], {"a": 1, "b": 1}, 2), 1.0)
    check("map_k1_miss", map_cut(["x", "a"], {"a": 1, "b": 1}, 1), 0.0)
    check("recall_k1_two_rel", recall_cut(["a"], {"a": 1, "b": 1}, 1), 0.5)
    return cases


# --------------------------------------------------------------------------
# Audit helpers
# --------------------------------------------------------------------------
def bootstrap_ci(x: np.ndarray, n: int = 2000, seed: int = 20261028) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n, len(x)))
    means = x[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def paired_ci(a: np.ndarray, b: np.ndarray, n: int = 2000, seed: int = 20261028):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(a), size=(n, len(a)))
    d = a[idx].mean(axis=1) - b[idx].mean(axis=1)
    return float(a.mean() - b.mean()), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def holm(pvals: list[float]) -> list[float]:
    """Holm step-down adjusted p-values, order preserved."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank_i, i in enumerate(order):
        running = max(running, min(1.0, (m - rank_i) * pvals[i]))
        adj[i] = running
    return adj


def sign_flip_p(a: np.ndarray, b: np.ndarray, n: int = 2000, seed: int = 20261028) -> float:
    """Two-sided paired sign-flip permutation p-value on the mean difference."""
    d = a - b
    obs = abs(d.mean())
    rng = np.random.default_rng(seed)
    signs = rng.choice([-1.0, 1.0], size=(n, len(d)))
    perm = np.abs((signs * d).mean(axis=1))
    return float((np.sum(perm >= obs) + 1) / (n + 1))


def run_dataset(name: str, root: str) -> dict:
    d = os.path.join(root, name)
    corpus = {r["_id"]: r for r in read_jsonl(os.path.join(d, "corpus.jsonl"))}
    queries = {r["_id"]: r["text"] for r in read_jsonl(os.path.join(d, "queries.jsonl"))}
    rel = read_qrels(os.path.join(d, "qrels", "test.tsv"))
    qids = [q for q in rel if q in queries and any(v > 0 for v in rel[q].values())]

    grade_hist = Counter(v for q in qids for v in rel[q].values())
    systems = {
        "bm25_k1=0.9_b=0.4": BM25(corpus, 0.9, 0.4),
        "bm25_k1=1.2_b=0.75": BM25(corpus, 1.2, 0.75),
        "bm25_k1=0.5_b=0.3": BM25(corpus, 0.5, 0.3),
        "bm25_k1=1.5_b=0.6": BM25(corpus, 1.5, 0.6),
        "tfidf_cosine": Tfidf(corpus),
    }

    per_system: dict[str, dict] = {}
    raw: dict[str, dict[str, np.ndarray]] = {}
    for sname, retr in systems.items():
        pq = {f"{m}@{k}": [] for m in ("ndcg", "ndcg_bin", "map", "recall") for k in K_EVAL}
        pq["tie_order_changed@10"] = []
        pq["tie_members_changed@10"] = []
        pq["tie_boundary@10"] = []
        pq["ndcg10_tieB"] = []
        for q in qids:
            sc = retr.scores(queries[q])
            ra = rank(sc, retr.ids, "id_asc", max(K_EVAL))
            rb = rank(sc, retr.ids, "id_desc", max(K_EVAL))
            for k in K_EVAL:
                pq[f"ndcg@{k}"].append(ndcg_cut(ra, rel[q], k, graded=True))
                pq[f"ndcg_bin@{k}"].append(ndcg_cut(ra, rel[q], k, graded=False))
                pq[f"map@{k}"].append(map_cut(ra, rel[q], k))
                pq[f"recall@{k}"].append(recall_cut(ra, rel[q], k))
            pq["ndcg10_tieB"].append(ndcg_cut(rb, rel[q], 10, graded=True))
            pq["tie_order_changed@10"].append(0.0 if ra[:10] == rb[:10] else 1.0)
            pq["tie_members_changed@10"].append(0.0 if set(ra[:10]) == set(rb[:10]) else 1.0)
            srt = np.sort(sc)[::-1]
            pq["tie_boundary@10"].append(1.0 if srt[9] == srt[10] else 0.0)
        raw[sname] = {k: np.array(v, dtype=float) for k, v in pq.items()}

        entry = {}
        for m in ("ndcg", "ndcg_bin", "map", "recall"):
            for k in K_EVAL:
                v = raw[sname][f"{m}@{k}"]
                lo, hi = bootstrap_ci(v)
                entry[f"{m}@{k}"] = {"mean": float(v.mean()), "ci95": [lo, hi]}
        entry["tie_policy"] = {
            "order_changed_rate@10": float(raw[sname]["tie_order_changed@10"].mean()),
            "members_changed_rate@10": float(raw[sname]["tie_members_changed@10"].mean()),
            "boundary_tie_rate@10": float(raw[sname]["tie_boundary@10"].mean()),
            "ndcg10_asc": float(raw[sname]["ndcg@10"].mean()),
            "ndcg10_desc": float(raw[sname]["ndcg10_tieB"].mean()),
            "ndcg10_gap": float(raw[sname]["ndcg@10"].mean() - raw[sname]["ndcg10_tieB"].mean()),
        }
        per_system[sname] = entry

    mism = checked = 0
    for sname, retr in systems.items():
        for q in qids[:20]:
            r = rank(retr.scores(queries[q]), retr.ids, "id_asc", 100)
            for k in K_EVAL:
                for graded in (True, False):
                    a = ndcg_cut(r, rel[q], k, graded=graded)
                    b = ndcg_cut_ref(r, rel[q], k, graded=graded)
                    checked += 1
                    if abs(a - b) > 1e-9:
                        mism += 1

    def order(key: str) -> list[tuple[str, float]]:
        return sorted(((s, per_system[s][key]["mean"]) for s in systems), key=lambda x: -x[1])

    rank10, rank100 = order("ndcg@10"), order("ndcg@100")
    pairs = []
    for i in range(len(rank10)):
        for j in range(i + 1, len(rank10)):
            a, b = rank10[i][0], rank10[j][0]
            diff, lo, hi = paired_ci(raw[a]["ndcg@10"], raw[b]["ndcg@10"])
            pairs.append({"higher": a, "lower": b, "diff": diff, "ci95": [lo, hi],
                          "p_signflip": sign_flip_p(raw[a]["ndcg@10"], raw[b]["ndcg@10"]),
                          "ci_excludes_zero": bool(lo > 0 or hi < 0)})
    adj = holm([p["p_signflip"] for p in pairs])
    for p, q in zip(pairs, adj):
        p["p_holm"] = q
        p["significant_holm"] = bool(q < 0.05)

    return {
        "dataset": name,
        "corpus_docs": len(corpus),
        "queries_evaluated": len(qids),
        "qrels_positive_pairs": int(sum(sum(1 for v in rel[q].values() if v > 0) for q in qids)),
        "grade_histogram": {str(k): int(v) for k, v in sorted(grade_hist.items())},
        "graded_equals_binary": set(grade_hist) <= {1},
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

    tests = self_test()
    out = {
        "metric_contract": {
            "ndcg_cut": "trec_eval ndcg_cut: gain = raw qrels grade; discount 1 at rank 1 then 1/log2(r+1); ideal = top-k grades",
            "map_cut": "trec_eval map_cut.K: sum of precision at each relevant hit within K, divided by total n_rel",
            "recall": "trec_eval recall.K: |relevant within top K| / n_rel",
            "binary_ndcg": "also reported for contrast; scifact qrels are binary so the two coincide there",
            "verification": "hand-computed counter-examples plus a second independent implementation; the pytrec_eval binary was NOT run",
            "ignore_identical_ids": "BEIR's default drops documents whose id equals the query id; on these subsets queries and corpus share no ids, so it cannot bind",
        },
        "self_test": tests,
        "datasets": [],
    }
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
              "grades=", ds["grade_histogram"],
              "k10==k100", ds["rank_order_same_k10_vs_k100"],
              "mism", ds["cross_impl_mismatches"], "/", ds["cross_impl_checks"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
