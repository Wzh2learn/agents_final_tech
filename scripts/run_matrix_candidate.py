#!/usr/bin/env python3
"""(K4 矩阵执行器, 批复 ②) 候选模型固定题库跑分 runner。

同一把尺子（K2 协议固定题库 tests/fixtures/m2_eval_questions.json, 冻结只读）
在不同候选模型上跑: 检索走生产同口径 (RAGService.smart_retrieve, 与
m2_eval_judge.py 同路径), 回答者换候选端点 (/v1/chat/completions),
确定性 check 复用 m2_eval_deterministic 的函数（同一判分逻辑）。

报告 schema 与 m2_deterministic_report.json 同构 (results/overall/n_pass),
可直接喂 m2_eval_judge.py (--input) 与 K2 检查点聚合。

用法:
  python scripts/run_matrix_candidate.py \
      --endpoint http://127.0.0.1:8007/v1/chat/completions \
      --model Qwen3-14B-Q4_K_M.gguf \
      --label c1_qwen3_14b_think_off \
      --thinking off
退出码: 0=跑完(分数不判失败) 2=端点/集合不可用
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from m2_eval_deterministic import run_checks  # noqa: E402

FIXTURE = os.path.join(REPO_ROOT, "tests", "fixtures", "m2_eval_questions.json")
EVAL_DIR = os.path.join(REPO_ROOT, "logs", "graph", "eval", "matrix")

SYSTEM_PROMPT = (
    "你是金融对账单问答助手。只根据【检索上下文】回答问题；"
    "回答需指明出处（样本/表/字段）。"
    "若上下文中没有答案，明确回答：未找到相关数据。不得编造。")


def _retrieve(rag, query: str, top_k: int) -> list[dict]:
    import m1_rag_ingest as ing
    try:
        return rag.smart_retrieve(query=query, top_k=top_k,
                                  collection_names=[ing.COLLECTION],
                                  max_results=top_k, use_rerank=False)
    except Exception as e:
        print(f"[warn] retrieve failed: {e}", file=sys.stderr)
        return []


def _sources_of(docs: list[dict]) -> list[dict]:
    out = []
    for d in docs:
        meta = d.get("metadata") or {}
        src = (meta.get("source") or d.get("source") or "")
        out.append({"doc": os.path.basename(str(src)),
                    "snippet": (d.get("content") or "")[:120]})
    return out


def ask_candidate(endpoint: str, model: str, question: str,
                  context: str, thinking: str, timeout: int) -> dict:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",
             "content": f"【检索上下文】\n{context[:6000]}\n\n"
                        f"【问题】\n{question}"}],
        "temperature": 0,
        "max_tokens": 1024,
    }
    if thinking in ("off", "low", "medium", "xhigh"):
        payload["chat_template_kwargs"] = {
            "enable_thinking": thinking != "off"}
        if thinking != "off":
            payload["reasoning_effort"] = thinking
    req = urllib.request.Request(
        endpoint, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    wall = round((time.monotonic() - t0) * 1000)
    msg = body["choices"][0]["message"]
    usage = body.get("usage", {})
    return {"answer": msg.get("content", ""),
            "reasoning": msg.get("reasoning") or msg.get("reasoning_content"),
            "wall_ms": wall,
            "completion_tokens": usage.get("completion_tokens"),
            "prompt_tokens": usage.get("prompt_tokens")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--endpoint", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", required=True,
                    help="候选标签, 如 c1_qwen3_14b_think_off")
    ap.add_argument("--thinking", default="off",
                    choices=["off", "low", "medium", "xhigh"])
    ap.add_argument("--fixture", default=FIXTURE)
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    # 端点健康
    try:
        base = args.endpoint.split("/v1/")[0]
        urllib.request.urlopen(base + "/health", timeout=5).close()
    except Exception:
        try:
            urllib.request.urlopen(
                args.endpoint.replace("/chat/completions", "/models"),
                timeout=5).close()
        except Exception as e:
            print(f"[fatal] 候选端点不可用 {args.endpoint}: {e}",
                  file=sys.stderr)
            return 2

    import m1_rag_ingest as ing
    rag = ing.RAGService(collection_name=ing.COLLECTION)
    if ing.COLLECTION not in rag.get_collection_names():
        print(f"[fatal] collection {ing.COLLECTION} 不存在", file=sys.stderr)
        return 2

    fx = json.load(open(args.fixture, encoding="utf-8"))
    questions = fx["questions"]
    if args.only:
        wanted = set(args.only.split(","))
        questions = [q for q in questions if q["id"] in wanted]

    results = []
    for q in questions:
        turns = q.get("turns") or [q["question"]]
        history = ""
        answers, walls, toks = [], [], 0
        sources = []
        for turn in turns:
            q_ret = f"{history} {turn}".strip()
            docs = _retrieve(rag, q_ret, args.top_k)
            context = "\n".join((d.get("content", "") or "")[:600]
                                for d in docs)
            sources = _sources_of(docs)
            try:
                r = ask_candidate(args.endpoint, args.model, turn, context,
                                  args.thinking, args.timeout)
            except Exception as e:
                r = {"answer": f"[candidate error] {type(e).__name__}: {e}",
                     "reasoning": None, "wall_ms": None,
                     "completion_tokens": None, "prompt_tokens": None}
            answers.append(r["answer"])
            walls.append(r["wall_ms"])
            if r.get("completion_tokens"):
                toks += r["completion_tokens"]
            history = f"{history} 问:{turn} 答:{r['answer'][:200]}"
        final = answers[-1]
        resp = {"sources": sources, "route": f"matrix:{args.label}"}
        checks = run_checks(q.get("checks", []), final, resp)
        row = {
            "id": q["id"], "category": q.get("category", ""),
            "turns": turns, "answers": answers, "checks": checks,
            "all_pass": all(c["pass"] for c in checks),
            "route": resp["route"], "model": args.model,
            "duration_ms": walls[-1], "sources": sources,
            "completion_tokens": toks,
        }
        results.append(row)
        mark = "PASS" if row["all_pass"] else "FAIL"
        print(f'{q["id"]:28s} {mark}  {walls[-1]}ms')

    n_pass = sum(1 for r in results if r["all_pass"])
    payload = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "overall": "PASS" if n_pass == len(results) else "FAIL",
        "n_questions": len(results), "n_pass": n_pass,
        "meta": {"candidate": args.label, "endpoint": args.endpoint,
                 "model": args.model, "thinking": args.thinking,
                 "top_k": args.top_k, "fixture": args.fixture,
                 "caliber": "K4 矩阵: 生产同口径检索 + 候选回答者 + 同判分"},
        "results": results,
    }
    os.makedirs(EVAL_DIR, exist_ok=True)
    out = args.out or os.path.join(EVAL_DIR, f"{args.label}_report.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
    print(f"\n[matrix] {args.label}: {n_pass}/{len(results)} PASS -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
