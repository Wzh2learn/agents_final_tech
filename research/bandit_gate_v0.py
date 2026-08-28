"""bandit 门 v0 离线 replay（台账 #10, 设计稿 2026-08-27_bandit_gate_v0_design.md）。

Thompson Sampling 于 (τ,ε) 六格, 批级奖励, 纯计算零端点（断言无网络调用）。
数据 = 实验 1 gated 臂 42 条金标（gain+collateral 实测）, 按轮次为批。
"""
import json
import random
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CKPT = REPO / "logs" / "graph" / "eval" / "vgmc_exp1_checkpoint.json"
OUT = REPO / "logs" / "graph" / "eval" / "bandit_gate_v0_eval.json"
GRID = [(t, e) for t in (0.05, 0.1, 0.2) for e in (0.0, 0.02)]
SEED = 20260827
PRIOR = (0.5, 0.5)  # Jeffreys; 生产 23 条无实测 ΔH, 仅作先验注记不作标签


def load_gold() -> list[dict]:
    c = json.loads(CKPT.read_text(encoding="utf-8"))
    sl = c["arm_gated"]["sugg_log"]
    gold = [s for s in sl if s.get("gain") is not None and s.get("collateral") is not None]
    return gold


def batch_reward(entries: list[dict], tau: float, eps: float) -> tuple[float, int]:
    acc = [s for s in entries if s["gain"] >= tau and s["collateral"] >= -eps]
    if not acc:
        return 0.0, 0  # 预注册: 空接受批 R=0（保守, 拒绝不记功）
    safe = 1.0 if all(s["collateral"] >= 0 for s in acc) else 0.0
    gain_rate = sum(1 for s in acc if s["gain"] >= tau) / len(acc)
    return safe * gain_rate, len(acc)


def main() -> int:
    assert "urllib" not in globals() and "requests" not in globals(), "零端点断言"
    gold = load_gold()
    rounds: dict[int, list[dict]] = {}
    for s in gold:
        rounds.setdefault(s["round"], []).append(s)
    rids = sorted(rounds)

    # --- Thompson 首跑（批=轮次, 4 决策点）
    rng = random.Random(SEED)
    post = {f"tau={t},eps={e}": list(PRIOR) for t, e in GRID}
    pulls = {k: 0 for k in post}
    rewards_log, ts_total = [], 0.0
    for r in rids:
        theta = {k: rng.betavariate(a, b) for k, (a, b) in post.items()}
        arm = max(theta, key=theta.get)
        tau, eps = [float(x.split("=")[1]) for x in arm.split(",")]
        R, n_acc = batch_reward(rounds[r], tau, eps)
        pulls[arm] += 1
        ts_total += R
        post[arm][0] += R > 0.999
        post[arm][1] += R < 0.001
        rewards_log.append({"round": r, "arm": arm, "theta": round(theta[arm], 4),
                            "reward": R, "n_accepted": n_acc})

    # --- 直接法: 每固定臂逐批反事实奖励
    direct = {}
    for t, e in GRID:
        k = f"tau={t},eps={e}"
        rs = [batch_reward(rounds[r], t, e)[0] for r in rids]
        direct[k] = {"mean_reward": round(sum(rs) / len(rs), 4), "per_round": rs}

    # --- 金标描述统计 + 生产先验注记
    prod = json.loads((REPO / "config" / "schema_suggestions.json").read_text(encoding="utf-8"))
    n_prod = len(prod) if isinstance(prod, list) else len(prod.get("suggestions", prod))
    out = {"meta": {"name": "bandit-gate-v0-replay", "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "design": "docs/experiments/2026-08-27_bandit_gate_v0_design.md",
                    "seed": SEED, "endpoint_calls": 0,
                    "gold_n": len(gold), "rounds": rids,
                    "production_prior_n": n_prod,
                    "conventions": "空接受批 R=0; Beta 更新按 R 二值化（>0.999/<0.001）; 生产 23 条无 ΔH 实测不作标签"},
           "thompson": {"pulls": pulls, "posterior": {k: {"alpha": a, "beta": b} for k, (a, b) in post.items()},
                        "total_reward": round(ts_total, 4), "trace": rewards_log},
           "direct": direct}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"gold": len(gold), "pulls": pulls, "ts_total": round(ts_total, 4),
                      "direct_best": max(direct, key=lambda k: direct[k]["mean_reward"]),
                      "out": str(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
