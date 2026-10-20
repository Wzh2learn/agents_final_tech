# 独立战略审查与下一阶段研究计划 v1

> 状态：`STRATEGIC_REVIEW / RECOMMENDATION_ONLY` | 日期：2026-10-12（Asia/Shanghai）
> 审查基线：LOCAL `bb9392518791f0c9fcced3eb81002814e1d1941f`；GB10 本轮未访问。
> 范围：研究问题、现稿论证、既有实验资产、科研 harness、资源配置。不是实验结果，不替代冻结 claim matrix、既有授权或历史预注册。
> 本轮：选择性阅读、三路 fresh-context 文本审查、少量公开一手文献查证；未运行实验、训练、judge、服务探针或数据库操作，未修改实现、稿件、冻结数据，未提交或发布。

## 1. 如果今天第一次接手，我会研究什么

**我会研究：一个分阶段 AI 系统的有限观测，什么时候足以区分真正有害的失败、合理的不变性，以及评估链自身没有测到目标的情况？**

这是现有结果共同指向的问题。它属于测试 oracle、测量有效性和故障可诊断性研究，已有成熟概念基础；无需再发明一个框架名称。成本约束是第二层问题：在目标可被独立判断后，哪些观测值得保留，哪些只是重复证据？

当前最有价值的资产不是十二个叶子、四层 Loop、某种优化器或学生模型，而是几组可追溯的反例：评分不同却排序相同；准确率低却仍有可区分信息；看不见变化却可能保持正确；注入发生了却没有进入检测对象；检查全绿却没走真实执行入口。

我的资源配置建议是：**保住并纠偏现有小论文；只开一条新的主研究线——独立目标下的 oracle 有效性。观测压缩和选择性决策先做小型资格审查，通过后最多升一条为第二主线。完整 Evaluate–Distill–Evolve 不再是必须完成的架构。**

### 1.1 证据等级

全文采用三类标记，不能相互晋级：

- **[E] 现有证据支持**：本轮读到的代码、工件或审计记录支持该窄结论。既有运行数字是引用，未在本轮复算；历史记录不能代表当前运行态。
- **[H] 合理但未验证**：有机制依据或可检验预测，仍缺独立标签、非退化对照、外部数据或有效实验。
- **[X] 探索性想法**：值得限定预算筛选，但尚不具备方法或论文资格。

数学推导另标 **[D] 条件性演绎**：结论由明确假设推出，不冒充新增经验结果。所有路线、预算和工作包均为建议；本轮不派发 GB10 执行。

## 2. 真正推荐的 TOP 3

### TOP 3 CONTINUE

| 顺位 | 继续什么 | 原因与下一步 |
|---|---|---|
| 1 | **现有 measurement-validity 小论文，但先修科学论证** | [E] 有可复查的边界案例；§4列出新的实质问题。先纠偏 C2、非直接叶信息和 harmfulness 证据，再谈投稿就绪；不为稿件补一个强行正结果。 |
| 2 | **挖现有数据里的观测碰撞、oracle 分歧和强基线残差** | [E] 比继续扩数据量或优化树权重更有信息；先回答哪些目标根本不可由当前观测区分，以及哪些错误值得新增检查。 |
| 3 | **最小复现与独立复算能力** | [E] 真实入口、明确归因和独立复算能直接减少无效实验。只补影响现稿可信度或下一实验可执行性的缺口，不扩大治理平台。 |

### TOP 3 STOP

| 顺位 | 停止什么 | 停止边界 |
|---|---|---|
| 1 | **在现有退化面上继续证明 hierarchy 优越、搜索权重或分析完美 codebook** | 固定加权平均可展开；满分已被直接叶 codebook解释。继续 PSO/随机搜索/换阈值几乎不能回答新增科学问题。保留历史，不重跑救结论。 |
| 2 | **以凑够 positive repair 为目标的恢复竞赛** | PR-03 不做第四轮；旧 Route B MVP、FinQA binding 收口不重开。修复软件错误不能自动产生修复方法；“几个 positive 才能综合”是管理规则，不是方法成立条件。 |
| 3 | **没有独立目标和稳定残差时的蒸馏、bandit、规则自增长** | 不因权重已下载或软件合同已实现而训练。当前数据路径不识别训练收益，奖励退化也不识别自适应收益。对原冻结来源/任务路线停止追加搜索和准备；全新来源与任务只能按新问题重新立项。 |

治理层另行停止：无明确失效案例就新增 skill/hook/receipt/registry；没有代码或运行变化就重复全量验收；把备份、导出包和镜像当成独立证据。这些不是第四条研究主线。

### TOP 3 NEW BETS

| 顺位 | 新赌注 | 当前等级 | 我的投入建议 |
|---|---|---|---|
| 1 | **独立 oracle 下区分有害变化与合理不变性，并检查共同失效** | [H] | 唯一优先主线。先用少量边界案例验证目标和标签是否可建立，不先训练模型。 |
| 2 | **从观测碰撞出发，寻找最少且足够的检查证据** | [H]；算法创新仍[X] | 先做解析/小规模穷举与强基线。只有出现非平凡碰撞、代价差异和可迁移增量，才开发方法。与已关闭的 causal checkpoint-selection MVP 无关，不复活旧分支。 |
| 3 | **检查点是否真的改善 map / defer / review 的决策价值** | [H] | 先挑战 B4：新增观测能否在同一批独立目标上降低风险或减少人工成本？它是蒸馏前的必要性探针，候补而非并行大项目。 |

## 3. 现有证据究竟支持什么

| 资产 | [E] 可以保留的结论 | 不能据此推出的结论 |
|---|---|---|
| 95 tables / 118 injections，96 visible；OCR-like 0/13、11 clusters | 指定冻结面和可见性定义下，有稳定的族级观测差异。[S2][S3] | 这些不可见项必然有害；真实 OCR 错误普遍不可见；系统能力差。 |
| 单响应叶、斜率约0.375、Spearman 1.0 | 当前分数结构给出相同排序和对应 ROC；原始同数值阈值的差距不代表信息优势。[S4] | 所有多叶协议都等价；clean-only 数据能唯一选择部署阈值。 |
| 2,382 clean contrastive rows 全为0 | 当前 clean score 构造不能唯一选正阈值；再加同样 clean rows 不解决问题。[S4] | 所有 matched-FPR 结构关系都不可推断；增加样本数即可解除阻塞。 |
| 72 clusters / 216 multi-leaf injections，full/direct均1.0 | 显式、契约导出的阶段签名可被解码；三次重复不是三个独立 cluster。[S5] | hierarchy 提供了增量信息；自然轨迹可定位；非直接叶完全没有阶段信息。 |
| FinQA V=89/89、D=0/89、O=0/89 | 工件复算与测量对象错配的 autopsy；变动的源字段没有因果重算进入检测所用 result 字段。[S6] | 协议 detection 能力为0；跨流证实 blindness；已验证 causal selection 方法。 |
| PR-03 v3 | 冻结复合规则的点估计判定为 NEGATIVE；不能支持 genuine repair。[S7] | 一个完备、独立审计且有诊断 CI 的零效应实验；0.8116 coverage 是可靠 repair 增益。 |
| Valentine / Phase 1a 路线 | 现批准来源不能满足原任务所需的独立单位和同样本标签桥；RQ2 NOT_IDENTIFIED。[S1] | 学生无用；不存在任何可用数据；蒸馏被证伪。 |

**结果状态必须按问题解释。** 有效实验的 NEGATIVE/NULL、执行无效的 INVALID、构造不可评的 NOT_EVALUABLE，以及目标不可识别的 NOT_IDENTIFIED 不能揉成“我们做了很多负结果”。PR-03 的历史判定保留，但其退化基线、不可达 POSITIVE 条款、未产出诊断 CI 和 self-audit 边界，使它不能承担一般修复效果的科学论证。[S7]

## 4. 现稿最强贡献与最危险的拒稿点

### 4.1 最强贡献

**[E] 最强的是一份有具体反例和可追溯工件的评估有效性审查：它说明为何某些看起来可比较的评分、阶段定位和跨流结果，实际上没有识别所声称的能力。**

这一贡献适合有边界的经验/负结果论文。它不是新的通用检测器，也不是对 long-horizon agent 的系统性实证。三构念的区分本身不足以成为主要新颖性；经典 RIPR/oracle 理论早已区分故障触发、传播和揭示，现有新文献也直接审查 perturbation audit 自身的失效。[W1][W2] 新颖性应落在具体 evaluator 的结构诊断、反例及它们改变了什么原本会被相信的结论。

### 4.2 最可能被一票否决的理由

**最强拒稿论点是：关键发现可能由注入器、标签和评分规则共同写入，而没有独立证明它们对应“本来应该发现的失败”；同时稿件对自己已有的观测信息作出了过强否定。**

对当前窄范围 RENE 稿，最直接、可证的攻击是下列 P0-1。它不是润色问题。文档里的 `SUBMISSION_DRAFT_COMPLETE` 可以表示包已编译，不能覆盖本轮新发现的论证风险。建议在正式外发前单独审定；本轮未改稿或更改冻结 claim authority。

| 优先级 | 新发现及依据 | 应如何处理 |
|---|---|---|
| **P0-1** | 稿件§6.3、193行说非直接叶“no stage information”。但 ablation 的 `parse.table.regression` 在 M 为72、R/N为0，MI=0.9183 bits；报告也明确它能识别M、R/N碰撞。0.3333准确率含0.6667 tie，不能等于信息为0。[S5] | 撤回零信息措辞。区分部分可区分性、全三类可诊断性、tie处理及hierarchy的增量；不改历史分数来救结果。 |
| **P0-2** | C2、scope lock和结论把 clean-only matched-FPR equality统称不可识别，但稿件139行和复分析已确认正仿射排序/ROC等价。[S4] | 分开四件事：数值阈值不唯一；仅由FPR约束不唯一决定TPR；仿射耦合下检测集合相同；无hierarchy优越证据。不要用一个NOT_IDENTIFIABLE覆盖它们。 |
| **P1-1** | 历史autopsy31–33行：13个OCR-like都被该judge判equivalent；D1有害归属依赖类型白名单，部分DR4失败来自lexicon residue，13/13数值不变。[S8] | 主文应清楚呈现“成功吸收无害变化”这个有证据的替代解释。judge不是独立金标准，不能反向宣判13项全部无害；但泛泛写equivalence caveat不够。 |
| **P1-2** | §5.1把“8 paired / 5 disagree”全读为canonical-vs-reader标准分歧；八项比较中未调用judge的 `Revenues→sales` 是deterministic visibility与oracle equivalence比较。[S8] | 重建异质对照的类型账，不把V/H差异当两个harm标准分歧。保留原表，不继续用5/8承担单一机制论证。 |
| **P1-3** | claim C3写detection predicate“undefined by construction”，而scorer是明确的res/answer差异布尔谓词。错在扰动未进入它的检测对象，能力估计不成立。旧FinQA recompute audit的transfer解释又与accepted autopsy相冲突。[S6] | 改建议措辞为“well-defined predicate on causally unmodified result fields”。保留复算PASS，标记旧解释已被autopsy取代，不能让算数PASS认证transfer。 |
| **P1-4** | 证据是一条文档数据流、合成签名和一次失败迁移；标题/开头使用long-horizon AI，容易让读者预期跨horizon或真实agent轨迹实验。[S2] | 长程系统仅作动机，经验结论落在staged document evaluator；若保留标题，在摘要开头和RQ直接限定对象。 |
| **P1-5** | Data Availability使用“are released”，closeout仍有匿名artifact URL待办。[S1][S2] | 外发前核对实际可访问、可重建范围与发布时态。内部草稿的未来发布承诺不能当已发布事实。 |

以上问题均可先用既有证据、解析推导和小范围文本建议处理，不需要重跑模型。是否重开科学冻结应由owner/作者审定；不要让旧冻结阻止发现问题，也不要静默修改历史结果。

### 4.3 统计与设计边界

- [E] OCR的0/13与0/11是不同estimand；既有说明已正确区分参考二项区间和退化bootstrap。保留这个纪律，不能把[0,0]视为人口确定性。[S3]
- [E] multi-leaf的三次重复共用阶段签名；更多重复不增加机制支持。permutation显著不解决构造写入标签的问题。[S5]
- [E] clean分数因`h_repeat=h`而为0；这是测量设计问题，不是power不足。[S4]
- **[待核]** 吸收口径`visible_frozen=96/118`与γ=0.2时阈值口径`85/118`不可混用；三seed pooled CI是否正确保留跨seed table依赖，需先核现存UID。现有runner在pooling时丢弃UID是风险线索，尚不能据此宣布CI错误；WP-02限额核对，不重采样。[S13]
- [H] 在harm标签部分依赖同一检测/等价路径时，`P(miss|harmful)`会带循环性。下一研究需要独立目标，而不是更窄CI。[S3][S8]
- [H] 数据量目标应由具体效应、风险上界、独立origin与精度需求推导。原路线的40 clusters门槛应在原路线继续保留，但不能机械变成所有新问题的自然常数。

## 5. 三个最大的 missed opportunities

### 5.1 已经发现 oracle 共同失效的风险线索，却主要把它放进 limitations

[E] shared-header overlays下，oracle ceiling的两个报告比例是20/21与40/67，分母不同，不能算成同群体退化效果；Hungarian没有改变决定。再加上harm标签与检测路径的依赖，提示问题可能在目标/表示，而不在分配求解器。[S2][S8]

**[H] 更值得研究的是：多个“不同”检测器是否共享同一normalizer、词表、gold构造或缺失策略，从而同时看不见同一类目标差异？** 四种edit-distance matcher的一致不是四个独立语义oracle。若能建立脱离这些表示的任务级目标，现有边界案例就能成为高价值挑战集；否则只能报告构造差异。

### 5.2 已经有强廉价基线，却先准备学生与完整闭环

[E] B4 residual memo记录146行、51个gold map、38个正确map、13个residual、9个harmful map；最大pair占6/13 residual，salted风险上界0.125未过原门。它是探索性证据，不是可外推效果。[S9]

**[H] 下一个问题应先是：观测能否改善这13个残差上的选择性决策，并避免破坏已有正确动作？** 比起“8B能否学会”，先测“是否存在稳定、分散、可泛化且无法由廉价规则解释的增量”更能决定是否值得训练。当前数量和cluster结构不足以直接确认该增量。

### 5.3 已经有观测碰撞，却把注意力放在完美定位

[E] 非直接叶能区分M但混淆R/N；full与direct codebook同为满分。这里真正有信息的是哪些状态共享同一观测、哪些叶重复，而不是再画一个1.0柱状图。[S5]

**[H] 从碰撞出发可以研究：何时必须拒绝定位？增添哪种独立观测才能拆开与决策有关的碰撞？删除哪个叶并不损失必要证据？** 这同时给研究设计和harness瘦身提供依据。单纯对构造codebook做feature selection不足以成为新方法。

## 6. 一个足够强、又不过度包装的统一抽象

令真实执行状态为`x`，当前观测为`R(x)`，检测规则为`D(R)`，目标后果为`Y(x)`。`Y`必须来自独立任务目标及已声明的等价标准，不能由`D`反推。FinQA提醒我们还须先检查：扰动是否沿实际执行路径改变了`R`或`Y`的输入对象。

### 6.1 [D] 相同观测的区分上限

如果`R(x)=R(x')`，任何只读取`R`的确定性定位器/聚合器都不能区分二者；随机规则也不能从相同观测中得到个体区分信息。是否需要区分，取决于任务目标：若`Y(x)=Y(x')`，保持不变可能正确；若目标不同，则需要新增观测或诚实拒绝判断。

这是已知的观测等价/可诊断性思想，不宣称新理论。[W1] 当前项目的机会在于把它用到独立目标、真实执行对象和成本约束上，并以数据检验其实际作用。

### 6.2 [D] 层级平均的减法

固定局部权重的递归平均可展开为

```text
root_score = Σ_leaf effective_weight(leaf) × leaf_score
effective_weight(leaf) = Π_path [child_weight / sibling_weight_sum]
```

[E] 代码`eval_checkpoint_aggregate.py:217–233`就是该结构；missing evidence先固定填值，不因缺失剔叶重归一。逐层round到4位会带来数值差异，不能据此宣称严格bitwise等价。hinge、leaf pass-rate、root threshold和stable是不同的非线性判定，不属于该分数恒等式。[S10]

更重要的是，正式multi-leaf runner已经实现`effective_leaf_weights()`；其secondary对照实际是等权flat与effective-weight flat，而不是对信息内容相同的“有树/无树”做独立干预。[S10]

**因此，今后所谓hierarchy增益必须拆成：观测增量、有效权重、非线性决策/缺失策略或执行策略的作用。固定权重树形组织本身没有创造观测信息。** 它仍可有可读性、责任分工和调试价值；那些是可用性问题，需要另一种证据。

### 6.3 这个抽象如何解释现有结果

| 已有现象 | 统一问题中的位置 |
|---|---|
| 单响应叶仿射变换 | 同一观测被不同尺度编码；没有新的区分能力。 |
| multi-leaf direct满分、非直接部分碰撞 | 增添了阶段对齐观测；信息来自观测设计，不来自树形外观。 |
| OCR-like不响应 | 先问目标是否相同；相同可能是鲁棒，不同才是目标相关盲区。 |
| FinQA源字段变、result不变 | 操作对象与检测对象之间的执行桥未成立；不能估计能力。 |
| B4残差集中 | 即使有可学习信号，也可能只识别origin特征；需要独立单位与真实决策价值。 |
| preflight全绿、正式入口失败 | 被观察的检查路径与被认证的真实路径不同。 |

## 7. 过去哪些决策我同意、推翻、重新打开

以下是独立建议，不自动更改既有decision ledger。

| 裁定 | 决策 | 理由 |
|---|---|---|
| **同意并坚持** | 冻结旧数据/协议；不回改分母和标签；承认DATA_NO_GO；PR-03不第四轮；Route B旧MVP关闭；FinQA binding不再恢复 | [E] 保住可追溯性，防止用新口径救旧结果。 |
| **同意但收窄** | GB10作为正式执行权威 | 环境纪律合理；但“只有GB10能证明科学正确”不成立。未来应允许独立离线复算成为补充证据，不能让硬件单点成为oracle。 |
| **推翻作为默认战略** | 完整Evaluate–Distill–Evolve是论文/大论文必须完成的链 | [E] 后两段证据未闭合；三段统一不产生同样本标签，也不证明训练必要。论文应按已识别问题组织。 |
| **推翻作为科学门** | 满足一定数量positive repair才值得形成方法 | 方法需要共同机制、算法定义、非平凡基线和泛化证据；几个positive既不必要也不充分。管理gate可留历史，但不指导寻找结果。 |
| **推翻** | 固定树的复杂性/多叶数/测试数/审计轮数代表研究增量 | [E] 有效权重展开、codebook与空集PASS已给反例。 |
| **重新打开科学解释** | C2阈值不可识别范围；非直接叶“零信息”；OCR-like有害性；5/8比较；FinQA旧audit解释 | §4有精确证据。重开解释，不重开旧实验，也不直接宣布新结论已通过。 |
| **条件重开** | 低成本选择性动作、观测删减 | 先独立目标、强基线、origin-disjoint与可识别性；不接续旧Route B实现。 |

治理上我还会推翻一个习惯：每次失败就增加一层通用规则。针对已发生风险的真实入口测试应保留；不断扩充抽象检查器却不让它经过失败对照，ROI低。

## 8. 小实验与 repair 能否自然上升为方法

**当前不能。** [E] 现有repair混合了实现补救、表示检查、阶段签名、对象错配与不同终点；没有一个已证明可以跨这些对象复用的输入—决策—目标机制。PR-03覆盖率相对常量baseline，且复合判定否定repair，不能成为方法核心。[S7]

一个值得claim的方法至少缺六块结构：

1. **独立目标**：要发现的harm或要改善的决策能独立于候选检测器定义；unresolved可以保留。
2. **可执行干预**：变更进入真实消费者和任务后果；不能只是JSON某字段变了。
3. **共同机制**：算法根据可观察输入作出什么选择，为什么；不能把几个case-specific predicate拼成框架。
4. **非平凡必要性**：等有效权重flat、直接叶规则、廉价启发式、随机/greedy和合理oracle上限不能已解释全部效果。
5. **泛化单位**：未见origin/机制/实现，而不只是新seed或同一template更多实例。
6. **有用输出**：能正确拒绝不确定定位，或在同风险下减少检查/人工成本；不只提升一个构造标签F1。

[H] 若路线N1建立独立目标、N2发现真实碰撞且简单方法存在稳定不足，才有开发新算法的理由。若一个直接规则已经足够，应发表清楚的经验/理论边界或保留为工程工具，不强造方法。

## 9. 候选路线的价值、风险、成本与前置条件

成本为规划估计的人日，不是已测GB10耗时；先做资格包，不能把整条路线一次性授权。

| 路线 | 可回答的问题与价值 | 风险 | 初始成本 | 前置条件 / 停止条件 |
|---|---|---|---|---|
| **R0 现稿纠偏** | 减少现有科学资产被错误解释；最高即时ROI | 冻结件联动、引用旧解释 | 1–3人日，0项目模型调用 | 按§4形成patch proposal；独立确认推导后再由作者决定改稿。不新增能力claim。 |
| **N1 独立harm / invariance oracle** | [H] 区分合理鲁棒与漏检；检验shared-normalization共同失效 | 人也可能无法一致判目标；judge与业务等价不同 | 3–5人日资格审查；可行后2–4周小研究 | 独立任务答案/可执行规则/盲审裁决至少有可核对的目标；预先定分歧/UNKNOWN政策，不按一致性筛案例。若目标循环定义，或主estimand在预设政策下不可估计，停止。 |
| **N2 观测碰撞与最小证据** | [H] 同目标风险下减少检查，明确不能定位的边界 | 退化成已知set-cover/feature selection或新codebook | 2–3人日离线审查；方法阶段另估 | 有非直接、重叠、噪声或部分缺失签名；有可区分目标及实测检查成本。若direct规则或穷举已解决且无迁移增量，不开发方法。 |
| **N3 B4选择性决策** | [H] 证明额外观测/学生是否有必要；风险—成本/coverage tradeoff | origin集中、标签桥缺失、把拒绝作弊当改进 | 1–2人日审查；正式pilot另批 | 同样本独立action target/outcome；与B4+简单defer公平比较。没有独立残差或收益只来自单origin，停止。 |
| **R4 harness失效案例研究** | [X] 揭示“检查绿但科学无效”的机制与成本 | 与Auditing the Audit等工作重叠；单团队self-audit偏差 | 最多1人日证据筛选，不立新平台 | 需外部独立案例或能改变他人结论的复现；只有内部事故分类则保留工程复盘，不开论文主线。[W2] |
| **R5 蒸馏/自学习** | [H] 有稳定难点后可能降低执行成本 | 数据/标签/功效不识别，训练遮蔽测量问题 | 当前不投入训练 | N3证明必要性、风险可控、独立origin充足后，以新合同再立项。下载完成不算科学准入。 |

N1是主线；N2/N3先各做小资格审查，最多择一升级。R4不分配长期预算，R5不排默认开始日期。

### 9.1 下一篇更强论文的证据门槛

**经验型论文**至少需要：独立定义的目标；对合理不变与有害改变同时有对照；真实consumer级干预；足以排除构造答案的未见origin/机制测试；配对cluster统计与正确分母；独立复算；无效批次和unknown标签完整披露。

**方法型论文**还需全部满足：

- 冻结可复用算法，而不是case-specific补丁；测试标签不得用于事后制定或调整观测选择、阈值、停止规则或fallback；预注册终止与报告规则可按约定应用。
- 在明确同成本/同风险口径下，超过最强简单baseline；预先定义实际有意义的最小效应或非劣界，按独立单位与所需精度做功效/可行性判断。
- 测试至少一个未参与设计的实现/数据流，并持出一个机制或origin层级；若只在原95表变换上有效，claim限于该构造，不能升通用方法。
- 拆开观测、聚合、目标oracle、校准与执行策略的消融；存在shared-normalizer时，必须测试一个不共享该路径的oracle。
- 报告拒绝判断、误警、漏检、harm risk、成本和collateral；单个macro-F1不能替代它们。adaptive方法须有与目标一致的有效反馈，以及可识别的策略对照或反事实估计设计；未执行的结果字段不能充当反事实。[S12]
- 证明软件结果可归因于冻结入口；由不导入核心被审算法的实现复算关键数值。

如果满足这些门槛的成本高于项目资源，应主动选择一篇更窄但有效的经验论文，而不是下调门槛换一个方法名。两条数据流本身也不保证上述条件。

## 10. Repo / harness：该减什么，保留什么

### 10.1 最小科研内核

建议保留的复现依赖只有四类：**不可变输入与谱系；实际执行/评分入口；带command/revision/hash的输出；claim到这些工件的映射。** 评审可从只读工件重建核心数字；生产FastAPI、M1/M2服务、Graph Loop调度和所有skill安装不应成为确定性结果复算的默认依赖。

这是一份依赖切面建议，不要求立即拆仓、搬历史文件或建立新的平台。先在现有位置写最短复算入口，证明哪些依赖可省，再决定是否抽取。

| 对象 | 建议 | 依据与迁移风险 |
|---|---|---|
| 业务系统与Graph Loop | 保留边界，科研offline replay不得默认启动服务 | [E] CORE已区分研发Loop与业务图；B默认可触发真实canary/API/PG，不是零调用验证。[S1][S10] |
| 固定树评分与多种搜索runner | 保留冻结实现供复现；新比较先使用effective weights和同一叶输入 | [E] 一般树平均已展开；减少无信息的搜索。不静默重写历史分数。 |
| `formal_experiment_preflight`与Track P execution preflight | 停止平行扩张；未来统一最小真实入口fixture、必需清单和归因接口 | [E] 保留的PR-03 v3历史preflight快照有硬写PASS、helper级metric路径和不完整readset；v2规范已要求真实入口E2E与归因，不能据此断言新实现仍有同样缺陷。[S7][S11] |
| source/runtime hash、raw/git blob、跨主机EOL规则 | 合并“同一语义”的命名与调用；明确不同identity type，禁止自动混用 | [E] FinQA与Track P发生过字段/字节身份混用。科学冻结件仍用原identity；未来统一必须版本化。[S1][S6][S11] |
| claim verifier、paper validator、submission audit | 先标清各自证明范围，重复身份检查才考虑共用 | [E] claim verifier不证明正文数字、实际执行和完整性；代码在清单为空或可选prereg缺失时可能仍PASS，这是保证范围缺口。本轮未发现现有冻结包实际缺件或清单为空。需closed expected inventory，不能称万能验证器。[S11] |
| STATE / THREADS / INDEX / research README / closeout / side handoff | status、open items、导航、执行合同分工；其余只引用，不再复制完整状态 | [E] research README仍将teacher-review与09-22计划称当前authority，而10-12 closeout已指SANER canonical；应先修入口冲突。[S1] |
| 同任务的带/不带日期目录、副本、export packs、test tree | 暂停新增可编辑副本；未来按hash+引用清单判同源/分歧，再只读归档 | 路径相似不证明重复可删；父目录可能有唯一证据。保留历史，不做本轮迁移。 |
| skill catalog、hook、通用治理文档 | 本研究只加载必要少数；新增必须绑定已发生且仍未被覆盖的失效 | skill数量与科学可信度无正比关系。已有历史保留，不另造skill注册系统。 |

**不应合并的重复**：独立数值复算、独立语义oracle与故障正负控。它们的价值恰在实现/目标路径不同；共享IO/CLI可以，不能把独立复算改成调用同一个核心函数，再称独立证据。

### 10.2 三个最优先的工程减法

1. **裁掉平行authority和状态复制。** 用现有INDEX指向一个实际稿件、一个claim authority、一个当前执行合同。修过期入口，而不是再加一个总管文档。
2. **裁掉没有新增观测信息的评分/搜索分支。** 保留复现，停止扩功能；按观测、权重、非线性规则分别归因。
3. **裁掉把文件身份/报告检查当成执行认证的宣称。** 身份检查仍有必要；另用真实入口toy E2E、closed inventory和独立关键输出复算弥补其保证范围，而非增加更多“已检查”字段。

### 10.3 治理工作的ROI判据

继续治理只因它能减少错误claim、提高新实验可执行性，或显著降低独立复算成本。以“文档数下降”“测试数增长”“audit PASS数”“所有主机都同步”为主要成绩，均不构成科学价值。

建议每次新实验前只回答五问：目标独立吗；干预到真实消费者吗；强简单基线有headroom吗；独立单位/统计可行吗；冻结入口能生成可归因结果吗。沿用已有contract承载，先不再新增一份通用checklist。失败时用toy/negative control证明对应修复有效，不能只加一个flag。

## 11. 删除历史路径依赖后的 counterfactual 计划

不使用Stage/Track/Loop等名称，我会这样从零设计：

1. **选一个有可执行目标的分阶段任务。** 先用公开表格中的具体数值问答或可核对输出；不要从“我们已经有十二个指标”出发，也不预设要训练。
2. **先冻结何为正确、何为等价。** 同时准备应保持答案的变化、应改变答案/触发错误的变化和无法裁决的情况；目标判定独立于待评估normalizer与mapper。
3. **沿实际数据流做成对干预。** 记录源状态、真实consumer输入、输出及必要证据；区别未触发、被正确吸收、传播后被发现、传播后漏检。未执行的result不能当反事实。
4. **只保留最少三个起点。** 终点检查、最强廉价局部规则、候选观测向量；比较相同目标和同一批独立origin。不先上树搜索、bandit或学生。
5. **先画观测碰撞与harm/invariance混淆表。** 若目标不同而观测相同，测试新增独立观测；若观测相同且目标相同，就奖励合理不变性而非强迫响应。
6. **验证一个最小干预是否有决策价值。** 超过直接规则且在未见origin成立，才研究成本受限检查选择；规则足够好就停止开发方法。
7. **最后才决定论文类型。** 有可靠反例写经验/负结果；有可复用选择机制与泛化写方法；有独立稳定残差和明确成本需求，才讨论学习模型。

如果只有一个研究生和一台GB10，我会采用这条路径。生产系统提供真实问题和可选验证场景，但不绑架科学任务；大论文围绕“测量目标—观测充分性—决策效用”逐步累积已成立的章节，不预先承诺三段学习系统。

## 12. GB10 Loop A 的独立 work packages（本轮全部不执行）

所有包默认：隔离工作目录，冻结资产只读，不接生产/数据库，不装依赖、不启动服务、不下载新数据。预算是未来建议上限；触发需要的新数据、人工标注、项目模型/judge或正式实验另立合同。不得把本报告当执行授权。人日含审查估计，CPU上限为toy/离线工作初始预算，超限停止估算而非自动加码。六包是独立选择，不是必须全部通过的串行流程；只有被选中的研究需要对应执行资格。

### WP-01：现稿科学论证纠偏提案

- **Owner / 输入**：Loop A；canonical manuscript、claim matrix、scope lock、[S4]–[S8]。只读原件。
- **输出**：一个独立patch proposal和逐句claim/evidence表，覆盖§4全部问题；每项写原句、建议句、依据、哪些数字/图不改变。包含Data Availability实际状态核对，不发布。
- **成功**：区分阈值/ROC、部分信息/tie、V/H与harm/harm、defined predicate/invalid能力估计；独立审查者能用所列工件复核；不增加新结果。
- **停止**：需要选新阈值、改harm标签或重跑来支撑原句。保留问题并交owner，不自动修冻结稿。
- **预算 / 依赖**：1–2人日，项目模型/judge/服务调用0，离线CPU≤10分钟；无上游依赖。作者审定后再单独合入稿件。

### WP-02：观测等价、层级展开与tie解释

- **Owner / 输入**：Loop A；aggregation代码、effective weights、既有multi-leaf响应和ablation。与WP-01分文件独立。
- **输出**：一份解析说明与小型离线复算表：有效权重、舍入例外、重复/常量叶、观测等价类、R/N碰撞、冻结tie计分说明；附visibility两定义对照和三seed独立单位审查。后两项新增读取≤6个明确命名文件，不重跑injector/matcher、不生成seed、不追加bootstrap；缺UID台账则记“依赖未核实”。新增诊断列单独命名为post-hoc，不能覆盖正式结果。
- **成功**：在相同叶输入下解释树与flat weighted关系；用现有响应证明“部分信息”而非零信息；同类目标中列出哪些必须/不必区分。不把rank或MI当作泛化证据。
- **停止**：需新模型观测或结果驱动调阈值；只形成缺口清单。若全部是已知直接codebook，不再展开feature-selection实验。
- **预算 / 依赖**：1–2人日，项目调用0，CPU≤10分钟；现有结果只读。支持WP-01及N2资格判定。

### WP-03：独立harm与合理不变性的可行性卡

- **Owner / 输入**：Loop A；OCR/alias/shared-header边界案例、原始公开任务目标、既有judge与DR4证据；先审最多24例的谱系/目标可用性。既有边界例的选择明确为post-hoc资格审查；新pilot的样本规则须在新oracle裁决前冻结，不声称已知案例是盲选确认性样本。
- **输出**：任务目标与oracle依赖图、每例是否有独立目标及unknown原因、盲审/可执行oracle方案、paired invariant/harmful control设计。只能记录既有标签，不能伪装新增裁决。
- **成功**：有不复用待测mapper/normalizer的目标桥；至少可设计合理不变与有害变化两个对照；冻结独立性/标注可见性、分歧/UNKNOWN处理，不筛除难以一致裁决的案例。正式预算必须列人数、判断次数、裁决工时与样本/cluster需求。
- **停止**：目标只能来自family白名单或同一个检测器；授权来源不含必要ground truth。输出`ORACLE_NOT_IDENTIFIED`，不把更多judge投票当替代。
- **预算 / 依赖**：2–3人日，新增judge/模型调用0，CPU≤10分钟；与WP-01/02可并行。待批标注pilot的初始规划上限为2人×24例×2种契约=96次判断、第三人裁决≤4小时；若预设UNKNOWN政策下主estimand不可估计则NO_GO，保留全体案例。该标注预算本轮不执行，也不能代替正式power设计。

### WP-04：最小观测研究的资格审查

- **Owner / 输入**：Loop A；WP-02碰撞表、WP-03独立目标资格；只读已有或明确标为toy的新构造。
- **输出**：一页`GO/NO_GO`与预注册草案：待区分的目标对、候选观测、成本定义、direct/effective-flat/random/greedy/小规模穷举基线、origin/mechanism holdout和拒绝定位政策。toy结果只能证明软件/机制，不算外部效度。
- **成功**：提出一个direct codebook或简单greedy未定义性解决的非平凡问题；能解释新增方法为什么必要，并有未来实测成本与独立测试来源。
- **停止**：仍是互斥stage flags、完美codebook或无成本差异；仅给最小工程实现建议，不立方法论文。
- **预算 / 依赖**：1–2人日，项目调用0，toy CPU≤15分钟；依赖WP-02/03。不是旧Route B恢复包。

### WP-05：B4选择性决策与训练必要性审查

- **Owner / 输入**：Loop A；[S9]的raw rows/labels/splits、B0–B4冻结规则。复用WP-03的独立性审查方法，但必须另行证明schema-action同样本action/target/outcome桥；OCR oracle资格不能转移过来。
- **输出**：residual的origin集中度、错误类别、独立action target/outcome可用性；B4+简单defer/review与额外检查的公平比较设计；明确quality/risk/coverage/人工成本分母。不运行学生、A2或Phase2。
- **成功**：存在可独立评估且不由单origin支配的增量任务，并能制定不读取test outcome的defer规则和实际效应门。
- **停止**：标签桥缺失、独立cluster不足，或只是用hold/skip刷低harm而coverage崩溃；保留`NECESSITY_NOT_ESTABLISHED`。不得用探索性13残差自动推导power充分。
- **预算 / 依赖**：1–2人日，项目调用0，CPU≤15分钟；依赖独立目标资格，N3先于任何训练准入。

### WP-06：选中实验的最小复现与执行资格

- **Owner / 输入**：Loop A；现有INDEX/authority与两个preflight、claim verifier；阶段B仅使用一个未来已批准实验的真实entrypoint和非held-out toy。
- **阶段A输出**：最多一页保留/合并/冻结清单和必要authority导航patch proposal；最短离线复算命令。明确拟减少哪条活跃实现/状态复制，标明两个可共享IO/identity边界及一个不能合并的独立复算边界。只提案，不搬仓、不迁移旧资产。
- **阶段B输出**：选中研究后，在既有入口做toy E2E和可归因receipt；missing-required、错误字段、空inventory、运行失败/不可归因负控；预估最重统计路径复杂度。不是追溯修复PR-03 receipt。
- **成功**：读者能找到canonical稿件/claim/执行合同；阶段B真实入口在故意破坏时确实失败，output绑定command/revision/input/output；独立复算不import该runner核心逻辑，不新增平行通用checker。
- **停止**：创建新总registry/调度平台、批量改历史hash、未选定合法实验、读到held-out结果、需生产连接或toy耗时外推超预算。不给科学结论。
- **预算 / 依赖**：阶段A≤1人日、静态CPU≤10分钟，可独立做；阶段B≤2人日、CPU≤30分钟，只在路线和新执行授权确定后做；项目调用均0。未来代码试点最多4文件/250行，超范围先缩小提案，不扩大框架。

### 12.1 立项裁决，不另建一个工作流

研究负责人根据已选资格包和§9.1，作一次`GO/NO_GO`：主问题、强简单baseline、独立目标/单位、实际效应/风险容差、精度与预算、什么结果会推翻方案。最多两页，复用包内产物，不再建立第七个包或新registry。独立目标、非平凡问题或可用origin任一不成立就NO_GO；通过才另订正式实验/标注/下载合同，预注册先于新结果。

## 13. 资源有限时的时间安排

以研究人员实际可用人日为约束，不能把所有包串成必须完成的巨大流程。

| 时间 | 优先事项 | 交付/拍板点 | 刻意不做 |
|---|---|---|---|
| **未来1周** | WP-01优先；WP-02与WP-03各做最小版本；WP-06只处理authority导航冲突 | 现稿纠偏提案；一张信息/碰撞表；N1是否有独立目标的GO/NO_GO。约5人日，若超量先砍治理整理。 | 训练、重开PR-03、扩基准、PSO、全库清理、方法命名。 |
| **未来1个月** | N1通过才冻结一个小型研究；WP-04/05各做资格审查、择一；选中实验才做WP-06阶段B及立项裁决 | 独立目标和成对对照；至少一个能排除构造解释的有效pilot；下一论文类型裁决。未过则停在经验/边界论文。 | 三条new bets同步铺开；用更多seed/同源变体假装外部验证；为了摘要赶造positive。 |
| **未来3–6个月** | 两个分支择一：独立oracle的跨实现经验研究；或有必要性证据的成本受限观测/选择性决策方法 | 未见origin与机制测试、独立复算、同风险/同成本强基线比较；满足§9.1才claim方法。 | 把EDR全部做完当毕业/论文进度；没有新证据仍扩治理系统。 |

如果1个月后仍无法获得独立目标，**停止方法型投入**，完成窄范围有效性论文及可复现反例集；不以大训练消耗资源来掩盖目标缺失。只有选择性决策证实廉价策略存在稳定不足时，学生模型才进入3–6个月候选，而非承诺任务。

## 14. 一手文献对战略的约束

本轮是定向查证，不是系统综述；“未见完全相同方法”不能作为novelty证明。

- **[W1]** Li & Offutt, *Test Oracle Strategies for Model-Based Testing*, TSE 2017：[作者全文](https://www.albany.edu/faculty/offutt/research/papers/testOracle.pdf)。RIPR区分传播与揭示；oracle观察量/频率及其成本已是成熟问题。本文的层级展开是基本代数，不能包装为新理论；真正增量需是独立目标和AI数据流上的可验证结果。
- **[W2]** Li et al., *Auditing the Audit: Five Failure Modes in Benchmark-Validity Audits*, 2026：[一手全文](https://arxiv.org/html/2607.02586v1)。已直接讨论扰动未进入实际scorer、评分不忠实、配对统计和目标类型混淆等审计失效。内部harness事故分类与新增gate本身难以成为独特贡献；需改变实质科学判断或外部独立验证。
- **[W3]** Tan et al., *AgentChaos*, 2026：[一手摘要](https://arxiv.org/abs/2608.06790)。已有runtime fault injection与触发确认工作；“给agent注入错误”不是空白。项目机会是目标有效性和观测必要性，而非再做通用注入平台。这里只核摘要范围。
- **[W4]** Wang et al., *GTA-2*, 2026：[一手摘要](https://arxiv.org/abs/2604.15715)。递归checkpoint evaluation已存在；借其long-horizon动机不等于本项目已经评价真实长程workflow。这里只核摘要范围，后续需全文核任务/指标差异。

## 15. 证据导航与本轮边界

选择文件的原则是“是否改变决策”：以当前closeout/claim为入口，跟到争议句的响应表、原对照、autopsy和少数实际runner；未机械遍历src、全部skill或所有历史实验。副本/export pack不算独立佐证。三路审查为文本/代码独立视角，不是新的GB10复算或项目Loop C运行认证。

| 编号 | 核心来源与本轮用途 |
|---|---|
| S1 | [历史closeout](../archive/2026-10-19_PROJECT_CLOSEOUT_AND_HANDOFF_v1.md)、[STATE](../../memory/STATE.md)、[科研README](README.md)：定位当前authority、分支终态、未成立任务与入口漂移。 |
| S2 | [canonical manuscript](../../paper/saner_rene_manuscript_v1.md)、[claim matrix](../../paper/saner_rene_claim_matrix_v1.json)、[scope lock](../../paper/saner_rene_manuscript_scope_lock_v1.md)：精读核心论证，不改冻结稿。 |
| S3 | [observability metrics](stage_e_observability_metrics_v1.md)、[zero-event note](stage_e_zero_event_uncertainty_note_v1.md)：构念、分母、循环标签与零事件不确定性。 |
| S4 | [matched-FPR说明](stage_e_matched_fpr_reanalysis_v1.md)、[既有复分析JSON](../../research/stage_e_method_revision_20261009/matched_fpr_reanalysis.json)：clean support、仿射结构及耦合阈值。 |
| S5 | [multi-leaf packet](stage_e_multileaf_result_packet_v1.md)、[signature ablation](stage_e_multileaf_signature_ablation_v1.md)：满分的来源、部分信息、R/N碰撞与重复测量。 |
| S6 | [accepted FinQA autopsy](finqa_v2_measurement_object_mismatch_autopsy_v1.md)、[旧复算audit](../experiments/2026-10-10_loop_c_finqa_v2_formal_v3_recompute_audit.md)、[scorer](../../research/finqa_independent_observation_scorer_v2.py)：复算正确与transfer解释有效性分开。 |
| S7 | [PR-03 v3结果](../../research/positive_repair_20261011/PR-03_v3_RESULT_v1.md)、[repair registry](../../research/positive_repair_20261011/POSITIVE_REPAIR_REGISTRY_v1.json)：退化baseline、点判、执行归因、closed分支。 |
| S8 | [D3历史autopsy](../experiments/2026-09-08_d3_autopsy_decision_record.md)、[Stage B原对照](../experiments/2026-09-06_d3_matched_fpr_stage_b.md)：OCR等价替代解释、标签生成与异质5/8比较。历史证据，不作现状authority。 |
| S9 | [Stage D residual memo](../experiments/2026-10-05_stage_d_necessity_residual_memo.md)、[necessity gate](../experiments/2026-10-05_stage_d_necessity_gate.md)：B4强基线、残差集中与训练必要性未成立。 |
| S10 | [aggregator](../../scripts/eval_checkpoint_aggregate.py)、[multi-leaf runner](../../research/stage_e_multileaf_20261010/run_multileaf_formal.py)、[CORE](../../memory/CORE.md)：有效权重、非线性例外和执行边界。 |
| S11 | [meta-retrospective独立audit](../experiments/2026-10-10_loop_c_graph_loop_meta_retrospective_audit.md)、[PR-03 v3历史preflight](../../research/positive_repair_20261011/runs_local_mirror/PR-EXP-03-v3/preflight.py)、[execution preflight v2规范](../../research/positive_repair_20261011/execution_preflight/EXECUTION_PREFLIGHT_SPEC_v2.md)、[claim verifier](../../scripts/verify_claim_evidence.py)：已有失效和检查器保证范围；历史audit不推断修复后当前运行态。 |
| S12 | [bandit gate既有记录](../../logs/graph/eval/bandit_gate_v0_eval.json)、[prospective记录](../../logs/graph/eval/bandit_prospective_eval.json)：原奖励全1；反事实增益取记录值。不能据此识别adaptivity效应。 |
| S13 | [visibility定义](stage_e_threshold_visibility_analysis_v1.md)、[三seed runner](../../research/paper_w2_e16_injector_seeds.py)：两种可见性口径和pooling依赖待核；不宣布既有CI错误。 |

本报告记录了新的审查风险和待裁决建议，**未宣布既有结果失效、投稿已撤回或新路线已批准**。旧数字、协议、代码和status保留；后续工作以独立可复核的提案进入作者/owner决策。
