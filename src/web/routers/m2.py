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

import time
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from biz.m2_service import ask as m2_ask
from biz.m2_service import clear_session, collection_name

router = APIRouter()


class M2AskRequest(BaseModel):
    question: str = Field(..., description="自然语言问题")
    top_k: int = Field(default=3, ge=1, le=10, description="检索条数")
    session_id: Optional[str] = Field(default=None, description="会话ID，不传则自动生成")


@router.get("/health")
async def m2_health():
    """Lightweight liveness probe (does not load the embedding model)."""
    return {"status": "ok", "collection": collection_name()}


@router.post("/ask")
async def m2_ask_endpoint(request: M2AskRequest):
    """Retrieve grounded chunks and generate an answer over M1-parsed statements."""
    t0 = time.perf_counter()
    result = m2_ask(
        request.question,
        top_k=request.top_k,
        session_id=request.session_id,
    )
    result["duration_ms"] = int((time.perf_counter() - t0) * 1000)
    return result


@router.post("/sessions/{session_id}/clear")
async def m2_clear_session(session_id: str):
    """Clear conversation history for a session."""
    clear_session(session_id)
    return {"status": "cleared"}
