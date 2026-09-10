#!/usr/bin/env bash
# dispatch_precheck.sh — 常备派发前置检查: watcher「双实证」机械化 (A4w 剩余范围, 2026-09-10)
#
# 为什么存在 (F-0907-1 教训的常备化):
#   「挂了 crontab ≠ 观察器在跑」。09-07 那次静默失败的成因是两条同时成立——
#   ① 脚本没有执行位, ② crontab 直呼脚本路径 (没有显式解释器) —— 于是 cron 每次都失败,
#   而没有人看见。D4 卡 BG-7 已把「执行位实证 + 首次 tick 实证, 缺一不派发」写进那一窗;
#   本脚本把同一条要求变成**所有后续窗口都能直接调用**的检查, 不再逐窗重写 (决策 17=A 批准)。
#
# 语义: 只读取证, 绝不安装/修改 cron, 绝不写仓库工件, 绝不碰 /tmp 下的既有现场。
#   任一 FAIL -> 退出码非零 (派发方必须停下, 不得带假设硬跑)。
set -uo pipefail

rc=0
watchers=(); tick_markers=(); cron_lines=(); max_age=0
while [ $# -gt 0 ]; do
  case "$1" in
    --watcher)     watchers+=("$2"); shift 2 ;;
    --tick-marker) tick_markers+=("$2"); shift 2 ;;
    --cron-line)   cron_lines+=("$2"); shift 2 ;;
    --max-tick-age-min) max_age="$2"; shift 2 ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown arg: $1 (see --help)"; exit 64 ;;
  esac
done

if [ ${#watchers[@]} -eq 0 ] && [ ${#tick_markers[@]} -eq 0 ] && [ ${#cron_lines[@]} -eq 0 ]; then
  echo "用法: dispatch_precheck.sh --watcher PATH [--watcher PATH ...] \\"
  echo "                            [--cron-line '5 3 * * * /path/x.sh >> log 2>&1'] \\"
  echo "                            --tick-marker PATH [--max-tick-age-min N]"
  echo
  echo "本脚本是**常备**派发前置检查: 任何装了 cron/one-shot 观察器的任务卡, 派发前必须跑它并"
  echo "把输出逐字入卡 (§8 执行节奏纪律 / 模板 §8「watcher 双实证」条)。零参数 = 只打印用法, 不产生证据。"
  exit 64
fi

pass() { echo "  PASS  $*"; }
fail() { echo "  FAIL  $*"; rc=1; }

echo "=== A4w 派发前置: 双实证机械检查 $(date '+%F %T %Z') ==="

# ---- 实证一: 执行位 (含语法可执行性) ----
for w in "${watchers[@]:-}"; do
  [ -n "$w" ] || continue
  echo "[watcher] $w"
  if [ ! -e "$w" ]; then fail "脚本不存在 (注册了 cron 却没有脚本 = 静默失败的第一种形态)"
  elif [ ! -f "$w" ]; then fail "不是普通文件"
  else
    [ -x "$w" ] || fail "缺执行位 (F-0907-1 成因 ①): chmod +x $w 之前不得派发"
    if bash -n "$w" 2>/dev/null; then pass "bash -n 语法合法"; else fail "bash -n 不通过 (cron 会立刻退出)"
    fi
    [ -s "$w" ] || fail "脚本为空文件 (0 字节 = 没有内容可跑)"
    echo "        mode=$(stat -c '%A' "$w" 2>/dev/null || stat -f '%Sp' "$w")  sha256=$(sha256sum "$w" | cut -c1-16)  bytes=$(stat -c '%s' "$w" 2>/dev/null || stat -f '%z' "$w")"
  fi
done

# ---- 实证一之二: cron 行的调用姿势 ----
for cl in "${cron_lines[@]:-}"; do
  [ -n "$cl" ] || continue
  echo "[cron-line] $cl"
  target=$(printf '%s' "$cl" | awk '{ for (i=1; i<=NF; i++) if ($i ~ /^\//) { print $i; exit } }')
  if [ -z "$target" ]; then
    fail "cron 行里找不到绝对路径目标 (无法核验)"
    continue
  fi
  case "$cl" in
    *" bash $target"*|*"bash  "*"$target"*|*"/bin/bash $target"*|*"/bin/sh $target"*)
      pass "显式解释器调用 $target (不依赖执行位)" ;;
    *)
      if [ -e "$target" ] && [ ! -x "$target" ]; then
        fail "F-0907-1 复现条件成立: cron 直呼 $target 且该文件无执行位 => 每次静默失败"
      else
        pass "直呼路径且目标有执行位 (或已不在盘上, 由 --watcher 项单独核验)"
      fi ;;
  esac
  case "$cl" in
    *">>"*|*"2>&1"*) pass "失败信号有落点 (重定向到日志, 事后可核)" ;;
    *) fail "cron 行无任何重定向: 静默失败时连日志都不留 (三件套要求工件路径显式声明)" ;;
  esac
done

# ---- 实证二: 首次 tick 真实发生 ----
now=$(date +%s)
for t in "${tick_markers[@]:-}"; do
  [ -n "$t" ] || continue
  echo "[tick-marker] $t"
  if [ ! -e "$t" ]; then
    fail "首次 tick 工件不存在 = 观察器从未真正跑过 (注册 != 执行)"
  elif [ ! -s "$t" ]; then
    fail "tick 工件存在但 0 字节 = 跑了但没产出证据"
  else
    mt=$(stat -c %Y "$t" 2>/dev/null || stat -f %m "$t")
    age=$(( (now - mt) / 60 ))
    echo "        age=${age}min  bytes=$(stat -c '%s' "$t" 2>/dev/null || stat -f '%z' "$t")"
    if [ "$max_age" -gt 0 ] && [ "$age" -gt "$max_age" ]; then
      fail "tick 距今 ${age}min > 上限 ${max_age}min = 观察器疑似已停 (一次性触发已耗尽?)"
    else
      pass "首次 tick 已实证 (age=${age}min)"
    fi
    head -2 "$t" | sed 's/^/        | /'
  fi
done
if [ ${#tick_markers[@]} -eq 0 ]; then
  fail "未提供 --tick-marker: 缺「首次 tick 实证」, 按 BG-7 口径 = 缺一不派发"
fi

echo "=== 结论: $([ $rc -eq 0 ] && echo '双实证齐备, 可派发' || echo '不满足 — 停下修完再派发 (不得带假设硬跑)') ==="
exit $rc
