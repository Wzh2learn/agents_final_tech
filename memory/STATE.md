# memory/STATE.md — 现状快照（唯一现状信源）

> 覆写: 2026-08-08 ~01:35 CST (P10 hook 实测闭环 + VLM :8007 重试结论)

## 模式
守护模式（等待用户下一步指令）。

## Git
- HEAD: 257f5cf（本地 = 远端 = GitHub 三方对齐）
- 今夜关键 commit: 257f5cf = pre-commit md5 守护实测通过 + graph-loop-rules 冻结口径更正 + pytest 基线 275

## 服务
- :5050 FastAPI（08-07 重启, PG 超时加固 c5a8ecf 已载入）: overall=healthy, embeddings=137, provider=local (qwen3-embedding-0.6b CPU), M2_OPENCODE_ROUTE=on + OPENCODE_ASK_TIMEOUT=18
- :4096 OpenCode sidecar（tmux opencode-serve, PID 1644919）, MCP 三件套为其 stdio 子进程
- :8004 Qwen3.6-35B（4 slots）/ :8005 14B / :8100 responses2chat proxy v3.2（PID 1679516）
- :8007 VLM **未运行**（08-08 验证完毕已 kill；结论与重启方法见 THREADS.md）
- docker: zhikuncode + pgvector_15432
- Loop A: deepseek-v4-flash-0731 via Token_Plan_Chat；Loop C: qwen3.8-max 全槽位（claude -p 需 --dangerously-skip-permissions）
- Loop B: PASS 00:36（30min 周期, graph-loop-b tmux 常驻）

## 质量基线
- pytest: 275 passed / 13 skipped / 0 failed（2026-08-08 00:51 实测）
- RAG QA: 15/15（两口径: rerank=False 08-05 + 生产 force_rerank=True 08-07）
- demo.sh: 6 步全绿（08-07）
- 冻结节点: test_m1_service.py md5 faa7565a 完好；运行时 schema md5 73d4f46e 完好（commit 钩子实测: 篡改 rc=1 拦截 / 恢复 rc=0）
- scenario1 OCR 样本现状（08-08 重跑）: NCAMC 1 表 4/8（坐标重建, 无 OCR）/ 华泰紫金 1 表 5/14（vision-8004）/ TraFax 3 表 2/4;8/11;4/11 / WaveFax 1 表 4/7（后两者 vlm-8007 与 vision-8004 命中率持平）

## 演示就绪
GO（条件）: 正式演示前建议关 M2_OPENCODE_ROUTE 切直连（~2s/轮, 回滚 23s 实测）；agent 路保留则按 docs/23 附录 C 话术解释 15-20s 延迟。

## 下一步（需人工）
- **docs/23 发送甲方 = 当前唯一人工阻塞项**（发送版 docx 已按 15/15 口径重生成, 等用户审阅后发送）。
- B4 观察时钟: 灰度数据积累 ≥100 次 ask / ≥3 天（目标 ~08-11）。

## 待办（唯一台账 → memory/THREADS.md）
见 THREADS.md（含: Loop C MCP 接线观望 / B4 灰度数据积累 / VLM 降采样优化候选 / 会话 delete-list 断言缺口）。
