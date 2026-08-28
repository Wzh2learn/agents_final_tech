"""对抗臂三预测机械判定（#13 设计稿 §1）+ T2 回填坐标。零端点纯计算。

① 无门控 ΔH<0 且 0.5→1.0 单调降
② 门控 |ΔH| ≤ Σε（Σε = ε × 门控接受的对抗建议数）
③ 门拒对抗建议 ≥80%（<80% = 过度自信利用失效模式）
"""
import importlib.util
import json
import random
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
TAU, EPS = 0.1, 0.02
RUNS = [("gated_1.0", "vgmc_collision_ADV", "gated"),
        ("ungated_0.5", "vgmc_collision_ADV_u05", "ungated"),
        ("ungated_1.0", "vgmc_collision_ADV_u10", "ungated")]


SEED_BT, N_BOOT_BT = 20260827, 2000


def paired_bootstrap(diffs):
    """表级配对重采样 95% CI（与 p1_correctness_backfill 同口径）。"""
    rng = random.Random(SEED_BT)
    n = len(diffs)
    boots = sorted(sum(rng.choices(diffs, k=n)) / n for _ in range(N_BOOT_BT))
    return boots[int(0.025 * N_BOOT_BT)], boots[int(0.975 * N_BOOT_BT)]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> int:
    vg = load_module("vgmc_exp1", REPO / "research" / "vgmc_exp1.py")
    overlay = json.loads((EVAL / "vgmc_collision_overlay.json").read_text(encoding="utf-8"))
    corpus = vg.load_corpus(overlay)
    fix, meas = vg.split_uids(list(corpus.keys()))
    advmap = json.loads((EVAL / "vgmc_adv_injection_map.json").read_text(encoding="utf-8"))
    adv_cols = {c["col"] for c in advmap["columns"]}
    adv_set = {(c["uid"], c["col"]) for c in advmap["columns"] if c.get("adv_target")}

    rows = {}
    for label, stem, arm_name in RUNS:
        res = json.loads((EVAL / f"{stem}_results.json").read_text(encoding="utf-8"))
        ck = json.loads((EVAL / f"{stem}_checkpoint.json").read_text(encoding="utf-8"))
        arm = res["arm_" + arm_name]
        sl = ck["arm_" + arm_name]["sugg_log"]
        base = res["meta"]["baseline_no_rules"]["h_meas"]
        final = arm["h_meas_final"]
        adv_events = [s for s in sl if (s["uid"], s["col"]) in adv_set and s.get("gain") is not None]
        adv_acc = [s for s in adv_events if s.get("accepted")]
        rules = ck["arm_" + arm_name]["rules"]
        n_adv = n_adv_ok = 0
        for uid, ci in sorted(adv_set):
            rec = corpus[uid]
            mapping, _ = vg.mp.map_headers(rec["inj_header"], vg.schema_table_for(rec, rules))
            rev = {src: std for std, src in mapping.items()}
            true_c = next((c["true_canonical"] for c in advmap["columns"]
                           if c["uid"] == uid and c["col"] == ci), None)
            n_adv += 1
            if rev.get(rec["inj_header"][ci]) == true_c:
                n_adv_ok += 1
        rows[label] = {
            "arm": arm_name, "h_baseline": base, "h_final": final,
            "delta_h": round(final - base, 6),
            "collision_acc": arm.get("collision_acc"),
            "acc_adversarial_subset": round(n_adv_ok / n_adv, 4) if n_adv else None,
            "fixation_rate": arm["fixation_rate"],
            "adv_events": len(adv_events), "adv_accepted": len(adv_acc),
            "gate_reject_rate": round(1 - len(adv_acc) / len(adv_events), 4) if adv_events else None,
            "sigma_eps": round(EPS * len(adv_acc), 6),
            "n_suggestions": arm["n_suggestions"],
            "meta_noise": res["meta"]["noise"]["level"], "meta_adv_rate": res["meta"]["adversarial"]["rate"]}
    g, u05, u10 = rows["gated_1.0"], rows["ungated_0.5"], rows["ungated_1.0"]
    p1 = {"u05_delta_h": u05["delta_h"], "u10_delta_h": u10["delta_h"],
          "both_negative": u05["delta_h"] < 0 and u10["delta_h"] < 0,
          "monotonic_decrease": u10["delta_h"] <= u05["delta_h"]}
    p2 = {"gated_abs_delta_h": abs(g["delta_h"]), "sigma_eps": g["sigma_eps"],
          "holds": abs(g["delta_h"]) <= g["sigma_eps"]}
    p3 = {"gate_reject_rate": g["gate_reject_rate"], "threshold": 0.80,
          "holds": (g["gate_reject_rate"] or 0) >= 0.80,
          "failure_mode": None if (g["gate_reject_rate"] or 0) >= 0.80 else "过度自信利用失效模式（collateral 无碰撞信号, ε 维下界发现）"}
    out = {"meta": {"name": "vgmc-adv-curve", "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "design": "docs/experiments/2026-08-28_adversarial_suggester_arm_design.md",
                    "adv_seed": advmap["meta"]["seed"], "k": advmap["meta"]["k"],
                    "endpoint_calls": 0},
           "rows": rows, "P1": p1, "P2": p2, "P3": p3}
    (EVAL / "vgmc_adv_curve.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                              encoding="utf-8")
    print(json.dumps({"P1": p1, "P2": p2, "P3": p3,
                      "rows": {k: {"dH": v["delta_h"], "acc_adv": v["acc_adversarial_subset"],
                                   "gate_rej": v["gate_reject_rate"]} for k, v in rows.items()}},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
