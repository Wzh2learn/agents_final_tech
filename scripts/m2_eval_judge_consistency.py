#!/usr/bin/env python3
"""judge 一致性检查（G13）: 同一答案重复 judge 3 次, 看四维分数是否漂移。

RAGAS/DeepEval 方法论要求 judge 可复现; 本脚本度量我们 :8004 temp=0 judge 的
自一致性。漂移 >1 分(任一维) 即标 DRIFT, 入台账。不碰冻结节点。
用法: venv/bin/python scripts/m2_eval_judge_consistency.py [--ids q01_fuxi_total_assets,...] [--runs 3]
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import m1_rag_ingest as ing
from m2_eval_judge import judge_one, DIMS, FIXTURE

DET = os.path.join("logs", "graph", "eval", "m2_deterministic_report.json")
OUT = os.path.join("logs", "graph", "eval", "judge_consistency_report.json")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ids", default="")
    ap.add_argument("--runs", type=int, default=3)
    args = ap.parse_args()

    det = json.load(open(DET, encoding="utf-8"))
    fx = {q["id"]: q for q in json.load(open(FIXTURE, encoding="utf-8"))["questions"]}
    results = det["results"]
    if args.ids:
        wanted = set(args.ids.split(","))
        results = [r for r in results if r["id"] in wanted]
    else:  # 默认抽 3 条: 首条 + 一条多轮 + 一条不可答(若有)
        picks = [results[0]]
        multi = next((r for r in results if len(r["turns"]) > 1), None)
        unans = next((r for r in results if fx.get(r["id"], {}).get("unanswerable")), None)
        for p in (multi, unans):
            if p and p not in picks:
                picks.append(p)
        results = picks[:3]

    rag = ing.RAGService(collection_name=ing.COLLECTION)
    out = []
    drift_any = False
    for r in results:
        qid = r["id"]
        answer = r["answers"][-1]
        q_ret = " ".join(r["turns"]) if len(r["turns"]) > 1 else r["turns"][-1]
        try:
            docs = rag.smart_retrieve(query=q_ret, top_k=5,
                                      collection_names=[ing.COLLECTION],
                                      max_results=5, use_rerank=False)
        except Exception:
            docs = []
        context = "\n".join((d.get("content") or d.get("text") or "") for d in docs)
        fxd = fx.get(qid, {})
        runs = []
        for _ in range(args.runs):
            runs.append(judge_one(q_ret, context, answer,
                                  json.dumps(r.get("sources", []), ensure_ascii=False),
                                  fxd.get("expected", ""), bool(fxd.get("unanswerable"))))
        per_dim = {}
        for d in DIMS:
            scores = [run[d]["score"] for run in runs]
            valid = [s for s in scores if s is not None]
            spread = (max(valid) - min(valid)) if valid else None
            per_dim[d] = {"scores": scores, "spread": spread}
            if spread is not None and spread > 1:
                drift_any = True
        out.append({"id": qid, "runs": runs, "per_dim": per_dim})
        print(f"{qid}: " + ", ".join(f"{d}={per_dim[d]['scores']}(spread {per_dim[d]['spread']})" for d in DIMS))
    json.dump({"runs": args.runs, "drift_any": drift_any, "results": out},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("DRIFT" if drift_any else "STABLE", "->", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
