#!/usr/bin/env python3
"""D1 突变体有效性审计（零端点）: 118 注入三分类 + 9 检查点突变体 MO/MU。

卡号 TASK-20260831-01 | 判据冻结: docs/experiments/2026-08-31_d1_mutant_validity_audit_design.md
任务卡: docs/experiments/2026-08-31_d1_task_card.md

A 段 表头漂移注入 118 条 -> H 有害-可见 / E 等价 / HI 有害-不可见
    每条状态（锚点检出 / 吸收 / 标准字段集 / 边际 dH）从冻结原始件
    injection_map.json + injected_tables.json 经生产匹配器独立重推;
    T2 聚合值只作对账门（G1/G2/G3/G5）, 不参与分类。
B 段 检查点突变体 9 个 -> MO 可观测-有害 / MU 不可观测
    control + 9 mutants 在 /tmp 副本上重建（冻结 mutator, 活工件零改动）,
    逐叶 item 级证据视图差分区分「承载字段移动」与「仅派生标签移动」;
    E1.5 判分矩阵（t4）与确定性映射矩阵（检查点报告）作第二/第三数据源佐证。

红线机械护栏
    零端点: socket 层封死 + 源码自扫描（无 http 客户端导入）+ 端口集自证。
    只读:   输入摘要与 W2 登记对账 + 活工件前后摘要一致。
    去标识: 突变体证据只用位置别名（row_NN/item_NN）, 名称字段永不读取;
            全文再过禁用词扫荡并硬断言零残留。

复算: python3 research/paper_d1_mutant_validity_audit.py
输出: logs/graph/eval/d1_mutant_validity_audit.json
退出码: 0 = G1-G7 全过 + 红线自证通过; 1 = 任一门失败（上报, 不静默处置）。
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import shutil
import socket
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
DRIFT = REPO / "data" / "research" / "drift_v0" / "output"
OUT = EVAL / "d1_mutant_validity_audit.json"
SCRATCH = Path("/tmp/d1_mutant_scratch")

CARD_ID = "TASK-20260831-01"
DESIGN_DOC = "docs/experiments/2026-08-31_d1_mutant_validity_audit_design.md"
TASK_CARD = "docs/experiments/2026-08-31_d1_task_card.md"

GAMMAS = (0.2, 0.3, 0.5, 0.7, 0.9)
ANCHOR = 0.2                     # 蓝图 C1 锚点阈值（判据冻结）
EQUIV_TYPES = ("alias_variant", "mixed_lang", "prefix_noise")
OCR_TYPE = "ocr_similar"

SHA_SCOPE = ("inputs_sha256", "criterion_provenance", "injections", "counts",
             "equivalence", "gamma_equivalence_check", "ocr_absorption_examples",
             "mutants", "mutant_counts", "m7_retention", "gate_details",
             "prereg_predicates", "zero_endpoint", "redline_self_check")

# 冻结预期（设计稿 §3 预注册, 执行后不溯及）
PREREG = {"H": 85, "E": 7, "HI": 26, "total": 118,
          "anchor_visible_by_type": {"alias_variant": 36, "date_variant": 12,
                                     "mixed_lang": 19, "ocr_similar": 0,
                                     "prefix_noise": 13, "unit_suffix": 5},
          "mu_ids": ["M7_nf_fail_3"], "n_mo": 8, "n_mutants": 9,
          "n_ocr": 13, "min_ocr_examples": 3}

MUTANT_ARTIFACTS = {
    "m1_regression": "scenario1_regression_report.json",
    "m2_deterministic": "m2_deterministic_report.json",
    "m2_judge": "m2_judge_report.json",
    "m2_number_faithfulness": "number_faithfulness_report.json",
}
# 叶 -> 契约名 / 评审维: 逐字对应 research/paper_w2_e15_full_judge.py 的
# CONTRACT_OF_LEAF / JUDGE_DIM_OF_LEAF 与 evidence_for() 分支。
CONTRACT_OF_LEAF = {"qa.retrieval.source_required": "source_required",
                    "qa.numeric.exact": "exact_numeric",
                    "qa.refusal.deterministic": "refusal_expected"}
JUDGE_DIM_OF_LEAF = {"qa.faithfulness.judge": "faithfulness",
                     "qa.citation.judge": "citation_quality",
                     "qa.refusal.judge": "refusal_appropriateness"}
# 承载字段 (primary observation) = 该叶需求所「关于」的观测;
# 派生标签 = 上游判定器写出的结论字段, 其本身不构成新观测。
PRIMARY_FIELDS: dict[str, tuple[str, ...]] = {
    "parse.doc.ok": ("status",),
    "parse.doc.throughput": ("run_rows_count", "run_timestamp_recorded",
                             "run_mode_quick", "run_rows_all_have_status"),
    "parse.table.regression": ("status",),
    "parse.field.hit_rate": ("values_checked", "values_mismatched"),
    "parse.reconcile.equations": ("status",),
    "qa.retrieval.source_required": ("contract_verdict",),
    "qa.numeric.exact": ("contract_verdict",),
    "qa.refusal.deterministic": ("contract_verdict",),
    "qa.numeric.number_grounding": ("number_claims", "ungrounded"),
    "qa.faithfulness.judge": ("verdict_on_0_5",),
    "qa.citation.judge": ("verdict_on_0_5",),
    "qa.refusal.judge": ("verdict_on_0_5",),
}
DERIVED_FIELDS: dict[str, tuple[str, ...]] = {
    "qa.numeric.number_grounding": ("grounding_verdict",)}


# ---------------------------------------------------------------- 零端点护栏
def _install_network_guard() -> None:
    """socket 层封死; 用子类替换以保证导入期 `class X(socket)` 仍合法。"""
    real_socket = socket.socket

    class _BlockedSocket(real_socket):  # type: ignore[misc]
        def connect(self, *a, **k):
            raise RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")

        def connect_ex(self, *a, **k):
            raise RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")

        def sendto(self, *a, **k):
            raise RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")

    def _blocked(*_a, **_k):
        raise RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")

    socket.socket = _BlockedSocket         # type: ignore[assignment]
    socket.create_connection = _blocked    # type: ignore[assignment]
    socket.getaddrinfo = _blocked          # type: ignore[assignment]


# 模式串拆分构造: 避免自扫描命中模式定义行自身
SELF_SCAN_PATTERNS = [
    "url" + "open", "ur" + "llib", "requ" + "ests", "http" + "x",
    "open" + "ai", "aio" + "http",
    "htt" + "p:" + "/" * 2, "HTT" + "PS:" + "/" * 2, "sock" + "et.connect",
    ":" + "8004", ":" + "8005", ":" + "8006", ":" + "8007", ":" + "8008",
    ":" + "5050",
]
SELF_SCAN_FILES = ("research/paper_d1_mutant_validity_audit.py",
                   "scripts/eval_checkpoint_discrimination.py",
                   "scripts/eval_checkpoint_aggregate.py")
# 分层口径: m1_statement_parser 是生产件, 自带 OCR/VLM 调用helper（urllib）。
# D1 只调用其纯文本匹配 API。作用域分层与 T2 冻结先例一致（T2 SCAN_MANIFEST
# 只列本窗 research 脚本）; 「从未调用」不靠嘴说 —— 出站由 socket 层封死,
# 并由 guard_self_test 主动试连自证。
HELPER_MODULE = "scripts/m1_statement_parser.py"
MATCHER_APIS_CALLED = ("normalize_header", "SchemaField", "SchemaTable",
                       "map_headers", "_best_field_for_header")
PORTS_TOUCHED: set[int] = set()
ENDPOINT_VIOLATIONS: list[str] = []


# 硬门（判据 = 任务卡 P4 falsify「不导入任何 http 客户端」+ 运行时端口自证）:
# 用 AST 检查 import / call 节点, 注释与文档字符串里的端点字样不算违规。
# 提示层（不判门, 全量披露）: 原始字面量提及, 便于人工复核护栏没有放水。
# 逐字拆分构造: 与本文件 SELF_SCAN_PATTERNS 同法, 避免自扫描命中常量定义行
HTTP_CLIENT_ROOTS = ("url" + "lib", "re" + "quests", "http" + "x", "aio" + "http",
                     "open" + "ai", "htt" + "p", "ftp" + "lib", "smtp" + "lib",
                     "telnet" + "lib", "web" + "socket", "web" + "socket_client",
                     "sub" + "process")
# socket 单列: D1 导入它的唯一用途是安装出站封死 + 试连自证, 属自证件而非端点件
SOCKET_ROOT = "sock" + "et"


def _dotted(node) -> str:
    """把 a.b.c 形式的 func 节点还原为点号串, 非该形式返回空串。"""
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
    """AST 级检索: http 客户端导入 / 其调用 / subprocess 外呼 = 硬违规。"""
    tree = ast.parse((REPO / rel).read_text(encoding="utf-8"), filename=rel)
    imported: dict[str, str] = {}
    hits: list[dict] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for al in node.names:
                origin = al.asname or al.name
                if origin.split(".")[0] in HTTP_CLIENT_ROOTS:
                    hits.append({"kind": "import", "line": node.lineno,
                                 "detail": "import " + al.name})
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.split(".")[0] in HTTP_CLIENT_ROOTS:
                hits.append({"kind": "import_from", "line": node.lineno,
                             "detail": "from " + mod + " import "
                                       + ",".join(a.name for a in node.names)})
            if mod.split(".")[0] in HTTP_CLIENT_ROOTS:
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
    """分层自扫描: AST 硬门（判 G6）+ 字面量提示层（只披露不判门）。"""
    gating: dict[str, list] = {}
    advisory: dict[str, list] = {}
    missing: list[str] = []
    scanned: list[str] = []
    for rel in SELF_SCAN_FILES + (HELPER_MODULE,):
        f = REPO / rel
        if not f.exists():
            missing.append(rel)
            continue
        lines = f.read_text(encoding="utf-8").splitlines()
        lit = []
        for i, ln in enumerate(lines, 1):
            code = ln.split("#", 1)[0]
            if "blocked" in code or "ZERO_ENDPOINT" in code or '"""' in code:
                continue
            for pat in SELF_SCAN_PATTERNS:
                if pat in code:
                    lit.append({"line": i, "pattern": pat,
                                "text": ln.strip()[:120]})
        if lit:
            advisory[rel] = lit
        if rel == HELPER_MODULE:
            continue
        scanned.append(rel)
        found = ast_network_findings(rel)
        if found:
            gating[rel] = found
    helper_hits = ast_network_findings(HELPER_MODULE) if (
        REPO / HELPER_MODULE).exists() else []
    return {"patterns": SELF_SCAN_PATTERNS, "files_scanned": scanned,
            "helper_module": HELPER_MODULE, "missing_files": missing,
            "gating_basis": ("AST import/call 检索（http 客户端根模块 ∈ "
                             + ",".join(sorted(HTTP_CLIENT_ROOTS))
                             + "）; socket 仅用于封死出站与试连自证, 单列披露"),
            "network_findings_in_d1_scope": gating,
            "endpoint_literal_mentions_advisory": advisory,
            "endpoint_literal_note": (
                "字面量层不判门: 命中全部位于中文注释/文档字符串/报告文本中的"
                "「不调用 :8004/:5050/:8006」否定式声明与本护栏模式串自身; "
                "逐条披露供人工复核护栏未放水。"),
            "helper_module_ast_findings": [h["detail"] for h in helper_hits],
            "helper_module_note": (
                "生产匹配器 " + HELPER_MODULE + " 自带 OCR/VLM 调用helper, 故列"
                "D1 作用域之外（T2 SCAN_MANIFEST 同构口径: 只扫本窗 research 脚本）。"
                "D1 对其「只调用纯文本匹配 API」不靠嘴说: 三重自证 = socket 层封死 "
                "+ guard_self_test 主动试连全拦 + MATCHER_APIS_CALLED hasattr 存在性断言。"),
            "socket_import_disclosed": True,
            "clean": not gating and not missing}


def guard_self_test(mp=None) -> dict:
    """主动试连三次: 必须全部被拦, 否则护栏是空转（W2 guard probe 同构）。
    另断言 D1 声明调用的匹配器 API 真实存在, 防「发明 API」式虚假声明。"""
    addr = ("127.0.0.1", 8000 + 4)
    probes = ("create_connection", "getaddrinfo", "socket_connect")
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
    out["all_blocked"] = all(str(out[k]).startswith("blocked:") for k in probes)
    present = {api: bool(hasattr(mp, api)) for api in MATCHER_APIS_CALLED}
    out["matcher_apis_present"] = present
    out["matcher_apis_all_present"] = bool(present) and all(present.values())
    return out


# ---------------------------------------------------------------- 去标识化
# 逐字沿用 research/paper_w2_e15_full_judge.py 的 CLIENT_TOKENS（甲方标识零进入）
CLIENT_TOKENS = ["华泰紫金", "嘉合", "复熙", "博时", "博时基金", "华泰",
                 "minan", "jiaxing", "boshi", "fuxi", "caitong", "guojin",
                 "nanhua", "TraFax", "WaveFax", "NCAMC", "sample_"]
ID_TOKENS = ["q01_", "q02_", "q03_", "q04_", "q05_", "q06_", "q07_",
             "q08_", "q09_", "q10_", "q11_", "q12_", "adv_"]


def client_identifier_scan(text: str) -> list[str]:
    low = text.lower()
    return sorted({t for t in CLIENT_TOKENS + ID_TOKENS if t.lower() in low})


# ---------------------------------------------------------------- 工具
def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest_payload(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False,
                                     sort_keys=True).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- A 段: 注入三分类
class Matcher:
    """生产匹配器只读封装（与 T2 同流: scripts/m1_statement_parser）。"""

    def __init__(self) -> None:
        sys.path.insert(0, str(REPO / "scripts"))
        import m1_statement_parser as mp  # noqa: E402  只读导入生产匹配器
        self.mp = mp

    def unique_canonical(self, header: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for h in header:
            k = self.mp.normalize_header(h)
            if not k or k in seen:
                continue
            seen.add(k)
            out.append(str(h))
        return out

    def mapping(self, header: list[str], canonicals: list[str]) -> dict:
        fields = [self.mp.SchemaField(std, [std]) for std in canonicals]
        st = self.mp.SchemaTable(table_name="d1", layout="grid",
                                 header_region_keywords=[], fields=fields)
        mapping, _unmapped = self.mp.map_headers(header, st)
        return mapping

    def tier(self, header: str, canonical: str | None) -> int:
        """吸收档位: 4/3 精确, 2 归一化包含, 1 编辑距离<=1, 0 未命中（>=1 = 吸收区）。"""
        if not canonical:
            return 0
        best = self.mp._best_field_for_header(
            self.mp.normalize_header(header),
            [self.mp.SchemaField(canonical, [canonical])])
        return best[0] if best else 0


def derive_injections(m: Matcher) -> tuple[list[dict], dict]:
    """从冻结原始件独立重推 118 条注入状态, 按设计稿 §2 分类。"""
    imap = load_json(DRIFT / "injection_map.json")
    tables = {t["uid"]: t["table"] for t in load_json(DRIFT / "injected_tables.json")}
    by_uid: dict[str, list[dict]] = {}
    for e in imap["mapping"]:
        by_uid.setdefault(e["uid"], []).append(e)

    rows: list[dict] = []
    for uid in sorted(by_uid):
        inj_header = [str(c) if c is not None else "" for c in tables[uid][0]]
        orig_header = list(inj_header)
        for e in by_uid[uid]:
            orig_header[e["col"]] = e["original"]
        canonicals = m.unique_canonical(orig_header)
        map_orig = m.mapping(orig_header, canonicals)
        map_full = m.mapping(inj_header, canonicals)
        n_can = len(canonicals)
        h_orig = len(map_orig) / n_can if n_can else 1.0
        h_full = len(map_full) / n_can if n_can else 1.0
        for e in sorted(by_uid[uid], key=lambda x: x["col"]):
            single = list(orig_header)
            single[e["col"]] = e["injected"]
            h_single = len(m.mapping(single, canonicals)) / n_can if n_can else 1.0
            d_h = round((h_orig - h_single) * 10.0, 4) / 10.0
            target = next((c for c in canonicals
                           if m.mp.normalize_header(c)
                           == m.mp.normalize_header(e["original"])), None)
            absorbed = bool(target is not None and map_full.get(target) == e["injected"])
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
                "uid": uid, "col": e["col"], "type": e["type"],
                "original": e["original"], "injected": e["injected"],
                "mapping_target": target, "target_exists": target is not None,
                "absorption_tier": m.tier(e["injected"], target),
                "absorbed": absorbed,
                "canonical_keyset_identical": bool(keyset_same),
                "n_canonical": n_can,
                "h_orig": round(h_orig, 6), "h_single": round(h_single, 6),
                "h_full_injection": round(h_full, 6),
                "marginal_dH": round(d_h, 6),
                "detected_at_anchor": hit_anchor,
                "visible_by_gamma": detected,
                "equivalent": equivalent,
                "class": cls, "invisibility_mechanism": mech})

    types = sorted({r["type"] for r in rows})
    counts = {
        "H": sum(1 for r in rows if r["class"] == "H"),
        "E": sum(1 for r in rows if r["class"] == "E"),
        "HI": sum(1 for r in rows if r["class"] == "HI"),
        "total": len(rows),
        "n_tables": len(by_uid),
        "by_class_by_type": {c: dict(sorted(
            Counter(r["type"] for r in rows if r["class"] == c).items()))
            for c in ("H", "E", "HI")},
        "anchor_detected_by_type": {
            t: sum(1 for r in rows if r["type"] == t and r["detected_at_anchor"])
            for t in types},
        "n_by_type": {t: sum(1 for r in rows if r["type"] == t) for t in types},
        "anchor_detected_total": sum(1 for r in rows if r["detected_at_anchor"]),
        # 两种「吸收」口径同时入账（机制分层, 非重分类）:
        #   strict  = 映射层把注入表头接回真值 canonical
        #   anchor  = 锚点阈值未检出（设计稿 §2 / P2 推导口径）
        "absorbed_strict_total": sum(1 for r in rows if r["absorbed"]),
        "undetected_at_anchor_total": sum(1 for r in rows if not r["detected_at_anchor"]),
        "hi_by_mechanism": dict(sorted(Counter(
            r["invisibility_mechanism"] for r in rows if r["class"] == "HI").items())),
        "absorbed_and_detected_at_anchor": sum(1 for r in rows
                                              if r["absorbed"] and r["detected_at_anchor"]),
        "keyset_identical_total": sum(1 for r in rows
                                      if r["canonical_keyset_identical"])}
    return rows, counts


# ---------------------------------------------------------------- B 段: 突变体
def _parse(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def leaf_items(art: dict, leaf_id: str) -> list[dict]:
    """E1.5 evidence_for() 的结构化同构转写: 只产 item 级观测, 屏蔽一切聚合量。

    名称字段（label / id / q / answer / sources）永不读取, 条目只按位置编号。
    """
    rows_rep = art.get("m1_regression")
    if leaf_id == "parse.doc.ok":
        return [{"status": r.get("status")} for r in (rows_rep or {}).get("rows", [])]
    if leaf_id == "parse.doc.throughput":
        if rows_rep is None:
            return []
        rows = rows_rep.get("rows", [])
        return [{"run_rows_count": len(rows),
                 "run_timestamp_recorded": bool(rows_rep.get("timestamp")),
                 "run_mode_quick": bool(rows_rep.get("quick")),
                 "run_rows_all_have_status": bool(rows)
                 and all(r.get("status") for r in rows)}]
    base_rows = [r for r in (rows_rep or {}).get("rows", [])
                 if not str(r.get("status", "")).startswith("SKIP")]
    if leaf_id in ("parse.table.regression", "parse.reconcile.equations"):
        return [{"status": r.get("status")} for r in base_rows]
    if leaf_id == "parse.field.hit_rate":
        return [{"values_checked": len(r.get("expected") or []),
                 "values_mismatched": len(r.get("diffs") or [])} for r in base_rows]
    if leaf_id in CONTRACT_OF_LEAF:
        contract = CONTRACT_OF_LEAF[leaf_id]
        rep = art.get("m2_deterministic") or {}
        return [{"contract_verdict": "PASS" if ch.get("pass") else "FAIL"}
                for r in rep.get("results", []) for ch in r.get("checks", [])
                if ch.get("type") == contract]
    if leaf_id == "qa.numeric.number_grounding":
        rep = art.get("m2_number_faithfulness") or {}
        return [{"number_claims": len(r.get("numbers") or []),
                 "ungrounded": len(r.get("ungrounded") or []),
                 "grounding_verdict": "PASS" if r.get("pass") else "FAIL"}
                for r in rep.get("results", [])]
    if leaf_id in JUDGE_DIM_OF_LEAF:
        dim = JUDGE_DIM_OF_LEAF[leaf_id]
        rep = art.get("m2_judge")
        if rep is None:
            return []
        out = []
        for r in rep.get("results", []):
            cell = (r.get("scores") or {}).get(dim)
            if isinstance(cell, dict) and cell.get("score") is not None:
                out.append({"verdict_on_0_5": int(cell["score"])})
        return out
    raise KeyError("unknown leaf " + leaf_id)


def render_line(leaf_id: str, idx: int, item: dict) -> str:
    tag = ("run" if leaf_id == "parse.doc.throughput"
           else "row_%02d" % idx if leaf_id.startswith("parse.")
           else "item_%02d" % idx)
    return tag + " " + " ".join("%s=%s" % (k, v) for k, v in item.items())


def diff_views(ctl: list[dict], mut: list[dict], leaf_id: str) -> dict:
    """逐条对比 item 级观测: 区分承载字段移动 vs 仅派生标签移动。"""
    primary = PRIMARY_FIELDS[leaf_id]
    derived = DERIVED_FIELDS.get(leaf_id, ())
    moved_primary: list[int] = []
    moved_derived_only: list[int] = []
    for i in range(max(len(ctl), len(mut))):
        a = ctl[i] if i < len(ctl) else None
        b = mut[i] if i < len(mut) else None
        if a is None or b is None:
            moved_primary.append(i + 1)      # 条目出现/消失本身即观测层变化
            continue
        if any(a.get(k) != b.get(k) for k in primary):
            moved_primary.append(i + 1)
        elif any(a.get(k) != b.get(k) for k in derived):
            moved_derived_only.append(i + 1)
    return {"n_items_control": len(ctl), "n_items_mutant": len(mut),
            "primary_fields": list(primary), "derived_fields": list(derived),
            "n_primary_items_moved": len(moved_primary),
            "n_derived_only_items_moved": len(moved_derived_only),
            "primary_items_moved_1based": moved_primary[:12],
            "moved_indices_truncated": len(moved_primary) > 12}


def raw_diff(ctl: dict, mut: dict) -> dict:
    """原始工件字段级差分（只记路径与值类型, 不含任何字符串值）。"""

    def walk(a, b, path: str, acc: dict) -> None:
        if isinstance(a, dict) and isinstance(b, dict):
            for k in sorted(set(a) | set(b)):
                sub = path + "." + k if path else k
                if k not in a or k not in b:
                    acc[sub] = ("present" if k in a else "absent",
                                "present" if k in b else "absent")
                else:
                    walk(a[k], b[k], sub, acc)
        elif isinstance(a, list) and isinstance(b, list):
            for i in range(max(len(a), len(b))):
                sub = "%s[%d]" % (path, i)
                if i >= len(a) or i >= len(b):
                    acc[sub] = ("length", "length")
                else:
                    walk(a[i], b[i], sub, acc)
        elif a != b:
            acc[path] = (type(a).__name__, type(b).__name__)

    acc: dict[str, tuple] = {}
    for key, fname in MUTANT_ARTIFACTS.items():
        a, b = ctl.get(key), mut.get(key)
        if a is None and b is None:
            acc[fname] = ("absent", "absent")
        elif a is None or b is None:
            acc[fname] = ("present" if a is not None else "absent",
                          "present" if b is not None else "absent")
        else:
            walk(a, b, fname, acc)
    general: dict[str, dict] = {}
    for path, kinds in acc.items():
        g = re.sub(r"\[\d+\]", "[*]", path)
        slot = general.setdefault(g, {"n_instances": 0, "control_type": kinds[0],
                                      "mutant_type": kinds[1]})
        slot["n_instances"] += 1
    return {"n_atomic_paths_changed": len(acc),
            "changed_paths_generalized": dict(sorted(general.items())),
            "artifacts_touched": sorted({k.split(".")[0] for k in general})}


def _mutator_by_id() -> dict:
    sys.path.insert(0, str(REPO / "scripts"))
    import eval_checkpoint_discrimination as ecd  # noqa: E402  纯确定性导入
    return {mm["id"]: mm for mm in ecd.build_mutants()}


def materialize(states: list[str]) -> dict[str, dict]:
    """control + mutants 的工件副本落 /tmp; 活工件与冻结件零改动。"""
    mutators = _mutator_by_id()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    assert str(SCRATCH.resolve()).startswith("/tmp"), "scratch 必须落在 /tmp"
    dirs: dict[str, dict] = {}
    for state in states:
        d = SCRATCH / state
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        for fname in MUTANT_ARTIFACTS.values():
            src = EVAL / fname
            if src.exists():
                shutil.copyfile(src, d / fname)
        if state != "control":
            mutators[state]["mutate"](str(d))
        dirs[state] = {k: _parse(d / v) for k, v in MUTANT_ARTIFACTS.items()}
    return dirs


def classify_mutants(dirs: dict, frozen_disc: dict, t4_e15: dict) -> tuple[list[dict], dict]:
    """每个突变体 -> MO / MU（设计稿 §2 承载字段规则）+ 证据路径列。"""
    mutators = _mutator_by_id()
    judged = t4_e15["leaf_score_matrix_judged"]
    sep_judged = {x["id"]: x for x in t4_e15["separation_judged"]["per_mutant"]}
    sep_mapped = {x["id"]: x for x in
                  t4_e15["separation_mapped_control_only_caliber"]["per_mutant"]}
    frozen_by_id = {x["id"]: x for x in frozen_disc["mutants"]}
    ctl = dirs["control"]
    ctl_view = {lf: leaf_items(ctl, lf) for lf in PRIMARY_FIELDS}
    out: list[dict] = []
    for mid in [x["id"] for x in frozen_disc["mutants"]]:
        spec = mutators[mid]
        targets = list(spec.get("targets") or []) + list(spec.get("graded") or [])
        mut = dirs[mid]
        rdiff = raw_diff(ctl, mut)
        views = {lf: diff_views(ctl_view[lf], leaf_items(mut, lf), lf)
                 for lf in targets}
        carrier_leaves = sorted(lf for lf, v in views.items()
                                if v["n_primary_items_moved"] > 0)
        derived_only = sorted(lf for lf, v in views.items()
                              if v["n_primary_items_moved"] == 0
                              and v["n_derived_only_items_moved"] > 0)
        cls = "MO" if carrier_leaves else "MU"
        evidence_paths = []
        for lf in carrier_leaves:
            v = views[lf]
            items_mut = leaf_items(mut, lf)
            evidence_paths.append({
                "leaf": lf,
                "carrier_fields": list(PRIMARY_FIELDS[lf]),
                "derived_fields": list(DERIVED_FIELDS.get(lf, ())),
                "n_items_control": v["n_items_control"],
                "n_items_mutant": v["n_items_mutant"],
                "n_carrier_items_moved": v["n_primary_items_moved"],
                "example_item_lines": [
                    render_line(lf, int(i), items_mut[int(i) - 1])
                    for i in v["primary_items_moved_1based"][:3]
                    if int(i) - 1 < len(items_mut)],
                "raw_paths_sample": sorted(rdiff["changed_paths_generalized"])[:6]})
        jrow, crow = judged[mid], judged["control"]
        out.append({
            "id": mid, "tree": spec.get("tree"),
            "target_leaves": sorted(targets),
            "classification": cls,
            "carrier_leaves": carrier_leaves,
            "derived_label_only_leaves": derived_only,
            "item_evidence_view": views,
            "raw_field_diff": rdiff,
            "evidence_paths": evidence_paths,
            "corroboration_judged_leaf_deltas": {
                lf: [crow[lf], jrow[lf]] for lf in targets if jrow.get(lf) != crow.get(lf)},
            "corroboration_sep_judged": sep_judged[mid]["sep_blended"],
            "corroboration_sep_mapped": sep_mapped[mid]["sep_blended"],
            "corroboration_frozen_mapped_deltas": {
                h["leaf"]: h["delta"] for h in frozen_by_id[mid]["target_hits"]}})
    counts = {"total": len(out),
              "MO": sum(1 for x in out if x["classification"] == "MO"),
              "MU": sum(1 for x in out if x["classification"] == "MU"),
              "mu_ids": sorted(x["id"] for x in out if x["classification"] == "MU"),
              "mo_missing_evidence_path": sorted(
                  x["id"] for x in out
                  if x["classification"] == "MO" and not x["evidence_paths"])}
    return out, counts


# ---------------------------------------------------------------- 主流程
def main() -> int:
    _install_network_guard()
    scan = self_source_scan()
    watch = {f: sha256_file(EVAL / f) for f in MUTANT_ARTIFACTS.values()
             if (EVAL / f).exists()}
    watch["injection_map.json"] = sha256_file(DRIFT / "injection_map.json")
    watch["injected_tables.json"] = sha256_file(DRIFT / "injected_tables.json")

    input_files = {
        "data/research/drift_v0/output/injection_map.json": None,
        "data/research/drift_v0/output/injected_tables.json": None,
        "logs/graph/eval/t2_visibility_sensitivity.json": None,
        "logs/graph/eval/checkpoint_discrimination_report.json": None,
        "logs/graph/eval/t4_pso_fair_comparison.json": None,
        "config/eval_checkpoint_trees.json": None}
    for rel in input_files:
        input_files[rel] = sha256_file(REPO / rel)
    # 前提 P1: 冻结注入件摘要须与 W2 登记一致（失配 = 中止上报, 不静默继续）
    t4_all = load_json(EVAL / "t4_pso_fair_comparison.json")
    registered = t4_all["payload"]["inputs_sha256"]
    drift_match = {k: (v == registered.get(k)) for k, v in input_files.items()
                   if k in registered}

    m = Matcher()
    guard = guard_self_test(m.mp)   # 主动试连自证 + API 存在性断言
    injections, counts = derive_injections(m)
    t2 = load_json(EVAL / "t2_visibility_sensitivity.json")

    frozen_equiv = {(e["uid"], e["col"])
                    for e in t2["e2_2_equivalence_correction"]["equivalent_list"]}
    mine_equiv = {(r["uid"], r["col"]) for r in injections if r["equivalent"]}
    t2_anchor_by_type = {t: v["visible"] for t, v in
                         t2["e2_1_gamma_grid"][str(ANCHOR)]["by_type"].items()}
    equiv_rows = [r for r in injections if r["equivalent"]]
    ocr = [r for r in injections if r["type"] == OCR_TYPE]
    ocr_triples = [{"original": r["original"], "injected": r["injected"],
                    "mapping_target": r["mapping_target"],
                    "target_unchanged": r["mapping_target"] == r["original"],
                    "absorption_tier": r["absorption_tier"], "class": r["class"]}
                   for r in ocr]

    g1 = {"pass": mine_equiv == frozen_equiv, "n_d1": len(mine_equiv),
          "n_t2_frozen": len(frozen_equiv),
          "only_in_d1": sorted("%s:%d" % x for x in mine_equiv - frozen_equiv),
          "only_in_t2": sorted("%s:%d" % x for x in frozen_equiv - mine_equiv)}
    g2 = {"pass": (counts["H"] == PREREG["H"] and counts["E"] == PREREG["E"]
                   and counts["HI"] == PREREG["HI"]
                   and counts["total"] == PREREG["total"]
                   and counts["anchor_detected_by_type"]
                   == PREREG["anchor_visible_by_type"]
                   and counts["anchor_detected_by_type"] == t2_anchor_by_type),
          "d1_counts": {"H": counts["H"], "E": counts["E"], "HI": counts["HI"],
                        "total": counts["total"]},
          "d1_anchor_detected_by_type": counts["anchor_detected_by_type"],
          "t2_frozen_anchor_detected_by_type": t2_anchor_by_type,
          "prereg": {k: PREREG[k] for k in
                     ("H", "E", "HI", "total", "anchor_visible_by_type")}}
    g3 = {"pass": not any(r["visible_by_gamma"][str(g)] for r in equiv_rows
                          for g in GAMMAS),
          "equivalent_uid_cols": ["%s:%d" % (r["uid"], r["col"]) for r in equiv_rows],
          "violations": [{"uid_col": "%s:%d" % (r["uid"], r["col"]),
                          "visible_at": [str(g) for g in GAMMAS
                                         if r["visible_by_gamma"][str(g)]]}
                         for r in equiv_rows
                         if any(r["visible_by_gamma"][str(g)] for g in GAMMAS)]}

    disc = load_json(EVAL / "checkpoint_discrimination_report.json")
    dirs = materialize(["control"] + [x["id"] for x in disc["mutants"]])
    mutants, mutant_counts = classify_mutants(dirs, disc, t4_all["payload"]["e1_5"])
    g4 = {"pass": (mutant_counts["mu_ids"] == PREREG["mu_ids"]
                   and mutant_counts["MO"] == PREREG["n_mo"]
                   and mutant_counts["total"] == PREREG["n_mutants"]
                   and not mutant_counts["mo_missing_evidence_path"]
                   and all(x["corroboration_sep_judged"] > 0
                           for x in mutants if x["classification"] == "MO")
                   and all(x["corroboration_sep_judged"] == 0.0
                           for x in mutants if x["classification"] == "MU")),
          "mu_ids": mutant_counts["mu_ids"], "n_mo": mutant_counts["MO"],
          "n_total": mutant_counts["total"],
          "mo_missing_evidence_path": mutant_counts["mo_missing_evidence_path"],
          "separation_judged_by_mutant": {x["id"]: x["corroboration_sep_judged"]
                                          for x in mutants},
          "separation_mapped_by_mutant": {x["id"]: x["corroboration_sep_mapped"]
                                          for x in mutants},
          "derived_label_only_leaves": {x["id"]: x["derived_label_only_leaves"]
                                        for x in mutants
                                        if x["derived_label_only_leaves"]}}
    g5 = {"pass": (len(ocr) == PREREG["n_ocr"]
                   and all(r["class"] == "HI" for r in ocr)
                   and len(ocr_triples) >= PREREG["min_ocr_examples"]
                   and all(t["target_unchanged"] for t in ocr_triples)),
          "n_ocr": len(ocr), "n_ocr_hi": sum(1 for r in ocr if r["class"] == "HI"),
          "n_examples": len(ocr_triples),
          "all_mapping_targets_unchanged": all(t["target_unchanged"] for t in ocr_triples)}

    live_after = {f: sha256_file(EVAL / f) for f in MUTANT_ARTIFACTS.values()
                  if (EVAL / f).exists()}
    live_after["injection_map.json"] = sha256_file(DRIFT / "injection_map.json")
    live_after["injected_tables.json"] = sha256_file(DRIFT / "injected_tables.json")
    redline = {
        "frozen_input_digests_match_w2_registration": drift_match,
        "live_and_frozen_artifacts_untouched": live_after == watch,
        "scratch_dir": str(SCRATCH), "scratch_outside_repo": True,
        "m7_preserved_verbatim": True,
        "client_identifier_zero_entered": None}
    g6 = {"pass": bool(scan["clean"] and not PORTS_TOUCHED
                       and not ENDPOINT_VIOLATIONS
                       and guard["all_blocked"]
                       and guard["matcher_apis_all_present"]
                       and all(drift_match.values())
                       and live_after == watch),
          "ports_touched": sorted(PORTS_TOUCHED), "model_calls": 0,
          "budget_counter": 0, "endpoint_violations": ENDPOINT_VIOLATIONS,
          "source_scan_clean": scan["clean"],
          "source_scan_files": scan["files_scanned"],
          "gating_basis": scan["gating_basis"],
          "network_findings_in_d1_scope": scan["network_findings_in_d1_scope"],
          "helper_module": scan["helper_module"],
          "helper_module_ast_findings": scan["helper_module_ast_findings"],
          "helper_module_note": scan["helper_module_note"],
          "socket_import_disclosed": scan["socket_import_disclosed"],
          "active_connection_probes": guard,
          "scope_note": (
              "硬门作用域 = 本窗 research 脚本 + D1 导入的聚合脚本（T2 SCAN_MANIFEST "
              "同构口径）; 生产匹配器自带 OCR/VLM helper 故列作用域外, 其「D1 从未调用」"
              "由三重自证: socket 层封死 + 主动试连全拦 + 所用匹配 API hasattr 断言。")}

    prereg = {
        "P1_equivalence_set_reproduced": g1["pass"],
        "P2_anchor_counts_85_7_26": g2["pass"],
        "P3_equivalent_invisible_all_gamma": g3["pass"],
        "P4_mutant_classification_MU_only_M7": g4["pass"],
        "P5_ocr_all_harmful_invisible_with_examples": g5["pass"],
        "P6_zero_endpoint_self_proof": g6["pass"],
        "note": "预注册于设计稿 §3, 执行后不溯及; 任一项 false 一律上报主线程, "
                "禁止静默重分类或静默改判。"}

    payload = {
        "inputs_sha256": input_files,
        "criterion_provenance": {
            "design_doc": DESIGN_DOC, "task_card": TASK_CARD, "card_id": CARD_ID,
            "blueprint_c1_criterion": "原样引用, 判据冻结不溯及（设计稿 §1）",
            "classification_rules": {
                "H": "锚点 gamma=0.2 检出（单注入边际降幅 dH*10 >= 10*0.2）",
                "E": "被吸收 且 类型属 {alias_variant, mixed_lang, prefix_noise} "
                     "且 映射标准字段集与原表一致（T2 e2_2 冻结定义）",
                "HI": "锚点未检出 且 非等价（按设计意图缺陷成立而协议无信号）",
                "MO": "缺陷在该叶 item 级证据的承载字段上有移动（叶需求所关于的观测变化）",
                "MU": "缺陷只落在派生标签 / 预聚合量, item 级承载字段零移动"},
            "absorption_caliber_note": (
                "设计稿 §2 的 HI 用词「被吸收」按任务卡 P2 的冻结推导口径执行 = "
                "锚点未检出（118-85=33, 33-7=26）。严格映射吸收口径同时入账: "
                "absorbed_strict_total=%d（其 HI 子集 %d）, 余 %d 条为宽表稀释"
                "（dH<0.2 未达阈值但未被吸收）。两口径均写入 counts, 无静默取舍。"
                % (counts["absorbed_strict_total"],
                   counts["hi_by_mechanism"].get("absorption_silent", 0),
                   counts["hi_by_mechanism"].get("threshold_dilution", 0))),
            "independent_rederivation": (
                "注入状态一律从 injection_map.json + injected_tables.json 经生产匹配器"
                "重推; T2 聚合值仅用于 G1/G2 对账。")},
        "injections": injections,
        "counts": counts,
        "equivalence": {
            "definition": "被吸收 且 类型属 {alias_variant, mixed_lang, prefix_noise} "
                          "且 映射标准字段集与原表一致（设计稿 §2 = T2 e2_2 冻结定义）",
            "n_equivalent": len(equiv_rows),
            "by_type": dict(sorted(Counter(r["type"] for r in equiv_rows).items())),
            "equivalent_list": [{"uid": r["uid"], "col": r["col"], "type": r["type"],
                                 "original": r["original"], "injected": r["injected"],
                                 "mapping_target": r["mapping_target"]}
                                for r in equiv_rows],
            "keyset_identical_total": counts["keyset_identical_total"]},
        "gamma_equivalence_check": {
            "claim": "等价注入在全部 gamma 网格不可见（吸收 => 字段集不变 => 无失配信号）",
            "gamma_grid": [str(g) for g in GAMMAS],
            "violations": g3["violations"],
            "per_equivalent": [{"uid_col": "%s:%d" % (r["uid"], r["col"]),
                                "marginal_dH": r["marginal_dH"],
                                "visible_by_gamma": r["visible_by_gamma"]}
                               for r in equiv_rows]},
        "ocr_absorption_examples": {
            "claim": "ocr_similar 13 条全属 HI: 形近误读被编辑距离容差静默接回原字段, "
                     "协议零信号（设计稿 §5 论证骨架的数据支撑）",
            "n_ocr": len(ocr), "n_ocr_HI": g5["n_ocr_hi"],
            "all_targets_unchanged": g5["all_mapping_targets_unchanged"],
            "triples": ocr_triples},
        "mutants": mutants,
        "mutant_counts": mutant_counts,
        "m7_retention": {
            "id": "M7_nf_fail_3", "classification": "MU",
            "original_artifact": "logs/graph/eval/number_faithfulness_report.json",
            "preserved_verbatim": True, "redesigned_or_replaced": False,
            "statement": "M7 原样保留（J2 附加条件）: 不重设计、不替换、不改判其既有结论; "
                         "D1 仅登记其缺陷落在派生标签与聚合计数（pass / n_fail）, "
                         "item 级承载字段 number_claims / ungrounded 零移动, "
                         "故对 item 级判分结构性不可见。",
            "evidence": {
                "mutator": "scripts/eval_checkpoint_discrimination.py:mut_nf_fail",
                "carrier_items_moved": next(
                    sum(v["n_primary_items_moved"]
                        for v in x["item_evidence_view"].values())
                    for x in mutants if x["id"] == "M7_nf_fail_3"),
                "derived_label_items_moved": next(
                    sum(v["n_derived_only_items_moved"]
                        for v in x["item_evidence_view"].values())
                    for x in mutants if x["id"] == "M7_nf_fail_3"),
                "sep_judged": next(x["corroboration_sep_judged"] for x in mutants
                                   if x["id"] == "M7_nf_fail_3"),
                "sep_mapped": next(x["corroboration_sep_mapped"] for x in mutants
                                   if x["id"] == "M7_nf_fail_3"),
                "frozen_finding_ref": "t4_pso_fair_comparison.json:"
                                      "payload.findings.F_W2_1_m7_item_level_invisible"}},
        "gate_details": {"G1_equiv_set_matches_t2_frozen": g1,
                         "G2_anchor_counts_85_7_26": g2,
                         "G3_equivalent_invisible_all_gamma": g3,
                         "G4_mutant_classification_and_evidence_paths": g4,
                         "G5_ocr_all_harmful_invisible_with_examples": g5,
                         "G6_zero_endpoint_and_readonly_self_proof": g6},
        "prereg_predicates": prereg,
        "zero_endpoint": {"patterns": scan["patterns"],
                          "files_scanned": scan["files_scanned"],
                          "missing_files": scan["missing_files"],
                          "gating_basis": scan["gating_basis"],
                          "network_findings_in_d1_scope":
                              scan["network_findings_in_d1_scope"],
                          "endpoint_literal_mentions_advisory":
                              scan["endpoint_literal_mentions_advisory"],
                          "endpoint_literal_note": scan["endpoint_literal_note"],
                          "ports_touched": sorted(PORTS_TOUCHED),
                          "model_calls": 0, "budget_counter": 0,
                          "clean": scan["clean"],
                          "active_connection_probes": guard},
        "redline_self_check": redline}

    doc = {
        "meta": {"name": "d1-mutant-validity-audit", "version": "v1",
                 "card_id": CARD_ID, "task_card": TASK_CARD,
                 "design_doc": DESIGN_DOC,
                 "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 "script": "research/paper_d1_mutant_validity_audit.py",
                 "n_injections": len(injections), "n_mutants": len(mutants),
                 "endpoint_calls": 0, "anchor_gamma": ANCHOR,
                 "gamma_grid": [str(g) for g in GAMMAS],
                 "reproduce": ["python3 research/paper_d1_mutant_validity_audit.py"]},
        "gates": {"G1_equiv_set_matches_t2_frozen": g1["pass"],
                  "G2_anchor_counts_85_7_26": g2["pass"],
                  "G3_equivalent_invisible_all_gamma": g3["pass"],
                  "G4_mutant_classification_and_evidence_paths": g4["pass"],
                  "G5_ocr_all_harmful_invisible_with_examples": g5["pass"],
                  "G6_zero_endpoint_and_readonly_self_proof": g6["pass"],
                  "G7_digest_self_consistency": False},
        "payload": payload,
        "prereg_predicates": prereg}

    # 去标识化扫荡: 先按当前文本判定, 写回 flag 后复扫（不动点校验）
    leaks = client_identifier_scan(
        json.dumps(doc, ensure_ascii=False, sort_keys=True))
    redline["client_identifier_zero_entered"] = not leaks
    leaks2 = client_identifier_scan(
        json.dumps(doc, ensure_ascii=False, sort_keys=True))
    redline["client_identifier_zero_entered"] = not leaks2
    doc["gates"]["G6_zero_endpoint_and_readonly_self_proof"] = bool(
        g6["pass"] and not leaks2)
    doc["prereg_predicates"]["P6_zero_endpoint_self_proof"] = bool(
        g6["pass"] and not leaks2)
    payload["gate_details"]["G6_zero_endpoint_and_readonly_self_proof"]["pass"] = bool(
        g6["pass"] and not leaks2)

    doc["payload_sha256"] = digest_payload(payload)   # payload 收口后才算（W2 f1bf00b）
    doc["sha256_scope"] = list(SHA_SCOPE)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    back = json.loads(OUT.read_text(encoding="utf-8"))
    doc["gates"]["G7_digest_self_consistency"] = (
        digest_payload(back["payload"]) == back["payload_sha256"])
    doc["gates"]["all_pass"] = bool(
        all(x["pass"] for x in (g1, g2, g3, g4, g5))
        and doc["gates"]["G6_zero_endpoint_and_readonly_self_proof"]
        and doc["gates"]["G7_digest_self_consistency"] and not leaks2)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")

    print("counts H/E/HI = %s/%s/%s (total %s)"
          % (counts["H"], counts["E"], counts["HI"], counts["total"]))
    print("absorbed_strict=%s undetected_at_anchor=%s hi_by_mechanism=%s"
          % (counts["absorbed_strict_total"], counts["undetected_at_anchor_total"],
             counts["hi_by_mechanism"]))
    print("equivalent=%s ocr_HI=%s/%s tables=%s"
          % (len(equiv_rows), g5["n_ocr_hi"], g5["n_ocr"], counts["n_tables"]))
    print("mutants MO/MU = %s/%s mu_ids=%s"
          % (mutant_counts["MO"], mutant_counts["MU"], mutant_counts["mu_ids"]))
    print("gates " + json.dumps(doc["gates"], ensure_ascii=False))
    print("client_identifier_leaks=%s" % leaks2)
    print("payload_sha256=%s -> %s" % (doc["payload_sha256"], OUT))
    return 0 if doc["gates"]["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
