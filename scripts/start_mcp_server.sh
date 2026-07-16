#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${JINRONG_MCP_PYTHON:-python}"

if [[ -z "${PGDATABASE_URL:-}" ]]; then
  echo "PGDATABASE_URL must be set before starting the MCP server." >&2
  exit 2
fi

export PYTHONPATH="${PROJECT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
cd "${PROJECT_ROOT}"
exec "${PYTHON_BIN}" -m mcp_server.server
