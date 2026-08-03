"""HTML page routes."""

import os
import time as _time

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates


router = APIRouter()

templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Render the chat page."""
    return templates.TemplateResponse("chat.html", {"request": request})


@router.get("/knowledge", response_class=HTMLResponse)
async def knowledge_page(request: Request):
    """Render the knowledge management page."""
    return templates.TemplateResponse("knowledge.html", {"request": request})


@router.get("/m1", response_class=HTMLResponse)
async def m1_page(request: Request):
    """Render the M1 rule extraction workbench."""
    return templates.TemplateResponse("m1.html", {"request": request})


@router.get("/collaboration")
async def collaboration_redirect():
    """Redirect collaboration entry to the chat page."""
    return RedirectResponse(url="/chat")


# ---------------------------------------------------------------------------
# Comprehensive health check (for demos + monitoring)
# ---------------------------------------------------------------------------
# Health check cache (30s TTL)
_health_cache: dict = {"result": None, "ts": 0.0}
_HEALTH_CACHE_TTL = 30.0


@router.get("/api/health/full")
async def health_full():
    """Check all system components. Returns status of each dependency. Cached 30s."""
    now = _time.time()
    if _health_cache["result"] is not None and (now - _health_cache["ts"]) < _HEALTH_CACHE_TTL:
        return _health_cache["result"]

    import urllib.request
    import json as _json

    checks = {}

    # 1. PGVector
    try:
        from biz.m2_service import _load_rag, collection_name, embedding_count
        _load_rag()
        col = collection_name()
        count = embedding_count()
        checks["pgvector"] = {"status": "ok", "collection": col, "embeddings": count}
    except Exception as e:
        checks["pgvector"] = {"status": "error", "detail": str(e)[:100]}

    # 2. LLM :8004
    try:
        req = urllib.request.Request("http://127.0.0.1:8004/health")
        with urllib.request.urlopen(req, timeout=3) as resp:
            checks["llm_8004"] = {"status": "ok"}
    except Exception as e:
        checks["llm_8004"] = {"status": "error", "detail": str(e)[:80]}

    # 3. Embedding (same as :8004 usually, but check /v1/models)
    try:
        req = urllib.request.Request("http://127.0.0.1:8004/v1/models")
        with urllib.request.urlopen(req, timeout=3) as resp:
            models = _json.loads(resp.read())
            model_ids = [m["id"] for m in models.get("data", [])]
            checks["embedding"] = {"status": "ok", "models": model_ids[:3]}
    except Exception as e:
        checks["embedding"] = {"status": "error", "detail": str(e)[:80]}

    # 4. Proxy :8100
    try:
        req = urllib.request.Request("http://127.0.0.1:8100/health")
        with urllib.request.urlopen(req, timeout=3) as resp:
            checks["proxy_8100"] = {"status": "ok"}
    except Exception:
        checks["proxy_8100"] = {"status": "unavailable"}

    # 5. M2 RAG QA (quick test)
    try:
        from biz.m2_service import retrieve
        sources = retrieve("test", top_k=1)
        checks["m2_rag"] = {"status": "ok", "retrieval_working": len(sources) > 0}
    except Exception as e:
        checks["m2_rag"] = {"status": "error", "detail": str(e)[:80]}

    # Overall
    all_ok = all(c.get("status") in ("ok", "unavailable") for c in checks.values())
    result = {
        "overall": "healthy" if all_ok else "degraded",
        "components": checks,
    }
    _health_cache["result"] = result
    _health_cache["ts"] = _time.time()
    return result
