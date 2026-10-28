#!/usr/bin/env python3
"""Before/after audit comparison on the public BEIR evaluation protocol.

The question is not "which retriever is best" but "does auditing the protocol
change the decision you would report, and does it change it in the right
places".

Three protocol views are compared on the same runs and the same information:

  B0  official leaderboard view   : mean nDCG@10, ordered, no uncertainty
  B1  strong simple rule          : B0 plus recall@100 (a cheap extra number
                                    that needs no audit machinery)
  A   audited view                : paired query-level bootstrap on nDCG@10,
                                    plus k-sensitivity (10 vs 100) and
                                    tie-policy sensitivity

Ground truth comes from two constructed controls whose answer is known by
construction:

  * a duplicate system (identical scores) -> a correct audit must say
    "indistinguishable", and must not report an ordering;
  * a degraded system (the top-ranked document is pushed below the cutoff)
    -> a correct audit must detect a real loss.

A decision rule that reports an order between the duplicate pair is a false
positive; one that fails to flag the degraded pair is a false negative.
No model is called.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beir_audit import (  # noqa: E402
    BM25, Tfidf, bootstrap_ci, map_cut, ndcg_cut, paired_ci, rank,
    read_jsonl, read_qrels, recall_cut,
)

K = (10, 100)


class Degraded:
    """Identical scores, but the top-ranked document is demoted below k=10.

    Simulates a retriever that found the relevant document and then loses it in
    the presentation layer: the observation exists, the reported ranking does
    not expose it. This is the concrete analogue of Paper E's visibility /
    detection split.
    """

    def __init__(self, base, corpus_ids):
        self.base = base
        self.ids = corpus_ids

    def scores(self, query: str) -> np.ndarray:
        s = self.base.scores(query)
        if len(s):
            top = int(np.argmax(s))
            s = s.copy()
            s[top] = s[top] - 1e6  # push it to the bottom deterministically
        return s


class Duplicate:
    def __init__(self, base, corpus_ids):
        self.base = base
        self.ids = corpus_ids

    def scores(self, query: str) -> np.ndarray:
        return self.base.scores(query)


def evaluate(systems, corpus, queries, rel, qids):
    out = {}
    for name, retr in systems.items():
        pq = {f"ndcg@{k}": [] for k in K}
        pq.update({f"recall@{k}": [] for k in K})
        pq["ndcg10_tieB"] = []
        pq["flip@10"] = []
        for q in qids:
            sc = retr.scores(queries[q])
            ra = rank(sc, retr.ids, "id_asc", max(K))
            rb = rank(sc, retr.ids, "id_desc", max(K))
            for k in K:
                pq[f"ndcg@{k}"].append(ndcg_cut(ra, rel[q], k))
                pq[f"recall@{k}"].append(recall_cut(ra, rel[q], k))
            pq["ndcg10_tieB"].append(ndcg_cut(rb, rel[q], 10))
            pq["flip@10"].append(0.0 if ra[:10] == rb[:10] else 1.0)
        out[name] = {k: np.array(v, dtype=float) for k, v in pq.items()}
    return out


def b0_order(m, key="ndcg@10"):
    return sorted(m, key=lambda s: -m[s][key].mean())


def verdict_sets(m, order):
    """Which pairs each view asserts as ordered."""
    b0 = set()
    for i in range(len(order)):
        for j in range(i + 1, len(order)):
            b0.add((order[i], order[j]))  # B0 always asserts a strict order

    b1 = set()
    lo = sorted(m, key=lambda s: -m[s]["recall@100"].mean())
    for i in range(len(lo)):
        for j in range(i + 1, len(lo)):
            b1.add((lo[i], lo[j]))

    audited = set()
    ties = set()
    for i in range(len(order)):
        for j in range(i + 1, len(order)):
            a, b = order[i], order[j]
            diff, lo_, hi_ = paired_ci(m[a]["ndcg@10"], m[b]["ndcg@10"])
            if lo_ > 0 or hi_ < 0:
                audited.add((a, b))
            else:
                ties.add((a, b))
    return b0, b1, audited, ties


def main() -> int:
    data = Path(sys.argv[1] if len(sys.argv) > 1 else "data")
    out_path = Path(sys.argv[2] if len(sys.argv) > 2 else "ab_result.json")

    report = {}
    for ds in ("scifact", "nfcorpus"):
        d = data / ds
        corpus = {r["_id"]: r for r in read_jsonl(str(d / "corpus.jsonl"))}
        queries = {r["_id"]: r["text"] for r in read_jsonl(str(d / "queries.jsonl"))}
        rel = read_qrels(str(d / "qrels" / "test.tsv"))
        qids = [q for q in rel if q in queries and any(v > 0 for v in rel[q].values())]

        base = BM25(corpus, 0.9, 0.4)
        systems = {
            "bm25_a": base,
            "bm25_b": BM25(corpus, 1.5, 0.6),
            "bm25_c": BM25(corpus, 1.2, 0.75),
            "tfidf": Tfidf(corpus),
            "dup_of_a": Duplicate(base, list(corpus)),
            "deg_a": Degraded(base, list(corpus)),
        }
        m = evaluate(systems, corpus, queries, rel, qids)
        order = b0_order(m)
        b0, b1, audited, ties = verdict_sets(m, order)

        # ground truth: dup pair is identical; deg pair is strictly worse
        truth_same = {("bm25_a", "dup_of_a")}
        truth_diff = {("deg_a", x) for x in ("bm25_a", "bm25_b", "bm25_c", "tfidf", "dup_of_a")}

        def classify(asserted):
            fp = sum(1 for p in asserted if tuple(sorted(p)) in {tuple(sorted(x)) for x in truth_same})
            tp = sum(1 for p in asserted if p in truth_diff)
            return {"asserted_orders": len(asserted), "true_different_flagged": tp,
                    "false_positive_on_duplicate": fp,
                    "true_different_total": len(truth_diff)}

        # explicit statements about the two controls
        dup = paired_ci(m["bm25_a"]["ndcg@10"], m["dup_of_a"]["ndcg@10"])
        deg = paired_ci(m["bm25_a"]["ndcg@10"], m["deg_a"]["ndcg@10"])

        report[ds] = {
            "queries": len(qids),
            "b0_order": [[s, float(m[s]["ndcg@10"].mean())] for s in order],
            "b0": classify(b0),
            "b1_recall100_order": [[s, float(m[s]["recall@100"].mean())]
                                   for s in sorted(m, key=lambda s: -m[s]["recall@100"].mean())],
            "b1": classify(b1),
            "audited_asserted": sorted(f"{a}>{b}" for a, b in audited),
            "audited_ties": sorted(f"{a}~{b}" for a, b in ties),
            "A": classify(audited),
            "control_duplicate": {"diff": dup[0], "ci95": list(dup[1:]),
                                  "audit_says_same": bool(dup[1] <= 0 <= dup[2])},
            "control_degraded": {"diff": deg[0], "ci95": list(deg[1:]),
                                 "audit_says_worse": bool(deg[1] > 0)},
            "k_sensitivity_order_agrees": list(order) ==
                                          list(sorted(m, key=lambda s: -m[s]["ndcg@100"].mean())),
            "tie_policy_query_flip_rate": float(np.mean(m["bm25_a"]["flip@10"])),
            "tie_policy_gap": float(m["bm25_a"]["ndcg@10"].mean() - m["bm25_a"]["ndcg10_tieB"].mean()),
        }
        print(ds, "B0 asserted", report[ds]["b0"]["asserted_orders"],
              "| A asserted", report[ds]["A"]["asserted_orders"],
              "| dup same", report[ds]["control_duplicate"]["audit_says_same"],
              "| deg worse", report[ds]["control_degraded"]["audit_says_worse"])

    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
