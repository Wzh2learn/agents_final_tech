"""Tests for M2 multi-turn conversation support.

Unit tests for session management, history trimming, TTL expiry, context
injection, and the API contract. Does NOT require live PGVector or :8004.

Integration test (marked ``integration``) requires the full stack.
"""
from __future__ import annotations

import time
import threading
from unittest.mock import patch, MagicMock

import pytest

# Ensure src/ is importable
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


# ---------------------------------------------------------------------------
# Session management unit tests
# ---------------------------------------------------------------------------

class TestSessionManagement:
    """Test in-memory session store logic."""

    def setup_method(self):
        """Reset global session state before each test."""
        import biz.m2_service as svc
        with svc._sessions_lock:
            svc._sessions.clear()

    def test_new_session_id_is_uuid(self):
        import biz.m2_service as svc
        sid = svc.new_session_id()
        assert len(sid) == 36  # UUID format
        assert sid.count("-") == 4

    def test_get_session_creates_new(self):
        import biz.m2_service as svc
        session = svc._get_session("test-123")
        assert session["history"] == []
        assert "last_active" in session

    def test_get_session_returns_existing(self):
        import biz.m2_service as svc
        s1 = svc._get_session("test-abc")
        svc._append_history(s1, "user", "hello")
        s2 = svc._get_session("test-abc")
        assert len(s2["history"]) == 1
        assert s2["history"][0]["content"] == "hello"

    def test_append_history_trims_to_max(self):
        import biz.m2_service as svc
        session = svc._get_session("trim-test")
        for i in range(25):
            svc._append_history(session, "user", f"msg {i}")
        assert len(session["history"]) == svc._MAX_TURNS
        # Oldest messages trimmed, newest kept
        assert session["history"][-1]["content"] == "msg 24"
        assert session["history"][0]["content"] == f"msg {25 - svc._MAX_TURNS}"

    def test_clear_session(self):
        import biz.m2_service as svc
        session = svc._get_session("clear-test")
        svc._append_history(session, "user", "q1")
        svc._append_history(session, "assistant", "a1")
        assert svc.clear_session("clear-test") is True
        assert session["history"] == []

    def test_clear_nonexistent_session(self):
        import biz.m2_service as svc
        assert svc.clear_session("nonexistent") is False

    def test_expired_sessions_cleaned_lazily(self):
        import biz.m2_service as svc
        session = svc._get_session("old-session")
        svc._append_history(session, "user", "old msg")
        # Manually age the session beyond TTL
        with svc._sessions_lock:
            svc._sessions["old-session"]["last_active"] = time.time() - svc._SESSION_TTL - 1
        # Accessing a different session triggers cleanup
        svc._get_session("new-session")
        with svc._sessions_lock:
            assert "old-session" not in svc._sessions

    def test_thread_safety(self):
        import biz.m2_service as svc
        errors = []

        def worker(n):
            try:
                for i in range(20):
                    sid = f"thread-{n}"
                    s = svc._get_session(sid)
                    svc._append_history(s, "user", f"msg {i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(n,)) for n in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []


# ---------------------------------------------------------------------------
# Context injection tests
# ---------------------------------------------------------------------------

class TestContextInjection:
    """Test that conversation history is injected into the prompt."""

    def test_build_prompt_without_history(self):
        import biz.m2_service as svc
        sources = [{"sample_id": "s1", "table_name": "t1", "score": 0.9, "text": "data"}]
        prompt = svc._build_prompt("问题", sources, history=None)
        assert "【对话历史】" not in prompt
        assert "【检索资料】" in prompt
        assert "【用户问题】" in prompt

    def test_build_prompt_with_history(self):
        import biz.m2_service as svc
        sources = [{"sample_id": "s1", "table_name": "t1", "score": 0.9, "text": "data"}]
        history = [
            {"role": "user", "content": "嘉兴民安的总资产是多少？"},
            {"role": "assistant", "content": "总资产为401383291.83元。"},
        ]
        prompt = svc._build_prompt("其中证券市值占多少？", sources, history=history)
        assert "【对话历史】" in prompt
        assert "嘉兴民安的总资产是多少？" in prompt
        assert "401383291.83" in prompt
        assert "其中证券市值占多少？" in prompt
        assert "金融对账单分析助手" in prompt

    def test_build_prompt_limits_history_to_context_turns(self):
        import biz.m2_service as svc
        sources = [{"sample_id": "s1", "table_name": "t1", "score": 0.9, "text": "x"}]
        history = [
            {"role": "user", "content": f"q{i}"} for i in range(20)
        ]
        prompt = svc._build_prompt("new q", sources, history=history)
        # Only last _CONTEXT_TURNS messages should appear
        assert "q0" not in prompt
        assert f"q{19}" in prompt


# ---------------------------------------------------------------------------
# ask() function tests (mocked retrieval + generation)
# ---------------------------------------------------------------------------

class TestAskFunction:
    """Test the ask() function with mocked dependencies."""

    def setup_method(self):
        import biz.m2_service as svc
        with svc._sessions_lock:
            svc._sessions.clear()

    @patch("biz.m2_service._generate")
    @patch("biz.m2_service.retrieve")
    @patch("biz.m2_service.collection_name", return_value="test_collection")
    def test_ask_returns_session_id(self, mock_col, mock_ret, mock_gen):
        import biz.m2_service as svc
        mock_ret.return_value = [
            {"sample_id": "jiaxing", "table_name": "asset", "score": 0.95, "text": "总资产 401383291.83"}
        ]
        mock_gen.return_value = ("总资产为401383291.83元。", "test-model")

        result = svc.ask("嘉兴民安的总资产是多少？", top_k=3)
        assert "session_id" in result
        assert len(result["session_id"]) == 36
        assert result["answer"] == "总资产为401383291.83元。"

    @patch("biz.m2_service._generate")
    @patch("biz.m2_service.retrieve")
    @patch("biz.m2_service.collection_name", return_value="test_collection")
    def test_ask_preserves_session_across_turns(self, mock_col, mock_ret, mock_gen):
        import biz.m2_service as svc
        mock_ret.return_value = [
            {"sample_id": "jiaxing", "table_name": "asset", "score": 0.9, "text": "data"}
        ]
        mock_gen.return_value = ("answer", "model")

        r1 = svc.ask("Q1", session_id="my-session")
        r2 = svc.ask("Q2", session_id="my-session")
        assert r1["session_id"] == "my-session"
        assert r2["session_id"] == "my-session"

        # History should have 4 messages (2 turns x 2 messages)
        session = svc._get_session("my-session")
        assert len(session["history"]) == 4
        assert session["history"][0] == {"role": "user", "content": "Q1"}
        assert session["history"][1] == {"role": "assistant", "content": "answer"}
        assert session["history"][2] == {"role": "user", "content": "Q2"}

    @patch("biz.m2_service._generate")
    @patch("biz.m2_service.retrieve")
    @patch("biz.m2_service.collection_name", return_value="test_collection")
    def test_ask_injects_history_into_prompt(self, mock_col, mock_ret, mock_gen):
        import biz.m2_service as svc
        mock_ret.return_value = [
            {"sample_id": "s1", "table_name": "t1", "score": 0.9, "text": "data"}
        ]
        mock_gen.return_value = ("resp", "model")

        svc.ask("First question", session_id="ctx-test")
        svc.ask("Follow-up question", session_id="ctx-test")

        # Check that the second call's prompt included history
        second_call_prompt = mock_gen.call_args_list[1][0][0]
        assert "First question" in second_call_prompt
        assert "【对话历史】" in second_call_prompt

    @patch("biz.m2_service.retrieve")
    @patch("biz.m2_service.collection_name", return_value="test_collection")
    def test_ask_no_sources_still_tracks_session(self, mock_col, mock_ret):
        import biz.m2_service as svc
        mock_ret.return_value = []

        result = svc.ask("unknown question", session_id="empty-test")
        assert result["session_id"] == "empty-test"
        assert "未找到" in result["answer"]

        session = svc._get_session("empty-test")
        assert len(session["history"]) == 2


# ---------------------------------------------------------------------------
# API contract tests (FastAPI TestClient)
# ---------------------------------------------------------------------------

class TestAPIContract:
    """Test the HTTP API contract using FastAPI TestClient."""

    @pytest.fixture
    def client(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from web.routers.m2 import router

        app = FastAPI()
        app.include_router(router, prefix="/api/m2")
        return TestClient(app)

    @patch("biz.m2_service._generate")
    @patch("biz.m2_service.retrieve")
    @patch("biz.m2_service.collection_name", return_value="test_col")
    def test_ask_without_session_id_generates_one(self, mock_col, mock_ret, mock_gen, client):
        mock_ret.return_value = [
            {"sample_id": "s", "table_name": "t", "score": 0.8, "text": "x"}
        ]
        mock_gen.return_value = ("ans", "m")

        resp = client.post("/api/m2/ask", json={"question": "test?"})
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert len(data["session_id"]) == 36

    @patch("biz.m2_service._generate")
    @patch("biz.m2_service.retrieve")
    @patch("biz.m2_service.collection_name", return_value="test_col")
    def test_ask_with_session_id_returns_same(self, mock_col, mock_ret, mock_gen, client):
        mock_ret.return_value = [
            {"sample_id": "s", "table_name": "t", "score": 0.8, "text": "x"}
        ]
        mock_gen.return_value = ("ans", "m")

        resp = client.post("/api/m2/ask", json={
            "question": "test?", "session_id": "fixed-id-123"
        })
        data = resp.json()
        assert data["session_id"] == "fixed-id-123"

    @patch("biz.m2_service._generate")
    @patch("biz.m2_service.retrieve")
    @patch("biz.m2_service.collection_name", return_value="test_col")
    def test_clear_session_endpoint(self, mock_col, mock_ret, mock_gen, client):
        mock_ret.return_value = [
            {"sample_id": "s", "table_name": "t", "score": 0.8, "text": "x"}
        ]
        mock_gen.return_value = ("ans", "m")

        # Create a session with history
        client.post("/api/m2/ask", json={"question": "q", "session_id": "clr-1"})
        # Clear it
        resp = client.post("/api/m2/sessions/clr-1/clear")
        assert resp.status_code == 200
        assert resp.json() == {"status": "cleared"}

    def test_health_endpoint(self, client):
        with patch("biz.m2_service.collection_name", return_value="test_col"):
            resp = client.get("/api/m2/health")
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Integration test (requires live services)
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestMultiTurnIntegration:
    """End-to-end multi-turn test requiring PGVector + :8004.

    Run with: pytest tests/test_m2_multiturn.py -m integration -v
    """

    def test_three_turn_conversation(self):
        import biz.m2_service as svc

        # Turn 1
        r1 = svc.ask("嘉兴民安的总资产是多少？", top_k=3)
        sid = r1["session_id"]
        assert "4013" in r1["answer"]  # partial match (may be masked)

        # Turn 2: follow-up referencing previous context
        r2 = svc.ask("其中证券市值占多少？", top_k=3, session_id=sid)
        assert r2["session_id"] == sid
        # Should reference 嘉兴 context, not ask "which sample?"
        assert "哪个" not in r2["answer"] or "嘉兴" in r2["answer"]

        # Turn 3: arithmetic follow-up
        r3 = svc.ask("和资金余额加起来对吗？", top_k=3, session_id=sid)
        assert r3["session_id"] == sid

        # Verify session has 6 messages (3 turns)
        session = svc._get_session(sid)
        assert len(session["history"]) == 6
