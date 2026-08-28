"""小 A 基线机械判定（段 D, 设计稿 §4）: ΔH + 配对 bootstrap CI vs no-gate 对照。

判据（预注册）: |ΔH| < 0.005 且 CI 跨 0 → 与 no-gate 不可分;
ΔH >= 0.02 → 基线有效需与 VGRM 直接对比; 其间 → 弱信号。零端点纯计算。
"""
import importlib.util
import json
import random
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
SEED, N_BOOT = 20260827, 2000
BASELINES = ["fewshot", "mem0", "awm"]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> int:
    vg = load_module("vgmc_exp1", REPO / "research" / "vgmc_exp1.py")
    corpus = vg.load_corpus()
    fix, meas = vg.split_uids(list(corpus.keys()))
    rules0 = json.loads((EVAL / "vgmc_exp1_checkpoint.json").read_text(encoding="utf-8"))
    ctrl = rules0["arm_ungated"]["rules"]
    ctrl_h = [vg.table_h(corpus[u], ctrl) for u in meas]
    rows, verdicts = [], {}
    for b in BASELINES:
        ck = json.loads((EVAL / f"vgmc_baseline_{b}_checkpoint.json").read_text(encoding="utf-8"))
        st = ck["arm_ungated"]
        rb = st["rules"]
        hb = [vg.table_h(corpus[u], rb) for u in meas]
        d = [x - y for x, y in zip(hb, ctrl_h)]
        rng = random.Random(SEED)
        boots = []
        for _ in range(N_BOOT):
            smp = rng.choices(d, k=len(d))
            boots.append(sum(smp) / len(smp))
        boots.sort()
        lo, hi = boots[int(0.025 * N_BOOT)], boots[int(0.975 * N_BOOT)]
        mean_d = sum(d) / len(d)
        if abs(mean_d) < 0.005 and lo <= 0 <= hi:
            v = "与 no-gate 不可分"
        elif mean_d >= 0.02:
            v = "基线有效, 需与 VGRM 直接对比"
        else:
            v = "弱信号"
        verdicts[b] = v
        rows.append({"baseline": b, "h_meas_final": round(sum(hb) / len(hb), 6),
                     "delta_h_vs_nogate": round(mean_d, 6), "ci95": [round(lo, 6), round(hi, 6)],
                     "n_memory_items": len(st.get("memory", [])),
                     "n_suggestions": len(st.get("sugg_log", [])), "verdict": v})
    out = {"meta": {"name": "vgmc-baseline-curve", "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "design": "docs/experiments/2026-08-27_small_a_baseline_protocol_design.md",
                    "control": "实验 1 ungated (no-gate), H_meas 终值 0.589048",
                    "seed": SEED, "n_boot": N_BOOT, "endpoint_calls": 0,
                    "window": "2026-08-28 #BASELINE-WINDOW"},
           "rows": rows, "verdicts": verdicts}
    (EVAL / "vgmc_baseline_curve.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                                   encoding="utf-8")
    print(json.dumps({"verdicts": verdicts, "rows": rows}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
