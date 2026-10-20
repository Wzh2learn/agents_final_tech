#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  printf 'usage: %s MANIFEST\n' "$0" >&2
  exit 64
fi

manifest="$1"
if [[ "$manifest" != /* ]]; then
  printf 'manifest path must be absolute\n' >&2
  exit 64
fi
manifest_dir="$(cd "$(dirname "$manifest")" && pwd)"
manifest_name="$(basename "$manifest")"
cd "$manifest_dir"
exec md5sum --check -- "$manifest_name"
