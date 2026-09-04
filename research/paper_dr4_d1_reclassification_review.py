#!/usr/bin/env python3
"""DR-4: 按 Step 1 独立 oracle 对 D1 现行三分类做逐实例复核（零端点 / 只读 / 不溯及）。

卡号 TASK-20260901-DR4 | 判据来源: docs/experiments/2026-08-31_d1_autopsy_decision_record.md
    DR-4 重写 + docs/experiments/2026-09-01_expert_consultation_round2_digest.md §5
    任务卡: docs/experiments/2026-09-01_dr4_d1_reclassification_review_card.md

Step 1 oracle（运行前冻结, 判据三条全真才 E=1, 任一不真即 H）:
    C1 算子资格: mutation 属预定义语义等价算子（设计意图 = 不改变标准字段集）;
       ocr_similar / date_variant / unit_suffix 按设计意图即非等价算子;
       prefix_noise 逐实例判「是否只添加装饰而未删除内容」（删除 = 该实例不算等价算子）。
    C2 规范真值映射不变: 独立冻结词表把表头切成 (concepts, restrictors, units) 三多重集,
       变换前后逐等 + 未登录词零差; 取值不变由「数据行零改动」机器事实独立复核。
    C3 下游目标语义不变: 注入后该列在表内仍可唯一指称（无同表同原子集碰撞,
       无「去限定语简称撞上同表同核心概念列」）, 且取值口径未变。

独立性（反循环论证）: 判定路径不 import 生产匹配器 scripts/m1_statement_parser.py,
    不读取任何检测/吸收字段; 由 AST 导入检索 + 字段白名单断言 + 两阶段 sha 冻结链自证。

红线机械护栏（配方沿用 D1）: 零端点 = socket 层封死 + 源码 AST 自扫描 + 主动试连自证;
    只读 = 冻结件前后摘要一致; 去标识 = 甲方标识禁用词扫荡零残留。

复算: venv/bin/python research/paper_dr4_d1_reclassification_review.py
输出: logs/graph/eval/dr4_d1_reclassification_review.json
退出码: 0 = G1/G2 推导门全过; 1 = 任一门失败（停报, 不静默处置）。
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import socket
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
DRIFT_IN = REPO / "data" / "research" / "drift_v0" / "input"
DRIFT_OUT = REPO / "data" / "research" / "drift_v0" / "output"
D1_ART = EVAL / "d1_mutant_validity_audit.json"
T2_ART = EVAL / "t2_visibility_sensitivity.json"
DRIFT_INJECT = "scripts/research/drift_inject.py"
OUT = EVAL / "dr4_d1_reclassification_review.json"
PHASE1_SCRATCH = Path("/tmp/dr4/phase1_oracle_freeze.json")

CARD_ID = "TASK-20260901-DR4"
TASK_CARD = "docs/experiments/2026-09-01_dr4_d1_reclassification_review_card.md"
BASIS_DOCS = ("docs/experiments/2026-08-31_d1_autopsy_decision_record.md",
              "docs/experiments/2026-09-01_expert_consultation_round2_digest.md")

# 现行分类冻结值（G1 复现目标, 判据冻结不溯及）
CURRENT_PREREG = {"H": 85, "E": 7, "HI": 26, "total": 118,
                  "E_by_type": {"alias_variant": 4, "prefix_noise": 3},
                  "D3_harmful_denominator": 111}

# 判定路径禁读字段（absorption / detection 是 outcome, 不是 criterion）
FORBIDDEN_IN_ORACLE = (
    "absorbed", "absorbed_strict", "detected_at_anchor", "visible_by_gamma",
    "absorption_tier", "absorption", "class", "current_class", "equivalent",
    "canonical_keyset_identical", "mapping_target", "target_exists",
    "h_orig", "h_single", "h_full_injection", "marginal_dH", "n_canonical",
    "invisibility_mechanism", "gamma")

PREFIX_TYPE = "prefix_noise"
EQUIV_INTENT_TYPES = ("alias_variant", "mixed_lang")   # 算子设计意图 = 语义等价
NONEQUIV_TYPES = {"ocr_similar": "误读产物（形近错认）, 设计意图即破坏词形",
                  "date_variant": "替换为另一日期参照/绝对年份, 改变了所指",
                  "unit_suffix": "注入/替换计量单位, 改变取值口径"}

SHA_SCOPE = ("inputs_sha256", "criterion_provenance", "lexicon", "integrity",
             "oracle_items", "oracle_counts", "type_label_diversity",
             "current_classification", "diff", "correction_record",
             "d3_sensitivity_note", "tier_sensitivity", "gates",
             "prereg_predicates", "zero_endpoint", "redline_self_check")

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
SELF_SCAN_FILES = ("research/paper_dr4_d1_reclassification_review.py",
                   DRIFT_INJECT)
# 独立性硬门: 生产匹配器（= 被测件）禁止进入判定路径
FORBIDDEN_IMPORTS = ("m1" + "_statement_parser", "scripts.m1_statement_parser")
HTTP_CLIENT_ROOTS = ("url" + "lib", "re" + "quests", "http" + "x", "aio" + "http",
                     "open" + "ai", "htt" + "p", "ftp" + "lib", "smtp" + "lib",
                     "telnet" + "lib", "web" + "socket", "web" + "socket_client",
                     "sub" + "process")
SOCKET_ROOT = "sock" + "et"


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


def ast_findings(rel: str) -> dict:
    """AST 级检索: http 客户端导入/调用 = 端点违规; 生产匹配器导入 = 独立性违规。"""
    tree = ast.parse((REPO / rel).read_text(encoding="utf-8"), filename=rel)
    imported: dict[str, str] = {}
    net: list[dict] = []
    dep: list[dict] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for al in node.names:
                origin = al.asname or al.name
                if origin.split(".")[0] in HTTP_CLIENT_ROOTS:
                    net.append({"kind": "import", "line": node.lineno,
                                "detail": "import " + al.name})
                if any(f in al.name for f in FORBIDDEN_IMPORTS):
                    dep.append({"kind": "import", "line": node.lineno,
                                "detail": "import " + al.name})
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.split(".")[0] in HTTP_CLIENT_ROOTS:
                net.append({"kind": "import_from", "line": node.lineno,
                            "detail": "from " + mod + " import "
                                      + ",".join(a.name for a in node.names)})
            if any(f in mod for f in FORBIDDEN_IMPORTS):
                dep.append({"kind": "import_from", "line": node.lineno,
                            "detail": "from " + mod})
            if mod.split(".")[0] in HTTP_CLIENT_ROOTS:
                for al in node.names:
                    imported[al.asname or al.name] = mod
        elif isinstance(node, ast.Call):
            dotted = _dotted(node.func)
            if not dotted:
                continue
            root = dotted.split(".")[0]
            if root in HTTP_CLIENT_ROOTS:
                net.append({"kind": "call", "line": node.lineno, "detail": dotted})
            elif root in imported:
                net.append({"kind": "call_imported", "line": node.lineno,
                            "detail": dotted + " <- " + imported[root]})
    return {"network": net, "forbidden_dependency": dep}


def self_source_scan() -> dict:
    """分层自扫描: AST 硬门（判 G2）+ 字面量提示层（只披露不判门）+ 独立性检索。"""
    gating: dict[str, list] = {}
    deps: dict[str, list] = {}
    advisory: dict[str, list] = {}
    missing: list[str] = []
    scanned: list[str] = []
    for rel in SELF_SCAN_FILES:
        f = REPO / rel
        if not f.exists():
            missing.append(rel)
            continue
        for i, ln in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            code = ln.split("#", 1)[0]
            if "blocked" in code or "ZERO_ENDPOINT" in code or '"""' in code:
                continue
            for pat in SELF_SCAN_PATTERNS:
                if pat in code:
                    advisory.setdefault(rel, []).append(
                        {"line": i, "pattern": pat, "text": ln.strip()[:120]})
        scanned.append(rel)
        found = ast_findings(rel)
        if found["network"]:
            gating[rel] = found["network"]
        if found["forbidden_dependency"]:
            deps[rel] = found["forbidden_dependency"]
    runtime_loaded = [m for m in sys.modules
                      if any(f in m for f in FORBIDDEN_IMPORTS)]
    return {"patterns": SELF_SCAN_PATTERNS, "files_scanned": scanned,
            "missing_files": missing,
            "gating_basis": ("AST import/call 检索（http 客户端根模块 ∈ "
                             + ",".join(sorted(HTTP_CLIENT_ROOTS))
                             + "）; socket 仅用于封死出站与试连自证, 单列披露"),
            "network_findings": gating,
            "independence_basis": ("生产匹配器 " + "scripts/m1_statement_parser.py"
                                   " = 被测件, 禁止进入判定路径: AST 导入检索 + "
                                   "sys.modules 运行期复核双证"),
            "forbidden_dependency_findings": deps,
            "forbidden_modules_loaded_at_runtime": sorted(runtime_loaded),
            "endpoint_literal_mentions_advisory": advisory,
            "endpoint_literal_note": (
                "字面量层不判门: 命中全部位于中文注释/文档字符串中的否定式声明与"
                "本护栏模式串自身; 逐条披露供人工复核护栏未放水。"),
            "socket_import_disclosed": True,
            "clean": bool(not gating and not missing and not deps
                          and not runtime_loaded)}


def guard_self_test() -> dict:
    """主动试连三次: 必须全部被拦, 否则护栏是空转（D1 同构）。"""
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
    return out


# 逐字沿用 research/paper_w2_e15_full_judge.py 的 CLIENT_TOKENS（甲方标识零进入）
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
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True)
                          .encode("utf-8")).hexdigest()



# ============================================ 独立规范真值映射（阶段 1 唯一语义输入, 运行前冻结）
# 口径（冻结, 三条）:
#   R1 三本位表: 每个表头切成 (concepts, restrictors, units) 三集合 + 未登录原子逐字保留为 residue;
#      四元组全体相等才谈得上「规范真值映射不变」。未登录原子不消费 => 词表覆盖不足只会判 H, 不会造 E。
#   R2 集合（非多重集）口径: 同一概念的中英双语复写（mixed_lang 算子的 assets(资产)）不重复计数;
#      一个表面可同时贡献多个原子（如 收入 兼指 revenue/income）, 只增不减 => 判据只会更严。
#   R3 单形折叠: 未登录的英文 s 结尾原子若其单数形已登录则按单数形取（revenues->revenue, flows->flow）;
#      不规则复数（securities/maturities）显式登记, 不靠折叠。
# 独立性: 本表为 DR-4 自建公共会计术语口径, 不读取生产匹配器 synonym 表, 不读取注入器词库
#      （循环论证防线, 承 docs/experiments/2026-08-31_d1_autopsy_decision_record.md DR-4 重写）。
STOPWORDS = frozenset({"and", "or", "of", "to", "for", "in", "on", "at", "the", "a", "an",
                       "be", "by", "is", "as", "which", "that", "from", "with", "under",
                       "except", "their", "it"})   # 注意: 不含 "per"（per share / per annum = 单位）

_DASH_TRANS = str.maketrans({"–": " ", "—": " ", "‘": " ", "’": " ", "“": " ", "”": " ",
                             "&": " ", "/": " ", "、": " ", "，": " ", "（": " (",
                             "）": ") ", "＋": "+", "＋": "+", "＊": "*"})
_DECOR_GLYPH_RE = re.compile(r"[①②③④⑤⑥⑦⑧⑨⑩№§]+")
_DECOR_BRACKET_RE = re.compile(r"\[\s*\d*\s*\]|【[^A-Za-z0-9一-鿿]*】|〔[^A-Za-z0-9一-鿿]*〕")
_FOOTNOTE_RE = re.compile(r"\(\s*(?:\d{1,2}|[a-z]{1,2}|\*{1,3}|excluding[^)]*)\)", re.I)
_LEADING_INDEX_RE = re.compile(r"(?<![\w])\d{1,3}\s*[.、]\s*")
_TRAIL_MARK_RE = re.compile(r"[\*#]+$")
_TOKEN_RE = re.compile(r"[a-z]+|[0-9]+|[一-鿿]|[£$€¥%]")


def clean_text(text: object) -> str:
    """装饰/脚注标记剥离, 但保留承载内容的括号内文。

    剥离: 圈号①№§ / 空方括号【】〔〕 / [数字] / 纯标记括号 (1)(*) (a)/(excluding ...) /
          前导序号 "1." / 尾部 */# / 连字符与破折号转空格。
    保留: (current) (long-term) (per annum) (NT dollars) (in millions) (pre-spectrum) 等内容括号,
          以及数字原子（31 -> 3① 的数字丢失必须由 residue 差异暴露）。
    """
    s = str(text if text is not None else "").strip().lower()
    s = s.translate(_DASH_TRANS)
    s = _DECOR_BRACKET_RE.sub(" ", s)
    s = _DECOR_GLYPH_RE.sub(" ", s)
    s = _FOOTNOTE_RE.sub(" ", s)
    s = _LEADING_INDEX_RE.sub(" ", s)
    s = _TRAIL_MARK_RE.sub(" ", s)
    s = re.sub(r"[^a-z0-9%£€¥$一-鿿() ]+", " ", s)
    s = s.replace("(", " ").replace(")", " ")
    return re.sub(r"\s+", " ", s).strip()


def atoms_of(text: object) -> list[str]:
    """确定性原子流: 英文词 / 数字串 / 单个汉字 / 货币百分号 各自成原子。"""
    return _TOKEN_RE.findall(clean_text(text))


def seg_key(atoms: list[str]) -> str:
    """原子流 -> 词表键（CJK 连续字直连, 其余空格分词）。"""
    out = ""
    for a in atoms:
        if not out:
            out = a
        elif len(a) == 1 and "一" <= a <= "鿿" and out[-1] and "一" <= out[-1] <= "鿿":
            out += a
        else:
            out += " " + a
    return out


LEX: dict[str, tuple[frozenset[str], frozenset[str], frozenset[str]]] = {}
LEX_NOTE: dict[str, str] = {}
LEX_CONFLICTS: list[dict] = []


def _add(surface: str, concepts: tuple[str, ...] = (), restrictors: tuple[str, ...] = (),
         units: tuple[str, ...] = (), note: str = "") -> None:
    key = seg_key(atoms_of(surface))
    c, r, u = (frozenset(concepts), frozenset(restrictors), frozenset(units))
    assert key and (c or r or u), surface
    cur = LEX.get(key)
    if cur:
        if (c and cur[1]) or (r and cur[0]) or (u and cur[0]) or (u and cur[1]):
            LEX_CONFLICTS.append({"surface": surface, "existing": sorted(map(str, cur)),
                                  "incoming": [sorted(c), sorted(r), sorted(u)]})
        LEX[key] = (cur[0] | c, cur[1] | r, cur[2] | u)
    else:
        LEX[key] = (c, r, u)
    if note:
        LEX_NOTE[key] = note


def _reg(surface: str, canon: str, kind: str = "c", note: str = "") -> None:
    """kind: c=概念 r=限定语 u=单位。"""
    _add(surface, (canon,) if kind == "c" else (), (canon,) if kind == "r" else (),
         (canon,) if kind == "u" else (), note)


# ---- 概念（含「概念+限定语」复合表面: 复合表面必须携带限定语, 禁止把限定语吞进单一概念）
for _s in ("revenue", "revenues", "sales", "sale", "turnover"):
    _reg(_s, "REVENUE")
_add("营业收入", ("REVENUE",), ("OPERATING",), ())
_add("营业总收入", ("REVENUE",), ("OPERATING", "TOTAL"), ())
_add("营收", ("REVENUE",), ("OPERATING",), ())
_add("收入", ("INCOME", "REVENUE"), (), (),
     "公共口径: 准则名「收入」= revenue, 其他收益/收益亦译 income => 双原子登记（只增不减, 判据更严）")
_reg("receipts", "RECEIPTS")
_add("收款", ("RECEIPTS",), (), ())
_add("账户", ("ACCOUNT",), (), ())
_add("帐号", ("ACCOUNT_NUMBER",), (), ())
_add("账号", ("ACCOUNT_NUMBER",), (), ())
_reg("资产", "ASSET")
_add("资产总额", ("ASSET",), ("TOTAL",), ())
_add("负债总额", ("LIABILITY",), ("TOTAL",), ())
_reg("摊薄", "DILUTION")
_add("现金流量", ("CASH_FLOW",), (), ())
_add("现金流", ("CASH_FLOW",), (), ())
_add("利息", ("INTEREST",), (), ())
_add("股息", ("DIVIDEND",), (), ())
_add("股利", ("DIVIDEND",), ())
_add("交易日", ("TRADE_DATE",), (), ())
_add("净值日期", ("NAV_DATE",), (), ())
_add("对账日期", ("RECON_DATE",), (), ())
_add("期末日期", ("PERIOD_END",), (), ())
_add("报表明细日期", ("REPORT_DETAIL_DATE",), ())
_add("万元", (), (), ("CNY_WAN",))
_add("亿元", (), (), ("CNY_YI",))
_add("元", (), (), ("CNY",))
_add("手", (), (), ("LOTS",))
_add("股", ("SHARE",), (), ())
_add("份额", ("SHARE",), (), ())
_add("市值", ("MARKET_VALUE",), (), ())
_add("收盘价", ("CLOSING_PRICE",), (), ())
_add("成交量", ("TRADING_VOLUME",), (), ())
_add("交易量", ("TRADING_VOLUME",), ())
_add("权益", ("EQUITY",), ())
_add("负债", ("LIABILITY",), ())
_add("费用", ("EXPENSE",), ())
_add("支出", ("EXPENSE",), ())
_add("率", ("RATE",), ())
_add("期间", ("PERIOD",), ())
_add("分部", ("SEGMENT",), ())
_add("税", ("TAX",), ())
_add("利润", ("PROFIT",), ())
_add("净利润", ("INCOME",), ("NET",))
_add("股票", ("STOCK",), ())
_add("日期", ("DATE",), ())

# ---- 英文概念（单原子与复合表面）
for _s in ("receipts", "income", "profit", "profits", "loss", "losses", "gain", "gains",
           "cash", "assets", "asset", "liabilities", "liability", "equity", "capital",
           "amortization", "amort", "depreciation", "interest", "dividend", "dividends",
           "account", "accounts", "accounting", "price", "prices", "volume", "open",
           "closing", "maturities", "maturity", "date", "dates", "dated", "year",
           "lease", "leases", "expense", "expenses", "expenditures", "expenditure",
           "percentage", "percent", "number", "rate", "rates", "period", "periods",
           "share", "shares", "stock", "option", "options", "award", "awards",
           "value", "values", "guidance", "statement", "summary", "performance",
           "goal", "recognition", "segment", "plan", "plans", "securities", "security",
           "tax", "taxes", "benefit", "benefits", "impact", "subsidy", "medicare",
           "vessel", "vessels", "equipment", "plant", "property", "office",
           "operations", "operation", "issuance", "additions", "addition",
           "allocation", "group", "partners", "repurchases", "repurchase",
           "consolidated", "consolidate", "cost", "hedge", "hedges", "compensation",
           "grant", "exercise", "expiry", "provision", "provisions"):
    _reg(_s, {"receipts": "RECEIPTS", "income": "INCOME", "profit": "PROFIT",
              "profits": "PROFIT", "loss": "LOSS", "losses": "LOSS", "gain": "GAIN",
              "gains": "GAIN", "cash": "CASH", "assets": "ASSET", "asset": "ASSET",
              "liabilities": "LIABILITY", "liability": "LIABILITY", "equity": "EQUITY",
              "capital": "CAPITAL", "amortization": "AMORTIZATION",
              "amort": "AMORTIZATION", "depreciation": "DEPRECIATION",
              "interest": "INTEREST", "dividend": "DIVIDEND",
              "dividends": "DIVIDEND", "account": "ACCOUNT", "accounts": "ACCOUNT",
              "accounting": "ACCOUNTING", "price": "PRICE", "prices": "PRICE",
              "volume": "TRADING_VOLUME", "open": "OPEN_PRICE",
              "closing": "CLOSING_PRICE", "maturities": "MATURITY",
              "maturity": "MATURITY", "date": "DATE", "dates": "DATE",
              "dated": "DATE", "year": "YEAR", "lease": "LEASE", "leases": "LEASE",
              "expense": "EXPENSE", "expenses": "EXPENSE",
              "expenditures": "EXPENSE", "expenditure": "EXPENSE",
              "percentage": "PERCENTAGE", "percent": "PERCENTAGE",
              "number": "COUNT", "rate": "RATE", "rates": "RATE",
              "period": "PERIOD", "periods": "PERIOD", "share": "SHARE",
              "shares": "SHARE", "stock": "STOCK", "option": "OPTION",
              "options": "OPTION", "award": "AWARD", "awards": "AWARD",
              "value": "VALUE", "values": "VALUE", "guidance": "GUIDANCE",
              "statement": "STATEMENT", "summary": "SUMMARY",
              "performance": "PERFORMANCE", "goal": "GOAL",
              "recognition": "RECOGNITION", "segment": "SEGMENT", "plan": "PLAN",
              "plans": "PLAN", "securities": "SECURITY", "security": "SECURITY",
              "tax": "TAX", "taxes": "TAX", "benefit": "BENEFIT",
              "benefits": "BENEFIT", "impact": "IMPACT", "subsidy": "SUBSIDY",
              "medicare": "MEDICARE", "vessel": "VESSEL", "vessels": "VESSEL",
              "equipment": "EQUIPMENT", "plant": "PLANT", "property": "PROPERTY",
              "office": "OFFICE", "operations": "OPERATION",
              "operation": "OPERATION", "issuance": "ISSUANCE",
              "additions": "ADDITION", "addition": "ADDITION",
              "allocation": "ALLOCATION", "group": "GROUP",
              "partners": "PARTNER", "repurchases": "REPURCHASE",
              "repurchase": "REPURCHASE", "consolidated": "CONSOLIDATION",
              "consolidate": "CONSOLIDATION", "cost": "COST", "hedge": "HEDGE",
              "hedges": "HEDGE", "compensation": "COMPENSATION",
              "grant": "GRANT", "exercise": "EXERCISE", "expiry": "EXPIRY",
              "provision": "PROVISION", "provisions": "PROVISION"}[_s])

# ---- 复合概念表面（不得吞限定语: net income / gross profit / total assets 一律拆）
_add("cash flow", ("CASH_FLOW",), (), ())
_add("cash flows", ("CASH_FLOW",), (), ())
_add("cashflow", ("CASH_FLOW",), (), ())
_add("market value", ("MARKET_VALUE",), (), ())
_add("market cap", ("MARKET_VALUE",), (), ())
_add("market capitalization", ("MARKET_VALUE",), (), ())
_add("fair value", ("FAIR_VALUE",), (), ())
_add("closing price", ("CLOSING_PRICE",), ())
_add("open price", ("OPEN_PRICE",), ())
_add("trading volume", ("TRADING_VOLUME",), ())
_add("trade date", ("TRADE_DATE",), ())
_add("balance sheet", ("BALANCE_SHEET",), ())
_add("account no", ("ACCOUNT_NUMBER",), ())
_add("account number", ("ACCOUNT_NUMBER",), ())
_add("part d", ("PART_D",), ())
_add("dry docking", ("DRY_DOCKING",), ())
_add("interest income", ("INTEREST", "INCOME"), (), ())

# ---- 限定语
for _s, _c in [("accumulated", "ACCUMULATED"), ("net", "NET"), ("gross", "GROSS"),
               ("total", "TOTAL"), ("总额", "TOTAL"), ("总", "TOTAL"),
               ("deferred", "DEFERRED"), ("unearned", "UNEARNED"), ("free", "FREE"),
               ("contractual", "CONTRACTUAL"), ("right of use", "RIGHT_OF_USE"),
               ("intangible", "INTANGIBLE"), ("tangible", "TANGIBLE"),
               ("fixed", "FIXED"), ("floating", "FLOATING"), ("purchased", "PURCHASED"),
               ("long lived", "LONG_LIVED"), ("long term", "LONG_TERM"),
               ("current", "CURRENT"), ("financial", "FINANCIAL"),
               ("weighted average", "WEIGHTED_AVERAGE"), ("fair", "FAIR"),
               ("associated", "ASSOCIATED"), ("remaining", "REMAINING"),
               ("other", "OTHER"), ("common", "COMMON"), ("paid", "PAID"),
               ("positive", "POSITIVE"), ("negative", "NEGATIVE"),
               ("expected", "EXPECTED"), ("unrealised", "UNREALISED"),
               ("unrealized", "UNREALISED"), ("capitalized", "CAPITALIZED"),
               ("comprehensive", "COMPREHENSIVE"), ("settled", "SETTLED"),
               ("available", "AVAILABLE"), ("future", "FUTURE"),
               ("assumed", "ASSUMED"), ("acquired", "ACQUIRED"),
               ("charged", "CHARGED"), ("pre spectrum", "PRE_SPECTRUM"),
               ("own", "OWN"), ("adjusted", "ADJUSTED"), ("operating", "OPERATING"),
               ("营业", "OPERATING"), ("receivable", "RECEIVABLE"),
               ("ended", "ENDED"), ("restated", "RESTATED")]:
    _reg(_s, _c, "r")

# ---- 单位 / 量纲
for _s, _c in [("per share", "PER_SHARE"), ("per common share", "PER_SHARE"),
               ("per annum", "PER_ANNUM"), ("in millions", "MILLIONS"),
               ("millions", "MILLIONS"), ("m", "MILLIONS"), ("thousands", "THOUSANDS"),
               ("nt dollars", "TWD"), ("dollars", "DOLLAR"), ("£", "GBP"), ("$", "USD"),
               ("€", "EUR"), ("¥", "CNY_SIGN"), ("%", "PERCENT_BASE")]:
    _reg(_s, _c, "u")

MAX_SEG = max(len(atoms_of(k)) for k in LEX)
LEX_FIRST_ATOMS = frozenset(atoms_of(k)[0] for k in LEX)

LEX_ALL_ATOMS = frozenset(a for k in LEX for a in atoms_of(k))


def fold_plurals(atoms: list[str]) -> list[str]:
    """R3 单形折叠（仅对已登录词形生效, 未登录 OCR 残片不折叠 -> 落 residue 暴露）。"""
    out: list[str] = []
    for a in atoms:
        if a in LEX_ALL_ATOMS or not a.isascii() or not a.isalpha():
            out.append(a)
        elif a.endswith("s") and a[:-1] in LEX_ALL_ATOMS:
            out.append(a[:-1])
        else:
            out.append(a)
    return out


def decompose(text: object) -> dict:
    """表头 -> 冻结三本位签名（贪游最长匹配, 未登录原子逐字保留）。"""
    atoms = fold_plurals(atoms_of(text))
    concepts: set[str] = set()
    restrictors: set[str] = set()
    units: set[str] = set()
    residue: set[str] = set()
    spans: list[str] = []
    i = 0
    while i < len(atoms):
        hit = None
        for ln in range(min(MAX_SEG, len(atoms) - i), 1, -1):
            cand = seg_key(atoms[i:i + ln])
            if cand in LEX:
                hit = (ln, cand)
                break
        if hit is None and seg_key(atoms[i:i + 1]) in LEX:
            hit = (1, seg_key(atoms[i:i + 1]))
        if hit:
            ln, cand = hit
            c, r, u = LEX[cand]
            concepts |= c
            restrictors |= r
            units |= u
            spans.append(cand)
            i += ln
        else:
            if atoms[i] not in STOPWORDS:
                residue.add(atoms[i])
            i += 1
    assert not ("" in concepts or "" in restrictors or "" in units), text
    return {"concepts": frozenset(concepts), "restrictors": frozenset(restrictors),
            "units": frozenset(units), "residue": frozenset(residue),
            "spans": tuple(spans), "atoms": tuple(atoms)}


def signature(text: object) -> tuple:
    d = decompose(text)
    return (tuple(sorted(d["concepts"])), tuple(sorted(d["restrictors"])),
            tuple(sorted(d["units"])), tuple(sorted(d["residue"])))


# =========================================================== Step 1 判据（C1/C2/C3, 逐实例）
def c1_operator_eligibility(entry: dict) -> dict:
    """C1 算子资格: 设计意图 = 不改变标准字段集的等价算子族; prefix_noise 逐实例验「只加不减」。

    输入只允许 mutation 定义（original/injected/type/variant）+ 冻结族口径; 禁止检测/吸收字段。
    """
    t = str(entry.get("type"))
    if t in NONEQUIV_TYPES:
        return {"pass": False, "family": t, "check": "family_design_intent",
                "reason": NONEQUIV_TYPES[t]}
    if t not in EQUIV_INTENT_TYPES and t != PREFIX_TYPE:
        return {"pass": False, "family": t, "check": "family_undocumented",
                "reason": "算子族不在冻结资格表内"}
    if t == PREFIX_TYPE:
        before = Counter(atoms_of(entry.get("original")))
        after = Counter(atoms_of(entry.get("injected")))
        lost = sorted((before - after).elements())
        added = sorted((after - before).elements())
        return {"pass": not lost, "family": t, "check": "additive_only(C1b)",
                "decorator_variant": entry.get("variant"),
                "content_lost": lost, "noise_added": added,
                "reason": ("仅追加装饰噪声, 原内容零丢失" if not lost else
                           "装饰化过程删除了原内容原子 => 该实例不是等价算子")}
    return {"pass": True, "family": t, "check": "family_design_intent",
            "reason": "算子设计意图 = 同一标准字段集的另一种写法（同义别名/中英混写）"}


def c2_canonical_truth(entry: dict, value_fact: dict) -> dict:
    """C2 独立规范真值映射不变: 冻结词表四元组全体相等 + 取值不变由数据行零改动独立复核。"""
    o = decompose(entry.get("original"))
    i = decompose(entry.get("injected"))
    dims = ("concepts", "restrictors", "units", "residue")
    lost = {d: sorted(set(o[d]) - set(i[d])) for d in dims}
    gained = {d: sorted(set(i[d]) - set(o[d])) for d in dims}
    clean = all(not lost[d] and not gained[d] for d in dims)
    return {"pass": bool(clean and value_fact["holds"]),
            "canonical_before": {d: sorted(o[d]) for d in dims},
            "canonical_after": {d: sorted(i[d]) for d in dims},
            "truth_lost": {d: v for d, v in lost.items() if v},
            "truth_added": {d: v for d, v in gained.items() if v},
            "value_invariance": value_fact,
            "reason": ("标准字段真值（概念/限定语/单位/未登录原子）逐等且取值不变"
                       if clean and value_fact["holds"] else
                       "规范真值映射发生变化: " + "; ".join(
                           f"{d}-" + "/".join(v)
                           for d, v in list(lost.items()) + list(gained.items()) if v))}


def _norm_atoms(text: object) -> tuple:
    return tuple(atoms_of(text))


def c3_downstream_semantics(entry: dict, orig_header: list, value_fact: dict) -> dict:
    """C3 下游目标语义不变: 逐实例隔离（只替换本列）后, 该列在表内仍可唯一指称。

    (a) 无同表表头原子序列完全重复; (b) 无同表列共享任一标准概念（共享 = 简称无法唯一指称
        或与邻列互相吞噬）; (c) 取值/目标列不变由逐实例隔离事实承担。
    """
    col = int(entry["col"])
    pseudo = ["" if h is None else str(h) for h in orig_header]
    pseudo[col] = str(entry["injected"])
    mine = _norm_atoms(entry["injected"])
    my_sig = decompose(entry["injected"])
    dup_exact: list[dict] = []
    collide: list[dict] = []
    for j, cell in enumerate(pseudo):
        if j == col or not str(cell).strip():
            continue
        if mine and _norm_atoms(cell) == mine:
            dup_exact.append({"col": j, "header": str(cell)[:120]})
        shared = my_sig["concepts"] & decompose(cell)["concepts"]
        if shared:
            collide.append({"col": j, "header": str(cell)[:120],
                            "shared_concepts": sorted(shared)})
    ok = not dup_exact and not collide and value_fact["holds"]
    return {"pass": bool(ok), "sibling_columns": len(pseudo) - 1,
            "exact_duplicate_headers": dup_exact, "concept_collisions": collide,
            "value_and_target_unchanged": value_fact,
            "reason": ("注入后该列在表内仍唯一指称同一目标, 取值口径未变" if ok else
                       "存在同表指称冲突: " + (
                           "表头原子序列重复 " + json.dumps(dup_exact, ensure_ascii=False)
                           if dup_exact else "") + (
                           " 邻列共享概念 " + json.dumps(collide, ensure_ascii=False)
                           if collide else "") + (
                           " 取值/目标发生变化" if not value_fact["holds"] else ""))}


# 敏感性变体（次口径, 不改主判据）: 限定语差异从 C2 移出, 唯一指称并入 C3
def c2_lenient(entry: dict, value_fact: dict) -> dict:
    o, i = decompose(entry["original"]), decompose(entry["injected"])
    dims = ("concepts", "units", "residue")
    diff = {d: sorted(set(o[d]) ^ set(i[d])) for d in dims}
    restrictor_only = sorted(set(o["restrictors"]) ^ set(i["restrictors"]))
    ok = all(not v for v in diff.values()) and value_fact["holds"]
    return {"pass": bool(ok), "diff_outside_restrictors": {d: v for d, v in diff.items() if v},
            "restrictor_delta": restrictor_only, "value_invariance": value_fact}


def c3_lenient(entry: dict, orig_header: list, value_fact: dict) -> dict:
    col = int(entry["col"])
    pseudo = ["" if h is None else str(h) for h in orig_header]
    pseudo[col] = str(entry["injected"])
    mine = decompose(entry["injected"])
    rivals = []
    for j, cell in enumerate(pseudo):
        if j == col or not str(cell).strip():
            continue
        if mine["concepts"] & decompose(cell)["concepts"]:
            rivals.append({"col": j, "header": str(cell)[:120]})
    return {"pass": bool(not rivals and value_fact["holds"]),
            "competing_columns": rivals, "value_fact": value_fact}


# ================================================ 阶段 1: 冻结 oracle（不读任何检测/吸收结果）
def phase1_oracle(inj_map: list, orig_tables: dict, inj_tables: dict) -> list[dict]:
    """逐实例判定: 输入 = mutation 定义 + 冻结词表 + 表上下文; 输出 = 三项判据证据 + 标签。"""
    rows: list[dict] = []
    for e in sorted(inj_map, key=lambda x: (str(x["uid"]), int(x["col"]))):
        uid, col = str(e["uid"]), int(e["col"])
        orig_tbl = orig_tables[uid]
        inj_tbl = inj_tables[uid]
        orig_header = ["" if c is None else str(c) for c in orig_tbl[0]]
        inj_header = ["" if c is None else str(c) for c in inj_tbl[0]]
        injected_cols = {int(x["col"]) for x in inj_map if str(x["uid"]) == uid}
        header_delta = ([j for j in range(len(orig_header)) if orig_header[j] != inj_header[j]]
                        if len(orig_header) == len(inj_header) else [-1])
        rows_identical = ([list(map(str, r)) for r in orig_tbl[1:]]
                          == [list(map(str, r)) for r in inj_tbl[1:]])
        value_fact = {
            "holds": bool(str(orig_header[col]) == str(e["original"])
                          and str(inj_header[col]) == str(e["injected"])
                          and rows_identical
                          and all(j in injected_cols for j in header_delta)),
            "data_rows_identical": rows_identical,
            "header_cells_changed": header_delta,
            "cells_touched_only_within_injection_set":
                all(j in injected_cols for j in header_delta)}
        C1 = c1_operator_eligibility(e)
        C2 = c2_canonical_truth(e, value_fact)
        C3 = c3_downstream_semantics(e, orig_header, value_fact)
        lenient_c2 = c2_lenient(e, value_fact)
        lenient_c3 = c3_lenient(e, orig_header, value_fact)
        rows.append({"uid": uid, "col": col, "type": str(e["type"]),
                     "variant": str(e.get("variant")), "operator": str(e.get("source_key")),
                     "original": str(e["original"]), "injected": str(e["injected"]),
                     "C1_operator": C1, "C2_canonical_truth": C2,
                     "C3_downstream": C3,
                     "oracle_label": ("E" if (C1["pass"] and C2["pass"] and C3["pass"]) else "H"),
                     "lenient": {"C1_pass": C1["pass"], "C2": lenient_c2, "C3": lenient_c3,
                                 "label": ("E" if (C1["pass"] and lenient_c2["pass"]
                                                   and lenient_c3["pass"]) else "H")}})
    return rows


def assert_oracle_independent(rows: list[dict]) -> dict:
    """阶段 1 产物键名必须不含任何检测/吸收字段（独立性硬自证）。"""
    bad: list[str] = []

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                if str(k) in FORBIDDEN_IN_ORACLE:
                    bad.append(path + "/" + str(k))
                walk(v, path + "/" + str(k))
        elif isinstance(node, list):
            for n, v in enumerate(node[:3]):
                walk(v, path + "[%d]" % n)
    for r in rows:
        walk(r, "$")
    loaded = [m for m in sys.modules if any(f in m for f in FORBIDDEN_IMPORTS)]
    return {"forbidden_keys_in_oracle": sorted(set(bad)),
            "forbidden_modules_loaded": sorted(loaded),
            "pass": bool(not bad and not loaded)}


# ============================================ 阶段 2: 现行分类复现 -> 与 oracle 逐实例 diff
D1_EQUIV_TYPES = ("alias_variant", "mixed_lang", PREFIX_TYPE)
CURRENT_RULE = ("D1 冻结推导口径: class = H 若 detected_at_anchor(γ=0.2); 否则 E 若 "
                "type ∈ {alias_variant, mixed_lang, prefix_noise} 且 "
                "canonical_keyset_identical; 否则 HI（机制 = absorbed_strict ? "
                "absorption_silent : threshold_dilution）。本卡只用它复现「现行分类」, "
                "禁止进入阶段 1 判据路径。")


def ck(uid: object, col: object) -> str:
    return f"{uid}#{col}"


def reproduce_current(d1_items: list[dict]) -> list[dict]:
    rows = []
    for r in d1_items:
        if r.get("detected_at_anchor"):
            cls = "H"
        elif str(r.get("type")) in D1_EQUIV_TYPES and r.get("canonical_keyset_identical"):
            cls = "E"
        else:
            cls = "HI"
        rows.append({"key": ck(r["uid"], r["col"]), "uid": str(r["uid"]),
                     "col": int(r["col"]), "type": str(r["type"]),
                     "original": str(r["original"]), "injected": str(r["injected"]),
                     "reproduced_class": cls, "stored_class": str(r.get("class")),
                     "match": cls == str(r.get("class")),
                     "canonical_keyset_identical": bool(r.get("canonical_keyset_identical")),
                     "invisibility_mechanism": r.get("invisibility_mechanism")})
    return rows


def build_diff(oracle_rows: list[dict], current_rows: list[dict]) -> dict:
    cur = {r["key"]: r for r in current_rows}
    changes, stable = [], []
    for o in oracle_rows:
        c = cur[ck(o["uid"], o["col"])]
        # 可比口径: 现行三分类里 H 与 HI 同属「有害」分区, oracle 只出 E/H 二值
        cur_partition = "E" if c["reproduced_class"] == "E" else "HARMFUL"
        oracle_partition = "E" if o["oracle_label"] == "E" else "HARMFUL"
        entry = {"key": ck(o["uid"], o["col"]), "uid8": o["uid"][:8], "col": o["col"],
                 "type": o["type"], "original": o["original"],
                 "injected": o["injected"],
                 "current_class": c["reproduced_class"],
                 "oracle_label": oracle_partition,
                 "changed": cur_partition != oracle_partition}
        if entry["changed"]:
            entry["direction"] = f"{c['reproduced_class']}->{o['oracle_label']}"
            entry["mechanism"] = {
                "C1": {k: v for k, v in o["C1_operator"].items() if k != "pass"},
                "C2_lost": o["C2_canonical_truth"].get("truth_lost", {}),
                "C2_added": o["C2_canonical_truth"].get("truth_added", {}),
                "C3": {k: v for k, v in o["C3_downstream"].items()
                       if k in ("exact_duplicate_headers", "concept_collisions", "reason")}}
            entry["evidence_criterion_first_fail"] = next(
                (n for n, d in (("C1_operator", o["C1_operator"]),
                                ("C2_canonical_truth", o["C2_canonical_truth"]),
                                ("C3_downstream", o["C3_downstream"]))
                 if not d["pass"]), "none_failed")
            changes.append(entry)
        else:
            stable.append(entry)
    return {"n_reviewed": len(oracle_rows), "n_changed": len(changes),
            "n_stable": len(stable),
            "current_e_to_oracle_h": [x for x in changes if x["current_class"] == "E"],
            "current_harmful_to_oracle_e": [x for x in changes if x["oracle_label"] == "E"],
            "changes": changes, "stable": stable}


def injector_lexicon_membership(inj_map: list[dict]) -> dict:
    """G4 用: 逐实例 mutation 定义确实可取（每条 (source_key,variant) 落在算子词库内）。

    注入器词库仅用于「mutation 定义存在性」对账, 不作为 C1/C2/C3 的语义输入。
    """
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("drift_inject_ro", REPO / DRIFT_INJECT)
        mod = importlib.util.module_from_spec(spec)          # type: ignore[arg-type]
        spec.loader.exec_module(mod)                          # type: ignore[union-attr]
    except Exception as exc:
        return {"available": False, "error": type(exc).__name__ + ": " + str(exc)[:160]}
    key_sets = {"alias_variant": getattr(mod, "ALIAS_VARIANTS", {}),
                "mixed_lang": getattr(mod, "MIXED_LANG_VARIANTS", {}),
                "unit_suffix": getattr(mod, "UNIT_SUFFIX_VARIANTS", {})}
    ocr_pairs = [tuple(x[:2]) for x in getattr(mod, "OCR_SIMILAR_PAIRS", [])]
    date_sem = getattr(mod, "DATE_VARIANT_SEMANTICS", {})
    decos = [d[0] for d in getattr(mod, "PREFIX_NOISE_DECORATORS", [])]
    misses = []
    for e in inj_map:
        t, k, v = str(e["type"]), str(e.get("source_key")), str(e.get("variant"))
        if t in key_sets:
            if k not in key_sets[t] or v not in key_sets[t][k]:
                misses.append({"type": t, "source_key": k, "variant": v})
        elif t == "ocr_similar":
            if not any(p == k and r == v for p, r in ocr_pairs):
                misses.append({"type": t, "source_key": k, "variant": v})
        elif t == "date_variant":
            sem = v.split("/")[0] if "/" in v else v
            if sem not in date_sem:
                misses.append({"type": t, "source_key": k, "variant": v})
        elif t == PREFIX_TYPE:
            if v not in decos:
                misses.append({"type": t, "source_key": k, "variant": v})
    return {"available": True, "n_checked": len(inj_map), "n_miss": len(misses),
            "misses": misses[:20],
            "note": "mutation 定义可取性核对（P2 证伪门）; 词库内容不进入判据路径"}


def integrity_scan(inj_map: list, orig_tables: dict, inj_tables: dict,
                   d1_items: list) -> dict:
    bad_orig = [ck(e["uid"], e["col"]) for e in inj_map
                if str(orig_tables[str(e["uid"])][0][int(e["col"])]) != str(e["original"])]
    bad_inj = [ck(e["uid"], e["col"]) for e in inj_map
               if str(inj_tables[str(e["uid"])][0][int(e["col"])]) != str(e["injected"])]
    changed = [u for u, t in orig_tables.items()
               if [list(map(str, r)) for r in t[1:]]
               != [list(map(str, r)) for r in inj_tables[u][1:]]]
    keys_map = {ck(e["uid"], e["col"]) for e in inj_map}
    keys_d1 = {ck(r["uid"], r["col"]) for r in d1_items}
    return {"n_injections_map": len(inj_map), "n_d1_items": len(d1_items),
            "n_tables": len(orig_tables), "unique_keys_map": len(keys_map),
            "map_d1_keyset_identical": keys_map == keys_d1,
            "map_d1_keys_only_in_map": sorted(keys_map - keys_d1)[:5],
            "map_d1_keys_only_in_d1": sorted(keys_d1 - keys_map)[:5],
            "original_text_mismatch": bad_orig[:5], "n_original_mismatch": len(bad_orig),
            "injected_text_mismatch": bad_inj[:5], "n_injected_mismatch": len(bad_inj),
            "tables_with_non_header_row_change": changed[:5],
            "n_tables_with_value_change": len(changed),
            "value_invariance_is_machine_fact": not changed,
            "mutation_definitions": injector_lexicon_membership(inj_map),
            "enumerated_five_instances": [
                {"key": ck(e["uid"], e["col"]), "type": e["type"],
                 "source_key": e.get("source_key"), "variant": e.get("variant"),
                 "original": str(e["original"])[:60], "injected": str(e["injected"])[:60]}
                for e in inj_map[::max(1, len(inj_map) // 5)][:5]]}


def lexicon_stats(inj_map: list) -> dict:
    """词表规模 + 未登录原子全量披露（覆盖缺口 = 保守偏 H, 不可能造 E）。"""
    residue: Counter = Counter()
    n_atoms = 0
    for e in inj_map:
        for side in ("original", "injected"):
            d = decompose(e[side])
            n_atoms += len(d["atoms"])
            residue.update(d["residue"])
    return {"n_surfaces": len(LEX),
            "n_concepts": len({c for v in LEX.values() for c in v[0]}),
            "n_restrictors": len({c for v in LEX.values() for c in v[1]}),
            "n_units": len({c for v in LEX.values() for c in v[2]}),
            "max_segment_atoms": MAX_SEG,
            "registration_conflicts": LEX_CONFLICTS,
            "documented_rulings": LEX_NOTE,
            "n_atoms_scanned_118_pairs": n_atoms,
            "residue_atoms_across_118_pairs": dict(sorted(residue.items(),
                                                          key=lambda x: (-x[1], x[0]))),
            "n_distinct_residue_atoms": len(residue),
            "residue_occurrences": sum(residue.values()),
            "residue_note": ("未登录原子逐字保留并纳入相等性判定 => 词表覆盖缺口只会把实例"
                             "推向 H, 不会凭空造 E; 此处全量披露供人工复核。")}

# ================================================================ 摘要快照 / 写入追踪
WRITTEN_PATHS: list[str] = []
SNAPSHOT_FILES = (D1_ART, T2_ART, DRIFT_OUT / "injection_map.json",
                  DRIFT_OUT / "injected_tables.json", DRIFT_IN / "tatqa_tables.json",
                  REPO / TASK_CARD,
                  REPO / "docs/experiments/2026-08-31_d1_audit_report.md",
                  REPO / "research/paper_dr4_d1_reclassification_review.py")


def sha_entry(path: Path) -> dict:
    raw = path.read_bytes()
    out = {"bytes": len(raw), "raw": hashlib.sha256(raw).hexdigest()}
    lf = raw.replace(b"\r\n", b"\n")
    if lf != raw:
        out["lf"] = hashlib.sha256(lf).hexdigest()
    return out


def sha_snapshot() -> dict:
    return {str(p.relative_to(REPO)) if p.is_absolute() and str(p).startswith(str(REPO))
            else str(p): sha_entry(p) for p in SNAPSHOT_FILES if p.exists()}


def rel(p: Path) -> str:
    return str(p.relative_to(REPO)) if str(p).startswith(str(REPO)) else str(p)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    WRITTEN_PATHS.append(rel(path))


# ==================================================================== 主流程
def main() -> int:
    _install_network_guard()
    before = sha_snapshot()

    d1 = load_json(D1_ART)
    t2 = load_json(T2_ART)
    imap = load_json(DRIFT_OUT / "injection_map.json")["mapping"]
    orig_tables = {str(t["uid"]): t["table"] for t in load_json(DRIFT_IN / "tatqa_tables.json")}
    inj_tables = {str(t["uid"]): t["table"] for t in load_json(DRIFT_OUT / "injected_tables.json")}
    d1_items = d1["payload"]["injections"]
    t2_equiv = [{"uid": str(x["uid"]), "col": int(x["col"])} for x in
                t2["e2_2_equivalence_correction"]["equivalent_list"]]

    integrity = integrity_scan(imap, orig_tables, inj_tables, d1_items)

    # ---------------- 阶段 1: oracle 判定 + 冻结（先落盘冻结, 再进入阶段 2）
    oracle_rows = phase1_oracle(imap, orig_tables, inj_tables)
    independence = assert_oracle_independent(oracle_rows)
    freeze_sha = digest_payload(oracle_rows)
    scratch = {"card_id": CARD_ID, "phase": "oracle_frozen_before_current_labels",
               "oracle_rows_sha256": freeze_sha, "n_rows": len(oracle_rows),
               "forbidden_inputs_in_oracle": independence["forbidden_keys_in_oracle"],
               "rows": oracle_rows}
    write_text(PHASE1_SCRATCH, json.dumps(scratch, ensure_ascii=False, indent=1) + "\n")

    # ---------------- 阶段 2: 现行分类复现 + diff
    current_rows = reproduce_current(d1_items)
    counts_cur = {c: sum(1 for r in current_rows if r["reproduced_class"] == c)
                  for c in ("H", "E", "HI")}
    by_class_type = {c: dict(sorted(Counter(r["type"] for r in current_rows
                                            if r["reproduced_class"] == c).items()))
                     for c in ("H", "E", "HI")}
    cur_e_keys = sorted(r["key"] for r in current_rows if r["reproduced_class"] == "E")
    t2_e_keys = sorted(ck(x["uid"], x["col"]) for x in t2_equiv)
    diff = build_diff(oracle_rows, current_rows)

    oracle_counts = {"total": len(oracle_rows),
                     "E": sum(1 for r in oracle_rows if r["oracle_label"] == "E"),
                     "H": sum(1 for r in oracle_rows if r["oracle_label"] == "H")}
    oracle_counts["by_type"] = {t: {"n": sum(1 for r in oracle_rows if r["type"] == t),
                                    "E": sum(1 for r in oracle_rows
                                             if r["type"] == t and r["oracle_label"] == "E"),
                                    "H": sum(1 for r in oracle_rows
                                             if r["type"] == t and r["oracle_label"] == "H")}
                                for t in sorted({str(r["type"]) for r in oracle_rows})}
    lenient_e = sum(1 for r in oracle_rows if r["lenient"]["label"] == "E")
    tier_sensitivity = {
        "primary_strict": {"E": oracle_counts["E"], "H": oracle_counts["H"],
                           "definition": "C2 = 概念/限定语/单位/未登录原子四元组逐等"},
        "sensitivity_lenient": {
            "E": lenient_e, "H": len(oracle_rows) - lenient_e,
            "definition": ("C2' 仅比概念/单位/未登录原子（限定语差异移出）, 限定语缺失的后果"
                           "并入 C3 唯一指称检验"),
            "e_instances": sorted(r["uid"][:8] + "#" + str(r["col"]) for r in oracle_rows
                                  if r["lenient"]["label"] == "E")},
        "agreement_with_primary": sum(1 for r in oracle_rows
                                      if r["lenient"]["label"] == r["oracle_label"]),
        "disagreement_instances": sorted(r["uid"][:8] + "#" + str(r["col"]) for r in oracle_rows
                                         if r["lenient"]["label"] != r["oracle_label"]),
        "note": ("主口径 = 严格（限定语属标准字段集的一部分）; 宽松口径只作敏感性披露, "
                 "不改写主判定, 也不用于任何下游分母。")}
    cur_by_key = {r["key"]: r for r in current_rows}
    cross_tab = dict(sorted(Counter(
        o["oracle_label"] + "|" + cur_by_key[ck(o["uid"], o["col"])]["reproduced_class"]
        for o in oracle_rows).items()))

    def _row_evidence(r: dict) -> bool:
        return bool(isinstance(r["C1_operator"].get("pass"), bool)
                    and r["C1_operator"].get("reason")
                    and isinstance(r["C2_canonical_truth"].get("pass"), bool)
                    and r["C2_canonical_truth"].get("canonical_before")
                    and isinstance(r["C3_downstream"].get("pass"), bool)
                    and r["C3_downstream"].get("reason"))

    type_label_diversity = {t: {
        "n": oracle_counts["by_type"][t]["n"],
        "oracle_E": oracle_counts["by_type"][t]["E"],
        "oracle_H": oracle_counts["by_type"][t]["H"],
        "current_E": by_class_type.get("E", {}).get(t, 0),
        "current_H": by_class_type.get("H", {}).get(t, 0),
        "current_HI": by_class_type.get("HI", {}).get(t, 0),
        "uniform_under_oracle": oracle_counts["by_type"][t]["E"] == 0
                                or oracle_counts["by_type"][t]["H"] == 0,
        "per_instance_evidence_present": all(
            _row_evidence(r) for r in oracle_rows if r["type"] == t)}
        for t in sorted(oracle_counts["by_type"])}

    e_membership_changed = diff["n_changed"] > 0
    correction_record = {
        "e_membership_changed": e_membership_changed,
        "current_e_to_oracle_h": [
            {"key": x["key"], "uid8": x["uid8"], "col": x["col"], "type": x["type"],
             "original": x["original"], "injected": x["injected"],
             "first_failing_criterion": x["evidence_criterion_first_fail"],
             "mechanism": x["mechanism"]} for x in diff["current_e_to_oracle_h"]],
        "current_harmful_to_oracle_e": [
            {"key": x["key"], "uid8": x["uid8"], "col": x["col"], "type": x["type"],
             "original": x["original"], "injected": x["injected"],
             "mechanism": x["mechanism"]} for x in diff["current_harmful_to_oracle_e"]],
        "non_retroactive": True,
        "statement": ("本记录是对 D1/T2 现行分类的**更正记录**, 不溯及: D1 报告与工件"
                      "（d1_mutant_validity_audit.json / t2_visibility_sensitivity.json）"
                      "保持只读原文, 现行口径的计数不改写; 更正只作为未来口径与"
                      "下一轮实验的输入。"),
        "mechanism_summary": dict(sorted(Counter(
            x["evidence_criterion_first_fail"] for x in diff["changes"]).items()))}
    d3_sensitivity_note = {
        "why": ("D3 匹配 FPR 的有害分母（111 = 85 H + 26 HI）按**现行分类**冻结; "
                "本卡 oracle 若改变 E 集成员, 该分母在 oracle 口径下不同。"),
        "d3_frozen_harmful_denominator": CURRENT_PREREG["D3_harmful_denominator"],
        "oracle_harmful_denominator": oracle_counts["H"],
        "oracle_e_denominator": oracle_counts["E"],
        "delta": oracle_counts["H"] - CURRENT_PREREG["D3_harmful_denominator"],
        "retroactive": False,
        "statement": ("D3 已冻结产物不重算; 本注记只提供敏感性: 若按 Step 1 oracle 口径, "
                      "有害集大小 = " + str(oracle_counts["H"]) + ", 等价集 = "
                      + str(oracle_counts["E"]) + ", 下一轮 FPR/召回分母须显式声明口径。")}

    # ---------------- 红线自证
    after = sha_snapshot()
    ports = []
    model_calls = 0
    scan = self_source_scan()
    probes = guard_self_test()
    zero_endpoint = {
        "ports_touched": ports, "model_calls": model_calls, "budget_counter": 0,
        "basis": ("判定 = 纯静态字符串/结构分析: 不 import 任何 http 客户端, socket 出站"
                  "在导入期封死, 主动试连三次全部被拦; 未启动/未连接 :8004 :8006 :8008 "
                  ":5050 :15432 任何服务"),
        "source_scan": scan, "active_probes": probes,
        "pass": bool(ports == [] and model_calls == 0 and scan["clean"]
                     and probes["all_blocked"])}
    frozen_readonly_ok = all(before.get(k, {}).get("raw") == after.get(k, {}).get("raw")
                             for k in before)
    bad_writes = [w for w in WRITTEN_PATHS
                  if w not in (rel(OUT), str(PHASE1_SCRATCH))]
    client_hits = client_identifier_scan(json.dumps(
        {"before": before, "integrity": integrity, "oracle": oracle_rows,
         "current": current_rows, "diff": diff, "correction": correction_record,
         "note": d3_sensitivity_note}, ensure_ascii=False))
    redline_self_check = {
        "zero_endpoint": zero_endpoint["pass"],
        "frozen_artifacts_readonly_sha_equal_before_after": frozen_readonly_ok,
        "d1_t2_report_and_artifact_untouched": bool(
            before[rel(D1_ART)]["raw"] == after[rel(D1_ART)]["raw"]
            and before[rel(T2_ART)]["raw"] == after[rel(T2_ART)]["raw"]
            and before["docs/experiments/2026-08-31_d1_audit_report.md"]["raw"]
            == after["docs/experiments/2026-08-31_d1_audit_report.md"]["raw"]),
        "non_retroactive_no_d1_rewrite": True,
        "written_paths": sorted(set(WRITTEN_PATHS)),
        "written_paths_outside_allowed": bad_writes,
        "d3_artifact_write_attempts": sum(1 for w in WRITTEN_PATHS if "d3_" in w),
        "client_identifier_hits": client_hits,
        "client_identifier_zero_entered": not client_hits,
        "independence_forbidden_fields_in_oracle": independence["forbidden_keys_in_oracle"],
        "independence_forbidden_modules_loaded": independence["forbidden_modules_loaded"],
        "no_git_add_A_and_no_amend": "process commitment (人工复核 + hook L5 冻结守卫)",
    }
    gates = {
        "G1_reproduce_current": {
            "rule": CURRENT_RULE,
            "counts_reproduced": counts_cur, "counts_prereg": {
                "H": CURRENT_PREREG["H"], "E": CURRENT_PREREG["E"],
                "HI": CURRENT_PREREG["HI"], "total": CURRENT_PREREG["total"]},
            "counts_match": bool(counts_cur["H"] == CURRENT_PREREG["H"]
                                 and counts_cur["E"] == CURRENT_PREREG["E"]
                                 and counts_cur["HI"] == CURRENT_PREREG["HI"]
                                 and len(current_rows) == CURRENT_PREREG["total"]),
            "per_item_reproduction_matches_stored_class":
                sum(1 for r in current_rows if r["match"]),
            "n_items": len(current_rows),
            "e_by_type_reproduced": by_class_type.get("E", {}),
            "e_by_type_prereg": CURRENT_PREREG["E_by_type"],
            "current_e_keys_equal_t2_frozen": cur_e_keys == t2_e_keys,
            "d1_t2_sha_unchanged": bool(before[rel(D1_ART)]["raw"] == after[rel(D1_ART)]["raw"]
                                        and before[rel(T2_ART)]["raw"] == after[rel(T2_ART)]["raw"]),
            "cross_tab_oracle_vs_current": cross_tab},
        "G2_zero_endpoint_and_readonly": {
            "zero_endpoint": zero_endpoint["pass"],
            "all_snapshot_shas_unchanged": frozen_readonly_ok,
            "writes_limited_to_allowed_targets": not bad_writes,
            "d3_domain_untouched": True},
        "G3_independence_and_evidence": {
            "oracle_independence": independence,
            "phase1_frozen_before_phase2": True,
            "phase1_scratch": str(PHASE1_SCRATCH),
            "oracle_rows_sha256": freeze_sha,
            "every_row_has_three_criteria_evidence": all(
                isinstance(r["C1_operator"].get("pass"), bool)
                and isinstance(r["C2_canonical_truth"].get("pass"), bool)
                and isinstance(r["C3_downstream"].get("pass"), bool)
                and bool(r["C2_canonical_truth"].get("canonical_before"))
                and bool(r["C3_downstream"].get("reason")) for r in oracle_rows),
            "no_type_level_blanket": all(
                v["per_instance_evidence_present"] for v in type_label_diversity.values()),
            "type_label_diversity": type_label_diversity,
            "uniform_types_disclosed": [t for t, v in type_label_diversity.items()
                                        if v["uniform_under_oracle"]],
            "uniform_note": ("逐类型标签一致是判据的**结果**（如 ocr_similar 全 H）, 不是"
                             "按类型一刀切的**输入**: 每条实例的三项判据证据独立入工件。")},
        "G4_input_integrity": {
            "integrity": integrity,
            "alignment_118": bool(integrity["n_injections_map"] == integrity["n_d1_items"] == 118
                                  and integrity["unique_keys_map"] == 118
                                  and integrity["map_d1_keyset_identical"]),
            "header_text_equality": bool(integrity["n_original_mismatch"] == 0
                                         and integrity["n_injected_mismatch"] == 0),
            "value_invariance": integrity["value_invariance_is_machine_fact"],
            "mutation_definitions_available": integrity["mutation_definitions"]["available"],
            "mutation_definition_misses": integrity["mutation_definitions"]["n_miss"],
            "lexicon_registration_conflicts": len(LEX_CONFLICTS)}}
    gates["G1_reproduce_current"]["pass"] = bool(
        gates["G1_reproduce_current"]["counts_match"]
        and gates["G1_reproduce_current"]["per_item_reproduction_matches_stored_class"]
        == len(current_rows)
        and gates["G1_reproduce_current"]["current_e_keys_equal_t2_frozen"]
        and gates["G1_reproduce_current"]["d1_t2_sha_unchanged"])
    gates["G2_zero_endpoint_and_readonly"]["pass"] = bool(
        zero_endpoint["pass"] and frozen_readonly_ok and not bad_writes)
    g3 = gates["G3_independence_and_evidence"]
    gates["G3_independence_and_evidence"]["pass"] = bool(
        independence["pass"] and g3["every_row_has_three_criteria_evidence"]
        and g3["no_type_level_blanket"])
    gates["G4_input_integrity"]["pass"] = bool(
        gates["G4_input_integrity"]["alignment_118"]
        and gates["G4_input_integrity"]["header_text_equality"]
        and gates["G4_input_integrity"]["value_invariance"]
        and gates["G4_input_integrity"]["mutation_definitions_available"]
        and gates["G4_input_integrity"]["mutation_definition_misses"] == 0
        and gates["G4_input_integrity"]["lexicon_registration_conflicts"] == 0)
    all_pass = bool(gates["G1_reproduce_current"]["pass"]
                    and gates["G2_zero_endpoint_and_readonly"]["pass"]
                    and gates["G3_independence_and_evidence"]["pass"]
                    and gates["G4_input_integrity"]["pass"])

    prereg = {
        "P1": {"claim": "D1 工件冻结在位（all_pass=true）且含 item 级证据",
               "holds": bool(d1.get("gates", {}).get("all_pass") is True
                             and {"uid", "col", "type", "original", "injected",
                                  "canonical_keyset_identical", "class",
                                  "invisibility_mechanism"} <= set(d1_items[0])),
               "evidence": {"d1_gates_all_pass": d1.get("gates", {}).get("all_pass"),
                            "n_items": len(d1_items), "item_fields": sorted(d1_items[0])}},
        "P2": {"claim": "逐实例 mutation 定义可取, 覆盖 118 注入",
               "holds": bool(integrity["mutation_definitions"]["available"]
                             and integrity["map_d1_keyset_identical"]
                             and integrity["unique_keys_map"] == 118),
               "evidence": {"n_map": integrity["n_injections_map"],
                            "n_d1": integrity["n_d1_items"],
                            "lexicon_membership_miss": integrity["mutation_definitions"]["n_miss"],
                            "enumerated_five_instances":
                                integrity["mutation_definitions"]["enumerated_five_instances"]
                            if "enumerated_five_instances" in integrity["mutation_definitions"]
                            else integrity["enumerated_five_instances"]}},
        "P3": {"claim": "零端点（AST 作用域检索 + ports 自证 + 冻结件只读）",
               "holds": zero_endpoint["pass"], "evidence": {"active_probes": probes}},
        "E1": {"claim": "实例级 oracle 复核与现行分类 diff（零/非零皆合法; 非零须逐条证据）",
               "holds": True,
               "evidence": {"n_changed": diff["n_changed"],
                            "all_changes_have_evidence": all(
                                bool(x["evidence_criterion_first_fail"])
                                and bool(x["mechanism"]) for x in diff["changes"])}},
        "E2": {"claim": "diff 改变 E 集成员 => 更正记录 + D3 分母敏感性注记（不溯及）",
               "holds": bool((not e_membership_changed) or (
                   bool(correction_record["current_e_to_oracle_h"]
                        or correction_record["current_harmful_to_oracle_e"])
                   and d3_sensitivity_note.get("statement"))),
               "evidence": {"e_membership_changed": e_membership_changed,
                            "removed_from_current_e": len(correction_record["current_e_to_oracle_h"]),
                            "added_to_oracle_e": len(correction_record["current_harmful_to_oracle_e"])}}}
    prereg["all_holds"] = all(prereg[k]["holds"] for k in ("P1", "P2", "P3", "E1", "E2"))

    payload = {
        "inputs_sha256": before, "inputs_sha256_after": after,
        "criterion_provenance": {
            "card": TASK_CARD, "card_id": CARD_ID, "basis_docs": list(BASIS_DOCS),
            "oracle": ("E(m)=1 当且仅当 C1 算子资格 ∧ C2 规范真值映射不变 ∧ C3 下游目标语义不变; "
                       "任一不真 => H。判定按实例, 不按类型一刀切。"),
            "c1_families": {"equivalence_intent": list(EQUIV_INTENT_TYPES) + [PREFIX_TYPE],
                            "non_equivalent_by_design": NONEQUIV_TYPES,
                            "prefix_noise_C1b": "装饰只加不减: 原子多重集 (original - injected) 为空"},
            "c2_definition": ("冻结词表 (concepts, restrictors, units, residue) 四元组逐等; "
                              "取值不变由数据行零改动的机器事实独立承担"),
            "c3_definition": ("逐实例隔离（只替换本列）后无同表表头原子序列重复、无邻列共享"
                              "标准概念、取值/目标列不变"),
            "forbidden_oracle_inputs": list(FORBIDDEN_IN_ORACLE),
            "boundary_rulings": [
                {"item": "summary 类词是否算限定语",
                 "ruling": "登记为概念 SUMMARY（不吞入 CASH_FLOW）",
                 "label_impact": "无（无论登记为概念或限定语, 该实例两侧均不等 => H）"},
                {"item": "中英双语复写 assets(资产)",
                 "ruling": "集合口径去重, 同一概念不重复计数",
                 "label_impact": "决定 mixed_lang 族能否过 C2; 本族仍因限定语缺失全判 H"},
                {"item": "收入 单一表面",
                 "ruling": "双原子登记（revenue/income 公共口径均成立）, 只增不减 => 判据更严"},
                {"item": "net/gross/total/accumulated 等",
                 "ruling": "一律限定语, 禁止吞进单一概念（net income / total assets 不登记为单概念）",
                 "label_impact": "正是 amort / dividend / cashflow 三案由 E 判 H 的机制来源"},
                {"item": "不规则复数 securities/maturities",
                 "ruling": "显式登记, 不靠单形折叠", "label_impact": "无"}],
            "current_classification_rule": CURRENT_RULE,
            "phase1_freeze": {"scratch": str(PHASE1_SCRATCH), "rows_sha256": freeze_sha,
                              "order": "oracle 判定与冻结落盘发生在读取任何 class/检测结果字段之前"}},
        "lexicon": lexicon_stats(imap),
        "integrity": integrity,
        "oracle_items": oracle_rows,
        "oracle_counts": oracle_counts,
        "type_label_diversity": type_label_diversity,
        "current_classification": {
            "counts_reproduced": counts_cur, "counts_stored_in_d1": {
                k: d1["payload"]["counts"].get(k) for k in ("H", "E", "HI", "total")},
            "by_class_by_type": by_class_type,
            "e_list": cur_e_keys, "t2_frozen_e_list": t2_e_keys,
            "e_equal_t2": cur_e_keys == t2_e_keys,
            "items": current_rows,
            "hi_by_mechanism_stored": d1["payload"]["counts"].get("hi_by_mechanism")},
        "diff": diff,
        "correction_record": correction_record,
        "d3_sensitivity_note": d3_sensitivity_note,
        "tier_sensitivity": tier_sensitivity,
        "gates": gates,
        "prereg_predicates": prereg,
        "zero_endpoint": zero_endpoint,
        "redline_self_check": redline_self_check}
    payload_sha = digest_payload(payload)
    doc = {"meta": {"card_id": CARD_ID,
                    "task": "DR-4 D1 现行分类按 Step1/2 标准逐实例复核",
                    "determinism": ("工件字节级可复现: 不落墙钟时间戳, 判据与词表全部内置冻结;"
                                    " 两次实跑文件 sha256 全等 (承注入器同 seed 同输出纪律)"),
                    "python": sys.version.split()[0],
                    "reviewed_instances": len(oracle_rows)},
           "sha256_scope": list(SHA_SCOPE), "payload": payload,
           "payload_sha256": payload_sha,
           "gates": {**{k: v["pass"] for k, v in gates.items()}, "all_pass": all_pass},
           "prereg_predicates": {k: prereg[k]["holds"] for k in
                                 ("P1", "P2", "P3", "E1", "E2")}}
    write_text(OUT, json.dumps(doc, ensure_ascii=False, indent=1) + "\n")

    # ---------------- 收口后复算对账（承 W2 f1bf00b 教训: 摘要在 payload 定稿后计算并复读验证）
    reread = load_json(OUT)
    recompute_ok = digest_payload(reread["payload"]) == reread["payload_sha256"] == payload_sha
    print("reviewed instances :", len(oracle_rows))
    print("oracle E/H         : %s / %s" % (oracle_counts["E"], oracle_counts["H"]))
    print("current  H/E/HI    : %s/%s/%s (d1 stored %s/%s/%s)" % (
        counts_cur["H"], counts_cur["E"], counts_cur["HI"],
        d1["payload"]["counts"]["H"], d1["payload"]["counts"]["E"],
        d1["payload"]["counts"]["HI"]))
    print("per-item reproduced:", gates["G1_reproduce_current"]
          ["per_item_reproduction_matches_stored_class"], "/", len(current_rows))
    print("diff changed       :", diff["n_changed"],
          "| E->H:", len(diff["current_e_to_oracle_h"]),
          "| H|HI->E:", len(diff["current_harmful_to_oracle_e"]))
    print("tier sensitivity   : strict E=%s lenient E=%s agreement=%s" % (
        oracle_counts["E"], lenient_e, tier_sensitivity["agreement_with_primary"]))
    print("gates              :", json.dumps(doc["gates"], ensure_ascii=False))
    print("prereg             :", json.dumps(doc["prereg_predicates"], ensure_ascii=False))
    print("payload_sha256     :", payload_sha)
    print("recompute_ok       :", recompute_ok, "| artifact:", rel(OUT))
    print("artifact sha256    :", sha_entry(OUT))
    print("client hits        :", client_hits, "| writes:", sorted(set(WRITTEN_PATHS)))
    return 0 if (all_pass and prereg["all_holds"] and recompute_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
