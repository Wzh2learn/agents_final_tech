#!/usr/bin/env python3
"""M2 AI judge 层 (P2.2 沉淀, 2026-08-09)。

用本地 :8004 35B (temperature=0) 对 /api/m2/ask 的答案做四维 rubric 打分：
- faithfulness           忠实度：答案只使用检索到的内容（期望答案随 prompt 注入，指令级隔离限定仅 numeric_correctness 可用；结构性隔离为后续项，见 audit 2026-08-10 F13）
- numeric_correctness    数值正确性：答案数值与参考期望一致（唯一允许看期望值的维度）
- citation_quality       引用质量：来源非空、具体、与答案一致
- refusal_appropriateness 拒绝恰当性：应拒答题明确拒绝；可答题不错误拒答

输入 = scripts/m2_eval_deterministic.py 的 report（复用其答案，不重复打 :5050）；
检索上下文另经 RAGService.smart_retrieve 现取（只读，与生产检索同路径）。
rubric prompt 存档于下方 JUDGE_PROMPT 常量 —— 唯一信源，改动需同步 docs/18 记录。

用法:
  python scripts/m2_eval_judge.py --input logs/graph/eval/m2_deterministic_report.json
退出码: 0=完成 (评分结果不判失败) 2=judge 服务或集合不可用
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

JUDGE_ENDPOINT = os.environ.get(
    "M2_JUDGE_ENDPOINT", "http://127.0.0.1:8004/v1/chat/completions")
JUDGE_MODEL = os.environ.get("M2_JUDGE_MODEL", "Qwen3.6-35B-A3B-Q4_K_M.gguf")
FIXTURE = os.path.join(REPO_ROOT, "tests", "fixtures", "m2_eval_questions.json")
REPORT_DEFAULT = os.path.join(REPO_ROOT, "logs", "graph", "eval",
                              "m2_judge_report.json")

# ============================ rubric（存档） ============================
JUDGE_PROMPT = """你是严格的 RAG 问答质量评审。按以下 rubric 对【模型答案】逐维打分（每维 0-5 整数分）并各给一句理由。

rubric:
1. faithfulness 忠实度：答案是否只使用【检索上下文】中的信息。出现上下文中没有的事实/数值/名称（包括对脱敏掩码 * 的补全猜测）按程度扣分；完全忠实=5。
2. numeric_correctness 数值正确性：答案中的关键数值是否与【参考期望】一致（脱敏掩码 * 视为通配；千分位差异不扣分）。无期望值或答案无数值时：答案未编造数值=5，编造=0。
3. citation_quality 引用质量：答案是否明确指出出处（样本/表/字段），且与【来源列表】一致。具体且一致=5；无出处或与来源矛盾=0-2。豁免：若该题【预期不可回答】且答案明确拒答，则按拒答说明的清晰度评分（来源为空不扣分）。
4. refusal_appropriateness 拒绝恰当性：若该题【预期不可回答】，明确说明未找到/无法回答=5，编造答案=0；若该题可回答，正常作答=5，错误拒答=0。

只输出一个 JSON 对象，不要 markdown 围栏以外的内容：
{{"faithfulness": {{"score": 0, "reason": ""}}, "numeric_correctness": {{"score": 0, "reason": ""}}, "citation_quality": {{"score": 0, "reason": ""}}, "refusal_appropriateness": {{"score": 0, "reason": ""}}}}

[问题]
{question}

[检索上下文]（faithfulness 的唯一事实依据）
{context}

[模型答案]
{answer}

[来源列表]
{sources}

[参考期望]（仅 numeric_correctness 可用；忠实度判断禁止参考）
{expected}

[该题是否预期不可回答]
{unanswerable}
"""

DIMS = ("faithfulness", "numeric_correctness", "citation_quality",
        "refusal_appropriateness")

# rubric 预注册版本号 (K1 T3, v1 批复 ①): 版本元数据只进报告, 不改 prompt
# 文本; 任何 rubric 语义改动必须升版本并同步 docs/18 记录 + 重跑基线。
RUBRIC_VERSION = "v_k1"


def _extract_json(content: str) -> dict | None:
    if not content:
        return None
    s = content.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```\s*$", "", s)
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    a, b = s.find("{"), s.rfind("}")
    if a != -1 and b > a:
        try:
            obj = json.loads(s[a:b + 1])
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None
    return None


def _judge_once(question: str, context: str, answer: str, sources: str,
                expected: str, unanswerable: bool) -> dict:
    prompt = JUDGE_PROMPT.format(
        question=question, context=context[:6000], answer=answer[:1500],
        sources=sources[:1500], expected=expected or "（无）",
        unanswerable="是" if unanswerable else "否")
    payload = {
        "model": JUDGE_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 1024,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(
        JUDGE_ENDPOINT, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}",
                **{d: {"score": None, "reason": "judge call failed"} for d in DIMS}}
    obj = _extract_json(content)
    if not obj:
        return {"error": "judge output not JSON", "raw": content[:300],
                **{d: {"score": None, "reason": "unparsable"} for d in DIMS}}
    out = {}
    for d in DIMS:
        cell = obj.get(d) or {}
        score = cell.get("score")
        out[d] = {"score": int(score) if isinstance(score, (int, float))
                  and 0 <= score <= 5 else None,
                  "reason": str(cell.get("reason", ""))[:200]}
    return out


def judge_one(question: str, context: str, answer: str, sources: str,
              expected: str, unanswerable: bool, runs: int = 1) -> dict:
    """runs=1 与历史行为逐字节一致; runs>1 = K1 T2 ensemble 均值化打分。

    聚合口径: score = k 次有效分均值 (保留 2 位), std = 总体标准差,
    runs 留档每次原始分 (含 None), reason 取最接近均分那次的理由。
    全部失败时保持历史 error 形状 (score=None)。
    """
    if runs <= 1:
        return _judge_once(question, context, answer, sources,
                           expected, unanswerable)
    collected = []
    for _ in range(runs):
        collected.append(_judge_once(question, context, answer, sources,
                                     expected, unanswerable))
    n_unusable = sum(1 for c in collected if c.get("error"))
    out = {}
    for d in DIMS:
        pairs = [(c[d].get("score"), c[d].get("reason", ""))
                 for c in collected if c[d].get("score") is not None]
        if not pairs:
            out[d] = {"score": None, "reason": "all runs unusable",
                      "runs": [c[d].get("score") for c in collected],
                      "std": None, "n_unusable": n_unusable}
            continue
        vals = [p[0] for p in pairs]
        mean = sum(vals) / len(vals)
        std = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5
        nearest = min(pairs, key=lambda p: abs(p[0] - mean))
        out[d] = {"score": round(mean, 2), "std": round(std, 3),
                  "runs": [c[d].get("score") for c in collected],
                  "reason": str(nearest[1])[:200],
                  "n_unusable": n_unusable}
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True,
                    help="m2_eval_deterministic.py 的 report JSON")
    ap.add_argument("--fixture", default=FIXTURE)
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--report", default=REPORT_DEFAULT)
    ap.add_argument("--only", default="")
    ap.add_argument("--runs", type=int, default=1,
                    help="K1 T2: 每题重复打分次数, >1 时取均值+方差 "
                         "(默认 1 = 历史行为零漂移)")
    args = ap.parse_args(argv)

    import m1_rag_ingest as ing
    rag = ing.RAGService(collection_name=ing.COLLECTION)
    if ing.COLLECTION not in rag.get_collection_names():
        print(f"[fatal] collection {ing.COLLECTION} 不存在", file=sys.stderr)
        return 2
    try:
        urllib.request.urlopen(JUDGE_ENDPOINT.replace("/chat/completions", "/health"),
                               timeout=5).close()
    except Exception:
        try:  # vLLM 只在根路径挂 /health (/v1/health 为 404), 回退一次
            base = JUDGE_ENDPOINT.split("/v1/")[0]
            urllib.request.urlopen(base + "/health", timeout=5).close()
        except Exception as e:
            print(f"[fatal] judge 端点不可用 {JUDGE_ENDPOINT}: {e}", file=sys.stderr)
            return 2

    det = json.load(open(args.input, encoding="utf-8"))
    fx = json.load(open(args.fixture, encoding="utf-8"))
    fx_by_id = {q["id"]: q for q in fx["questions"]}
    results = det.get("results", [])
    if args.only:
        wanted = set(args.only.split(","))
        results = [r for r in results if r["id"] in wanted]

    judged = []
    for r in results:
        q = r["turns"][-1]
        # 多轮追问: 裸追问缺实体上下文, 检索用全部 turns 拼接 (模拟生产
        # conversation-aware retrieval 的改写结果), 否则 judge 拿到的上下文
        # 与答案脱节, faithfulness 误判 (2026-08-09 定标发现)。
        q_retrieve = " ".join(r["turns"]) if len(r["turns"]) > 1 else q
        try:
            docs = rag.smart_retrieve(query=q_retrieve, top_k=args.top_k,
                                      collection_names=[ing.COLLECTION],
                                      max_results=args.top_k, use_rerank=False)
        except Exception as e:
            docs = []
            print(f"[warn] retrieve failed for {r['id']}: {e}", file=sys.stderr)
        context = "\n".join((d.get("content", "") or "")[:600] for d in docs)
        sources = json.dumps(r.get("sources", [])[:5], ensure_ascii=False)
        fxq = fx_by_id.get(r["id"], {})
        expects = [c.get("expect", "") for c in fxq.get("checks", [])
                   if c["type"] in ("exact_numeric", "contains_keyword")]
        unanswerable = any(c["type"] == "refusal_expected"
                           for c in fxq.get("checks", []))
        scores = judge_one(q, context, r["answers"][-1], sources,
                           " ; ".join(e for e in expects if e), unanswerable,
                           runs=args.runs)
        unusable = [d for d in DIMS if scores[d]["score"] is None]
        if unusable:
            print(f'  [unusable] {r["id"]} dims={unusable} '
                  f'(runs={args.runs})', file=sys.stderr)
        judged.append({"id": r["id"], "route": r.get("route"),
                       "scores": scores})
        line = " ".join(
            f"{d[:4]}={scores[d]['score']}" for d in DIMS)
        print(f'{r["id"]:28s} {line}')

    valid = [j for j in judged if all(j["scores"][d]["score"] is not None for d in DIMS)]
    summary = {}
    for d in DIMS:
        vals = [j["scores"][d]["score"] for j in valid]
        summary[d] = {"avg": round(sum(vals) / len(vals), 2) if vals else None,
                      "n": len(vals)}
    print("\n[judge] 维度均分:", json.dumps(summary, ensure_ascii=False))
    low = [(j["id"], d, j["scores"][d]) for j in judged for d in DIMS
           if j["scores"][d]["score"] is not None and j["scores"][d]["score"] <= 2]
    for qid, d, cell in low:
        print(f"  [low] {qid} {d}={cell['score']}: {cell['reason'][:100]}")

    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as fh:
        json.dump({"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "judge_model": JUDGE_MODEL, "judge_endpoint": JUDGE_ENDPOINT,
                   "rubric_version": RUBRIC_VERSION, "judge_runs": args.runs,
                   "n_unusable": sum(
                       1 for j in judged
                       if any(j["scores"][d]["score"] is None for d in DIMS)),
                   "summary": summary, "results": judged},
                  fh, ensure_ascii=False, indent=2)
    print(f"[report] {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
