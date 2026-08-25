#!/usr/bin/env bash
# cron 闸语义助手 (2026-08-25, E1a 缺陷修复固化):
# 闸不达标 = 改期 (至多 N 次), 禁止 SKIP。改期耗尽 = BLOCKED 标记 + 台账, 仍不静默。
# 案例: 08-25 01:50 W4 闸撞 W3 eval 收尾 → SKIP → W5 连环 abort (教训条目 #E1-DEFECTS)。
#
# 用法 (在 cron one-shot 脚本顶部):
#   source scripts/graph/cron_gate_helper.sh
#   cron_gate "W4" "[ -f /tmp/w3_done.txt ] && [ \"\$(cat /tmp/w3_done.txt)\" = EVAL_PASS ]" \
#             2 "+10 minutes" "bash /tmp/w4_xxx.sh >> /tmp/w4_cron.log 2>&1" \
#             /tmp/w4_blocked.txt logs/graph/eval/w4_artifact.md
# 返回: 0=闸过(继续执行) 1=已改期(调用方 exit 0) 2=已 BLOCKED(调用方 exit 0)
cron_gate() {
  local name="$1" cond="$2" max="$3" interval="$4" selfline="$5" marker="$6" log="$7"
  if bash -c "$cond"; then return 0; fi
  local arms_file="/tmp/cron_gate_arms_${name}"
  local arms=$(cat "$arms_file" 2>/dev/null || echo 0)
  if [ "$arms" -lt "$max" ]; then
    echo $((arms+1)) > "$arms_file"
    local next=$(date -d "$interval" '+%M %H %d %m')
    local key=$(echo "$selfline" | awk '{print $2}')   # 脚本路径 = 自删键 (grep -vF 空串会清空 crontab, E1a 回归捕获)
    (crontab -l 2>/dev/null | grep -vF "$key"; echo "$next * $selfline") | crontab -
    echo "[$name] gate 未达标 -> 改期 $next (第 $((arms+1))/$max 次, 禁 SKIP)" | tee -a "$log"
    return 1
  fi
  echo "BLOCKED $name $(date '+%F %T'): gate $max 次改期仍未过" > "$marker"
  echo "[$name] gate BLOCKED ($max 次改期耗尽) $(date '+%F %T')" | tee -a "$log"
  return 2
}
