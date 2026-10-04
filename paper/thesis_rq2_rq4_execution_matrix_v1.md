# 大论文 RQ2–RQ4 执行矩阵 v1

> 状态：后续章节规划/回填合同，不是实验结果 | 更新：2026-10-04
> 来源：`paper/research_story_v2.md`、`paper/method_theory_materials_v1.md`、`docs/handoff/2026-09-22-paper-research-next-phase.md`
> 原则：先满足数据与预注册门，再产生任何 RQ2–RQ4 数字；当前全部为空槽。

## 1 RQ2：checkpoint 筛选能否改善小模型动作学习

| 维度 | 执行合同 |
|---|---|
| 输入 | 同一母池内 checkpoint 证据、Q3 动作/目标标签、结果/正确性；FinQA 与 Valentine 不混成同分布数据 |
| 对照臂 | B0–B4 简单基线；A0 zero-shot、A1 unfiltered SFT、A2 checkpoint-filtered SFT、A3=A2+DPO（条件臂） |
| 必报 | action macro-F1、target exact、harmful-action acceptance、coverage、worst family、成本；自然量与 size/token/group-matched 两套口径 |
| 确认性族 | 质量非劣、安全非劣、风险约束下覆盖；族内 Holm，其余指标/家族标 exploratory |
| 门序 | SOURCE_GO → LABEL_GO → SPLIT_GO → POWER_GO → BASELINE_GO → MODEL_GO |
| 当前状态 | **空槽**。模型矩阵不是蒸馏结果；146 列 Q3 只有输入包；`DATA_NO_GO` / `NOT_IDENTIFIED` 不变 |
| 禁止写法 | 不得写“蒸馏已闭合”“RQ2 已确认”“学生优于基线”；4B 不作主实验或参数量消融 |

## 2 RQ3：经验能否安全积累

| 维度 | 执行合同 |
|---|---|
| 输入 | 相同候选序列；各臂独立维护规则状态，逐步重算 gain/collateral，不复用旧臂反事实分数 |
| 对照臂 | no-gate、gain-only、collateral-only、confidence-only、fixed dual gate、独立 gate-validation 增强门、rollback-versioning |
| 必报 | harmful consolidation、valid-rule retention、collision-column ACC、验证次数、回滚次数、累计成本、最坏家族 |
| 确认性族 | UID-any-harm 与 valid-rule retention；其他逐臂/逐家族指标标 exploratory |
| 门序 | Phase 2 共享候选流 + 功效分析 + 独立 gate-validation；sealed test 只读冻结快照 |
| 当前状态 | **空槽**。7/7 与 5/5 是机制级拒绝证据，不是稳定净收益；规则累计与收敛未证 |
| 禁止写法 | 不得把“能拒绝有害候选”写成“能持续安全改进”；若只能证明拒绝，Stage R 只写安全机制 |

## 3 RQ4：三阶段是否改善质量—成本—风险权衡

| 维度 | 执行合同 |
|---|---|
| 输入 | RQ1 评估信号、RQ2 学生策略、RQ3 规则状态与回滚记录在同一端到端协议中 |
| 对照 | 全闭环 vs 仅评估/仅蒸馏/仅门控的消融；质量、成本、缺陷可见性、回归风险同报 |
| 必报 | 端到端质量、验证/训练成本、风险覆盖、有害固化/回滚、最坏家族与不确定性 |
| 门序 | RQ2/RQ3 均过各自门 + 统一分析计划 + 独立验收后才允许写闭环收益 |
| 当前状态 | **空槽**。只能写系统设计与目标假设 |
| 禁止写法 | 不得用 RQ1 的成熟结果替代 RQ4 的端到端证据；不得把目标贡献写成已有闭环 |

## 4 共享边界

1. 独立单元统一为 lineage UID；proposal/train 内部 dev 可调参，gate-validation 只接受/回滚，sealed test 一次揭封，future replay 只读。
2. FinQA 与 Valentine 分命名空间报告；不把两条互补证据拼成一个主实验。
3. 所有阈值、家族、容差、停止条件先冻结；失败/null/adverse 原样保留。
4. 146 列 Q3 即使完成也只能作 exploratory learnability evidence，不改变上述 RQ 状态。

## 5 2026-10-04 execution addendum

### 5.1 Stage R confirmatory contrast

The confirmatory comparison is the strongest preregistered baseline selected from no-gate, gain-only, collateral-only, confidence-only, and fixed-dual using proposal/train only, versus the full `independent-gate-validation + rollback-versioning` gate. Gate/sealed results cannot select the comparator. The remaining arms are mechanism ablations.

All arms consume the same hash-bound candidate order and maintain independent rule state. Gain, collateral, and gate delta are recomputed on each arm's current state. Predeclared order perturbations use the same candidate multiset and only alter order. Required trajectory metrics include time/step to first harmful consolidation, maximum validation-set drawdown, first rollback step, and recovery step.

### 5.2 RQ4 causal symmetry

Use C0 teacher/no persistence, C1 teacher/strong gate+rollback, C2 student/no persistence, and C3 student/strong gate+rollback. Compare teacher/student at fixed persistence and persistence/no-persistence at fixed actor using the same candidate stream and evaluation time. Without independent RQ2 and RQ3 evidence, these groups remain design slots and cannot support a closed-loop claim.

### 5.3 Execution annexes

Q3/B0-B4 preconditions are in `docs/experiments/2026-10-04_q3_b0_b4_execution_plan.md`. RQ2 identification and the data/licence/split/power application are in `docs/datasets/2026-10-04_rq2_identification_and_acquisition_card.md`. Neither annex authorizes execution.
