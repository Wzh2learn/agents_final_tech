#!/usr/bin/env python3
"""Per-query cross-check of graded nDCG and MAP against the official trec_eval.

The audit's metrics are re-implementations. This script writes each system's
ranking as a TREC run file (scores made strictly decreasing so the run encodes
exactly the ranking the audit produced), runs the official trec_eval binary
with `-q -m ndcg_cut -m map_cut -m recall`, and compares every query.

It validates the *metric definitions given a ranking*; it does not validate the
audit's tie-breaking, which is a protocol question audited separately.

Usage: python official_crosscheck.py --data DIR --trec_eval BIN --out OUT.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beir_audit import (  # noqa: E402
    BM25, Tfidf, map_cut, ndcg_cut, rank, read_jsonl, read_qrels, recall_cut,
)

KS = (10, 100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--trec_eval", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = {"trec_eval": {"binary": args.trec_eval}, "datasets": {}}
    ver = subprocess.run([args.trec_eval, "-v"], capture_output=True, text=True)
    out["trec_eval"]["version_output"] = (ver.stdout + ver.stderr).strip()[:400]

    for ds in ("scifact", "nfcorpus"):
        d = Path(args.data) / ds
        corpus = {r["_id"]: r for r in read_jsonl(str(d / "corpus.jsonl"))}
        queries = {r["_id"]: r["text"] for r in read_jsonl(str(d / "queries.jsonl"))}
        rel = read_qrels(str(d / "qrels" / "test.tsv"))
        qids = [q for q in rel if q in queries and any(v > 0 for v in rel[q].values())]

        systems = {
            "bm25_09_04": BM25(corpus, 0.9, 0.4),
            "bm25_12_075": BM25(corpus, 1.2, 0.75),
            "bm25_05_03": BM25(corpus, 0.5, 0.3),
            "bm25_15_06": BM25(corpus, 1.5, 0.6),
            "tfidf": Tfidf(corpus),
        }
        ds_out = {"queries": len(qids), "systems": {}, "max_abs_diff": 0.0,
                  "mismatches": 0, "comparisons": 0, "per_metric": {}}
        with tempfile.TemporaryDirectory() as td:
            qrels_f = Path(td) / "qrels.txt"
            with qrels_f.open("w", encoding="utf-8") as fh:
                for q in qids:
                    for doc, g in rel[q].items():
                        if g > 0:
                            fh.write(f"{q} 0 {doc} {g}\n")
            for sname, retr in systems.items():
                run_f = Path(td) / f"{sname}.run"
                mine = {q: {} for q in qids}
                with run_f.open("w", encoding="utf-8") as fh:
                    for q in qids:
                        r = rank(retr.scores(queries[q]), retr.ids, "id_asc", 1000)
                        for pos, doc in enumerate(r, start=1):
                            # strictly decreasing scores encode exactly this ranking
                            fh.write(f"{q} Q0 {doc} {pos} {100000 - pos} {sname}\n")
                        for k in KS:
                            mine[q][f"ndcg_cut_{k}"] = ndcg_cut(r, rel[q], k, graded=True)
                            mine[q][f"map_cut_{k}"] = map_cut(r, rel[q], k)
                            mine[q][f"recall_{k}"] = recall_cut(r, rel[q], k)
                cmd = [args.trec_eval, "-q",
                       "-m", "ndcg_cut." + ",".join(str(k) for k in KS),
                       "-m", "map_cut." + ",".join(str(k) for k in KS),
                       "-m", "recall." + ",".join(str(k) for k in KS),
                       str(qrels_f), str(run_f)]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode != 0:
                    raise SystemExit(f"trec_eval failed: {res.stderr[:400]}")
                official = {}
                for line in res.stdout.splitlines():
                    parts = line.split()
                    if len(parts) == 3 and parts[0] in ("ndcg_cut_10", "ndcg_cut_100",
                                                        "map_cut_10", "map_cut_100",
                                                        "recall_10", "recall_100"):
                        official.setdefault(parts[1], {})[parts[0]] = float(parts[2])
                sysm = {"queries_compared": 0, "max_abs_diff": 0.0, "mismatches": 0}
                for q in qids:
                    if q not in official:
                        continue
                    sysm["queries_compared"] += 1
                    for metric, val in official[q].items():
                        diff = abs(val - mine[q][metric])
                        sysm["max_abs_diff"] = max(sysm["max_abs_diff"], diff)
                        ds_out["max_abs_diff"] = max(ds_out["max_abs_diff"], diff)
                        ds_out["comparisons"] += 1
                        # trec_eval prints with four decimals, so the smallest
                        # observable disagreement is one unit in the last place.
                        if diff > 1e-4:
                            sysm["mismatches"] += 1
                            ds_out["mismatches"] += 1
                        if round(val, 4) == round(mine[q][metric], 4):
                            sysm["match_at_printed_precision"] = sysm.get(
                                "match_at_printed_precision", 0) + 1
                        pm = ds_out["per_metric"].setdefault(metric, {"n": 0, "max": 0.0})
                        pm["n"] += 1
                        pm["max"] = max(pm["max"], diff)
                ds_out["systems"][sname] = sysm
        out["datasets"][ds] = ds_out
        print(ds, "queries", ds_out["queries"], "comparisons", ds_out["comparisons"],
              "mismatches", ds_out["mismatches"], "max|diff|", f"{ds_out['max_abs_diff']:.3e}")

    Path(args.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
