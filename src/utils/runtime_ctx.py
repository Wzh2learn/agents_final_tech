"""
Lightweight runtime context utilities to replace previous Coze context helpers.
Provides request-scoped identifiers and default headers for outbound requests.
"""
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Context:
    method: str = ""
    headers: Optional[Any] = None
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    logid: str = field(default_factory=lambda: uuid.uuid4().hex)
    space_id: str = ""
    project_id: str = ""
    x_tt_env: str = ""


def new_context(method: str = "", headers: Optional[Any] = None) -> Context:
    """Create a new request context with unique identifiers."""
    ctx = Context(method=method, headers=headers)
    # Prefer propagated IDs from headers when available
    if headers:
        ctx.run_id = headers.get("X-Request-ID", ctx.run_id)
        ctx.logid = headers.get("X-Request-ID", ctx.logid)
        ctx.space_id = headers.get("X-Space-ID", "")
        ctx.project_id = headers.get("X-Project-ID", "")
        ctx.x_tt_env = headers.get("X-TT-Env", "")
    return ctx


def default_headers(ctx: Optional[Context] = None) -> Dict[str, str]:
    """Build default headers for outbound LLM/API calls."""
    if ctx is None:
        return {}
    headers: Dict[str, str] = {}
    if ctx.run_id:
        headers["X-Request-ID"] = ctx.run_id
    if ctx.space_id:
        headers["X-Space-ID"] = ctx.space_id
    if ctx.project_id:
        headers["X-Project-ID"] = ctx.project_id
    if ctx.x_tt_env:
        headers["X-TT-Env"] = ctx.x_tt_env
    return headers


__all__ = ["Context", "new_context", "default_headers"]
