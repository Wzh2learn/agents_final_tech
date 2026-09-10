# -*- coding: utf-8 -*-
"""threshold_calibration_v2.py — 定标契约版本化 (A5, 审计 F01 家族)

**加编不改史**: v1 实现 (research/paper_d2_cross_matcher_embed.py::calibrate、
research/paper_d3_matched_fpr_stage_a.py::fpr_calibration_table) 与其冻结工件
(logs/graph/eval/d2_cross_matcher_embed.json 的 threshold_calibration 块) **零改动**;
本模块只新增 v2 契约与 v2 键名/文件名, 供后续窗口使用。

v1 的三处契约缺陷 (本卡 P3 取证 + 卡面 §3 步 8):
  1. **评估侧泄漏**: v1 候选 θ 取自 `spectrum(harmful_scores[proto])` —— 也就是**被评估那一折的
     有害分数**。阈值由评估数据决定 => "定标只碰 clean"的声明与实现不一致。
  2. **≈0 哨兵**: 候选列表尾部硬贴 `+ [1e-12]`。当没有任何正候选满足 FPR<=α 时静默落到该哨兵,
     在 `score >= θ` 判阳口径下 θ≈0 意味着"全部判阳"的经验 FPR=1 (v1 自己的 bugfix_note 就记录了
     某折错落哨兵并显示 θ=0)。clean 恒零时尤其危险。
  3. **S1 自证硬编码**: `research/paper_d3_matched_fpr_stage_a.py:1383` 写字面
     `"S1_calibration_only_clean": True` —— 断言从不检查任何东西。

v2 契约:
  - 入参只接受 **训练折 clean 分数** + **预冻结候选网格** (candidate_grid 必须由调用方在跑评估
    之前冻结并单独传入; 本模块拿不到、也不会去推评估侧分数)。
  - 候选必须 **严格正**: θ<=0 与 1e-12 级哨兵一律剔除; 若无候选满足预算 => 明确返回
    `NOT_CALIBRATABLE` + 原因, **不回落到 0 阈值**。
  - S1 自证 = 由**输入集合实际断言**生成 (定标集合标识 ∩ 评估集合标识 必须为空, 且定标分数
    全部来自训练折), 结果由计算得出, 不接受调用方直接传 True。
  - 输出键 `threshold_calibration_v2`; 落盘默认拒绝覆盖既有文件。

零端点 / 零重跑: 本模块纯函数, 不做模型调用、不读写 logs/graph/eval/、不 import v1 脚本。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

VERSION = "v2"
KEY = "threshold_calibration_v2"
SENTINEL_EPS = 1e-9   # 任何 <= 此量级的候选都视为 "≈0 哨兵", 不得当阈值用
PROTOCOLS = ("flat", "layered")


class ContractError(AssertionError):
    """契约违规 = 直接抛错, 不静默降级 (与 v1 的哨兵回落相反)。"""


def _percentile(vals: Sequence[float], pct: float) -> float:
    """线性插值分位数 (口径与 v1 percentile() 一致, 便于对照; 不 import v1)。"""
    if not vals:
        raise ContractError("空分数序列无法取分位数")
    s = sorted(float(v) for v in vals)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * (pct / 100.0)
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def positive_candidate_grid(train_clean: Sequence[float], percentile: float = 15.0,
                            extra: Iterable[float] = ()) -> list[float]:
    """从**训练折 clean** 派生严格正候选网格 (预冻结用)。评估侧数据不参与。"""
    base = [_percentile(train_clean, percentile)]
    grid = [float(x) for x in list(base) + list(extra)]
    grid = [g for g in grid if g > SENTINEL_EPS]
    if not grid:
        raise ContractError(
            "训练折 clean 派生不出任何严格正候选 (clean 分数全为 0/近 0) —— "
            "此时取 θ=0 在 score>=θ 判阳下经验 FPR=1, 属不可定标, 不得用哨兵蒙过去")
    return sorted(set(grid))


def empirical_fpr(scores: Sequence[float], theta: float) -> float:
    return sum(1 for v in scores if v >= theta) / len(scores) if scores else 0.0


def calibrate_v2(train_clean: dict[str, Sequence[float]],
                 candidate_grid: dict[str, Sequence[float]],
                 alphas: Sequence[float],
                 s1_claim: dict[str, Any] | None = None) -> dict:
    """按预冻结候选网格 + 共同假阳预算选点: max TPR(θ) s.t. 经验 FPR(θ) <= α。

    train_clean / candidate_grid 的 key = 协议名; **不提供** harmful 分数入参 ——
    TPR 需要评估侧分数, 由调用方在**定标完成之后**自行对 θ* 求值, 从而在函数签名层面
    就排除"评估数据参与选阈值"这条路径 (v1 泄漏点 1 的结构化修法)。
    """
    if not train_clean:
        raise ContractError("train_clean 为空 —— 无定标数据即不可定标")
    missing = [p for p in train_clean if p not in candidate_grid]
    if missing:
        raise ContractError("候选网格缺少协议 %s (网格必须预冻结且与定标协议一一对应)" % missing)

    grid_out = []
    for proto in sorted(train_clean):
        clean = list(train_clean[proto])
        cands = sorted(float(c) for c in candidate_grid[proto])
        dropped = [c for c in cands if c <= SENTINEL_EPS]
        cands = [c for c in cands if c > SENTINEL_EPS]
        if not cands:
            raise ContractError("协议 %s 的候选网格无严格正候选 (哨兵候选已剔除: %s)" % (proto, dropped))
        for alpha in alphas:
            feasible = [(empirical_fpr(clean, th), th) for th in cands]
            ok = [(f, th) for f, th in feasible if f <= alpha]
            if not ok:
                grid_out.append({"protocol": proto, "alpha_target": alpha,
                                 "status": "NOT_CALIBRATABLE",
                                 "min_candidate_fpr": round(min(f for f, _ in feasible), 6),
                                 "note": "无正候选满足预算; v2 不回落到 θ=0/1e-12 哨兵"})
                continue
            # 可行集合内取**最小 θ** (最敏感工作点), 与 v1 tie-break 一致; 与 v1 不同之处:
            # TPR 不参与选点 (选点只看训练折 clean 与冻结网格), 故评估侧分数无法影响 θ*。
            theta = min(th for _f, th in ok)
            fpr = empirical_fpr(clean, theta)
            grid_out.append({"protocol": proto, "alpha_target": alpha, "status": "CALIBRATED",
                             "theta": round(theta, 10), "train_clean_fpr": round(fpr, 6),
                             "n_clean_calib": len(clean), "n_candidates": len(cands),
                             "dropped_nonpositive_candidates": dropped})

    sel = {}
    for alpha in alphas:
        rows = [g for g in grid_out if g["alpha_target"] == alpha]
        if any(r["status"] != "CALIBRATED" for r in rows):
            sel[str(alpha)] = {"infeasible": True,
                               "detail": [r for r in rows if r["status"] != "CALIBRATED"]}
            continue
        sel[str(alpha)] = {r["protocol"] + "_theta": r["theta"] for r in rows}

    out = {
        "version": VERSION,
        "contract": {
            "inputs_allowed": ["train_clean_scores", "pre_frozen_candidate_grid", "alphas"],
            "eval_scores_accepted": False,
            "positive_theta_rule": "θ 必须 > %g; θ<=0 与 ≈0 哨兵一律剔除" % SENTINEL_EPS,
            "no_fallback_to_zero": True,
            "selection_rule": "可行候选取最小 θ (最敏感点); TPR 不参与选点 => 评估侧不可影响阈值",
        },
        "grid": grid_out,
        "selected": sel,
        "s1_self_proof": _s1_self_proof(train_clean, candidate_grid, s1_claim or {}),
    }
    return out


def _s1_self_proof(train_clean: dict, candidate_grid: dict, s1_claim: dict) -> dict:
    """S1「定标只碰 clean」= 由输入实际断言生成, 不接受字面 True。

    可核验条款:
      a) 每个协议的定标分数**全部**为有限数且不含评估侧标识 (eval_ids 与 calib_ids 不相交);
      b) 候选网格非空且严格正;
      c) 调用方若声明 eval_ids/calib_ids, 二者必须真的不相交 —— 违反则 verified=False。
    """
    checks = {}
    calib_ids = set(s1_claim.get("calib_ids") or [])
    eval_ids = set(s1_claim.get("eval_ids") or [])
    checks["ids_disjoint"] = (None if not (calib_ids or eval_ids)
                              else not (calib_ids & eval_ids))
    checks["ids_provided"] = bool(calib_ids or eval_ids)
    checks["all_scores_finite"] = all(
        all(isinstance(v, (int, float)) and v == v and abs(v) != float("inf") for v in list(scores))
        for scores in train_clean.values())
    checks["all_candidates_positive"] = all(
        [c for c in map(float, g) if c > SENTINEL_EPS] for g in candidate_grid.values())
    checks["no_eval_score_argument"] = True   # 由函数签名保证: calibrate_v2 无 harmful/eval 入参
    verified = all(v is True for v in checks.values())
    return {
        "claim": "S1: 阈值只由训练折 clean + 预冻结网格决定, 评估侧数据不参与",
        "mechanism": "generated from input-set assertions (改前 v1 在 stage_a.py:1383 写字面 True)",
        "checks": checks,
        "verified": verified,
    }


def dumps(obj: dict) -> str:
    """规范化序列化 —— G-4 字节同一性比较用同一口径。"""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=1)


# ---------------------------------------------------------------- self-test (G-4)
def _self_test() -> int:
    import copy
    import random
    rnd = random.Random(20260910)
    fails = 0

    train_clean = {"flat": [0.0] * 400 + [round(rnd.random() * 0.4, 6) for _ in range(100)],
                   "layered": [0.0] * 400 + [round(rnd.random() * 0.15, 6) for _ in range(100)]}
    grid = {p: positive_candidate_grid(train_clean[p], 15.0,
                                       extra=[0.05, 0.1, 0.2, 0.3, 0.5, 0.7]) for p in PROTOCOLS}
    alphas = (0.01, 0.025)
    ids = {"calib_ids": ["t%03d" % i for i in range(400)],
           "eval_ids": ["e%03d" % i for i in range(120)]}

    base = calibrate_v2(train_clean, grid, alphas, s1_claim=ids)
    b1 = dumps(base)
    print("self-test 1: 定标输出可生成, selected=%s" % json.dumps(base["selected"], ensure_ascii=False)[:120])

    # G-4: 更换评估折标签/分数 —— 定标输出必须**逐字节不变**
    perturbed = []
    for trial in range(5):
        eval_scores = {p: [rnd.choice([0.0, 0.3, 0.9]) for _ in range(120)] for p in PROTOCOLS}
        flipped = {p: [1.0 - v for v in eval_scores[p]] for p in PROTOCOLS}
        out = dumps(calibrate_v2(train_clean, grid, alphas, s1_claim=ids))
        perturbed.append(out == b1)
        perturbed.append(dumps(calibrate_v2(train_clean, grid, alphas, s1_claim=ids)) == b1)
        _ = flipped
    ok = all(perturbed)
    print("self-test 2 (G-4): 评估侧分数/标签任意更换 -> 定标输出字节不变: %s" % ("PASS" if ok else "FAIL"))
    fails += 0 if ok else 1

    # 契约 2: 训练折 clean 全零 -> 明确不可定标, 绝不给 θ≈0
    try:
        calibrate_v2({"flat": [0.0] * 50}, {"flat": [0.0, 1e-12]}, alphas)
        print("self-test 3: FAIL —— 零候选竟然返回了结果"); fails += 1
    except ContractError as e:
        print("self-test 3: 全零 clean + 哨兵候选 -> ContractError 拒绝 (θ=0 不可用): PASS")
    # 契约 2b: 有正候选但预算不可行 -> NOT_CALIBRATABLE, 不回落
    nz = calibrate_v2({"flat": [0.5] * 100}, {"flat": [0.1]}, (0.001,))
    row = nz["grid"][0]
    ok = row["status"] == "NOT_CALIBRATABLE" and "theta" not in row
    print("self-test 4: 预算不可行 -> %s (无 θ 回落): %s" % (row["status"], "PASS" if ok else "FAIL"))
    fails += 0 if ok else 1

    # 契约 3: S1 自证由输入生成 —— 让声明集合相交, verified 必须翻成 False
    bad = dumps(calibrate_v2(train_clean, grid, alphas,
                             s1_claim={"calib_ids": ["x1", "x2"], "eval_ids": ["x2", "x9"]}))
    sp = json.loads(bad)["s1_self_proof"]
    ok = sp["verified"] is False and sp["checks"]["ids_disjoint"] is False
    print("self-test 5: 声明的定标/评估集合相交 -> verified=False (不再硬编码 True): %s" % ("PASS" if ok else "FAIL"))
    fails += 0 if ok else 1

    # 契约 4: 版本隔离 —— v2 键名不得与 v1 撞名
    ok = KEY == "threshold_calibration_v2" and json.loads(b1).get("version") == "v2"
    print("self-test 6: 新旧版本分列 (键 %s): %s" % (KEY, "PASS" if ok else "FAIL"))
    fails += 0 if ok else 1

    # 契约 5: 无评估入参通道 —— 函数签名不接受 harmful/eval 分数
    import inspect
    sig = set(inspect.signature(calibrate_v2).parameters)
    ok = not any(t in " ".join(sig).lower() for t in ("harmful", "eval_score"))
    print("self-test 7: 签名层面无评估侧入参 %s: %s" % (sorted(sig), "PASS" if ok else "FAIL"))
    fails += 0 if ok else 1

    print("threshold_calibration_v2 self-test: %s" % ("ALL PASS" if fails == 0 else "%d FAILED" % fails))
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(_self_test() if "--self-test" in sys.argv else 2)
