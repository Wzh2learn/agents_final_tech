#!/usr/bin/env python3
"""Clean responses2chat proxy v2 - strips Responses-API-only fields."""
import json, os, sys, time, uuid, urllib.request, urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8100
UPSTREAM = "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"

def get_api_key():
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        for line in open(os.path.expanduser("~/.bashrc")):
            if "OPENAI_API_KEY" in line and '"' in line:
                key = line.split('"')[1]; break
    return key

API_KEY = get_api_key()

# Fields that chat/completions accepts
CHAT_ALLOWED = {"model", "messages", "stream", "temperature", "top_p", "max_tokens",
                "tools", "tool_choice", "parallel_tool_calls", "stop", "presence_penalty",
                "frequency_penalty", "seed", "response_format", "n", "logprobs", "top_logprobs"}

def responses_to_chat(body):
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
                    parts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") in ("input_text", "text")]
                    content = "\n".join(parts) if parts else str(content)
                messages.append({"role": role, "content": content})
    chat = {"model": body.get("model", "glm-5.2"), "messages": messages, "stream": body.get("stream", False)}
    # Only pass through allowed fields
    for k in CHAT_ALLOWED:
        if k in body and k not in chat:
            chat[k] = body[k]
    return chat

def chat_to_responses(resp, model):
    choices = resp.get("choices", [])
    text = choices[0].get("message", {}).get("content", "") if choices else ""
    # Handle tool calls
    tool_calls = choices[0].get("message", {}).get("tool_calls", []) if choices else []
    output = []
    if tool_calls:
        for tc in tool_calls:
            output.append({
                "type": "function_call",
                "id": f"fc_{uuid.uuid4().hex[:24]}",
                "call_id": tc.get("id", f"call_{uuid.uuid4().hex[:12]}"),
                "name": tc.get("function", {}).get("name", ""),
                "arguments": tc.get("function", {}).get("arguments", "{}"),
                "status": "completed",
            })
    output.append({
        "type": "message",
        "id": f"msg_{uuid.uuid4().hex[:24]}",
        "status": "completed",
        "role": "assistant",
        "content": [{"type": "output_text", "text": text}],
    })
    usage = resp.get("usage", {})
    return {
        "id": f"resp_{uuid.uuid4().hex[:24]}",
        "object": "response",
        "created_at": int(time.time()),
        "model": model,
        "output": output,
        "usage": {"input_tokens": usage.get("prompt_tokens", 0), "output_tokens": usage.get("completion_tokens", 0), "total_tokens": usage.get("total_tokens", 0)},
        "status": "completed",
    }

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write(f"[proxy] {args[0]}\n")

    def do_GET(self):
        if "/models" in self.path:
            self.send_json(200, {"object": "list", "data": [
                {"id": "glm-5.2", "object": "model", "owned_by": "token-plan"},
                {"id": "deepseek-v4-pro", "object": "model", "owned_by": "token-plan"},
                {"id": "qwen3.8-max-preview", "object": "model", "owned_by": "token-plan"},
                {"id": "qwen3.7-max", "object": "model", "owned_by": "token-plan"},
            ]})
        else:
            self.send_error(404)

    def do_POST(self):
        cl = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(cl)) if cl else {}
        if "/responses" not in self.path:
            self.send_error(404); return
        model = body.get("model", "glm-5.2")
        is_stream = body.get("stream", False)
        chat = responses_to_chat(body)
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        if is_stream:
            chat["stream"] = False  # Always non-stream upstream, emit SSE ourselves
            try:
                req = urllib.request.Request(f"{UPSTREAM}/chat/completions", data=json.dumps(chat).encode(), headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=300) as resp:
                    cr = json.loads(resp.read().decode())
                rr = chat_to_responses(cr, model)
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                rid = rr["id"]
                for evt, data in [
                    ("response.created", {"type": "response.created", "response": {"id": rid, "object": "response", "status": "in_progress", "model": model, "output": []}}),
                    ("response.output_item.added", {"type": "response.output_item.added", "output_index": 0, "item": {"type": "message", "id": rr["output"][-1]["id"], "status": "in_progress", "role": "assistant", "content": []}}),
                    ("response.content_part.added", {"type": "response.content_part.added", "output_index": 0, "content_index": 0, "part": {"type": "output_text", "text": ""}}),
                ]:
                    self.wfile.write(f"event: {evt}\ndata: {json.dumps(data)}\n\n".encode())
                text = rr["output"][-1]["content"][0]["text"] if rr["output"][-1]["content"] else ""
                self.wfile.write(f"event: response.output_text.delta\ndata: {json.dumps({'type': 'response.output_text.delta', 'output_index': 0, 'content_index': 0, 'delta': text})}\n\n".encode())
                self.wfile.write(f"event: response.output_text.done\ndata: {json.dumps({'type': 'response.output_text.done', 'output_index': 0, 'content_index': 0, 'text': text})}\n\n".encode())
                self.wfile.write(f"event: response.completed\ndata: {json.dumps({'type': 'response.completed', 'response': rr})}\n\n".encode())
                self.wfile.flush()
            except urllib.error.HTTPError as e:
                err = e.read().decode() if e.fp else str(e)
                self.send_json(e.code, {"error": {"message": err, "type": "upstream_error"}})
            except Exception as e:
                self.send_json(502, {"error": {"message": str(e), "type": "proxy_error"}})
        else:
            try:
                req = urllib.request.Request(f"{UPSTREAM}/chat/completions", data=json.dumps(chat).encode(), headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=300) as resp:
                    cr = json.loads(resp.read().decode())
                self.send_json(200, chat_to_responses(cr, model))
            except urllib.error.HTTPError as e:
                err = e.read().decode() if e.fp else str(e)
                self.send_json(e.code, {"error": {"message": err, "type": "upstream_error"}})
            except Exception as e:
                self.send_json(502, {"error": {"message": str(e), "type": "proxy_error"}})

    def send_json(self, code, data):
        b = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

if __name__ == "__main__":
    print(f"[proxy-v2] Listening on :{PORT}, upstream: {UPSTREAM}")
    print(f"[proxy-v2] API Key: {API_KEY[:12]}...")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()