"""2026-08-23 :5050 代码窗修复测试: FK 菜单 a (超时不删) + vector_store 实例缓存。"""
import importlib
import os
import sys

import pytest

# [Loop C 审计后续] 单文件独立运行的 sys.path 守卫: pytest.ini pythonpath=. (仓库根),
# 全量跑依赖其他测试的 sys.path 副作用; 单跑本文件需自带 src, 否则 biz/tools 不可导入。
_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)


@pytest.fixture()
def adapter():
    mod = importlib.import_module("biz.opencode_adapter")
    return importlib.reload(mod)


class _Resp:
    def __init__(self, payload=None, status=200):
        self._payload = payload or {}
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class _FakeHttpx:
    def __init__(self, message_exc=None, info=None):
        self.message_exc = message_exc
        self.info = info or {}
        self.posts = []

    def post(self, url, json=None, timeout=None, trust_env=False):
        self.posts.append(url)
        if url.endswith("/session"):
            return _Resp({"id": "sess-1"})
        if self.message_exc is not None:
            raise self.message_exc
        return _Resp({"parts": [{"type": "text", "text": "答案: 42"}], "info": self.info})


def test_fk_success_path_deletes(adapter, monkeypatch):
    deleted = []
    monkeypatch.setattr(adapter, "sidecar_health", lambda: True)
    monkeypatch.setattr(adapter, "httpx", _FakeHttpx())
    monkeypatch.setattr(adapter, "delete_session", lambda sid: deleted.append(sid) or True)
    monkeypatch.setattr(adapter, "list_sessions", lambda: [])
    out = adapter.ask_via_opencode("q")
    assert out is not None and out["route"] == "opencode"
    assert deleted == ["sess-1"]


def test_fk_timeout_path_keeps_session(adapter, monkeypatch):
    import httpx as real_httpx
    deleted = []
    monkeypatch.setattr(adapter, "sidecar_health", lambda: True)
    monkeypatch.setattr(adapter, "httpx", _FakeHttpx(message_exc=real_httpx.TimeoutException("boom")))
    monkeypatch.setattr(adapter, "delete_session", lambda sid: deleted.append(sid) or True)
    monkeypatch.setattr(adapter, "list_sessions", lambda: [])
    out = adapter.ask_via_opencode("q")
    assert out is None
    assert deleted == []  # 菜单 a: 超时不删, 留给侧车跑完


def test_fk_compaction_guard_keeps_session(adapter, monkeypatch):
    deleted = []
    monkeypatch.setattr(adapter, "sidecar_health", lambda: True)
    monkeypatch.setattr(adapter, "httpx", _FakeHttpx(info={"agent": "compaction"}))
    monkeypatch.setattr(adapter, "delete_session", lambda sid: deleted.append(sid) or True)
    monkeypatch.setattr(adapter, "list_sessions", lambda: [])
    out = adapter.ask_via_opencode("q")
    assert out is None
    assert deleted == []


def test_fk_watermark_cleanup_still_runs(adapter, monkeypatch):
    import httpx as real_httpx
    deleted = []
    sessions = [{"id": str(i), "time": {"updated": float(i)}} for i in range(adapter.MAX_SESSIONS + 1)]
    monkeypatch.setattr(adapter, "sidecar_health", lambda: True)
    monkeypatch.setattr(adapter, "httpx", _FakeHttpx(message_exc=real_httpx.TimeoutException("boom")))
    monkeypatch.setattr(adapter, "delete_session", lambda sid: deleted.append(sid) or True)
    monkeypatch.setattr(adapter, "list_sessions", lambda: sessions)
    adapter.ask_via_opencode("q")
    assert "sess-1" not in deleted  # 当前在途会话不删
    assert deleted == ["0"]  # [Loop C 审计 F17 补强] 被删的恰为最旧会话 (updated 升序)


def test_vector_store_instance_cache(monkeypatch):
    import tools.vector_store as vs
    created = []

    class FakePGV:
        def __init__(self, **kw):
            created.append(kw)

    monkeypatch.setattr(vs, "_vector_store", FakePGV)
    monkeypatch.setattr(vs, "get_embeddings", lambda *a, **k: object())
    vs._STORE_INSTANCE_CACHE.clear()
    conn = "postgresql+psycopg://u:p@h:1/db"
    a = vs.get_vector_store(collection_name="c1", connection_string=conn)
    b = vs.get_vector_store(collection_name="c1", connection_string=conn)
    assert a is b
    assert len(created) == 1  # engine 只构造一次
    c = vs.get_vector_store(collection_name="c2", connection_string=conn)
    assert c is not a
    assert len(created) == 2
    vs._STORE_INSTANCE_CACHE.clear()
