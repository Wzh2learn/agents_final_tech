#!/usr/bin/env bash
# Drift check: every repo skills/<name>/ (with SKILL.md) must be listed in
# sync_skills.sh (A_SKILLS or C_SKILLS), and every listed name must exist.
# Catches the 2026-08-09 incident where m2-rag-playbook existed in skills/
# but was never distributed because the lists were not updated.
#
# Exit: 0 = in sync, 1 = drift found.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SYNC="$ROOT/scripts/graph/sync_skills.sh"

LISTED=$(sed -n "s/^A_SKILLS=(\(.*\))/\1/p; s/^C_SKILLS=(\(.*\))/\1/p" "$SYNC" | tr " " "\n" | sort -u)
ACTUAL=$(cd "$ROOT/skills" && for d in */; do [ -f "$d/SKILL.md" ] && echo "${d%/}"; done | sort -u)

MISSING_DIST=$(comm -23 <(echo "$ACTUAL") <(echo "$LISTED"))
GHOST=$(comm -13 <(echo "$ACTUAL") <(echo "$LISTED"))

STATUS=0
if [ -n "$MISSING_DIST" ]; then
  echo "[skill-sync] DRIFT: repo skills not in any distribution list:"
  echo "$MISSING_DIST" | sed "s/^/  - /"
  STATUS=1
fi
if [ -n "$GHOST" ]; then
  echo "[skill-sync] DRIFT: listed in sync_skills.sh but missing from skills/:"
  echo "$GHOST" | sed "s/^/  - /"
  STATUS=1
fi
if [ "$STATUS" = "0" ]; then
  echo "[skill-sync] PASS: $(echo "$ACTUAL" | wc -l) skills in sync (repo <-> sync_skills.sh)"
fi
exit $STATUS
