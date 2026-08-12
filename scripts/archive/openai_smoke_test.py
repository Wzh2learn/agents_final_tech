"""Minimal OpenAI-compatible model smoke test."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test an OpenAI-compatible chat endpoint.")
    parser.add_argument("--base-url", required=True, help="Base URL, e.g. http://127.0.0.1:8002/v1")
    parser.add_argument("--model", default="local-model", help="Model name sent to the endpoint.")
    parser.add_argument(
        "--prompt",
        default='Return only this JSON object: {"status":"ok","count":1}',
        help="User prompt.",
    )
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--disable-thinking", action="store_true")
    return parser.parse_args()


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Authorization": "Bearer local-dev"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    args = parse_args()
    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": args.prompt}],
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
    }
    if args.disable_thinking:
        payload["chat_template_kwargs"] = {"enable_thinking": False}

    started = time.perf_counter()
    try:
        response = post_json(f"{args.base_url.rstrip('/')}/chat/completions", payload)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code}: {body}") from exc

    elapsed = time.perf_counter() - started
    choice = response.get("choices", [{}])[0]
    message = choice.get("message", {})
    usage = response.get("usage", {})

    print(json.dumps({
        "elapsed_sec": round(elapsed, 3),
        "finish_reason": choice.get("finish_reason"),
        "content": message.get("content"),
        "reasoning_content": message.get("reasoning_content"),
        "usage": usage,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
