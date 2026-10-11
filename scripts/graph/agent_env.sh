#!/usr/bin/env bash
# Non-secret path loader for local and GB10 agent runtimes.
set -euo pipefail

JINRONG_AGENT_PATHS_FILE="${JINRONG_AGENT_PATHS_FILE:-$HOME/.config/jinrongagents/paths.env}"
if [[ -f "$JINRONG_AGENT_PATHS_FILE" ]]; then
  # This file contains paths only. Secret values belong in the named files below.
  source "$JINRONG_AGENT_PATHS_FILE"
fi

export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export CLAUDE_CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
export OPENALEX_CONFIG="${OPENALEX_CONFIG:-$HOME/.config/openalex.env}"
export CODEX_API_ENV="${CODEX_API_ENV:-$CODEX_HOME/token_plan.env}"
export AGENT_RUNTIME_ROOT="${AGENT_RUNTIME_ROOT:-$HOME/wzh/loop_runs}"
export AGENT_PROJECT_ROOT="${AGENT_PROJECT_ROOT:-$HOME/wzh/projects/agents_final_tech}"
export CODEX_AUTH_FILE="${CODEX_AUTH_FILE:-$CODEX_HOME/auth.json}"

agent_env_validate() {
  local missing=0
  for path in "$CODEX_HOME/config.toml" "$CLAUDE_CONFIG_DIR/settings.json" \
    "$OPENALEX_CONFIG"; do
    if [[ ! -f "$path" ]]; then
      echo "MISSING $path" >&2
      missing=1
    fi
  done
  if [[ ! -f "$CODEX_API_ENV" && ! -f "$CODEX_AUTH_FILE" ]]; then
    echo "MISSING Codex auth carrier: $CODEX_API_ENV or $CODEX_AUTH_FILE" >&2
    missing=1
  fi
  return "$missing"
}

agent_env_load_codex_api() {
  if [[ -f "$CODEX_API_ENV" ]]; then
    source "$CODEX_API_ENV"
    [[ -n "${OPENAI_API_KEY:-}" ]] || { echo "OPENAI_API_KEY_EMPTY" >&2; return 1; }
    return 0
  fi
  [[ -f "$CODEX_AUTH_FILE" ]] || { echo "MISSING $CODEX_AUTH_FILE" >&2; return 1; }
  return 0
}

agent_env_preflight() {
  agent_env_validate || return 1
  agent_env_load_codex_api || return 1
  echo "agent_env: paths valid; secret values loaded but not printed"
}
