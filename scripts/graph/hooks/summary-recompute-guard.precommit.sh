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
deleted=$(git -c core.quotepath=false diff --cached --name-only --no-renames --diff-filter=D -- "*.md")
if [ -n "$deleted" ]; then
  echo "[summary-guard] NOTE 本次提交删除/移走以下 .md (其收据不再受复核; 受保护文件由 L5 冻结守卫拦截):"
  printf '%s\n' "$deleted" | sed 's/^/[summary-guard]   - /'
fi

for f in $staged; do
  # T4's *_mismatch.md files are intentional negative fixtures. The checker
  # must still reject them when invoked directly, but pre-commit must not treat
  # a correctly detected mismatch as a real summary defect.
  case "$f" in
    research/harness_rsi_v1/runs/*/fixtures/summary/*_mismatch.md)
      echo "[summary-guard] NOTE skip intentional mismatch fixture: $f"
      continue ;;
  esac
  if ! git cat-file -e ":$f" 2>/dev/null; then
    echo "[summary-guard] WARN 无法读取 $f 的 staged blob, 本项未复核 (跳过不等于通过)"
    continue
  fi
  # RW-2 修复 (2026-09-12, 侧线验收 RW-2; 严重度高于 RW-1): 直接对 staged blob 的**原始字节流** grep,
  # 去掉旧实现里 python 解码/重编码这一道。旧行为 =
  #   content=$(git show ":$f" | "$PY" -c "...sys.stdout.write(stdin.buffer.read().decode(utf-8,replace))" 2>/dev/null)
  # 在 Windows 上 python 的 stdout 编码是 gbk/cp936, 文件含 gbk 不可编码字符 (如 U+2717 / U+21D2)
  # 即抛 UnicodeEncodeError, 而该异常被行尾的 2>/dev/null 吞掉 => content 捕获 **0 字符** =>
  # 下面的 grep 无从匹配 => guard check **根本不执行** => **静默放行且零输出 (fail-open)**,
  # 直接违反本钩子自述的「跳过不等于通过」。实测 (git 自带 bash 跑同一条管线, memory/THREADS.md):
  #   不设 PYTHONUTF8 -> stdout.encoding=gbk / content_chars=0 / stderr 187 B
  #                       (UnicodeEncodeError: 'gbk' codec ... position 31572) / grep NO -> 静默跳过
  #   设 PYTHONUTF8=1 -> stdout.encoding=utf-8 / content_chars=227300 / stderr 0 B / grep MATCH -> guard RUNS
  # => 守卫是否生效竟取决于提交者 shell 里一个无人声明的环境变量。字节流 grep 不经任何编解码,
  #    故与 locale / PYTHONUTF8 / 平台无关 (GB10 与 Windows 行为一致)。
  # **不变量 (RW-2, 硬要求)**: blob 非空而取到的内容为空 = 必须 WARN, 绝不静默跳过。
  blob_size=$(git --no-pager show ":$f" 2>/dev/null | wc -c | tr -d "[:space:]")
  case "$blob_size" in
    ""|*[!0-9]*)
      echo "[summary-guard] WARN $f 的 staged blob 字节数无法测定 (取到: ${blob_size:-<空>}), 本项未复核 (跳过不等于通过)"
      continue ;;
  esac
  if [ "$blob_size" -eq 0 ]; then
    echo "[summary-guard] WARN $f 的 staged blob 取出为 0 字节 (但 cat-file 报其存在), 本项未复核 (跳过不等于通过)"
    continue
  fi
  if git --no-pager show ":$f" | grep -aq "SUMMARY-GUARD"; then
    "$PY" "$GUARD" check "$f" --staged --warn-missing || rc=1
  elif echo "$f" | grep -q "^docs/experiments/" && echo "$f" | grep -Eq "(report|window|汇报|decision|spot)"; then
    # 报告型文档: 引用本地存在的工件 json 却无收据 = WARN
    refs=$(git --no-pager show ":$f" | grep -aoE "logs/graph/eval/[A-Za-z0-9_.-]+\.json" | sort -u)
    for r in $refs; do
      if [ -f "$ROOT/$r" ]; then
        echo "[summary-guard] WARN: $f 引用工件 $r 但无 SUMMARY-GUARD 收据块 (建议: python3 scripts/graph/hooks/summary_recompute_guard.py gen $r <claim=value>...)"
      fi
    done
  fi
done
exit $rc
