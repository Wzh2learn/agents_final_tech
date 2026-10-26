# 方法、结果与局限（C1—C3）

版本：2026-10-26
目标时间线：2027 年 10 月学位评审窗口；确切日期尚未由 Owner 提供，不得假定为 10 月 31 日。

## 0. 证据等级定义

- **已验证**：可由当前冻结工件、确定性重算或当前包审计直接支持的事实/结果；
  “已验证”只在所写构造、分母、模型和契约范围内有效。
- **开发观察**：development replay、post-hoc 修正、复用面板、单次本地运行或不可部署诊断；
  可用于方法边界和停止判断，不用于独立泛化主张。
- **未验证**：当前证据缺少的跨来源、前瞻、独立、人评、成本稳定性或部署效用证据。

## 1. C1：Paper E 测量审计

### 1.1 方法

本研究点不提出新的模型或通用评价理论，而是审计一个评价能否支持其报告的推断。
测量对象被拆为六个相互关联但不可互换的量：observation visibility、downstream
detection、contract-relative harmfulness、score sensitivity、decision stability 和
reproduction gap。

Case 1 使用 95 张公开 TAT-QA 表和 118 次合成 header injections，覆盖六个 family。
每个注入保留 source table、family、seed、changed field 和预期观察面。逐 seed 的不确定性
以注入的 source-table 为单位；合并三个 seed 时，对重复 source-table UID 做 cluster bootstrap。
阶段对齐研究在相同 12-leaf observation surface 上构造 216 次 injection 和 72 个 clusters，
用 leave-one-cluster-out、cluster bootstrap 和 permutation null 评估受控三阶段可分性。
FinQA 是 Case 1 内嵌的 measurement-object boundary probe，不是第三案例。

Case 2 对 FinRank revision `916dc27e77b90e294ea1b3a2cc5b0abcf07392d1`
执行确定性审计。对象为 1,185 条记录、TF-IDF/BM25、candidate construction、tie order、
source identity、metadata filtering 和报告指标。问题、tie metrics 与 materiality thresholds
在 v1 中预先固定；v2 因 v1 使用 raw-exact 而改为作者的 canonical `text_sha1` identity，
故所有 v2 identity 结果明确标记为 post-hoc。

### 1.2 结果

**已验证。** 在冻结的主观察面上，118 次注入中 96 次 visible、22 次 silently absorbed；
OCR-like family 为 0/13 visible，跨 11 个 source-table clusters 且在五个测试阈值下均不可见。
该结果证明 aggregate visibility 会掩盖 family boundary，但不证明 OCR-like 变更有害。
单一既有 judge 将 13 个 cases 判为 referentially equivalent，只提供 benign absorption
的替代解释，不构成独立 human gold。

**已验证。** 在当前 single-responsive-leaf construction 中，未取整的 hierarchical
contrastive score 是 flat contrastive score 的正重标度，拟合斜率约为 0.375，排名与对应
decision 完全一致。因此 Table 2 的原始 protocol gap 不能被解释为 ranking-quality 差异。
这不是 flat 与 hierarchical 评价一般等价的定理。

**已验证。** 2,382 条可用 clean records 的 score support 均为 `{0}`，所以当前 clean-only
程序无法识别唯一 matched-FPR operating point。该负结果只针对当前 clean-only contract，
不否定 matched-FPR 比较在其他 clean support 下的可用性。

**已验证。** 三个 injection seeds 的 flat table-run point estimate 为 219/282=0.7766，
但 282 次 run 只对应 119 个唯一 source-table UIDs。post-hoc deterministic UID-cluster
bootstrap 的 95% interval 为 [0.7117, 0.8364]；等权 UID estimate 为 0.7535，
interval 为 [0.6835, 0.8207]。仅三个 seeds 不支持总体 seed interval。

**已验证。** 显式 instrumented 的 216-injection 构造中，leave-one-cluster-out
macro-F1 与 top-1 均为 1.000，cluster-bootstrap 区间均为 [1,1]，permutation
`p=1/10001`。但三-direct-leaf codebook 同样为 1.000，移除直接叶后 top-1 与
macro-F1 均降至 0.3333。该结果验证的是 contract-derived stage instrumentation，
不是 hierarchy 的自然定位能力。

**已验证。** 嵌套 FinQA probe 的结果为 V=89/89、D=0/89、O=0/89。由于扰动未重算
下游 result fields，D=0 只说明检测谓词读取了与被修改字段不同的对象；
它不是协议盲、迁移失败或检测能力估计。

**已验证。** 在 FinRank 上，TF-IDF 的 hard/random gap 在 ties-positive、strict-win、
half-credit 下分别为 14.179、13.821、14.000 个百分点；BM25 分别为 13.009、12.666、
12.838。ties-positive 到 strict-win 使 random absolute accuracy 变化 1.084/1.029 点，
跨过预设 1.0 点阈值，而 hardness gap 只变化约 0.359/0.343 点且方向不变。

**开发观察。** canonical `text_sha1` 复现作者披露的 442 个 hard-negative occurrences
跨 305 个 records，以及 metadata filter 导致 33 个 records 丢失至少一个 gold、2 个丢失全部 gold。
这些是 post-hoc v2 identity reproductions，不是第二项前瞻冻结应用，也不是 FinRank 缺陷发现。

**已验证的边界。** in-record MRR/nDCG 和 pair metrics 在当前环境中精确复现；
global metrics 最多漂移 0.19 点，metadata-filtered metrics 最多漂移 0.16 点；
第二环境的部分全局值最多漂移 0.47 点。没有 original score matrices 或完整执行环境，
漂移原因无法唯一归因于 tie order 或 dependency drift。

### 1.3 局限

Case 1 是单 corpus 上的合成 perturbation，119 个 source-table UIDs 不估计自然缺陷分布。
harmfulness 受 equivalence contract 控制，语义边界分析只有一个 judge。
阶段分离依赖明确的 contract-derived instrument。FinRank v2 在看到 v1 身份错误后修改代码，
因此不能作为完全冻结的独立确认。当前证据也未覆盖 neural/generative FinRank baselines。

### 1.4 下一缺失证据

**未验证。** 在任何“普适测量审计方法”或“跨来源迁移规律”成章之前，需要一个真正
前瞻冻结、因果对齐、第二数据流的独立应用；同时需要独立 human semantic/harmfulness
标签、自然缺陷分母和可获得原始 score matrices 的锁定复现环境。

## 2. C2：反馈学习的证据边界

### 2.1 方法

C2 比较固定 ordinary checkpoint 上的一次性修订表示。主线使用 24 个 families、每个
3 个自然输出变体，共 72 条冻结 ordinary outputs。可见反馈条件包括 deterministic
rerun control、neutral revision、localization feedback 和 execution feedback。
目标是检验可见诊断能否把错误输出修成正确输出，同时保留原始正确输出。

O/R/E 的概念定义仍为：O 为 frozen ordinary model，N 为同模型一次 neutral retry，
R 为从 ordinary checkpoint 训练的 full-program revision，E 为同一 checkpoint 上训练的
restricted local-edit revision。该前置观察阶段没有训练 E；后续 Phase B 在资格收窄后，
使用 reference-derived visible set-binding revision supervision 完成了真实 R/E 训练，
但仍不构成 feedback-derived learning 或 source-isolated confirmation。

### 2.2 结果

**开发观察。** 72 条输出中，neutral retry 得到 56 条 numeric correct，且
wrong-to-correct 与 correct-to-wrong 均为 0。Localization feedback 也为 49 条 numeric
correct，但产生 0 次 wrong-to-correct 和 7 次 correct-to-wrong；execution feedback 只有
40 条 numeric correct，产生 0 次 wrong-to-correct 和 16 次 correct-to-wrong。
在当前 checkpoint、decoder、prompt family 和 development panel 上，
可见 feedback revision 没有超过 neutral retry。

**开发观察。** Post-hoc expected-program mapping 在 72 条中产生 3 条 false-alarm feedback
和 12 条 insufficient diagnosis。该映射可能把 algebraically equivalent programs 标错，
因此它是 development diagnostic，不是训练监督 gold。

**开发观察。** Oracle localization diagnostic 使用隐藏的 initial-correctness 与
post-hoc discrepancy-class features，仅有 3 次 wrong-to-correct，同时发生 54 次
correct-to-wrong，completion/interface 稳定性也很低。它不能作为可部署反馈机制，
也不能用隐藏状态训练 E。

**开发观察，而非独立确认。** 后续 24-family replay 与 V4/V5 natural-error pool 的
task-ID 交集为 24/24，且其中四条已是 ordinary-model errors 并参与过 error-targeted
training selection。该面板必须标记为 `PRIOR_ERROR_POOL_DEVELOPMENT_REPLAY`；
其中出现的 neutral-retry corrections 不能证明 cross-source generalization。

**前置停止判断。** 当时的 one-shot localization/execution representations 不支持继续训练 E。
该结果是 bounded negative，不等于“反馈学习整体无效”。现有结果与“localization 不充分”
和“模型不能稳定执行任何一次文本修订”均一致，但没有把两者因果分离。

### 2.2.1 Phase B：child-only 训练、集合代理指标与接口修复

**监督与训练。** B1 从 24 个 families、72 条冻结 outputs 中收窄出 5 条可训练
set-binding 纠正轨迹，覆盖 3 个 families 和两种可见行/期间角色误绑定。监督身份是
`REFERENCE_DERIVED_VISIBLE_SET_BINDING_REVISION_SUPERVISION`。算子、减法方向和单位
不是训练目标；3/5 个合格目标相对冻结参考发生符号反向，因此唯一 estimand 是保持 O
的算子、顺序和单位时的 `SET_BINDING_SET_ACCURACY`，不是答案正确性。开发面板为
12 families ×3 repeated-measure variants，其中 7/12 个 family 的 original variant
原本正确。R/E 各训练 128 steps，合计 319,948 processed-text training tokens、
287.98 GPU 秒。但训练路径加载 ordinary parent 后立即新增并激活 `b2_child`；PEFT
一次只激活一个 adapter，因此该实验不是已验证的 ordinary-parent continuation。
36 条唯一轨迹被扩成每臂 256 行：39 条纠正呈现、217 条 no-op/未决。39 条呈现由
5 个纠正身份以 `11/7/7/7/7` 的不对称权重重复得到，不是 39 个独立纠正；loss 覆盖
全部 prompt+target tokens。这些是训练失败的候选解释，不是已识别根因。

**接口修复后的结果。** 第一轮 192-token 生成使 R/E 各 24/36 条进入 syntax-adapter
failure，判为 interface-truncation run。使用同一 R/E checkpoint、同一面板重新生成
R/E 72 条，将上限提高到 384 并要求只输出合同对象，新增 66,592 generation tokens，
未重训。按 source-family 配对的行级 `SET_BINDING_SET_ACCURACY` 为 N=72.2%、
R=69.4%、E=0%；E-R 为
-69.4 个百分点，区间 [-91.7,-44.4]，E-N 为 -72.2 个百分点，区间 [-94.4,-47.2]，
R-N 为 -2.8 个百分点，区间 [-19.4,+13.9]。三变体全对只作 paired-completion 次要诊断。

**失败分布与判断。** 这些 correct 数只表示证据集合匹配，不是答案语义正确数。N 为
26 set-binding match、6 wrong、4 reasonable UNKNOWN；R 为 25 match、7 wrong、
4 reasonable UNKNOWN；O 为 27 match、5 wrong、4 reasonable UNKNOWN。
E 的接口口径为 36 个 interface-caused UNKNOWN、0 个合法 patch；按目标可得性口径，
4 条无目标样本是合理 UNKNOWN，其余 32 条为 WRONG/LOST，即 `CORRECT 0 / UNKNOWN 4 /
WRONG 32`。E 还造成 5 个 originally-correct family damage。72 条修复生成仍全部达到
384-token 上限。O/N 为 strict whole JSON；R/E 为 36/36 embedded JSON，strict 为 0。
E 先败在 keys/schema，随后出现虚构 JSON Schema、错误 hash 字段和非法 operation keys。
SHA 要求属于模型/工具责任混杂，不能单独解释 0 个合法 patch。
reference-derived deterministic patch control 为 88.9%，但它是不可部署的 oracle control。
R 虽能抽取首个对象，但没有严格可交付输出；R-N 配置不匹配且区间跨零，只能记为
`NO_GAIN_OBSERVED_IN_THIS_CONFIGURATION`，不是干净的方法级因果负结果。证据支持停止
当前 R/E 实现，不支持推广为反馈学习或局部编辑普遍无效。

### 2.3 局限

当前 feedback 是 development 诊断，不是 deployment feedback event；B1/B2 标签是
reference-derived set-binding revision supervision，不是教师反馈学习产物。
面板不是 source-isolated confirmation；numeric correctness 也不等同于任务级有用性、
单位/期间正确性或行动安全。B1 旧门使用 24-family semantic correctness，B2 实际替换为
12-family `SET_BINDING_SET_ACCURACY` 且新增 zero-damage ceiling；两者不是同一分母或同一
目标。Neutral correction 与 oracle correction 的存在说明“没有纠错能力”同样不是可支持
结论。E 的失败还混合 patch schema、hash 约束、重复输出和 max-token 截断；hash 应由
工具计算，不能要求模型凭空生成。R/E 72 条修复生成均未自然终止。N 又是首轮
sampling/192-token 配置，R/E 是 greedy/384-token/
contract-suffix 配置，R-N 的小幅差异混有配置差异；累计物理生成调用为 188。方向门在该
面板上结构性不可满足：2/3 个 eligible families 由 set-difference 方向规则产生符号反向，
不能再计作 E 的额外失败。已安装 TRL 含自动 EOS 处理，因此不能把 runner 未手写 EOS
认定为训练失败根因。

### 2.4 下一缺失证据

当前 R/E 候选已满足停止规则，不应进入 exposure-clean confirmation 或第二 seed，也不应
继续在同一面板上调提示或堆样本。若未来重启，必须先验证有效父计算路径，允许训练参考
使用合法完整目标，由工具计算 hash/完整性字段，并形成新的来源隔离、经 verifier 核验的
自然纠正监督；确认集须在生成前通过历史曝光并集检查。在此之前，C2 保留为实现失败和
方法边界材料，资源转向与 C3 有区分的新问题。

**决策残差资格筛查。** 后续对“条件化证据适用性”和“可核验的证据获取”做了有界筛查。
角色/期间适用性被可见角色规则解释；TAT-QA 389 个自然 text-only 开发问题中，TF-IDF
top-3 覆盖 378，top-5 和 top-3+top-1 邻域均覆盖 385，top-10 覆盖 389/389。但 top-10
在 359/389 题上已经等同 always-expand，top-5 在 262/389 题上也已等同 always-expand；
该筛查只测证据覆盖，不测成本感知策略优势。固定 top-k、邻域扩展或 always-expand 已解释
主要证据获取余量，因此没有释放模型探针。该结果只说明
当前两个候选缺少独立残差，不证明条件判断或证据获取问题不存在；下一步需要未曝光自然
来源、完整语义参考和能同时越过这些强基线的可执行残差。

**补充资格复核。** 2026-10-26 的自然原题复核进一步把 P1 的 5 个 frozen
incorrect 候选拆成 4 个真实模型语义错误和 1 个 reference/scoring defect。一个
可见、无 gold、固定顺序的 axis/scope policy 对 4 个真实错误全部修复，残差为 0；
因此该证据使用候选停止且不可复活。P2 改用 507 个 TAT-QA `table-text` 原题后，
506 个有完整语义参考，1 个 hidden-percent 项预先标为 `NOT_MODEL_READY`。来源需求为
table 197、paragraph 44、both 265、unresolved 1；offline semantic-potential
为 table-only 197、top-3 452、top-1-neighbor 414、top-5 486、transparent
stop/expand 481、always-expand 506。成本最优的 top-3 约为 always-expand 上下文
66.8%，但与上限差 10.65 个百分点，远超预注册 2.0 个百分点容差；top-5 更接近但
超过 75%/50% 成本门。最终 `qualified_challenger=null`，模型小探针不释放。
这里的主筛查量是 offline `semantic_reference_potential`，未来模型实验才使用
`full_semantic_answer_accuracy`；字符数只是上下文体积代理。

## 3. C3：固定模型交付的风险—覆盖—成本边界

### 3.1 方法

C3 不训练新模型。它在固定 Qwen3-4B + ordinary SFT adapter、greedy decoding、
`max_new_tokens=256` 上，对复用的 24-family × 3-variant development replay 比较交付策略：

1. always accept original；
2. always accept neutral retry；
3. always accept localization revision；
4. semantic gate original；
5. bounded repair，即 original 有效时保留，否则使用 verified revision。

评价同时报告 correct delivery、wrong delivery、abstention、delivery coverage、
conditional wrong rate、tokens 和 observed local wall time。

### 3.2 结果

**开发观察。** Always-accept original 在 72 条中交付 60 条正确、12 条错误，
coverage 为 100%，conditional wrong rate 为 16.7%。Always-accept neutral retry 交付
62 条正确、10 条错误，coverage 为 100%，conditional wrong rate 为 13.9%；
它是当前复用 development panel 上最强的简单基线。

**开发观察。** Semantic gate original 只交付 38/72 条，其中 32 条正确、6 条错误、
34 条 abstain；delivery coverage 为 52.8%，conditional wrong rate 为 15.8%。
Bounded repair 交付 39/72 条，其中 33 条正确、6 条错误、33 条 abstain；
delivery coverage 为 54.2%，conditional wrong rate 为 15.4%。两种策略把 accepted-wrong
从 10–12 降到 6，主要通过丢弃 33–34 个任务实现，并没有提高 correct delivery，
也没有在风险—覆盖曲线上显示超越 neutral retry 的已验证优势。

**开发观察。** Always-accept localization revision 为 59 条正确、13 条错误、100%
coverage，correct coverage 81.9%，低于 original 的 83.3% 和 retry 的 86.1%；
它不能作为当前交付策略候选。

**开发观察的成本边界。** 在该本地单次运行中，original 条件为 38,445 prompt +
3,552 completion = 41,997 tokens，observed wall time 51.99 秒；neutral retry 为
52,223 tokens、94.42 秒；localization revision 为 64,326 tokens、173.91 秒。
三条件合计 216 attempts、158,546 tokens。墙钟时间只反映一次本地执行，
不证明稳定吞吐；各 policy 的边际部署成本也没有从预计算三条件中单独识别。

### 3.3 局限与贡献边界

C3 的面板是旧 V4/V5 error pool 的 development replay，不是新的自然来源确认。
它只覆盖一个固定 checkpoint、decoder、prompt 和 72 个变体。当前证据说明
transparent gate 的主要作用是 abstention 换低 accepted-wrong，而不是已建立的风险降低或行动效用。
**C3 不是已建立创新，也不应与 C2 使用同一 repair mechanism 重复计为两个贡献。**

### 3.4 下一缺失证据

**未验证。** 在把 C3 写成第三个贡献之前，需要一个真正 disjoint、新 family 的冻结面板，
在预注册阈值下同时比较 always-accept、neutral retry、确定性可见 checker 和有限行动策略；
必须报告 matched risk-coverage、边际 token/GPU/tool/wall cost、wrong-to-correct、
correct-to-wrong、abstention 和行动效用。若风险下降只来自 abstention，或 C3 与 C2
共享同一修复机制，则合并或停止 C3。

## 4. 面向 2027 年 10 月评审的时间线

| 目标窗口 | 必须完成的证据动作 | 不可提前声称 |
|---|---|---|
| 2026-10-29 前 | Owner 决定 Paper E ICAART/SNCS 条件路线；不因截止临近提高科学主张 | ICAART 已获 Owner 批准或更易接收 |
| 2026-11 | 关闭当前 R/E 候选并保留真实训练后的实现失败与前提纠偏；冻结 C3 资格、停止和证据身份规则 | C2/C3 已建立、已泛化 |
| 2026-12—2027-02 | 为第三研究点选择有区分的新问题；若重启经验学习，先取得新来源、稳定合同和 verifier 核验监督 | feedback learning 有效 |
| 2027-03—2027-06 | 对新候选做小规模开发与真正来源隔离确认；不再在同一 C2 面板复验 | E 优于 R 或 neutral retry |
| 2027-04—2027-07 | 在真正 disjoint panel 上完成 C3 cost-aware risk/coverage；独立审计机制、单位和成本 | gate 或 abstention 是新交付方法 |
| 2027-07—2027-09 | 将已接受证据写入论文；完成 claim/evidence、引用、限制和下一缺口复核 | 超出分母/模型/契约的总体结论 |
| 2027-10 | 形成评审包并按 Owner 提供的确切日期执行评审准备 | 具体答辩日为 10 月 31 日 |

## 5. 本轮后的下一门槛

**最近科学门槛：** 当前 C2 R/E 实现已停止；C3 必须与 C2 去重并建立真实决策残差。
第三研究点应在不重复 patch/checker 的前提下形成独立问题，否则合并贡献点而不是拆章凑数。

**最近外部门槛：** Paper E 的 Owner 路线、身份、学校认定、旅行/报告和投稿授权。

## 6. 证据路径

- `docs/governance/audit/loop_d_control_review/PHASE_A_RETURN.md`
- `paper/saner_rene_manuscript_v1.md`
- `research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/G1_ICAART_PACKAGE_AUDIT_20261025.json`
- `research/feedback_delivery_continuation_20261025_v1/FINAL_STAGE_INDEPENDENT_REVIEW.md`
- `research/feedback_delivery_continuation_20261025_v1/SAME_CANDIDATE_FEEDBACK_A_FINAL.json`
- `research/feedback_delivery_continuation_20261025_v1/DELIVERY_CONFIRMATION_C_V1.json`
- `research/feedback_delivery_continuation_20261025_v1/RESOURCE_RECEIPT_20261025.json`


## 7. 自然筛查事后复核：代理与语义结论的界限（2026-10-26）

本阶段507条表文问题的逐行计数与哈希可复现，但这种一致性不等于构念有效性。来源分类以参考答案或推导数字在表格/段落中的字面包含为依据；本次在原实现上构造并复现了两种误判：数字子串命中，以及相同数值属于不同语义角色。因此，197/44/265/1是启发式来源分类，506是自动参考状态，不能直接解释为完整语义充分性或模型正确率上界。两条反例仅为审计fixture；五条自然数值边界敏感性标记尚待语义裁决。

对于原题错误，四条真实错误可以得到可见规则解释，但现有交付未定位统一可执行规则actor及全部24题的非破坏回归，不能由错误子集的4/4推出一般证据使用问题已关闭。后续应保持旧R/E实现停止，以同一actor、完整可复核参考和真实调用成本校准检索代理，再决定是否值得投入新方法。原离线门下暂停仍保留其历史身份，尚未执行的模型实验不作为方法负结果。证据见docs/governance/audit/loop_d_control_review/NATURAL_COST_POST_RETURN_REVIEW.md及同目录机器收据。


## 8. Publication 与代理校准补充（2026-10-26）

P1 的统一可见规则 actor 仍只读取问题与完整可见表格，历史 24 个 ordinary
original 未被重跑或改写。应将三种身份分开：23/24 是冻结数值程序正确，13/24
是数值、可观察单位和方向合同同时满足的完整语义正确，14/24 是可观察单位一致；
其余 10 个单位 `UNKNOWN` 是规则允许的单位不确定，不是数值失败。第 07 项保留
later-minus-earlier 的 -1955 与参考方向的 +1955 两种可接受读法，结论为
`UNRESOLVED`。这组证据是同一可见规则在 frozen 24-item 面板上的身份修正，
不是新来源泛化。

P2 在生成前完成了 hash-bound runner→visible-context adapter→model actor→strict
parser→scorer-input 的零输出 dry run 和正式 preflight，状态为
`END_TO_END_PREFLIGHT_PASS`；actor payload 对 12×3 项均未包含 gold、UID、隐藏
尺度或参考链。首次 40-call 过程在生成后因已被严格解析器接受的
`TABLE:<column>` 在语义规范化中缺少 row/column 分隔而停止，失败过程和 40 条
完整响应已原样保留；修复后仅复用既有响应完成计分，没有新增生成调用。该停止
链是工程接口缺陷证据，不是代理是否具有信息价值的科学结果。

真实三臂开发面板固定使用本地 Qwen3-4B。table+top-3 为 ACCEPT/REJECT
2/10，交付错误风险 0.833，输入/输出 token 8,863/778，平均可见字符 1,710，
生成墙钟 46.91s；table+top-5 为 3/9，风险 0.750，token 9,780/778，
平均可见字符 2,040，墙钟 46.45s；table+all 为 3/9，风险 0.750，
token 11,384/786，平均可见字符 2,630，墙钟 47.69s。合计 40 次调用
（36 primary + 4 bounded retries）、2,609 output token、33,207 input
token 和 157.01s；只有 1 个配对项从 top-3 的 REJECT 变为 top-5/all 的
ACCEPT，语义 `PENDING_ADJUDICATION` 为 0。旧 507-item heuristic proxy
计数、潜在覆盖和可见字符仍与这些真实 token/调用账目分开。该 12-item
面板只显示更宽上下文提高了 1 个 ACCEPT 同时增加了输入成本，不能支持
2-point noninferiority、generalization 或上下文臂的上/下界。

Paper E 现为保留原两案例边界的完整 journal-derived manuscript：结构化摘要
195 词，正文覆盖 Introduction、Related Work、Method/Measurement Contract、
Experimental Setup、Results、Discussion/Limitations、Data Availability 和
Declarations，并以 24 条真实条目和全部 in-text citation 接通 bibliography。
96/118 保留 checkpoint-level 限定，FinRank 保留 post-hoc/clustered
`text_sha1` 身份及未解释的 global/metadata reproduction drift。交付 PDF 为
15 页、6,879 个抽取文本 token 的本地 PyMuPDF full-content fallback，不是
TeX-engine compilation；Canonical LaTeX 仍待 D 的 approved document tool
编译。该稿件未被声明为 accepted、published 或 school-recognized，作者、
资助、专利、artifact release 和 submission 字段仍为 `TBD_OWNER`。
