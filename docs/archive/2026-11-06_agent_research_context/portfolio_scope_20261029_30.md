> 历史快照归位于 2026-11-06。原文件 `research/agent_frontier_portfolio_20261029/AGENT_FRONTIER_RESEARCH_PORTFOLIO.md` 的连续片段；旧任务、结果与预算保持当时口径，不能作为当前授权。现状见[第二阶段计划](../../../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。

## 2026-10-30：连续技能学习公开基准资格探索

**实际动作**：在 GB10 `/home/testuser/wzh/research_evidence/agent_learning_20261030/` 获取 [SkillLearnBench](https://github.com/cxcscmu/SkillLearnBench) commit `726e1f79b96b0cb3d729d0e55a1c847e0b5353ae`（仓库声明 MIT，约 2.2 GB）与 [ContinualSkillBench](https://github.com/gtynnn060110-hash/continual-skill-bench-final) commit `91c76f887c2a422d1f8d4c1adacc944c9c2ad6c1`（仓库声明 Apache-2.0，约 4.7 GB）；两者各自依赖的原始数据许可仍需分别确认。未安装依赖、运行上游脚本或接触生产服务。源码和数据在 GB10，未纳入项目 Git。

运行 [只读资格脚本](../../../research/agent_frontier_portfolio_20261029/inspect_continual_skillbench.py)；GB10 的 [聚合回执](../../../research/agent_frontier_portfolio_20261029/continual_skillbench_qualification_20261030.json) 记录 6 个仓库 task streams 各 100 条以及来源和评价方式，6 个 stream 不等同论文报告的 5 个主域，也不说明已经运行 600 条。金融 stream 有 51 条 rubric judge、13 条程序检查、13 条 F1、12 条数值、11 条精确匹配，来源含 10 条 TAT-QA 和 11 条 FinQA，与本项目已有研究来源重叠；是否具体题目或模型训练曝光仍需核验，不能作为无污染外部确认。Office 有 35 条 rubric judge，math 有 25 条；即使筛除 judge，也须检查基础题、数据和检查器是否可独立运行。项目说明预装任务技能，且环境注释说明 `tasks_spec.json` 留在 host；实际 agent 镜像和工具权限须逐项验收，不将静态阅读视为真实泄漏测试。

**合成反例**：直接调用金融 stream 的 `tests/qa_eval.py` 辅助函数，`numeric` 将 `12%` 和 `$12` 评分为 1，`f1` 将 `-5` 与 `5` 评分为 1；`numeric` 对 `-5` vs `5` 为 0，正确同值控制为 1。它揭示辅助函数在这些构造输入下忽略单位或标点的行为，**未证明原始题目出现该反例，也未证明官方 agent 实际运行链一定使用该函数**。文件存在类 pytest 检查不等价语义验证；官方 test.sh 依赖运行时 feedback 聚合，后续须追踪每种调用链并验证端到端合同，不能把静态发现扩大为官方成绩无效。

**可操作判断**：SkillLearnBench 明确提供 20 任务、100 实例、human/no-skill/one-shot/self/teacher 经验基线，环境依赖 Docker 和原作者特定 agent；ContinualSkillBench 的 sequential/pure ICL/independent 直接对应我们的核心竞争基线。已查的 `organize-messy-files-1` Dockerfile 构建时下载 100 份 PDF，金融任务 Dockerfile 需要 Ubuntu 安装依赖；本机镜像未命中对应基础镜像。不能把它们描述为已经可离线复现。优先选择 2 类无凭据、数据可离线核验、来源族可隔离的开发任务，复核 `skills` 与验证器挂载，做正负输出控制，再适配本地 OpenCode/Qwen；保留合成变化与自然任务的区别。当前仍未做真实 sequential agent run，不能声称新方法收益或新颖性。

**资源**：本次科研模型生成、judge、训练及付费 API 均为 0；源码克隆、GPU 状态查询和 CPU 只读检查已完成，不影响既有实验账本或生产环境。

## 2026-10-29 第二篇：用户认可的两条主线与首个比较

**问题池，不是已证明的新方法**：① Agent 怎样把执行反馈转化为之后可迁移的经验；② 任务或环境变化后，怎样判断记忆/skill 的适用性并更新。两者可以在同一连续任务链中联系：先做任务、获得可见反馈、再遇到变化任务，但不能把“把经验写成 skill”或“旧记忆失效”本身当新颖性。旧实验停止针对特定实现，不否定整个领域。

**论文对照（本次仅核对论文摘要/主页，非全文查新）**：[SkillLearnBench](https://arxiv.org/abs/2604.20087) 已研究多种持续 skill 学习；[ContinualSkillBench](https://arxiv.org/abs/2608.03874) 的 v3 摘要称，在两模型三域的比较中，保留上下文与反馈不维护显式 skill 的平均效果接近显式 skill，且部分程序性任务仍受益；[Mem2ActBench](https://aclanthology.org/2026.acl-long.370/) 评估记忆驱动工具选择与参数；[STALE/CUPMem](https://arxiv.org/abs/2605.06527) 已研究旧状态失效和传播；[AMA-Bench](https://proceedings.mlr.press/v306/zhao26bs.html) 涵盖真实/合成 Agent 轨迹并提出因果图记忆检索。**可检验的切入假设**：结合来源条件和可观察反馈，有可能在任务变化时减少错误经验复用而保留成功率；这不是已确认文献空白，需逐篇全文核查已有机制、基线和环境，再选可区分的具体变量。

**可复用素材与适用范围**：

| 素材 | 已获得什么 | 不得直接推论 |
|---|---|---|
| [历史基线地图](../../../research/research_baseline_governance_20261023/RESEARCH_BASELINE_AND_REUSE_MAP.md) | FinRank 当前角色面板一次成功率饱和，历史经验无可识别空间；STALE 的事实/行动/未知分层可用 | 历史经验普遍无效；AI 评审是人工金标准 |
| [Phase B 事后修正](../../../research/decision_residual_pivot_20261026_v1/D_PREMISE_CORRECTION.md) | 真实 LoRA、输出/轨迹和 5 条参考构造的可用纠正；旧 adapter、指标、截断和 schema 问题已查明 | 这 5 条是自然反馈轨迹；旧 R/E 是有效普通父模型继续训练；其失败否定全部反馈学习 |
| [SFT 与模型资产](../../../research/feedback_learning_finance_20261023_v1/FIRST_METHOD_RETURN.md) | Qwen3-4B、PEFT/TRL、冻结生成及按表源隔离工具；可重用普通 SFT 控制 | 早期相关变化得分：须使用后续修正后的评分器和重叠审计；历史外部任务自动等同未暴露来源 |
| [SkillsBench 单任务比较](../../../research/agent_skill_method_20261029/DOCS_AVAILABLE_CONTROL_RETURN.md) | 真实工具 Agent、隔离容器、验证器、raw 工具轨迹；一次强制 skill 通过、可选文档未通过 | 单次即方法优势；提示信息、实际成本和超时完全匹配；适配执行等于官方评测 |
| [既有记忆/行动材料](../../../research/publication_thesis_goals_v1/revision_v5/RESEARCH_SPRINT_RETURN_V5.md) 与 [后续对账](../../../research/research_baseline_governance_20261023/RESEARCH_BASELINE_AND_REUSE_MAP.md) | 区分事实恢复、行动、合理 UNKNOWN 和额外拒绝；存在安全与覆盖取舍观察 | 原 judge 为独立人工 gold；旧状态卡分数证明通用记忆方法；错误的 G2 机制归因可以照搬 |
| [迁移任务资产](../../../research/publication_thesis_goals_v1/revision_v2/G2_V2_REPORT.md) | NtripBrowser、Partridge 实环境与行为/结构检查可供开发 | 旧任务未曝光；简单规则已覆盖的案例存在方法残差 |

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

<!-- End of preserved historical segment. -->
