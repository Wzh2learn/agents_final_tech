#!/usr/bin/env python3
"""M2 端到端确定性检验层 (P2.1 沉淀, 2026-08-09)。

对 /api/m2/ask 做结构化判分（不再人肉比对）：
- exact_numeric    数值精确匹配（千分位/单位容差, * 通配脱敏位）
- contains_keyword 答案包含关键词
- source_required  sources 非空且 sample_id/table 含指定片段
- refusal_expected 无答案题必须明确拒答（不得编造）

问题集: tests/fixtures/m2_eval_questions.json
输出:   机器可读 eval_report.json（每题: 逐项 check pass/fail + 证据 +
        延迟 + route 直连/agent）

用法:
  python scripts/m2_eval_deterministic.py                 # 跑全集
  python scripts/m2_eval_deterministic.py --calibrate     # 只打印答案供定标
  python scripts/m2_eval_deterministic.py --report PATH
退出码: 0=全过 1=有 check 失败 2=服务不可用
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import sys
import time
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(REPO_ROOT, "tests", "fixtures", "m2_eval_questions.json")
REPORT_DEFAULT = os.path.join(REPO_ROOT, "logs", "graph", "eval",
                              "m2_deterministic_report.json")
REFUSAL_MARKERS = ("未找到", "无法", "没有相关", "没有收录", "未收录", "不包含",
                   "没有足够", "无法回答", "没有该", "不存在", "没有关于")


def ask(endpoint: str, question: str, session_id: str | None,
        top_k: int = 5, timeout: int = 120) -> dict:
    body = {"question": question, "top_k": top_k}
    if session_id:
        body["session_id"] = session_id
    req = urllib.request.Request(
        endpoint, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    data["_wall_ms"] = round((time.monotonic() - t0) * 1000)
    return data


def _norm_number(s: str) -> str:
    """去千分位/单位/空白, 保留数字 . * 与小数。"""
    s = re.sub(r"[,，\s元¥人民币]", "", str(s))
    return s


def check_exact_numeric(answer: str, expect: str) -> tuple[bool, str]:
    """答案中提取所有数值片段, 与期望(可含*通配)做规范化匹配。"""
    want = _norm_number(expect)
    nums = re.findall(r"-?[\d*,，.]+", answer)
    for n in nums:
        cand = _norm_number(n)
        if cand and (fnmatch.fnmatch(cand, want) or fnmatch.fnmatch(want, cand)):
            return True, f"matched {n!r}"
    return False, f"want {expect!r}, nums in answer: {nums[:8]}"


def check_contains(answer: str, kw: str) -> tuple[bool, str]:
    return (kw in answer), f"keyword {kw!r}"


def check_sources(resp: dict, frag: str) -> tuple[bool, str]:
    srcs = resp.get("sources") or []
    if not srcs:
        return False, "sources empty"
    hay = json.dumps(srcs, ensure_ascii=False)
    return (frag in hay), f"{len(srcs)} sources, frag {frag!r}"


def check_refusal(answer: str) -> tuple[bool, str]:
    if any(m in answer for m in REFUSAL_MARKERS):
        return True, "refusal marker found"
    return False, f"no refusal marker; answer head: {answer[:80]!r}"


def run_checks(checks: list[dict], answer: str, resp: dict) -> list[dict]:
    out = []
    for c in checks:
        t = c["type"]
        if t == "exact_numeric":
            ok, ev = check_exact_numeric(answer, c["expect"])
        elif t == "contains_keyword":
            ok, ev = check_contains(answer, c["expect"])
        elif t == "source_required":
            ok, ev = check_sources(resp, c.get("sample_id_contains", ""))
        elif t == "refusal_expected":
            ok, ev = check_refusal(answer)
        else:
            ok, ev = False, f"unknown check type {t}"
        out.append({"type": t, "expect": c.get("expect", c.get("sample_id_contains", "")),
                    "pass": ok, "evidence": ev})
    return out


def run_question(endpoint: str, q: dict, session_id: str | None,
                 timeout: int = 120) -> dict:
    turns = q.get("turns") or [q["question"]]
    sid = session_id
    resp = {}
    answers = []
    for turn in turns:
        resp = ask(endpoint, turn, sid, timeout=timeout)
        sid = resp.get("session_id", sid)
        answers.append(resp.get("answer", ""))
    final_answer = answers[-1]
    checks = run_checks(q.get("checks", []), final_answer, resp)
    return {
        "id": q["id"],
        "category": q.get("category", ""),
        "turns": turns,
        "answers": answers,
        "checks": checks,
        "all_pass": all(c["pass"] for c in checks),
        "route": resp.get("route", "direct"),
        "model": resp.get("model", ""),
        "duration_ms": resp.get("duration_ms", resp.get("_wall_ms")),
        "session_id": sid,
        "sources": resp.get("sources", []),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fixture", default=FIXTURE)
    ap.add_argument("--endpoint", default=None,
                    help="默认取 fixture 内 endpoint")
    ap.add_argument("--report", default=REPORT_DEFAULT)
    ap.add_argument("--calibrate", action="store_true",
                    help="只跑并打印答案, 不判分 (定标用)")
    ap.add_argument("--only", default="", help="只跑指定 id (逗号分隔)")
    ap.add_argument("--timeout", type=int, default=120,
                    help="每题 HTTP 超时秒数 (默认 120; Loop B canary 用 45)")
    args = ap.parse_args(argv)

    with open(args.fixture, encoding="utf-8") as fh:
        fx = json.load(fh)
    endpoint = args.endpoint or fx.get("endpoint", "http://127.0.0.1:5050/api/m2/ask")
    questions = fx["questions"]
    if args.only:
        wanted = set(args.only.split(","))
        questions = [q for q in questions if q["id"] in wanted]

    try:
        base = endpoint.split("/api/")[0]
        probe = urllib.request.urlopen(base + "/health", timeout=5)
        probe.close()
    except Exception as e:
        print(f"[fatal] 服务不可用: {e}", file=sys.stderr)
        return 2

    results = []
    for q in questions:
        r = run_question(endpoint, q, None, timeout=args.timeout)
        results.append(r)
        if args.calibrate:
            print(f"--- {q['id']} ({r['route']}, {r['duration_ms']}ms)")
            for a in r["answers"]:
                print("A:", a[:400].replace("\n", " "))
            print("sources:", json.dumps(r["sources"][:2], ensure_ascii=False)[:300])
        else:
            mark = "PASS" if r["all_pass"] else "FAIL"
            print(f'{q["id"]:28s} {mark:4s} {r["route"]:8s} '
                  f'{r["duration_ms"]}ms '
                  f'{sum(c["pass"] for c in r["checks"])}/{len(r["checks"])}')

    if args.calibrate:
        return 0

    n_pass = sum(1 for r in results if r["all_pass"])
    overall = "PASS" if n_pass == len(results) else "FAIL"
    print(f"\n[m2-eval] {overall}: {n_pass}/{len(results)} 题全过")

    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    report = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
              "endpoint": endpoint, "overall": overall,
              "n_questions": len(results), "n_pass": n_pass,
              "results": results}
    with open(args.report, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(f"[report] {args.report}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
