"""bandit 门前瞻验证（台账 #10, 设计稿 §2 评估协议照抄执行）。

holdout 体制 = 碰撞 C1（bandit 未见过的体制）; 固定门 (τ=0.1,ε=0.02) vs
bandit 门（TS 后验采样, 后验来自 08-27 replay 原样）在退化率/接受率两指标
直接法离线对照。零端点纯计算; 问题流固定为记录流（直法假设, 注记在案）。
"""
import importlib.util
import json
import random
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
SEED = 20260828
TAU_F, EPS_F = 0.1, 0.02


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def batch_reward(acc: list[dict]) -> float:
    if not acc:
        return 0.0
    safe = 1.0 if all(s["collateral"] >= 0 for s in acc) else 0.0
    return safe * (sum(1 for s in acc if s["gain"] >= 0) / len(acc))


def main() -> int:
    vg = load_module("vgmc_exp1", REPO / "research" / "vgmc_exp1.py")
    overlay = json.loads((EVAL / "vgmc_collision_overlay.json").read_text(encoding="utf-8"))
    corpus = vg.load_corpus(overlay)
    fix, meas = vg.split_uids(list(corpus.keys()))
    c1c = json.loads((EVAL / "vgmc_collision_C1_checkpoint.json").read_text(encoding="utf-8"))
    c1r = json.loads((EVAL / "vgmc_collision_C1_results.json").read_text(encoding="utf-8"))
    base_h = c1r["meta"]["baseline_no_rules"]["h_meas"]
    sl = c1c["arm_gated"]["sugg_log"]
    gold = [s for s in sl if s.get("gain") is not None]
    rounds: dict[int, list[dict]] = {}
    for s in gold:
        rounds.setdefault(s["round"], []).append(s)
    rids = sorted(rounds)

    def accept_of(entries, tau, eps):
        return [s for s in entries if s["gain"] >= tau and s["collateral"] >= -eps]

    def run_policy(chooser) -> tuple[dict, int, list]:
        rules: dict = {}
        n_acc, trace = 0, []
        for r in rids:
            arm = chooser(r)
            acc = accept_of(rounds[r], arm[0], arm[1])
            for s in acc:
                rules.setdefault(s["target"], [])
                if s["injected"] not in rules[s["target"]]:
                    rules[s["target"]].append(s["injected"])
            n_acc += len(acc)
            trace.append({"round": r, "arm": f"tau={arm[0]},eps={arm[1]}",
                          "reward": batch_reward(acc), "n_accepted": len(acc)})
        return rules, n_acc, trace

    # 固定门
    rules_f, nacc_f, _ = run_policy(lambda r: (TAU_F, EPS_F))
    h_f = vg.pool_h(meas, corpus, rules_f)
    anchor = c1r["arm_gated"]["h_meas_final"]
    assert abs(h_f - anchor) < 5e-6, f"固定门复演锚点失配: {h_f} vs {anchor}"  # 工件 6 位舍入容差

    # bandit 门（后验原样前瞻, 不做新训练; 逐批更新=前瞻协议）
    bt = json.loads((EVAL / "bandit_gate_v0_eval.json").read_text(encoding="utf-8"))
    post = {k: [v["alpha"], v["beta"]] for k, v in bt["thompson"]["posterior"].items()}
    rng = random.Random(SEED)

    def bandit_choose(r):
        theta = {k: rng.betavariate(a, b) for k, (a, b) in post.items()}
        arm = max(theta, key=theta.get)
        tau, eps = [float(x.split("=")[1]) for x in arm.split(",")]
        acc = accept_of(rounds[r], tau, eps)
        R = batch_reward(acc)
        post[arm][0] += R > 0.999
        post[arm][1] += R < 0.001
        return tau, eps
    rules_b, nacc_b, trace_b = run_policy(bandit_choose)
    h_b = vg.pool_h(meas, corpus, rules_b)

    n_sugg = len(sl)
    out = {"meta": {"name": "bandit-prospective-eval", "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "design": "docs/experiments/2026-08-27_bandit_gate_v0_design.md §2",
                    "holdout_regime": "collision_C1（bandit 未见体制）", "seed": SEED,
                    "endpoint_calls": 0, "n_suggestion_events": n_sugg,
                    "method": "直接法离线复演（问题流固定为记录流, 反事实增益取记录值）",
                    "anchor": f"固定门复演终值与 C1 工件逐位一致 ({anchor})"},
           "fixed_gate": {"tau": TAU_F, "eps": EPS_F, "n_accepted": nacc_f,
                          "acceptance_rate": round(nacc_f / n_sugg, 4),
                          "h_meas_final": round(h_f, 6),
                          "degradation_vs_baseline": round(base_h - h_f, 6)},
           "bandit_gate": {"n_accepted": nacc_b, "acceptance_rate": round(nacc_b / n_sugg, 4),
                           "h_meas_final": round(h_b, 6),
                           "degradation_vs_baseline": round(base_h - h_b, 6),
                           "posterior_final": {k: {"alpha": a, "beta": b}
                                               for k, (a, b) in post.items()},
                           "trace": trace_b}}
    (EVAL / "bandit_prospective_eval.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"anchor_ok": True,
                      "fixed": {"acc_rate": out["fixed_gate"]["acceptance_rate"],
                                "degrad": out["fixed_gate"]["degradation_vs_baseline"]},
                      "bandit": {"acc_rate": out["bandit_gate"]["acceptance_rate"],
                                 "degrad": out["bandit_gate"]["degradation_vs_baseline"]}},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
