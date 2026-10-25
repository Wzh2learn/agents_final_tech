# Research Entry

Status: `CURRENT_SINGLE_ENTRY` | Updated: 2026-10-25

本页是唯一现役科研入口。`docs/INDEX.md` 负责导航，`memory/STATE.md` 保留短状态，`memory/THREADS.md` 只记录未决事项。各阶段回执保留其日期与证据边界。

## 当前任务与证据

2026-10-25 完成 P0 可见表头/常数合同修正、同一候选反馈干预、oracle 机制诊断、24-family 交付回放和 Paper E 路由适配。开发面板上 neutral 56/72，localization 49/72，execution 40/72，均无 `wrong_to_correct`；先前 V4/V5 error-pool 回放上 neutral 62/72、original 60/72、localization 59/72。独立复核确认回放的 24/24 task IDs 与旧 error pool 重合，不能作为新 family 确认。O/R/E 因缺少反馈衍生且训练合格的纠正监督未训练。当前权威结果见 [Research Return 2026-10-25](../../research/feedback_delivery_continuation_20261025_v1/RESEARCH_RETURN_20261025.md)。

2026-10-25 小型修订算子诊断继续：共同语法适配后正确复制 2/2、已知最小编辑 2/2；neutral/category/localization 对两个开发错误均 0/2 目标精确。结果支持“明确编辑可执行、可见诊断未转化为编辑动作”的当前边界。完整训练和新来源确认需使用[独立预算](../../research/feedback_delivery_continuation_20261025_v1/NEXT_PHASE_BUDGET_REQUEST_V1.json)，不消耗旧余额重置阶段。

| 用途 | 权威记录 |
|---|---|
| 当前方法实验与成本 | [RESEARCH_RETURN_20261025](../../research/feedback_delivery_continuation_20261025_v1/RESEARCH_RETURN_20261025.md)、[RESOURCE_RECEIPT](../../research/feedback_delivery_continuation_20261025_v1/RESOURCE_RECEIPT_20261025.json)、[EXPERIMENT_A](../../research/feedback_delivery_continuation_20261025_v1/SAME_CANDIDATE_FEEDBACK_A_FINAL.json)、[REPLAY_C](../../research/feedback_delivery_continuation_20261025_v1/DELIVERY_CONFIRMATION_C_V1.json) |
| 修订算子诊断 | [RETURN](../../research/feedback_delivery_continuation_20261025_v1/REVISION_OPERATOR_DIAGNOSTIC_RETURN.md)、[CONTROL](../../research/feedback_delivery_continuation_20261025_v1/REVISION_OPERATOR_V2_CONTROL_RESCORED.json)、[MECHANISM](../../research/feedback_delivery_continuation_20261025_v1/REVISION_OPERATOR_V3_MECHANISM.json)、[RESOURCE](../../research/feedback_delivery_continuation_20261025_v1/REVISION_OPERATOR_RESOURCE_RECEIPT_V1.json) |
| Paper E 路由与办理 | [PAPER_E_ROUTE_ADAPTATION](../../research/feedback_delivery_continuation_20261025_v1/PAPER_E_ROUTE_ADAPTATION_20261025.md)、[G1_SUBMISSION_PACKAGE](../../research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/README.md) |
| 当前科研基线、资产与实验卡 | [RESEARCH_BASELINE_AND_REUSE_MAP](../../research/research_baseline_governance_20261023/RESEARCH_BASELINE_AND_REUSE_MAP.md)；[RECONCILIATION](../../research/research_baseline_governance_20261023/RECONCILIATION.json) 保存复算、hash 与来源关系 |
| 新一轮发表与学位研究方向 | [Loop D 四项 Goals v2](LOOP_D_PUBLICATION_AND_THESIS_GOALS_V2_20261022.md)：有限冲刺、分阶段验收、自主探索；[v1](LOOP_D_PUBLICATION_AND_THESIS_GOALS_20261021.md)保留任务来源 |
| 当前回执 | [V5 RESEARCH_SPRINT_RETURN](../../research/publication_thesis_goals_v1/revision_v5/RESEARCH_SPRINT_RETURN.md)；V4/V3/V2 回执为前序证据 |
| 本轮治理、资产分类与 Git 收口 | [工作区治理报告](../governance/2026-10-21_workspace_git_closeout.md)；跨主机与分支实况以报告的最终核验为准 |
| 发表/学位当前账本 | [RESOURCE_LEDGER](../../research/publication_thesis_goals_v1/RESOURCE_LEDGER.json)：当前 Goal 4,064 attempts / 9,169,672 tokens；训练 token 3,495,424 单列 |
| 历史 Portfolio V2 账本 | [COST_AND_CANDIDATES.json](../../research/research_portfolio_v2/COST_AND_CANDIDATES.json)；失败调用补记采用 post-hoc adjustment，原始回执不改 |
| 历史独立账本 | [747-record ledger](../../research/research_direction_sprint_20261020_v1/execution_v1/RESEARCH_GENERATION_LEDGER.json)；更早账本继续隔离，不与 Portfolio V2 混算 |

当前账本的失败调用补记及 101 条 raw pair 复核见[对账说明](../../research/research_portfolio_v2/governance_20261021/LEDGER_RECONCILIATION.md)；其可重放脚本保留负例校验。

`execution_v2/MERGED_GOAL_RETURN.md` 和既有 feature 分支是历史证据及恢复线索，不承担当前 Git 状态的权威角色。

## 科学判断与解释边界

| 研究线 | 当前判断与证据 |
|---|---|
| C1 测量 / Paper E | `NARROW_AND_CONTINUE_PACKAGE_AUDIT_PASS`，受限两案例测量审计；[唯一主稿](../../paper/saner_rene_manuscript_v1.md)、[ICAART 包](../../research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/README.md)与[目标包审计](../../research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/G1_ICAART_PACKAGE_AUDIT_20261025.json) |
| C2 学习 / 证据反馈 | `EXPLICIT_EDIT_EXECUTABLE_VISIBLE_DIAGNOSIS_NO_INCREMENT_OE_NOT_TRAINED`。copy 2/2、known edit 2/2；两个开发错误上 neutral/category/localization 均 0/2 目标精确。允许教师/工具生成合格纠正来训练修订，但须与普通答案监督和同起点 R 严格比较 |
| C3 交付 / 核验与修复 | `PRIOR_ERROR_POOL_REPLAY_NEUTRAL_RETRY_STRONG_LOCALIZATION_STOPPED`。回放上 neutral 62/72、original 60/72、localization 59/72，但 24/24 与 V4/V5 error pool 重合；只支持开发停止判断，不支持新 family 泛化 |
| Paper E | `CONDITIONAL_ICAART_PRIMARY_SNCS_BACKUP`，12 页包审计、24/24 引用和私有 artifact 完整性通过；未投稿/付款/公开 |
| FinRank 历史经验 | `STOP_ON_CURRENT_PANEL`；缺少可识别的匹配纠错空间，[失败历史资格复核](../../research/decision_space_autopsy_v1/exploratory_b0_v1/FAILURE_HISTORY_QUALIFICATION_AUDIT.md)不支持重开 H/K，也不否定经验复用的一般可能性 |
| MA-CERD | 资源基线是 `resource_ids` membership localization；不是真实依赖边传播。Selective escalation 未验证，handling 完整集合匹配与动作可接受性须区分；见[更正](../../research/ma_cerd_independent_v1/CORRECTIONS_20261021.md) |
| Adaptive V3 | 当前 authored fixtures 上简单 greedy 已足够，two-step 无正向配对收益；[实现报告](../../research/research_portfolio_v2/ADAPTIVE_V3_IMPLEMENTATION_REPORT.md)。RPC capability 边界不等于操作系统沙箱 |
| CodeUpdateArena | 修正执行器后的开发集与新 families 都是有界负结果；[V2 报告](../../research/research_portfolio_v2/CODEUPDATEARENA_ADAPTER_REPORT_V2.md)与[新 families 确认](../../research/research_portfolio_v2/CODEUPDATEARENA_CONFIRMATION_REPORT.md)。不重复同一 prose-update 臂；合成变化不等于真实自然漂移 |
| VersiCode | 八个 name-change families 只支持语法/API 名称可观测性结论；[独立复核](../../research/research_portfolio_v2/versicode_observability_v1/POSTRUN_INDEPENDENT_REVIEW.md)。不证明行为正确或 prose/structured 孰优 |
| PyMigBench/真实迁移 | NtripBrowser 与 Partridge 显示行为/合同边界；v3 actual-module 与 paired intervention 已拒绝审计反例，但 alias-aware static + tests/behavior 同样 6/6。一个自然 Qwen 候选为等价正确实现。见 [G2 V2](../../research/publication_thesis_goals_v1/revision_v2/G2_V2_REPORT.md) 与 [G3 V2](../../research/publication_thesis_goals_v1/revision_v2/G3_V2_REPORT.md) |
| G2 状态到行动 | plain/decision fact 完成为 2/8 对 3/8，action 均为 1/8；当前 action 分类为 plain `1 grounded / 6 reasonable / 1 unnecessary refusal`、decision `1/5/2`。现有 bundle 会丢失充分的新事实，因此尚未隔离“正确状态到行动”的迁移失败。见 [基线更正](../../research/research_baseline_governance_20261023/RESEARCH_BASELINE_AND_REUSE_MAP.md) |
| G3 增量证据补查 | 43/400 useful expansions；oracle-selective 187/400 BOTH、37,292 mean chars 对 always-expand 64,338，只证明目标定义下的覆盖/成本 headroom。depth-2 的 5/43 与同预算随机相容（`P(X>=5)=0.434752`），不是可学习信号；模型策略未有效评估 |

NtripBrowser 证明该案例的行为测试会产生错误迁移的假阳性。行为与结构合同需要分别观察；现有证据不证明 hybrid oracle 普遍充分，也不支持比较两种信息表示的优劣。新迁移案例尚未纳入 Paper E 的两案例主张。

## 可继续利用的研究资产

- [外部变化来源独立审查](../../research/research_portfolio_v2/EXTERNAL_CHANGE_SOURCE_INDEPENDENT_REVIEW.md)：保留来源版本、重复结构、许可证与可观测性限制。
- [PyMigBench 资格筛选](../../research/research_portfolio_v2/pymigbench_external_change_v1/CURATION_REPORT.md)：历史环境复活暴露时区、tzdata 和传递版本合同缺口；资格失败不等于研究假设被否定。
- [依赖合同来源审计](../../research/research_portfolio_v2/pymigbench_external_change_v1/DEPENDENCY_CONTRACT_AUDIT.json)：36 条候选中 33 条可审计；manifest diff 缺失不等于不存在迁移意图。
- [Adaptive V3 可重放环境](../../research/adaptive_revalidation_v3/README.md)：透明机制、预算曲线和能力边界可复用；已有 fixture 结果不应包装为真实分布泛化。

这些资产已供 V2-V5、首轮 C2/C3 和自然 TAT-QA 方法实验复用。旧 G2 消费/迁移方法、G3 复杂 planner、scope 面板和四个失败反馈候选继续停止。下一步从教师/工具核验的纠正轨迹构建 O/R/E 监督，并只在曝光并集为空的新来源上确认；不再堆同类文本定位或错误加权变体。Paper E 首投保持两案例，12 页费用和缺项见 [OWNER_DECISIONS_REQUIRED](../../research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/OWNER_DECISIONS_REQUIRED.md)。具体外部事项见[当前未决事项](../../memory/THREADS.md)。

## Paper E 唯一写作线

- [canonical manuscript](../../paper/saner_rene_manuscript_v1.md)
- [claim/evidence matrix](../../paper/saner_rene_claim_matrix_v1.json)与[scope lock](../../paper/saner_rene_manuscript_scope_lock_v1.md)
- [整合独立复核](../../research/research_portfolio_v2/PAPER_E_INDEPENDENT_REVIEW.md)与[投稿门禁](PAPER_E_SUBMISSION_READINESS_GATE_v1.md)

当前范围为两个测量审计案例，FinQA 归入 Case 1，FinRank 为 Case 2。9pt、11页 PDF、目标包审计和私有 artifact 复现已完成；有界比较后选择 ICAART 2027 Regular Paper 主投、SN Computer Science 顺序备投，正式外部动作待 Owner。原修订稿、旧审稿与各次 gate 保留为历史证据，不构成第二份现役主稿。

## 学位范围与历史

- [治理基线](THESIS_RESEARCH_GOVERNANCE_BASELINE_v1.md)、[学位架构 v3](THESIS_RESEARCH_ARCHITECTURE_v3.md)、[工作包蓝图](THESIS_EXECUTION_BLUEPRINT_v1.md)及资产地图/稿件骨架均已接 V2。旧数据 NO_GO、已停止面板及冻结证据不随新授权解除。
- [旧 THREADS 全文快照](../../memory/archive/THREADS_2026-10-21_pre_workspace_governance.md)保存历史原文；现役未决事项只在 [THREADS](../../memory/THREADS.md) 维护。
- Raw、failed/partial 响应、冻结结果、独立审查与历史账本保留来源身份。AI 语义评审不是人工 Gold、盲审或导师签字。
