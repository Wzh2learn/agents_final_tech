#!/bin/bash
# Graph Engineering - Skill sync (Phase 0)
# Copies repo skills/ (source of truth) to the harness skill dirs on this
# machine. Idempotent: safe to re-run; validates a staged copy before replacing
# an installation, and never touches skills not listed here.
#   Loop A (Codex CLI):   A-list -> ~/.codex/skills/
#   Loop C (Claude Code): C-list -> ~/.claude/skills/
set -euo pipefail

# 用法: sync_skills.sh                         # 同步 (幂等)
#       sync_skills.sh --check                 # 只检查 repo 与两端安装一致性
#       sync_skills.sh --sync-one NAME DEST    # 受控单项同步（也用于测试）
CHECK_MODE=0
case "${1:-}" in
  "") ;;
  --check) CHECK_MODE=1 ;;
  --sync-one) ;;
  *) echo "usage: $0 [--check | --sync-one NAME DEST_ROOT]" >&2; exit 2 ;;
esac

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SRC="${SKILL_SYNC_SOURCE:-$PROJECT_ROOT/skills}"
CODEX_SKILLS_ROOT="${CODEX_SKILLS_ROOT:-$HOME/.codex/skills}"
CLAUDE_SKILLS_ROOT="${CLAUDE_SKILLS_ROOT:-$HOME/.claude/skills}"

A_SKILLS=(systematic-debugging executing-plans subagent-driven-development jinrong-docs-sync m1-gap-triage m2-rag-playbook graph-loop-rules agent-prompt-contracts research-writing-skill office-academic-skill scientific-toolkit-skill verify-before-done shift-notes context-budget tool-restraint spec-first sprint-contract eval-harness experiment-autopsy decision-record paper-polish-and-audit recsys-toolkit paper-review-check algorithm-description neat-freak code-cleanup-helper skill-doctor skill-map agent-rules cloudflare-deploy codebase-map dispatching-parallel-agents figma figma-code-connect-components figma-generate-design figma-generate-library figma-implement-design figma-use jupyter-notebook pdf playwright playwright-interactive security-threat-model skills-best-practices vercel-deploy writing-plans experiment-analysis research-driven-design offline-eval-playbook code-pathology organize-logs train-monitor gpu-env data-sync dependency-audit authz-check input-validation secret-scan init-script-contract progress-reading-protocol harness-stripping structured-output prompt-caching pdf-ingestion planner-spec-expand skill-merger skill-hook-trigger socrates dream-engine exp-lifecycle commit-and-pr-hygiene code-simplification git-history-ops db-schema-change frontend-quality testing-practices)
C_SKILLS=(requesting-code-review receiving-code-review review-codebase differential-review spec-to-code-compliance security-best-practices jinrong-docs-sync m2-rag-playbook agent-prompt-contracts verify-before-done self-eval-bias repo-audit readme-audit paper-review-check audit-cycle owasp-review sql-review feature-list-json subagent-fanout using-loopkit eval-harness)

sync_one() {
  local name=$1 dest_root=$2
  local src="$SRC/$name" dest="$dest_root/$name"
  local staging backup=""
  if [[ ! "$name" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
    echo "INVALID skill name: $name"
    return 2
  fi
  if [ -z "$dest_root" ] || [ "$dest_root" = "/" ]; then
    echo "INVALID destination root: $dest_root"
    return 2
  fi
  if [ ! -f "$src/SKILL.md" ]; then
    echo "MISSING source: $name (expected $src/SKILL.md)"
    return 1
  fi
  mkdir -p "$dest_root"

  staging="$(mktemp -d "$dest_root/.skill-sync-${name}.staging.XXXXXX")"
  if ! cp -a "$src/." "$staging/"; then
    rm -rf -- "$staging"
    echo "FAILED staging copy: $name"
    return 1
  fi
  if [ ! -f "$staging/SKILL.md" ] || ! diff -rq "$src" "$staging" >/dev/null 2>&1; then
    rm -rf -- "$staging"
    echo "FAILED staging validation: $name"
    return 1
  fi
  if [ "${SYNC_SKILLS_FAIL_AFTER_COPY:-}" = "$name" ]; then
    rm -rf -- "$staging"
    echo "FAILED injected failure after validated copy: $name"
    return 1
  fi

  if [ -e "$dest" ] || [ -L "$dest" ]; then
    backup="$(mktemp -d "$dest_root/.skill-sync-${name}.backup.XXXXXX")"
    rmdir "$backup"
    if ! mv "$dest" "$backup"; then
      rm -rf -- "$staging"
      echo "FAILED preserving previous install: $name"
      return 1
    fi
  fi
  if [ "${SYNC_SKILLS_FAIL_AFTER_BACKUP:-}" = "$name" ]; then
    if [ -n "$backup" ]; then
      mv "$backup" "$dest"
    fi
    rm -rf -- "$staging"
    echo "FAILED injected failure after backup: $name"
    return 1
  fi
  if ! mv "$staging" "$dest"; then
    if [ -n "$backup" ]; then
      mv "$backup" "$dest"
    fi
    rm -rf -- "$staging"
    echo "FAILED activating staged install: $name"
    return 1
  fi
  if [ -n "$backup" ]; then
    rm -rf -- "$backup"
  fi
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

if [ "${1:-}" = "--sync-one" ]; then
  if [ "$#" -ne 3 ]; then
    echo "usage: $0 --sync-one NAME DEST_ROOT" >&2
    exit 2
  fi
  sync_one "$2" "$3"
  exit $?
fi

if [ "$CHECK_MODE" = "1" ]; then
  DRIFT=0; TOTAL=0
  echo "== --check: repo skills/ vs 两端安装 =="
  for s in "${A_SKILLS[@]}"; do TOTAL=$((TOTAL+1)); check_one "$s" "$CODEX_SKILLS_ROOT" || DRIFT=$((DRIFT+1)); done
  for s in "${C_SKILLS[@]}"; do TOTAL=$((TOTAL+1)); check_one "$s" "$CLAUDE_SKILLS_ROOT" || DRIFT=$((DRIFT+1)); done
  if [ "$DRIFT" = "0" ]; then
    echo "[sync_skills --check] PASS: $TOTAL skill 安装项与 repo 一致"
  else
    echo "[sync_skills --check] FAIL: $DRIFT/$TOTAL 项漂移 (上方 DRIFT 行)"
    exit 1
  fi
  exit 0
fi

echo "== Loop A (Codex CLI) -> ~/.codex/skills =="
for s in "${A_SKILLS[@]}"; do sync_one "$s" "$CODEX_SKILLS_ROOT"; done

echo "== Loop C (Claude Code) -> ~/.claude/skills =="
for s in "${C_SKILLS[@]}"; do sync_one "$s" "$CLAUDE_SKILLS_ROOT"; done

echo "== manifest =="
echo "[$CODEX_SKILLS_ROOT]"; ls "$CODEX_SKILLS_ROOT" 2>/dev/null
echo "[$CLAUDE_SKILLS_ROOT]"; ls "$CLAUDE_SKILLS_ROOT" 2>/dev/null
echo "DONE"
