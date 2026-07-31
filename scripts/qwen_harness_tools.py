#!/usr/bin/env python3
"""Qwen Token Plan Harness Tools CLI Wrapper.

Provides shell-accessible wrappers for Qwen platform-side tools:
  web_search, code_interpreter, web_extractor, t2i_search, i2i_search

Uses the Qwen Responses API (/compatible-mode/v1/responses) which supports
harness tools via the "tools" parameter with {"type": "<tool_name>"} format.

Usage:
  python scripts/qwen_harness_tools.py web_search "query"
  python scripts/qwen_harness_tools.py code_interpreter "print(2+2)"
  python scripts/qwen_harness_tools.py web_extractor "https://example.com"

Requires: OPENAI_API_KEY env var (Token Plan personal key).
Model: qwen3.8-max-preview (supports all 5 tools).
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

# Harness tools use the Responses API, NOT Chat Completions
API_BASE = "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/responses"
MODEL = "qwen3.8-max-preview"
TIMEOUT = 60  # code_interpreter may need more time

SUPPORTED_TOOLS = {"web_search", "code_interpreter", "web_extractor"}
STUB_TOOLS = {"t2i_search", "i2i_search"}


def call_harness_tool(tool_name: str, user_input: str) -> str:
    """Call Qwen Responses API with a platform harness tool enabled."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return "ERROR: OPENAI_API_KEY environment variable not set."

    payload = {
        "model": MODEL,
        "input": user_input,
        "tools": [{"type": tool_name}],
        "enable_thinking": True,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_BASE,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        return f"ERROR: HTTP {e.code} - {e.reason}\n{err_body}"
    except urllib.error.URLError as e:
        return f"ERROR: Network - {e.reason}"
    except Exception as e:
        return f"ERROR: {type(e).__name__} - {e}"

    # Responses API: extract output_text from output array
    output_items = body.get("output", [])
    text_parts = []
    for item in output_items:
        if item.get("type") == "message":
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    text_parts.append(content.get("text", ""))

    # Fallback: try top-level output_text (SDK convenience field)
    if not text_parts and body.get("output_text"):
        text_parts.append(body["output_text"])

    result = "\n".join(text_parts) if text_parts else ""

    if not result:
        return f"ERROR: No text in response.\nRaw: {json.dumps(body, ensure_ascii=False)[:800]}"

    # Append tool usage info if available
    usage = body.get("usage", {})
    x_tools = usage.get("x_tools", {})
    if x_tools:
        tool_info = ", ".join(
            f"{k}: {v.get('count', '?')} calls" for k, v in x_tools.items()
        )
        result += f"\n\n[Tool usage: {tool_info}]"

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Qwen Token Plan Harness Tools CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python scripts/qwen_harness_tools.py web_search "Python 3.12 release date"
  python scripts/qwen_harness_tools.py code_interpreter "print(sum(range(100)))"
  python scripts/qwen_harness_tools.py web_extractor "https://docs.python.org/3/"
""",
    )
    parser.add_argument(
        "tool",
        choices=sorted(SUPPORTED_TOOLS | STUB_TOOLS),
        help="Harness tool to invoke",
    )
    parser.add_argument("input", help="Query/code/URL to pass to the tool")
    args = parser.parse_args()

    if args.tool in STUB_TOOLS:
        print(f"STUB: {args.tool} is not yet implemented (M1/M2 do not need it).")
        print(f"Reserved for future image search capabilities.")
        sys.exit(0)

    result = call_harness_tool(args.tool, args.input)
    print(result)

    # Exit non-zero on error for scripting
    if result.startswith("ERROR:"):
        sys.exit(1)


if __name__ == "__main__":
    main()
