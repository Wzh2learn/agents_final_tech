# 大论文稿件骨架与小论文继承表（v1）

> 状态：写作骨架，不是完成稿 | 更新：2026-09-22
> 原则：小论文先交；大论文复用其证据，但不得阻塞小论文送审。

## 暂定总题目

面向长流程文档智能系统的评估引导蒸馏与验证门控自进化方法研究

## 总研究问题

长流程文档智能系统中，如何先获得可信的过程级评估信号，再把这些信号迁移给低成本小模型，并将稳定经验安全固化为可验证、可回滚的规则，使系统持续进化？

## 章节—创新—证据映射

| 章节 | 核心内容 | 继承小论文 | 大论文必须新增 | 当前状态 |
|---|---|---|---|---|
| 第 1 章 绪论 | 问题、意义、研究问题与贡献 | 小论文 motivation 与限制 | 学位论文场景、研究边界、章节关系 | 可写 |
| 第 2 章 相关工作与问题定义 | 长流程评测、元评测、故障注入、语义裁判 | 小论文 Related Work | 更系统的分类体系与术语定义 | 可写但需扩充文献 |
| 第 3 章 判别力感知的分层评测 | 检查点树、契约/裁判分工、聚合与校准 | SP-RQ2、SP-RQ3 | 成本模型、强基线、第二类长流程 | 中高成熟度 |
| 第 4 章 缺陷可见性与静默吸收 | 可见性谱、等价类、盲区归因 | SP-RQ1 主体结果 | 强度梯度、跨数据流复现、匹配器边界 | 中高成熟度 |
| 第 5 章 评估引导的小模型蒸馏 | checkpoint 动作过滤、规则候选蒸馏、质量—成本 Pareto | 小论文目标主线，但当前尚无训练结果 | 8B 主学生、4B 仅 smoke、SFT/条件 DPO、四层隔离、未见家族 | 低成熟度，先数据/可学性门 |
| 第 6 章 验证门控的规则自学习 | 候选生成、gain–collateral + 独立 gate-validation、固化与回滚 | 小论文第三阶段 | 七类门基线、功效、碰撞控制和独立 future replay | 机制级，效果未闭合 |
| 第 7 章 系统实现与综合实验 | 工程架构、复现、成本和综合分析 | 复用证据链与工具 | 跨章节统一实验协议 | 待整合 |
| 第 8 章 总结与展望 | 结论、适用边界、后续工作 | 继承小论文限制 | 总体回答与学位贡献闭环 | 后写 |

## 学位创新点口径

1. **TH-I1：判别力感知的分层评测。** 当前可主张可审计的证据分解；额外定位收益必须在多个输入敏感 leaf 的场景中验证。
2. **TH-I2：缺陷可见性与静默吸收分析。** 当前证据支持按缺陷家族揭示盲区；普遍性需要第二数据流和等价类边界实验。
3. **TH-I3：评估引导的小模型动作策略蒸馏。** 当前有训练前模型矩阵（执行记录：`docs/experiments/2026-08-18_small_model_matrix_design.md`、`2026-08-19_small_model_matrix_c1c2.md`、`2026-08-21_small_model_matrix_c3.md`、`2026-08-24_t4_14b_anomaly_retest.md`）、文献和偏好对，没有学生训练结果；记录不是完整推理轨迹，必须补齐规则候选学习证据才能成为创新点。
4. **TH-I4：验证门控的规则自学习。** 当前只是机制可行性（门拒执行记录：`docs/experiments/2026-08-28_adversarial_arm_experiment.md`、`docs/experiments/2026-08-29_collision_expansion_experiment.md`）；没有强基线、功效分析、独立 gate-validation 与 sealed test/future replay 证据前，不写成已证实的效果创新。

视觉跨层补盲不再单列创新点；通过预注册门后作为 TH-I2 的扩展，否则只记为失败边界。

## 写作与实验顺序

本骨架只管章节及证据继承，执行唯一依据是 `docs/handoff/2026-09-22-paper-research-next-phase.md`，不另设大论文排期。

1. 三阶段故事已确认；用现有评估子稿和方向说明组成近期导师包，不等蒸馏结果。
2. 先审计动作标签、独立 uid、四层数据边界与功效，再做简单规则/分类器可学性探针。
3. 在训练前完成同一候选流上的 TH-I4 强门控基线；逐臂维护规则状态，不能沿用旧臂分数模拟其他臂。
4. 离线门通过并获窗口批准后，4B 仅验证训练链，8B 跑主实验，DPO 条件执行；A1/A2 同报自然量与 size/token/group-matched 比较。
5. 冻结系统后做 sealed test 只读终评，future replay 单列；再按原计划决定统一稿或评估保底稿，最后形成第 7–8 章。

proposal/train（含内部 dev）、gate-validation、sealed test、future replay 的 uid 必须隔离；sealed test 不参与接受、阈值或 early stopping。正式新实验数字由 GB10 产生，本地仅分析既有事实和验证代码合同，另一台服务器环境本轮不探测。

## 不得混写的边界

- 小论文的 matched-FPR null 不能写成层级协议优于扁平协议。
- 小模型零样本矩阵不能被称为蒸馏结果。
- 小论文的门控案例不能替代大论文规则自学习的效果验证。
- 第二数据流与第二 scorer 未完成前，不作跨域或普适性主张。
- 专利状态确认前，所有稿件仅限内部审阅。
- G-D 的 146 列 Q3 复核只可写为 exploratory learnability evidence；当前仅有输入包和零 gold 可见性证据，尚无 R1/R2 判定、裁决、label ledger 或指标，不得写成 Stage D 闭合、RQ2 确认或 `DATA_GO`。
- V2-3 已正式关闭步级重执行路线；不得重开 v3、更换读法或申报 FinQA 官方算子材料来挽救原结果。

## 章节级框架加记（§x.y 级，2026-09-24；门注记更新于 2026-09-25；v1 正文不回改）

> 口径：每节给出「继承锚点 / 必须新增 / 证据指针 / 门依赖 / 状态」。空槽位与
> `paper/figure_plan_v1.md`、`paper/teacher_review_finalization_v1.md` 的回填位一一对应；
> 门通过前任何节不得写入数字或已证表述。

### 第 3 章 判别力感知的分层评测

- 3.1 检查点森林与打分合同｜继承：小论文 §3.1、`config/eval_checkpoint_trees.json`｜新增：逐叶成本模型（证据字节/运行时）｜证据：`logs/graph/eval/checkpoint_discrimination_tables_v2.json`｜可写
- 3.2 契约/裁判分工与泄漏保护｜继承：小论文 §3.1/§4｜新增：裁判分辨率与样本上限的形式化｜证据：`logs/graph/eval/d3_stage_b_*`｜可写
- 3.3 聚合与校准（Algorithm 1）｜继承：小论文 §3.3、`docs/experiments/2026-09-20_algorithm1_lines_vs_impl.md`｜新增：强基线对照表｜门：Phase 2 强基线｜可写（对照表空槽）
- 3.4 阈值敏感与可复现性｜继承：小论文 §5.3｜新增：跨种子/跨匹配器边界｜证据：`t2_visibility_sensitivity.json`、`d2_cross_matcher_*`｜可写

### 第 4 章 缺陷可见性与静默吸收

- 4.1 三分类结果与家族剖面｜继承：小论文 §3.2/§5.1、大论文 §2.9｜证据：`t2_visibility_sensitivity.json`｜可写
- 4.2 盲区归因（评测器盲 vs 无效变异体）｜继承：小论文 §5.1｜证据：`d1_mutant_validity_audit.json`｜可写
- 4.3 matched-FPR 与仿射等价（退化情形标注）｜继承：小论文 §5.2｜证据：`d3_matched_fpr_stage_a/b`｜可写；一般性情形空槽（OP-1）
- 4.4 强度梯度与跨数据流复现｜新增｜门：第二数据流（OP-1）｜空槽

### 第 5 章 评估引导的小模型蒸馏

- 5.1 动作事件抽取与 checkpoint 过滤｜继承：`research/vgmc_exp1.py` 事件 schema｜新增：过滤统计｜门：SOURCE_GO（2026-09-25 已过）/SPLIT_GO（分层仪器就绪且四层几何可填，但动作包因注册表 role_fit 与十簇规模未通过，见开题报告 §7.3）｜空槽
- 5.2 监督/偏好数据构造｜继承：`research/dpo_pairs_v0.py`（60 对，仅审计素材）｜门：LABEL_GO（2026-09-25 实测：D-C 批准来源内该门无可用载体，成因与裁定项见开题报告 §7.3）｜空槽
- 5.3 8B 主学生与 4B smoke｜门：MODEL_GO｜空槽
- 5.4 质量—成本 Pareto 与 A1/A2 双口径｜空槽（FIG-D-1/FIG-D-2）

### 第 6 章 验证门控的规则自学习

- 6.1 候选生成与 gain–collateral 双门｜继承：小论文 §5.5、`research/phase2_rule_gate_replay.py` 合同｜机制级可写
- 6.2 独立 gate-validation 与七类门基线｜门：Phase 2｜空槽
- 6.3 固化、版本化与回滚｜机制级可写；回滚曲线空槽（FIG-R-2）

### 第 7 章 系统实现与综合实验

- 7.1 工程架构与复现合同｜继承：`scripts/research/*`、`docs/governance/2026-09-24_gb10_experiment_safety_gates.md`｜可写
- 7.2 跨章节统一实验协议｜继承：预注册件、`paper/dataset_protocol_v1.md`｜可写
- 7.3 综合分析（质量/成本/可见性/回归四轴）｜空槽

### 第 8 章 总结与展望

- 8.1 结论与适用边界｜继承：小论文 §6/§7｜后写
- 8.2 后续工作｜继承：`paper/method_theory_materials_v1.md` §10 的 OP-1..OP-5｜可写

## 9 当前证据指针（2026-10-04，零模型）

- 第 3-4 章可直接继承评估保底稿与既有 artifact；matched-FPR null、OCR 盲区与停止条件保持原样。
- 第 5 章只写方法/边界：D-B `licence_record` 已接受但仅覆盖 D-B annex 三件，仍无 label_ledger、student result 或 `DATA_GO`；146 列 Q3 仍是“已装配未复核”的 exploratory 输入包。
- 第 6 章只写机制级门控与回填位；Phase 2、功效、gate-validation、rollback curve 仍是空槽，不得写成自学习效果。
- 第 7 章复现材料见 `paper/reproducibility_statement_arr_www_v1.md`；第 8 章后写时只汇总已验收边界和开放问题，不把目标贡献改写成结果。
- 第 5–6 章的 RQ2/RQ3/RQ4 臂、指标、门序与禁止写法见 `paper/thesis_rq2_rq4_execution_matrix_v1.md`；所有槽位在真实实验过门前保持空槽。
