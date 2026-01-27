# 深入设计：基于 RecSys 思想的层次化记忆管理 (HMM)

## 1. 核心动机
在金融咨询场景中，用户的问题往往具有高度的上下文依赖性。传统的滑动窗口（Sliding Window）记忆机制存在两个致命缺陷：
1. **长程遗忘**：超过窗口限制的关键信息（如上周提到的业务前提）会被彻底丢弃。
2. **检索噪声**：简单的向量检索可能召回大量不相关的片段，导致模型推理偏离。

受推荐系统（RecSys）中 **DIN (Deep Interest Network)** 和 **DIEN (Deep Interest Evolution Network)** 的启发，我们将记忆建模为“用户兴趣序列”，通过 **Target Attention** 机制实现精准召回。

## 2. 层次化存储架构 (The Hierarchy)

| 层级 | 名称 | 存储介质 | 对应推荐概念 | 作用 |
| :--- | :--- | :--- | :--- | :--- |
| **L1** | 工作记忆 (Working Memory) | 内存 (LangGraph State) | 近期行为 (Short-term Sequence) | 维持当前对话的即时连贯性（最近 5-10 轮）。 |
| **L2** | 情景记忆 (Episodic Memory) | 向量数据库 (PGVector) | 历史兴趣 (Long-term Interest) | 存储对话碎片。通过 Attention 召回与当前 Query 语义相关的历史。 |
| **L3** | 语义画像 (Profile Memory) | 关系数据库 (SQL) | 用户画像 (User Profile) | 存储已确定的静态事实（如用户公司名、适用规则版本）。 |

## 3. 核心算法设计

### 3.1 记忆感知检索 (Attention-based Retrieval)
不再是简单的 Top-K 召回，而是引入注意力分数计算：
$$Score(q, m_i) = \text{softmax}(\frac{f_{align}(q, m_i)}{\sqrt{d}})$$
其中 $q$ 是当前查询，$m_i$ 是记忆片段，$f_{align}$ 是对齐函数（语义相似度）。

### 3.2 兴趣演化建模 (DIEN 启发)
引入时间衰减因子 $\lambda$。金融规则具有时效性，更近期的对话权重更高：
$$W_{final} = Score(q, m_i) \cdot e^{-\lambda \Delta t}$$

### 3.3 记忆压缩与触发机制
- **触发条件**：当 Working Memory 长度达到阈值（如 20 轮）时。
- **操作**：
    1. 使用 LLM 对最早的 5 轮对话进行 **Summarization**。
    2. 将摘要及原始片段向量化，存入 L2 (Episodic Memory)。
    3. 将提取出的静态事实（如：“我公司是做贷款业务的”）更新至 L3 (Profile Memory)。

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

### 5.1 算法动机：解决“形似神异”的金融噪声
在金融场景中，检索常面临 **“难负样本” (Hard Negatives)**：
*   **例子**：用户询问“2024年贷款准入规则”，系统召回了“2023年贷款准入规则”。两者向量距离极近，但事实逻辑完全互斥。
*   **RecSys 类比**：类比推荐系统中的**多阶段漏斗模型**（召回 -> 粗排 -> 精排）。召回保证候选集，精排保证最终准确度。

### 5.2 详细流程：基于漏斗模型的自适应链路
我们设计一套 **Adaptive-RAG** 流程：

1.  **分级召回 (Multi-channel Recall)**：
    *   **向量召回**：捕捉语义意图。
    *   **关键词召回 (BM25)**：锁定特定科目代码（如“1001 现金”）。
2.  **硬负样本过滤 (Hard Negative Filtering)**：
    *   引入一个 **Conflict Detector (冲突检测器)**：识别召回结果中是否存在相互矛盾的版本或规则。
3.  **自适应精排 (Adaptive Reranking)**：
    *   根据问题复杂度决定 Rerank 深度。如果问题包含“对比”、“差异”、“最新”等关键词，自动增加 Reranker 的候选集数量（Top-20 提升至 Top-50）。

### 5.3 推荐算法类比：对比学习与负采样
*   **对比学习 (Contrastive Learning)**：在训练检索器时，不仅要让正样本靠近，更要通过 **Hard Negative Mining** 让容易混淆的负样本（如旧版准则）原理。
*   **多阶段过滤**：类比推荐系统的过滤逻辑（如黑名单、已读过滤），在此处转化为“版本一致性过滤”。

### 5.4 冲突检测器详细设计

#### 5.4.1 核心算法

```python
# src/tools/conflict_detector.py
class ConflictDetector:
    """
    硬负样本检测器
    核心思想：识别召回结果中的版本冲突、时间矛盾、金额冲突
    """
    
    def detect(self, documents: List[Document]) -> List[Conflict]:
        """
        检测文档列表中的冲突
        
        Returns:
            List[Conflict]: 冲突列表，每项包含:
                - doc_a, doc_b: 冲突的双方
                - type: CONTRADICTION / VERSION / TEMPORAL
                - score: 冲突置信度 (0-1)
        """
        pass
```

#### 5.4.2 冲突类型分类

| 类型 | 触发条件 | 示例 |
| :--- | :--- | :--- |
| **版本冲突** | 年份/版本号不一致 | "2024年贷款准入规则" vs "2023年贷款准入规则" |
| **时间矛盾** | 时间范围重叠但结论相反 | "有效期至2024-12-31" vs "有效期至2024-06-30" |
| **金额冲突** | 数值范围不兼容 | "贷款额度≤100万" vs "贷款额度≤50万" |

#### 5.4.3 实现策略

1. **规则匹配 (Rule-based)**
   - 正则提取年份、金额、时间等关键实体
   - 构建冲突规则库

2. **语义对比 (LLM-based)**
   - 使用 LLM 判断两段文本是否存在事实矛盾
   - Prompt: "判断以下两段金融规则是否存在冲突，返回 JSON 格式"

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
*   **修改** `src/biz/rag_service.py`：实现 `AdaptiveRetriever` 类。
*   **新增** `src/tools/conflict_detector.py`：利用规则匹配或小模型检测检索碎片间的版本冲突。

### 5.6 在线链路：Adaptive-RAG 推理时序 (Serving Path)

1.  **Candidate Recall**
    - 向量召回 Top-K1（语义）
    - BM25/关键词召回 Top-K2（符号/科目/规则编号）
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
- **实体替换负样本**：同模板不同科目/参数（1001 vs 1002）
- **时间窗口负样本**：同规则不同有效期

#### 5.7.2 对比学习目标 (InfoNCE 风格)
设查询为 `q`，正样本为 `d+`，负样本集合为 `{d-}`：
$$\mathcal{L} = -\log \frac{\exp(sim(q, d^+)/\tau)}{\exp(sim(q, d^+)/\tau)+\sum_{d^-}\exp(sim(q, d^-)/\tau)}$$
其中负样本优先采样“冲突检测器判定为高冲突但高相似”的候选。

### 5.8 评测指标与消融 (Offline Metrics)

#### 5.8.1 检索/排序指标（RecSys 对齐）
- **Recall@K**：K 候选覆盖正确规则片段的比例
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
| **Actor** | "你是一个金融顾问，目标是提供完整、准确的回答" | 生成完整答案，整合所有检索信息 |
| **Critic** | "你是一个严格的审计员，专门检查金融规则的准确性" | 验证事实一致性，标注错误 |
| **Domain Expert** | "你是贷款/风控/会计领域的专家" | 针对特定领域提供专业意见 |

### 6.3 算法创新：基于博弈论的权重动态分配

#### 6.3.1 MMoE 启发的 Expert 权重分配

```python
class MultiExpertRouter:
    """
    根据任务类型动态分配 Agent 权重
    类似于 MMoE 中的 Gate 网络
    """
    
    def compute_weights(self, query: str) -> Dict[str, float]:
        """
        输入: 用户查询
        输出: 各 Expert 的权重分布
        
        示例:
        - 查询"贷款准入条件" -> {"product": 0.7, "tech": 0.2, "risk": 0.1}
        - 查询"科目余额表格式" -> {"accounting": 0.8, "product": 0.1, "tech": 0.1}
        """
        pass
```

#### 6.3.2 Consensus Score 计算

$$Consensus = \frac{1}{N^2} \sum_{i=1}^{N} \sum_{j=1}^{N} \text{sim}(e_i, e_j)$$

其中 $e_i$ 是第 $i$ 个 Agent 输出的 embedding，$\text{sim}$ 是余弦相似度。

**判定规则**：
- `Consensus ≥ 0.95` → 达成共识，输出结果
- `Consensus < 0.95` → 触发重写循环（最多 3 次）
- 3 次后仍未共识 → 返回最高权重 Agent 的答案 + 标注分歧点

### 6.4 强化学习赋能：协作策略的自主进化 (RL-based Optimization)

#### 6.4.1 建模为马尔可夫决策过程 (MDP)
我们将多 Agent 的协作博弈建模为一个 MDP 过程，通过强化学习优化 Agent 的决策质量：
- **State (S)**：当前对话上下文、检索到的证据片段、其他 Agent 的历史回复。
- **Action (A)**：
    - **Actor**：生成回答、选择工具调用（类似于推荐中的下一跳预测）、决定是否重写。
    - **Critic**：给出评估得分、标注错误、决定是否通过（Termination Action）。
- **Reward (R)**：
    - **R_fact**：基于事实对齐的奖励（由专家标注或 RAG 指标自动计算）。
    - **R_cons**：多 Agent 共识得分。
    - **R_eff**：效率惩罚（Token 消耗与回合数惩罚）。

#### 6.4.2 RecSys 类比：从静态排序到动态策略 (Policy Evolution)
- **从 Ranking 到 Policy**：传统的 RAG 类似于静态的推荐排序（Top-K），而引入多 Agent 和工具调用后，系统转变为**序列决策 (Sequential Recommendation)**。
- **工具调用即探索 (Exploration)**：Agent 选择调用不同的金融工具（如查利率、查规则、查历史）类似于推荐算法中的 **Explore & Exploit**，旨在通过最小的交互代价获取最高价值的信息。

#### 6.4.3 离线强化学习 (Offline RL) 与 DPO 调优
利用历史对话数据，通过 **DPO (Direct Preference Optimization)** 训练 Actor 模型：
- **正样本**：Critic 判定为 "Pass" 且共识度高、工具调用链路精简的路径。
- **负样本**：Critic 判定为 "Fail"、存在幻觉或无效工具调用的路径。

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
- 触发式启用：仅在问题类型为“规则对比/最新/高风险”时启用多 Agent

### 6.6 强化学习与工具调用的深度融合 (RL & Tool-Use)
- **多步推理作为路径搜索**：在复杂的金融咨询中，工具调用（Tool-use）不再是单次操作，而是类似于推荐系统中的**路径发现（Path Finding）**。Agent 需要在工具空间中搜索最优的证据链条。
- **Contextual Bandits 策略**：在多工具选择场景下，引入 **Contextual Multi-Armed Bandits (CMAB)** 模型。系统基于当前上下文特征（User Persona, Query Intent, History State）实时预估每个工具的“预期收益”（即该工具能提供的证据增益），动态调整调用优先级。
- **用户反馈闭环 (RLHF)**：
    - **显式反馈**：用户对回答的点赞/踩，直接作为 RL 训练的最终 Reward。
    - **隐式反馈**：用户是否采纳了 Agent 建议的后续步骤（类似于推荐系统中的点击率 CTR）。
- **Reward Shaping**：
  - **路径长度惩罚**：鼓励 Agent 用最少的工具调用步数解决问题。
  - **信息增益奖励**：每次工具调用后，如果新获取的信息能显著改变共识得分或减少幻觉，给予正向奖励。

### 6.7 论文切入点
*   *“基于强化学习的多 Agent 协作与工具调用路径优化研究”*。
*   *“从静态检索到动态策略：金融场景下的 RL-Agent 演进范式”*。

---

## 7. 论文创新点总结
1.  **HMM (层次化记忆)**：DIN/DIEN 思想解决长程对话背景丢失。
2.  **Adaptive Ranking**：漏斗模型与对比学习思想解决金融难负样本识别。
3.  **Consensus Multi-Agent**：Actor-Critic 与 MMoE 思想解决 Agent 生成幻觉。
4.  **Sequential Policy Optimization**：将工具调用建模为 MDP，利用 RL 提升协作效率与路径质量。

---

## 8. 实验评估与消融设计 (Experiment & Ablation)

### 8.1 数据与标注
- **Query 集合**：覆盖金融咨询常见意图（规则解释/对比/故障排查/流程）。
- **文档集合**：包含多版本规则文本、科目说明、流程文档。
- **标注**：标注最优工具调用路径、正确证据片段、最终回答质量、以及偏好对齐（DPO 训练）。

### 8.2 评测维度
- **检索质量**：Recall@K、MRR@K、nDCG@K。
- **回答质量**：Answer-F1、人工评分（准确/完整/可执行）。
- **协作效率**：平均工具调用步数（Path Length）、平均对话回合数、Token 消耗。
- **RL 表现**：Reward 分布随训练轮数的变化、DPO 胜率（Win Rate vs Base Model）。
- **可信度**：引用覆盖率、Version Consistency Rate。

### 8.3 消融设置
- **Base**：滑动窗口 + 向量召回。
- **+ HMM**：加入 L2 记忆召回与反射压缩。
- **+ Adaptive Retrieval**：多通道召回 + 自适应 rerank。
- **+ Multi-Agent**：Actor-Critic 共识。
- **+ RL Optimization**：加入策略优化与工具调用路径选择。

### 8.4 预期结论（论文叙事）
- HMM 提升长程一致性与跨窗口召回。
- 冲突检测显著降低“形似神异”的错误引用。
- RL 优化显著缩短了工具调用路径（提升效率），同时通过 Reward Shaping 减少了冗余信息。
- 多 Agent 共识在高风险问题上提供了更坚实的准确度保障。

### 8.5 环境模拟器设计 (Environment Simulator for RL)
为了高效训练 RL 策略，我们设计了一套**金融咨询模拟环境**：
- **User Simulator**：基于历史数据分布，模拟不同偏好和背景的用户（如“保守型投资者”、“技术导向型会计”）。
- **Knowledge Environment**：模拟知识库的动态更新，包括注入相互冲突的规则，测试 Agent 的冲突检测能力。
- **Reward Engine**：自动计算 RAG 指标（Faithfulness, Answer Relevance）并结合模拟用户的反馈。

---
**文档版本**：v1.6
**作者**：学硕算法研究小组 (Claude Assistant)
**最后更新**：2026-01-27
