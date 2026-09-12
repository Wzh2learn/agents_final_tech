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
import re
from typing import Any, Optional

import httpx

logger = logging.getLogger("m1.opencode_adapter")

SIDECAR_URL = os.environ.get("OPENCODE_SERVE_URL", "http://127.0.0.1:4096")
ASK_TIMEOUT = float(os.environ.get("OPENCODE_ASK_TIMEOUT", "90"))
MAX_SESSIONS = int(os.environ.get("OPENCODE_MAX_SESSIONS", "50"))
M2_AGENT = os.environ.get("OPENCODE_M2_AGENT", "m2-qa")
# [C1 2026-09-13 决策 43] best-effort run 级中止的等待上限。fire-and-forget: 到点即弃,
# 绝不让回落路径多等。默认 2.0s => 用户可见延迟增量上界 = 2s(见 ask_via_opencode 的 finally)。
ABORT_TIMEOUT = float(os.environ.get("OPENCODE_ABORT_TIMEOUT", "2.0"))

_FORMAT_HINT = (
    "\n\n输出格式（机器解析, 必须遵守）: 只输出一个 JSON 对象, 不要其他文字、"
    "markdown 代码块或列表: "
    '{"answer": "自然语言回答, 注明出处文档/表/字段", '
    '"sources": [{"sample_id": "...", "table_name": "...", "field": "..."}]}'
    " sources 必须与 answer 中的每个结论一一对应；凡从检索命中回答, "
    "sources 必须非空, 不得返回 []。\n/no_think"
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


# [C1 终结孤儿续跑 2026-09-13 决策 43] ----------------------------------------------
# 为什么需要 abort(不变量, 改动本文件前必读):
#   08-22 的 FK 修复(菜单 a)让超时/异常时**故意不删 session**, 于是每次回落都留下一个继续在
#   :8006 上生成的孤儿 run。实测孤儿续跑 p95 = 133s、max = 69min(L2 §8), 而适配层 45s 就已
#   放弃它 => 产出全部被丢弃, 却持续占着引擎。后果被量化为一条自增强环:
#     :8006 有 47.4% 的时间 >=2 并发(Running 直方图 {1:649, 2:428, 3:208, 4:18, 0:76}),
#     按 Running 均摊的单请求解码速率随并发塌陷 7.40 -> 3.75 -> 1.93 tok/s(Running=3 时单步
#     decode 就要 ~23s), KV 使用率 p95 达 100% => 下一次请求更容易撞 45s 天花板, 于是产生
#     更多孤儿。**45s 预算制造了让它自己失效的负载。**
#   浪费量级 = 每日 172 个 ask 中 ~91% 回落 => ~2.0-5.8 GPU·h/日, 且与承载全部论文数字的
#   :8004 同一块 GPU。abort 是唯一能拆掉这个环、又不改 SLO/阈值/判据的杠杆(方案 C 的 C1)。
#
# abort != delete(硬约束):
#   * 本函数**只**中止在途 run, 绝不删 session。delete_session 的触发条件保持不变
#     (= 仅 completed 为真才删), 因为删父 session 会撞在途 part/message 的 FK 约束并丢
#     transcript -- 那正是 08-22 修掉的病灶, 不得用 delete 代替 abort。
#   * best-effort / fire-and-forget: 任何异常(含路由不存在 404/405、连接失败、超时)一律
#     swallow + logger.info, 绝不抛给调用方, 绝不影响回落路径。失败也必须出声(不得静默到
#     连日志都没有), 否则"abort 未生效"与"abort 已生效"在日志上不可区分。
#   * 路由存在性证据 = opencode 二进制路由表含 /session/{id}/abort(两处), **仅存在性证据,
#     未验证行为语义**; 按零主动端点红线**不得主动探测**, 只允许生产路径在真实超时时自然
#     触发。若自然触发后日志显示 404/405 => 停下报用户, 不得改用 delete_session。
def abort_session_run(session_id: str, timeout: float = ABORT_TIMEOUT) -> bool:
    """Best-effort abort of an in-flight sidecar run. Never raises."""
    try:
        r = httpx.post(f"{SIDECAR_URL}/session/{session_id}/abort", timeout=timeout, trust_env=False)
        logger.info(
            "opencode abort session %s -> HTTP %s (C1 orphan-run termination)",
            session_id,
            r.status_code,
        )
        return r.status_code < 300
    except Exception as exc:
        logger.info(
            "opencode abort session %s failed (%s); fallback path unaffected (C1 best-effort)",
            session_id,
            exc,
        )
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


_SAMPLE_RE = re.compile(
    r"(?:样本[:：]\s*|sample_id[:：]\s*|样本=\s*)"
    r"(?P<sample>sample_[A-Za-z0-9_\u4e00-\u9fa5.\-]+)",
    re.IGNORECASE,
)


def _extract_cited_sources(text: str) -> list[dict[str, Any]]:
    """Conservative fallback: parse explicit 样本/表/字段 citations already
    present in the answer text. Never invents sources not stated in the text.
    """
    sources: list[dict[str, Any]] = []
    segments = re.split(r"(?=[\u4e00-\u9fa5]*样本[:：]|sample_id[:：]|\b样本=\b)", text)
    for seg in segments:
        m = _SAMPLE_RE.search(seg)
        if not m:
            continue
        table = None
        tm = re.search(r"(?:表[:：]\s*|table_name[:：]\s*|表=\s*)([A-Za-z0-9_\u4e00-\u9fa5.\-]+)", seg)
        if tm:
            table = tm.group(1)
        field = None
        fm = re.search(r"(?:字段[:：]\s*|field[:：]\s*|字段=\s*)([A-Za-z0-9_\u4e00-\u9fa5.\-]+)", seg)
        if fm:
            field = fm.group(1)
        entry: dict[str, Any] = {"sample_id": m.group("sample").rstrip(".")}
        if table or field:
            entry["source_text"] = seg.strip()
        if table:
            entry["table_name"] = table
        if field:
            entry["field"] = field
        if entry not in sources:
            sources.append(entry)
    return sources


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
    answer = text.strip()
    return answer, _extract_cited_sources(answer)


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
    completed = False  # [FK 修复·菜单 a 2026-08-23] 仅确认完成的 run 才删 session
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
        info = payload.get("info", {}) if isinstance(payload, dict) else {}
        # Compaction guard: a session-compaction summary is not an answer.
        # Fall back to direct RAG instead of surfacing the raw info blob.
        if str(info.get("agent", "")) == "compaction" or str(info.get("mode", "")) == "compaction":
            logger.warning("opencode final message is a compaction summary; fallback")
            return None
        answer, sources = _parse_structured(_extract_text(payload))
        completed = True
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
            if completed:
                delete_session(session_id)
            else:
                # [C1 2026-09-13 决策 43] 先 best-effort 中止在途 run, 再按 FK 修复保留 session。
                # 顺序不可颠倒: abort 需要 session 仍在, 而"保留 session"是本分支的既有行为。
                abort_session_run(session_id)
                # [FK 修复·菜单 a 2026-08-23] 超时/异常不删: 侧车 run 可能在途,
                # 删父 session 致在途 part/message FK 失败 + transcript 丢失;
                # 留给侧车跑完, 水位闸门 cleanup_sessions() 兜底。
                # [C1 更新] "留给侧车跑完"现已先经一次 abort 尝试; 若 abort 不可用(路由缺失/
                # 异常/超时), 行为与 08-22 完全一致(仍保留 session、仍靠水位闸门兜底)
                # => 本改动对该分支是纯追加, 未改 delete_session 的任何触发条件。
                logger.info("opencode session %s kept (run may be in flight); FK-fix menu a", session_id)
            try:
                if len(list_sessions()) > MAX_SESSIONS:
                    cleanup_sessions()
            except Exception:
                pass
