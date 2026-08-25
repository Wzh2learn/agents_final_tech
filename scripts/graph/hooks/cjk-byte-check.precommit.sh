#!/bin/bash
# pre-commit: cjk-byte-check
# 移植自 skills-loop-engineering@7ffbe44 hooks/cjk-byte-check.sh (Claude Code PreToolUse → git pre-commit 形态)
# 规则: staged 变更的 .md 文件做 U+FFFD 替换符扫描 (edit 工具链 CJK 编码副作用; 源仓库三次实证)
# 降级原则: python3 不可用或解析失败时警告放行, 不无声 fail-open
# 注意: U+FFFD 必须用 chr(0xFFFD) 显式构造——直接输入该字符会被传输链吞掉导致空串误报
if ! command -v python3 >/dev/null 2>&1; then
  echo "[pre-commit:cjk-byte-check] ⚠️ 守卫降级: python3 不可用, 本次放行" >&2
  exit 0
fi
MD_FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null | grep -E '\.md$')
[ -z "$MD_FILES" ] && exit 0
BAD=$(echo "$MD_FILES" | python3 -c "
import sys
REPL = chr(0xFFFD)
bad = []
for line in sys.stdin:
    f = line.strip()
    if not f:
        continue
    try:
        s = open(f, encoding='utf-8').read()
    except Exception:
        continue
    n = s.count(REPL)
    if n:
        bad.append(f'{f}（{n} 处）')
print('\n'.join(bad))
")
if [ -n "$BAD" ]; then
  echo "[pre-commit:cjk-byte-check] 拦截: staged Markdown 含 U+FFFD 替换符:" >&2
  echo "$BAD" | sed 's/^/  - /' >&2
  echo "请修复乱码后再提交。" >&2
  exit 1
fi
exit 0
