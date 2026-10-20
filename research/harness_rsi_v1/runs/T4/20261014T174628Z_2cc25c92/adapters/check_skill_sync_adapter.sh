#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
exec "$repo_root/scripts/graph/check_skill_sync.sh"
