#!/usr/bin/env python3
"""Qwen3.8-27B + vLLM 探针基准 (模型升级专项 P1/P2, 2026-08-15).

对候选 LLM 端点 (:8006 vLLM 探针) 做生产直连路等价基准:
复用 src/biz/m2_service.py 的检索/prompt 构造与
scripts/m2_eval_deterministic.py 的判分函数, 只替换生成端点,
不触碰 :5050 进程。

思考档位实测口径 (chat_template.jinja 实证):
  - enable_thinking 默认 true; false 时模板注入空 <think></think> -> 零推理
  - reasoning_effort 合法集: xhigh(默认) / medium / low (prompt 引导式, 非硬上限)
  - thinking_budget 不在模板中 -> 传入被忽略; "high" 非法 -> 400

模式 (--mode):
  thinking-probe   思考控制验证 (零推理/budget 忽略实证/effort 三档/非法档 400)
  matrix           三档思考 x 固定 10 题: p50/p95 延迟 + token 分布
  deterministic    全 16 题确定性检验 (thinking off, 生产等价口径),
                   输出 schema 与 m2_eval_judge.py --input 兼容
  concurrency      3 路并发直连路, 记录单请求与 makespan 延迟
  vision           图像转写冒烟, 可与 --compare-endpoint (旧栈 :8004) 对比

用法 (GB10):
  cd ~/wzh/projects/agents_final_tech
  ./venv/bin/python scripts/m2_model_probe_benchmark.py --mode thinking-probe \
      --endpoint http://127.0.0.1:8006/v1/chat/completions \
      --model qwen38-27b-fp8

输出: logs/graph/eval/model_probe_<mode>.json + 终端摘要。
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import json
import os
import statistics
import sys
import time
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

FIXTURE = os.path.join(REPO_ROOT, "tests", "fixtures", "m2_eval_questions.json")
EVAL_DIR = os.path.join(REPO_ROOT, "logs", "graph", "eval")
MATRIX_QUESTION_COUNT = 10

PROBE_PROMPT = "桌上有 3 个苹果, 又拿来 2 个, 现在一共有几个? 简要说明。"

# 三档思考配置 (模板实证口径; A=快路候选, B=轻思考, C=准路候选)
TIERS = {
    "A_off": {"chat_template_kwargs": {"enable_thinking": False}},
    "B_effort_low": {"chat_template_kwargs": {"enable_thinking": True,
                                               "reasoning_effort": "low"}},
    "C_effort_xhigh": {"chat_template_kwargs": {"enable_thinking": True,
                                                 "reasoning_effort": "xhigh"}},
}


def load_dotenv(path: str) -> None:
    """最小 .env 载入: 不覆盖已存在的环境变量。"""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def _post(endpoint: str, payload: dict, timeout: float) -> tuple[dict, int]:
    req = urllib.request.Request(
        endpoint, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body, int((time.monotonic() - t0) * 1000)


def generate(endpoint: str, model: str, messages: list, tier_kwargs: dict | None,
             max_tokens: int = 512, timeout: float = 300) -> dict:
    payload = {"model": model, "messages": messages,
               "temperature": 0, "max_tokens": max_tokens}
    if tier_kwargs:
        payload.update(tier_kwargs)
    try:
        body, wall_ms = _post(endpoint, payload, timeout)
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8")[:300]
        except Exception:
            pass
        return {"error": f"HTTP {exc.code}: {detail}",
                "wall_ms": int((time.monotonic()) * 0)}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}",
                "wall_ms": int(timeout * 1000)}
    choice = (body.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    usage = body.get("usage") or {}
    details = usage.get("completion_tokens_details") or {}
    return {
        "content": (msg.get("content") or "").strip(),
        "reasoning_content": (msg.get("reasoning_content") or msg.get("reasoning") or ""),
        "reasoning_tokens": details.get("reasoning_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "prompt_tokens": usage.get("prompt_tokens"),
        "wall_ms": wall_ms,
        "finish_reason": choice.get("finish_reason"),
    }


def _percentile(vals: list, pct: float) -> float | None:
    if not vals:
        return None
    vals = sorted(vals)
    k = (len(vals) - 1) * pct
    lo, hi = int(k), min(int(k) + 1, len(vals) - 1)
    return round(vals[lo] + (vals[hi] - vals[lo]) * (k - lo), 1)


def _summary_rows(rows: list[dict]) -> dict:
    walls = [r["wall_ms"] for r in rows if "error" not in r]
    rts = [r["reasoning_tokens"] for r in rows
           if r.get("reasoning_tokens") is not None]
    cts = [r["completion_tokens"] for r in rows
           if r.get("completion_tokens") is not None]
    return {
        "n": len(rows),
        "n_error": sum(1 for r in rows if "error" in r),
        "p50_ms": _percentile(walls, 0.5),
        "p95_ms": _percentile(walls, 0.95),
        "avg_ms": round(statistics.mean(walls), 1) if walls else None,
        "reasoning_tokens_avg": round(statistics.mean(rts), 1) if rts else None,
        "reasoning_tokens_max": max(rts) if rts else None,
        "completion_tokens_avg": round(statistics.mean(cts), 1) if cts else None,
    }


def save_report(mode: str, report: dict, path: str | None) -> str:
    os.makedirs(EVAL_DIR, exist_ok=True)
    out = path or os.path.join(EVAL_DIR, f"model_probe_{mode}.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    return out


# ---------------------------------------------------------------------------
# mode: thinking-probe
# ---------------------------------------------------------------------------
def mode_thinking_probe(args) -> dict:
    rows = []

    def probe(label: str, tier_kwargs: dict, max_tokens: int = 800) -> dict:
        r = generate(args.endpoint, args.model,
                     [{"role": "user", "content": PROBE_PROMPT}],
                     tier_kwargs, max_tokens=max_tokens, timeout=180)
        r["label"] = label
        rows.append(r)
        print(f'{label:32s} wall={r.get("wall_ms")}ms '
              f'reasoning_tokens={r.get("reasoning_tokens")} '
              f'rc_chars={len(r.get("reasoning_content") or "")} '
              f'completion={r.get("completion_tokens")} '
              f'err={str(r.get("error", ""))[:80]}')
        return r

    probe("1_enable_thinking_false", TIERS["A_off"], max_tokens=300)
    probe("2_budget512_expect_ignored",
          {"chat_template_kwargs": {"enable_thinking": True,
                                    "thinking_budget": 512}})
    probe("3a_effort_low", {"chat_template_kwargs": {
        "enable_thinking": True, "reasoning_effort": "low"}})
    probe("3b_effort_medium", {"chat_template_kwargs": {
        "enable_thinking": True, "reasoning_effort": "medium"}})
    probe("3c_effort_xhigh", TIERS["C_effort_xhigh"])
    probe("4_effort_high_expect_400", {"chat_template_kwargs": {
        "enable_thinking": True, "reasoning_effort": "high"}}, max_tokens=300)

    def _rt(r):
        if r.get("reasoning_tokens") is not None:
            return r["reasoning_tokens"]
        return len(r.get("reasoning_content") or "")  # fallback: 字符数

    r1, r2 = rows[0], rows[1]
    r3a, r3b, r3c, r4 = rows[2], rows[3], rows[4], rows[5]
    v1 = ("error" not in r1 and _rt(r1) == 0)
    # budget 档: 模板不支持 -> 参数被忽略, 行为应等同默认 xhigh (非封顶)
    v2 = ("error" not in r2 and _rt(r2) > 96)
    v3 = all("error" not in r for r in (r3a, r3b, r3c))
    v4 = ("error" in r4 and "400" in str(r4.get("error", "")))
    verdict = {
        "V1_enable_thinking_false_zero_reasoning": "PASS" if v1 else "FAIL",
        "V2_thinking_budget_ignored_as_documented": "PASS" if v2 else "FAIL",
        "V3_effort_low_medium_xhigh_accepted": "PASS" if v3 else "FAIL",
        "V4_effort_high_rejected_400": "PASS" if v4 else "FAIL",
        "note": ("模板合法 effort 集 = xhigh(默认)/medium/low; vLLM 0.27 reasoning 存 message.reasoning; thinking_budget "
                 "不在模板中, 传入无效; reasoning_tokens 缺失时以 "
                 "reasoning_content 字符数近似"),
    }
    print("\n[verdict]", json.dumps(verdict, ensure_ascii=False))
    return {"mode": "thinking-probe", "endpoint": args.endpoint,
            "model": args.model, "verdict": verdict, "rows": rows}


# ---------------------------------------------------------------------------
# mode: matrix
# ---------------------------------------------------------------------------
def mode_matrix(args) -> dict:
    import biz.m2_service as m2s
    with open(FIXTURE, encoding="utf-8") as fh:
        questions = json.load(fh)["questions"][:MATRIX_QUESTION_COUNT]
    prep = []
    for q in questions:
        first = (q.get("turns") or [q["question"]])[0]
        sources = m2s.retrieve(first, top_k=5)
        prompt = m2s._build_prompt(first, sources, history=[])
        prep.append({"id": q["id"], "question": first, "prompt": prompt,
                     "n_sources": len(sources)})
        print(f'[prep] {q["id"]}: {len(sources)} sources, '
              f'{len(prompt)} prompt chars')

    results = {}
    for tier_name, tier_kwargs in TIERS.items():
        if args.tier and args.tier != tier_name:
            continue
        rows = []
        for p in prep:
            r = generate(args.endpoint, args.model,
                         [{"role": "user", "content": p["prompt"]}],
                         tier_kwargs, max_tokens=512, timeout=args.timeout)
            r["id"] = p["id"]
            r["question"] = p["question"]
            rows.append(r)
            print(f'{tier_name:15s} {p["id"]:28s} wall={r.get("wall_ms")}ms '
                  f'rt={r.get("reasoning_tokens")} ct={r.get("completion_tokens")} '
                  f'err={str(r.get("error", ""))[:50]}')
        results[tier_name] = {"summary": _summary_rows(rows), "rows": rows}
        print(f'[{tier_name}] {json.dumps(results[tier_name]["summary"])}\n')
    return {"mode": "matrix", "endpoint": args.endpoint, "model": args.model,
            "tiers": results}


# ---------------------------------------------------------------------------
# mode: deterministic
# ---------------------------------------------------------------------------
def mode_deterministic(args) -> dict:
    import m2_eval_deterministic as med
    import biz.m2_service as m2s
    with open(FIXTURE, encoding="utf-8") as fh:
        fx = json.load(fh)
    results = []
    for q in fx["questions"]:
        turns = q.get("turns") or [q["question"]]
        session_id = m2s.new_session_id()
        answers, resp = [], {}
        t_start = time.monotonic()
        for turn in turns:
            t0 = time.monotonic()
            resp = m2s.ask(turn, top_k=5, session_id=session_id)
            resp["_wall_ms"] = int((time.monotonic() - t0) * 1000)
            answers.append(resp.get("answer", ""))
        total_ms = int((time.monotonic() - t_start) * 1000)
        final = answers[-1]
        checks = med.run_checks(q.get("checks", []), final, resp)
        row = {
            "id": q["id"], "category": q.get("category", ""),
            "question": q.get("question", turns[0]), "turns": turns, "answers": answers,
            "checks": checks, "all_pass": all(c["pass"] for c in checks),
            "route": "direct-probe", "model": resp.get("model", args.model),
            "duration_ms": total_ms, "session_id": session_id,
            "sources": resp.get("sources", []),
        }
        results.append(row)
        mark = "PASS" if row["all_pass"] else "FAIL"
        print(f'{q["id"]:28s} {mark:4s} {total_ms}ms '
              f'{sum(c["pass"] for c in checks)}/{len(checks)}')
    n_pass = sum(1 for r in results if r["all_pass"])
    overall = "PASS" if n_pass == len(results) else "FAIL"
    print(f"\n[probe-deterministic] {overall}: {n_pass}/{len(results)}")
    return {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "endpoint": args.endpoint, "overall": overall,
            "n_questions": len(results), "n_pass": n_pass,
            "results": results}


# ---------------------------------------------------------------------------
# mode: concurrency
# ---------------------------------------------------------------------------
def mode_concurrency(args) -> dict:
    import biz.m2_service as m2s
    with open(FIXTURE, encoding="utf-8") as fh:
        questions = [q for q in json.load(fh)["questions"]
                     if not q.get("turns")][:3]

    def one(q: dict) -> dict:
        t0 = time.monotonic()
        try:
            r = m2s.ask(q["question"], top_k=5)
            return {"id": q["id"],
                    "wall_ms": int((time.monotonic() - t0) * 1000),
                    "n_sources": len(r.get("sources", [])),
                    "answer_head": r.get("answer", "")[:100]}
        except Exception as exc:
            return {"id": q["id"], "error": f"{type(exc).__name__}: {exc}",
                    "wall_ms": int((time.monotonic() - t0) * 1000)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        t0 = time.monotonic()
        rows = list(ex.map(one, questions))
        makespan = int((time.monotonic() - t0) * 1000)
    for r in rows:
        print(json.dumps(r, ensure_ascii=False)[:200])
    serial_sum = sum(r["wall_ms"] for r in rows)
    print(f'[concurrency] makespan={makespan}ms sum={serial_sum}ms '
          f'batch_factor={round(serial_sum / max(makespan, 1), 2)}')
    return {"mode": "concurrency", "endpoint": args.endpoint,
            "model": args.model, "makespan_ms": makespan,
            "serial_sum_ms": serial_sum, "rows": rows}


# ---------------------------------------------------------------------------
# mode: vision
# ---------------------------------------------------------------------------
def mode_vision(args) -> dict:
    if not args.image or not os.path.exists(args.image):
        raise SystemExit("vision 模式需要 --image <png/jpg 路径>")
    ext = os.path.splitext(args.image)[1].lstrip(".").lower() or "png"
    if ext == "jpg":
        ext = "jpeg"
    with open(args.image, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode("ascii")
    prompt = args.prompt or ("请把图中的全部文字与表格内容逐字转写出来, "
                             "保持表格结构; 不要添加图中没有的信息。")
    messages = [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {
            "url": f"data:image/{ext};base64,{b64}"}}]}]
    out = {"image": args.image, "prompt": prompt}
    r = generate(args.endpoint, args.model, messages, TIERS["A_off"],
                 max_tokens=2048, timeout=args.timeout)
    out["candidate"] = {"endpoint": args.endpoint, "model": args.model, **r}
    print(f'[candidate] wall={r.get("wall_ms")}ms err={str(r.get("error", ""))[:80]}')
    print((r.get("content") or "")[:600])
    if args.compare_endpoint:
        rc = generate(args.compare_endpoint, args.compare_model, messages,
                      None, max_tokens=2048, timeout=args.timeout)
        out["baseline_old_stack"] = {"endpoint": args.compare_endpoint,
                                     "model": args.compare_model, **rc}
        print(f'\n[old-stack] wall={rc.get("wall_ms")}ms '
              f'err={str(rc.get("error", ""))[:80]}')
        print((rc.get("content") or "")[:600])
    return {"mode": "vision", **out}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", required=True,
                    choices=["thinking-probe", "matrix", "deterministic",
                             "concurrency", "vision"])
    ap.add_argument("--endpoint",
                    default="http://127.0.0.1:8006/v1/chat/completions")
    ap.add_argument("--model", default="qwen38-27b-fp8")
    ap.add_argument("--timeout", type=float, default=300)
    ap.add_argument("--tier", default="", help="matrix 模式只跑指定档")
    ap.add_argument("--image", default="", help="vision 模式图片路径")
    ap.add_argument("--prompt", default="", help="vision 模式自定义 prompt")
    ap.add_argument("--compare-endpoint", default="",
                    help="vision 对照端点 (旧栈 :8004)")
    ap.add_argument("--compare-model", default="Qwen3.6-35B-A3B-Q4_K_M.gguf")
    ap.add_argument("--report", default=None)
    args = ap.parse_args(argv)

    load_dotenv(os.path.join(REPO_ROOT, ".env"))
    # m2_service 在 import 时读取这两个 env -> 必须在 import 前设置
    os.environ["M2_LLM_ENDPOINT"] = args.endpoint
    os.environ["M2_LLM_MODEL"] = args.model
    os.environ["M2_LLM_TIMEOUT"] = str(int(args.timeout))

    t0 = time.monotonic()
    fn = {"thinking-probe": mode_thinking_probe, "matrix": mode_matrix,
          "deterministic": mode_deterministic,
          "concurrency": mode_concurrency, "vision": mode_vision}[args.mode]
    report = fn(args)
    report["total_wall_s"] = round(time.monotonic() - t0, 1)
    out = save_report(args.mode, report, args.report)
    print(f"\n[report] {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
