#!/usr/bin/env python3
"""T2 缺陷可见性敏感性（Phase 2 E2.1-E2.3, 零端点）。

设计稿（判据冻结）: docs/experiments/2026-08-30_t2_visibility_sensitivity_design.md

E2.1 gamma 阈值网格（单注入边际降幅 dH, 五档 gamma; 表级配套 drop10 >= 10*gamma）
E2.2 等价变异标记与校正（语义等价三类, 从可见性分母剔除后重算）
E2.3 强度梯度 W / S / S'（全部由冻结注入映射确定性派生, 无新随机源）

纯 stdlib + 生产匹配器只读导入; 运行时硬断言零网络。
复算: PYTHONPATH=src python research/paper_t2_visibility_sensitivity.py
输出: logs/graph/eval/t2_visibility_sensitivity.json
"""
from __future__ import annotations

import hashlib
import json
import random
import socket
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
DRIFT = REPO / "data" / "research" / "drift_v0" / "output"
TABLES_FROZEN = EVAL / "checkpoint_discrimination_tables_v2.json"
OUT = EVAL / "t2_visibility_sensitivity.json"

SEED = 20260830
GAMMAS = (0.2, 0.3, 0.5, 0.7, 0.9)
GAMMA_ANCHOR = 0.2          # = 冻结判据 2.0/10 的锚点（设计稿 3.1）
EQUIV_TYPES = ("alias_variant", "mixed_lang", "prefix_noise")
SEMANTIC_TYPES = ("ocr_similar", "date_variant", "unit_suffix")
SHA_SCOPE = ["gates", "e2_1_gamma_grid", "e2_2_equivalence_correction",
             "e2_3_strength_gradient", "prereg_predicates", "tables", "injections",
             "zero_endpoint"]


# ---------------------------------------------------------------- 零端点护栏
def _install_network_guard() -> None:
    """socket 层封死; 用子类替换以保证导入期 `class SSLSocket(socket)` 仍合法。"""
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


# ---------------------------------------------------------------- 语料与匹配
def load_corpus(mp):
    tables = json.loads((DRIFT / "injected_tables.json").read_text(encoding="utf-8"))
    imap = json.loads((DRIFT / "injection_map.json").read_text(encoding="utf-8"))
    by_uid = {t["uid"]: t["table"] for t in tables}
    ent: dict[str, list[dict]] = {}
    for e in imap["mapping"]:
        ent.setdefault(e["uid"], []).append(e)
    return by_uid, ent


def unique_canonical(header: list[str], mp) -> list[str]:
    seen, out = set(), []
    for h in header:
        k = mp.normalize_header(h)
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(str(h))
    return out


def map_header(header: list[str], canonicals: list[str], mp):
    fields = [mp.SchemaField(std, [std]) for std in canonicals]
    st = mp.SchemaTable(table_name="t2", layout="grid",
                        header_region_keywords=[], fields=fields)
    mapping, _unmapped = mp.map_headers(header, st)
    return mapping


def _tier_for(header: str, canonical: str | None, mp) -> int:
    """匹配器吸收档位: 4/3 精确, 2 归一化包含, 1 编辑距离<=1, 0 未命中（吸收区 = >=1）。"""
    if not canonical:
        return 0
    best = mp._best_field_for_header(mp.normalize_header(header),
                                    [mp.SchemaField(canonical, [canonical])])
    return best[0] if best else 0


def h_rate(header: list[str], canonicals: list[str], mp) -> tuple[float, dict]:
    n = len(canonicals)
    mapping = map_header(header, canonicals, mp)
    return (len(mapping) / n if n else 1.0), mapping


def strength_variants(original: str, injected: str, typ: str, mp) -> dict:
    """E2.3 强度档构造（确定性, 无随机源）。

    W 档（五类）: original + "(" + injected + ")" —— 保留原件子串的括号追加式。
    S 档: 冻结 v0 注入原样。
    S' 档（仅 ocr_similar）: 在 S 相对 original 的首个差异位点邻接重复一字符
      （编辑距离 2, 击穿匹配器 <=1 兜底）。工作在归一化域上做, 结果仍为合法表头串。
    """
    out: dict = {"S": injected}
    meta: dict = {}
    if typ != "ocr_similar":
        out["W"] = f"{original}({injected})"
    else:
        a, b = mp.normalize_header(original), mp.normalize_header(injected)
        i = 0
        while i < min(len(a), len(b)) and a[i] == b[i]:
            i += 1
        sp = b[:i + 1] + b[i] + b[i + 1:] if i < len(b) else b + (b[-1] if b else "?")
        out["S_PRIME"] = sp
        meta = {"first_diff_pos": i,
                "lev_S": mp.edit_distance(a, b),
                "lev_S_PRIME": mp.edit_distance(a, sp)}
    return {"arms": out, "meta": meta}


# ---------------------------------------------------------------- 主计算
def compute(mp) -> dict:
    by_uid, ent = load_corpus(mp)
    injections: list[dict] = []
    tables: list[dict] = []

    for uid in sorted(ent):
        inj_header = [str(c) if c is not None else "" for c in by_uid[uid][0]]
        orig_header = list(inj_header)
        for e in ent[uid]:
            orig_header[e["col"]] = e["original"]
        canonicals = unique_canonical(orig_header, mp)
        h_orig, map_orig = h_rate(orig_header, canonicals, mp)
        h_inj, map_inj = h_rate(inj_header, canonicals, mp)
        drop10_full = round((h_orig - h_inj) * 10.0, 4)
        # 冻结口径的注入级 absorbed（全注入并表, 与 k2 v2 同流）
        map_full_for_abs = map_inj
        rows = []
        for e in sorted(ent[uid], key=lambda x: x["col"]):
            single = list(orig_header)
            single[e["col"]] = e["injected"]
            h_s, map_s = h_rate(single, canonicals, mp)
            dH = round((h_orig - h_s) * 10.0, 4) / 10.0
            target_c = next((c for c in canonicals
                             if mp.normalize_header(c) == mp.normalize_header(e["original"])), None)
            absorbed_single = target_c is not None and map_s.get(target_c) == e["injected"]
            absorbed_full = target_c is not None and map_full_for_abs.get(target_c) == e["injected"]
            # E2.2 行为等价: 映射的标准字段集完全一致（文本层 mapping==mapping_orig 另计）
            keys_same = set(map_inj) == set(map_orig)
            text_same = map_inj == map_orig
            equiv_candidate = (e["type"] in EQUIV_TYPES) and keys_same
            # E2.3 强度档
            sv = strength_variants(e["original"], e["injected"], e["type"], mp)
            grad = dict(sv["meta"])
            for arm, text in sv["arms"].items():
                hdr = list(orig_header)
                hdr[e["col"]] = text
                h_v, map_v = h_rate(hdr, canonicals, mp)
                absorbed_v = bool(target_c) and map_v.get(target_c) == text
                grad[arm] = {
                    "header": text, "absorbed": absorbed_v, "visible": not absorbed_v,
                    "dH": round(h_orig - h_v, 6),
                    "drop10": round((h_orig - h_v) * 10.0, 4),
                    "match_tier": _tier_for(hdr[e["col"]], target_c, mp),
                }
            rec = {
                "uid": uid, "col": e["col"], "type": e["type"],
                "original": e["original"], "injected": e["injected"],
                "canonical": target_c, "n_canonical": len(canonicals),
                "n_columns_same_norm_as_canonical": (
                    0 if target_c is None else
                    sum(1 for h in orig_header
                        if mp.normalize_header(h) == mp.normalize_header(target_c))),
                "h_orig": round(h_orig, 6), "h_single": round(h_s, 6),
                "dH": round(dH, 6), "drop10": round(dH * 10.0, 4),
                "absorbed_single": absorbed_single,
                "absorbed_full_injection": absorbed_full,
                "visible_frozen": not absorbed_full,
                "mapping_keys_same_full": keys_same,
                "mapping_text_same_full": text_same,
                "equivalent_mutation": equiv_candidate,
                "visible_by_gamma": {str(g): (round(dH * 10.0, 4) >= 10 * g) for g in GAMMAS},
                "gradient": grad,
            }
            rows.append(rec)
        injections.extend(rows)
        tables.append({
            "uid": uid, "n_canonical": len(canonicals),
            "n_injections": len(rows), "h_orig": round(h_orig, 6),
            "h_inj": round(h_inj, 6), "drop10": drop10_full,
            "discriminated": drop10_full >= 2.0,
            "detected_by_gamma": {str(g): drop10_full >= 10 * g for g in GAMMAS},
            "types": sorted({r["type"] for r in rows}),
        })

    types = sorted({i["type"] for i in injections})
    n_inj, n_tab = len(injections), len(tables)

    # ---- E2.1 gamma 网格
    grid = {}
    for g in GAMMAS:
        per_type = {}
        for t in types:
            its = [i for i in injections if i["type"] == t]
            nv = sum(1 for i in its if i["visible_by_gamma"][str(g)])
            per_type[t] = {"n": len(its), "visible": nv,
                           "visibility_rate": round(nv / len(its), 4)}
        rates = [v["visibility_rate"] for v in per_type.values()]
        tab_det = sum(1 for t in tables if t["detected_by_gamma"][str(g)])
        grid[str(g)] = {
            "role": "anchor_2.0/10" if g == GAMMA_ANCHOR else "preregistered grid point",
            "by_type": per_type,
            "type_range": round(max(rates) - min(rates), 4),
            "ocr_similar_visibility": per_type.get("ocr_similar", {}).get("visibility_rate"),
            "table_level_detected": tab_det, "table_level_rate": round(tab_det / n_tab, 4),
            "absorption_based_by_type": {
                t: {"n": len([i for i in injections if i["type"] == t]),
                    "visible": sum(1 for i in injections
                                   if i["type"] == t and i["visible_frozen"]),
                    "visibility_rate": round(
                        sum(1 for i in injections if i["type"] == t and i["visible_frozen"])
                        / max(len([i for i in injections if i["type"] == t]), 1), 4)}
                for t in types},
        }

    # ---- E2.2 等价变异校正
    equiv = [i for i in injections if i["equivalent_mutation"]]
    by_type_equiv = {}
    for t in EQUIV_TYPES:
        its = [i for i in injections if i["type"] == t]
        ev = [i for i in its if i["equivalent_mutation"]]
        by_type_equiv[t] = {"n": len(its), "n_equivalent": len(ev),
                            "n_absorbed": sum(1 for i in its if i["absorbed_full_injection"])}
    corrected = {}
    for g in GAMMAS:
        per_type = {}
        for t in types:
            its = [i for i in injections if i["type"] == t and not i["equivalent_mutation"]]
            nv = sum(1 for i in its if i["visible_by_gamma"][str(g)])
            per_type[t] = {"n_after_correction": len(its), "visible": nv,
                           "visibility_rate": round(nv / len(its), 4) if its else None}
        rates = [v["visibility_rate"] for v in per_type.values() if v["visibility_rate"] is not None]
        corrected[str(g)] = {"by_type": per_type,
                             "type_range": round(max(rates) - min(rates), 4) if rates else None}
    corr_abs_based = {}
    for t in types:
        its = [i for i in injections if i["type"] == t and not i["equivalent_mutation"]]
        nv = sum(1 for i in its if i["visible_frozen"])
        corr_abs_based[t] = {"n_after_correction": len(its), "visible": nv,
                             "visibility_rate": round(nv / len(its), 4) if its else None}
    e2_2 = {
        "definition": "等价变异 = 全注入表头的映射标准字段集与原始完全一致 且 类型属 "
                      "{alias_variant, mixed_lang, prefix_noise}（设计稿 3.2 语义等价类）",
        "mechanical_note": "冻结工件 locality_clean=95/95, 故 absorbed(全注入) <=> 标准字段集不变; "
                           "文本层 mapping_inj == mapping_orig 恒不成立（吸收即映射值换为注入文本）, "
                           "故按行为等价（字段集）口径机械执行, 两种口径的计数同时入工件",
        "n_equivalent": len(equiv),
        "by_type": by_type_equiv,
        "equivalent_list": [{"uid": i["uid"], "col": i["col"], "type": i["type"],
                             "original": i["original"], "injected": i["injected"]} for i in equiv],
        "n_mapping_text_identical": sum(1 for i in injections if i["mapping_text_same_full"]),
        "n_mapping_keyset_identical": sum(1 for i in injections if i["mapping_keys_same_full"]),
        "corrected_visibility_by_gamma": corrected,
        "corrected_absorption_based_by_type": corr_abs_based,
    }

    # ---- E2.3 强度梯度
    s_prime_rows = [
        {"uid": i["uid"], "col": i["col"], "original": i["original"], "S": i["injected"],
         "S_visible": i["gradient"]["S"]["visible"], "S_tier": i["gradient"]["S"]["match_tier"],
         "S_PRIME": i["gradient"]["S_PRIME"]["header"],
         "S_PRIME_visible": i["gradient"]["S_PRIME"]["visible"],
         "S_PRIME_tier": i["gradient"]["S_PRIME"]["match_tier"],
         "lev_S": i["gradient"].get("lev_S"), "lev_S_PRIME": i["gradient"].get("lev_S_PRIME"),
         "first_diff_pos": i["gradient"].get("first_diff_pos")}
        for i in injections if i["type"] == "ocr_similar"]
    grad = {}
    violations = []
    for t in types:
        its = [i for i in injections if i["type"] == t]
        arms = {}
        for arm in ("W", "S", "S_PRIME"):
            rows = [i for i in its if arm in i["gradient"]]
            if not rows:
                continue
            nv = sum(1 for i in rows if i["gradient"][arm]["visible"])
            arms[arm] = {"n": len(rows), "visible": nv,
                         "visibility_rate": round(nv / len(rows), 4),
                         "mean_dH": round(sum(i["gradient"][arm]["dH"] for i in rows) / len(rows), 6),
                         "examples": [{"uid": i["uid"], "col": i["col"], "original": i["original"],
                                       "variant_header": i["gradient"][arm]["header"],
                                       "match_tier": i["gradient"][arm]["match_tier"],
                                       "dH": i["gradient"][arm]["dH"],
                                       "n_columns_same_norm_as_canonical":
                                           i["n_columns_same_norm_as_canonical"],
                                       "visible": i["gradient"][arm]["visible"]}
                                      for i in (rows if arm != "W"
                                                else [r for r in rows if r["gradient"]["W"]["visible"]])[:5]]}
        if "W" in arms and "S" in arms and arms["W"]["visibility_rate"] > arms["S"]["visibility_rate"]:
            violations.append({"type": t, "rule": "W <= S", "W": arms["W"]["visibility_rate"],
                               "S": arms["S"]["visibility_rate"]})
        if t == "ocr_similar" and "S" in arms and "S_PRIME" in arms \
                and arms["S_PRIME"]["visible"] < arms["S"]["visible"]:
            violations.append({"type": t, "rule": "S <= S_PRIME", "S": arms["S"]["visible"],
                               "S_PRIME": arms["S_PRIME"]["visible"]})
        grad[t] = arms
    e2_3 = {"by_type": grad, "monotonicity_violations": violations,
            "criterion": "可见 = 该档表头不再被映射回其真值 canonical（吸收判据, 无阈值; "
                         "机制锚 = 精确 并 归一化包含 并 编辑距离<=1 的吸收区）",
            "ocr_s_prime_construction": "在归一化域取 S 相对 original 的首个差异位点, 重复该位字符"
                                        "（编辑距离 1 -> 2, 击穿 <=1 兜底）",
            "s_prime_detail": s_prime_rows,
            "s_prime_lev_dist": sorted({i["gradient"].get("lev_S_PRIME")
                                        for i in injections if i["type"] == "ocr_similar"}),
            "s_prime_lev_visible_crosstab": {
                f"lev_S_PRIME={lev}": {
                    "n": len([r for r in s_prime_rows if r["lev_S_PRIME"] == lev]),
                    "n_visible": len([r for r in s_prime_rows
                                      if r["lev_S_PRIME"] == lev and r["S_PRIME_visible"]]),
                    "all_visible": all(r["S_PRIME_visible"] for r in s_prime_rows
                                       if r["lev_S_PRIME"] == lev)}
                for lev in sorted({r["lev_S_PRIME"] for r in s_prime_rows})},
            "mechanism_verdict": (
                "吸收区边界 = 编辑距离 <=1 的机制预测在 S' 臂 100% 成立"
                if all(r["S_PRIME_visible"] == (r["lev_S_PRIME"] >= 2) for r in s_prime_rows)
                else "吸收区边界机制预测在 S' 臂有反例, 见 s_prime_detail 逐条")}
    return {"injections": injections, "tables": tables, "types": types,
            "n_tables": n_tab, "n_injections": n_inj,
            "e2_1": grid, "e2_2": e2_2, "e2_3": e2_3}


def frozen_reproduction_gate(res: dict, frozen: dict) -> dict:
    fz_tab = {t["uid"]: t for t in frozen["tables"]}
    fz_inj = {(t["uid"], i["col"]): i for t in frozen["tables"] for i in t["injections"]}
    tab_mismatch, inj_mismatch = [], []
    for t in res["tables"]:
        f = fz_tab.get(t["uid"])
        if f is None or abs(f["drop10"] - t["drop10"]) > 1e-9 or f["discriminated"] != t["discriminated"]:
            tab_mismatch.append(t["uid"])
    for i in res["injections"]:
        f = fz_inj.get((i["uid"], i["col"]))
        if f is None or f["absorbed"] != i["absorbed_full_injection"] or f["type"] != i["type"]:
            inj_mismatch.append([i["uid"], i["col"]])
    n_disc = sum(1 for t in res["tables"] if t["discriminated"])
    recomputed = {t: {"n_injections": len([i for i in res["injections"] if i["type"] == t]),
                      "n_visible": len([i for i in res["injections"]
                                        if i["type"] == t and i["visible_frozen"]]),
                      "n_absorbed": len([i for i in res["injections"]
                                         if i["type"] == t and i["absorbed_full_injection"]])}
                  for t in res["types"]}
    frozen_bt = {t: {"n_injections": v["n_injections"], "n_visible": v["n_visible"],
                     "n_absorbed": v["n_absorbed"]} for t, v in frozen["by_type"].items()}
    by_type_err = sum(abs(recomputed[t][k] - frozen_bt[t][k])
                      for t in recomputed for k in recomputed[t] if t in frozen_bt)
    return {"tables_discriminated_recomputed": n_disc,
            "tables_discriminated_frozen": frozen["properties"]["discrimination"]["tables_discriminated"],
            "n_tables": len(res["tables"]),
            "table_level_mismatches": tab_mismatch,
            "injection_level_mismatches": inj_mismatch,
            "by_type_recomputed": recomputed, "by_type_frozen": frozen_bt,
            "by_type_total_count_error": by_type_err,
            "pass": (n_disc == frozen["properties"]["discrimination"]["tables_discriminated"]
                     and not tab_mismatch and not inj_mismatch and by_type_err == 0)}


def main() -> int:
    _install_network_guard()
    t0 = time.time()
    sys.path.insert(0, str(REPO / "scripts"))
    import m1_statement_parser as mp  # noqa: E402  只读导入生产匹配器
    frozen = json.loads(TABLES_FROZEN.read_text(encoding="utf-8"))

    res_a = compute(mp)
    res_b = compute(mp)      # 确定性门: 同输入双跑
    double_run_identical = json.dumps(
        {k: res_a[k] for k in ("injections", "tables")}, sort_keys=True,
        ensure_ascii=False) == json.dumps({k: res_b[k] for k in ("injections", "tables")},
                                          sort_keys=True, ensure_ascii=False)
    g3 = frozen_reproduction_gate(res_a, frozen)

    grid = res_a["e2_1"]
    anchor = grid[str(GAMMA_ANCHOR)]
    prereg = {
        "E2_1_ocr_similar_blind_all_gamma": {
            "by_gamma": {g: grid[g]["ocr_similar_visibility"] for g in grid},
            "holds": all(v == 0.0 for v in (grid[g]["ocr_similar_visibility"] for g in grid))},
        "E2_1_type_range_ge_0p5_all_gamma_injection_level": {
            "by_gamma": {g: grid[g]["type_range"] for g in grid},
            "holds": all(grid[g]["type_range"] >= 0.5 for g in grid),
            "failing_gamma_points": [g for g in grid if grid[g]["type_range"] < 0.5],
            "holds_on_preregistered_grid_only": all(
                grid[g]["type_range"] >= 0.5 for g in grid if g != str(GAMMA_ANCHOR)),
            "note": "字面判据（全部 gamma 点极差 >=0.5）在 0.7/0.9 两点不成立: "
                    "单注入边际降幅按 1/n_canonical 量化, 多数表 n>=4 -> 单列损失 dH<=0.25, "
                    "高 gamma 只剩窄表（n_canonical<=2, dH>=0.5）与单列全失的个例; "
                    "设计稿 4.2 允许高 gamma 大幅衰减但要求排序不均匀性存续, 见下一条"},
        "E2_1_ranking_non_degenerate_all_gamma": {
            "by_gamma": {g: {"range": grid[g]["type_range"],
                             "n_types_above_floor": sum(
                                 1 for v in grid[g]["by_type"].values()
                                 if v["visibility_rate"] > grid[g]["ocr_similar_visibility"])}
                         for g in grid},
            "holds": all(grid[g]["type_range"] > 0 for g in grid)
            and all(sum(1 for v in grid[g]["by_type"].values() if v["visibility_rate"] > 0) >= 1
                    for g in grid),
            "note": "ocr_similar 在全部 gamma 点稳居 0 下界, 至少一类始终严格高于下界 -> 排序不均匀性存续"},
        "E2_1_type_range_absorption_based": {
            "by_type": anchor["absorption_based_by_type"],
            "range": round(max(v["visibility_rate"] for v in anchor["absorption_based_by_type"].values())
                           - min(v["visibility_rate"] for v in anchor["absorption_based_by_type"].values()), 4)},
        "E2_1_type_range_table_level": {
            "by_gamma": {g: grid[g]["table_level_detected"] for g in grid},
            "rates": {g: grid[g]["table_level_rate"] for g in grid}},
        "E2_2_equivalent_expected_about_7": {
            "n_equivalent": res_a["e2_2"]["n_equivalent"], "by_type": res_a["e2_2"]["by_type"],
            "ocr_blind_survives_correction": all(
                v["by_type"]["ocr_similar"]["visibility_rate"] in (0.0, None)
                for v in res_a["e2_2"]["corrected_visibility_by_gamma"].values()),
            "type_inequality_survives_correction": {
                g: res_a["e2_2"]["corrected_visibility_by_gamma"][g]["type_range"] for g in grid}},
        "E2_3_monotonicity": {
            "W_le_S_per_type": {t: {"W": a.get("W", {}).get("visibility_rate"),
                                    "S": a.get("S", {}).get("visibility_rate")}
                                for t, a in res_a["e2_3"]["by_type"].items()},
            "violations": res_a["e2_3"]["monotonicity_violations"],
            "ocr_S_visible": res_a["e2_3"]["by_type"]["ocr_similar"].get("S", {}).get("visible"),
            "ocr_S_PRIME_visible": res_a["e2_3"]["by_type"]["ocr_similar"].get("S_PRIME", {}).get("visible"),
            "predicted_S_PRIME_ge_10_of_13":
                res_a["e2_3"]["by_type"]["ocr_similar"].get("S_PRIME", {}).get("visible", 0) >= 10,
            "S_PRIME_actual_visible": res_a["e2_3"]["by_type"]["ocr_similar"]["S_PRIME"]["visible"],
            "S_PRIME_prediction_miss_attribution":
                "构造性偏差: 首差异位邻接重复字符仅在 S 为替换型损坏时把编辑距离推到 2; "
                "S 为删除/插入型时 S' 落回距离 1（实测 13 条 = 8 条距离2 + 5 条距离1）。"
                "机制判据本身无一反例: 距离==2 的 8/8 全部可见, 距离==1 的 5/5 全部被吸收, "
                "见 e2_3_strength_gradient.s_prime_lev_visible_crosstab",
            "lev2_all_visible": all(v["all_visible"] for k, v in
                                    res_a["e2_3"]["s_prime_lev_visible_crosstab"].items()
                                    if k == "lev_S_PRIME=2"),
            "absorption_region_perfectly_predicted":
                res_a["e2_3"]["mechanism_verdict"].startswith("吸收区边界 = 编辑距离 <=1")},
    }
    payload = {
        "meta": {
            "name": "t2-visibility-sensitivity", "version": "v1",
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "script": str(Path(__file__).relative_to(REPO)),
            "design_doc": "docs/experiments/2026-08-30_t2_visibility_sensitivity_design.md",
            "task_card": "docs/experiments/2026-08-30_w1_window_card_t1t2t6.md",
            "seed": SEED, "gammas": list(GAMMAS), "gamma_anchor": GAMMA_ANCHOR,
            "endpoint_calls": 0, "n_tables": res_a["n_tables"],
            "n_injections": res_a["n_injections"], "types": res_a["types"],
            "inputs": [str(DRIFT.relative_to(REPO)) + "/{injected_tables,injection_map}.json",
                       str(TABLES_FROZEN.relative_to(REPO))],
            "runtime_s": round(time.time() - t0, 2),
        },
        "gates": {
            "g3_s_arm_reproduction_tables": f"{g3['tables_discriminated_recomputed']}/{g3['n_tables']}",
            "g3_s_arm_frozen": f"{g3['tables_discriminated_frozen']}/{g3['n_tables']}",
            "g3_by_type_count_error": g3["by_type_total_count_error"],
            "g3_table_mismatches": g3["table_level_mismatches"],
            "g3_injection_mismatches": g3["injection_level_mismatches"],
            "g3_pass": g3["pass"],
            "determinism_double_run_identical": double_run_identical,
            "all_pass": bool(g3["pass"] and double_run_identical),
            "numbering_note": "任务卡 G3 = 本工件 g3_*; 设计稿 T2 §4.1 的 G1 即本门",
        },
        "g3_detail": g3,
        "e2_1_gamma_grid": res_a["e2_1"],
        "e2_2_equivalence_correction": res_a["e2_2"],
        "e2_3_strength_gradient": res_a["e2_3"],
        "prereg_predicates": prereg,
        "tables": res_a["tables"],
        "injections": res_a["injections"],
        "zero_endpoint": self_source_scan(),
    }
    body = json.dumps({k: payload[k] for k in SHA_SCOPE}, ensure_ascii=False, sort_keys=True)
    payload["payload_sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    payload["sha256_scope"] = SHA_SCOPE
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"gates": payload["gates"], "out": str(OUT),
                      "payload_sha256": payload["payload_sha256"],
                      "zero_endpoint_clean": payload["zero_endpoint"]["clean"]},
                     ensure_ascii=False, indent=1))
    return 0 if payload["gates"]["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
