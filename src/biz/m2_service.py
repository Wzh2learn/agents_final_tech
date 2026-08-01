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
import threading
import time as _time
import uuid

# --- Generation config: :8004 Qwen3.6-35B-A3B (chat completions) ---
LLM_ENDPOINT = os.environ.get(
    "M2_LLM_ENDPOINT", "http://127.0.0.1:8004/v1/chat/completions")
LLM_MODEL = os.environ.get("M2_LLM_MODEL", "Qwen3.6-35B-A3B-Q4_K_M.gguf")
LLM_TIMEOUT = float(os.environ.get("M2_LLM_TIMEOUT", "60"))
LLM_MAX_TOKENS = int(os.environ.get("M2_LLM_MAX_TOKENS", "512"))

# Max chars of each chunk fed into the generation prompt.
_CONTEXT_CHUNK_LIMIT = 600

# --- Session / conversation history ---
_MAX_TURNS = 10          # max messages stored per session
_CONTEXT_TURNS = 5       # last N messages injected into prompt
_SESSION_TTL = 30 * 60   # 30 minutes inactivity expiry (seconds)

_sessions_lock = threading.Lock()
_sessions: dict[str, dict[str, Any]] = {}
# Each entry: {"history": [{"role":..., "content":...}, ...], "last_active": float}


def _get_session(session_id: str) -> dict[str, Any]:
    """Get or create a session, performing lazy TTL cleanup."""
    now = _time.time()
    with _sessions_lock:
        # Lazy cleanup of expired sessions
        expired = [
            sid for sid, s in _sessions.items()
            if now - s["last_active"] > _SESSION_TTL
        ]
        for sid in expired:
            del _sessions[sid]
        # Get or create
        if session_id not in _sessions:
            _sessions[session_id] = {"history": [], "last_active": now}
        session = _sessions[session_id]
        session["last_active"] = now
        return session


def _append_history(session: dict[str, Any], role: str, content: str) -> None:
    """Append a message and trim to _MAX_TURNS."""
    session["history"].append({"role": role, "content": content})
    if len(session["history"]) > _MAX_TURNS:
        session["history"] = session["history"][-_MAX_TURNS:]


def clear_session(session_id: str) -> bool:
    """Clear conversation history for a session. Returns True if existed."""
    with _sessions_lock:
        if session_id in _sessions:
            _sessions[session_id]["history"] = []
            _sessions[session_id]["last_active"] = _time.time()
            return True
        return False


def new_session_id() -> str:
    """Generate a new session UUID."""
    return str(uuid.uuid4())

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


def retrieve(question: str, top_k: int = 10) -> list[dict[str, Any]]:
    """Retrieve relevant desensitized chunks for a question.

    Returns a list of ``{sample_id, table_name, score, text}`` dicts.
    """
    rag = _load_rag()
    docs = rag.smart_retrieve(
        query=question,
        top_k=top_k,
        collection_names=[_rag_mod.COLLECTION],
        max_results=top_k,
        use_rerank=True,
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


def _build_prompt(
    question: str,
    sources: list[dict[str, Any]],
    history: list[dict[str, str]] | None = None,
) -> str:
    """Build a grounded RAG prompt from retrieved chunks + conversation history."""
    ctx_blocks: list[str] = []
    for i, s in enumerate(sources, 1):
        text = (s.get("text") or "")[:_CONTEXT_CHUNK_LIMIT]
        ctx_blocks.append(
            f"[{i}] 样本={s.get('sample_id','')} | 表={s.get('table_name','')} | "
            f"相关度={s.get('score','')}\n{text}"
        )
    context = "\n\n".join(ctx_blocks) if ctx_blocks else "(无检索结果)"

    # Conversation history section
    history_section = ""
    if history:
        recent = history[-_CONTEXT_TURNS:]
        lines = []
        for msg in recent:
            role_label = "用户" if msg["role"] == "user" else "助手"
            lines.append(f"{role_label}: {msg['content']}")
        history_section = (
            "\n【对话历史】\n"
            + "\n".join(lines)
            + "\n"
        )

    system_instruction = (
        "你是金融对账单分析助手。以下是之前的对话历史，请结合历史上下文回答新问题。\n"
        "只依据下面的【检索资料】回答用户问题，"
        "不要使用资料外的知识，不要编造数值。\n"
        "注意：资料中的数值可能已脱敏（如 4013****.83），请原样引用，不要还原或猜测。\n"
        "回答要求：\n"
        "  1. 先用一两句中文直接回答问题；\n"
        "  2. 若资料能支撑答案，在结尾用一行注明出处，格式：\n"
        "     出处: 样本=<sample_id>, 表=<table_name>；\n"
        "  3. 若资料不足以回答，直接说明「检索资料中未找到相关数据」，不要编造。\n"
        "\n"
        "## 回答示例\n"
        "\n"
        "示例 1:\n"
        "用户问: 复熙混合25号的资产总值是多少？\n"
        "检索到的信息: 资产总值=22161557.90, 币种=人民币, 来源=复熙混合25号对账单\n"
        "你的回答: 复熙混合25号的资产总值为 22,161,557.90 元（人民币）。\n"
        "来源：复熙混合25号对账单，资产总值字段。\n"
        "\n"
        "示例 2:\n"
        "用户问: 嘉兴民安有哪些证券持仓？\n"
        "检索到的信息: 证券代码=600157, 证券名称=永泰能源, 市值=401379783.28, 来源=嘉兴民安对账单\n"
        "你的回答: 根据嘉兴民安对账单，持有永泰能源（证券代码 600157），市值 401,379,783.28 元。\n"
        "来源：嘉兴民安对账单，证券持仓明细表。\n"
        "\n"
        "示例 3:\n"
        "用户问: 博时传统产品的基金名称是什么？\n"
        "检索到的信息: 基金名称=博时****混合A, 基金代码=00****22, 来源=博时传统产品对账单\n"
        "你的回答: 博时传统产品的基金名称为博时****混合A（基金代码 00****22）。\n"
        "来源：博时传统产品对账单，表头信息区。\n"
        "\n"
        "## 回答规则\n"
        "- 必须引用来源文档名称\n"
        "- 数值保留原始精度，加千分位逗号\n"
        "- 如果检索结果不包含答案，明确说\"根据现有对账单数据，未找到相关信息\"\n"
        "- 不要编造数据\n"
    )

    return (
        f"{system_instruction}"
        f"{history_section}\n"
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



# ---------------------------------------------------------------------------
# Query rewriting for multi-turn follow-ups
# ---------------------------------------------------------------------------
_REWRITE_TRIGGERS = ["其中", "它的", "占比", "分别", "各自", "哪个", "多少", "呢", "吗", "那", "还有", "另外"]

_REWRITE_PROMPT = """根据对话历史，将用户的追问改写为一个独立的、完整的检索查询。
只输出改写后的查询，不要解释，不要加引号。

对话历史:
{history}

用户追问: {query}

改写后的独立查询:"""


def _should_rewrite(query: str, history: list) -> bool:
    if not history:
        return False
    return any(t in query for t in _REWRITE_TRIGGERS)


def _rewrite_query(query: str, history: list) -> str:
    if not _should_rewrite(query, history):
        return query
    history_str = "\n".join(
        f"{'用户' if m['role'] == 'user' else '助手'}: {m['content'][:200]}"
        for m in history[-4:]
    )
    prompt = _REWRITE_PROMPT.format(history=history_str, query=query)
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 100,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    try:
        req = urllib.request.Request(
            LLM_ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        rewritten = body["choices"][0]["message"]["content"].strip()
        if rewritten and len(rewritten) > 3:
            return rewritten
    except Exception:
        pass
    return query

def ask(
    question: str,
    top_k: int = 3,
    session_id: str | None = None,
) -> dict[str, Any]:
    """End-to-end M2 RAG QA with multi-turn conversation support.

    Returns ``{answer, sources, model, collection, top_k, session_id}``.
    On generation failure, still returns the retrieved sources with a
    fallback answer so the UI remains useful.
    """
    question = (question or "").strip()
    top_k = max(1, min(int(top_k or 3), 10))

    # Session management
    if not session_id:
        session_id = new_session_id()
    session = _get_session(session_id)
    history = list(session["history"])  # snapshot before appending

    # Query rewriting: use LLM to resolve follow-ups into standalone queries
    retrieval_query = _rewrite_query(question, history)

    sources = retrieve(retrieval_query, top_k=top_k)

    if not sources:
        answer = "检索资料中未找到相关数据（集合可能为空或问题与已入库样本无关）。"
        _append_history(session, "user", question)
        _append_history(session, "assistant", answer)
        return {
            "answer": answer,
            "sources": [],
            "model": "",
            "collection": collection_name(),
            "top_k": top_k,
            "session_id": session_id,
        }

    prompt = _build_prompt(question, sources, history=history)
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

    # Store in conversation history
    _append_history(session, "user", question)
    _append_history(session, "assistant", answer)

    return {
        "answer": answer,
        "sources": sources,
        "model": model,
        "collection": collection_name(),
        "top_k": top_k,
        "session_id": session_id,
    }
