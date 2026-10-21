#!/usr/bin/env python3
"""CLI for DeepSeek's read-only Search and Fetch JSON APIs."""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "deepseek_search.json"


class RequestValidationError(ValueError):
    """Raised before an API request when CLI input violates the public contract."""


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RequestValidationError(f"cannot load config {path}: {exc}") from exc

    required = {"api_key_env", "api_base", "search_path", "fetch_path", "timeout_seconds"}
    if set(config) != required:
        raise RequestValidationError("config fields must match the DeepSeek tools contract")
    if not isinstance(config["api_key_env"], str) or not config["api_key_env"]:
        raise RequestValidationError("api_key_env must be a non-empty string")
    if not isinstance(config["api_base"], str):
        raise RequestValidationError("api_base must be a string")
    base = urllib.parse.urlsplit(config["api_base"])
    if base.scheme not in {"http", "https"} or not base.netloc:
        raise RequestValidationError("api_base must be an HTTP(S) URL")
    for key in ("search_path", "fetch_path"):
        if not isinstance(config[key], str) or not config[key].startswith("/"):
            raise RequestValidationError(f"{key} must be an absolute API path")
    if isinstance(config["timeout_seconds"], bool) or not isinstance(
        config["timeout_seconds"], int
    ):
        raise RequestValidationError("timeout_seconds must be an integer")
    if not 1 <= config["timeout_seconds"] <= 300:
        raise RequestValidationError("timeout_seconds must be between 1 and 300")
    return config


def validate_query(query: str) -> str:
    if not isinstance(query, str):
        raise RequestValidationError("query must be a string")
    if not query.strip():
        raise RequestValidationError("query must not be empty or whitespace")
    if len(query) > 128:
        raise RequestValidationError("query must be at most 128 Unicode characters")
    return query


def validate_optional_question(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise RequestValidationError("ori_question must be non-empty when provided")
    if len(value) > 128:
        raise RequestValidationError("ori_question must be at most 128 characters")
    return value


def validate_localization(value: str) -> str:
    if not isinstance(value, str):
        raise RequestValidationError("localization must be a string")
    if not value:
        return ""
    try:
        ipaddress.ip_address(value)
    except ValueError as exc:
        raise RequestValidationError("localization must be a valid IPv4 or IPv6 address") from exc
    return value


def validate_count(count: int) -> int:
    if isinstance(count, bool) or not isinstance(count, int):
        raise RequestValidationError("count must be an integer")
    if not 1 <= count <= 50:
        raise RequestValidationError("count must be between 1 and 50")
    return count


def validate_url(url: str) -> str:
    if not isinstance(url, str):
        raise RequestValidationError("url must be a string")
    if len(url) > 8192:
        raise RequestValidationError("url must be at most 8192 characters")
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RequestValidationError("url must be an HTTP(S) URL with a host")
    if parsed.username is not None or parsed.password is not None:
        raise RequestValidationError("url must not contain a username or password")
    return url


def build_search_payload(
    query: str,
    count: int,
    ori_question: str | None,
    localization: str,
    need_content: bool,
) -> dict[str, Any]:
    return {
        "query": validate_query(query),
        "count": validate_count(count),
        "ori_question": validate_optional_question(ori_question),
        "localization": validate_localization(localization),
        "need_content": need_content,
    }


def build_fetch_payload(url: str) -> dict[str, str]:
    return {"url": validate_url(url)}


def call_tools(
    path: str,
    payload: dict[str, Any],
    config: dict[str, Any],
    api_key: str,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, Any]:
    endpoint = urllib.parse.urljoin(config["api_base"], path)
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with opener(request, timeout=config["timeout_seconds"]) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {
                "error": {
                    "message": raw[:500] or exc.reason,
                    "type": "api_error",
                    "param": None,
                    "code": str(exc.code),
                }
            }
        raise RuntimeError(json.dumps(parsed, ensure_ascii=True)) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            json.dumps(
                {
                    "error": {
                        "message": f"network error: {exc.reason}",
                        "type": "network_error",
                        "param": None,
                        "code": "network_error",
                    }
                }
            )
        ) from exc

    try:
        result = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            json.dumps(
                {
                    "error": {
                        "message": "DeepSeek returned non-JSON content",
                        "type": "api_error",
                        "param": None,
                        "code": "invalid_response",
                    }
                }
            )
        ) from exc
    if not isinstance(result, dict):
        raise RuntimeError(
            json.dumps(
                {
                    "error": {
                        "message": "DeepSeek response must be a JSON object",
                        "type": "api_error",
                        "param": None,
                        "code": "invalid_response",
                    }
                }
            )
        )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DeepSeek Search and Fetch tools CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python scripts/deepseek_search_tools.py search "measurement validity evaluation"
  python scripts/deepseek_search_tools.py fetch "https://api-docs.deepseek.com/guides/search"
""",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="JSON config path",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search the web")
    search.add_argument("query")
    search.add_argument("--count", type=int, default=10)
    search.add_argument("--ori-question")
    search.add_argument("--localization", default="")
    search.add_argument("--need-content", action="store_true")

    fetch = subparsers.add_parser("fetch", help="Fetch one page as Markdown")
    fetch.add_argument("url")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.config)
        api_key = os.environ.get(config["api_key_env"], "")
        if not api_key:
            raise RequestValidationError(
                f"{config['api_key_env']} environment variable not set"
            )
        if args.command == "search":
            path = config["search_path"]
            payload = build_search_payload(
                args.query,
                args.count,
                args.ori_question,
                args.localization,
                args.need_content,
            )
        else:
            path = config["fetch_path"]
            payload = build_fetch_payload(args.url)
        result = call_tools(path, payload, config, api_key)
    except RequestValidationError as exc:
        print(
            json.dumps(
                {
                    "error": {
                        "message": str(exc),
                        "type": "invalid_request_error",
                        "param": None,
                        "code": "invalid_request_error",
                    }
                },
                ensure_ascii=True,
            )
        )
        return 2
    except RuntimeError as exc:
        print(str(exc))
        return 1

    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
