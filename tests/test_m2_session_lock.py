"""Regression: get_history/append_turn self-deadlock (fixed 2026-08-06).

get_history() acquired _sessions_lock then called _get_session(), which
re-acquired the same non-reentrant threading.Lock -> instant deadlock on
the first OpenCode-route ask, freezing the uvicorn worker permanently.
The fix switches _sessions_lock to threading.RLock.

Test strategy: run each public session API in a daemon thread with a hard
join timeout. A deadlock leaves the thread alive -> test fails. Persistence
is monkeypatched off so the test is hermetic (no PG needed).
"""
from __future__ import annotations

import os
import sys
import threading
import uuid

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture()
def mem_only_sessions(monkeypatch):
    from biz import m2_service

    monkeypatch.setattr(m2_service, "_HAS_PERSISTENCE", False, raising=False)
    yield m2_service


def _run_with_deadline(fn, timeout_s: float = 5.0):
    box: dict = {}

    def target():
        try:
            box["result"] = fn()
        except Exception as exc:  # noqa: BLE001 - surfaced via box
            box["error"] = exc

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout_s)
    assert not t.is_alive(), "DEADLOCK: call did not return within %ss" % timeout_s
    assert "error" not in box, box.get("error")
    return box.get("result")


def test_lock_is_reentrant(mem_only_sessions):
    import threading as _th

    assert isinstance(mem_only_sessions._sessions_lock, _th.RLock.__class__) or hasattr(
        mem_only_sessions._sessions_lock, "acquire"
    )
    # Direct proof: nested acquisition must not deadlock
    lock = mem_only_sessions._sessions_lock

    def nested():
        with lock:
            with lock:
                return True

    assert _run_with_deadline(nested) is True


def test_get_history_no_deadlock(mem_only_sessions):
    sid = str(uuid.uuid4())
    assert _run_with_deadline(lambda: mem_only_sessions.get_history(sid)) == []


def test_append_turn_then_get_history_roundtrip(mem_only_sessions):
    sid = str(uuid.uuid4())
    _run_with_deadline(lambda: mem_only_sessions.append_turn(sid, "user", "问题A"))
    _run_with_deadline(lambda: mem_only_sessions.append_turn(sid, "assistant", "回答A"))
    hist = _run_with_deadline(lambda: mem_only_sessions.get_history(sid))
    assert hist == [
        {"role": "user", "content": "问题A"},
        {"role": "assistant", "content": "回答A"},
    ]


def test_clear_session_no_deadlock(mem_only_sessions):
    sid = str(uuid.uuid4())
    _run_with_deadline(lambda: mem_only_sessions.append_turn(sid, "user", "x"))
    _run_with_deadline(lambda: mem_only_sessions.clear_session(sid))
    assert _run_with_deadline(lambda: mem_only_sessions.get_history(sid)) == []
