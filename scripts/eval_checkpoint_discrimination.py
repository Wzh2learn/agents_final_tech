#!/usr/bin/env python3
"""(v1, 批复 ①) 检查点树判别力测试床 — 构造缺陷样本验证判别力。

K2 v0 阈值 k=5/7/8 在真实工件上全绿（区分度不足，v0 报告 §5 已自陈）。
v1 用确定性 mutation 生成 mutant 工件副本（契约失败/judge 降分/回归 FAIL/
NF 失败/工件缺失），对每份跑 Algorithm 1 聚合，验证三条性质：
  1. 判别力: 目标叶子按预期下降 >= 2 分（缺陷能被树看见）;
  2. 局部性: 非目标叶子零移动（叶映射互不串扰）;
  3. 零漂移: control（未突变副本）与活工件得分逐叶一致。

纯确定性计算: 不调 :5050/:8004/:8006, 不改活工件（副本全部落在
<eval-dir>/_mutants/<id>/）, 不碰冻结节点。增量新增, 基线零漂移。

用法:
  python scripts/eval_checkpoint_discrimination.py [--eval-dir logs/graph/eval]
      [--trees config/eval_checkpoint_trees.json] [--keep]
退出码: 0 = 全部 mutant 判别性质通过; 1 = 有 mutant 未达判据。
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eval_checkpoint_aggregate import (  # noqa: E402
    _load_json, _resolve_artifacts, aggregate_tree)

ARTIFACTS = {
    "m1_regression": "scenario1_regression_report.json",
    "m2_deterministic": "m2_deterministic_report.json",
    "m2_judge": "m2_judge_report.json",
    "m2_number_faithfulness": "number_faithfulness_report.json",
}
DROP_THRESHOLD = 2.0  # 目标叶子下降判据（分）


# ---------------- mutators（对副本工件做确定性突变） ----------------

def mut_m1_rows_fail(d: str) -> None:
    p = os.path.join(d, ARTIFACTS["m1_regression"])
    rep = _load_json(p)
    n = 0
    for row in rep.get("rows", []):
        if row.get("status") == "PASS" and row.get("expected") and n < 2:
            row["status"] = "FAIL"
            row["diffs"] = [{"field": "mutated_field", "expected": "1",
                             "actual": "2"}]
            n += 1
    rep["overall"] = "FAIL"
    json.dump(rep, open(p, "w", encoding="utf-8"), ensure_ascii=False)


def mut_contract_fail(d: str, contract: str) -> None:
    p = os.path.join(d, ARTIFACTS["m2_deterministic"])
    rep = _load_json(p)
    for r in rep.get("results", []):
        for ch in r.get("checks", []):
            if ch.get("type") == contract:
                ch["pass"] = False
        r["all_pass"] = all(c.get("pass") for c in r.get("checks", []))
    json.dump(rep, open(p, "w", encoding="utf-8"), ensure_ascii=False)


def mut_judge_degrade(d: str, dim: str, new_avg: float) -> None:
    p = os.path.join(d, ARTIFACTS["m2_judge"])
    rep = _load_json(p)
    if dim in rep.get("summary", {}):
        rep["summary"][dim]["avg"] = new_avg
    for r in rep.get("results", []):
        cell = r.get("scores", {}).get(dim)
        if isinstance(cell, dict):
            cell["score"] = int(round(new_avg))
    json.dump(rep, open(p, "w", encoding="utf-8"), ensure_ascii=False)


def mut_nf_fail(d: str, n: int) -> None:
    p = os.path.join(d, ARTIFACTS["m2_number_faithfulness"])
    rep = _load_json(p)
    for i, r in enumerate(rep.get("results", [])):
        r["pass"] = i >= n
    rep["n_fail"] = min(n, len(rep.get("results", [])))
    json.dump(rep, open(p, "w", encoding="utf-8"), ensure_ascii=False)


def mut_delete_artifact(d: str, key: str) -> None:
    p = os.path.join(d, ARTIFACTS[key])
    if os.path.exists(p):
        os.remove(p)


def build_mutants() -> list[dict]:
    return [
        {"id": "M1_m1_rows_fail", "desc": "scenario1 两行 PASS->FAIL (带 diffs)",
         "targets": ["parse.doc.ok", "parse.table.regression",
                     "parse.field.hit_rate",
                     # reconcile_derived 从回归状态派生, FAIL 行必连带 ->
                     # 属真实依赖而非串扰, 列入目标
                     "parse.reconcile.equations"],
         "tree": "parse", "mutate": mut_m1_rows_fail},
        {"id": "M2_exact_numeric_fail", "desc": "exact_numeric 契约全部失败",
         "targets": ["qa.numeric.exact"], "tree": "qa",
         "mutate": lambda d: mut_contract_fail(d, "exact_numeric")},
        {"id": "M3_source_required_fail", "desc": "source_required 契约全部失败",
         "targets": ["qa.retrieval.source_required"], "tree": "qa",
         "mutate": lambda d: mut_contract_fail(d, "source_required")},
        {"id": "M4_refusal_expected_fail", "desc": "refusal_expected 契约全部失败",
         "targets": ["qa.refusal.deterministic"], "tree": "qa",
         "mutate": lambda d: mut_contract_fail(d, "refusal_expected")},
        {"id": "M5_judge_faithfulness_degrade", "desc": "judge faithfulness 5.0->2.0",
         "targets": ["qa.faithfulness.judge"], "tree": "qa",
         "mutate": lambda d: mut_judge_degrade(d, "faithfulness", 2.0)},
        {"id": "M6_judge_citation_degrade", "desc": "judge citation_quality 5.0->1.5",
         "targets": ["qa.citation.judge"], "tree": "qa",
         "mutate": lambda d: mut_judge_degrade(d, "citation_quality", 1.5)},
        {"id": "M7_nf_fail_3", "desc": "NF 前 3 条未落地",
         "targets": ["qa.numeric.number_grounding"], "tree": "qa",
         "mutate": lambda d: mut_nf_fail(d, 3)},
        {"id": "M8_judge_artifact_missing", "desc": "judge 工件缺失 -> missing_score 降级",
         "targets": ["qa.faithfulness.judge", "qa.citation.judge",
                     "qa.refusal.judge"], "tree": "qa",
         "mutate": lambda d: mut_delete_artifact(d, "m2_judge")},
    ]


# ---------------- 聚合与对比 ----------------

def run_aggregate(trees_def: dict, eval_dir: str,
                  thresholds=(5, 7, 8)) -> dict:
    artifacts = _resolve_artifacts(eval_dir)
    out = {}
    for tree in trees_def["trees"]:
        res = aggregate_tree(copy.deepcopy(tree), artifacts, thresholds)
        out[tree["id"]] = res
    return out


def leaves_flat(results: dict) -> dict:
    flat = {}
    for tree_id, res in results.items():
        for leaf, score in res["leaves"].items():
            flat[leaf] = score
    return flat


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--eval-dir", default="logs/graph/eval")
    ap.add_argument("--trees", default="config/eval_checkpoint_trees.json")
    ap.add_argument("--out", nargs="*",
                    default=["logs/graph/eval/checkpoint_discrimination_report.json",
                             "logs/graph/eval/checkpoint_discrimination_report.md"])
    ap.add_argument("--keep", action="store_true",
                    help="保留 mutant 副本目录（默认跑完清理）")
    args = ap.parse_args(argv)

    trees_def = _load_json(args.trees)
    if "__missing__" in trees_def:
        print(f"[fatal] trees 不可读: {args.trees}", file=sys.stderr)
        return 2

    # 活工件基线（只读）
    live = run_aggregate(trees_def, args.eval_dir)
    live_leaves = leaves_flat(live)

    mutants_dir = os.path.join(args.eval_dir, "_mutants")
    if os.path.isdir(mutants_dir):
        shutil.rmtree(mutants_dir)
    os.makedirs(mutants_dir, exist_ok=True)

    def copy_artifacts(dest: str) -> None:
        os.makedirs(dest, exist_ok=True)
        for fname in ARTIFACTS.values():
            src = os.path.join(args.eval_dir, fname)
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(dest, fname))

    # M0 control: 纯副本, 验证副本中性
    m0_dir = os.path.join(mutants_dir, "M0_control")
    copy_artifacts(m0_dir)
    control = run_aggregate(trees_def, m0_dir)
    control_leaves = leaves_flat(control)
    control_drift = {k: round(control_leaves[k] - live_leaves[k], 4)
                     for k in live_leaves
                     if abs(control_leaves.get(k, 0) - live_leaves[k]) > 1e-9}

    report_mutants = []
    n_pass = 0
    for spec in build_mutants():
        mdir = os.path.join(mutants_dir, spec["id"])
        copy_artifacts(mdir)
        spec["mutate"](mdir)
        res = run_aggregate(trees_def, mdir)
        m_leaves = leaves_flat(res)
        deltas = {k: round(m_leaves.get(k, 0) - live_leaves.get(k, 0), 4)
                  for k in sorted(set(live_leaves) | set(m_leaves))}
        target_hits = []
        for t in spec["targets"]:
            d_val = deltas.get(t, 0.0)
            target_hits.append({"leaf": t, "delta": d_val,
                                "hit": d_val <= -DROP_THRESHOLD})
        non_target_moves = {k: v for k, v in deltas.items()
                            if k not in spec["targets"] and abs(v) > 1e-6}
        stable_now = all(r["stable"]["stable"] for r in res.values())
        stable_live = all(r["stable"]["stable"] for r in live.values())
        ok = all(h["hit"] for h in target_hits) and not non_target_moves
        n_pass += 1 if ok else 0
        report_mutants.append({
            "id": spec["id"], "desc": spec["desc"], "tree": spec["tree"],
            "target_hits": target_hits, "non_target_moves": non_target_moves,
            "root_scores": {t: r["subtree_score"] for t, r in res.items()},
            "stable": stable_now, "stable_flip": stable_live and not stable_now,
            "verdict": "PASS" if ok else "FAIL"})
        print(f"{spec['id']:32s} {'PASS' if ok else 'FAIL'}  "
              + "  ".join(f"{h['leaf']}:{h['delta']:+.1f}"
                          for h in target_hits))

    if not args.keep:
        shutil.rmtree(mutants_dir, ignore_errors=True)

    payload = {
        "meta": {"name": "checkpoint-discrimination", "version": "v1",
                 "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                 "drop_threshold": DROP_THRESHOLD,
                 "caliber": "v1 批复 ①: 增量/基线零漂移/判别力验证",
                 "eval_dir": args.eval_dir, "trees": args.trees},
        "control": {"live_leaves": live_leaves, "copy_drift": control_drift,
                    "zero_drift": not control_drift},
        "mutants": report_mutants,
        "summary": {"n_mutants": len(report_mutants), "n_pass": n_pass,
                    "all_pass": n_pass == len(report_mutants)},
    }
    for of in (args.out or []):
        os.makedirs(os.path.dirname(of) or ".", exist_ok=True)
        if of.endswith(".md"):
            open(of, "w", encoding="utf-8").write(_format_md(payload))
        else:
            json.dump(payload, open(of, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
        print(f"[report] {of}")
    return 0 if payload["summary"]["all_pass"] and not control_drift else 1


def _format_md(p: dict) -> str:
    L = ["# 检查点树判别力报告 (v1)", "",
         f"> 生成: {p['meta']['generated']} | 判据: 目标叶子下降 >= "
         f"{p['meta']['drop_threshold']} 分 且非目标叶子零移动",
         f"> 工件目录: {p['meta']['eval_dir']} (只读)", ""]
    c = p["control"]
    L += [f"## Control 零漂移校验: {'PASS' if c['zero_drift'] else 'FAIL'}", ""]
    if c["copy_drift"]:
        L += [f"- 漂移: {c['copy_drift']}", ""]
    L += ["## Mutants", "",
          "| mutant | 判 | 目标叶子 delta | STABLE 翻转 |",
          "|---|---|---|---|"]
    for m in p["mutants"]:
        deltas = " ".join(f"{h['leaf']} {h['delta']:+.1f}"
                          for h in m["target_hits"])
        L.append(f"| {m['id']} | {m['verdict']} | {deltas} | "
                 f"{'是' if m['stable_flip'] else '否'} |")
    L += ["", f"总计: {p['summary']['n_pass']}/{p['summary']['n_mutants']} "
          f"mutant 判别性质通过", ""]
    return "\n".join(L)


if __name__ == "__main__":
    raise SystemExit(main())
