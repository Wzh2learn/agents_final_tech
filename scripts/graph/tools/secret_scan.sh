#!/usr/bin/env bash
# Credential-shape scanner for committed artifacts and optional Git history.
#
# Default scope is Git-tracked files. Use --all-files for an explicit local
# working-tree audit, including ignored runtime carriers. Project codenames and
# internal identifiers belong in out-of-repo lists supplied with --words or
# --patterns. Home-path disclosure is opt-in through --paths.
#
# Usage: secret_scan.sh [--words FILE] [--patterns FILE] [--history]
#                       [--all-files] [--paths] [DIR]
# Exit: 0 clean, 1 findings, 2 usage error.
set -u

WORDS=""
PATTERNS=""
HISTORY=0
ALL_FILES=0
SHOW_PATHS=0
DIR=""
while [ $# -gt 0 ]; do
  case "$1" in
    --words)
      WORDS="${2:-}"
      [ -n "$WORDS" ] || { echo "--words needs FILE" >&2; exit 2; }
      shift 2
      ;;
    --patterns)
      PATTERNS="${2:-}"
      [ -n "$PATTERNS" ] || { echo "--patterns needs FILE" >&2; exit 2; }
      shift 2
      ;;
    --history) HISTORY=1; shift ;;
    --all-files) ALL_FILES=1; shift ;;
    --paths) SHOW_PATHS=1; shift ;;
    -*) echo "unknown flag: $1" >&2; exit 2 ;;
    *) DIR="$1"; shift ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIR="${DIR:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"
[ -d "$DIR" ] || { echo "not a directory: $DIR" >&2; exit 2; }
for f in "$WORDS" "$PATTERNS"; do
  [ -z "$f" ] && continue
  [ -f "$f" ] || { echo "words/patterns file not found: $f" >&2; exit 2; }
done

IS_GIT=0
git -C "$DIR" rev-parse --git-dir >/dev/null 2>&1 && IS_GIT=1

findings=0
report() {
  echo "FINDING [$1] $2"
  findings=$((findings + 1))
}

is_self_test_file() {
  case "$1" in
    scripts/graph/tools/secret_scan.sh|scripts/graph/tools/test_secret_scan.sh|tests/graph_tools/test_secret_scan.sh|./scripts/graph/tools/secret_scan.sh|./scripts/graph/tools/test_secret_scan.sh|./tests/graph_tools/test_secret_scan.sh)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

is_placeholder_hit() {
  printf '%s' "$1" | grep -qiE '(from-env-|your[-_]|example|placeholder|dummy|fake|sample|redacted|no-key|must-not|must_not|never-read|<[a-z_]+>)'
}

iter_files() {
  if [ "$IS_GIT" = 1 ] && [ "$ALL_FILES" = 0 ]; then
    git -C "$DIR" ls-files -z
  else
    find "$DIR" -type f -not -path "$DIR/.git/*" -print0
  fi
}

while IFS= read -r -d '' file; do
  case "$file" in
    /*) rel="${file#"$DIR"/}" ;;
    *) rel="$file" ;;
  esac
  is_self_test_file "$rel" && continue

  while IFS= read -r hit; do
    [ -z "$hit" ] && continue
    case "$hit" in *"secret-scan:allow"*) continue ;; esac
    is_placeholder_hit "$hit" && continue
    report "shape" "$hit"
  done < <(grep -nIE 'LTAI[A-Za-z0-9]{12,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|xox[baprs]-[A-Za-z0-9-]{10,}|sk-[A-Za-z0-9]{32,}|AIza[0-9A-Za-z_-]{35}|([Aa][Pp][Ii][_-]?[Kk][Ee][Yy]|[Ss][Ee][Cc][Rr][Ee][Tt]|[Tt][Oo][Kk][Ee][Nn]|[Pp][Aa][Ss][Ss][Ww]([Oo][Rr])?[Dd])["'"'"']?[[:space:]]*[:=][[:space:]]*["'"'"'][A-Za-z0-9/+=_.-]{16,}["'"'"']' "$file" 2>/dev/null)

  if [ "$SHOW_PATHS" = 1 ]; then
    while IFS= read -r hit; do
      [ -z "$hit" ] && continue
      case "$hit" in *"secret-scan:allow"*) continue ;; esac
      report "path" "$hit"
    done < <(grep -nIE '(/Users|/home)/[a-z][a-z0-9._-]{2,}' "$file" 2>/dev/null)
  fi

  if grep -qE '^-----BEGIN [A-Z ]*PRIVATE KEY-----$' "$file" 2>/dev/null \
    && grep -qE '^[A-Za-z0-9+/]{40,}={0,2}$' "$file" 2>/dev/null; then
    report "pem-body" "$rel (private-key header and base64 body)"
  fi

  if [ -n "$WORDS" ]; then
    while IFS= read -r hit; do
      [ -z "$hit" ] && continue
      case "$hit" in *"secret-scan:allow"*) continue ;; esac
      report "word" "$hit"
    done < <(grep -nIF -f "$WORDS" "$file" 2>/dev/null)
  fi

  if [ -n "$PATTERNS" ]; then
    while IFS= read -r hit; do
      [ -z "$hit" ] && continue
      case "$hit" in *"secret-scan:allow"*) continue ;; esac
      report "pattern" "$hit"
    done < <(grep -nIE -f "$PATTERNS" "$file" 2>/dev/null)
  fi
done < <(iter_files)

if [ -z "$WORDS" ] && [ -z "$PATTERNS" ]; then
  echo "NOTE: no maintainer list; project-specific identifiers are not covered"
fi
if [ "$SHOW_PATHS" = 0 ]; then
  echo "NOTE: home-path disclosure scan disabled; pass --paths to enable it"
fi

if [ "$HISTORY" = 1 ]; then
  if [ "$IS_GIT" = 1 ]; then
    ids="$(git -C "$DIR" log --all --format='%an <%ae>%n%cn <%ce>' | sort -u)"
    echo "--- git identities (review before public release) ---"
    echo "$ids"
    if [ -n "$WORDS$PATTERNS" ]; then
      while IFS= read -r id; do
        [ -z "$id" ] && continue
        if [ -n "$WORDS" ] && grep -qF -f "$WORDS" <<<"$id"; then
          report "history" "$id"
          continue
        fi
        if [ -n "$PATTERNS" ] && grep -qE -f "$PATTERNS" <<<"$id"; then
          report "history" "$id"
        fi
      done <<<"$ids"
    fi
  else
    echo "NOTE: --history requested but $DIR is not a git repository; dimension skipped"
  fi
fi

if [ "$findings" -gt 0 ]; then
  echo "[secret_scan] $findings finding(s); fix or document each inline exemption"
  exit 1
fi
echo "[secret_scan] clean ($( [ "$ALL_FILES" = 1 ] && echo 'all files' || echo 'tracked files')$( [ -n "$WORDS$PATTERNS" ] && echo ' + maintainer lists')$( [ "$SHOW_PATHS" = 1 ] && echo ' + path review')$( [ "$HISTORY" = 1 ] && echo ' + history review'))"
