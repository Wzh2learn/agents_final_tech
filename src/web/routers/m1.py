"""M1 rule extraction demo API + statement parser API."""

from __future__ import annotations

import os
import sys
import tempfile
from typing import Any

from fastapi import APIRouter, File, UploadFile

from biz.m1_service import M1ExtractionRequest, M1ReviewRequest, get_m1_service

router = APIRouter()

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
@router.post("/parse-file")
async def parse_file(file: UploadFile = File(...)):
    """Parse an uploaded statement file (TXT/PDF/XLSX/DOCX) via the M1 parser."""
    parser = _get_parser()

    suffix = os.path.splitext(file.filename or "upload.txt")[1].lower()
    if suffix not in parser.PARSERS:
        return {"status": "error", "error": f"不支持的文件类型: {suffix}"}

    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        schema = parser.Schema.load(parser.DEFAULT_SCHEMA)
        result: dict[str, Any] = parser.process_sample(tmp_path, schema)
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
    reconcile_pass = sum(1 for c in reconcile if c.get("pass"))

    metrics = {
        "tables": result.get("table_count", 0),
        "columns": total_cols,
        "hit_rate": hit_rate,
        "kv_count": result.get("header_meta_count", 0),
        "unmapped": len(unmapped_all),
        "reconcile_pass": f"{reconcile_pass}/{len(reconcile)}",
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

    return {
        "status": "success",
        "result": {
            "file": result["file"],
            "kind": result["kind"],
            "needs_ocr": result.get("needs_ocr", False),
            "note": result.get("note", ""),
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
