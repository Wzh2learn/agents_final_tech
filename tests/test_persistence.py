"""Tests for chat session persistence to PostgreSQL.

Requires PGDATABASE_URL to be set and PG reachable. Skipped otherwise.

Verifies:
1. Session + messages are persisted to PG.
2. Clearing a session deletes messages from PG.
"""
import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Check PG availability
_PG_URL = os.environ.get("PGDATABASE_URL", "")


def _pg_available() -> bool:
    if not _PG_URL:
        return False
    try:
        import psycopg
        conn = psycopg.connect(_PG_URL, autocommit=True, connect_timeout=3)
        conn.close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _pg_available(), reason="PGDATABASE_URL not set or PG unreachable"
)


@pytest.fixture(autouse=True)
def setup_pg_env(monkeypatch):
    """Ensure PGDATABASE_URL is set for the persistence module."""
    monkeypatch.setenv("PGDATABASE_URL", _PG_URL)
    # Reset the connection state
    import storage.chat_persistence as cp
    cp._conn = None
    cp._tables_created = False
    yield


class TestSessionPersistence:
    """PG-backed session persistence."""

    def test_session_persisted(self):
        """Create session, add messages, verify in PG."""
        from storage.chat_persistence import (
            persist_session_create,
            persist_message,
            load_messages,
            session_exists_in_pg,
        )

        sid = str(uuid.uuid4())
        persist_session_create(sid)
        assert session_exists_in_pg(sid)

        persist_message(sid, "user", "hello")
        persist_message(sid, "assistant", "hi there")

        msgs = load_messages(sid)
        assert len(msgs) == 2
        assert msgs[0] == {"role": "user", "content": "hello"}
        assert msgs[1] == {"role": "assistant", "content": "hi there"}

    def test_session_survives_clear(self):
        """Clear session, verify messages deleted from PG."""
        from storage.chat_persistence import (
            persist_session_create,
            persist_message,
            load_messages,
            clear_messages,
        )

        sid = str(uuid.uuid4())
        persist_session_create(sid)
        persist_message(sid, "user", "q1")
        persist_message(sid, "assistant", "a1")

        # Verify messages exist
        assert len(load_messages(sid)) == 2

        # Clear
        clear_messages(sid)

        # Verify deleted
        assert len(load_messages(sid)) == 0
