"""M2 RAG QA demo API.

Endpoint:
    POST /api/m2/ask  {"question": "...", "top_k": 3}
        -> {"answer": "...", "sources": [...], "model": "...", ...}

Retrieval reuses the M1->M2 RAG pipeline (collection ``m1_parsed_statements``);
generation runs on the :8004 Qwen3.6-35B chat model. See ``biz.m2_service``.
"""
from __future__ import annotations

import time

from fastapi import APIRouter
from pydantic import BaseModel, Field

from biz.m2_service import ask as m2_ask
from biz.m2_service import collection_name

router = APIRouter()


class M2AskRequest(BaseModel):
    question: str = Field(..., description="自然语言问题")
    top_k: int = Field(default=3, ge=1, le=10, description="检索条数")


@router.get("/health")
async def m2_health():
    """Lightweight liveness probe (does not load the embedding model)."""
    return {"status": "ok", "collection": collection_name()}


@router.post("/ask")
async def m2_ask_endpoint(request: M2AskRequest):
    """Retrieve grounded chunks and generate an answer over M1-parsed statements."""
    t0 = time.perf_counter()
    result = m2_ask(request.question, top_k=request.top_k)
    result["duration_ms"] = int((time.perf_counter() - t0) * 1000)
    return result
