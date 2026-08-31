# -*- coding: utf-8 -*-
"""D2 阶段 B 抽验（主线程独立复算, 只读本地工件）。
输入: logs/graph/eval/d2_cross_matcher_embed.json + d2_cross_matcher_det.json
输出: logs/graph/eval/d2_phase_b_spotcheck_recompute.json
"""
import json, hashlib, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EMB = ROOT / "logs" / "graph" / "eval" / "d2_cross_matcher_embed.json"
DET = ROOT / "logs" / "graph" / "eval" / "d2_cross_matcher_det.json"
OUT = ROOT / "logs" / "graph" / "eval" / "d2_phase_b_spotcheck_recompute.json"

RECEIPT_PAYLOAD_SHA = "299ab1c7acfc8b272fce6c1a3bbf18ca01d35810d715cd1b62c3c651f121f950"
RECEIPT_RAW_SHA = "ed3d3905e42c41ab71d4dfacc64a3609de2dd12d5e20cf9b5b363a90d29d4bbf"
PHASE_A_PAYLOAD_SHA = "caf1e3bdea4621c685f184d308bdd9123c843f20fb00909fb5a945ef3d0c9558"
GAMMAS = ["0.2", "0.3", "0.5", "0.7", "0.9"]
EXPECTED_COUNTS = {"greedy_production": (85, 7, 26), "greedy_embedding": (23, 57, 38),
                   "hungarian_embedding": (19, 66, 33)}
EXPECTED_TAU_MIN = {"greedy_production": 1.0, "greedy_embedding": 0.276026,
                    "hungarian_embedding": -0.298142}
EXPECTED_BLIND = {"greedy_production": ["ocr_similar"],
                  "greedy_embedding": ["ocr_similar", "prefix_noise"],
                  "hungarian_embedding": ["ocr_similar", "prefix_noise", "unit_suffix"]}

results = []
def ck(name, ok, detail=None):
    results.append({"check": name, "pass": bool(ok), "detail": detail or {}})

raw = EMB.read_bytes()
doc = json.loads(raw.decode("utf-8"))
p = doc["payload"]

# 1. payload_sha256 独立复算（Loop A 规范化口径: dumps ensure_ascii=False sort_keys=True）
mine = hashlib.sha256(json.dumps(p, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
ck("payload_sha256_recompute", mine == doc["payload_sha256"] == RECEIPT_PAYLOAD_SHA,
   {"mine": mine, "stored": doc["payload_sha256"], "receipt": RECEIPT_PAYLOAD_SHA})

# 2. 原始文件 LF 口径 sha（双口径设计: 本地 CRLF checkout 归一化后与 GB10 逐字节一致）
sha_raw = hashlib.sha256(raw).hexdigest()
sha_lf = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
ck("raw_file_lf_sha256", RECEIPT_RAW_SHA in (sha_lf, sha_raw),
   {"receipt": RECEIPT_RAW_SHA, "lf": sha_lf, "raw": sha_raw,
    "matched_caliber": "lf" if sha_lf == RECEIPT_RAW_SHA else ("raw" if sha_raw == RECEIPT_RAW_SHA else "NONE")})

# 3. 门状态
g = doc["gates"]
ck("gates_all_pass", all(g[k] is True for k in
   ("G0_production_reproduces_d1", "G1_threshold_calibration_valid",
    "G3_equivalence_observation_noncriterion", "G4_p4_zero_endpoint_and_readonly",
    "G5_transition_matrix_completeness", "G6_digest_self_consistency"))
   and g["all_pass"] is True and g["P2_embedding_pass_fail"] == "none_by_preregistration",
   {"gates": {k: v for k, v in g.items()}})

# 4. tau-b 独立复算（由 concordant/discordant/ties 重建, 不信任存储 tau）
tau_min_mine, bad = {}, []
for m, blk in p["ordering_kendall_tau"].items():
    ts = []
    for gam, cell in blk["per_gamma"].items():
        C, D, Ta, Tb = cell["concordant"], cell["discordant"], cell["ties_a"], cell["ties_b"]
        denom = math.sqrt((C + D + Ta) * (C + D + Tb))
        t = (C - D) / denom if denom > 0 else None
        if t is None:
            ts.append(None); continue
        if abs(t - cell["tau"]) > 1e-4:
            bad.append((m, gam, t, cell["tau"]))
        ts.append(t)
    defined = [t for t in ts if t is not None]
    tau_min_mine[m] = min(defined) if defined else None
ok4 = (not bad) and all(tau_min_mine[m] is not None and
                        abs(tau_min_mine[m] - blk["tau_min"]) < 1e-4 and
                        abs(tau_min_mine[m] - EXPECTED_TAU_MIN[m]) < 1e-4
                        for m, blk in p["ordering_kendall_tau"].items())
ck("tau_b_independent_recompute", ok4,
   {"tau_min_mine": {k: round(v, 6) for k, v in tau_min_mine.items()},
    "expected": EXPECTED_TAU_MIN, "cell_mismatch": bad})

# 5. 盲集: ocr_similar 全 γ 零可见 + blind_types 与声明一致
ok5, blind_detail = True, {}
for m in p["spectrum"]:
    for gam in GAMMAS:
        cell = p["spectrum"][m][gam]["by_type"]["ocr_similar"]
        if cell["visible"] != 0 or cell["n"] != 13:
            ok5 = False; blind_detail.setdefault("bad_ocr", []).append((m, gam, cell))
    if p["blind_types"][m] != EXPECTED_BLIND[m]:
        ok5 = False; blind_detail["bad_blind_types_" + m] = p["blind_types"][m]
ck("blind_set_ocr_all_gamma", ok5, blind_detail or {"note": "ocr 13/13 恒零可见, 盲集 = 声明"})

# 6. 计数自洽 + 谱交叉（γ0.2 Σvisible == H, Σn == 118, H+E+HI == 118, 机制和 == HI）
ok6, det6 = True, {}
for m, (eH, eE, eHI) in EXPECTED_COUNTS.items():
    c = p["counts_by_matcher"][m]
    if (c["H"], c["E"], c["HI"]) != (eH, eE, eHI) or c["H"] + c["E"] + c["HI"] != 118:
        ok6 = False; det6["counts_bad_" + m] = c
    hm = c["hi_by_mechanism"]
    if hm["absorption_silent"] + hm["threshold_dilution"] != c["HI"]:
        ok6 = False; det6["mech_bad_" + m] = hm
    sp = p["spectrum"][m]["0.2"]["by_type"]
    if sum(v["visible"] for v in sp.values()) != c["H"] or sum(v["n"] for v in sp.values()) != 118:
        ok6 = False
        det6["spectrum_cross_bad_" + m] = {"sum_visible": sum(v["visible"] for v in sp.values()),
                                           "sum_n": sum(v["n"] for v in sp.values()), "H": c["H"]}
ck("counts_vs_spectrum_crosscheck", ok6, det6 or {"note": "三匹配器计数/机制/谱三方闭合"})

# 7. 迁移矩阵: 99 格零缺 + 翻转 0/8/8 + 翻转全为 HI(threshold_dilution)->E 且 keyset 全等
tm = p["transition_matrix"]
rows, cols = tm["rows"], tm["columns"]
cells = sum(len(r["cells"]) for r in rows)
flips, bad_flip = {c: 0 for c in cols}, []
for r in rows:
    for c in cols:
        cell = r["cells"][c]
        if cell["flipped_to"]:
            flips[c] += 1
            if not (r["d1_class"] == "HI" and r["d1_mechanism"] == "threshold_dilution"
                    and cell["flipped_to"] == "E" and cell["canonical_keyset_identical"]):
                bad_flip.append((r["uid"], c, r["d1_class"], r["d1_mechanism"], cell["flipped_to"]))
ck("transition_matrix_completeness_and_flips",
   len(rows) == 33 and cells == 99 and flips == {"greedy_production": 0, "greedy_embedding": 8,
                                                  "hungarian_embedding": 8} and not bad_flip,
   {"n_rows": len(rows), "n_cells": cells, "flips": flips, "bad_flip": bad_flip})

# 8. 等价稳定性（7 条零翻转）
eq = p["equivalence_stability"]
ck("equivalence_stability", eq["n_equivalence_rows"] == 7 and eq["n_flips"] == 0
   and eq["missing_cells"] == 0, dict(eq))

# 9. 定标算术（margin = p05_pos - p95_neg; 阈值 = p05_pos 冻结; 弱门控事实）
tc = p["threshold_calibration"]
margin_calc = tc["positive_control_distribution"]["p05"] - tc["negative_control_distribution"]["p95"]
ck("threshold_calibration_arithmetic",
   abs(margin_calc - tc["separation_margin_p05_pos_minus_p95_neg"]) < 1e-4
   and abs(tc["threshold_frozen"] - tc["positive_control_distribution"]["p05"]) < 1e-3
   and tc["frozen_before_injection_scoring"] is True
   and tc["negative_control_distribution"]["p75"] > tc["threshold_frozen"],
   {"margin_calc": round(margin_calc, 5), "margin_stored": tc["separation_margin_p05_pos_minus_p95_neg"],
    "threshold": tc["threshold_frozen"], "neg_p75": tc["negative_control_distribution"]["p75"]})

# 10. 零端点自证（工件内证据）
g4 = p["gate_details"]["G4_p4_zero_endpoint_and_readonly"]
ck("zero_endpoint_self_proof",
   g4["ports_touched"] == [] and g4["model_service_calls"] == 0
   and g4["local_inference_batches"] == 16 and g4["local_encoded_texts"] == 496
   and g4["endpoint_violations"] == [] and g4["socket_attempts_blocked"]["n"] == 3
   and g4["active_connection_probes"]["all_blocked"] is True
   and doc["meta"]["endpoint_calls"] == 0,
   {"ports": g4["ports_touched"], "service_calls": g4["model_service_calls"],
    "batches": g4["local_inference_batches"], "texts": g4["local_encoded_texts"]})

# 11. 阶段 A 工件零覆写（本地 det 件 payload sha 独立复算 == 阶段 A 收据 LF 口径）
det_doc = json.loads(DET.read_bytes().decode("utf-8"))
det_sha = hashlib.sha256(json.dumps(det_doc["payload"], ensure_ascii=False,
                                    sort_keys=True).encode("utf-8")).hexdigest()
ck("phase_a_artifact_zero_overwrite", det_sha == PHASE_A_PAYLOAD_SHA,
   {"mine": det_sha, "phase_a_receipt": PHASE_A_PAYLOAD_SHA})

# 12. P2 findings 一致性（不判过判 + 吸收维持口径 = absorbed 字段重算）
pf = p["p2_findings"]
abs_mine = {c: sum(1 for r in rows if r["cells"][c]["absorbed"]) for c in cols}
ck("p2_findings_consistency",
   pf["no_pass_fail_adjudicated"] is True
   and pf["ocr_similar_under_embedding"]["visible_any_gamma"] is False
   and pf["ocr_similar_under_embedding"]["n"] == 13
   and abs_mine == pf["absorption_maintained_of_33"],
   {"abs_mine": abs_mine, "stored": pf["absorption_maintained_of_33"]})

n_pass = sum(1 for r in results if r["pass"])
report = {"n_checks": len(results), "n_pass": n_pass,
          "all_pass": n_pass == len(results), "results": results}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=1))