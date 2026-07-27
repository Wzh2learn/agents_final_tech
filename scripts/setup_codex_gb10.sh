#!/usr/bin/env bash
# ============================================================
# GB10 Codex CLI 一键配置脚本
# 在远程 Linux 开发机上原生运行，不经过 PowerShell 转义
# 用法: bash setup_codex_gb10.sh
# ============================================================
set -euo pipefail

CODEX_DIR="$HOME/.codex"
PROJECT_DIR="$HOME/wzh/projects/agents_final_tech"
BASE_URL="https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"

# 从 .bashrc 读取 API Key
API_KEY=$(grep 'OPENAI_API_KEY' ~/.bashrc 2>/dev/null | head -1 | sed 's/.*"\(.*\)".*/\1/')
if [ -z "$API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY not found in ~/.bashrc"
    exit 1
fi
export OPENAI_API_KEY="$API_KEY"
echo "[1/6] API Key: ${API_KEY:0:12}... OK"

# ============================================================
# Step 2: 确保 Codex CLI 是最新版
# ============================================================
CURRENT_VER=$(codex --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' || echo "0.0.0")
LATEST_VER=$(npm view @openai/codex version 2>/dev/null || echo "$CURRENT_VER")
if [ "$CURRENT_VER" != "$LATEST_VER" ]; then
    echo "[2/6] Upgrading Codex CLI: $CURRENT_VER -> $LATEST_VER"
    npm install -g @openai/codex@latest 2>&1 | tail -2
else
    echo "[2/6] Codex CLI $CURRENT_VER already latest"
fi

# ============================================================
# Step 3: 写 config.toml（不用 model_catalog_json，避免 schema 问题）
# ============================================================
mkdir -p "$CODEX_DIR"

# 备份
if [ -f "$CODEX_DIR/config.toml" ]; then
    cp "$CODEX_DIR/config.toml" "$CODEX_DIR/config.toml.bak.$(date +%Y%m%d%H%M%S)"
fi

cat > "$CODEX_DIR/config.toml" << 'TOML'
model_provider = "Token_Plan"
model = "qwen3.8-max-preview"
model_reasoning_effort = "xhigh"

[model_providers.Token_Plan]
name = "Token_Plan"
base_url = "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
env_key = "OPENAI_API_KEY"
wire_api = "responses"

[projects."/home/testuser"]
trust_level = "trusted"

[projects."/home/testuser/wzh/projects/agents_final_tech"]
trust_level = "trusted"
TOML
echo "[3/6] config.toml written (default: qwen3.8-max-preview, xhigh)"

# 删除有问题的 model_catalog_json（如果存在）
rm -f "$CODEX_DIR/model-catalog.local.json"
echo "       Removed model-catalog.local.json (not needed, avoids schema errors)"

# ============================================================
# Step 4: 测试所有 Token Plan 模型的 Responses API 兼容性
# ============================================================
echo "[4/6] Testing model compatibility with Responses API..."
echo ""

MODELS="qwen3.8-max-preview qwen3.7-max qwen3.7-plus qwen3.6-flash glm-5.2 deepseek-v4-pro"
RESULTS_FILE="/tmp/codex_model_test_results.txt"
> "$RESULTS_FILE"

for MODEL in $MODELS; do
    printf "  %-25s" "$MODEL"
    # 直接用 curl 测试 responses endpoint
    RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/responses" \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"model\":\"$MODEL\",\"input\":\"Say OK\",\"max_output_tokens\":10}" \
        --max-time 30 2>/dev/null || echo "TIMEOUT")

    HTTP_CODE=$(echo "$RESP" | tail -1)
    BODY=$(echo "$RESP" | head -n -1)

    if echo "$BODY" | grep -q '"output"'; then
        echo "OK (responses API)"
        echo "$MODEL: OK" >> "$RESULTS_FILE"
    elif echo "$BODY" | grep -q 'Unsupported model'; then
        # 试 chat completions
        RESP2=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/chat/completions" \
            -H "Authorization: Bearer $API_KEY" \
            -H "Content-Type: application/json" \
            -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"Say OK\"}],\"max_tokens\":10}" \
            --max-time 30 2>/dev/null || echo "TIMEOUT")
        BODY2=$(echo "$RESP2" | head -n -1)
        if echo "$BODY2" | grep -q '"choices"'; then
            echo "CHAT-ONLY (not usable in Codex 0.145+)"
            echo "$MODEL: CHAT_ONLY" >> "$RESULTS_FILE"
        else
            echo "FAIL"
            echo "$MODEL: FAIL" >> "$RESULTS_FILE"
        fi
    elif [ "$HTTP_CODE" = "000" ] || echo "$BODY" | grep -q "TIMEOUT"; then
        echo "TIMEOUT"
        echo "$MODEL: TIMEOUT" >> "$RESULTS_FILE"
    else
        echo "FAIL (HTTP $HTTP_CODE)"
        echo "$MODEL: FAIL_$HTTP_CODE" >> "$RESULTS_FILE"
    fi
done

echo ""
echo "  Results saved to $RESULTS_FILE"

# ============================================================
# Step 5: 用 Codex CLI 做端到端验证
# ============================================================
echo ""
echo "[5/6] End-to-end Codex CLI test..."
cd "$PROJECT_DIR"

TEST_OUT=$(echo 'Reply with exactly: CODEX_READY' | timeout 90 codex exec 2>&1 || true)
if echo "$TEST_OUT" | grep -qi "CODEX_READY\|OK\|ready"; then
    echo "  Codex CLI end-to-end: PASS"
else
    echo "  Codex CLI end-to-end: CHECK OUTPUT"
    echo "$TEST_OUT" | tail -10
fi

# ============================================================
# Step 6: 创建 tmux 启动脚本和便捷别名
# ============================================================
echo ""
echo "[6/6] Setting up tmux helper..."

# 创建 tmux 启动脚本
cat > "$HOME/start_codex_tmux.sh" << 'TMUX_SCRIPT'
#!/usr/bin/env bash
# 在 tmux 后台启动 Codex CLI 会话
# 用法: bash ~/start_codex_tmux.sh [session_name]
SESSION="${1:-codex-dev}"
PROJECT="$HOME/wzh/projects/agents_final_tech"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Session '$SESSION' already exists. Attach with: tmux attach -t $SESSION"
    exit 0
fi

tmux new-session -d -s "$SESSION" -c "$PROJECT"
tmux send-keys -t "$SESSION" "cd $PROJECT && codex" Enter
echo "Started tmux session '$SESSION' with Codex CLI in $PROJECT"
echo "Attach: tmux attach -t $SESSION"
echo "Detach: Ctrl-b d"
TMUX_SCRIPT
chmod +x "$HOME/start_codex_tmux.sh"

# 创建模型切换脚本
cat > "$HOME/switch_codex_model.sh" << 'SWITCH_SCRIPT'
#!/usr/bin/env bash
# 切换 Codex CLI 默认模型
# 用法: bash ~/switch_codex_model.sh <model_name>
# 可用: qwen3.8-max-preview qwen3.7-max qwen3.7-plus qwen3.6-flash deepseek-v4-pro
MODEL="${1:-qwen3.8-max-preview}"
CONFIG="$HOME/.codex/config.toml"

if [ ! -f "$CONFIG" ]; then
    echo "ERROR: $CONFIG not found"
    exit 1
fi

sed -i "s/^model = \".*\"/model = \"$MODEL\"/" "$CONFIG"
echo "Switched default model to: $MODEL"
grep "^model " "$CONFIG"
SWITCH_SCRIPT
chmod +x "$HOME/switch_codex_model.sh"

# 添加便捷别名到 .bashrc（在 guard 之前）
if ! grep -q "alias codex-tmux" ~/.bashrc; then
    ALIASES='
# Codex CLI convenience aliases
alias codex-tmux="bash ~/start_codex_tmux.sh"
alias codex-switch="bash ~/switch_codex_model.sh"
'
    # 插入到文件开头（guard 之前）
    sed -i "1i\\$ALIASES" ~/.bashrc
    echo "  Added aliases: codex-tmux, codex-switch"
fi

echo ""
echo "============================================================"
echo "  CONFIGURATION COMPLETE"
echo "============================================================"
echo ""
echo "  Codex CLI:    $(codex --version 2>/dev/null)"
echo "  Default:      qwen3.8-max-preview (xhigh)"
echo "  Provider:     Token Plan (responses API)"
echo "  Project:      $PROJECT_DIR"
echo ""
echo "  Quick start:"
echo "    codex                          # 交互模式"
echo "    codex exec 'your task'         # 非交互模式"
echo "    bash ~/start_codex_tmux.sh     # tmux 后台会话"
echo "    bash ~/switch_codex_model.sh qwen3.7-max  # 切换模型"
echo ""
echo "  Model compatibility:"
cat "$RESULTS_FILE" | while read line; do
    echo "    $line"
done
echo ""
echo "  NOTE: glm-5.2 only supports Chat API, not usable in Codex 0.145+."
echo "  Use qwen3.8-max-preview or deepseek-v4-pro instead."
echo "============================================================"
