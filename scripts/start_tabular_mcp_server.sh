#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${JINRONG_MCP_PYTHON:-$HOME/miniconda3/envs/wzh_vllm/bin/python}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "JINRONG_MCP_PYTHON must reference an executable Python interpreter." >&2
  exit 2
fi

export PYTHONPATH="${PROJECT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
cd "${PROJECT_ROOT}"
exec "${PYTHON_BIN}" -m tabular_mcp_server.server
