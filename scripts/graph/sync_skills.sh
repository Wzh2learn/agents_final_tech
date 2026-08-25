#!/bin/bash
# Graph Engineering - Skill sync (Phase 0)
# Copies repo skills/ (source of truth) to the harness skill dirs on this
# machine. Idempotent: safe to re-run; replaces previous copies, never
# touches skills not listed here (e.g. neat-freak).
#   Loop A (Codex CLI):   A-list -> ~/.codex/skills/
#   Loop C (Claude Code): C-list -> ~/.claude/skills/
set -euo pipefail

# 用法: sync_skills.sh          # 同步 (幂等)
#       sync_skills.sh --check  # 只检查 repo 与两端安装一致性, 漂移 exit 1 (Q3)
CHECK_MODE=0
[ "${1:-}" = "--check" ] && CHECK_MODE=1

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SRC="$PROJECT_ROOT/skills"

A_SKILLS=(systematic-debugging executing-plans subagent-driven-development verification-before-completion jinrong-docs-sync m1-gap-triage m2-rag-playbook graph-loop-rules agent-prompt-contracts research-writing-skill office-academic-skill scientific-toolkit-skill verify-before-done shift-notes context-budget tool-restraint spec-first sprint-contract broken-window-check eval-harness evaluator-calibration experiment-autopsy decision-record paper-polish-and-audit recsys-toolkit)
C_SKILLS=(requesting-code-review receiving-code-review review-codebase differential-review spec-to-code-compliance security-best-practices jinrong-docs-sync m2-rag-playbook agent-prompt-contracts verify-before-done self-eval-bias evaluator-calibration repo-audit readme-audit)

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

check_one() {
  local name=$1 dest_root=$2
  local src="$SRC/$name" dest="$dest_root/$name"
  if [ ! -f "$src/SKILL.md" ]; then
    echo "DRIFT: source missing: $name (expected $src/SKILL.md)"; return 1
  fi
  if [ ! -d "$dest" ]; then
    echo "DRIFT: not installed: $name -> $dest_root"; return 1
  fi
  if ! diff -rq "$src" "$dest" >/dev/null 2>&1; then
    echo "DRIFT: content differs: $name vs $dest"; return 1
  fi
  return 0
}

if [ "$CHECK_MODE" = "1" ]; then
  DRIFT=0; TOTAL=0
  echo "== --check: repo skills/ vs 两端安装 =="
  for s in "${A_SKILLS[@]}"; do TOTAL=$((TOTAL+1)); check_one "$s" "$HOME/.codex/skills" || DRIFT=$((DRIFT+1)); done
  for s in "${C_SKILLS[@]}"; do TOTAL=$((TOTAL+1)); check_one "$s" "$HOME/.claude/skills" || DRIFT=$((DRIFT+1)); done
  if [ "$DRIFT" = "0" ]; then
    echo "[sync_skills --check] PASS: $TOTAL skill 安装项与 repo 一致"
  else
    echo "[sync_skills --check] FAIL: $DRIFT/$TOTAL 项漂移 (上方 DRIFT 行)"
    exit 1
  fi
  exit 0
fi

echo "== Loop A (Codex CLI) -> ~/.codex/skills =="
for s in "${A_SKILLS[@]}"; do sync_one "$s" "$HOME/.codex/skills"; done

echo "== Loop C (Claude Code) -> ~/.claude/skills =="
for s in "${C_SKILLS[@]}"; do sync_one "$s" "$HOME/.claude/skills"; done

echo "== manifest =="
echo "[~/.codex/skills]"; ls "$HOME/.codex/skills" 2>/dev/null
echo "[~/.claude/skills]"; ls "$HOME/.claude/skills" 2>/dev/null
echo "DONE"
