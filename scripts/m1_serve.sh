#!/usr/bin/env bash
# Compatibility wrapper. New callers should invoke the root serve.sh directly.
set -euo pipefail
cd "$(dirname "$0")/.."
export M1_HOST="${M1_HOST:-127.0.0.1}"
export M1_PORT="${M1_SERVE_PORT:-${M1_PORT:-5050}}"
exec ./serve.sh
