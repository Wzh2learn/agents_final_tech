#!/bin/bash
# summary-recompute-guard.precommit.sh — Hook Escalation Ladder 第 3 次触发上机械强制
# (声明摘要 ≠ 存储工件 三连: f1bf00b / 36ab25f / d4e749a)。
# 规则: staged .md 内凡含 SUMMARY-GUARD 收据块, 必须重读工件复算通过才可提交;
#       报告型文档引用本地存在的 logs/graph/eval/*.json 而无收据块 -> WARN (暂不阻断)。
# 降级原则: python 缺失 -> 警告放行 (不无声 fail-open)。
#
# F02 修复 (2026-09-10, Loop A / TASK-20260910-A4A5A4W):
#  1. 校验对象 = **staged blob** (git show :<path>), 不再是工作树文件。旧实现读工作树 =>
#     「工作树干净、index 里是缺陷件」可绕过守卫 (staged 与工作树对象漂移)。
#  2. --no-renames: 重命名拆成 D + A, 使「把带收据的 .md 改名走」不再隐身。
#  3. 删除/移走的 .md 显式告警, 不再用 `[ -f "$f" ] || continue` 静默消失。
#  4. staged blob 不可读 = 显式 WARN「未复核」, 不静默跳过 (跳过不等于通过)。
ROOT=$(git rev-parse --show-toplevel)
PY=""
for cand in python3 python py; do
  command -v "$cand" >/dev/null 2>&1 || continue
  # WindowsApps store 存根会静默失败: 必须实跑探测才算可用
  if "$cand" -c "import sys" >/dev/null 2>&1; then PY="$cand"; break; fi
done
if [ -z "$PY" ]; then
  echo "[summary-guard] WARN: python 不可用, 收据复核跳过 (降级放行)"
  exit 0
fi
rc=0
GUARD="$ROOT/scripts/graph/hooks/summary_recompute_guard.py"

staged=$(git -c core.quotepath=false diff --cached --name-only --no-renames --diff-filter=ACM -- "*.md")
deleted=$(git diff --cached --name-only --no-renames --diff-filter=D -- "*.md")
if [ -n "$deleted" ]; then
  echo "[summary-guard] NOTE 本次提交删除/移走以下 .md (其收据不再受复核; 受保护文件由 L5 冻结守卫拦截):"
  printf '%s\n' "$deleted" | sed 's/^/[summary-guard]   - /'
fi

for f in $staged; do
  if ! git cat-file -e ":$f" 2>/dev/null; then
    echo "[summary-guard] WARN 无法读取 $f 的 staged blob, 本项未复核 (跳过不等于通过)"
    continue
  fi
  content=$(git --no-pager show ":$f" | "$PY" -c "import sys; sys.stdout.write(sys.stdin.buffer.read().decode('utf-8','replace'))" 2>/dev/null)
  if printf '%s' "$content" | grep -q "SUMMARY-GUARD"; then
    "$PY" "$GUARD" check "$f" --staged --warn-missing || rc=1
  elif echo "$f" | grep -q "^docs/experiments/" && echo "$f" | grep -Eq "(report|window|汇报|decision|spot)"; then
    # 报告型文档: 引用本地存在的工件 json 却无收据 = WARN
    refs=$(printf '%s' "$content" | grep -oE "logs/graph/eval/[A-Za-z0-9_.-]+\.json" | sort -u)
    for r in $refs; do
      if [ -f "$ROOT/$r" ]; then
        echo "[summary-guard] WARN: $f 引用工件 $r 但无 SUMMARY-GUARD 收据块 (建议: python3 scripts/graph/hooks/summary_recompute_guard.py gen $r <claim=value>...)"
      fi
    done
  fi
done
exit $rc
