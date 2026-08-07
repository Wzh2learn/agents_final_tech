# memory/STATE.md — 现状快照（唯一现状信源）

> 覆写: 2026-08-07 ~23:59 CST (用户批复四项执行完毕; 08-07 夜盘点收口后守护)

## 模式
守护模式 (2h 盘点 loop 已完成; 等待用户下一步指令)。

## Git
- HEAD: 见 git log (本地/远端/GitHub 三方对齐); 昨夜以来关键 commit: c5a8ecf (审计闭环 F1-F6) → 912099d (differential ACCEPTED + agent-prompt-contracts skill) → 9bc0f93 (文档漂移修复 15/15 口径) → 本轮盘点 commit。
- 审计状态: Loop C 双 ACCEPTED (T1 复核 + T2 differential 4a151dd..HEAD, 33 findings: 0 CRITICAL / 1 HIGH[E1 已闭环] / 8 MEDIUM)。

## 服务
- :5050 FastAPI (08-07 00:23 重启, 已载入 c5a8ecf PG 超时加固): overall=healthy, embeddings=137, embedding provider=local (qwen3-embedding-0.6b CPU), M2_OPENCODE_ROUTE=on + OPENCODE_ASK_TIMEOUT=18
- :4096 OpenCode sidecar (tmux opencode-serve), MCP 三件套为其 stdio 子进程
- :8004 Qwen3.6-35B (4 slots) / :8005 14B / :8100 responses2chat proxy v3.2
- docker: zhikuncode + pgvector_15432
- Loop A (codex CLI): deepseek-v4-flash-0731 via Token_Plan_Chat; Loop C: qwen3.8-max 全槽位 (claude -p 需 --dangerously-skip-permissions)

## 质量基线
- pytest: 266 passed / 13 skipped / 0 failed (2026-08-07 01:10 复跑)
- RAG QA: 15/15 (两口径: rerank=False 08-05 + 生产 force_rerank=True 08-07 复验)
- demo.sh: 6 步全绿 (08-07 01:00 实跑)
- Loop B: PASS 00:36 (30min 周期)
- 冻结节点: tests/test_m1_service.py md5 faa7565a 完好

## 演示就绪
GO (条件): 正式演示前建议关 M2_OPENCODE_ROUTE 切直连 (~2s/轮, 回滚 23s 实测); agent 路保留则按 docs/23 附录 C 话术解释 15-20s 延迟。

## 下一步（需人工）
- **docs/23 发送甲方 = 当前唯一人工阻塞项**（等用户审阅 docs/23_甲方阶段汇报_发送版.docx 后发送）。
- B4 观察时钟随之启动：灰度数据积累 ≥100 次 ask / ≥3 天，门槛见 docs/25 §4.3（目标 ~08-11）。

## 待办（唯一台账 → memory/THREADS.md）
E4 一行修 / P1-P3 随手修 / 会话 delete-list 断言缺口 / :5050 重启后 PG 超时已生效无需再启 / opencode_m1_extract.sh 封装待批 / Loop C MCP 接线观望 / B4 灰度数据积累中 (目标 ~08-11)
