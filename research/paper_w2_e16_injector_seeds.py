#!/usr/bin/env python3
"""W2 段 E1.6: 3 个 injector seeds 的臂 B 判别率重复性（零模型调用）。

任务卡: docs/experiments/2026-08-30_w2_window_card_8004.md §3.2
判据: 蓝图 C2 成功标准中的">=3 seeds CI 可算"一维。
卡 §2.2 预测: 三 seed 臂 B（E1.2_flat）表级判别率 ∈ [0.70, 0.85]（seed 42 = 75/95 = 0.7895 邻域）。

口径:
  - 臂 B 协议 = research/paper_t1_eval_baselines.run_arm_b 逐字复用（同 TAU=2.0,
    同 FLAT_TAU_H=0.2, 同 bootstrap N=2000 / SEED=20260830）, 本段只换注入种子。
  - 注入器 = scripts/research/drift_inject.py CLI 同码路（ratio=0.3 冻结同基线）。
  - 新 seed 产物只写 /tmp; 冻结 data/research/drift_v0/output/ 只读。
  - 开门门: seed 42 重跑必须与冻结工件字节一致（否则说明注入器码路漂移, 本段作废）。

红线: 零网络零模型调用 -> socket 层封死, 任何连接尝试立即抛错。

用法: python3 research/paper_w2_e16_injector_seeds.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
import socket
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
DRIFT_IN = REPO / "data" / "research" / "drift_v0" / "input" / "tatqa_tables.json"
DRIFT_FROZEN = REPO / "data" / "research" / "drift_v0" / "output"
SCRATCH = Path("/tmp/w2_e16_inject")
OUT = EVAL / "_w2_e16_section.json"

SEEDS = [42, 20260831, 20260832]      # 卡 §3.2 指定
RATIO = 0.3                           # 与冻结基线一致（唯一变量 = seed）
FROZEN_FLAT_RATE = 0.7895             # seed 42 冻结值 = 75/95
PRED_BAND = (0.70, 0.85)              # 卡 §2.2 预测区间

PORTS_TOUCHED: list = []


def install_zero_guard() -> None:
    real = socket.socket

    class Blocked(real):  # type: ignore[misc]
        def connect(self, address, *a, **k):
            if isinstance(address, tuple) and len(address) >= 2:
                PORTS_TOUCHED.append(str(address[:2]))
            raise RuntimeError("ZERO_ENDPOINT: blocked outbound %r" % (address,))

        def connect_ex(self, address, *a, **k):
            if isinstance(address, tuple) and len(address) >= 2:
                PORTS_TOUCHED.append(str(address[:2]))
            raise RuntimeError("ZERO_ENDPOINT: blocked outbound %r" % (address,))

    socket.socket = Blocked                       # type: ignore[misc]
    socket.create_connection = lambda *a, **k: (_ for _ in ()).throw(
        RuntimeError("ZERO_ENDPOINT: blocked create_connection"))
    socket.getaddrinfo = lambda *a, **k: (_ for _ in ()).throw(
        RuntimeError("ZERO_ENDPOINT: blocked getaddrinfo"))


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def inject(seed: int) -> Path:
    """同码路重跑注入器（CLI main）到新目录。"""
    out_dir = SCRATCH / ("seed_%d" % seed)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    sys.path.insert(0, str(REPO / "scripts" / "research"))
    import drift_inject
    # 相对路径与冻结工件生成时一致 -> 连 meta.input 溯源字段也字节相同
    rc = drift_inject.main(["--input", str(DRIFT_IN.relative_to(REPO)), "--out", str(out_dir),
                            "--ratio", str(RATIO), "--seed", str(seed)])
    if rc != 0:
        raise RuntimeError("injector failed seed=%d rc=%d" % (seed, rc))
    return out_dir


def main() -> int:
    install_zero_guard()
    sys.path.insert(0, str(REPO / "research"))
    import paper_t1_eval_baselines as t1          # 复用臂 B 协议
    sys.path.insert(0, str(REPO / "scripts"))
    import m1_statement_parser as mp              # 生产匹配器（只读, 确定性）

    per_seed, flags_by_proto = [], {"E1.1_end_to_end": [], "E1.2_flat": [], "E1.3_hier_expert": []}
    gate_bytes = None
    for seed in SEEDS:
        d = inject(seed)
        rep = json.loads((d / "report.json").read_text(encoding="utf-8"))
        if seed == SEEDS[0]:                      # 开门门: 与冻结工件字节一致
            gate_bytes = {
                "injected_tables": [sha(d / "injected_tables.json"),
                                    sha(DRIFT_FROZEN / "injected_tables.json")],
                "injection_map": [sha(d / "injection_map.json"),
                                  sha(DRIFT_FROZEN / "injection_map.json")],
                "determinism_sha256": [rep.get("determinism_sha256"),
                                       json.loads((DRIFT_FROZEN / "report.json")
                                                  .read_text(encoding="utf-8"))
                                       .get("determinism_sha256")],
            }
        t1.DRIFT = d
        arm = t1.run_arm_b(mp)
        pr = {}
        for name in flags_by_proto:
            st = arm["protocols"][name]
            key = {"E1.1_end_to_end": "E1.1_detected", "E1.2_flat": "E1.2_detected",
                   "E1.3_hier_expert": "E1.3_detected"}[name]
            flags = [1 if t[key] else 0 for t in sorted(arm["tables"], key=lambda x: x["uid"])]
            flags_by_proto[name].extend(flags)
            pr[name] = {"tables_detected": st["tables_detected"], "n_tables": st["n_tables"],
                        "table_detect_rate": st["table_detect_rate"],
                        "table_detect_rate_ci95": st["table_detect_rate_ci95"],
                        "injection_detect_rate": st["injection_detect_rate"],
                        "worst_type": st["worst_type"],
                        "worst_type_detect_rate": st["worst_type_detect_rate"],
                        "separation_mean": st["separation_mean"]}
        entry = {"seed": seed, "n_tables_injected": rep.get("n_tables_injected"),
                 "n_injections": rep.get("n_injections_total"),
                 "injection_rate_per_table": rep.get("injection_rate_per_table"),
                 "by_type": rep.get("by_type"), "determinism_sha256": rep.get("determinism_sha256"),
                 "protocols": pr,
                 "g1_frozen_reconciliation_applicable": seed == SEEDS[0],
                 "g1_frozen_reconciliation_pass": (arm["g1_armb"]["pass"]
                                                   if seed == SEEDS[0] else None),
                 "n_tables_recomputed": arm["n_tables"]}
        per_seed.append(entry)
        print("seed %-9s tables=%s inj=%s  E1.2_flat=%s CI=%s  g1=%s"
              % (seed, arm["n_tables"], rep.get("n_injections_total"),
                 pr["E1.2_flat"]["table_detect_rate"], pr["E1.2_flat"]["table_detect_rate_ci95"],
                 entry["g1_frozen_reconciliation_pass"]), flush=True)

    flat = [e["protocols"]["E1.2_flat"]["table_detect_rate"] for e in per_seed]
    pooled = {name: {"n_tables": len(f), "table_detect_rate": round(sum(f) / len(f), 4),
                     "table_detect_rate_ci95": t1.bootstrap_ci_table(f)}
              for name, f in flags_by_proto.items()}
    rates = [e["protocols"]["E1.2_flat"]["table_detect_rate"] for e in per_seed]
    section = {
        "protocol_reuse": ("research/paper_t1_eval_baselines.run_arm_b 逐字复用; "
                           "TAU=2.0 / FLAT_TAU_H=0.2 / bootstrap N=2000 SEED=20260830 冻结"),
        "variable_changed": "injector seed only (ratio=0.3, input, matcher, protocol identical)",
        "seeds": SEEDS, "ratio": RATIO,
        "gate_seed42_byte_identity": gate_bytes,
        "gate_seed42_pass": bool(gate_bytes) and (
            gate_bytes["injected_tables"][0] == gate_bytes["injected_tables"][1]
            and gate_bytes["injection_map"][0] == gate_bytes["injection_map"][1]
            and gate_bytes["determinism_sha256"][0] == gate_bytes["determinism_sha256"][1]),
        "per_seed": per_seed,
        "seed_distribution_E1_2_flat": {
            "values": rates, "n_seeds": len(rates),
            "min": min(rates), "max": max(rates),
            "spread": round(max(rates) - min(rates), 4),
            "mean": round(sum(rates) / len(rates), 4),
            "frozen_seed42_reference": FROZEN_FLAT_RATE,
            "reproduces_frozen_seed42": any(
                abs(e["protocols"]["E1.2_flat"]["table_detect_rate"] - FROZEN_FLAT_RATE) < 1e-9
                for e in per_seed if e["seed"] == SEEDS[0]),
        },
        "pooled_across_seeds": pooled,
        "prediction_check": {
            "c2_multi_seed_ci_computable": all(
                e["protocols"]["E1.2_flat"]["table_detect_rate_ci95"] for e in per_seed)
            and len(per_seed) >= 3,
            "e1_6_band": list(PRED_BAND),
            "all_seeds_in_band": all(PRED_BAND[0] <= r <= PRED_BAND[1] for r in rates),
            "values_out_of_band": [r for r in rates if not (PRED_BAND[0] <= r <= PRED_BAND[1])],
        },
        "zero_endpoint": {"ports_touched": sorted(set(PORTS_TOUCHED)), "model_calls": 0},
    }
    OUT.write_text(json.dumps(section, ensure_ascii=False, indent=1), encoding="utf-8")
    print("gate_seed42_byte_identity=%s  E1.2_flat across seeds=%s  -> %s"
          % (section["gate_seed42_pass"], rates, OUT))
    return 0 if (section["gate_seed42_pass"] and not PORTS_TOUCHED) else 1


if __name__ == "__main__":
    sys.exit(main())
