# Open Decisions And Blockers

Updated: 2026-10-23

当前短状态见 [STATE.md](STATE.md)，科研证据路由见 [Research Entry](../docs/research/README.md)。本表保留真实未决事项；完成或被后续证据更正的历史条目保留原文归档。

## 当前未决

| ID | 状态 | 待决内容与证据 |
|---|---|---|
| NEXT-RESEARCH-GOAL | `V5_TWO_CANDIDATES_WITH_DISTINCT_MEASUREMENTS` | [V5 回执](../research/publication_thesis_goals_v1/revision_v5/RESEARCH_SPRINT_RETURN.md)明确 Paper E handoff、G2 fixed-state 独立评审、G3 selective evidence headroom 及各自停止条件 |
| MIGRATION-ORACLE-DESIGN | `G2_METHOD_INCREMENT_NOT_IDENTIFIED_STOP` | actual-module paired intervention 已修复审计反例，但 alias-aware static + repo/behavior 和 consumption + behavior 均6/6；自然模型候选也无新错误机制 |
| REVALIDATION-POLICY-DESIGN | `G3_COMPLEX_PLANNER_PAUSED` | 六对象多个 simple baseline 均6/6；单次 wall-clock 不支持成本优胜，停止复杂 planner |
| G2-STATE-ACTION | `CONTINUE_NARROWED_DEVELOPMENT_ONLY` | 固定证据/固定状态下 fact 2/8→3/8、action 均 1/8；独立评审要求 information-matched held-out 验证，否则停止 |
| G3-INCREMENTAL-EVIDENCE | `KEEP_WITH_HEADROOM_MODEL_POLICY_UNEVALUATED` | 43 useful expansions、oracle 成本差、depth-2 弱信号；visible rule 停止，模型接口无有效决策 |
| NEXT-STATE-ACTION-EXPERIMENT | `NEEDS_INDEPENDENT_ACTION_REFERENCE` | 下一步需多合法行动、safe UNKNOWN、合理拒绝和新 natural families；不能把 CLARIFY/UNKNOWN 一律计成功 |
| PAPER-E-SCOPE | `TWO_CASES_FOR_CURRENT_SUBMISSION` | 当前首投保持[主稿](../paper/saner_rene_manuscript_v1.md)两案例。FinQA 为89行/30 report clusters；UID 聚类与事后统计已同步，不追认事后分析为预注册 |
| PAPER-E-SUBMISSION | `LIVE_HANDOFF_READY_OWNER_EXTERNAL_ACTIONS` | [V5 handoff](../research/publication_thesis_goals_v1/revision_v5/PAPER_E_SUBMISSION_HANDOFF.md)已含实时 ICAART 截止、PRIMORIS 入口冲突、费用/展示和 Owner 字段；未投稿/付款/公开 |
| THESIS-DOC-CONTINUITY | `G4_V5_TWO_CANDIDATES_DOCUMENTED` | 导师一页稿与骨架已区分 G2 状态到行动边界、G3 增量补查；正式章节和 held-out 结果仍待整合 |
| OWNER_EXTERNAL_ACTIONS | `AUTHORS_FEES_SUBMISSION_PUBLIC_RELEASE` | 作者/单位/通讯、专利、AI披露批准、artifact/DOI公开、注册差旅、正式投稿付款及学校认定 |
| LEGACY-DATA-TRAINING | `HISTORICAL_NO_GO_RETAINED_NEW_STUDIES_AUTHORIZED` | Owner 新授权允许合格新数据上的小规模 LoRA/SFT 等研究；旧 Phase 1a `DATA_NO_GO`、RQ2 `NOT_IDENTIFIED` 及已停止面板的证据缺陷不解除，不洗掉旧训练/数据判定。新阶段范围见四项 Goals |
| SKILL-METADATA-DEBT | `NONBLOCKING_KNOWN_WARNINGS` | skill-doctor 为 0 errors / 141 既有 warnings（completion contract 与 frontmatter 排序）；本轮不批量格式化技能，实际分发 check 两端均通过 |

## 未复核的历史运行与外部事项

本轮未连接生产后端复验。下列事项继续保留，归档不表示解决；完整描述、日期和原始状态见[旧 THREADS 全文](archive/THREADS_2026-10-21_pre_workspace_governance.md)。

| 事项 | 本轮状态 | 原文检索线索 |
|---|---|---|
| PostgreSQL 空闲连接、Loop B/kiosk 并发写、orphan/sidecar session、历史性能风险 | `NOT_REVALIDATED` | `PG`、`idle`、`schema_suggestions`、`orphan`、`sidecar` |
| M1 元数据缺失与 OCR/坐标边界 | `NOT_REVALIDATED` | `110/137`、`product_name`、`coord_table` |
| 导师/客户实际发送、旧投稿日期、专利与公开权限 | `NOT_CONFIRMED_THIS_PASS` | `发送`、`NLPCC`、`CCIR`、`专利`、`权限` |
| 其他历史 pending、known risk、待审批事项 | `RETAIN_ORIGINAL_STATUS` | 以原文状态为准；新证据出现后再逐项裁决 |

## 已收口或被更正条目的去向

- GOV-20261021 已完成：独有材料保全、九个历史独有提交合并、旧工作树退役、三端 main 对齐；范围、恢复入口和离线验收见[治理报告](../docs/governance/2026-10-21_workspace_git_closeout.md)。
- 原 `memory/THREADS.md` 全文通过 `git mv` 原样保留为 [THREADS_2026-10-21_pre_workspace_governance.md](archive/THREADS_2026-10-21_pre_workspace_governance.md)，SHA256 为 `63246e3e23aaa7445c30bdaefee672d34f57e2cf3770edb64f87e3f84d9f516d`。快照内相对链接沿用原文件位于 `memory/THREADS.md` 时的基址，不重写历史正文。
- MA-CERD 的旧 dependency-propagation 与 handling 解释由[日期更正](../research/ma_cerd_independent_v1/CORRECTIONS_20261021.md)取代；原始分数和实验回执不改。
- 旧 Goal “待转发”、Paper E “修订未落实”及 wide-evidence 源绑定阻塞已有后续执行或更正，不再作为现役待办；Paper E 的外部投稿事项仍开放。
- 旧 24 题统一人工门禁已有 AI 开发性裁决与后续资格判断；AI review 不等于人工 Gold。FinRank 当前面板已停止，不再以旧人工门禁要求重开。
- 747-record 与更早账本继续独立保存；当前 Portfolio V2 成本仅以[聚合账本](../research/research_portfolio_v2/COST_AND_CANDIDATES.json)及其可重放更正为准。
- FinRank H/K、TAT-DQA 及各训练/数据门禁、同一 CodeUpdateArena prose-update 臂和已饱和 authored fixtures 的停止或授权边界继续有效。归档不产生新的运行许可。
