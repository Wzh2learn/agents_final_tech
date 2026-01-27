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

### 6.4 论文切入点
*   *“基于对抗性博弈的金融知识库问答可信度增强研究”*。
*   *“多任务专家网络架构下的跨角色金融 Agent 协作范式”*。

---

## 7. 论文创新点总结
1.  **HMM (层次化记忆)**：DIN/DIEN 思想解决长程对话背景丢失。
2.  **Adaptive Ranking**：漏斗模型与对比学习思想解决金融难负样本识别。
3.  **Consensus Multi-Agent**：Actor-Critic 与 MMoE 思想解决 Agent 生成幻觉。

---
**文档版本**：v1.3
**作者**：学硕算法研究小组 (Claude Assistant)
**最后更新**：2026-01-27
