"""M1 rule extraction demo API + statement parser API."""

from __future__ import annotations

import os
import sys
import tempfile
import time
from typing import Any, Optional

from fastapi import APIRouter, File, Query, UploadFile

from biz.m1_service import M1ExtractionRequest, M1ReviewRequest, get_m1_service

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

    try:
        schema = parser.Schema.load(parser.DEFAULT_SCHEMA)
        t0 = time.perf_counter()
        result: dict[str, Any] = parser.process_sample(
            tmp_path, schema, llm_fallback=use_llm
        )
        parse_ms = int((time.perf_counter() - t0) * 1000)
    finally:
        os.unlink(tmp_path)

    if not result.get("ok"):
        return {"status": "error", "result": result}

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
