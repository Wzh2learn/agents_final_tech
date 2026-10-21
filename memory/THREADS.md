# Open Decisions And Blockers

Updated: 2026-10-21

当前短状态见 [STATE.md](STATE.md)，科研证据路由见 [Research Entry](../docs/research/README.md)。本表保留真实未决事项；完成或被后续证据更正的历史条目保留原文归档。

## 当前未决

| ID | 状态 | 待决内容与证据 |
|---|---|---|
| NEXT-RESEARCH-GOAL | `READY_FOR_LOOP_D_HANDOFF` | Owner 已确认发表优先、学硕三贡献及送审前倒排；[四项 Goals](../docs/research/LOOP_D_PUBLICATION_AND_THESIS_GOALS_20261021.md)已备好，待 Owner 转发 Loop D 执行；本次交接未运行新实验 |
| MIGRATION-ORACLE-DESIGN | `G2_CANDIDATE_METHOD_UNCONFIRMED` | G2 获准复用并扩展真实变化研究；分报 behavior/contract/hybrid，以独立参考审查误接受/误拒绝；[既有复核](../research/research_portfolio_v2/pymigbench_external_change_v1/ntripbrowser_qualification_v2/INDEPENDENT_PROBE_REVIEW.md)仍只支持单案例，方法创新未定 |
| PAPER-E-SCOPE | `TWO_CASES_FOR_CURRENT_SUBMISSION` | 当前首投保持[主稿](../paper/saner_rene_manuscript_v1.md)与[scope lock](../paper/saner_rene_manuscript_scope_lock_v1.md)的两案例，不等待新迁移结果；新增 pooled CI 分析单位复核，不追认事后分析为预注册 |
| PAPER-E-SUBMISSION | `PREPARATION_AUTHORIZED_EXTERNAL_ACTIONS_PENDING` | SANER RENE 摘要未注册；G1 选择主备渠道并完成可审阅包，Owner 最终确认署名/单位、渠道、费用及正式投稿。会议须送审前已召开并展示；期刊认定凭证仍需结合具体路径核实 |
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
