#!/usr/bin/env python3
"""科研线 Phase 1（纯计算零端点）: ① 注入级正确性回填 + H null 裁定
② ΔV 双指标配对 bootstrap CI ③ oracle 上界/匹配器下界 headroom。

正确性定义: 注入表头在终局规则下映射回其真值 canonical。
bootstrap: 表级配对重采样, seed=20260827, n=2000, 百分位法。
"""
import importlib.util
import json
import random
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
SEED, N_BOOT = 20260827, 2000
REGIMES = [
    ("exp1", "vgmc_exp1", False),
    ("noise_L1s42", "vgmc_noise_L1s42", False),
    ("noise_L1s43", "vgmc_noise_L1s43", False),
    ("noise_L2", "vgmc_noise_L2", False),
    ("noise_L3", "vgmc_noise_L3", False),
    ("baseline_fewshot", "vgmc_baseline_fewshot", False),
    ("baseline_mem0", "vgmc_baseline_mem0", False),
    ("baseline_awm", "vgmc_baseline_awm", False),
    ("collision_C0", "vgmc_collision_C0", True),
    ("collision_C1", "vgmc_collision_C1", True),
    ("ADV_g10", "vgmc_collision_ADV", True),
    ("ADV_u05", "vgmc_collision_ADV_u05", True),
    ("ADV_u10", "vgmc_collision_ADV_u10", True),
]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def per_table_correctness(vg, corpus, uids, rules, collision_only=False):
    """每表注入级正确率: (正确数, 注入总数); collision_only=仅移植碰撞条目。"""
    out = {}
    for uid in uids:
        rec = corpus[uid]
        if not rec["entries"]:
            continue
        mapping, _ = vg.mp.map_headers(rec["inj_header"], vg.schema_table_for(rec, rules))
        rev = {src: std for std, src in mapping.items()}
        n = ok = 0
        for e in rec["entries"]:
            if collision_only and e.get("type") != "collision":
                continue
            n += 1
            true_c = next((c for c in rec["canonicals"]
                           if vg.mp.normalize_header(c) == vg.mp.normalize_header(e["original"])), None)
            if rev.get(rec["inj_header"][e["col"]]) == true_c:
                ok += 1
        out[uid] = (ok, n)
    return out


def paired_bootstrap(diffs):
    rng = random.Random(SEED)
    n = len(diffs)
    boots = sorted(sum(rng.choices(diffs, k=n)) / n for _ in range(N_BOOT))
    return boots[int(0.025 * N_BOOT)], boots[int(0.975 * N_BOOT)]


def main() -> int:
    vg = load_module("vgmc_exp1", REPO / "research" / "vgmc_exp1.py")
    overlay = json.loads((EVAL / "vgmc_collision_overlay.json").read_text(encoding="utf-8"))
    corpus_plain = vg.load_corpus()
    corpus_ovl = vg.load_corpus(overlay)
    fix, meas = vg.split_uids(list(corpus_plain.keys()))
    rows, dv_rows, headroom, corr_store = {}, [], {}, {}

    # oracle 规则: 真值别名全注入（plain 与 overlay 两口径）
    def oracle_rules(corpus):
        r = {}
        for uid, rec in corpus.items():
            for e in rec["entries"]:
                true_c = next((c for c in rec["canonicals"]
                               if vg.mp.normalize_header(c) == vg.mp.normalize_header(e["original"])), None)
                if true_c:
                    r.setdefault(true_c, [])
                    h = rec["inj_header"][e["col"]]
                    if h not in r[true_c]:
                        r[true_c].append(h)
        return r

    for name, stem, use_ovl in REGIMES:
        corpus = corpus_ovl if use_ovl else corpus_plain
        ck = json.loads((EVAL / f"{stem}_checkpoint.json").read_text(encoding="utf-8"))
        res = json.loads((EVAL / f"{stem}_results.json").read_text(encoding="utf-8"))
        row = {}
        for arm in ck:
            if not arm.startswith("arm_"):
                continue
            an = arm[4:]
            rules = ck[arm]["rules"]
            corr_all = per_table_correctness(vg, corpus, list(corpus.keys()), rules)
            corr_meas = {u: corr_all[u] for u in meas if u in corr_all}
            ok = sum(v[0] for v in corr_all.values()); n = sum(v[1] for v in corr_all.values())
            okm = sum(v[0] for v in corr_meas.values()); nm = sum(v[1] for v in corr_meas.values())
            row[an] = {"acc_all": round(ok / n, 4) if n else None,
                       "acc_meas": round(okm / nm, 4) if nm else None,
                       "n_inj": n, "h_final": res["arm_" + an]["h_meas_final"]}
            corr_store[(name, an)] = corr_meas
        rows[name] = row
        # ΔV 配对 bootstrap（两臂体制; 碰撞体制用碰撞列子集 = 判别性度量）
        if "gated" in row and "ungated" in row:
            if use_ovl:
                cg = per_table_correctness(vg, corpus, meas, ck["arm_gated"]["rules"], True)
                cu = per_table_correctness(vg, corpus, meas, ck["arm_ungated"]["rules"], True)
                ug = [cg[u][0] / cg[u][1] - cu[u][0] / cu[u][1] for u in cg if u in cu and cg[u][1] > 0]
                acc_note = "碰撞列子集"
            else:
                ug = [corr_store[(name, "gated")][u][0] / corr_store[(name, "gated")][u][1]
                      - corr_store[(name, "ungated")][u][0] / corr_store[(name, "ungated")][u][1]
                      for u in meas if corr_store[(name, "gated")][u][1] > 0]
                acc_note = "全注入"
            uh = [vg.table_h(corpus[u], ck["arm_gated"]["rules"]) - vg.table_h(corpus[u], ck["arm_ungated"]["rules"])
                  for u in meas]
            lo_a, hi_a = paired_bootstrap(uh)
            lo_c, hi_c = paired_bootstrap(ug) if ug else (None, None)
            dv_rows.append({"regime": name,
                            "dV_H": round(sum(uh) / len(uh), 6), "dV_H_ci95": [round(lo_a, 6), round(hi_a, 6)],
                            "dV_ACC": round(sum(ug) / len(ug), 6) if ug else None,
                            "dV_ACC_ci95": [round(lo_c, 6), round(hi_c, 6)] if ug else None,
                            "acc_scope": acc_note, "n_tables_H": len(uh), "n_tables_ACC": len(ug)})
    # ADV 跨跑批配对（g10 gated vs u10 ungated, 碰撞列子集）
    ck_g = json.loads((EVAL / "vgmc_collision_ADV_checkpoint.json").read_text(encoding="utf-8"))
    ck_u = json.loads((EVAL / "vgmc_collision_ADV_u10_checkpoint.json").read_text(encoding="utf-8"))
    cg = per_table_correctness(vg, corpus_ovl, meas, ck_g["arm_gated"]["rules"], True)
    cu = per_table_correctness(vg, corpus_ovl, meas, ck_u["arm_ungated"]["rules"], True)
    ug = [cg[u][0] / cg[u][1] - cu[u][0] / cu[u][1] for u in cg if u in cu and cg[u][1] > 0]
    uh = [vg.table_h(corpus_ovl[u], ck_g["arm_gated"]["rules"]) - vg.table_h(corpus_ovl[u], ck_u["arm_ungated"]["rules"])
          for u in meas]
    lo_a, hi_a = paired_bootstrap(uh)
    lo_c, hi_c = paired_bootstrap(ug)
    dv_rows.append({"regime": "ADV_g10_vs_u10", "dV_H": round(sum(uh) / len(uh), 6),
                    "dV_H_ci95": [round(lo_a, 6), round(hi_a, 6)],
                    "dV_ACC": round(sum(ug) / len(ug), 6), "dV_ACC_ci95": [round(lo_c, 6), round(hi_c, 6)],
                    "acc_scope": "碰撞列子集", "n_tables_H": len(uh), "n_tables_ACC": len(ug)})

    # headroom: oracle 上界 + 匹配器下界
    for tag, corpus in (("plain", corpus_plain), ("overlay", corpus_ovl)):
        orc = oracle_rules(corpus)
        h_orc_meas = vg.pool_h(meas, corpus, orc)
        h_base_meas = vg.pool_h(meas, corpus, {})
        corr_orc = per_table_correctness(vg, corpus, meas, orc)
        acc_orc = sum(v[0] for v in corr_orc.values()) / sum(v[1] for v in corr_orc.values())
        headroom[tag] = {"h_oracle_meas": round(h_orc_meas, 6),
                         "h_baseline_meas": round(h_base_meas, 6),
                         "acc_oracle_meas": round(acc_orc, 6)}

    # H null 裁定: 终值 H 相同的臂对, ACC 是否分离
    verdicts = []
    for name, row in rows.items():
        if "gated" in row and "ungated" in row and abs(row["gated"]["h_final"] - row["ungated"]["h_final"]) < 0.005:
            dacc = row["gated"]["acc_all"] - row["ungated"]["acc_all"]
            verdicts.append({"regime": name, "h_pair_same": True,
                             "acc_gated": row["gated"]["acc_all"], "acc_ungated": row["ungated"]["acc_all"],
                             "d_acc": round(dacc, 4),
                             "verdict": "H null 非真 null（ACC 分离 ≥0.02）" if abs(dacc) >= 0.02
                             else "H null = 真 null（ACC 同水平）"})
    out = {"meta": {"name": "p1-correctness-backfill", "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "seed": SEED, "n_boot": N_BOOT, "endpoint_calls": 0,
                    "definition": "注入级正确性 = 注入表头映射回真值 canonical（逐表逐列）"},
           "per_regime": rows, "dV_bootstrap": dv_rows, "headroom": headroom,
           "h_null_verdicts": verdicts}
    (EVAL / "p1_correctness_backfill.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"dV": dv_rows, "headroom": headroom, "verdicts": verdicts},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
