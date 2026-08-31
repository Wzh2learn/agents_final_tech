#!/bin/bash
# summary-recompute-guard.precommit.sh — Hook Escalation Ladder 第 3 次触发上机械强制
# (声明摘要 ≠ 存储工件 三连: f1bf00b / 36ab25f / d4e749a)。
# 规则: staged .md 内凡含 SUMMARY-GUARD 收据块, 必须重读工件复算通过才可提交;
#       报告型文档引用本地存在的 logs/graph/eval/*.json 而无收据块 -> WARN (暂不阻断)。
# 降级原则: python 缺失 -> 警告放行 (不无声 fail-open)。
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
staged=$(git diff --cached --name-only --diff-filter=ACM -- "*.md")
for f in $staged; do
  [ -f "$f" ] || continue
  if grep -q "SUMMARY-GUARD" "$f"; then
    "$PY" "$ROOT/scripts/graph/hooks/summary_recompute_guard.py" check "$f" --warn-missing || rc=1
  elif echo "$f" | grep -q "^docs/experiments/" && echo "$f" | grep -Eq "(report|window|汇报|decision|spot)"; then
    # 报告型文档: 引用本地存在的工件 json 却无收据 = WARN
    refs=$(grep -oE "logs/graph/eval/[A-Za-z0-9_.-]+\.json" "$f" | sort -u)
    for r in $refs; do
      if [ -f "$ROOT/$r" ]; then
        echo "[summary-guard] WARN: $f 引用工件 $r 但无 SUMMARY-GUARD 收据块 (建议: python3 scripts/graph/hooks/summary_recompute_guard.py gen $r <claim=value>...)"
      fi
    done
  fi
done
exit $rc