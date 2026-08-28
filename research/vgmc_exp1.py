#!/usr/bin/env python3
"""VGMC 实验 1 — 固化机制闭环（漂移注入 + 门控, 论文 A 贡献 1）。

闭环: 确定性匹配 -> 未映射列送 LLM(:8004, temp=0) 建议 -> 门控判定 ->
规则固化（全局同义词库, 实验副本）-> 重跑。课程式轮次: 每轮引入一批新
固化集表, 已学规则自动复用 -> λ(t) 衰减曲线 + H(t) 上升曲线。

臂:
  A 有门控: 建议 s 接受 ⟺ gain(source 表 ΔH) >= τ 且 collateral(其余固化表
    ΔH) >= -ε（docs/33 §4 固化门公式的操作化）
  B 无门控直固: 全部建议直接固化（唯一变量 = 门控）

预注册见 docs/experiments/2026-08-26_vgmc_exp1_design.md:
  切分 60/35 seed=20260826; τ=0.1 ε=0.02 主档; 网格 3x2 收口重放;
  :8006 零调用（运行时断言）; 生产配置零写。

用法:
  python3 research/vgmc_exp1.py [--arm both|gated|ungated] [--rounds 4]
      [--batch 15] [--pilot 2] [--fresh]
产出:
  logs/graph/eval/vgmc_exp1_checkpoint.json   每轮末检查点（可续跑）
  logs/graph/eval/vgmc_exp1_results.json      终件（逐轮数据+网格重放+终值）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import m1_statement_parser as mp  # noqa: E402

DRIFT_OUT = REPO / "data" / "research" / "drift_v0" / "output"
EVAL = REPO / "logs" / "graph" / "eval"
CKPT = EVAL / "vgmc_exp1_checkpoint.json"
OUT = EVAL / "vgmc_exp1_results.json"

SEED = 20260826
N_MEAS = 35
TAU_MAIN, EPS_MAIN = 0.1, 0.02
GRID = [(t, e) for t in (0.05, 0.1, 0.2) for e in (0.0, 0.02)]
QA_ENDPOINT = "http://127.0.0.1:8004/v1/chat/completions"


def assert_endpoint_safe() -> None:
    if "8006" in QA_ENDPOINT or "127.0.0.1:8004" not in QA_ENDPOINT:
        raise RuntimeError(f"endpoint must be :8004 only: {QA_ENDPOINT}")


# ---------------------------------------------------------------- corpus
def load_corpus(overlay: dict | None = None):
    """95 注入表: uid -> {inj_header, orig_header, canonicals, rows}"""
    tables = json.loads((DRIFT_OUT / "injected_tables.json").read_text(encoding="utf-8"))
    imap = json.loads((DRIFT_OUT / "injection_map.json").read_text(encoding="utf-8"))
    by_uid = {t["uid"]: t["table"] for t in tables}
    ent: dict[str, list[dict]] = {}
    for e in imap["mapping"]:
        ent.setdefault(e["uid"], []).append(e)
    corpus = {}
    for uid, es in ent.items():
        rows = by_uid[uid]
        inj_header = [str(c) if c is not None else "" for c in rows[0]]
        orig_header = list(inj_header)
        for e in es:
            orig_header[e["col"]] = e["original"]
        seen, canonicals = set(), []
        for h in orig_header:
            if not mp.normalize_header(h):
                continue
            k = mp.normalize_header(h)
            if k not in seen:
                seen.add(k)
                canonicals.append(str(h))
        corpus[uid] = {"uid": uid, "rows": rows, "inj_header": inj_header,
                       "orig_header": orig_header, "canonicals": canonicals,
                       "entries": es}
    return merge_overlay(corpus, overlay)


def merge_overlay(corpus: dict, overlay: dict | None) -> dict:
    """碰撞语料: 移植列只增列不改原列（甲方零进入, ground truth 在工件）。"""
    if not overlay:
        return corpus
    for uid, spec in overlay.get("tables", {}).items():
        rec = corpus.get(uid)
        if not rec:
            continue
        for c in spec["cols"]:
            idx = len(rec["inj_header"])
            rec["inj_header"].append(c["header"])
            for r_i, row in enumerate(rec["rows"]):
                row.append(row[c["data_col_idx"]] if r_i > 0 and c["data_col_idx"] < len(row)
                           else c["header"])
            rec["entries"].append({"col": idx, "original": c["true_canonical"],
                                   "injected": c["header"], "type": "collision"})
    return corpus


def split_uids(uids: list[str]) -> tuple[list[str], list[str]]:
    rng = random.Random(SEED)
    meas = set(rng.sample(sorted(uids), N_MEAS))
    fix = [u for u in sorted(uids) if u not in meas]
    return fix, sorted(meas)


# ---------------------------------------------------------------- matching
def schema_table_for(rec: dict, rules: dict) -> mp.SchemaTable:
    fields = [mp.SchemaField(c, [c] + list(rules.get(c, [])))
              for c in rec["canonicals"]]
    return mp.SchemaTable(table_name=f"vgmc_{rec['uid'][:8]}", layout="grid",
                          header_region_keywords=[], fields=fields)


def table_h(rec: dict, rules: dict) -> float:
    n = len(rec["canonicals"])
    if not n:
        return 1.0
    mapping, _ = mp.map_headers(rec["inj_header"], schema_table_for(rec, rules))
    return len(mapping) / n


def pool_h(uids: list[str], corpus: dict, rules: dict) -> float:
    if not uids:
        return 1.0
    return sum(table_h(corpus[u], rules) for u in uids) / len(uids)


def unresolved_cols(rec: dict, rules: dict) -> list[int]:
    """注入表头中未被当前规则库映射到其原字段的列。"""
    st = schema_table_for(rec, rules)
    mapping, _ = mp.map_headers(rec["inj_header"], st)
    rev = {src: std for std, src in mapping.items()}
    out = []
    for e in rec["entries"]:
        col, o, x = e["col"], e["original"], e["injected"]
        c = next((c for c in rec["canonicals"]
                  if mp.normalize_header(c) == mp.normalize_header(o)), None)
        if c is None or rev.get(x) != c:
            out.append(col)
    return sorted(set(out))


# ---------------------------------------------------------------- LLM
def llm_suggest(rec: dict, cols: list[int], rules: dict, noise: str = "none",
                noise_temp: float = 0.8, force_rate: float = 0.0,
                noise_seed: int = 0, mem_text: str = "") -> list[dict]:
    assert_endpoint_safe()
    hdr = rec["inj_header"]
    data_rows = [] if noise == "prompt" else rec["rows"][1:3]
    tbl = "\n".join("| " + " | ".join(str(c) if c is not None else "" for c in r) + " |"
                    for r in [hdr] + data_rows)
    canon = "\n".join(f"- {c}" + ("" if noise == "prompt" else (f"（已有别名: {', '.join(rules[c])}）" if rules.get(c) else ""))
                      for c in rec["canonicals"])
    asked = "\n".join(f"- 第 {c + 1} 列: {hdr[c]!r}" for c in cols)
    extra = "\n\n已有经验（可参考）:\n" + mem_text if mem_text else ""
    prompt = (
        "下面是表格（首行为表头）:\n" + tbl + "\n\n标准字段清单:\n" + canon +
        "\n\n未解析的表头列:\n" + asked +
        extra +
        "\n\n请为每个未解析列判断它对应哪个标准字段（可能是别名/变体/中英混写/OCR 形近/单位后缀/日期变体）。"
        "只输出 JSON 数组, 每项: {\"column\": 列号(从1起), \"action\": \"map_to\" 或 \"skip\", "
        "\"target\": 标准字段名或null, \"confidence\": \"high\"/\"medium\"/\"low\", "
        "\"reason\": 一句话}。不要输出其他文字。"
    )
    body = json.dumps({
        "model": "local",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": noise_temp if noise == "temp" else 0.0, "max_tokens": 1024,
        "chat_template_kwargs": {"enable_thinking": False},
    }).encode("utf-8")
    req = urllib.request.Request(QA_ENDPOINT, data=body,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
    sgs = _extract_suggestions(text)
    if noise == "force":
        sgs = force_inject(sgs, rec, cols, force_rate, noise_seed)
    return sgs


def _extract_suggestions(text: str) -> list[dict]:
    s = text.strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.startswith("json"):
            s = s[4:]
    a, b = s.find("["), s.rfind("]")
    if a == -1 or b == -1 or b <= a:
        return []
    try:
        v = json.loads(s[a:b + 1])
        return [x for x in v if isinstance(x, dict)]
    except Exception:
        return []


def force_inject(sgs: list[dict], rec: dict, cols: list[int],
                 rate: float, seed: int) -> list[dict]:
    """L3 噪声: 每未解析列以概率 rate 尾插合成错误建议（目标=随机其他 canonical, col2sg 后写覆盖）。"""
    out = list(sgs)
    for c in cols:
        rng = random.Random(f"{seed}:{rec['uid']}:{c}")
        if rng.random() > rate:
            continue
        e = next((e for e in rec["entries"] if e["col"] == c), None)
        true_c = next((x for x in rec["canonicals"] if e and
                       mp.normalize_header(x) == mp.normalize_header(e["original"])), None)
        wrong = [x for x in rec["canonicals"] if x != true_c]
        if wrong:
            out.append({"column": c + 1, "action": "map_to", "target": rng.choice(wrong),
                        "confidence": "low", "synthetic": True, "reason": "forced_noise"})
    return out


# ---------------------------------------------------------------- gate
def gate_eval(rec: dict, corpus: dict, fix_uids: list[str], rules: dict,
              target: str, syn: str) -> dict:
    """gain = source 表 ΔH; collateral = 其余固化表 ΔH（含未引入表: 全固化集）。"""
    r2 = {k: list(v) for k, v in rules.items()}
    r2.setdefault(target, []).append(syn)
    h_src_b = table_h(rec, rules)
    h_src_a = table_h(rec, r2)
    others = [u for u in fix_uids if u != rec["uid"]]
    h_oth_b = pool_h(others, corpus, rules)
    h_oth_a = pool_h(others, corpus, r2)
    return {"gain": round(h_src_a - h_src_b, 6),
            "collateral": round(h_oth_a - h_oth_b, 6)}


# ---------------------------------------------------------------- baselines
def _norm_tok(s: str) -> str:
    return "".join(ch for ch in str(s).lower() if ch.isalnum())


def fewshot_pool(corpus: dict, fix_uids: list[str]) -> list[dict]:
    """静态示例池 = 固化集前 10 表已解决案例（holdout 零泄漏, 确定性）。"""
    pool = []
    for uid in fix_uids[:10]:
        for e in corpus[uid]["entries"]:
            pool.append({"header": corpus[uid]["inj_header"][e["col"]],
                         "canonical": e["original"]})
    return pool


def memory_text(baseline: str, mem: list, cols_hdrs: list[str], pool: list[dict]) -> str:
    """读侧: fewshot top-6 / mem0 top-8（词法重叠排序, 确定性）/ awm 全量 ≤15。"""
    if baseline == "awm":
        return "\n".join(f"- {x}" for x in mem[:15]) if mem else ""
    if baseline == "fewshot":
        cands = [(x["header"], f"表头 {x['header']!r} 对应标准字段 {x['canonical']}") for x in pool]
    else:
        cands = [(f, f) for f in mem] if baseline == "mem0" else []
    qchars = set().union(*[set(_norm_tok(h)) for h in cols_hdrs]) if cols_hdrs else set()
    idx = sorted(range(len(cands)), key=lambda i: (-len(set(_norm_tok(cands[i][0])) & qchars), i))
    return "\n".join("- " + cands[i][1] for i in idx[:6 if baseline == "fewshot" else 8]) if cands else ""


def memory_write_llm(kind: str, items: list[tuple[str, str]]) -> list[str]:
    """写侧每轮 1 次（temp=0, 仅 :8004）: mem0 抽事实 / awm 归纳过程。"""
    assert_endpoint_safe()
    listing = "\n".join(f"- 表头 {h!r} -> 标准字段 {c}" for h, c in items)
    ask = ("从下面的表头映射案例中抽取可复用的简短事实陈述" if kind == "mem0"
           else "从下面的表头映射案例中归纳可复用的简短过程性规则（启发式）")
    prompt = ask + "，每条一句话，只输出 JSON 字符串数组（≤8 条），不要输出其他文字。\n案例:\n" + listing
    body = json.dumps({"model": "local", "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0.0, "max_tokens": 512,
                       "chat_template_kwargs": {"enable_thinking": False}}).encode("utf-8")
    req = urllib.request.Request(QA_ENDPOINT, data=body, headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        text = (json.loads(resp.read().decode("utf-8")).get("choices") or [{}])[0].get(
            "message", {}).get("content", "") or ""
    a, b = text.find("["), text.rfind("]")
    if a == -1 or b <= a:
        return []
    try:
        return [str(x) for x in json.loads(text[a:b + 1])][:8]
    except Exception:
        return []


# ---------------------------------------------------------------- arm loop
def run_arm(name: str, fix_uids: list[str], meas_uids: list[str], corpus: dict, rounds: int,
            batch: int, pilot: int, state: dict, noise_kw: dict | None = None,
            baseline_kw: dict | None = None) -> dict:
    rules: dict = state.get("rules", {})
    introduced: list[str] = state.get("introduced", [])
    asked: set = set(state.get("asked", []))
    rounds_log: list[dict] = state.get("rounds", [])
    sugg_log: list[dict] = state.get("sugg_log", [])
    pilot_log: list[dict] = state.get("pilot_log", [])
    noise_kw = noise_kw or {}
    baseline_kw = baseline_kw or {}
    baseline = baseline_kw.get("baseline", "none")
    mem: list = state.get("memory", [])
    pool: list[dict] = baseline_kw.get("pool", [])

    def ckpt():
        state.update({"rules": rules, "introduced": introduced,
                      "asked": sorted(asked), "rounds": rounds_log,
                      "sugg_log": sugg_log, "pilot_log": pilot_log})

    # pilot（λ 外, 单记）: 用固化集前 pilot 张表试 prompt
    if pilot and not state.get("pilot_done"):
        for uid in fix_uids[:pilot]:
            rec = corpus[uid]
            cols = unresolved_cols(rec, rules)
            if not cols:
                continue
            t0 = time.time()
            sgs = llm_suggest(rec, cols, rules, **noise_kw)
            pilot_log.append({"uid": uid, "cols": cols, "n_sugg": len(sgs),
                              "latency_s": round(time.time() - t0, 2),
                              "sample": sgs[:2]})
        state["pilot_done"] = True
        ckpt()

    start_round = len(rounds_log)
    for r in range(start_round, rounds):
        chunk = fix_uids[r * batch:(r + 1) * batch]
        if not chunk:
            break
        introduced.extend(chunk)
        lam = 0
        round_acc: list[tuple[str, str]] = []
        n_asked_cols = 0
        n_sugg = 0
        accepted = 0
        for uid in chunk:
            rec = corpus[uid]
            cols = [c for c in unresolved_cols(rec, rules)
                    if f"{uid}:{c}" not in asked]
            if not cols:
                continue
            lam += 1
            n_asked_cols += len(cols)
            hdrs = [rec["inj_header"][c] for c in cols]
            sgs = llm_suggest(rec, cols, rules, mem_text=memory_text(baseline, mem, hdrs, pool),
                              **noise_kw)
            col2sg = {}
            for s in sgs:
                try:
                    col2sg[int(s.get("column", 0)) - 1] = s
                except Exception:
                    pass
            for c in cols:
                asked.add(f"{uid}:{c}")
                e = next((e for e in rec["entries"] if e["col"] == c), None)
                s = col2sg.get(c)
                if not s or s.get("action") != "map_to" or not s.get("target"):
                    sugg_log.append({"round": r, "uid": uid, "col": c,
                                     "type": e["type"] if e else None,
                                     "injected": rec["inj_header"][c],
                                     "action": (s or {}).get("action", "parse_fail"),
                                     "accepted": False, "reason": "no_map"})
                    n_sugg += 1
                    continue
                target = s["target"]
                if target not in rec["canonicals"]:
                    sugg_log.append({"round": r, "uid": uid, "col": c,
                                     "type": e["type"] if e else None,
                                     "injected": rec["inj_header"][c],
                                     "action": "map_to", "target": target,
                                     "accepted": False, "reason": "target_not_canonical"})
                    n_sugg += 1
                    continue
                syn = rec["inj_header"][c]
                g = gate_eval(rec, corpus, fix_uids, rules, target, syn)
                n_sugg += 1
                if name == "gated":
                    ok = g["gain"] >= TAU_MAIN and g["collateral"] >= -EPS_MAIN
                else:
                    ok = True
                entry = {"round": r, "uid": uid, "col": c,
                         "action": "map_to",
                         "type": e["type"] if e else None,
                         "injected": syn, "target": target,
                         "confidence": s.get("confidence"),
                         "gain": g["gain"], "collateral": g["collateral"],
                         "accepted": bool(ok),
                         "reason": "gated_pass" if ok and name == "gated"
                         else ("gated_fail" if name == "gated" else "ungated")}
                sugg_log.append(entry)
                if ok:
                    rules.setdefault(target, [])
                    if syn not in rules[target]:
                        rules[target].append(syn)
                    accepted += 1
                    round_acc.append((syn, target))
        if baseline in ("mem0", "awm") and round_acc:
            for item in memory_write_llm(baseline, round_acc):
                if item not in mem:
                    mem.append(item)
            state["memory"] = mem
        rec_row = {
            "round": r, "arm": name,
            "introduced_n": len(introduced),
            "lambda_calls": lam, "asked_cols": n_asked_cols,
            "suggestions": n_sugg, "accepted": accepted,
            "h_fix": round(pool_h(introduced, corpus, rules), 6),
            "h_meas": round(pool_h(meas_uids, corpus, rules), 6),
            "n_rules": sum(len(v) for v in rules.values()),
        }
        rounds_log.append(rec_row)
        ckpt()
        save_ckpt({"arm_" + name: state}, merge=True)
        print(f"[{name}] round {r}: λ={lam} sugg={n_sugg} acc={accepted} "
              f"H_fix={rec_row['h_fix']:.4f} H_meas={rec_row['h_meas']:.4f}",
              file=sys.stderr)
    return state


def save_ckpt(payload: dict, merge: bool = False):
    cur = {}
    if CKPT.exists() and merge:
        try:
            cur = json.loads(CKPT.read_text(encoding="utf-8"))
        except Exception:
            cur = {}
    cur.update(payload)
    CKPT.write_text(json.dumps(cur, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------- replay
def grid_replay(sugg_log: list[dict], corpus: dict, fix_uids: list[str],
                meas_uids: list[str]) -> dict:
    """对臂 A 建议流水做 (τ,ε) 网格机械重放（零 LLM 调用）。"""
    out = {}
    ordered = [s for s in sugg_log if s.get("gain") is not None]
    for tau, eps in GRID:
        rules: dict = {}
        n_acc = 0
        for s in ordered:
            if s["gain"] >= tau and s["collateral"] >= -eps:
                rules.setdefault(s["target"], [])
                if s["injected"] not in rules[s["target"]]:
                    rules[s["target"]].append(s["injected"])
                n_acc += 1
        out[f"tau={tau},eps={eps}"] = {
            "accepted": n_acc, "total": len(ordered),
            "accept_rate": round(n_acc / len(ordered), 4) if ordered else None,
            "h_fix_final": round(pool_h(fix_uids, corpus, rules), 6),
            "h_meas_final": round(pool_h(meas_uids, corpus, rules), 6),
        }
    return out


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="both", choices=["both", "gated", "ungated"])
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--batch", type=int, default=15)
    ap.add_argument("--pilot", type=int, default=2)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--noise", default="none", choices=["none", "temp", "prompt", "force"])
    ap.add_argument("--noise-temp", type=float, default=0.8)
    ap.add_argument("--force-rate", type=float, default=0.5)
    ap.add_argument("--noise-seed", type=int, default=20260827)
    ap.add_argument("--label", default=None)
    ap.add_argument("--collision-overlay", default=None)
    ap.add_argument("--baseline", default="none", choices=["none", "fewshot", "mem0", "awm"])
    args = ap.parse_args()
    assert_endpoint_safe()
    global CKPT, OUT
    label = args.label or ("exp1" if args.noise == "none" and args.baseline == "none"
                           else (f"baseline_{args.baseline}" if args.baseline != "none"
                                 else f"noise_{args.noise}"))
    CKPT = EVAL / f"vgmc_{label}_checkpoint.json"
    OUT = EVAL / f"vgmc_{label}_results.json"

    t0 = time.time()

    overlay = None
    if args.collision_overlay:
        overlay = json.loads(Path(args.collision_overlay).read_text(encoding="utf-8"))
    corpus = load_corpus(overlay)
    fix_uids, meas_uids = split_uids(list(corpus.keys()))
    split_digest = hashlib.sha256(json.dumps(
        {"fix": fix_uids, "meas": meas_uids}, ensure_ascii=False).encode()).hexdigest()

    ckpt = {}
    if CKPT.exists() and not args.fresh:
        try:
            ckpt = json.loads(CKPT.read_text(encoding="utf-8"))
            print(f"[resume] arms in checkpoint: {[k for k in ckpt if k.startswith('arm_')]}",
                  file=sys.stderr)
        except Exception:
            ckpt = {}

    baseline = {
        "h_fix": round(pool_h(fix_uids, corpus, {}), 6),
        "h_meas": round(pool_h(meas_uids, corpus, {}), 6),
    }
    print(f"baseline: H_fix={baseline['h_fix']:.4f} H_meas={baseline['h_meas']:.4f} "
          f"(fix={len(fix_uids)}, meas={len(meas_uids)})", file=sys.stderr)

    noise_kw = {"noise": args.noise, "noise_temp": args.noise_temp, "noise_seed": args.noise_seed,
                "force_rate": args.force_rate if args.noise == "force" else 0.0}
    pool = fewshot_pool(corpus, fix_uids) if args.baseline == "fewshot" else []
    baseline_kw = {"baseline": args.baseline, "pool": pool}
    arms = ["gated", "ungated"] if args.arm == "both" else [args.arm]
    for arm in arms:
        state = ckpt.get("arm_" + arm, {})
        state = run_arm(arm, fix_uids, meas_uids, corpus, args.rounds,
                        args.batch, args.pilot, state, noise_kw, baseline_kw)
        ckpt["arm_" + arm] = state
        save_ckpt({"arm_" + arm: state}, merge=True)

    payload = {
        "meta": {
            "name": "vgmc-exp1", "version": "v1",
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "design": "docs/experiments/2026-08-26_vgmc_exp1_design.md",
            "prereg": {"seed": SEED, "n_meas": N_MEAS, "tau_main": TAU_MAIN,
                       "eps_main": EPS_MAIN, "grid": GRID,
                       "split_digest_sha256": split_digest,
                       "fix_uids": fix_uids, "meas_uids": meas_uids},
            "endpoint": QA_ENDPOINT,
            "collision_overlay": ({"path": args.collision_overlay, "n_cols": overlay["meta"]["n_cols"],
                                    "seed": overlay["meta"]["seed"]} if overlay else None),
            "baseline": {"level": args.baseline,
                          "pool_n": len(pool) if args.baseline == "fewshot" else None},
            "noise": {"level": args.noise, "label": label,
                      "temp": args.noise_temp if args.noise == "temp" else None,
                      "force_rate": args.force_rate if args.noise == "force" else None,
                      "seed": args.noise_seed if args.noise != "none" else None},
            "baseline_no_rules": baseline,
            "runtime_s": round(time.time() - t0, 2),
        },
    }
    for arm in arms:
        st = ckpt["arm_" + arm]
        rounds_log = st.get("rounds", [])
        sugg_log = st.get("sugg_log", [])
        n_sugg = len(sugg_log)
        n_acc = sum(1 for s in sugg_log if s.get("accepted"))
        meas_improved = 0
        rules_final = st.get("rules", {})
        for u in meas_uids:
            if table_h(corpus[u], rules_final) > table_h(corpus[u], {}) + 1e-9:
                meas_improved += 1
        ovl_acc = None
        if overlay:
            n_ovl = ok = 0
            for u in meas_uids:
                rec = corpus[u]
                mapping, _ = mp.map_headers(rec["inj_header"], schema_table_for(rec, rules_final))
                rev = {src: std for std, src in mapping.items()}
                for e in rec["entries"]:
                    if e.get("type") == "collision":
                        n_ovl += 1
                        ok += rev.get(rec["inj_header"][e["col"]]) == e["original"]
            ovl_acc = round(ok / n_ovl, 4) if n_ovl else None
        payload["arm_" + arm] = {
            "rounds": rounds_log,
            "n_suggestions": n_sugg, "n_accepted": n_acc,
            "fixation_rate": round(n_acc / n_sugg, 4) if n_sugg else None,
            "h_fix_final": rounds_log[-1]["h_fix"] if rounds_log else None,
            "h_meas_final": rounds_log[-1]["h_meas"] if rounds_log else None,
            "degradation_vs_baseline": round(
                baseline["h_meas"] - (rounds_log[-1]["h_meas"] if rounds_log
                                      else baseline["h_meas"]), 6),
            "transfer_rate": round(meas_improved / len(meas_uids), 4),
            "collision_acc": ovl_acc,
            "memory_final": st.get("memory", []) if args.baseline in ("mem0", "awm") else None,
            "pilot": st.get("pilot_log", []),
            "rules": rules_final,
        }
    if "gated" in arms:
        payload["grid_replay"] = grid_replay(
            ckpt["arm_gated"].get("sugg_log", []), corpus, fix_uids, meas_uids)

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(json.dumps({"out": str(OUT),
                      "arms": arms,
                      "summary": {a: {"h_meas_final": payload["arm_" + a]["h_meas_final"],
                                      "fixation_rate": payload["arm_" + a]["fixation_rate"],
                                      "degradation": payload["arm_" + a]["degradation_vs_baseline"]}
                                  for a in arms}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
