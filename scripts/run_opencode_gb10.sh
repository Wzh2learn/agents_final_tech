#!/usr/bin/env bash
set -euo pipefail

# Avoid a remote models.dev refresh on development machines with restricted VPN access.
export OPENCODE_DISABLE_MODELS_FETCH="${OPENCODE_DISABLE_MODELS_FETCH:-1}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export JINRONG_MCP_PYTHON="${JINRONG_MCP_PYTHON:-${PROJECT_ROOT}/venv/bin/python}"
if [[ ! -x "${JINRONG_MCP_PYTHON}" && -x "${HOME}/miniconda3/envs/wzh_vllm/bin/python" ]]; then
  export JINRONG_MCP_PYTHON="${HOME}/miniconda3/envs/wzh_vllm/bin/python"
fi

if [[ "${JINRONG_SKIP_PG_CHECK:-0}" != "1" && -z "${PGDATABASE_URL:-}" ]]; then
  echo "PGDATABASE_URL must be set before starting OpenCode." >&2
  echo "Example: export PGDATABASE_URL='postgresql://USER:PASSWORD@127.0.0.1:15432/vector_db'" >&2
  exit 2
fi

if [[ ! -x "${JINRONG_MCP_PYTHON}" ]]; then
  echo "MCP Python executable not found: ${JINRONG_MCP_PYTHON}" >&2
  exit 2
fi

if [[ ! -x "${HOME}/.opencode/bin/opencode" ]]; then
  echo "OpenCode executable not found: ${HOME}/.opencode/bin/opencode" >&2
  exit 2
fi

exec "${HOME}/.opencode/bin/opencode" "$@"
