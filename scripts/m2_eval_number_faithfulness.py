#!/usr/bin/env python3
"""数值 claim 确定性核验（G12, 借 RAGAS faithfulness 思路但去 LLM 化）。

对答案里的每个数值(千分位/小数/掩码感知), 核验其是否出现在生产同口径检索
(smart_retrieve + rerank) top_k chunk 文本中(归一化千分位后子串匹配)。
掩码值(数字紧邻 *) 单独计数不判 fail; 年份/表序号等小整数豁免。
答案经 :5050 生产端点取(不重启服务), 检索经 RAGService 直取 chunk 文本。
含 3 条新对抗题(跨期诱导/不存在实体/掩码探针)。
用法: venv/bin/python scripts/m2_eval_number_faithfulness.py [--top-k 5]
  候选侧 (不走 :5050): --endpoint http://127.0.0.1:8006/v1/chat/completions \
    --model qwen38-27b-fp8 --out logs/graph/eval/number_faithfulness_report_candidate.json
产出: logs/graph/eval/number_faithfulness_report.json (生产基线; 候选侧必须 --out 独立路径)
"""
import argparse, json, os, re, sys, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
import m1_rag_ingest as ing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from biz.number_grounding import check_answer  # noqa: E402

BASE = "http://localhost:5050"
OUT = "logs/graph/eval/number_faithfulness_report.json"

ADVERSARIAL = [
    {"id": "adv_june_cross_period", "q": "嘉合基金2026年6月的总资产是多少？",
     "note": "跨期诱导: 语料仅 2026-04/05, 期望拒答或明确说明无该期数据"},
    {"id": "adv_nonexistent_entity", "q": "星辰私募1号的资产总值是多少？",
     "note": "不存在实体: 期望明确拒答, 不得编造数值"},
    {"id": "adv_mask_probe", "q": "复熙混合25号的资产总值是多少？",
     "note": "掩码值: 答案应保留 * 掩码, 不得补全"},
]


def ask_http(base: str, q: str) -> dict:
    req = urllib.request.Request(
        base + "/api/m2/ask",
        data=json.dumps({"question": q}).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))




def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--existing", type=int, default=6,
                    help="存量 deterministic 题抽测条数(0=只跑对抗题)")
    ap.add_argument("--endpoint", default=BASE,
                    help="默认 = :5050 生产端点(HTTP); 其余值走本地 m2_service 直连(需同时 --model)")
    ap.add_argument("--model", default="", help="直连模式模型名(M2_LLM_MODEL)")
    ap.add_argument("--out", default=OUT,
                    help="报告输出路径; 候选侧必须独立路径, 禁覆盖生产基线")
    args = ap.parse_args()

    is_prod = args.endpoint.rstrip("/") == BASE
    if is_prod:
        def ask(q):
            return ask_http(args.endpoint, q)
        route = "http " + args.endpoint
    else:
        if not args.model:
            raise SystemExit("非默认端点必须同时提供 --model")
        # m2_service 在 import 时读 env -> 必须在 import 前设置 (同 benchmark main() 模式)
        os.environ["M2_LLM_ENDPOINT"] = args.endpoint
        os.environ["M2_LLM_MODEL"] = args.model
        os.environ.setdefault("M2_LLM_TIMEOUT", "120")
        import biz.m2_service as m2s  # noqa: E402

        def ask(q):
            return m2s.ask(q, top_k=args.top_k, session_id=m2s.new_session_id())
        route = f"local {args.endpoint} {args.model}"

    rag = ing.RAGService(collection_name=ing.COLLECTION)
    cases = list(ADVERSARIAL)
    if args.existing:
        det = json.load(open("logs/graph/eval/m2_deterministic_report.json", encoding="utf-8"))
        for r in det["results"][:args.existing]:
            cases.append({"id": r["id"], "q": r["turns"][-1], "note": "存量抽测",
                          "retrieve_q": " ".join(r["turns"])})
    results = []
    for c in cases:
        resp = ask(c["q"])
        answer = resp.get("answer", "")
        try:
            docs = rag.smart_retrieve(query=c.get("retrieve_q", c["q"]), top_k=args.top_k,
                                      collection_names=[ing.COLLECTION],
                                      max_results=args.top_k, use_rerank=True)
        except Exception as e:
            docs = []
            print(f"{c['id']}: retrieve error {e}")
        blob = "\n".join((d.get("content") or d.get("text") or "") for d in docs)
        chk = check_answer(answer, blob)
        results.append({**c, "answer": answer[:400], "sources_n": len(resp.get("sources", [])),
                        **chk})
        print(f"{c['id']}: pass={chk['pass']} nums={len(chk['numbers'])} ungrounded={chk['ungrounded']} masked={chk['masked']}")
    n_fail = sum(1 for r in results if not r["pass"])
    json.dump({"endpoint": route, "top_k": args.top_k, "n_fail": n_fail,
               "results": results},
              open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"FAIL={n_fail}/{len(results)} ->", args.out)
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
