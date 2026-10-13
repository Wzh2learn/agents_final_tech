#!/usr/bin/env bash
# Fetch the raw TAT-QA records (public, CC BY 4.0) via the repository tarball and verify integrity.
# Authorised 2026-10-13 (WP-0 item A2). Writes only under data/research/tatqa_raw_2026/.
# Integrity gates: tar exit status, JSON parse, non-empty record list. A truncated fetch FAILS loudly.
set -euo pipefail
DEST="${1:-data/research/tatqa_raw_2026}"
DEST="$(mkdir -p "$DEST" && cd "$DEST" && pwd)"   # absolute
TARBALL="$(mktemp -t tatqa_repo_XXXX).tar.gz"
cd "$DEST"

echo "downloading tarball..."
curl -sSL --http1.1 --retry 5 --retry-delay 3 --retry-all-errors --max-time 1800 \
  -o "$TARBALL" "https://codeload.github.com/NExTplusplus/TAT-QA/tar.gz/refs/heads/master"
echo "tarball bytes: $(wc -c < "$TARBALL")"

WORK="$(mktemp -d)"
tar -xzf "$TARBALL" -C "$WORK" --wildcards '*/dataset_raw/*.json'
find "$WORK" -name 'tatqa_dataset_train.json' -o -name 'tatqa_dataset_dev.json' | while read -r f; do
  cp -f "$f" "$DEST/$(basename "$f")"
done
rm -rf "$WORK" "$TARBALL"

python3 - <<'PY'
import json, sys
for name in ("tatqa_dataset_train.json", "tatqa_dataset_dev.json"):
    d = json.load(open(name))
    n = len(d)
    assert n > 100, f"{name}: implausible record count {n}"
    tables = sum(len(r.get("table", {}).get("table", [])) > 0 for r in d)
    print(f"{name}: {n} records, {tables} with a table body")
PY

sha256sum tatqa_dataset_train.json tatqa_dataset_dev.json > FETCH_RECEIPT.sha256
{
  echo "source: https://github.com/NExTplusplus/TAT-QA (dataset_raw, master)"
  echo "method: repository tarball via codeload.github.com, integrity-gated (tar + JSON parse + record count)"
  echo "fetch_date_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "licence: repo MIT; data CC BY 4.0 (README)"
  cat FETCH_RECEIPT.sha256
} > FETCH_RECEIPT.txt
cat FETCH_RECEIPT.txt