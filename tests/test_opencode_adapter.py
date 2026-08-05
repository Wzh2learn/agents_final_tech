"""Unit tests for the OpenCode sidecar adapter and the M2 grey switch."""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from biz import opencode_adapter as oc


class FakeResp:
    def __init__(self, status=200, payload=None):
        self.status_code = status
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")


def test_route_switch_default_off(monkeypatch):
    monkeypatch.delenv("M2_OPENCODE_ROUTE", raising=False)
    assert oc.route_enabled() is False
    monkeypatch.setenv("M2_OPENCODE_ROUTE", "on")
    assert oc.route_enabled() is True


def test_ask_returns_none_when_sidecar_down(monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("down")

    monkeypatch.setattr(oc.httpx, "get", boom)
    assert oc.ask_via_opencode("x") is None


def test_ask_success_parses_json_and_cleans_session(monkeypatch):
    deleted = []
    posts = []

    def fake_get(*a, **k):
        return FakeResp(200, [])

    def fake_post(url, json=None, timeout=None):
        posts.append((url, json))
        if url.endswith("/session"):
            return FakeResp(200, {"id": "ses_t1"})
        return FakeResp(
            200,
            {
                "info": {"modelID": "qwen3.6-35b-a3b"},
                "parts": [
                    {
                        "type": "text",
                        "text": 'noise {"answer": "总资产为 1 元, 出处 sample_x/table_1/总资产", '
                        '"sources": [{"sample_id": "sample_x", "table_name": "table_1", "field": "总资产"}]}',
                    }
                ],
            },
        )

    monkeypatch.setattr(oc.httpx, "get", fake_get)
    monkeypatch.setattr(oc.httpx, "post", fake_post)
    monkeypatch.setattr(
        oc.httpx, "delete", lambda url, timeout=None: deleted.append(url) or FakeResp(200, {})
    )

    res = oc.ask_via_opencode("总资产是多少？")
    assert res is not None
    assert res["answer"].startswith("总资产")
    assert res["sources"][0]["sample_id"] == "sample_x"
    assert res["route"] == "opencode"
    assert res["model"].startswith("opencode:")
    assert any("ses_t1" in u for u in deleted), "throwaway session must be deleted"
    assert posts[1][1]["agent"] == "m2-qa"


def test_ask_retries_without_agent_on_400(monkeypatch):
    calls = []

    def fake_post(url, json=None, timeout=None):
        if url.endswith("/session"):
            return FakeResp(200, {"id": "ses_t2"})
        calls.append(json)
        if "agent" in json:
            return FakeResp(400, {"error": "bad agent"})
        return FakeResp(200, {"parts": [{"type": "text", "text": '{"answer": "ok", "sources": []}'}]})

    monkeypatch.setattr(oc.httpx, "get", lambda *a, **k: FakeResp(200, []))
    monkeypatch.setattr(oc.httpx, "post", fake_post)
    monkeypatch.setattr(oc.httpx, "delete", lambda *a, **k: FakeResp(200, {}))
    res = oc.ask_via_opencode("q")
    assert res is not None and res["answer"] == "ok"
    assert len(calls) == 2 and "agent" not in calls[1]


def test_cleanup_caps_oldest(monkeypatch):
    sessions = [
        {"id": "a", "time": {"updated": 1}},
        {"id": "b", "time": {"updated": 3}},
        {"id": "c", "time": {"updated": 2}},
    ]
    deleted = []
    monkeypatch.setattr(oc.httpx, "get", lambda *a, **k: FakeResp(200, sessions))
    monkeypatch.setattr(
        oc.httpx,
        "delete",
        lambda url, timeout=None: deleted.append(url.rsplit("/", 1)[-1]) or FakeResp(200, {}),
    )
    out = oc.cleanup_sessions(max_keep=1)
    assert out == {"before": 3, "deleted": 2, "kept": 1}
    assert sorted(deleted) == ["a", "c"]


def test_parse_structured_fallback():
    assert oc._parse_structured("plain text only") == ("plain text only", [])


# --- router-level switch behavior (isolated module load, stubbed m2_service) ---


def _load_router_with_stub(monkeypatch, oc_result):
    stub = types.ModuleType("biz.m2_service")
    state = {"direct": 0, "appended": []}

    def ask(question, top_k=3, session_id=None):
        state["direct"] += 1
        return {"answer": "direct", "sources": [], "model": "m", "session_id": session_id or "sid-direct"}

    stub.ask = ask
    stub.clear_session = lambda sid: True
    stub.collection_name = lambda: "c"
    stub.list_products = lambda: []
    stub.get_product_timeline = lambda n: {}
    stub.compare_dates = lambda *a, **k: {}
    stub.compare_positions = lambda *a, **k: {}
    stub.detect_compare_intent = lambda q: False
    stub.get_history = lambda sid: []
    stub.append_turn = lambda sid, role, content: state["appended"].append((role, content))
    stub.new_session_id = lambda: "sid-new"
    monkeypatch.setitem(sys.modules, "biz.m2_service", stub)

    spec = importlib.util.spec_from_file_location("m2_router_under_test", SRC / "web" / "routers" / "m2.py")
    mod = importlib.util.module_from_spec(spec)
    # pydantic resolves annotations via sys.modules[cls.__module__]; register it
    monkeypatch.setitem(sys.modules, "m2_router_under_test", mod)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod.opencode_adapter, "ask_via_opencode", lambda *a, **k: oc_result)
    return mod, state


def _client_for(mod):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()
    app.include_router(mod.router, prefix="/api/m2")
    return TestClient(app)


def test_router_switch_off_uses_direct(monkeypatch):
    monkeypatch.delenv("M2_OPENCODE_ROUTE", raising=False)
    mod, state = _load_router_with_stub(
        monkeypatch, {"answer": "oc", "sources": [], "model": "x", "route": "opencode"}
    )
    r = _client_for(mod).post("/api/m2/ask", json={"question": "q"})
    assert r.status_code == 200
    assert r.json()["answer"] == "direct"
    assert state["direct"] == 1


def test_router_switch_on_uses_opencode_and_records_history(monkeypatch):
    monkeypatch.setenv("M2_OPENCODE_ROUTE", "on")
    mod, state = _load_router_with_stub(
        monkeypatch,
        {"answer": "oc-answer", "sources": [{"sample_id": "s"}], "model": "opencode:m", "route": "opencode"},
    )
    body = _client_for(mod).post("/api/m2/ask", json={"question": "q"}).json()
    assert body["answer"] == "oc-answer"
    assert body["route"] == "opencode"
    assert body["session_id"] == "sid-new"
    assert state["direct"] == 0
    assert state["appended"] == [("user", "q"), ("assistant", "oc-answer")]


def test_router_switch_on_fallback_when_sidecar_fails(monkeypatch):
    monkeypatch.setenv("M2_OPENCODE_ROUTE", "on")
    mod, state = _load_router_with_stub(monkeypatch, None)
    r = _client_for(mod).post("/api/m2/ask", json={"question": "q"})
    assert r.json()["answer"] == "direct"
    assert state["direct"] == 1
