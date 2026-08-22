#!/usr/bin/env bash
# scripts/sidecar_launch.sh — opencode 侧车启动/恢复启动器
# (仓库资产化 2026-08-22 夜间审计; 原 /tmp/sidecar_launch.sh, 内容照搬)
#
# 用途: 侧车重启与 opencode.db 恢复 SOP (dispatch #SIDECAR-DB-REBUILD) 的唯一
#       执行入口。/tmp 重启即失, 故入库定型。
# 用法: bash scripts/sidecar_launch.sh
#       (前台 exec; 建议置于 tmux 窗口内运行以便观察日志)
# 依赖: ~/.sidecar_env.bin — env 快照 (chmod 600, 含 API key, 不打印/不入 git,
#       与 logs/graph/eval/sidecar_restart_archive_0822.txt 配对存档)
# 修复点: 必须用 mapfile 重建 env 数组; xargs -0 -a F env -i CMD 会把变量追加到
#         CMD 参数尾部, yargs 收到未知位置参量 → 打 help 退出 (2026-08-22 实测坐实)
mapfile -d "" -t VARS < /home/testuser/.sidecar_env.bin
cd /home/testuser/wzh/projects/agents_final_tech
exec env -i "${VARS[@]}" /home/testuser/.opencode/bin/opencode serve --port 4096
