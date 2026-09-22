#!/usr/bin/env bash
set -euo pipefail
ROOT="${JINRONG_LOOP_C_HOME:-$HOME/.jinrong-loop-c}"
exec python3 "$ROOT/loop_c_lead.py" "$@"
