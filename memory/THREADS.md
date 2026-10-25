# Open Decisions And Blockers

Updated: 2026-10-26

当前短状态见 [STATE.md](STATE.md)，科研证据路由见 [Research Entry](../docs/research/README.md)。本表保留真实未决事项；完成或被后续证据更正的历史条目保留原文归档。

## 当前未决

| ID | 状态 | 待决内容与证据 |
|---|---|---|
| LOOP-D-PHASE-B-DISPATCH | `APPROVED_FOR_OWNER_HANDOFF_NOT_DISPATCHED` | [唯一指令](../docs/research/LOOP_D_RESEARCH_PROMPT.md)接续已审阅A；Owner转发后D可派发GB10 A/C；本会话尚未启动任务 |
| LEDGER-340 | `UNRECONCILED_KEEP_CONSERVATIVE_TOTAL` | [自审证据](../docs/governance/audit/loop_d_control_review/RECONCILIATION.json)：35个生成/评审事件加5个训练事件复算9,169,332，比聚合9,169,672少340；attempts均4,064；不释放差额、不改旧账 |
| UNIT-OBSERVABILITY | `UNOBSERVABLE_UNIT_CASE_EXCLUDED_FROM_INFERABLE_DENOMINATOR` | [A回执](../docs/governance/audit/loop_d_control_review/PHASE_A_RETURN.md)已确认单位尺度不可见；仅可修引用题0/1，后续监督按可观测性资格核验 |
| ADAPTER-SEMANTICS | `SAFE_TAIL_AND_STRICT_SPLIT_VERIFIED_PHASE_A` | [A复算](../research/feedback_delivery_continuation_20261025_v1/PHASE_A_RECOMPUTE_V1.json)已阻止1)0→10反例，raw/strict/embedded分开；不把旧适配器继续写成现役实现，未来合同仍需C核验 |
| NEXT-C2-SUPERVISION | `TEACHER_OR_TOOL_CORRECTIONS_REQUIRED` | [Phase A 回执](../docs/governance/audit/loop_d_control_review/PHASE_A_RETURN.md)确认单位题不可见、唯一可修引用题仍0/1；教师/工具合格纠正和同起点比较属于阶段 B |
| NEXT-PHASE-BUDGET | `APPROVED_FOR_OWNER_HANDOFF_672_ATTEMPTS` | 当前范围和各资源帽只见[唯一指令§9](../docs/research/LOOP_D_RESEARCH_PROMPT.md#9-唯一阶段预算与资源调度)；旧REQUESTED文件是历史申请，32余额不混入；本轮尚未消耗 |
| C2-FEEDBACK-REPAIR | `ONE_ELIGIBLE_DEVELOPMENT_CASE_NO_METHOD_CLAIM` | A已修评分/适配边界，唯一可修引用题的neutral/category/localization仍0/1；O/N/R/E监督资格与训练是下一实验，不把0/1写成普遍机制 |
| C3-DELIVERY-POLICY | `PRIOR_ERROR_POOL_REPLAY_NEUTRAL_RETRY_STRONG_LOCALIZATION_STOPPED` | [回放 C](../research/feedback_delivery_continuation_20261025_v1/DELIVERY_CONFIRMATION_C_V1.json) 中 original 60/72、neutral 62/72、localization 59/72；定位修订修对 3、破坏 4。24/24 task IDs 与 V4/V5 error pool 重合，只作开发回放，透明门控只以大面积弃答降低条件错误率 |
| PAPER-E-ROUTE | `ICAART_CONDITIONAL_PRIMARY_SNCS_BACKUP` | [路由适配](../research/feedback_delivery_continuation_20261025_v1/PAPER_E_ROUTE_ADAPTATION_20261025.md)是日期化建议，尚非Owner最终批准；动作前核验窗口、展示/认定和合理总费用，路线变化须明确确认，不自动转投 |
| THESIS-REVIEW-DATE | `OCTOBER_2027_EXACT_DATE_UNKNOWN` | Owner 更正此前 2027 年 4 月信息；不得假设具体送审日为 10 月 31 日 |
| PAPER-E-SCOPE | `TWO_CASES_FOR_CURRENT_SUBMISSION` | 当前首投保持[主稿](../paper/saner_rene_manuscript_v1.md)两案例。FinQA 为89行/30 report clusters；UID 聚类与事后统计已同步，不追认事后分析为预注册 |
| PAPER-E-SUBMISSION | `PACKAGE_AUDIT_PASS_OWNER_EXTERNAL_ACTIONS` | [G1 package](../research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/README.md)已更新 12 页 PDF、24/24 引用和可办理决策；未投稿/付款/公开 |
| THESIS-DOC-CONTINUITY | `C1_C2_C3_BOUNDARIES_UPDATED` | C1 测量、C2 学习、C3 交付已写入现役入口；正式中文章节仍需把 A/C 负结果和停止条件整合成正文 |
| OWNER_EXTERNAL_ACTIONS | `AUTHORS_FEES_SUBMISSION_PUBLIC_RELEASE` | 作者/单位/通讯、专利、AI披露批准、artifact/DOI公开、注册差旅、正式投稿付款及学校认定 |
| LEGACY-DATA-TRAINING | `HISTORICAL_NO_GO_RETAINED_NEW_STUDIES_AUTHORIZED` | Owner 新授权允许合格新数据上的小规模 LoRA/SFT 等研究；旧 Phase 1a `DATA_NO_GO`、RQ2 `NOT_IDENTIFIED` 及已停止面板的证据缺陷不解除，不洗掉旧训练/数据判定。本轮范围以唯一指令和Owner转发为准；历史广泛授权不恢复停止面板 |
| SKILL-METADATA-DEBT | `NONBLOCKING_KNOWN_WARNINGS` | skill-doctor 为 0 errors / 141 既有 warnings（completion contract 与 frontmatter 排序）；本轮不批量格式化技能，实际分发 check 两端均通过 |

旧 `MIGRATION-ORACLE-DESIGN`、`REVALIDATION-POLICY-DESIGN`、`G2-STATE-ACTION`、`G3-INCREMENTAL-EVIDENCE` 和 `NEXT-STATE-ACTION-EXPERIMENT` 已降为历史研究线，现役入口统一使用 C1 测量、C2 学习、C3 交付；原始证据和停止结论不改写。

## 未复核的历史运行与外部事项

本轮未连接生产后端复验。下列事项继续保留，归档不表示解决；完整描述、日期和原始状态见[旧 THREADS 全文](archive/THREADS_2026-10-21_pre_workspace_governance.md)。

| 事项 | 本轮状态 | 原文检索线索 |
|---|---|---|
| PostgreSQL 空闲连接、Loop B/kiosk 并发写、orphan/sidecar session、历史性能风险 | `NOT_REVALIDATED` | `PG`、`idle`、`schema_suggestions`、`orphan`、`sidecar` |
| M1 元数据缺失与 OCR/坐标边界 | `NOT_REVALIDATED` | `110/137`、`product_name`、`coord_table` |
| 导师/客户实际发送、旧投稿日期、专利与公开权限 | `NOT_CONFIRMED_THIS_PASS` | `发送`、`NLPCC`、`CCIR`、`专利`、`权限` |
| 其他历史 pending、known risk、待审批事项 | `RETAIN_ORIGINAL_STATUS` | 以原文状态为准；新证据出现后再逐项裁决 |

## 已收口或被更正条目的去向

- 2026-10-26：阶段A回报已由科研负责人审阅，接受单位可观测性、strict/embedded与安全尾部复算的限定结论；340 token未解释，不因A完成关闭。B交接方案已准备，尚未派发。

- GOV-20261021 已完成：独有材料保全、九个历史独有提交合并、旧工作树退役、三端 main 对齐；范围、恢复入口和离线验收见[治理报告](../docs/governance/2026-10-21_workspace_git_closeout.md)。
- 原 `memory/THREADS.md` 全文通过 `git mv` 原样保留为 [THREADS_2026-10-21_pre_workspace_governance.md](archive/THREADS_2026-10-21_pre_workspace_governance.md)，SHA256 为 `63246e3e23aaa7445c30bdaefee672d34f57e2cf3770edb64f87e3f84d9f516d`。快照内相对链接沿用原文件位于 `memory/THREADS.md` 时的基址，不重写历史正文。
- MA-CERD 的旧 dependency-propagation 与 handling 解释由[日期更正](../research/ma_cerd_independent_v1/CORRECTIONS_20261021.md)取代；原始分数和实验回执不改。
- 旧 Goal “待转发”、Paper E “修订未落实”及 wide-evidence 源绑定阻塞已有后续执行或更正，不再作为现役待办；Paper E 的外部投稿事项仍开放。
- 旧 24 题统一人工门禁已有 AI 开发性裁决与后续资格判断；AI review 不等于人工 Gold。FinRank 当前面板已停止，不再以旧人工门禁要求重开。
- 747-record 与更早账本继续独立保存；当前 Portfolio V2 成本仅以[聚合账本](../research/research_portfolio_v2/COST_AND_CANDIDATES.json)及其可重放更正为准。
- FinRank H/K、TAT-DQA 及各训练/数据门禁、同一 CodeUpdateArena prose-update 臂和已饱和 authored fixtures 的停止或授权边界继续有效。归档不产生新的运行许可。
