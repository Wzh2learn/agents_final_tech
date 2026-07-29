#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."
PORT="${M1_SERVE_PORT:-5050}"
fuser -k ${PORT}/tcp 2>/dev/null
pkill -f "m1_harness_${PORT}" 2>/dev/null
sleep 1
cat > /tmp/m1_harness_${PORT}.py << PY
import uvicorn, sys
sys.path.insert(0, 'src')
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from web.routers.m1 import router
app = FastAPI()
app.mount('/static', StaticFiles(directory='src/web/static'), name='static')
app.include_router(router, prefix='/api/m1')
@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})
uvicorn.run(app, host='127.0.0.1', port=${PORT})
PY
nohup ./venv/bin/python /tmp/m1_harness_${PORT}.py > /tmp/m1_harness_${PORT}.log 2>&1 &
echo "m1_serve pid $! on :${PORT}"
sleep 4
curl -s -o /dev/null -w "  :${PORT}/health -> %{http_code}\n" http://127.0.0.1:${PORT}/health
curl -s -o /dev/null -w "  :${PORT}/api/m1/sample -> %{http_code}\n" http://127.0.0.1:${PORT}/api/m1/sample
