# 大论文稿件骨架与小论文继承表（v1）

> 状态：`CURRENT_WRITING_SCAFFOLD / NOT_FINAL_THESIS` | 更新：2026-10-26
> 当前执行见[唯一指令](../docs/research/LOOP_D_RESEARCH_PROMPT.md)；B及后续no-go已执行。下一阶段/协作增量为待接受提案；本骨架不派发实验。

> 当前证据修正：[负责人复核](../docs/governance/audit/loop_d_control_review/PHASE_B_POST_RETURN_REVIEW.md)。27/26/25/0为集合匹配，R36/36为embedded抽取；禁止作为答案准确率或干净的ordinary续训方法负结果引用。

> 最新范围：[no-go复核](../docs/governance/audit/loop_d_control_review/DECISION_RESIDUAL_POST_RETURN_REVIEW.md)。389题仅record内text-only覆盖；未测的答案/风险/成本不写成无研究空间。后两章继续作为候选，先定位既有自然语义失效，再决定方法。

## 现役题目、问题与章节

暂定题目：**《面向文档智能任务的评测有效性与证据约束学习方法研究》**；待后两项贡献成立后与导师确认定稿。

总问题：评测认可的成功、模型学到的证据使用能力与实际可交付结果如何保持一致？

| 章节 | 当前内容 | 证据身份 |
|---|---|---|
| 第1—2章 绪论、相关工作与问题定义 | 测量有效性、反馈监督、证据绑定、风险与成本 | 背景与近邻，不冒称创新 |
| 第3章 测量有效性审计 | Paper E两案例、六构念、FinQA/FinRank边界 | 当前唯一较成熟的受限论文证据；尚未发表 |
| 第4章 证据约束反馈学习 | 普通SFT、候选负结果、评分与来源纠偏、后续合格纠正监督 | 历史14次与独立B两次child训练；ordinary有效续训未满足，新方法未成立 |
| 第5章 固定模型的可靠交付 | 原始/neutral/定位、门控、修复与风险覆盖全成本 | 旧错误池开发回放；无独立策略增量 |
| 第6章 综合验证、总结与限制 | 来源隔离、复现、成本及研究问题回答 | 系统工程提供证据，不作为独立算法创新 |

旧迁移、scope、state-card、补查等按动机/基线/限制整合，不因探索数量另设创新章。C2与C3须有独立问题、机制和确认；否则合并或替换。

## 当前写作口径与待补证据

- 最新控制是参考辅助、适配后2/2小控制；A已将缺尺度单位题排出可推断修复分母，并修安全尾部适配。唯一可修引用题0/1不能写成普遍诊断利用失败。
- 24/24旧错误池回放不是新来源确认；95/648重评分修正、旧训练表重叠及代理假成功的撤回须保留。
- 严格JSON全零和外部direct全零是早期版本结果，已有接口与stale-table纠偏，不能继续用作当前成熟度。
- C2当前优先候选为可见信息充分时的合格纠正与受限编辑比较，旧B实现已停止，且有效父模型/语义目标前提不合格，不是已确定学位方法。
- 2027年10月送审，具体日未知；7月完整初稿、8—9月导师修改和成果材料缓冲。

以下首轮结果保留日期化历史身份；部分结论被后续修正，引用现役结论须转向[STATE](../memory/STATE.md)及[自审证据](../docs/governance/audit/loop_d_control_review/RECONCILIATION.json)。

## 2026-10-24 首轮方法结果

在 TAT-QA 真实金融表格派生任务上完成六个 Qwen3-4B LoRA SFT 臂。同源 held-out 中，`evidence_cf` 的 direct paired completion 为 71.4%，比 `exec_cf`/`cheap_cf` 高 11.5 个百分点，但 source-cluster 95% 区间下界为 0。外部 TAT-QA source 上所有模型 direct paired completion 均为 0；工具执行冻结公式后，`exec_cf`/`cheap_orig` 为 35.7%，`evidence_cf` 为 28.6%。因此当前证据支持“公式/证据选择可学习”，不支持 evidence-dependency filtering 的独立增量。

严格 JSON 成功率为 0，导致 C3 强规则和严格风险策略均无可交付答案。post-hoc JSON 恢复后风险策略可在测试集提高覆盖率且未观察到错误交付，但样本仅 14 个 paired tasks，不能作为部署结果。下一方法实验应固定计算器和约束 JSON，先移除算术/接口混淆，再比较交付策略。

## V2 当前中文正文摘要

### 变化任务完成验证

在 Partridge 的真实迁移上，原仓库 42 项测试无法区分 parent 与 migration commit；一个调用目标 detector 却丢弃结果的反例也能通过旧行为检查。新版验证器对同一实际模块施加两种合法目标结果，要求下游返回值随目标结果改变，并把参考裁决与方法预测分开。该反例现被拒绝，但 alias-aware 静态合同加原仓库测试已经对六个对象全部分类正确，因此没有证据表明配对消费在此面板上提供额外准确率收益。自然 Qwen 输出只增加一行中性的 `bytearray` 转换，也未提供新错误类型。

### 验证决策与成本

真实动作比较显示，仅跑仓库测试仍会误放行 parent 和 source-fallback；加入静态合同或消费证据可以消除这些误放行。不同证据组合都达到 6/6，单次 wall-clock 只能作为开发诊断，不能支持稳定成本排序。复杂 planner 因此保持暂停。

### 证据失效与复用

真实 fixture 上的 PASS 不能无条件迁移到短输入范围：natural migration 和 alias 控制在两个范围间发生行为差异。策略探针把证据粒度纳入合同，只有逐输入绑定的旧证据才能 exact-input `REUSE`；同 regime 新输入使用 `PARTIAL_CHECK`，依赖或输入 regime 改变使用 `FULL_CHECK`，缺 fingerprint 使用 `DEFER`。在 20 个 development transition 上，scope 与 always-full 均为 15 CORRECT、5 ABSTAIN，probe 为 30 对 35。但零模型 post-hoc replay 表明，精确缓存＋miss 重验同样为 15/5 和 30 probes，且 20 个最终决策与 scope 完全相同。因此 5 次节省是 exact-input cache 效应，不是 scope 推断的独特收益；这些 transition 也不是自然 family。

### 状态表示与失效传播（开放探索）

STALE/CUPMem 公开材料进一步区分检索、状态传播和行动适配。CUPMem 已覆盖 user-only 状态抽取、显式/推断更新、write-time stale/unknown-current 裁决、propagation-aware search 和 constrained readout；本项目不把 state card 本身写成新机制。零模型检索比较显示，BM25 top-3 到 top-5 使全 400 个 dim1 的新证据召回从 `0.370` 提高到 `0.473`，新旧证据同时命中率从 `0.360` 提高到 `0.468`，冻结 16 UID 从 `3/16` 提高到 `8/16`。

固定 Qwen3.6 的 oracle 诊断中，显式 `M_old/M_new` 在 4 个开发 UID 上为 `4/4`，再加 `explanation` 仍为 `4/4`；这只能说明显式状态表示有诊断价值，不能作为可部署成绩。旧的首词极性代理可被固定 `No + STALE_DETECTED` 通过，故不作为语义准确率。严格、方法盲的辅助 judge 在 top-5 dim1 上得到 one-call facts `4/16`、通用 timeline `3/16`、state card `5/16`；在 8 个检索覆盖子集上为 `4/8、3/8、5/8`。

逐 UID 配对中，state card 相对 one-call 为 2 个独有成功、1 个独有失败、3 个共同成功、10 个共同失败，3 个不一致样本不足以支持稳定优势。dim3 行动检查在去除空答案、safe-unknown 和 judge 自相矛盾后，one-call 为 `3/16`，state card 为 `2/16`；检索覆盖子集为 `2/6` 对 `0/6`。因此 state card 仅保留为 dim1 表示候选，当前没有行动收益。下一门必须使用独立行动参考和真实下游结果；若简单事实抽取继续追平，则第三研究点收窄为测量与边界材料。

### 增量证据选择性补查（独立候选）

固定同一 BM25 top-3 后，400 个 UID 中 144 个同时命中旧/新证据。把 ranks 4-5 全部加入可达到 187/400，但只有 43 次扩展真正新增相关证据，357 次没有增益，平均上下文由 34,713 增至 64,338 chars。隐藏结果驱动的 oracle-selective 同样达到 187/400，却只需 43 次扩展、37,292 mean chars；这证明选择性补查存在成本空间，但 oracle 不可部署。

现有 visible cue 规则只识别 1/43 useful expansion，停止该候选。depth-2 tree 在 40/400 动作数下找到 5/43，但同预算随机期望为 4.3，精确 `P(X>=5)=0.434752`，所以没有识别到超出随机的信号；其所谓内层阈值也未用于外层最终决策，40 次动作并非成本匹配。模型 KEEP/EXPAND 接口两次均失败，记为 `UNEVALUATED_NO_VALID_DECISION`。RQ-A 只保留为独立候选，下一步必须使用 same-budget random、强廉价基线和固定 reader。

## 历史骨架（2026-09-22）
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
- G-D 的 146 列 Q3 复核只可写为 exploratory learnability evidence；raw R1/R2/ADJ、corrected ledger 与 hash 已封存，corrected 分布为 `51/58/37`。R1 看到 lineage 分组且 R2/ADJ 缺独立签署 visibility receipt，故不得写成 Stage D 闭合、RQ2 确认或 `DATA_GO`。
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
- 第 5 章只写方法/边界：D-B `licence_record` 已接受但仅覆盖 D-B annex 三件，仍无 confirmatory label_ledger、student result 或 `DATA_GO`；146 列 Q3 已完成 exploratory review，但不能替代确认性标签或训练证据。
- 第 6 章只写机制级门控与回填位；Phase 2、功效、gate-validation、rollback curve 仍是空槽，不得写成自学习效果。
- 第 7 章复现材料见 `paper/reproducibility_statement_arr_www_v1.md`；第 8 章后写时只汇总已验收边界和开放问题，不把目标贡献改写成结果。
- 第 5–6 章的 RQ2/RQ3/RQ4 臂、指标、门序与禁止写法见 `paper/thesis_rq2_rq4_execution_matrix_v1.md`；所有槽位在真实实验过门前保持空槽。

## 10. Route V structural-audit addendum (2026-10-05)

The Valentine full benchmark was audited through bounded ZIP Range reads only. Although it contains 551 complete pair directories, conservative shared-origin grouping yields 8 independent origin components, below the required 40. The archive also has no native trajectory/checkpoint bridge. The adapter route is stopped before download/implementation. Chapters 5-8 therefore retain Stage D/R/RQ4 as future-work slots and cannot be backfilled from this benchmark.

Track B evidence is explicitly within-origin and exploratory: Q3 is sealed with visibility exceptions and corrected `map_to=51 / skip=58 / hold=37`; Option A quarantines three invalid action references; Option B is the mandatory 9-cluster / 130-column pair-invalid sensitivity; B0-B4 v2 is a baseline/pilot surface, not student-training evidence. No Track B item confirms RQ2, Stage D, Stage R, RQ4, or the full E-D-R loop.

Future work requires a new exact source/task-definition annex with at least 40 conservative independent origin clusters, immutable paths/hashes/licence scope, native same-sample checkpoint evidence plus action/target and correctness, independent reviewer visibility receipts, non-empty split roles, and real variance-based power receipts. Chapters 5-8 remain open until those gates pass; the current negative boundary is `DATA_NO_GO / RQ2 NOT_IDENTIFIED`.
