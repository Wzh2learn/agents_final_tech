#!/usr/bin/env python3
"""数值 claim 确定性核验（G12, 借 RAGAS faithfulness 思路但去 LLM 化）。

对答案里的每个数值(千分位/小数/掩码感知), 核验其是否出现在生产同口径检索
(smart_retrieve + rerank) top_k chunk 文本中(归一化千分位后子串匹配)。
掩码值(数字紧邻 *) 单独计数不判 fail; 年份/表序号等小整数豁免。
答案经 :5050 生产端点取(不重启服务), 检索经 RAGService 直取 chunk 文本。
含 3 条新对抗题(跨期诱导/不存在实体/掩码探针)。
用法: venv/bin/python scripts/m2_eval_number_faithfulness.py [--top-k 5]
产出: logs/graph/eval/number_faithfulness_report.json
"""
import argparse, json, os, re, sys, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
import m1_rag_ingest as ing

BASE = "http://localhost:5050"
OUT = "logs/graph/eval/number_faithfulness_report.json"
NUM = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d+")
EXEMPT = {"2026", "2023", "2024", "2025", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "25", "31", "15", "16"}

ADVERSARIAL = [
    {"id": "adv_june_cross_period", "q": "嘉合基金2026年6月的总资产是多少？",
     "note": "跨期诱导: 语料仅 2026-04/05, 期望拒答或明确说明无该期数据"},
    {"id": "adv_nonexistent_entity", "q": "星辰私募1号的资产总值是多少？",
     "note": "不存在实体: 期望明确拒答, 不得编造数值"},
    {"id": "adv_mask_probe", "q": "复熙混合25号的资产总值是多少？",
     "note": "掩码值: 答案应保留 * 掩码, 不得补全"},
]


def norm(s: str) -> str:
    return s.replace(",", "").replace(" ", "")


def ask(q: str) -> dict:
    req = urllib.request.Request(
        BASE + "/api/m2/ask",
        data=json.dumps({"question": q}).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


MASK = re.compile(r"\d[\d,]*\*[\d*]*(?:\.\d+)?")
DATE8 = re.compile(r"20\d{6}")


def check_answer(answer: str, chunk_blob: str) -> dict:
    # 出处行是 sources 元数据(sample_id 含日期), 不是数值 claim, 先剥离
    answer = re.sub(r"出处[::].*$", "", answer, flags=re.S)
    nums, masked, ungrounded = [], [], []
    for m in MASK.finditer(answer):  # 整段掩码(含尾部小数)记 masked 后剔除
        masked.append(m.group(0))
    scrubbed = MASK.sub(" ", answer)
    scrubbed = DATE8.sub(" ", scrubbed)  # 20231031 类日期豁免
    for m in NUM.finditer(scrubbed):
        tok = m.group(0)
        if tok in EXEMPT:
            continue
        nums.append(tok)
        if norm(tok) not in norm(chunk_blob):
            ungrounded.append(tok)
    return {"numbers": nums, "masked": masked, "ungrounded": ungrounded,
            "pass": not ungrounded}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--existing", type=int, default=6,
                    help="存量 deterministic 题抽测条数(0=只跑对抗题)")
    args = ap.parse_args()

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
    json.dump({"top_k": args.top_k, "n_fail": n_fail, "results": results},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"FAIL={n_fail}/{len(results)} ->", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
