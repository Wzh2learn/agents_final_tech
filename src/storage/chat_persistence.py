"""Chat session persistence to PostgreSQL.

Tables: chat_sessions, chat_messages (created on first use).
Uses PGDATABASE_URL env var. Falls back gracefully if PG is unavailable.
"""
from __future__ import annotations

import logging
import os
import threading
from typing import Any

logger = logging.getLogger("m1.chat_persist")

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36) REFERENCES chat_sessions(session_id),
    role VARCHAR(10) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
"""

# Bounded PG I/O when held under m2_service._sessions_lock (Loop C audit F1).
# connect_timeout bounds the TCP/SSL establish; statement_timeout bounds each
# query so a stalled PG cannot hang the :5050 worker indefinitely. Aligns with
# the memory_saver.py connect_timeout precedent. Values are env-tunable.
_CONNECT_TIMEOUT = int(os.environ.get("M2_PG_CONNECT_TIMEOUT", "5"))   # seconds
_STATEMENT_TIMEOUT = int(os.environ.get("M2_PG_STATEMENT_TIMEOUT", "10000"))  # ms

_conn_lock = threading.Lock()
_conn = None
_tables_created = False


def _get_conn():
    """Get or create a psycopg connection. Returns None if unavailable."""
    global _conn, _tables_created
    url = os.environ.get("PGDATABASE_URL", "")
    if not url:
        return None
    with _conn_lock:
        if _conn is None or _conn.closed:
            try:
                import psycopg
                _conn = psycopg.connect(
                    url,
                    autocommit=True,
                    connect_timeout=_CONNECT_TIMEOUT,
                    options=f"-c statement_timeout={_STATEMENT_TIMEOUT}",
                )
            except Exception as e:
                logger.warning(f"Chat persistence: cannot connect to PG: {e}")
                _conn = None
                return None
        if not _tables_created and _conn is not None:
            try:
                _conn.execute(_CREATE_SQL)
                _tables_created = True
                logger.info("Chat persistence tables ensured")
            except Exception as e:
                logger.warning(f"Chat persistence: table creation failed: {e}")
        return _conn


def persist_session_create(session_id: str) -> None:
    """Insert a new session row (idempotent)."""
    conn = _get_conn()
    if conn is None:
        return
    try:
        conn.execute(
            "INSERT INTO chat_sessions (session_id) VALUES (%s) ON CONFLICT (session_id) DO UPDATE SET last_active = NOW()",
            (session_id,),
        )
    except Exception as e:
        logger.debug(f"persist_session_create failed: {e}")


def persist_message(session_id: str, role: str, content: str) -> None:
    """Insert a message row."""
    conn = _get_conn()
    if conn is None:
        return
    try:
        conn.execute(
            "INSERT INTO chat_messages (session_id, role, content) VALUES (%s, %s, %s)",
            (session_id, role, content),
        )
        conn.execute(
            "UPDATE chat_sessions SET last_active = NOW() WHERE session_id = %s",
            (session_id,),
        )
    except Exception as e:
        logger.debug(f"persist_message failed: {e}")


def load_messages(session_id: str) -> list[dict[str, str]]:
    """Load all messages for a session ordered by id."""
    conn = _get_conn()
    if conn is None:
        return []
    try:
        cur = conn.execute(
            "SELECT role, content FROM chat_messages WHERE session_id = %s ORDER BY id",
            (session_id,),
        )
        return [{"role": row[0], "content": row[1]} for row in cur.fetchall()]
    except Exception as e:
        logger.debug(f"load_messages failed: {e}")
        return []


def clear_messages(session_id: str) -> None:
    """Delete all messages for a session."""
    conn = _get_conn()
    if conn is None:
        return
    try:
        conn.execute(
            "DELETE FROM chat_messages WHERE session_id = %s",
            (session_id,),
        )
    except Exception as e:
        logger.debug(f"clear_messages failed: {e}")


def session_exists_in_pg(session_id: str) -> bool:
    """Check if a session exists in PG."""
    conn = _get_conn()
    if conn is None:
        return False
    try:
        cur = conn.execute(
            "SELECT 1 FROM chat_sessions WHERE session_id = %s",
            (session_id,),
        )
        return cur.fetchone() is not None
    except Exception:
        return False
