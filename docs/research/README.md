# Research Entry

Status: `CURRENT_SINGLE_ENTRY` | Updated: 2026-10-21

本页是唯一现役科研入口。`docs/INDEX.md` 负责导航，`memory/STATE.md` 保留短状态，`memory/THREADS.md` 只记录未决事项。各阶段回执保留其日期与证据边界。

## 当前任务与证据

Portfolio V2 的有界探索及工作区治理已收口。Owner 已确认：Paper E 尽快正规发表，学硕论文按约 2027 年 4 月送审前完成成果认定倒排，合理复用 GB10 与本机素材，并允许新研究中的推理、工具、研究 Memory 和小规模 LoRA/SFT。完整执行方向见[四项 Goals](LOOP_D_PUBLICATION_AND_THESIS_GOALS_20261021.md)，供 Owner 转发 Loop D；本次文档交接尚未运行新实验或投稿。

| 用途 | 权威记录 |
|---|---|
| 新一轮发表与学位研究方向 | [Loop D 四项 Goals](LOOP_D_PUBLICATION_AND_THESIS_GOALS_20261021.md)：G1 Paper E 发表；G2 正确性验证；G3 验证决策/适应；G4 学硕写作与认定倒排 |
| 当前可审阅回执 | [publication_thesis_goals_v1/GOAL_RETURN.md](../../research/publication_thesis_goals_v1/GOAL_RETURN.md) |
| 本轮治理、资产分类与 Git 收口 | [工作区治理报告](../governance/2026-10-21_workspace_git_closeout.md)；跨主机与分支实况以报告的最终核验为准 |
| 最新科研回执 | [Portfolio V2 GOAL_RETURN](../../research/research_portfolio_v2/GOAL_RETURN.md)；其中成本为当时快照 |
| 当前聚合记账 | [COST_AND_CANDIDATES.json](../../research/research_portfolio_v2/COST_AND_CANDIDATES.json)；失败调用补记采用 post-hoc adjustment，原始回执不改 |
| 历史独立账本 | [747-record ledger](../../research/research_direction_sprint_20261020_v1/execution_v1/RESEARCH_GENERATION_LEDGER.json)；更早账本继续隔离，不与 Portfolio V2 混算 |

当前账本的失败调用补记及 101 条 raw pair 复核见[对账说明](../../research/research_portfolio_v2/governance_20261021/LEDGER_RECONCILIATION.md)；其可重放脚本保留负例校验。

`execution_v2/MERGED_GOAL_RETURN.md` 和既有 feature 分支是历史证据及恢复线索，不承担当前 Git 状态的权威角色。

## 科学判断与解释边界

| 研究线 | 当前判断与证据 |
|---|---|
| 发表/学位阶段 | Paper E 为 `CONDITIONAL_GO_FOR_ICAART`；G2 目标结果消费验证与 G3 风险触发选择性重验证均为候选方法线，不是已成立创新。见[本轮总回执](../../research/publication_thesis_goals_v1/GOAL_RETURN.md) |
| Paper E | `NARROW_AND_CONTINUE`，受限两案例测量审计；[唯一主稿](../../paper/saner_rene_manuscript_v1.md)与[整合报告](../../research/research_portfolio_v2/PAPER_E_INTEGRATION_REPORT.md) |
| FinRank 历史经验 | `STOP_ON_CURRENT_PANEL`；缺少可识别的匹配纠错空间，[失败历史资格复核](../../research/decision_space_autopsy_v1/exploratory_b0_v1/FAILURE_HISTORY_QUALIFICATION_AUDIT.md)不支持重开 H/K，也不否定经验复用的一般可能性 |
| MA-CERD | 资源基线是 `resource_ids` membership localization；不是真实依赖边传播。Selective escalation 未验证，handling 完整集合匹配与动作可接受性须区分；见[更正](../../research/ma_cerd_independent_v1/CORRECTIONS_20261021.md) |
| Adaptive V3 | 当前 authored fixtures 上简单 greedy 已足够，two-step 无正向配对收益；[实现报告](../../research/research_portfolio_v2/ADAPTIVE_V3_IMPLEMENTATION_REPORT.md)。RPC capability 边界不等于操作系统沙箱 |
| CodeUpdateArena | 修正执行器后的开发集与新 families 都是有界负结果；[V2 报告](../../research/research_portfolio_v2/CODEUPDATEARENA_ADAPTER_REPORT_V2.md)与[新 families 确认](../../research/research_portfolio_v2/CODEUPDATEARENA_CONFIRMATION_REPORT.md)。不重复同一 prose-update 臂；合成变化不等于真实自然漂移 |
| VersiCode | 八个 name-change families 只支持语法/API 名称可观测性结论；[独立复核](../../research/research_portfolio_v2/versicode_observability_v1/POSTRUN_INDEPENDENT_REVIEW.md)。不证明行为正确或 prose/structured 孰优 |
| PyMigBench | 一个真实 NtripBrowser 迁移中，BASE 通过测试却以异常回退掩盖未完成迁移；[资格回执](../../research/research_portfolio_v2/pymigbench_external_change_v1/ntripbrowser_qualification_v2/QUALIFICATION_RETURN.md)与[独立模型探针复核](../../research/research_portfolio_v2/pymigbench_external_change_v1/ntripbrowser_qualification_v2/INDEPENDENT_PROBE_REVIEW.md) |

NtripBrowser 证明该案例的行为测试会产生错误迁移的假阳性。行为与结构合同需要分别观察；现有证据不证明 hybrid oracle 普遍充分，也不支持比较两种信息表示的优劣。新迁移案例尚未纳入 Paper E 的两案例主张。

## 可继续利用的研究资产

- [外部变化来源独立审查](../../research/research_portfolio_v2/EXTERNAL_CHANGE_SOURCE_INDEPENDENT_REVIEW.md)：保留来源版本、重复结构、许可证与可观测性限制。
- [PyMigBench 资格筛选](../../research/research_portfolio_v2/pymigbench_external_change_v1/CURATION_REPORT.md)：历史环境复活暴露时区、tzdata 和传递版本合同缺口；资格失败不等于研究假设被否定。
- [依赖合同来源审计](../../research/research_portfolio_v2/pymigbench_external_change_v1/DEPENDENCY_CONTRACT_AUDIT.json)：36 条候选中 33 条可审计；manifest diff 缺失不等于不存在迁移意图。
- [Adaptive V3 可重放环境](../../research/adaptive_revalidation_v3/README.md)：透明机制、预算曲线和能力边界可复用；已有 fixture 结果不应包装为真实分布泛化。

这些资产优先供新四项 Goals 复用。G2/G3 的具体方法与最终创新点仍需科研验证；当前 Paper E 首投保持两案例，不等待新迁移研究。具体外部事项与未定研究选择见[当前未决事项](../../memory/THREADS.md)。

## Paper E 唯一写作线

- [canonical manuscript](../../paper/saner_rene_manuscript_v1.md)
- [claim/evidence matrix](../../paper/saner_rene_claim_matrix_v1.json)与[scope lock](../../paper/saner_rene_manuscript_scope_lock_v1.md)
- [整合独立复核](../../research/research_portfolio_v2/PAPER_E_INDEPENDENT_REVIEW.md)与[投稿门禁](PAPER_E_SUBMISSION_READINESS_GATE_v1.md)

当前范围为两个测量审计案例，FinQA 归入 Case 1，FinRank 为 Case 2。源绑定更正已收口；新增 pooled CI 分析单位复核与渠道适配列入 G1。SANER RENE 摘要未注册，改选发表渠道；作者最终确认、artifact 公开、正式投稿和费用尚有外部事项。原修订稿、旧审稿与各次 gate 保留为历史证据，不构成第二份现役主稿。

## 学位范围与历史

- [治理基线](THESIS_RESEARCH_GOVERNANCE_BASELINE_v1.md)、[学位架构 v3](THESIS_RESEARCH_ARCHITECTURE_v3.md)、[工作包蓝图](THESIS_EXECUTION_BLUEPRINT_v1.md)保留历史依据；新阶段的执行与训练授权按[四项 Goals](LOOP_D_PUBLICATION_AND_THESIS_GOALS_20261021.md)衔接。旧数据 NO_GO、已停止面板及冻结证据不随新授权解除；现役架构和旧稿件骨架的统一更新属于 G4。
- [旧 THREADS 全文快照](../../memory/archive/THREADS_2026-10-21_pre_workspace_governance.md)保存历史原文；现役未决事项只在 [THREADS](../../memory/THREADS.md) 维护。
- Raw、failed/partial 响应、冻结结果、独立审查与历史账本保留来源身份。AI 语义评审不是人工 Gold、盲审或导师签字。
