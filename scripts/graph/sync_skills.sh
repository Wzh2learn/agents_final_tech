#!/bin/bash
# Graph Engineering - Skill sync (Phase 0)
# Copies repo skills/ (source of truth) to the harness skill dirs on this
# machine. Idempotent: safe to re-run; replaces previous copies, never
# touches skills not listed here (e.g. neat-freak).
#   Loop A (Codex CLI):   A-list -> ~/.codex/skills/
#   Loop C (Claude Code): C-list -> ~/.claude/skills/
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SRC="$PROJECT_ROOT/skills"

A_SKILLS=(systematic-debugging executing-plans subagent-driven-development verification-before-completion jinrong-docs-sync)
C_SKILLS=(requesting-code-review receiving-code-review review-codebase differential-review spec-to-code-compliance security-best-practices jinrong-docs-sync)

sync_one() {
  local name=$1 dest_root=$2
  local src="$SRC/$name" dest="$dest_root/$name"
  if [ ! -f "$src/SKILL.md" ]; then
    echo "MISSING source: $name (expected $src/SKILL.md)"
    return 1
  fi
  mkdir -p "$dest_root"
  rm -rf "$dest"
  cp -r "$src" "$dest"
  echo "synced: $name -> $dest"
}

echo "== Loop A (Codex CLI) -> ~/.codex/skills =="
for s in "${A_SKILLS[@]}"; do sync_one "$s" "$HOME/.codex/skills"; done

echo "== Loop C (Claude Code) -> ~/.claude/skills =="
for s in "${C_SKILLS[@]}"; do sync_one "$s" "$HOME/.claude/skills"; done

echo "== manifest =="
echo "[~/.codex/skills]"; ls "$HOME/.codex/skills" 2>/dev/null
echo "[~/.claude/skills]"; ls "$HOME/.claude/skills" 2>/dev/null
echo "DONE"