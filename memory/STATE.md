# memory/STATE.md
更新: 2026-08-13 夜（收尾小队列 T1/T2/T3 完成, M0 差异化判定已出）

## 模式
守护模式。**docs/23 已发送甲方（08-12, 用户亲发）; B4 观察时钟运行中** — asks=120（08-13 08:27 实测, ≥100 数量维度已达标）, 继续等 ≥3 天, 两条件同时满足为达标。缓至甲方首轮反馈: 任务二 B 一期 / 场景 B / _cleanup_backup 删除 / Qoder PAT。

## Git
- HEAD: 本 commit（T2/T3 收口）; 本轮链: 6e345df(R3 科研线) → 0d938d7(T1 建议数据入账) → 本 commit
- 三方对齐（GB10 push → GitHub → 本机 fetch+merge）

## 本轮战绩（08-13 T1/T2/T3）
- T1: schema_suggestions 08-12 23:33 批次入账（walkthrough 上传 tmp2s004xv5.pdf 7 条建议）; 产品份额①→持仓数量(high) 列下轮 apply 候选（走 SOP, 本次不 apply）
- T2: **M0 文献调研完成, 差异化判定 = 差异化成立（附条件）**; 报告 docs/experiments/2026-08-13_m0_literature_survey.md; 意外发现: CAIS/STATE-Bench 锚点无法公开核验（疑似检索幻觉）入 blocked_questions
- T3: B4 分布入账 — agent=15/fallback=92/error=0（77% 经 18s 超时回落）= A2 遗留量化证据 + docs/30 B 模块实证动机

## 服务
- :5050 UP (route=on, provider=local, embeddings=137, tmux coding-jinrong:api5050)
- :4096 sidecar UP; :8004/:8005/:8100/:15432 UP; :8007 down
- Loop B 强化版 30min 周期运行（canary/git/lint/flip）; tmux 禁杀 graph-loop-b/opencode-serve
- 科研隔离资产: ~/wzh/venvs/openai4s_probe + ~/wzh/research/{openai4s_probe,openai4s_data_probe,academic_skills_audit,m0_lit}; docling venv 均在生产外

## 质量基线
- pytest: 见收口验证（本轮未动代码, 仅数据/文档）; docs_lint 0 fail / 0 warn; sync_skills --check 21/21; 冻结节点 PASS
- eval 基线 (08-12 21:57): 确定性 16/16 / NF 0/9 / judge 4.94/5.0/5.0/5.0
- B4: asks=120 (agent=15/fallback=92/error=0); agent 路 warm best 13.5s; 回滚 10s

## 下一步（等用户/甲方）
1. 甲方首轮反馈 → 解锁: 任务二 B 一期 / 场景 B / 多期数据 / 字段规则表; A2 延迟修复优先级随反馈定
2. B4 继续积累（status.sh 可查）; eval 每天经生产端点跑一遍
3. 科研线: M0 完成 → M1 前置 = 人工核验 CAIS/STATE-Bench + 查 NLPCC/CCIR 截稿日（blocked_questions）; 产品份额① apply 候选等窗口
4. 菜单待拍板: Docling NCAMC 增强 / :8005 judge 分流常态化 / OpenAI4S 接入科研线 / docs/28 #2→#1→#4
