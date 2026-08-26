#!/usr/bin/env python3
"""K2 表臂统计清账（骨架台账 #8 + #7 注入侧）——零 LLM 纯计算。

#8  mutation score 点估计 + 配对 bootstrap 95% CI（Efron 1979, n_boot=2000,
    seed=20260827 预注册）:
      - 注入级 MS = visible/total（unit=注入, 附聚类警示）
      - 表级   MS = discriminated/total（unit=表, 主口径——表内注入相关）
      - 配对 bootstrap: 专利四型可见率两两差（同表重采样配对）
#7  盲锥测度 BC(δ, D) 注入侧估计: δ=1（与编辑距离≤1 吸收机制一致）于 118
    注入分布; 真实 OCR 错误分布部分待公开语料或合成渲染（接 C4 合成题库）,
    甲方真实 OCR 数据红线禁入——显式注记。

数据源: logs/graph/eval/checkpoint_discrimination_tables_v2.json（@34c93ab）
产出:   logs/graph/eval/k2_ms_bc_analysis.json
用法:   python3 research/k2_ms_bootstrap.py [--boot 2000] [--seed 20260827]
"""
from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "logs" / "graph" / "eval" / "checkpoint_discrimination_tables_v2.json"
OUT = REPO / "logs" / "graph" / "eval" / "k2_ms_bc_analysis.json"

PATENT_GROUPS = {
    "别名型": ["alias_variant", "mixed_lang"],
    "列名型": ["ocr_similar", "prefix_noise"],
    "类型型": ["unit_suffix", "date_variant"],
}
DROP_THRESHOLD = 2.0


def pct(x: float) -> float:
    return round(100 * x, 2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20260827)
    args = ap.parse_args()
    t0 = time.time()

    d = json.loads(SRC.read_text(encoding="utf-8"))
    tables = d["tables"]
    n_tab = len(tables)
    inj_all = [(t["uid"], i) for t in tables for i in t["injections"]]
    n_inj = len(inj_all)
    vis_inj = sum(1 for _, i in inj_all if i["visible"])
    disc_tab = sum(1 for t in tables if t["discriminated"])

    ms_inj = vis_inj / n_inj
    ms_tab = disc_tab / n_tab

    rng = random.Random(args.seed)
    # 注入级 bootstrap（iid 口径, 附聚类警示; 报告用）
    boot_inj = []
    vis_flags = [1 if i["visible"] else 0 for _, i in inj_all]
    for _ in range(args.boot):
        smp = [vis_flags[rng.randrange(n_inj)] for _ in range(n_inj)]
        boot_inj.append(sum(smp) / n_inj)
    # 表级 bootstrap（主口径）
    disc_flags = [1 if t["discriminated"] else 0 for t in tables]
    boot_tab = []
    for _ in range(args.boot):
        smp = [disc_flags[rng.randrange(n_tab)] for _ in range(n_tab)]
        boot_tab.append(sum(smp) / n_tab)

    def ci(v):
        v = sorted(v)
        lo = v[int(0.025 * len(v))]
        hi = v[int(0.975 * len(v))]
        return [round(lo, 4), round(hi, 4)]

    # 配对 bootstrap: 专利三型可见率两两差（unit=表, 表内注入聚合）
    def type_vis_by_table():
        per = {g: [] for g in PATENT_GROUPS}
        for t in tables:
            seen = {g: [0, 0] for g in PATENT_GROUPS}  # [visible, total]
            for i in t["injections"]:
                for g, members in PATENT_GROUPS.items():
                    if i["type"] in members:
                        seen[g][1] += 1
                        if i["visible"]:
                            seen[g][0] += 1
            per_g = {}
            for g, (v_, n_) in seen.items():
                per_g[g] = (v_ / n_) if n_ else None
            for g in PATENT_GROUPS:
                per[g].append(per_g[g])
        return per

    per_tab = type_vis_by_table()
    pairs = {}
    groups = list(PATENT_GROUPS.keys())
    for a in range(len(groups)):
        for b in range(a + 1, len(groups)):
            ga, gb = groups[a], groups[b]
            diffs = []
            for _ in range(args.boot):
                idx = [rng.randrange(n_tab) for _ in range(n_tab)]
                va = [per_tab[ga][k] for k in idx if per_tab[ga][k] is not None]
                vb = [per_tab[gb][k] for k in idx if per_tab[gb][k] is not None]
                if va and vb:
                    diffs.append(sum(va) / len(va) - sum(vb) / len(vb))
            diffs.sort()
            pairs[f"{ga}-{gb}"] = {
                "point_diff": round(
                    (d["patent_crosswalk"][ga]["visibility_rate"]
                     - d["patent_crosswalk"][gb]["visibility_rate"]), 4),
                "ci95": [round(diffs[int(0.025 * len(diffs))], 4),
                          round(diffs[int(0.975 * len(diffs))], 4)],
            }

    # #7 BC(δ=1, D) 注入侧
    absorbed = n_inj - vis_inj
    bc_by_type = {t: {"n": v["n_injections"], "blind": v["n_absorbed"],
                      "blind_rate": round(v["n_absorbed"] / v["n_injections"], 4)
                      if v["n_injections"] else None}
                  for t, v in d["by_type"].items()}

    payload = {
        "meta": {
            "name": "k2-ms-bootstrap-bc", "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": str(SRC), "n_boot": args.boot, "seed": args.seed,
            "caliber": "台账 #8 MS+bootstrap CI（Efron 1979）+ #7 BC(δ=1) 注入侧; 零 LLM; "
                       "表级为主口径（表内注入相关, 注入级 iid 仅参考）; "
                       "真实 OCR 错误分布待公开语料或合成渲染（接 C4 合成题库）, 甲方真实 OCR 红线禁入",
            "runtime_s": round(time.time() - t0, 2),
        },
        "mutation_score": {
            "injection_level": {"n": n_inj, "visible": vis_inj, "ms": round(ms_inj, 4),
                                "ci95_boot": ci(boot_inj)},
            "table_level_primary": {"n": n_tab, "discriminated": disc_tab,
                                    "ms": round(ms_tab, 4), "ci95_boot": ci(boot_tab)},
            "paired_bootstrap_type_diffs": pairs,
        },
        "blind_cone_bc_delta1": {
            "delta": 1,
            "bc_blind_mass": round(absorbed / n_inj, 4),
            "n_blind": absorbed, "n_total": n_inj,
            "by_type": bc_by_type,
            "note": "δ=1 与编辑距离≤1 吸收机制一致: 盲区质量 22/118 中 13 集中于 ocr_similar"
                    "（match_tier=1 全吸收）, 其余分布于 prefix_noise/alias 的 tier1-2 吸收; "
                    "真实分布侧待补（见 meta.caliber）",
        },
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({
        "ms_injection": f"{vis_inj}/{n_inj} = {pct(ms_inj)}% CI95 {ci(boot_inj)}",
        "ms_table": f"{disc_tab}/{n_tab} = {pct(ms_tab)}% CI95 {ci(boot_tab)}",
        "bc_blind_mass": payload["blind_cone_bc_delta1"]["bc_blind_mass"],
        "out": str(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
