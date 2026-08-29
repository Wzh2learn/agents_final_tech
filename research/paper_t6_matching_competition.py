#!/usr/bin/env python3
"""T6 匹配竞争控制（Phase 5 E5.1-E5.2, 零端点）。

设计稿（判据冻结）: docs/experiments/2026-08-30_t6_matching_competition_design.md

E5.1 Hungarian 全局最优分配 vs 现行贪心（map_headers 局部 argmax + 高优先占用）
     双臂 x {original, injected} 两套表头 x 95 表 = 380 次分配
E5.2 oracle ACC 天花板复核（p1_correctness_backfill 口径独立重算 plain / overlay 两 regime）

纯 stdlib（含自实现 O(n^3) 匈牙利算法）+ 生产匹配器只读导入; 运行时硬断言零网络。
复算: PYTHONPATH=src python research/paper_t6_matching_competition.py
输出: logs/graph/eval/t6_matching_competition.json
"""
from __future__ import annotations

import hashlib
import importlib.util
import random
import json
import socket
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
DRIFT = REPO / "data" / "research" / "drift_v0" / "output"
TABLES_FROZEN = EVAL / "checkpoint_discrimination_tables_v2.json"
P1_ART = EVAL / "p1_correctness_backfill.json"
OUT = EVAL / "t6_matching_competition.json"

SEED = 20260830
BIG = 10 ** 6           # 禁用边代价（匈牙利臂）
ORACLE_EXPECTED = {"plain": {"acc_oracle_meas": 0.952381, "h_baseline_meas": 0.558095},
                   "overlay": {"acc_oracle_meas": 0.597015, "h_baseline_meas": 0.594762}}
# 判据 P3 影响范围三选一（数值规则在执行前写定于此, 不随实算调整）
IMPACT_RULE = (
    "无实质改变: Hungarian 臂 ocr_similar 可见数仍为 0 且六类可见率极差变化 <= 0.10 且表级判别数变化 <= 2;"
    " 需降级: ocr_similar 可见数 >= 3（13 条中）或类型排序坍缩;"
    " 其余落 限定条件下成立（1-2 条翻转或极差变化 0.10-0.30）")
SHA_SCOPE = ["gates", "solver_validation", "e5_1_arm_comparison", "e5_2_oracle_reproduction",
             "prereg_predicates", "tables", "zero_endpoint"]


# ---------------------------------------------------------------- 零端点护栏
def _install_network_guard() -> None:
    real_socket = socket.socket

    class _BlockedSocket(real_socket):  # type: ignore[misc]
        def connect(self, *a, **k):
            raise RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")

        def connect_ex(self, *a, **k):
            raise RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")

        def sendto(self, *a, **k):
            raise RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")

    def _blocked(*_a, **_k):
        raise RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")

    socket.socket = _BlockedSocket       # type: ignore[assignment]
    socket.create_connection = _blocked  # type: ignore[assignment]
    socket.getaddrinfo = _blocked        # type: ignore[assignment]


def self_source_scan() -> dict:
    pats = ["url" + "open", "request" + "s.",
            "htt" + "p:" + "/" * 2, "HTT" + "PS:" + "/" * 2,
            ":" + "8004", ":" + "8005", ":" + "8006", ":" + "8007", ":" + "8008",
            ":" + "5050", "sock" + "et.connect"]
    hits = {}
    files = sorted((REPO / "research").glob("paper_t*_*.py"))
    for f in files:
        found = []
        for i, ln in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            code = ln.split("#", 1)[0]
            for p in pats:
                if p in code and "blocked" not in code and "ZERO_ENDPOINT" not in code:
                    found.append({"line": i, "pattern": p, "text": ln.strip()[:120]})
        if found:
            hits[f.name] = found
    return {"patterns": pats, "files_scanned": [f.name for f in files],
            "hits_outside_comments": hits, "clean": not hits}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- 匈牙利算法
def hungarian_max(weight: list[list[float]]) -> tuple[list[int], float]:
    """最大权完备分配（方阵, 自实现 JV/势函数 O(n^3), 纯 stdlib, 确定性）。

    返回 cols_of_row[i] = j 与总权重。矩阵需已按 max(rows, cols) 补方;
    无效/占位边以 0 或负代价进入, 由调用方保证补方行列提供退路。
    """
    n = len(weight)
    m = max(n, max((len(r) for r in weight), default=0))
    cost = [[0.0] * m for _ in range(n)]
    for i in range(n):
        for j in range(m):
            cost[i][j] = -float(weight[i][j])
    INF = float("inf")
    u = [0.0] * (n + 1)
    v = [0.0] * (m + 1)
    p = [0] * (m + 1)
    way = [0] * (m + 1)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [INF] * (m + 1)
        used = [False] * (m + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = INF
            j1 = -1
            row = cost[i0 - 1]
            for j in range(1, m + 1):
                if used[j]:
                    continue
                cur = row[j - 1] - u[i0] - v[j]
                if cur < minv[j]:
                    minv[j] = cur
                    way[j] = j0
                if minv[j] < delta:
                    delta = minv[j]
                    j1 = j
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break
    cols_of_row = [-1] * n
    for j in range(1, m + 1):
        if p[j]:
            cols_of_row[p[j] - 1] = j - 1
    total = sum(weight[i][cols_of_row[i]] for i in range(n) if cols_of_row[i] >= 0)
    return cols_of_row, total


def solver_validation() -> dict:
    """匈牙利求解器自证（防"静默退化成贪心"导致分支 a 假阳性）。

    1) 随机小矩阵上与暴力枚举最优值对拍（定种子, 纯确定性）;
    2) 正例对照: 构造一个贪心必然次优的打分矩阵, 求解器必须找出增量。
    """
    import itertools
    rng = random.Random(SEED)
    worst_gap = 0.0
    n_checked = 0
    for trial in range(300):
        n = rng.randint(2, 6)
        m = rng.randint(n, 7)
        w = [[float(rng.randint(0, 4) * 100 + rng.randint(0, 9)) if rng.random() > 0.25 else 0.0
              for _ in range(m)] for _ in range(n)]
        cols_of_row, total = hungarian_max(w)
        best = 0
        for combo in itertools.permutations(range(m), n):
            if len(set(combo)) != n:
                continue
            best = max(best, sum(w[i][combo[i]] for i in range(n)))
        worst_gap = max(worst_gap, best - total)
        n_checked += 1
    # 正例对照: 列 A 对 f1/f2 均为高分且 f1 更高, 列 B 只配得上 f1 -> 贪心取 A-f1 后 B 无路
    demo = [[403.0, 402.0], [404.0, 0.0]]          # A: f1=403 f2=402 ; B: f1=404 f2=无
    greedy_pick = max(range(2), key=lambda j: demo[0][j])   # 贪心按列 A 的 argmax -> f1
    greedy_total = demo[0][greedy_pick] + 0.0
    _cols, opt_total = hungarian_max(demo)
    return {"bruteforce_random_trials": n_checked,
            "bruteforce_max_optimality_gap": worst_gap,
            "bruteforce_exact": worst_gap == 0.0,
            "positive_control_greedy_total": greedy_total,
            "positive_control_hungarian_total": opt_total,
            "positive_control_detects_improvement": opt_total > greedy_total,
            "note": "随机对拍证明求解器返回全局最优; 正例对照证明它能发现贪心漏掉的增量, "
                    "因此语料内 0 差异不是求解器退化所致"}


# ---------------------------------------------------------------- 打分与双臂
def pair_score(header_text: str, canonical: str, mp) -> tuple[int, int]:
    """匹配器对 (源列, canonical) 的打分元组 (score, syn_len); 无匹配 -> (0, 0)。"""
    best = mp._best_field_for_header(mp.normalize_header(header_text),
                                     [mp.SchemaField(canonical, [canonical])])
    if not best:
        return 0, 0
    return int(best[0]), int(best[1])


def encode(score: int, syn_len: int) -> float:
    """设计稿 3.1 标量编码: score*100 + min(syn_len, 99)（忠实贪心优先级序）。"""
    return score * 100 + min(syn_len, 99)


def greedy_map(header: list[str], canonicals: list[str], mp) -> dict:
    fields = [mp.SchemaField(std, [std]) for std in canonicals]
    st = mp.SchemaTable(table_name="t6_greedy", layout="grid",
                        header_region_keywords=[], fields=fields)
    mapping, _ = mp.map_headers(header, st)
    return mapping


def hungarian_map(header: list[str], canonicals: list[str], mp) -> tuple[dict, float]:
    rows = [i for i, h in enumerate(header) if mp.normalize_header(h)]
    cols = list(range(len(canonicals)))
    if not rows or not cols:
        return {}, 0.0
    n, m = len(rows), len(cols)
    N = max(n, m)
    w = [[0.0] * N for _ in range(N)]
    raw = {}
    for ri, i in enumerate(rows):
        for cj, j in enumerate(cols):
            sc, sl = pair_score(header[i], canonicals[j], mp)
            raw[(i, canonicals[j])] = (sc, sl)
            if sc == 0:
                w[ri][cj] = -BIG          # 无效边: 大负权, 补方行列恒提供 0 权退路
            else:
                w[ri][cj] = encode(sc, sl)
    cols_of_row, _total = hungarian_max(w)
    mapping: dict[str, str] = {}
    total = 0.0
    for ri, i in enumerate(rows):
        cj = cols_of_row[ri]
        if cj < 0 or cj >= m:
            continue                      # 落到补方列 = 该源列未分配
        canon = canonicals[cols[cj]]
        sc, sl = raw[(i, canon)]
        if sc == 0:
            continue
        mapping[canon] = header[i]
        total += encode(sc, sl)
    return mapping, total


def unique_canonical(header: list[str], mp) -> list[str]:
    seen, out = set(), []
    for h in header:
        k = mp.normalize_header(h)
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(str(h))
    return out


# ---------------------------------------------------------------- E5.1
def run_e5_1(mp, frozen: dict) -> dict:
    tables = json.loads((DRIFT / "injected_tables.json").read_text(encoding="utf-8"))
    imap = json.loads((DRIFT / "injection_map.json").read_text(encoding="utf-8"))
    by_uid = {t["uid"]: t["table"] for t in tables}
    ent: dict[str, list[dict]] = {}
    for e in imap["mapping"]:
        ent.setdefault(e["uid"], []).append(e)

    per_table = []
    audit = []
    inj_diff = []
    scoring_rows = []
    for uid in sorted(ent):
        inj_header = [str(c) if c is not None else "" for c in by_uid[uid][0]]
        orig_header = list(inj_header)
        for e in ent[uid]:
            orig_header[e["col"]] = e["original"]
        canonicals = unique_canonical(orig_header, mp)
        n = len(canonicals)
        rec = {"uid": uid, "n_canonical": n, "n_injections": len(ent[uid])}
        for head_tag, header in (("orig", orig_header), ("inj", inj_header)):
            g = greedy_map(header, canonicals, mp)
            h, h_total = hungarian_map(header, canonicals, mp)
            diff = [c for c in canonicals if g.get(c) != h.get(c)]
            g_total = sum(encode(*pair_score(g[c], c, mp)) for c in g) if g else 0.0
            rec[f"greedy_{head_tag}"] = {c: g.get(c) for c in canonicals}
            rec[f"hung_{head_tag}"] = {c: h.get(c) for c in canonicals}
            rec[f"h_{head_tag}_greedy"] = round(len(g) / n, 6) if n else 1.0
            rec[f"h_{head_tag}_hung"] = round(len(h) / n, 6) if n else 1.0
            rec[f"diff_{head_tag}_cols"] = diff
            rec[f"weight_{head_tag}_greedy"] = g_total
            rec[f"weight_{head_tag}_hung"] = h_total
            if diff:
                for c in diff:
                    audit.append({
                        "uid": uid, "header": head_tag, "canonical": c,
                        "greedy_src": g.get(c), "hungarian_src": h.get(c),
                        "greedy_weight_on_col": (None if g.get(c) is None
                                                 else encode(*pair_score(g[c], c, mp))),
                        "hungarian_weight_on_col": (None if h.get(c) is None
                                                    else encode(*pair_score(h[c], c, mp))),
                        "is_injected_col": any(e["col"] == header.index(x)
                                               for e in ent[uid] for x in [g.get(c) or "\0",
                                                                          h.get(c) or "\0"]
                                               if x in header),
                    })
        per_table.append(rec)

        # 注入级正确性/吸收翻转（全注入表头）
        g = greedy_map(inj_header, canonicals, mp)
        h, _ = hungarian_map(inj_header, canonicals, mp)
        for e in sorted(ent[uid], key=lambda x: x["col"]):
            tc = next((c for c in canonicals
                       if mp.normalize_header(c) == mp.normalize_header(e["original"])), None)
            g_ok = tc is not None and g.get(tc) == e["injected"]
            h_ok = tc is not None and h.get(tc) == e["injected"]
            row = {"uid": uid, "col": e["col"], "type": e["type"],
                   "original": e["original"], "injected": e["injected"], "canonical": tc,
                   "greedy_absorbed": g_ok, "hungarian_absorbed": h_ok,
                   "greedy_correct": g_ok, "hungarian_correct": h_ok,
                   "flip": g_ok != h_ok}
            inj_diff.append(row)
            # 打分层证据（在注入表头上算）: 漂移串是否"以正分被接受"且无更高分竞争列
            sc_true = pair_score(e["injected"], tc, mp) if tc else (0, 0)
            rivals = [pair_score(h, tc, mp) for h in inj_header
                      if h and h != e["injected"] and mp.normalize_header(h)]
            rival_best = max(rivals, key=lambda t2: encode(*t2)) if rivals else (0, 0)
            other_canons = [c for c in canonicals if c != tc]
            other_best = max([pair_score(e["injected"], c, mp) for c in other_canons],
                             key=lambda t2: encode(*t2)) if other_canons else (0, 0)
            scoring_rows.append({
                "uid": uid, "col": e["col"], "type": e["type"],
                "injected": e["injected"], "canonical": tc,
                "score_on_true_canonical": list(sc_true),
                "n_rival_columns": len([r for r in rivals if r[0] > 0]),
                "best_rival_column_score": list(rival_best),
                "best_other_canonical_score_for_this_column": list(other_best),
                "drift_accepted": sc_true[0] > 0,
                "no_higher_scoring_rival": encode(*sc_true) >= encode(*rival_best),
                "no_better_alternative_field": encode(*sc_true) >= encode(*other_best),
                "greedy_absorbed": g_ok, "hungarian_absorbed": h_ok,
            })
            if row["flip"]:
                audit.append({"uid": uid, "level": "injection", "col": e["col"],
                              "type": e["type"], "original": e["original"],
                              "injected": e["injected"], "canonical": tc,
                              "greedy_absorbed": g_ok, "hungarian_absorbed": h_ok})

    ocr_rows = [r for r in scoring_rows if r["type"] == "ocr_similar"]
    tier_hist: dict[str, int] = {}
    for r in ocr_rows:
        tier_hist[str(r["score_on_true_canonical"][0])] = \
            tier_hist.get(str(r["score_on_true_canonical"][0]), 0) + 1
    scoring_summary = {
        "definition": "竞争可否由分配层消解 = 在注入表头上, 漂移列对真值 canonical 的打分是否不劣于"
                      "任何竞争列（若有列打分更高, 全局分配可把 canonical 让给该列而消掉吸收）;"
                      " 全部比较在注入表头上做, 不含 original 文本（孪生原文不在注入表头中）",
        "ocr_similar": {
            "n": len(ocr_rows),
            "drift_accepted_with_positive_score": sum(1 for r in ocr_rows if r["drift_accepted"]),
            "no_higher_scoring_rival": sum(1 for r in ocr_rows
                                           if r["drift_accepted"] and r["no_higher_scoring_rival"]),
            "assignment_layer_could_unabsorb": sum(1 for r in ocr_rows
                                                   if not r["no_higher_scoring_rival"]),
            "score_tier_hist_on_true_canonical": tier_hist},
        "all_types": {
            "n": len(scoring_rows),
            "absorbed": sum(1 for r in scoring_rows if r["greedy_absorbed"]),
            "absorbed_and_no_higher_rival": sum(1 for r in scoring_rows
                                                if r["greedy_absorbed"]
                                                and r["no_higher_scoring_rival"])},
        "mechanism_claim": "打分层污染 = 形近串在真值 canonical 上获得正分（tier 1, 编辑距离<=1 兜底）"
                           "且无更高分竞争列 -> 吸收是打分层给出的『无异常』结论, 换任何分配策略都同样命中",
        "rows": scoring_rows}

    n_t = len(per_table)
    diff_tables = {"orig": [t["uid"] for t in per_table if t["diff_orig_cols"]],
                   "inj": [t["uid"] for t in per_table if t["diff_inj_cols"]]}
    diff_cols = {"orig": sum(len(t["diff_orig_cols"]) for t in per_table),
                 "inj": sum(len(t["diff_inj_cols"]) for t in per_table)}
    weight_gain = {"orig": sum(t["weight_orig_hung"] - t["weight_orig_greedy"] for t in per_table),
                   "inj": sum(t["weight_inj_hung"] - t["weight_inj_greedy"] for t in per_table)}
    flips = [r for r in inj_diff if r["flip"]]

    def vis_stats(flag: str) -> dict:
        by_type: dict[str, dict] = {}
        for r in inj_diff:
            e = by_type.setdefault(r["type"], {"n": 0, "visible": 0})
            e["n"] += 1
            if not r[flag]:
                e["visible"] += 1
        for e in by_type.values():
            e["visibility_rate"] = round(e["visible"] / e["n"], 4)
        rates = [e["visibility_rate"] for e in by_type.values()]
        return {"by_type": {k: by_type[k] for k in sorted(by_type)},
                "type_range": round(max(rates) - min(rates), 4),
                "ocr_similar_visible": by_type.get("ocr_similar", {}).get("visible"),
                "n_absorbed_total": sum(r["n"] - r["visible"] for r in by_type.values())}

    table_disc = {
        "greedy": sum(1 for t in per_table
                      if round((t["h_orig_greedy"] - t["h_inj_greedy"]) * 10, 4) >= 2.0),
        "hungarian": sum(1 for t in per_table
                         if round((t["h_orig_hung"] - t["h_inj_hung"]) * 10, 4) >= 2.0)}
    # 贪心臂与冻结工件对账（G4 之一）
    fz = {t["uid"]: t for t in frozen["tables"]}
    fz_inj = {(t["uid"], i["col"]): i for t in frozen["tables"] for i in t["injections"]}
    tab_mismatch = [t["uid"] for t in per_table
                    if abs(fz[t["uid"]]["drop10"]
                           - round((t["h_orig_greedy"] - t["h_inj_greedy"]) * 10, 4)) > 1e-9
                    or fz[t["uid"]]["discriminated"]
                    != (round((t["h_orig_greedy"] - t["h_inj_greedy"]) * 10, 4) >= 2.0)]
    inj_mismatch = [[r["uid"], r["col"]] for r in inj_diff
                    if fz_inj.get((r["uid"], r["col"]), {}).get("absorbed") != r["greedy_absorbed"]]
    return {"tables": per_table, "injections": inj_diff,
            "n_tables": n_t, "n_injections": len(inj_diff),
            "assignment_diff_tables": diff_tables, "assignment_diff_cols": diff_cols,
            "hungarian_minus_greedy_weight": weight_gain,
            "greedy_globally_optimal_tables": sum(
                1 for t in per_table
                if t["weight_orig_hung"] == t["weight_orig_greedy"]
                and t["weight_inj_hung"] == t["weight_inj_greedy"]),
            "table_level_discriminated": table_disc,
            "visibility_greedy": vis_stats("greedy_absorbed"),
            "visibility_hungarian": vis_stats("hungarian_absorbed"),
            "injection_flips": flips,
            "flip_count_by_type": {t: len([r for r in flips if r["type"] == t])
                                   for t in sorted({r["type"] for r in flips})},
            "ocr_similar_flip_count": len([r for r in flips if r["type"] == "ocr_similar"]),
            "audit_list": audit,
            "scoring_layer_evidence": scoring_summary,
            "frozen_reproduction": {
                "tables_discriminated_greedy": table_disc["greedy"],
                "tables_discriminated_frozen":
                    frozen["properties"]["discrimination"]["tables_discriminated"],
                "table_level_mismatches": tab_mismatch,
                "injection_level_mismatches": inj_mismatch,
                "by_type_greedy": vis_stats("greedy_absorbed")["by_type"],
                "by_type_frozen": {k: {"n_injections": v["n_injections"],
                                       "n_visible": v["n_visible"],
                                       "n_absorbed": v["n_absorbed"]}
                                   for k, v in frozen["by_type"].items()},
                "pass": (table_disc["greedy"]
                         == frozen["properties"]["discrimination"]["tables_discriminated"]
                         and not tab_mismatch and not inj_mismatch)}}


# ---------------------------------------------------------------- E5.2
def run_e5_2() -> dict:
    vg = load_module("vgmc_exp1_t6", REPO / "research" / "vgmc_exp1.py")
    overlay = json.loads((EVAL / "vgmc_collision_overlay.json").read_text(encoding="utf-8"))
    corpus_plain = vg.load_corpus()
    corpus_ovl = vg.load_corpus(overlay)
    _fix, meas = vg.split_uids(list(corpus_plain.keys()))

    def oracle_rules(corpus):
        r: dict[str, list[str]] = {}
        for _uid, rec in corpus.items():
            for e in rec["entries"]:
                tc = next((c for c in rec["canonicals"]
                           if vg.mp.normalize_header(c) == vg.mp.normalize_header(e["original"])),
                          None)
                if tc:
                    r.setdefault(tc, [])
                    hh = rec["inj_header"][e["col"]]
                    if hh not in r[tc]:
                        r[tc].append(hh)
        return r

    def per_table_correctness(corpus, uids, rules):
        out = {}
        for uid in uids:
            rec = corpus[uid]
            if not rec["entries"]:
                continue
            mapping, _ = vg.mp.map_headers(rec["inj_header"],
                                           vg.schema_table_for(rec, rules))
            rev = {src: std for std, src in mapping.items()}
            n = ok = 0
            for e in rec["entries"]:
                n += 1
                tc = next((c for c in rec["canonicals"]
                           if vg.mp.normalize_header(c) == vg.mp.normalize_header(e["original"])),
                          None)
                if rev.get(rec["inj_header"][e["col"]]) == tc:
                    ok += 1
            out[uid] = (ok, n)
        return out

    recomputed = {}
    for tag, corpus in (("plain", corpus_plain), ("overlay", corpus_ovl)):
        orc = oracle_rules(corpus)
        h_orc = vg.pool_h(meas, corpus, orc)
        h_base = vg.pool_h(meas, corpus, {})
        corr = per_table_correctness(corpus, meas, orc)
        ok = sum(v[0] for v in corr.values())
        tot = sum(v[1] for v in corr.values())
        recomputed[tag] = {"h_oracle_meas": round(h_orc, 6),
                           "h_baseline_meas": round(h_base, 6),
                           "acc_oracle_meas": round(ok / tot, 6) if tot else None,
                           "n_correct": ok, "n_injections": tot,
                           "n_meas_tables": len(meas)}
    art = json.loads(P1_ART.read_text(encoding="utf-8"))
    errs, pass_all = {}, True
    for tag in recomputed:
        f = art["headroom"][tag]
        r = recomputed[tag]
        errs[tag] = {k: round(abs(r[k] - f[k]), 9) for k in
                     ("acc_oracle_meas", "h_oracle_meas", "h_baseline_meas")}
        errs[tag]["acc_expected_frozen_design"] = ORACLE_EXPECTED[tag]["acc_oracle_meas"]
        errs[tag]["acc_vs_design_doc_err"] = round(
            abs(r["acc_oracle_meas"] - ORACLE_EXPECTED[tag]["acc_oracle_meas"]), 9)
        if errs[tag]["acc_oracle_meas"] >= 1e-6 or errs[tag]["h_baseline_meas"] >= 1e-6:
            pass_all = False
    return {"recomputed": recomputed, "frozen_artifact": art["headroom"],
            "abs_err_vs_artifact": errs,
            "scope_note": "天花板数字属 VGMC 碰撞语料口径（overlay 185 注入列 / plain 118 注入）, "
                          "与 95 表 plain 语料分列报告, 不混同（设计稿 3.2 范围声明）",
            "oracle_rule_definition": "真值别名全注入规则库（每条注入的 original 文本作为其 canonical 的同义词）",
            "mechanism": "overlay 共享表头下同一 canonical 的多个变体争唯一槽位, 真值规则全在时"
                         "正确性上限仍被列间竞争压缩（0.597 << plain 0.952）; 门控只拦增量伤害, 不解决存量竞争",
            "pass": pass_all}


# ---------------------------------------------------------------- 判据与主流程
def main() -> int:
    _install_network_guard()
    t0 = time.time()
    sys.path.insert(0, str(REPO / "scripts"))
    import m1_statement_parser as mp  # noqa: E402  只读导入生产匹配器
    frozen = json.loads(TABLES_FROZEN.read_text(encoding="utf-8"))

    e51 = run_e5_1(mp, frozen)
    e52 = run_e5_2()
    solver = solver_validation()
    rep = e51["frozen_reproduction"]

    n_diff_cols = e51["assignment_diff_cols"]["orig"] + e51["assignment_diff_cols"]["inj"]
    branch = ("a" if n_diff_cols == 0 and not e51["injection_flips"]
              else ("b" if e51["injection_flips"] or
                    abs(e51["table_level_discriminated"]["hungarian"]
                        - e51["table_level_discriminated"]["greedy"]) > 2
                    else "a_partial"))
    v_g = e51["visibility_greedy"]
    v_h = e51["visibility_hungarian"]
    d_range = round(abs(v_h["type_range"] - v_g["type_range"]), 4)
    d_disc = abs(e51["table_level_discriminated"]["hungarian"]
                 - e51["table_level_discriminated"]["greedy"])
    if (v_h["ocr_similar_visible"] == 0 and d_range <= 0.10 and d_disc <= 2):
        impact = "无实质改变"
    elif v_h["ocr_similar_visible"] >= 3 or v_h["type_range"] <= 0.5 * v_g["type_range"]:
        impact = "需降级"
    else:
        impact = "限定条件下成立"
    prereg = {
        "P1_branch": {
            "branch": branch,
            "assignment_diff_tables": {k: len(v) for k, v in
                                       e51["assignment_diff_tables"].items()},
            "assignment_diff_cols": e51["assignment_diff_cols"],
            "hungarian_minus_greedy_weight": e51["hungarian_minus_greedy_weight"],
            "greedy_globally_optimal_tables": e51["greedy_globally_optimal_tables"],
            "n_injection_flips": len(e51["injection_flips"]),
            "conclusion": ("贪心在该打分层级下已全局最优（分配零差异）-> 匹配竞争不可由分配层消解, "
                           "根因在打分层污染（形近串获得与真值同档打分）"
                           if branch == "a" else
                           "分配层存在可改进空间 -> 报告 Hungarian 带来的正确性增量与吸收翻转清单, "
                           "C1 可见性谱加匹配器次优性注记（分支 b）"
                           if branch == "b" else
                           "分配存在列级差异但不改变任何注入级吸收/可见判定（分支 a_partial）"
                           "-> 竞争在打分层而非分配层显现: 重排发生在等权变体之间, 判定不变"),
        },
        "P2_ocr_similar_flips": {
            "n_ocr_injections": v_g["by_type"]["ocr_similar"]["n"],
            "flip_count": e51["ocr_similar_flip_count"],
            "flip_list": [r for r in e51["injection_flips"] if r["type"] == "ocr_similar"],
            "hungarian_ocr_visible": v_h["ocr_similar_visible"],
            "greedy_ocr_visible": v_g["ocr_similar_visible"],
            "predicted": "多数不翻转（形近串对真值字段的打分不低于竞争字段）",
            "holds": e51["ocr_similar_flip_count"] * 2 <= v_g["by_type"]["ocr_similar"]["n"]},
        "P3_impact_scope": {
            "decision_rule_written_before_run": IMPACT_RULE,
            "ocr_similar_visible_hungarian": v_h["ocr_similar_visible"],
            "type_range_greedy": v_g["type_range"], "type_range_hungarian": v_h["type_range"],
            "type_range_delta": d_range,
            "table_level_discriminated": e51["table_level_discriminated"],
            "table_level_discriminated_delta": d_disc,
            "verdict": impact},
    }
    payload = {
        "meta": {
            "name": "t6-matching-competition", "version": "v1",
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "script": str(Path(__file__).relative_to(REPO)),
            "design_doc": "docs/experiments/2026-08-30_t6_matching_competition_design.md",
            "task_card": "docs/experiments/2026-08-30_w1_window_card_t1t2t6.md",
            "seed": SEED, "endpoint_calls": 0,
            "edge_weight_encoding": "score*100 + min(syn_len, 99)",
            "arms": ["greedy=map_headers（生产原样）", "hungarian=自实现 O(n^3) 最大权完备分配"],
            "runs": "95 表 x 2 臂 x 2 头 = 380 次分配 + 118 注入级判定双臂",
            "inputs": [str(DRIFT.relative_to(REPO)) + "/{injected_tables,injection_map}.json",
                       str(TABLES_FROZEN.relative_to(REPO)), str(P1_ART.relative_to(REPO))],
            "runtime_s": round(time.time() - t0, 2),
        },
        "gates": {
            "g4_greedy_arm_tables": f"{rep['tables_discriminated_greedy']}/{e51['n_tables']}",
            "g4_greedy_arm_frozen": f"{rep['tables_discriminated_frozen']}/{e51['n_tables']}",
            "g4_table_mismatches": rep["table_level_mismatches"],
            "g4_injection_mismatches": rep["injection_level_mismatches"],
            "g4_greedy_arm_pass": rep["pass"],
            "solver_global_optimality_exact": solver["bruteforce_exact"],
            "solver_positive_control_ok": solver["positive_control_detects_improvement"],
            "g4_oracle_plain": e52["recomputed"]["plain"]["acc_oracle_meas"],
            "g4_oracle_overlay": e52["recomputed"]["overlay"]["acc_oracle_meas"],
            "g4_oracle_plain_err": e52["abs_err_vs_artifact"]["plain"]["acc_vs_design_doc_err"],
            "g4_oracle_overlay_err": e52["abs_err_vs_artifact"]["overlay"]["acc_vs_design_doc_err"],
            "g4_oracle_pass": e52["pass"],
            "all_pass": bool(rep["pass"] and e52["pass"] and solver["bruteforce_exact"]
                             and solver["positive_control_detects_improvement"]),
            "numbering_note": "任务卡 G4 = 本工件 g4_*; 设计稿 T6 §4 的 G1/G2 即 g4_greedy_arm / g4_oracle",
        },
        "solver_validation": solver,
        "e5_1_arm_comparison": {k: v for k, v in e51.items() if k != "tables"},
        "e5_2_oracle_reproduction": e52,
        "prereg_predicates": prereg,
        "tables": e51["tables"],
        "zero_endpoint": self_source_scan(),
    }
    body = json.dumps({k: payload[k] for k in SHA_SCOPE}, ensure_ascii=False, sort_keys=True)
    payload["payload_sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    payload["sha256_scope"] = SHA_SCOPE
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"gates": payload["gates"], "branch": prereg["P1_branch"]["branch"],
                      "impact": impact, "diff_cols": e51["assignment_diff_cols"],
                      "flips": len(e51["injection_flips"]),
                      "payload_sha256": payload["payload_sha256"],
                      "zero_endpoint_clean": payload["zero_endpoint"]["clean"]},
                     ensure_ascii=False, indent=1))
    return 0 if payload["gates"]["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
