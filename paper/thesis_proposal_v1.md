# 博士学位论文开题报告 v1

> 状态：可讨论稿（供导师开题讨论用）| 更新：2026-09-24 | 密级：**仅限内部审阅**
> 公开边界：专利申请状态未经用户确认前，本件与其派生稿**不得外发、不得上传预印本、不得公开代码**（`claim_manifest_v1.json` 的 `release_gate = patent_status_confirmation_required`）。
> 叙事权威：`paper/research_story_v2.md`；证据账本：`paper/research_asset_map_v2.md`；分层权威与冲突裁定：`docs/research/README.md`；阶段门与执行序唯一依据：`docs/handoff/2026-09-22-paper-research-next-phase.md`。
> 诚实性口径：本件严格区分**已取得证据**与**目标贡献**。凡未闭环者一律标注为「目标 / 待验证」，并写明缺什么；不把目标贡献写成已有结果。

## 1 选题背景与意义

### 1.1 背景

文档智能系统已从单一预测器演变为**长流程管线**：一份金融文档可能依次经历版面解码、表格切分、字段映射到规范 schema、算术一致性校验、检索索引，最后由语言模型作答。每个阶段都可能独立失败，而后续阶段既可能补偿、也可能**掩盖**前序错误。

由此产生两个层次的问题。第一层是系统层面的：最终答案正确并不能说明系统走过了一条可靠的路径。第二层更隐蔽，是**评测层面的**：评测协议本身可能对某类缺陷完全无观测能力。若一个被扰动的表头在进入第一个受测检查点之前就已被归一化回原字段，则所有下游分数都不会变化——此时「最终答案正确」至少有两种解释：系统对该扰动鲁棒，**或者**评测对它是盲的。单一端到端分数无法区分这两种情形。

### 1.2 意义

- **方法论意义**：把「评测协议自身」作为研究对象，使评测报告能够刻画自己的盲区，而不是只给出一个聚合分数。这一立场与机器翻译领域的元评测（meta-evaluation）传统一致，但针对长流程系统提出了一个新的前置问题：协议能否**观测到**被注入的缺陷。
- **工程意义**：长流程系统的回归排查成本极高。若评测能按缺陷家族给出可见性剖面（visibility profile）并保留逐检查点证据，则「静默吸收」类缺陷可被定位而非被平均分掩盖。
- **学位层面的意义**：本课题不止于评估。评估信号若能被迁移，则可支撑低成本小模型的动作策略学习；若经验能被安全固化，则系统可持续进化。由此形成 **Evaluate → Distill → Evolve** 三阶段闭环，这是本论文的总体研究框架。

### 1.3 三阶段闭环的定位（重要口径）

三阶段闭环是本论文的**目标框架**，不是现成结果。按 `research_story_v2.md` 的当前证据分级：

| 阶段 | 内容 | 当前证据成熟度 |
|---|---|---|
| **Stage E（Evaluate）** | 分层检查点评估、确定性契约 + 受泄漏保护的语义裁判、缺陷注入与可见性分析 | **成熟**。95 张公开表、118 个受控注入，阈值 / 匹配器 / 种子 / matched-FPR 审计均已落仓并经独立验收 |
| **Stage D（Distill）** | 以 checkpoint 过滤可追溯动作事件，构造监督 / 偏好数据，训练 8B 主学生 | **尚未闭环**。已有 4B/8B/14B 零样本能力矩阵、蒸馏文献核验、60 条 DPO 偏好对；**没有学生模型训练、蒸馏基线或训练后评测**。60 对均偏向 `skip`，A3 仅为条件臂，14B 既有异常尚未归因 |
| **Stage R（Evolve）** | gain–collateral 双门 + 独立 gate-validation，规则版本化与回滚 | **机制级成立、功效未闭合**。对抗建议 7/7 被拒、扩展碰撞候选 5/5 被拒；碰撞体制出现方向性收益，但总体下游效应未达强结论标准；独立验证门与长期版本回滚的完整对照仍待实验 |

## 2 国内外研究现状

本节为开题阶段的综述纲要；完整分类体系与术语定义在第 2 章展开。已核验的引用池见 `paper/references_v0.md`（逐条附 arXiv ID / DOI），其中 venue 除个别外一律标注为 arXiv preprint，不标注未经核实的会议归属。

### 2.1 元评测（meta-evaluation）

机器翻译挑战集（如 ACES）评估一个指标能否区分真实错误与可接受变体 [Amrhein et al., 2022; Amrhein et al., 2023; Moghe et al., 2024]；语境化指标元评测把这一视角扩展到局部、依赖上下文的正确性 [Deviyani and Diaz, 2025]。更近的研究表明，排名会随协议轴、prompt 子集、随机种子或指标所要测量的属性而改变 [Kendiukhov, 2026; Du et al., 2026; Ross et al., 2024]。**与本课题的关系**：本课题采纳同一元评测原则，但追问一个更前置的问题——长流程协议能否**观测到**被注入的缺陷。

### 2.2 过程级与层级评测

面向过程的基准在工具使用型与网页型 agent 上诊断中间行为，而非只对最终成功打分 [Fan et al., 2026; Chung et al., 2026]；GTA-2 把任务表示为递归聚合的检查点 [Wang et al., 2026]。**与本课题的关系**：本课题的聚合沿用该递归检查点结构，但增加了确定性契约、显式的缺失证据行为，以及按缺陷家族暴露评测器敏感度的受控注入。

### 2.3 变异测试与故障注入

变异测试与蜕变测试通过引入受控变化来度量测试或指标是否察觉 [Cho et al., 2025]；AgentChaos 把程序化故障注入用于 agent 系统 [Tan et al., 2026]。这些传统通常把每个变异体概括为「被杀死」或「存活」。**与本课题的关系**：本课题保留**第三种结果——静默吸收（silent absorption）**，并按家族分别报告；同时区分「评测器盲区」与「无效变异体」（其预期损害在被打分的那一层不可观测）。

### 2.4 语义裁判的可靠性

LLM 裁判适用于开放语义质量，但存在位置偏置、冗长偏置、自我偏好与扰动敏感 [Zheng et al., 2023; Li et al., 2025a; Li et al., 2025b]。**与本课题的关系**：因此本课题把可契约化属性交给确定性检查，只在语义维度使用裁判，对裁判隐藏注入真值，并显式报告裁判的分辨率与样本上限。

### 2.5 知识蒸馏与 agent 蒸馏（Stage D 的文献基础）

经典蒸馏 [Hinton et al., 2015] 与综述 [Gou et al., 2021]、面向大模型的蒸馏综述 [Xu et al., 2024] 构成方法基础；DeepSeek-R1、Qwen2.5、Llama 3 等技术报告提供了当代模型侧的实证参照。**与本课题的关系及边界**：本课题的蒸馏对象被严格限定为**动作策略 / 规则候选**（学生提出 `map_to / skip / hold` 与目标字段并做验证预筛），**不替代最终确定性验证门**；完整推理轨迹蒸馏不在本课题范围内，因为现有记录（`research/vgmc_exp1.py`）只含动作事件、不含完整推理轨迹。该方向在本论文中作为**目标贡献**，其证据缺口见 §6 的 TH-I3。

### 2.6 规则学习与自进化（Stage R 的文献基础）

规则归纳、程序合成与自我改进 agent 的相关工作为「经验固化」提供了方法论参照。**与本课题的关系及边界**：本课题的特色是把固化置于**确定性验证门**之后，并要求独立 gate-validation、版本化与可回滚，以避免自进化累积有害规则。该方向在本论文中为**机制级可行、效果未闭合**，见 §6 的 TH-I4。

### 2.7 现状小结与本课题的切入点

现有工作在「如何给长流程系统打分」上已相当丰富，但在「**打分这件事本身能否看见某类缺陷**」上缺少系统方法：变异测试传统把结果二值化，元评测传统关注指标排序稳定性，过程级基准关注中间步骤正确性。三者都没有把**缺陷可见性**与**协议结构对结论解释的影响**作为一等研究对象。本课题的切入点即在此。

## 3 研究目标与研究问题

### 3.1 总目标

研究如何把长流程大模型系统的中间过程变成**可测量、可迁移、可安全积累**的能力：先用分层检查点评估流程，再把 checkpoint 筛选出的规则动作蒸馏给小模型，最后由确定性验证门控制规则固化与版本化回滚。

### 3.2 总研究问题

长流程文档智能系统中，如何先获得可信的过程级评估信号，再把这些信号迁移给低成本小模型，并将稳定经验安全固化为可验证、可回滚的规则，使系统持续进化？

### 3.3 分解研究问题与主张边界

下表直接沿用 `research_story_v2.md` §3 的口径，**「当前可写主张」与「还缺什么」两列同等重要**，后者定义了各阶段的验收门：

| RQ | 问题 | 当前可写主张 | 还缺什么 |
|---|---|---|---|
| **RQ1** | 如何获得可诊断、可复现的长流程评估信号？ | 分层证据与可见性谱能揭示协议盲区；**不主张**层级聚合有更高检出率 | 第二数据流或第二 scorer |
| **RQ2** | checkpoint 筛选能否改善小模型规则动作学习？ | 只能提出方法与数据构造；现有小模型矩阵**不是**蒸馏结果 | 8B 主学生、A1/A2 双口径、条件 DPO、独立 sealed 未见家族 |
| **RQ3** | 蒸馏或推理得到的经验能否安全积累？ | 门控机制能拒绝已构造的有害候选；**不主张**已获得稳定显著净收益 | 强门控基线、功效分析、版本回滚与长期曲线 |
| **RQ4** | 三阶段闭环是否改善质量—成本—风险权衡？ | 当前只能作为总假设与系统设计 | 统一端到端实验与消融 |

## 4 研究内容与章节安排

| 章节 | 核心内容 | 继承小论文 | 大论文必须新增 | 当前成熟度 |
|---|---|---|---|---|
| 第 1 章 绪论 | 问题、意义、研究问题与贡献 | 小论文 motivation 与限制 | 学位论文场景、研究边界、章节关系 | 可写 |
| 第 2 章 相关工作与问题定义 | 长流程评测、元评测、故障注入、语义裁判 | 小论文 Related Work | 更系统的分类体系与术语定义 | 可写，需扩充文献 |
| 第 3 章 判别力感知的分层评测 | 检查点树、契约/裁判分工、聚合与校准 | SP-RQ2、SP-RQ3 | 成本模型、强基线、第二类长流程 | 中高 |
| 第 4 章 缺陷可见性与静默吸收 | 可见性谱、等价类、盲区归因 | SP-RQ1 主体结果 | 强度梯度、跨数据流复现、匹配器边界 | 中高 |
| 第 5 章 评估引导的小模型蒸馏 | checkpoint 动作过滤、规则候选蒸馏、质量—成本 Pareto | 目标主线，**当前无训练结果** | 8B 主学生、4B 仅 smoke、SFT/条件 DPO、四层隔离、未见家族 | **低，先过数据/可学性门** |
| 第 6 章 验证门控的规则自学习 | 候选生成、gain–collateral + 独立 gate-validation、固化与回滚 | 小论文第三阶段 | 七类门基线、功效、碰撞控制、独立 future replay | **机制级，效果未闭合** |
| 第 7 章 系统实现与综合实验 | 工程架构、复现、成本与综合分析 | 复用证据链与工具 | 跨章节统一实验协议 | 待整合 |
| 第 8 章 总结与展望 | 结论、适用边界、后续工作 | 继承小论文限制 | 总体回答与学位贡献闭环 | 后写 |

## 5 研究方案与技术路线

### 5.1 总体路线

```text
Stage E  分层检查点评估（已成熟）
   ↓ 产出：逐检查点证据、缺陷家族标签、可见性剖面
Stage D  评估引导的动作策略蒸馏（待数据门）
   ↓ 产出：学生动作策略 + 质量—成本/风险—覆盖对照
Stage R  验证门控的规则固化与回滚（机制已通、功效待闭合）
   ↓ 产出：可审计的规则增量与版本化回滚
闭环评测  质量 / 成本 / 缺陷可见性 / 回归风险 四轴统一报告
```

### 5.2 预注册门序列（不得跳门）

按 `docs/experiments/2026-09-22_distillation_mvp_preregistration.md` §3，必须**按顺序**通过，不可跳门：

1. `SOURCE_GO`：公开来源 URL、license 适用范围、commit/release、字节 hash 与零甲方数据证明已核。
2. `LABEL_GO`：Q3 双审 / 裁决、action/target 正确性、冲突隔离通过。
3. `SPLIT_GO`：按 namespaced lineage UID 与 independence cluster 分 proposal/train、gate-validation、sealed test；同母表的 clean/mutant/轨迹/规则事件不跨层；future replay 允许暂空但须有哈希绑定的获取协议，并标 `LONGITUDINAL_EVIDENCE_UNAVAILABLE`。
4. `POWER_GO`：用**开发侧方差假设**做 UID 聚类 MDE / 功效分析；**不用 sealed 结果反推参数**。
5. `BASELINE_GO`：五类简单基线（always-skip、确定性匹配器、词法/模糊、confidence-only、简单分类器）仍留有可学残差；`SIMPLE_SUFFICIENT` / `NO_CLEAR_SIGNAL` / `PILOT_ONLY` / `DATA_NO_GO` 均停止主训练。
6. `MODEL_GO`：用户批准模型、权重许可、GB10 窗口、预算、输出目录与恢复策略。

### 5.3 数据边界与泄漏规则

proposal/train（含内部 dev）、gate-validation、sealed test、future replay 的 UID **必须隔离**；sealed test 不参与接受、阈值选择或 early stopping。阈值只在 proposal/train 内部 dev 上按预注册规则选取。四层数据边界的完整规则见 `paper/dataset_protocol_v1.md`。

### 5.4 fail-closed 的工程化

本课题的一个方法学特色是：**数据验收、简单基线、七臂规则门与表图接口都被固化为 fail-closed 的软件合同**，而非人工检查清单：

- `research/phase1a_data_contract.py`：私有包预检，7 个机器门、98 个失败码；阻断 Python socket 入口；只输出聚合计数、哈希、门错误与人工复核清单，**从不写入样本文本**。两种结局：`DATA_NO_GO`（exit 2）或 `READY_FOR_INDEPENDENT_ACCEPTANCE`（exit 0）——后者**不等于** `DATA_GO`、不等于训练许可、不等于论文结果。
- `research/phase1a_learnability_baselines.py`：五臂基线，拒绝 gate/sealed/future 样本与 `gain`/`collateral`/`accepted`/`split`/`partition` 字段；只输出开发级信号，四个决策（`SIMPLE_SUFFICIENT` / `LEARNABILITY_SIGNAL` / `NO_CLEAR_SIGNAL` / `PILOT_ONLY`）一律携带 `training_authorized=false` 与 `paper_result=false`。
- `research/phase2_rule_gate_replay.py`：七臂共享候选顺序、各臂自维护规则状态，源 gain / proposal collateral / 独立 gate delta 均从**该臂当前状态重算**，不沿用旧臂分数；输入重复 JSON 键被 `object_pairs_hook` 拒绝。
- `research/paper_result_views.py`：Table 2 / Figure 4 的聚合接口，始终输出 `paper_result=false` 与未验收水印，需独立审查后才允许被论文生成器消费。

这套合同的意义在于：**「通过」是有机器判据的，不依赖研究者自觉**。它同时也是本论文方法论章节的一部分贡献。

### 5.5 实验环境与验收纪律

GB10 是唯一权威运行 / 实验 / 验收环境；本机只做 git 同步、文本编辑与控制面分析。所有正式数字由 GB10 产生并带 artifact 路径、命令、退出码、资源占用与停止条件。资源门（磁盘 / inode / 内存 available / GPU utilization / 并发 / 产物体量 / 调用预算 / 进程回收 / 8 条立即停止条件）见 `docs/governance/2026-09-24_gb10_experiment_safety_gates.md`。每阶段由 Loop B（纯 bash 验证层）与 Loop C（独立审计）独立验收，**实现者不自验**。

## 6 学位创新点及其成熟度口径

以下四条沿用 `paper/thesis_manuscript_scaffold_v1.md` 的口径，**逐条标明当前可主张到什么程度**：

1. **TH-I1：判别力感知的分层评测。** 当前**可主张**可审计的证据分解；**额外定位收益必须在多个输入敏感 leaf 的场景中验证**——目前只有一个受打分 leaf 随注入输入变化，故定位价值尚未确立。
2. **TH-I2：缺陷可见性与静默吸收分析。** 当前证据支持**按缺陷家族揭示盲区**；**普遍性**需要第二数据流与等价类边界实验。
3. **TH-I3：评估引导的小模型动作策略蒸馏。** 当前有训练前模型矩阵、文献核验与偏好对，**没有学生训练结果**；且记录不是完整推理轨迹。**必须补齐规则候选学习证据才能成为创新点**，否则只作为研究计划呈现。
4. **TH-I4：验证门控的规则自学习。** 当前**只是机制可行性**；没有强基线、功效分析、独立 gate-validation 与 sealed test / future replay 证据前，**不写成已证实的效果创新**。

视觉跨层补盲不再单列创新点；通过预注册门后作为 TH-I2 的扩展，否则只记为失败边界。

## 7 已有工作基础与可追溯证据

### 7.1 已成稿并通过机器验收的小论文（评估保底路线）

`paper/teacher_review_draft_v1.md`（另有 `.docx`）已具备 `paper/claim_manifest_v1.json` 要求的全部 9 个章节（Abstract / Introduction / Related Work / Method / Experimental Setup / Results / Discussion and Limitations / Conclusion / References），两张必需图件均存在，4 个交付文件齐备，且该 manifest 列出的 **10 个内部流程标记零命中**（标记清单以 manifest 为唯一出处，本件不逐条复述，以免正文自身触发该项检查）。仓库自带的验收测试 `tests/test_paper_claim_acceptance.py` **7 passed**，其中含反例 `test_acceptance_rejects_reversed_visibility_claim` 与专利门检查 `test_teacher_review_docx_keeps_patent_gate_closed`。

其核心实证结论（全部来自已验收 artifact，可追溯）：在含 **95 张表、118 个合成表头漂移注入**的冻结公开表格语料上，检查点级分析使 **96** 个注入可见，但可见性**强烈依赖类型**——字符级 OCR 类扰动在**五个阈值下全部 13 例**中均不可见；协议级结果在同一语料上差异巨大：端到端、扁平、层级专家加权聚合分别检出 **112 / 85 / 13** 个注入；在**匹配假阳率**之后，扁平与层级分数在该语料上**仿射等价**，说明原始差距来自**阈值摆放**而非更好的判别力。

由此得到的是一条**刻意收窄**的结论：层级结构提供**证据分解**，而非在当前设定下更好的检出灵敏度；其额外定位价值**尚未确立**，因为只有一个受打分 leaf 随注入输入变化。

### 7.2 claim–evidence 映射

`paper/claim_manifest_v1.json` 以机器可读方式记录 4 条主张及其状态，状态词本身即体现克制：`SP-C1 = supported_with_scope_limit`、`SP-C2 = supported_as_diagnostic_not_superiority`、`SP-C3 = supported_with_external_validity_gap`、`SP-C4 = mechanism_case_only`。

### 7.3 尚未取得的关键证据（如实列，不掩饰）

- **Phase 1a 数据门当前为 `DATA_NO_GO`**。经跨 production 与全盘的穷尽搜索确认：`gold_action` / `label_ledger` / `confidence_manifest` / `parser_contract_receipt` / `analysis_plan` / `phase1a_manifest` 六项命中均为 **0**，即**全盘不存在任何 Phase 1a 包根**，也不存在带 ≥2 独立 reviewer 身份与裁决记录的正确性标签账本。见 `docs/experiments/2026-09-24_phase1a_data_gate_reverification.md`。
- 已有的 `source_tables`（`tatqa_tables.json`，sha `3e7e0568…`）与 `injection_map`（118 条 / 95 uid / 含 `deterministic=true, seed=42, ratio=0.3` 溯源，sha `d7612405…`）**可直接哈希绑定、不必重新交付**；故外部补充范围收窄为 **7 个角色 + 1 个包根**。
- `H3a_uid_any_harm` 因被钉为 `exact_mcnemar`，在 α=0.05 下需 **≥5 个不一致对**才可能显著，而合同对 `minimum_uid_by_action` 只要求 `>= 2`（健全性下限，非功效下限）⇒ 存在**结构性欠功效**风险，处置目标为补充 **250–500 个有效 UID**，达不到则该假设降为 exploratory，**不改检验方法、不以功效不足冒充显著**。见 `docs/experiments/2026-09-24_phase1a_power_mde_sensitivity_grid.md`。
- D 类参数（`minimum_uid_*`、`mde_by_confirmatory_contrast`）在拿到真实开发侧 σ 之前**在数学上无法收敛到唯一值**（同一 δ 下所需独立 UID 数跨一个数量级，主导项是 σ²）。

## 8 进度安排与阶段门

本开题不设独立排期，**执行序唯一依据** `docs/handoff/2026-09-22-paper-research-next-phase.md`：

1. **数据补充与 Phase 1 审计**：还原 checkpoint / 规则候选 / 门控标签的 provenance，按源表 uid 分组去重，报告独立样本、冲突与四层数据边界。
2. **Phase 1a 零端点可学性探针 + Phase 2 规则强基线**：五臂回答「为什么需要小模型」；同一候选流上的七类规则门回答「确定性安全门的增量价值」。
3. **训练窗口**：离线门通过后才申请；4B 仅做训练链 smoke test，8B 为主学生；GGUF 不能作训练底座。数据不足只能申请明确标注的 smoke/pilot，**不自动升级为主实验**。
4. **近期蒸馏范围**：只做动作策略 / 规则候选蒸馏；学生提出 `map_to / skip / hold` 与目标字段并做验证预筛，**不替代最终确定性门**。
5. **止损门随时执行**，而非等满三周：数据仅 `PILOT_ONLY`、简单规则已解决问题、非劣失败或安全回归时，立即转评估保底稿内部交导师，D/R 留给大论文。

**双轨不互相阻塞**：评估保底稿（已成稿）与三阶段完整稿是两条交付线，不能用前者冒充后者。所有 null / adverse result **原样保留**，不改 split、阈值、家族或容差来救结论。

## 9 预期成果与风险

### 9.1 预期成果

- 一篇评估方向的完整小论文（**已成稿**，待专利门确认后送审）。
- 三阶段闭环的大论文（**目标**）；若 Stage D/R 未在安全边界内闭环，则按止损门转为「成熟评估子稿 + D/R 边界与后续工作」，**不无限等待**。
- 一套可复用的 fail-closed 数据 / 基线 / 规则门软件合同与论文视图接口（**已落仓并有测试**）。

### 9.2 主要风险与对策

| 风险 | 影响 | 对策 |
|---|---|---|
| 私有数据补充不到位 | Stage D/R 无法启动，TH-I3/TH-I4 不能成为已证实创新 | 已把外部索取范围收窄到 7 角色 + 1 包根；同时按止损门以评估保底稿交付，D/R 明确写成边界与后续工作 |
| `H3a` 结构性欠功效 | RQ3 的安全主张无法达到确认性显著 | 目标补充 250–500 有效 UID；达不到则降 exploratory，不改检验方法 |
| 层级评测无判别力增益（已实测的 null） | TH-I1 的定位价值受限 | **原样保留该 null**，把主张收窄为「证据分解」而非「更好检出」，并以 matched-FPR 仿射等价作为证据 |
| 单一数据流 / 单一 scorer | 无法作普适性主张 | 明确写入边界：第二数据流与第二 scorer 未完成前不作跨域或普适性主张 |
| 专利公开门未确认 | 全部稿件只能内部审阅 | `release_gate = patent_status_confirmation_required`；确认前不外发、不上 arXiv、不公开代码 |

## 10 不得混写的边界（沿用骨架，逐条生效）

- 小论文的 matched-FPR null **不能**写成「层级协议优于扁平协议」。
- 小模型零样本矩阵**不能**被称为蒸馏结果。
- 小论文的门控案例**不能**替代大论文规则自学习的效果验证。
- 第二数据流与第二 scorer 未完成前，**不作**跨域或普适性主张。
- 专利状态确认前，所有稿件**仅限内部审阅**。

## 11 参考文献

引用池见 `paper/references_v0.md`（逐条含 arXiv ID / DOI 与 BibTeX，未核实项单列且**不入引用**）与 `paper/method_data_references_v1.bib`。本开题正文中的作者—年份标注均取自该已核验池；venue 除已核实者外一律写 arXiv preprint，不标注未经核实的会议归属，不引用未经核实的 CFP。

同姓同年消歧（标注 → cite key）：`Li et al., 2025a` = `li2025robustjudge`，`Li et al., 2025b` = `li2025scoringbias`；`Amrhein et al., 2022` / `Amrhein et al., 2023` 分别 = `amrhein2022aces` / `amrhein2023aceswmt`；`Gou et al., 2021` = `gou2021kdsurvey`。本开题正文未引用池外任何条目。

### 11.1 本开题正文引用的 18 条（逐条回指已核验池）

1. `amrhein2022aces` — ACES: Translation Accuracy Challenge Sets for Evaluating Machine Translation Metrics, arXiv:2210.15615, 2022.
2. `amrhein2023aceswmt` — ACES: Translation Accuracy Challenge Sets at WMT 2023, arXiv:2311.01153, 2023.
3. `moghe2024acesjournal` — Machine Translation Meta Evaluation through Translation Accuracy Challenge Sets, arXiv:2401.16313, 2024.
4. `deviyani2025contextual` — Contextual Metric Meta-Evaluation by Measuring Local Metric Accuracy, arXiv:2503.19828, 2025.
5. `kendiukhov2026ranking` — Quantifying Ranking Instability Across Evaluation Protocol Axes in Gene Regulatory Network Benchmarking, arXiv:2603.03493, 2026.
6. `du2026promptranking` — On the Stability of Prompt Ranking in Large Language Model Evaluation, arXiv:2606.24381, 2026.
7. `ross2024goodmetric` — What makes a good metric? Evaluating automatic metrics for text-to-image consistency, arXiv:2412.13989, 2024.
8. `fan2026agentprocessbench` — AgentProcessBench: Diagnosing Step-Level Process Quality in Tool-Using Agents, arXiv:2603.14465, 2026.
9. `chung2026webstep` — Where Did It Go Wrong? Process-Level Evaluation of Web Agents with Semantic State Tracking, arXiv:2606.15673, 2026.
10. `wang2026gta2` — GTA-2: Benchmarking General Tool Agents from Atomic Tool-Use to Open-Ended Workflows, arXiv:2604.15715, 2026.
11. `cho2025metamorphic` — Metamorphic Testing of Large Language Models for Natural Language Processing, arXiv:2511.02108, 2025.
12. `tan2026agentchaos` — AgentChaos: Chaos Engineering for Agent Systems via Programmatic Fault Injection, arXiv:2608.06790, 2026.
13. `zheng2023judge` — Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena, arXiv:2306.05685, 2023.
14. `li2025robustjudge` — LLMs Cannot Reliably Judge (Yet?): A Comprehensive Assessment on the Robustness of LLM-as-a-Judge, arXiv:2506.09443, 2025.
15. `li2025scoringbias` — Evaluating Scoring Bias in LLM-as-a-Judge, arXiv:2506.22316, 2025.
16. `hinton2015distilling` — Distilling the Knowledge in a Neural Network, arXiv:1503.02531, 2015.
17. `gou2021kdsurvey` — Knowledge Distillation: A Survey, IJCV, DOI 10.1007/s11263-021-01453-z, 2021.
18. `xu2024kdsurveyllm` — A Survey on Knowledge Distillation of Large Language Models, arXiv:2402.13116, 2024.

上表 18 条与正文 18 处作者—年份标注一一对应；池内其余条目（如 `messing2026measurementerror`、
`li2024pedants` 与 KD 簇其余件）在本开题正文**未被引用**，仅保留在池中供第 2 章与后续章节取用。
