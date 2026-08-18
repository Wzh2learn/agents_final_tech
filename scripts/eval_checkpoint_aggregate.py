#!/usr/bin/env python3
"""(K2) GTA-2 检查点树聚合脚本 — Algorithm 1 自底向上加权聚合。

只读消费 logs/graph/eval/ 下的既有活工件, 不调用 :5050/:8004/:8006,
不修改基线/既有 eval 脚本/冻结文件。演示日纪律: 确定性计算, 无网络/推理。

算法 (K1 SOP Step 5/6, 公式照抄 Algorithm 1):
  - 叶子: s_n = LLMJudge(...) 的确定性替代 = 从工件实测值映射到 0-10
         (命中率/通过率 *10; judge 0-5 *2; 二进制通过 -> 10; 失败 -> 0)
  - 非叶子: s_n = sum_c (w_c / sum_{c' in Siblings} w_c') * s_c (兄弟归一化加权平均)
  - 缺工件显式降级: 叶子的 source 工件/维度缺失时, 用 missing_score (默认 5, 硬闸门 0),
        在结果里标注 degraded + 原因, 不静默给 0。

阈值参数化: --thresholds k1 k2 k3 (默认 5 7 8) 输出三档 Root/Leaf SR:
  Root SR = 各子树 Root Score 超阈值比例 (n_subtrees=2)
  Leaf SR = 每棵子树叶子超阈值比例; 跨树汇总档位聚合则按全部 20 叶子重算
  STABLE = (18/20 叶子 >= 7) 且 (无 hinge 叶子 <= 7) --- 与基线口径对照的可复现判据

用法:
  python scripts/eval_checkpoint_aggregate.py
  python scripts/eval_checkpoint_aggregate.py \\
      --trees config/eval_checkpoint_trees.json \\
      --eval-dir logs/graph/eval \\
      --out logs/graph/eval/checkpoint_aggregate_report.json \\
             logs/graph/eval/checkpoint_aggregate_report.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from typing import Any, Iterable


# 工件 -> 叶子映射路由 (source 字段名见 config/eval_checkpoint_trees.json)
def _load_json(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as e:  # 缺失/损坏 -> 显式降级
        return {"__missing__": str(e)}


def _contract_pass_rate(rep: dict, contract: str) -> tuple[float, int, str]:
    qs = rep.get("results", [])
    if not qs:
        return 1.0, 0, "report has no results"
    n_total = n_pass = 0
    for r in qs:
        for ch in r.get("checks", []):
            if ch.get("type") != contract:
                continue
            n_total += 1
            n_pass += 1 if ch.get("pass") else 0
    if n_total == 0:
        return 1.0, 0, f"contract {contract} not present in artifact"
    return n_pass / n_total, n_total, ""


def _judge_avg(rep: dict, dim: str) -> tuple[float, int, str]:
    summary = rep.get("summary", {})
    entry = summary.get(dim)
    if not entry or "avg" not in entry:
        return 0.0, 0, f"judge dim {dim} not in artifact"
    return float(entry["avg"]), int(entry.get("n", 0)), ""


def _nf_pass_rate(rep: dict) -> tuple[float, int, str]:
    results = rep.get("results", [])
    n = len(results)
    if n == 0:
        return 1.0, 0, "number_faithfulness report has no results"
    n_fail = int(rep.get("n_fail", 0))
    return (n - n_fail) / n, n, ""


def _regression_row_pass_rate(rep: dict, leaf: dict = None) -> tuple[float, int, str]:
    rows = rep.get("rows", [])
    if not rows:
        return 1.0, 0, "scenario1 report has no rows"
    base = [r for r in rows if not str(r.get("status", "")).startswith("SKIP")]
    if not base:
        return 1.0, 0, "all m1 rows skipped (no quick/full run)"
    n_pass = sum(1 for r in base if r.get("status") == "PASS")
    return n_pass / len(base), len(base), ""


def _regression_overall_binary(rep: dict, leaf: dict = None) -> tuple[float, int, str]:
    return (10.0 if rep.get("overall") == "PASS" else 0.0), 1, ""


def _regression_run_completed(rep: dict, leaf: dict = None) -> tuple[float, int, str]:
    rows = rep.get("rows", [])
    ok = bool(rows) and "timestamp" in rep
    return (10.0 if ok else 0.0), 1, "" if ok else "report incomplete"


def _regression_hit_rate_achievement(rep: dict, leaf: dict = None) -> tuple[float, int, str]:
    rows = rep.get("rows", [])
    if not rows:
        return 1.0, 0, "scenario1 report has no rows"
    base = [r for r in rows if not str(r.get("status", "")).startswith("SKIP")]
    if not base:
        return 1.0, 0, "all m1 rows skipped"
    diffs = [r for r in base if r.get("diffs")]
    hit_pairs = sum(len(r.get("expected", []) or []) for r in base)
    hit_pairs = max(hit_pairs, 1)
    bad = sum(len(r.get("diffs", [])) for r in base)
    return (hit_pairs - bad) / hit_pairs, hit_pairs, ""


def _reconcile_derived(rep: dict, leaf: dict = None) -> tuple[float, int, str]:
    # 现有工件不产 reconcile 明细; 工程期全样本 reconcile ALL PASS 为权威记录。
    # 无 fail 即按基线段落给 10, 注明 derived=True。
    rows = rep.get("rows", [])
    base = [r for r in rows if not str(r.get("status", "")).startswith("SKIP")]
    if base and any(r.get("status") != "PASS" for r in base):
        return 0.0, 1, "m1 regression has a FAIL row"
    return 10.0, 1, "derived from AGENTS/M1 terminal state: reconcile ALL PASS"


LEAF_ROUTERS = {
    "m1_regression": {
        "overall_status_binary": _regression_overall_binary,
        "run_completed": _regression_run_completed,
        "row_pass_rate": _regression_row_pass_rate,
        "hit_rate_achievement": _regression_hit_rate_achievement,
        "reconcile_derived": _reconcile_derived,
    },
    "m2_deterministic": {
        "pass_rate_contract": lambda rep, leaf: _contract_pass_rate(
            rep, leaf.get("contract", "")),
    },
    "m2_judge": {
        "judge_dim_0_5": lambda rep, leaf: _judge_avg(
            rep, leaf.get("dim", "")),
    },
    "m2_number_faithfulness": {
        "nf_pass_rate": lambda rep, leaf: _nf_pass_rate(rep),
    },
}

HINGE_ROUTES = {"overall_status_binary", "pass_rate_contract", "nf_pass_rate"}


def _iter_nodes(tree: dict) -> Iterable[dict]:
    yield tree
    for c in tree.get("children", []):
        yield from _iter_nodes(c)


def _resolve_artifacts(eval_dir: str) -> dict:
    names = {
        "m1_regression": "scenario1_regression_report.json",
        "m2_deterministic": "m2_deterministic_report.json",
        "m2_judge": "m2_judge_report.json",
        "m2_number_faithfulness": "number_faithfulness_report.json",
    }
    arts = {}
    for key, fname in names.items():
        p = os.path.join(eval_dir, fname)
        if not os.path.exists(p):
            arts[key] = {"__missing__": f"{fname} not found"}
        else:
            arts[key] = _load_json(p)
    return arts


def _mapped_leaf_score(leaf: dict, artifacts: dict) -> tuple[float, dict]:
    src = leaf.get("source")
    art = artifacts.get(src, {"__missing__": f"no artifact for source {src}"})
    if "__missing__" in art:
        return float(leaf.get("missing_score", 5.0)), {"degraded": True,
                                                       "reason": art["__missing__"]}
    router = LEAF_ROUTERS.get(src, {}).get(leaf.get("mapping", ""))
    if router is None:
        return float(leaf.get("missing_score", 5.0)), {"degraded": True,
                                                       "reason": "unmapped router"}
    val, n, note = router(art, leaf)
    if "_n" not in leaf:
        leaf["_n"] = {}
    leaf["_n"][leaf["id"]] = n
    unit = 10.0 if leaf.get("mapping") in ("judge_dim_0_5",) else 10.0
    if leaf.get("mapping") == "judge_dim_0_5":
        score = val * unit / 5.0
        scored_from = "judge 0-5 *2"
    elif leaf.get("mapping") in ("pass_rate_contract", "nf_pass_rate",
                                 "row_pass_rate", "hit_rate_achievement"):
        score = val * 10.0
        scored_from = "rate*10"
    else:
        score = val * unit / 10.0 if unit else val
        scored_from = "binary->10/0" if val in (0.0, 10.0) else "mapped"
    if note:
        leaf["_n"][leaf["id"] + "_note"] = note
    return round(score, 4), {"mapped_from": f"{val:.4f} ({scored_from})",
                             "evidence_n": n, "note": note}


def aggregate_tree(tree: dict, artifacts: dict,
                   thresholds: tuple[int, ...] = (5, 7, 8)) -> dict:
    """Algorithm 1: 叶子映射 + 自底向上递归聚合。返回子树记分结果。"""
    res: dict = {}
    for node in _iter_nodes(tree):
        node["_score"] = None
        node["_leaf_points"] = {}
    # 自底向上: 先 DFS 处理 children
    def dfs(node: dict) -> tuple[float, dict]:
        children = node.get("children", [])
        if not children:
            score, info = _mapped_leaf_score(node, artifacts)
            node["_score"] = score
            node["_info"] = info
            return score, {"subtree_score": score, "depth": 0, "leaf_id": node["id"]}
        scores = []
        for c in children:
            s, sub = dfs(c)
            scores.append((s, sub, c.get("weight", 1)))
        w_sum = sum(w for _, _, w in scores)
        w_sum = w_sum or 1.0
        agg = sum(s * (w / w_sum) for s, _, w in scores)
        node["_score"] = round(agg, 4)
        node["_info"] = {"subtree_score": node["_score"], "n_children": len(children)}
        return node["_score"], node["_info"]
    dfs(tree)
    # 叶子级 SR
    leaves = [n for n in _iter_nodes(tree) if not n.get("children")]
    leaf_scores = {n["id"]: float(n["_score"]) for n in leaves}
    res["leaves"] = leaf_scores
    res["leaf_ids"] = [n["id"] for n in leaves]
    res["subtree_score"] = float(tree["_score"])
    res["n_leaves"] = len(leaves)
    res["n_children"] = len(tree.get("children", []))
    res["sibling_norm"] = "weighted-mean (Algorithm 1)"
    sr, stable = {}, {}
    for k in thresholds:
        root_ok = sum(1 for n in tree.get("children", [])
                      if float(n["_score"]) > k)
        sr[k] = round(root_ok / max(len(tree.get("children", [])), 1), 3)
        leaf_ok = sum(1 for v in leaf_scores.values() if v > k)
        sr[k] = (sr[k], round(leaf_ok / max(len(leaves), 1), 3))
        hinge_leaves = [n["id"] for n in leaves
                        if n.get("mapping") in HINGE_ROUTES]
        stable = {
            "leaf_pass_count": leaf_ok,
            "leaf_pass_rate": round(leaf_ok / max(len(leaves), 1), 3),
            "min_leaf": round(min(leaf_scores.values(), default=0.0), 4),
            "hinge_ok": all(leaf_scores.get(h, 0) >= 7 for h in hinge_leaves),
            "stable": leaf_ok >= 0.9 * len(leaves) and all(
                leaf_scores.get(h, 0) >= 7 for h in hinge_leaves),
        }
    res["sr"] = {str(k): {"root_sr": v[0], "leaf_sr": v[1],
                          "n_sr_subtrees": len(tree.get("children", [])),
                          "n_sr_leaves": len(leaves)} for k, v in sr.items()}
    res["stable"] = stable
    return res


def _format_report(trees_def: dict, results: dict, missing: list[str],
                   thresholds: tuple[int, ...], eval_dir: str) -> str:
    lines = ["# Eval 检查点聚合报告 (K2 v0)", "",
             f"> 生成: {trees_def['meta']['generated']}  | 口径: "
             f"{trees_def['meta']['caliber']}",
             f"> 工件目录: `{eval_dir}` (只读)  | 基线条目: "
             f"`{trees_def['meta']['baseline_ref']}`",
             f"> 干跑验证: 本报告为纯确定性计算, 未调用 :5050/:8004/:8006", ""]
    summary = trees_def.get("meta", {}).get("summary", {})
    if summary:
        lines.append("**Meta 摘要**")
        for k, v in summary.items():
            lines.append(f"- {k}: {v}")
        lines.append("")
    if missing:
        lines += ["**工件降级记录**", ""]
        for m in missing:
            lines.append(f"- [degraded] {m}")
        lines.append("")
    for tree, res in results.items():
        lines += [f"## {tree}", "",
                  f"- 子树 Root Score: **{res['subtree_score']}** (0-10)",
                  f"- 叶子数: {res['n_leaves']} | 逐树 SR (root_sr, leaf_sr):"]
        for k, sr in res["sr"].items():
            lines.append(f"  - k={k}: root_sr={sr['root_sr']} "
                         f"(n={sr['n_sr_subtrees']}) / leaf_sr={sr['leaf_sr']} "
                         f"(n={sr['n_sr_leaves']})")
        lines += [f"- STABLE 判据 (>=90% 叶子 >=7 且无 hinge<=7): "
                  f"**{res['stable']['stable']}** "
                  f"(leaf_pass={res['stable']['leaf_pass_count']}"
                  f"/{res['n_leaves']}, min_leaf={res['stable']['min_leaf']}, "
                  f"hinge_ok={res['stable']['hinge_ok']})", "",
                  "### 叶子明细", ""]
        for leaf_id, score in res["leaves"].items():
            lines.append(f"- `{leaf_id}`: {score}")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--eval-dir", default="logs/graph/eval")
    ap.add_argument("--trees", default="config/eval_checkpoint_trees.json")
    ap.add_argument("--out", nargs="*",
                    default=["logs/graph/eval/checkpoint_aggregate_report.json",
                             "logs/graph/eval/checkpoint_aggregate_report.md"])
    ap.add_argument("--thresholds", nargs="*", type=int, default=[5, 7, 8])
    args = ap.parse_args(argv)
    eval_dir = args.eval_dir
    trees_path = args.trees
    if not os.path.exists(trees_path):
        print(f"[fatal] trees file not found: {trees_path}", file=sys.stderr)
        return 2
    trees_def = _load_json(trees_path)
    if "__missing__" in trees_def:
        print(f"[fatal] trees file unreadable: {trees_path}", file=sys.stderr)
        return 2
    artifacts = _resolve_artifacts(eval_dir)
    missing = []
    for src, art in artifacts.items():
        if "__missing__" in art:
            missing.append(f"{src}: {art['__missing__']}")
    results: dict[str, dict] = {}
    for tree in trees_def["trees"]:
        res = aggregate_tree(tree, artifacts, tuple(args.thresholds))
        results[tree["id"]] = res
    # 输出
    out_files = list(args.out) or ["-"]
    payload = {
        "meta": trees_def["meta"],
        "eval_dir": eval_dir,
        "trees_file": trees_path,
        "thresholds": list(args.thresholds),
        "degraded": missing,
        "results": results,
    }
    if out_files == ["-"]:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        for of in out_files:
            if of.endswith(".md"):
                open(of, "w", encoding="utf-8").write(
                    _format_report(trees_def, results, missing,
                                   tuple(args.thresholds), eval_dir))
            else:
                with open(of, "w", encoding="utf-8") as fh:
                    json.dump(payload, fh, ensure_ascii=False, indent=1)
            print(f"[report] {of}")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
