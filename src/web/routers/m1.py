"""M1 rule extraction demo API + statement parser API."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import tempfile
import time
from typing import Any, Optional

import json
import logging

from fastapi import APIRouter, File, Header, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel

from biz.m1_service import M1ExtractionRequest, M1ReviewRequest, get_m1_service
from utils.metrics import m1_parse_total, m1_parse_duration_seconds

router = APIRouter()

# LLM fallback: env-var controlled (consistent with CLI default=on)
_LLM_FALLBACK_DEFAULT = os.environ.get("M1_LLM_FALLBACK", "1") != "0"

# ---------------------------------------------------------------------------
# Lazy-load the statement parser that lives in scripts/ (outside src/)
# ---------------------------------------------------------------------------
_parser_mod = None


def _get_parser():
    global _parser_mod
    if _parser_mod is None:
        scripts_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts")
        )
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        import m1_statement_parser as mod  # noqa: E402

        _parser_mod = mod
    return _parser_mod


# ---------------------------------------------------------------------------
# Legacy rule-extraction endpoints (unchanged)
# ---------------------------------------------------------------------------
@router.get("/sample")
async def sample_document():
    """Return the built-in M1 demo document."""
    return {"status": "success", "sample": get_m1_service().sample_document()}


@router.post("/extract")
async def extract_rules(request: M1ExtractionRequest):
    """Run the local M1 extraction baseline."""
    return get_m1_service().extract(request)


@router.post("/review")
async def review_rule(request: M1ReviewRequest):
    """Apply an in-memory human review decision."""
    return get_m1_service().review(request)


# ---------------------------------------------------------------------------
# Statement parser endpoint (Phase 3)
# ---------------------------------------------------------------------------
@router.post(
    "/parse-file",
    summary="M1 对账单解析",
    description="上传对账单文件 (PDF/TXT/DOCX/XLSX)，返回结构化表格、字段映射、勾稽校验结果。支持 LLM 兜底映射。",
)
async def parse_file(
    file: UploadFile = File(...),
    llm_fallback: Optional[bool] = Query(
        default=None,
        description="启用/禁用 LLM 兜底抽取 (默认跟随 M1_LLM_FALLBACK 环境变量)",
    ),
):
    """Parse an uploaded statement file (TXT/PDF/XLSX/DOCX) via the M1 parser."""
    parser = _get_parser()

    suffix = os.path.splitext(file.filename or "upload.txt")[1].lower()
    if suffix not in parser.PARSERS:
        return {"status": "error", "error": f"不支持的文件类型: {suffix}"}

    use_llm = llm_fallback if llm_fallback is not None else _LLM_FALLBACK_DEFAULT

    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    fmt_label = suffix.lstrip(".")
    try:
        schema = parser.Schema.load(parser.resolve_schema_path())
        t0 = time.perf_counter()
        result: dict[str, Any] = parser.process_sample(
            tmp_path, schema, llm_fallback=use_llm
        )
        parse_ms = int((time.perf_counter() - t0) * 1000)
    finally:
        os.unlink(tmp_path)

    if not result.get("ok"):
        m1_parse_total.inc({"format": fmt_label, "status": "error"})
        m1_parse_duration_seconds.observe(parse_ms / 1000.0, {"format": fmt_label})
        return {"status": "error", "result": result}

    m1_parse_total.inc({"format": fmt_label, "status": "ok"})
    m1_parse_duration_seconds.observe(parse_ms / 1000.0, {"format": fmt_label})

    # Prepare tables: expose records (capped), strip internal key
    tables_out: list[dict[str, Any]] = []
    for tbl in result.get("tables", []):
        records = tbl.pop("_records", [])
        tbl["records"] = records[:50]
        tbl["total_records"] = len(records)
        tables_out.append(tbl)

    # Collect all unmapped columns
    unmapped_all = [
        {"table": t["table"], "column": col}
        for t in tables_out
        for col in t.get("unmapped", [])
    ]

    # Aggregate metrics
    total_cols = sum(t["cols"] for t in tables_out)
    total_hits = sum(t["hits"] for t in tables_out)
    hit_rate = round(total_hits / total_cols * 100, 1) if total_cols else 0.0
    reconcile = result.get("reconcile", [])
    real_pass_count = sum(1 for c in reconcile if c.get("disposition") == "real_pass")
    skipped_count = sum(1 for c in reconcile if c.get("disposition") == "skipped")
    fail_count = sum(1 for c in reconcile if c.get("disposition") == "fail")

    metrics = {
        "tables": result.get("table_count", 0),
        "columns": total_cols,
        "hit_rate": hit_rate,
        "kv_count": result.get("header_meta_count", 0),
        "unmapped": len(unmapped_all),
        "reconcile_real_pass": real_pass_count,
        "reconcile_skipped": skipped_count,
        "reconcile_fail": fail_count,
        "reconcile_pass": f"{real_pass_count}/{len(reconcile)}",
    }

    # M2 payload (compact, no raw records)
    m2_payload = {
        "file": result["file"],
        "kind": result["kind"],
        "header_meta": result.get("header_meta", {}),
        "tables": [
            {k: v for k, v in t.items() if k != "records"} for t in tables_out
        ],
        "reconcile": reconcile,
        "metrics": metrics,
    }

    # Detect whether LLM fallback was actually invoked
    llm_used = any(t.get("llm_extracted") for t in tables_out)

    # Explicit note for image-only files that cannot be structured yet
    note = result.get("note", "")
    if result.get("needs_ocr") and result.get("table_count", 0) == 0:
        ocr_note = "暂不支持影像件（纯图片 PDF/DOCX），需 OCR 能力后方可结构化"
        note = f"{note} {ocr_note}".strip() if note else ocr_note

    return {
        "status": "success",
        "result": {
            "file": result["file"],
            "kind": result["kind"],
            "needs_ocr": result.get("needs_ocr", False),
            "ocr_used": result.get("ocr_used", False),
            "ocr_engine": result.get("ocr_engine", ""),
            "note": note,
            "llm_used": llm_used,
            "llm_fallback_enabled": use_llm,
            "parse_duration_ms": parse_ms,
            "header_meta": result.get("header_meta", {}),
            "header_meta_count": result.get("header_meta_count", 0),
            "tables": tables_out,
            "table_count": result.get("table_count", 0),
            "reconcile": reconcile,
            "unmapped": unmapped_all,
            "metrics": metrics,
        },
        "m2_payload": m2_payload,
    }


# ---------------------------------------------------------------------------
# Schema CRUD API (Phase 2 - client self-service)
# ---------------------------------------------------------------------------
_logger = logging.getLogger("m1.schema")
_ADMIN_TOKEN: Optional[str] = os.environ.get("M1_ADMIN_TOKEN") or None

if not _ADMIN_TOKEN:
    _logger.warning("M1_ADMIN_TOKEN not set, schema write endpoints unprotected")


def _get_schema_path() -> str:
    """Return the active schema file path (config/ override or frozen default)."""
    parser = _get_parser()
    return parser.resolve_schema_path()


def _get_local_schema_path() -> str:
    """Return the project-local writable schema path (config/m1_table_schema.json)."""
    parser = _get_parser()
    return parser.LOCAL_SCHEMA


def _read_schema() -> dict:
    path = _get_schema_path()
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def _write_schema(data: dict) -> None:
    """Write schema to the project-local config/ path (never touches frozen file)."""
    local_path = _get_local_schema_path()
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def _check_admin(x_admin_token: Optional[str]) -> None:
    """Validate admin token for write operations."""
    if _ADMIN_TOKEN is None:
        return  # unprotected mode (warning already logged at startup)
    if x_admin_token != _ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Admin-Token")


def _validate_schema(data: dict) -> list[str]:
    """Basic structural validation of schema JSON. Returns list of errors."""
    errors = []
    if not isinstance(data, dict):
        return ["Schema must be a JSON object"]
    tables = data.get("tables")
    if tables is None:
        errors.append("Missing 'tables' array")
    elif not isinstance(tables, list):
        errors.append("'tables' must be an array")
    else:
        seen_names = set()
        for i, t in enumerate(tables):
            if not isinstance(t, dict):
                errors.append(f"tables[{i}] must be an object")
                continue
            name = t.get("table_name", "")
            if not name:
                errors.append(f"tables[{i}] missing 'table_name'")
            elif name in seen_names:
                errors.append(f"Duplicate table_name: {name}")
            seen_names.add(name)
            fields = t.get("fields", [])
            if not isinstance(fields, list):
                errors.append(f"tables[{i}].fields must be an array")
            else:
                seen_fields = set()
                for j, fld in enumerate(fields):
                    if not isinstance(fld, dict):
                        errors.append(f"tables[{i}].fields[{j}] must be an object")
                        continue
                    std = fld.get("standard", "")
                    if not std:
                        errors.append(f"tables[{i}].fields[{j}] missing 'standard'")
                    elif std in seen_fields:
                        errors.append(f"tables[{i}] duplicate field: {std}")
                    seen_fields.add(std)
                    syns = fld.get("synonyms", [])
                    if not isinstance(syns, list):
                        errors.append(f"tables[{i}].fields[{j}].synonyms must be an array")
    return errors


class SchemaFieldBody(BaseModel):
    standard: str
    synonyms: list[str] = []


class SchemaTableBody(BaseModel):
    table_name: str
    layout: str = "grid"
    header_region_keywords: list[str] = []
    fields: list[SchemaFieldBody] = []


@router.get("/schema", summary="获取当前解析规则")
async def get_schema():
    """Return the current schema JSON (read-only, no auth required)."""
    try:
        data = _read_schema()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Schema file not found")
    return data


@router.put("/schema", summary="更新完整解析规则")
async def put_schema(request: Request, x_admin_token: Optional[str] = Header(None)):
    """Replace the full schema. Validates structure before writing."""
    _check_admin(x_admin_token)
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid JSON body")
    errors = _validate_schema(body)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})
    _write_schema(body)
    return {"status": "ok", "message": "Schema updated", "tables": len(body.get("tables", []))}


@router.post("/schema/tables", summary="新增表定义", status_code=201)
async def add_table(body: SchemaTableBody, x_admin_token: Optional[str] = Header(None)):
    """Add a new table definition to the schema."""
    _check_admin(x_admin_token)
    data = _read_schema()
    tables = data.setdefault("tables", [])
    if any(t.get("table_name") == body.table_name for t in tables):
        raise HTTPException(status_code=409, detail=f"Table '{body.table_name}' already exists")
    tables.append({
        "table_name": body.table_name,
        "layout": body.layout,
        "header_region_keywords": body.header_region_keywords,
        "fields": [{"standard": f.standard, "synonyms": f.synonyms} for f in body.fields],
    })
    _write_schema(data)
    return {"status": "ok", "message": f"Table '{body.table_name}' added"}


@router.post("/schema/tables/{name}/fields", summary="新增字段", status_code=201)
async def add_field(name: str, body: SchemaFieldBody, x_admin_token: Optional[str] = Header(None)):
    """Add a field to an existing table."""
    _check_admin(x_admin_token)
    data = _read_schema()
    table = next((t for t in data.get("tables", []) if t.get("table_name") == name), None)
    if table is None:
        raise HTTPException(status_code=404, detail=f"Table '{name}' not found")
    fields = table.setdefault("fields", [])
    if any(f.get("standard") == body.standard for f in fields):
        raise HTTPException(status_code=409, detail=f"Field '{body.standard}' already exists in '{name}'")
    fields.append({"standard": body.standard, "synonyms": body.synonyms})
    _write_schema(data)
    return {"status": "ok", "message": f"Field '{body.standard}' added to '{name}'"}


@router.delete("/schema/tables/{name}/fields/{standard}", summary="删除字段")
async def delete_field(name: str, standard: str, x_admin_token: Optional[str] = Header(None)):
    """Remove a field from a table."""
    _check_admin(x_admin_token)
    data = _read_schema()
    table = next((t for t in data.get("tables", []) if t.get("table_name") == name), None)
    if table is None:
        raise HTTPException(status_code=404, detail=f"Table '{name}' not found")
    fields = table.get("fields", [])
    original_len = len(fields)
    table["fields"] = [f for f in fields if f.get("standard") != standard]
    if len(table["fields"]) == original_len:
        raise HTTPException(status_code=404, detail=f"Field '{standard}' not found in '{name}'")
    _write_schema(data)
    return {"status": "ok", "message": f"Field '{standard}' removed from '{name}'"}


@router.delete("/schema/tables/{name}", summary="删除表定义")
async def delete_table(name: str, x_admin_token: Optional[str] = Header(None)):
    """Remove an entire table definition."""
    _check_admin(x_admin_token)
    data = _read_schema()
    tables = data.get("tables", [])
    original_len = len(tables)
    data["tables"] = [t for t in tables if t.get("table_name") != name]
    if len(data["tables"]) == original_len:
        raise HTTPException(status_code=404, detail=f"Table '{name}' not found")
    _write_schema(data)
    return {"status": "ok", "message": f"Table '{name}' removed"}


# ---------------------------------------------------------------------------
# Schema mapping suggestions (选择题体验 场景 A, docs/26)
# ---------------------------------------------------------------------------

def _suggestions_path() -> str:
    return os.path.join(os.path.dirname(_get_schema_path()),
                        "schema_suggestions.json")


def _read_suggestions() -> dict:
    path = _suggestions_path()
    if not os.path.isfile(path):
        return {"suggestions": [], "applied": [], "rejected": []}
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    data.setdefault("suggestions", [])
    data.setdefault("applied", [])
    data.setdefault("rejected", [])
    return data


def _write_suggestions(data: dict) -> None:
    path = _suggestions_path()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


class SuggestionItem(BaseModel):
    raw_column: str
    standard_field: str
    table: str


class SuggestionsActionBody(BaseModel):
    items: list[SuggestionItem]


def _match_key(sg: dict, it: SuggestionItem) -> bool:
    """Match on (raw_column, table) only: the UI lets the user retarget the
    standard_field via a select, so the requested target may differ from the
    stored suggestion."""
    return (sg.get("raw_column") == it.raw_column
            and sg.get("table") == it.table)


@router.get("/schema-suggestions", summary="获取待确认的映射建议（选择题面板）")
async def get_schema_suggestions():
    """Return pending mapping suggestions for the 建议映射 panel."""
    data = _read_suggestions()
    return {"suggestions": data["suggestions"],
            "applied_count": len(data["applied"]),
            "rejected_count": len(data["rejected"])}


@router.post("/schema-suggestions/apply", summary="应用所选映射建议（写 schema + 回归门禁）")
async def apply_schema_suggestions(body: SuggestionsActionBody,
                                   x_admin_token: Optional[str] = Header(None)):
    """Apply selected suggestions: merge synonyms into schema, gate with the
    quick scenario1 regression; roll back on regression."""
    _check_admin(x_admin_token)
    # F1 (audit 2026-08-10): 拒绝写穿冻结 schema — 写入目标必须是可写 config/ 副本
    if os.path.abspath(_get_schema_path()) != os.path.abspath(_get_local_schema_path()):
        raise HTTPException(status_code=403,
                            detail="schema 解析到不可写路径（冻结节点保护），拒绝写入")
    # F4: single-flight — 回归门禁同时只跑一个
    if not _apply_lock.acquire(blocking=False):
        raise HTTPException(status_code=409,
                            detail="另一个 apply 正在进行（回归门禁运行中），请稍候重试")
    try:
        return await _apply_locked(body)
    finally:
        _apply_lock.release()


async def _apply_locked(body: SuggestionsActionBody):
    data = _read_suggestions()
    chosen: list[dict] = []
    for it in body.items:
        for sg in data["suggestions"]:
            if _match_key(sg, it):
                item = dict(sg)
                item["standard_field"] = it.standard_field  # user may retarget
                chosen.append(item)
                break
    if not chosen:
        raise HTTPException(status_code=404, detail="No matching pending suggestions")

    apply_mod = _get_apply_mod()
    schema_path = _get_schema_path()
    with open(schema_path, "rb") as fh:  # F5: 字节级备份（格式/BOM 安全）
        backup = fh.read()
    merged_path = schema_path + ".merged"
    added, skips = apply_mod.merge_into_schema(schema_path, chosen, merged_path)
    if added == 0:
        if os.path.isfile(merged_path):
            os.remove(merged_path)
        raise HTTPException(status_code=409,
                            detail=f"No new synonyms merged: {skips}")
    # write merged schema live, then gate with quick regression
    merged = open(merged_path, encoding="utf-8").read()
    with open(schema_path, "w", encoding="utf-8") as fh:
        fh.write(merged)
    try:
        proc = subprocess.run(
            [sys.executable,
             os.path.join(os.path.dirname(schema_path), "..", "scripts",
                          "m1_scenario1_regression.py"), "--quick"],
            capture_output=True, text=True, timeout=300,
            cwd=os.path.abspath(os.path.join(os.path.dirname(schema_path), "..")))
        gate_ok = "[scenario1-regression] PASS" in proc.stdout
    except Exception as exc:  # noqa: BLE001
        gate_ok = False
        proc = None
        skips.append(f"regression gate error: {exc}")
    if not gate_ok:
        with open(schema_path, "wb") as fh:
            fh.write(backup)
        if os.path.isfile(merged_path):
            os.remove(merged_path)
        raise HTTPException(status_code=409,
                            detail="Regression gate failed; schema rolled back. "
                                   + (proc.stdout[-400:] if proc else ""))
    if os.path.isfile(merged_path):
        os.remove(merged_path)
    import datetime as _dt
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    for sg in chosen:
        sg["applied_at"] = now
        data["applied"].append(sg)
    data["suggestions"] = [sg for sg in data["suggestions"]
                           if not any(_match_key(sg, it) for it in body.items)]
    _write_suggestions(data)
    hint = "规则已热加载，重新解析相关样本即可看到命中率提升"
    ocr_hit = _ocr_samples_in_baseline() & {sg.get("sample") for sg in chosen}
    if ocr_hit:  # F3: quick 门禁盲区如实提示
        hint += ("；注意: 本次含 OCR 来源建议，quick 门禁不含 OCR 样本，"
                 "请手动重解析对应样本复核")
    return {"status": "ok", "applied": len(chosen), "added_synonyms": added,
            "skips": skips, "hint": hint}


@router.post("/schema-suggestions/reject", summary="拒绝所选建议（不再重复推荐）")
async def reject_schema_suggestions(body: SuggestionsActionBody,
                                    x_admin_token: Optional[str] = Header(None)):
    """Move selected suggestions to the rejected list (no schema change)."""
    _check_admin(x_admin_token)  # F2: reject 是状态破坏操作，与 apply 同门禁
    data = _read_suggestions()
    import datetime as _dt
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    moved = [sg for sg in data["suggestions"]
             if any(_match_key(sg, it) for it in body.items)]
    for sg in moved:
        sg["rejected_at"] = now
        data["rejected"].append(sg)
    data["suggestions"] = [sg for sg in data["suggestions"]
                           if not any(_match_key(sg, it) for it in body.items)]
    _write_suggestions(data)
    return {"status": "ok", "rejected": len(moved)}


_apply_mod = None
_apply_lock = threading.Lock()  # F4: single-flight gate


def _ocr_samples_in_baseline() -> set:
    """F3: OCR 样本文件名集合（门禁盲区提示用），读取失败静默降级。"""
    try:
        path = os.path.join(os.path.dirname(_get_schema_path()), "..",
                            "tests", "baselines", "scenario1_baseline.json")
        with open(path, encoding="utf-8") as fh:
            cases = json.load(fh).get("cases", [])
        return {os.path.basename(c.get("file", "")) for c in cases
                if c.get("ocr_expected")}
    except Exception:
        return set()


def _get_apply_mod():
    global _apply_mod
    if _apply_mod is None:
        scripts_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts"))
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        import m1_apply_schema_suggestions as mod  # noqa: E402
        _apply_mod = mod
    return _apply_mod
