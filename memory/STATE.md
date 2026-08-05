# memory/STATE.md — 当前快照（覆写式）| 快照: 2026-08-06 00:52 | 写入: Loop D（模型分工调整: Loop A → deepseek-v4-flash-0731）

## 系统状态
- git: 三方对齐（本机 / GB10 / GitHub），链: a438f0d A1 → 6787509 skill sync → 04477ab OCR meta 修复 → 9f3e655 doctype 测试 → dcbe5fb 审计报告 → 7da6d6f 审计闭环 → ad56ae2 proxy v3.2 → 5fb8460 DECISIONS 分工记录
- 模型分工（2026-08-06 00:17 生效）: Loop A → deepseek-v4-flash-0731（Token_Plan_Chat, 经 :8100 responses2chat 代理 v3.2）; Loop D 子代理默认 flash, 集成 review/多模态用 qwen3.8-max; Claude Code 全槽位 / qwen_harness_tools.py / Loop D 主线程不动（max）。冒烟 PASS: codex exec 两数之和 34s / 30.8K tokens（缓存 14.3K）, exec_command round-trip 成立, reasoning_tokens=0。回滚标准与命令见 DECISIONS.md [2026-08-06] 条
- 服务: :8004 up; :5050 up（23:09 重启, 本地 embedding provider=local, 137 chunks, 非 fallback）; :4096 opencode-serve up（tmux）; :8100 代理 v3.2 up（PID 106381, PROXY_DEBUG=1 → /tmp/proxy_debug.log）; docker zhikuncode + pgvector
- RAG QA: **15/15 = 100%**（OCR meta-query RESOLVED, Loop B 独立复验 04477ab）; pytest: **251 passed / 13 skipped**
- A1 完成: opencode_adapter + M2_OPENCODE_ROUTE 开关（默认 off）+ 会话清理, 9 单测, 存量 sidecar 会话已清零; A2 待办: 等用户确认 :5050 重启窗口 → 开关打开 → 冒烟 + OCR meta-query :5050 端复验
- 彩排: 8/8 全绿, 0 JS 错误, 0 演示前必修项（docs/experiments/2026-08-05_rehearsal_post_embedding/）
- Skill 武库: m1-gap-triage + graph-loop-rules 已分发 GB10, 注册表补齐（6787509）
- 红线: 冻结节点零触碰（test_m1_service.py md5 faa7565a 复算一致）/ API key / 72B 未碰; Loop B 未扰动; B 阶段未启动

## 下一步（闸门顺序）
1. 用户确认 :5050 重启窗口 → A2 开关打开 → 冒烟 + OCR meta-query :5050 端复验
2. Loop A（flash）首个正式任务完成 → Loop C 重点审计该 diff（用户明示）
3. B4 对等验收（清单 docs/25 §4.2; 条目 3 前置 = supervisord 增配 [program:opencode-serve]）
4. B 阶段不启动, 等甲方/用户拍板

## 台账规则
- gap/遗留项台账唯一存放于 memory/THREADS.md, 其他文档只引用不复述
- STATE/THREADS 的 "已 X" 断言以 dispatch_log 验证条目时间戳为准回写（漂移案例 3 教训, 见 DECISIONS.md）