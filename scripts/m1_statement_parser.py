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
import urllib.request
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

# Project-local schema override (checked before frozen ~/wzh/m1_samples copy)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_SCHEMA = os.path.join(_PROJECT_ROOT, "config", "m1_table_schema.json")


def resolve_schema_path() -> str:
    """Return the active schema path: config/ override first, then frozen default."""
    if os.path.isfile(LOCAL_SCHEMA):
        return LOCAL_SCHEMA
    return DEFAULT_SCHEMA


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
        # 客户端域同义词(内存层，不动冻结 schema 文件)：证券市值≈合计金额类总量
        for t in tables:
            if t.table_name == "资金资产汇总" and not any(f.standard == "证券市值" for f in t.fields):
                t.fields.append(SchemaField("证券市值", ["证券市值", "证券总市值"]))
        # 内存层补充：交易帐号/交易账号 -> 资产账号 (甲方样本常见变体)
        for t in tables:
            if t.table_name == "表头信息":
                for fld in t.fields:
                    if fld.standard == "资产账号":
                        for extra in ("交易帐号", "交易账号"):
                            if extra not in fld.synonyms:
                                fld.synonyms.append(extra)
        # Build header_meta_fields: prefer kv-layout tables, fallback to legacy dict
        meta: dict[str, list[str]] = {}
        for t in tables:
            if t.layout == "kv" and t.table_name != "_unattributed":
                for fld in t.fields:
                    syns = list(fld.synonyms) if fld.synonyms else [fld.standard]
                    meta[fld.standard] = syns
        if not meta:
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
        std_norm = normalize_header(fld.standard)
        if std_norm and std_norm == header_norm:
            key4 = (4, len(std_norm))
            if best is None or key4 > (best[0], best[1]):
                best = (4, len(std_norm), fld.standard)
        for syn in fld.synonyms:
            syn_norm = normalize_header(syn)
            if not syn_norm:
                continue
            if syn_norm == header_norm:
                score = 3
            elif len(syn_norm) >= 2 and (syn_norm in header_norm or header_norm in syn_norm):
                # 包含匹配：更长的 synonym 命中更可信
                score = 2
                # 防止 "在途数量" 通过通用同义词 "数量" 错配到 "持仓数量"
                _SUSPECT_KW = ("在途", "配号", "冻结", "质押", "担保")
                std_norm_fld = normalize_header(fld.standard)
                if any(kw in header_norm and kw not in std_norm_fld for kw in _SUSPECT_KW):
                    continue
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
    """在所有 grid 布局 schema 表中选命中数最高者作为该源表的归属表。"""
    best: MatchResult | None = None
    for st in schema.tables:
        if st.layout == "kv":
            continue
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
        rf"(?P<key>{key_alt})\s*(?:为)?\s*[:：]\s*(?P<val>.*?)"
        rf"(?=\s+(?:{bound_alt})\s*(?:为)?\s*[:：]|$)",
    )
    found: dict[str, str] = {}
    lines = text.splitlines()
    # 用于下一行值fallback时排除"另一个键开头"的行
    bound_prefix_set = set(bound_keys)
    for idx, line in enumerate(lines):
        for m in pattern.finditer(line):
            std = syn2std.get(m.group("key"), m.group("key"))
            val = m.group("val").strip().strip(" \t,，;；")
            if val and std not in found:
                found[std] = val
            elif not val and std not in found:
                # 值为空(键在行尾、值在下一行)：向下看最多2行
                for j in range(idx + 1, min(idx + 3, len(lines))):
                    nxt = lines[j].strip()
                    if not nxt:
                        continue
                    # 如果下一行以已知键名开头，说明不是值，跳过
                    if any(nxt.startswith(bk) for bk in bound_prefix_set):
                        break
                    found[std] = nxt.strip(" \t,，;；")
                    break
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
    ocr_used: bool = False
    ocr_engine: str = ""


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


# =========================================================================
# OCR 兜底：影像件 PDF/DOCX -> 提取图片 -> PaddleOCR / :8004 视觉模型
# =========================================================================
_OCR_PADDLE_PYTHON = os.path.expanduser(
    "~/miniconda3/envs/wzh_vision/bin/python")
_OCR_PADDLE_SCRIPT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "m1_ocr_fallback.py")
_OCR_VISION_ENDPOINT = os.environ.get(
    "M1_OCR_VISION_ENDPOINT", "http://127.0.0.1:8004/v1/chat/completions")
_OCR_VISION_MODEL = os.environ.get(
    "M1_OCR_VISION_MODEL", "Qwen3.6-35B-A3B-Q4_K_M.gguf")
_OCR_VISION_PROMPT = (
    "Extract all text and tables from this financial document image. "
    "IMPORTANT: For any tabular data, you MUST output it as a markdown table "
    "with | column separators and a header row separated by |---|. "
    "Example:\n"
    "| Column1 | Column2 | Column3 |\n"
    "|---------|---------|---------|\n"
    "| value1  | value2  | value3  |\n\n"
    "Preserve all numbers exactly as shown. Do not summarize or omit any rows. "
    "For non-table text, preserve reading order.")
_OCR_TIMEOUT = float(os.environ.get("M1_OCR_TIMEOUT", "120"))
# Vision engine (:8004) concurrency. llama-server is started with 4 slots, so 4
# parallel requests match its capacity; tune via env if the server config changes.
_OCR_VISION_WORKERS = int(os.environ.get("M1_OCR_VISION_WORKERS", "4"))
# Per-image vision timeout. Scanned pages can take ~60-70s each, so default above
# the old hard-coded 60s to avoid silently dropping slow pages.
_OCR_VISION_TIMEOUT = float(os.environ.get("M1_OCR_VISION_TIMEOUT", "120"))
_PADDLEOCR_INCOMPATIBLE_MARKER = "PADDLEOCR_INCOMPATIBLE"
# Set True after the PaddleOCR subprocess reports a permanent incompatibility
# (e.g. transformers>=5.0), so later calls skip the subprocess entirely.
_PADDLEOCR_UNAVAILABLE = False
_MD_TABLE_SEP_RE = re.compile(r"^\s*\|[\s\-:|]+\|\s*$")


def _extract_pdf_page_images(path: str) -> list[bytes]:
    """Render each PDF page as a PNG (200 DPI) for OCR."""
    images: list[bytes] = []
    if not _HAS_FITZ:
        return images
    try:
        pdf = fitz.open(path)
        for page in pdf:
            try:
                pix = page.get_pixmap(dpi=200)
                images.append(pix.tobytes("png"))
            except Exception:
                for img_info in page.get_images():
                    try:
                        xref = img_info[0]
                        ipix = fitz.Pixmap(pdf, xref)
                        if ipix.n > 4:
                            ipix = fitz.Pixmap(fitz.csRGB, ipix)
                        images.append(ipix.tobytes("png"))
                    except Exception:
                        pass
        pdf.close()
    except Exception:
        pass
    return images


def _extract_docx_images(path: str) -> list[bytes]:
    """Extract embedded images from DOCX word/media/ via zipfile."""
    images: list[bytes] = []
    _IMG_EXT = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".gif")
    try:
        import zipfile
        with zipfile.ZipFile(path) as zf:
            for name in sorted(zf.namelist()):
                if name.startswith("word/media/") and name.lower().endswith(_IMG_EXT):
                    images.append(zf.read(name))
    except Exception:
        pass
    return images


def _try_paddleocr(images: list[bytes], source_name: str) -> str:
    """PaddleOCR VL subprocess (scripts/m1_ocr_fallback.py manifest pattern).

    Returns "" on any failure so the caller falls back to the vision engine.
    If the subprocess reports a permanent incompatibility (transformers>=5.0),
    _PADDLEOCR_UNAVAILABLE is latched so later calls skip the spawn entirely.
    """
    global _PADDLEOCR_UNAVAILABLE
    if _PADDLEOCR_UNAVAILABLE:
        return ""
    if not os.path.isfile(_OCR_PADDLE_PYTHON) or not os.path.isfile(_OCR_PADDLE_SCRIPT):
        return ""
    import shutil
    import subprocess
    import tempfile
    tmpdir = tempfile.mkdtemp(prefix="m1_ocr_")
    try:
        manifest_images = []
        for idx, img_bytes in enumerate(images):
            png_name = f"img_{idx:03d}.png"
            png_path = os.path.join(tmpdir, png_name)
            with open(png_path, "wb") as fh:
                fh.write(img_bytes)
            manifest_images.append({
                "sample": source_name, "unit": f"img_{idx:03d}",
                "png": png_path, "png_basename": png_name,
                "width": 0, "height": 0,
            })
        manifest_path = os.path.join(tmpdir, "manifest.json")
        out_path = os.path.join(tmpdir, "ocr_results.json")
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump({"images": manifest_images}, fh)
        proc = subprocess.run(
            [_OCR_PADDLE_PYTHON, _OCR_PADDLE_SCRIPT,
             "--manifest", manifest_path, "--out", out_path],
            capture_output=True, text=True, timeout=_OCR_TIMEOUT,
        )
        if proc.returncode != 0 or not os.path.isfile(out_path):
            signal_text = f"{proc.stdout or ''}\n{proc.stderr or ''}"
            if _PADDLEOCR_INCOMPATIBLE_MARKER in signal_text:
                _PADDLEOCR_UNAVAILABLE = True
            return ""
        with open(out_path, encoding="utf-8") as fh:
            payload = json.load(fh)
        texts = [r["text"] for r in payload.get("results", [])
                 if r.get("status") == "ok" and r.get("text", "").strip()]
        return "\n\n".join(texts)
    except Exception:
        return ""
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _vision_ocr_one(img_bytes: bytes) -> str:
    """OCR a single image via :8004 /v1/chat/completions (mmproj vision).

    Returns extracted text or "" on any error. Runs inside a worker thread.
    Results are cached by image hash to avoid redundant vision calls.
    """
    import base64
    import hashlib

    # --- OCR cache: skip vision call for previously-seen images ---
    _OCR_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".ocr_cache")
    img_hash = hashlib.sha256(img_bytes).hexdigest()[:16]
    cache_path = os.path.join(_OCR_CACHE_DIR, f"{img_hash}.txt")
    if os.path.isfile(cache_path):
        try:
            cached = open(cache_path, "r", encoding="utf-8").read()
            if cached.strip():
                return cached
        except Exception:
            pass

    b64 = base64.b64encode(img_bytes).decode("ascii")
    payload = {
        "model": _OCR_VISION_MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "image_url",
             "image_url": {"url": f"data:image/png;base64,{b64}"}},
            {"type": "text", "text": _OCR_VISION_PROMPT},
        ]}],
        "temperature": 0,
        "max_tokens": 2048,
    }
    try:
        req = urllib.request.Request(
            _OCR_VISION_ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=_OCR_VISION_TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        result = content.strip() if content and content.strip() else ""
        # Write to cache
        if result:
            try:
                os.makedirs(_OCR_CACHE_DIR, exist_ok=True)
                open(cache_path, "w", encoding="utf-8").write(result)
            except Exception:
                pass
        return result
    except Exception:
        return ""



# ---------------------------------------------------------------------------
# VLM table extraction (:8007 Qwen3-VL-8B, falls back to :8004 mmproj)
# ---------------------------------------------------------------------------
_VLM_ENDPOINT = os.environ.get(
    "M1_VLM_ENDPOINT", "http://127.0.0.1:8007/v1/chat/completions")
_VLM_MODEL = os.environ.get("M1_VLM_MODEL", "Qwen3-VL-8B-Instruct")
_VLM_PROMPT = (
    "请识别图片中的表格，以 markdown 表格格式输出。"
    "保留所有列名和数据值，不要省略任何行。"
    "如果图片中有多个表格，分别输出。"
    "如果图片中没有表格，输出图片中的所有文字。")
_VLM_TIMEOUT = float(os.environ.get("M1_VLM_TIMEOUT", "60"))
_vlm_available: bool | None = None  # cached health check


def _check_vlm_available() -> bool:
    """Check if :8007 VLM server is running (cached)."""
    global _vlm_available
    if _vlm_available is not None:
        return _vlm_available
    try:
        req = urllib.request.Request(
            _VLM_ENDPOINT.replace("/v1/chat/completions", "/health"),
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            _vlm_available = resp.status == 200
    except Exception:
        _vlm_available = False
    return _vlm_available


def _vlm_ocr_one(img_bytes: bytes) -> str:
    """Send image to VLM (:8007) for table-aware OCR. Returns text or empty."""
    import base64
    b64 = base64.b64encode(img_bytes).decode("ascii")
    payload = {
        "model": _VLM_MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            {"type": "text", "text": _VLM_PROMPT},
        ]}],
        "temperature": 0,
        "max_tokens": 4096,
    }
    try:
        req = urllib.request.Request(
            _VLM_ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=_VLM_TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        return content.strip() if content and content.strip() else ""
    except Exception:
        return ""


def _try_vlm_table(images: list[bytes]) -> str:
    """Try VLM (:8007) for table-aware OCR. Falls back to empty string.

    If VLM is not available, returns "" immediately (caller will use mmproj).
    If VLM output contains markdown table markers (|), returns the text
    which can be parsed by _parse_markdown_tables.
    """
    if not _check_vlm_available():
        return ""
    if not images:
        return ""
    # Process images concurrently (same pattern as _try_vision_ocr)
    workers = max(1, min(4, len(images)))
    if workers == 1:
        texts = [_vlm_ocr_one(img) for img in images]
    else:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=workers) as pool:
            texts = list(pool.map(_vlm_ocr_one, images))
    return "\n\n".join(t for t in texts if t.strip())


def _try_vision_ocr(images: list[bytes]) -> str:
    """Fallback: base64 images -> :8004 /v1/chat/completions (mmproj vision).

    Images are processed concurrently (ThreadPoolExecutor, _OCR_VISION_WORKERS)
    to cut multi-page DOCX/PDF OCR wall time. pool.map preserves input order so
    the concatenated text keeps reading order.
    """
    if not images:
        return ""
    workers = max(1, min(_OCR_VISION_WORKERS, len(images)))
    if workers == 1:
        texts = [_vision_ocr_one(img) for img in images]
    else:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=workers) as pool:
            texts = list(pool.map(_vision_ocr_one, images))
    return "\n\n".join(t for t in texts if t.strip())


def _ocr_fallback(path: str, kind: str) -> tuple[str, str]:
    """OCR 兜底入口：提取图片 -> PaddleOCR -> :8004 视觉。

    Returns (extracted_text, engine_name); engine_name="" if all failed.
    """
    if kind == "pdf":
        images = _extract_pdf_page_images(path)
    elif kind == "docx":
        images = _extract_docx_images(path)
    else:
        return "", ""
    if not images:
        return "", ""
    text = _try_paddleocr(images, os.path.basename(path))
    if text.strip():
        return text, "paddleocr-vl"
    # Try VLM (:8007) first - outputs markdown tables directly
    vlm_text = _try_vlm_table(images)
    if vlm_text.strip():
        return vlm_text, "vlm-8007"
    # Fall back to mmproj vision OCR (:8004)
    text = _try_vision_ocr(images)
    if text.strip():
        return text, "vision-8004"
    return "", ""


def _parse_markdown_tables(text: str) -> list[ParsedTable]:
    """Parse markdown pipe-tables from OCR text into ParsedTable objects."""
    tables: list[ParsedTable] = []
    lines = text.splitlines()
    i, tidx = 0, 0
    while i < len(lines):
        line = lines[i].strip()
        if (line.startswith("|") and i + 1 < len(lines)
                and _MD_TABLE_SEP_RE.match(lines[i + 1])):
            headers = [c.strip() for c in line.strip("|").split("|") if c.strip()]
            j = i + 2
            rows: list[list[str]] = []
            while j < len(lines) and lines[j].strip().startswith("|"):
                cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                if any(c for c in cells):
                    rows.append(cells)
                j += 1
            if headers:
                tidx += 1
                tables.append(ParsedTable(f"ocr_table_{tidx}", headers, rows))
            i = j
            continue
        i += 1
    return tables



# =========================================================================
# Fallback: text-line-based table detection for borderless PDFs
# =========================================================================
_KV_LINE_RE = re.compile(r"^(?P<key>[^\s：:]{2,30})\s*[：:]\s*(?P<val>.+)$")


def _text_lines_to_tables(text: str) -> list[ParsedTable]:
    """Regex fallback: extract tables from plain text when find_tables fails.

    Two strategies tried in order:
    1. Multi-space column detection: consecutive lines split by 2+ spaces
       with consistent column count (>= 2) form a grid table.
    2. Repeating KV-block detection: groups of key：value lines sharing a
       repeated anchor key are pivoted into a grid table (one row per block).
    """
    tables: list[ParsedTable] = []

    # --- Strategy 1: multi-space-separated columns ---
    lines = text.splitlines()
    run: list[list[str]] = []
    tidx = 0
    for line in lines:
        cells = [c.strip() for c in re.split(r"\s{2,}", line.strip()) if c.strip()]
        if len(cells) >= 2:
            run.append(cells)
        else:
            if len(run) >= 3:
                ncols = max(len(r) for r in run)
                if min(len(r) for r in run) >= 2:
                    padded = [r + [""] * (ncols - len(r)) for r in run]
                    tidx += 1
                    tables.append(ParsedTable(f"text_col_{tidx}", padded[0], padded[1:]))
            run = []
    if len(run) >= 3:
        ncols = max(len(r) for r in run)
        if min(len(r) for r in run) >= 2:
            padded = [r + [""] * (ncols - len(r)) for r in run]
            tidx += 1
            tables.append(ParsedTable(f"text_col_{tidx}", padded[0], padded[1:]))

    # --- Strategy 1.5: single-space separated columns (loose) ---
    # For OCR text where columns are separated by single spaces but have
    # consistent column counts >= 3 (e.g. Huatai OCR output)
    run15: list[list[str]] = []
    tidx15 = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if len(run15) >= 3:
                ncols = max(len(r) for r in run15)
                if ncols >= 3 and min(len(r) for r in run15) >= 3:
                    # Check column count consistency: at least 80% of rows have same count
                    from collections import Counter
                    counts = Counter(len(r) for r in run15)
                    most_common_count, most_common_freq = counts.most_common(1)[0]
                    if most_common_count >= 3 and most_common_freq >= len(run15) * 0.7:
                        padded = [r + [""] * (most_common_count - len(r)) if len(r) < most_common_count else r[:most_common_count] for r in run15]
                        tidx15 += 1
                        tables.append(ParsedTable(f"text_loose_{tidx15}", padded[0], padded[1:]))
            run15 = []
            continue
        cells = [c.strip() for c in re.split(r"\s+", stripped) if c.strip()]
        if len(cells) >= 3:
            run15.append(cells)
        else:
            if len(run15) >= 3:
                ncols = max(len(r) for r in run15)
                if ncols >= 3 and min(len(r) for r in run15) >= 3:
                    from collections import Counter
                    counts = Counter(len(r) for r in run15)
                    most_common_count, most_common_freq = counts.most_common(1)[0]
                    if most_common_count >= 3 and most_common_freq >= len(run15) * 0.7:
                        padded = [r + [""] * (most_common_count - len(r)) if len(r) < most_common_count else r[:most_common_count] for r in run15]
                        tidx15 += 1
                        tables.append(ParsedTable(f"text_loose_{tidx15}", padded[0], padded[1:]))
            run15 = []
    if len(run15) >= 3:
        ncols = max(len(r) for r in run15)
        if ncols >= 3 and min(len(r) for r in run15) >= 3:
            from collections import Counter
            counts = Counter(len(r) for r in run15)
            most_common_count, most_common_freq = counts.most_common(1)[0]
            if most_common_count >= 3 and most_common_freq >= len(run15) * 0.7:
                padded = [r + [""] * (most_common_count - len(r)) if len(r) < most_common_count else r[:most_common_count] for r in run15]
                tidx15 += 1
                tables.append(ParsedTable(f"text_loose_{tidx15}", padded[0], padded[1:]))

        # --- Strategy 2: repeating KV blocks -> grid ---
    kv_pairs: list[tuple[str, str]] = []
    for line in lines:
        m = _KV_LINE_RE.match(line.strip())
        if m:
            key = m.group("key").rstrip("为")
            kv_pairs.append((key, m.group("val").strip()))
    if len(kv_pairs) >= 4:
        blocks: list[dict[str, str]] = []
        current: dict[str, str] = {}
        for key, val in kv_pairs:
            if key in current:
                if len(current) >= 2:
                    blocks.append(current)
                current = {}
            current[key] = val
        if len(current) >= 2:
            blocks.append(current)
        if len(blocks) >= 2:
            common = list(blocks[0].keys())
            for b in blocks[1:]:
                common = [k for k in common if k in b]
            if len(common) >= 2:
                tidx += 1
                headers = common
                rows = [[b.get(k, "") for k in headers] for b in blocks]
                tables.append(ParsedTable(f"kv_grid_{tidx}", headers, rows))

    return tables



def _coordinate_table_reconstruction(path: str) -> list[ParsedTable]:
    """Reconstruct tables from PDF text span coordinates.

    Fallback for PDFs where find_tables() fails (e.g. vertical layout,
    no grid lines). Groups text spans by y-coordinate into rows,
    detects header row by matching known schema field names,
    then assigns data spans to columns by x-overlap.
    """
    try:
        import fitz
    except ImportError:
        return []

    # Load schema for header detection
    schema_path = resolve_schema_path()
    try:
        schema = Schema.load(schema_path)
    except Exception:
        return []

    # Collect all known header names from schema
    known_headers: set[str] = set()
    for st in schema.tables:
        for fld in st.fields:
            known_headers.add(fld.standard)
            for syn in fld.synonyms:
                known_headers.add(syn)

    doc = fitz.open(path)
    tables: list[ParsedTable] = []

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        blocks = page.get_text("dict")["blocks"]

        # Collect spans with coordinates
        spans = []
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if text:
                        bbox = span["bbox"]
                        spans.append({
                            "text": text,
                            "x0": bbox[0], "y0": bbox[1],
                            "x1": bbox[2], "y1": bbox[3],
                            "cy": (bbox[1] + bbox[3]) / 2,
                        })

        if not spans:
            continue

        # Group by y-coordinate into rows
        spans.sort(key=lambda s: (s["cy"], s["x0"]))
        rows: list[list[dict]] = []
        current_row = [spans[0]]
        row_y = spans[0]["cy"]
        for s in spans[1:]:
            if abs(s["cy"] - row_y) < 5:
                current_row.append(s)
            else:
                rows.append(current_row)
                current_row = [s]
                row_y = s["cy"]
        if current_row:
            rows.append(current_row)

        # Find header rows (rows where multiple cells match known headers)
        for hi, row in enumerate(rows):
            texts = [s["text"] for s in row]
            matches = sum(1 for t in texts if t in known_headers or any(t in kh or kh in t for kh in known_headers if len(kh) >= 2))
            if matches < 3 or len(row) < 3:
                continue

            # This looks like a header row
            header_spans = sorted(row, key=lambda s: s["x0"])
            headers = [s["text"] for s in header_spans]
            col_ranges = [(s["x0"] - 10, s["x1"] + 10) for s in header_spans]

            # Extract data rows
            data_rows: list[list[str]] = []
            for di in range(hi + 1, len(rows)):
                drow = rows[di]
                drow_texts = [s["text"] for s in drow]

                # Stop if we hit another header row or footer
                drow_matches = sum(1 for t in drow_texts if t in known_headers)
                if drow_matches >= 3 and len(drow) >= 3:
                    break  # next table header
                if any("温馨提示" in t or "本账单" in t or "友情提示" in t for t in drow_texts):
                    break
                if len(drow) < 2:
                    continue

                # Assign spans to columns by x-overlap
                cells = [""] * len(headers)
                for s in sorted(drow, key=lambda s: s["x0"]):
                    best_col = 0
                    best_overlap = 0
                    for ci, (cx0, cx1) in enumerate(col_ranges):
                        overlap = max(0, min(s["x1"], cx1) - max(s["x0"], cx0))
                        if overlap > best_overlap:
                            best_overlap = overlap
                            best_col = ci
                    if cells[best_col]:
                        cells[best_col] += " " + s["text"]
                    else:
                        cells[best_col] = s["text"]

                if any(c.strip() for c in cells):
                    data_rows.append(cells)

            if data_rows:
                tidx = len(tables) + 1
                tables.append(ParsedTable(f"coord_table_{tidx}", headers, data_rows))

    doc.close()
    return tables


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
            page_text = page.get_text()
            all_text.append(page_text)
            total_images += len(page.get_images())
            try:
                found = page.find_tables()
            except Exception:
                found = None
            # Fallback (a): text-based strategy for borderless tables
            if (not found or not found.tables) and page_text.strip():
                try:
                    found = page.find_tables(strategy="text")
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
        # Fallback (b): regex text-line parsing for borderless/KV tables
        if doc.text.strip():
            text_tables = _text_lines_to_tables(doc.text)
            doc.tables.extend(text_tables)
        # Coordinate reconstruction: always try, prefer if better than find_tables
        coord_tables = _coordinate_table_reconstruction(path)
        if coord_tables:
            # Use coordinate tables if find_tables produced junk (low column count
            # or single-column tables from watermark/vertical text)
            find_tables_junk = all(
                len(t.headers) <= 2 or len(t.rows) == 0 for t in doc.tables
            ) if doc.tables else True
            if find_tables_junk:
                doc.tables = coord_tables
        if not doc.text.strip() and total_images > 0 and not doc.tables:
            doc.needs_ocr = True
            doc.note = f"image-only PDF ({total_images} image(s), no text layer) -> needs OCR/vision"
            ocr_text, ocr_engine = _ocr_fallback(path, "pdf")
            if ocr_text.strip():
                doc.text = ocr_text
                doc.tables = _parse_markdown_tables(ocr_text)
                doc.ocr_used = True
                doc.ocr_engine = ocr_engine
                doc.note = (f"OCR applied ({ocr_engine}, "
                            f"{len(doc.tables)} table(s) from OCR); "
                            + doc.note)
            else:
                doc.note = f"OCR attempted but failed; {doc.note}"
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
                ocr_text, ocr_engine = _ocr_fallback(path, "docx")
                if ocr_text.strip():
                    doc.text = ocr_text
                    doc.tables = _parse_markdown_tables(ocr_text)
                    doc.ocr_used = True
                    doc.ocr_engine = ocr_engine
                    doc.note = (f"OCR applied ({ocr_engine}, "
                                f"{len(doc.tables)} table(s) from OCR); "
                                + doc.note)
                else:
                    doc.note = f"OCR attempted but failed; {doc.note}"
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


# 明细表的「合计/小计/总计」汇总行标记。若与数据行一起求和会重复计数。
_TOTAL_ROW_MARKERS = ("合计", "小计", "总计")


def _is_total_row(rec: dict[str, str]) -> bool:
    """判断某标准化记录是否为汇总行（任一字段值含「合计/小计/总计」）。

    标记只可能出现在标签类字段（证券名称/股东账号/摘要等），数值字段不会含这些词。
    """
    for v in rec.values():
        if v and any(m in v for m in _TOTAL_ROW_MARKERS):
            return True
    return False


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
        # 明细表常含「合计/小计」汇总行；若与数据行一起求和会重复计数
        # (jiaxing 案例: 1 数据行 + 1 合计行 -> sum 翻倍 -> 401M 假差异)。
        detail_data = [r for r in detail_records if not _is_total_row(r)]
        mv_vals = [_parse_number(r.get("市值", "")) for r in detail_data]
        mv_vals = [v for v in mv_vals if v is not None]
        total_mv = sum(mv_vals) if mv_vals else None

        summary_total = None
        summary_field = None
        # 市值勾稽应对比「市值类」总量(资产市值/证券市值)，其次才是
        # 合计/资产总值/总资产（总资产=市值+资金余额，含现金会引入偏差）。
        for r in summary_records:
            for fld in ("资产市值", "证券市值", "合计金额", "资产总值", "总资产"):
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
                std_norm = normalize_header(std_field)
                for kw in _SUSPECT_SRC_KEYWORDS:
                    if kw in src_norm and kw not in std_norm:
                        suspects.append(f"{std_field}←{src_col}(含'{kw}')")
        # 市值勾稽失败由独立检查项报告，不再作为错配嫌疑
        # (市值差异可能源于数据本身而非映射错误)
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

    # ---- disposition 标注 (Loop C Cycle 5: 区分真实通过 / 跳过 / 失败) ----
    for chk in checks:
        note = chk.get("note", "")
        if "数据不足" in note or "跳过" in note:
            chk["disposition"] = "skipped"
        elif chk.get("pass"):
            chk["disposition"] = "real_pass"
        else:
            chk["disposition"] = "fail"

    return checks


# =========================================================================
# _unattributed 兜底 KV 扫描
# =========================================================================
def scan_unattributed_kv(text: str, schema: Schema) -> dict[str, str]:
    """对文档剩余文本做一轮 kv 扫描，匹配 _unattributed 表的字段。"""
    ua_table = None
    for t in schema.tables:
        if t.table_name == "_unattributed" and t.layout == "kv":
            ua_table = t
            break
    if ua_table is None or not ua_table.fields:
        return {}
    syn2std: dict[str, str] = {}
    for fld in ua_table.fields:
        for syn in (fld.synonyms or [fld.standard]):
            syn2std[syn] = fld.standard
        syn2std.setdefault(fld.standard, fld.standard)
    keys = sorted(syn2std.keys(), key=len, reverse=True)
    if not keys:
        return {}
    key_alt = "|".join(re.escape(k) for k in keys)
    pattern = re.compile(rf"(?P<key>{key_alt})\s*[:：]\s*(?P<val>.+?)(?:\s|$)")
    found: dict[str, str] = {}
    lines = text.splitlines()
    # 用于下一行值fallback时排除"另一个键开头"的行
    bound_prefix_set = set(keys)
    for idx, line in enumerate(lines):
        for m in pattern.finditer(line):
            std = syn2std.get(m.group("key"), m.group("key"))
            val = m.group("val").strip().strip(" \t,，;；")
            if val and std not in found:
                found[std] = val
            elif not val and std not in found:
                # 值为空(键在行尾、值在下一行)：向下看最多2行
                for j in range(idx + 1, min(idx + 3, len(lines))):
                    nxt = lines[j].strip()
                    if not nxt:
                        continue
                    # 如果下一行以已知键名开头，说明不是值，跳过
                    if any(nxt.startswith(bk) for bk in bound_prefix_set):
                        break
                    found[std] = nxt.strip(" \t,，;；")
                    break
    return found


# =========================================================================
# LLM 兜底：对 unmapped 源列调用本地 35B 模型抽值
# =========================================================================
# 默认端点/模型可被环境变量覆盖；调用失败一律优雅降级为 {}（规则结果不受影响）。
LLM_ENDPOINT = os.environ.get(
    "M1_LLM_ENDPOINT", "http://127.0.0.1:8004/v1/chat/completions")
LLM_MODEL = os.environ.get("M1_LLM_MODEL", "Qwen3.6-35B-A3B-Q4_K_M.gguf")
LLM_TIMEOUT = float(os.environ.get("M1_LLM_TIMEOUT", "30"))
# 送入 prompt 的文本上限，避免超长上下文（35B 服务 64K，留足余量）。
_LLM_TEXT_LIMIT = 12000


def _llm_extract_json(content: str) -> dict | None:
    """从 LLM 输出里稳健地取出第一个 JSON 对象（容忍 ```json 围栏/前后缀）。"""
    if not content:
        return None
    s = str(content).strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```\s*$", "", s)
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    start, end = s.find("{"), s.rfind("}")
    if start != -1 and end > start:
        try:
            obj = json.loads(s[start:end + 1])
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None
    return None


def llm_fallback_unmapped(text: str, unmapped_cols: list[str],
                          schema_table_name: str) -> dict[str, str]:
    """对规则映射后仍未映射的源列，调用本地 35B 模型从文档文本中抽值。

    - prompt 列出 unmapped 列名，要求按三态输出 JSON：
      有数据->取第一个值 / 有表头无数据->"无" / 列名缺失->""；
    - 通过 chat_template_kwargs.enable_thinking=false 关闭思考，temperature=0；
    - 单次调用 30s 超时；任何异常/非法 JSON 一律返回 {}（规则结果兜底不变）。

    返回 {col_name: extracted_value}（仅含非空值）。
    """
    cols = [c for c in (unmapped_cols or []) if c and str(c).strip()]
    if not cols:
        return {}
    cols_desc = "\n".join(f"  * {c}" for c in cols)
    snippet = (text or "")[:_LLM_TEXT_LIMIT]
    prompt = (
        "任务：在对账单/报表纯文本中，判断指定列是否有数据并抽取值。\n"
        "背景：文本由表格压平而来，含「列名行」与「数据行」；很多明细表只有列名、没有数据行。"
        "列名可能因排版被换行拆开（如\"财汇局征\"+\"费\"实为\"财汇局征费\"），请合并理解。\n"
        f"归属表：{schema_table_name or '未知'}。\n\n"
        "判定规则（对每个指定列）：\n"
        "  A. 文本里有该列的【真实数据值】(数字/金额/日期/备注文字等) -> 抽取第一个非空值；\n"
        "  B. 该列名出现、但所在表格没有数据行(只有表头) -> 输出\"无\"；\n"
        "  C. 该列名在文本中完全找不到 -> 输出\"\"(空字符串)。\n"
        "严禁把【其它列名/表头词】当作值输出；若某列名之后紧跟的仍是其它列名，说明无数据，判 B。\n\n"
        f"指定列：\n{cols_desc}\n\n"
        f"对账单文本：\n```\n{snippet}\n```\n\n"
        "只输出一个 JSON 对象，键=列名，值=字符串(数据值/\"无\"/\"\")，不要解释或 markdown。\n"
        "示例：{\"列名A\":\"123.45\",\"列名B\":\"无\",\"列名C\":\"\"}"
    )
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 1024,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    try:
        req = urllib.request.Request(
            LLM_ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=LLM_TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        data = _llm_extract_json(content)
        if not isinstance(data, dict):
            return {}
        allowed = set(cols)
        out: dict[str, str] = {}
        for k, v in data.items():
            if k in allowed and v is not None and str(v).strip():
                out[k] = str(v).strip()
        return out
    except Exception:
        return {}


# =========================================================================
# 单样本编排
# =========================================================================
def process_sample(path: str, schema: Schema, llm_fallback: bool = False) -> dict[str, Any]:
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
    result.update(ocr_used=doc.ocr_used, ocr_engine=doc.ocr_engine)
    if not doc.ok:
        return result

    # 路由伪网格表(表头信息区 kv 块)：从 doc.tables 移除，文本回流 doc.text，
    # 使其被表头区 KV 提取捕获。这是路由不是隐藏；判定=无表头命中且含全角冒号 kv。
    kept = []
    extra = []
    for t in doc.tables:
        cells = [c for c in t.headers if c] + [c for r in t.rows for c in r if c]
        n_fw = sum(1 for c in cells if "：" in c)
        pre_match = best_schema_match(t.headers, schema)
        if pre_match.hits == 0 and n_fw >= 2:
            for r in ([t.headers] + t.rows):
                line = " ".join(c for c in r if c and c.strip())
                if line:
                    extra.append(line)
            result["note"] = (result.get("note") or "") + " [reclassified kv-block: " + t.name + "]"
        else:
            kept.append(t)
    if extra:
        doc.text = doc.text + chr(10) + chr(10).join(extra)
    doc.tables = kept

    # 表头区 KV（优先用 kv 表字段）
    meta = extract_header_meta(doc.text, schema)
    # _unattributed 兜底扫描
    ua_kv = scan_unattributed_kv(doc.text, schema)
    for k, v in ua_kv.items():
        if k not in meta:
            meta[k] = v
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

    # LLM 兜底：对仍有 unmapped 列的表，调用本地 35B 抽值并合并（默认关闭，
    # 由脚本入口显式开启；Web/实验脚本等直接调用方保持纯规则行为不变）。
    if llm_fallback:
        # 全文表头词表：拦截「把其它列名当值」的幻觉（unmapped 列本身也是表头）。
        header_vocab = {normalize_header(h) for t in doc.tables for h in t.headers}
        llm_total = 0
        for tr in table_reports:
            if not tr.get("unmapped"):
                continue
            extracted = llm_fallback_unmapped(doc.text, tr["unmapped"],
                                              tr["matched_schema"])
            if not extracted:
                continue
            still: list[str] = []
            llm_vals: dict[str, str] = {}
            for col in tr["unmapped"]:
                val = extracted.get(col, "").strip()
                # 空值=未抽到，保持 unmapped；值若是其它表头词，判为幻觉丢弃。
                if not val or normalize_header(val) in header_vocab:
                    still.append(col)
                    continue
                llm_vals[col] = desensitize_value(col, val)
            if llm_vals:
                tr["llm_extracted"] = llm_vals
                tr["unmapped"] = still
                llm_total += len(llm_vals)
        if llm_total:
            result["note"] = (result.get("note") or "") + \
                f" [llm-fallback: {llm_total} cols extracted]"

    # 勾稽校验
    result["reconcile"] = reconcile(table_reports, meta, schema)
    return result


# =========================================================================
# 只读诊断：收集 unmapped 源列（冷启动候选）
# =========================================================================
def collect_unmapped_columns(sample_paths: list[str], schema: Schema) -> dict[str, Any]:
    """只读收集各样本 unmapped 源列 + 脱敏样本值，按 (归属 schema 表, 列名) 去重。

    复用既有 PARSERS / best_schema_match / desensitize_value，不改动解析逻辑；
    仅为未知表头冷启动提供候选清单（列名 + 前 3 个脱敏样本值 + 所属表）。
    """
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    total_occurrences = 0
    for path in sample_paths:
        parser = PARSERS.get(os.path.splitext(path)[1].lower())
        if parser is None:
            continue
        doc = parser(path)
        if not doc.ok:
            continue
        fname = os.path.basename(path)
        for t in doc.tables:
            match = best_schema_match(t.headers, schema)
            if not match.unmapped:
                continue
            col_idx = {h: i for i, h in enumerate(t.headers)}
            for col in match.unmapped:
                ci = col_idx.get(col)
                vals: list[str] = []
                if ci is not None:
                    for row in t.rows:
                        if ci < len(row) and (row[ci] or "").strip():
                            raw = (row[ci] or "").replace("\n", "").strip()
                            vals.append(desensitize_value(col, raw))
                        if len(vals) >= 3:
                            break
                total_occurrences += 1
                key = (match.schema_table, col)
                entry = by_key.get(key)
                if entry is None:
                    entry = {
                        "column": col,
                        "matched_schema": match.schema_table,
                        "tables": [],
                        "files": [],
                        "sample_values": [],
                        "occurrence_count": 0,
                    }
                    by_key[key] = entry
                entry["occurrence_count"] += 1
                if t.name not in entry["tables"]:
                    entry["tables"].append(t.name)
                if fname not in entry["files"]:
                    entry["files"].append(fname)
                for v in vals:
                    if v and v not in entry["sample_values"] and len(entry["sample_values"]) < 3:
                        entry["sample_values"].append(v)
    unique = sorted(by_key.values(), key=lambda e: (e["matched_schema"], e["column"]))
    return {
        "total_unmapped_occurrences": total_occurrences,
        "unique_column_count": len(unique),
        "unique_columns": unique,
    }


# =========================================================================
# 紧凑摘要（供 evidence-verifier 复核，体积 << 16K tokens）
# =========================================================================
_RECONCILE_KEY_MAP = {
    "市值勾稽": "market_value",
    "币种一致": "currency",
    "日期格式": "date",
    "静默错配嫌疑": "silent_mismatch",
}


def build_compact_summary(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """从全量结果构建紧凑摘要：每样本仅保留勾稽结论 + unmapped 列名。"""
    compact = []
    for res in results:
        entry: dict[str, Any] = {
            "sample_id": res["file"],
            "n_tables": res.get("table_count", 0),
        }
        if not res.get("ok"):
            entry["error"] = res.get("error", "parse failed")
            compact.append(entry)
            continue
        reconcile: dict[str, str] = {}
        for chk in res.get("reconcile", []):
            key = _RECONCILE_KEY_MAP.get(chk["check"], chk["check"])
            if "数据不足" in chk.get("note", ""):
                reconcile[key] = "SKIP"
            else:
                reconcile[key] = "PASS" if chk["pass"] else "FAIL"
        entry["reconcile"] = reconcile
        unmapped_cols: list[str] = []
        for t in res.get("tables", []):
            unmapped_cols.extend(t.get("unmapped", []))
        entry["n_unmapped"] = len(unmapped_cols)
        if unmapped_cols:
            entry["unmapped_cols"] = unmapped_cols
        compact.append(entry)
    return compact


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
        if t.get("llm_extracted"):
            print(f"     LLM兜底抽取(脱敏): {json.dumps(t['llm_extracted'], ensure_ascii=False)}")
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
    ap.add_argument("--dump-unmapped", default="",
                        help="只读：把 unmapped 源列(带脱敏样本值)去重后写入该 JSON")
    ap.add_argument("--compact-summary", default="",
                        help="紧凑勾稽摘要 JSON（< 2KB），供 evidence-verifier 复核")
    ap.add_argument("--no-llm", action="store_true",
                        help="关闭 unmapped 列的本地 35B LLM 兜底（纯规则，离线可复现）")
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

    use_llm = (not args.no_llm) and os.environ.get("M1_LLM_FALLBACK", "1") != "0"
    print(f"llm-fallback: {use_llm} (endpoint={LLM_ENDPOINT}, model={LLM_MODEL})")
    results = [process_sample(p, schema, llm_fallback=use_llm) for p in samples]
    for res in results:
        _print_result(res)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(results, fh, ensure_ascii=False, indent=2)
        print(f"\n[json] 脱敏汇总已写入 {args.json}")

    if args.dump_unmapped:
        dump = collect_unmapped_columns(samples, schema)
        dump["schema"] = args.schema
        dump["samples_dir"] = args.samples_dir
        with open(args.dump_unmapped, "w", encoding="utf-8") as fh:
            json.dump(dump, fh, ensure_ascii=False, indent=2)
        print(f"\n[dump-unmapped] {dump['unique_column_count']} 个去重 unmapped 列 "
              f"({dump['total_unmapped_occurrences']} 次出现) 已写入 {args.dump_unmapped}")

    if args.compact_summary:
        compact = build_compact_summary(results)
        with open(args.compact_summary, "w", encoding="utf-8") as fh:
            json.dump(compact, fh, ensure_ascii=False, separators=(",", ":"))
        size = os.path.getsize(args.compact_summary)
        print(f"\n[compact-summary] {len(compact)} 样本, {size} bytes -> {args.compact_summary}")

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
