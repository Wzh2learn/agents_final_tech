"""Unit tests for M2 RAG QA service (src/biz/m2_service.py).

All external dependencies (PGVector, embedding model, LLM :8004) are mocked.
"""

import os
import sys
from unittest import mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import biz.m2_service as m2


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

class TestSessionManagement:
    def test_new_session_id_unique(self):
        ids = {m2.new_session_id() for _ in range(10)}
        assert len(ids) == 10

    def test_get_session_creates_and_reuses(self):
        sid = m2.new_session_id()
        s1 = m2._get_session(sid)
        s2 = m2._get_session(sid)
        assert s1 is s2

    def test_append_history_trims(self):
        session = {"history": [], "last_active": 0}
        for i in range(15):
            m2._append_history(session, "user", f"msg{i}")
        assert len(session["history"]) == m2._MAX_TURNS

    def test_clear_session(self):
        sid = m2.new_session_id()
        m2._get_session(sid)
        assert m2.clear_session(sid) is True
        assert m2.clear_session("nonexistent-id") is False


# ---------------------------------------------------------------------------
# _build_prompt
# ---------------------------------------------------------------------------

class TestBuildPrompt:
    def test_sources_injected(self):
        sources = [
            {"sample_id": "s1", "table_name": "持仓", "score": 0.9, "text": "平安银行 100"},
        ]
        prompt = m2._build_prompt("市值多少?", sources)
        assert "平安银行" in prompt
        assert "市值多少?" in prompt
        assert "检索资料" in prompt

    def test_empty_sources(self):
        prompt = m2._build_prompt("问题", [])
        assert "无检索结果" in prompt

    def test_history_injected(self):
        history = [
            {"role": "user", "content": "之前的问题"},
            {"role": "assistant", "content": "之前的回答"},
        ]
        prompt = m2._build_prompt("新问题", [], history=history)
        assert "对话历史" in prompt
        assert "之前的问题" in prompt


# ---------------------------------------------------------------------------
# ask: end-to-end with mocked retrieve + generate
# ---------------------------------------------------------------------------

class TestAsk:
    def test_rag_answer_with_context(self):
        """Mock retrieve + generate -> structured answer response."""
        fake_sources = [
            {"sample_id": "s1", "table_name": "持仓", "score": 0.85, "text": "市值 100"},
        ]
        with mock.patch.object(m2, "retrieve", return_value=fake_sources), \
             mock.patch.object(m2, "_generate", return_value=("答案是100", "test-model")), \
             mock.patch.object(m2, "collection_name", return_value="test_col"):
            result = m2.ask("市值多少?", top_k=3)
        assert result["answer"] == "答案是100"
        assert len(result["sources"]) == 1
        assert result["model"] == "test-model"
        assert result["collection"] == "test_col"
        assert result["top_k"] == 3

    def test_rag_empty_collection(self):
        """Empty retrieval -> fallback message, no LLM call."""
        with mock.patch.object(m2, "retrieve", return_value=[]), \
             mock.patch.object(m2, "_generate") as mock_gen, \
             mock.patch.object(m2, "collection_name", return_value="test_col"):
            result = m2.ask("不存在的问题")
        assert "未找到" in result["answer"]
        assert result["sources"] == []
        mock_gen.assert_not_called()

    def test_rag_session_context(self):
        """Multi-turn: second call sees first turn in history."""
        sid = m2.new_session_id()
        fake_sources = [{"sample_id": "s1", "table_name": "t", "score": 0.5, "text": "data"}]

        captured_prompts = []
        def fake_generate(prompt):
            captured_prompts.append(prompt)
            return ("ok", "m")

        with mock.patch.object(m2, "retrieve", return_value=fake_sources), \
             mock.patch.object(m2, "_generate", side_effect=fake_generate), \
             mock.patch.object(m2, "collection_name", return_value="c"):
            m2.ask("第一个问题", session_id=sid)
            m2.ask("第二个问题", session_id=sid)

        assert len(captured_prompts) == 2
        assert "第一个问题" in captured_prompts[1]

    def test_rag_top_k_parameter(self):
        """top_k is clamped and forwarded to retrieve."""
        with mock.patch.object(m2, "retrieve", return_value=[]) as mock_ret, \
             mock.patch.object(m2, "collection_name", return_value="c"):
            result = m2.ask("q", top_k=99)
        assert result["top_k"] == 10  # clamped to max 10
        mock_ret.assert_called_once_with("q", top_k=10)

    def test_rag_generation_failure_fallback(self):
        """LLM failure -> retrieval-only fallback with sources."""
        fake_sources = [
            {"sample_id": "s1", "table_name": "t", "score": 0.9, "text": "some data"},
        ]
        with mock.patch.object(m2, "retrieve", return_value=fake_sources), \
             mock.patch.object(m2, "_generate", side_effect=RuntimeError("timeout")), \
             mock.patch.object(m2, "collection_name", return_value="c"):
            result = m2.ask("q")
        assert "生成模型调用失败" in result["answer"]
        assert len(result["sources"]) == 1
        assert result["model"] == ""
