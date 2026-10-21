from __future__ import annotations

import importlib.util
import io
import json
import urllib.error
from pathlib import Path
from types import SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "deepseek_search_tools.py"
SPEC = importlib.util.spec_from_file_location("deepseek_search_tools", MODULE_PATH)
assert SPEC and SPEC.loader
tools = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tools)


CONFIG = {
    "api_key_env": "DEEPSEEK_API_KEY",
    "api_base": "https://api.deepseek.com",
    "search_path": "/v1/tools/search",
    "fetch_path": "/v1/tools/fetch",
    "timeout_seconds": 60,
}


class Response:
    def __init__(self, body: dict) -> None:
        self.body = json.dumps(body).encode("utf-8")

    def __enter__(self) -> "Response":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


def test_search_request_matches_public_contract() -> None:
    captured = {}

    def opener(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return Response({"results": []})

    payload = tools.build_search_payload(
        "DeepSeek Search API", 5, "What is the endpoint?", "127.0.0.1", True
    )
    result = tools.call_tools(
        CONFIG["search_path"], payload, CONFIG, "test-key", opener=opener
    )

    assert result == {"results": []}
    request = captured["request"]
    assert request.full_url == "https://api.deepseek.com/v1/tools/search"
    assert request.get_header("Authorization") == "Bearer test-key"
    assert request.get_header("Content-type") == "application/json"
    assert json.loads(request.data.decode("utf-8")) == payload
    assert captured["timeout"] == 60


def test_fetch_request_contains_only_url() -> None:
    captured = {}

    def opener(request, timeout):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return Response({"title": "Docs", "content": "# Docs"})

    payload = tools.build_fetch_payload("https://api-docs.deepseek.com/guides/search")
    result = tools.call_tools(
        CONFIG["fetch_path"], payload, CONFIG, "test-key", opener=opener
    )

    assert result == {"title": "Docs", "content": "# Docs"}
    assert captured["body"] == {
        "url": "https://api-docs.deepseek.com/guides/search"
    }


@pytest.mark.parametrize(
    "query",
    ["", "   ", "x" * 129],
)
def test_search_query_boundaries_are_fail_closed(query: str) -> None:
    with pytest.raises(tools.RequestValidationError):
        tools.build_search_payload(query, 10, None, "", False)


@pytest.mark.parametrize("count", [0, 51, True, 1.5])
def test_search_count_boundaries_are_fail_closed(count) -> None:
    with pytest.raises(tools.RequestValidationError):
        tools.build_search_payload("query", count, None, "", False)


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com/file",
        "/relative/path",
        "https://user:pass@example.com/page",
        "https://example.com/" + "a" * 8200,
    ],
)
def test_fetch_url_validation_is_fail_closed(url: str) -> None:
    with pytest.raises(tools.RequestValidationError):
        tools.build_fetch_payload(url)


def test_http_error_preserves_provider_error_contract_without_key() -> None:
    body = json.dumps(
        {
            "error": {
                "message": "invalid request",
                "type": "invalid_request_error",
                "param": None,
                "code": "invalid_request_error",
            }
        }
    ).encode("utf-8")

    def opener(request, timeout):
        raise urllib.error.HTTPError(
            request.full_url, 400, "Bad Request", {}, io.BytesIO(body)
        )

    with pytest.raises(RuntimeError) as exc:
        tools.call_tools(
            CONFIG["search_path"],
            {"query": "x", "count": 1},
            CONFIG,
            "very-secret-test-key",
            opener=opener,
        )

    parsed = json.loads(str(exc.value))
    assert parsed["error"]["code"] == "invalid_request_error"
    assert "very-secret-test-key" not in str(exc.value)


def test_non_json_response_is_rejected() -> None:
    class TextResponse(Response):
        def read(self) -> bytes:
            return b"not json"

    def opener(request, timeout):
        return TextResponse({})

    with pytest.raises(RuntimeError, match="non-JSON"):
        tools.call_tools(
            CONFIG["search_path"],
            {"query": "x", "count": 1},
            CONFIG,
            "test-key",
            opener=opener,
        )


def test_console_json_escapes_non_ascii(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        tools,
        "parse_args",
        lambda: SimpleNamespace(
            config=Path("unused.json"),
            command="search",
            query="query",
            count=1,
            ori_question=None,
            localization="",
            need_content=False,
        ),
    )
    monkeypatch.setattr(tools, "load_config", lambda path: CONFIG)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr(
        tools,
        "call_tools",
        lambda *args, **kwargs: {"results": [{"title": "\U0001d4a5"}]},
    )

    assert tools.main() == 0
    output = capsys.readouterr().out
    assert "\\ud835\\udca5" in output
