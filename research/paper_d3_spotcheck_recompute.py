# -*- coding: utf-8 -*-
"""D3 阶段 A 抽验（只读本地工件, 独立复算）。

F04 改造 (2026-09-10, Loop A / TASK-20260910-A4A5A4W 修复包 ④):
  - 全部断言改走 research/spotcheck_lib.py: 缺键即失败 / 无实测量的恒真项禁止登记 /
    存在性项降级为 L1-OBSERVED 不入 PASS 分母 / 观察项标 INFO 不入分母。
  - **退出码**: 0 全过 / 1 有 FAIL / 2 无 gating 项 (改前本脚本 sys.exit 出现 0 次, 恒 exit 0)。
  - 修第 8 项恒真缺陷: 改前 `rho = find_margin(a4, {"rho","spearman","rank_correlation"})`
    找不到任何键 (真名是 `...matched_fpr_difference.identity_evidence.spearman_rho_rank_identical`),
    于是 `rho is None or abs(rho-1.0)<1e-9 or True` 三段全部成立 -> 恒 PASS, ρ 从未被检查。
    现按真实键路径要求实测值 == 1.0, 缺 rho 键 = FAIL。
  - `--artifact` / `--out`: 抽验输入与输出工件路径可注入 (默认 = 历史路径, 行为不变),
    使验收方能把缺陷工件投到 /tmp 而不覆盖 logs/graph/eval/ 下的审计证据。
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spotcheck_lib import Spotcheck, dig, MissingKey  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT = ROOT / "logs" / "graph" / "eval" / "d3_matched_fpr_stage_a.json"
DEFAULT_OUT = ROOT / "logs" / "graph" / "eval" / "d3_spotcheck_recompute.json"
RECEIPT_RAW_SHA = "3318ac178a0c3317ce18d69663b942e289c2668f4b604082606a549172f2ab10"
# 真键路径 (改前 find_margin 的键名集合命中不了它 => ρ 从未被读)
RHO_PATH = "payload.a4_matched_fpr.matched_fpr_difference.identity_evidence.spearman_rho_rank_identical"

s = Spotcheck("D3-stage-A")


def req(name, doc, path, level="L2", detail=""):
    try:
        return dig(doc, path)
    except MissingKey:
        s._add(name, "FAIL", level, "缺键: %s 不存在 (缺键不等于通过)%s" % (path, ("; " + str(detail)) if detail else ""))
        return None


ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--artifact", default=str(DEFAULT_ARTIFACT), help="被抽验的阶段 A 工件 (只读)")
ap.add_argument("--out", default=str(DEFAULT_OUT), help="抽验工件输出路径 (验收方请指向仓外临时路径)")
args = ap.parse_args()

raw = Path(args.artifact).read_bytes()
doc = json.loads(raw.decode("utf-8"))
p = doc["payload"]

# 1. payload_sha256 复算 (规范化口径同族: dumps ensure_ascii=False sort_keys=True)  [L3]
mine = hashlib.sha256(json.dumps(p, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
s.check("payload_sha256_recompute", mine, doc.get("payload_sha256"), level="L3",
        detail={"mine": mine[:20], "stored": str(doc.get("payload_sha256"))[:20]})

# 2. 原始文件 sha 双口径必须有一口径命中收据值  [L3]
sha_raw = hashlib.sha256(raw).hexdigest()
sha_lf = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
hit = "MATCH" if RECEIPT_RAW_SHA in (sha_lf, sha_raw) else "NONE"
s.check("raw_file_sha256_matches_receipt", hit, "MATCH", level="L3",
        detail={"receipt": RECEIPT_RAW_SHA[:20], "lf": sha_lf[:20], "raw": sha_raw[:20],
                "matched_caliber": "lf" if sha_lf == RECEIPT_RAW_SHA else ("raw" if sha_raw == RECEIPT_RAW_SHA else "NONE")})

# 3. 门状态 + 零端点声明 (ports_touched 必须**实测为空列表**, 不接受 None)  [L2]
g_all = req("gates_all_pass", doc, "gates.all_pass")
ep_calls = req("meta_endpoint_calls", doc, "meta.endpoint_calls")
mc_calls = req("zero_endpoint_model_calls", doc, "payload.zero_endpoint.model_calls")
ports = req("zero_endpoint_ports_touched", doc, "payload.zero_endpoint.ports_touched")
s.check("gates_all_pass", g_all, True, level="L2", detail={"gates.all_pass": g_all})
s.check("endpoint_calls_is_zero", ep_calls, 0, level="L2", detail={"meta.endpoint_calls": ep_calls})
s.check("model_calls_is_zero", mc_calls, 0, level="L2", detail={"zero_endpoint.model_calls": mc_calls})
s.check("ports_touched_is_empty_list", ports, [], level="L2",
        detail={"zero_endpoint.ports_touched": ports, "note": "None 不再视为通过 (声明缺失!=声明为空)"})

# 4. G-1 冻结复现  [L2]
fr = req("g1_frozen_counts_reproduced", doc, "payload.g1_reproduction.checks.frozen_counts_reproduced_from_recomputed_scores")
s.check("g1_frozen_reproduction", fr, True, level="L2", detail={"value": fr})

# 5. A1 定标诊断 = (b) 且决策在案; margin 恶化方向为观察项  [L2 + INFO]
state = req("a1_state_b_decision", doc, "payload.a1_embedding_calibration.e1_state")
decision = req("a1_embedding_citation_decision", doc, "payload.a1_embedding_calibration.embedding_citation_decision")
s.check("a1_state_is_b", state, "b", level="L2", detail={"e1_state": state})
s.observe("a1_citation_decision_recorded", {"embedding_citation_decision": decision})
# 改前这两行找的是**不存在的键** (margin_original / margin_after_same_string_removal),
# 旧实现靠 .get() 兜底 + find_margin 递归, 静默拿到 None 还照样 PASS。
# 现按工件真实键读, 且只作为观察项 (方向性描述, 不构成闸门)。
mb = req("a1_best_margin_candidate", doc,
         "payload.a1_embedding_calibration.best_margin_candidate.margin_pq_pos_minus_p95_neg", level="L1")
ipairs = req("a1_identical_pairs_recorded", doc, "payload.a1_embedding_calibration.identical_pairs", level="L1")
if mb is not None:
    s.observe("a1_best_margin_candidate_value", mb)

# 6. A2 clean controls: n=2382 / 零非零观测 / pivot 触发 / CP 上界独立复算  [L2 + L3]
nclean = req("a2_n_clean_usable", doc, "payload.a2_clean_controls_fpr.enumeration.n_clean_usable")
flat_nz = req("a2_flat_nonzero_observations", doc, "payload.a2_clean_controls_fpr.contrastive_fpr_spectrum.flat_nonzero_observations")
piv = req("a2_pivot_triggered", doc, "payload.a2_clean_controls_fpr.pivot.triggered")
s.check("a2_clean_controls_pivot", [nclean, flat_nz, piv], [2382, 0, True], level="L2",
        detail={"n_clean_usable": nclean, "flat_nonzero": flat_nz, "pivot_triggered": piv})
if isinstance(nclean, int) and nclean > 0:
    s.observe("a2_cp95_upper_recomputed", round(1 - (0.025) ** (1 / nclean), 6))

# 7. A4 matched-FPR: 分母 111, 差点 0.0, bootstrap 0/2000, CI [0,0]  [L2]
den = req("a4_denominator_S2", doc, "payload.a4_matched_fpr.denominator_S2.harmful_H_union_HI")
point = req("a4_difference_point", doc, "payload.a4_matched_fpr.matched_fpr_difference.point")
nzrep = req("a4_bootstrap_nonzero_replicates", doc, "payload.a4_matched_fpr.matched_fpr_difference.bootstrap.difference_nonzero_replicates")
nboot = req("a4_bootstrap_n_boot", doc, "payload.a4_matched_fpr.matched_fpr_difference.bootstrap.n_boot")
s.check("a4_matched_fpr_identity", [den, point, nzrep, nboot], [111, 0.0, 0, 2000], level="L2",
        detail={"denominator": den, "point": point, "nonzero_replicates": nzrep, "n_boot": nboot,
                "note": "n_boot 入断言 = 把注释里的 '0/2000' 分母从散文变成机器核验"})
ci95 = req("a4_difference_ci95_present", doc, "payload.a4_matched_fpr.matched_fpr_difference.bootstrap.difference_ci95")
s.observe("a4_difference_ci95", {"value": ci95, "path": "payload.a4_matched_fpr.matched_fpr_difference.bootstrap.difference_ci95",
                                 "fix_note": "改前 detail 读 bs['n_replicates'] 与 diff['ci'] 两个不存在的键, 恒 null = 假字段; 真实键名 = n_boot 与 difference_ci95"})

# 8. 仿射恒等: ρ 必须**实读到**且 == 1.0 (改前恒真的那条, 现为第 ⑦ 个反例的靶点)  [L2]
rho = req("a4_spearman_rho_rank_identical", doc, RHO_PATH)
s.check("a4_affine_identity_rho_is_one", rho, 1.0, level="L2",
        detail={"path": RHO_PATH, "rho": rho, "fix_note": "改前 find_margin 键名不命中 => rho=None => `or True` 恒 PASS"})
try:
    slope = dig(doc, 'payload.a4_matched_fpr.matched_fpr_difference.identity_evidence["slope_max_abs_deviation_from_0.375"]' )
    s.observe("a4_slope_deviation_from_3_8", slope)
except MissingKey:
    s._add("a4_slope_deviation_from_3_8", "FAIL", "L1", "缺键: identity_evidence 未记录斜率偏差 (缺键不等于通过)")

# 9. A3 救援: 11 = 5 + 8 - 2 重叠, 未救 0 (算术独立复算)  [L3]
un = req("a3_union_n", doc, "payload.a3_dilution_rescue.union_deterministic.n")
n_theta = req("a3_channel_theta_n", doc, "payload.a3_dilution_rescue.channel_theta_recallibration.n")
n_tab = req("a3_channel_table_n", doc, "payload.a3_dilution_rescue.channel_table_aggregation.n")
n_ovl = req("a3_overlap_both", doc, "payload.a3_dilution_rescue.union_deterministic.overlap_both_channels")
unres = req("a3_still_unrescued", doc, "payload.a3_dilution_rescue.union_deterministic.still_unrescued")
arith_ok = None
try:
    arith_ok = (un == n_theta + n_tab - n_ovl) and un == 11
except TypeError:
    arith_ok = False
s.check("a3_rescue_11_of_11", [un, n_theta, n_tab, n_ovl, unres, arith_ok], [11, 5, 8, 2, 0, True],
        level="L3", detail={"union_n": un, "theta": n_theta, "table": n_tab, "overlap": n_ovl,
                            "unrescued": unres, "arithmetic": "5+8-2=11"})

# 10. judge 需求清单 = 28  [L2]
jn = req("judge_estimated_calls", doc, "payload.judge_rescoring_needs.estimated_calls")
s.check("judge_needs_28", jn, 28, level="L2", detail={"estimated_calls": jn})

# 11-12. 存在性项: 只登记 OBSERVED, 不入 PASS 分母 (改前它们占据 2 个 PASS 名额)  [L1]
for name, path in (("prereg_predicates_present", "payload.prereg_predicates"),
                   ("inputs_sha256_present", "payload.inputs_sha256")):
    try:
        val = dig(doc, path)
        s._add(name, "OBSERVED", "L1", {"path": path, "n_keys": len(val) if isinstance(val, dict) else "n/a",
                                        "note": "仅存在性, 不入分母"})
    except MissingKey:
        s._add(name, "FAIL", "L1", "缺键: %s 不存在 (缺键不等于通过)" % path)

sys.exit(s.finalize(
    {"artifact": args.artifact, "receipt_raw_sha": RECEIPT_RAW_SHA, "n_items_recorded": len(s.rows)},
    out_path=Path(args.out)))
