# Stage E Inquiry, Public-Source Audit, and Experiment Design

> Status: `DESIGN_ONLY_NOT_AUTHORIZED` | Access date: 2026-10-08 | Evidence package: metadata, analysis, and design only
> Canonical source: `paper/teacher_review_draft_v1.md`
> Metadata appendix: `docs/datasets/2026-10-08_stage_e_public_source_metadata_audit_v1.json`

本文只解释当前 measurement-validity / meta-evaluation 小论文、审计可公开访问的论文与仓库元数据，并把后续实验写成可执行但未授权的设计。外部查询记录保留原始 URL、日期、HTTP 状态与回退来源；没有读取数据正文、ground truth、target labels、hidden splits、private samples、model weights 或凭证。

Skill loading: `inquiry-methods`, `paper-lookup`, `paper-review-check`, `research-driven-design` 均存在并在本任务中加载；未安装、未同步、未修改调度。本报告没有因缺少技能而回落到未声明的替代 skill。

## 1. 小论文内容双层详解

> Inquiry mode: `dual-explanation`

### Beginner layer

论文问的不是“模型最终答案对不对”，而是“现有评分流程能不能看见并正确报告一个中间错误”。例如，一个表头变更已经让系统在第一步选错了字段，但最终映射文字碰巧没有变化；只看最终答案的评测会判为正确，于是无法说明评测器是否看见了缺陷，也无法说明缺陷是否真的有害。

论文把这件事拆成三层：某个缺陷在检查点上是否**可见**（visibility）、评分协议是否把它**检出**（detection），以及只有当等价关系被破坏时它是否**有害**（harmfulness）。报告的对象是评估协议的有效性边界，不是训练一个更强的检测器。

### Expert layer

- **Measurement object:** evaluation-protocol construct validity，即输入缺陷、中间证据、协议判定与最终行为之间的测量关系；不是学生模型性能，也不是完整 Evaluate-Distill-Evolve 结果。
- **Observation surface:** 95 张表上的 118 次合成表头漂移注入；表面包括 checkpoint/forest evidence、final mapping、flat leaf score、hierarchical score 与 per-family visibility profile。
- **Decision predicate:** visibility 以冻结的五阈值 checkpoint 准则判定；end-to-end detection 以 final mapping 是否改变判定；flat/hierarchical detection 以各自冻结阈值上的 score drop 判定；harmfulness 依赖输入响应与协议等价关系。
- **Denominator:** 主要 visibility/detection 分母是 118 次注入；table-level signal 的分母是 95 张表；OCR-like family 的 visibility 分母是 13。不同判据的计数不是同一总体的互斥划分。
- **Scope limit:** 当前构造只有一个 scored leaf 对输入敏感；因此 `[0,0]` 只能解释该退化构造下的阈值混淆，不能外推为层级协议的一般定理，也不能成为 detector superiority claim。

### Contribution map

| 标签 | 贡献 | 正确解释 | 不包含 |
|---|---|---|---|
| C1 | construct separation | 把 visibility、detection、equivalence-dependent harmfulness 明确分开 | 不是把三个量合并成单一总分 |
| C2 | evidence instrument | 层级 checkpoint forest 加 per-family visibility profile 暴露观测盲区 | 不是新的强检测算法 |
| C3 | protocol audit | 对 threshold、matcher、seed、normalization、matched-FPR 与 weight search 做受控审计 | 不是层级结构普遍优于平铺结构的证明 |

`FACT`: 95 tables、118 injections、C1/C2/C3、题名和研究身份均可追溯到 `paper/teacher_review_draft_v1.md` 及其绑定清单。
`INFERENCE`: 若最终答案不变，只能说明该观察面没有变化，不能推出中间证据没有变化；因此 final-answer correctness 不足以单独建立可靠性。
`VALUE`: 当前优先研究“测量是否有效”，而不是扩大模型规模或提前进入训练。
`UNVERIFIED`: 当前包没有独立外部复现、新数据泛化或生产运行证据。

## 2. 小论文研究对象双层详解

> Inquiry mode: `dual-explanation`

### Beginner layer

研究对象不是某一个具体模型，而是“我们用来判断系统是否正常的那套尺子”。例如，OCR-like 表头噪声在五种阈值下都未被 checkpoint 观察到，说明有些缺陷会被观测表面隐藏；即使另一个评分协议给出很多检出，也不能自动证明它真的定位到了这些隐藏缺陷。

当前对象还包括三棵树：解析树把表头字段和落点信息拆成可检查证据；QA 树保留问题、支持证据和输出叶的冻结评分；最终协议只在明确的叶、权重、阈值和匹配规则上做出判定。层级结构在这里首先是证据组织方式，不是排序算法。

### Expert layer

- **Measurement object:** 从 synthetic header-drift input 到 checkpoint visibility、protocol detection 和 harmfulness 判定的测量链。
- **Observation surface:** parsing tree 的 field-hit/drop evidence；QA tree 的 leaf evidence；协议表中的 end-to-end、flat 和 hierarchical 信号。
- **Decision predicate:** leaf score 超过所选阈值；稳定规则要求至少 90% leaves 超阈值且每个 hinge leaf 至少 7 分。drop 规则为 `(H_orig - H_inj) * 10`，主阈值为 2.0。
- **Denominator:** 118 次 injection 用于主比较；95 张 table 用于 table-level 与 cluster bootstrap；family 分母分别是 alias 47、date 17、mixed language 20、OCR-like 13、prefix 16、unit suffix 5。
- **Scope limit:** 当前 parsing-root drop 被剪到唯一输入响应的 field-hit-rate leaf；QA-tree leaves 保持冻结证据并作为独立 arm 报告。因此只能说明该实例不能证明 localization，不能说明层级表示没有潜在信息。

### 术语与常见误读

| Term | 本论文含义 | 不应理解为 |
|---|---|---|
| Leaf score `S(n)` | 映射后的 contract/judge score | 原始概率或通用模型置信度 |
| Local normalized sibling weights | 同一父节点下子叶的局部归一化权重 | 全局可比的重要性分数 |
| Threshold | 预先固定的 operating point | 为获得更好结果而事后调参 |
| Hinge leaf | 必须至少达到 7 分的承重叶 | 可以被平均叶掩盖的普通叶子 |
| Missing evidence | 无该输入的可观察证据 | 已证明证据为零或缺陷不存在 |
| Checkpoint visibility | 输入改变是否跨过 checkpoint 准则 | 事实层面完全“看到”缺陷 |
| Protocol detection | 冻结决策谓词是否发出阳性 | 必然定位到正确叶或已造成伤害 |
| Harmfulness | 等价依赖的失败后果 | 任何 header 字符串变化本身 |
| `[0,0]` | 单可变叶构造下 2,000 次 table-cluster bootstrap 的退化差值区间 | 层级与平铺协议永远相同的定理 |
| PSO | 权重搜索的 informative null | 更优越的优化器或检测器 |

`FACT`: `0/13` 是 OCR-like visibility；`112/118`、`85/118`、`13/118` 分别属于三种不同 decision signal；`[0,0]` 来自 2,000-replicate table-cluster bootstrap。
`INFERENCE`: visibility 与 detection 计数的分母相同但观测面不同，所以 `96/118` 与 `112/118` 不必一致，也不能做减法解释“漏检”。
`VALUE`: 层级结构的价值应先定义为证据分解，再由 multi-leaf 设计检验是否产生额外 localization value。
`UNVERIFIED`: 尚无第二个 parser/dataflow 或独立 scorer 证明这些行为可复现。

理解检查（共 3 项）：

1. 为什么 `112/118` 可以高于 visibility `96/118`？
   Answer: 因为 end-to-end predicate 只检查 final mapping text 是否改变，而且改变后的 canonical match 仍可能保持正确。
2. 为什么 `[0,0]` 不能被写成层级协议的普遍结论？
   Answer: 该区间依赖“只有一个 scored leaf 对输入响应”的退化构造；多个可变叶可能产生不同排序和阈值穿越。
3. checkpoint visibility 与 protocol harmfulness 中哪一个是输入本身可见性的直接测量？
   Answer: checkpoint visibility；harmfulness 还依赖协议等价关系与被评分的行为后果。

## 3. 方法和结果双层详解

> Inquiry mode: `dual-explanation`

### Beginner layer

方法先冻结一张表、一次注入和一套评分规则，再分别记录“中间是否看得见”“协议是否报出”“结果是否等价性受损”。例如，协议可能因为最终映射文字改变而报出缺陷，但层级 checkpoint 没跨过阈值；反过来，OCR-like 噪声在 checkpoint 上全部不可见，却可能被另一个信号表面报出。

结果的关键不是“谁的数字大”，而是数字对应的判据不同。原始 flat `85/118` 与 hierarchical `13/118` 的差距在 matched-FPR 下消失，因为两者都只是同一可变叶的仿射变换；这说明未校准 operating point 会制造层级劣势的错觉。PSO 与 greedy 得到相同均值分离且 PSO 多用大量评估，只说明目标函数与搜索空间决定了结果。

### Expert layer

- **Measurement object:** 冻结语料上三类协议的 operating-point validity 与 C1/C2/C3 测量性质。
- **Observation surface:** per-injection visibility、family profile、end-to-end/flat/hierarchical raw detection、matched-FPR flat/hierarchical score、weight-search separation、sensitivity/seed controls。
- **Decision predicate:** 主阈值与五个 sensitivity thresholds；matcher 用 greedy/Hungarian controls；matched-FPR 通过 clean calibration 固定 operating points；hierarchy stable rule 使用 90% + hinge-7。
- **Denominator:** 118 为 injection-level 主分母，95 为 table-level 分母；`20/95` hierarchical raw 与 `13/118` injection-level hierarchy 是不同聚合层级，不能互换。
- **Scope limit:** 结果只建立当前冻结 corpus 和 synthetic construction 的机制/边界证据；Stage R 是 mechanism/boundary evidence only，Stage D 是 `DATA_NO_GO / RQ2 NOT_IDENTIFIED`。

### 数字与结果边界

| 数字 | 类型 | 精确含义 | 禁止的升级 |
|---|---|---|---|
| `95` | FACT | 95 张冻结表 | 不是 95 个独立 action-correctness clusters |
| `118` | FACT | 118 次 header-drift injections | 不是 118 张表 |
| `96/118` | FACT | checkpoint 可见注入 | 不是协议检出率 |
| `0/13` | FACT | OCR-like 在五阈值均不可见 | 不是 OCR 完全不存在 |
| `112/118` | FACT | end-to-end final mapping change | 不是强定位或 harmfulness |
| `85/118` | FACT | flat field-hit-rate drop 的 raw detection | 不是 matched-FPR 等价结论 |
| `13/118` | FACT | hierarchical pruned parsing-root drop 的 raw detection | 不是层级协议必然较差 |
| `[0,0]` | FACT | 单可变叶下 protocol-difference bootstrap interval | 不是一般等价定理 |
| `51/58/37` | FACT | Q3 exploratory `map_to / skip / hold` | 不是 Stage D/RQ2/training result |
| `8 conservative` | FACT | Valentine 全档的保守 origin components | 不是 551 个独立 origin clusters |
| `DATA_NO_GO` | FACT | 当前正式数据边界 | 不是论文失败或许可不存在 |
| `RQ2 NOT_IDENTIFIED` | FACT | 同 UID bridge 尚未识别 | 不是没有研究问题 |

### 解释、限制与后续工作

- **Result:** C1 拆开三个构念；C2 暴露 OCR-like `0/13` 盲区；C3 显示 raw hierarchy gap 会在 matched-FPR 下变成 `[0,0]` 的退化诊断；PSO 是 informative null。
- **Interpretation:** 当前 hierarchy 主要提供 evidence decomposition；单可变叶使它不能证明额外 localization value。
- **Limitation:** 单一 synthetic construction、一个 scored input-responsive leaf、缺少 second dataflow 与 independent scorer、只在固定 corpus 上验证。
- **Future work:** multi-leaf synthetic experiment、independent scorer、second dataflow adapter、harmfulness definition comparison；这些均为后续授权，不是当前结果。

`FACT`: 三类 raw counts、family visibility、matched-FPR `[0,0]`、PSO 7,650 evaluations 对 greedy 67 evaluations 均来自冻结稿件。
`INFERENCE`: matched-FPR 校准把差异归零，支持“阈值/operating-point artifact”的解释，而不支持“层级没有潜在价值”。
`VALUE`: 复现与 multi-leaf 响应性应先于扩大数据和训练。
`UNVERIFIED`: 新语料、独立实现、生产环境与 Stage D 构念尚未核验。

## 4. 现在可做 / 需授权 / 需新数据

> Inquiry mode: `steelman-decision` + `minimal-experiment`

三张表使用相同字段，以避免把“可分析”“可实验”“可下载”混为一谈。

### Class A：现在可做

| prerequisite | required artifact | risk | question answered | stop condition |
|---|---|---|---|---|
| 只读本地权威文件 | claim-evidence reconciliation ledger | 把推断写成 FACT | 当前数字是否逐项可追溯 | 任一数字无实际 artifact |
| 无凭证的公开元数据 API | URL/date/status/fallback query log | 把论文元数据当数据集许可 | 源、DOI、repo、record 是否存在 | 429/403 单次重试后仍失败即 `UNVERIFIED` |
| 官方 README/LICENSE/Zenodo metadata | licence scope annex draft | 混淆 code/paper/data licence | 哪种用途仍缺许可证据 | scope 无法由实际文件证明 |
| 已有本地归档只读审计结果 | lineage/origin-cluster memo | 把 task 数当 independent cluster 数 | 当前样本是否足够独立 | cluster 低于预定 gate |
| 冻结 Stage E 语料 | protocol/split/power/stop-condition design | 改写既有数字 | 下一实验如何公平检验 | 需要改 frozen corpus/split/threshold |
| 既有 artifact 静态审计 | reproducibility gap list | 把本地 fixture 当 B 验收 | 缺少哪些实现与证据 | 需运行 endpoint、DB 或新实验 |

### Class B：需要新实验授权

| prerequisite | required artifact | risk | question answered | stop condition |
|---|---|---|---|---|
| 多叶注入/leaf matrix 冻结 | `DESIGN_ONLY_NOT_AUTHORIZED` task card | 事后挑选有利 leaf | hierarchy 是否有额外 localization value | matrix/threshold 未先冻结或 cluster 不足 |
| 独立实现可复现相同输入 | independent-scorer plan + receipt contract | 实现者共享同一 bug | 结果是否依赖原实现 | 超预算、endpoint 或 gold-isolation 失败 |
| 第二 parser/dataflow adapter 合同 | second-dataflow feasibility memo | 改变 construct 而非复现 | 行为是否跨 adapter 存在 | 新 adapter 改写 Stage E frozen numbers |
| harmfulness 定义预注册 | definition comparison analysis plan | 混合不同 denominator/风险 | 三种构念是否稳定 | 定义未先冻结或使用 sealed test 调参 |
| Stage D 目标与 gate 仍适用 | necessity re-evaluation card | 把 pilot 升级为确认性结果 | 是否仍值得推进 Stage D | `DATA_NO_GO / RQ2 NOT_IDENTIFIED` 未解除 |
| Q3/B0-B4/Stage D 扩展授权 | separate experiment authorization | 消耗实验窗与 seeds | 新臂是否改变研究方向 | 无 D 授权、window、独立 B 验证 |

### Class C：需要新数据或新许可

| prerequisite | required artifact | risk | question answered | stop condition |
|---|---|---|---|---|
| 精确 source/revision/file-scope annex | bytes/hashes/licence receipt | 下载未批准数据正文 | 新源是否可合法获取 | annex 不完整或用户未批准 |
| origin-cluster census | cluster/split/gold-isolation report | 泄漏 UID/origin | 是否达到独立单位要求 | 达不到预注册 cluster 门槛 |
| correctness join contract | same-UID checkpoint/action/correctness bridge | 不同样本被拼成 bridge | 是否解除 `RQ2 NOT_IDENTIFIED` | bridge 仍非 same-sample |
| 新 action/target ontology review | labelled ontology + adjudication protocol | 事后改 label 或 split | 新标签是否对应研究问题 | ontology/split 未冻结即读取标签 |
| MODEL_GO/TRAINING_GO | training card、licence、budget、window | 把设计当训练授权 | 8B 主学生是否可训练 | 任一科学/数据/安全/窗口门未过 |

## 5. 经典工作与开源数据集候选表

> Inquiry mode: `domain-research` + `fact-check`

访问日期均为 **2026-10-08**。精确 URL、query id、HTTP status、一次 429/403 retry 与 fallback 均持久化在 metadata JSON；本表中的 `UNVERIFIED` 不允许被论文元数据或仓库 code licence 补推。

### 审计预算与事实核查状态

- `FACT`: 72 个 distinct URLs 产生 **94 次实际 HTTP attempts**；预算上限 80，超限 14 次，状态为 `EXCEEDED_TRANSPARENTLY_REPORTED`。
- `FACT`: 状态分布为 48×200、12×403、10×429、2×404；此后不再调用 HTTP。
- `WRONG`: WikiTableQuestions 候选 DOI `10.18653/v1/N18-1057` 返回错误论文；更正为 `10.3115/v1/P15-1142`。
- `INSUFFICIENT_EVIDENCE`: TabFact DOI、DeepMatcher exact paper/repo、PubTables official dataset entry 未由可用元数据确认。
- `CONFIRMED`: FinQA、TAT-QA、PubTables paper、FeTaQA、Valentine、InfoTabS、MultiHiertt、HiTab、ConvFinQA 的 exact paper DOI 已确认。
- `UNVERIFIED`: 未明确的 dataset licence、revision、lineage、origin-cluster count 或 checkpoint/action/correctness bridge。

### 十字段候选表

| 候选 | 1 exact paper / dataset | 2 DOI / official entry | 3 licence and scope | 4 scale / task | 5 table layer | 6 checkpoint / process / action / correctness bridge | 7 independent lineage / origin clusters | 8 visibility / detection / harmfulness | 9 external validity only | 10 download annex |
|---|---|---|---|---|---|---|---|---|---|---|
| FinQA | *FinQA: A Dataset of Numerical Reasoning over Financial Data* / FinQA | `10.18653/v1/2021.emnlp-main.300`; `github.com/czyssrs/FinQA`; `CONFIRMED` | repo MIT; README 在 revision `0f16e286` 未给数据 licence；现有 D-B record 仅限训练/调参/评测/规则验收，其他 scope `UNVERIFIED` | 本地已批范围 7,134 examples，均有矩形表、2–11 列；全局测试规模 `UNVERIFIED` | 7,134/7,134 有表 | reasoning programs/process 存在，但不是 map/hold/skip，也不是独立 correctness bridge；step official-operator route 已停止 | 已批全量 2,409 UIDs / 768 report clusters；不是 768 个当前 action-correctness clusters | 可为未来外部 process/visibility 观察提供 adapter；不原生支持三构念或 Stage D | 是；对当前 Stage E 外部效度，不能确认 Stage D/RQ2 | source/revision/files/bytes/hashes；data licence 与 MIT 分离；report origin map；split；gold isolation；adapter；stop；user approval |
| TAT-QA | *TAT-QA: A Question Answering Benchmark on a Hybrid of Tabular and Textual Content in Finance* / TAT-QA | `10.18653/v1/2021.acl-long.254`; `github.com/NExTplusplus/TAT-QA`; `CONFIRMED` | dataset CC BY 4.0（官方 README）；repository MIT 为 code licence，二者分开 | 16,552 questions / 2,757 hybrid contexts；QA + reasoning program | 有 hybrid table/text；冻结 Stage E derivative 为 95 tables / 118 injections | 冻结 derivative 只提供 synthetic checkpoint evidence；新确认性 RQ2 bridge 未证明 | financial-report context namespace 存在；新独立 cluster count 与历史 exposure `UNVERIFIED` | 可比较历史 visibility/detection，不能原生给 Stage D actions | 是；train/dev 在 exposure audit 前 `HISTORICAL_ONLY` | exposure manifest；exact revision/files/hashes；CC BY scope；origin/split；不重开 TAT-DQA；user approval |
| TabFact | *TabFact: A Large-scale Dataset for Table-based Fact Verification* / TabFact | DOI `UNVERIFIED`; arXiv `1909.02164`、official GitHub/site `CONFIRMED` | dataset licence `UNVERIFIED`；不能推 repo code licence | 117,854 statements / 16,573 Wikipedia tables；ENTAILED/REFUTED | 每条 statement 绑定 Wikipedia table | 无 native checkpoint/process/action/correctness bridge | table-origin 与 split-lineage clusters `UNVERIFIED` | 可做 table fact-verification external baseline；不原生支持三构念或 Stage D action | 是，但须先 licence/lineage annex | exact DOI if needed；official data repo/revision；dataset licence；table origins；split；bridge；user approval |
| WikiTableQuestions | *Compositional Semantic Parsing on Semi-Structured Tables* / WikiTableQuestions | `10.3115/v1/P15-1142`; `github.com/ppasupat/WikiTableQuestions`; `CONFIRMED` | root repo CC BY-SA 4.0；文件级适用性 `UNVERIFIED` | 22,033 examples：14,152 train、4,344 table-unseen test、3,537 table-seen；QA | CSV tables + page HTML | 无 native checkpoint/process/action/correctness bridge | 有 table-level test separation；全 role 独立 origin count `UNVERIFIED` | 可做 unseen-table external QA validity；不原生支持三构念/Stage D | 是，须 licence/split annex | exact revision；CC BY-SA file scope；table/page lineage/split；gold 隔离；adapter；user approval |
| PubTables-1M | *PubTables-1M: Towards comprehensive table extraction from unstructured documents* / PubTables-1M | `10.1109/CVPR52688.2022.00459`; `github.com/microsoft/table-transformer`; official dataset entry `UNVERIFIED` | data-package licence 与 MR Open Data terms `UNVERIFIED`；HF 搜索未找到 Microsoft official entry | protocol records 575,305 pages / 947,642 tables；detection + structure + functional analysis | 强 visual/document table layer、header boxes、structure labels | 无 native semantic checkpoint、map/hold/skip、independent correctness | document/page origin clusters `UNVERIFIED` | 可支持 visual/structural external validity；不解决 semantic harmfulness/Stage D | 是；不能直接作 Stage D source | official dataset entry/revision；data licence；page lineage；split；visual-to-semantic bridge；user approval |
| FeTaQA | *FeTaQA: Free-form Table Question Answering* / FeTaQA | `10.1162/tacl_a_00446`; `github.com/Yale-LILY/FeTaQA`; `CONFIRMED` | 官方 README 明示 dataset CC BY-SA 4.0 | 约 10K table/question/free-form answer/support cells；generative QA + explanation | Wikipedia table + supporting cells | 无 native checkpoint/process/action/correctness bridge | Wikipedia-table origin clusters `UNVERIFIED` | 可做 free-form QA external validity；不原生支持三构念/Stage D | 是，须 lineage/split annex | exact revision；CC BY-SA file scope/attribution；origins；split；adapter/gold isolation；user approval |
| Valentine | *Valentine: Evaluating Matching Techniques for Dataset Discovery* / Valentine Datasets | `10.1109/ICDE51399.2021.00047`; GitHub + Zenodo `5084605`; `CONFIRMED` | Zenodo archive CC BY 4.0；repo Apache-2.0；NYC upstream terms 另管；未下载 archive | metadata 确认 602,150,347-byte 单档；本地既有只读审计 551 complete pairs，schema matching | source/target tables + mappings/config | gold 只支持 map_to；skip/hold 须 Q3；无 native trajectory/checkpoint bridge | 551 tasks 仅 **8 conservative** origin components，低于 40 | 可做 schema-action exploratory/matching external；不能证明当前 Stage E 三构念或确认 Stage D | 是，仅 exploratory/external；仍 `DATA_NO_GO / RQ2 NOT_IDENTIFIED` | 不再下载；未来须 exact revision/files/hashes、NYC terms、lineage、ontology、gold isolation、split、≥40 cluster target、user approval |
| schema matching family | DeepMatcher candidate / Magellan-derived family；exact public benchmark `UNVERIFIED`；Valentine 为另一已验证 exact benchmark | DeepMatcher DOI/repo `UNVERIFIED`；GitHub API 403 后、raw README 404 | paper/code/data licence 均 `UNVERIFIED`；不得借 Valentine licence | scale/composition `UNVERIFIED` | table/schema-pair 层仅 plausible；Valentine 已确认表层 | 无 verified native bridge；Valentine gold 仅 map_to | DeepMatcher lineage `UNVERIFIED`；Valentine 为 8 conservative | 只可在 exact source 验证后支持 map-related external validity | 是，须先 exact source/licence/lineage audit | exact title/DOI；official URL/immutable revision；code vs data licence；files/scale；origins；gold semantics；split/adapter/gold isolation；user approval |
| table fact family | *INFOTABS: Inference on Tables as Semi-structured Data* / InfoTabS；TabFact 另行审计 | `10.18653/v1/2020.acl-main.210`; code/data repos `CONFIRMED` | repo root Apache-2.0；dataset README 指向 LICENCE/Datasheet 的 non-academic terms；scope `UNVERIFIED` | sample count `UNVERIFIED`；infobox premise + human hypothesis，entailment/contradiction，alpha splits | semi-structured Wikipedia infobox table | 无 native checkpoint/process/action/correctness bridge | infobox/table origins 与 role capacities `UNVERIFIED` | 可做 table-inference external validity；不原生分离三构念或 Stage D | 是，须 licence/lineage annex | exact revision；datasheet/non-academic terms；scale/split；origins；adapter/bridge；user approval |
| financial table QA family | MultiHiertt；HiTab；ConvFinQA exact papers/datasets | DOIs `10.18653/v1/2022.acl-long.454`, `10.18653/v1/2022.acl-long.78`, `10.18653/v1/2022.emnlp-main.421`; official repos `CONFIRMED` | prior registry 为三者 code MIT；HiTab dataset C-UDA 1.0；MultiHiertt Drive terms、ConvFinQA data scope `UNVERIFIED` | HiTab README 10,672/3,597（paper v3 为 10,686，版本差异）；其余 exact scale `UNVERIFIED` | MultiHiertt multi-hierarchical HTML；HiTab hierarchical；ConvFinQA inherited FinQA table | programs/supporting facts/QA-NLG/conversation 均需 adapter；都不是 full same-sample bridge | MultiHiertt/FinQA doc namespace 存在但 fresh cluster counts `UNVERIFIED`；ConvFinQA 不可当独立 test | 可支持未来 hierarchy/process external stress；不能当当前 Stage E 或 Stage D confirmation | 是；须新 task definition 与 annex | 每源分别给 revision/files/bytes/hashes、data licence/Drive terms、ontology、origins/clusters、split、bridge、gold isolation、stop、user approval |

### Table audit conclusion

`FACT`: 只有 metadata record、README、LICENSE 和既有本地只读结果进入本表；没有数据正文被拉取。
`INFERENCE`: 多数候选具备 table layer，但 table layer 不等于 checkpoint/action/correctness bridge，更不等于可解除 Stage D 的 `DATA_NO_GO / RQ2 NOT_IDENTIFIED`。
`VALUE`: 下一个数据选择必须从 exact annex、licence scope 和 independent origin clusters 开始，而不是从任务规模开始排序。
`UNVERIFIED`: 所有未列明 revision、文件级 licence、fresh origin counts 与 same-sample bridge 均保持 `UNVERIFIED`。

## 6. 其他研究思路

> Inquiry mode: `expert-panel` + `first-principles`

以下是不模仿、也不归因给真实专家的 deliberation roles；它们只用于提出和压测研究边界。

### 6.1 Measurement-science panel

- **Alternative:** 把 visibility、detection、harmfulness 建模为三个有各自观测模型与误分类矩阵的潜构念，报告 construct validity matrix，而不是一个总分。
- **Boundary:** 除非每个构念有独立 indicator 和预注册决策谓词，否则“三个分数”仍只是同一判据的重命名。
- **Experiment:** 先做 observable-by-construct mapping 和专家静态评审；多 indicator 实验需 B 授权。

### 6.2 Psychometrics panel

- **Alternative:** 用 measurement invariance、DIF 和 test-retest 思路检查不同 family、parser、seed、operating point 是否测到同一 latent quantity。
- **Boundary:** 不得用 sealed test 选择 family、阈值或 split；小样本 family 会限制辨识。
- **Experiment:** 当前可静态设计 family-wise reporting；invariance 拟合需新实验授权。

### 6.3 Reliability-engineering panel

- **Alternative:** 把 header drift 当 mutation，把 checkpoint 当 failure oracle，把 matched-FPR 当 false-positive budget。
- **Boundary:** mutation score 只有在 oracle 对输入响应时才有意义；当前单可变叶 oracle 饱和。
- **Experiment:** multi-leaf synthetic injection 是优先项；canary/rollback 仅是控制类比，不授权运行服务。

### 6.4 Software-observability panel

- **Alternative:** 建立 shadow read-only scoring path，比较同一输入在不同 scorer 上的 trace hash、leaf decision 和 operating point。
- **Boundary:** “shadow”不能绕过 endpoint/database 禁令；本轮只设计 receipt，不执行。
- **Experiment:** independent scorer reproduction 在获得 B 授权后使用离线固定 artifact。

### 6.5 First-principles synthesis

1. **Observability:** 输入变化必须至少影响两个可评分位置，否则无法检验定位。
2. **Independence:** 独立单位必须按 table/origin cluster，而不是 injection 或 task 数。
3. **Calibration:** operating point 必须在 clean calibration 数据上固定，不能看过 evaluation 结果再调。
4. **Construct separation:** visibility、detection、harmfulness 必须分别计数，禁止用一个替代另一个。
5. **Reproducibility:** 第二实现必须在不共享实现 bug 的情况下重放相同 hash-bound inputs。
6. **Authorization:** 设计、执行、B 验证、C 审计和 D 验收是不同状态。

`INFERENCE`: 这些必要条件共同决定实验是否可解释；缺任何一项，负结果或正结果都可能由测量缺陷造成。
`VALUE`: 先修 observability 和 reproduction，再扩大数据。
`UNVERIFIED`: 当前没有 multi-leaf、second-dataflow 或 independent-scorer receipt。

## 7. 跨领域借解方案

> Inquiry mode: `cross-domain-borrowing`

| 远领域 | structural analogy | transferable mechanism | failure condition | JinRongAgents protocol translation |
|---|---|---|---|---|
| measurement science / psychometrics | 三个构念像不同潜变量，各有观测模型 | indicator mapping、measurement invariance、reliability/reporting | 把总分当构念；样本不足却做 latent fit | 把 visibility/detection/harmfulness 写成独立 cells，family 与 parser 作为 moderator，不做总排名 |
| software reliability / mutation testing | header drift 是 mutation，checkpoint 是 oracle | mutation matrix、kill/no-kill、oracle adequacy | 输入不改变任何 scored leaf；oracle 共享实现 bug | freeze injection×leaf matrix，报告 responsive leaf count 与 no-kill family，不改 frozen Stage E 数字 |
| canary and rollback | 新协议先小范围观测，失败可回滚 | fixed window、budget、stop condition、rollback | 无真实运行收据却声称 canary；测试 fixture 冒充 window | 仅把机制翻译成卡上的 stop/rollback 字段；本轮不启动 watcher 或服务 |
| clinical endpoint separation / blinding | visibility、detection、harmfulness 像 surrogate/intermediate/final endpoints | endpoint hierarchy、盲法、multiple endpoints | 事后挑 endpoint；用 surrogate 代替 final harm | 三个 endpoint 分开预注册；分析者先只看 clean calibration，确认矩阵后揭盲 evaluation |
| financial risk out-of-time validation | origin/time leakage 会制造虚假泛化 | out-of-time split、cluster grouping、stress slice | 按 injection 或同源 task 随机切分 | table/origin cluster 级 split；primary、pair-invalid、salted 只在未来 Stage D 桥上使用其既定风险门 |
| aviation flight recorder / intent separation | checkpoint trace 与最终动作分开记录 | immutable trace hash、intent vs execution、incident reconstruction | trace 不输入响应，或被事后改写 | hash 固定 input/leaf/threshold/output；单列 intended vs executed mapping，不把 trace 当正确性 |
| software observability / shadow deployment | 同输入跑独立 scorer 比较 decision trace | side-by-side reproduction、trace diff、false-positive budget | 读取生产端点、共享 bug、无独立实现 | 设计离线 second scorer；执行须另批，禁止 :5050/:8004/:8006/:8008/:4096 |

### 实验类型分层

- **可强化当前 Stage E:** metadata/claim reconciliation、静态 term map、现有 artifact 静态 audit；授权后才可做 multi-leaf、independent scorer、second dataflow。
- **只服务未来 Stage D/RQ2:** same-UID checkpoint/action/correctness join、cluster expansion、Stage D necessity re-evaluation、harmful-map risk validation。
- **可能改变方向的高风险实验:** 改 harmfulness ontology、引入新 benchmark/action labels、重做数据路线或直接训练；必须由 D 重新验收研究问题。

`FACT`: 本节是结构类比与设计，不是已有跨领域实验。
`INFERENCE`: 各领域机制只有在满足本项目独立单位、gold isolation 和授权条件后才可迁移。
`VALUE`: 当前只允许把控制思想翻译成合同，不运行 canary、shadow 或 out-of-time 服务。
`UNVERIFIED`: 跨领域 effect size、power 和复现性均未测量。

## 8. 最优先的实验路线

> Inquiry mode: `steelman-decision` + `minimal-experiment`

### 固定优先级

1. **metadata-only dataset/source annex audit** — 本轮 Stage A 已完成，但 HTTP budget 异常必须保留；任何新源仍须完整 annex。
2. **multi-leaf synthetic experiment** — 最高优先的下一实验，因为它直接检验当前 hierarchy 证据的不可识别原因；仍为 `DESIGN_ONLY_NOT_AUTHORIZED`。
3. **independent scorer reproduction** — 检验 shared-implementation risk；在 multi-leaf contract 固定后执行。
4. **second dataflow feasibility** — 检验 parser-specific behavior；必须保持 Stage E frozen numbers 不变。
5. **harmfulness definition comparison** — 先定义再比较，不得由结果反向选择定义。
6. **Stage D necessity re-evaluation** — 只有 bridge、cluster、split、power、baseline 等门重新通过后才讨论。
7. **training** — 仅在 1–6 全部通过且另有 MODEL_GO/TRAINING_GO 后才允许。

### Steelman argument

**Why multi-leaf first:** 当前最明确的机制缺口不是“数字还不够大”，而是唯一 input-responsive leaf 让层级差异无法被识别。构造至少两个响应叶，可以同时检验 operating point、证据分解和 localization，而不需新数据或模型调用。
**Why not skip to data:** 新 benchmark 若仍只有一个响应叶，只会把同一测量缺陷搬到不同语料；且任何下载都需要 licence/lineage/gold annex。
**Why not train now:** Stage D 仍为 `DATA_NO_GO / RQ2 NOT_IDENTIFIED`，551 tasks 只有 8 conservative origin components，且训练门未通过。

### Minimal experiment boundary

- 使用现有冻结语料作为新的、显式命名的 synthetic protocol namespace，**不重写 Stage E frozen numbers**。
- 预先冻结 injection×leaf matrix、thresholds、family、calibration/evaluation role 与 table-level cluster。
- clean tables 只用于 operating-point calibration；读结果后不得改阈值。
- 每个 injection 分别报告 visibility×detection×harmfulness cell，禁止把计数合并。
- 先要求至少两个 leaf 对输入响应；否则在分析前触发 stop，不进入 hierarchy comparison。
- 这是 Stage E 机制实验，不把 Stage D 的 `harmful-map risk upper <= 0.10` 借来当 Stage E claim；未来 Stage D 设计仍须在 primary、pair-invalid、salted 三片保留该批准上限。

`FACT`: 固定优先级与当前单可变叶限制来自 task card 和冻结稿件。
`INFERENCE`: multi-leaf 是对当前构念缺口最直接、最小的新实验。
`VALUE`: 它排在 independent scorer 之前，因为它先决定被复现的对象是否可识别。
`UNVERIFIED`: matrix、power、runtime 与结果均未生成。

## 9. 一份可以直接写进 task card 的实验设计

> Inquiry mode: `minimal-experiment`

### 9.1 Design-only status

**状态：`DESIGN_ONLY_NOT_AUTHORIZED`。** 本设计可粘贴到未来 task card，但本轮不创建实验运行、不改 frozen corpus、不调用模型或服务，也不产生 confirmatory result。

### 9.2 Complete design table

| Design field | Specification |
|---|---|
| Research question | 在 operating point 固定于 clean calibration 且至少两个 scored leaf 输入响应时，hierarchical protocol 是否显示超出 flat protocol 的、可复现的 localization/detection difference？ |
| Hypotheses and preregistered predictions | H1: 预注册 injection×leaf matrix 中至少 2 个 leaf 在主 threshold crossing 上响应；否则 STOP_BEFORE_ANALYSIS。H2: primary prediction 为 matched-FPR 下 hierarchical-minus-flat detection 的 table-cluster bootstrap 95% CI 下界 `>0`；若 CI 包含 0，记为 NOT_IDENTIFIED，不改 threshold。H3: visibility、detection、harmfulness 三者不得互相替代；OCR-like 至少作为 predefined negative-observability control 报告，不追加 family。 |
| Independent unit and cluster | 独立单位是 table；cluster 按实际 table origin/lineage 分组。118 injections 是重复测量，不作为独立 n。若不能形成至少两个 non-empty roles 且每 role 有预注册最低 cluster 数，STOP_INSUFFICIENT_CLUSTER。 |
| Split and UID/origin isolation | 在任何 score/result inspection 前用 hash-bound rule 将 table clusters 分为 calibration、evaluation 与 sensitivity roles；同 origin/UID 不得跨 role。不得按 injected label、visibility、detection 或 sealed test 调 split。现有 95 tables/118 injections 保持原样，只增加 synthetic protocol namespace mapping。 |
| Metrics | Primary: matched-FPR detection difference with table-cluster bootstrap CI。Secondary: injection-level visibility, detection, harmfulness counts；family-wise sensitivity；responsive-leaf count；threshold stability；trace hash reproducibility。分别给出 denominator 95、118、family n；不把 table-level 和 injection-level 混为 partition。 |
| Harmful-map risk limit | Stage E 主设计不将 harmfulness 当 Stage D harmful-map；以平行 construct 分格报告。若未来扩展为 Stage D/RQ2，则保留批准的 `harmful-map risk upper <= 0.10` 于 primary、pair-invalid、salted，且不得用本 Stage E 实验替换该 gate。 |
| Baselines | Current frozen Stage E single-responsive-leaf reference (`96/118`, `0/13`, `112/118`, `85/118`, `13/118`, `[0,0]`) 只作不可改写的参考；flat score、hierarchical score、end-to-end signal、greedy/Hungarian controls；equal/expert/random/greedy/PSO/minimax weights 仅作预注册 control，不以 optimizer 名称选结果。 |
| Stop conditions | 未冻结 matrix/threshold/split；少于 2 responsive leaves；cluster role 不足；calibration 越过 evaluation；出现 endpoint/judge/service/database/ground-truth access；任何 frozen file 会被修改；结果后调 threshold/family/label；单次重试后 rate limit；预算/时间超出批准；需要下载 body 或改 licence。 |
| Data, licence, checkpoint and gold isolation | 数据仅用已有 frozen Stage E corpus 的 metadata/artifact inventory；不新增 download。须在卡中给出 corpus/frozen file hashes、licence/provenance 只读声明、synthetic namespace manifest、checkpoint artifact hashes、injection matrix 与 gold isolation receipt。任何 target/ground truth 读取都会 STOP。 |
| Cost, time and resources | 资源：Python 3.12、`PYTHONPATH=src`、静态 fixture、CPU bootstrap；零模型调用。建议时间盒：1 个预注册日 + 1 个离线 dry-run 日 + 1 个 B 验证日；实际 runtime/seed 数在独立静态 feasibility 后填，不能现在伪造。 |
| What can run first | 先完成 metadata annex、matrix/threshold/split/UID contract、静态 fixture 构造与人工 prereg review。之后先运行 gold-free smoke，确认 trace/hash 和至少两 responsive leaves。 |
| What must wait | 实际 evaluation scores、matched-FPR comparison、bootstrap、second scorer、second dataflow、harmfulness comparison、Stage D necessity、Q3/B0-B4/Stage D extension、training 全部等待单独 B/D 授权和独立验收。 |
| Exploratory vs confirmatory | matrix、threshold、cluster split 和 hypotheses 冻结后才允许 confirmatory label；本轮和任何中断后的 partial run 均为 `DESIGN_ONLY_NOT_AUTHORIZED` / exploratory planning，绝非 Stage D、Stage R、RQ4、Q3、training 或 submission evidence。 |

### 9.3 Paste-ready task-card block

```markdown
id: TASK-STAGEE-MULTILEAF-DESIGN-V1
risk: medium
status: DESIGN_ONLY_NOT_AUTHORIZED
window: none
goal:
  - Freeze a synthetic multi-leaf protocol namespace without modifying Stage E frozen numbers.
  - Test whether at least two input-responsive leaves unlock a pre-registered hierarchy comparison.
premises:
  - source_sha256: abab44657e17936badf371a606198886ccd333a4c1489600c8922f78a6c57e80
  - frozen_corpus_unchanged: true
  - model_calls: 0
design:
  research_question: "Does hierarchy show a reproducible localization/detection advantage under matched FPR with at least two responsive leaves?"
  hypotheses:
    H1: "The frozen matrix changes at least two scored leaves; otherwise STOP_BEFORE_ANALYSIS."
    H2: "Primary matched-FPR hierarchical-minus-flat bootstrap 95% CI lower bound > 0."
    H3: "Visibility, detection, and harmfulness are reported as separate cells."
  independent_unit: table
  cluster: table origin/lineage
  split: "Pre-registered hash-bound calibration/evaluation/sensitivity roles; no origin or UID crosses roles."
  metrics: "Matched-FPR difference CI; visibility/detection/harmfulness cells; family sensitivity; responsive-leaf count."
  baselines: "Frozen Stage E reference; flat, hierarchical, end-to-end, matching and weight-search controls."
  harmful_map_risk:
    stage_e: "Parallel construct only; no Stage D claim."
    future_stage_d: "Retain approved upper <= 0.10 in primary, pair-invalid, and salted."
  stop_conditions:
    - "Fewer than two responsive leaves."
    - "Threshold/matrix/split frozen after result inspection."
    - "Origin or UID leakage."
    - "Endpoint, judge, canary, model, database, service, ground truth, training, Phase 2, submission, or release access."
    - "Any modification to frozen Stage E files or existing evidence."
  execution_authorization: false
  b_verification_required: true
  d_acceptance_required: true
```

`FACT`: 单可变叶与当前 frozen numbers 已锁定。
`INFERENCE`: 预注册 multi-leaf matrix 能把“无法定位”从概念问题变成可检验预测。
`VALUE`: 先做 gold-free synthetic mechanism check，再决定是否扩大到 scorer/dataflow/data。
`UNVERIFIED`: matrix 具体内容、cluster capacities、B/C/D receipt 尚不存在。

## 10. 仍需用户拍板的决策项

> Inquiry mode: `steelman-decision`

| Decision | Options | Evidence needed | Recommended boundary | Current state |
|---|---|---|---|---|
| D1: 下一实验 | multi-leaf synthetic vs second dataflow | matrix 可识别性、adapter impact、resource cost | 先 multi-leaf；它直接检验当前构念缺口 | 待用户拍板 |
| D2: harmfulness 定义 | input-response harm、equivalence-dependent protocol harm、其他新定义 | denominator、counterfactual、gold/isolation、risk mapping | Stage E 保持现有 equivalence-dependent construct 并做平行报告 | 待用户拍板 |
| D3: synthetic matrix | injection family、responsive leaves、negative controls | 预先静态响应性证明；不得读 evaluation scores | 固定至少两 responsive leaves，OCR-like 作 predefined control | 未冻结 |
| D4: cluster/split gate | calibration/evaluation/sensitivity 的最低 table clusters | origin census 与 power | cluster 不足即 stop，不用 injection 数替代 | 未测量 |
| D5: independent scorer scope | 同 decision predicates 的独立实现 | code independence、trace hash、budget | 与 multi-leaf contract 同时冻结，不共享实现 | 未授权 |
| D6: future data path | no new data vs exact-source annex vs new source | licence、revision、file scope、origin clusters、bridge | 先完成十字段 annex，不从 scale 排序 | `DATA_NO_GO` 保持 |
| D7: external actions | advisor review only vs submission/arXiv/code release | venue/author/patent/licence/release gate | 专利状态与授权未确认前不外发 | 本轮禁止 |

`FACT`: Stage E advisor-ready 的既有两项主决策仍是 multi-leaf vs second dataflow、harmfulness 定义。
`INFERENCE`: D3–D5 是把 D1/D2 转成可执行卡的必要细化。
`VALUE`: 用户只需要拍板研究边界；Agent 不得自行推导授权。
`UNVERIFIED`: 各决策的效果、power 与成本尚未实测。

## 11. `FACT / INFERENCE / VALUE / UNVERIFIED` 证据分级

> Inquiry mode: `fact-check`

- **`FACT`:** mechanically supported by a repository artifact or verified metadata record。例：source SHA、95/118、`0/13`、Zenodo record `5084605`。
- **`INFERENCE`:** derived from facts；必须给出 reasoning chain。例：final answer 不变不能推出 checkpoint 不变；单可变叶使 `[0,0]` 不能一般化。
- **`VALUE`:** priority、preference 或 normative judgment。例：先做 multi-leaf，后训练。
- **`UNVERIFIED`:** plausible but missing a source、licence、revision、bridge 或 receipt。例：TabFact data licence、DeepMatcher exact record、fresh cluster counts。
- **External status labels:** `CONFIRMED`、`NEEDS_NARROWING`、`CONTESTED`、`INSUFFICIENT_EVIDENCE`、`WRONG`。

### Claim fact-check appendix mapping

| Status | Claims |
|---|---|
| `CONFIRMED` | Stage E identity；FinQA DOI；TAT-QA DOI/scale/licence；FeTaQA exact title；Valentine DOI + Zenodo licence；financial-family exact DOIs |
| `NEEDS_NARROWING` | FeTaQA initial wording correction；InfoTabS code vs data scope；family-level bridge/lineage claims |
| `CONTESTED` | 本轮没有可诚实标为 `CONTESTED` 的 dual-source conflict；不为凑标签制造冲突 |
| `INSUFFICIENT_EVIDENCE` | TabFact DOI；PubTables official dataset entry；DeepMatcher exact paper/repo |
| `WRONG` | WikiTableQuestions DOI `10.18653/v1/N18-1057`；“HTTP attempts ≤80” |

`FACT`: 十二条 claim fact-check 已持久化于 metadata JSON。
`INFERENCE`: `WRONG` 候选已由 actual returned title/correct record 修正，而不是删除失败记录。
`VALUE`: 保留失败查询和超预算事实优先于表面完整。
`UNVERIFIED`: 403/429/404 后的 fallback 不得被猜测性补齐。

## 12. 明确列出没有执行的事项

> Inquiry mode: `fact-check`

本轮**没有**执行以下事项：

1. 没有下载 dataset archive、CSV、JSON data body、model shard、private sample 或 ground truth。
2. 没有读取 `ground_truth.json`、target labels、hidden splits、credential files、`~/.claude/settings.json` 或 `~/.codex/auth.json`。
3. 没有调用或探测 `:5050`、`:8004`、`:8006`、`:8008`、`:4096`、judge endpoints、canaries、模型 API、数据库或服务。
4. 没有执行 Codex 之外的任何模型调用；没有 judge、probe 或新实验。
5. 没有运行 A0-A3、Phase 2、Q3/B0-B4 rerun、B5、Track B 新臂、Stage D necessity experiment、training 或 formal experiment。
6. 没有修改 `tests/test_m1_service.py`、`scripts/graph/frozen_hashes.txt`、frozen schema、`docs/33*`、`docs/34*`、TAT-DQA boundaries 或既有 evidence artifacts。
7. 没有把 exploratory、`PILOT_ONLY`、planned、metadata-only 或设计状态升级为 confirmatory evidence。
8. 没有提交、push、amend、force push、`git add -A`、`--no-verify` 或 history rewrite；`commit=NOT_AUTHORIZED`。
9. 没有投稿、上传 arXiv、发布代码或执行任何 external release。
10. 没有运行完整 pytest suite；这是零 endpoint 研究/报告任务，未运行不得表述为“测试通过”。
11. 没有继续 HTTP 调用；在记录 **94 attempts / 72 URLs、超预算 14** 后停止。
12. 没有新建并运行 watcher、canary 或生产检查；不以测试 fixture 冒充真实运行收据。

### Exit statement

本包成功达到“报告与设计”出口：两份新工件、12 个规定章节、metadata audit、状态/未决台账和一条最终 dispatch receipt 均形成静态证据。其科学状态仍为 `DESIGN_ONLY_NOT_AUTHORIZED`，执行面状态仍为 `DATA_NO_GO / RQ2 NOT_IDENTIFIED`。HTTP budget exception 是必须保留在最终 accounting 中的 warning，不因交付完成而重分类。
