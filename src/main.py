import argparse
import asyncio
import json
import logging
import os
from typing import Any, Dict, AsyncGenerator, Optional
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from web.middleware import BearerAuthMiddleware, RequestLoggingMiddleware

from biz.agent_service import get_agent_service, get_agent_service_sync
from biz.rag_service import get_rag_service, get_rag_service_sync
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
        self._agent_service = None
        # 用于跟踪正在运行的任务（使用asyncio.Task）
        self.running_tasks: Dict[str, asyncio.Task] = {}
    
    async def _get_agent_service(self):
        """延迟加载 AgentService（线程安全）"""
        if self._agent_service is None:
            self._agent_service = await get_agent_service()
        return self._agent_service
    
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
            
            agent_service = await self._get_agent_service()
            result = await agent_service.chat(message, conversation_id=run_id)
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
            agent_service = await self._get_agent_service()
            async for chunk in agent_service.stream_chat(message, conversation_id=run_id):
                yield self._sse_event({"content": chunk, "run_id": run_id})
        finally:
            pass

    def cancel_run(self, run_id: str, ctx: Optional[Any] = None) -> Dict[str, Any]:
        """取消运行"""
        return {"status": "not_implemented", "run_id": run_id}

    async def run_node(self, node_id: str, payload: Dict[str, Any], ctx=None) -> Any:
        """运行单个节点 (通过 AgentService 代理)"""
        message = payload.get("message", "你好")
        agent_service = await self._get_agent_service()
        result = await agent_service.chat(message, conversation_id=f"node_{node_id}")
        return {"content": result, "node_id": node_id}

    def graph_inout_schema(self) -> Any:
        """返回 Schema (静态定义)"""
        return {"input_schema": {"message": "string"}, "output_schema": {"content": "string"}}

service = GraphService()
app = FastAPI(
    title="金融对账单智能解析与问答系统",
    version="2.0.0",
    description="""
## 核心能力

- **M1 解析**: 上传对账单 (PDF/TXT/DOCX)，返回结构化表格 + 勾稽校验
- **M2 问答**: 自然语言查询已解析数据，支持多轮对话 + 答案溯源
- **健康检查**: 全组件状态监控

## 快速测试

```bash
# 解析
curl -X POST /api/m1/parse-file -F "file=@statement.pdf"

# 问答
curl -X POST /api/m2/ask -H "Content-Type: application/json" \
  -d '{"question": "嘉兴民安的总资产是多少？"}'

# 多轮追问
curl -X POST /api/m2/ask -H "Content-Type: application/json" \
  -d '{"question": "其中证券市值呢？", "session_id": "<上轮返回的id>"}'
```
""",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置
# 生产环境应通过环境变量 CORS_ORIGINS 配置允许的源，多个源用逗号分隔
_cors_origins = os.getenv("CORS_ORIGINS", "*")
_allowed_origins = [origin.strip() for origin in _cors_origins.split(",")] if _cors_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# --- Production middleware (auth + request logging) ---
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(BearerAuthMiddleware)

# 静态文件
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    logger.warning(f"Static directory not found: {static_dir}")

# 整合路由
from web.routers import api_router, include_routers
include_routers()
app.include_router(api_router)

# Metrics endpoint (registered directly, not under api_router prefix)
from web.routers.metrics import router as metrics_router
app.include_router(metrics_router)

# WebSocket 服务状态
_ws_started = False


@app.on_event("startup")
async def startup_event():
    """FastAPI 启动时初始化 WebSocket 服务"""
    global _ws_started
    from utils.config_loader import get_config
    from web.collaboration_service import start_websocket_thread

    cfg = get_config()
    if not _ws_started and cfg.get("features", {}).get("realtime_collaboration", False):
        ws_host = cfg.get("websocket.host", "0.0.0.0")
        ws_port = int(cfg.get("websocket.port", 8765))
        started = start_websocket_thread(host=ws_host, port=ws_port)
        _ws_started = started or _ws_started
        if _ws_started:
            logger.info(f"WebSocket server started on {ws_host}:{ws_port}")


@app.post("/run")
async def http_run(request: Request) -> Dict[str, Any]:
    ctx = new_context(method="run", headers=request.headers)
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


# ---------------------------------------------------------------------------
# Request ID middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    import uuid as _uuid_mid
    request_id = request.headers.get("X-Request-ID", str(_uuid_mid.uuid4())[:8])
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ---------------------------------------------------------------------------
# Global exception handler: unified error format, no stack traces
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import uuid as _uuid_err
    import logging
    import traceback as _tb
    from fastapi.responses import JSONResponse

    _logger = logging.getLogger("m1.error")
    request_id = getattr(request.state, "request_id", str(_uuid_err.uuid4())[:8])
    _logger.error(f"[{request_id}] {request.method} {request.url.path}: {type(exc).__name__}: {exc}")

    status = getattr(exc, "status_code", 500)
    return JSONResponse(
        status_code=status,
        content={"error": {"code": type(exc).__name__, "message": str(exc)[:200], "request_id": request_id}},
        headers={"X-Request-ID": request_id},
    )
