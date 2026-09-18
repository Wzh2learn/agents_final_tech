---
name: research-driven-design
version: 0.2.0
description: |
  从论文出发的训练策略设计引擎。
  核心流程：论文机制提取 → 核心原理归纳 → 框架映射 → 适配性分析 → 训练信号设计 → 实验验证方案。
  参数耦合适配分析（Step 4.5），防止"改了A忘了配套调B"的系统性失误。
  触发词：设计训练策略、训练信号设计、从论文出发、机制分析、design training、
  怎么训练、loss 设计、梯度路径、训练流程设计、借鉴论文。
  示例：帮我设计 Writer 的训练信号、从记忆压缩类论文出发分析我们的 loss、
  分析这几篇论文的压缩训练策略差异。
metadata:
  author: anonymous
  category: research-tools
  tags: [training, design, paper-analysis, loss-design, mechanism-extraction]
allowed-tools: [Read, Glob, Grep, Agent, WebSearch, WebFetch, Write]
---

# Research-Driven Design — 从论文出发的训练策略设计引擎

> **设计哲学**：the framework is fixed，问题是每个模块的训练信号从哪来、梯度怎么流。
> 答案不在我们脑子里，在已发表的论文里——但不能照搬，需要提取核心机制后映射到我们的框架。

## 什么时候用这个 Skill

- 需要为某个模块设计/改进训练信号（loss function、梯度路径、训练策略）
- 想从一组论文中提取可借鉴的训练机制
- 需要分析"别人的做法"和"我们的框架"之间的映射关系
- 要给训练策略变更设计对应的消融实验

## 核心流程：5 步设计法

### Step 1: 问题定义（Problem Framing）

**明确要解决的问题**，格式化为：

```
模块: [哪个模块需要改进]
当前状态: [现在怎么训练的，效果如何]
核心矛盾: [为什么当前方式不够好]
约束条件: [哪些不能改——架构、复杂度、部署方式]
```

**关键原则**：
- 不要从"我想加什么 loss"出发，要从"这个模块应该学到什么能力"出发
- 把模块的**部署时行为**想清楚，训练信号要让模块学会部署时需要的能力
- 例：Writer 部署时是"session 结束后异步压缩写入"→ 训练时 Writer 应学会"产生对未来检索有用的 episode"

### Step 2: 论文机制提取（Mechanism Extraction）

**从相关论文中提取训练机制**，每篇论文回答 5 个问题：

```
论文: [名称]
对应模块: [它的哪个模块和我们要设计的模块功能类似]
训练信号: [这个模块的 loss 是什么，梯度从哪来]
是否端到端: [推荐 loss 能反传到这个模块吗]
stop-gradient: [哪些地方有 detach/no_grad，为什么]
核心洞察: [一句话说清楚这个设计为什么 work]
```

**常用论文索引（推荐系统 + 记忆压缩）**：

| 论文 | 核心贡献 | mapping to core operations |
|------|---------|---------------|
| **记忆前向路径类** | 记忆读取走 forward-path,最大化 I(M;Y) 而非 I(M;X) | 压缩模块梯度路径 |
| **离线压缩类** | 查询感知的离线压缩 + 生命周期流 | 写入侧预缓存 + 离线压缩 |
| **ICLRec** | K-means prototype + EM framework | 原型初始化与更新 |
| **HSTU** | 生成式全位置 loss, O(N) 效率 | Decoder 训练策略 |
| **锚点交叉注意力类** | 用 cross-attention 锚点做信息聚合 | 压缩模块设计 |
| **Compressive TF** | stop-gradient 压缩记忆 + segment recurrence | 缓存重建设计 |
| **新颖度门控类** | 基于分布(如 vMF)的 novelty gate | 写入门决策信号 |
| **LLM 决策类** | 用 LLM 做写入决策 | Write Gate 的认知动机 |
| **认知折叠类** | 主动认知折叠(认知科学动机) | Write 的认知科学基础 |
| **Infini-Attention** | Delta Rule 去冗余 | Writer 去冗余信号 |

**如何搜索新论文**：
1. 在 Semantic Scholar / arXiv 搜索关键词
2. 重点看 Method 的 Training 章节和 Loss 公式
3. 关注 ablation 中"去掉某个 loss 后效果变化"的实验

### Step 3: 核心原理归纳（Principle Extraction）

从多篇论文中归纳出**通用原则**（不是照搬某篇论文的做法）：

**常见原则模板**：

- **信息瓶颈原则**：压缩模块应最大化 I(M;Y)（对下游任务的信息），而非 I(M;X)（对输入的重建）
  - 来源:重建型 loss 的删除消融(去掉重建 loss 后指标不降反稳)
  - 推论：Writer 的 loss 不应该是"还原输入"，而是"帮助预测"

- **Forward-path 原则**：如果希望推荐 loss 反传到某模块，该模块必须在 forward path 上
  - 来源:记忆前向路径类(读取在 forward-path)对比离线压缩/stop-grad 类(Compressive TF)
  - 推论：rebuild_cache (no_grad) 和 forward-path Writer 是互补的，不是替代的

- **训练-部署一致性原则**：训练时模块看到的输入分布应接近部署时
  - 来源:压缩质量 loss(记忆前向路径类) + ICLRec per-epoch 重聚类
  - 推论：rebuild_cache 每 epoch 更新是必要的

- **选择性编码原则**：不是所有输入都值得压缩存储，Gate 需要任务驱动的信号
  - 来源:新颖度门控类(novelty gate)、LLM 写入决策类、认知折叠类
  - 推论：Gate 应通过 L_gen 梯度或 novelty 信号学习

- **阶段性训练原则**：复杂模块应分阶段训练，避免初始化阶段的梯度冲突
  - 来源:分阶段训练(记忆前向路径类 / 离线压缩类的 Stage 1→2→3) + curriculum learning
  - 推论：先稳定基础模块，再开启高级模块的训练

- **参数耦合适配原则**：改变任何一个超参数时，必须检查所有与之耦合的参数是否需要同步调整
  - 来源:过往实验教训 + batch size scaling law(linear scaling rule)
  - 核心逻辑：超参数不是独立的，它们通过梯度流、score scale、训练 budget 等隐式耦合
  - 典型耦合关系见 Step 4.5 的耦合图谱
  - 推论：**一个"好 idea"配上不适配的周边参数，结果可能是负向的**——失败不代表 idea 错，可能只是适配没做

### Step 4: 框架映射与方案设计（Framework Mapping）

将归纳出的原则映射到自己的框架，生成具体方案：

```
方案名: [简短标识]
原理来源: [基于哪条原则]
具体做法: [代码级描述：哪个函数改什么]
梯度路径: [画出 loss → ... → 目标模块的反传路径]
与部署的一致性: [训练时 vs 部署时的行为差异]
预期效果: [期望改善什么指标]
风险: [可能的负面效果]
```

**梯度路径可视化格式**：
```
L_gen → Decoder → Router → episodes → [Gate·PGC] → Prototype
                                        ↑ 有梯度    ↑ 有梯度
```

**方案对比矩阵**：
对每个方案评估 5 个维度（1-5 分）：
- 理论合理性（是否有论文支撑）
- 实现复杂度（代码改动量）
- 训练效率（额外计算开销）
- 部署一致性（训练 vs 部署的 gap）
- 可消融性（能否设计清晰的 ablation）

### Step 4.5: 适配性分析（Adaptation Analysis）🔑

> **这是关键步骤。** 过往实验的教训：score 归一化替换、新增 attention gate 等"好 idea"失败(均为明显负向)，
> 根因不是 idea 本身有问题，而是改了 A 没有同步调 B。这一步强制你在写代码之前完成耦合检查。

**核心思想**：超参数之间存在隐式耦合。改变 X 时，通过以下耦合图谱检查所有受影响的 Y。

#### 4.5.1 耦合图谱（Coupling Map）

```
改动类型              必须检查的耦合参数
─────────────────────────────────────────────────────────
Score 归一化方式改变    → 所有可学习 scale/weight 的初始值
 (add→zscore/softmax)    （归一化后 scale 语义完全不同）
                       → K（检索数量，影响统计量稳定性）

新增可学习参数         → 训练 epoch 数（新参数需要足够 budget）
 (新 MLP/Gate/Head)      → 该参数的 LR（可能需要独立 param group）
                       → 初始化策略（应偏向已知的好初始点）
                       → Curriculum 兼容性（新参数在哪个 Phase 开始训练）

模块 LR 倍率改变       → rebuild_every（学得更快 → cache 过时更快）
 (writer_lr_mult)       → Phase 长度（学得快 → 可能提前收敛）
                       → K_segments（LR 是间接补偿，信号量是根本）

Batch size 改变        → LR（linear scaling: LR × sqrt(new/old)）
                       → Epochs（steps = data / bs, 保持总 steps 一致）
                       → Gradient accumulation steps

K（检索数量）改变      → Router 的 score 分布（K 大 → 更多噪声候选）
                       → 归一化方式的统计稳定性
                       → 内存和计算开销

Curriculum Phase 调整  → 各模块在新 Phase 划分下的训练 epoch 数
                       → 新参数是否在某个 Phase 被静默跳过
                       → rebuild 时机是否仍与 Phase 切换对齐

Loss 权重 / 新 Loss    → 梯度量级平衡（新 loss 是否淹没旧 loss）
                       → 是否需要 loss warmup / annealing
```

#### 4.5.2 适配检查清单（必须逐项过）

对 Step 4 中设计的每个方案，填写以下表格：

```
方案名: ____
主改动: ____（一句话描述改了什么）

耦合检查:
 □ Scale/初始化: 改动是否改变了某个量的数值范围？相关权重初始值是否匹配新范围？
 □ 训练预算: 新增参数是否有足够 epoch 训练？是否被 Curriculum 某个 Phase 屏蔽？
 □ LR 分组: 新参数/改动模块是否需要独立 LR？与现有 param group 的 LR 是否冲突？
 □ Rebuild 频率: 改动是否加速/减缓某个模块的参数变化？cache 更新频率是否匹配？
 □ 统计量稳定性: 如果用了归一化/统计量，样本数（K, J, batch_size）是否足够？
 □ 初始化偏置: 新组件的初始行为是否接近已知的好配置？（不要从均匀随机开始）

遗漏的适配 → 补充到实验设计中，或作为单独的 ablation 验证
```

#### 4.5.3 案例：一次"改了A忘配B"的适配缺失复盘

| 实验 | 主改动 | 适配缺失 | 后果 | 修复方案 |
|------|--------|---------|------|---------|
| score 归一化替换 | 打分融合 add→zscore | 两个权重仍取旧的 0.1（z-score 后应为 1.0） | importance/semantic 被压制到约 10%，明显负向 | init 改为 1.0 |
| 新增 attention gate | 新增小 MLP | 前若干 epoch 无梯度，剩余训练不足；初始化均匀≈等权 | 欠拟合+gate collapse，明显负向 | bias init 偏向主信号 + gate lr 提高 + 延长该阶段 |
| 动态提速某模块 | 该模块 lr 动态递增 | 从 1x 起步递增，到中段才达峰值(已证明应一开始就用峰值) | 关键早期阶段 lr 不足，轻度负向 | 起点即峰值,在此基础上微调 |
| lr 提峰后到顶 | 该模块 lr 提到峰值 | 缓存重建频率没跟着调(模块变快→缓存过时更快);分段数没增 | 增益很快到顶 | 提高重建频率配合,或增分段数 |

**教训**：每个"失败"实验的 idea 本身都是合理的，失败原因是改了一个旋钮没有转配套的旋钮。

### Step 5: 实验验证方案（Experiment Design）

为选定的方案设计消融实验：

```
实验矩阵:
  基线: [对照组配置]
  变量: [只改一个因素]
  指标: [关注哪些指标，每个指标说明什么]
  判断标准: [什么结果说明方案有效/无效/需要调整]
```

**实验设计原则**：
- 每次只改一个变量（不要同时改 loss + 架构 + 训练策略）
- 控制总训练 steps 一致（避免"多训了"的混淆因素）
- 关注指标组合而非单一指标（HR@10 + NDCG + MRR 综合看）
- 设计"如果结果是 X 则说明 Y"的预判
- **适配验证**：每个实验必须通过 Step 4.5 的耦合检查清单。如果发现有未适配项，要么修复后再跑，要么拆成两组实验——一组不适配（验证 idea 的 raw effect），一组适配后（验证 idea + 适配的 joint effect）。**实验失败时，先排查适配缺失，再否定 idea 本身。**

---

## 使用示例

### 示例 1: 设计 Writer 训练信号

用户: `/research-driven-design Writer 的训练信号应该怎么设计？`

执行流程:
1. **问题定义**: Writer(Gate+PGC) 负责将 session 压缩为 episode 写入 L2。当前纯靠 L_gen 通过 forward-path 反传，信号微弱。
2. **论文提取**: 读记忆前向路径类(I(M;Y))、离线压缩类(detach)、新颖度门控类、Compressive TF(stop-grad)
3. **原理归纳**: I(M;Y) > I(M;X); forward-path 保证梯度; Gate 需要任务驱动信号
4. **方案设计**: 3个候选方案 + 对比矩阵
5. **实验验证**: 消融矩阵 + 判断标准

### 示例 2: 从某篇新论文借鉴训练策略

用户: `/research-driven-design 看看 XYZ 论文的训练策略能不能用在我们的 Router 上`

执行流程:
1. 读论文，提取 5 问题模板
2. 识别与 Router 的对应关系
3. 评估可迁移性（架构差异、假设差异）
4. 设计适配方案
5. 设计 A/B 实验

---

## 输出格式

每次执行输出一个结构化报告:

```markdown
# [模块名] 训练策略设计报告

## 1. 问题定义
...

## 2. 论文机制提取
| 论文 | 对应模块 | 训练信号 | 端到端 | 核心洞察 |
...

## 3. 核心原则
- 原则 1: ...
- 原则 2: ...

## 4. 候选方案
### 方案 A: ...
### 方案 B: ...
### 对比矩阵
| 维度 | 方案A | 方案B |
...

## 5. 推荐方案 + 实验设计
...
```

---

## 与其他 Skill 的关系

- **research-paper-pipeline**: 写论文用的全流程 skill。research-driven-design 聚焦于"训练策略设计"这个子问题
- **dream-engine**: 做梦产出 idea。research-driven-design 把 idea 落地为具体的训练方案
- **socrates**: paper study。research-driven-design 更侧重"怎么改进"而非"怎么理解"
- **neat-freak**: 文档同步。design 产出的报告会被 neat-freak 整理到 docs/
