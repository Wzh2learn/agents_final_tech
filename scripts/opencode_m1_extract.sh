#!/usr/bin/env bash
# opencode m1-extraction agent 稳定入口 (替代 prompt 内联长命令, 2026-08-07 用户批准)
# 用法: bash scripts/opencode_m1_extract.sh [--samples-dir DIR]
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SAMPLES_DIR="${HOME}/wzh/m1_samples"
if [[ "${1:-}" == "--samples-dir" && -n "${2:-}" ]]; then
  SAMPLES_DIR="$2"
fi
PYTHON_BIN="${PROJECT_ROOT}/venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "ERROR: venv python not found at $PYTHON_BIN" >&2
  exit 2
fi
mkdir -p /tmp/opencode
"$PYTHON_BIN" "$PROJECT_ROOT/scripts/m1_statement_parser.py" \
  --samples-dir "$SAMPLES_DIR" \
  --json /tmp/opencode/m1_extract.json \
  --compact-summary /tmp/opencode/m1_compact_summary.json 2>&1 | tail -20
