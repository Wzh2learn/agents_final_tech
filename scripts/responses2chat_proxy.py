#!/usr/bin/env python3
"""Lightweight Responses API -> Chat Completions proxy for Codex CLI 0.145+.

Runs on the GB10 dev machine. Accepts OpenAI Responses API requests from
Codex CLI, converts them to Chat Completions format, forwards to Token Plan,
and converts the response back. This enables chat-only models (glm-5.2,
deepseek-v4-pro) to work with Codex CLI which only supports wire_api="responses".

Usage:
    python3 responses2chat_proxy.py [--port 8100] [--upstream URL]

Then in ~/.codex/config.toml:
    [model_providers.Token_Plan_Chat]
    base_url = "http://127.0.0.1:8100/v1"
    wire_api = "responses"
"""

import argparse
import json
import os
import sys
import time
import uuid
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

DEFAULT_PORT = 8100
DEFAULT_UPSTREAM = "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"


def get_api_key():
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        bashrc = os.path.expanduser("~/.bashrc")
        if os.path.exists(bashrc):
            for line in open(bashrc):
                if "OPENAI_API_KEY" in line and '"' in line:
                    key = line.split('"')[1]
                    break
    return key


def responses_to_chat(body: dict) -> dict:
    """Convert a Responses API request to Chat Completions format."""
    messages = []

    instructions = body.get("instructions", "")
    if instructions:
        messages.append({"role": "system", "content": instructions})

    inp = body.get("input", "")
    if isinstance(inp, str):
        messages.append({"role": "user", "content": inp})
    elif isinstance(inp, list):
        for item in inp:
            if isinstance(item, str):
                messages.append({"role": "user", "content": item})
            elif isinstance(item, dict):
                role = item.get("role", "user")
                content = item.get("content", "")
                if isinstance(content, list):
                    text_parts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "input_text"]
                    content = "\n".join(text_parts) if text_parts else str(content)
                messages.append({"role": role, "content": content})

    chat_body = {
        "model": body.get("model", "glm-5.2"),
        "messages": messages,
        "stream": body.get("stream", False),
    }

    if "max_output_tokens" in body:
        chat_body["max_tokens"] = body["max_output_tokens"]
    if "temperature" in body:
        chat_body["temperature"] = body["temperature"]
    if "top_p" in body:
        chat_body["top_p"] = body["top_p"]

    return chat_body


def chat_to_responses(chat_resp: dict, model: str) -> dict:
    """Convert a Chat Completions response to Responses API format."""
    choices = chat_resp.get("choices", [])
    text = ""
    if choices:
        msg = choices[0].get("message", {})
        text = msg.get("content", "")

    usage = chat_resp.get("usage", {})
    resp_id = f"resp_{uuid.uuid4().hex[:24]}"

    return {
        "id": resp_id,
        "object": "response",
        "created_at": int(time.time()),
        "model": model,
        "output": [
            {
                "type": "message",
                "id": f"msg_{uuid.uuid4().hex[:24]}",
                "status": "completed",
                "role": "assistant",
                "content": [{"type": "output_text", "text": text}],
            }
        ],
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        },
        "status": "completed",
    }


def stream_chat_to_responses(upstream_url, headers, chat_body, model, wfile):
    """Stream Chat Completions SSE and convert to Responses API SSE."""
    req = urllib.request.Request(
        f"{upstream_url}/chat/completions",
        data=json.dumps(chat_body).encode(),
        headers=headers,
        method="POST",
    )

    resp_id = f"resp_{uuid.uuid4().hex[:24]}"
    msg_id = f"msg_{uuid.uuid4().hex[:24]}"

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            created_event = {
                "type": "response.created",
                "response": {"id": resp_id, "object": "response", "status": "in_progress", "model": model, "output": []},
            }
            wfile.write(f"event: response.created\ndata: {json.dumps(created_event)}\n\n".encode())
            wfile.flush()

            item_event = {
                "type": "response.output_item.added",
                "output_index": 0,
                "item": {"type": "message", "id": msg_id, "status": "in_progress", "role": "assistant", "content": []},
            }
            wfile.write(f"event: response.output_item.added\ndata: {json.dumps(item_event)}\n\n".encode())
            wfile.flush()

            part_event = {
                "type": "response.content_part.added",
                "output_index": 0,
                "content_index": 0,
                "part": {"type": "output_text", "text": ""},
            }
            wfile.write(f"event: response.content_part.added\ndata: {json.dumps(part_event)}\n\n".encode())
            wfile.flush()

            full_text = ""
            for line in resp:
                line = line.decode("utf-8", errors="replace").strip()
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        full_text += content
                        delta_event = {
                            "type": "response.output_text.delta",
                            "output_index": 0,
                            "content_index": 0,
                            "delta": content,
                        }
                        wfile.write(f"event: response.output_text.delta\ndata: {json.dumps(delta_event)}\n\n".encode())
                        wfile.flush()
                except json.JSONDecodeError:
                    continue

            done_event = {"type": "response.output_text.done", "output_index": 0, "content_index": 0, "text": full_text}
            wfile.write(f"event: response.output_text.done\ndata: {json.dumps(done_event)}\n\n".encode())

            completed_event = {
                "type": "response.completed",
                "response": {
                    "id": resp_id, "object": "response", "status": "completed", "model": model,
                    "output": [{"type": "message", "id": msg_id, "status": "completed", "role": "assistant",
                                "content": [{"type": "output_text", "text": full_text}]}],
                },
            }
            wfile.write(f"event: response.completed\ndata: {json.dumps(completed_event)}\n\n".encode())
            wfile.flush()

    except Exception as e:
        error_event = {"type": "error", "error": {"message": str(e), "type": "proxy_error"}}
        wfile.write(f"event: error\ndata: {json.dumps(error_event)}\n\n".encode())
        wfile.flush()


class ProxyHandler(BaseHTTPRequestHandler):
    upstream = DEFAULT_UPSTREAM
    api_key = ""

    def log_message(self, format, *args):
        sys.stderr.write(f"[proxy] {args[0]}\n")

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length)) if content_length else {}

        if "/responses" in self.path:
            self.handle_responses(body)
        elif "/chat/completions" in self.path:
            self.forward_chat(body)
        else:
            self.send_error(404, "Not found")

    def do_GET(self):
        if "/models" in self.path:
            models = {"object": "list", "data": [
                {"id": "glm-5.2", "object": "model", "owned_by": "token-plan"},
                {"id": "deepseek-v4-pro", "object": "model", "owned_by": "token-plan"},
                {"id": "qwen3.8-max-preview", "object": "model", "owned_by": "token-plan"},
                {"id": "qwen3.7-max", "object": "model", "owned_by": "token-plan"},
            ]}
            self.send_json(200, models)
        else:
            self.send_error(404)

    def handle_responses(self, body):
        model = body.get("model", "glm-5.2")
        is_stream = body.get("stream", False)
        chat_body = responses_to_chat(body)
        chat_body["stream"] = is_stream

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if is_stream:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            stream_chat_to_responses(self.upstream, headers, chat_body, model, self.wfile)
        else:
            req = urllib.request.Request(
                f"{self.upstream}/chat/completions",
                data=json.dumps(chat_body).encode(),
                headers=headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=300) as resp:
                    chat_resp = json.loads(resp.read().decode())
                responses_resp = chat_to_responses(chat_resp, model)
                self.send_json(200, responses_resp)
            except urllib.error.HTTPError as e:
                err_body = e.read().decode() if e.fp else str(e)
                self.send_json(e.code, {"error": {"message": err_body, "type": "upstream_error"}})
            except Exception as e:
                self.send_json(502, {"error": {"message": str(e), "type": "proxy_error"}})

    def forward_chat(self, body):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        req = urllib.request.Request(
            f"{self.upstream}/chat/completions",
            data=json.dumps(body).encode(),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                result = json.loads(resp.read().decode())
            self.send_json(200, result)
        except Exception as e:
            self.send_json(502, {"error": {"message": str(e), "type": "proxy_error"}})

    def send_json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser(description="Responses-to-Chat proxy for Codex CLI")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--upstream", default=DEFAULT_UPSTREAM)
    args = parser.parse_args()

    api_key = get_api_key()
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found", file=sys.stderr)
        sys.exit(1)

    ProxyHandler.upstream = args.upstream
    ProxyHandler.api_key = api_key

    server = HTTPServer(("127.0.0.1", args.port), ProxyHandler)
    print(f"[responses2chat] Listening on http://127.0.0.1:{args.port}")
    print(f"[responses2chat] Upstream: {args.upstream}")
    print(f"[responses2chat] API Key: {api_key[:12]}...")
    print(f"[responses2chat] Models: glm-5.2, deepseek-v4-pro (chat-only -> responses)")
    print(f"[responses2chat] Use in config.toml: base_url = \"http://127.0.0.1:{args.port}/v1\"")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[responses2chat] Shutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
