# SANER Scientific Adjudication v1

> 日期：2026-10-12。角色：作者级科学审查 / claim 裁决。
> 状态：`REVIEW_COMPLETE / RECOMMENDED_REVISIONS_NOT_APPLIED`。
> 对象：当前 SANER RENE Route A 稿件、C1–C3 claim matrix，以及战略审查 §4.2 的 P0/P1。
> 基线：Git HEAD `bb9392518791f0c9fcced3eb81002814e1d1941f`；以本轮工作区实际文件为准。
> 范围：只裁决现有证据与现有 claim。未改稿、未改 claim authority 或历史结果、未新增实验；不提出新路线或执行工作包。本轮仅新增本文档。

## 1. 总裁决：现有核心表述不能原样签署，收窄后的论文仍有科学成立空间

**不应把上一轮的 P0/P1 自动解释为整篇论文不成立。** 现有证据仍能支撑一篇有明确边界的测量有效性审查：指定 observation surface 上的族级非响应、单响应叶下的评分结构关系、显式阶段签名的构造边界，以及一次测量对象未对齐的失败迁移。它们不能支撑通用有害盲点、层级定位能力、自然故障分布或长程智能体的一般经验结论。

**真正阻断当前核心论证的是 C2 对 matched-FPR 的概括。** “没有唯一部署阈值”不能推出“正仿射耦合下的对应检测差值也不可确定”。这需要改写贡献级 claim。non-direct 的“零阶段信息”同样必须撤回，但它是局部解释错误，不使正式多叶实验及其历史分数失效。

本轮没有发现必须通过新增实验才能完成下述 claim 修复的事项。修复后是否达到录用所需的新颖性与影响力，仍是 reviewer 的判断；这里裁决科学成立范围，不预测录用。

裁决等级的含义：

| 等级 | 本文含义 |
|---|---|
| **BLOCKING** | 当前核心 claim 存在逻辑错位，作者不能原样签署；必须改变 claim 后再外发。不是宣告全部数据无效。 |
| **MAJOR** | 必须纠正实质解释、贡献边界或证据归属；可能保留全部数字，不要求新增实验。 |
| **MINOR** | 概念用词或事实时态需准确化，不改变主要科学结论；也不能因此放任事实错误。 |
| **NO_CHANGE** | 现有结论在已声明范围内成立，保留其数字、状态和边界。 |

以下用 **[E]** 标记已存在的实现、工件或结果证据，**[D]** 标记由定义/代数得到的推论，**[U]** 标记现有证据未回答的对象。没有把替代解释升级为事实。

## 2. 裁决总表

| 编号 / 上轮问题 | 主裁决 | 对稿件成立的实际影响 | claim-level 原则 |
|---|---|---|---|
| A1 / P0-1：non-direct 信息 | **MAJOR** | §6.3 的零信息结论错误；多叶实验、满分及冻结 ablation 分数仍有效。 | 撤回 “no stage information”；改为保留 M vs R/N 的部分信息，但不能完成三类区分。 |
| A2 / P0-2：matched-FPR | **BLOCKING** | C2、贡献段和结论把工作点未确定与结构等价混为一谈，需重写核心分句。 | 分别报告结构等价、校准面退化、未选定部署规则；不能泛称 equality 不可识别。 |
| A3 / P1-1：OCR-like 0/13 | **MAJOR**（解释披露）；原始非响应 **NO_CHANGE** | 0/13 是有效观测结果，但缺少良性吸收的具体证据会误导读者将其理解为有害漏检。 | 保留非响应；披露单 judge 的 13/13 equivalent，既不据此宣布全部无害，也不将非响应当有害 false negatives。 |
| A4 / P1-2：8 项 / 5 分歧 | **MAJOR** | 异质比较不能承担单一 oracle 分歧率及排除随机噪声的机制结论。 | 拆成 7 项 judge–DR4 比较与 1 项 visibility–equivalence 比较；撤回合并机制推断。 |
| A5 / P1-3：FinQA | **MAJOR**（证据解释冲突）；正文错配结论 **NO_CHANGE**；`undefined` **MINOR** | 复算通过不能认证迁移成立；“谓词未定义”也不准确。 | 保留 V/D/O 与 accepted autopsy；谓词有定义，所读 result 字段没有随扰动重算。 |
| A6 / P1-4：long-horizon AI | **MAJOR**（经验范围）；作为动机 **NO_CHANGE** | 当前标题和结尾容易赋予未经测量的长程系统外推。 | 经验对象改为 staged document-intelligence evaluator；long-horizon 仅保留为动机。 |
| A7 / P1-5：artifact 已发布 | **MINOR**（非科研事实） | 不使实验失效，但现有仓库记录不能认证 “are released / provided to reviewers”。 | 发布时态必须与可核验状态一致；与科学贡献、复算通过分开。 |

## 3. A1：non-direct leaves 有部分信息，缺的是完整三类可区分性

**裁决：MAJOR。撤回零信息；保留正式结果及其构造边界。**

### 3.1 证据与错误发生的位置

[E] 冻结 ablation 报告：full vector 与 direct three-leaf codebook 均为 macro-F1/top-1 = 1.0；non-direct 为 0.3333/0.3333，tie rate = 0.6667。原规则将距离平局计为错误；R、N 的 144 行落入平局，M 的 72 行可区分。[N1][N2]

[E] 非直接叶 `parse.table.regression` 的响应是 M=72、R=0、N=0；现有 post-hoc 表给出 mutual information = 0.9183 bits，并明确说明它可识别 M、R/N 碰撞。该 MI 是已有探索性派生结果，不新增为确认性主结果。[N1]

所以，当前 §6.3 的 “the remaining hierarchy carries no stage information” 与已有响应表矛盾。**三类准确率在 tie-as-incorrect 下恰好等于 1/3，不意味着观测与标签独立。** 它描述的是该分类/平局规则下的分数，不是信息量为零的检验。[D]

### 3.2 推荐的修改原则

- **必须撤回：** “non-direct carries no stage information”、将 chance-level score 解释为完全没有信息。
- **不得新增推断：** 将 full vs non-direct 差距归因于 hierarchy 创造了信息。现稿已经否认 emergent localization，这条边界应保留，不能错述为现稿已有的主张。
- **必须改写：** 非直接观测可区分 M 与 R/N，不能区分 R 与 N；因此没有完成三阶段定位。
- **可保留：** 0.3333 与三类 chance top-1 数值相等，但必须紧邻报告 tie rate 和部分可区分性；不要把 macro-F1 的同数值参考也包装成一般的“随机性能证明”。
- **可保留并加强：** full 和 direct 同为 1.0，当前结果没有显示 full 对 direct codebook 的性能增量；它证明冻结构造中显式观测携带阶段签名，没有证明层级组织带来额外定位能力。
- **不能通过改评分救叙事：** 不重新打破平局、不更换 historical metric、不宣称另一套评分下的新性能。正式定位实验和 post-hoc ablation 的证据身份保持区分。

可采用的 claim 句意，而非本轮直接替换稿件：

> Under the frozen tie-as-incorrect rule, non-direct leaves yield top-1 accuracy and macro-F1 of 0.3333 with a tie rate of 0.6667. They distinguish M from R/N but do not distinguish R from N in this construction.

**更强之处：** 从“删除后什么都没有”改为准确指出剩余观测的碰撞位置。这个解释更可核查，不提高性能 claim，也不否定原实验。

## 4. A2：把结构等价、FPR 约束和部署工作点拆开

**裁决：BLOCKING，针对当前 C2 的 blanket non-identifiability 分句；不是否定 affine/rank 结果。**

### 4.1 四个不同对象

| 对象 | 现有证据与正确结论 |
|---|---|
| 分数/排序结构 | [D] 固定单响应叶、未舍入的当前加权构造给出 `H = aF`，`a=0.375>0`；一般正仿射式为 `H=aF+b`。结构关系不依赖 clean 校准是否完成。[F1][F2] |
| clean 经验 FPR | [E] 2,382 个 clean contrastive 分数均为 0；代码对同一个确定性计算作 `h-h_repeat`，所以这是构造退化，不是增加相同样本即可解决的 power 问题。[F1][F3] |
| 单独部署工作点 | [E] 现行 clean-only 程序没有选出唯一部署工作点。[D] 多个正阈值的经验 FPR 都为 0，却可给 harmful 样本不同决策；单独 TPR 不能仅由该 FPR 约束唯一决定。 |
| 对应决策/ROC 与协议差值 | [D] 精确正仿射关系、相同比较符、按变换配对阈值时，两个检测集合相同；这个结论不需要先选定唯一数值阈值。 |

对于精确的正仿射分数及一致的严格比较符：

```text
H(x) = a F(x) + b, a > 0
1{F(x) > t} = 1{H(x) > a t + b}
```

因此，在同一批正/负样本上，对应阈值给出相同 FPR 和 TPR；可达到的 ROC 工作点集合相同，对同一个 `FPR≤α` 预算的最优可达 TPR 也相同。[D] **这是一条结构推论，不是新完成的 clean-calibrated 性能实验。**

必须同时保留一个反向限制：**“两个任意阈值具有同样 FPR”不保证它们具有同样 TPR。** 在 clean 全为 0 时尤其如此。等价结论针对对应阈值/相同秩截点，或明确保持该对应关系的校准规则；不针对随意独立选出的两个阈值。

### 4.2 `FPR=0.05` 与 `FPR≤0.05` 不能互换

[D] clean 分数全相等时，确定性 score threshold 在这个面板上只能产生经验 FPR 0 或 1，不能恰好达到 0.05。现有分析没有实施随机化 tie policy，不能把随机化后可能达到的期望 FPR 当已有结果。

[D] `FPR≤0.05` 则完全可行：所有正阈值都给 FPR=0。因此问题不是这个预算“不可能满足”，而是约束没有唯一选择部署规则。旧 D3 的 max-TPR 分析明确用 `≤α`，同时用 harmful scores/TPR 搜索阈值；它不能升级成 clean-only 校准。[F2]

### 4.3 现行程序的状态，不能上升为一般识别定理

[E] 复分析把 `positive_clean_flat>0 and positive_clean_layered>0` 用作 `threshold_identifiable` 标志。这是此脚本的判定，不是一般阈值可识别性的充分必要条件。[F1]

[E] protocol 要求“只用 clean scores，选择使 TPR 最大的最小正阈值”。clean 数据不提供 harmful TPR；连续正数集合也未必有最小元素。候选阈值集、选择规则与 tie convention 没有形成足以产生唯一工作点的完整定义。[F4]

所以作者应写 **“the registered clean-only procedure did not select a unique deployment operating point on this degenerate clean panel”**，而不是将脚本的 `UNIDENTIFIED` 状态认证为普遍的统计非可识别性结果。没有正 clean support 不阻止另一个预先完整定义的规则给出阈值；有正 support 也不自动保证唯一。这是对当前结论范围的解释，不是建议本轮新增校准程序。[D]

### 4.4 舍入与比较符的边界

[E] 记录分数经过舍入：90 个正分数对的斜率相对 0.375 最大偏差约 `8.75e-08`；harmful 面板 Spearman=1，已核六个配对网格点在各 fold 计数相同。新复分析用 `>`，旧函数存在 `≥` 及数值容差。[F1][F2][F3]

因此应分开写：未舍入构造的代数关系、记录样本的秩一致、已核网格的一致。**不能声称舍入后任意实数阈值都严格满足 `θH=.375θF` 的逐行等价。** 精确正仿射关系对一致的 `>` 或一致的 `≥` 都成立；混用比较符或不按尺度变换的容差不在该证明内。

### 4.5 作者应撤回、保留和重写什么

- **撤回：** C2/结论中的 “clean-only matched-FPR equality is not identifiable” 作为无条件总判断；摘要由此导出的 blanket “cannot rank at matched FPR” 也要拆开，不能暗示结构等价未知。
- **保留：** 单响应叶下的结构诊断；没有 hierarchy 排序优势的证据；当前 clean-only 程序未完成唯一部署工作点选择。
- **重写贡献：** 从一个笼统的 “matched-FPR non-identifiability result”，改为 **正仿射/秩结构等价诊断，加上 clean 校准面退化及部署规则未确定**。
- **不恢复：** 旧 90/111 和历史 `[0,0]` 仍只是历史敏感性材料，不能因为结构推论正确就升级为 clean-calibrated 确认性性能证据。
- **不外推：** 多响应叶的其他权重、非线性规则、missingness 或不同观测，不受当前单叶推论保证。

推荐的 claim 句意：

> In the frozen single-responsive-leaf comparison, the unrounded hierarchical contrastive score is a positive rescaling of the flat score, and the recorded scores retain identical ranks. This establishes a structural equivalence of corresponding decisions, not a newly calibrated performance estimate. The zero-by-construction clean panel leaves the registered deployment operating point unresolved; that calibration degeneracy does not negate the structural equivalence.

**更强之处：** 论文不必把可推导的相同区分能力写成“不知道”。它可以明确解释原始 flat/hierarchical 差距为何不能代表排序质量差距，同时诚实声明没有完成新的部署校准。

## 5. A3：OCR-like 0/13 是非响应；是否是需要修复的盲点取决于目标

**裁决：原始非响应 NO_CHANGE；解释披露 MAJOR；有害漏检结论不成立。**

### 5.1 三层结论

| 层次 | 可签署的结论 | 不能签署的结论 |
|---|---|---|
| observation surface | [E] 冻结 scored surface 在已测试阈值下未记录 13 个 OCR-like 注入，涉及 11 个 clusters。 | 系统在所有内部表示上都看不见这些输入变动；所有 OCR 错误都不可见。 |
| benign invariance / absorption | [E] 既有单 judge 在 table-context reader-referent 契约下把这 13 个案例全部判为 equivalent；已有 autopsy 还报告数值不变。它支持良性吸收这个具体替代解释。[O1][O2] | 13 项已被独立任务金标准证明全部无害；该 judge 的判据优于 canonical-form 判据。 |
| harmfulness / false negative | [U] 这些非响应是否遗漏了任务应识别的有害变化，现有证据没有独立裁定。 | 0/13 就是有害错误上的 detection recall=0，或 evaluator 具有已验证的有害盲点。 |

“blind spot”如保留，只能明确限定为 **对这些构造扰动的操作性观测非响应**。推荐主表述仍用 “unobserved on the frozen scored surface”，避免术语自行带入“本应报警”的规范判断。

类型级 harmful 标签不是独立的逐例 harm 证据：D1 的类型白名单、DR4 的 family-design-intent 与 residue 规则都参与过归类。autopsy 中“4 例仅有 residue、无概念丢失”和“13/13 数值不变”削弱了把所有非响应当有害漏检的解释，但也没有回答所有任务后果。[O2][O3] 不要复述历史叙事中过宽的“全部实例条件不变”；原始 A14 的 canonical-keyset 一致仅为 12/13。[O3]

### 5.2 推荐的修改原则

- 在正文解释 0/13 时直接披露 **13/13 single-judge equivalent**，不能只留一句抽象的 criterion-dependence caveat。
- 把 canonical-form preservation 与 reader-referent recoverability 写成不同测量目标；它们的分歧说明 contract-sensitive labels，没有独立标准就不能选出“正确 oracle”。
- 保留 0/13 injections 与 0/11 cluster-event 两个不同 estimand，以及已有区间的独立性假设；不把零事件/退化 bootstrap 当成总体零概率。
- C1 的“构念区分 + 指定 evaluator 的族级边界”保留；将 harm 与非响应分开，反而使 C1 更扎实。

推荐的 claim 句意：

> All 13 OCR-like perturbations were unobserved on the frozen scored surface, while the existing single judge classified all 13 as referentially equivalent under its table-context contract. This supports benign absorption as an alternative interpretation, not independent ground truth; non-response alone does not establish harmful false negatives.

**更强之处：** 非响应本身不是 detector 的失败判决；作者准确说明什么目标下 invariance 可能合理。论文的贡献成为审计测量目标，而不是把更多“看不见”都算作缺陷。

## 6. A4：5/8 可保留为历史异质 tally，不能作为同一机制的证据

**裁决：MAJOR。改变的是解释单位，原始案例与原表不需要删除。**

[E] 八项表中的七项才是 judge–DR4 对照：四项分歧、三项一致。第八项 `Revenues→sales` 没有 judge call，比较的是 deterministic visibility 与 DR4 equivalence；原文已经明确标记 zero calls。[O1][O4]

因此：

- **撤回：** 将 5/8 称为同质 oracle disagreement rate；以这八项断言所有分歧都来自 canonical-vs-reader 轴。
- **撤回：** “rather than appearing as random case-level noise” 所暗示的排除性机制判断。少量选定案例及同形案例的一致不能排除判据效应之外的变异，也没有完成噪声模型比较。
- **改写：** 七项对照可说明这些案例在各自标准下存在四项不一致；第八项单独说明 visibility 与 equivalence 不是同一构念。不要用两类 tally 的合计比例解释单一 latent truth 的测量误差。
- **保留：** 标签会随契约和粒度变化；但 criterion difference 是有定义依据的解释，不能据此宣称已独立证实一个排他性机制或 judge 正确性。

这不会推翻 C1，反而要求作者真正实行 C1 所说的构念分离。摘要无须新增 4/7 数字；正文与任何承担机制论证的 caption/ledger 表述需同步准确化。

## 7. A5：FinQA 是未完成有效迁移测量，谓词不是未定义

**裁决：正文 §5.6 的主要错配解释 NO_CHANGE；证据链冲突 MAJOR；C3 的 `undefined` MINOR 精确化。**

### 7.1 最准确的对象级结论

[E] 注入器改变 source/evidence、program op 或 args，未据变动重新计算 step `res`；terminal answer 又直接读取保留的末步 `res`。scorer 明确计算各字段差异，runner 的定义是：[Q1][Q2][Q3]

```text
V = any(observation_vector[field] == 1)
D = step_result_consistency == 1 OR answer_consistency == 1
O = answer_consistency == 1
```

所以 **D 是有定义、能执行、能复算的布尔谓词**，并非 undefined。错配在于它读取的下游 result/answer 字段没有沿注入后的执行路径重新生成。`V=89/89, D=0/89, O=0/89` 是这个载体构造上的有效描述；它没有提供关于执行扰动语义后 detector 表现的有效能力估计。[D]

特别要区分：**“观测到的 D 频率可计算”与“目标 detection ability 已得到估计”不是同一件事。** 同样，O=0 只表示存储 answer 字段未变，不能宣告执行后语义结果无害。当前 scorer 自己明确不作 semantic-correctness claim。[Q2]

推荐主结论：

> The predicate is well-defined on stored result fields, but those fields were not recomputed from the perturbed program. The observed V/D/O pattern is reproducible evidence of a measurement-object mismatch in this attempted transfer, not an estimate of detection ability on executed perturbations.

### 7.2 必须纠正的证据继承

[E] 旧 Loop C recompute audit 的 §5–§6 将该 pattern 称为 “separation transfers” 和 “confirmatory-grade evidence ... not of one dataset or one scorer”。后来的 accepted autopsy 明确禁止将此流用于 separation-transfer 或 protocol-blindness claim。[Q4][Q5]

作者级裁决是：

- **NO_CHANGE：** 复算一致、89/30 的样本/cluster 记录、正式 `SECOND_FLOW_MIXED` 分类及历史 PASS 状态；它们认证计算与记录，不认证目标测量成立。
- **MAJOR 撤回：** 旧 audit 的正迁移/跨 scorer 科学解释作为当前论文证据。引用旧 audit 时必须限定为 numerical reproduction，并明确科学解释已由 accepted autopsy 取代。
- **MINOR 改词：** C3 的 “predicate was undefined by construction” 改为“well-defined predicate on downstream fields not causally recomputed for the perturbation”。
- **MAJOR 收窄：** §6.3 的 “the comparison is not estimable” 指向目标能力/迁移结论，不要让读者以为 V/D/O 数字本身不可计算或不可复现。
- **NO_CHANGE：** 将 causal alignment 写成测量设计前提，不能写成已通过对照实验验证的因果定律或新方法；也不因这个错配诊断排除 scorer portability、threshold transfer 或 corpus shift 等其他问题。

**更强之处：** 源代码足以定位本次对象错配，而不只是笼统猜测 “consistent with mismatch”。但机制定位的确定性不能转换成 detector 无能、无害性、跨域迁移或通用因果方法的确定性。

## 8. A6：long-horizon 超过当前经验范围，应收回到动机位置

**裁决：经验范围 MAJOR；动机 NO_CHANGE。**

[E] 当前主证据来自冻结文档/表格 evaluator、合成 header perturbations、契约导出的 M/R/N 签名，以及一次未对齐的 FinQA 迁移。没有操纵 horizon length，也没有测量真实 agent 轨迹、状态积累、长程误差传播或不同长度下的变化。[M][C]

因此：

- **推荐改标题范围：** `Visibility Is Not Detection: Auditing Observation Boundaries in Staged Document-Intelligence Evaluation`。这是作者裁决建议，本轮没有改标题文件。
- **摘要开头：** 先说 staged document-intelligence evaluation 的实际对象；long-horizon/tool-using systems 可作为问题动机，不作为这些实验已覆盖的总体。
- **结论：** 经验结论落在本 evaluator 与受控扰动。面向其他 staged systems 的启示应写成测量设计建议，不能用 “therefore” 把一个窄实例升级成长程系统经验定律。
- **不必增加新实验来保住标签：** 当前论文不需要 long-horizon 性质才能成立；撤掉该经验外衣不会删掉现有结构诊断与 autopsy 的价值。

这改变标题/摘要的适用域与结论外推，不改变 95/118、72/216、89/30 等原始记录，也不取消 long-horizon 作为引出问题的背景。

## 9. A7：Data Availability 是事实校正，不应与科学证据混算

**裁决：MINOR，外发前必须准确。**

[E] 稿件写 “are released” 并称材料已通过匿名 repository 提供给 reviewers；当前 closeout 则列明匿名 artifact 发布计划未执行、URL 待建立。[M][H] 本轮没有进行外部 URL 可达性核验，因此不能替作者认证已发布，也不对工作区之外的发布状态作断言。[U]

原则是按实际状态写“已提供”“随稿提供”或“计划提供”，不能把编译完成、内部 manifest 齐备或复算 PASS 等同于 reviewer 已能访问。DOI 的未来承诺也不能补足当前事实。

它不改变 C1–C3 的科学内容、abstract 或结论；属于 artifact availability 的事实一致性。本文不执行发布、上传或投稿。

## 10. 哪些修改改变 contribution / abstract / conclusion

### 10.1 三条贡献的最终处置

| Claim | 作者级处置 | 修订后的贡献边界 |
|---|---|---|
| **C1** | **保留，不拔高。** OCR 与异质案例的解释需修正。 | visibility、detection、contract-relative harmfulness 是不同对象；当前 evaluator 有具体族级观测边界。0/13 不自动是有害失败。这是具体审计的贡献，不把概念区分本身包装成新理论。 |
| **C2** | **实质重写。** 删除 blanket equality non-identifiability；保留多叶结果但纠正零信息。 | 单响应叶的结构等价解释原始分数差距；退化 clean 面板下现行部署规则未选定。多叶构造有显式阶段 codebook，non-direct 仍有部分信息；未显示 full 超过 direct 的定位性能。 |
| **C3** | **保留失败迁移 autopsy，收回正迁移证据继承，改准谓词。** | 一次对象未对齐的测量迁移可以数值复现，却没有测量目标 detection ability。causal alignment 是设计前提；不是已验证方法、普遍定律或 FinQA blindness。 |

### 10.2 修改传播表

| 裁决 | Contribution / claim matrix | Abstract | Conclusion | 其他必须准确的位置 |
|---|---|---|---|---|
| A1 non-direct | C2 的“无 hierarchy 增量证据”保留；删零信息推断。 | chance-level 后须说明 tie/部分信息，或直接用“不能区分 R/N”替代有歧义的解释。 | 若概括定位，保留 construction-bound；不能写 remaining leaves 无信息。 | §5.5、Figure 3 caption、§6.3。历史数字不改。 |
| A2 matched-FPR | **改变贡献分句：** 结构等价 + 校准退化，替代 blanket non-identifiability。 | **必须改：** 不再用未选阈值暗示无法得知对应排序/决策关系。 | **必须改：** 当前 central-result 句的 equality non-identifiability。 | §5.2、§6.1；protocol/analysis 状态仅作过程记录，不作为一般定理。 |
| A3 OCR | C1 保留，明确不识别 harmful false negatives。 | 保留 0/13，但不得暗示已证实有害；可用短句交代 referential-equivalence 替代解释。 | 可以概括 family-specific non-response，不能升级为 harmful blindness。 | §5.1/limitations 中披露具体 13/13 single-judge 证据。 |
| A4 异质 5/8 | 不新增贡献，不改变 C1 的窄结论。 | 无须加入案例 tally。 | 不新增机制定律。 | §5.1 的同质比例与排除噪声措辞必须撤回。 |
| A5 FinQA | C3 改 `undefined`；旧正迁移解释停止承担证据。 | 现有 mismatch 方向保留；“nothing detected downstream”明确是存储结果字段上的判定。 | 如提及此流，仅作 measurement-object boundary。 | §5.6/§6.3、证据 ledger 对 audit PASS 的限定。 |
| A6 long-horizon | thesis 的经验适用域缩到实际 evaluator。 | **改开头研究对象。** | **改结尾外推范围。** | 推荐收窄标题；背景动机可保留。 |
| A7 availability | 不改变科学贡献。 | 无影响。 | 无影响。 | Data Availability 的事实时态与真实可访问状态一致。 |

### 10.3 作者可保留的最强结论

**在这个冻结、受控的 staged document-intelligence evaluator 中，观测是否响应、决策是否触发、变化是否有害不能互相代替。** 单响应叶下的层级分数差距有尺度与阈值解释；多叶满分依赖显式阶段签名，并未显示超出 direct codebook 的性能；FinQA 的可复算 V/D/O 分离来自没有重算检测对象，不能被当成能力迁移。这些具体诊断足以支持一个有边界的 measurement-validity audit，不足以支持通用检测器、层级定位方法或长程 AI 经验定律。

当前稿件若要让作者重新签署，需要先解决 A2 的核心逻辑，并落实 A1/A3/A4/A5/A6 的必要范围修正；不能只在 limitations 追加一句免责声明而让 abstract、contribution 和 conclusion 保留旧推断。**所有数字、正式运行状态与历史审计痕迹可以保留。需要改变的是读者被允许从这些证据推出什么。**

## 11. 证据索引与本轮执行边界

下列行号对应本轮读取版本。N1 的 ablation 是既有 post-hoc 结果；F 类区分代码定义、已有复分析与代数推论；Q4 只认证复算，其旧科学解释不继承为当前 claim。历史决策文档不是高于实现和原始案例的科学证据。

| ID | 关键材料与定位 |
|---|---|
| M | [当前 manuscript](D:/AIRcommend/JinRongAgents/agents_final_tech/paper/saner_rene_manuscript_v1.md:1)：abstract 5；贡献 15；OCR/8 项 119–125；结构 139；ablation 159–163；FinQA 167；综合 193；结论 197；availability 201。 |
| C | [当前 C1–C3 matrix](D:/AIRcommend/JinRongAgents/agents_final_tech/paper/saner_rene_claim_matrix_v1.json:9)：thesis 9；C1 13；C2 24；C3 34。 |
| S | [上一轮战略审查 §4.2](D:/AIRcommend/JinRongAgents/agents_final_tech/docs/research/STRATEGIC_REVIEW_AND_NEXT_PLANS_v1.md:78)：本轮问题范围来源；其 P0/P1 是风险优先级，不直接等于本轮科学裁决等级。 |
| N1 | [non-direct ablation 报告](D:/AIRcommend/JinRongAgents/agents_final_tech/docs/research/stage_e_multileaf_signature_ablation_v1.md:3)：状态 3；分数 7–16；叶响应/MI 20–33；部分区分 38。 |
| N2 | [ablation 原始结果](D:/AIRcommend/JinRongAgents/agents_final_tech/research/stage_e_multileaf_20261010/results/multileaf_signature_ablation.json:252) 与 [冻结多叶 preregistration](D:/AIRcommend/JinRongAgents/agents_final_tech/docs/research/stage_e_multileaf_preregistration_v1.md:112)：平局输出及 tie-as-incorrect 规则。 |
| F1 | [clean-only 复分析代码](D:/AIRcommend/JinRongAgents/agents_final_tech/research/stage_e_method_revision_20261009/stage_e_matched_fpr_reanalysis.py:63)：clean 自相减 63–76；status 84–88；配对阈值/strict predicate 107–125；rank 128–136。 |
| F2 | [D3 原分析](D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_d3_matched_fpr_stage_a.py:508)：单响应叶 508–527；旧 `FPR≤α`、harmful TPR selection 830–853；[加权聚合](D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_t1_eval_baselines.py:119)：固定加权均值与 round 119–136。 |
| F3 | [复分析记录](D:/AIRcommend/JinRongAgents/agents_final_tech/docs/research/stage_e_matched_fpr_reanalysis_v1.md:1) 与 [JSON](D:/AIRcommend/JinRongAgents/agents_final_tech/research/stage_e_method_revision_20261009/matched_fpr_reanalysis.json:1)：2,382 clean support、秩、比例偏差与六点网格。 |
| F4 | [复分析 protocol](D:/AIRcommend/JinRongAgents/agents_final_tech/docs/research/stage_e_matched_fpr_reanalysis_protocol_v1.md:24)：clean-only 下最大 TPR / 最小正阈值的现行规则。 |
| O1 | [Stage B 案例表](D:/AIRcommend/JinRongAgents/agents_final_tech/docs/experiments/2026-09-06_d3_matched_fpr_stage_b.md:122)：七项 judge 对照 122–132；八项异质表及 zero-call 137–151。 |
| O2 | [OCR autopsy 决策记录](D:/AIRcommend/JinRongAgents/agents_final_tech/docs/experiments/2026-09-08_d3_autopsy_decision_record.md:31)：13/13 equivalent、residue、value invariance 与类型级归类；其中旧 5/8 机制总括不被本轮继承。 |
| O3 | [autopsy 原始 recompute](D:/AIRcommend/JinRongAgents/agents_final_tech/logs/graph/eval/d3_autopsy_recompute.json:398)：A12–A14，含 family-design-intent、value invariance、canonical-keyset 12/13。 |
| O4 | [Stage B 原始 JSON](D:/AIRcommend/JinRongAgents/agents_final_tech/logs/graph/eval/d3_matched_fpr_stage_b.json:2493)：`dr4_comparison_8rows` 的 deterministic/zero-call 证据类型。 |
| Q1 | [FinQA paired-artifact 构造](D:/AIRcommend/JinRongAgents/agents_final_tech/research/finqa_v2_20261010/build_finqa_v2_execution_freeze.py:182)：terminal `res` 读取与 op/args/evidence mutation 182–221。 |
| Q2 | [FinQA observation scorer](D:/AIRcommend/JinRongAgents/agents_final_tech/research/finqa_independent_observation_scorer_v2.py:109)：字段差异谓词 109–121；measurement object / 禁止语义正确性 131–132。 |
| Q3 | [FinQA formal runner](D:/AIRcommend/JinRongAgents/agents_final_tech/research/finqa_v2_20261010/run_finqa_v2_formal_experiment.py:540)：V/D/O 的实际定义 540–545。 |
| Q4 | [旧 FinQA recompute audit](D:/AIRcommend/JinRongAgents/agents_final_tech/docs/experiments/2026-10-10_loop_c_finqa_v2_formal_v3_recompute_audit.md:93)：PASS 93；旧正迁移解释 97/101，本轮不继承。 |
| Q5 | [accepted FinQA mismatch autopsy](D:/AIRcommend/JinRongAgents/agents_final_tech/docs/research/finqa_v2_measurement_object_mismatch_autopsy_v1.md:8)：对象错配解释与 allowed/forbidden claims。 |
| H | [closeout / handoff](D:/AIRcommend/JinRongAgents/agents_final_tech/PROJECT_CLOSEOUT_AND_HANDOFF_v1.md:59)：发布计划未执行 59；匿名 URL 待建立 65；编译完成与实际提供的区别。 |

本轮只做选择性阅读、定义核对、代数审查与文档记录，没有调用模型/评审服务，没有新数据采样、统计重跑、校准实验或代码改动。本文的修订原则尚未应用到稿件、claim matrix、冻结协议或历史 audit。
