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
import re as _re

# --- PG persistence (graceful fallback if PG unavailable) ---
try:
    from storage.chat_persistence import (
        persist_session_create,
        persist_message,
        load_messages as pg_load_messages,
        clear_messages as pg_clear_messages,
    )
    _HAS_PERSISTENCE = True
except Exception:
    _HAS_PERSISTENCE = False

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
    """Get or create a session, performing lazy TTL cleanup.

    On first access for a session not in memory, attempts to load history
    from PostgreSQL (lazy load). New sessions are persisted to PG.
    """
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
            # Try loading from PG first
            history: list[dict[str, str]] = []
            if _HAS_PERSISTENCE:
                history = pg_load_messages(session_id)
            _sessions[session_id] = {"history": history, "last_active": now}
            if not history and _HAS_PERSISTENCE:
                persist_session_create(session_id)
        session = _sessions[session_id]
        session["last_active"] = now
        return session


def _append_history(session: dict[str, Any], role: str, content: str, session_id: str | None = None) -> None:
    """Append a message and trim to _MAX_TURNS. Persists to PG if available."""
    session["history"].append({"role": role, "content": content})
    if len(session["history"]) > _MAX_TURNS:
        session["history"] = session["history"][-_MAX_TURNS:]
    if _HAS_PERSISTENCE and session_id:
        persist_message(session_id, role, content)


def clear_session(session_id: str) -> bool:
    """Clear conversation history for a session. Returns True if existed."""
    with _sessions_lock:
        existed = session_id in _sessions
        if existed:
            _sessions[session_id]["history"] = []
            _sessions[session_id]["last_active"] = _time.time()
    if _HAS_PERSISTENCE:
        pg_clear_messages(session_id)
    return existed


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


def embedding_count() -> int:
    """Count embedding rows in the M2 collection (real PG count).

    Used by /api/health/full. RAGService has no `.collection` attribute,
    so the count must come from the langchain PG tables directly.
    """
    _load_rag()
    try:
        from storage.database.db import get_session
        from storage.database.shared.model import (
            LangchainPgCollection,
            LangchainPgEmbedding,
        )
        db = get_session()
        try:
            return int(
                db.query(LangchainPgEmbedding)
                .join(
                    LangchainPgCollection,
                    LangchainPgEmbedding.collection_id == LangchainPgCollection.uuid,
                )
                .filter(LangchainPgCollection.name == _rag_mod.COLLECTION)
                .count()
            )
        finally:
            db.close()
    except Exception:
        return 0


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

    # Comparison intent routing: detect and handle comparison queries
    if detect_compare_intent(question):
        try:
            cmp_result = handle_compare_query(question)
            cmp_answer = cmp_result.get("answer", "")
            _append_history(session, "user", question, session_id)
            _append_history(session, "assistant", cmp_answer, session_id)
            cmp_result["collection"] = collection_name()
            cmp_result["top_k"] = top_k
            cmp_result["session_id"] = session_id
            return cmp_result
        except Exception:
            pass  # fall through to regular RAG on comparison failure

    # Query rewriting: use LLM to resolve follow-ups into standalone queries
    retrieval_query = _rewrite_query(question, history)

    sources = retrieve(retrieval_query, top_k=top_k)

    if not sources:
        answer = "检索资料中未找到相关数据（集合可能为空或问题与已入库样本无关）。"
        _append_history(session, "user", question, session_id)
        _append_history(session, "assistant", answer, session_id)
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
    _append_history(session, "user", question, session_id)
    _append_history(session, "assistant", answer, session_id)

    return {
        "answer": answer,
        "sources": sources,
        "model": model,
        "collection": collection_name(),
        "top_k": top_k,
        "session_id": session_id,
    }


# ---------------------------------------------------------------------------
# Cross-document comparison (Phase 1)
# ---------------------------------------------------------------------------

_COMPARE_TRIGGERS = ["对比", "变化", "比上月", "差异", "增减", "比较", "vs", "VS"]


def _get_db_session():
    """Get a SQLAlchemy session for metadata queries (same PGVector DB)."""
    from storage.database.db import get_session
    return get_session()


def _query_collection_chunks(product_name: str | None = None,
                             statement_date: str | None = None,
                             table_name: str | None = None) -> list[dict[str, Any]]:
    """Query chunk documents + metadata from the M2 collection.

    Read-only metadata aggregation on the existing PGVector collection —
    does NOT create a second vector store or bypass RAGService for retrieval.
    """
    from storage.database.shared.model import LangchainPgCollection, LangchainPgEmbedding
    db = _get_db_session()
    try:
        col_name = collection_name()
        query = (
            db.query(LangchainPgEmbedding.document, LangchainPgEmbedding.cmetadata)
            .join(LangchainPgCollection,
                  LangchainPgEmbedding.collection_id == LangchainPgCollection.uuid)
            .filter(LangchainPgCollection.name == col_name)
        )
        if product_name:
            query = query.filter(
                LangchainPgEmbedding.cmetadata["product_name"].astext == product_name)
        if statement_date:
            query = query.filter(
                LangchainPgEmbedding.cmetadata["statement_date"].astext == statement_date)
        if table_name:
            query = query.filter(
                LangchainPgEmbedding.cmetadata["table_name"].astext == table_name)
        rows = query.all()
        return [{"document": r[0], "metadata": r[1] or {}} for r in rows]
    finally:
        db.close()


def list_products() -> list[str]:
    """Return distinct product_name values from the M2 collection metadata."""
    from storage.database.shared.model import LangchainPgCollection, LangchainPgEmbedding
    from sqlalchemy import distinct
    db = _get_db_session()
    try:
        col_name = collection_name()
        rows = (
            db.query(distinct(LangchainPgEmbedding.cmetadata["product_name"].astext))
            .join(LangchainPgCollection,
                  LangchainPgEmbedding.collection_id == LangchainPgCollection.uuid)
            .filter(LangchainPgCollection.name == col_name)
            .filter(LangchainPgEmbedding.cmetadata["product_name"].astext != "")
            .all()
        )
        return sorted([r[0] for r in rows if r[0]])
    finally:
        db.close()


def _parse_chunk_fields(text: str) -> dict[str, str]:
    """Parse 'key=value' pairs from a chunk text line."""
    fields: dict[str, str] = {}
    for line in (text or "").split("\n"):
        if line.startswith("字段:") or line.startswith("字段: "):
            pairs_str = line.split(":", 1)[-1].strip()
            if pairs_str.startswith(" "):
                pairs_str = pairs_str[1:]
            for pair in pairs_str.split(", "):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    fields[k.strip()] = v.strip()
    return fields


def get_product_timeline(product: str) -> dict[str, Any]:
    """Return snapshots for a product sorted by statement_date.

    Each snapshot: {date, total_assets, position_count, currency}.
    """
    chunks = _query_collection_chunks(product_name=product)
    if not chunks:
        return {"product": product, "timeline": []}

    dates_seen: dict[str, dict[str, Any]] = {}
    for chunk in chunks:
        meta = chunk["metadata"]
        date = meta.get("statement_date", "")
        if not date:
            continue
        if date not in dates_seen:
            dates_seen[date] = {
                "date": date,
                "total_assets": "",
                "position_count": 0,
                "currency": "人民币",
            }
        text = chunk["document"] or ""
        # table_name may be a raw id (p0_table_3); matched_schema carries the
        # schema table name (证券持仓明细/资金资产汇总) needed for detection.
        table = f'{meta.get("table_name", "")} {meta.get("matched_schema", "")}'
        fields = _parse_chunk_fields(text)
        if "资产汇总" in table or "资金资产" in table:
            for key in ("总资产", "资产总值", "资产合计"):
                if key in fields and fields[key]:
                    dates_seen[date]["total_assets"] = fields[key]
                    break
            for key in ("币种", "货币"):
                if key in fields and fields[key]:
                    dates_seen[date]["currency"] = fields[key]
                    break
        if "持仓" in table:
            dates_seen[date]["position_count"] += 1

    timeline = sorted(dates_seen.values(), key=lambda x: x["date"])
    return {"product": product, "timeline": timeline}


def compare_dates(product: str, date_a: str, date_b: str,
                  fields: list[str] | None = None) -> dict[str, Any]:
    """Field-level diff between two statement dates for a product.

    If the product has fewer than 2 dates, returns insufficient_data status.
    """
    timeline = get_product_timeline(product)
    available_dates = [s["date"] for s in timeline["timeline"]]
    if len(available_dates) < 2:
        return {
            "product": product,
            "date_a": date_a,
            "date_b": date_b,
            "status": "insufficient_data",
            "message": "该产品仅有一期对账单，跨期对比需甲方提供多期数据",
            "available_dates": available_dates,
        }

    chunks_a = _query_collection_chunks(product_name=product, statement_date=date_a)
    chunks_b = _query_collection_chunks(product_name=product, statement_date=date_b)

    def _collect_fields(chunks: list[dict]) -> dict[str, str]:
        all_fields: dict[str, str] = {}
        for c in chunks:
            all_fields.update(_parse_chunk_fields(c["document"] or ""))
        return all_fields

    fa = _collect_fields(chunks_a)
    fb = _collect_fields(chunks_b)
    target_fields = fields or sorted(set(fa.keys()) | set(fb.keys()))

    diffs = []
    for field in target_fields:
        va = fa.get(field, "")
        vb = fb.get(field, "")
        change = ""
        change_pct = ""
        na = _try_float(va)
        nb = _try_float(vb)
        if na is not None and nb is not None:
            delta = nb - na
            change = f"{delta:+,.2f}"
            if na != 0:
                change_pct = f"{(delta / na) * 100:+.2f}%"
        diffs.append({
            "field": field,
            "value_a": va,
            "value_b": vb,
            "change": change,
            "change_pct": change_pct,
        })

    return {
        "product": product,
        "date_a": date_a,
        "date_b": date_b,
        "status": "ok",
        "diffs": diffs,
    }


def _try_float(val: str) -> float | None:
    """Try to parse a numeric value from a (possibly desensitized) string."""
    if not val or "****" in val:
        return None
    try:
        return float(val.replace(",", "").replace("，", ""))
    except (ValueError, AttributeError):
        return None


def compare_positions(product: str, date: str) -> dict[str, Any]:
    """Compare positions within a single statement.

    Returns all positions sorted by market value with percentage of total.
    """
    chunks = _query_collection_chunks(product_name=product, statement_date=date)
    if not chunks:
        chunks = _query_collection_chunks(product_name=product)

    positions: list[dict[str, str]] = []
    total_mv = 0.0
    for chunk in chunks:
        meta = chunk["metadata"]
        table = f'{meta.get("table_name", "")} {meta.get("matched_schema", "")}'
        if "持仓" not in table:
            continue
        fields = _parse_chunk_fields(chunk["document"] or "")
        if not fields:
            continue
        name = ""
        for k in ("证券名称", "证券简称", "名称", "股票名称"):
            if k in fields and fields[k]:
                name = fields[k]
                break
        mv_str = ""
        for k in ("市值", "证券市值", "持仓市值", "最新市值"):
            if k in fields and fields[k]:
                mv_str = fields[k]
                break
        mv = _try_float(mv_str)
        positions.append({
            "name": name or "(未知)",
            "market_value": mv_str,
            "market_value_num": mv,
            "fields": fields,
        })
        if mv is not None:
            total_mv += mv

    positions.sort(key=lambda p: p.get("market_value_num") or 0, reverse=True)
    for p in positions:
        mv = p.get("market_value_num")
        if mv is not None and total_mv > 0:
            p["pct_of_total"] = f"{(mv / total_mv) * 100:.2f}%"
        else:
            p["pct_of_total"] = "-"
        del p["market_value_num"]

    return {
        "product": product,
        "date": date,
        "total_market_value": f"{total_mv:,.2f}" if total_mv > 0 else "-",
        "position_count": len(positions),
        "positions": positions,
    }


# ---------------------------------------------------------------------------
# Natural-language comparison routing
# ---------------------------------------------------------------------------

def detect_compare_intent(question: str) -> bool:
    """Return True if the question looks like a comparison query."""
    return any(t in question for t in _COMPARE_TRIGGERS)


def _extract_compare_params(question: str) -> dict[str, Any]:
    """Extract product name, dates, and fields from a comparison question.

    Uses keyword matching against known products + regex for dates.
    Falls back to LLM extraction when keyword matching is insufficient.
    """
    params: dict[str, Any] = {"product": None, "date_a": None, "date_b": None, "fields": None}

    try:
        products = list_products()
    except Exception:
        products = []
    for p in products:
        if p in question:
            params["product"] = p
            break

    dates = _re.findall(r"\d{8}", question)
    if len(dates) >= 2:
        params["date_a"] = dates[0]
        params["date_b"] = dates[1]
    elif len(dates) == 1:
        params["date_a"] = dates[0]

    known_fields = ["总资产", "资产总值", "资金余额", "市值", "证券市值", "份额", "净值"]
    found = [f for f in known_fields if f in question]
    if found:
        params["fields"] = found

    return params


def _format_compare_answer(result: dict[str, Any]) -> str:
    """Format a comparison result dict as a natural-language answer."""
    if result.get("status") == "insufficient_data":
        msg = result.get("message", "数据不足，无法对比。")
        dates = result.get("available_dates", [])
        extra = f"（现有日期: {', '.join(dates)}）" if dates else ""
        return f"⚠ {msg}{extra}"

    if "positions" in result:
        lines = [f"📊 {result['product']} 持仓对比（{result['date']}）"]
        lines.append(f"持仓数: {result['position_count']}  总市值: {result['total_market_value']}")
        lines.append("")
        for i, p in enumerate(result["positions"], 1):
            lines.append(f"{i}. {p['name']}  市值={p['market_value']}  占比={p['pct_of_total']}")
        return "\n".join(lines)

    if "diffs" in result:
        lines = [f"📊 {result['product']} 跨期对比: {result['date_a']} vs {result['date_b']}"]
        lines.append("")
        for d in result["diffs"]:
            change_str = f"  变化={d['change']}" if d["change"] else ""
            pct_str = f" ({d['change_pct']})" if d["change_pct"] else ""
            lines.append(f"- {d['field']}: {d['value_a']} → {d['value_b']}{change_str}{pct_str}")
        return "\n".join(lines)

    return json.dumps(result, ensure_ascii=False, indent=2)


def handle_compare_query(question: str) -> dict[str, Any]:
    """Handle a comparison-intent question end-to-end.

    Returns the same shape as ask(): {answer, sources, model, ...}.
    """
    params = _extract_compare_params(question)
    product = params.get("product")

    if not product:
        try:
            products = list_products()
        except Exception:
            products = []
        if products:
            product = products[0]
        else:
            return {
                "answer": "未找到可对比的产品。请先确认 M1 解析结果已入库。",
                "sources": [],
                "model": "",
                "compare_mode": True,
            }

    if params.get("date_a") and params.get("date_b"):
        result = compare_dates(product, params["date_a"], params["date_b"],
                               params.get("fields"))
    else:
        timeline = get_product_timeline(product)
        dates = [s["date"] for s in timeline["timeline"]]
        if len(dates) >= 2:
            result = compare_dates(product, dates[0], dates[-1], params.get("fields"))
        else:
            date = dates[0] if dates else ""
            result = compare_positions(product, date)

    answer = _format_compare_answer(result)
    return {
        "answer": answer,
        "sources": [],
        "model": "rule-based-compare",
        "compare_mode": True,
        "compare_result": result,
    }
