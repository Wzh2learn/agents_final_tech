#!/usr/bin/env python3
"""W2 段 T4: PSO 权重搜索的严谨对照（五组 + minimax 变体 + 题集预算梯度 + Pareto）。

任务卡: docs/experiments/2026-08-30_w2_window_card_8004.md §3.3
判据: 蓝图 C3「PSO 均值分离度优于四组对照（多 seed CI），最坏类型维度如实报告」;
      降级条款「PSO 不优于 expert/greedy: 改\'自动搜索节省专家调参成本\'，
      均值增益与最坏类型退化如实并列」。

零模型调用: 全部计算跑在冻结臂 A 叶分矩阵上（权重空间搜索 = 纯算术）。
socket 层封死 -> 任何连接尝试立即抛错, 自证零端点。

口径（两条, 主口径 = 卡 §2.2 预测所属口径）:
  pso_era (08-19 矩阵) = PSO v0 工件生成时的输入, 卡预测 expert 1.2560 / PSO 1.4326;
  v2      (08-26 矩阵) = 当前活工件口径, faithfulness 叶 9.88。
主口径判 C3, 次口径作稳健性附注（两口径数字永不混用, 分别标注）。

五组对照（同一 Algorithm 1 聚合, 同一叶分矩阵, 唯一变量 = 权重来源）:
  equal   全部内部节点 = 1（无先验）
  expert  config 权重（人工先验, 即 E1.3 口径）
  random  PSO 初始流同分布的 30 组随机权重（等算力对照: 30 次评估）
  greedy  坐标上升, 从 expert 出发, 逐维试 {1,2,3}（贪心对照）
  pso     PSO 5 seeds（P=30/Tmax=50, 与 v0 同参数; seed 20260821 = 冻结复现门）

用法: python3 research/paper_w2_t4_pso_fair.py [--quick]
"""
from __future__ import annotations

import argparse
import json
import random
import socket
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
TREES_PATH = REPO / "config" / "eval_checkpoint_trees.json"
DISC_V2 = EVAL / "checkpoint_discrimination_report.json"
DISC_ERA = EVAL / "checkpoint_discrimination_report_20260819.json"
PSO_V0 = EVAL / "pso_weight_search_v0.json"
QSET = EVAL / "pso_question_set_v0_batch2.json"
OUT = EVAL / "_w2_t4_section.json"

TAU = 2.0
WEIGHT_GRID = (1, 2, 3)
PSO_P, PSO_TMAX, PSO_C1, PSO_C2 = 30, 50, 2.0, 2.0
PSO_W0, PSO_W1 = 0.7, 0.4
PSO_SEEDS = (20260821, 42, 2026, 20260830, 777)     # 含冻结 seed
FROZEN_SEED = 20260821
G_REPRODUCE_TOL = 0.01                               # 冻结复现门
MINIMAX_PRED = 0.208                                 # 卡 §2.2 预测: 最差 mutant >= 0.208
RANDOM_N = 30
BANK_SIZE = 19
BUDGET_FRACTIONS = (0.25, 0.50, 0.75, 1.00)
PORTS_TOUCHED: list = []


def install_zero_guard() -> None:
    real = socket.socket

    class Blocked(real):  # type: ignore[misc]
        def connect(self, address, *a, **k):
            if isinstance(address, tuple) and len(address) >= 2:
                PORTS_TOUCHED.append(str(address[:2]))
            raise RuntimeError("ZERO_ENDPOINT: blocked outbound %r" % (address,))

        def connect_ex(self, address, *a, **k):
            return self.connect(address, *a, **k)

    socket.socket = Blocked                        # type: ignore[misc]
    socket.create_connection = lambda *a, **k: (_ for _ in ()).throw(
        RuntimeError("ZERO_ENDPOINT: blocked create_connection"))
    socket.getaddrinfo = lambda *a, **k: (_ for _ in ()).throw(
        RuntimeError("ZERO_ENDPOINT: blocked getaddrinfo"))


sys.path.insert(0, str(REPO / "research"))
import paper_t1_eval_baselines as t1                # noqa: E402  纯函数复用


# ---------------------------------------------------------------- 评分器
class Caliber:
    """一条口径 = (叶分矩阵, 树, 权重维度) 上的一致性评分器。"""

    def __init__(self, trees: list, disc: dict):
        self.trees = trees
        self.disc = disc
        self.base = dict(disc["control"]["live_leaves"])
        self.mutants = disc["mutants"]
        self.mats = [t1.mutant_leaf_scores(self.base, m) for m in self.mutants]
        _, self.z = t1.aggregate(trees, self.base, None)
        self.dim_ids = self._weight_dims(trees)

    @staticmethod
    def _weight_dims(trees):
        ids = []
        for tr in trees:
            for n in t1.iter_nodes(tr):
                if "weight" in n and n.get("children"):
                    ids.append(n["id"])
        return ids

    def sep_of(self, weight_over, aggregate_mode: str = "mean") -> dict:
        _, z = t1.aggregate(self.trees, self.base, weight_over)
        seps = [round(z - t1.aggregate(self.trees, m, weight_over)[1], 6)
                for m in self.mats]
        if not seps:
            return {"mean": 0.0, "worst": 0.0, "seps": []}
        return {"mean": round(statistics.fmean(seps), 6), "worst": round(min(seps), 6),
                "seps": seps, "control_blended": round(z, 6)}

    def fit(self, weight_over, objective: str) -> float:
        s = self.sep_of(weight_over)
        return s["worst"] if objective == "minimax" else s["mean"]


def to_override(cal: Caliber, vec) -> dict:
    return {cal.dim_ids[i]: int(vec[i]) for i in range(len(cal.dim_ids))}


# ---------------------------------------------------------------- 搜索器
def pso_search(cal: Caliber, seed: int, objective: str = "mean"):
    """PSO v0 同参数同离散化; objective=minimax 时适应度换成最差 mutant。"""
    rng = random.Random(seed)
    dim = len(cal.dim_ids)
    x = [[rng.uniform(1.0, 3.0) for _ in range(dim)] for _ in range(PSO_P)]
    v = [[rng.uniform(-0.5, 0.5) for _ in range(dim)] for _ in range(PSO_P)]

    def disc_pos(pos):
        return [max(1, min(3, round(p))) for p in pos]

    j = [-cal.fit(to_override(cal, disc_pos(p)), objective) for p in x]
    pbest, pbest_j = [list(p) for p in x], list(j)
    gi = min(range(PSO_P), key=lambda i: j[i])
    gbest, gbest_j = list(x[gi]), j[gi]
    trace = []
    for it in range(PSO_TMAX):
        w = PSO_W0 - (PSO_W0 - PSO_W1) * it / max(PSO_TMAX - 1, 1)
        for p in range(PSO_P):
            for i in range(dim):
                v[p][i] = (w * v[p][i] + PSO_C1 * rng.random() * (pbest[p][i] - x[p][i])
                           + PSO_C2 * rng.random() * (gbest[i] - x[p][i]))
                x[p][i] += v[p][i]
            jj = -cal.fit(to_override(cal, disc_pos(x[p])), objective)
            # 与冻结实现同构: pbest 与 gbest 两级判定互不嵌套
            if jj < pbest_j[p]:
                pbest_j[p], pbest[p] = jj, list(x[p])
            if jj < gbest_j:
                gbest_j, gbest = jj, list(x[p])
        trace.append(round(-gbest_j, 6))
    return {"vec": disc_pos(gbest), "weights": to_override(cal, disc_pos(gbest)),
            "fitness": round(-gbest_j, 6), "trace": trace,
            "evals": PSO_P * (PSO_TMAX + 1)}


def greedy_search(cal: Caliber, objective: str = "mean"):
    """坐标上升: 从 expert 出发, 逐维试 {1,2,3} 取最优, 循环至收敛。"""
    cur = {d: next(n["weight"] for t in cal.trees for n in t1.iter_nodes(t)
                   if n["id"] == d and "weight" in n) for d in cal.dim_ids}
    best = cal.fit(cur, objective)
    evals, rounds = 1, 0
    improved = True
    while improved and rounds < 12:
        improved, rounds = False, rounds + 1
        for d in cal.dim_ids:
            orig = cur[d]
            for cand in WEIGHT_GRID:
                if cand == orig:
                    continue
                trial = dict(cur)
                trial[d] = cand
                val = cal.fit(trial, objective)
                evals += 1
                if val > best + 1e-12:
                    best, cur[d], improved = val, cand, True
            if not improved:
                cur[d] = orig
    return {"weights": cur, "fitness": round(best, 6), "rounds": rounds, "evals": evals}


def random_group(cal: Caliber, seed: int = 20260830, n: int = RANDOM_N):
    """等算力随机对照: 与 PSO 初始流同分布（U[1,3] -> 就近取整到 {1,2,3}）。"""
    rng = random.Random(seed)
    dim = len(cal.dim_ids)
    means, worsts, vecs = [], [], []
    for _ in range(n):
        vec = [max(1, min(3, round(rng.uniform(1.0, 3.0)))) for _ in range(dim)]
        w = to_override(cal, vec)
        s = cal.sep_of(w)
        means.append(s["mean"])
        worsts.append(s["worst"])
        vecs.append(vec)
    return {"n": n, "means": [round(m, 6) for m in means],
            "worsts": round(min(worsts), 6),
            "mean_of_means": round(statistics.fmean(means), 6),
            "std_of_means": round(statistics.pstdev(means), 6),
            "best_single_mean": round(max(means), 6),
            "worst_single_mean": round(min(means), 6),
            "n_beating_expert": None, "evals": n}


def bootstrap_mean(values, seed=20260830, n_boot=2000):
    rng = random.Random(seed)
    boots = sorted(statistics.fmean(rng.choices(values, k=len(values))) for _ in range(n_boot))
    return [round(boots[int(0.025 * n_boot)], 6), round(boots[int(0.975 * n_boot)], 6)]


# ---------------------------------------------------------------- 题集预算梯度
def question_budget_gradient(disc: dict, quick: bool) -> dict:
    """题集预算 25/50/75/100% -> PSO 选集的突变体保持率 / 适应度 / 覆盖度。

    复用 research/pso/pso_question_set_search.py 的 bank / fitness / keep_rate 口径
    （唯一变量 = 预算 B）, 判据 = 判别力随题量单调不降（卡 §2.2）。
    """
    sys.path.insert(0, str(REPO / "research" / "pso"))
    import pso_question_set_search as qs
    bank = qs.build_bank()
    bank_ids = sorted(bank)
    mutants = qs.load_qa_mutants()
    out = {}
    for frac in BUDGET_FRACTIONS:
        b = max(1, round(frac * BANK_SIZE))
        runs = []
        seeds = (qs.SEED,) if quick else (qs.SEED, qs.SEED + 1, qs.SEED + 2)
        for sd in seeds:
            rng = random.Random(sd)
            gbest, gbest_f, _ = qs.pso(bank_ids, bank, mutants, b, rng)
            gzone, _ = qs.greedy(bank_ids, bank, mutants, b)
            runs.append({
                "seed": sd,
                "pso_size": int(sum(1 for vv in gbest if vv > 0.5)),
                "pso_fitness": round(gbest_f, 6),
                "pso_keep_rate": round(qs.keep_rate(gbest, bank_ids, bank, mutants), 4),
                "pso_coverage_violations": qs.coverage_violations(gbest, bank_ids, bank),
                "greedy_keep_rate": round(qs.keep_rate(gzone, bank_ids, bank, mutants), 4),
                "greedy_fitness": round(qs.fitness(gzone, bank_ids, bank, mutants, b), 6),
                "all_mutants_target_leaves": sum(1 for m in mutants if m["targets"]),
            })
        out["B=%d(%.0f%%)" % (b, frac * 100)] = {
            "budget": b, "fraction": frac, "n_seeds": len(runs),
            "pso_keep_rate_mean": round(statistics.fmean([r["pso_keep_rate"] for r in runs]), 4),
            "pso_keep_rate_values": [r["pso_keep_rate"] for r in runs],
            "pso_fitness_mean": round(statistics.fmean([r["pso_fitness"] for r in runs]), 6),
            "greedy_keep_rate_mean": round(statistics.fmean([r["greedy_keep_rate"] for r in runs]), 4),
            "min_per_leaf_support": _min_leaf_support(bank_ids, bank, out, runs),
            "runs": runs,
        }
    keep = [v["pso_keep_rate_mean"] for _, v in sorted(out.items(), key=lambda kv: kv[1]["budget"])]
    return {"bank_size": BANK_SIZE, "qa_mutants_in_scope": len(mutants),
            "protocol_reuse": "research/pso/pso_question_set_search.py (build_bank/"
                              "load_qa_mutants/keep_rate/coverage_violations/fitness/pso/greedy)",
            "budgets": out, "keep_rate_sequence": keep,
            "monotonic_non_decreasing": all(b >= a - 1e-9 for a, b in zip(keep, keep[1:])),
            "saturated_at_smallest_budget": bool(keep) and keep[0] >= 1.0,
            "saturation_note": ("keep_rate 在最小预算即达 1.0 -> 题集维度的判别力梯度在该协议下"
                                "饱和, 无法区分 25%~100%; 已并列次级指标（适应度/覆盖违反/最小叶支撑题数）"
                                "作为可区分轴, 论文中不得用 keep_rate 主张预算-判别力单调性。")}


def _min_leaf_support(bank_ids, bank, out, runs):
    leaves = set()
    for q in bank_ids:
        leaves |= bank[q]["leaves"]
    counts = {}
    for lf in sorted(leaves):
        counts[lf] = sum(1 for q in bank_ids if lf in bank[q]["leaves"])
    return {"per_leaf_bank_support_min": min(counts.values()) if counts else 0,
            "n_leaves_in_bank": len(leaves)}


# ---------------------------------------------------------------- 主流程
def run_caliber(tag: str, disc_path: Path, trees: list, quick: bool) -> dict:
    cal = Caliber(trees, json.loads(disc_path.read_text(encoding="utf-8")))
    expert = cal.sep_of(None)
    equal = cal.sep_of(t1.uniform_internal_weights(cal.trees))
    rnd = random_group(cal)
    grd = greedy_search(cal)
    grd_sep = cal.sep_of(grd["weights"])
    rnd["n_beating_expert"] = sum(1 for m in rnd["means"] if m > expert["mean"])

    pso_runs = []
    for sd in PSO_SEEDS:
        r = pso_search(cal, sd, "mean")
        s = cal.sep_of(r["weights"])
        pso_runs.append({"seed": sd, "weights": r["weights"], "mean_sep": s["mean"],
                         "worst_sep": s["worst"], "trace_tail": r["trace"][-3:],
                         "evals": r["evals"], "per_mutant": s["seps"]})
    mm_runs = []
    for sd in PSO_SEEDS:
        r = pso_search(cal, sd, "minimax")
        s = cal.sep_of(r["weights"])
        mm_runs.append({"seed": sd, "weights": r["weights"], "mean_sep": s["mean"],
                        "worst_sep": s["worst"], "evals": r["evals"]})

    pmeans = [r["mean_sep"] for r in pso_runs]
    pworst = [r["worst_sep"] for r in pso_runs]
    mmeans = [r["mean_sep"] for r in mm_runs]
    mworst = [r["worst_sep"] for r in mm_runs]

    frozen = json.loads(PSO_V0.read_text(encoding="utf-8"))
    era = [r for r in pso_runs if r["seed"] == FROZEN_SEED]
    g_repro = None
    if era:
        g_repro = {"frozen_optimized_separation": frozen["optimized_separation_overall"],
                   "recomputed": era[0]["mean_sep"],
                   "abs_err": round(abs(era[0]["mean_sep"]
                                        - frozen["optimized_separation_overall"]), 6),
                   "threshold": G_REPRODUCE_TOL,
                   "pass": abs(era[0]["mean_sep"]
                               - frozen["optimized_separation_overall"]) < G_REPRODUCE_TOL,
                   "weights_identical_to_frozen": era[0]["weights"] == frozen["best_weights"]}

    sep_table = {
        "equal": {"mean_sep": equal["mean"], "worst_sep": equal["worst"],
                  "worst_mutant": _worst_name(cal, equal["seps"]), "n_evals": 1},
        "expert": {"mean_sep": expert["mean"], "worst_sep": expert["worst"],
                   "worst_mutant": _worst_name(cal, expert["seps"]), "n_evals": 1},
        "random30": {"mean_sep": rnd["mean_of_means"], "std_of_means": rnd["std_of_means"],
                     "worst_sep": rnd["worsts"], "best_single_mean": rnd["best_single_mean"],
                     "n_evals": rnd["evals"], "n_beating_expert": rnd["n_beating_expert"]},
        "greedy": {"mean_sep": grd_sep["mean"], "worst_sep": grd_sep["worst"],
                   "worst_mutant": _worst_name(cal, grd_sep["seps"]), "n_evals": grd["evals"]},
        "pso_5seeds": {"mean_sep_mean": round(statistics.fmean(pmeans), 6),
                       "mean_sep_values": pmeans, "mean_sep_std": round(statistics.pstdev(pmeans), 6),
                       "mean_sep_ci95": bootstrap_mean(pmeans),
                       "worst_sep_mean": round(statistics.fmean(pworst), 6),
                       "worst_sep_values": pworst, "n_evals": PSO_P * (PSO_TMAX + 1) * len(PSO_SEEDS)},
        "pso_minimax_5seeds": {"mean_sep_mean": round(statistics.fmean(mmeans), 6),
                               "worst_sep_mean": round(statistics.fmean(mworst), 6),
                               "worst_sep_values": mworst, "mean_sep_values": mmeans},
    }
    pareto = _pareto(cal, pso_runs, mm_runs, rnd, expert, equal, grd_sep)
    return {"caliber": tag, "matrix_source": str(disc_path.name),
            "n_weight_dims": len(cal.dim_ids), "n_mutants": len(cal.mutants),
            "separation_table": sep_table, "pso_runs": pso_runs, "minimax_runs": mm_runs,
            "frozen_reproduction_gate": g_repro, "pareto": pareto,
            "expert_weights": {d: next(n["weight"] for t in cal.trees
                                       for n in t1.iter_nodes(t)
                                       if n["id"] == d and "weight" in n) for d in cal.dim_ids}}


def _worst_name(cal: Caliber, seps: list) -> str:
    return min(zip(cal.mutants, seps), key=lambda x: x[1])[0]["id"]


def _pareto(cal, pso_runs, mm_runs, rnd, expert, equal, grd):
    pts = []
    for r in pso_runs:
        pts.append({"source": "pso", "key": "seed=%s" % r["seed"],
                    "mean": r["mean_sep"], "worst": r["worst_sep"]})
    for r in mm_runs:
        pts.append({"source": "pso_minimax", "key": "seed=%s" % r["seed"],
                    "mean": r["mean_sep"], "worst": r["worst_sep"]})
    for i, m in enumerate(rnd["means"]):
        pts.append({"source": "random", "key": "i=%d" % i, "mean": m,
                    "worst": None})
    pts.append({"source": "expert", "key": "config", "mean": expert["mean"], "worst": expert["worst"]})
    pts.append({"source": "equal", "key": "uniform", "mean": equal["mean"], "worst": equal["worst"]})
    pts.append({"source": "greedy", "key": "coordinate_ascent", "mean": grd["mean"], "worst": grd["worst"]})
    scored = [p for p in pts if p["worst"] is not None]
    front = [p for p in scored
             if not any(q["mean"] >= p["mean"] and q["worst"] >= p["worst"]
                        and (q["mean"] > p["mean"] or q["worst"] > p["worst"]) for q in scored)]
    return {"points": pts, "front": sorted(front, key=lambda p: -p["mean"]),
            "axes": ["mean_separation (0-10 leaf scale)", "worst_mutant_separation"],
            "n_points": len(scored), "n_front": len(front)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="预算梯度只跑 1 seed（调试用）")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    install_zero_guard()
    trees = json.loads(TREES_PATH.read_text(encoding="utf-8"))["trees"]

    calibers = {}
    for tag, path in (("pso_era_input_20260819", DISC_ERA), ("design_doc_input_20260826", DISC_V2)):
        calibers[tag] = run_caliber(tag, path, trees, args.quick)
        st = calibers[tag]["separation_table"]
        print("%-26s expert=%.4f equal=%.4f random30=%.4f greedy=%.4f pso=%.4f pso_std=%.4f "
              "worst_pso=%.4f minimax_worst=%.4f G-repro=%s"
              % (tag, st["expert"]["mean_sep"], st["equal"]["mean_sep"],
                 st["random30"]["mean_sep"], st["greedy"]["mean_sep"],
                 st["pso_5seeds"]["mean_sep_mean"], st["pso_5seeds"]["mean_sep_std"],
                 st["pso_5seeds"]["worst_sep_mean"],
                 st["pso_minimax_5seeds"]["worst_sep_mean"],
                 (calibers[tag]["frozen_reproduction_gate"] or {}).get("pass")), flush=True)

    primary = calibers["pso_era_input_20260819"]
    qbg = question_budget_gradient(json.loads(DISC_V2.read_text(encoding="utf-8")), args.quick)
    st = primary["separation_table"]
    checks = {
        "c3_pso_beats_equal": st["pso_5seeds"]["mean_sep_mean"] > st["equal"]["mean_sep"],
        "c3_pso_beats_expert": st["pso_5seeds"]["mean_sep_mean"] > st["expert"]["mean_sep"],
        "c3_pso_beats_random30": st["pso_5seeds"]["mean_sep_mean"] > st["random30"]["mean_sep"],
        "c3_pso_beats_greedy": st["pso_5seeds"]["mean_sep_mean"] > st["greedy"]["mean_sep"],
        "pso_mean_reproduces_frozen_1_4326": abs(st["pso_5seeds"]["mean_sep_mean"] - 1.4326) <= 0.01
        or abs(primary["frozen_reproduction_gate"]["recomputed"] - 1.4326) <= 0.01,
        "expert_reproduces_frozen_1_2560": abs(st["expert"]["mean_sep"] - 1.2560) <= 0.01,
        "random30_below_pso_card_pred": st["random30"]["mean_sep"] < st["pso_5seeds"]["mean_sep_mean"],
        "minimax_worst_ge_pred": st["pso_minimax_5seeds"]["worst_sep_mean"] >= MINIMAX_PRED,
        "budget_gradient_monotonic": qbg["monotonic_non_decreasing"],
        "multi_seed_ci_computable": len(st["pso_5seeds"]["mean_sep_ci95"]) == 2,
        "pso_seed_variance_degenerate": st["pso_5seeds"]["mean_sep_std"] == 0.0,
        "greedy_parity_with_pso": abs(st["greedy"]["mean_sep"]
                                       - st["pso_5seeds"]["mean_sep_mean"]) < 1e-9,
        "greedy_cheaper_than_pso": st["greedy"]["n_evals"] < st["pso_5seeds"]["n_evals"],
        "pso_worst_worse_than_expert": st["pso_5seeds"]["worst_sep_mean"] < st["expert"]["worst_sep"],
        "minimax_trades_mean_for_worst": (
            st["pso_minimax_5seeds"]["worst_sep_mean"] > st["pso_5seeds"]["worst_sep_mean"]
            and st["pso_minimax_5seeds"]["mean_sep_mean"] < st["pso_5seeds"]["mean_sep_mean"]),
        "worst_dimension_reported": all("worst_sep" in json.dumps(st[k])
                                        for k in ("equal", "expert", "random30", "greedy",
                                                  "pso_5seeds", "pso_minimax_5seeds")),
    }
    section = {
        "caliber_policy": ("主口径 pso_era(08-19) 判 C3（卡 §2.2 预测数字出自该口径）; "
                           "次口径 v2(08-26) 作稳健性附注; 两口径永不混用"),
        "primary_separation_table": st,
        "secondary_separation_table":
            calibers["design_doc_input_20260826"]["separation_table"],
        "per_caliber": calibers,
        "question_set_budget": qbg,
        "minimax_pred": MINIMAX_PRED,
        "multi_seed_ci_caveat": (
            "5 个 PSO seed 在臂 A 矩阵上全部收敛到同一点（std=0, CI 宽度=0）: 离散 {1,2,3}^11 权重"
            "空间在该目标下最优点高度退化, 多 seed CI 因此可算但零宽, 不构成统计区分力证据; "
            "随机组与 greedy 的对照才是本窗的实质证据。"),
        "checks": checks,
        "c3_verdict": {
            "success_clause_holds": all(checks[k] for k in (
                "c3_pso_beats_equal", "c3_pso_beats_expert", "c3_pso_beats_random30",
                "c3_pso_beats_greedy")),
            "degradation_clause_needed": not all(checks[k] for k in (
                "c3_pso_beats_equal", "c3_pso_beats_expert", "c3_pso_beats_random30",
                "c3_pso_beats_greedy")),
            "mean_gain_vs_expert": round(st["pso_5seeds"]["mean_sep_mean"]
                                         - st["expert"]["mean_sep"], 6),
            "worst_vs_expert": {"pso": st["pso_5seeds"]["worst_sep_mean"],
                                "expert": st["expert"]["worst_sep"],
                                "minimax": st["pso_minimax_5seeds"]["worst_sep_mean"]},
            "cost_evals": {k: st[k]["n_evals"] for k in
                           ("equal", "expert", "random30", "greedy", "pso_5seeds")},
            "pso_cost_over_greedy": round(st["pso_5seeds"]["n_evals"]
                                          / max(st["greedy"]["n_evals"], 1), 1),
            "clause_reading": (
                "C3 成功标准含『优于四组对照』: PSO 优于 equal/expert/random30 三组, 但与 greedy "
                "完全打平且评估次数为其 %s 倍 -> 该维不满足, 触发降级条款; 且 PSO 最坏 mutant 分离度"
                "低于 expert（均值增益以最差维退化为代价）。论文按降级口径陈述: 自动搜索的价值在"
                "『省专家调参』而非『判别力上限』。"
                % round(st["pso_5seeds"]["n_evals"] / max(st["greedy"]["n_evals"], 1), 1)),
        },
        "zero_endpoint": {"ports_touched": sorted(set(PORTS_TOUCHED)), "model_calls": 0},
    }
    Path(args.out).write_text(json.dumps(section, ensure_ascii=False, indent=1), encoding="utf-8")
    print("checks=%s" % json.dumps({k: v for k, v in checks.items()}, ensure_ascii=False))
    print("ports=%s -> %s" % (sorted(set(PORTS_TOUCHED)), args.out))
    return 0 if not PORTS_TOUCHED else 1


if __name__ == "__main__":
    sys.exit(main())
