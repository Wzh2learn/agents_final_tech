#!/usr/bin/env bash
set -euo pipefail

# Keep the tabular path independent from PostgreSQL and unrelated MCP startup.
export JINRONG_SKIP_PG_CHECK=1
export OPENCODE_CONFIG_CONTENT='{
  "mcp": {
    "jinrong-rag": {"enabled": false},
    "jinrong-vision": {"enabled": false},
    "jinrong-tabular": {"enabled": true}
  },
  "permission": {
    "jinrong-tabular_*": "allow"
  }
}'

exec bash scripts/run_opencode_gb10.sh "$@"
