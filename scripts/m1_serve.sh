#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."
PORT="${M1_SERVE_PORT:-5050}"
fuser -k ${PORT}/tcp 2>/dev/null
pkill -f "m1_harness_${PORT}" 2>/dev/null
sleep 1
PROJECT_ROOT="$(pwd)"
cat > /tmp/m1_harness_${PORT}.py << PY
import uvicorn, sys
sys.path.insert(0, '${PROJECT_ROOT}/src')
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from web.routers.m1 import router
from web.routers.m2 import router as m2_router
app = FastAPI()
app.mount('/static', StaticFiles(directory='${PROJECT_ROOT}/src/web/static'), name='static')
app.include_router(router, prefix='/api/m1')
app.include_router(m2_router, prefix='/api/m2')
templates = Jinja2Templates(directory='${PROJECT_ROOT}/src/web/templates')
@app.get("/m1", response_class=HTMLResponse)
async def m1_page(request: Request):
    return templates.TemplateResponse("m1.html", {"request": request})
@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})
PY
# workers=2 requires import string; add /tmp to PYTHONPATH so uvicorn can import
export PYTHONPATH="/tmp:${PYTHONPATH:-}"
nohup ./venv/bin/uvicorn "m1_harness_${PORT}:app" --host 127.0.0.1 --port ${PORT} --workers 2 > /tmp/m1_harness_${PORT}.log 2>&1 &
echo "m1_serve pid $! on :${PORT} (workers=2)"
sleep 4
curl -s -o /dev/null -w "  :${PORT}/health -> %{http_code}\n" http://127.0.0.1:${PORT}/health
curl -s -o /dev/null -w "  :${PORT}/m1 -> %{http_code}\n" http://127.0.0.1:${PORT}/m1
curl -s -o /dev/null -w "  :${PORT}/api/m1/sample -> %{http_code}\n" http://127.0.0.1:${PORT}/api/m1/sample
curl -s -o /dev/null -w "  :${PORT}/api/m2/health -> %{http_code}\n" http://127.0.0.1:${PORT}/api/m2/health
