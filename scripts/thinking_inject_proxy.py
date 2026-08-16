#!/usr/bin/env python3
"""Thinking 注入代理 (模型升级专项 S4, 2026-08-16)。

vLLM 0.27 (vllm-gb10) reasoning-parser 行为实证: 请求未显式携带
chat_template_kwargs.enable_thinking 时, 即使服务端模板已把 thinking 关掉
(渲染结果逐字节一致), 裸输出仍被整体归入 reasoning 字段 (content=null)。
显式传 enable_thinking (true/false 均可) 则正常。

本代理在 opencode sidecar 与 :8006 之间, 对未显式携带 enable_thinking 的
/v1/chat/completions 请求注入 {"enable_thinking": false} (思考默认关,
与改造模板 qwen38_think_off_default.jinja 的服务器默认一致); 显式值原样透传
(judge 的 false / 未来 thinking-on 实验不受影响)。其余路径原样转发, 支持 SSE 流式。

用法: venv/bin/python scripts/thinking_inject_proxy.py [--port 8008]
      [--upstream http://127.0.0.1:8006]
"""
import argparse
import json
import os

# tmux/交互 shell 环境的 socks 代理变量会污染 httpx (SOP §2 同款陷阱)
for _v in ("all_proxy", "ALL_PROXY", "http_proxy", "HTTP_PROXY",
           "https_proxy", "HTTPS_PROXY"):
    os.environ.pop(_v, None)

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

app = FastAPI(title="thinking-inject-proxy")
UPSTREAM = "http://127.0.0.1:8006"
client = httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=10.0), trust_env=False)


@app.get("/proxy-health")
async def proxy_health():
    return {"proxy": "thinking-inject", "upstream": UPSTREAM}


@app.api_route("/{path:path}",
               methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy(path: str, request: Request):
    body = await request.body()
    if path.endswith("chat/completions") and request.method == "POST" and body:
        try:
            payload = json.loads(body)
            ctk = payload.get("chat_template_kwargs")
            if not isinstance(ctk, dict) or "enable_thinking" not in ctk:
                payload["chat_template_kwargs"] = {**(ctk or {}),
                                                   "enable_thinking": False}
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        except (ValueError, TypeError):
            pass
    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in ("host", "content-length")}
    req = client.build_request(request.method, f"{UPSTREAM}/{path}",
                               content=body, headers=headers)
    resp = await client.send(req, stream=True)
    resp_headers = {k: v for k, v in resp.headers.items()
                    if k.lower() not in ("content-length",
                                         "transfer-encoding", "connection")}
    return StreamingResponse(resp.aiter_raw(), status_code=resp.status_code,
                             headers=resp_headers,
                             background=BackgroundTask(resp.aclose))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=8008)
    ap.add_argument("--upstream", default=UPSTREAM)
    args = ap.parse_args()
    UPSTREAM = args.upstream
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
