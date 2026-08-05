# memory/STATE.md — 当前快照（覆写式）| 快照: 2026-08-06 02:05 | 写入: Loop D（夜间队列 T1-T5 完成: A2 灰度上线）

## 系统状态
- git: 三方对齐, 链: a1943a9 → cf5df3d（RLock 死锁 + 对比路由顺序 + hook 收窄 + 回归测试）→ a9ddfc4（trust_env 代理修复）→ 本检查点 commit
- 模型分工（2026-08-06）: Loop A → deepseek-v4-flash-0731（Token_Plan_Chat, :8100 代理 v3.2, 冒烟 PASS 34s/30.8K tokens）; Loop D 子代理默认 flash; Claude Code/qwen_harness_tools/Loop D 主线程 = max; 回滚标准与命令见 DECISIONS.md
- A2 灰度: M2_OPENCODE_ROUTE=on 已生效; /api/m2/ask route=opencode 验证通过（18s/70s 两轮带引用; 已知限制: agent sources JSON 遵从度不稳定）; 回滚演练实测 23s（B4 ≤30s PASS）; 对比类查询绕过 opencode 走进程内规则对比
- 服务: :8004/:8005（LM Studio）up; :5050 up（embedding provider=local 137 chunks）; :4096 opencode-serve up; :8100 代理 v3.2 up; docker zhikuncode + pgvector_15432
- 质量: pytest 254 passed / 14 skipped; RAG QA 15/15（进程内 + :5050 端 OCR meta-query 复验）
- L5 hook: 已收窄（tests/test_m1_service.py + docs/m1_schema/ + frozen_hashes.txt + manifest 路径）, 入库 scripts/graph/hooks/pre-commit; 新单测不再需要 --no-verify
- tmux: coding-jinrong（codex-idle + m1harness）/ graph-loop-b / opencode-serve; 盘点 docs/experiments/2026-08-06_tmux_inventory.md; GB10 skill 分发漂移（2 个 SKILL.md 缺失）已重跑 sync 修复
- 红线: 冻结节点零触碰（md5 复算一致）; API key / 72B 未碰; Loop B 未扰动（其 01:36 FAIL 为 :5050 死锁期准确报警, 下轮自愈）

## 下一步（闸门顺序）
1. Loop C 审计: Loop A（flash）首个正式任务 diff + 今夜 cf5df3d/a9ddfc4 三修复（用户明示）
2. B4 对等验收（docs/25 §4.2; 条目 3 前置 = supervisord 增配 [program:opencode-serve]）
3. B 阶段不启动, 等甲方/用户拍板; 已知改进项: m2-qa FORMAT_HINT 遵从度, opencode serve 口令, tat-dqa train zip 重试下载

## 台账规则
- gap/遗留项台账唯一存放于 memory/THREADS.md, 其他文档只引用不复述
- STATE/THREADS 的 "已 X" 断言以 dispatch_log 验证条目时间戳为准回写（漂移案例 3 教训, 见 DECISIONS.md）
