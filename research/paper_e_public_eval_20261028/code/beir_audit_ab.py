#!/usr/bin/env python3
"""Before/after comparison on the public BEIR evaluation protocol.

Revision 2 — corrected control pairing and a fair simple baseline.

Three views on the *same* target (mean graded nDCG@10) and the same available
information:

  B0  naive leaderboard   : sort by the mean, assert an order for every pair,
                            including pairs whose means are exactly equal.
  B1  point estimate      : sort by the mean but treat exactly equal means as a
                            tie. This is the strong simple baseline: no
                            resampling, no correction, one line of code.
  A   audit               : assert an order only when a paired query-level
                            bootstrap interval excludes zero, with Holm
                            adjustment reported alongside.

Two systems have a known answer by construction, and the pairing is checked in
both directions:

  duplicate(base)  identical scores            -> correct verdict: indistinguishable
  degraded(base)   top document pushed below k -> correct verdict: base is better

A view passes the duplicate control if it does *not* assert an order on that
pair, and passes the degradation control if it *does* assert base > degraded.

What the audit cannot do is adjudicate the near-tie pairs it withdraws: "not
distinguished" is a statement about the interval, not a proof of equality.

No model is called.

Usage:
    python beir_audit_ab.py --data DIR --out OUT.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beir_audit import (  # noqa: E402
    BM25, Tfidf, holm, ndcg_cut, paired_ci, rank, read_jsonl, read_qrels,
    recall_cut, sign_flip_p,
)

K = (10, 100)


class Duplicate:
    """Identical scores: a correct comparison must report a tie."""

    def __init__(self, base, ids):
        self.base, self.ids = base, ids

    def scores(self, q):
        return self.base.scores(q)


class Degraded:
    """Identical scores except the top document is pushed below the cutoff."""

    def __init__(self, base, ids):
        self.base, self.ids = base, ids

    def scores(self, q):
        s = self.base.scores(q).copy()
        if len(s):
            s[int(np.argmax(s))] -= 1e6
        return s


def evaluate(systems, queries, rel, qids):
    out = {}
    for name, retr in systems.items():
        nd, rc, fl_order, fl_members = [], [], [], []
        for q in qids:
            sc = retr.scores(queries[q])
            ra = rank(sc, retr.ids, "id_asc", max(K))
            rb = rank(sc, retr.ids, "id_desc", max(K))
            nd.append(ndcg_cut(ra, rel[q], 10, graded=True))
            rc.append(recall_cut(ra, rel[q], 100))
            fl_order.append(0.0 if ra[:10] == rb[:10] else 1.0)
            fl_members.append(0.0 if set(ra[:10]) == set(rb[:10]) else 1.0)
        out[name] = {"ndcg10": np.array(nd, float), "recall100": np.array(rc, float),
                     "flip_order": np.array(fl_order), "flip_members": np.array(fl_members)}
    return out


def views(m):
    """Assertion sets for the three views, plus the evidence behind each."""
    names = list(m)
    mean = {n: float(m[n]["ndcg10"].mean()) for n in names}
    naive = sorted(names, key=lambda n: -mean[n])          # stable: orders exact ties

    b0 = {(naive[i], naive[j]) for i in range(len(naive)) for j in range(i + 1, len(naive))}

    b1 = set()
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            if mean[a] > mean[b]:
                b1.add((a, b))
            elif mean[b] > mean[a]:
                b1.add((b, a))
            # exactly equal -> tie, assert nothing

    detail = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            hi, lo = (a, b) if mean[a] >= mean[b] else (b, a)
            diff, l, h = paired_ci(m[hi]["ndcg10"], m[lo]["ndcg10"])
            detail[(hi, lo)] = {"diff": diff, "ci95": [l, h],
                                "p": sign_flip_p(m[hi]["ndcg10"], m[lo]["ndcg10"]),
                                "excludes_zero": bool(l > 0 or h < 0)}
    keys = list(detail)
    adj = holm([detail[k]["p"] for k in keys])
    for k, q in zip(keys, adj):
        detail[k]["p_holm"] = q

    audit = {k for k in keys if detail[k]["excludes_zero"]}
    audit_holm = {k for k in keys if detail[k]["p_holm"] < 0.05}
    return {"mean": mean, "b0": b0, "b1": b1, "audit": audit,
            "audit_holm": audit_holm, "detail": detail, "naive_order": naive}


def control_report(asserted, dup_pair, deg_pair):
    """dup_pair=(base,dup) unordered; deg_pair=(base,deg) with base better."""
    dup_hit = dup_pair in asserted or (dup_pair[1], dup_pair[0]) in asserted
    deg_hit = deg_pair in asserted
    return {"asserts_order_on_duplicate": bool(dup_hit),
            "asserts_base_above_degraded": bool(deg_hit),
            "passes_duplicate_control": not dup_hit,
            "passes_degradation_control": deg_hit}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    data, out_path = Path(args.data), Path(args.out)

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
        m = evaluate(systems, queries, rel, qids)
        v = views(m)

        dup_pair = ("bm25_a", "dup_of_a")
        deg_pair = ("bm25_a", "deg_a")
        ctrl = {k: control_report(v[k], dup_pair, deg_pair)
                for k in ("b0", "b1", "audit", "audit_holm")}

        # near-tie pairs: B1 asserts them, the audit withdraws them
        withdrawn = sorted(f"{a}>{b}" for (a, b) in v["b1"] - v["audit"])
        # do the withdrawn pairs include the constructed controls?
        withdrawn_touches_control = [p for p in withdrawn
                                     if "dup_of_a" in p or "deg_a" in p]

        degd = v["detail"][deg_pair]
        dupd = v["detail"].get(dup_pair) or v["detail"].get((dup_pair[1], dup_pair[0]))

        report[ds] = {
            "queries": len(qids),
            "naive_order": [[s, round(v["mean"][s], 6)] for s in v["naive_order"]],
            "asserted_counts": {"b0": len(v["b0"]), "b1": len(v["b1"]),
                                "audit": len(v["audit"]), "audit_holm": len(v["audit_holm"])},
            "controls": ctrl,
            "duplicate_pair_detail": dupd,
            "degraded_pair_detail": degd,
            "pairs_b1_asserts_audit_withdraws": withdrawn,
            "withdrawn_touching_controls": withdrawn_touches_control,
            "tie_policy": {
                "order_changed_rate@10": float(m["bm25_a"]["flip_order"].mean()),
                "members_changed_rate@10": float(m["bm25_a"]["flip_members"].mean()),
            },
            "multiplicity": {
                "pairs": len(v["detail"]),
                "uncorrected_assertions": len(v["audit"]),
                "holm_assertions": len(v["audit_holm"]),
            },
        }
        print(ds, "B0", len(v["b0"]), "B1", len(v["b1"]), "A", len(v["audit"]),
              "A_holm", len(v["audit_holm"]),
              "| dup pass", ctrl["b1"]["passes_duplicate_control"],
              "| deg pass", ctrl["b1"]["passes_degradation_control"])

    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
