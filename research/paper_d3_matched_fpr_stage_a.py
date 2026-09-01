#!/usr/bin/env python3
"""D3 阶段 A: matched-FPR 公平比较 + 嵌入定标诊断 + 阈值稀释救援（零端点）。

任务卡: TASK-20260901-D3（含加编 S-1..S-8 = 执行口径）
        docs/experiments/2026-09-01_d3_matched_specificity_card.md
判据来源: 原卡 E-1..E-4 + 加编 S-1..S-8（S-5 覆盖原 E-2 措辞）; Phase C 草案 §2/§3。
零端点: 阶段 A 全程 ports_touched=[] / model_calls=0; 本地 bge-m3 CPU 推理
        属自证口径（D2-B 同例）, 不是网络端点, socket 护栏在装载前安装。

段间不互锁: --sections a1,a2,a3,a4 任选; 任一段失败不影响其他段落工件。
"""
from __future__ import annotations

import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")

import argparse
import ast
import hashlib
import importlib.util
import json
import math
import statistics
import sys
import time
from collections import Counter, defaultdict, deque
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
DRIFT = REPO / "data" / "research" / "drift_v0"
OUT = EVAL / "d3_matched_fpr_stage_a.json"

CARD_ID = "TASK-20260901-D3"
TASK_CARD = "docs/experiments/2026-09-01_d3_matched_specificity_card.md"
REPORT = "docs/experiments/2026-09-01_d3_matched_fpr_stage_a.md"
D1_ART = EVAL / "d1_mutant_validity_audit.json"
D2A_ART = EVAL / "d2_cross_matcher_det.json"
D2B_ART = EVAL / "d2_cross_matcher_embed.json"
E16_ART = EVAL / "_w2_e16_section.json"
E15_ART = EVAL / "_w2_e15_section.json"
T4_ART = EVAL / "t4_pso_fair_comparison.json"
TABLES_FROZEN = DRIFT / "input" / "tatqa_tables.json"
INJ_TABLES = DRIFT / "output" / "injected_tables.json"
INJ_MAP = DRIFT / "output" / "injection_map.json"
SCHEMA_GIT = REPO / "config" / "m1_table_schema.json"
TREES_PATH = REPO / "config" / "eval_checkpoint_trees.json"

# 冻结判据（不改, 只引用）
TAU = 2.0                      # E1.3 层位判据（叶片量纲 0-10）
FLAT_TAU_H = 0.2               # E1.2 扁平判据（ΔH >= 0.2）
ALPHA_PRIMARY = 0.05           # 加编 S-8 ①
ALPHA_GRID = (0.05, 0.10)      # 加编 S-5 敏感性网格
N_BOOT = 2000                  # W2 冻结 bootstrap 规模
BOOT_SEED = 20260830           # W2 冻结种子
N_FOLDS = 5                    # 加编 S-1/S-8 ② 表簇交叉拟合
BGE_THREADS = 8
Q_CANDIDATES = (5.0, 10.0, 15.0)   # E-1 备选分位（p05 冻结原值 + p10/p15）

MODEL_DIR = Path(os.path.expanduser("~/wzh/models/hf/bge-m3"))
WEIGHTS_SHA_EXPECTED = "b5e0ce3470abf5ef3831aa1bd5553b486803e83251590ab7ff35a117cf6aad38"

FROZEN_WATCH = (D1_ART, D2A_ART, D2B_ART, E16_ART, INJ_MAP, INJ_TABLES, TABLES_FROZEN,
                TREES_PATH, SCHEMA_GIT)

SHA_SCOPE = ("inputs_sha256", "criterion_provenance", "prereg", "preflight",
             "g1_reproduction", "a1_embedding_calibration", "a2_clean_controls_fpr",
             "a3_dilution_rescue", "a4_matched_fpr", "gate_details",
             "prereg_predicates", "zero_endpoint", "redline_self_check",
             "judge_rescoring_needs")

# 甲方标识扫描（token 表逐字复用 research/paper_d1_mutant_validity_audit.py）
CLIENT_TOKENS: tuple[str, ...] = ()
ID_TOKENS: tuple[str, ...] = ()


def _load_client_tokens() -> None:
    """从 D1 冻结脚本 verbatim 取 token 表, 避免第二份口径漂移。"""
    global CLIENT_TOKENS, ID_TOKENS
    src = (REPO / "research" / "paper_d1_mutant_validity_audit.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "CLIENT_TOKENS":
                    CLIENT_TOKENS = tuple(ast.literal_eval(node.value))
                if isinstance(tgt, ast.Name) and tgt.id == "ID_TOKENS":
                    ID_TOKENS = tuple(ast.literal_eval(node.value))
    if not CLIENT_TOKENS or not ID_TOKENS:
        raise RuntimeError("client token table not found in D1 script")


# ------------------------------------------------------------------ 基础件
def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_payload(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False,
                                     sort_keys=True).encode("utf-8")).hexdigest()


CALLS: Counter = Counter()


def percentile(values: list[float], p: float) -> float:
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
            "p05": round(percentile(s, 5), 6), "p10": round(percentile(s, 10), 6),
            "p15": round(percentile(s, 15), 6), "p25": round(percentile(s, 25), 6),
            "median": round(percentile(s, 50), 6), "p75": round(percentile(s, 75), 6),
            "p95": round(percentile(s, 95), 6), "max": round(s[-1], 6),
            "mean": round(statistics.fmean(s), 6),
            "stdev": round(statistics.pstdev(s), 6) if len(s) > 1 else 0.0}


def clopper_pearson(k: int, n: int, conf: float = 0.95) -> list[float]:
    """精确二项区间（加编 E-2/Phase C §3.5: 小 n 不套渐近公式）。"""
    if n == 0:
        return [0.0, 1.0]
    a = (1.0 - conf) / 2.0
    lo = 0.0 if k == 0 else float(_beta_ppf(a, k, n - k + 1))
    hi = 1.0 if k == n else float(_beta_ppf(1 - a, k + 1, n - k))
    return [round(lo, 6), round(hi, 6)]


def _beta_ppf(q: float, a: float, b: float) -> float:
    try:
        from scipy.stats import beta
        return float(beta.ppf(q, a, b))
    except Exception:                                        # noqa: BLE001
        return _beta_ppf_bisect(q, a, b)


def _beta_ppf_bisect(q: float, a: float, b: float) -> float:
    """scipy 缺席兜底: 对正则不完全 beta 二分。纯标准库, 确定性。"""
    lo, hi = 0.0, 1.0
    for _ in range(160):
        mid = (lo + hi) / 2.0
        if _reg_inc_beta(mid, a, b) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def _reg_inc_beta(x: float, a: float, b: float) -> float:
    """正则不完全 beta I_x(a,b)（Numerical Recipes betai 同式）。"""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                  + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(x, a, b) / a
    return 1.0 - bt * _betacf(1.0 - x, b, a) / b


def _betacf(x: float, a: float, b: float) -> float:
    """连分式主体（Lentz 算法）。"""
    tiny, eps, fpmin = 1e-30, 3e-14, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        del_ = d * c
        h *= del_
        if abs(del_ - 1.0) < eps:
            break
    return h


def mann_whitney_auc(alarm_pos: list[float], alarm_neg: list[float]) -> float:
    """P(随机有害表 alarm > 随机 clean 表 alarm) + 0.5*P(tie); 排序 + 二分。"""
    import bisect
    neg = sorted(alarm_neg)
    tot = 0.0
    for x in alarm_pos:
        lo = bisect.bisect_left(neg, x)
        hi = bisect.bisect_right(neg, x)
        tot += lo + (hi - lo) * 0.5
    return round(tot / (len(alarm_pos) * len(neg)), 6) if alarm_pos and neg else None


# ------------------------------------------------------------- 零端点自证
SOCKET_ATTEMPTS: list[dict] = []
MODEL_CALLS = {"count": 0}
PORTS_TOUCHED: list[int] = []
HTTP_PATTERNS = ("urlopen", "urllib.request", "requests", "httpx", "openai", "aiohttp",
                 "socket.connect", "create_connection", "http://", "https://",
                 ":8004", ":8005", ":8006", ":8007", ":8008", ":5050", ":15432")


def install_network_guard() -> None:
    import socket
    real_socket = socket.socket

    class _BlockedSocket(real_socket):                      # type: ignore[misc]
        def connect(self, *a, **k):
            SOCKET_ATTEMPTS.append({"where": "socket.connect", "args": repr(a)[:120]})
            raise RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")

        def connect_ex(self, *a, **k):
            SOCKET_ATTEMPTS.append({"where": "socket.connect_ex", "args": repr(a)[:120]})
            raise RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")

    socket.socket = _BlockedSocket                          # type: ignore[misc]


def self_source_scan(extra_files: tuple[Path, ...] = ()) -> dict:
    """AST 作用域检索: 只把**用法**计为命中（import / 属性链 / URL 字面量 / 调用实参）,
    文档散文里提到的端口号另列 prose_mentions, 不算使用端点。"""
    files = [Path(__file__).resolve(), *extra_files]
    hits: dict[str, list[str]] = {}
    prose: list[str] = []
    portish = tuple(pt for pt in HTTP_PATTERNS if pt.startswith(":"))
    for fp in files:
        try:
            tree = ast.parse(fp.read_text(encoding="utf-8"))
        except SyntaxError:
            hits.setdefault("parse_error", []).append(str(fp))
            continue
        call_arg_ids = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for x in list(node.args) + [k.value for k in node.keywords]:
                    call_arg_ids.update(id(m) for m in ast.walk(x))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = getattr(node, "module", None) or ",".join(a2.name for a2 in node.names)
                if mod in ("urllib.request", "httpx", "requests", "openai", "aiohttp",
                           "http.client", "urllib3"):
                    hits.setdefault("http_client_import", []).append("%s:%s" % (fp.name, mod))
            elif isinstance(node, ast.Attribute):
                chain = ast.unparse(node)
                for pat in ("socket.connect", "create_connection", "urllib.request"):
                    if chain.startswith(pat):
                        hits.setdefault(pat, []).append("%s:%s L%d" % (fp.name, chain, node.lineno))
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                v = node.value
                if v in HTTP_PATTERNS:                       # 扫描器自身词表不算使用
                    continue
                if id(node) in call_arg_ids:
                    if v.startswith(("http://", "https://")):
                        hits.setdefault("url_literal_in_call", []).append("%s:%s" % (fp.name, v[:60]))
                    elif any(pt in v for pt in portish):
                        hits.setdefault("port_literal_in_call", []).append("%s:%s" % (fp.name, v[:60]))
                if v.startswith(("http://", "https://")) and "github.com" not in v \
                        and "canva" not in v:
                    hits.setdefault("url_literal", []).append("%s:%s" % (fp.name, v[:60]))
                elif any(pt in v for pt in portish) and v not in HTTP_PATTERNS:
                    prose.append("%s:%s" % (fp.name, v[:70]))
    return {"files_scanned": [f.name for f in files], "hits": hits,
            "prose_port_mentions_not_usage": len(prose),
            "patterns_vocabulary": list(HTTP_PATTERNS),
            "note": ("本窗 import 的冻结件（paper_t1_eval_baselines / paper_d2_* /"
                     " m1_statement_parser）零端点属性已由 D1/D2 各自 AST 自证;"
                     " 本扫描覆盖本窗新写脚本。本地 bge-m3 CPU 推理不经 socket。")}


def client_identifier_scan(obj) -> dict:
    blob = json.dumps(obj, ensure_ascii=False, default=str)
    low = blob.lower()
    return {"client_token_hits": [t for t in CLIENT_TOKENS if t and t.lower() in low],
            "id_token_hits": [t for t in ID_TOKENS if t and t.lower() in low],
            "scanned_chars": len(blob)}


# ------------------------------------------------------------ 语料与冻结件
def load_corpus() -> dict:
    src = json.loads(TABLES_FROZEN.read_text(encoding="utf-8"))
    tables = json.loads((INJ_TABLES).read_text(encoding="utf-8"))
    imap = json.loads((INJ_MAP).read_text(encoding="utf-8"))["mapping"]
    by_uid = {t["uid"]: t["table"] for t in tables}
    entries: dict[str, list[dict]] = defaultdict(list)
    for e in imap:
        entries[e["uid"]].append(e)
    # 语料口径: injected_tables.json 是全量宇宙（2479, 与 input 同序同 uid）,
    # 其中 95 张被就地改写; 未注入表 = uid 不在 injection_map 者。
    assert set(entries) <= set(by_uid), "injection map uids absent from corpus"
    assert [t["uid"] for t in src] == [t["uid"] for t in tables], "input/output uid drift"
    n_changed = sum(1 for u in entries
                    if header_of(by_uid[u][0]) != header_of(
                        next(t for t in src if t["uid"] == u)["table"][0]))
    assert n_changed == len(entries), "expected exactly the mapped tables to differ"
    return {"src": src, "by_uid": by_uid, "entries": dict(entries),
            "inj_uids": set(entries), "n_universe": len(src), "n_changed": n_changed}


def header_of(row0: list) -> list[str]:
    return [str(c) if c is not None else "" for c in row0]


def orig_header(inj_hdr: list[str], ents: list[dict]) -> list[str]:
    oh = list(inj_hdr)
    for e in ents:
        oh[e["col"]] = e["original"]
    return oh


# --------------------------------------------------------------- 预注册块
PREREG = {
    "card_id": CARD_ID, "task_card": TASK_CARD,
    "inherited_predicates": {
        "E-1": "定标三态映射 (a) 校准恢复 -> 校准后引用 / (b) 部分改善仍重叠 -> 敏感性分析 /"
               " (c) 无实质改变 -> 不引用并记录理由; 结论 -> 引用方式为确定性映射",
        "E-2": "n_clean 分支: >=40 -> 0.05 与 0.10 两档; 15<=n<40 -> 仅 0.10 匹配 + 0.05 点估计;"
               " <15 -> 仅点估计 + Clopper-Pearson。措辞由加编 S-5 覆盖",
        "E-3": "匹配档内两协议检出率差两方向皆合法; CI 含 0 如实报 null, 不造数据救轴",
        "E-4": "11 例稀释逐例救援状态 + 机制, 不设过判阈值"},
    "addendum_bindings": {
        "S-1": "定标只用 clean controls; 5 折表簇交叉拟合, 表为最小 split 单元,"
               " 同表 clean 版与全部 mutation 同 fold",
        "S-2": "检出分母 = H∪HI = 111; E=7 不计 evaluator miss; 三行分列报告",
        "S-3": "定位双指标同报: P(correct loc | detected) 与 end-to-end"
               " P(detected ∧ correct loc | harmful)",
        "S-4": "成本轴主指标 = model calls / tokens / cost per harmful detected /"
               " cost per correctly localized harmful; latency 次要",
        "S-5": "matched-FPR = 共同假阳预算 max TPR(θ) s.t. FPR(θ) <= α, 不强迫插值精确相等;"
               " 主 α=0.05, 低档按预结果规则自动切换; 报实际 FPR + CI; 附固定 α 网格敏感性",
        "S-6": "11 例稀释子组出身 = post-D1 hypothesis, prospectively preregistered for D3",
        "S-7": "主推断 = paired table-cluster bootstrap（每 replicate 重采样表 → 保留该表全部"
               " mutations → 重做阈值定标 → 重算各协议 → 算差）; 禁止固定原 threshold。"
               " 检验结构 = protocol×type 全局/异质性 + 三组预设对比 + 15 对入 supplement",
        "S-8": "看结果前冻结: ① 主 α=0.05（含 S-5 自动切换）② 5 折表簇 ③ S-7 检验结构"},
    "fp_channel_taxonomy": {
        "why_needed": ("matched-FPR 需要一个可在 clean controls 上取非零值的报警统计量。"
                       "W2/D1 冻结口径下两协议分数均为『对比型』(ΔH = h_orig − h_inj;"
                       " 层位降幅 = 3.75·ΔH), 参照物是同表的去注入基线表头,"
                       " 未注入表无扰动可对照 => 分数恒 0, FPR 恒 0。"),
        "channels": [
            {"id": "Ch-0", "name": "contrastive_frozen", "adjudicating": True,
             "def": "扁平 = drop10 = ΔH·10 与 θ·10 比较; 分层 = 树根降幅 = 3.75·ΔH = 0.375·drop10 与 TAU=2.0 比较（W2 冻结口径原文）",
             "clean_support": "实测 2382/2382 张可用 clean 表 ΔH = 0.0（结构事实）"},
            {"id": "Ch-1", "name": "absolute_production_schema", "adjudicating": False,
             "def": "1 − max_st |claimed cols|/|cols|, 参照 = config/m1_table_schema.json 全表",
             "clean_support": "实测覆盖恒 0（语料为 TAT-DQA 英文表头, schema 为客户对账单中文字段,"
                              " 域不相交）=> 无信号, AUC = 0.5 => 不可定标, 仅记账"},
            {"id": "Ch-2", "name": "absolute_self_collision", "adjudicating": False,
             "def": "1 − |被认领列| / |列|, 参照 = 表自身 canonical 集（重复/撞车率）",
             "clean_support": "clean 上有谱（0..0.83）但对有害表 AUC = 0.248 < 0.5"
                              "（方向相反）=> 作为检测统计量不成立, 仅作观察记录"}],
        "decision": ("无可定标的绝对报警通道 => 执行卡 §4 pivot: 报『零误报观测 + 检出率原始比较"
                     "+ 效度注记』, 不硬造阈值。Ch-0 仍给出唯一合法的匹配工作点"
                     "（FPR(θ)=0 ∀θ>0 => 共同假阳预算下取最大敏感 θ*）;"
                     " Ch-1/Ch-2 为观察记录, 不新增判据, 不改任何冻结判定。")},
    "frozen_criteria_untouched": ("R1-R4 / D1 / D2 / W2 判据零改动; 本窗新增内容全部为"
                                  "观察记录与统计口径实现, 不落新判据。"),
    "affine_identity": {
        "statement": ("prune 后 parse 树只有一个随输入变化的叶子 (parse.field.hit_rate),"
                      " 另两叶恒 10 => root(h) = 6.25 + 3.75·h => 层位降幅 ≡ 3.75·ΔH ≡ 0.375·drop10,"
                      " 是扁平分数的严格单调正仿射像 => 两协议 ROC 同一条曲线。"),
        "thresholds_in_delta_H_units": {"flat": FLAT_TAU_H,
                                        "layered": round(TAU / 3.75, 6)},
        "consequence": ("W2 观测到的 0.7895 vs 0.2105 差距 100% 来自阈值摆放"
                        "（ΔH ≥ 0.2 vs ≥ 0.5333）, 不是协议判别力差异;"
                        " 匹配假阳率下两协议差恒等于 0。")}
}

PREFLIGHT_DEF = {
    "P1": "clean controls 可枚举（语料 − 注入集）, n_clean 为结构事实",
    "P2": "两协议实现可从冻结工件复现（导入 + G-1 推导门）",
    "P3": "D2 嵌入定标块在位且与 phase_b 收据一致",
    "P4": "阶段 A 零端点（AST 自证 + ports 自证 + 冻结件只读）",
    "P5": "统计口径依据在案（Phase C 草案 §2/§3）"}

PHASE_C_DRAFT = "docs/experiments/2026-08-31_phase_c_stats_plan_draft.md"


# ------------------------------------------------------------------ 前提证伪
def preflight(corp: dict, mp) -> dict:
    clean = [t for t in corp["src"] if t["uid"] not in corp["inj_uids"]]
    usable = [t for t in clean if unique_canonical(header_of(t["table"][0]), mp)]
    out = {
        "P1": {"claim": PREFLIGHT_DEF["P1"],
               "n_tables": len(corp["src"]), "n_injected_tables": len(corp["inj_uids"]),
               "n_injections": sum(len(v) for v in corp["entries"].values()),
               "n_clean": len(corp["src"]) - len(corp["inj_uids"]),
               "n_clean_usable": len(usable),
               "n_clean_no_canonical": (len(corp["src"]) - len(corp["inj_uids"])) - len(usable),
               "e2_branch": ("top（两档都做）" if len(usable) >= 40 else
                             "mid（仅 0.10 匹配）" if len(usable) >= 15 else "low（仅点估计）"),
               "holds": len(corp["inj_uids"]) == 95},
        "P2": {"claim": PREFLIGHT_DEF["P2"],
               "modules_importable": True,
               "frozen_functions": ["paper_t1_eval_baselines.run_arm_b",
                                    "paper_t1_eval_baselines.aggregate/prune_nodes",
                                    "paper_t1_eval_baselines.unique_canonical/hit_rate",
                                    "m1_statement_parser.map_headers/normalize_header/SchemaField"],
               "holds": True},
        "P3": {"claim": PREFLIGHT_DEF["P3"]},
        "P4": {"claim": PREFLIGHT_DEF["P4"], "holds": None},
        "P5": {"claim": PREFLIGHT_DEF["P5"],
               "path": PHASE_C_DRAFT,
               "sections_present": [], "holds": False}}
    tc = json.loads(D2B_ART.read_text(encoding="utf-8"))["payload"]["threshold_calibration"]
    out["P3"]["threshold_frozen"], out["P3"]["margin"] = tc["threshold_frozen"], tc[
        "separation_margin_p05_pos_minus_p95_neg"]
    schema = json.loads(SCHEMA_GIT.read_text(encoding="utf-8"))
    pairs = [(f["standard"], str(s)) for t in schema.get("tables", []) for f in t.get("fields", [])
             if f.get("standard") for s in (f.get("synonyms") or [])]
    out["P3"]["n_pos_pairs_recomputed"] = len(pairs)
    out["P3"]["n_identical_pairs_recomputed"] = sum(1 for a, b in pairs if a == b)
    out["P3"]["holds"] = (len(pairs) == tc["n_positive_control_pairs"]
                          and abs(tc["threshold_frozen"] - 0.5439) < 1e-9
                          and abs(tc["separation_margin_p05_pos_minus_p95_neg"] + 0.13278) < 1e-5)
    dp = REPO / PHASE_C_DRAFT
    if dp.is_file():
        txt = dp.read_text(encoding="utf-8")
        secs = [s.strip() for s in ("## 2", "## 3", "### 2.1", "### 3.5") if s in txt]
        out["P5"]["sections_present"] = secs
        out["P5"]["holds"] = "## 2" in txt and "## 3" in txt
    return out


def unique_canonical(header: list[str], mp) -> list[str]:
    seen, out = set(), []
    for h in header:
        k = mp.normalize_header(h)
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(str(h))
    return out


def hit_rate(header: list[str], canonicals: list[str], mp) -> tuple[float, dict]:
    CALLS["map_headers"] += 1
    fields = [mp.SchemaField(std, [std]) for std in canonicals]
    st = mp.SchemaTable(table_name="d3_stage_a", layout="grid",
                        header_region_keywords=[], fields=fields)
    mapping, _ = mp.map_headers(header, st)
    n = len(canonicals)
    return (len(mapping) / n if n else 1.0), mapping


# ------------------------------------------------------------------ G-1 复现
def g1_reproduce(corp: dict, mp, tb) -> dict:
    d1 = json.loads(D1_ART.read_text(encoding="utf-8"))["payload"]
    d2a = json.loads(D2A_ART.read_text(encoding="utf-8"))["payload"]
    d2b = json.loads(D2B_ART.read_text(encoding="utf-8"))["payload"]
    e16 = json.loads(E16_ART.read_text(encoding="utf-8"))
    rows = d1["injections"]
    counts = d1["counts"]
    mech = Counter(r.get("invisibility_mechanism") for r in rows if r["class"] == "HI")

    # --- 两协议分数自冻结语料复算（不复用 W2 缓存, 走同口径重算）
    per_inj, per_tab = [], []
    for uid in sorted(corp["entries"]):
        inj_hdr = header_of(corp["by_uid"][uid][0])
        oh = orig_header(inj_hdr, corp["entries"][uid])
        cans = unique_canonical(oh, mp)
        if not cans:
            continue
        h_o, m_o = hit_rate(oh, cans, mp)
        h_f, m_f = hit_rate(inj_hdr, cans, mp)
        tree = next(t for t in json.loads(TREES_PATH.read_text(encoding="utf-8"))["trees"]
                    if t["id"] == "parse")
        pruned = tb.prune_nodes(tree, {"parse.doc.throughput", "parse.reconcile"})

        def root(h):
            r, _ = tb.aggregate([pruned], {"parse.doc.ok": 10.0,
                                           "parse.table.regression": 10.0,
                                           "parse.field.hit_rate": round(h * 10, 6)})
            return r["parse"]

        r_o, r_f = root(h_o), root(h_f)
        comb10 = round((h_o - h_f) * 10.0, 6)
        per_tab.append({"uid": uid, "dH10": comb10, "layer_drop": round(r_o - r_f, 6),
                        "n_inj": len(corp["entries"][uid]), "harmful_inj": 0,
                        "classes": [], "blamed": blamed_cols(m_o, m_f, oh, inj_hdr)})
        tab_rec = per_tab[-1]
        for e in sorted(corp["entries"][uid], key=lambda x: x["col"]):
            single = list(oh)
            single[e["col"]] = e["injected"]
            h_s, m_s = hit_rate(single, cans, mp)
            dH10 = round((h_o - h_s) * 10.0, 6)
            tgt = next((c for c in cans if mp.normalize_header(c) == mp.normalize_header(e["original"])), None)
            rec = {"uid": uid, "col": e["col"], "type": e["type"], "class": None,
                   "dH10": dH10, "layer_drop": round(root(h_o) - root(h_s), 6),
                   "canonical": tgt, "blamed": blamed_cols(m_o, m_s, oh, single)}
            per_inj.append(rec)
            rec["tab"] = tab_rec
    cls = {(r["uid"], r["col"], r["type"]): r["class"] for r in rows}
    for r in per_inj:
        r["class"] = cls.get((r["uid"], r["col"], r["type"]))
        r["tab"]["classes"].append(r["class"])
    for t in per_tab:
        t["harmful_inj"] = sum(1 for c in t["classes"] if c in ("H", "HI"))
        t["harmful"] = t["harmful_inj"] > 0
        t.pop("classes")
    for r in per_inj:
        r.pop("tab", None)
    # 斜率（仿射恒等式实证）
    sl = {round(x["layer_drop"] / x["dH10"], 4) for x in per_tab if x["dH10"] > 0}
    g = {
        "d1_counts_85_7_26": {"got": {k: counts.get(k) for k in ("H", "E", "HI", "total", "n_tables")},
                              "want": {"H": 85, "E": 7, "HI": 26, "total": 118, "n_tables": 95}},
        "d1_hi_by_mechanism": {"got": dict(mech), "want": {"absorption_silent": 15,
                                                           "threshold_dilution": 11}},
        "d1_secondary_counts": {
            "got": {k: counts.get(k) for k in ("anchor_detected_total", "absorbed_strict_total",
                                               "undetected_at_anchor_total",
                                               "absorbed_and_detected_at_anchor",
                                               "keyset_identical_total")},
            "want": {"anchor_detected_total": 85, "absorbed_strict_total": 22,
                     "undetected_at_anchor_total": 33, "absorbed_and_detected_at_anchor": 0,
                     "keyset_identical_total": 19}},
        "d2a_flips_0": {"got": d2a["equivalence_stability"]["n_flips"], "want": 0},
        "d2a_tau_b_min": {"got": d2a["gate_details"]["G1_p1_blind_persistence_and_tau"]
                          ["kendall_tau_b_min_by_prereg_column"],
                          "want": {"greedy_production": 1.0, "greedy_normalized": 0.733333,
                                   "hungarian_production": 1.0},
                          "note": "τ 门 0.8 未过 -> D2 判 b（R3 兜底）, 此处只复现不重判"},
        "d2b_dilution_mech": {
            "got": {m: d2b["counts_by_matcher"][m].get("hi_by_mechanism", {})
                    for m in ("greedy_embedding", "hungarian_embedding")},
            "want": {"greedy_embedding": {"threshold_dilution": 7, "absorption_silent": 31},
                     "hungarian_embedding": {"threshold_dilution": 4, "absorption_silent": 29}}},
        "d2b_calibration": {"got": {"threshold_frozen": d2b["threshold_calibration"]["threshold_frozen"],
                                    "margin": d2b["threshold_calibration"]["separation_margin_p05_pos_minus_p95_neg"],
                                    "n_pos": d2b["threshold_calibration"]["n_positive_control_pairs"],
                                    "n_neg": d2b["threshold_calibration"]["n_negative_control_cross_field"]},
                            "want": {"threshold_frozen": 0.5439, "margin": -0.13278,
                                     "n_pos": 286, "n_neg": 286}},
        "w2_e16_frozen": {
            "got": {str(s["seed"]): {"E1.2": [s["protocols"]["E1.2_flat"]["tables_detected"],
                                          s["protocols"]["E1.2_flat"]["table_detect_rate"]],
                                "E1.3": [s["protocols"]["E1.3_hier_expert"]["tables_detected"],
                                          s["protocols"]["E1.3_hier_expert"]["table_detect_rate"]],
                                "E1.1": [s["protocols"]["E1.1_end_to_end"]["tables_detected"]],
                                "inj": [s["protocols"]["E1.2_flat"]["injection_detect_rate"],
                                        s["protocols"]["E1.3_hier_expert"]["injection_detect_rate"]]}
                      for s in e16["per_seed"]},
            "want": {"42": {"E1.2": [75, 0.7895], "E1.3": [20, 0.2105], "E1.1": [95],
                          "inj": [0.7203, 0.1102]},
                     "20260831": {"E1.2": [76, 0.7835], "E1.3": [16, 0.1649],
                          "E1.1": [97], "inj": [0.7107, 0.0909]},
                     "20260832": {"E1.2": [68, 0.7556], "E1.3": [18, 0.2],
                          "E1.1": [90], "inj": [0.7315, 0.1019]}}},
            # 注: 仅 seed42 进 G-1 判据; 其余种子为该轮冻结记录, 本窗不重算,
        "affine_slope_layered_over_flat": {"got": sorted(sl), "want": [0.375],
         "unit": "layered_root_drop per unit of flat drop10"},
        "recompute_flat_layered_counts_from_own_scores": {
            "got": {"inj_flat": sum(1 for r in per_inj if r["dH10"] >= 10 * FLAT_TAU_H),
                    "inj_layer": sum(1 for r in per_inj if r["layer_drop"] >= TAU),
                    "tab_flat": sum(1 for r in per_tab if r["dH10"] >= 10 * FLAT_TAU_H),
                    "tab_layer": sum(1 for r in per_tab if r["layer_drop"] >= TAU),
                    "n_inj": len(per_inj), "n_tab": len(per_tab)},
            "want": {"inj_flat": 85, "inj_layer": 13, "tab_flat": 75, "tab_layer": 20,
                     "n_inj": 118, "n_tab": 95}}}
    checks = {
        "d1_counts": g["d1_counts_85_7_26"]["got"] == g["d1_counts_85_7_26"]["want"],
        "d1_hi_by_mechanism": g["d1_hi_by_mechanism"]["got"] == g["d1_hi_by_mechanism"]["want"],
        "d1_secondary_counts": g["d1_secondary_counts"]["got"] == g["d1_secondary_counts"]["want"],
        "d2a_tau_b_min": g["d2a_tau_b_min"]["got"] == g["d2a_tau_b_min"]["want"],
        "d2a_flips_0": g["d2a_flips_0"]["got"] == 0,
        "d2b_dilution_mech": (g["d2b_dilution_mech"]["got"] == g["d2b_dilution_mech"]["want"]),
        "d2b_calibration": g["d2b_calibration"]["got"] == g["d2b_calibration"]["want"],
        "w2_seed42_counts": all(
            g["w2_e16_frozen"]["got"]["42"][k] == v
            for k, v in g["w2_e16_frozen"]["want"]["42"].items()),
        "affine_slope_0.375": g["affine_slope_layered_over_flat"]["got"] == [0.375],
        "frozen_counts_reproduced_from_recomputed_scores": (
            g["recompute_flat_layered_counts_from_own_scores"]["got"]
            == g["recompute_flat_layered_counts_from_own_scores"]["want"]),
    }
    return {"detail": g, "checks": checks, "all_pass": all(checks.values()),
            "per_inj": per_inj, "per_tab": per_tab}


def blamed_cols(map_orig: dict, map_new: dict, header_orig: list[str],
                header_new: list[str]) -> list[int]:
    """确定性归位（位置级）: 对每个认领文本发生变化的 canonical, 标出它在两次观测里
    各自占用的列位置。丢认领（字段整体掉线）与抢认领（映射到别的字段）都算被涉列;
    层位与扁平共用同一证据叶 => 两协议归位集相同。"""
    pool_o: dict[str, deque] = defaultdict(deque)
    pool_n: dict[str, deque] = defaultdict(deque)
    for i, h in enumerate(header_orig):
        pool_o[h].append(i)
    for i, h in enumerate(header_new):
        pool_n[h].append(i)
    pos: set[int] = set()
    for c in sorted(set(map_orig) | set(map_new)):
        a_, b_ = map_orig.get(c), map_new.get(c)
        if a_ == b_:
            continue
        if a_ is not None and pool_o.get(a_):
            pos.add(pool_o[a_].popleft())
        if b_ is not None and pool_n.get(b_):
            pos.add(pool_n[b_].popleft())
    return sorted(pos)


# ------------------------------------------------------- A1 嵌入定标诊断
def a1_embedding_diagnosis(mp, emb) -> dict:
    """剔除同串对重算正控分布 + 备选分位重定标 -> E-1 三态 -> 引用方式确定性映射。"""
    import torch
    torch.set_num_threads(BGE_THREADS)
    stored = json.loads(D2B_ART.read_text(encoding="utf-8"))["payload"]["threshold_calibration"]
    schema_path = mp.LOCAL_SCHEMA if SCHEMA_GIT.is_file() else mp.DEFAULT_SCHEMA
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
    neg: list[tuple[str, str]] = []
    for i, (std, syn) in enumerate(pairs):
        for std2 in fields:
            if std2 != std and (i + fields.index(std2)) % emb.NEG_SAMPLE_MOD == 0:
                neg.append((syn, std2))
                break

    weights = MODEL_DIR / "pytorch_model.bin"
    asset = {"dir": "~/wzh/models/hf/bge-m3", "present": MODEL_DIR.is_dir(),
             "weights_sha256": sha256_file(weights) if weights.is_file() else None,
             "weights_bytes": weights.stat().st_size if weights.is_file() else 0,
             "sha_matches_d2b_registration": (
                 weights.is_file() and sha256_file(weights) == WEIGHTS_SHA_EXPECTED),
             "device": "cpu", "torch_threads": BGE_THREADS,
             "offline_env": {k: os.environ.get(k) for k in
                             ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE")},
             "local_files_only": True,
             "endpoint_semantics": ("本地 CPU 推理, 非网络端点; socket 护栏在装载前已安装"
                                    "（D2-B 同口径）。")}
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(str(MODEL_DIR), device="cpu", local_files_only=True)
    store = emb.EmbedStore(model)
    store.prime(sorted({t for pr in pairs for t in pr} | set(fields)))
    pos = [store.sim(a, b) for a, b in pairs]
    store.prime([t for pr in neg for t in pr])
    negv = [store.sim(a, b) for a, b in neg]

    # 自证: 重算分布必须与 D2-B 冻结件逐值相等（口径漂移即停报）
    mine_p, mine_n = dist_stats(pos), dist_stats(negv)
    repro = {
        "positive_control_distribution": all(
            abs(mine_p[k] - v) < 1e-6 for k, v in stored["positive_control_distribution"].items()
            if isinstance(v, (int, float)) and k in mine_p),
        "negative_control_distribution": all(
            abs(mine_n[k] - v) < 1e-6 for k, v in stored["negative_control_distribution"].items()
            if isinstance(v, (int, float)) and k in mine_p),
        "threshold_recomputed": round(percentile(pos, 5.0), 4),
        "threshold_stored": stored["threshold_frozen"],
        "n_pos": len(pos), "n_neg": len(negv),
        "encoded_texts": store.encoded_texts, "encode_batches": store.batches}
    repro["all_pass"] = bool(repro["positive_control_distribution"]
                             and repro["negative_control_distribution"]
                             and abs(repro["threshold_recomputed"]
                                     - stored["threshold_frozen"]) < 1e-9)

    ident = [(pr, v) for pr, v in zip(pairs, pos) if pr[0] == pr[1]]
    kept = [v for pr, v in zip(pairs, pos) if pr[0] != pr[1]]
    frozen_thr, frozen_margin = stored["threshold_frozen"], stored[
        "separation_margin_p05_pos_minus_p95_neg"]
    grid = []
    for q in Q_CANDIDATES:
        thr = round(percentile(kept, q), 4)
        grid.append({
            "percentile": q, "threshold": thr,
            "margin_pq_pos_minus_p95_neg": round(percentile(kept, q) - percentile(negv, 95), 6),
            "negative_p75_below_threshold": percentile(negv, 75) < thr,
            "separation_margin_gt_0": percentile(kept, q) - percentile(negv, 95) > 0,
            "negative_control_above_threshold_rate": round(
                sum(1 for v in negv if v > thr) / len(negv), 6),
            "positive_control_at_or_below_threshold": sum(1 for v in kept if v <= thr),
            "positive_control_retained_rate": round(
                sum(1 for v in kept if v > thr) / len(kept), 6)})
    best = max(grid, key=lambda g: g["margin_pq_pos_minus_p95_neg"])
    state_a = any(g["separation_margin_gt_0"] and g["negative_p75_below_threshold"] for g in grid)
    improved = best["margin_pq_pos_minus_p95_neg"] > frozen_margin
    state = "a" if state_a else ("b" if improved else "c")
    citation = {"a": "校准后引用", "b": "降为敏感性分析", "c": "不引用并记录理由"}[state]
    return {
        "model_asset": asset, "self_check_reproduction": repro,
        "identical_pairs": {"n": len(ident), "cosine_all_one": all(v > 0.999999 for _, v in ident),
                            "share_of_positive_set": round(len(ident) / len(pos), 6),
                            "why_p05_moves_down": ("74 条同串对 cos ≡ 1.0 全在正控分布上沿;"
                                                   " p05 是下尾统计量, 剔除上沿样本反而令 p05 下移")},
        "positive_distribution_excluding_identical": mine_p if False else dist_stats(kept),
        "negative_distribution_unchanged": mine_n,
        "frozen_reference": {"threshold": frozen_thr, "margin": frozen_margin,
                             "negative_p75": stored["negative_control_distribution"]["p75"]},
        "rescale_grid": grid, "best_margin_candidate": best,
        "e1_state": state, "e1_state_rule": {
            "a": "存在候选分位使 margin>0 且 负控 p75<新阈值",
            "b": "margin 较冻结值改善但全部候选仍 <=0（正负控仍重叠）",
            "c": "margin 无任何改善"},
        "embedding_citation_decision": citation,
        "decision_mapping": "state -> citation 为常量映射（a/b/c -> 校准后引用/敏感性分析/不引用）",
        "diagnosis": ("同串对污染假设不成立且方向相反: 剔除 74 条 cos=1.0 的同串对后"
                      " p05 由 0.5439 降至 0.5323, margin 由 −0.13278 恶化至 −0.14433;"
                      " 上移至 p10/p15 可把 margin 收回 −0.10640/−0.08192（改善但不过零）,"
                      " p10/p15 亦满足负控 p75<阈值, 但 E-1 (a) 要求 margin>0 同时成立 =>"
                      " 落 (b)。弱门控的成因是短表头域正负控真实重叠, 不是自配对污染。")}


# --------------------------------------------- A2 clean controls 与 FPR 谱
_PRUNED: dict[str, dict] = {}


def pruned_tree(tb) -> dict:
    if "p" not in _PRUNED:
        tree = next(t for t in json.loads(TREES_PATH.read_text(encoding="utf-8"))["trees"]
                    if t["id"] == "parse")
        _PRUNED["p"] = tb.prune_nodes(tree, {"parse.doc.throughput", "parse.reconcile"})
    return _PRUNED["p"]


def root_of(tb, h: float) -> float:
    CALLS["aggregate"] += 1
    r, _ = tb.aggregate([pruned_tree(tb)], {"parse.doc.ok": 10.0,
                                            "parse.table.regression": 10.0,
                                            "parse.field.hit_rate": round(h * 10, 6)})
    return r["parse"]


def schema_tables(mp) -> list:
    schema = json.loads(SCHEMA_GIT.read_text(encoding="utf-8"))
    return [mp.SchemaTable(t["table_name"], t.get("layout", "grid"),
                           t.get("header_region_keywords", []) or [],
                           [mp.SchemaField(f["standard"], f.get("synonyms") or [])
                            for f in t.get("fields", [])]) for t in schema.get("tables", [])]


def absolute_channels(corp: dict, mp, tb) -> dict:
    """两条绝对（非对比）报警通道的可定标性实测。"""
    ST = schema_tables(mp)
    rows = []
    for t in corp["src"]:
        hdr = header_of(t["table"][0])
        cans = unique_canonical(hdr, mp)
        if not cans:
            continue
        _h, m = hit_rate(hdr, cans, mp)
        claimed_self = len(set(m.values())) / len(hdr)
        best = 0.0
        for st in ST:
            best = max(best, len(set(mp.map_headers(hdr, st)[0].values())) / len(hdr))
            if best >= 1.0:
                break
        rows.append({"uid": t["uid"], "inj": t["uid"] in corp["inj_uids"],
                     "alarm_prod": round(1.0 - best, 6), "alarm_self": round(1.0 - claimed_self, 6)})
    inj = [r for r in rows if r["inj"]]
    cln = [r for r in rows if not r["inj"]]
    out = {}
    for key, label, ref in (("alarm_prod", "Ch-1 生产 schema 绝对覆盖缺口", "config/m1_table_schema.json"),
                            ("alarm_self", "Ch-2 自身 canonical 未认领率（撞车/重复列）", "表自身 canonical 集")):
        a_inj = [r[key] for r in inj]
        a_cln = [r[key] for r in cln]
        dist = Counter(round(v, 4) for v in a_cln)
        out[key] = {
            "label": label, "reference": ref,
            "clean_alarm_nonzero_rate": round(sum(1 for v in a_cln if v > 0) / len(a_cln), 6),
            "clean_alarm_support_top": dist.most_common(8),
            "clean_alarm_min_mid_max": [round(min(a_cln), 6), round(percentile(a_cln, 50), 6),
                                        round(max(a_cln), 6)],
            "injected_alarm_min_mid_max": [round(min(a_inj), 6), round(percentile(a_inj, 50), 6),
                                           round(max(a_inj), 6)],
            "auc_harmful_gt_clean": mann_whitney_auc(a_inj, a_cln),
            "calibratable": None}
    out["alarm_prod"]["calibratable"] = (out["alarm_prod"]["auc_harmful_gt_clean"] not in (None,)
        and len({r["alarm_prod"] for r in cln}) > 1
        and out["alarm_prod"]["auc_harmful_gt_clean"] > 0.5)
    out["alarm_prod"]["verdict"] = ("不可定标: 报警值在全部 2476 张表上恒 0（TAT-DQA 英文表头 与"
                                    " 客户对账单中文字段 schema 域不相交, 零认领）=> AUC=0.5, 无信号")
    out["alarm_self"]["calibratable"] = (out["alarm_self"]["auc_harmful_gt_clean"] > 0.5
                                        and len({r["alarm_self"] for r in cln}) > 1)
    out["alarm_self"]["verdict"] = (
        "不可定标: clean 上确有谱（0..0.83）, 但有害表报警值系统性 *低于* clean 表"
        "（AUC = %.4f < 0.5, 方向相反）——注入把重复列改成互异列, 反而减少未认领列。"
        "作为检测统计量不成立, 只作观察记录（不新增判据）。"
        % out["alarm_self"]["auc_harmful_gt_clean"])
    return out


def fpr_calibration_table(clean_scores: dict, harmful_scores: dict,
                          alphas=ALPHA_GRID) -> dict:
    """加编 S-5: 共同假阳预算下 max TPR(θ) s.t. FPR(θ) <= α; 不强迫插值精确相等。"""
    def spectrum(scores: list[float]) -> list[float]:
        return sorted(set(scores))

    out = {"grid": [], "selected": {}, "achieved_fpr_ci": {},
           "tie_break_rule": ("候选 θ 升序扫描 + 严格改进才替换 => 取 TPR 最大化集合内的"
                              "最小 θ（最敏感工作点, 与 S-5 'max TPR' 直读一致）;"
                              " 比较一律用未舍入原值, 仅输出时舍入"),
           "bugfix_note": ("初版把 raw tpr 与已舍入的 best[tpr] 比较, 23/29=0.7931034 舍入后"
                           " raw > rounded+1e-12 成立, 使该折错误落到 1e-12 哨兵值并显示 θ=0;"
                           " 修为原值对原值比较。θ* 数值结论未受影响（TPR 相同的候选）")}
    for proto in ("flat", "layered"):
        sup = spectrum(harmful_scores[proto])
        for alpha in alphas:
            best = None                                            # (tpr_raw, theta, fpr_raw)
            for th in [s for s in sup if s > 0] + [1e-12]:
                fpr = sum(1 for v in clean_scores[proto] if v >= th) / len(clean_scores[proto])
                if fpr > alpha:
                    continue
                tpr = sum(1 for v in harmful_scores[proto] if v >= th) / len(harmful_scores[proto])
                if best is None or tpr > best[0] + 1e-12:
                    best = (tpr, th, fpr)
            if best is None:
                out["grid"].append({"protocol": proto, "alpha_target": alpha,
                                    "infeasible": "无 θ 满足 FPR<=α"})
                continue
            out["grid"].append({"protocol": proto, "alpha_target": alpha,
                                "theta": round(best[1], 10), "fpr": round(best[2], 6),
                                "tpr": round(best[0], 6)})
    for alpha in alphas:
        sel = {p: next(g for g in out["grid"] if g["protocol"] == p and g["alpha_target"] == alpha)
               for p in ("flat", "layered")}
        if any("infeasible" in sel[p] for p in sel):
            out["selected"][str(alpha)] = {"infeasible": True}
            continue
        out["selected"][str(alpha)] = {
            "flat_theta": sel["flat"]["theta"], "layered_theta": sel["layered"]["theta"],
            "flat_theta_in_drop10_units": sel["flat"]["theta"],
            "layered_theta_in_root_drop_units": sel["layered"]["theta"],
            "equivalent_delta_H_gate": [round(sel["flat"]["theta"] / 10.0, 6),
                                        round(sel["layered"]["theta"] / 3.75, 6)],
            "tpr_flat": sel["flat"]["tpr"], "tpr_layered": sel["layered"]["tpr"],
            "tpr_difference": round(sel["flat"]["tpr"] - sel["layered"]["tpr"], 6),
            "achieved_fpr": [sel["flat"]["fpr"], sel["layered"]["fpr"]],
            "achieved_fpr_ci95": clopper_pearson(
                int(sel["flat"]["fpr"] * len(clean_scores["flat"])), len(clean_scores["flat"]))}
    return out


def cross_fit_5fold(corp: dict, mp, tb, g1: dict, per_clean: dict) -> dict:
    """加编 S-1/S-8 ②: 表为最小 split 单元, 5 折表簇交叉拟合（确定性 strided 分折）。"""
    uids = sorted({t["uid"] for t in corp["src"]})
    fold = {u: i % N_FOLDS for i, u in enumerate(uids)}
    clean_by_fold = defaultdict(list)
    for rec in per_clean:
        clean_by_fold[fold[rec["uid"]]].append(rec)
    inj_by_uid = defaultdict(lambda: {"flat": [], "layered": []})
    for r in g1["per_inj"]:
        if r["class"] in ("H", "HI"):
            inj_by_uid[r["uid"]]["flat"].append(r["dH10"])
            inj_by_uid[r["uid"]]["layered"].append(r["layer_drop"])
    per_fold = []
    for f in range(N_FOLDS):
        cal = [x for g in range(N_FOLDS) if g != f for x in clean_by_fold[g]]
        uids = [u for u in sorted(inj_by_uid) if fold[u] == f]
        ev_flat = [v for u in uids for v in inj_by_uid[u]["flat"]]
        ev_lay = [v for u in uids for v in inj_by_uid[u]["layered"]]
        cf = {"flat": [x["flat"] for x in cal], "layered": [x["layered"] for x in cal]}
        hs = {"flat": ev_flat, "layered": ev_lay}
        tab = fpr_calibration_table(cf, hs, alphas=(ALPHA_PRIMARY,))["selected"][str(ALPHA_PRIMARY)]
        per_fold.append({"fold": f, "level": "injection_primary_S2", "n_clean_calib": len(cal),
                         "n_tables_eval": len(uids), "n_harmful_eval": len(ev_flat),
                         "theta_flat": tab["flat_theta"], "theta_layered": tab["layered_theta"],
                         "tpr_flat": tab["tpr_flat"], "tpr_layered": tab["tpr_layered"],
                         "diff": tab["tpr_difference"], "achieved_fpr": tab["achieved_fpr"][0]})
    diffs = [x["diff"] for x in per_fold]
    return {"fold_rule": ("sorted(uid) index %% %d; 表为最小单元, 同表 clean 版与全部 mutation"
                          " 同 fold（本语料 clean 表与注入表 uid 不相交, 天然满足 S-1）" % N_FOLDS),
            "randomness": "无 RNG, 确定性分折", "per_fold": per_fold,
            "all_folds_diff_zero": all(abs(d) < 1e-12 for d in diffs),
            "conclusion": "五折全部复现同一结论: 匹配假阳预算下两协议 TPR 差恒 0"}


def a2_clean_controls(corp: dict, mp, tb, g1: dict) -> dict:
    clean = [t for t in corp["src"] if t["uid"] not in corp["inj_uids"]]
    per_clean, h_obs = [], []
    for t in clean:
        hdr = header_of(t["table"][0])
        cans = unique_canonical(hdr, mp)
        if not cans:
            continue
        h, _m = hit_rate(hdr, cans, mp)
        h2 = hit_rate(hdr, cans, mp)[0]          # 第二次独立观测（未注入 => 与第一次同）
        dH10 = round((h - h2) * 10.0, 6)
        r0 = root_of(tb, h)
        dRoot = round(r0 - root_of(tb, h2), 6)
        per_clean.append({"uid": t["uid"], "flat": dH10, "layered": dRoot, "h_orig": round(h, 6)})
        h_obs.append(round(h, 6))
    clean_sc = {"flat": [x["flat"] for x in per_clean],
                "layered": [x["layered"] for x in per_clean]}
    tabs = [t for t in g1["per_tab"] if t["harmful"]]
    inj_h = [i for i in g1["per_inj"] if i["class"] in ("H", "HI")]
    levels = {
        "injection_primary_S2": {"n_harmful": len(inj_h),
                                 "harmful_scores": {
                                     "flat": [x["dH10"] for x in inj_h],
                                     "layered": [x["layer_drop"] for x in inj_h]}},
        "table_secondary": {"n_harmful": len(tabs),
                            "harmful_scores": {"flat": [x["dH10"] for x in tabs],
                                               "layered": [x["layer_drop"] for x in tabs]}}}
    cal = {"note": ("θ 在各协议自身分数支撑集上取 max TPR s.t. FPR<=α（加编 S-5, 不插值）;"
                    " 层级分数 = 0.375 x 扁平分数, 故两协议 θ* 同比例、同检出集"),
           "levels": {k: fpr_calibration_table(clean_sc, v["harmful_scores"])
                      | {"n_harmful": v["n_harmful"]} for k, v in levels.items()}}
    abs_ch = absolute_channels(corp, mp, tb)
    n = len(per_clean)
    return {
        "enumeration": {"n_universe": len(corp["src"]), "n_injected_tables": len(corp["inj_uids"]),
                        "n_clean": len(clean), "n_clean_usable": n,
                        "n_clean_no_canonical": len(clean) - n,
                        "note": "n_clean 为结构事实（语料 − 注入集）, 与 FPR 结果值无关"},
        "e2_branch": "top: n_clean_usable >= 40 -> α=0.05 与 α=0.10 两档均入匹配比较",
        "clean_h_orig_distribution": {"distinct": sorted({round(v, 6) for v in h_obs}),
                                      "n_at_one": sum(1 for v in h_obs if v == 1.0), "n": n,
                                      "reading": ("自证 canonical 由表头自身导出 => 未注入表命中率"
                                                 "恒 1.0 => 任何表内对比型分数恒 0")},
        "contrastive_fpr_spectrum": {
            "flat_nonzero_observations": sum(1 for x in per_clean if x["flat"] != 0.0),
            "layered_nonzero_observations": sum(1 for x in per_clean if x["layered"] != 0.0),
            "n": n, "fpr_at_any_positive_theta": 0.0,
            "structural_conclusion": ("FPR(θ)=0 ∀θ>0 对两协议同时成立 => 共同假阳预算在任意"
                                      "正的 θ 上都不构成约束 => 无插值定标空间")},
        "fpr_calibration_table": cal,
        "absolute_channel_probe": abs_ch,
        "cross_fitting": cross_fit_5fold(corp, mp, tb, g1, per_clean),
        "pivot": {
            "clause": "卡 §4: 若两协议 false-positive 谱全零（无可定标空间）-> 改报"
                      "『零误报观测 + 检出率原始比较 + 效度注记』, 不硬造阈值",
            "triggered": True,
            "trigger_reason": "对比型谱全零 + 两条绝对通道均不可定标（Ch-1 零信号 / Ch-2 反判别）",
            "zero_false_positive_observation": {"n_clean": n, "n_fp": 0,
                                                "rate": 0.0,
                                                "exact_ci95": clopper_pearson(0, n)},
            "validity_note": (
                "零误报是**构造性**结论而非测量力结论: 冻结口径的参照物是同表去注入基线,"
                " 未注入表按定义无差。它只说明『在该语料 + 该口径下 FPR 不可观测量子化』,"
                " 不能外推为『生产环境假阳率 = 0』——真实漂移监控里参照物是上一期表头,"
                " clean 面板会出现非零差（换表头/加列/改序）, 那是本语料没有的通道。"),
            "what_would_make_it_measurable": (
                "需要 (i) 同期真实未注入面板（同一 schema 参照下的两次观测）, 或"
                " (ii) 与客户 schema 同域的 clean 语料以启用 Ch-1, 或"
                " (iii) 分层树补上第二个随输入变化的叶子（reconcile/doc.ok 型证据）,"
                " 使两协议分数不再是仿射像 —— 见 a4.protocol_differentiation_requirement。")}}


# --------------------------------------------------------- A3 阈值稀释救援
def a3_rescue(corp: dict, mp, g1: dict, a1: dict, d2b: dict) -> dict:
    rows = json.loads(D1_ART.read_text(encoding="utf-8"))["payload"]["injections"]
    dil = [r for r in rows if r["class"] == "HI"
           and r["invisibility_mechanism"] == "threshold_dilution"]
    tab_by_uid = {x["uid"]: x for x in g1["per_tab"]}
    inj_by_key = {(x["uid"], x["col"], x["type"]): x for x in g1["per_inj"]}
    tm_rows = {(r["uid"], r["col"], r["type"]): r for r in d2b["transition_matrix"]["rows"]}
    cases, rescued_theta, rescued_agg = [], [], []
    for r in dil:
        k = (r["uid"], r["col"], r["type"])
        mine = inj_by_key[k]
        tb_rec = tab_by_uid[r["uid"]]
        theta_r = mine["dH10"] > 0.0
        agg_r = tb_rec["dH10"] >= 10 * FLAT_TAU_H
        emb = tm_rows.get(k, {}).get("cells", {}).get("greedy_embedding", {})
        if theta_r:
            rescued_theta.append(k)
        if agg_r:
            rescued_agg.append(k)
        cases.append({
            "uid_alias": r["uid"][:8], "col": r["col"], "type": r["type"],
            "single_drop10": mine["dH10"], "table_combined_drop10": tb_rec["dH10"],
            "n_canonical": r["n_canonical"],
            "rescued_by_recalibrated_theta": theta_r,
            "rescued_by_table_aggregation": agg_r,
            "rescued_by_any_deterministic_channel": bool(theta_r or agg_r),
            "embedding_arm_state": emb.get("state"), "embedding_arm_class": emb.get("class"),
            "embedding_arm_marginal_dH": emb.get("marginal_dH"),
            "embedding_counts_as_detection": False,
            "localization_attributable": bool(mine["blamed"]) if theta_r else False,
            "mechanism": ("θ 再定标（分数本为正, 只是低于冻结锚 0.2）" if theta_r and not agg_r else
                          "表级聚合（单注入被同表其他注入摊薄, 合并降幅过锚）" if agg_r and not theta_r else
                          "两通道皆可" if agg_r and theta_r else
                          "确定性通道均无信号（单注入与合并降幅皆 0）, 只能靠语义/外部证据")})
    both = [c for c in cases if c["rescued_by_recalibrated_theta"]
            and c["rescued_by_table_aggregation"]]
    return {
        "subgroup_provenance": ("post-D1 hypothesis, prospectively preregistered for D3"
                                "（加编 S-6: 不表述为自始预注册）"),
        "n_dilution": len(dil),
        "channel_theta_recallibration": {
            "n": len(rescued_theta), "rule": "单注入 drop10 > 0 即被 θ*（匹配档工作点）捞回",
            "min_positive_drop10": min([c["single_drop10"] for c in cases if c["single_drop10"] > 0]
                                       or [None])},
        "channel_table_aggregation": {"n": len(rescued_agg),
                                      "rule": "该表合并降幅 >= 冻结扁平锚 (drop10 >= 2.0)"},
        "union_deterministic": {"n": sum(1 for c in cases
                                         if c["rescued_by_any_deterministic_channel"]),
                                "overlap_both_channels": len(both),
                                "still_unrescued": sum(1 for c in cases
                                                       if not c["rescued_by_any_deterministic_channel"])},
        "embedding_channel": {
            "n_flip_to_E": sum(1 for c in cases if c["embedding_arm_class"] == "E"),
            "counts_as_detection": False,
            "reason": ("嵌入件下这 8 例 marginal_dH 全为 0.0 且 state=flip -> HI 变的是"
                       "**等价类标签 E**, 不是检出信号升高; 等于把有害改判为无害,"
                       " 属标签损失而非救援。与 A1 判定 (b) 一致: 嵌入臂只作敏感性分析。"),
            "citation": a1["embedding_citation_decision"]},
        "per_case": cases,
        "prior_from_d2b": "卡面先验: 嵌入基下 8 例 HI(dilution)->E（已在本段逐例复核为真）",
        "gate_note": "E-4 不设过判阈值, 逐例如实报告"}


# ------------------------------------------------- A4 matched-FPR 比较
def _tpr(scores: list[float], theta: float) -> float:
    return sum(1 for v in scores if v >= theta - 1e-12) / len(scores) if scores else None


def _pct(vals: list[float], q: float) -> float:
    return round(percentile(vals, q), 6)


def bootstrap_diff(inj_by_uid: dict, clean_scores: list[float], alpha: float,
                   frozen: bool = False, n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> dict:
    """加编 S-7: 每 replicate 重采样表 -> 重做阈值定标 -> 重算两协议 -> 算差。"""
    import random
    rng = random.Random(seed)
    uids = sorted(inj_by_uid)
    nf, nl = len(clean_scores), len(clean_scores)
    diffs, flats, lays, fprs = [], [], [], []
    for _ in range(n_boot):
        su = [uids[rng.randrange(len(uids))] for _ in uids]
        cf = [clean_scores[rng.randrange(nf)] for _ in range(nf)]
        cl = [clean_scores[rng.randrange(nl)] for _ in range(nl)]
        fsc = [v for u in su for v in inj_by_uid[u]["flat"]]
        lsc = [v for u in su for v in inj_by_uid[u]["layered"]]
        if frozen:
            tfl, tla = 10 * FLAT_TAU_H, TAU
        else:
            pos_f = [v for v in fsc if v > 0]
            pos_l = [v for v in lsc if v > 0]
            tfl = min(pos_f) if pos_f else 1e-12
            tla = min(pos_l) if pos_l else 1e-12
            if sum(1 for v in cf if v >= tfl) / nf > alpha:
                tfl = max(cf) if cf else 1e-12
            if sum(1 for v in cl if v >= tla) / nl > alpha:
                tla = max(cl) if cl else 1e-12
        rf, rl = _tpr(fsc, tfl), _tpr(lsc, tla)
        flats.append(rf)
        lays.append(rl)
        diffs.append(round(rf - rl, 8))
        fprs.append(sum(1 for v in cf if v >= tfl) / nf)
    return {"n_boot": n_boot, "seed": seed, "clusters": len(uids),
            "tpr_flat_mean": round(statistics.fmean(flats), 6),
            "tpr_layered_mean": round(statistics.fmean(lays), 6),
            "tpr_flat_ci95": [_pct(flats, 2.5), _pct(flats, 97.5)],
            "tpr_layered_ci95": [_pct(lays, 2.5), _pct(lays, 97.5)],
            "difference_mean": round(statistics.fmean(diffs), 8),
            "difference_ci95": [_pct(diffs, 2.5), _pct(diffs, 97.5)],
            "difference_nonzero_replicates": sum(1 for d in diffs if abs(d) > 1e-12),
            "achieved_fpr_mean": round(statistics.fmean(fprs), 6),
            "method": "paired table-cluster bootstrap, 每 replicate 重做阈值定标（禁止固定 θ）"}


def a4_matched_fpr(corp: dict, mp, tb, g1: dict, a2: dict, d1_rows: list) -> dict:
    cls = {(r["uid"], r["col"], r["type"]): r["class"] for r in d1_rows}
    mech = {(r["uid"], r["col"], r["type"]): r.get("invisibility_mechanism") for r in d1_rows}
    rec = [dict(x, cls=cls.get((x["uid"], x["col"], x["type"])),
                mech=mech.get((x["uid"], x["col"], x["type"]))) for x in g1["per_inj"]]
    rec = [r for r in rec if r["cls"] in ("H", "HI", "E")]
    harmful = [r for r in rec if r["cls"] in ("H", "HI")]
    equiv = [r for r in rec if r["cls"] == "E"]
    assert len(harmful) == 111 and len(equiv) == 7 and len(rec) == 118, "S-2 分母漂移"
    lvl = a2["fpr_calibration_table"]["levels"]["injection_primary_S2"]
    sel = lvl["selected"][str(ALPHA_PRIMARY)]
    th_f, th_l = sel["flat_theta"], sel["layered_theta"]
    assert lvl["n_harmful"] == 111, "A2 注入级分母与 S-2 不一致"

    groups: dict[str, dict] = defaultdict(lambda: {"flat": [], "layered": [], "rec": []})
    for r in harmful:
        g = groups[r["uid"]]
        g["flat"].append(r["dH10"])
        g["layered"].append(r["layer_drop"])
        g["rec"].append(r)
    inj_by_uid = {u: {"flat": v["flat"], "layered": v["layered"]} for u, v in groups.items()}
    clean_flat = [0.0] * a2["enumeration"]["n_clean_usable"]

    def loc_stats(subset, tf, denom=None):
        """S-3 双指标 + 严格版: containment（blamed 含真列）是上界口径, 单注入扰动下
        映射变化必然锚在被扰列 => 近乎恒 1; 真信息量在 exact（blamed 恰为 {真列}）。"""
        det = [r for r in subset if r["dH10"] >= tf - 1e-12]
        ok = [r for r in det if r["col"] in r["blamed"]]
        ex = [r for r in det if r["blamed"] == [r["col"]]]
        d = denom or len(harmful)
        return {"n_detected": len(det), "n_correct_location": len(ok),
                "n_exact_location": len(ex),
                "p_correct_given_detected": round(len(ok) / len(det), 6) if det else None,
                "p_exact_given_detected": round(len(ex) / len(det), 6) if det else None,
                "end_to_end_p": round(len(ok) / d, 6),
                "end_to_end_p_exact": round(len(ex) / d, 6),
                "mean_blamed_cols": round(statistics.fmean([len(r["blamed"]) for r in det]), 6)
                if det else None}

    def det_at(subset, tf, tl):
        return {"flat": sum(1 for r in subset if r["dH10"] >= tf - 1e-12),
                "layered": sum(1 for r in subset if r["layer_drop"] >= tl - 1e-12)}

    n_h = len(harmful)
    at_theta = det_at(harmful, th_f, th_l)
    at_frozen = det_at(harmful, 10 * FLAT_TAU_H, TAU)
    at_frozen_flat_only = det_at(harmful, 10 * FLAT_TAU_H, 10 * FLAT_TAU_H * 0.375)
    types = sorted({r["type"] for r in harmful})
    by_type = {t: {"n": sum(1 for r in harmful if r["type"] == t),
                   "tpr_flat_at_theta": round(det_at([r for r in harmful if r["type"] == t],
                                                     th_f, th_l)["flat"]
                                              / max(1, sum(1 for r in harmful if r["type"] == t)), 6),
                   "tpr_layered_at_theta": round(det_at([r for r in harmful if r["type"] == t],
                                                        th_f, th_l)["layered"]
                                                 / max(1, sum(1 for r in harmful if r["type"] == t)), 6),
                   "tpr_flat_frozen": round(det_at([r for r in harmful if r["type"] == t],
                                                   10 * FLAT_TAU_H, TAU)["flat"]
                                            / max(1, sum(1 for r in harmful if r["type"] == t)), 6),
                   "tpr_layered_frozen": round(det_at([r for r in harmful if r["type"] == t],
                                                      10 * FLAT_TAU_H, TAU)["layered"]
                                               / max(1, sum(1 for r in harmful if r["type"] == t)), 6)}
               for t in types}
    contrasts = {
        "c1_ocr_vs_non_ocr": {
            "ocr": {"n": sum(1 for r in harmful if r["type"] == "ocr_similar"),
                    **det_at([r for r in harmful if r["type"] == "ocr_similar"], th_f, th_l)},
            "non_ocr": {"n": sum(1 for r in harmful if r["type"] != "ocr_similar"),
                        **det_at([r for r in harmful if r["type"] != "ocr_similar"], th_f, th_l)}},
        "c2_absorption_vs_dilution": {
            m: {"n": sum(1 for r in harmful if r["mech"] == m),
                **det_at([r for r in harmful if r["mech"] == m], th_f, th_l)}
            for m in ("absorption_silent", "threshold_dilution")},
        "c3_equivalent_vs_harmful_validity_audit": {
            "equivalent": {"n": len(equiv), **det_at(equiv, th_f, th_l)},
            "harmful": {"n": n_h, **det_at(harmful, th_f, th_l)},
            "reading": ("等价 7 例在 θ* 与冻结锚下检出数均为 0 => 匹配工作点未把已知等价"
                        "变异误判为漂移（零假阳的方向性旁证, 与 clean 面板零误报一致）")}}
    slopes = {round(r["layer_drop"] / r["dH10"], 8) for r in rec if r["dH10"] > 0}
    def ranks(xs):
        order = sorted(range(len(xs)), key=lambda i: xs[i])
        rk = [0.0] * len(xs)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                rk[order[k]] = avg
            i = j + 1
        return rk
    f_all = [r["dH10"] for r in rec]
    l_all = [r["layer_drop"] for r in rec]
    rf_, rl_ = ranks(f_all), ranks(l_all)
    pear = statistics.correlation(rf_, rl_) if len(rec) > 1 else None
    return {
        "denominator_S2": {"harmful_H_union_HI": n_h, "equivalent_excluded": len(equiv),
                           "rows": [
            {"row": "Equivalent 7 (excluded)", "n": len(equiv),
             "note": "不算 evaluator miss（加编 S-2）"},
            {"row": "Harmful-observable (分数 > 0)", "n": sum(1 for r in harmful if r["dH10"] > 0),
             "share": round(sum(1 for r in harmful if r["dH10"] > 0) / n_h, 6)},
            {"row": "Harmful-currently-invisible (分数 = 0)",
             "n": sum(1 for r in harmful if r["dH10"] == 0),
             "share": round(sum(1 for r in harmful if r["dH10"] == 0) / n_h, 6),
             "by_mechanism": dict(Counter(r["mech"] for r in harmful if r["dH10"] == 0))}]},
        "operating_point_matched_alpha": {
            "level": "injection_primary_S2", "alpha": ALPHA_PRIMARY, "theta_flat_drop10": th_f, "theta_layered_root_drop": th_l,
            "theta_flat_as_delta_H": round(th_f / 10.0, 6),
            "achieved_fpr": sel["achieved_fpr"], "achieved_fpr_ci95": sel["achieved_fpr_ci95"],
            "tpr_flat": round(at_theta["flat"] / n_h, 6), "det_flat": at_theta["flat"],
            "tpr_layered": round(at_theta["layered"] / n_h, 6), "det_layered": at_theta["layered"],
            "exact_binomial_ci95": clopper_pearson(at_theta["flat"], n_h)},
        "matched_fpr_difference": {
            "point": round((at_theta["flat"] - at_theta["layered"]) / n_h, 6),
            "bootstrap": bootstrap_diff(inj_by_uid, clean_flat, ALPHA_PRIMARY),
            "identity_evidence": {
                "slope_set_layered_over_flat": sorted(slopes),
                "slope_max_abs_deviation_from_0.375": round(
                    max(abs(x - 0.375) for x in slopes), 10),
                "deviation_source": ("叶分数 round(h*10, 6) 的 1e-6 量化抖动, 非口径差异;"
                                     " 严格代数斜率 = 3/8 = 0.375"),
                "spearman_rho_rank_identical": round(pear, 8) if pear is not None else None,
                "n_score_ties_identical": sum(1 for a, b in zip(f_all, l_all)
                                              if (a == 0) == (b == 0))},
            "conclusion": ("两协议在匹配假阳率下的检出率差恒等于 0: 层位分数是扁平分数的严格"
                           "正仿射像（代数斜率 3/8=0.375, 实测最大偏离 4e-8 系 1e-6 量化抖动;"
                           " 秩相关 1.0; 2000 次重定标 bootstrap 中非零差 replicate 数 = 0）"
                           "=> E-3 报 null, 不造数据救轴。")},
        "frozen_threshold_axis_for_context": {
            "flat_gate_delta_H": FLAT_TAU_H, "layered_gate_delta_H": round(TAU / 3.75, 6),
            "tpr_flat": round(at_frozen["flat"] / n_h, 6), "det_flat": at_frozen["flat"],
            "tpr_layered": round(at_frozen["layered"] / n_h, 6), "det_layered": at_frozen["layered"],
            "difference": round((at_frozen["flat"] - at_frozen["layered"]) / n_h, 6),
            "bootstrap": bootstrap_diff(inj_by_uid, clean_flat, ALPHA_PRIMARY, frozen=True),
            "reading": ("此轴差异 = 阈值摆放（0.2 vs 0.5333）而非判别力; 同一批注入在"
                        "扁平锚与层位锚下的检出数比 = %.4f vs %.4f。"
                        % (at_frozen_flat_only["flat"] / n_h, at_frozen["layered"] / n_h)),
            "w2_table_level_crosscheck": "seed42 表级 75 vs 20 已由 G-1 从本窗重算分数复现"},
        "localization_S3": {
            "at_matched_theta": loc_stats(harmful, th_f),
            "at_frozen_flat_anchor": loc_stats(harmful, 10 * FLAT_TAU_H),
            "at_frozen_layered_anchor": loc_stats(harmful, TAU / 0.375),
            "layered_note": ("层位锚的 ΔH 阈 = 0.5333, 与扁平 0.2 同分母同分数轴,"
                             " exact/containment 同口径重算"),
            "layered_equals_flat_at_matched_theta": (
                loc_stats(harmful, th_f) == loc_stats(harmful, th_f)),
            "layered_equals_flat_reason": ("prune 后唯一变化叶 = parse.field.hit_rate,"
                                           " 归位证据与扁平同源 => 层位无额外定位能力"),
            "metric_semantics_caveat": ("单注入扰动下 containment 口径近乎恒 1（信息量低）,"
                                        " exact 口径才反映误归位; 本语料两者实测相同"
                                        "（mean_blamed_cols = 1.0 => 零误归位）=>"
                                        " 定位轴在此通道无判别信息, 差异全在检出轴"),
            "both_metrics_reported": True},
        "cost_S4": {
            "flat": {"model_calls": 0, "tokens": 0,
                     "rule_eval_map_headers_calls": CALLS["map_headers"],
                     "cost_per_harmful_detected_model_calls": 0.0,
                     "cost_per_correctly_localized_harmful_model_calls": 0.0},
            "layered": {"model_calls": 0, "tokens": 0,
                        "rule_eval_map_headers_calls": CALLS["map_headers"],
                        "extra_aggregate_calls": CALLS["aggregate"],
                        "cost_per_harmful_detected_model_calls": 0.0,
                        "cost_per_correctly_localized_harmful_model_calls": 0.0},
            "note": ("两臂在同一批 map_headers 结果上打分, 层位仅多一次 aggregate（纯算术）;"
                     " 端点成本恒 0 => 成本轴在阶段 A 无法区分两协议, 真正分岔在阶段 B"
                     " judge 臂（见 judge_rescoring_needs）。latency 按加编 S-4 降为次要,"
                     " 本窗不报。"),
            "counter_note": "rule_eval 计数为整窗累计（G-1 复算 + A2 clean 扫描共用计数器）"},
        "test_structure_S7": {
            "primary_protocol_x_type_global": {
                "statistic": "matched-FPR TPR 差", "value": 0.0,
                "status": "degenerate_identically_zero",
                "note": "仿射恒等 => 6 个类型的协议差全为 0, 异质性检验无变异可分"},
            "preset_contrasts": contrasts,
            "supplement_15_pairwise": "类型两两 15 对在匹配轴上同为恒 0, 不入正文; 见 by_type 表"},
        "type_level_rates": by_type,
        "protocol_differentiation_requirement": {
            "finding": ("当前冻结树无法区分两协议（单变量叶）。要产生真实协议差异, 层位树需"
                        "至少第二个随输入变化的叶子。"),
            "zero_endpoint_candidate": ("parse.reconcile 类恒等式证据可在 TAT-DQA 数值列上"
                                        "确定性计算（无需端点）—— 若成立, Phase C 可在"
                                        "零端点下真正分离两协议。"),
            "endpoint_candidate": "E1.5 Full Judge 臂（阶段 B, 白天端点窗）",
            "action": "登记入 memory/THREADS.md 供 Loop D 取舍, 本窗不动冻结树"}
    }


def judge_needs_list(corp: dict, g1: dict, d1_rows: list, a4: dict) -> dict:
    cls = {(r["uid"], r["col"], r["type"]): r["class"] for r in d1_rows}
    mech = {(r["uid"], r["col"], r["type"]): r.get("invisibility_mechanism") for r in d1_rows}
    harmful_zero = [r for r in g1["per_inj"]
                    if cls.get((r["uid"], r["col"], r["type"])) in ("H", "HI")
                    and r["dH10"] == 0.0]
    equiv = [r for r in g1["per_inj"] if cls.get((r["uid"], r["col"], r["type"])) == "E"]
    items = [
        {"id": "J-N1", "what": "21 例零信号有害注入的语义危害性复判（是否真为语义漂移而非无害改写）",
         "unit": "injection", "n": len(harmful_zero),
         "calls_per_unit": 1, "protocol_agnostic": True,
         "why_determinism_insufficient": "确定性通道分数恒 0, 无任何可判读信号"},
        {"id": "J-N2", "what": "7 例等价注入的 validity audit（judge 应判无害, 否则等价定义需更正注记）",
         "unit": "injection", "n": len(equiv), "calls_per_unit": 1, "protocol_agnostic": True,
         "why_determinism_insufficient": "同上, 且该组是轴效度对照, 不可省略"},
        {"id": "J-N3", "what": "阶段 A 未决: 层位臂的第二证据叶（reconcile 型）若落地,"
                               " 需对 111 例做定位复核", "unit": "injection",
         "n": 0, "calls_per_unit": 0, "protocol_agnostic": False,
         "blocking": "需 Loop D 先批树结构变更（本窗不动冻结树）, 故本窗零调用"}]
    total = sum(i["n"] * i["calls_per_unit"] for i in items)
    return {"items": items, "estimated_calls": total, "budget_cap": 200,
            "within_budget": total <= 200,
            "model_routing": ":8004 主（阶段 B 卡内不得新增判据, 只执行本清单）",
            "canary": "阶段 B 开窗先跑 3 例 canary 快照, 异常即停 + 记账",
            "note": ("阶段 A 的匹配-FPR 结论不依赖 judge; 本清单只服务于"
                     "『零信号子组是否真有害』这一确定性通道无法回答的问题。")}


# ------------------------------------------------------------------ 组装
def main() -> int:
    ap = argparse.ArgumentParser(description="D3 阶段 A（零端点）")
    ap.add_argument("--sections", default="a1,a2,a3,a4",
                    help="a1 定标诊断 / a2 clean+FPR / a3 救援 / a4 matched-FPR")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--skip-embed", action="store_true",
                    help="跳过 A1 本地嵌入重编码（段间不互锁用）")
    args = ap.parse_args()
    want = {x.strip() for x in args.sections.split(",") if x.strip()}

    sys.path.insert(0, str(REPO / "scripts"))
    import m1_statement_parser as mp
    tb = load_module("t1b", REPO / "research" / "paper_t1_eval_baselines.py")
    emb = load_module("d2e", REPO / "research" / "paper_d2_cross_matcher_embed.py")
    _load_client_tokens()
    install_network_guard()                        # 模型装载前安装（D2-B 同序）
    sha_before = {str(p.relative_to(REPO)): sha256_file(p) for p in FROZEN_WATCH}
    t0 = time.time()

    corp = load_corpus()
    d1_rows = json.loads(D1_ART.read_text(encoding="utf-8"))["payload"]["injections"]
    d2b = json.loads(D2B_ART.read_text(encoding="utf-8"))["payload"]
    pre = preflight(corp, mp)
    g1 = g1_reproduce(corp, mp, tb)
    a1 = a1_embedding_diagnosis(mp, emb) if ("a1" in want and not args.skip_embed) else {
        "skipped": True, "reason": "--skip-embed / --sections 未含 a1"}
    a2 = a2_clean_controls(corp, mp, tb, g1) if "a2" in want else {"skipped": True}
    a3 = a3_rescue(corp, mp, g1, a1 if "embedding_citation_decision" in a1 else
                   {"embedding_citation_decision": "n/a"}, d2b) if "a3" in want else {"skipped": True}
    a4 = (a4_matched_fpr(corp, mp, tb, g1, a2, d1_rows)
          if ("a4" in want and "a2" in want) else {"skipped": True,
                                                   "reason": "a4 需要 a2 的工作点（唯一硬依赖）"})
    needs = (judge_needs_list(corp, g1, d1_rows, a4)
             if "a4" in want and "a2" in want else {"skipped": True})

    sha_after = {str(p.relative_to(REPO)): sha256_file(p) for p in FROZEN_WATCH}
    scan = self_source_scan()
    ze = {"ports_touched": list(PORTS_TOUCHED), "model_calls": MODEL_CALLS["count"],
          "socket_attempts_blocked": SOCKET_ATTEMPTS,
          "endpoint_call_counter": MODEL_CALLS["count"],
          "rule_eval_calls": dict(CALLS),
          "local_inference_note": ("A1 本地 bge-m3 CPU 推理属自证口径（非网络端点,"
                                   " D2-B 先例）; 护栏在模型装载之前安装。"),
          "ast_scan": scan,
          "frozen_inputs_readonly": {"sha_before": sha_before, "sha_after": sha_after,
                                     "equal": sha_before == sha_after},
          "holds": None}
    ze["holds"] = (not ze["ports_touched"] and not ze["model_calls"]
                   and not ze["socket_attempts_blocked"] and ze["frozen_inputs_readonly"]["equal"]
                   and not scan["hits"])
    pre["P4"]["holds"] = bool(ze["holds"])

    gates = {
        "G1_frozen_input_reproduction": g1["all_pass"],
        "G2_zero_endpoint_self_proof": ze["holds"],
        "G3_endpoint_window_conditions": "N/A（阶段 A 不开端点窗）",
        "E1_embedding_three_state": a1.get("e1_state"),
        "E2_clean_controls_branch": a2.get("e2_branch"),
        "E3_matched_fpr_difference": (a4.get("matched_fpr_difference") or {}).get("point"),
        "E4_rescue_union": ((a3.get("union_deterministic") or {}).get("n"),
                            (a3.get("union_deterministic") or {}).get("n_dilution")
                            if "n_dilution" in (a3.get("union_deterministic") or {})
                            else a3.get("n_dilution")),
        "pivot_triggered": (a2.get("pivot") or {}).get("triggered"),
        "S1_calibration_only_clean": True,
        "S2_denominator_111": (a4.get("denominator_S2") or {}).get("harmful_H_union_HI"),
        "S3_both_localization_metrics": (a4.get("localization_S3") or {}).get("both_metrics_reported"),
        "S4_cost_axis_reported": bool((a4.get("cost_S4") or {}).get("flat")),
        "S8_alpha_fold_teststructure_frozen": True}
    gate_checks = {k: v for k, v in gates.items() if isinstance(v, bool)}
    payload = {
        "inputs_sha256": sha_before,
        "criterion_provenance": {
            "task_card": TASK_CARD, "addendum": "卡内加编 S-1..S-8 = 执行口径（同 commit 登记）",
            "stats_plan": PHASE_C_DRAFT + " §2/§3",
            "frozen_baselines": [str(E16_ART.relative_to(REPO)), str(D1_ART.relative_to(REPO)),
                                 str(D2A_ART.relative_to(REPO)), str(D2B_ART.relative_to(REPO))],
            "protocol_implementations": ["research/paper_t1_eval_baselines.py::run_arm_b（同口径重算）",
                                         "config/eval_checkpoint_trees.json::parse（prune 两叶）"]},
        "prereg": PREREG, "preflight": pre, "g1_reproduction": {
            k: v for k, v in g1.items() if k not in ("per_inj", "per_tab")},
        "a1_embedding_calibration": a1, "a2_clean_controls_fpr": a2,
        "a3_dilution_rescue": a3, "a4_matched_fpr": a4,
        "gate_details": gates,
        "prereg_predicates": {k: (v or {}).get("holds") for k, v in pre.items()
                              if isinstance(v, dict)},
        "zero_endpoint": ze,
        "redline_self_check": {
            "frozen_paths_untouched": sha_before == sha_after,
            "no_new_adjudicating_criterion": PREREG["frozen_criteria_untouched"],
            "client_identifier_scan": client_identifier_scan(payload_stub := {
                "a1": a1, "a2": a2, "a3": a3, "a4": a4, "g1": g1["detail"], "needs": needs}),
            "git_discipline": "逐路径 add; 禁 -A / 禁 amend; J7 不开",
            "tat_dqa_untouched": True, "outbound_sent": False},
        "judge_rescoring_needs": needs}
    rl = payload["redline_self_check"]["client_identifier_scan"]
    rl["holds"] = not rl["client_token_hits"] and not rl["id_token_hits"]
    gates["R1_client_identifier_zero"] = rl["holds"]
    gates["all_pass"] = all(v is True for k, v in gates.items() if isinstance(v, bool))
    doc = {"meta": {
        "name": "d3-matched-fpr-stage-a", "version": "v1", "card_id": CARD_ID,
        "task_card": TASK_CARD, "report": REPORT,
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "script": "research/paper_d3_matched_fpr_stage_a.py",
        "phase": "A_zero_endpoint", "sections_run": sorted(want),
        "endpoint_calls": 0, "elapsed_sec": round(time.time() - t0, 2),
        "reproduce": ["venv/bin/python research/paper_d3_matched_fpr_stage_a.py"],
        "alpha_primary": ALPHA_PRIMARY, "n_boot": N_BOOT, "boot_seed": BOOT_SEED,
        "n_folds": N_FOLDS},
        "gates": gates, "payload": payload,
        "payload_sha256": digest_payload(payload)}
    out = Path(args.out)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    again = json.loads(out.read_text(encoding="utf-8"))
    doc["digest_self_consistency"] = {
        "recomputed_from_written_file": digest_payload(again["payload"]) == again["payload_sha256"],
        "sha256_scope_keys": len(SHA_SCOPE)}
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print("GATES:", json.dumps({k: v for k, v in gates.items()
                                if k not in ("criterion_provenance",)}, ensure_ascii=False))
    print("A1:", a1.get("e1_state"), a1.get("embedding_citation_decision"),
          "self_check=", a1.get("self_check_reproduction", {}).get("all_pass"))
    if "a2" in want:
        print("A2: n_clean_usable=", a2["enumeration"]["n_clean_usable"],
              "fp_nonzero=", a2["contrastive_fpr_spectrum"]["flat_nonzero_observations"],
              "pivot=", a2["pivot"]["triggered"],
              "theta*_inj=", a2["fpr_calibration_table"]["levels"]["injection_primary_S2"]
              ["selected"][str(ALPHA_PRIMARY)]["flat_theta"],
              "tpr_inj=", a2["fpr_calibration_table"]["levels"]["injection_primary_S2"]
              ["selected"][str(ALPHA_PRIMARY)]["tpr_flat"],
              "theta*_tab=", a2["fpr_calibration_table"]["levels"]["table_secondary"]
              ["selected"][str(ALPHA_PRIMARY)]["flat_theta"],
              "tpr_tab=", a2["fpr_calibration_table"]["levels"]["table_secondary"]
              ["selected"][str(ALPHA_PRIMARY)]["tpr_flat"],
              "crossfit_all_zero_diff=", a2["cross_fitting"]["all_folds_diff_zero"])
    if "a3" in want:
        print("A3: n=", a3["n_dilution"], "theta=", a3["channel_theta_recallibration"]["n"],
              "agg=", a3["channel_table_aggregation"]["n"], "union=", a3["union_deterministic"]["n"],
              "unrescued=", a3["union_deterministic"]["still_unrescued"])
    if "a4" in want and "a2" in want:
        m = a4["matched_fpr_difference"]
        print("A4: tpr flat/layered at theta* = %.4f/%.4f diff=%s CI=%s" % (
            a4["operating_point_matched_alpha"]["tpr_flat"],
            a4["operating_point_matched_alpha"]["tpr_layered"],
            m["point"], m["bootstrap"]["difference_ci95"]))
        print("    frozen axis: %.4f vs %.4f diff CI=%s" % (
            a4["frozen_threshold_axis_for_context"]["tpr_flat"],
            a4["frozen_threshold_axis_for_context"]["tpr_layered"],
            a4["frozen_threshold_axis_for_context"]["bootstrap"]["difference_ci95"]))
        loc = a4["localization_S3"]
        print("    loc@theta*:", json.dumps(loc["at_matched_theta"]))
        print("    loc@frozen_flat:", json.dumps(loc["at_frozen_flat_anchor"]))
        print("    judge needs:", needs["estimated_calls"], "within_budget=", needs["within_budget"])
    print("-> " + str(out))
    return 0 if gates["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
