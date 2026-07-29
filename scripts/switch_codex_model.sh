#!/usr/bin/env bash
# Switch the GB10 Codex CLI default model/provider (Token Plan).
# Usage: bash scripts/switch_codex_model.sh [qwen|glm|deepseek]
set -uo pipefail
MODE="${1:-qwen}"
CFG="$HOME/.codex/config.toml"
case "$MODE" in
  qwen)     MODEL="qwen3.8-max-preview"; PROV="Token_Plan" ;;
  glm)      MODEL="glm-5.2";            PROV="Token_Plan_Chat" ;;
  deepseek) MODEL="deepseek-v4-pro";    PROV="Token_Plan_Chat" ;;
  *) echo "usage: $0 [qwen|glm|deepseek]"; exit 2 ;;
esac
if [ "$PROV" = "Token_Plan_Chat" ]; then
  if [ -x "$HOME/start_proxy.sh" ]; then
    bash "$HOME/start_proxy.sh" >/dev/null 2>&1 || true
  else
    pgrep -f responses2chat_proxy >/dev/null 2>&1 || nohup python3 "$HOME/.local/bin/responses2chat_proxy.py" >/tmp/responses2chat_proxy.log 2>&1 &
  fi
fi
python3 - "$CFG" "$MODEL" "$PROV" << 'PY'
import sys, re
cfg, model, prov = sys.argv[1], sys.argv[2], sys.argv[3]
lines = open(cfg, encoding="utf-8").read().split("\n")
out = []
for ln in lines:
    if re.match(r'^model\s*=', ln):
        out.append('model = "%s"' % model)
    elif re.match(r'^model_provider\s*=', ln):
        out.append('model_provider = "%s"' % prov)
    else:
        out.append(ln)
open(cfg, "w", encoding="utf-8").write("\n".join(out))
print("switched codex model ->", model, "provider ->", prov)
PY
grep -E '^model(_provider)?\s*=' "$CFG"
