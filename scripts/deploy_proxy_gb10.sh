#!/usr/bin/env bash
# DEPRECATED 2026-10-09: current routes are Xiaomi_Token_Plan mimo-v2.6-flash/pro. Do not run this legacy installer without explicit approval.
# Deploy responses2chat proxy on GB10 and configure Codex dual-provider.
# Usage: bash deploy_proxy_gb10.sh
set -euo pipefail

PROXY_PORT=8100
PROXY_SCRIPT="$HOME/.local/bin/responses2chat_proxy.py"
CODEX_DIR="$HOME/.codex"

echo "[1/5] Installing proxy script..."
mkdir -p "$HOME/.local/bin"
cp /tmp/responses2chat_proxy.py "$PROXY_SCRIPT"
chmod +x "$PROXY_SCRIPT"
echo "  Installed: $PROXY_SCRIPT"

echo "[2/5] Configuring Codex dual-provider..."
cat > "$CODEX_DIR/config.toml" << 'TOML'
# Default: qwen3.8-max-preview via direct Responses API
model_provider = "Token_Plan"
model = "qwen3.8-max-preview"
model_reasoning_effort = "xhigh"

# Direct provider (models that support Responses API natively)
[model_providers.Token_Plan]
name = "Token_Plan"
base_url = "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
env_key = "OPENAI_API_KEY"
wire_api = "responses"

# Proxy provider (chat-only models via local responses2chat proxy)
[model_providers.Token_Plan_Chat]
name = "Token_Plan_Chat"
base_url = "http://127.0.0.1:8100/v1"
env_key = "OPENAI_API_KEY"
wire_api = "responses"

[projects."/home/testuser"]
trust_level = "trusted"

[projects."/home/testuser/wzh/projects/agents_final_tech"]
trust_level = "trusted"
TOML
echo "  config.toml written with dual providers"

echo "[3/5] Creating proxy launcher scripts..."
cat > "$HOME/start_proxy.sh" << 'LAUNCHER'
#!/usr/bin/env bash
# DEPRECATED 2026-10-09: current routes are Xiaomi_Token_Plan mimo-v2.6-flash/pro. Do not run this legacy installer without explicit approval.
PROXY="$HOME/.local/bin/responses2chat_proxy.py"
PIDFILE="/tmp/responses2chat_proxy.pid"
if [ -f "$PIDFILE" ] && kill -0 "$(cat $PIDFILE)" 2>/dev/null; then
    echo "Proxy already running (PID $(cat $PIDFILE))"
    exit 0
fi
nohup python3 "$PROXY" --port 8100 > /tmp/responses2chat_proxy.log 2>&1 &
echo $! > "$PIDFILE"
sleep 1
if kill -0 "$(cat $PIDFILE)" 2>/dev/null; then
    echo "Proxy started (PID $(cat $PIDFILE)) on port 8100"
else
    echo "ERROR: Proxy failed to start. Check /tmp/responses2chat_proxy.log"
    exit 1
fi
LAUNCHER
chmod +x "$HOME/start_proxy.sh"

cat > "$HOME/stop_proxy.sh" << 'STOPPER'
#!/usr/bin/env bash
# DEPRECATED 2026-10-09: current routes are Xiaomi_Token_Plan mimo-v2.6-flash/pro. Do not run this legacy installer without explicit approval.
PIDFILE="/tmp/responses2chat_proxy.pid"
if [ -f "$PIDFILE" ]; then
    kill "$(cat $PIDFILE)" 2>/dev/null && echo "Proxy stopped" || echo "Not running"
    rm -f "$PIDFILE"
else
    echo "No PID file"
fi
STOPPER
chmod +x "$HOME/stop_proxy.sh"

echo "[4/5] Starting proxy..."
bash "$HOME/start_proxy.sh"

echo "[5/5] Testing models via proxy..."
sleep 2

RESP=$(curl -s -X POST "http://127.0.0.1:$PROXY_PORT/v1/responses" \
    -H "Content-Type: application/json" \
    -d '{"model":"glm-5.2","input":"Reply with exactly: PROXY_OK","stream":false}' \
    --max-time 60 2>/dev/null || echo "CURL_FAILED")

if echo "$RESP" | grep -q "PROXY_OK\|output_text"; then
    echo "  glm-5.2 via proxy: PASS"
else
    echo "  glm-5.2 via proxy: CHECK"
    echo "  $(echo "$RESP" | head -c 300)"
fi

RESP2=$(curl -s -X POST "http://127.0.0.1:$PROXY_PORT/v1/responses" \
    -H "Content-Type: application/json" \
    -d '{"model":"deepseek-v4-pro","input":"Reply with exactly: DS_OK","stream":false}' \
    --max-time 60 2>/dev/null || echo "CURL_FAILED")

if echo "$RESP2" | grep -q "DS_OK\|output_text"; then
    echo "  deepseek-v4-pro via proxy: PASS"
else
    echo "  deepseek-v4-pro via proxy: CHECK"
    echo "  $(echo "$RESP2" | head -c 300)"
fi

echo ""
echo "============================================================"
echo "  DEPLOYMENT COMPLETE"
echo "============================================================"
echo ""
echo "  Model routing:"
echo "    qwen3.8-max-preview  -> Token_Plan (direct)"
echo "    qwen3.7-max          -> Token_Plan (direct)"
echo "    glm-5.2              -> Token_Plan_Chat (proxy :8100)"
echo "    deepseek-v4-pro      -> Token_Plan_Chat (proxy :8100)"
echo ""
echo "  Switch model:"
echo "    bash ~/switch_codex_model.sh glm-5.2"
echo "    (also switches provider to Token_Plan_Chat)"
echo ""
echo "  Manage proxy:"
echo "    bash ~/start_proxy.sh / bash ~/stop_proxy.sh"
echo "============================================================"
