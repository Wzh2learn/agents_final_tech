#!/usr/bin/env bash
# Print non-secret runtime/config health for local and GB10.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/agent_env.sh"
agent_env_preflight
printf 'CODEX_HOME=%s\n' "$CODEX_HOME"
printf 'CLAUDE_CONFIG_DIR=%s\n' "$CLAUDE_CONFIG_DIR"
printf 'OPENALEX_CONFIG=%s\n' "$OPENALEX_CONFIG"
printf 'CODEX_API_ENV=%s\n' "$CODEX_API_ENV"
printf 'CODEX_AUTH_FILE=%s\n' "$CODEX_AUTH_FILE"
printf 'AGENT_RUNTIME_ROOT=%s\n' "$AGENT_RUNTIME_ROOT"
printf 'AGENT_PROJECT_ROOT=%s\n' "$AGENT_PROJECT_ROOT"
command -v codex >/dev/null && codex --version || echo 'codex=missing'
command -v claude >/dev/null && claude --version || echo 'claude=missing'
