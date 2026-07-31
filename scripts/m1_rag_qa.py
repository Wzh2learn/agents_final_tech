#!/usr/bin/env python3
"""M2 RAG QA 质量扩展：基于 M1 解析结果入库内容的检索问答评测。

定位（遵守仓库架构边界）：
- 只读评测脚本。不另建向量库、不绕过 RAGService；检索一律走
  RAGService.smart_retrieve（向量 + BM25 混合），集合 m1_parsed_statements。
- 入库由 scripts/m1_rag_ingest.py 负责；本脚本直接 import 它复用环境变量、
  COLLECTION 常量与 RAGService，避免重复配置。
- 入库 chunk 已脱敏（值打码，字段名/表名保留），因此评测目标是**检索相关性**
  （top-k 是否命中“正确样本 + 正确字段/表”），而非还原原始数值。

查询集设计（15 条）：
- 13 条 answerable：覆盖跨表汇总、KV 字段、持仓明细、OCR 样本等金融场景，
  期望命中（expect=hit）。
- 2 条 gap：勾稽结论 / 解析速度等“解析元数据”当前未入库，期望 MISS
  （expect=miss）。MISS 是正确行为，用于记录 RAG 覆盖盲区（同 xinhua 先例）。

用法:
    ./venv/bin/python scripts/m1_rag_qa.py            # top_k=5
    ./venv/bin/python scripts/m1_rag_qa.py --top-k 8
退出码:
    0 = answerable 准确率 >= 80%
    1 = answerable 准确率 < 80%
    2 = 集合不存在（需先跑 m1_rag_ingest.py ingest）
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

# 复用入库脚本的环境变量设置、COLLECTION 与 RAGService（不重复配置、不另建库）
import m1_rag_ingest as ing  # noqa: E402

RAGService = ing.RAGService
COLLECTION = ing.COLLECTION


# 每条查询: query / want_sample(样本前缀, None=任意) / want_key(内容关键词)
#           expect(hit|miss) / category(场景分类)
QA_QUERIES: list[dict[str, Any]] = [
    # --- 原始 3 条（保持连续性）---
    {"query": "复熙混合25号的资产总值是多少？", "want_sample": "sample_fuxi_hunhe25",
     "want_key": "资产总值", "expect": "hit", "category": "资金资产汇总"},
    {"query": "嘉兴民安有哪些证券持仓？", "want_sample": "sample_jiaxing_minan",
     "want_key": "证券持仓", "expect": "hit", "category": "证券持仓明细"},
    {"query": "博时传统产品的基金名称是什么？", "want_sample": "sample_boshi_chuantong",
     "want_key": "基金名称", "expect": "hit", "category": "表头KV"},
    # --- 跨表 / 汇总字段查询 ---
    {"query": "嘉兴样本的总资产是多少？", "want_sample": "sample_jiaxing_minan",
     "want_key": "总资产", "expect": "hit", "category": "跨表汇总"},
    {"query": "复熙混合25号的证券市值是多少？", "want_sample": "sample_fuxi_hunhe25",
     "want_key": "证券市值", "expect": "hit", "category": "跨表汇总"},
    {"query": "嘉兴民安的资金余额是多少？", "want_sample": "sample_jiaxing_minan",
     "want_key": "资金余额", "expect": "hit", "category": "资金资产汇总"},
    # --- KV 字段查询 ---
    {"query": "博时传统产品的基金代码是什么？", "want_sample": "sample_boshi_chuantong",
     "want_key": "基金代码", "expect": "hit", "category": "表头KV"},
    {"query": "复熙混合25号的客户全称是什么？", "want_sample": "sample_fuxi_hunhe25",
     "want_key": "客户全称", "expect": "hit", "category": "表头KV"},
    {"query": "嘉兴民安的对账结束日期是什么时候？", "want_sample": "sample_jiaxing_minan",
     "want_key": "结束日期", "expect": "hit", "category": "表头KV"},
    {"query": "博时传统产品的基金资产总额是多少？", "want_sample": "sample_boshi_chuantong",
     "want_key": "基金资产总额", "expect": "hit", "category": "表头KV"},
    # --- 持仓明细查询 ---
    {"query": "复熙混合25号持有哪些证券名称？", "want_sample": "sample_fuxi_hunhe25",
     "want_key": "证券名称", "expect": "hit", "category": "证券持仓明细"},
    {"query": "嘉兴民安持仓的盈亏金额是多少？", "want_sample": "sample_jiaxing_minan",
     "want_key": "盈亏金额", "expect": "hit", "category": "证券持仓明细"},
    # --- OCR 样本查询（正向：OCR 样本确实入库且可检索）---
    {"query": "哪个样本通过OCR解析了交易对账单？", "want_sample": "sample_20260506",
     "want_key": "交易对账单", "expect": "hit", "category": "OCR样本"},
    # --- 覆盖盲区（解析元数据未入库，期望 MISS）---
    {"query": "哪个样本的勾稽校验全部通过？", "want_sample": None,
     "want_key": "勾稽", "expect": "miss", "category": "盲区:勾稽结论未入库"},
    {"query": "哪个样本的解析速度最快？", "want_sample": None,
     "want_key": "解析速度", "expect": "miss", "category": "盲区:解析耗时未入库"},
]


def _is_relevant(docs: list[dict[str, Any]], want_sample: str | None, want_key: str) -> bool:
    """top-k 中是否存在 (样本匹配) 且 (内容含关键词) 的 chunk。"""
    key = want_key.lower()
    for d in docs:
        sid = str(d.get("metadata", {}).get("sample_id", ""))
        content = (d.get("content", "") or "").lower()
        sample_ok = want_sample is None or want_sample in sid
        if sample_ok and key in content:
            return True
    return False


def run_qa(top_k: int) -> int:
    rag = RAGService(collection_name=COLLECTION)
    available = rag.get_collection_names()
    if COLLECTION not in available:
        print(f"[qa] ERROR collection {COLLECTION} not found; run m1_rag_ingest.py ingest first")
        print(f"[qa] available collections: {available}")
        return 2
    print(f"[qa] collection {COLLECTION} present | top_k={top_k} | queries={len(QA_QUERIES)}")

    results = []
    answerable_total = answerable_hit = 0
    correct_total = 0
    for spec in QA_QUERIES:
        query = spec["query"]
        try:
            docs = rag.smart_retrieve(
                query=query, top_k=top_k, collection_names=[COLLECTION],
                max_results=top_k, use_rerank=False,
            )
        except Exception as exc:  # 检索失败记为错误
            print(f"[qa] QUERY FAIL: {query!r} -> {type(exc).__name__}: {exc}")
            results.append({**spec, "relevant": False, "correct": False, "error": str(exc)})
            continue

        relevant = _is_relevant(docs, spec["want_sample"], spec["want_key"])
        expect_hit = spec["expect"] == "hit"
        correct = relevant == expect_hit
        correct_total += 1 if correct else 0
        if expect_hit:
            answerable_total += 1
            answerable_hit += 1 if relevant else 0

        top = [{
            "sample_id": str(d.get("metadata", {}).get("sample_id", "")),
            "table_name": d.get("metadata", {}).get("table_name", ""),
            "score": round(float(d.get("relevance_score") or 0.0), 4),
            "text": (d.get("content", "") or "").replace("\n", " ")[:120],
        } for d in docs[:3]]
        results.append({**spec, "relevant": relevant, "correct": correct, "top": top})

        mark = "OK " if correct else "BAD"
        kind = "hit" if expect_hit else "miss(expected)"
        print(f"[qa] {mark} [{spec['category']}] {query}")
        print(f"        relevant={relevant} want={kind} "
              f"(sample~{spec['want_sample']}, key~{spec['want_key']})")
        for r in top:
            print(f"        - [{r['sample_id']}|{r['table_name']}|{r['score']}] {r['text']}")

    answerable_acc = (answerable_hit / answerable_total) if answerable_total else 0.0
    overall_acc = correct_total / len(QA_QUERIES) if QA_QUERIES else 0.0
    gaps = [r["category"] for r in results if r["expect"] == "miss" and r["correct"]]

    print("\n[qa] ===== SUMMARY =====")
    print(f"[qa] answerable HIT: {answerable_hit}/{answerable_total} "
          f"= {answerable_acc:.0%}  (quality gate >=80%)")
    print(f"[qa] overall correct (expect-aware): {correct_total}/{len(QA_QUERIES)} = {overall_acc:.0%}")
    print(f"[qa] confirmed coverage gaps: {gaps}")
    print("[qa] json=" + json.dumps(results, ensure_ascii=False))

    return 0 if answerable_acc >= 0.8 else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="M2 RAG QA 质量扩展评测（15 查询）")
    ap.add_argument("--top-k", type=int, default=5)
    args = ap.parse_args(argv)
    return run_qa(args.top_k)


if __name__ == "__main__":
    sys.exit(main())
