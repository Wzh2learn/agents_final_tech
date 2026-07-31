#!/usr/bin/env python3
"""M1+M2 端到端性能基准测试。

目标（Loop A 任务）：
- 对 ~/wzh/m1_samples/ 下 5 个甲方对账单样本，分别计时
  M1 解析（POST /api/m1/parse-file）与 M2 问答（POST /api/m2/ask），
  每样本跑 N 次取中位数，输出 markdown 表格。
- 记录 sample / parse_ms / qa_ms / total_ms / ocr_used / table_count。
- 可选 --breakdown：直接 import biz.m2_service，把 M2 QA 拆成
  retrieve(嵌入+PGVector 检索) 与 generate(:8004 LLM 生成) 两段，
  用于定位瓶颈。纯只读测量，不改任何 src/ 代码。

用法:
    ./venv/bin/python scripts/m1_benchmark.py                 # 5 样本 x 3 次
    ./venv/bin/python scripts/m1_benchmark.py --runs 1        # 快速冒烟
    ./venv/bin/python scripts/m1_benchmark.py --samples sample_fuxi_hunhe25_20231101.txt
    ./venv/bin/python scripts/m1_benchmark.py --breakdown     # 追加 QA 分段计时
    ./venv/bin/python scripts/m1_benchmark.py --json-out /tmp/bench.json

约束：不修改 tests/ / 样本 / 冻结文件；默认不改 src/ 代码。
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from typing import Any

import requests

BASE = os.environ.get("M1_BENCH_BASE", "http://127.0.0.1:5050")
SAMPLES_DIR = os.environ.get(
    "M1_BENCH_SAMPLES", os.path.expanduser("~/wzh/m1_samples"))
SAMPLE_EXTS = (".txt", ".pdf", ".xlsx", ".docx")

# 每个样本配一个“相关问题”（取自 scripts/m1_rag_qa.py 的查询集）。
# xinhua 为运营文档（0/11 schema 命中，可能未入库），用一个通用问题，
# 计时不以正确性为目标，miss 也照样走完检索/生成路径。
SAMPLE_QUESTIONS: dict[str, str] = {
    "sample_fuxi_hunhe25_20231101.txt": "复熙混合25号的资产总值是多少？",
    "sample_jiaxing_minan_20231031.pdf": "嘉兴样本的总资产是多少？",
    "sample_boshi_chuantong.pdf": "博时传统产品的基金名称是什么？",
    "sample_20260506_233222LU.pdf": "哪个样本通过OCR解析了交易对账单？",
    "sample_xinhua.docx": "新华样本涉及哪些产品或内容？",
}
DEFAULT_QUESTION = "哪个样本的总资产最高？"


def list_samples(only: list[str] | None = None) -> list[str]:
    """返回 sample_* 的 5 个对账单文件名（排除 mapping_*/ui_* 参考件）。"""
    names: list[str] = []
    for name in sorted(os.listdir(SAMPLES_DIR)):
        if not name.startswith("sample_"):
            continue
        if os.path.splitext(name)[1].lower() not in SAMPLE_EXTS:
            continue
        if only and not any(tag in name for tag in only):
            continue
        names.append(name)
    return names


def time_parse(path: str) -> dict[str, Any]:
    """计时一次 M1 解析。返回 wall/server 时延 + 元数据。"""
    url = f"{BASE}/api/m1/parse-file"
    with open(path, "rb") as fh:
        files = {"file": (os.path.basename(path), fh, "application/octet-stream")}
        t0 = time.perf_counter()
        try:
            resp = requests.post(url, files=files, timeout=900)
            wall_ms = int((time.perf_counter() - t0) * 1000)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # noqa: BLE001 - 记录失败但不中断基准
            wall_ms = int((time.perf_counter() - t0) * 1000)
            return {"wall_ms": wall_ms, "server_ms": 0, "ocr_used": False,
                    "ocr_engine": "", "table_count": 0, "llm_used": False,
                    "status": "error", "error": f"{type(exc).__name__}: {exc}"}
    result = data.get("result", {}) if isinstance(data, dict) else {}
    return {
        "wall_ms": wall_ms,
        "server_ms": int(result.get("parse_duration_ms", 0) or 0),
        "ocr_used": bool(result.get("ocr_used", False)),
        "ocr_engine": result.get("ocr_engine", "") or "",
        "table_count": int(result.get("table_count", 0) or 0),
        "llm_used": bool(result.get("llm_used", False)),
        "status": data.get("status", ""),
    }


def time_qa(question: str) -> dict[str, Any]:
    """计时一次 M2 问答。返回 wall/server 时延 + 命中数。"""
    url = f"{BASE}/api/m2/ask"
    t0 = time.perf_counter()
    try:
        resp = requests.post(url, json={"question": question, "top_k": 3},
                             timeout=300)
        wall_ms = int((time.perf_counter() - t0) * 1000)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        wall_ms = int((time.perf_counter() - t0) * 1000)
        return {"wall_ms": wall_ms, "server_ms": 0, "n_sources": 0,
                "status": "error", "error": f"{type(exc).__name__}: {exc}"}
    return {
        "wall_ms": wall_ms,
        "server_ms": int(data.get("duration_ms", 0) or 0),
        "n_sources": len(data.get("sources", []) or []),
        "status": "ok",
    }


def warmup(sample_names: list[str]) -> None:
    """预热：触发解析模块懒加载 + 嵌入模型/LLM 路径，避免污染首个样本计时。"""
    fast = next((n for n in sample_names if n.endswith(".txt")), sample_names[0])
    print(f"[warmup] parse {fast} ...", flush=True)
    time_parse(os.path.join(SAMPLES_DIR, fast))
    print("[warmup] qa ...", flush=True)
    time_qa(DEFAULT_QUESTION)
    print("[warmup] done", flush=True)


def median(vals: list[int]) -> int:
    return int(statistics.median(vals)) if vals else 0


def run_benchmark(sample_names: list[str], runs: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in sample_names:
        path = os.path.join(SAMPLES_DIR, name)
        question = SAMPLE_QUESTIONS.get(name, DEFAULT_QUESTION)
        parse_runs: list[dict[str, Any]] = []
        qa_runs: list[dict[str, Any]] = []
        for r in range(1, runs + 1):
            print(f"[bench] {name} run {r}/{runs} parse ...", flush=True)
            p = time_parse(path)
            parse_runs.append(p)
            print(f"[bench] {name} run {r}/{runs} qa ...", flush=True)
            q = time_qa(question)
            qa_runs.append(q)
            print(f"        parse={p['wall_ms']}ms ocr={p['ocr_used']} "
                  f"tables={p['table_count']} | qa={q['wall_ms']}ms "
                  f"src={q['n_sources']}", flush=True)
        parse_ms = [p["wall_ms"] for p in parse_runs]
        qa_ms = [q["wall_ms"] for q in qa_runs]
        totals = [p["wall_ms"] + q["wall_ms"]
                  for p, q in zip(parse_runs, qa_runs)]
        last = parse_runs[-1]
        rows.append({
            "sample": name,
            "kind": os.path.splitext(name)[1].lower().lstrip("."),
            "question": question,
            "ocr_used": last["ocr_used"],
            "ocr_engine": last["ocr_engine"],
            "table_count": last["table_count"],
            "llm_used": last["llm_used"],
            "parse_ms_med": median(parse_ms),
            "parse_ms_min": min(parse_ms),
            "parse_ms_max": max(parse_ms),
            "parse_server_ms_med": median(
                [p["server_ms"] for p in parse_runs]),
            "qa_ms_med": median(qa_ms),
            "qa_ms_min": min(qa_ms),
            "qa_ms_max": max(qa_ms),
            "qa_server_ms_med": median(
                [q["server_ms"] for q in qa_runs]),
            "total_ms_med": median(totals),
            "parse_runs": parse_ms,
            "qa_runs": qa_ms,
            "parse_status": last["status"],
        })
    return rows


def run_breakdown(question: str) -> dict[str, Any]:
    """把 M2 QA 拆成 retrieve(嵌入+PGVector) 与 generate(:8004) 两段计时。

    直接 import biz.m2_service（只读）。会在本进程加载本地嵌入模型，
    与 :5050 服务进程相互独立。仅用于瓶颈定位，跑 3 次取中位数。
    """
    proj = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    for sub in ("src", "scripts"):
        p = os.path.join(proj, sub)
        if p not in sys.path:
            sys.path.insert(0, p)
    from biz import m2_service  # noqa: E402

    # 预热一次（加载嵌入模型 + 编译），避免首次冷启动计入
    m2_service.retrieve(question, top_k=3)

    ret_ms: list[int] = []
    gen_ms: list[int] = []
    n_src = 0
    for _ in range(3):
        t0 = time.perf_counter()
        sources = m2_service.retrieve(question, top_k=3)
        ret_ms.append(int((time.perf_counter() - t0) * 1000))
        n_src = len(sources)
        prompt = m2_service._build_prompt(question, sources)
        t0 = time.perf_counter()
        m2_service._generate(prompt)
        gen_ms.append(int((time.perf_counter() - t0) * 1000))
    return {
        "question": question,
        "n_sources": n_src,
        "retrieve_ms_med": median(ret_ms),
        "retrieve_ms_runs": ret_ms,
        "generate_ms_med": median(gen_ms),
        "generate_ms_runs": gen_ms,
        "total_ms_med": median(ret_ms) + median(gen_ms),
    }


def render_markdown(rows: list[dict[str, Any]], runs: int,
                    breakdown: dict[str, Any] | None) -> str:
    lines: list[str] = []
    lines.append("| 样本 | 类型 | OCR | 表数 | parse_ms | qa_ms | total_ms |")
    lines.append("|------|------|-----|------|----------|-------|----------|")
    for r in rows:
        ocr = "✓" if r["ocr_used"] else "—"
        lines.append(
            f"| {r['sample']} | {r['kind']} | {ocr} | {r['table_count']} "
            f"| {r['parse_ms_med']} | {r['qa_ms_med']} | {r['total_ms_med']} |")
    lines.append("")
    lines.append(f"> 每样本 {runs} 次取中位数（wall-clock, localhost 回环）。")
    lines.append("")
    lines.append("### 每样本明细 (min/med/max, ms)")
    lines.append("")
    lines.append("| 样本 | parse min/med/max | qa min/med/max | ocr_engine |")
    lines.append("|------|-------------------|----------------|------------|")
    for r in rows:
        lines.append(
            f"| {r['sample']} "
            f"| {r['parse_ms_min']}/{r['parse_ms_med']}/{r['parse_ms_max']} "
            f"| {r['qa_ms_min']}/{r['qa_ms_med']}/{r['qa_ms_max']} "
            f"| {r['ocr_engine'] or '—'} |")
    if breakdown:
        lines.append("")
        lines.append("### M2 QA 分段计时（瓶颈定位）")
        lines.append("")
        lines.append("| 阶段 | 中位 ms | 说明 |")
        lines.append("|------|---------|------|")
        lines.append(
            f"| retrieve (嵌入+PGVector) | {breakdown['retrieve_ms_med']} "
            f"| 本地 Qwen3-Embedding-0.6B + 向量/BM25 混合检索 |")
        lines.append(
            f"| generate (:8004 LLM) | {breakdown['generate_ms_med']} "
            f"| Qwen3.6-35B-A3B 答案生成 (max_tokens=512) |")
        lines.append(
            f"| 合计 | {breakdown['total_ms_med']} | retrieve + generate |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="M1+M2 E2E benchmark")
    ap.add_argument("--runs", type=int, default=3, help="每样本重复次数")
    ap.add_argument("--samples", type=str, default="",
                    help="逗号分隔的样本名子串过滤")
    ap.add_argument("--no-warmup", action="store_true")
    ap.add_argument("--breakdown", action="store_true",
                    help="追加 M2 QA retrieve/generate 分段计时")
    ap.add_argument("--json-out", type=str, default="")
    args = ap.parse_args()

    only = [s for s in args.samples.split(",") if s] or None
    sample_names = list_samples(only)
    if not sample_names:
        print("[bench] ERROR no samples found in", SAMPLES_DIR)
        return 2
    print(f"[bench] base={BASE} samples={len(sample_names)} runs={args.runs}")
    for n in sample_names:
        print("   -", n)

    if not args.no_warmup:
        warmup(sample_names)

    rows = run_benchmark(sample_names, args.runs)

    breakdown = None
    if args.breakdown:
        q = SAMPLE_QUESTIONS.get(sample_names[0], DEFAULT_QUESTION)
        print(f"[breakdown] question={q}")
        breakdown = run_breakdown(q)
        print(f"[breakdown] retrieve={breakdown['retrieve_ms_med']}ms "
              f"generate={breakdown['generate_ms_med']}ms")

    md = render_markdown(rows, args.runs, breakdown)
    print("\n" + md)

    if args.json_out:
        payload = {"base": BASE, "runs": args.runs, "rows": rows,
                   "breakdown": breakdown}
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        print(f"\n[bench] json -> {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
