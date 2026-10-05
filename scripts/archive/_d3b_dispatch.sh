#!/usr/bin/env bash
set -e
cd ~/wzh/projects/agents_final_tech
echo "---PULL---"
git pull --no-rebase origin main 2>&1 | tail -1
git log --oneline -1
echo "---DISPATCH---"
tmux new-session -d -s loop-a-d3b 'cd ~/wzh/projects/agents_final_tech && source ~/.bashrc && { cat scripts/graph/loop_a_exec_constraints.md; cat docs/experiments/2026-09-01_d3_matched_specificity_card.md; echo; echo "【Loop D 派发指令 2026-09-06 13:5x · 阶段 B judge 窗】本次派发范围 = 仅阶段 B（卡加编 2 + 澄清节 + 加编 3 C3-1..C3-6 = 测量契约, 零现场定义空间）; 阶段 A 已交付（51cbed9 + 加编 1 口径）, 禁止重跑阶段 A 分析。执行要点: 前置断言 C3-1 五条任一失败即停报; canary 1 次推理探针计数, 异常即停; 28 调用 = J-N1 21 + J-N2 7, J-N3 零调用; ≤200 硬门（计数器 + JSONL 实时落）; 仅 :8004, :8006 零触碰; judge prompt 防泄漏白黑名单; invalid 字节相同 payload 重试 1 次, 不填补; 本窗只收集 + 确定性聚合, 结论判定归 Loop D。产出 = logs/graph/eval/d3_matched_fpr_stage_b.json + 报告 docs/experiments/2026-09-06_d3_matched_fpr_stage_b.md（SUMMARY-GUARD 收据）+ THREADS 记账 + commit（逐路径, 禁 -A 禁 amend）+ push（若 origin 领先先 pull --no-rebase 再 push）。大工件按需读键段, 禁全量复读; 增量写脚本。"; } | codex exec --dangerously-bypass-approvals-and-sandbox --profile loopa-exec 2>&1 | tee -a logs/graph/loop_a.log'
sleep 3
tmux has-session -t '=loop-a-d3b' && echo SESSION_UP
echo "---CRON---"
(crontab -l 2>/dev/null | grep -v d3b_watcher; echo '*/5 * * * * /tmp/d3b_watcher.sh') | crontab -
crontab -l | grep d3b_watcher
date '+%F %T %Z'
