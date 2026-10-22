# Open Decisions And Blockers

Updated: 2026-10-23

当前短状态见 [STATE.md](STATE.md)，科研证据路由见 [Research Entry](../docs/research/README.md)。本表保留真实未决事项；完成或被后续证据更正的历史条目保留原文归档。

## 当前未决

| ID | 状态 | 待决内容与证据 |
|---|---|---|
| NEXT-RESEARCH-GOAL | `V3_EVIDENCE_EXIT_WITH_BOUNDED_SIGNAL` | [V3 回执](../research/publication_thesis_goals_v1/revision_v3/SPRINT_RETURN.md)明确 Paper E 可交 Owner 投稿、G2 保持停止、G3 复杂 planner 暂停、Valentine LoRA 资格停止、STALE 状态卡取得同源新 UID 配对信号 |
| MIGRATION-ORACLE-DESIGN | `G2_METHOD_INCREMENT_NOT_IDENTIFIED_STOP` | actual-module paired intervention 已修复审计反例，但 alias-aware static + repo/behavior 和 consumption + behavior 均6/6；自然模型候选也无新错误机制 |
| REVALIDATION-POLICY-DESIGN | `G3_COMPLEX_PLANNER_PAUSED` | 六对象多个 simple baseline 均6/6；单次 wall-clock 不支持成本优胜，停止复杂 planner |
| THIRD-CONTRIBUTION-SCOPE | `TRANSPARENT_REUSE_RULE_QUALIFIED_PLANNER_PAUSED` | scope policy 与 always-full 在 20 个 development transition 上同为 15 CORRECT、5 ABSTAIN，probe 30 对 35；仍缺自然 family 和真实下游收益 |
| STALE-STATE-CARD | `BOUNDED_REPRESENTATION_SIGNAL` | oracle 检索下开发 1/4 对 3/4，同源未用 UID 配对 0/8 对 4/8；下一步只在非 oracle 检索和独立来源下升级判断 |
| PAPER-E-SCOPE | `TWO_CASES_FOR_CURRENT_SUBMISSION` | 当前首投保持[主稿](../paper/saner_rene_manuscript_v1.md)两案例。FinQA 为89行/30 report clusters；UID 聚类与事后统计已同步，不追认事后分析为预注册 |
| PAPER-E-SUBMISSION | `INTERNAL_PACKAGE_READY_OWNER_EXTERNAL_ACTIONS` | 9pt、11页、目标包审计、artifact clean reproduction 均通过；只待 Owner 身份、投稿、付款、展示和公开许可 |
| THESIS-DOC-CONTINUITY | `G4_PARTIAL_COMPLETE_CONTINUING` | 中文 Paper E 引用正文、导师一页稿、素材地图和现役骨架已更新；正式章节整合仍继续 |
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
