#!/usr/bin/env python3
"""responses2chat proxy v3 - Responses API <-> Chat Completions bridge.

v3 (2026-08-06):
- Tool-call round-trip for Codex CLI built-in tools: local_shell is exposed to
  the chat model as function "shell" with a command-array schema; upstream
  tool calls are mapped back to local_shell_call items Codex can execute.
- Input items function_call / local_shell_call / *_output are converted to
  assistant tool_calls / role=tool messages (v2 dropped them silently).
- enable_thinking / thinking_budget pass through for Chat-only models.
- PROXY_DEBUG=1 dumps each request + upstream response to /tmp/proxy_debug.log.
- /models also returns a "models" field (codex models-manager compat).
"""
import json, os, sys, time, uuid, urllib.request, urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8100
UPSTREAM = "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
DEBUG = os.environ.get("PROXY_DEBUG", "") == "1"
DEBUG_LOG = "/tmp/proxy_debug.log"

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
                "frequency_penalty", "seed", "response_format", "n", "logprobs", "top_logprobs",
                "enable_thinking", "thinking_budget"}

SHELL_SCHEMA = {
    "type": "object",
    "properties": {
        "command": {
            "type": "array",
            "items": {"type": "string"},
            "description": 'The command to run as argv array, e.g. ["bash","-c","ls -la"]',
        },
    },
    "required": ["command"],
}

def _debug(label, obj):
    if not DEBUG:
        return
    try:
        with open(DEBUG_LOG, "a") as f:
            f.write(f"===== {label} {time.strftime('%H:%M:%S')} =====\n")
            f.write(json.dumps(obj, ensure_ascii=False)[:20000] + "\n")
    except Exception:
        pass

def _item_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [p.get("text", "") for p in content
                 if isinstance(p, dict) and p.get("type") in ("input_text", "text", "output_text")]
        return "\n".join(parts) if parts else ""
    return ""

def _append_tool_call(messages, tc):
    if messages and messages[-1].get("role") == "assistant" and "tool_calls" in messages[-1]:
        messages[-1]["tool_calls"].append(tc)
    else:
        messages.append({"role": "assistant", "content": "", "tool_calls": [tc]})

def responses_to_chat(body):
    messages = []
    instructions = body.get("instructions", "")
    if instructions:
        messages.append({"role": "system", "content": instructions})
    shell_names = set()
    for t in body.get("tools", []) or []:
        if isinstance(t, dict) and t.get("type") == "local_shell":
            shell_names.add(t.get("name", "shell"))
    inp = body.get("input", "")
    if isinstance(inp, str):
        messages.append({"role": "user", "content": inp})
    elif isinstance(inp, list):
        for item in inp:
            if isinstance(item, str):
                messages.append({"role": "user", "content": item})
                continue
            if not isinstance(item, dict):
                continue
            itype = item.get("type", "message")
            if itype == "reasoning":
                continue
            if itype in ("function_call", "local_shell_call"):
                call_id = item.get("call_id") or item.get("id") or f"call_{uuid.uuid4().hex[:12]}"
                if itype == "local_shell_call":
                    action = item.get("action") or {}
                    command = action.get("command") or []
                    if isinstance(command, str):
                        command = ["bash", "-c", command]
                    args = json.dumps({"command": command}, ensure_ascii=False)
                    name = "shell"
                else:
                    name = item.get("name", "")
                    args = item.get("arguments", "{}")
                _append_tool_call(messages, {"id": call_id, "type": "function",
                                             "function": {"name": name, "arguments": args}})
                continue
            if itype in ("function_call_output", "local_shell_call_output"):
                call_id = item.get("call_id", "")
                out = item.get("output", item.get("content", ""))
                if not isinstance(out, str):
                    out = json.dumps(out, ensure_ascii=False)
                messages.append({"role": "tool", "tool_call_id": call_id, "content": out})
                continue
            role = item.get("role", "user")
            if role == "developer":
                role = "system"
            messages.append({"role": role, "content": _item_text(item.get("content", ""))})
    chat = {"model": body.get("model", "glm-5.2"), "messages": messages, "stream": body.get("stream", False)}
    for k in CHAT_ALLOWED:
        if k in body and k not in chat:
            chat[k] = body[k]
    if "tools" in chat:
        converted = []
        for t in chat["tools"]:
            if not isinstance(t, dict):
                continue
            if t.get("type") == "local_shell":
                converted.append({"type": "function", "function": {
                    "name": t.get("name", "shell"),
                    "description": "Run a shell command on the host.",
                    "parameters": SHELL_SCHEMA}})
            elif "function" in t:
                converted.append(t)
            elif "name" in t:
                converted.append({"type": "function", "function": {
                    "name": t.get("name", ""),
                    "description": t.get("description", ""),
                    "parameters": t.get("parameters", {"type": "object", "properties": {}})}})
            else:
                sys.stderr.write(f"[proxy] WARNING: unknown tool format: {list(t.keys())}\n")
                continue
        chat["tools"] = converted
    return chat, shell_names

def chat_to_responses(resp, model, shell_names):
    choices = resp.get("choices", [])
    msg = choices[0].get("message", {}) if choices else {}
    text = msg.get("content") or ""
    tool_calls = msg.get("tool_calls") or []
    output = []
    for tc in tool_calls:
        fn = tc.get("function", {})
        name = fn.get("name", "")
        args_raw = fn.get("arguments", "{}")
        if name in shell_names or name == "shell":
            try:
                args = json.loads(args_raw)
            except Exception:
                args = {}
            command = args.get("command")
            if not command and isinstance(args.get("string"), str):
                command = ["bash", "-c", args["string"]]
            if isinstance(command, str):
                command = ["bash", "-c", command]
            if not command:
                command = ["bash", "-c", args_raw]
            output.append({"type": "local_shell_call",
                           "id": f"fc_{uuid.uuid4().hex[:24]}",
                           "call_id": tc.get("id", f"call_{uuid.uuid4().hex[:12]}"),
                           "status": "completed",
                           "action": {"type": "shell", "command": command}})
        else:
            output.append({"type": "function_call",
                           "id": f"fc_{uuid.uuid4().hex[:24]}",
                           "call_id": tc.get("id", f"call_{uuid.uuid4().hex[:12]}"),
                           "name": name, "arguments": args_raw, "status": "completed"})
    if text or not output:
        output.append({"type": "message", "id": f"msg_{uuid.uuid4().hex[:24]}",
                       "status": "completed", "role": "assistant",
                       "content": [{"type": "output_text", "text": text}]})
    usage = resp.get("usage", {})
    return {
        "id": f"resp_{uuid.uuid4().hex[:24]}",
        "object": "response",
        "created_at": int(time.time()),
        "model": model,
        "output": output,
        "usage": {"input_tokens": usage.get("prompt_tokens", 0),
                  "output_tokens": usage.get("completion_tokens", 0),
                  "total_tokens": usage.get("total_tokens", 0)},
        "status": "completed",
    }

def _sse(write, event, data):
    write(f"event: {event}\ndata: {json.dumps(data)}\n\n".encode())

MODEL_LIST = [
    {"id": "glm-5.2", "object": "model", "owned_by": "token-plan"},
    {"id": "deepseek-v4-pro", "object": "model", "owned_by": "token-plan"},
    {"id": "deepseek-v4-flash-0731", "object": "model", "owned_by": "token-plan"},
    {"id": "qwen3.8-max-preview", "object": "model", "owned_by": "token-plan"},
    {"id": "qwen3.7-max", "object": "model", "owned_by": "token-plan"},
]

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write(f"[proxy] {args[0]}\n")

    def do_GET(self):
        if "/health" in self.path:
            self.send_json(200, {"status": "ok", "port": PORT, "upstream": UPSTREAM, "version": "v3"})
            return
        if "/models" in self.path:
            self.send_json(200, {"object": "list", "data": MODEL_LIST, "models": MODEL_LIST})
        else:
            self.send_error(404)

    def do_POST(self):
        cl = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(cl)) if cl else {}
        if "/responses" not in self.path:
            self.send_error(404); return
        model = body.get("model", "glm-5.2")
        is_stream = body.get("stream", False)
        chat, shell_names = responses_to_chat(body)
        _debug("REQUEST", {"model": model, "stream": is_stream, "chat": chat})
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        try:
            req = urllib.request.Request(f"{UPSTREAM}/chat/completions",
                                         data=json.dumps(chat).encode(), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=300) as resp:
                cr = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            err = e.read().decode() if e.fp else str(e)
            _debug("UPSTREAM_ERROR", {"code": e.code, "err": err[:2000]})
            self.send_json(e.code, {"error": {"message": err, "type": "upstream_error"}})
            return
        except Exception as e:
            _debug("PROXY_ERROR", {"err": str(e)})
            self.send_json(502, {"error": {"message": str(e), "type": "proxy_error"}})
            return
        _debug("UPSTREAM_RESPONSE", cr)
        rr = chat_to_responses(cr, model, shell_names)
        if not is_stream:
            self.send_json(200, rr)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        rid = rr["id"]
        _sse(self.wfile.write, "response.created",
             {"type": "response.created", "response": {"id": rid, "object": "response",
              "status": "in_progress", "model": model, "output": []}})
        for idx, item in enumerate(rr["output"]):
            inprog = dict(item)
            inprog["status"] = "in_progress"
            _sse(self.wfile.write, "response.output_item.added",
                 {"type": "response.output_item.added", "output_index": idx, "item": inprog})
            if item.get("type") == "message":
                text = item["content"][0]["text"] if item.get("content") else ""
                _sse(self.wfile.write, "response.content_part.added",
                     {"type": "response.content_part.added", "output_index": idx,
                      "content_index": 0, "part": {"type": "output_text", "text": ""}})
                _sse(self.wfile.write, "response.output_text.delta",
                     {"type": "response.output_text.delta", "output_index": idx,
                      "content_index": 0, "delta": text})
                _sse(self.wfile.write, "response.output_text.done",
                     {"type": "response.output_text.done", "output_index": idx,
                      "content_index": 0, "text": text})
                _sse(self.wfile.write, "response.content_part.done",
                     {"type": "response.content_part.done", "output_index": idx,
                      "content_index": 0, "part": {"type": "output_text", "text": text}})
            _sse(self.wfile.write, "response.output_item.done",
                 {"type": "response.output_item.done", "output_index": idx, "item": item})
        _sse(self.wfile.write, "response.completed",
             {"type": "response.completed", "response": rr})
        self.wfile.flush()

    def send_json(self, code, data):
        b = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

if __name__ == "__main__":
    print(f"[proxy-v3] Listening on :{PORT}, upstream: {UPSTREAM}, debug={DEBUG}")
    print(f"[proxy-v3] API Key: {API_KEY[:12]}...")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()