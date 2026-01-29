# 深入设计：基于 RecSys 思想的层次化记忆管理 (HMM)

## 1. 核心动机
在知识密集型对话/问答场景中，用户的问题往往具有高度的上下文依赖性。传统的滑动窗口（Sliding Window）记忆机制存在两个致命缺陷：
1. **长程遗忘**：超过窗口限制的关键信息（如上周提到的业务前提）会被彻底丢弃。
2. **检索噪声**：简单的向量检索可能召回大量不相关的片段，导致模型推理偏离。

受推荐系统（RecSys）中 **DIN (Deep Interest Network)** 和 **DIEN (Deep Interest Evolution Network)** 的启发，我们将记忆建模为“用户兴趣序列”，通过 **Target Attention** 机制实现精准召回。

## 2. 层次化存储架构 (The Hierarchy)

| 层级 | 名称 | 存储介质 | 对应推荐概念 | 作用 |
| :--- | :--- | :--- | :--- | :--- |
| **L1** | 工作记忆 (Working Memory) | 内存 (LangGraph State) | 近期行为 (Short-term Sequence) | 维持当前对话的即时连贯性（最近 5-10 轮）。 |
| **L2** | 情景记忆 (Episodic Memory) | 向量数据库 (PGVector) | 历史兴趣 (Long-term Interest) | 存储对话碎片。通过 Attention 召回与当前 Query 语义相关的历史。 |
| **L3** | 语义画像 (Profile Memory) | 关系数据库 (SQL) | 用户画像 (User Profile) | 存储已确定的静态事实（如用户组织、偏好、适用文档版本）。 |

## 3. 核心算法设计

### 3.1 记忆感知检索 (Attention-based Retrieval)
不再是简单的 Top-K 召回，而是引入注意力分数计算：
$$Score(q, m_i) = \text{softmax}(\frac{f_{align}(q, m_i)}{\sqrt{d}})$$
其中 $q$ 是当前查询，$m_i$ 是记忆片段，$f_{align}$ 是对齐函数（语义相似度）。

### 3.2 兴趣演化建模 (DIEN 启发)
引入时间衰减因子 $\lambda$。版本化知识/政策/制度类文档往往具有时效性，更近期的对话与证据权重更高：
$$W_{final} = Score(q, m_i) \cdot e^{-\lambda \Delta t}$$

### 3.3 记忆压缩与触发机制
- **触发条件**：当 Working Memory 长度达到阈值（如 20 轮）时。
- **操作**：
    1. 使用 LLM 对最早的 5 轮对话进行 **Summarization**。
    2. 将摘要及原始片段向量化，存入 L2 (Episodic Memory)。
    3. 将提取出的静态事实（如：“用户所在组织/偏好/约束条件”）更新至 L3 (Profile Memory)。

## 4. 实现细节与代码路径

### 4.1 核心类设计

```python
# src/storage/memory/episodic_memory.py
class EpisodicMemoryProvider:
    """情景记忆存储层 (L2)"""
    async def add_memory(session_id, content, metadata):
        """向量化存储记忆片段"""
        pass
    
    async def search_memory(query, session_id, top_k=5):
        """Attention-based 检索"""
        pass

# src/tools/memory_reflector.py
class MemoryReflector:
    """记忆压缩与反射触发器"""
    async def reflect(messages: List[Message]) -> ReflectionResult:
        """LLM摘要 + 事实提取"""
        pass

# src/biz/agent_service.py
class AgentService:
    """HMM 核心编排层"""
    async def _get_long_term_context(message, conversation_id):
        """L2 检索"""
        pass
    
    async def _check_and_trigger_reflection(conversation_id, messages):
        """触发 L2 压缩"""
        pass
```

### 4.2 数据流图

```
User Query → L1 Working Memory (滑动窗口)
              ↓
        [判断是否需要 L2 召回]
              ↓
    ┌───────┴───────┐
    ↓               ↓
  No             Yes
    ↓               ↓
  普通回复      L2 Attention 检索 (Top-3)
              ↓
        注入 L1 上下文
              ↓
    ┌───────┴───────┐
    ↓               ↓
  消息 < 15      消息 ≥ 15
    ↓               ↓
  返回          触发 Reflection
                    ↓
              LLM 摘要 → L2 存储
                    ↓
              更新 L3 Profile
```

### 4.3 关键配置参数

| 参数 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `reflection_threshold` | 15 | 触发记忆压缩的消息数阈值 |
| `max_l1_messages` | 20 | L1 工作记忆最大轮数 |
| `l2_top_k` | 3 | L2 检索返回条数 |
| `memory_ttl_days` | 30 | L2 记忆过期时间 |

---

## 5. 自适应检索与负采样策略 (Adaptive Retrieval & Hard Negative Mining)

### 5.1 算法动机：解决“形似神异”的领域噪声
在知识库问答中，检索常面临 **“难负样本” (Hard Negatives)**：
*   **例子**：用户询问“2024 年某政策/产品/制度版本”，系统召回了“2023 年旧版本”。两者语义相近，但事实约束互斥。
*   **RecSys 类比**：类比推荐系统中的**多阶段漏斗模型**（召回 -> 粗排 -> 精排）。召回保证候选集，精排保证最终准确度。

### 5.2 详细流程：基于漏斗模型的自适应链路
我们设计一套 **Adaptive-RAG** 流程：

1.  **分级召回 (Multi-channel Recall)**：
    *   **向量召回**：捕捉语义意图。
    *   **关键词召回 (BM25)**：锁定特定标识符（如“API-001 / TERM-1001 / Section-3.2”）。
2.  **硬负样本过滤 (Hard Negative Filtering)**：
    *   引入一个 **Conflict Detector (冲突检测器)**：识别召回结果中是否存在相互矛盾的版本/约束/主张。
3.  **自适应精排 (Adaptive Reranking)**：
    *   根据问题复杂度决定 Rerank 深度。如果问题包含“对比”、“差异”、“最新”等关键词，自动增加 Reranker 的候选集数量（Top-20 提升至 Top-50）。

### 5.3 推荐算法类比：对比学习与负采样
*   **对比学习 (Contrastive Learning)**：在训练检索器时，不仅要让正样本靠近，更要通过 **Hard Negative Mining** 让容易混淆的负样本（如旧版本内容/相似但互斥条款）拉开间隔。
*   **多阶段过滤**：类比推荐系统的过滤逻辑（如黑名单、已读过滤），在此处转化为“版本一致性过滤”。

### 5.4 冲突检测器详细设计

#### 5.4.1 核心算法

```python
# src/tools/conflict_detector.py
class ConflictDetector:
    """
    硬负样本检测器
    核心思想：识别召回结果中的版本冲突、时间矛盾、数值冲突
    """
    
    def detect(self, documents: List[Document]) -> List[Conflict]:
        """
        检测文档列表中的冲突
        
        Returns:
            List[Conflict]: 冲突列表，每项包含：
                - doc_a, doc_b: 冲突的双方
                - type: CONTRADICTION / VERSION / TEMPORAL
                - score: 冲突置信度 (0-1)
        """
        pass
```

#### 5.4.2 冲突类型分类

| 类型 | 触发条件 | 示例 |
| :--- | :--- | :--- |
| **版本冲突** | 年份/版本号不一致 | "2024 版条款" vs "2023 版条款" |
| **时间矛盾** | 时间范围重叠但结论相反 | "有效期至2024-12-31" vs "有效期至2024-06-30" |
| **数值冲突** | 数值范围不兼容 | "阈值≤100" vs "阈值≤50" |

#### 5.4.3 实现策略

1. **模式匹配 (Rule-based)**
   - 正则提取年份、金额、时间等关键实体
   - 构建冲突判定规则库

2. **语义对比 (LLM-based)**
   - 使用 LLM 判断两段文本是否存在事实矛盾
   - Prompt: "判断以下两段文本/条款是否存在冲突，返回 JSON 格式"

3. **向量空间分析**
   - 计算两文档 embedding 的余弦相似度
   - 相似度极高但关键实体不同 → 硬负样本

#### 5.4.4 过滤策略

```python
def filter_hard_negatives(documents: List[Document]) -> List[Document]:
    """
    硬负样本过滤流程:
    1. 按语义聚类 (Cosine Similarity > 0.85)
    2. 每类只保留最新版本
    3. 移除时间矛盾的条目
    """
    pass
```

### 5.5 代码实现路径
*   （示例实现）实现 `AdaptiveRetriever`：负责多通道召回、冲突过滤与自适应 rerank。
*   （示例实现）实现 `ConflictDetector`：利用模式匹配或小模型检测检索碎片间的版本冲突。

### 5.6 在线链路：Adaptive-RAG 推理时序 (Serving Path)

1.  **Candidate Recall**
    - 向量召回 Top-K1（语义）
    - BM25/关键词召回 Top-K2（标识符/术语/章节号）
2.  **Hard Negative Filtering (Conflict Detector)**
    - 对候选做冲突检测，输出 `conflict_score` 与 `conflict_type`
    - 冲突样本不直接丢弃，而是进入“降权池”（避免误杀）
3.  **Adaptive Rerank**
    - 规则：根据 Query 类型/复杂度自适应调节 rerank 深度（Top-N）
    - rerank feature：相似度、版本一致性、时间距离、来源可信度
4.  **Context Packing**
    - 将 Top-N 文档按“同版本聚类 + 去重”后拼接，减少 token 噪声

### 5.7 训练视角：Hard Negative Mining 与对比学习构造

#### 5.7.1 难负样本构造
- **版本替换负样本**：同主题不同年份/版本（2024 vs 2023）
- **实体替换负样本**：同模板不同实体/参数（A vs B）
- **时间窗口负样本**：同条款不同有效期

#### 5.7.2 对比学习目标 (InfoNCE 风格)
设查询为 `q`，正样本为 `d+`，负样本集合为 `{d-}`：
$$\mathcal{L} = -\log \frac{\exp(sim(q, d^+)/\tau)}{\exp(sim(q, d^+)/\tau)+\sum_{d^-}\exp(sim(q, d^-)/\tau)}$$
其中负样本优先采样“冲突检测器判定为高冲突但高相似”的候选。

### 5.8 评测指标与消融 (Offline Metrics)

#### 5.8.1 检索/排序指标（RecSys 对齐）
- **Recall@K**：K 候选覆盖正确证据片段的比例
- **MRR@K**：首个正确片段的排名倒数
- **nDCG@K**：多相关性标注下的排序质量

#### 5.8.2 冲突过滤指标（Hard Negative 对齐）
- **Conflict Precision**：被判定冲突的候选中，真实冲突占比
- **Conflict Recall**：真实冲突中被检测出的比例
- **Version Consistency Rate**：最终上下文中版本一致的比例

#### 5.8.3 消融实验
- **w/o Conflict Detector**：不做冲突检测
- **w/o Adaptive Rerank**：固定 Top-N rerank
- **w/o BM25 Recall**：只用向量召回
- **w/o Context Packing**：不做聚类去重

---

## 6. 深入设计：多 Agent 协作博弈架构 (Multi-Agent Debate & Consensus)

### 6.1 算法动机：抑制单智能体的“自信幻觉”
单 Agent 容易在生成过程中为了维持语境连贯而编造细节。引入博弈机制是为了通过“红蓝对抗”实现事实对齐。

### 6.2 架构设计：Consensus Graph (共识图)
利用 **LangGraph** 构建以下拓扑结构：

1.  **Actor (Proposer)**：
    *   **目标**：最大化召回信息的利用率，生成完整方案。
    *   **RecSys 类比**：**Candidate Generator**。
2.  **Critic (Reviewer)**：
    *   **目标**：最小化事实错误（Precision-focused）。
    *   **RecSys 类比**：**Policy Evaluator / Guardrail**。
3.  **Refinement Loop**：
    *   Actor 生成回答 -> Critic 指出错误 -> Actor 根据反馈重写。

#### 6.2.1 LangGraph 拓扑结构

```python
# src/agents/debate_agent.py
from langgraph import StateGraph

def build_consensus_graph() -> StateGraph:
    """
    构建共识图:
    START -> Actor -> Critic -> [共识?] -> END
                              |
                           [分歧] -> Actor (重写)
    """
    graph = StateGraph(AgentState)
    
    # 节点定义
    graph.add_node("actor", actor_node)
    graph.add_node("critic", critic_node)
    graph.add_node("refine", refine_node)
    
    # 边定义
    graph.add_edge("START", "actor")
    graph.add_edge("actor", "critic")
    graph.add_conditional_edges(
        "critic",
        check_consensus,
        {"consensus": "END", "disagree": "actor"}
    )
    
    return graph.compile()
```

#### 6.2.2 角色定义

| Agent | System Prompt 摘要 | 职责 |
| :--- | :--- | :--- |
| **Actor** | "你是一个领域助手，目标是提供完整、准确的回答" | 生成完整答案，整合所有检索信息 |
| **Critic** | "你是一个严格的审计员，专门检查事实一致性与引用" | 验证事实一致性，标注错误 |
| **Domain Expert** | "你是领域专家" | 针对特定领域提供专业意见 |

### 6.3 算法创新：基于博弈论的权重动态分配

#### 6.3.1 MMoE 启发的 Expert 权重分配
 - **思路**：将不同角色 Agent 视为不同 Expert，由一个轻量“Gate”根据问题类型/风险等级分配权重。
 - **工程落点**：这里的“权重”可落地为：
   - 是否启用某角色参与
   - 是否进入 Critic 复核
   - 失败时是否触发重写

#### 6.3.2 Consensus Score 计算
 
 $$Consensus = \frac{1}{N^2} \sum_{i=1}^{N} \sum_{j=1}^{N} \text{sim}(e_i, e_j)$$
 
 其中 $e_i$ 是第 $i$ 个 Agent 输出的 embedding，$\text{sim}$ 是余弦相似度。
 
 **判定规则**：
 - `Consensus ≥ 0.95` → 达成共识，输出结果
 - `Consensus < 0.95` → 触发重写循环（最多 3 次）
 - 3 次后仍未共识 → 返回最高权重 Agent 的答案 + 标注分歧点

### 6.4 强化学习相关创新（收敛版）：反馈驱动的策略优化 (Feedback-driven Policy)

为了避免把 RL 扩展成与项目实现脱节的重型框架，我们将 RL 内容收敛为一条与当前代码能力强相关、且论文可叙述的创新点：

- **核心目标**：利用 QA 质检/反思流程与反馈信号，把“问题分类→检索策略→Top-K/Rerank 参数→是否触发反思重写”等决策做成可学习策略。
 - **RecSys 类比**：从静态策略路由升级为“带反馈的在线学习”（Contextual Bandit）+“偏好优化”（DPO/ODPO 思路）。

#### 6.4.1 Contextual Bandit：用于检索策略与参数自适应

将一次问答视为一次 bandit 轮次：

 - **Context**：问题类型（任务分类器）、用户角色、历史质检失败类型、会话长度。
- **Action**：选择 `vector/bm25/hybrid`、Top-K、是否启用 rerank、rerank top_n。
- **Reward**：质检通过/用户反馈（显式 like/dislike 或隐式采纳/追问减少），并加入 token/延迟惩罚。

#### 6.4.2 偏好优化（DPO/ODPO 思路）：用于回答风格与“是否重写”阈值

不引入重型在线 RL 训练，而是采用更易落地的偏好优化：

- **正样本**：质检通过 + 用户满意的回答/轨迹。
- **负样本**：质检失败/证据不足却强答/高成本低收益轨迹。
- **产物**：改进 QA 固定流程中“生成-质检-反思”的阈值与模板选择。

### 6.5 工程化实现要点 (Practical Considerations)

#### 6.5.1 Critic 的结构化输出
 Critic 不只给自然语言意见，要求输出结构化 JSON，便于自动化循环：
 - `verdict`: pass / fail
 - `issues`: [{type, span, rationale, severity}]
 - `missing_citations`: [doc_id...]
 - `rewrite_suggestions`: ["...", "..."]

#### 6.5.2 分歧聚合与回退策略

- **分歧聚合**：当多 Critic/Expert 分歧时，聚合成“争议点列表”，要求 Actor 在重写时逐条回应
- **回退策略**：
  - 达不到共识但成本已超限：输出最高权重 Agent 的答案，并附带“争议点+不确定性声明”
  - 检索证据不足：优先提示需要补充信息，而非编造

#### 6.5.3 成本控制

- 限制回合数：最多 3 次 refinement
- Token 预算：超过预算时切换到轻量 Critic（只做一致性检查）
- 触发式启用：仅在问题类型为“对比/最新/高风险”时启用多 Agent

### 6.6 相关研究（可联网补充，避免硬引用细节）

- **Agentic RAG Survey (2025)**：https://arxiv.org/abs/2501.09136
- **From Local to Global: GraphRAG (2024)**：https://arxiv.org/abs/2404.16130
- **Graph Retrieval-Augmented Generation: A Survey (2024)**：https://arxiv.org/abs/2408.08921
- **Retrieval-Augmented Generation with Graphs (GraphRAG) (2025)**：https://arxiv.org/abs/2501.00309
- **Microsoft GraphRAG (Docs/Toolkit)**：https://microsoft.github.io/graphrag/
- **GRAG: Graph Retrieval-Augmented Generation (2024)**：https://arxiv.org/abs/2405.16506
- **OG-RAG: Ontology-Grounded RAG (2024)**：https://arxiv.org/abs/2412.15235
- **RAPTOR (Tree-Organized Retrieval) (2024)**：https://arxiv.org/abs/2401.18059
- **Awesome-GraphRAG (Resource List)**：https://github.com/DEEP-PolyU/Awesome-GraphRAG
- **GraphRAG Benchmark (2025)**：https://github.com/GraphRAG-Bench/GraphRAG-Benchmark
- **ODPO (ACL Findings 2024)**：https://aclanthology.org/2024.findings-acl.592/
- **DPO（OpenReview）**：https://openreview.net/pdf?id=HPuSIXJaa9

---

## 7. 论文创新点总结

1.  **HMM (层次化记忆)**：DIN/DIEN 思想解决长程对话背景丢失。
2.  **Adaptive Ranking**：漏斗模型与对比学习思想解决领域难负样本识别。
3.  **Consensus Multi-Agent**：Actor-Critic 与 MMoE 思想解决 Agent 生成幻觉。
4.  **Feedback-driven Policy (Bandit + Preference)**：利用质检/用户反馈闭环，自适应优化检索策略与 QA 流程阈值。

---

## 8. 实验评估与消融设计 (Experiment & Ablation)

### 8.1 数据与标注
 
 - **Query 集合**：覆盖知识密集型问答的常见任务类型（解释/对比/故障排查/流程/综述/多跳）。
 - **文档集合**：包含多版本文档、术语定义、流程说明、API/规范/论文等。
 - **标注**：标注正确证据片段（ground truth evidence）、最终回答质量（ground truth answer），以及偏好对齐（偏好对/排序对）。
 
 **公开数据集如何接入本 Reg/RAG 系统（论文可复现口径）**：
 - **检索评测基准（IR-first）**：BEIR 系列数据集（每个任务自带 corpus + queries + qrels），可直接用于评测 `Adaptive Retrieval`/rerank/GraphRAG 等组件。
 - **开放域 QA（single-hop）**：Natural Questions (NQ), TriviaQA 等。构建语料库的常见做法：
   - 使用数据集提供的 Wikipedia 段落/证据作为 corpus；或
   - 统一用 Wikipedia dump 构建 corpus，并用数据集问题做 query。
 - **多跳 QA（multi-hop）**：HotpotQA / 2WikiMultiHopQA / MuSiQue 等，用于验证“多证据拼接 + 冲突过滤 + 图检索/多跳检索”的收益。
 - **长文/长上下文任务**：可选引入长文 QA/长上下文基准，用于验证压缩记忆与结构化索引（GraphRAG/RAPTOR）的增益。
 
 ### 8.2 评测维度
 
  - **检索质量（IR Metrics）**：Recall@K、MRR@K、nDCG@K、Precision@K。
  - **上下文质量（Context Metrics）**：
    - Context Precision：检索到的上下文中“真正有用证据”的比例
    - Context Recall：回答所需证据是否被召回（覆盖率）
    - 多跳覆盖率：多跳任务中每一跳关键证据的覆盖情况
  - **回答质量（Answer Metrics）**：
    - EM / F1（适用于开放域 QA）
    - ROUGE-L（适用于摘要/综述类问题）
    - 人工评分（准确/完整/可执行）
  - **事实一致性与可追溯性（Faithfulness / Groundedness）**：
    - Faithfulness / Groundedness：回答是否被检索证据支持
    - Citation Correctness：引用是否指向正确证据片段
    - 引用覆盖率：关键结论是否有引用支撑
  - **Agentic/工具调用评估（Agent Metrics）**：
    - Tool Success Rate：工具调用成功率
    - Invalid Tool Call Rate：无效/冗余工具调用率
    - 平均步数：平均工具调用步数（Path Length）与平均回合数
    - 成本与时延：Token/Latency/调用次数
  - **反馈策略表现（Preference/Feedback Metrics）**：
    - 质检通过率/用户反馈分
    - 偏好优化胜率（Win Rate vs Base Model）
    - 成本（Token/延迟）变化
 
 **开源评估框架（建议写入论文方法部分）**：
 - **RAGAS**：https://github.com/explodinggradients/ragas
   - 覆盖常见的 RAG 指标族：Answer Relevancy / Faithfulness / Context Precision / Context Recall 等（以 LLM-as-a-judge + 规则化输入输出为主）。

 #### 8.2.1 自动化评测流程（Offline Pipeline）
 
 目标：把“Reg/RAG/Agent”系统评估做成可重复、可对比、可统计检验的离线流水线。
 
 1. **准备数据与语料**
    - 选择数据集与任务类型（IR / single-hop QA / multi-hop QA / long-context）。
    - 构建或加载 corpus（chunks/text units），并固化版本（写入 `corpus_version`）。
    - 固化 query 集、gold answer、gold evidence/qrels（如果数据集提供）。
 
 2. **离线跑检索（Retriever / Reranker）**
    - 对每条 query 输出：Top-K 文档、每条文档分数、可选的路径/社区/图证据。
    - 生成 TREC 风格 run 文件（便于复用 IR 工具链）。
    - IR 指标评测工具建议：
      - BEIR：https://github.com/beir-cellar/beir
      - pytrec_eval：https://github.com/cvangysel/pytrec_eval
      - ir_measures：https://github.com/terrierteam/ir_measures
 
 3. **离线跑生成（Generator）**
    - 输入：query + top-k context（或 graph context / community summaries）。
    - 输出：answer + citations（doc_id + span/offset）+ 过程信息（可选：tool trace / route decisions）。
    - 记录随机种子/模型版本/prompt 版本（保证可复现实验）。
 
 4. **RAG 质量打分（RAGAS / LLM-as-a-judge）**
    - 用 RAGAS 对每条样本计算：Answer Relevancy / Faithfulness / Context Precision / Context Recall 等。
    - 输出 per-sample 分数与失败原因（便于 error analysis）。
    - RAGAS：https://github.com/explodinggradients/ragas
 
 5. **统计汇总（reporting）**
    - 对每个指标输出：均值、方差/标准差、分位数（P50/P90），并区分任务子集（single-hop vs multi-hop）。
    - 同时统计效率指标：平均 token、平均时延、平均工具调用次数/步数。
 
 6. **消融对比（ablation）**
    - 固定相同数据/相同 seed，逐项打开：`+HMM`、`+Adaptive Retrieval`、`+Multi-Agent`、`+Feedback Policy`。
    - 每次只改变一个因素，避免“多因素叠加”导致解释困难。
 
 7. **显著性检验（bootstrap / paired test）**
    - 使用 paired bootstrap：对 query 级别样本做有放回重采样，计算两系统指标差的置信区间。
    - 输出：95% CI、p-value（或差值 CI 是否跨 0），用于论文中“提升是否显著”。
    - 注意：同一条 query 在两个系统下必须成对出现（paired），否则检验不稳。
 
 ### 8.3 消融设置

- **Base**：滑动窗口 + 向量召回。
- **+ HMM**：加入 L2 记忆召回与反射压缩。
- **+ Adaptive Retrieval**：多通道召回 + 自适应 rerank。
- **+ Multi-Agent**：Actor-Critic 共识。
- **+ Feedback Policy**：加入 bandit/偏好优化，用反馈调策略路由与阈值。

### 8.4 预期结论（论文叙事）
 
 - HMM 提升长程一致性与跨窗口召回。
 - 冲突检测显著降低“形似神异”的错误引用。
 - Feedback Policy 在保证准确率不下降的前提下，降低平均成本（token/延迟）并提升质检通过率/用户满意度。

---
 
 ## 9. 后续探索方向（Future Work / 可与导师沟通）
 
 这部分不作为当前主线实现承诺，仅作为可探索的“fancy ideas”，便于后续与导师/老师讨论确定取舍。
 
 ### 9.1 图检索 / Graph RAG（结构化知识增强）
 - **动机**：很多知识密集任务本质是“实体-关系-约束-多跳依赖”的图结构；纯向量检索对全局结构问题、跨段落多跳链路往往不稳。
 - **方向**：从文本中抽取实体/关系构建图（知识图谱或文档图），通过图遍历/社区发现/路径召回生成候选证据，再与向量/BM25 混合，最后交给 rerank + 生成。
 - **RecSys 类比**：从“文本匹配召回”升级到“结构化特征增强的召回与排序”（Graph feature enhanced retrieval/ranking）。
 - **典型 pipeline（可迁移实现骨架）**：
   - 将语料切分为可引用的 TextUnits/Chunks
   - 抽取实体、关系、关键主张/断言，形成图索引
   - 对图做社区发现/层次聚类，并为社区生成自底向上摘要
   - 查询阶段区分 Local/Global 等模式：
     - Local：围绕实体邻域展开
     - Global：利用社区摘要回答“全局/综述类”问题
 - **可参考工作（2024-2025）**：
   - https://arxiv.org/abs/2404.16130
   - https://arxiv.org/abs/2408.08921
   - https://arxiv.org/abs/2501.00309
   - https://microsoft.github.io/graphrag/
   - https://github.com/DEEP-PolyU/Awesome-GraphRAG
   - https://github.com/GraphRAG-Bench/GraphRAG-Benchmark
 
 ### 9.2 Agent 路由的可解释性与可控性
 - **方向**：为“策略路由/工具选择/检索策略选择”的决策输出可解释原因（输入特征、证据缺口、风险/不确定性），并允许人工策略覆盖或注入约束（如强制检索、强制引用、强制两轮质检）。
 
 ### 9.3 工具调用轨迹的离线挖掘
 - **方向**：从高质量轨迹中挖掘“常见工具链模板/失败模式”（pattern mining），沉淀为可复用的 plan library，作为 prompt 或 policy 的先验。
 
 ---
 **文档版本**：v1.8-pruned
 **作者**：学硕算法研究小组 (Claude Assistant)
 **最后更新**：2026-01-27
