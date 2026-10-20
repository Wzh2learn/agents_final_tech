#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
target="$repo_root/scripts/graph/dispatch_precheck.sh"

exec "$target" "$@"
