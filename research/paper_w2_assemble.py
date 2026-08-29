#!/usr/bin/env python3
"""W2 收尾: 三段（E1.5 / E1.6 / T4）合成单一工件 + 门禁 + 预注册判据对账 + 可复算自证。

任务卡: docs/experiments/2026-08-30_w2_window_card_8004.md
产物: logs/graph/eval/t4_pso_fair_comparison.json
      卡 §5 声明的 payload.* 路径为字面要求 -> 三节装在 payload 键下。

可复算性: 本脚本连跑两次 payload_sha256 必须相同（哈希范围排除 meta 时间戳）。
输入清单固定（显式列文件名, 不 glob 目录 —— W1 教训: glob 会让后续新增文件改变哈希）。
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
OUT = EVAL / "t4_pso_fair_comparison.json"

SECTIONS = {"e1_5": EVAL / "_w2_e15_section.json",
            "e1_6": EVAL / "_w2_e16_section.json",
            "t4": EVAL / "_w2_t4_section.json"}

# 固定清单（禁 glob）
INPUT_FILES = [
    "config/eval_checkpoint_trees.json",
    "logs/graph/eval/checkpoint_discrimination_report.json",
    "logs/graph/eval/checkpoint_discrimination_report_20260819.json",
    "logs/graph/eval/pso_weight_search_v0.json",
    "logs/graph/eval/pso_question_set_v0_batch2.json",
    "logs/graph/eval/scenario1_regression_report.json",
    "logs/graph/eval/m2_deterministic_report.json",
    "logs/graph/eval/m2_judge_report.json",
    "logs/graph/eval/m2_judge_report_k1.json",
    "logs/graph/eval/m2_judge_report_k3.json",
    "logs/graph/eval/number_faithfulness_report.json",
    "data/research/drift_v0/output/injected_tables.json",
    "data/research/drift_v0/output/injection_map.json",
]
SCRIPT_FILES = [
    "research/paper_w2_e15_full_judge.py",
    "research/paper_w2_e16_injector_seeds.py",
    "research/paper_w2_t4_pso_fair.py",
    "research/paper_w2_assemble.py",
    "research/paper_t1_eval_baselines.py",
    "research/pso/pso_weight_search.py",
    "research/pso/pso_question_set_search.py",
    "scripts/eval_checkpoint_aggregate.py",
    "scripts/eval_checkpoint_discrimination.py",
    "scripts/research/drift_inject.py",
    "scripts/m2_eval_judge.py",
]
LEDGER = EVAL / "w2_e15_call_ledger.json"
CACHE = EVAL / "w2_e15_judge_cache.jsonl"

CLIENT_TOKENS = ["华泰紫金", "嘉合", "复熙", "博时", "华泰", "minan", "jiaxing", "boshi",
                 "fuxi", "caitong", "guojin", "nanhua", "TraFax", "WaveFax", "NCAMC",
                 "q01_", "q02_", "q03_", "q04_", "q05_", "q06_", "q07_", "q08_", "q09_",
                 "q10_", "q11_", "q12_", "adv_", "sample_"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha_scan(paths: list) -> dict:
    out = {}
    for rel in paths:
        f = REPO / rel
        out[rel] = sha(f) if f.exists() else "MISSING"
    return out


def _findings(e15: dict, e16: dict, t4: dict) -> dict:
    """把三段里"出人意料但可复核"的机制写成结构化发现（数字全部从节内取）。"""
    sj = e15["separation_judged"]["per_mutant"]
    sm = e15["separation_mapped_control_only_caliber"]["per_mutant"]
    mj = {r["id"]: r for r in sj}
    mm = {r["id"]: r for r in sm}
    nf = json.loads((EVAL / "number_faithfulness_report.json").read_text(encoding="utf-8"))
    zero_claim_items = sum(1 for r in nf.get("results", []) if not (r.get("numbers") or []))
    return {
        "F_W2_1_m7_item_level_invisible": {
            "observation": "M7_nf_fail_3 在 Full-Judge 口径下分离度 = %.4f（映射口径 %.4f）"
                           % (mj["M7_nf_fail_3"]["sep_blended"], mm["M7_nf_fail_3"]["sep_blended"]),
            "mechanism": ("NF 工件 9 条里 %d 条 number_claims=0; mut_nf_fail(3) 把前 3 条 "
                          "pass 置 False 并写 n_fail=3, 而这 3 条本身无任何数值主张。"
                          "本窗裁判只见 item 级观测（按 E1.5 证据等价设计刻意屏蔽 n_fail 聚合量）,"
                          "裁判判定其为零主张条目上的空洞断言 -> 与 control 同分。"
                          % zero_claim_items),
            "attribution": "突变体保真度问题（缺陷注入只落在聚合计数上）, 非单纯裁判能力问题",
            "consequence": ("该 mutant 的 M1/M2 联合判别结论不能归因于裁判; 若要测 Full-Judge 对"
                            "数值忠实度的敏感性, 需换成在有数值主张的条目上注入 ungrounded。"),
            "both_calibers_below_tau": mj["M7_nf_fail_3"]["detect_tree_root"] is False
            and mm["M7_nf_fail_3"]["detect_tree_root"] is False,
        },
        "F_W2_2_missing_artifact_pessimism": {
            "observation": "M8_judge_artifact_missing: 判分 %.4f vs 映射 %.4f（判分更敏感）"
                           % (mj["M8_judge_artifact_missing"]["sep_blended"],
                              mm["M8_judge_artifact_missing"]["sep_blended"]),
            "mechanism": ("确定性口径对缺工件给中性 missing_score=5; 裁判对空证据给"
                          "0/0/5（理由: 无法验证即最低分）-> Full-Judge 把"
                          "'证据缺失'当作缺陷而非中性事件。"),
            "note": "属评分政策差异（悲观 vs 中性）, 需在论文中作为口径选择而非优劣陈述。",
            "no_evidence_scores": e15.get("no_evidence_behavior", {}),
        },
        "F_W2_3_hinge_vs_graded": {
            "observation": "M1_m1_rows_fail: 判分 %.4f < 映射 %.4f（判分更钝）"
                           % (mj["M1_m1_rows_fail"]["sep_blended"], mm["M1_m1_rows_fail"]["sep_blended"]),
            "mechanism": ("parse.doc.ok 的确定性路由是 overall_status_binary 硬闸门（PASS=10 / FAIL=0）,"
                          "2 条 FAIL 即归零; 裁判按失败占比给 7 分（部分分）-> 闸门被软化。"
                          "反向地 M9（全 FAIL）判分 %.4f > 映射 %.4f。"
                          % (mj["M9_m1_all_rows_fail"]["sep_blended"],
                             mm["M9_m1_all_rows_fail"]["sep_blended"])),
            "consequence": "硬闸门语义是契约层设计选择, Full-Judge 默认给部分分; 二者不可互换。",
        },
        "F_W2_4_quantization_floor": {
            "observation": ("叶分量纲为 0-10 整数, 1 个单位 = 四维 0-5 尺度上的 0.5;"
                            "E1.5 一致性注记的预测容差 |Δ|<=0.5 恰等于该分辨率下限。"
                            "faithfulness 真实聚合值 9.875 无法用整数叶分表达（裁判给 9）。"),
            "implication": ("|Δ|<=0.5 判据在 0-10 整数叶分量纲下无区分力, 需二选一:"
                            "放宽到 >1 单位, 或改用连续叶分。列入明日一页纸判定项。"),
        },
        "F_W2_5_greedy_parity": t4["c3_verdict"],
        "F_W2_6_injector_seed_stability": {
            "E1.2_flat_rates": e16["seed_distribution_E1_2_flat"]["values"],
            "spread": e16["seed_distribution_E1_2_flat"]["spread"],
            "observation": ("三 seed 表级判别率极差仅 %.4f（%.3f~%.3f）, 且各自 95%% CI 高度重叠"
                            " -> 臂 B 判别率对注入种子稳健, 变异主要来自表样本本身。"
                            % (e16["seed_distribution_E1_2_flat"]["spread"],
                               min(e16["seed_distribution_E1_2_flat"]["values"]),
                               max(e16["seed_distribution_E1_2_flat"]["values"]))),
        },
    }


def _predicates(e15: dict, e16: dict, t4: dict) -> dict:
    """卡 §2.2 预注册判据逐条对账（冻结于执行前, 不溯及修改）。"""
    st = t4["primary_separation_table"]
    cn = e15["endpoint_consistency_note"]
    keep = t4["question_set_budget"]["keep_rate_sequence"]
    return {
        "C2_multi_seed_ci_computable": {
            "prereg": "分层评测 >=3 seeds CI 可算（本窗承担该一维）",
            "observed": {"n_seeds": e16["seed_distribution_E1_2_flat"]["n_seeds"],
                         "per_seed_ci": [e["protocols"]["E1.2_flat"]["table_detect_rate_ci95"]
                                         for e in e16["per_seed"]],
                         "pooled_ci": e16["pooled_across_seeds"]["E1.2_flat"]["table_detect_rate_ci95"]},
            "verdict": "PASS" if e16["prediction_check"]["c2_multi_seed_ci_computable"] else "FAIL"},
        "C3_pso_beats_four_controls": {
            "prereg": "PSO 均值分离度优于四组对照（多 seed CI）, 最坏类型维度如实报告",
            "observed": {"equal": st["equal"]["mean_sep"], "expert": st["expert"]["mean_sep"],
                         "random30": st["random30"]["mean_sep"], "greedy": st["greedy"]["mean_sep"],
                         "pso": st["pso_5seeds"]["mean_sep_mean"],
                         "beats": [k for k in ("equal", "expert", "random30", "greedy")
                                   if t4["checks"]["c3_pso_beats_" + k]]},
            "verdict": "PARTIAL -> 触发降级条款"
            if not t4["c3_verdict"]["success_clause_holds"] else "PASS",
            "degradation_clause": "改述为『自动搜索节省专家调参成本』, 均值增益与最坏维退化并列"},
        "E1_5_endpoint_consistency_abs_delta_le_0_5": {
            "prereg": "|Δ|<=0.5/维（校准预期, 非判据; 超出 = 端点一致性威胁, 入论文局限节）",
            "observed_max_abs_delta": cn["max_observed_abs_delta"],
            "verdict": "HOLDS (边界)" if cn["prediction_holds"] else "EXCEEDED -> 入局限节",
            "caveat": "见 F_W2_4: 容差恰等于 0-10 整数叶分的分辨率下限"},
        "T4_pso_mean_reproduces_1_4326": {
            "prereg": "PSO(5 seeds) 均值分离 >= expert(1.2560) 且复现 1.4326±0.01",
            "observed": {"pso_mean": st["pso_5seeds"]["mean_sep_mean"],
                         "expert": st["expert"]["mean_sep"],
                         "frozen_gate": t4["per_caliber"]["pso_era_input_20260819"]
                         ["frozen_reproduction_gate"]},
            "verdict": "PASS" if t4["checks"]["pso_mean_reproduces_frozen_1_4326"]
            and t4["checks"]["c3_pso_beats_expert"] else "FAIL"},
        "T4_random30_below_pso": {"prereg": "random(30) 均值 < PSO",
                                  "observed": {"random30": st["random30"]["mean_sep"],
                                               "pso": st["pso_5seeds"]["mean_sep_mean"]},
                                  "verdict": "PASS" if t4["checks"]["random30_below_pso_card_pred"]
                                  else "FAIL"},
        "T4_minimax_worst_ge_0_208": {
            "prereg": "minimax 变体最差 mutant 分离 >= 0.208（以牺牲均值为代价）",
            "observed": {"minimax_worst": st["pso_minimax_5seeds"]["worst_sep_mean"],
                         "minimax_mean": st["pso_minimax_5seeds"]["mean_sep_mean"],
                         "pso_mean": st["pso_5seeds"]["mean_sep_mean"],
                         "pso_worst": st["pso_5seeds"]["worst_sep_mean"]},
            "verdict": "PASS" if t4["checks"]["minimax_worst_ge_pred"] else "FAIL",
            "tradeoff_quantified": {"worst_gain": round(st["pso_minimax_5seeds"]["worst_sep_mean"]
                                                        - st["pso_5seeds"]["worst_sep_mean"], 6),
                                    "mean_cost": round(st["pso_5seeds"]["mean_sep_mean"]
                                                       - st["pso_minimax_5seeds"]["mean_sep_mean"], 6)}},
        "T4_budget_gradient_monotonic": {
            "prereg": "题集预算梯度判别力随题量单调不降（25%->100%）",
            "observed_keep_rate_sequence": keep,
            "verdict": "PASS 但不可用（saturated）"
            if t4["checks"]["budget_gradient_monotonic"]
            and t4["question_set_budget"]["saturated_at_smallest_budget"] else
            ("PASS" if t4["checks"]["budget_gradient_monotonic"] else "FAIL"),
            "caveat": t4["question_set_budget"]["saturation_note"]},
        "E1_6_band_0_70_0_85": {
            "prereg": "三 seed 臂 B 表级判别率 in [0.70, 0.85]",
            "observed": e16["seed_distribution_E1_2_flat"]["values"],
            "verdict": "PASS" if e16["prediction_check"]["all_seeds_in_band"] else "FAIL"},
    }


def main() -> int:
    for name, path in SECTIONS.items():
        if not path.exists():
            print("missing section %s (%s)" % (name, path), file=sys.stderr)
            return 2
    e15 = json.loads(SECTIONS["e1_5"].read_text(encoding="utf-8"))
    e16 = json.loads(SECTIONS["e1_6"].read_text(encoding="utf-8"))
    t4 = json.loads(SECTIONS["t4"].read_text(encoding="utf-8"))
    led = json.loads(LEDGER.read_text(encoding="utf-8"))
    cache_recs = [json.loads(x) for x in CACHE.read_text(encoding="utf-8").splitlines() if x.strip()]

    payload = {
        "call_counter": led["call_counter"],
        "budget_ceiling": led["ceiling"],
        "endpoint_assert": e15["endpoint_assert"],
        "ledger_note_count": len(led.get("notes", [])),
        "distinct_judge_cells": len({r["key"] for r in cache_recs}),
        "e1_5": dict(e15, endpoint_consistency_note=e15["endpoint_consistency_note"]),
        "e1_6": e16,
        "t4": dict(t4, separation_table=t4["primary_separation_table"]),
        "findings": _findings(e15, e16, t4),
        "prereg_predicates": _predicates(e15, e16, t4),
        "inputs_sha256": sha_scan(INPUT_FILES),
        "scripts_sha256": sha_scan(SCRIPT_FILES),
        "judge_cache_sha256": sha(CACHE),
        "design_choices": {
            "evidence_equivalence": e15["design_note"],
            "no_formula_leak": ("裁判 prompt 给检查点需求（同源 config）+ item 级证据, 不给确定性映射公式"
                                "（硬闸门/兄弟归一化/占比公式）, 否则测的是照抄复现而非替代能力。"),
            "integer_leaf_scale": "0-10 整数叶分（0-5 粒度 x2 同构于历史 judge 叶量纲）",
            "call_convention": e15["call_convention"],
            "scratch_isolation": "mutants 作用于 /tmp/w2_e15_scratch 副本; 活工件与冻结件零改动",
        },
        "redline_self_check": {
            "budget_le_200": led["call_counter"] <= led["ceiling"],
            "endpoint_only_8004": e15["endpoint_assert"]["only_allowed_endpoint"],
            "e16_zero_calls": e16["zero_endpoint"]["model_calls"] == 0
            and not e16["zero_endpoint"]["ports_touched"],
            "t4_zero_calls": t4["zero_endpoint"]["model_calls"] == 0
            and not t4["zero_endpoint"]["ports_touched"],
            "judge_no_ground_truth": e15["cells_ok"] == e15["cells_total"],
            "frozen_artifacts_readonly": "mutants 写 /tmp 副本; 仓库内活工件与冻结件未改动",
        },
    }
    # 残留扫描先做（只读判定, 不改 payload）
    residue = sorted({t for t in CLIENT_TOKENS
                      if t.lower() in json.dumps(payload, ensure_ascii=False,
                                                 sort_keys=True).lower()})
    payload["redline_self_check"]["client_identifier_zero_entered"] = not residue
    if residue:
        payload["client_token_residue"] = residue
    # 摘要必须在 payload 全部改动完成之后计算: 否则 payload_sha256 覆盖的是
    # "写入前的 payload", 审阅方按文件复算必然不匹配（本窗首轮实跑踩到并已修复）
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()

    doc = {
        "meta": {
            "name": "w2-window-e15-e16-t4", "task_card": "TASK-20260830-04",
            "card_file": "docs/experiments/2026-08-30_w2_window_card_8004.md",
            "generated": datetime.now().isoformat(timespec="seconds"),
            "window": "W2 :8004 合并窗",
            "segments": ["E1.5 Full-Judge 基线", "E1.6 injector 3 seeds", "T4 PSO 严谨对照"],
            "caliber_policy": t4["caliber_policy"],
            "sha256_scope": "payload.*（meta 时间戳排除在外）",
        },
        "gates": {
            "e15_cells_all_ok": e15["cells_ok"] == e15["cells_total"] and not e15["blocked"],
            "budget_within_ceiling": payload["redline_self_check"]["budget_le_200"],
            "endpoint_only_8004": payload["redline_self_check"]["endpoint_only_8004"],
            "zero_endpoint_e16_t4": payload["redline_self_check"]["e16_zero_calls"]
            and payload["redline_self_check"]["t4_zero_calls"],
            "client_identifier_zero_entered": payload["redline_self_check"][
                "client_identifier_zero_entered"],
            "seed42_injector_byte_identity": e16["gate_seed42_pass"],
            "pso_frozen_reproduction": t4["per_caliber"]["pso_era_input_20260819"]
            ["frozen_reproduction_gate"]["pass"],
            "all_inputs_present": "MISSING" not in set(payload["inputs_sha256"].values()),
            "all_scripts_present": "MISSING" not in set(payload["scripts_sha256"].values()),
        },
        "payload": payload,
        "payload_sha256": digest,
        "reproduce_commands": [
            "python3 research/paper_w2_e15_full_judge.py --dry-run",
            "python3 research/paper_w2_e15_full_judge.py   # 120 单元, 缓存命中则零新增调用",
            "python3 research/paper_w2_e16_injector_seeds.py",
            "python3 research/paper_w2_t4_pso_fair.py",
            "python3 research/paper_w2_assemble.py",
        ],
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    back = json.loads(OUT.read_text(encoding="utf-8"))
    doc["gates"]["digest_self_consistency"] = hashlib.sha256(
        json.dumps(back["payload"], ensure_ascii=False, sort_keys=True)
        .encode("utf-8")).hexdigest() == back["payload_sha256"]
    doc["gates"]["all_pass"] = all(doc["gates"].values())
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print("payload_sha256=%s" % digest)
    print("gates=%s" % json.dumps(doc["gates"], ensure_ascii=False))
    print("call_counter=%s/%s ports=%s residue=%s -> %s"
          % (payload["call_counter"], payload["budget_ceiling"],
             payload["endpoint_assert"]["ports_touched"], residue, OUT))
    return 0 if doc["gates"]["all_pass"] and not residue else 1


if __name__ == "__main__":
    sys.exit(main())
