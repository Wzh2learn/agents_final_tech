# memory/STATE.md
更新: 2026-08-12 深夜（"已发送"信号 → S1/S2 完成）

## 模式
守护模式 + 队列执行中。**docs/23 已发送甲方（2026-08-12, 用户亲发）; B4 观察时钟启动**（≥100 asks / ≥3 天）。队列: S3①→⑤ 执行中; 缓至甲方反馈: 任务二 B 一期/场景 B/_cleanup_backup 删除/Qoder PAT。

## Git
- HEAD: 本 commit（S1/S2 入账）; 链: 9d4f545(台账更正) → cab17b9(S1+S2 载入件) → d8504fb(warm-up 修正) → 本 commit
- 三方对齐（GB10 push → GitHub → 本机 fetch+merge）

## S1/S2 战绩（2026-08-12 夜）
- S1① THREADS/STATE 记"已发送+B4 时钟"; S1② /api/m2/ask JSONL 仪表上线; S1③ status.sh 一页健康上线（三方/Loop B/端口/B4/dispatch/冻结/docs_lint 全段 PASS）
- S2 载入: 延迟 a(warm-up 真实检索题, 冷路 45s 预付) + b(/no_think 契约 C-1) + Q2 别名链 + 批 A 加固 + vision roots
- 六步验证全过; agent 路 warm 实测 13.5s 成功/多检索题 >18s 回落(如实记账, 根因入 A2 遗留)
- 回滚演练 kill→health200 实测 10s（≤30s 达标）; pytest 330 passed/13 skipped; docs_lint 0/0

## 服务
- :5050 UP（route=on, provider=local, embeddings=137, tmux coding-jinrong:api5050, PYTHONPATH=src）
- :4096 sidecar UP（16 skills, warm-up 已跑）; :8004/:8005/:8100/:15432 UP; :8007 down
- Loop B 23:38 PASS head=d8504fb; tmux 禁杀 graph-loop-b/opencode-serve

## 质量基线
- pytest 330 passed / 13 skipped; docs_lint 五项 0/0; 冻结节点 PASS; docx bc3785cb 已发送（冻结解除于发送时）
- eval 基线 (21:57): 确定性 16/16 / NF 0/9 fail / judge 4.94/5.0/5.0/5.0
- agent 路延迟: 13.5s best / 成功率 1/4（a+b 后, 待 A2 稳态化）; 直连 warm 2.7-3s

## 下一步（队列中）
1. S3① docs/28 #2 数值 claim 核验产品化 → ② dify 5 docx synonyms 挖掘 → ③ #1 检索透明面板 → ④ #4 Docling 探针（独立 venv）→ ⑤ :8005 judge 分流 flag（每项前后回归门禁 + eval 对比）
2. B4 积累中（当前 asks 见 status.sh）; eval 每天经生产端点跑一遍
3. 缓至甲方首轮反馈: 任务二 B 一期 / 场景 B / 备份目录删除; Qoder 等 PAT
