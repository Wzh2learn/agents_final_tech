#!/bin/bash
# ============================================================
# Multi-Tool Config Sync Script
#
# Keeps rule files (CLAUDE.md / AGENTS.md) and skills/hooks in sync
# across two AI coding tools (e.g., Claude Code ↔ another AI IDE).
#
# Design principles:
#   - Auto-direction: whichever file is newer becomes the source
#   - Skills/hooks: one-directional (SSOT side → mirror side)
#   - Safe: never deletes without rsync --delete explicitly chosen
#
# Usage:
#   bash sync_config.sh                 # auto-direction (recommended)
#   bash sync_config.sh --to-claude     # force AGENTS.md → CLAUDE.md
#   bash sync_config.sh --to-agents     # force CLAUDE.md → AGENTS.md
#
# Discipline: after editing any rule file, run this script once.
# ============================================================
set -euo pipefail
cd "$(dirname "$0")"

# Mirror notice injected at top of CLAUDE.md (stripped when syncing back)
NOTICE='<!-- This file mirrors AGENTS.md; run bash sync_config.sh after editing either -->'

MODE="${1:-auto}"

to_claude() {
    {
        echo "$NOTICE"
        cat AGENTS.md
    } > CLAUDE.md
    touch -r AGENTS.md CLAUDE.md   # align mtime to avoid drift false-positives
    echo "[OK] AGENTS.md → CLAUDE.md"
}

to_agents() {
    # Strip the mirror notice before syncing back
    tail -n +2 CLAUDE.md > AGENTS.md
    touch -r CLAUDE.md AGENTS.md
    echo "[OK] CLAUDE.md → AGENTS.md (mirror notice stripped)"
}

[ -f AGENTS.md ] || { echo "[ERR] AGENTS.md not found"; exit 1; }
[ -f CLAUDE.md ] || { echo "[ERR] CLAUDE.md not found; run --to-claude first"; exit 1; }

case "$MODE" in
    --to-claude) to_claude ;;
    --to-agents) to_agents ;;
    auto)
        if [ CLAUDE.md -nt AGENTS.md ]; then
            echo "[AUTO] CLAUDE.md is newer → syncing to AGENTS.md"
            to_agents
        else
            to_claude
        fi
        ;;
    *) echo "Usage: bash sync_config.sh [--to-claude|--to-agents]"; exit 1 ;;
esac

# ---------- Skills: one-directional sync ----------
# Choose your SSOT side (the one you actually edit in daily workflow)
SSOT_SKILLS=".claude/skills"     # Change to your SSOT directory
MIRROR_SKILLS=".other-tool/skills"  # Change to your mirror directory

if [ -d "$SSOT_SKILLS" ]; then
    mkdir -p "$MIRROR_SKILLS"
    rsync -a --delete "$SSOT_SKILLS/" "$MIRROR_SKILLS/"
    echo "[OK] $SSOT_SKILLS → $MIRROR_SKILLS ($(ls "$SSOT_SKILLS" 2>/dev/null | wc -l | tr -d ' ') skills)"
fi

# ---------- Hooks: one-directional sync ----------
SSOT_HOOKS=".claude/hooks"
MIRROR_HOOKS=".other-tool/hooks"

if [ -d "$SSOT_HOOKS" ]; then
    mkdir -p "$MIRROR_HOOKS"
    rsync -a --delete "$SSOT_HOOKS/" "$MIRROR_HOOKS/"
    echo "[OK] $SSOT_HOOKS → $MIRROR_HOOKS ($(ls "$SSOT_HOOKS" 2>/dev/null | wc -l | tr -d ' ') hooks)"
fi

echo "[DONE] Multi-tool config synced"
