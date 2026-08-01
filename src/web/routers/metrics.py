"""Prometheus-compatible /api/metrics endpoint."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from utils.metrics import registry

router = APIRouter()


@router.get("/api/metrics", response_class=PlainTextResponse)
async def metrics_endpoint():
    """Expose all application metrics in Prometheus text format."""
    return PlainTextResponse(content=registry.expose(), media_type="text/plain; charset=utf-8")
