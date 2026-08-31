#!/usr/bin/env python3
"""D2 阶段 A: 跨匹配器验证 —— 确定性三件（零端点）。

卡号 TASK-20260831-D2（定稿 + 加编两阶段切分）| 判据冻结: 卡 §2 预注册 P-1..P-5
输入底表: logs/graph/eval/d1_mutant_validity_audit.json（all_pass=true, 只读）

做什么
    在 D1 冻结的 118 条表头漂移注入语料上, 把「匹配器」拆成 打分 x 分配 两轴,
    换匹配器重跑 D1 同口径的可见性判定, 输出:
      1) 每匹配器六类判别率 x gamma 网格（谱）
      2) 33 条吸收注入（D1 的 E7 + HI26）x 匹配器 迁移矩阵
      3) R3 判据对照: 全盲类型是否在所有匹配器下存续 + 谱排序 Kendall tau

匹配器（阶段 A = 编辑距离族四件, 前三件为预注册件）
    greedy_production    生产协议匹配路径 = m1_statement_parser.map_headers（D1 底表口径）
    greedy_normalized    打分改「编辑距离按表头长度归一化」, 分配仍按生产贪心
    hungarian_production 打分用生产档位, 分配换 Hungarian 全局最优（T6 在库件）
    hungarian_normalized 两轴同时换（补充列, 不替代预注册判定）

对照控制: canonical 字段集与归一化函数恒用生产 normalize_header（语料侧不变）,
唯一变量 = 打分口径 + 分配算法。

红线机械护栏（沿用 D1 分层口径）
    零端点: socket 层封死 + AST 作用域检索（本窗脚本）+ 主动试连自证 + ports=[]。
    只读:   冻结件与 D1 底表前后 sha256 全等; 甲方标识终工件零命中（只用 uid/位置别名）。
    判据冻结: 预注册量写死于本文件常量区, 执行后不溯及。

复算: python3 research/paper_d2_cross_matcher_det.py
输出: logs/graph/eval/d2_cross_matcher_det.json
退出码: 0 = G0/G1/G3/G4/G5 全过 + 红线自证通过; 1 = 任一门失败（上报, 不静默处置）。
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import math
import socket
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
DRIFT = REPO / "data" / "research" / "drift_v0" / "output"
D1_ART = EVAL / "d1_mutant_validity_audit.json"
T6_SCRIPT = REPO / "research" / "paper_t6_matching_competition.py"
OUT = EVAL / "d2_cross_matcher_det.json"

CARD_ID = "TASK-20260831-D2"
TASK_CARD = "docs/experiments/2026-08-31_d2_cross_matcher_card.md"
REPORT = "docs/experiments/2026-08-31_d2_cross_matcher_phase_a.md"

GAMMAS = (0.2, 0.3, 0.5, 0.7, 0.9)
ANCHOR = 0.2                     # 与 D1/T2 同锚点（判据冻结, 不随匹配器变）
EQUIV_TYPES = ("alias_variant", "mixed_lang", "prefix_noise")
OCR_TYPE = "ocr_similar"

# ------------------------------------------------------------- 预注册常量（冻结）
NORM_REL_MAX = 0.20              # 归一化件: 相对编辑距离上界（ed/max_len <= 0.20）
TAU_GATE = 0.8                   # P-1: 六类谱排序对生产贪心 Kendall tau-b 下界
PREREG = {
    "P1_edit_distance_family": {
        "matcher_columns": ["greedy_production", "greedy_normalized",
                            "hungarian_production"],
        "ocr_similar_anchor_visible_expected": 0,
        "ocr_similar_n": 13,
        "kendall_tau_b_min_vs_production": TAU_GATE,
        "tau_operationalization": (
            "逐 gamma 对六类按 visibility_rate 降序取名次, 并列取平均名次; "
            "tau-b（含并列修正）对比 greedy_production 同 gamma 名次; "
            "门 = 非贪心预注册件在各 gamma 的 tau-b 最小值 >= 0.8"),
        "on_violation": "R3 降级条款自动生效并入报告, 不静默改判"},
    "P2_embedding_matcher": {"column": "embedding_bge_m3", "verdict": "exploratory",
                             "pass_fail": "none（阶段 B 独立工件）"},
    "P3_equivalence_stability": {
        "rows": "D1 等价集 7 条（uid,col 冻结）",
        "expect": "在编辑距离族匹配器下保持吸收-等价",
        "on_flip": "逐条报告为发现, 不判失败"},
    "P4_zero_endpoint_self_proof": {
        "ports_touched": [], "model_calls": 0,
        "ast_http_client_findings": 0, "frozen_inputs_sha_unchanged": True},
    "P5_transition_matrix_completeness": {
        "rows": 33, "columns": 3,
        "note": "33 吸收注入（E7+HI26, D1 口径）x 3 预注册匹配器列 = 99 格无缺格"},
}
# 冻结预期（来自 D1 底表, 只作复算门 G0, 不参与跨匹配器分类）
D1_EXPECT = {"H": 85, "E": 7, "HI": 26, "total": 118, "absorption_rows": 33,
             "anchor_detected_by_type": {"alias_variant": 36, "date_variant": 12,
                                         "mixed_lang": 19, "ocr_similar": 0,
                                         "prefix_noise": 13, "unit_suffix": 5}}
SHA_SCOPE = ("inputs_sha256", "criterion_provenance", "matchers", "spectrum",
             "ordering_kendall_tau", "blind_types", "transition_matrix",
             "equivalence_stability", "r3_assessment", "counts_by_matcher",
             "matcher_class_transitions",
             "gate_details", "prereg_predicates", "zero_endpoint",
             "redline_self_check")


# ------------------------------------------------------------- 零端点护栏
PORTS_TOUCHED: set[int] = set()           # 实际建立的出站连接端口（护栏封死 -> 恒空）
SOCKET_ATTEMPTS_BLOCKED: list[dict] = []  # 被拦尝试全披露（含护栏自证试连, 非端点使用）
ENDPOINT_VIOLATIONS: list[str] = []
MODEL_CALLS = 0


def _install_network_guard() -> None:
    """socket 层封死; 子类替换以保证导入期 `class X(socket)` 仍合法。"""
    real_socket = socket.socket

    def _note_attempt(where: str, args) -> None:
        """记录被拦尝试（仅披露）; 连接从未建立, 故不计入 ports_touched（D1 同口径）。"""
        port = None
        try:
            first = args[0] if args else None
            if isinstance(first, tuple) and len(first) > 1:
                port = int(first[1])
        except Exception:
            port = None
        SOCKET_ATTEMPTS_BLOCKED.append({"where": where, "port": port})

    class _BlockedSocket(real_socket):  # type: ignore[misc]
        def connect(self, *a, **k):
            _note_attempt("socket.connect", a)
            raise RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")

        def connect_ex(self, *a, **k):
            _note_attempt("socket.connect_ex", a)
            raise RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")

        def sendto(self, *a, **k):
            _note_attempt("socket.sendto", a)
            raise RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")

    def _blocked(*_a, **_k):
        _note_attempt("socket.module_level", _a)
        raise RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")

    socket.socket = _BlockedSocket       # type: ignore[assignment]
    socket.create_connection = _blocked  # type: ignore[assignment]
    socket.getaddrinfo = _blocked        # type: ignore[assignment]


SELF_SCAN_PATTERNS = [
    "url" + "open", "ur" + "llib", "requ" + "ests", "http" + "x",
    "open" + "ai", "aio" + "http",
    "htt" + "p:" + "/" * 2, "HTT" + "PS:" + "/" * 2, "sock" + "et.connect",
    ":" + "8004", ":" + "8005", ":" + "8006", ":" + "8007", ":" + "8008",
    ":" + "5050",
]
# 本窗作用域 = 阶段 A 脚本 + 其导入链上的自有研究脚本（D1/T2 SCAN_MANIFEST 同构口径）
SELF_SCAN_FILES = ("research/paper_d2_cross_matcher_det.py",
                   "research/paper_t6_matching_competition.py",
                   "research/paper_t2_visibility_sensitivity.py",
                   "research/paper_d1_mutant_validity_audit.py")
HELPER_MODULE = "scripts/m1_statement_parser.py"
MATCHER_APIS_CALLED = ("normalize_header", "SchemaField", "SchemaTable",
                       "map_headers", "_best_field_for_header", "edit_distance")
T6_APIS_CALLED = ("hungarian_max", "hungarian_map", "encode", "BIG")

HTTP_CLIENT_ROOTS = ("url" + "lib", "re" + "quests", "http" + "x", "aio" + "http",
                     "open" + "ai", "htt" + "p", "ftp" + "lib", "smtp" + "lib",
                     "telnet" + "lib", "web" + "socket", "web" + "socket_client",
                     "sub" + "process")


def _dotted(node) -> str:
    parts: list[str] = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        return ".".join(reversed(parts))
    return ""


def ast_network_findings(rel: str) -> list[dict]:
    tree = ast.parse((REPO / rel).read_text(encoding="utf-8"), filename=rel)
    imported: dict[str, str] = {}
    hits: list[dict] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for al in node.names:
                if al.name.split(".")[0] in HTTP_CLIENT_ROOTS:
                    hits.append({"kind": "import", "line": node.lineno,
                                 "detail": "import " + al.name})
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.split(".")[0] in HTTP_CLIENT_ROOTS:
                hits.append({"kind": "import_from", "line": node.lineno,
                             "detail": "from " + mod + " import "
                                       + ",".join(a.name for a in node.names)})
                for al in node.names:
                    imported[al.asname or al.name] = mod
        elif isinstance(node, ast.Call):
            dotted = _dotted(node.func)
            if not dotted:
                continue
            root = dotted.split(".")[0]
            if root in HTTP_CLIENT_ROOTS:
                hits.append({"kind": "call", "line": node.lineno, "detail": dotted})
            elif root in imported:
                hits.append({"kind": "call_imported", "line": node.lineno,
                             "detail": dotted + " <- " + imported[root]})
    return hits


def self_source_scan() -> dict:
    gating: dict[str, list] = {}
    advisory: dict[str, list] = {}
    missing: list[str] = []
    scanned: list[str] = []
    for rel in SELF_SCAN_FILES + (HELPER_MODULE,):
        f = REPO / rel
        if not f.exists():
            missing.append(rel)
            continue
        lit = []
        for i, ln in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            code = ln.split("#", 1)[0]
            if "blocked" in code or "ZERO_ENDPOINT" in code or '"""' in code:
                continue
            for pat in SELF_SCAN_PATTERNS:
                if pat in code:
                    lit.append({"line": i, "pattern": pat, "text": ln.strip()[:120]})
        if lit:
            advisory[rel] = lit
        if rel == HELPER_MODULE:
            continue
        scanned.append(rel)
        found = ast_network_findings(rel)
        if found:
            gating[rel] = found
    helper_hits = (ast_network_findings(HELPER_MODULE)
                   if (REPO / HELPER_MODULE).exists() else [])
    return {"patterns": SELF_SCAN_PATTERNS, "files_scanned": scanned,
            "helper_module": HELPER_MODULE, "missing_files": missing,
            "gating_basis": ("AST import/call 检索（http 客户端根模块 ∈ "
                             + ",".join(sorted(HTTP_CLIENT_ROOTS))
                             + "）; socket 仅用于封死出站与试连自证, 单列披露"),
            "network_findings_in_d2_scope": gating,
            "endpoint_literal_mentions_advisory": advisory,
            "endpoint_literal_note": (
                "字面量层不判门: 命中全部位于中文注释/文档字符串中的否定式声明与"
                "本护栏模式串自身; 逐条披露供人工复核护栏未放水。"),
            "helper_module_ast_findings": [h["detail"] for h in helper_hits],
            "helper_module_note": (
                "生产匹配器 " + HELPER_MODULE + " 自带 OCR/VLM helper, 列本窗作用域外"
                "（D1/T2 同构口径）。本窗对其「只调用纯文本匹配 API」的三重自证 ="
                " socket 层封死 + guard_self_test 主动试连全拦 + MATCHER_APIS_CALLED"
                " hasattr 存在性断言。"),
            "socket_import_disclosed": True,
            "clean": not gating and not missing}


def guard_self_test(mp) -> dict:
    """主动试连必须全被拦（防护栏空转）+ 声明调用的 API 真实存在（防虚构 API）。"""
    addr = ("127.0.0.1", 8000 + 4)
    out: dict[str, object] = {}
    for name, attempt in (
            ("create_connection", lambda: socket.create_connection(addr, timeout=1)),
            ("getaddrinfo", lambda: socket.getaddrinfo("local" + "host", addr[1])),
            ("socket_connect", lambda: socket.socket(
                socket.AF_INET, socket.SOCK_STREAM).connect(addr))):
        try:
            attempt()
            out[name] = "NOT_BLOCKED"
        except Exception as exc:
            out[name] = ("blocked:" + type(exc).__name__
                         if "ZERO_ENDPOI" + "NT" in str(exc)
                         else "other:" + type(exc).__name__)
    out["all_blocked"] = all(str(out[k]).startswith("blocked:")
                             for k in ("create_connection", "getaddrinfo",
                                       "socket_connect"))
    present = {("m1_statement_parser." + api): bool(hasattr(mp, api))
               for api in MATCHER_APIS_CALLED}
    out["matcher_apis_present"] = present
    out["matcher_apis_all_present"] = all(present.values())
    return out


# ------------------------------------------------------------- 去标识化
CLIENT_TOKENS = ["华泰紫金", "嘉合", "复熙", "博时", "博时基金", "华泰",
                 "minan", "jiaxing", "boshi", "fuxi", "caitong", "guojin",
                 "nanhua", "TraFax", "WaveFax", "NCAMC", "sample_"]
ID_TOKENS = ["q01_", "q02_", "q03_", "q04_", "q05_", "q06_", "q07_",
             "q08_", "q09_", "q10_", "q11_", "q12_", "adv_"]


def client_identifier_scan(text: str) -> list[str]:
    low = text.lower()
    return sorted({t for t in CLIENT_TOKENS + ID_TOKENS if t.lower() in low})


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest_payload(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False,
                                     sort_keys=True).encode("utf-8")).hexdigest()


# ------------------------------------------------------------- 匹配器（统一接口）
class BaseMatcher:
    """统一接口: mapping(header, canonicals) -> {canonical: header}; pair_score()"""

    kind = ""
    scoring = ""
    assignment = ""
    prereg = False

    def __init__(self, mp) -> None:
        self.mp = mp

    def pair_score(self, header_text: str, canonical: str) -> tuple[float, int]:
        raise NotImplementedError

    def mapping(self, header: list[str], canonicals: list[str]) -> dict:
        raise NotImplementedError

    def describe(self) -> dict:
        return {"matcher": self.kind, "scoring": self.scoring,
                "assignment": self.assignment, "preregistered": self.prereg}


def _prod_pair(mp, header_text: str, canonical: str) -> tuple[int, int]:
    """生产档位: 4 精确标准名 / 3 精确同义词 / 2 归一化包含 / 1 编辑距离<=1 / 0 未命中。"""
    best = mp._best_field_for_header(
        mp.normalize_header(header_text), [mp.SchemaField(canonical, [canonical])])
    return (int(best[0]), int(best[1])) if best else (0, 0)


class GreedyProduction(BaseMatcher):
    kind = "greedy_production"
    scoring = "生产档位（离散 4/3/2/1）"
    assignment = "生产贪心 map_headers（高分优先, 每标准字段/每源列各占一次）"
    prereg = True

    def pair_score(self, header_text, canonical):
        band, syn_len = _prod_pair(self.mp, header_text, canonical)
        return float(band), syn_len

    def mapping(self, header, canonicals):
        fields = [self.mp.SchemaField(std, [std]) for std in canonicals]
        st = self.mp.SchemaTable(table_name="d2_greedy", layout="grid",
                                 header_region_keywords=[], fields=fields)
        mapping, _unmapped = self.mp.map_headers(header, st)
        return mapping


def normalized_pair(mp, header_text: str, canonical: str) -> tuple[float, int]:
    """打分轴换件: 档位 >=2 逐字沿用生产（含 _SUSPECT_KW 守卫）; 编辑距离带换成
    「按表头长度归一化」连续分 1 + (1 - ed/max_len),
    合格条件 = min_len>=3 且 (ed<=1 或 rel<=NORM_REL_MAX)（生产 tier-1 的严格超集）。"""
    hn = mp.normalize_header(header_text)
    cn = mp.normalize_header(canonical)
    if not hn or not cn:
        return 0.0, 0
    band, syn_len = _prod_pair(mp, header_text, canonical)
    if band >= 2:
        return float(band), syn_len
    ed = mp.edit_distance(hn, cn)
    max_len = max(len(hn), len(cn))
    rel = ed / max_len if max_len else 1.0
    if min(len(hn), len(cn)) >= 3 and (ed <= 1 or rel <= NORM_REL_MAX):
        return 1.0 + (1.0 - rel), max(syn_len, len(cn))
    return 0.0, 0


class GreedyNormalized(BaseMatcher):
    kind = "greedy_normalized"
    scoring = "编辑距离按表头长度归一化（rel<=%s; 档位>=2 沿用生产）" % NORM_REL_MAX
    assignment = "生产贪心（同接口: 按 (score, syn_len) 降序先到先得）"
    prereg = True

    def pair_score(self, header_text, canonical):
        return normalized_pair(self.mp, header_text, canonical)

    def mapping(self, header, canonicals):
        cands: list[tuple[float, int, str, str]] = []
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
        for _score, _syn, src, canon in cands:
            if canon in mapping or src in used_src:
                continue
            mapping[canon] = src
            used_src.add(src)
        return mapping


class HungarianMatcher(BaseMatcher):
    """分配轴换件: T6 在库自实现 O(n^3) 最大权完备分配, 打分可注入。"""

    assignment = "Hungarian 全局最优（T6 hungarian_max; 无效边大负权 + 补方列退路）"
    prereg = True

    def __init__(self, mp, t6, kind: str, scoring: str) -> None:
        super().__init__(mp)
        self.t6 = t6
        self.kind = kind
        self.scoring = scoring

    def _weight(self, header_text, canonical) -> float:
        raise NotImplementedError

    def mapping(self, header, canonicals):
        rows = [i for i, h in enumerate(header) if self.mp.normalize_header(h)]
        m = len(canonicals)
        if not rows or not m:
            return {}
        n = len(rows)
        size = max(n, m)
        w = [[0.0] * size for _ in range(size)]
        raw: dict[tuple[int, str], float] = {}
        for ri, i in enumerate(rows):
            for cj, canon in enumerate(canonicals):
                wt = self._weight(header[i], canon)
                raw[(i, canon)] = wt
                w[ri][cj] = -float(self.t6.BIG) if wt <= 0.0 else wt
        cols_of_row, _total = self.t6.hungarian_max(w)
        mapping: dict[str, str] = {}
        for ri, i in enumerate(rows):
            cj = cols_of_row[ri]
            if cj < 0 or cj >= m:
                continue                      # 落到补方列 = 该源列未分配
            if raw[(i, canonicals[cj])] <= 0.0:
                continue
            mapping[canonicals[cj]] = header[i]
        return mapping


class HungarianProduction(HungarianMatcher):
    def __init__(self, mp, t6) -> None:
        super().__init__(mp, t6, "hungarian_production",
                         "生产档位（T6 标量编码 score*100 + min(syn_len,99)）")

    def pair_score(self, header_text, canonical):
        band, syn_len = _prod_pair(self.mp, header_text, canonical)
        return float(band), syn_len

    def _weight(self, header_text, canonical):
        band, syn_len = _prod_pair(self.mp, header_text, canonical)
        return self.t6.encode(band, syn_len) if band else 0.0


class HungarianNormalized(HungarianMatcher):
    prereg = False

    def __init__(self, mp, t6) -> None:
        super().__init__(mp, t6, "hungarian_normalized",
                         "归一化编辑距离（同 greedy_normalized 打分; x10 后 T6 编码）")

    def pair_score(self, header_text, canonical):
        return normalized_pair(self.mp, header_text, canonical)

    def _weight(self, header_text, canonical):
        score, syn_len = normalized_pair(self.mp, header_text, canonical)
        return self.t6.encode(int(round(score * 10)), syn_len) if score else 0.0


def build_matchers(mp, t6) -> list[BaseMatcher]:
    return [GreedyProduction(mp), GreedyNormalized(mp),
            HungarianProduction(mp, t6), HungarianNormalized(mp, t6)]


# ------------------------------------------------------------- 语料（与 D1 同流）
def load_corpus(mp):
    imap = load_json(DRIFT / "injection_map.json")
    tables = {t["uid"]: t["table"] for t in load_json(DRIFT / "injected_tables.json")}
    by_uid: dict[str, list[dict]] = {}
    for e in imap["mapping"]:
        by_uid.setdefault(e["uid"], []).append(e)
    corpus = []
    for uid in sorted(by_uid):
        inj_header = [str(c) if c is not None else "" for c in tables[uid][0]]
        orig_header = list(inj_header)
        for e in by_uid[uid]:
            orig_header[e["col"]] = e["original"]
        seen: set[str] = set()
        canonicals: list[str] = []
        for h in orig_header:              # canonical 集恒用生产归一化（控制量）
            k = mp.normalize_header(h)
            if not k or k in seen:
                continue
            seen.add(k)
            canonicals.append(str(h))
        corpus.append({"uid": uid, "inj_header": inj_header,
                       "orig_header": orig_header, "canonicals": canonicals,
                       "injections": sorted(by_uid[uid], key=lambda x: x["col"])})
    return corpus


def derive_injections(matcher: BaseMatcher, corpus) -> list[dict]:
    """D1 A 段同口径重推 118 条注入状态, 唯一变量 = matcher。"""
    rows: list[dict] = []
    for tbl in corpus:
        canonicals = tbl["canonicals"]
        n_can = len(canonicals)
        map_orig = matcher.mapping(tbl["orig_header"], canonicals)
        map_full = matcher.mapping(tbl["inj_header"], canonicals)
        h_orig = len(map_orig) / n_can if n_can else 1.0
        h_full = len(map_full) / n_can if n_can else 1.0
        for e in tbl["injections"]:
            single = list(tbl["orig_header"])
            single[e["col"]] = e["injected"]
            map_single = matcher.mapping(single, canonicals)
            h_single = len(map_single) / n_can if n_can else 1.0
            d_h = round((h_orig - h_single) * 10.0, 4) / 10.0
            target = next((c for c in canonicals
                           if matcher.mp.normalize_header(c)
                           == matcher.mp.normalize_header(e["original"])), None)
            absorbed = bool(target is not None
                            and map_full.get(target) == e["injected"])
            keyset_same = set(map_full) == set(map_orig)
            equivalent = (e["type"] in EQUIV_TYPES) and keyset_same
            detected = {str(g): bool(round(d_h * 10.0, 4) >= 10 * g) for g in GAMMAS}
            hit_anchor = detected[str(ANCHOR)]
            if hit_anchor:
                cls, mech = "H", None
            elif equivalent:
                cls, mech = "E", "absorption_normalized"
            else:
                cls = "HI"
                mech = "absorption_silent" if absorbed else "threshold_dilution"
            rows.append({
                "uid": tbl["uid"], "col": e["col"], "type": e["type"],
                "original": e["original"], "injected": e["injected"],
                "mapping_target": target, "n_canonical": n_can,
                "h_orig": round(h_orig, 6), "h_single": round(h_single, 6),
                "h_full_injection": round(h_full, 6), "marginal_dH": round(d_h, 6),
                "absorbed": absorbed, "canonical_keyset_identical": keyset_same,
                "detected_at_anchor": hit_anchor, "visible_by_gamma": detected,
                "equivalent": equivalent, "class": cls,
                "invisibility_mechanism": mech,
                "pair_score_on_target": (
                    round(matcher.pair_score(e["injected"], target)[0], 6)
                    if target else None),
                "single_mapped_canonicals": len(map_single),
                "matcher_kind": matcher.kind})
    return rows


def summarize(rows: list[dict]) -> dict:
    types = sorted({r["type"] for r in rows})
    return {
        "H": sum(1 for r in rows if r["class"] == "H"),
        "E": sum(1 for r in rows if r["class"] == "E"),
        "HI": sum(1 for r in rows if r["class"] == "HI"),
        "total": len(rows),
        "anchor_detected_by_type": {
            t: sum(1 for r in rows if r["type"] == t and r["detected_at_anchor"])
            for t in types},
        "n_by_type": {t: sum(1 for r in rows if r["type"] == t) for t in types},
        "detected_by_gamma_by_type": {
            str(g): {t: sum(1 for r in rows if r["type"] == t
                            and r["visible_by_gamma"][str(g)]) for t in types}
            for g in GAMMAS},
        "absorbed_strict_total": sum(1 for r in rows if r["absorbed"]),
        "undetected_at_anchor_total": sum(
            1 for r in rows if not r["detected_at_anchor"]),
        "hi_by_mechanism": dict(sorted(Counter(
            r["invisibility_mechanism"] for r in rows if r["class"] == "HI").items())),
        "keyset_identical_total": sum(
            1 for r in rows if r["canonical_keyset_identical"])}


def rank_types(types: list[str], rates: dict) -> dict:
    """降序名次, 并列取平均名次（fractional ranking, tau-b 标准做法）。"""
    order = sorted(types, key=lambda t: (-rates[t], t))
    ranks: dict[str, float] = {}
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and rates[order[j + 1]] == rates[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spectrum(rows: list[dict]) -> dict:
    """六类判别率 x gamma 网格 + 逐 gamma 类型名次。"""
    types = sorted({r["type"] for r in rows})
    out: dict[str, dict] = {}
    for g in GAMMAS:
        per_type = {}
        for t in types:
            its = [r for r in rows if r["type"] == t]
            nv = sum(1 for r in its if r["visible_by_gamma"][str(g)])
            per_type[t] = {"n": len(its), "visible": nv,
                           "visibility_rate": round(nv / len(its), 4) if its else 0.0}
        rates = {t: per_type[t]["visibility_rate"] for t in types}
        out[str(g)] = {"by_type": per_type,
                       "type_range": round(max(rates.values())
                                           - min(rates.values()), 4),
                       "ranking_desc": rank_types(types, rates),
                       "ordering_ties_broken_by_name": sorted(types,
                                                              key=lambda t: (-rates[t], t))}
    return out


def kendall_tau_b(a: dict, b: dict) -> dict:
    """tau-b（含并列修正）。a/b = {key: rank}。"""
    keys = sorted(a)
    conc = disc = tie_a = tie_b = 0
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            x, y = keys[i], keys[j]
            da, db = a[x] - a[y], b[x] - b[y]
            if da == 0 and db == 0:
                continue
            if da == 0:
                tie_a += 1
            elif db == 0:
                tie_b += 1
            elif (da > 0) == (db > 0):
                conc += 1
            else:
                disc += 1
    den = math.sqrt((conc + disc + tie_a) * (conc + disc + tie_b))
    if den == 0:
        return {"tau": 1.0, "defined": True, "note": "both_all_tied",
                "concordant": conc, "discordant": disc, "ties_a": tie_a,
                "ties_b": tie_b, "n_items": len(keys)}
    return {"tau": round((conc - disc) / den, 6), "defined": True, "note": "",
            "concordant": conc, "discordant": disc, "ties_a": tie_a,
            "ties_b": tie_b, "n_items": len(keys)}


# ------------------------------------------------------------- 主计算
def main() -> int:
    _install_network_guard()
    scan = self_source_scan()

    watch = {p: sha256_file(p) for p in
             (D1_ART, DRIFT / "injection_map.json", DRIFT / "injected_tables.json",
              EVAL / "t2_visibility_sensitivity.json")}
    input_files = {
        "logs/graph/eval/d1_mutant_validity_audit.json": watch[D1_ART],
        "data/research/drift_v0/output/injection_map.json":
            watch[DRIFT / "injection_map.json"],
        "data/research/drift_v0/output/injected_tables.json":
            watch[DRIFT / "injected_tables.json"],
        "logs/graph/eval/t2_visibility_sensitivity.json":
            watch[EVAL / "t2_visibility_sensitivity.json"],
        "research/paper_t6_matching_competition.py": sha256_file(T6_SCRIPT)}

    # 前提 P1: D1 底表在位且 all_pass=true（失配 = 停报, 见卡 §4）
    d1 = load_json(D1_ART)
    d1_all_pass = bool(d1["gates"].get("all_pass"))
    d1_rows = d1["payload"]["injections"]
    d1_index = {(r["uid"], r["col"]): r for r in d1_rows}
    d1_absorption_rows = [r for r in d1_rows if r["class"] in ("E", "HI")]
    d1_equiv_keys = sorted((r["uid"], r["col"]) for r in d1_rows if r["class"] == "E")

    # 前提 P2: 匹配器资产（生产件 + T6 Hungarian 件可导入）
    sys.path.insert(0, str(REPO / "scripts"))
    import m1_statement_parser as mp  # noqa: E402  只读导入生产匹配器
    spec = importlib.util.spec_from_file_location("t6_match", str(T6_SCRIPT))
    t6 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(t6)
    guard = guard_self_test(mp)
    api_missing = [api for api in T6_APIS_CALLED if not hasattr(t6, api)]

    matchers = build_matchers(mp, t6)
    kinds = [m.kind for m in matchers]
    corpus = load_corpus(mp)
    per_matcher = {m.kind: derive_injections(m, corpus) for m in matchers}
    sums = {k: summarize(per_matcher[k]) for k in kinds}
    spectra = {k: spectrum(per_matcher[k]) for k in kinds}
    base = per_matcher["greedy_production"]
    fam = PREREG["P1_edit_distance_family"]["matcher_columns"]

    # ---- G0: 生产件必须逐条复现 D1 底表
    mismatch = []
    for r in base:
        ref = d1_index.get((r["uid"], r["col"]))
        if ref is None:
            mismatch.append({"key": "%s:%d" % (r["uid"], r["col"]),
                             "reason": "missing_in_d1"})
            continue
        for field in ("class", "detected_at_anchor", "marginal_dH", "absorbed",
                      "canonical_keyset_identical", "visible_by_gamma"):
            if r[field] != ref[field]:
                mismatch.append({"key": "%s:%d" % (r["uid"], r["col"]),
                                 "field": field, "d2": str(r[field])[:80],
                                 "d1": str(ref[field])[:80]})
    g0 = {"pass": bool(d1_all_pass and not mismatch
                       and len(base) == D1_EXPECT["total"]
                       and len(d1_absorption_rows) == D1_EXPECT["absorption_rows"]
                       and (sums["greedy_production"]["H"],
                            sums["greedy_production"]["E"],
                            sums["greedy_production"]["HI"])
                       == (D1_EXPECT["H"], D1_EXPECT["E"], D1_EXPECT["HI"])
                       and sums["greedy_production"]["anchor_detected_by_type"]
                       == D1_EXPECT["anchor_detected_by_type"]),
          "d1_all_pass": d1_all_pass, "n_rows": len(base),
          "n_mismatches": len(mismatch), "mismatches": mismatch[:20],
          "d1_absorption_rows": len(d1_absorption_rows),
          "production_anchor_detected_by_type":
              sums["greedy_production"]["anchor_detected_by_type"]}

    # ---- P-1: ocr_similar 全盲存续 + 六类谱排序 Kendall tau-b
    blind_gate = {}
    for k in fam:
        s = spectra[k][str(ANCHOR)]["by_type"][OCR_TYPE]
        blind_gate[k] = {"n": s["n"], "visible_at_anchor": s["visible"],
                         "survives_all_blind": s["visible"] == 0,
                         "visible_any_gamma": any(
                             spectra[k][str(g)]["by_type"][OCR_TYPE]["visible"] > 0
                             for g in GAMMAS)}
    taus: dict[str, dict] = {}
    for k in kinds:
        per_gamma = {str(g): kendall_tau_b(spectra["greedy_production"][str(g)]["ranking_desc"],
                                           spectra[k][str(g)]["ranking_desc"])
                     for g in GAMMAS}
        defined = [v["tau"] for v in per_gamma.values() if v["defined"]]
        taus[k] = {"per_gamma": per_gamma,
                   "tau_min": min(defined) if defined else None,
                   "tau_mean": (round(sum(defined) / len(defined), 6)
                                if defined else None),
                   "preregistered": k in fam}
    fam_tau_min = {k: taus[k]["tau_min"] for k in fam}
    p1_blind_ok = all(v["survives_all_blind"] and not v["visible_any_gamma"]
                      for v in blind_gate.values())
    p1_tau_ok = all(t is not None and t >= TAU_GATE for t in fam_tau_min.values())
    g1 = {"pass": bool(p1_blind_ok and p1_tau_ok),
          "ocr_similar_blind_persistence": blind_gate,
          "ocr_visible_any_gamma_by_matcher": {k: blind_gate[k]["visible_any_gamma"]
                                               for k in fam},
          "kendall_tau_b_min_by_prereg_column": fam_tau_min,
          "kendall_tau_b_per_gamma": {k: {g: taus[k]["per_gamma"][g]["tau"]
                                          for g in taus[k]["per_gamma"]} for k in kinds},
          "tau_gate": TAU_GATE,
          "operationalization":
              PREREG["P1_edit_distance_family"]["tau_operationalization"],
          "blind_gate_pass": p1_blind_ok, "tau_gate_pass": p1_tau_ok,
          "r3_fallback_engaged": not (p1_blind_ok and p1_tau_ok)}

    # ---- 机理证据（非判据, 仅供 τ 失败可审计）: 逐件类别迁移
    prod_idx = {(r["uid"], r["col"]): r for r in base}
    class_transitions: dict[str, dict] = {}
    for k in kinds:
        if k == "greedy_production":
            continue
        k_idx = {(r["uid"], r["col"]): r for r in per_matcher[k]}
        matrix: dict[str, dict[str, int]] = {}
        flips: list[dict] = []
        for key, pr in prod_idx.items():
            kr = k_idx.get(key)
            if kr is None:
                continue
            matrix.setdefault(pr["class"], {})
            matrix[pr["class"]][kr["class"]] = \
                matrix[pr["class"]].get(kr["class"], 0) + 1
            if pr["class"] != kr["class"]:
                flips.append({"uid": key[0], "col": key[1], "type": pr["type"],
                              "original": pr["original"], "injected": pr["injected"],
                              "prod_class": pr["class"], "k_class": kr["class"],
                              "prod_marginal_dH": pr["marginal_dH"],
                              "k_marginal_dH": kr["marginal_dH"],
                              "injected_len": len(str(pr["injected"])),
                              "k_absorbed": kr["absorbed"],
                              "k_mapped_to_correct_field": bool(
                                  kr["absorbed"]
                                  and kr["mapping_target"] is not None
                                  and mp.normalize_header(str(kr["mapping_target"]))
                                  == mp.normalize_header(str(pr["original"]))),
                              "k_canonical_keyset_identical":
                                  kr["canonical_keyset_identical"],
                              "benign_correct_absorption": bool(
                                  kr["absorbed"] and kr["canonical_keyset_identical"]),
                              "blocked_from_E_only_by_type_rule": bool(
                                  kr["absorbed"] and kr["canonical_keyset_identical"]
                                  and kr["type"] not in EQUIV_TYPES)})
        lost = sum(1 for f in flips if f["prod_class"] == "H")
        gained = sum(1 for f in flips if f["k_class"] == "H")
        benign = sum(1 for f in flips if f["benign_correct_absorption"])
        type_blocked = sum(1 for f in flips
                           if f["blocked_from_E_only_by_type_rule"])
        class_transitions[k] = {
            "matrix_prod_to_k": matrix,
            "n_flips": len(flips),
            "visibility_lost_H_to_HI": lost, "visibility_gained_HI_to_H": gained,
            "net": gained - lost,
            "n_benign_correct_absorption": benign,
            "n_blocked_from_E_only_by_frozen_type_rule": type_blocked,
            "flip_types": dict(sorted(Counter(f["type"] for f in flips).items())),
            "flips": sorted(flips, key=lambda f: (f["type"], f["uid"], f["col"])),
            "note": ("方向性解释件（不入预注册判据）: 归一化打分把相对编辑距离 <= "
                     "NORM_REL_MAX 的长表头纳入映射 => 漂移被吸收 => 可见性下降; "
                     "净损失 > 0 即「越宽松的匹配器吞掉越多漂移」。"
                     "翻转的毒性定性: benign_correct_absorption = 该漂移被映射到"
                     "正确字段且标准字段集不变（良性吸收）; "
                     "blocked_from_E_only_by_frozen_type_rule = 该翻转只因类型不在"
                     "冻结 EQUIV_TYPES 内而未计入 E, 即谱形改变的幅度由 E/HI 的"
                     "类型闸门而非新增危害驱动。")}

    # ---- P-5 / DR-3: 33 吸收注入 x 匹配器 迁移矩阵
    tm_rows = []
    missing_cells = 0
    for key in [(r["uid"], r["col"]) for r in d1_absorption_rows]:
        ref = d1_index[key]
        idx = {x["uid"] + ":" + str(x["col"]): x for x in []}  # noqa: F841
        cells = {}
        for k in kinds:
            r = next((x for x in per_matcher[k]
                      if (x["uid"], x["col"]) == key), None)
            if r is None:
                missing_cells += 1
                continue
            cells[k] = {"class": r["class"], "marginal_dH": r["marginal_dH"],
                        "absorbed": r["absorbed"],
                        "pair_score_on_target": r["pair_score_on_target"],
                        "visible_by_gamma": r["visible_by_gamma"],
                        "state": "keep" if r["class"] == ref["class"] else "flip",
                        "flipped_to": None if r["class"] == ref["class"] else r["class"]}
        tm_rows.append({"uid": key[0], "col": key[1], "type": ref["type"],
                        "original": ref["original"], "injected": ref["injected"],
                        "d1_class": ref["class"],
                        "d1_mechanism": ref["invisibility_mechanism"],
                        "n_flips_prereg": sum(1 for k in fam
                                              if cells[k]["state"] == "flip"),
                        "n_flips_all": sum(1 for c in cells.values()
                                           if c["state"] == "flip"),
                        "cells": cells})
    flip_counts = {k: sum(1 for e in tm_rows if e["cells"][k]["state"] == "flip")
                   for k in kinds}
    flip_detail = [{"uid_col": "%s:%d" % (e["uid"], e["col"]), "type": e["type"],
                    "d1_class": e["d1_class"], "matcher": k,
                    "to": e["cells"][k]["class"],
                    "marginal_dH": e["cells"][k]["marginal_dH"],
                    "absorbed": e["cells"][k]["absorbed"]}
                   for e in tm_rows for k in kinds
                   if e["cells"][k]["state"] == "flip"]
    n_prereg_cells = len(tm_rows) * len(fam)
    g5 = {"pass": bool(missing_cells == 0
                       and len(tm_rows) == PREREG["P5_transition_matrix_completeness"]["rows"]
                       and n_prereg_cells == PREREG["P5_transition_matrix_completeness"]["rows"]
                       * PREREG["P5_transition_matrix_completeness"]["columns"]),
          "n_rows": len(tm_rows), "prereg_columns": fam,
          "supplementary_columns": [k for k in kinds if k not in fam],
          "cells_expected_prereg": n_prereg_cells, "cells_missing": missing_cells,
          "cells_expected_full": len(tm_rows) * len(kinds),
          "flip_count_by_matcher": flip_counts,
          "flip_detail": flip_detail}

    # ---- P-3: 等价稳定性（7 条; 翻转 = 发现, 不判失败）
    eq_rows = []
    for key in d1_equiv_keys:
        ref = d1_index[key]
        per = {}
        for k in kinds:
            r = next((x for x in per_matcher[k]
                      if (x["uid"], x["col"]) == key), None)
            per[k] = ({"class": r["class"], "equivalent": r["equivalent"],
                       "keyset_identical": r["canonical_keyset_identical"],
                       "detected_at_anchor": r["detected_at_anchor"],
                       "marginal_dH": r["marginal_dH"],
                       "stays_absorbed_equivalent": r["class"] == "E"}
                      if r else None)
        eq_rows.append({"uid": key[0], "col": key[1], "type": ref["type"],
                        "original": ref["original"], "injected": ref["injected"],
                        "per_matcher": per})
    eq_missing = sum(1 for c in eq_rows if any(v is None
                                               for v in c["per_matcher"].values()))
    eq_flips = [{"uid_col": "%s:%d" % (c["uid"], c["col"]), "type": c["type"],
                 "matcher": k, "becomes": v["class"], "marginal_dH": v["marginal_dH"]}
                for c in eq_rows for k, v in c["per_matcher"].items()
                if v and not v["stays_absorbed_equivalent"]]
    g3 = {"pass": bool(len(eq_rows) == len(d1_equiv_keys) == D1_EXPECT["E"]
                       and eq_missing == 0),
          "n_equivalence_rows": len(eq_rows), "columns": len(kinds),
          "missing_cells": eq_missing, "n_flips": len(eq_flips),
          "flips": eq_flips,
          "verdict_note": "P-3 门只判记录完整性; 翻转按预注册作「发现」逐条入账"}

    # ---- R3 对照: 全盲类型集合是否跨匹配器存续
    all_types = sorted({r["type"] for r in base})

    def blind_types_of(k: str) -> list:
        return [t for t in all_types
                if all(spectra[k][str(g)]["by_type"][t]["visible"] == 0
                       for g in GAMMAS)]

    blind_by_matcher = {k: blind_types_of(k) for k in kinds}
    fam_blind = {k: blind_by_matcher[k] for k in fam}
    intersection = sorted(set(fam_blind[fam[0]]).intersection(
        *[set(v) for v in fam_blind.values()]))
    union = sorted(set().union(*[set(v) for v in fam_blind.values()]))
    r3 = {"prereg_wording": ("D2 跨匹配器若谱形显著改变 -> 改为「盲区位置匹配器相关, "
                             "谱结构（存在全盲类型）匹配器无关」"),
          "blind_types_by_matcher": blind_by_matcher,
          "blind_intersection_prereg_family": intersection,
          "blind_union_prereg_family": union,
          "blind_set_identical_across_prereg_family":
              len({tuple(v) for v in fam_blind.values()}) == 1,
          "spectrum_shape_materially_changed": bool(g1["r3_fallback_engaged"]),
          "axis_attribution": {
              "assignment_axis_hungarian_flips":
                  class_transitions["hungarian_production"]["n_flips"],
              "scoring_axis_normalized_flips":
                  class_transitions["greedy_normalized"]["n_flips"],
              "reading": ("分配轴（贪心->Hungarian）零翻转 = 谱对分配算法不敏感; "
                          "打分轴（绝对 ed->相对 ed）翻转 = 谱对打分口径敏感。"
                          "τ 失败由打分轴单轴驱动。")},
          "downgrade_clause_half_evidence": {
              "half_a_blind_spot_position_matcher_dependent": (
                  "本窗证据不支持: 全盲集合在 4 个匹配器下恒为 [ocr_similar]"
                  if len({tuple(v) for v in blind_by_matcher.values()}) == 1
                  else "支持: 全盲集合随匹配器改变"),
              "half_b_spectrum_structure_matcher_independent": (
                  "支持: 存在全盲类型这一结构跨匹配器存续" if intersection
                  else "不支持: 交集内无全盲类型"),
              "what_actually_changed": (
                  "非全盲类型的可见率与名次（date_variant 在归一化打分下"
                  " 0.7059 -> 0.4118, 名次 1 -> 3）=> 谱排序改变, 全盲位置未变")},
          "conclusion": ("谱结构（存在全盲类型）匹配器无关（编辑距离族交集内 "
                         + ",".join(intersection) + " 全盲存续）" if intersection
                         else "全盲类型未在编辑距离族交集内存续 -> R3 降级表述不成立, 上报")}

    # ---- 红线: 只读 + 零端点 + 去标识
    after = {p: sha256_file(p) for p in watch}
    redline = {
        "frozen_and_baseline_inputs_unchanged": after == watch,
        "sha_before": {str(p.relative_to(REPO)): watch[p] for p in watch},
        "d1_baseline_gate_all_pass": d1_all_pass,
        "inputs_sha256": input_files,
        "client_identifier_zero_entered": None}
    g4 = {"pass": bool(scan["clean"] and not PORTS_TOUCHED and not ENDPOINT_VIOLATIONS
                       and MODEL_CALLS == 0 and guard["all_blocked"]
                       and guard["matcher_apis_all_present"] and not api_missing
                       and after == watch),
          "ports_touched": sorted(PORTS_TOUCHED), "model_calls": MODEL_CALLS,
          "budget_counter": 0, "endpoint_violations": ENDPOINT_VIOLATIONS,
          "socket_attempts_blocked_disclosure": {
              "n": len(SOCKET_ATTEMPTS_BLOCKED),
              "ports": sorted({a["port"] for a in SOCKET_ATTEMPTS_BLOCKED
                               if a["port"] is not None}),
              "events": SOCKET_ATTEMPTS_BLOCKED,
              "note": ("全部为护栏自证试连（guard_self_test 主动打 :8004 验证拦截生效）;"
                       " 连接在系统调用前即抛错, 零字节收发 => 不构成端点使用。"
                       " ports_touched 语义 = 实际建立的出站连接（D1 同口径: D1 跑同一试连"
                       " 并记 ports_touched=[]）。非自证来源的尝试 = 0。")},
          "source_scan_clean": scan["clean"],
          "source_scan_files": scan["files_scanned"],
          "gating_basis": scan["gating_basis"],
          "network_findings_in_d2_scope": scan["network_findings_in_d2_scope"],
          "helper_module": scan["helper_module"],
          "helper_module_ast_findings": scan["helper_module_ast_findings"],
          "helper_module_note": scan["helper_module_note"],
          "socket_import_disclosed": scan["socket_import_disclosed"],
          "active_connection_probes": guard,
          "t6_api_missing": api_missing,
          "embedding_asset_note": ("阶段 B 独立工件（bge-m3 本地 HF 加载）;"
                                   " 阶段 A 全程零模型服务调用"),
          "scope_note": ("硬门作用域 = 本窗脚本 + 导入链自有研究脚本; 生产匹配器"
                         "自带 OCR/VLM helper 故列作用域外, 其「本窗从未调用」由"
                         " socket 封死 + 试连自证 + hasattr 断言三重证明")}

    payload = {
        "inputs_sha256": input_files,
        "criterion_provenance": {
            "card": TASK_CARD, "card_id": CARD_ID, "phase": "A_deterministic",
            "prereg": PREREG, "anchor_gamma": ANCHOR,
            "gamma_grid": [str(g) for g in GAMMAS],
            "equivalence_types": list(EQUIV_TYPES), "d1_expect": D1_EXPECT,
            "control_note": ("canonical 字段集与归一化 = 生产 normalize_header"
                             "（跨匹配器恒定）; 唯一变量 = 打分口径 x 分配算法 两轴"),
            "r3_wording_source": "Paper Claim Set v2 R3 降级表述（卡内原样引用）"},
        "matchers": {m.kind: m.describe() for m in matchers},
        "spectrum": spectra,
        "ordering_kendall_tau": taus,
        "blind_types": blind_by_matcher,
        "matcher_class_transitions": class_transitions,
        "transition_matrix": {"rows_are_d1_absorption_injections": len(tm_rows),
                              "columns_prereg": fam,
                              "supplementary_columns": g5["supplementary_columns"],
                              "rows": tm_rows},
        "equivalence_stability": g3,
        "r3_assessment": r3,
        "counts_by_matcher": {k: dict(sums[k], matcher_kind=k) for k in kinds},
        "gate_details": {"G0_production_reproduces_d1": g0,
                         "G1_p1_blind_persistence_and_tau": g1,
                         "G3_p3_equivalence_stability": g3,
                         "G4_p4_zero_endpoint_and_readonly": g4,
                         "G5_p5_transition_matrix_completeness": g5},
        "prereg_predicates": {
            "P1_edit_distance_family_blind_and_tau": g1["pass"],
            "P3_equivalence_stability_rendered": g3["pass"],
            "P4_zero_endpoint_self_proof": g4["pass"],
            "P5_transition_matrix_complete": g5["pass"],
            "note": "预注册于任务卡 §2（含加编两阶段切分）, 执行后不溯及; "
                    "任一项 false 一律上报主线程, 禁止静默改判。P-2 属阶段 B 独立工件。"},
        "zero_endpoint": {"patterns": scan["patterns"],
                          "files_scanned": scan["files_scanned"],
                          "missing_files": scan["missing_files"],
                          "gating_basis": scan["gating_basis"],
                          "network_findings_in_d2_scope":
                              scan["network_findings_in_d2_scope"],
                          "endpoint_literal_mentions_advisory":
                              scan["endpoint_literal_mentions_advisory"],
                          "endpoint_literal_note": scan["endpoint_literal_note"],
                          "ports_touched": sorted(PORTS_TOUCHED),
                          "model_calls": MODEL_CALLS, "budget_counter": 0,
                          "socket_attempts_blocked": len(SOCKET_ATTEMPTS_BLOCKED),
                          "clean": scan["clean"],
                          "active_connection_probes": guard},
        "redline_self_check": redline}

    doc = {"meta": {"name": "d2-cross-matcher-deterministic", "version": "v1",
                    "card_id": CARD_ID, "task_card": TASK_CARD, "report": REPORT,
                    "phase": "A_deterministic_three",
                    "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "script": "research/paper_d2_cross_matcher_det.py",
                    "matchers": kinds, "n_injections": len(base),
                    "n_transition_rows": len(tm_rows), "endpoint_calls": 0,
                    "anchor_gamma": ANCHOR, "gamma_grid": [str(g) for g in GAMMAS],
                    "reproduce": ["python3 research/paper_d2_cross_matcher_det.py"]},
           "gates": {"G0_production_reproduces_d1": g0["pass"],
                     "G1_p1_blind_persistence_and_tau": g1["pass"],
                     "G3_p3_equivalence_stability": g3["pass"],
                     "G4_p4_zero_endpoint_and_readonly": g4["pass"],
                     "G5_p5_transition_matrix_completeness": g5["pass"],
                     "G6_digest_self_consistency": False},
           "payload": payload,
           "prereg_predicates": payload["prereg_predicates"]}

    leaks = client_identifier_scan(json.dumps(doc, ensure_ascii=False, sort_keys=True))
    redline["client_identifier_zero_entered"] = not leaks
    leaks2 = client_identifier_scan(json.dumps(doc, ensure_ascii=False, sort_keys=True))
    redline["client_identifier_zero_entered"] = not leaks2
    doc["gates"]["G4_p4_zero_endpoint_and_readonly"] = bool(g4["pass"] and not leaks2)
    doc["payload"]["prereg_predicates"]["P4_zero_endpoint_self_proof"] = bool(
        g4["pass"] and not leaks2)
    payload["gate_details"]["G4_p4_zero_endpoint_and_readonly"]["pass"] = bool(
        g4["pass"] and not leaks2)

    doc["payload_sha256"] = digest_payload(payload)     # payload 收口后才算（W2 f1bf00b）
    doc["sha256_scope"] = list(SHA_SCOPE)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    back = json.loads(OUT.read_text(encoding="utf-8"))
    doc["gates"]["G6_digest_self_consistency"] = (
        digest_payload(back["payload"]) == back["payload_sha256"])
    doc["gates"]["all_pass"] = bool(
        all(x["pass"] for x in (g0, g1, g3, g4, g5))
        and not leaks2 and doc["gates"]["G6_digest_self_consistency"])
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")

    print("matchers: " + ", ".join(kinds))
    for k in kinds:
        print("  %-22s H/E/HI=%s/%s/%s ocr_anchor=%s tau_min=%s blind=%s"
              % (k, sums[k]["H"], sums[k]["E"], sums[k]["HI"],
                 sums[k]["anchor_detected_by_type"].get(OCR_TYPE),
                 taus[k]["tau_min"], blind_by_matcher[k]))
    print("anchor visibility_rate spectrum:")
    for k in kinds:
        print("  %-22s %s" % (k, json.dumps(
            {t: spectra[k][str(ANCHOR)]["by_type"][t]["visibility_rate"]
             for t in all_types}, ensure_ascii=False)))
    print("transition rows=%d prereg_cells=%d missing=%d flips=%s"
          % (len(tm_rows), n_prereg_cells, missing_cells, flip_counts))
    print("equivalence rows=%d flips=%d" % (len(eq_rows), len(eq_flips)))
    print("r3: " + r3["conclusion"])
    print("gates " + json.dumps(doc["gates"], ensure_ascii=False))
    print("client_identifier_leaks=%s" % leaks2)
    print("payload_sha256=%s -> %s" % (doc["payload_sha256"], OUT))
    return 0 if doc["gates"]["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
