# memory/STATE.md — 当前快照（覆写式）| 快照: 2026-08-06 00:10 | 写入: Loop D（OCR meta-query 收口 + A1 集成 + Loop C 审计闭环）

## 系统状态
- git: 三方对齐（本机 / GB10 / GitHub），链: a438f0d A1 → 6787509 skill sync 补漏 → 04477ab OCR meta 修复 → dca0bdd 台账 → 9f3e655 doctype 测试 → dcbe5fb 审计报告 → 本收口 commit
- RAG QA: **15/15 = 100%**（OCR meta-query RESOLVED: doc_type 标记 + 过滤召回 + 重排; Loop B 独立复跑 scripts/m1_rag_qa.py 确认 exit 0; 04477ab）
- pytest: **251 passed / 13 skipped**（GB10 rebase 后全量复跑: 242 基线 + 9 adapter）
- 服务: :8004 up; :5050 up（23:09 重启, 本地 embedding 已载入 provider=local, 137 chunks, 非 fallback）; :4096 opencode-serve up（tmux）; docker zhikuncode + pgvector
- A1 完成: src/biz/opencode_adapter.py + M2_OPENCODE_ROUTE 开关（默认 off）+ /api/m2/opencode/cleanup + scripts/opencode_session_cleanup.py, 9 单测; 存量 130 sidecar 会话已清零
- A2 待办: 等用户确认 :5050 重启窗口 → .env 加 M2_OPENCODE_ROUTE=on → 冒烟 + :5050 端 OCR meta-query 复验（进程内旧代码, 重启即生效）
- 彩排: 8/8 全绿, 0 JS 错误, 0 演示前必修项（docs/experiments/2026-08-05_rehearsal_post_embedding/）
- Loop A/C: 本轮任务完成（A session 已回收; C 审计 CONDITIONAL → 3 项闭环全部落地 + 建议实现: DEVICE 缺省 cpu / .env.example LOCAL_EMBEDDING 段 / health/full 暴露 embedding provider）
- Skill 武库: m1-gap-triage + graph-loop-rules 已分发 GB10 ~/.codex/skills; sync_skills.sh A 列表 + AGENTS.md 注册表已补齐（6787509）
- 红线: 冻结节点零触碰（test_m1_service.py md5 faa7565a 独立复算一致）/ API key / 72B 未碰; Loop B 未扰动; B 阶段未启动

## 下一步（闸门顺序）
1. 用户确认 :5050 重启窗口 → A2 开关打开 → 冒烟验证 + OCR meta-query :5050 端复验
2. B4 对等验收（清单见 docs/25 §4.2; 条目 3 前置 = supervisord 增配 [program:opencode-serve]）
3. B 阶段（docs/25 路线 B）不启动, 等甲方/用户拍板

## 台账规则
- gap/遗留项台账唯一存放于 memory/THREADS.md, 其他文档只引用不复述
- STATE/THREADS 的 "已 X" 断言以 dispatch_log 验证条目时间戳为准回写（漂移案例 3 教训, 见 DECISIONS.md）
