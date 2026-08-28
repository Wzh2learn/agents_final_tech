#!/usr/bin/env python3
"""B 扩碰撞判定（E1-E4 + 配对 bootstrap CI + 功效注记 + E3 闭环机械触发）。

E3 闭环判据（用户卡, 冻结）: ΔV(ACC) CI 不含 0 且点估计 ≥0.05 → 伤害显形 → 版本 B→A。
设计稿辅判据并记: |ΔV(ACC)|≥0.15 且 |ΔV(H)|>0.005。
"""
import importlib.util
import json
import random
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
SEED, N_BOOT, EPS = 20260827, 2000, 0.02
RUNS = {"EXP_u05": ("vgmc_collision_EXP_u05", "ungated", 0.5),
        "EXP_u10": ("vgmc_collision_EXP_u10", "ungated", 1.0),
        "EXP_g10": ("vgmc_collision_EXP_g10", "gated", 1.0)}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def paired_bootstrap(diffs):
    rng = random.Random(SEED)
    n = len(diffs)
    boots = sorted(sum(rng.choices(diffs, k=n)) / n for _ in range(N_BOOT))
    return boots[int(0.025 * N_BOOT)], boots[int(0.975 * N_BOOT)]


def collision_acc_per_table(vg, corpus, meas, rules):
    out = {}
    for u in meas:
        rec = corpus[u]
        cols = [e for e in rec["entries"] if e.get("type") == "collision"]
        if not cols:
            continue
        mapping, _ = vg.mp.map_headers(rec["inj_header"], vg.schema_table_for(rec, rules))
        rev = {src: std for std, src in mapping.items()}
        ok = sum(1 for e in cols
                 if rev.get(rec["inj_header"][e["col"]]) == e["original"])
        out[u] = (ok, len(cols))
    return out


def main() -> int:
    vg = load_module("vgmc_exp1", REPO / "research" / "vgmc_exp1.py")
    ovl10 = json.loads((EVAL / "vgmc_collision_overlay_v2_rho10.json").read_text(encoding="utf-8"))
    corpus10 = vg.load_corpus(ovl10)
    ovl05 = json.loads((EVAL / "vgmc_collision_overlay_v2_rho05.json").read_text(encoding="utf-8"))
    corpus05 = vg.load_corpus(ovl05)
    fix, meas = vg.split_uids(list(corpus10.keys()))
    advmap = json.loads((EVAL / "vgmc_adv_injection_map.json").read_text(encoding="utf-8"))
    adv_keys = {(c["uid"], c["col"]) for c in advmap["columns"] if c.get("adv_target")}

    rows = {}
    for name, (stem, arm_name, rho) in RUNS.items():
        corpus = corpus10 if rho == 1.0 else corpus05
        res = json.loads((EVAL / f"{stem}_results.json").read_text(encoding="utf-8"))
        ck = json.loads((EVAL / f"{stem}_checkpoint.json").read_text(encoding="utf-8"))
        arm = res["arm_" + arm_name]
        sl = ck["arm_" + arm_name]["sugg_log"]
        base = res["meta"]["baseline_no_rules"]["h_meas"]
        acc_tbl = collision_acc_per_table(vg, corpus, meas, ck["arm_" + arm_name]["rules"])
        n_ok = sum(v[0] for v in acc_tbl.values()); n_all = sum(v[1] for v in acc_tbl.values())
        adv_ev = [s for s in sl if (s["uid"], s["col"]) in adv_keys and s.get("gain") is not None]
        adv_acc = [s for s in adv_ev if s.get("accepted")]
        rows[name] = {
            "arm": arm_name, "rho": rho, "h_baseline": base, "h_final": arm["h_meas_final"],
            "delta_h": round(arm["h_meas_final"] - base, 6),
            "coll_acc": round(n_ok / n_all, 4) if n_all else None,
            "coll_n_tables": len(acc_tbl), "coll_n_cols": n_all,
            "fixation_rate": arm["fixation_rate"],
            "adv_events": len(adv_ev), "adv_accepted": len(adv_acc),
            "gate_reject_rate": round(1 - len(adv_acc) / len(adv_ev), 4) if adv_ev else None,
            "_acc_tbl": acc_tbl, "_rules": ck["arm_" + arm_name]["rules"], "_corpus": corpus}

    # E1 单调（无门控臂, ρ0 参考 = ADV_u10 数据引用）
    adv_u10 = json.loads((EVAL / "vgmc_collision_ADV_u10_results.json").read_text(encoding="utf-8"))
    ref_base = adv_u10["meta"]["baseline_no_rules"]["h_meas"]
    ref_dh = adv_u10["arm_ungated"]["h_meas_final"] - ref_base
    e1 = {"rho0_ref_delta_h": round(ref_dh, 6),
          "rho05_delta_h": rows["EXP_u05"]["delta_h"],
          "rho10_delta_h": rows["EXP_u10"]["delta_h"],
          "monotonic_H": rows["EXP_u10"]["delta_h"] <= rows["EXP_u05"]["delta_h"],
          "rho0_ref_coll_acc": adv_u10["arm_ungated"]["collision_acc"],
          "rho05_coll_acc": rows["EXP_u05"]["coll_acc"],
          "rho10_coll_acc": rows["EXP_u10"]["coll_acc"],
          "monotonic_ACC": rows["EXP_u10"]["coll_acc"] <= rows["EXP_u05"]["coll_acc"]}

    # E3 配对 bootstrap（ρ=1.0: gated vs ungated, 逐表）
    g, u = rows["EXP_g10"], rows["EXP_u10"]
    common = [t for t in g["_acc_tbl"] if t in u["_acc_tbl"]]
    d_acc = [g["_acc_tbl"][t][0] / g["_acc_tbl"][t][1] - u["_acc_tbl"][t][0] / u["_acc_tbl"][t][1]
             for t in common]
    d_h = [vg.table_h(corpus10[t], g["_rules"]) - vg.table_h(corpus10[t], u["_rules"])
           for t in meas]
    lo_a, hi_a = paired_bootstrap(d_acc)
    lo_h, hi_h = paired_bootstrap(d_h)
    dv_acc = sum(d_acc) / len(d_acc) if d_acc else 0.0
    dv_h = sum(d_h) / len(d_h)
    card_trigger = not (lo_a <= 0 <= hi_a) and dv_acc >= 0.05
    design_e3 = abs(dv_acc) >= 0.15 and abs(dv_h) > 0.005
    e3 = {"dV_ACC": round(dv_acc, 4), "dV_ACC_ci95": [round(lo_a, 4), round(hi_a, 4)],
          "dV_H": round(dv_h, 6), "dV_H_ci95": [round(lo_h, 6), round(hi_h, 6)],
          "n_tables_ACC": len(common), "n_tables_H": len(d_h),
          "power_note": f"碰撞表数 12（C0 基线）→ {len(common)}（扩容后, +{len(common)-12}）",
          "card_trigger_B_to_A": card_trigger,
          "design_e3_both": design_e3}

    # E2 有界
    sigma = EPS * g["adv_accepted"]
    e2 = {"gated_abs_delta_h": abs(g["delta_h"]), "sigma_eps": round(sigma, 6),
          "holds": abs(g["delta_h"]) <= sigma or g["delta_h"] > 0}

    # E4 null 分支
    e4 = {"fired": abs(dv_acc) < 0.005 and abs(dv_h) < 0.005}

    out = {"meta": {"name": "vgmc-expansion-curve", "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "seed_boot": SEED, "n_boot": N_BOOT, "endpoint_calls": 0},
           "rows": {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")}
                    for k, v in rows.items()},
           "E1": e1, "E2": e2, "E3": e3, "E4": e4,
           "verdict": ("伤害显形 → 版本 B 切 A 机械触发（判据冻结不溯及）" if card_trigger
                       else "未显形 → 版本 B 维持, 下一步另行裁定（如实记账）")}
    (EVAL / "vgmc_expansion_curve.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"E1": e1, "E2": e2, "E3": e3, "E4": e4, "verdict": out["verdict"],
                      "rows": {k: {kk: vv for kk, vv in v.items() if not kk.startswith('_')} for k, v in rows.items()}},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
