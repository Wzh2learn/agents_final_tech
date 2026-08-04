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

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "JINRONG_MCP_PYTHON must reference an executable Python interpreter." >&2
  exit 2
fi

export PYTHONPATH="${PROJECT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
cd "${PROJECT_ROOT}"
exec "${PYTHON_BIN}" -m tabular_mcp_server.server
