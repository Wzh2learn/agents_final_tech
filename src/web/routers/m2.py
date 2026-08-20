"""M2 RAG QA demo API with multi-turn conversation support.

Endpoints:
    POST /api/m2/ask  {"question": "...", "top_k": 3, "session_id": "optional"}
        -> {"answer": "...", "sources": [...], "model": "...", "session_id": "..."}

    POST /api/m2/sessions/{session_id}/clear
        -> {"status": "cleared"}

Retrieval reuses the M1->M2 RAG pipeline (collection ``m1_parsed_statements``);
generation runs on the :8004 Qwen3.6-35B chat model. See ``biz.m2_service``.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import os
import time
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from biz import opencode_adapter
from biz.m2_service import append_turn, get_history, new_session_id
from biz.m2_service import ask as m2_ask
from utils.metrics import m2_qa_total, m2_qa_duration_seconds
from biz.m2_service import clear_session, collection_name
from biz.m2_service import (
    detect_compare_intent,
    list_products,
    get_product_timeline,
    compare_dates,
    compare_positions,
)

router = APIRouter()

logger = logging.getLogger("m1.m2_router")

_ADMIN_TOKEN: Optional[str] = os.environ.get("M1_ADMIN_TOKEN") or None


# --- B4 观察窗口结构化日志 (S1, 2026-08-12; 发送后 ≥100 ask / ≥3 天统计) ---
# M1_B4_LOG_PATH env override: test processes (conftest) point this at a scratch file so
# TestClient traffic does not pollute production B4 stats (2026-08-21 N1 incident: pytest
# rows leaked into lines 3097-3100). Production has no such env var -> unchanged, no restart.
_B4_LOG = os.environ.get("M1_B4_LOG_PATH") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "logs", "graph", "b4_ask_log.jsonl",
)


def _b4_log(route: str, latency_ms: int, sources_count: int, fell_back: bool,
            status: str = "ok") -> None:
    """每次 /api/m2/ask 追加一行 JSONL: ts/route/latency_ms/sources_count/fell_back/status。"""
    try:
        os.makedirs(os.path.dirname(_B4_LOG), exist_ok=True)
        with open(_B4_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "ts": dt.datetime.now().isoformat(timespec="seconds"),
                "route": route,
                "latency_ms": latency_ms,
                "sources_count": sources_count,
                "fell_back": fell_back,
                "status": status,
            }, ensure_ascii=False) + "\n")
    except OSError:
        logger.debug("b4 log write failed", exc_info=True)


def _check_admin(x_admin_token: Optional[str]) -> None:
    """Validate admin token for sensitive ops (mirrors m1.py pattern)."""
    if _ADMIN_TOKEN is None:
        return
    if x_admin_token != _ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Admin-Token")


class M2AskRequest(BaseModel):
    question: str = Field(..., description="自然语言问题")
    top_k: int = Field(default=3, ge=1, le=10, description="检索条数")
    session_id: Optional[str] = Field(default=None, description="会话ID，不传则自动生成")


class M2CompareRequest(BaseModel):
    product: str = Field(..., description="产品名称")
    date_a: str = Field(..., description="日期A (YYYYMMDD)")
    date_b: str = Field(..., description="日期B (YYYYMMDD)")
    fields: Optional[list[str]] = Field(default=None, description="对比字段列表")


class M2PositionsRequest(BaseModel):
    product: str = Field(..., description="产品名称")
    date: str = Field(default="", description="对账单日期 (YYYYMMDD)")


@router.get("/health")
async def m2_health():
    """Lightweight liveness probe (does not load the embedding model)."""
    return {"status": "ok", "collection": collection_name()}


@router.post(
    "/ask",
    summary="M2 智能问答",
    description="基于 RAG 的自然语言问答。支持多轮对话（通过 session_id）。返回答案 + 来源溯源。",
    responses={
        200: {"description": "问答结果", "example": {"answer": "嘉兴民安的总资产为401,383,291.83元。", "sources": [{"sample_id": "sample_jiaxing_minan_20231031.pdf", "table_name": "p0_table_2", "score": 0.42}], "session_id": "uuid", "model": "Qwen3.6-35B-A3B"}},
    },
)
async def m2_ask_endpoint(request: M2AskRequest):
    """Retrieve grounded chunks and generate an answer over M1-parsed statements."""
    t0 = time.perf_counter()
    fell_back_from_agent = False
    if opencode_adapter.route_enabled() and not detect_compare_intent(request.question):
        sid = request.session_id or new_session_id()
        oc = opencode_adapter.ask_via_opencode(
            request.question, history=get_history(sid)
        )
        if oc is not None:
            append_turn(sid, "user", request.question)
            append_turn(sid, "assistant", oc["answer"])
            elapsed = time.perf_counter() - t0
            oc["session_id"] = sid
            oc["duration_ms"] = int(elapsed * 1000)
            m2_qa_total.inc({"status": "ok"})
            m2_qa_duration_seconds.observe(elapsed)
            _b4_log("agent", int(elapsed * 1000), len(oc.get("sources") or []), False)
            return oc
        logger.warning("opencode route enabled but unavailable; served by direct path")
        fell_back_from_agent = True
    try:
        result = m2_ask(
            request.question,
            top_k=request.top_k,
            session_id=request.session_id,
        )
        elapsed = time.perf_counter() - t0
        result["duration_ms"] = int(elapsed * 1000)
        m2_qa_total.inc({"status": "ok"})
        m2_qa_duration_seconds.observe(elapsed)
        _b4_log("direct", int(elapsed * 1000), len(result.get("sources") or []), fell_back_from_agent)
        return result
    except Exception:
        elapsed = time.perf_counter() - t0
        m2_qa_total.inc({"status": "error"})
        m2_qa_duration_seconds.observe(elapsed)
        _b4_log("direct", int(elapsed * 1000), 0, fell_back_from_agent, status="error")
        raise


@router.post("/sessions/{session_id}/clear")
async def m2_clear_session(session_id: str):
    """Clear conversation history for a session."""
    clear_session(session_id)
    return {"status": "cleared"}


@router.post("/opencode/cleanup", summary="Sidecar 会话清理")
async def m2_opencode_cleanup(
    purge_all: bool = False,
    max_keep: int = 50,
    x_admin_token: Optional[str] = Header(None),
):
    """Purge orphaned OpenCode sidecar sessions (capped or full purge)."""
    _check_admin(x_admin_token)
    return opencode_adapter.cleanup_sessions(max_keep=max_keep, purge_all=purge_all)


# ---------------------------------------------------------------------------
# Cross-document comparison endpoints (Phase 1)
# ---------------------------------------------------------------------------

@router.get("/products", summary="产品列表")
async def m2_products():
    """Return distinct product names from the M2 collection metadata."""
    products = list_products()
    return {"products": products}


@router.get("/products/{name}/timeline", summary="产品时间线")
async def m2_product_timeline(name: str):
    """Return statement snapshots for a product sorted by date."""
    return get_product_timeline(name)


@router.post("/compare", summary="跨期对比")
async def m2_compare(request: M2CompareRequest):
    """Field-level diff between two statement dates for a product."""
    return compare_dates(request.product, request.date_a, request.date_b, request.fields)


@router.post("/compare/positions", summary="组合内持仓对比")
async def m2_compare_positions(request: M2PositionsRequest):
    """Compare positions within a single statement (ranked by market value)."""
    return compare_positions(request.product, request.date)
