# Open Decisions And Blockers

Updated: 2026-10-21

当前短状态见 [STATE.md](STATE.md)，科研证据路由见 [Research Entry](../docs/research/README.md)。本表保留真实未决事项；完成或被后续证据更正的历史条目保留原文归档。

## 当前未决

| ID | 状态 | 待决内容与证据 |
|---|---|---|
| GOV-20261021 | `IN_PROGRESS` | 本轮工作区分类、独有材料保全、分支合并与跨主机核验；以[治理报告](../docs/governance/2026-10-21_workspace_git_closeout.md)最终记录为准 |
| NEXT-RESEARCH-GOAL | `PENDING_OWNER_REVIEW` | 先完成治理，再由 owner 与科研负责人依据资产和[最新回执](../research/research_portfolio_v2/GOAL_RETURN.md)决定新的探索与论文写作 Goal |
| MIGRATION-ORACLE-DESIGN | `UNDECIDED` | 是否扩充真实迁移 commit、如何分报 behavior/structure/hybrid、如何分析假阳性机制；[现有独立复核](../research/research_portfolio_v2/pymigbench_external_change_v1/ntripbrowser_qualification_v2/INDEPENDENT_PROBE_REVIEW.md)只支持单案例观察 |
| PAPER-E-SCOPE | `PENDING_AUTHOR_DECISION` | 新迁移证据保持独立研究线，还是以后作为额外测量审计案例；当前[主稿](../paper/saner_rene_manuscript_v1.md)与[scope lock](../paper/saner_rene_manuscript_scope_lock_v1.md)仍为两案例，不追认新材料为既有预注册 |
| PAPER-E-SUBMISSION | `PENDING_EXTERNAL_ACTIONS` | 作者、venue、artifact URL/DOI、注册和投稿尚待外部决定；派生 PDF 非致命警告继续披露，见[投稿门禁](../docs/research/PAPER_E_SUBMISSION_READINESS_GATE_v1.md)后续更正 |
| LEGACY-DATA-TRAINING | `NO_NEW_AUTHORIZATION` | 旧 Phase 1a `DATA_NO_GO`、RQ2 `NOT_IDENTIFIED`、Phase 2 replay、PRM/训练门禁与已停止面板不因整理自动解除；见[治理基线](../docs/research/THESIS_RESEARCH_GOVERNANCE_BASELINE_v1.md)及下方原文快照 |

## 未复核的历史运行与外部事项

本轮未连接生产后端复验。下列事项继续保留，归档不表示解决；完整描述、日期和原始状态见[旧 THREADS 全文](archive/THREADS_2026-10-21_pre_workspace_governance.md)。

| 事项 | 本轮状态 | 原文检索线索 |
|---|---|---|
| PostgreSQL 空闲连接、Loop B/kiosk 并发写、orphan/sidecar session、历史性能风险 | `NOT_REVALIDATED` | `PG`、`idle`、`schema_suggestions`、`orphan`、`sidecar` |
| M1 元数据缺失与 OCR/坐标边界 | `NOT_REVALIDATED` | `110/137`、`product_name`、`coord_table` |
| 导师/客户实际发送、旧投稿日期、专利与公开权限 | `NOT_CONFIRMED_THIS_PASS` | `发送`、`NLPCC`、`CCIR`、`专利`、`权限` |
| 其他历史 pending、known risk、待审批事项 | `RETAIN_ORIGINAL_STATUS` | 以原文状态为准；新证据出现后再逐项裁决 |

## 已收口或被更正条目的去向

- 原 `memory/THREADS.md` 全文通过 `git mv` 原样保留为 [THREADS_2026-10-21_pre_workspace_governance.md](archive/THREADS_2026-10-21_pre_workspace_governance.md)，SHA256 为 `63246e3e23aaa7445c30bdaefee672d34f57e2cf3770edb64f87e3f84d9f516d`。快照内相对链接沿用原文件位于 `memory/THREADS.md` 时的基址，不重写历史正文。
- MA-CERD 的旧 dependency-propagation 与 handling 解释由[日期更正](../research/ma_cerd_independent_v1/CORRECTIONS_20261021.md)取代；原始分数和实验回执不改。
- 旧 Goal “待转发”、Paper E “修订未落实”及 wide-evidence 源绑定阻塞已有后续执行或更正，不再作为现役待办；Paper E 的外部投稿事项仍开放。
- 旧 24 题统一人工门禁已有 AI 开发性裁决与后续资格判断；AI review 不等于人工 Gold。FinRank 当前面板已停止，不再以旧人工门禁要求重开。
- 747-record 与更早账本继续独立保存；当前 Portfolio V2 成本仅以[聚合账本](../research/research_portfolio_v2/COST_AND_CANDIDATES.json)及其可重放更正为准。
- FinRank H/K、TAT-DQA 及各训练/数据门禁、同一 CodeUpdateArena prose-update 臂和已饱和 authored fixtures 的停止或授权边界继续有效。归档不产生新的运行许可。
