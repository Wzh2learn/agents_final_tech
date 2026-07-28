#!/usr/bin/env python3
"""M1 真实对账单解析原型（表头近义词映射）。

把各家格式不统一的对账单/报表（TXT/PDF/XLSX/DOCX）解析成标准化结构：
    文档解析 -> 识别表头 -> 近义词映射到标准字段 -> 标准化记录。

纯规则实现（stdlib + PyMuPDF + openpyxl + python-docx），不下载/调用模型。
样本通过绝对路径 ~/wzh/m1_samples 读取，绝不入库；输出全部脱敏。

用法:
    ./venv/bin/python scripts/m1_statement_parser.py [--samples-dir DIR] [--json OUT]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any

# ---- 可选第三方库（缺失时优雅降级） -------------------------------------
try:
    import fitz  # PyMuPDF
    _HAS_FITZ = True
except Exception:  # pragma: no cover
    _HAS_FITZ = False

try:
    import openpyxl
    _HAS_OPENPYXL = True
except Exception:  # pragma: no cover
    _HAS_OPENPYXL = False

try:
    import docx  # python-docx
    _HAS_DOCX = True
except Exception:  # pragma: no cover
    _HAS_DOCX = False

DEFAULT_SAMPLES_DIR = os.path.expanduser("~/wzh/m1_samples")
DEFAULT_SCHEMA = os.path.join(DEFAULT_SAMPLES_DIR, "m1_table_schema.json")

# 分隔线（--- / === / ___ 等）
_SEP_RE = re.compile(r"^\s*[-=_\u2013\u2014]{4,}\s*$")
# 归一化时要剔除的字符：空白 + 常见中英文标点
_NORM_DROP = re.compile(r"[\s\u3000\(\)\[\]{}（）【】《》<>:：;；,，.。、/\\\-—_~`'\"!！?？*]+")


# =========================================================================
# 基础工具
# =========================================================================
def normalize_header(text: str) -> str:
    """归一化列名：去空白/标点/全角，转小写。用于近义词包含与编辑距离匹配。"""
    if text is None:
        return ""
    return _NORM_DROP.sub("", str(text)).lower()


def edit_distance(a: str, b: str) -> int:
    """Levenshtein 编辑距离（DP，短串场景足够）。"""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost))
        prev = cur
    return prev[-1]


def read_text_autoenc(path: str) -> str:
    """按 gbk -> utf-8(-sig) 顺序探测编码读取文本。"""
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "gbk", "gb18030", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


# =========================================================================
# Schema 加载
# =========================================================================
@dataclass
class SchemaField:
    standard: str
    synonyms: list[str]


@dataclass
class SchemaTable:
    table_name: str
    layout: str
    header_region_keywords: list[str]
    fields: list[SchemaField]


@dataclass
class Schema:
    tables: list[SchemaTable]
    header_meta_fields: dict[str, list[str]]

    @classmethod
    def load(cls, path: str) -> "Schema":
        with open(path, encoding="utf-8-sig") as fh:
            data = json.load(fh)
        tables = []
        for t in data.get("tables", []):
            fields = [SchemaField(f["standard"], list(f.get("synonyms", [])))
                      for f in t.get("fields", [])]
            tables.append(SchemaTable(
                t.get("table_name", ""),
                t.get("layout", "grid"),
                list(t.get("header_region_keywords", [])),
                fields,
            ))
        meta = {k: list(v) for k, v in data.get("header_meta_fields", {}).items()
                if not k.startswith("_")}
        return cls(tables, meta)


# =========================================================================
# 表头近义词映射
# =========================================================================
@dataclass
class MatchResult:
    schema_table: str
    mapping: dict[str, str]          # standard_field -> source_column
    unmapped: list[str]              # 未映射上的源列名
    hits: int
    source_headers: list[str]


def _best_field_for_header(header_norm: str, fields: list[SchemaField]):
    """为单个源列名找到最佳标准字段，返回 (standard, score, syn_len)。"""
    best = None  # (score, syn_len, standard)
    for fld in fields:
        for syn in fld.synonyms:
            syn_norm = normalize_header(syn)
            if not syn_norm:
                continue
            if syn_norm == header_norm:
                score = 3
            elif len(syn_norm) >= 2 and (syn_norm in header_norm or header_norm in syn_norm):
                # 包含匹配：更长的 synonym 命中更可信
                score = 2
            elif min(len(syn_norm), len(header_norm)) >= 3 and edit_distance(syn_norm, header_norm) <= 1:
                # 编辑距离兜底：仅对>=3字符且距离<=1，避免短列名误配（如 币种->券商）
                score = 1
            else:
                continue
            key = (score, len(syn_norm))
            if best is None or key > (best[0], best[1]):
                best = (score, len(syn_norm), fld.standard)
    return best


def map_headers(source_headers: list[str], schema_table: SchemaTable) -> tuple[dict[str, str], list[str]]:
    """把源列名映射到指定 schema 表的标准字段。

    匹配优先级：精确 > 归一化包含 > 编辑距离<=2。每个标准字段至多被占用一次
    （按得分贪心），未命中的源列名进入 unmapped。
    """
    candidates: list[tuple[int, int, str, str]] = []  # score, syn_len, src, standard
    for src in source_headers:
        hn = normalize_header(src)
        if not hn:
            continue
        best = _best_field_for_header(hn, schema_table.fields)
        if best:
            score, syn_len, standard = best
            candidates.append((score, syn_len, src, standard))

    # 贪心：高分优先；同一标准字段只接受一次；同一源列只接受一次
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    mapping: dict[str, str] = {}
    used_std: set[str] = set()
    used_src: set[str] = set()
    for score, syn_len, src, standard in candidates:
        if standard in used_std or src in used_src:
            continue
        mapping[standard] = src
        used_std.add(standard)
        used_src.add(src)

    unmapped = [h for h in source_headers if normalize_header(h) and h not in used_src]
    return mapping, unmapped


def best_schema_match(source_headers: list[str], schema: Schema) -> MatchResult:
    """在所有 schema 表中选命中数最高者作为该源表的归属表。"""
    best: MatchResult | None = None
    for st in schema.tables:
        mapping, unmapped = map_headers(source_headers, st)
        hits = len(mapping)
        cand = MatchResult(st.table_name, mapping, unmapped, hits, list(source_headers))
        if best is None or hits > best.hits:
            best = cand
    if best is None:
        best = MatchResult("", {}, list(source_headers), 0, list(source_headers))
    return best


def normalize_rows(rows: list[list[str]], mapping: dict[str, str],
                   source_headers: list[str]) -> list[dict[str, str]]:
    """按 mapping 把数据行转成标准化 dict（键为标准字段名）。"""
    idx = {h: i for i, h in enumerate(source_headers)}
    out: list[dict[str, str]] = []
    for row in rows:
        rec: dict[str, str] = {}
        for standard, src in mapping.items():
            i = idx.get(src)
            val = ""
            if i is not None and i < len(row):
                val = (row[i] or "").replace("\n", "").strip()
            rec[standard] = val
        out.append(rec)
    return out


# =========================================================================
# 表头信息区（键值对）提取
# =========================================================================
# 仅用于“值边界”识别的常见对账单键名（不一定在 schema header_meta 里）。
# 它们让一行多 KV 时上一个值能正确截断，避免把相邻键的值吞进来。
_EXTRA_BOUND_KEYS = [
    "客户名称", "客户编号", "客户号", "客户全称", "客户姓名", "户名",
    "资产账号", "资金账号", "证券账号", "股东账号", "股东帐号", "账号",
    "证件类型", "证件号码", "证件号", "统一社会信用代码",
    "打印时间", "打印柜员", "生成时间", "统计日期", "开始日期", "结束日期",
    "制表", "基金名称", "基金代码", "交易帐号", "交易账号",
    "基金份额净值", "基金资产总额", "基金账户份额",
    "人民币市值", "美元市值", "港币市值", "资金余额", "资产总值", "证券市值",
]


def extract_header_meta(text: str, schema: Schema) -> dict[str, str]:
    """用 header_meta_fields 的键名/近义词从自由文本里提取键值对。

    支持一行多个 KV（如 `客户编号:xx  资产账号:yy`）。只用 schema 定义的
    header_meta_fields 记录结果；另用一组更宽的常见键名作为“值边界”，确保
    相邻键的值不会被吞并（如 证件号码 不会吞掉后面的 证券账号）。
    """
    syn2std: dict[str, str] = {}
    for standard, syns in schema.header_meta_fields.items():
        for syn in syns:
            syn2std[syn] = standard
        syn2std.setdefault(standard, standard)
    record_keys = sorted(syn2std.keys(), key=len, reverse=True)
    if not record_keys:
        return {}
    bound_keys = sorted(set(record_keys) | set(_EXTRA_BOUND_KEYS),
                        key=len, reverse=True)
    key_alt = "|".join(re.escape(k) for k in record_keys)
    bound_alt = "|".join(re.escape(k) for k in bound_keys)
    pattern = re.compile(
        rf"(?P<key>{key_alt})\s*[:：]\s*(?P<val>.*?)"
        rf"(?=\s+(?:{bound_alt})\s*[:：]|$)",
    )
    found: dict[str, str] = {}
    for line in text.splitlines():
        for m in pattern.finditer(line):
            std = syn2std.get(m.group("key"), m.group("key"))
            val = m.group("val").strip().strip(" \t,，;；")
            if val and std not in found:
                found[std] = val
    return found


# =========================================================================
# 各格式解析器：统一返回 ParsedDoc
# =========================================================================
@dataclass
class ParsedTable:
    name: str
    headers: list[str]
    rows: list[list[str]]


@dataclass
class ParsedDoc:
    path: str
    kind: str
    ok: bool = True
    error: str = ""
    needs_ocr: bool = False
    text: str = ""
    tables: list[ParsedTable] = field(default_factory=list)
    note: str = ""


def _split_cells(line: str) -> list[str]:
    return [c for c in re.split(r"\s+", line.strip()) if c != ""]


def parse_txt(path: str) -> ParsedDoc:
    """解析 GBK/UTF-8 文本对账单：表头区 KV + 分隔线之间的网格表。"""
    doc = ParsedDoc(path=path, kind="txt")
    try:
        text = read_text_autoenc(path)
    except Exception as exc:  # pragma: no cover
        doc.ok, doc.error = False, f"read fail: {exc}"
        return doc
    doc.text = text
    lines = text.splitlines()
    n = len(lines)
    i = 0
    table_idx = 0
    while i < n:
        line = lines[i]
        # 表头行：其后紧跟分隔线
        if line.strip() and i + 1 < n and _SEP_RE.match(lines[i + 1]):
            headers = _split_cells(line)
            j = i + 2
            rows: list[list[str]] = []
            while j < n and not _SEP_RE.match(lines[j]) and lines[j].strip():
                rows.append(_split_cells(lines[j]))
                j += 1
            if headers:
                table_idx += 1
                doc.tables.append(ParsedTable(f"table_{table_idx}", headers, rows))
            i = j + 1 if j < n else j
            continue
        i += 1
    return doc


def parse_pdf(path: str) -> ParsedDoc:
    """PyMuPDF：find_tables 取网格表 + get_text 取表头区文本。"""
    doc = ParsedDoc(path=path, kind="pdf")
    if not _HAS_FITZ:
        doc.ok, doc.error = False, "PyMuPDF(fitz) unavailable"
        return doc
    try:
        pdf = fitz.open(path)
        all_text: list[str] = []
        tidx = 0
        total_images = 0
        for pno in range(pdf.page_count):
            page = pdf[pno]
            all_text.append(page.get_text())
            total_images += len(page.get_images())
            try:
                found = page.find_tables()
            except Exception:
                found = None
            if not found:
                continue
            for tb in found.tables:
                grid = tb.extract()
                if not grid:
                    continue
                # 清洗 None / 换行
                clean = [[(c or "").replace("\n", "").strip() for c in row]
                         for row in grid]
                headers = clean[0]
                rows = [r for r in clean[1:] if any(x for x in r)]
                if not any(headers):
                    continue
                tidx += 1
                doc.tables.append(ParsedTable(f"p{pno}_table_{tidx}", headers, rows))
        doc.text = "\n".join(all_text)
        if not doc.text.strip() and total_images > 0 and not doc.tables:
            doc.needs_ocr = True
            doc.note = f"image-only PDF ({total_images} image(s), no text layer) -> needs OCR/vision"
    except Exception as exc:
        doc.ok, doc.error = False, f"pdf parse fail: {exc}"
    return doc


def parse_xlsx(path: str) -> ParsedDoc:
    """openpyxl：读首个非空 sheet 为单张网格表。"""
    doc = ParsedDoc(path=path, kind="xlsx")
    if not _HAS_OPENPYXL:
        doc.ok, doc.error = False, "openpyxl unavailable"
        return doc
    try:
        wb = openpyxl.load_workbook(path, data_only=True)
        target = None
        for ws in wb.worksheets:
            if ws.max_row and ws.max_row > 0 and ws.max_column and ws.max_column > 0:
                target = ws
                break
        if target is None:
            doc.ok, doc.note = False, "empty workbook"
            return doc
        rows = []
        for row in target.iter_rows(values_only=True):
            cells = ["" if v is None else str(v) for v in row]
            if any(c.strip() for c in cells):
                rows.append(cells)
        if rows:
            headers = [h.strip() for h in rows[0]]
            data = rows[1:]
            doc.tables.append(ParsedTable(target.title, headers, data))
            doc.text = "\n".join(" ".join(r) for r in rows[:5])
        doc.note = f"sheet={target.title} dims={target.dimensions}"
    except Exception as exc:
        doc.ok, doc.error = False, f"xlsx parse fail: {exc}"
    return doc


def parse_docx(path: str) -> ParsedDoc:
    """python-docx：读 document.tables + 段落 KV；纯图片文档标记 needs_ocr。"""
    doc = ParsedDoc(path=path, kind="docx")
    if not _HAS_DOCX:
        doc.ok, doc.error = False, "python-docx unavailable"
        return doc
    try:
        d = docx.Document(path)
        para_text = [p.text.strip() for p in d.paragraphs if p.text.strip()]
        doc.text = "\n".join(para_text)
        tidx = 0
        for tb in d.tables:
            grid = [[c.text.strip() for c in row.cells] for row in tb.rows]
            grid = [r for r in grid if any(x for x in r)]
            if not grid:
                continue
            tidx += 1
            doc.tables.append(ParsedTable(f"table_{tidx}", grid[0], grid[1:]))
        # 纯图片判定：无文本、无表格，但 zip 内有 media 图片
        if not doc.text and not doc.tables:
            import zipfile
            try:
                imgs = [n for n in zipfile.ZipFile(path).namelist()
                        if n.startswith("word/media/")]
            except Exception:
                imgs = []
            if imgs:
                doc.needs_ocr = True
                doc.note = f"image-only DOCX ({len(imgs)} embedded image(s), no text) -> needs OCR/vision"
            else:
                doc.note = "no text and no tables found"
    except Exception as exc:
        doc.ok, doc.error = False, f"docx parse fail: {exc}"
    return doc


PARSERS = {
    ".txt": parse_txt,
    ".pdf": parse_pdf,
    ".xlsx": parse_xlsx,
    ".docx": parse_docx,
}


# =========================================================================
# 脱敏
# =========================================================================
def _mask_middle(value: str, head: int, tail: int) -> str:
    value = str(value)
    n = len(value)
    if n == 0:
        return value
    if n <= head + tail:
        head = max(1, n // 3)
        tail = max(1, n // 3)
        if head + tail >= n:
            tail = max(0, n - head - 1)
    if tail > 0:
        return f"{value[:head]}****{value[n - tail:]}"
    return f"{value[:head]}****"


def desensitize_value(key: str, value: str) -> str:
    """按字段语义脱敏：证件/账号保首尾，名称保首尾，金额保整数首4+小数。"""
    if value is None:
        return ""
    val = str(value).strip()
    if not val:
        return val
    k = str(key)
    # 证件号/统一社会信用代码：保首4尾4（先于金额，避免“资产账号”之类被当金额）
    if re.search(r"(证件|信用|执照)", k):
        return _mask_middle(val.replace(" ", ""), 4, 4)
    # 账号/编号/代码类：保首4尾4
    if re.search(r"(账号|帐号|编号|代码|股东|柜员)", k):
        return _mask_middle(val.replace(" ", ""), 4, 4)
    # 名称类：保首2尾3
    if re.search(r"(名称|姓名|客户|户名|全称|管理人|券商|营业部|公司|产品)", k):
        return _mask_middle(val, 2, 3)
    # 金额/市值/净值类：保留整数部分前 4 位 + 小数
    if re.search(r"(金额|市值|净值|资产|余额|盈亏|成本|价|总额|总值|份额|数量|持仓|股数)", k):
        m = re.match(r"^(-?)(\d+)(\.\d+)?$", val.replace(",", ""))
        if m:
            sign, ints, frac = m.groups()
            frac = frac or ""
            if len(ints) > 4:
                return f"{sign}{ints[:4]}****{frac}"
            return f"{sign}{ints}{frac}"
    return val


def desensitize_record(rec: dict[str, str]) -> dict[str, str]:
    return {k: desensitize_value(k, v) for k, v in rec.items()}



# =========================================================================
# 勾稽校验
# =========================================================================
_NUM_RE = re.compile(r"[-+]?[\d,]+\.?\d*")


def _parse_number(text: str) -> float | None:
    """从字符串中提取数值（去逗号/空格），失败返回 None。"""
    if not text:
        return None
    m = _NUM_RE.search(text.replace(",", "").replace("，", ""))
    if m:
        try:
            return float(m.group())
        except ValueError:
            return None
    return None


_DATE_PATTERNS = [
    (re.compile(r"^\d{8}$"), "YYYYMMDD"),
    (re.compile(r"^\d{4}年\d{1,2}月\d{1,2}日$"), "YYYY年MM月DD日"),
    (re.compile(r"^\d{4}-\d{2}-\d{2}$"), "YYYY-MM-DD"),
    (re.compile(r"^\d{4}/\d{2}/\d{2}$"), "YYYY/MM/DD"),
]


def reconcile(table_reports: list[dict[str, Any]],
              header_kv: dict[str, str],
              schema: Schema) -> list[dict[str, Any]]:
    """对解析结果做算术勾稽校验，返回 check 结果列表。

    每项: {check, expected, actual, pass, note}
    勾稽异常时 try/except 保护，记 mismatch=ERROR 继续。
    """
    checks: list[dict[str, Any]] = []

    # 收集各 schema 表的标准化记录
    detail_records: list[dict[str, str]] = []   # 证券持仓明细
    summary_records: list[dict[str, str]] = []  # 资金资产汇总 / 交易对账单
    detail_mappings: list[dict[str, str]] = []  # 明细表的 mapping
    for tr in table_reports:
        recs = tr.get("_records", [])
        if tr["matched_schema"] == "证券持仓明细":
            detail_records.extend(recs)
            detail_mappings.append(tr["mapping"])
        elif tr["matched_schema"] in ("资金资产汇总", "交易对账单"):
            summary_records.extend(recs)

    # ---- 1. 市值勾稽 ----
    try:
        mv_vals = [_parse_number(r.get("市值", "")) for r in detail_records]
        mv_vals = [v for v in mv_vals if v is not None]
        total_mv = sum(mv_vals) if mv_vals else None

        summary_total = None
        summary_field = None
        for r in summary_records:
            for fld in ("合计金额", "资产总值", "总资产"):
                v = _parse_number(r.get(fld, ""))
                if v is not None and v != 0:
                    summary_total = v
                    summary_field = fld
                    break
            if summary_total is not None:
                break

        if total_mv is not None and summary_total is not None and summary_total != 0:
            tol = max(0.01, 0.005 * abs(summary_total))
            diff = abs(total_mv - summary_total)
            passed = diff <= tol
            checks.append({
                "check": "市值勾稽",
                "expected": f"sum(市值)≈{summary_field}={summary_total:.2f}",
                "actual": f"sum(市值)={total_mv:.2f}, diff={diff:.2f}, tol={tol:.2f}",
                "pass": passed,
                "note": "" if passed else f"差异 {diff:.2f} 超容差 {tol:.2f}",
            })
        else:
            checks.append({
                "check": "市值勾稽",
                "expected": "明细市值 + 汇总合计同时存在",
                "actual": f"明细市值={'有' if total_mv else '无'}, 汇总={'有' if summary_total else '无'}",
                "pass": True,
                "note": "数据不足，跳过",
            })
    except Exception as exc:
        checks.append({"check": "市值勾稽", "expected": "", "actual": "",
                       "pass": False, "note": f"ERROR: {exc}"})

    # ---- 2. 币种一致 ----
    try:
        currencies = set()
        for r in detail_records:
            c = r.get("币种", "").strip()
            if c:
                currencies.add(c)
        if currencies:
            passed = len(currencies) == 1
            note = ""
            if not passed:
                note = f"明细币种不唯一: {currencies}"
            checks.append({
                "check": "币种一致",
                "expected": "明细币种去重=1",
                "actual": f"去重={len(currencies)} {currencies}",
                "pass": passed,
                "note": note,
            })
        else:
            checks.append({
                "check": "币种一致",
                "expected": "明细含币种列",
                "actual": "无币种数据",
                "pass": True,
                "note": "数据不足，跳过",
            })
    except Exception as exc:
        checks.append({"check": "币种一致", "expected": "", "actual": "",
                       "pass": False, "note": f"ERROR: {exc}"})

    # ---- 3. 日期格式 ----
    try:
        date_fields = ["对账日期", "统计日期", "开始日期", "结束日期", "打印时间"]
        date_vals_found = []
        for fld in date_fields:
            v = header_kv.get(fld, "").strip()
            if v:
                date_vals_found.append((fld, v))
        if date_vals_found:
            all_ok = True
            details = []
            for fld, v in date_vals_found:
                matched_fmt = None
                for pat, fmt in _DATE_PATTERNS:
                    if pat.match(v):
                        matched_fmt = fmt
                        break
                if matched_fmt:
                    details.append(f"{fld}={v}({matched_fmt})")
                else:
                    # 打印时间等含时分秒的也接受
                    if re.search(r"\d{4}", v):
                        details.append(f"{fld}={v}(含日期)")
                    else:
                        all_ok = False
                        details.append(f"{fld}={v}(格式异常)")
            checks.append({
                "check": "日期格式",
                "expected": "YYYYMMDD / YYYY年MM月DD日 / YYYY-MM-DD",
                "actual": "; ".join(details),
                "pass": all_ok,
                "note": "" if all_ok else "存在非标准日期格式",
            })
        else:
            checks.append({
                "check": "日期格式",
                "expected": "表头含日期字段",
                "actual": "无日期KV",
                "pass": True,
                "note": "数据不足，跳过",
            })
    except Exception as exc:
        checks.append({"check": "日期格式", "expected": "", "actual": "",
                       "pass": False, "note": f"ERROR: {exc}"})

    # ---- 4. 静默错配嫌疑 ----
    try:
        suspects: list[str] = []
        # 检查明细表 mapping 中语义可疑的映射
        _SUSPECT_SRC_KEYWORDS = ["在途", "配号", "冻结", "质押", "担保"]
        for mapping in detail_mappings:
            for std_field, src_col in mapping.items():
                src_norm = normalize_header(src_col)
                for kw in _SUSPECT_SRC_KEYWORDS:
                    if kw in src_norm:
                        suspects.append(f"{std_field}←{src_col}(含'{kw}')")
        # 市值勾稽失败也标记为错配嫌疑
        mv_check = next((c for c in checks if c["check"] == "市值勾稽"), None)
        if mv_check and not mv_check["pass"] and "ERROR" not in mv_check.get("note", ""):
            suspects.append("市值勾稽失败→明细/汇总映射可能错配")
        checks.append({
            "check": "静默错配嫌疑",
            "expected": "映射列语义等价",
            "actual": f"{len(suspects)} 项嫌疑" if suspects else "无可疑映射",
            "pass": len(suspects) == 0,
            "note": "; ".join(suspects) if suspects else "",
        })
    except Exception as exc:
        checks.append({"check": "静默错配嫌疑", "expected": "", "actual": "",
                       "pass": False, "note": f"ERROR: {exc}"})

    return checks


# =========================================================================
# 单样本编排
# =========================================================================
def process_sample(path: str, schema: Schema) -> dict[str, Any]:
    ext = os.path.splitext(path)[1].lower()
    parser = PARSERS.get(ext)
    result: dict[str, Any] = {
        "file": os.path.basename(path),
        "kind": ext.lstrip("."),
    }
    if parser is None:
        result.update(ok=False, error=f"no parser for {ext}")
        return result

    doc = parser(path)
    result.update(ok=doc.ok, needs_ocr=doc.needs_ocr, note=doc.note, error=doc.error)
    if not doc.ok:
        return result

    # 表头区 KV
    meta = extract_header_meta(doc.text, schema)
    result["header_meta"] = desensitize_record(meta)
    result["header_meta_count"] = len(meta)

    # 逐表映射 + 标准化
    table_reports = []
    for t in doc.tables:
        match = best_schema_match(t.headers, schema)
        std_rows = normalize_rows(t.rows, match.mapping, t.headers)
        hit_rate = (match.hits / len(t.headers) * 100) if t.headers else 0.0
        sample = desensitize_record(std_rows[0]) if std_rows else {}
        table_reports.append({
            "table": t.name,
            "rows": len(t.rows),
            "cols": len(t.headers),
            "matched_schema": match.schema_table,
            "headers": t.headers,
            "mapping": match.mapping,
            "unmapped": match.unmapped,
            "hits": match.hits,
            "hit_rate": round(hit_rate, 1),
            "sample_record": sample,
            "_records": std_rows,
        })
    result["tables"] = table_reports
    result["table_count"] = len(doc.tables)

    # 勾稽校验
    result["reconcile"] = reconcile(table_reports, meta, schema)
    return result


# =========================================================================
# 报告打印
# =========================================================================
def _print_result(res: dict[str, Any]) -> None:
    print("=" * 78)
    print(f"样本: {res['file']}  类型: {res['kind']}  解析OK: {res.get('ok')}")
    if res.get("error"):
        print(f"  ERROR: {res['error']}")
    if res.get("needs_ocr"):
        print(f"  [需OCR] {res.get('note','')}")
    elif res.get("note"):
        print(f"  备注: {res['note']}")
    if not res.get("ok"):
        return
    print(f"  表格数: {res.get('table_count',0)}  表头区KV数: {res.get('header_meta_count',0)}")
    if res.get("header_meta"):
        print(f"  表头区KV(脱敏): {json.dumps(res['header_meta'], ensure_ascii=False)}")
    for t in res.get("tables", []):
        print(f"  -- 表 {t['table']} -> schema[{t['matched_schema']}] "
              f"行x列={t['rows']}x{t['cols']} 命中={t['hits']}/{t['cols']} "
              f"({t['hit_rate']}%) unmapped={t['unmapped']}")
        print(f"     映射: {json.dumps(t['mapping'], ensure_ascii=False)}")
        if t["sample_record"]:
            print(f"     标准记录样例(脱敏): {json.dumps(t['sample_record'], ensure_ascii=False)}")
    for chk in res.get("reconcile", []):
        status = "PASS" if chk["pass"] else "FAIL"
        print(f"  [勾稽] {chk['check']}: {status}  {chk.get('note','')}")
        if not chk["pass"]:
            print(f"         expected={chk['expected']}  actual={chk['actual']}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="M1 对账单解析原型（表头近义词映射）")
    ap.add_argument("--samples-dir", default=DEFAULT_SAMPLES_DIR)
    ap.add_argument("--schema", default=DEFAULT_SCHEMA)
    ap.add_argument("--json", default="", help="把汇总结果(已脱敏)写入该 JSON 文件")
    args = ap.parse_args(argv)

    print(f"libs: fitz={_HAS_FITZ} openpyxl={_HAS_OPENPYXL} docx={_HAS_DOCX}")
    schema = Schema.load(args.schema)
    print(f"schema: {len(schema.tables)} tables, "
          f"{len(schema.header_meta_fields)} header_meta fields")

    samples = sorted(
        os.path.join(args.samples_dir, f)
        for f in os.listdir(args.samples_dir)
        if f.startswith("sample_") or f.startswith("mapping_")
    )
    samples = [s for s in samples if os.path.splitext(s)[1].lower() in PARSERS]

    results = [process_sample(p, schema) for p in samples]
    for res in results:
        _print_result(res)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(results, fh, ensure_ascii=False, indent=2)
        print(f"\n[json] 脱敏汇总已写入 {args.json}")

    # 汇总表
    print("\n" + "=" * 78)
    print("汇总:")
    print(f"{'样本':32} {'类型':5} {'表格':>4} {'表/命中':>10} {'KV':>3} {'需OCR':>6}")
    for res in results:
        if not res.get("ok"):
            print(f"{res['file'][:32]:32} {res['kind']:5}  ERR {res.get('error','')[:30]}")
            continue
        tables = res.get("tables", [])
        hitdesc = ";".join(f"{t['hits']}/{t['cols']}" for t in tables) or "-"
        print(f"{res['file'][:32]:32} {res['kind']:5} {res.get('table_count',0):>4} "
              f"{hitdesc:>10} {res.get('header_meta_count',0):>3} "
              f"{str(res.get('needs_ocr',False)):>6}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
