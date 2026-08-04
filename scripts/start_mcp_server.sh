#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${JINRONG_MCP_PYTHON:-}"
if [[ -z "${PYTHON_BIN}" ]]; then
  if [[ -x "${PROJECT_ROOT}/venv/bin/python" ]]; then
    PYTHON_BIN="${PROJECT_ROOT}/venv/bin/python"
  elif [[ -x "${HOME}/miniconda3/envs/wzh_vllm/bin/python" ]]; then
    PYTHON_BIN="${HOME}/miniconda3/envs/wzh_vllm/bin/python"
  else
    echo "No MCP Python found: set JINRONG_MCP_PYTHON or provide ${PROJECT_ROOT}/venv/bin/python." >&2
    exit 2
  fi
fi

if [[ -z "${PGDATABASE_URL:-}" ]]; then
  echo "PGDATABASE_URL must be set before starting the MCP server." >&2
  exit 2
fi

# Load project .env (embedding API key etc.) if present, so MCP retrieval
# matches the :5050 FastAPI process environment. Values never leave this host.
if [[ -f "${PROJECT_ROOT}/.env" ]]; then
  set -a
  . "${PROJECT_ROOT}/.env"
  set +a
fi

export PYTHONPATH="${PROJECT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
cd "${PROJECT_ROOT}"
exec "${PYTHON_BIN}" -m mcp_server.server
