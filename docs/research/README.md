# Research Entry

Status: `CURRENT_SINGLE_ENTRY` | Updated: 2026-10-27

本页是唯一现役科研入口。`docs/INDEX.md` 负责导航，`memory/STATE.md` 保留短状态，`memory/THREADS.md` 只记录未决事项。各阶段回执保留其日期与证据边界。

## 当前任务与证据

Adaptive Mechanism阶段已完成A实作、C固定快照审阅和D零模型集成。scoring V2有效，C确认gold `answer_type`基线是oracle-assisted；D问题文本消融恢复31 ACCEPT/5 UNKNOWN，但只支持暴露开发面板的题面启发式边界。Paper E交付完整源包但正式TeX构建为 `BUILD_BLOCKED`。本轮新增模型、训练、judge和生产探针为0，A/C累计26/26。

A确认单位题不可推断尺度，唯一可修引用题0/1；安全尾部适配已阻止旧1)0→10反例，strict/embedded分报。旧诊断与24/24错误池回放均保留开发身份，C2/C3方法尚未成立；340 token差额继续保守保留。参见[Phase A](../governance/audit/loop_d_control_review/PHASE_A_RETURN.md)。

| 用途 | 权威记录 |
|---|---|
| 当前方法实验与成本 | [A_RETURN](../../research/adaptive_mechanism_20261027_v1/A_RETURN.md)、[QUESTION_ONLY_ABLATION](../../research/adaptive_mechanism_20261027_v1/d_integration/results/QUESTION_ONLY_ABLATION.json)、[C_AUDIT](../../research/adaptive_mechanism_20261027_v1/audits/C_JOINT_AUDIT.md) |
| 当前自然错误/取证成本阶段 | [STAGE_RETURN](../../research/natural_error_evidence_cost_20261026_v1/STAGE_RETURN.md)、[A_CLOSEOUT](../../research/natural_error_evidence_cost_20261026_v1/a_closeout/A_CLOSEOUT_RESULT.json)、[C_FINAL](../../research/natural_error_evidence_cost_20261026_v1/audits/TASK_RESULT_C_FINAL.json) |
| 修订算子诊断 | [RETURN](../../research/feedback_delivery_continuation_20261025_v1/REVISION_OPERATOR_DIAGNOSTIC_RETURN.md)、[CONTROL](../../research/feedback_delivery_continuation_20261025_v1/REVISION_OPERATOR_V2_CONTROL_RESCORED.json)、[MECHANISM](../../research/feedback_delivery_continuation_20261025_v1/REVISION_OPERATOR_V3_MECHANISM.json)、[RESOURCE](../../research/feedback_delivery_continuation_20261025_v1/REVISION_OPERATOR_RESOURCE_RECEIPT_V1.json) |
| Paper E 路由与办理 | [FORMAL_BUILD_PACKAGE](../../research/adaptive_mechanism_20261027_v1/paper_e_formal_build/)、[SNCS_DERIVED_PACKAGE](../../research/publication_proxy_calibration_20261026_v1/paper_e_sncs/)、[OWNER_SHEET](../../research/publication_proxy_calibration_20261026_v1/paper_e_sncs/OWNER_DECISION_SHEET.md) |
| 当前科研基线、资产与实验卡 | [RESEARCH_BASELINE_AND_REUSE_MAP](../../research/research_baseline_governance_20261023/RESEARCH_BASELINE_AND_REUSE_MAP.md)；[RECONCILIATION](../../research/research_baseline_governance_20261023/RECONCILIATION.json) 保存复算、hash 与来源关系 |
| 唯一执行正文 | [LOOP_D_RESEARCH_PROMPT](LOOP_D_RESEARCH_PROMPT.md)：A/C 26/26已执行；评分、预算、机制边界和Paper E构建阻断已接续 |
| 最新科研回执 | [D_INTEGRATION_RETURN](../../research/adaptive_mechanism_20261027_v1/D_INTEGRATION_RETURN.md)、[A_RETURN](../../research/adaptive_mechanism_20261027_v1/A_RETURN.md)、[C_TASK_RESULT](../../research/adaptive_mechanism_20261027_v1/audits/TASK_RESULT_C.json) |
| 本轮治理、资产分类与 Git 收口 | [工作区治理报告](../governance/2026-10-21_workspace_git_closeout.md)；跨主机与分支实况以报告的最终核验为准 |
| 发表/学位当前账本 | [RESOURCE_LEDGER](../../research/publication_thesis_goals_v1/RESOURCE_LEDGER.json)：不含独立Phase B的历史阶段4,064 accounting attempts / 9,169,672 tokens；训练3,495,424已含总量；事件复算9,169,332，340差额待核，保持原保守记账 |
| 历史 Portfolio V2 账本 | [COST_AND_CANDIDATES.json](../../research/research_portfolio_v2/COST_AND_CANDIDATES.json)；失败调用补记采用 post-hoc adjustment，原始回执不改 |
| 历史独立账本 | [747-record ledger](../../research/research_direction_sprint_20261020_v1/execution_v1/RESEARCH_GENERATION_LEDGER.json)；更早账本继续隔离，不与 Portfolio V2 混算 |

当前账本的失败调用补记及 101 条 raw pair 复核见[对账说明](../../research/research_portfolio_v2/governance_20261021/LEDGER_RECONCILIATION.md)；其可重放脚本保留负例校验。

`execution_v2/MERGED_GOAL_RETURN.md` 和既有 feature 分支是历史证据及恢复线索，不承担当前 Git 状态的权威角色。

## 科学判断与解释边界

| 研究线 | 当前判断与证据 |
|---|---|
| C1 测量 / Paper E | `BUILD_BLOCKED_SOURCE_READY`，受限两案例测量审计；[正式源包](../../research/adaptive_mechanism_20261027_v1/paper_e_formal_build/)和[SNCS派生稿](../../research/publication_proxy_calibration_20261026_v1/paper_e_sncs/paper_e_sncs.tex)已具备，精确TeX编译受工具阻断，非缺少科研许可 |
| C2 学习 / 证据反馈 | `STOP_CURRENT_R_E_CANDIDATE_NOT_GENERAL_CLAIM`。真实child-only训练完成但未满足有效ordinary续训；N/R/E是集合代理比较且有接口混杂，仅停止当前实现，不作为干净方法负结论 |
| C3 交付 / 核验与修复 | `PRIOR_ERROR_POOL_REPLAY_NEUTRAL_RETRY_STRONG_LOCALIZATION_STOPPED`。回放上 neutral 62/72、original 60/72、localization 59/72，但 24/24 与 V4/V5 error pool 重合；只支持开发停止判断，不支持新 family 泛化 |
| Paper E | `SNCS_SUBSCRIPTION_CONDITIONAL_PRIMARY`，完整派生稿、24/24 引用和Owner表已具备；精确TeX构建、作者/专利/artifact许可、投稿/付款/公开仍待办 |
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

这些资产已供 V2-V5、首轮 C2/C3 和自然 TAT-QA 方法实验复用。旧 G2 消费/迁移方法、G3 复杂 planner、scope 面板和四个失败反馈候选继续停止。A已完成增量核对，B方案待Owner转发；D/A/C按监督资格—同起点开发—隔离确认推进，340差额不阻塞新阶段，不重复关闭配方。Paper E 首投保持两案例，12 页费用和缺项见 [OWNER_DECISIONS_REQUIRED](../../research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/OWNER_DECISIONS_REQUIRED.md)。具体外部事项见[当前未决事项](../../memory/THREADS.md)。

## Paper E 唯一写作线

- [canonical manuscript](../../paper/saner_rene_manuscript_v1.md)
- [claim/evidence matrix](../../paper/saner_rene_claim_matrix_v1.json)与[scope lock](../../paper/saner_rene_manuscript_scope_lock_v1.md)
- [整合独立复核](../../research/research_portfolio_v2/PAPER_E_INDEPENDENT_REVIEW.md)与[投稿门禁](PAPER_E_SUBMISSION_READINESS_GATE_v1.md)

当前范围为两个测量审计案例，FinQA 归入 Case 1，FinRank 为 Case 2。9pt、12页 PDF、目标包审计和私有 artifact 复现已完成；当前建议SNCS订阅条件主投、ICAART历史时间门备选；SNCS实质派生稿待交付，Owner最终渠道与外部动作待确认；正式动作前核官方窗口和总成本。原修订稿、旧审稿与各次 gate 保留为历史证据，不构成第二份现役主稿。

## 学位范围与历史

- [治理基线](THESIS_RESEARCH_GOVERNANCE_BASELINE_v1.md)、[学位架构 v3](THESIS_RESEARCH_ARCHITECTURE_v3.md)、[工作包蓝图](THESIS_EXECUTION_BLUEPRINT_v1.md)及稿件骨架的现役区已接唯一指令；2027年10月送审，C2/C3待验证或替换。旧数据 NO_GO、已停止面板及冻结证据不随新授权解除。
- [旧 THREADS 全文快照](../../memory/archive/THREADS_2026-10-21_pre_workspace_governance.md)保存历史原文；现役未决事项只在 [THREADS](../../memory/THREADS.md) 维护。
- Raw、failed/partial 响应、冻结结果、独立审查与历史账本保留来源身份。AI 语义评审不是人工 Gold、盲审或导师签字。
