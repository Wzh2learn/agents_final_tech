#!/bin/bash
# pre-commit: index-guard
# 移植自 skills-loop-engineering@7ffbe44 hooks/readme-index-guard.sh (README 口径 → docs/INDEX.md 口径)
# 规则: staged 新增的 scripts/**/*.py|sh 必须在 docs/INDEX.md 有索引行
# 源仓库七次"打地鼠"实证; 对应本项目既有纪律 "INDEX 最后更新与内容变更必须同 commit"
NEW_FILES=$(git diff --cached --diff-filter=A --name-only 2>/dev/null | grep -E '^scripts/.*\.(py|sh)$')
[ -z "$NEW_FILES" ] && exit 0
MISSING=""
for f in $NEW_FILES; do
  base=$(basename "$f")
  if ! grep -qF "$base" docs/INDEX.md 2>/dev/null; then
    MISSING="$MISSING $f"
  fi
done
if [ -n "$MISSING" ]; then
  echo "[pre-commit:index-guard] 拦截: 新增脚本未在 docs/INDEX.md 索引:" >&2
  for f in $MISSING; do echo "  - $f" >&2; done
  echo "请先在 docs/INDEX.md 补索引行再提交。" >&2
  exit 1
fi
exit 0
