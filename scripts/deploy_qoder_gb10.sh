#!/usr/bin/env bash
# Deploy Qoder CLI config on GB10 (settings.json + verify auth)
set -uo pipefail
QODER="$HOME/.local/qoder/node_modules/.bin/qodercli"
QODER_DIR="$HOME/.qoder"

echo "=== 1. Check qodercli binary ==="
if [ -x "$QODER" ]; then
  echo "OK: $QODER version $($QODER --version 2>/dev/null || echo unknown)"
else
  echo "BLOCKED: qodercli not found at $QODER"
  echo "Install: npm install --prefix ~/.local/qoder @qoder-ai/qodercli"
  exit 1
fi

echo "=== 2. Deploy settings.json ==="
mkdir -p "$QODER_DIR"
cp /tmp/qoder_settings_template.json "$QODER_DIR/settings.json"
echo "Deployed: $QODER_DIR/settings.json"

echo "=== 3. Check auth ==="
if [ -n "${QODER_PERSONAL_ACCESS_TOKEN:-}" ]; then
  echo "PAT is set (length ${#QODER_PERSONAL_ACCESS_TOKEN})"
  echo "Testing: $QODER --list-models 2>&1 | head -5"
  $QODER --list-models 2>&1 | head -5 || echo "list-models failed (may need valid PAT format)"
else
  echo "WARNING: QODER_PERSONAL_ACCESS_TOKEN not set"
  echo "To enable Qoder loops, set it in ~/.bashrc:"
  echo '  export QODER_PERSONAL_ACCESS_TOKEN="your-pat-here"'
  echo "Get PAT from: https://qoder.com/account/integrations"
fi

echo "=== 4. Verify providers config ==="
python3 -c "
import json
s = json.load(open('$QODER_DIR/settings.json'))
for pid, p in s.get('providers', {}).items():
    models = [m['modelId'] for m in p.get('models', [])]
    print(f'  {pid}: {p[\"baseUrl\"]} -> {models}')
" 2>/dev/null || echo "settings.json parse error"

echo "=== 5. Quick connectivity (local-llama, no auth needed for provider itself) ==="
curl -s http://127.0.0.1:8004/v1/models 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  :8004 OK: {d[\"data\"][0][\"id\"]}')" 2>/dev/null || echo "  :8004 not reachable"
curl -s http://127.0.0.1:8100/v1/models 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  :8100 OK: {len(d[\"data\"])} models')" 2>/dev/null || echo "  :8100 not reachable"

echo "=== DONE ==="
echo "Next: set QODER_PERSONAL_ACCESS_TOKEN, then run loop with:"
echo "  $QODER -m local-llama/qwen3-14b -p 'your prompt' --dangerously-skip-permissions"