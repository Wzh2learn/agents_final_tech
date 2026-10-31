# Agent 研究方向前瞻与论文候选（2026-10-29）

状态：文献初筛及开发性模型、真实工具 Agent 探针；不是系统综述、已确认创新或独立确认。目标是为学术硕士寻找可验证方法和可发表论文，金融文档不是限制，现有工程系统主要提供执行与评测基础设施。外部论文是否已正式接收只按对应来源说明，arXiv 论文按预印本处理；不能宣称未核查的研究空白。

2026-10-31：[PDF/Excel 跨任务探索](PDF_EXCEL_TRANSFER_RETURN_20261031.md)完成三条真实工具 Agent 和事后简单对照。带经验组原检查 11/11，无经验组 7/11；无经验组已有正确的 15/15 删除与 20/20 修改，展平其嵌套输出后也为 11/11，且与带经验组结果相同。无模型的公开输入确定性基线也通过。该单实例支持分离事实与输出合同，不证明经验学习有因果收益；下一步仍是不同来源、多任务族的经验适用与反馈更新。

同日新增 [SkillLearnBench 来源与反馈合同发现](FINANCIAL_FEEDBACK_CONTRACT_FINDING_20261031.md)：六个公开金融任务的 solution 存在相邻股票类别字符串拼接；在两个已暴露任务上，代码运行时计数与参考一致，而分开字符串的反事实会被原 pytest 拒绝。后者不是独立财务 gold，也没有进行 Agent 学习实验。它提供了“可执行任务规则与评价反馈冲突时如何学习”的候选场景，需同简易规则和普通历史比较。

2026-10-30 补充：[跨任务经验迁移与元件匹配尸检](CROSS_TASK_TRANSFER_RETURN_20261030.md)已运行三个真实制造任务 Agent 和四个无模型代码控制。观察到标识符切分、大小写及类别语义共同影响结果；原任务检查和单次轨迹不足以确认迁移收益。当前可复用的是带成本的轨迹与任务设计约束，不是已成立的方法。

后续工作、训练可选条件、强基线和 IJCNN 倒排见 [实验执行路线](IJCNN_EXPERIMENT_PROGRAM_20261030.md)。

2026-10-30 新增 [IJCNN 近邻核查与下一实验候选](IJCNN_RELATED_WORK_REFRESH_20261030.md)，包括 Skill-V、SkillShift-Bench、SkillEvolBench、RSE-Bench、CFOE 和 SEAL 等：技能合同、环境适配、反馈噪声、非回归及从失败迁移均已有直接先例，须进一步全文比较和复现相应强基线。

## 2026-10-30：真实工具 Agent 的技能与执行预算探针

**后续接续**：[真实 dialogue-parser 反馈与验证器研究](DIALOGUE_PILOT_RETURN_20261030.md)在新的任务上运行了 8 次 Agent episode。发现一次同起点修复中的真实文件权限阻断，并修复后重新执行；也发现原 verifier 可对缺少解析器的构造控制给出 35/35，以及对可达的 End 终点产生误拒。具体反馈与 neutral 两组在单案例中均通过新增解析烟测，原测试分别为 34/35 与 29/35，其中部分测试对图结构表示有争议。记录为候选问题和测量约束，不将它包装成反馈方法已成立。

**第二任务接续**：[prefix-cache 反馈修复](PREFIX_FEEDBACK_RETURN_20261030.md)中，现成任务技能在同起点上通过 10/10 且在上游参考下 2,000 行一致；中性重试及可见合同诊断未达到该基线，诊断扩容后为 5/10。技能包含完整策略知识，不与短反馈视为信息等量；重复执行与 2,000 行复核均已实际运行。下一轮应研究新任务族上的知识/反馈选择与可靠迁移，而不把同任务手工 skill 的有效性当作新方法。

在 SkillsBench 开发任务 `tictoc-unnecessary-abort-detection` 上，将 OpenCode 与 GB10 本地 Qwen 组成可执行工具 Agent；相同任务分别提供 no-skill 和全部三份任务 skill。Docker 无网络、任务 verifier 不在 Agent 容器中；运行结束后在隔离环境执行原验证器。这里只是一个公开任务的开发探索，没有独立任务族、重复试验、source-isolated 测试，也没有经验学习或反馈更新。

首次各运行一次时本地模型传输超时，两个条件都未交付；[no-skill 原回执](tictoc_timeout_no_skill_receipt_20261030.json)和 [all-skill 原回执](tictoc_timeout_all_skill_receipt_20261030.json)分别有 4 和 2 个物理 POST。第二轮仅将服务及回合超时上限从 120/300 秒调整到 300/600 秒，其余请求上限等保持，使用 [可复现适配脚本](run_tictoc_extended.py)，不是重写第一轮。

| 第二轮条件 | Agent | 独立输出验证 | 模型物理 POST | 墙时 |
|---|---|---|---:|---:|
| [no-skill](tictoc_extended_no_skill_receipt_20261030.json) | 退出码 0，生成文件 | 3 项格式测试通过；任务语义评分 **0.05/1** | 5 | 125.3 秒 |
| [all-skill](tictoc_extended_all_skill_receipt_20261030.json) | 触及 8 POST 上限，退出码 1，无输出文件 | 3 项格式测试失败；无可评价语义答案 | 8 | 227.2 秒 |

第二轮的已完成步骤分别报告 37,407 和 87,495 tokens（包含各自报告的缓存输入，不可重复相加）；原始实验日志保存在 GB10 `/home/testuser/wzh/research_evidence/agent_learning_20261030/agent_tictoc_extended/`，首次实验日志保存在 `/home/testuser/wzh/research_evidence/agent_skill_method_20261029/`。首次超时请求的未返回 usage 为 UNKNOWN；本地 Qwen 直接模型反馈探针另有 9 次、8,818 reported tokens，不与此混为同一种调用。没有训练、付费 API 或生产 Memory 写回。

**可行动研究假设**：当经验或技能增加 Agent 上下文与推理步骤时，额外信息的潜在收益可能被执行预算、输出长度或错误反馈抵消。这个单任务结果不能区分技能内容、提示长度、工具使用与上限等因素；不能说 skill 导致性能下降。后续应在多个可执行任务上比较 no-skill、完整 skill、等长度无效文本、简短摘录和基于可见反馈的选择或修订，匹配输入及总预算并报告任务成功、合法输出、调用数、缓存、墙时；同时引入普通重试与随机选择。先做开发和运行合同校验，再使用未见来源/任务族开展独立确认，复查 SkillLearnBench、SkillsBench 及近邻文献是否已覆盖候选机制。

## 2026-10-30：IJCNN 目标及首次连续反馈开发运行

**目标**：第二篇独立研究以 [IJCNN 2027](https://ijcnn.org/2027/) 为目标，regular 截止 2027-01-31，通知 03-15，会议 06-14–18；首篇与第二篇须有独立问题、数据和贡献。IJCNN 主题涵盖基础模型、参数高效适配、持续学习、Agentic AI；一般免费篇幅 6 页，费用及超过 6 页的条件按当时 [官方作者须知](https://ijcnn.org/2027/authors/initial-author-instructions)核验。该方向仍为研究假设，不伪装为已成立方法。

**倒排**：2026-11-06 前打通真实任务可见反馈、输出合同和强基线；11 月中下旬对已筛选家族运行重复开发，对照模型历史、简单 ICL、检索、skill 和工具反馈；12 月上旬确定方法或转向另一候选，完成公开近邻复现与消融；12 月下旬至 2027 年 1 月进行来源隔离确认、多个种子和成本核算；1 月中旬写完整 6 页稿、审阅与修订，1 月 31 日前确定是否具备可投稿证据。时间点是工作目标，任务数据与硬件决定实际规模，不以进度代替科研结果。

**已执行最小探针**：[脚本](run_sequential_feedback_pilot.py)、[摘要](sequential_feedback_pilot_summary_20261030.json)、[逐次账本](sequential_feedback_pilot_ledger_20261030.json)。固定 ContinualSkillBench finance stream 中 FinQA 题 5/25/26；GB10 本地 Qwen3.6-35B-A3B-Q4_K_M，独立与历史+前序正确/错误反馈两臂，每臂 3 次，temperature 0，输出 cap 1024，无 retry。该探针为**直接单轮模型接口、不是工具 Agent 或官方 benchmark 运行**，任务与旧来源曝光，模型预训练曝光未知。每次独立 JSON 合同合规；按上游 numeric helper 计分两臂均为 `[1,0,0]`。第一题两臂输入本来相同；不能把 1/3 作为反馈方法有效或无效。

**发生判断变化的观察**：两条错判涉及百分数合同。题 25 问百分比，独立臂输出 `65.6%`，参考为比例 `0.65644`；题 26 独立臂输出 `5.62%`，参考为 `0.05624`。上游 helper 删除 `%` 而不将百分数换成比例，且容差不考虑显示舍入。将显式百分数解释为比例后，它们接近参考，但具体正确性需按题目和精度合同独立核验；历史臂输出无 `%` 的 `65.6` 与 `5.6`，不得自动断定单位。第二题的上游 `incorrect` 反馈被第三题历史臂看到，因此这是可能存在的反馈污染，不能用它评估可信纠正学习。保持 raw 与原判分不变，新评分另版本并先做正负例。

**事后确定性诊断**：[数值格式诊断器](numeric_semantic_diagnostic.py)按明确百分号、比例、十进制末位舍入区间和符号做有界分析，单位不明确保留 unresolved；本地与 GB10 的三组正反例测试均通过。[固定 raw 重评](sequential_feedback_posthoc_diagnostic_20261030.json)中独立臂 3 项都与该舍入约定相容，历史臂 1 项相容、2 项为缺少百分号的 unresolved。它是为理解旧输出的事后诊断，依赖选定的四舍五入与单位假设，并非事前冻结 gold 或独立人工裁决，不能作为方法胜负。

**反馈标签反事实探针**：对先前历史臂题 25 的固定回答，维持同一前题、回答和目标题 26，仅将合成反馈设为 `incorrect` / `uncertain` / `correct`，[脚本](run_feedback_label_probe.py)在 GB10 分别执行 1 次，结果为 `5.69` / `5.7` / `5.7`（均无明确百分号）；[账本](feedback_label_pilot_ledger_20261030.json)共 3 次、4,010 reported tokens、0 retry。该探针由前轮观察后提出，不是独立确认；其输入不包含第一题历史，与前轮历史臂不是相同上下文。它说明此固定输入下反馈标签可以伴随输出变化，但单个确定性任务不能判断反馈机制的泛化、行动收益或答案准确性。实验没有训练或 tool-agent 调用，raw 和请求保存在 `/home/testuser/wzh/research_evidence/agent_learning_20261030/feedback_label_development_20261030_v1/`。

**成本与来源**：实际 6 次 HTTP、0 retry、0 judge、0 训练、0 付费 API；返回 usage 总计 4,808 tokens（含已报告缓存输入，不重复相加）；full request/response 在 `/home/testuser/wzh/research_evidence/agent_learning_20261030/sequential_feedback_development_20261030_v1/`。本研究使用公开 benchmark 题目的请求和结果，不写生产 Memory。下一步先制定百分数、单位和舍入的冻结参考并重评固定 raw，随后使用可执行工具任务和 source-disjoint 面板开展真实 agent 对照；实验条件由实况迭代，不把本次错误归因于模型或完整基准。

## 2026-10-30：连续技能学习公开基准资格探索

**实际动作**：在 GB10 `/home/testuser/wzh/research_evidence/agent_learning_20261030/` 获取 [SkillLearnBench](https://github.com/cxcscmu/SkillLearnBench) commit `726e1f79b96b0cb3d729d0e55a1c847e0b5353ae`（仓库声明 MIT，约 2.2 GB）与 [ContinualSkillBench](https://github.com/gtynnn060110-hash/continual-skill-bench-final) commit `91c76f887c2a422d1f8d4c1adacc944c9c2ad6c1`（仓库声明 Apache-2.0，约 4.7 GB）；两者各自依赖的原始数据许可仍需分别确认。未安装依赖、运行上游脚本或接触生产服务。源码和数据在 GB10，未纳入项目 Git。

运行 [只读资格脚本](inspect_continual_skillbench.py)；GB10 的 [聚合回执](continual_skillbench_qualification_20261030.json) 记录 6 个仓库 task streams 各 100 条以及来源和评价方式，6 个 stream 不等同论文报告的 5 个主域，也不说明已经运行 600 条。金融 stream 有 51 条 rubric judge、13 条程序检查、13 条 F1、12 条数值、11 条精确匹配，来源含 10 条 TAT-QA 和 11 条 FinQA，与本项目已有研究来源重叠；是否具体题目或模型训练曝光仍需核验，不能作为无污染外部确认。Office 有 35 条 rubric judge，math 有 25 条；即使筛除 judge，也须检查基础题、数据和检查器是否可独立运行。项目说明预装任务技能，且环境注释说明 `tasks_spec.json` 留在 host；实际 agent 镜像和工具权限须逐项验收，不将静态阅读视为真实泄漏测试。

**合成反例**：直接调用金融 stream 的 `tests/qa_eval.py` 辅助函数，`numeric` 将 `12%` 和 `$12` 评分为 1，`f1` 将 `-5` 与 `5` 评分为 1；`numeric` 对 `-5` vs `5` 为 0，正确同值控制为 1。它揭示辅助函数在这些构造输入下忽略单位或标点的行为，**未证明原始题目出现该反例，也未证明官方 agent 实际运行链一定使用该函数**。文件存在类 pytest 检查不等价语义验证；官方 test.sh 依赖运行时 feedback 聚合，后续须追踪每种调用链并验证端到端合同，不能把静态发现扩大为官方成绩无效。

**可操作判断**：SkillLearnBench 明确提供 20 任务、100 实例、human/no-skill/one-shot/self/teacher 经验基线，环境依赖 Docker 和原作者特定 agent；ContinualSkillBench 的 sequential/pure ICL/independent 直接对应我们的核心竞争基线。已查的 `organize-messy-files-1` Dockerfile 构建时下载 100 份 PDF，金融任务 Dockerfile 需要 Ubuntu 安装依赖；本机镜像未命中对应基础镜像。不能把它们描述为已经可离线复现。优先选择 2 类无凭据、数据可离线核验、来源族可隔离的开发任务，复核 `skills` 与验证器挂载，做正负输出控制，再适配本地 OpenCode/Qwen；保留合成变化与自然任务的区别。当前仍未做真实 sequential agent run，不能声称新方法收益或新颖性。

**资源**：本次科研模型生成、judge、训练及付费 API 均为 0；源码克隆、GPU 状态查询和 CPU 只读检查已完成，不影响既有实验账本或生产环境。

## 2026-10-29 第二篇：用户认可的两条主线与首个比较

**问题池，不是已证明的新方法**：① Agent 怎样把执行反馈转化为之后可迁移的经验；② 任务或环境变化后，怎样判断记忆/skill 的适用性并更新。两者可以在同一连续任务链中联系：先做任务、获得可见反馈、再遇到变化任务，但不能把“把经验写成 skill”或“旧记忆失效”本身当新颖性。旧实验停止针对特定实现，不否定整个领域。

**论文对照（本次仅核对论文摘要/主页，非全文查新）**：[SkillLearnBench](https://arxiv.org/abs/2604.20087) 已研究多种持续 skill 学习；[ContinualSkillBench](https://arxiv.org/abs/2608.03874) 的 v3 摘要称，在两模型三域的比较中，保留上下文与反馈不维护显式 skill 的平均效果接近显式 skill，且部分程序性任务仍受益；[Mem2ActBench](https://aclanthology.org/2026.acl-long.370/) 评估记忆驱动工具选择与参数；[STALE/CUPMem](https://arxiv.org/abs/2605.06527) 已研究旧状态失效和传播；[AMA-Bench](https://proceedings.mlr.press/v306/zhao26bs.html) 涵盖真实/合成 Agent 轨迹并提出因果图记忆检索。**可检验的切入假设**：结合来源条件和可观察反馈，有可能在任务变化时减少错误经验复用而保留成功率；这不是已确认文献空白，需逐篇全文核查已有机制、基线和环境，再选可区分的具体变量。

**可复用素材与适用范围**：

| 素材 | 已获得什么 | 不得直接推论 |
|---|---|---|
| [历史基线地图](../research_baseline_governance_20261023/RESEARCH_BASELINE_AND_REUSE_MAP.md) | FinRank 当前角色面板一次成功率饱和，历史经验无可识别空间；STALE 的事实/行动/未知分层可用 | 历史经验普遍无效；AI 评审是人工金标准 |
| [Phase B 事后修正](../decision_residual_pivot_20261026_v1/D_PREMISE_CORRECTION.md) | 真实 LoRA、输出/轨迹和 5 条参考构造的可用纠正；旧 adapter、指标、截断和 schema 问题已查明 | 这 5 条是自然反馈轨迹；旧 R/E 是有效普通父模型继续训练；其失败否定全部反馈学习 |
| [SFT 与模型资产](../feedback_learning_finance_20261023_v1/FIRST_METHOD_RETURN.md) | Qwen3-4B、PEFT/TRL、冻结生成及按表源隔离工具；可重用普通 SFT 控制 | 早期相关变化得分：须使用后续修正后的评分器和重叠审计；历史外部任务自动等同未暴露来源 |
| [SkillsBench 单任务比较](../agent_skill_method_20261029/DOCS_AVAILABLE_CONTROL_RETURN.md) | 真实工具 Agent、隔离容器、验证器、raw 工具轨迹；一次强制 skill 通过、可选文档未通过 | 单次即方法优势；提示信息、实际成本和超时完全匹配；适配执行等于官方评测 |
| [既有记忆/行动材料](../publication_thesis_goals_v1/revision_v5/RESEARCH_SPRINT_RETURN_V5.md) 与 [后续对账](../research_baseline_governance_20261023/RESEARCH_BASELINE_AND_REUSE_MAP.md) | 区分事实恢复、行动、合理 UNKNOWN 和额外拒绝；存在安全与覆盖取舍观察 | 原 judge 为独立人工 gold；旧状态卡分数证明通用记忆方法；错误的 G2 机制归因可以照搬 |
| [迁移任务资产](../publication_thesis_goals_v1/revision_v2/G2_V2_REPORT.md) | NtripBrowser、Partridge 实环境与行为/结构检查可供开发 | 旧任务未曝光；简单规则已覆盖的案例存在方法残差 |

**第一轮实际探索的建议合同**：选 2 个公开可执行的任务/环境来源，优先检查 ContinualSkillBench / SkillLearnBench 代码及许可证、Qwen 接口和验证器可复用性，不适配时寻找其他真实工具任务；来源/仓库/版本按族隔离，先小规模开发并保留未见家族。对同任务序列比较：无历史、原始轨迹/普通检索、同信息量简短文档或历史摘要、现有公开方法（可运行时）、候选带适用条件及反馈更新的经验。固定模型、任务和可见信息；分别记录更新前、更新后、变化后及不变控制，验证同族重复/预训练曝光与 oracle 泄漏。输出任务成功、旧经验误用、合理弃答/不必要弃答及全部推理、检索、验证成本，按独立任务族报告。开发阶段可使用人工或确定性规则构造探针，但必须与自然反馈分报；不把一次运行当确认。优先复跑接口与零/少量真实 episode，再决定是否实现新方法或训练。

**首轮判读**：如果简单历史或版本规则已达同样成功/风险/成本，仍可研究何种变化或任务需要更丰富的条件，不强推复杂方法；如果有稳定剩余差异，先排查信息量、任务难度和成本，再做未见来源确认。若近邻已有同机制，以全文对比后改题而非包装“首次”。Paper E 的投稿准备仍优先。

## 2026-10-29 负责人补充：长期研究不收窄为一次评价发现

近期第一优先级仍是 Paper E 的投稿。第二篇和学位后续方法点保持开放：上一轮“产物正确但 Agent 进程未正常完成”只是评价与诊断视角，不是第二篇唯一主题；下方历史建议“优先 A”不构成已冻结的选题。金融文档可用于验证，不限制任务领域；GB10、OpenCode/Qwen、既有数据与训练链是可复用基础设施，不预设问题必须从旧资产中产生。

| 方向 | 候选科学问题 | 可用基础与先比较的简单方案 |
|---|---|---|
| 反馈、自学习及蒸馏 | Agent 如何把可核验的执行反馈转化为后续任务的可迁移改进？反馈的来源、粒度和错误成本何时重要？ | 复用既有 SFT/LoRA 和执行轨迹链；先比较普通 SFT、同起点/同数据继续训练、普通重试和无反馈条件。旧 R/E 的父 adapter 未按设想激活，不能据此否定整个方向。 |
| 经验、记忆和状态演进 | 历史经验在环境或状态变化后怎样保持适用并指导行动，而不把过期信息传给下游？ | 复用 STALE 分解、旧状态到行动评测合同；对比不使用记忆、普通检索、直接事实恢复和时间/版本规则。已有面板有天花板与信息损失，不自动代表记忆无效。 |
| Skill 和工具适配 | 工具接口或任务条件变化时，Agent 如何选取、更新或组合可复用技能？ | 复用 SkillsBench 与 OpenCode；对比无 skill、固定 skill、等信息文档、静态规则及普通重试。当前单任务只作开发信号，已有近邻需继续核查。 |
| Agent 规划与协作 | 在质量和总成本约束下，什么时候需要额外推理、验证或其他 Agent？ | 复用隔离任务、账本和验证器；对比单 Agent 同预算延长、固定策略、随机分配和确定性测试。实际性能与独立贡献待验证。 |
| 可靠工具执行与恢复 | 部分失败或环境变化下，Agent 怎样利用反馈恢复任务并控制错误和副作用？ | 优先隔离环境和可执行参考；对比普通重试、只读核验、幂等和合理弃答。是否形成独立方法问题取决于数据、近邻和自然残差。 |

这些是可组合或替换的方向池，不预先认定为论文创新或承诺同时展开。每个方向后续都应查近期原文、确定可运行任务与基线、做有信息量的开发实验，再决定候选方法和学位贡献；必要时可以小规模训练或引入新任务，不重开被判停止的同一旧实验。Agent 产物/进程/成本分层可以服务任意方向的评价，也可以不作为独立研究主题。

## 1. 已有研究的界限：什么不能直接算创新

| 研究 | 已有内容与要避免的重复 | 可供借鉴的配置 |
|---|---|---|
| [SkillsBench v1.1 / paper](https://arxiv.org/abs/2602.12670) | 在跨领域真实任务上比较无 skill、精选 skill 和自生成 skill，设置可执行验证；自动 skill 获益并不稳定。不能只提出“Agent 用 skill”。 | 固定任务＋skill 有无配对、独立 verifier、隔离执行环境。[v1.1 版本和开源说明](https://www.skillsbench.ai/blogs/skillsbench-1-1) |
| [SkillLearnBench (COLM 2026)](https://arxiv.org/abs/2604.20087) | 已研究 one-shot、自反馈、外部反馈和持续技能学习，并区分技能质量、轨迹和任务结果。不能只做“外部反馈生成 skill”。 | 同一源任务族拆开发/验证；分别评价技能、轨迹和下游结果。代码 [SkillLearnBench](https://github.com/cxcscmu/SkillLearnBench)，需逐项核对许可与资源。 |
| [General AgentBench (2026 preprint)](https://arxiv.org/abs/2602.18998) | 已比较顺序交互和并行采样两个 test-time scaling 轴，提出饱和与验证鸿沟。不能只画“多采样更好/更差”。 | 同任务、不同预算、单次与多轨迹；尤其在比较时包含最后选优成本。 |
| [MultiAgentBench (ACL 2025)](https://aclanthology.org/2025.acl-long.421/) 和 [Multi-Agent Reasoning cost scaling (2026 preprint)](https://arxiv.org/abs/2605.01566) | 已比较多 agent 拓扑/协作和相同计算预算下策略效率；“多智能体比单体好”不是新发现。 | 单 agent 同成本自一致性/自反思；团队计总输入、输出、工具调用和总时延。 |
| [Mem2ActBench (ACL 2026)](https://aclanthology.org/2026.acl-long.370/) 与 [STALE (2026 preprint)](https://arxiv.org/abs/2605.06527) | 已覆盖隐式记忆使用、工具参数、状态变更及动作的偏差。不能只做“历史信息用于动作”。 | 冻结可用事实与允许行动；报告错误行动、合理 UNKNOWN、覆盖率和来源。 |
| [UndoBench (2026 preprint)](https://arxiv.org/abs/2610.05622) 与 [RobustBench-TC / ToolRL-DR (2026 preprint)](https://arxiv.org/abs/2605.11928) | 前者已研究不同失败阶段、重复副作用和幂等/确认，后者已模拟工具输入/状态/调用干扰并研究 3B RL。不能只做“工具失败后重试”或“训练抗扰”。 | 配对同任务同种子、区分失败前/中/后、计算副作用；同时比较幂等、只读核实和简单重试。代码与数据的许可需逐条核查。 |

注意 SkillsBench 官网 v1.1 当前为 87 个任务、8 个域，论文历史版本数字不同；写作应固定确切版本，勿把版本差错当作科学发现。

## 2. 候选 A：环境变化下的 Agent skill 适用性与可靠迁移（优先资格验证）

**问题与待证机制**：已有工作评估 skill 是否帮助解任务，却不能据此断言：当某个 skill 在旧版本工具上有效、但工具语义或接口发生自然演进时，Agent 能否只凭运行时可见证据识别其适用边界，并修正或避免错误使用。候选机制是将每条 skill 绑定可检查的适用条件和验证结果，在不满足条件时采用透明 fallback 或有限修复；不是声称“条件化 skill”首次提出。须在获取真实变更和复现 SkillLearnBench/SkillsBench 基线后重新查新颖性。

**资格/数据**：先钉住 SkillsBench v1.1 task 与 code license，再从公开仓库正式 release / commit 中选择 API、CLI 或软件依赖的历史改变，离线对照原 skill 所需执行合同；每族分离仓库/版本、避免把版本变体当独立样本。受控变更仅为机制探针，和自然变更结果分报。项目已有 NtripBrowser/Partridge 迁移和 PyMigBench 样本只作可执行资格/开发，不作未见新样本；其当前强基线已能解释旧面板，不重开旧方法结论。

**至少四臂**：无 skill / 原 skill（同长度）/ 静态版本或可见 metadata 规则 / 普通重试或验证器失败后重试 / 新的合同条件候选；资源允许则用官方适配技能或 SkillLearnBench 可复现流程。信息可见性和 token 预算匹配。结果通过目标系统行为测试＋合法 API/状态合同；oracle 合同仅用于评测，禁止作为 agent 提示泄漏。负作用、正确任务、UNKNOWN/过度拒绝、总 token、工具次数、GPU 秒和墙时分别统计。

**可证伪预测**：相同预算下，条件化候选在变更版本的真实任务族降低误用或提升可验证成功，同时在未变更时不过度弃答；若静态版本检测、无 skill、普通重试在匹配成功/风险/成本下追平，则方法停止，仅保留负结果。先约 3–5 个版本族做资格控制、再冻结 20–30 个未见族（具体数量以可获取数据和资源评估为准），报告 family 聚类区间，不把小样本当显著确证。

**论文潜力/风险**：对应热门技能进化与 agent 可靠性，与 Paper E 形成“度量—方法”联系；最大风险是任务由简单版本规则完全解决、skill 内容与测试相互泄漏或只在一个软件生态生效。可基于约束写机制性实证或新问题，但不能由小样本直接推出跨域普遍定理。

## 3. 候选 B：可验证预算分配：什么时候让更多 Agent 帮忙？

**问题**：对真实工具任务的中间状态，能否在观察开销计入后决定“继续单 agent、请求独立审阅、还是执行确定性测试”，使同预算下正确交付更高？要超越 General AgentBench、MultiAgentBench 和 Google 2026 的[规模研究](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/)，必须明确新变量是可部署的中间状态/验证证据，而不是重复比较 agent 数量。

**候选数据**：SkillsBench/公开软件工程 benchmark 和可离线验证的结构化工具环境；校验许可证、可运行容器、源码与测试是否暴露。多 agent 实验应把共享上下文、检索、模型 calls、额外 verifier、串/并行墙时都记入预算；使用 OpenCode/Qwen 组成真实工具 agent，而不是把三次单轮回答算成多 agent。

**基线**：单 agent 等 token 延长、等预算多样采样＋同一个可部署选择器、固定验证顺序、确定性本地测试、随机审阅/固定规则；项目过去 exact-cache 已完全解释的收益不得复用为新发现。候选只用实际可见日志与资源，不用隐藏答案或 gold 预测难度。

**判据**：按未见任务族配对报告任务成功率、质量—成本 Pareto 曲线以及额外验证成本；两种以上任务结构、多次重复后若动态机制仍无法超过最强固定/随机方案或成本抵消，停止。训练是可选备选，须先确认可执行训练标签、分离任务族与不训练对照。预估首轮 3–5 天准备和 100–300 个 agent episode 是规划上界而非实测；并发和计算由实际 GB10 资源测定。

**风险**：管理系统本身造成收益、任务选择偏差和多重比较；小模型可能在基线任务失败而无可识别 headroom；未证明可推广。若无强基线残差，则降为经验结果而不是硬造学习算法。

## 4. 候选 C：不确定工具结果下的执行恢复与受控副作用

**问题**：模拟或真实可离线重放环境中，工具返回超时后，agent 是否能凭可见副作用证据选择重试、只读核实、补偿或 UNKNOWN，避免重复/遗漏？对标 UndoBench 的同阶段故障和幂等、以及 ToolRL-DR 的 transition 干扰；仅重复它们不构成创新。候选差异可检验“部分可见、跨工具组合的恢复合同”，但须核对其现有 8 域/36 族覆盖和最近后续研究。

**实验**：优先在隔离模拟 API/文件操作中按开发、未见工作流分组；冻结 ground-truth effect ledger，部署 agent 只能看到可公开的读取接口。强基线：普通 retry、只读查询+重试、server idempotency、回滚补偿、always abstain；不可声称具备线上支付/生产验证。量化 conditional recovery success、重复或丢失副作用、任务成功、不可恢复状态、成本。需要含至少 2 类故障时序和独立来源；如 server 幂等/只读查询简单可靠则停止候选。仅在此基础上才考虑训练小模型并比较 no-training 和普通 SFT。

## 5. 已完成的只读资格检查和下一步

- 补充真实历史源码的离线执行资格：参见 [Partridge qualification](PARTRIDGE_NATURAL_VERSION_QUALIFICATION.md)。复制的两版在既有兼容性测试补丁下均为 42 passed；`__version__` 均为 `0.11.0`，仅版本号无法区分，但针对已知变更的简单静态检查可区分。没有找到其历史 `SKILL.md`，也未跑固定 skill/普通重试/模型；不能视为 skill 方法实验或残差。原项目旧面板强基线结论依然有效。
- GB10 上实际检查：`/home/testuser/.opencode/bin/opencode`、项目 `venv/bin/python`、`scripts/graph` 和 `/usr/bin/docker` 存在；Python 为 3.12.3。`nvidia-smi` 可见 `NVIDIA GB10`，该查询的总/空闲显存返回 N/A。`command -v opencode` 在非登录 SSH PATH 中未找到，但绝对路径存在。
- 这仅证明文件/命令存在：未检查 Docker 守护进程、未访问模型服务、未调用 OpenCode 或模型、未检验模型权重/许可证、没有进行 agent episode；不可称为 Agent 实验。不开启生产 `:5050` 或现有服务探针，不读取/打印密钥。
- GB10 旧项目两个开发来源的报告实际存在并计算 SHA-256：`research/publication_thesis_goals_v1/revision_v2/G2_V2_REPORT.md` 为 `51412f1059fef4b504d7787d18d1c369396ec7adfff9f5d8332eaf3ec8eb3ac2`；`research/research_portfolio_v2/pymigbench_external_change_v1/ntripbrowser_qualification_v2/QUALIFICATION_RETURN.md` 为 `4d9d301957e1a516ecbc679562fad3d2b175f7a1fe2516475648de7c3488323b`。文件存在与哈希一致不代表复跑、环境可用或满足未见来源条件。
- 下一阶段先冻结 A/B/C 的选择、时间和次数上限，完成公开任务版本/许可/环境资格；任务在隔离工作区运行，原始观测和失败保留，禁止训练测试交叉泄漏。优先 A，B 为另一路候选，C 对照当前非常新的 UndoBench 后再裁决。依据真实残差调整顺序，不因“热”而忽略基线。
