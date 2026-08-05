"""OpenCode sidecar adapter (Route A, see docs/25).

:5050 remains the single entrypoint. When M2_OPENCODE_ROUTE=on, /api/m2/ask
delegates generation to the m2-qa agent running in the ``opencode serve``
sidecar; any failure (sidecar down, timeout, malformed payload) returns None
so the caller transparently falls back to the in-process RAG pipeline and the
demo surface never breaks.

Session lifecycle: one throwaway sidecar session per ask (create -> use ->
delete). Orphans are capped at OPENCODE_MAX_SESSIONS and can be purged via
POST /api/m2/opencode/cleanup or scripts/opencode_session_cleanup.py.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

import httpx

logger = logging.getLogger("m1.opencode_adapter")

SIDECAR_URL = os.environ.get("OPENCODE_SERVE_URL", "http://127.0.0.1:4096")
ASK_TIMEOUT = float(os.environ.get("OPENCODE_ASK_TIMEOUT", "90"))
MAX_SESSIONS = int(os.environ.get("OPENCODE_MAX_SESSIONS", "50"))
M2_AGENT = os.environ.get("OPENCODE_M2_AGENT", "m2-qa")

_FORMAT_HINT = (
    "\n\n输出格式（机器解析, 必须遵守）: 只输出一个 JSON 对象, 不要其他文字: "
    '{"answer": "自然语言回答, 注明出处文档/表/字段", '
    '"sources": [{"sample_id": "...", "table_name": "...", "field": "..."}]}'
)


def route_enabled() -> bool:
    """A2 grey switch, default off."""
    return os.environ.get("M2_OPENCODE_ROUTE", "off").strip().lower() == "on"


def sidecar_health(timeout: float = 3.0) -> bool:
    try:
        return httpx.get(f"{SIDECAR_URL}/session", timeout=timeout, trust_env=False).status_code == 200
    except Exception:
        return False


def list_sessions() -> list[dict[str, Any]]:
    r = httpx.get(f"{SIDECAR_URL}/session", timeout=10, trust_env=False)
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, list) else []


def delete_session(session_id: str) -> bool:
    try:
        return httpx.delete(f"{SIDECAR_URL}/session/{session_id}", timeout=10, trust_env=False).status_code < 300
    except Exception:
        return False


def _updated_key(session: dict[str, Any]) -> float:
    t = session.get("time") or {}
    return float(t.get("updated") or t.get("created") or 0)


def cleanup_sessions(max_keep: int = MAX_SESSIONS, purge_all: bool = False) -> dict[str, int]:
    """Delete every session (purge_all) or the oldest ones beyond max_keep."""
    sessions = list_sessions()
    doomed = sessions if purge_all else sorted(sessions, key=_updated_key, reverse=True)[max_keep:]
    deleted = sum(1 for s in doomed if delete_session(str(s.get("id", ""))))
    return {"before": len(sessions), "deleted": deleted, "kept": len(sessions) - len(doomed)}


def _extract_text(payload: Any) -> str:
    if isinstance(payload, dict):
        parts = payload.get("parts")
        if isinstance(parts, list):
            texts = [
                str(p.get("text", ""))
                for p in parts
                if isinstance(p, dict) and p.get("type") == "text"
            ]
            if texts:
                return "\n".join(texts)
    return json.dumps(payload, ensure_ascii=False)[:2000]


def _parse_structured(text: str) -> tuple[str, list[dict[str, Any]]]:
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            obj = json.loads(text[start : end + 1])
            if isinstance(obj, dict) and obj.get("answer"):
                sources = obj.get("sources") or []
                return str(obj["answer"]), [s for s in sources if isinstance(s, dict)]
        except Exception:
            pass
    return text.strip(), []


def _history_block(history: Optional[list[dict[str, str]]]) -> str:
    if not history:
        return ""
    lines = [
        f"{'用户' if m.get('role') == 'user' else '助手'}: {str(m.get('content', ''))[:200]}"
        for m in history[-4:]
    ]
    return "对话历史:\n" + "\n".join(lines) + "\n\n追问: "


def ask_via_opencode(
    question: str,
    history: Optional[list[dict[str, str]]] = None,
    timeout_s: float = ASK_TIMEOUT,
) -> Optional[dict[str, Any]]:
    """One M2 ask through the m2-qa agent; None means caller must fall back."""
    if not sidecar_health():
        logger.warning("opencode sidecar unhealthy at %s; fallback", SIDECAR_URL)
        return None
    session_id: Optional[str] = None
    try:
        session_id = httpx.post(f"{SIDECAR_URL}/session", json={}, timeout=10, trust_env=False).json()["id"]
        body: dict[str, Any] = {
            "parts": [{"type": "text", "text": _history_block(history) + question + _FORMAT_HINT}],
            "agent": M2_AGENT,
        }
        r = httpx.post(f"{SIDECAR_URL}/session/{session_id}/message", json=body, timeout=timeout_s, trust_env=False)
        if r.status_code == 400:  # older serve builds may reject the agent field
            body.pop("agent", None)
            r = httpx.post(f"{SIDECAR_URL}/session/{session_id}/message", json=body, timeout=timeout_s, trust_env=False)
        r.raise_for_status()
        payload = r.json()
        answer, sources = _parse_structured(_extract_text(payload))
        info = payload.get("info", {}) if isinstance(payload, dict) else {}
        return {
            "answer": answer,
            "sources": sources,
            "model": f"opencode:{info.get('modelID', M2_AGENT)}",
            "route": "opencode",
        }
    except Exception as exc:
        logger.warning("opencode ask failed (%s); fallback", exc)
        return None
    finally:
        if session_id:
            delete_session(session_id)
            try:
                if len(list_sessions()) > MAX_SESSIONS:
                    cleanup_sessions()
            except Exception:
                pass
