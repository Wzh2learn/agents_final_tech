"""
OpenAI/SiliconFlow 网络客户端配置
默认禁用系统代理（trust_env=False），避免本地系统代理干扰 API 调用。
"""

from __future__ import annotations

import os
from typing import Any, Dict

import httpx

from utils.config_loader import get_config

_SYNC_DIRECT_CLIENT: httpx.Client | None = None
_ASYNC_DIRECT_CLIENT: httpx.AsyncClient | None = None


def _to_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


def use_env_proxy(default: bool = False) -> bool:
    """
    是否继承系统代理（trust_env=True）。
    优先级：环境变量 OPENAI_TRUST_ENV > 配置 network.openai_trust_env > 默认值
    """
    env_value = os.getenv("OPENAI_TRUST_ENV")
    if env_value is not None:
        return _to_bool(env_value, default)

    try:
        config_value = get_config().get("network.openai_trust_env", default)
        return _to_bool(config_value, default)
    except Exception:
        return default


def get_chat_openai_network_kwargs() -> Dict[str, Any]:
    """
    返回 ChatOpenAI 可用的网络参数（含同步/异步客户端）。
    """
    if use_env_proxy(default=False):
        return {}

    global _SYNC_DIRECT_CLIENT, _ASYNC_DIRECT_CLIENT
    timeout = httpx.Timeout(60.0, connect=15.0)

    if _SYNC_DIRECT_CLIENT is None:
        _SYNC_DIRECT_CLIENT = httpx.Client(trust_env=False, timeout=timeout)
    if _ASYNC_DIRECT_CLIENT is None:
        _ASYNC_DIRECT_CLIENT = httpx.AsyncClient(trust_env=False, timeout=timeout)

    return {
        "http_client": _SYNC_DIRECT_CLIENT,
        "http_async_client": _ASYNC_DIRECT_CLIENT,
    }


def get_openai_sync_network_kwargs() -> Dict[str, Any]:
    """
    返回 OpenAI（同步客户端）可用的网络参数。
    """
    if use_env_proxy(default=False):
        return {}

    global _SYNC_DIRECT_CLIENT
    timeout = httpx.Timeout(60.0, connect=15.0)
    if _SYNC_DIRECT_CLIENT is None:
        _SYNC_DIRECT_CLIENT = httpx.Client(trust_env=False, timeout=timeout)

    return {"http_client": _SYNC_DIRECT_CLIENT}


def get_thinking_kwargs(thinking_type: Any) -> Dict[str, Any]:
    """
    根据 thinking 配置构造 LLM 参数。
    当 thinking 为 disabled/空 时，返回空字典（非思考模式）。
    """
    text = str(thinking_type or "").strip().lower()
    if text in {"", "disabled", "none", "false", "off", "0"}:
        return {}
    return {"extra_body": {"thinking": {"type": str(thinking_type).strip()}}}
