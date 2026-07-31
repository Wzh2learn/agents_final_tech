"""M2 RAG QA service: retrieval over M1-parsed statements + :8004 generation.

Reuses the existing M2 RAG pipeline (``scripts/m1_rag_ingest.py`` ->
``RAGService.smart_retrieve`` over the ``m1_parsed_statements`` collection) and
adds an answer-generation step on the :8004 Qwen3.6-35B chat model.

Architecture boundary (per AGENTS.md):
- Retrieval goes through ``RAGService`` only — no second vector store, no ad-hoc
  DB queries.
- The retrieval embedding stays the local Qwen3-Embedding-0.6B used at ingest
  time (switching it would break similarity against ingested chunks). :8004 is
  used only for answer generation.
- Ingested chunks are desensitized (values partially masked, field/table names
  preserved). The generated answer therefore reports masked values as-is.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from typing import Any, Optional

# --- Generation config: :8004 Qwen3.6-35B-A3B (chat completions) ---
LLM_ENDPOINT = os.environ.get(
    "M2_LLM_ENDPOINT", "http://127.0.0.1:8004/v1/chat/completions")
LLM_MODEL = os.environ.get("M2_LLM_MODEL", "Qwen3.6-35B-A3B-Q4_K_M.gguf")
LLM_TIMEOUT = float(os.environ.get("M2_LLM_TIMEOUT", "60"))
LLM_MAX_TOKENS = int(os.environ.get("M2_LLM_MAX_TOKENS", "512"))

# Max chars of each chunk fed into the generation prompt.
_CONTEXT_CHUNK_LIMIT = 600

_rag_mod = None       # cached scripts/m1_rag_ingest.py module (env + RAGService)
_rag_service = None   # cached RAGService instance (embedding model loaded once)


def _load_rag():
    """Lazy-import the M2 RAG pipeline from scripts/ and cache a RAGService.

    Mirrors the lazy-load pattern used by ``web.routers.m1`` for the parser.
    Importing ``m1_rag_ingest`` sets the local-embedding + PGVector env vars and
    exposes ``RAGService`` / ``COLLECTION``.
    """
    global _rag_mod, _rag_service
    if _rag_mod is None:
        scripts_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "scripts")
        )
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        import m1_rag_ingest as mod  # noqa: E402

        _rag_mod = mod
    if _rag_service is None:
        _rag_service = _rag_mod.RAGService(collection_name=_rag_mod.COLLECTION)
    return _rag_service


def collection_name() -> str:
    """Return the M2 collection name (loaded from the ingest module)."""
    _load_rag()
    return _rag_mod.COLLECTION


def retrieve(question: str, top_k: int = 3) -> list[dict[str, Any]]:
    """Retrieve relevant desensitized chunks for a question.

    Returns a list of ``{sample_id, table_name, score, text}`` dicts.
    """
    rag = _load_rag()
    docs = rag.smart_retrieve(
        query=question,
        top_k=top_k,
        collection_names=[_rag_mod.COLLECTION],
        max_results=top_k,
        use_rerank=False,
    )
    sources: list[dict[str, Any]] = []
    for d in docs:
        meta = d.get("metadata", {}) or {}
        sources.append({
            "sample_id": str(meta.get("sample_id", "")),
            "table_name": meta.get("table_name", ""),
            "score": round(float(d.get("relevance_score") or 0.0), 4),
            "text": (d.get("content", "") or "").strip(),
        })
    return sources


def _build_prompt(question: str, sources: list[dict[str, Any]]) -> str:
    """Build a grounded RAG prompt from retrieved chunks."""
    ctx_blocks: list[str] = []
    for i, s in enumerate(sources, 1):
        text = (s.get("text") or "")[:_CONTEXT_CHUNK_LIMIT]
        ctx_blocks.append(
            f"[{i}] 样本={s.get('sample_id','')} | 表={s.get('table_name','')} | "
            f"相关度={s.get('score','')}\n{text}"
        )
    context = "\n\n".join(ctx_blocks) if ctx_blocks else "(无检索结果)"
    return (
        "你是金融对账单问答助手。只依据下面的【检索资料】回答用户问题，"
        "不要使用资料外的知识，不要编造数值。\n"
        "注意：资料中的数值可能已脱敏（如 4013****.83），请原样引用，不要还原或猜测。\n"
        "回答要求：\n"
        "  1. 先用一两句中文直接回答问题；\n"
        "  2. 若资料能支撑答案，在结尾用一行注明出处，格式：\n"
        "     出处: 样本=<sample_id>, 表=<table_name>；\n"
        "  3. 若资料不足以回答，直接说明「检索资料中未找到相关数据」，不要编造。\n\n"
        f"【检索资料】\n{context}\n\n"
        f"【用户问题】\n{question}\n\n"
        "【回答】"
    )


def _generate(prompt: str) -> tuple[str, str]:
    """Call :8004 chat completions. Returns (answer_text, model_name)."""
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": LLM_MAX_TOKENS,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(
        LLM_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=LLM_TIMEOUT) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    content = body["choices"][0]["message"]["content"]
    model = body.get("model", LLM_MODEL)
    return (content or "").strip(), model


def ask(question: str, top_k: int = 3) -> dict[str, Any]:
    """End-to-end M2 RAG QA: retrieve -> generate.

    Returns ``{answer, sources, model, collection, top_k}``.
    On generation failure, still returns the retrieved sources with a
    fallback answer so the UI remains useful.
    """
    question = (question or "").strip()
    top_k = max(1, min(int(top_k or 3), 10))

    sources = retrieve(question, top_k=top_k)

    if not sources:
        return {
            "answer": "检索资料中未找到相关数据（集合可能为空或问题与已入库样本无关）。",
            "sources": [],
            "model": "",
            "collection": collection_name(),
            "top_k": top_k,
        }

    prompt = _build_prompt(question, sources)
    try:
        answer, model = _generate(prompt)
    except Exception as exc:  # generation failed -> retrieval-only fallback
        answer = (
            "（生成模型调用失败，以下为检索到的原始资料）\n"
            + "\n".join(
                f"- [{s['sample_id']} | {s['table_name']} | {s['score']}] {s['text'][:160]}"
                for s in sources
            )
            + f"\n错误: {type(exc).__name__}: {exc}"
        )
        model = ""

    return {
        "answer": answer,
        "sources": sources,
        "model": model,
        "collection": collection_name(),
        "top_k": top_k,
    }
