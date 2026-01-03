import argparse
import asyncio
import json
import traceback
import logging
from typing import Any, Dict, AsyncGenerator, Optional
import uvicorn
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

from biz.agent_service import get_agent_service
from biz.rag_service import get_rag_service
from utils.log.write_log import setup_logging, request_context
from utils.log.config import LOG_LEVEL, LOG_FILE
from utils.runtime_ctx import new_context

setup_logging(
    log_file=LOG_FILE,
    max_bytes=100 * 1024 * 1024, # 100MB
    backup_count=5,
    log_level=LOG_LEVEL,
    use_json_format=True,
    console_output=True
)

logger = logging.getLogger(__name__)
from utils.log.err_trace import extract_core_stack

# 超时配置常量
TIMEOUT_SECONDS = 900  # 15分钟

class GraphService:
    def __init__(self):
        self.agent_service = get_agent_service()
        # 用于跟踪正在运行的任务（使用asyncio.Task）
        self.running_tasks: Dict[str, asyncio.Task] = {}
    
    @staticmethod
    def _sse_event(data: Any) -> str:
        return f"event: message\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"

    async def run(self, payload: Dict[str, Any], ctx=None) -> Dict[str, Any]:
        if ctx is None:
            ctx = new_context("run")

        run_id = ctx.run_id
        logger.info(f"Starting run with run_id: {run_id}")

        try:
            message = payload.get("message", "你好")
            if isinstance(message, dict):
                # 兼容原有消息格式
                message = message.get("content", {}).get("query", {}).get("prompt", [{}])[0].get("content", {}).get("text", "你好")
            
            result = await self.agent_service.chat(message, conversation_id=run_id)
            return {"content": result, "run_id": run_id}

        except asyncio.CancelledError:
            logger.info(f"Run {run_id} was cancelled")
            return {"status": "cancelled", "run_id": run_id, "message": "Execution was cancelled"}
        except Exception as e:
            logger.error(f"Error in GraphService.run: {str(e)}\nTraceback:\n{extract_core_stack()}")
            raise
        finally:
            self.running_tasks.pop(run_id, None)

    async def stream_sse(self, payload: Dict[str, Any], ctx=None) -> AsyncGenerator[str, None]:
        if ctx is None:
            ctx = new_context(method="stream_sse")

        run_id = ctx.run_id
        logger.info(f"Starting stream with run_id: {run_id}")

        try:
            message = payload.get("message", "你好")
            async for chunk in self.agent_service.stream_chat(message, conversation_id=run_id):
                yield self._sse_event({"content": chunk, "run_id": run_id})
        finally:
            pass

    def cancel_run(self, run_id: str, ctx: Optional[Any] = None) -> Dict[str, Any]:
        """取消运行"""
        return {"status": "not_implemented", "run_id": run_id}

    async def run_node(self, node_id: str, payload: Dict[str, Any], ctx=None) -> Any:
        """运行单个节点 (通过 AgentService 代理)"""
        message = payload.get("message", "你好")
        result = await self.agent_service.chat(message, conversation_id=f"node_{node_id}")
        return {"content": result, "node_id": node_id}

    def graph_inout_schema(self) -> Any:
        """返回 Schema (静态定义)"""
        return {"input_schema": {"message": "string"}, "output_schema": {"content": "string"}}

service = GraphService()
app = FastAPI()

@app.post("/run")
async def http_run(request: Request) -> Dict[str, Any]:
    ctx = new_context(method="run", headers=request.headers)
    run_id = ctx.run_id
    request_context.set(ctx)
    try:
        payload = await request.json()
        result = await service.run(payload, ctx)
        return result
    except Exception as e:
        logger.error(f"Error in http_run: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stream_run")
async def http_stream_run(request: Request):
    ctx = new_context(method="stream_run", headers=request.headers)
    run_id = ctx.run_id
    request_context.set(ctx)
    try:
        payload = await request.json()
        async def cancellable_stream():
            async for chunk in service.stream_sse(payload, ctx):
                yield chunk
        return StreamingResponse(cancellable_stream(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Error in http_stream_run: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cancel/{run_id}")
async def http_cancel(run_id: str, request: Request):
    ctx = new_context(method="cancel", headers=request.headers)
    return service.cancel_run(run_id, ctx)

@app.post("/node_run/{node_id}")
async def http_node_run(node_id: str, request: Request):
    ctx = new_context(method="node_run", headers=request.headers)
    payload = await request.json()
    return await service.run_node(node_id, payload, ctx)

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Service is running"}

@app.get("/graph_parameter")
async def http_graph_inout_parameter(request: Request):
    return service.graph_inout_schema()

def parse_args():
    parser = argparse.ArgumentParser(description="Start FastAPI server")
    parser.add_argument("-m", type=str, default="http", help="Run mode, support http")
    parser.add_argument("-p", type=int, default=5000, help="HTTP server port")
    return parser.parse_args()

def start_http_server(port):
    logger.info(f"Start HTTP Server, Port: {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False, workers=1)

if __name__ == "__main__":
    args = parse_args()
    if args.m == "http":
        start_http_server(args.p)
