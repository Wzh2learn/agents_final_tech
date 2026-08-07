"""Unit tests for responses2chat proxy (2026-08-08).

Covers:
- P1: chat_to_responses must not map a custom function tool named "shell" to
      local_shell_call unless it was declared as a local_shell tool.
- P2: PROXY_DEBUG log uses a secure 0600 temp file (no symlink following) and
      caps per-entry + cumulative size.

纯函数测试，不启动 :8100 进程（由 Loop D 择机重启）。
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import responses2chat_proxy as proxy  # noqa: E402


# ---------------------------------------------------------------------------
# P1: shell_names trust boundary
# ---------------------------------------------------------------------------

def _upstream_response(name: str) -> dict:
    return {
        "choices": [{
            "message": {
                "content": "",
                "tool_calls": [{
                    "id": "call_1",
                    "function": {"name": name, "arguments": '{"command":["touch","/tmp/pwned"]}'},
                }],
            }
        }],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


def test_chat_to_responses_custom_function_named_shell_is_not_local_shell():
    # A custom function tool legitimately named "shell" must stay a function_call,
    # not be executed on the host as local_shell_call.
    out = proxy.chat_to_responses(_upstream_response("shell"), "glm-5.2", shell_names=set())
    assert len(out["output"]) == 1
    item = out["output"][0]
    assert item["type"] == "function_call"
    assert item["name"] == "shell"


def test_chat_to_responses_declared_local_shell_still_maps():
    # When "shell" is declared as a local_shell tool, it still maps to local_shell_call.
    out = proxy.chat_to_responses(_upstream_response("shell"), "glm-5.2", shell_names={"shell"})
    assert len(out["output"]) == 1
    assert out["output"][0]["type"] == "local_shell_call"


def test_chat_to_responses_custom_function_other_name_is_function_call():
    out = proxy.chat_to_responses(_upstream_response("web_search"), "glm-5.2", shell_names=set())
    assert out["output"][0]["type"] == "function_call"
    assert out["output"][0]["name"] == "web_search"


# ---------------------------------------------------------------------------
# P2: PROXY_DEBUG secure log + truncation
# ---------------------------------------------------------------------------

def test_debug_log_0600_and_no_symlink(tmp_path, monkeypatch):
    monkeypatch.setattr(proxy, "DEBUG", True)
    # Simulate a pre-placed symlink at the target path that must NOT be followed.
    target = tmp_path / "victim.txt"
    target.write_text("precious")
    link = tmp_path / "proxy_debug_99999.log"
    link.symlink_to(target)
    monkeypatch.setattr(proxy, "DEBUG_LOG", str(link))

    proxy._debug("REQ", {"k": "v"})

    # The symlink must not be followed; victim stays untouched.
    assert target.read_text() == "precious"


def test_debug_log_runs_with_tempfile_path(tmp_path, monkeypatch):
    monkeypatch.setattr(proxy, "DEBUG", True)
    monkeypatch.setattr(proxy, "DEBUG_LOG", str(tmp_path / "proxy_debug_x.log"))
    proxy._debug("REQUEST", {"chat": {"messages": [{"content": "x" * 500}]}})
    content = (tmp_path / "proxy_debug_x.log").read_text()
    assert "REQUEST" in content
    assert "x" * 500 not in content  # per-message content capped at 300


def test_debug_log_truncates_big_payload(tmp_path, monkeypatch):
    monkeypatch.setattr(proxy, "DEBUG", True)
    monkeypatch.setattr(proxy, "DEBUG_LOG", str(tmp_path / "proxy_debug_y.log"))
    monkeypatch.setattr(proxy, "_DEBUG_MAX_ENTRY", 100)
    proxy._debug("UPSTREAM_RESPONSE", {"answer": "y" * 5000})
    content = (tmp_path / "proxy_debug_y.log").read_text()
    assert len(content) <= 100 + 200  # entry cap + suffix overhead
    assert "[+" in content and "chars]" in content  # truncation marker present
