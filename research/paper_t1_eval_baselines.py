#!/usr/bin/env python3
"""T1 评测基线对照（Phase 1 E1.1-E1.4, 零端点）。

设计稿（判据冻结）: docs/experiments/2026-08-30_t1_eval_baseline_comparison_design.md

臂 A = 检查点树 mutant 臂（9 mutant x 12 活叶），四协议对照:
  E1.1 end-to-end only / E1.2 flat weighted / E1.3 hierarchical expert（= 冻结协议）
  / E1.4 hierarchical + PSO
臂 B = 95 表头漂移臂（drift_v0 语料 x map_headers 纯规则），三协议 + E1.4 N/A

纯 stdlib + 仓内脚本只读导入; 运行时硬断言零网络（socket 层封死 + 自身源码扫描）。
复算: PYTHONPATH=src python research/paper_t1_eval_baselines.py
输出: logs/graph/eval/t1_eval_baseline_comparison.json
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import socket
import sys
import time
from copy import deepcopy
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
DRIFT = REPO / "data" / "research" / "drift_v0" / "output"
TREES_PATH = REPO / "config" / "eval_checkpoint_trees.json"
DISC_V2 = EVAL / "checkpoint_discrimination_report.json"
DISC_PSO_ERA = EVAL / "checkpoint_discrimination_report_20260819.json"
PSO_PATH = EVAL / "pso_weight_search_v0.json"
TABLES_FROZEN = EVAL / "checkpoint_discrimination_tables_v2.json"
AGG_REF = REPO / "scripts" / "eval_checkpoint_aggregate.py"
OUT = EVAL / "t1_eval_baseline_comparison.json"

SEED = 20260830
TAU = 2.0                    # 冻结判据（叶片量纲 0-10）
FLAT_TAU_H = 0.2             # E1.2 判据: ΔH >= 0.2（= TAU/10 同量纲锚）
N_BOOT = 2000
SHA_SCOPE = ["gates", "aggregation_isomorphism", "arm_a", "arm_a_pso_reproduction",
             "arm_b", "prereg_predicates", "zero_endpoint"]
PROTOCOLS = ("E1.1_end_to_end", "E1.2_flat", "E1.3_hier_expert", "E1.4_hier_pso")


# ---------------------------------------------------------------- 零端点护栏
def _install_network_guard() -> None:
    """socket 层封死: 任何连接尝试立即抛错（本窗红线 = 零网络零模型调用）。

    用子类而非函数替换, 保证 `class SSLSocket(socket)` 这类导入期继承仍然合法
    （urllib/ssl 在被导入的模块链里, 但本脚本永不向其发起任何调用）。
    """
    real_socket = socket.socket

    class _BlockedSocket(real_socket):  # type: ignore[misc]
        def connect(self, *args, **kwargs):
            raise RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")

        def connect_ex(self, *args, **kwargs):
            raise RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")

        def sendto(self, *args, **kwargs):
            raise RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")

    def _blocked(*_a, **_k):
        raise RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")

    socket.socket = _BlockedSocket       # type: ignore[assignment]
    socket.create_connection = _blocked  # type: ignore[assignment]
    socket.getaddrinfo = _blocked        # type: ignore[assignment]


def self_source_scan() -> dict:
    """扫描本窗脚本源码中的网络/端点模式（命中只允许出现在注释与断言字符串）。"""
    # 字面量分片拼写, 避免扫描器（与本卡 P5 的外部 grep）在模式清单自身上误报
    pats = ["url" + "open", "request" + "s.",
            "htt" + "p:" + "/" * 2, "HTT" + "PS:" + "/" * 2,
            ":" + "8004", ":" + "8005", ":" + "8006", ":" + "8007", ":" + "8008",
            ":" + "5050", "sock" + "et.connect"]
    hits = {}
    for f in sorted((REPO / "research").glob("paper_t*_*.py")):
        lines = f.read_text(encoding="utf-8").splitlines()
        found = []
        for i, ln in enumerate(lines, 1):
            code = ln.split("#", 1)[0]
            for p in pats:
                if p in code and "blocked" not in code and "ZERO_ENDPOINT" not in code:
                    found.append({"line": i, "pattern": p, "text": ln.strip()[:120]})
        if found:
            hits[f.name] = found
    return {"patterns": pats, "files_scanned": len(list((REPO / "research").glob("paper_t*_*.py"))),
            "hits_outside_comments": hits, "clean": not hits}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- Algorithm 1
def iter_nodes(node: dict):
    yield node
    for c in node.get("children", []):
        yield from iter_nodes(c)


def aggregate(trees: list[dict], leaf_scores: dict, weight_over: dict | None = None):
    """Algorithm 1（兄弟归一化自底向上加权均值）纯函数式实现。

    返回 (per_tree_root, overall_root)；overall = 根权重加权均值。
    """
    per_tree = {}
    for tree in trees:
        def dfs(node):
            ch = node.get("children", [])
            if not ch:
                return float(leaf_scores[node["id"]])
            pairs = [(dfs(c), (weight_over or {}).get(c["id"], c.get("weight", 1)))
                     for c in ch]
            wsum = sum(w for _, w in pairs) or 1.0
            return sum(s * w for s, w in pairs) / wsum
        per_tree[tree["id"]] = round(dfs(tree), 6)
    wsum = sum(t.get("weight", 1) for t in trees) or 1.0
    overall = round(sum(per_tree[t["id"]] * t.get("weight", 1) for t in trees) / wsum, 6)
    return per_tree, overall


def prune_nodes(tree: dict, drop_ids: set) -> dict:
    """按 node id 删除节点及其整个子树（内部节点 N/A 时整支摘除）。"""
    t = deepcopy(tree)

    def rec(node):
        if node["id"] in drop_ids:
            return False
        ch = node.get("children", [])
        if not ch:
            return True
        node["children"] = [c for c in ch if rec(c)]
        return bool(node["children"])
    rec(t)
    return t


def flatten_weights(tree: dict, out: dict | None = None) -> dict:
    out = {} if out is None else out
    for n in iter_nodes(tree):
        if n.get("children") and "weight" in n:
            out[n["id"]] = n["weight"]
    return out


def uniform_internal_weights(trees: list[dict]) -> dict:
    w = {}
    for t in trees:
        w.update(flatten_weights(t))
    return {k: 1 for k in w}


def isomorphism_check(trees: list[dict], leaf_scores: dict) -> dict:
    """与 scripts/eval_checkpoint_aggregate.py 的 aggregate_tree 对账（同构性校验）。

    方法: 只替换其叶分来源（_mapped_leaf_score -> 注入给定叶分），聚合逻辑原样跑。
    """
    ref = load_module("agg_ref_t1", AGG_REF)
    max_err = 0.0
    detail = {}
    for tree in trees:
        t = deepcopy(tree)

        def fake_leaf(leaf, _arts, _ls=leaf_scores):
            return float(_ls[leaf["id"]]), {"injected": True}

        ref._mapped_leaf_score = fake_leaf
        res = ref.aggregate_tree(t, {}, (5, 7, 8))
        mine, _ = aggregate([tree], leaf_scores, None)
        err = abs(res["subtree_score"] - mine[tree["id"]])
        max_err = max(max_err, err)
        detail[tree["id"]] = {"reference": res["subtree_score"], "mine": mine[tree["id"]],
                              "abs_err": round(err, 8)}
    return {"aggregator_reference": str(AGG_REF.relative_to(REPO)),
            "via": "aggregate_tree with leaf-score source patched",
            "max_abs_err": round(max_err, 8), "per_tree": detail,
            "pass": max_err < 1e-6}


# ---------------------------------------------------------------- 臂 A
def mutant_leaf_scores(base: dict, m: dict) -> dict:
    ls = dict(base)
    for hit in list(m.get("target_hits", [])) + list(m.get("graded_hits", [])):
        lf = hit["leaf"]
        if lf in ls:
            ls[lf] = max(0.0, min(10.0, ls[lf] + float(hit["delta"])))
    for lf, d in (m.get("non_target_moves") or {}).items():
        if lf in ls:
            ls[lf] = max(0.0, min(10.0, ls[lf] + d))
    return ls


def run_arm_a(trees: list[dict], disc: dict, disc_pso_era: dict, pso: dict) -> dict:
    """四协议逐 mutant 根分/分离度/检出/定位/成本。

    检出落点（口径注记）: E1.1 = 混池终局标量降幅 >= TAU（端到端只有这一个数）;
    E1.2/E1.3/E1.4 = 受影响子树根分降幅 >= TAU（分层可定位，与冻结 K2 协议同落点）。
    两落点对所有协议都产出，跨协议可比性由表格承载，不做单一口径隐藏。
    """
    base = dict(disc["control"]["live_leaves"])
    mutants = disc["mutants"]
    leaf_ids = sorted(base)
    weight_sets = {
        "E1.1_end_to_end": None,
        "E1.2_flat": uniform_internal_weights(trees),
        "E1.3_hier_expert": None,
        "E1.4_hier_pso": pso["best_weights"],
    }
    per_protocol = {}
    for proto in PROTOCOLS:
        w = weight_sets[proto]
        _, z_overall = aggregate(trees, base, w)
        z_roots, _ = aggregate(trees, base, w)
        rows = []
        for m in mutants:
            ls = mutant_leaf_scores(base, m)
            roots, overall = aggregate(trees, ls, w)
            tid = m["tree"]
            sep_blended = round(z_overall - overall, 4)
            sep_root = round(z_roots[tid] - roots[tid], 4)
            touched = sorted({h["leaf"] for h in list(m.get("target_hits", []))
                              + list(m.get("graded_hits", []))
                              if h["leaf"].startswith(tid + ".")})
            rows.append({
                "id": m["id"], "tree": tid,
                "root_scores": {k: round(v, 4) for k, v in roots.items()},
                "blended_final": overall,
                "sep_tree_root": sep_root, "sep_blended": sep_blended,
                "detect_tree_root": sep_root >= TAU,
                "detect_blended": sep_blended >= TAU,
                "primary_detect": sep_blended >= TAU if proto == "E1.1_end_to_end" else sep_root >= TAU,
                "localizable": bool(touched),
                "target_leaves": touched,
                "primary_target_leaf": (m.get("target_hits") or [{}])[0].get("leaf"),
            })
        n = len(rows)
        per_protocol[proto] = {
            "weights": "config expert" if proto in ("E1.1_end_to_end", "E1.3_hier_expert")
            else ("uniform internal=1" if proto == "E1.2_flat" else "pso_weight_search_v0 best_weights"),
            "control_blended_final": z_overall,
            "control_tree_roots": z_roots,
            "per_mutant": rows,
            "mean_separation_blended": round(sum(r["sep_blended"] for r in rows) / n, 6),
            "mean_separation_tree_root": round(sum(r["sep_tree_root"] for r in rows) / n, 6),
            "worst_separation_blended": min(r["sep_blended"] for r in rows),
            "worst_separation_mutant_blended": min(rows, key=lambda r: r["sep_blended"])["id"],
            "detected_tree_root": sum(1 for r in rows if r["detect_tree_root"]),
            "detected_blended": sum(1 for r in rows if r["detect_blended"]),
            "detected_primary": sum(1 for r in rows if r["primary_detect"]),
            "n_mutants": n,
            "localization_rate": round(sum(1 for r in rows if r["localizable"]) / n, 4)
            if proto != "E1.1_end_to_end" else 0.0,
            "cost_proxy": {"scored_units": 2 if proto == "E1.1_end_to_end" else len(leaf_ids),
                           "unit_kind": "tree roots" if proto == "E1.1_end_to_end" else "leaves",
                           "model_calls": 0},
        }
    # G1: E1.3 逐 mutant 根分与冻结报告对账
    e13 = {r["id"]: r["root_scores"] for r in per_protocol["E1.3_hier_expert"]["per_mutant"]}
    g1_err = 0.0
    g1_detail = []
    for m in mutants:
        for tid, val in m["root_scores"].items():
            err = abs(e13[m["id"]][tid] - val)
            g1_err = max(g1_err, err)
            g1_detail.append({"mutant": m["id"], "tree": tid, "frozen": val,
                              "recomputed": e13[m["id"]][tid], "abs_err": round(err, 6)})
    return {"n_mutants": len(mutants), "leaf_ids": leaf_ids,
            "control_live_leaves": base, "protocols": per_protocol,
            "g1_root_score_reproduction": {"max_abs_err": round(g1_err, 6),
                                           "threshold": 0.01,
                                           "pass": g1_err < 0.01,
                                           "per_cell": g1_detail}}


def run_arm_a_pso_reproduction(trees: list[dict], disc_era: dict, pso: dict) -> dict:
    """G2: 在 PSO v0 当时的输入口径（08-19 报告, 全叶 10.0）上复算分离度。

    pivot 注记: 设计稿 §2 列出的臂 A 工件为 08-26 v2 报告; PSO 工件生成于 08-21,
    其 control.live_leaves 口径为 08-19 报告（qa.faithfulness.judge=10.0, M5 delta=-6.0）。
    本函数同时给出两口径的复算结果，如实记录差异，不静默改判据。
    """
    out = {}
    for tag, disc in (("pso_era_input_20260819", disc_era),
                      ("design_doc_input_20260826", json.loads(DISC_V2.read_text(encoding="utf-8")))):
        base = dict(disc["control"]["live_leaves"])
        D = [mutant_leaf_scores(base, m) for m in disc["mutants"]]
        res = {}
        for wname, w in (("expert", None), ("pso", pso["best_weights"])):
            _, z = aggregate(trees, base, w)
            seps = [{"id": m["id"], "sep": round(z - aggregate(trees, d, w)[1], 4)}
                    for m, d in zip(disc["mutants"], D)]
            res[wname] = {
                "control_blended": z,
                "per_mutant": seps,
                "mean_sep": round(sum(s["sep"] for s in seps) / len(seps), 6),
                "worst_sep": min(s["sep"] for s in seps),
                "worst_mutant": min(seps, key=lambda s: s["sep"])["id"],
            }
        out[tag] = res
    era = out["pso_era_input_20260819"]["pso"]
    frozen_mean = pso["optimized_separation_overall"]
    worst_rec = next(x["sep"] for x in pso["per_mutant_optimized"] if x["id"] == "M7_nf_fail_3")
    per_mutant_err = max(abs(next(x["sep"] for x in era["per_mutant"] if x["id"] == r["id"]) - r["sep"])
                         for r in pso["per_mutant_optimized"])
    base_err = max(abs(next(x["sep"] for x in out["pso_era_input_20260819"]["expert"]["per_mutant"]
                            if x["id"] == r["id"]) - r["sep"])
                   for r in pso["per_mutant_baseline"])
    return {"caliber_variants": out,
            "g2_pso_mean_sep": era["mean_sep"], "g2_pso_mean_sep_frozen": frozen_mean,
            "g2_pso_mean_sep_err": round(abs(era["mean_sep"] - frozen_mean), 6),
            "g2_worst_sep": era["worst_sep"], "g2_worst_mutant": era["worst_mutant"],
            "g2_worst_sep_frozen": worst_rec,
            "g2_worst_sep_err": round(abs(era["worst_sep"] - worst_rec), 6),
            "g2_per_mutant_max_err": round(per_mutant_err, 6),
            "g2_baseline_per_mutant_max_err": round(base_err, 6),
            "g2_pass": abs(era["mean_sep"] - frozen_mean) < 0.01
            and abs(era["worst_sep"] - worst_rec) < 0.01}


# ---------------------------------------------------------------- 臂 B
def unique_canonical(orig_header: list[str], mp) -> list[str]:
    seen, out = set(), []
    for h in orig_header:
        k = mp.normalize_header(h)
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(str(h))
    return out


def hit_rate(header: list[str], canonicals: list[str], mp) -> tuple[float, dict]:
    fields = [mp.SchemaField(std, [std]) for std in canonicals]
    st = mp.SchemaTable(table_name="t1_armb", layout="grid",
                        header_region_keywords=[], fields=fields)
    mapping, unmapped = mp.map_headers(header, st)
    n = len(canonicals)
    return (len(mapping) / n if n else 1.0), mapping


def run_arm_b(mp) -> dict:
    tables = json.loads((DRIFT / "injected_tables.json").read_text(encoding="utf-8"))
    imap = json.loads((DRIFT / "injection_map.json").read_text(encoding="utf-8"))
    by_uid = {t["uid"]: t["table"] for t in tables}
    entries_by_uid: dict[str, list[dict]] = {}
    for e in imap["mapping"]:
        entries_by_uid.setdefault(e["uid"], []).append(e)
    parse_tree = next(t for t in json.loads(TREES_PATH.read_text(encoding="utf-8"))["trees"]
                      if t["id"] == "parse")
    parse_armb = prune_nodes(parse_tree, {"parse.doc.throughput", "parse.reconcile"})
    armb_leaves = {"parse.doc.ok", "parse.table.regression", "parse.field.hit_rate"}
    dropped = sorted(set(n["id"] for n in iter_nodes(parse_tree)
                         if not n.get("children")) - armb_leaves)

    per_table = []
    for uid in sorted(entries_by_uid):
        inj_header = [str(c) if c is not None else "" for c in by_uid[uid][0]]
        orig_header = list(inj_header)
        for e in entries_by_uid[uid]:
            orig_header[e["col"]] = e["original"]
        canonicals = unique_canonical(orig_header, mp)
        n_canon = len(canonicals)
        h_orig, map_orig = hit_rate(orig_header, canonicals, mp)
        h_inj, map_inj = hit_rate(inj_header, canonicals, mp)
        drop10 = round((h_orig - h_inj) * 10.0, 4)
        # 三协议表级
        root_orig, _ = aggregate([parse_armb], {"parse.doc.ok": 10.0,
                                                "parse.table.regression": 10.0,
                                                "parse.field.hit_rate": round(h_orig * 10, 6)})
        root_inj, _ = aggregate([parse_armb], {"parse.doc.ok": 10.0,
                                               "parse.table.regression": 10.0,
                                               "parse.field.hit_rate": round(h_inj * 10, 6)})
        changed = {c for c in canonicals if map_orig.get(c) != map_inj.get(c)}
        per_table.append({
            "uid": uid, "n_cols": len(inj_header), "n_canonical": n_canon,
            "n_injections": len(entries_by_uid[uid]),
            "types": sorted({e["type"] for e in entries_by_uid[uid]}),
            "h_orig": round(h_orig, 6), "h_inj": round(h_inj, 6),
            "drop10": drop10,
            "E1.1_detected": map_inj != map_orig,
            "E1.1_final_change_kind": ("mapping_text_changed" if map_inj != map_orig else "unchanged"),
            "E1.2_detected": drop10 >= 10 * FLAT_TAU_H,
            "E1.2_score_delta_H": round(drop10 / 10.0, 6),
            "E1.3_detected": (root_orig["parse"] - root_inj["parse"]) >= TAU,
            "E1.3_root_orig": round(root_orig["parse"], 4),
            "E1.3_root_inj": round(root_inj["parse"], 4),
            "E1.3_root_drop": round(root_orig["parse"] - root_inj["parse"], 4),
            "E1.4_detected": None,
            "changed_canonicals": sorted(changed),
        })

    # 注入级（单注入构造, 与 T2 §3.1 同流）
    per_inj = []
    for uid in sorted(entries_by_uid):
        inj_header = [str(c) if c is not None else "" for c in by_uid[uid][0]]
        orig_header = list(inj_header)
        for e in entries_by_uid[uid]:
            orig_header[e["col"]] = e["original"]
        canonicals = unique_canonical(orig_header, mp)
        h_orig, map_orig = hit_rate(orig_header, canonicals, mp)
        root_orig_tab, _ = aggregate([parse_armb], {"parse.doc.ok": 10.0,
                                                   "parse.table.regression": 10.0,
                                                   "parse.field.hit_rate": round(h_orig * 10, 6)})
        for e in sorted(entries_by_uid[uid], key=lambda x: x["col"]):
            single = list(orig_header)
            single[e["col"]] = e["injected"]
            h_s, map_s = hit_rate(single, canonicals, mp)
            dH = h_orig - h_s
            root_s, _ = aggregate([parse_armb], {"parse.doc.ok": 10.0,
                                                 "parse.table.regression": 10.0,
                                                 "parse.field.hit_rate": round(h_s * 10, 6)})
            target_c = next((c for c in canonicals
                             if mp.normalize_header(c) == mp.normalize_header(e["original"])), None)
            changed = {c for c in canonicals if map_orig.get(c) != map_s.get(c)}
            absorbed = target_c is not None and map_s.get(target_c) == e["injected"]
            per_inj.append({
                "uid": uid, "col": e["col"], "type": e["type"],
                "original": e["original"], "injected": e["injected"],
                "canonical": target_c, "n_canonical": len(canonicals),
                "h_orig": round(h_orig, 6), "h_single": round(h_s, 6),
                "dH": round(dH, 6), "drop10": round(dH * 10, 4),
                "E1.1_detected": map_s != map_orig,
                "E1.2_detected": round(dH * 10, 4) >= 10 * FLAT_TAU_H,
                "E1.3_root_drop": round(root_orig_tab["parse"] - root_s["parse"], 4),
                "E1.3_detected": (root_orig_tab["parse"] - root_s["parse"]) >= TAU,
                "E1.4_detected": None,
                "absorbed": absorbed,
                "attribution_correct": bool(changed) and target_c in changed,
                "changed_canonicals": sorted(changed),
            })

    n_t = len(per_table)
    stats = {}
    for proto in PROTOCOLS:
        if proto == "E1.4_hier_pso":
            stats[proto] = {"applicable": False, "note":
                            "PSO 权重定义在臂 A 的 11 维内部节点空间, 与臂 B 实例化树不同构, 不迁移; "
                            "行如实标 N/A（设计稿 §3.2）, PSO 结果引用臂 A"}
            continue
        key = {"E1.1_end_to_end": "E1.1_detected", "E1.2_flat": "E1.2_detected",
               "E1.3_hier_expert": "E1.3_detected"}[proto]
        det = [t for t in per_table if t[key]]
        inj_det = [i for i in per_inj if i[key]]
        by_type = {}
        for typ in sorted({i["type"] for i in per_inj}):
            its = [i for i in per_inj if i["type"] == typ]
            by_type[typ] = {"n_injections": len(its),
                            "n_detected": sum(1 for i in its if i[key]),
                            "detect_rate": round(sum(1 for i in its if i[key]) / len(its), 4),
                            "n_tables_with_type": len({i["uid"] for i in its})}
        scored = [i for i in per_inj if i[key]]
        loc = sum(1 for i in scored if i["attribution_correct"])
        sep = (sum(t["E1.2_score_delta_H"] for t in per_table) / n_t if proto == "E1.2_flat"
               else sum(t["E1.3_root_drop"] for t in per_table) / n_t if proto == "E1.3_hier_expert"
               else sum(1.0 if t[key] else 0.0 for t in per_table) / n_t)
        stats[proto] = {
            "applicable": True,
            "tables_detected": len(det), "n_tables": n_t,
            "table_detect_rate": round(len(det) / n_t, 4),
            "table_detect_rate_ci95": bootstrap_ci_table([1 if t[key] else 0 for t in sorted(per_table, key=lambda x: x["uid"])]),
            "injections_detected": len(inj_det), "n_injections": len(per_inj),
            "injection_detect_rate": round(len(inj_det) / len(per_inj), 4),
            "by_type": by_type,
            "worst_type_detect_rate": min((v["detect_rate"] for v in by_type.values()), default=None),
            "worst_type": min(by_type, key=lambda k: by_type[k]["detect_rate"]) if by_type else None,
            "separation_mean": round(sep, 6),
            "separation_unit": {"E1.1_end_to_end": "检出布尔均值（0-1, 终局标量无降幅量纲）",
                                "E1.2_flat": "ΔH（命中率先验 0-1 均值）",
                                "E1.3_hier_expert": "parse 根分降幅（0-10 叶片量纲）"}[proto],
            "localization_rate": 0.0 if proto == "E1.1_end_to_end" else round(loc / len(scored), 4) if scored else None,
            "cost_proxy": {"model_calls": 0,
                           "deterministic_checks": n_t * 2 if proto == "E1.1_end_to_end"
                           else (n_t * 2 + len(per_inj) * 1)},
        }

    # G1-臂B: 与冻结判别工件对账
    frozen = json.loads(TABLES_FROZEN.read_text(encoding="utf-8"))
    fz = {t["uid"]: t for t in frozen["tables"]}
    mism_tables, mism_inj = [], []
    for t in per_table:
        f = fz.get(t["uid"])
        if f is None or abs(f["drop10"] - t["drop10"]) > 1e-9 or f["discriminated"] != t["E1.2_detected"]:
            mism_tables.append(t["uid"])
    fz_inj = {(t["uid"], i["col"]): i for t in frozen["tables"] for i in t["injections"]}
    for i in per_inj:
        f = fz_inj.get((i["uid"], i["col"]))
        if f is None or f["absorbed"] != i["absorbed"] or f["type"] != i["type"]:
            mism_inj.append([i["uid"], i["col"]])
    n_disc = sum(1 for t in per_table if t["drop10"] >= TAU)
    g1b = {"tables_discriminated_recomputed": n_disc,
           "tables_discriminated_frozen": frozen["properties"]["discrimination"]["tables_discriminated"],
           "n_tables": n_t,
           "table_level_mismatches": mism_tables,
           "injection_level_mismatches": mism_inj,
           "by_type_recomputed": by_type_counts(per_inj),
           "by_type_frozen": {k: {"n_injections": v["n_injections"], "n_visible": v["n_visible"],
                                  "n_absorbed": v["n_absorbed"]}
                              for k, v in frozen["by_type"].items()},
           }
    g1b["pass"] = (n_disc == g1b["tables_discriminated_frozen"] and not mism_tables
                   and not mism_inj)
    return {"n_tables": n_t, "n_injections": len(per_inj),
            "armB_tree": {"pruned": True, "dropped_na_leaves": dropped,
                          "note": "reconcile 与 throughput 在本臂 N/A, 按 missing 排除并注记（设计稿 §3.2）",
                          "live_leaves": sorted(armb_leaves)},
            "protocols": stats, "tables": per_table, "injections": per_inj,
            "g1_armb": g1b}


def by_type_counts(per_inj: list[dict]) -> dict:
    out = {}
    for i in per_inj:
        e = out.setdefault(i["type"], {"n_injections": 0, "n_visible": 0, "n_absorbed": 0})
        e["n_injections"] += 1
        if i["absorbed"]:
            e["n_absorbed"] += 1
        else:
            e["n_visible"] += 1
    return {k: out[k] for k in sorted(out)}


def bootstrap_ci_table(flags: list[int], n_boot: int = N_BOOT) -> list:
    """表级检出率 95% CI（百分位法, 确定性 seed）。"""
    rng = random.Random(SEED)
    n = len(flags)
    boots = sorted(sum(rng.choices(flags, k=n)) / n for _ in range(n_boot))
    return [round(boots[int(0.025 * n_boot)], 4), round(boots[int(0.975 * n_boot)], 4)]


# ---------------------------------------------------------------- 主流程
def main() -> int:
    _install_network_guard()
    t0 = time.time()
    sys.path.insert(0, str(REPO / "scripts"))
    import m1_statement_parser as mp  # noqa: E402  只读导入生产匹配器
    trees = json.loads(TREES_PATH.read_text(encoding="utf-8"))["trees"]
    disc = json.loads(DISC_V2.read_text(encoding="utf-8"))
    disc_era = json.loads(DISC_PSO_ERA.read_text(encoding="utf-8"))
    pso = json.loads(PSO_PATH.read_text(encoding="utf-8"))

    iso = isomorphism_check(trees, dict(disc["control"]["live_leaves"]))
    arm_a = run_arm_a(trees, disc, disc_era, pso)
    arm_a_pso = run_arm_a_pso_reproduction(trees, disc_era, pso)
    arm_b = run_arm_b(mp)

    gates = {
        "g1_max_err": arm_a["g1_root_score_reproduction"]["max_abs_err"],
        "g1_armA_pass": arm_a["g1_root_score_reproduction"]["pass"],
        "g1_armb_tables": f"{arm_b['g1_armb']['tables_discriminated_recomputed']}"
                          f"/{arm_b['g1_armb']['n_tables']}",
        "g1_armb_frozen_tables": f"{arm_b['g1_armb']['tables_discriminated_frozen']}"
                                 f"/{arm_b['g1_armb']['n_tables']}",
        "g1_armb_pass": arm_b["g1_armb"]["pass"],
        "g2_mean_sep": arm_a_pso["g2_pso_mean_sep"],
        "g2_mean_sep_frozen": arm_a_pso["g2_pso_mean_sep_frozen"],
        "g2_mean_sep_err": arm_a_pso["g2_pso_mean_sep_err"],
        "g2_worst_sep": arm_a_pso["g2_worst_sep"],
        "g2_worst_sep_frozen": arm_a_pso["g2_worst_sep_frozen"],
        "g2_worst_sep_err": arm_a_pso["g2_worst_sep_err"],
        "g2_pass": arm_a_pso["g2_pass"],
        "aggregation_isomorphism_pass": iso["pass"],
        "all_pass": bool(arm_a["g1_root_score_reproduction"]["pass"]
                         and arm_b["g1_armb"]["pass"] and arm_a_pso["g2_pass"] and iso["pass"]),
        "numbering_note": "任务卡 G1 = 本工件 g1_max_err + g1_armb_*; 任务卡 G2 = g2_*; "
                          "设计稿 §4 的 G1/G2/G3 依次对应本工件 g1_max_err / g1_armb / g2_*",
    }
    payload = {
        "meta": {
            "name": "t1-eval-baseline-comparison", "version": "v1",
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "script": str(Path(__file__).relative_to(REPO)),
            "design_doc": "docs/experiments/2026-08-30_t1_eval_baseline_comparison_design.md",
            "task_card": "docs/experiments/2026-08-30_w1_window_card_t1t2t6.md",
            "seed": SEED, "n_boot": N_BOOT, "tau": TAU, "flat_tau_H": FLAT_TAU_H,
            "endpoint_calls": 0,
            "inputs": [str(p.relative_to(REPO)) for p in
                       (DISC_V2, DISC_PSO_ERA, PSO_PATH, TABLES_FROZEN, TREES_PATH, AGG_REF)],
            "scope_note": "E1.5(Full Judge, 需在线推理端点)/E1.6(3 seeds) 不在本窗; "
                          "成功标准第三维 '≥3 seeds CI 可算' 由表级 bootstrap CI 部分承担, 完整多种子属 E1.6",
            "runtime_s": round(time.time() - t0, 2),
        },
        "gates": gates,
        "aggregation_isomorphism": iso,
        "arm_a": arm_a,
        "arm_a_pso_reproduction": arm_a_pso,
        "arm_b": arm_b,
        "prereg_predicates": {
            "P1_pso_ge_expert_mean_sep": {
                "pso": arm_a["protocols"]["E1.4_hier_pso"]["mean_separation_tree_root"],
                "expert": arm_a["protocols"]["E1.3_hier_expert"]["mean_separation_tree_root"],
                "note": "探索性, 不作假设承诺; 臂 A 均值分离度按检出落点(受影响子树根)与混池终局两口径同时给出",
                "pso_blended": arm_a["protocols"]["E1.4_hier_pso"]["mean_separation_blended"],
                "expert_blended": arm_a["protocols"]["E1.3_hier_expert"]["mean_separation_blended"],
            },
            "P6_criterion_evaluation_design_s4_6": {
                "question": "E1.3 相对 E1.1/E1.2 在检出维度是否有优势（无优势则触发 §1 降级表述）",
                "armA_det_primary": {k: v["detected_blended"] if k == "E1.1_end_to_end"
                                     else v["detected_tree_root"]
                                     for k, v in arm_a["protocols"].items()},
                "armA_mean_sep_tree_root": {k: v["mean_separation_tree_root"]
                                            for k, v in arm_a["protocols"].items()},
                "armB_table_detect_rate": {k: (v.get("table_detect_rate"))
                                           for k, v in arm_b["protocols"].items()},
                "armB_injection_detect_rate": {k: (v.get("injection_detect_rate"))
                                               for k, v in arm_b["protocols"].items()},
                "e13_has_detection_advantage": None,
                "verdict": "两臂一致: E1.3 检出维度不优于端到端/扁平协议"
                           "（臂 A 检出数 3/9 vs E1.1 2/9、E1.2 4/9；臂 B 表级 0.2105 显著低于 E1.1 1.0 / E1.2 0.7895）"
                           "→ 触发设计稿 §1 预注册降级表述评估（本卡只产证据, 表述切换在写作卡 T7）",
                "mechanism_note": "臂 B E1.3 的根分降幅 = 3.75 x ΔH（field.hit_rate 在剪枝后的 parse 树中占 3/8 权重, "
                                  "doc.ok 与 table.regression 恒 10 稀释了降幅）, 同 τ=2.0 下等效于 ΔH >= 0.533, "
                                  "远严于 E1.2 的 ΔH >= 0.2；分层优势体现在定位率 1.0 vs 0.0",
            },
            "P2_armB_e11_detect_ge_hier_but_localization_zero": {
                "E1.1_table": arm_b["protocols"]["E1.1_end_to_end"]["table_detect_rate"],
                "E1.2_table": arm_b["protocols"]["E1.2_flat"]["table_detect_rate"],
                "E1.3_table": arm_b["protocols"]["E1.3_hier_expert"]["table_detect_rate"],
                "E1.1_localization_rate": arm_b["protocols"]["E1.1_end_to_end"]["localization_rate"],
                "holds": (arm_b["protocols"]["E1.1_end_to_end"]["injection_detect_rate"]
                          >= max(arm_b["protocols"]["E1.2_flat"]["injection_detect_rate"],
                                 arm_b["protocols"]["E1.3_hier_expert"]["injection_detect_rate"])
                          and arm_b["protocols"]["E1.1_end_to_end"]["localization_rate"] == 0.0),
            },
        },
        "zero_endpoint": self_source_scan(),
    }
    # 摘要只覆盖确定性结果段（meta.generated / meta.runtime_s 为易变字段, 不入摘要）
    result = {k: payload[k] for k in SHA_SCOPE}
    payload["payload_sha256"] = hashlib.sha256(
        json.dumps(result, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    payload["sha256_scope"] = SHA_SCOPE
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"gates": gates, "out": str(OUT),
                      "runtime_s": payload["meta"]["runtime_s"],
                      "zero_endpoint_clean": payload["zero_endpoint"]["clean"]},
                     ensure_ascii=False, indent=1))
    return 0 if gates["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
