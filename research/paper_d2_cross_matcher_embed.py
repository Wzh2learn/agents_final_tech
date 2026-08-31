#!/usr/bin/env python3
"""D2 阶段 B: 跨匹配器验证 —— 嵌入匹配器（bge-m3 本地加载, 零端点）。

卡号 TASK-20260831-D2（加编阶段 B）| 预注册 P-2 = **探索性, 不设通过/失败判据**
底表: logs/graph/eval/d1_mutant_validity_audit.json（只读）
阶段 A 件: logs/graph/eval/d2_cross_matcher_det.json（只读, 本件独立不覆写）

做什么
    把打分基从「字符串编辑距离」换成「语义嵌入余弦」(bge-m3), 分配轴仍用生产贪心
    （主件）+ Hungarian（补充件）, 在 D1 同口径 118 注入语料上重跑可见性判定, 输出:
      1) 嵌入件六类谱 x gamma 网格 + 对生产贪心的 Kendall tau-b
      2) 33 吸收注入 x 嵌入件 的迁移矩阵列（并入 DR-3 全表）
      3) 「盲区位置是否匹配器相关」的第二个打分基证据（两个方向都是合法答案）
    P-2 按预注册**不做过判**: 本脚本不产生 P-2 的 pass/fail, 只产出谱与迁移。

阈值定标（执行前定死规则, 看注入数据之前冻结）
    正控 = 生产 schema 的 (standard, synonym) 对（人工批准的合法变体, 与注入语料无关,
    非循环）; 阈值 = 正控余弦分布的 **p05**（即 95% 合法变体被接受）。
    负控 = 跨字段 (synonym_A, standard_B) A!=B 确定性抽样（"不该匹配"参照）。
    定标先于 derive_injections 完成并写死进工件; 之后不调阈值。

零端点（P-4 口径的阶段 B 版）
    全程零模型服务调用。嵌入 = 本地 HF 权重加载（device=cpu 显式, 不占 :8004 生产 GPU
    内存）+ HF_HUB_OFFLINE=1 + TRANSFORMERS_OFFLINE=1 + local_files_only=True +
    socket 层封死（装载与编码全程在护栏之下）+ 主动试连自证。
    model_service_calls 与 local_inference_batches 分列, 不得混读。

红线: 判据冻结（P-2 无过判）; 冻结件与底表前后 sha 全等; 甲方标识零进入;
      本卡不使用 :8006; 阶段 A 工件只读不覆写。

复算: HF_HUB_OFFLINE=1 python3 research/paper_d2_cross_matcher_embed.py
输出: logs/graph/eval/d2_cross_matcher_embed.json
退出码: 0 = 完整性门 G0/G1/G3/G4/G5 全过; 1 = 任一门失败或资产不可用（上报, 不静默）。
"""
from __future__ import annotations

import os

# 离线护栏必须在任何 HF 导入之前落位（防 hub 联网）
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")

import hashlib
import importlib.util
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
D1_ART = EVAL / "d1_mutant_validity_audit.json"
D2A_ART = EVAL / "d2_cross_matcher_det.json"
OUT = EVAL / "d2_cross_matcher_embed.json"
A_SCRIPT = REPO / "research" / "paper_d2_cross_matcher_det.py"

CARD_ID = "TASK-20260831-D2"
TASK_CARD = "docs/experiments/2026-08-31_d2_cross_matcher_card.md"
REPORT = "docs/experiments/2026-08-31_d2_cross_matcher_phase_a.md"

MODEL_DIR = Path(os.path.expanduser("~/wzh/models/hf/bge-m3"))
TORCH_THREADS = 8                 # GB10 20 核, 给生产服务留量
CALIB_PERCENTILE = 5.0            # 阈值 = 正控分布 p05（冻结规则）
NEG_SAMPLE_MOD = 7                # 负控确定性抽样步长（不用随机数）
COS_QUANT = 1000                  # 嵌入余弦量化到 1e-3 后进入 T6 标量编码
PREREG_P2 = {
    "column": "greedy_embedding",
    "supplementary_column": "hungarian_embedding",
    "verdict": "exploratory",
    "pass_fail": "none（卡 2 预注册 P-2: 不设通过/失败判据）",
    "threshold_rule": ("阈值 = 生产 schema (standard, synonym) 正控余弦分布 p05;"
                       " 定标先于 derive_injections, 看结果后不调"),
    "questions_reported": [
        "嵌入件下 ocr_similar 是否仍全盲（盲区位置匹配器相关性）",
        "嵌入件谱排序对生产贪心的 tau-b",
        "33 条 D1 吸收注入在嵌入件下是否仍吸收（迁移矩阵列）",
        "等价 7 条在嵌入件下是否保持吸收-等价"]}

SHA_SCOPE = ("inputs_sha256", "criterion_provenance", "model_asset",
             "threshold_calibration", "matchers", "spectrum", "ordering_kendall_tau",
             "blind_types", "transition_matrix", "equivalence_stability",
             "p2_findings", "counts_by_matcher", "gate_details", "prereg_predicates",
             "zero_endpoint", "redline_self_check")


def _load_a_module():
    spec = importlib.util.spec_from_file_location("d2det", str(A_SCRIPT))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_payload(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False,
                                     sort_keys=True).encode("utf-8")).hexdigest()


def percentile(values: list[float], p: float) -> float:
    """线性插值分位数（确定性, 无第三方依赖）。"""
    if not values:
        raise ValueError("empty distribution")
    s = sorted(values)
    if len(s) == 1:
        return float(s[0])
    k = (len(s) - 1) * (p / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    frac = k - lo
    return float(s[lo] * (1 - frac) + s[hi] * frac)


def dist_stats(values: list[float]) -> dict:
    s = sorted(values)
    return {"n": len(s), "min": round(s[0], 6), "p01": round(percentile(s, 1), 6),
            "p05": round(percentile(s, 5), 6), "p25": round(percentile(s, 25), 6),
            "median": round(percentile(s, 50), 6), "p75": round(percentile(s, 75), 6),
            "p95": round(percentile(s, 95), 6), "max": round(s[-1], 6),
            "mean": round(statistics.fmean(s), 6),
            "stdev": round(statistics.pstdev(s), 6) if len(s) > 1 else 0.0}


# ------------------------------------------------------------- 嵌入向量库
class EmbedStore:
    """本地 bge-m3 编码 + 文本级缓存; 余弦 = 归一化向量点积。"""

    def __init__(self, model) -> None:
        self.model = model
        self._vec: dict[str, list[float]] = {}
        self.batches = 0
        self.encoded_texts = 0

    def prime(self, texts) -> None:
        todo = [t for t in dict.fromkeys(texts) if t not in self._vec]
        bs = 32
        for i in range(0, len(todo), bs):
            chunk = todo[i:i + bs]
            vec = self.model.encode(chunk, normalize_embeddings=True,
                                    batch_size=len(chunk), show_progress_bar=False,
                                    convert_to_numpy=True)
            self.batches += 1
            self.encoded_texts += len(chunk)
            for t, v in zip(chunk, vec):
                self._vec[t] = [float(x) for x in v]

    def sim(self, a: str, b: str) -> float:
        va, vb = self._vec.get(a), self._vec.get(b)
        if va is None or vb is None:
            raise KeyError("text not primed: %r / %r" % (a[:40], b[:40]))
        return round(sum(x * y for x, y in zip(va, vb)), 6)


# ------------------------------------------------------------- 嵌入匹配器
def build_embedding_matchers(d2, store, threshold):

    class EmbeddingBase(d2.BaseMatcher):
        scoring = "bge-m3 余弦（阈值门控: cos <= %s 记 0 不合格）" % threshold
        prereg = False

        def __init__(self, mp) -> None:
            super().__init__(mp)
            self.store = store
            self.threshold = threshold

        def pair_score(self, header_text, canonical):
            hn = self.mp.normalize_header(header_text)
            cn = self.mp.normalize_header(canonical)
            if not hn or not cn:
                return 0.0, 0
            cos = self.store.sim(str(header_text), str(canonical))
            if cos <= self.threshold:
                return 0.0, 0
            return cos, max(0, len(cn))

    class GreedyEmbedding(EmbeddingBase):
        kind = "greedy_embedding"
        assignment = "与阶段 A 归一化件同构的贪心（按 (score, len) 降序先到先得）"
        prereg = True                        # P-2 预注册列（但不设过判）

        def mapping(self, header, canonicals):
            cands = []
            for src in header:
                if not self.mp.normalize_header(src):
                    continue
                for canon in canonicals:
                    score, syn_len = self.pair_score(src, canon)
                    if score > 0:
                        cands.append((score, syn_len, src, canon))
            cands.sort(key=lambda x: (x[0], x[1]), reverse=True)
            mapping: dict[str, str] = {}
            used_src: set[str] = set()
            for _s, _l, src, canon in cands:
                if canon in mapping or src in used_src:
                    continue
                mapping[canon] = src
                used_src.add(src)
            return mapping

    class HungarianEmbedding(d2.HungarianMatcher):
        prereg = False

        def __init__(self, mp, t6) -> None:
            super().__init__(
                mp, t6, "hungarian_embedding",
                "bge-m3 余弦（T6 标量编码 cos*%s -> score）" % COS_QUANT)
            self.store = store
            self.threshold = threshold

        def pair_score(self, header_text, canonical):
            cos = self.store.sim(str(header_text), str(canonical))
            return (cos, len(canonical)) if cos > self.threshold else (0.0, 0)

        def _weight(self, header_text, canonical):
            cos = self.store.sim(str(header_text), str(canonical))
            if cos <= self.threshold:
                return 0.0
            return self.t6.encode(int(round(cos * COS_QUANT)),
                                  len(self.mp.normalize_header(canonical)))

    return GreedyEmbedding, HungarianEmbedding


# ------------------------------------------------------------- 阈值定标
def calibrate(store, mp, d2) -> dict:
    """正控 = schema (standard, synonym) 对; 负控 = 跨字段对。全部在派生任何注入
    状态之前完成, 且只看 schema（与注入语料零重叠 => 非循环定标）。"""
    schema_path = (mp.LOCAL_SCHEMA if os.path.isfile(mp.LOCAL_SCHEMA)
                   else mp.DEFAULT_SCHEMA)
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    pairs: list[tuple[str, str]] = []
    fields: list[str] = []
    for tbl in schema.get("tables", []):
        for f in tbl.get("fields", []):
            std = str(f.get("standard", ""))
            if not std:
                continue
            fields.append(std)
            for syn in (f.get("synonyms") or []):
                pairs.append((std, str(syn)))
    texts = sorted({t for p in pairs for t in p} | set(fields))
    store.prime(texts)
    pos = [store.sim(a, b) for a, b in pairs]
    neg: list[tuple[str, str]] = []
    for i, (std, syn) in enumerate(pairs):
        for std2 in fields:
            if std2 != std and (i + fields.index(std2)) % NEG_SAMPLE_MOD == 0:
                neg.append((syn, std2))
                break
    store.prime([t for p in neg for t in p])
    negvals = [store.sim(a, b) for a, b in neg]
    thr = round(percentile(pos, CALIB_PERCENTILE), 4)
    return {
        "rule": PREREG_P2["threshold_rule"],
        "percentile": CALIB_PERCENTILE,
        "threshold_frozen": thr,
        "schema_source": str(Path(schema_path).resolve().relative_to(
            Path(mp._PROJECT_ROOT).resolve())) if os.path.isabs(schema_path)
        and str(schema_path).startswith(str(mp._PROJECT_ROOT)) else str(schema_path),
        "n_positive_control_pairs": len(pos),
        "n_negative_control_cross_field": len(negvals),
        "positive_control_distribution": dist_stats(pos),
        "negative_control_distribution": dist_stats(negvals),
        "separation_margin_p05_pos_minus_p95_neg": round(
            percentile(pos, 5) - percentile(negvals, 95), 6),
        "overlap_note": ("margin <= 0 = 正控 p05 未与负控 p95 分开, 即嵌入余弦在短表头"
                         "域上分离力弱, 阈值只能作弱门控; 如实入账, 不调阈值救它"),
        "frozen_before_injection_scoring": True}


# ------------------------------------------------------------- 主计算
def main() -> int:
    import torch
    torch.set_num_threads(TORCH_THREADS)
    d2 = _load_a_module()
    sys.path.insert(0, str(REPO / "scripts"))
    import m1_statement_parser as mp
    t6spec = importlib.util.spec_from_file_location(
        "t6_match", str(REPO / "research" / "paper_t6_matching_competition.py"))
    t6 = importlib.util.module_from_spec(t6spec)
    t6spec.loader.exec_module(t6)

    watch = {p: sha256_file(p) for p in
             (D1_ART, D2A_ART, d2.DRIFT / "injection_map.json",
              d2.DRIFT / "injected_tables.json",
              EVAL / "t2_visibility_sensitivity.json")}
    input_files = {
        "logs/graph/eval/d1_mutant_validity_audit.json": watch[D1_ART],
        "logs/graph/eval/d2_cross_matcher_det.json": watch[D2A_ART],
        "data/research/drift_v0/output/injection_map.json":
            watch[d2.DRIFT / "injection_map.json"],
        "data/research/drift_v0/output/injected_tables.json":
            watch[d2.DRIFT / "injected_tables.json"],
        "logs/graph/eval/t2_visibility_sensitivity.json":
            watch[EVAL / "t2_visibility_sensitivity.json"]}

    # 零端点护栏: 在模型装载与编码之前安装（装载期任何 hub 联网都会被拦下）
    d2._install_network_guard()

    weights = MODEL_DIR / "pytorch_model.bin"
    asset = {"dir": "~/wzh/models/hf/bge-m3", "present": MODEL_DIR.is_dir(),
             "config_present": (MODEL_DIR / "config.json").is_file(),
             "weights_sha256": sha256_file(weights) if weights.is_file() else None,
             "weights_bytes": weights.stat().st_size if weights.is_file() else 0,
             "device": "cpu", "torch_threads": TORCH_THREADS,
             "gpu_avoided_reason": ("GB10 GPU 内存由 :8004 生产 llama-server 占用;"
                                    " 本窗不引入争用, 显式 device=cpu"),
             "offline_env": {k: os.environ.get(k) for k in
                             ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE",
                              "HF_DATASETS_OFFLINE")},
             "local_files_only": True}

    load_error, model = None, None
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(str(MODEL_DIR), device="cpu",
                                    local_files_only=True)
    except Exception as exc:                                  # noqa: BLE001
        load_error = "%s: %s" % (type(exc).__name__, str(exc)[:280])
    if model is None:
        # 卡 4 中止条款: 加载失败 -> 嵌入件降级为「资产不可用」如实记账, 不静默跳过
        payload = {"inputs_sha256": input_files, "model_asset": asset,
                   "asset_unavailable": {
                       "error": load_error,
                       "action": "阶段 B 嵌入件未产出; 阶段 A 绿态下限不受影响",
                       "discipline": "卡 4: 不静默跳过, 如实记账"}}
        doc = {"meta": {"name": "d2-cross-matcher-embedding", "phase": "B_embedding",
                        "card_id": CARD_ID,
                        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "ASSET_UNAVAILABLE", "script": str(A_SCRIPT.name)},
               "gates": {"all_pass": False, "asset_unavailable": True},
               "payload": payload, "payload_sha256": digest_payload(payload)}
        OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        print("EMBEDDING ASSET UNAVAILABLE: " + str(load_error))
        print("-> " + str(OUT))
        return 1

    store = EmbedStore(model)
    calibration = calibrate(store, mp, d2)
    thr = calibration["threshold_frozen"]

    corpus = d2.load_corpus(mp)
    GreedyEmbedding, HungarianEmbedding = build_embedding_matchers(d2, store, thr)
    # 一次性收齐全部待编码文本（表头 x canonical 配对的两侧）=> 批确定 => 结果确定
    need: list[str] = []
    for tbl in corpus:
        srcs = ([str(x) for x in tbl["orig_header"]]
                + [str(x) for x in tbl["inj_header"]]
                + [str(e["injected"]) for e in tbl["injections"]])
        canons = [str(c) for c in tbl["canonicals"]]
        need += srcs + canons
    store.prime(need)
    # 配对所需: 每个 canonical 与其表内所有源表头都要在库里（上面已覆盖两侧）

    matchers = [d2.GreedyProduction(mp), GreedyEmbedding(mp),
                HungarianEmbedding(mp, t6)]
    kinds = [m.kind for m in matchers]
    per = {m.kind: d2.derive_injections(m, corpus) for m in matchers}
    sums = {k: d2.summarize(per[k]) for k in kinds}
    spectra = {k: d2.spectrum(per[k]) for k in kinds}
    all_types = sorted({r["type"] for r in per["greedy_production"]})

    taus = {}
    for k in kinds:
        per_gamma = {str(g): d2.kendall_tau_b(
            spectra["greedy_production"][str(g)]["ranking_desc"],
            spectra[k][str(g)]["ranking_desc"]) for g in d2.GAMMAS}
        vals = [v["tau"] for v in per_gamma.values() if v["defined"]]
        taus[k] = {"per_gamma": per_gamma, "tau_min": min(vals) if vals else None,
                   "tau_mean": round(sum(vals) / len(vals), 6) if vals else None,
                   "preregistered": k == PREREG_P2["column"]}

    def blind_of(k):
        return [t for t in all_types
                if all(spectra[k][str(g)]["by_type"][t]["visible"] == 0
                       for g in d2.GAMMAS)]

    blind = {k: blind_of(k) for k in kinds}

    d1 = json.loads(D1_ART.read_text(encoding="utf-8"))
    d1_index = {(r["uid"], r["col"]): r for r in d1["payload"]["injections"]}
    mismatch = []
    for r in per["greedy_production"]:
        ref = d1_index.get((r["uid"], r["col"]))
        if ref is None:
            mismatch.append({"key": "%s:%d" % (r["uid"], r["col"]),
                             "reason": "missing_in_d1"})
            continue
        for f in ("class", "detected_at_anchor", "marginal_dH", "absorbed",
                  "canonical_keyset_identical", "visible_by_gamma"):
            if r[f] != ref[f]:
                mismatch.append({"key": "%s:%d" % (r["uid"], r["col"]), "field": f,
                                 "b": str(r[f])[:60], "d1": str(ref[f])[:60]})
    g0 = {"pass": bool(d1["gates"].get("all_pass") and not mismatch
                       and len(per["greedy_production"]) == 118),
          "d1_all_pass": bool(d1["gates"].get("all_pass")),
          "n_rows": len(per["greedy_production"]), "n_mismatches": len(mismatch),
          "mismatches": mismatch[:20],
          "note": "阶段 B 内重算生产件仍须逐条复现 D1, 否则嵌入件对比失分母"}

    d1_abs = [r for r in d1["payload"]["injections"] if r["class"] in ("E", "HI")]
    tm_rows, missing = [], 0
    for ref in d1_abs:
        cells = {}
        for k in kinds:
            r = next((x for x in per[k] if (x["uid"], x["col"]) ==
                      (ref["uid"], ref["col"])), None)
            if r is None:
                missing += 1
                continue
            cells[k] = {"class": r["class"], "marginal_dH": r["marginal_dH"],
                        "absorbed": r["absorbed"],
                        "canonical_keyset_identical": r["canonical_keyset_identical"],
                        "visible_by_gamma": r["visible_by_gamma"],
                        "state": "keep" if r["class"] == ref["class"] else "flip",
                        "flipped_to": None if r["class"] == ref["class"] else r["class"]}
        tm_rows.append({"uid": ref["uid"], "col": ref["col"], "type": ref["type"],
                        "d1_class": ref["class"],
                        "d1_mechanism": ref.get("invisibility_mechanism"),
                        "cells": cells,
                        "n_flips": sum(1 for v in cells.values()
                                       if v["state"] == "flip")})
    g5 = {"pass": bool(len(tm_rows) == 33 and missing == 0
                       and all(len(r["cells"]) == len(kinds) for r in tm_rows)),
          "n_rows": len(tm_rows), "columns": kinds,
          "cells_expected": 33 * len(kinds), "cells_missing": missing,
          "flip_count_by_matcher": {
              k: sum(1 for r in tm_rows
                     if r["cells"].get(k, {}).get("state") == "flip") for k in kinds}}

    d1_eq = [r for r in d1["payload"]["injections"] if r["class"] == "E"]
    eq_rows, eq_missing = [], 0
    for ref in d1_eq:
        per_m = {}
        for k in kinds:
            r = next((x for x in per[k] if (x["uid"], x["col"]) ==
                      (ref["uid"], ref["col"])), None)
            if r is None:
                eq_missing += 1
                per_m[k] = None
                continue
            per_m[k] = {"class": r["class"], "absorbed": r["absorbed"],
                        "keyset_identical": r["canonical_keyset_identical"],
                        "stays_absorbed_equivalent": bool(
                            r["absorbed"] and r["canonical_keyset_identical"])}
        eq_rows.append({"uid": ref["uid"], "col": ref["col"], "type": ref["type"],
                        "per_matcher": per_m})
    eq_flips = [r["uid"] + ":" + str(r["col"]) for r in eq_rows
                for k, v in r["per_matcher"].items()
                if v and not v["stays_absorbed_equivalent"]]
    g3 = {"pass": bool(len(eq_rows) == 7 and eq_missing == 0),
          "n_equivalence_rows": len(eq_rows), "columns": kinds,
          "missing_cells": eq_missing, "n_flips": len(eq_flips), "flips": eq_flips,
          "note": "P-3 属编辑距离族预注册; 此处对嵌入件作同口径观察（非判据）"}

    g1 = {"pass": bool(calibration["n_positive_control_pairs"] >= 100
                       and 0.0 < thr < 1.0
                       and calibration["frozen_before_injection_scoring"]),
          "threshold_frozen": thr,
          "n_positive_control_pairs": calibration["n_positive_control_pairs"],
          "percentile": CALIB_PERCENTILE,
          "note": "定标有效性门（阈值可定标 + 先于注入打分冻结）, 非 P-2 过判"}

    guard = d2.guard_self_test(mp)
    blocked = d2.SOCKET_ATTEMPTS_BLOCKED
    after = {p: sha256_file(p) for p in watch}
    scan = d2.self_source_scan()
    g4 = {"pass": bool(not d2.PORTS_TOUCHED and not d2.ENDPOINT_VIOLATIONS
                       and guard["all_blocked"] and after == watch),
          "ports_touched": sorted(d2.PORTS_TOUCHED),
          "model_service_calls": 0,
          "local_inference_batches": store.batches,
          "local_encoded_texts": store.encoded_texts,
          "endpoint_violations": d2.ENDPOINT_VIOLATIONS,
          "socket_attempts_blocked": {
              "n": len(blocked),
              "ports": sorted({a["port"] for a in blocked if a["port"] is not None}),
              "events": blocked,
              "note": "全部为护栏自证试连, 系统调用前抛错, 零字节收发 => 非端点使用"},
          "active_connection_probes": guard,
          "frozen_and_baseline_inputs_unchanged": after == watch,
          "sha_before": {str(p.relative_to(REPO)): watch[p] for p in watch},
          "source_scan": {"clean": scan["clean"],
                          "files_scanned": scan["files_scanned"],
                          "findings_in_scope": scan["network_findings_in_d2_scope"],
                          "note": "AST 作用域检索沿用阶段 A 件（本脚本 + 自有导入链）"},
          "scope_note": ("sentence_transformers/transformers/huggingface_hub 具备网络"
                         "能力, 本窗四重护栏 = 离线 env 三件套 + local_files_only +"
                         " socket 封死（装载与编码全程在护栏下）+ 试连自证;"
                         " model_service_calls=0 与 local_inference_batches 分列")}

    se = spectra["greedy_embedding"]
    p2_findings = {
        "prereg_status": PREREG_P2["verdict"] + " / " + PREREG_P2["pass_fail"],
        "no_pass_fail_adjudicated": True,
        "ocr_similar_under_embedding": {
            "visible_at_anchor":
                se[str(d2.ANCHOR)]["by_type"]["ocr_similar"]["visible"],
            "n": se[str(d2.ANCHOR)]["by_type"]["ocr_similar"]["n"],
            "visible_any_gamma": any(
                se[str(g)]["by_type"]["ocr_similar"]["visible"] > 0
                for g in d2.GAMMAS)},
        "blind_types_by_matcher": blind,
        "blind_still_ocr_similar_only": {k: blind[k] == ["ocr_similar"] for k in kinds},
        "tau_b_min_vs_production": {k: taus[k]["tau_min"] for k in kinds},
        "spectrum_at_anchor": {k: {t: spectra[k][str(d2.ANCHOR)]["by_type"][t]
                                     ["visibility_rate"] for t in all_types}
                               for k in kinds},
        "absorption_maintained_of_33": {
            k: sum(1 for r in tm_rows if r["cells"].get(k, {}).get("absorbed"))
            for k in kinds},
        "directional_reading": (
            "P-2 探索性: 两个方向都是合法答案。若 ocr_similar 在嵌入件下仍全盲 =>"
            " 「谱结构（存在全盲类型）匹配器无关」获第二打分基支持; 若被照亮 =>"
            " 「盲区位置匹配器相关」获支持, R3 降级表述第一半句翻正")}

    payload = {
        "inputs_sha256": input_files,
        "criterion_provenance": {
            "card": TASK_CARD, "card_id": CARD_ID, "phase": "B_embedding",
            "prereg_P2": PREREG_P2, "anchor_gamma": d2.ANCHOR,
            "gamma_grid": [str(g) for g in d2.GAMMAS],
            "phase_a_artifact_readonly": "logs/graph/eval/d2_cross_matcher_det.json",
            "inheritance": ("可见性判定/三分类/gamma 网格/tau-b 口径逐字沿用阶段 A"
                            " (research/paper_d2_cross_matcher_det.py), 唯一变量 ="
                            " 打分基（字符串编辑距离 -> 语义嵌入余弦）")},
        "model_asset": asset,
        "threshold_calibration": calibration,
        "matchers": {m.kind: m.describe() for m in matchers},
        "spectrum": spectra,
        "ordering_kendall_tau": taus,
        "blind_types": blind,
        "transition_matrix": {"rows_are_d1_absorption_injections": 33,
                              "columns": kinds, "rows": tm_rows,
                              "note": "生产列为参照列（阶段 A 已判定）,"
                                      " 嵌入两列为 P-2 探索列"},
        "equivalence_stability": g3,
        "p2_findings": p2_findings,
        "counts_by_matcher": {k: dict(sums[k], matcher_kind=k) for k in kinds},
        "gate_details": {"G0_production_reproduces_d1": g0,
                         "G1_threshold_calibration_valid": g1,
                         "G3_equivalence_observation_noncriterion": g3,
                         "G4_p4_zero_endpoint_and_readonly": g4,
                         "G5_transition_matrix_completeness": g5},
        "prereg_predicates": {
            "P2_embedding_verdict": "none（探索性, 预注册不设过判 -> 本窗不判定）",
            "P4_zero_endpoint_self_proof_phase_b": g4["pass"],
            "P5_matrix_complete_phase_b_columns": g5["pass"],
            "note": "P-1/P-3 判定见阶段 A 工件; 阶段 B 只补 P-2 谱与迁移证据"}}

    redline = {"phase_a_artifact_not_overwritten": True,
               "phase_a_sha_unchanged": watch[D2A_ART] == sha256_file(D2A_ART),
               "client_identifier_zero_entered": None}
    payload["redline_self_check"] = redline

    doc = {"meta": {"name": "d2-cross-matcher-embedding", "version": "v1",
                    "card_id": CARD_ID, "task_card": TASK_CARD, "report": REPORT,
                    "phase": "B_embedding_exploratory",
                    "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "script": "research/paper_d2_cross_matcher_embed.py",
                    "matchers": kinds, "n_injections": len(per["greedy_production"]),
                    "endpoint_calls": 0, "anchor_gamma": d2.ANCHOR,
                    "gamma_grid": [str(g) for g in d2.GAMMAS],
                    "reproduce": ["HF_HUB_OFFLINE=1 python3 "
                                  "research/paper_d2_cross_matcher_embed.py"]},
           "gates": {"G0_production_reproduces_d1": g0["pass"],
                     "G1_threshold_calibration_valid": g1["pass"],
                     "G3_equivalence_observation_noncriterion": g3["pass"],
                     "G4_p4_zero_endpoint_and_readonly": g4["pass"],
                     "G5_transition_matrix_completeness": g5["pass"],
                     "G6_digest_self_consistency": False,
                     "P2_embedding_pass_fail": "none_by_preregistration"},
           "payload": payload,
           "prereg_predicates": payload["prereg_predicates"]}

    leaks = d2.client_identifier_scan(json.dumps(doc, ensure_ascii=False, sort_keys=True))
    redline["client_identifier_zero_entered"] = not leaks
    g4["pass"] = bool(g4["pass"] and not leaks)
    payload["gate_details"]["G4_p4_zero_endpoint_and_readonly"] = g4
    payload["prereg_predicates"]["P4_zero_endpoint_self_proof_phase_b"] = g4["pass"]

    doc["payload_sha256"] = digest_payload(payload)
    doc["sha256_scope"] = list(SHA_SCOPE)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    back = json.loads(OUT.read_text(encoding="utf-8"))
    doc["gates"]["G6_digest_self_consistency"] = (
        digest_payload(back["payload"]) == back["payload_sha256"])
    doc["gates"]["all_pass"] = bool(
        all(x["pass"] for x in (g0, g1, g3, g4, g5))
        and not leaks and doc["gates"]["G6_digest_self_consistency"])
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")

    print("model bge-m3 loaded on cpu; encoded %d texts in %d local batches"
          % (store.encoded_texts, store.batches))
    print("threshold frozen = %s (p05 of %d positive-control pairs; neg n=%d; margin=%s)"
          % (thr, calibration["n_positive_control_pairs"],
             calibration["n_negative_control_cross_field"],
             calibration["separation_margin_p05_pos_minus_p95_neg"]))
    for k in kinds:
        print("  %-22s H/E/HI=%s/%s/%s tau_min=%s blind=%s ocr_anchor=%s"
              % (k, sums[k]["H"], sums[k]["E"], sums[k]["HI"], taus[k]["tau_min"],
                 blind[k], sums[k]["anchor_detected_by_type"].get(d2.OCR_TYPE)))
    print("anchor spectrum:")
    for k in kinds:
        print("  %-22s %s" % (k, json.dumps(
            {t: spectra[k][str(d2.ANCHOR)]["by_type"][t]["visibility_rate"]
             for t in all_types}, ensure_ascii=False)))
    print("tm rows=%d cells_missing=%d flips=%s"
          % (len(tm_rows), missing, g5["flip_count_by_matcher"]))
    print("gates " + json.dumps(doc["gates"], ensure_ascii=False))
    print("leaks=%s ports_touched=%s service_calls=0 local_batches=%d"
          % (leaks, sorted(d2.PORTS_TOUCHED), store.batches))
    print("payload_sha256=%s -> %s" % (doc["payload_sha256"], OUT))
    return 0 if doc["gates"]["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
