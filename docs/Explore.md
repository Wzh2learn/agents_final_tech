# JinRongAgents 架构探索与技术调研

## 1. 业务架构图

```mermaid
graph TB
    subgraph 用户层
        A[产品经理] --> B[Web界面]
        C[技术开发] --> B
        D[销售运营] --> B
        E[估值会计] --> B
    end

    subgraph 核心业务流
        B --> F{路由分发}
        F -->|文档上传| G[文档处理流程]
        F -->|问题查询| H[智能问答流程]
        F -->|反馈处理| I[反馈处理流程]
        F -->|协作需求| J[实时协作流程]

        G --> G1[文档解析]
        G1 --> G2[规则提取]
        G2 --> G3[规则校验]
        G3 --> G4[差异生成]
        G4 --> G5[人工确认]
        G5 --> G6[入库持久化]

        H --> H1[问题分类]
        H1 --> H2[智能检索]
        H2 --> H3[生成回答]
        H3 --> H4[质量检测]
        H4 --> H5{质检评分}
        H5 -->|≥85分| H6[直接回复]
        H5 -->|<85分| H7[反思优化]
        H7 --> H6

        I --> I1[反馈检测]
        I1 --> I2[反馈分类]
        I2 --> I3[通知相关方]
        I3 --> I4[记录存档]

        J --> J1[会话创建]
        J1 --> J2[角色设置]
        J2 --> J3[消息同步]
        J3 --> J4[历史存储]
    end

    subgraph 知识库管理
        K[文档上传] --> L[向量化]
        L --> M[PGVector存储]
        N[统计分析] --> M
        O[文档导出] --> M
        P[答案溯源] --> M
    end

    G6 --> M
    H2 --> M
    I4 --> Q[SQLite]
    J4 --> Q

    style A fill:#e1f5ff
    style C fill:#e1f5ff
    style D fill:#e1f5ff
    style E fill:#e1f5ff
    style G fill:#fff3cd
    style H fill:#d4edda
    style I fill:#f8d7da
    style J fill:#d1ecf1
```

### 业务价值主张

| 角色 | 核心需求 | 系统支持 |
|------|---------|---------|
| 产品经理 | 业务流程和用户体验 | 从产品角度解释建账规则，关注业务流程和用户痛点 |
| 技术开发 | 技术实现和系统架构 | 从技术角度解释建账规则，关注技术链路和数据库交互 |
| 销售运营 | 客户价值和市场竞争 | 从商业角度解释建账规则，关注客户价值和市场竞争力 |
| 估值会计 | 自动化建账操作 | 替代手动操作，一键完成估值前的数据准备 |

---

## 2. 技术架构图

```mermaid
graph TB
    subgraph 表示层 [Web Layer]
        A1[FastAPI Routes]
        A2[WebSocket Server]
        A3[Static Files]
        A4[Jinja2 Templates]

        A1 --> A11[/api/chat - 聊天API]
        A1 --> A12[/api/knowledge - 知识库API]
        A1 --> A13[/api/chat/sessions - 会话管理]
        A2 --> A21[实时协作通信]
    end

    subgraph 业务逻辑层 [Business Layer]
        B1[AgentService]
        B2[RAGService]

        B1 --> B11[会话管理]
        B1 --> B12[消息处理]
        B1 --> B13[流式输出]

        B2 --> B21[智能检索]
        B2 --> B22[文档入库]
        B2 --> B23[答案溯源]
        B2 --> B24[方法对比]
    end

    subgraph Agent层 [Agent Layer]
        C1[LangGraph ReAct Agent]
        C2[滑动窗口记忆 Max 40]
        C3[系统提示词注入]

        C1 --> C11[角色识别路由]
        C1 --> C12[工具调度]
        C1 --> C13[推理循环]
    end

    subgraph 工具层 [Tools Layer - 17个工具]
        D1[文档工具]
        D2[QA工具]
        D3[检索工具]
        D4[存储工具]
        D5[反馈工具]

        D1 --> D11[document_processor - 规则提取]
        D1 --> D12[validate_rules - 规则校验]

        D2 --> D21[qa_agent - 知识库问答]
        D2 --> D22[classify_query - 查询分类]

        D3 --> D31[smart_retrieve - 智能检索]
        D3 --> D32[batch_retrieve - 批量检索]
        D3 --> D33[vector_store - 向量检索]
        D3 --> D34[bm25_retriever - 全文检索]
        D3 --> D35[hybrid_retriever - 混合检索]
        D3 --> D36[reranker_tool - 重排序]

        D4 --> D41[write_to_file - 本地写入]
        D4 --> D42[write_to_storage - S3写入]
        D4 --> D43[save_rule_to_knowledge - 规则持久化]

        D5 --> D51[feedback_handler - 反馈处理]
        D5 --> D52[generate_summary_report - 报告生成]
    end

    subgraph 数据访问层 [Storage Layer]
        E1[Provider ACL]
        E2[数据库层]
        E3[内存层]
        E4[对象存储]

        E1 --> E11[Schema验证]
        E1 --> E12[访问控制]

        E2 --> E21[PostgreSQL + PGVector]
        E2 --> E22[SQLite - 协作会话]
        E2 --> E23[DocumentManager - CRUD]

        E3 --> E31[LangGraph Checkpointer]
        E3 --> E32[Cache - TTL缓存]

        E4 --> E41[S3 - 原始文档]
        E4 --> E42[LocalFile备份]
    end

    subgraph 外部依赖
        F1[SiliconFlow API]
        F2[DeepSeek-V3.2]
        F3[Qwen3-Embedding]
        F4[Qwen3-Reranker]

        F1 --> F2
        F1 --> F3
        F1 --> F4
    end

    A1 --> B1
    A1 --> B2
    A2 --> E22

    B1 --> C1
    B2 --> D3

    C1 --> D1
    C1 --> D2
    C1 --> D3
    C1 --> D4
    C1 --> D5

    D1 --> E1
    D2 --> E1
    D3 --> E1
    D4 --> E1
    D5 --> E22

    E1 --> E2
    E1 --> E3
    E1 --> E4

    C1 --> F1
    D2 --> F1
    D3 --> F1

    style 表示层 fill:#e3f2fd
    style 业务逻辑层 fill:#f3e5f5
    style Agent层 fill:#fff3e0
    style 工具层 fill:#e8f5e9
    style 数据访问层 fill:#fce4ec
```

### 关键技术特性

#### 1. 分层架构设计 (Layered Architecture)

- **Web层**：FastAPI异步框架，支持SSE流式响应和WebSocket实时通信
- **业务层**：单例模式服务，封装核心业务逻辑
- **Agent层**：LangGraph ReAct范式，自主工具调用和推理
- **工具层**：17个专用工具，涵盖文档、检索、存储、QA全流程
- **存储层**：ACL访问控制，多数据源适配（PostgreSQL、SQLite、S3）

#### 2. RAG智能检索策略

```
用户查询
    ↓
问题分类器 (7种类型)
    ├─ concept: 概念解释
    ├─ process: 流程说明
    ├─ compare: 对比分析
    ├─ factual: 事实查询
    ├─ rule: 规则查询
    ├─ troubleshooting: 故障排查
    └─ general: 通用问题
    ↓
策略选择器
    ├─ vector: 向量检索 (语义相似)
    ├─ bm25: 全文检索 (关键词匹配)
    └─ hybrid: 混合检索 (RRF融合)
    ↓
Rerank重排序 (Qwen3-Reranker)
    ↓
Top-K结果返回
```

#### 3. 数据流转链路

**聊天请求流**：
```
User → FastAPI /api/chat
    → AgentService.stream_chat()
    → LangGraph Agent.astream()
    → Tool Execution (qa_agent/smart_retrieve)
    → PGVector查询
    → LLM生成
    → SSE流式返回
```

**文档入库流**：
```
上传文件 → FastAPI /api/knowledge/upload
    → RAGService.ingest_file()
    → 文档加载 (PDF/DOCX/TXT)
    → 文本分割 (Recursive/Markdown/Hierarchical)
    → 原始文件存储 (S3/LocalFile)
    → 向量化 (Qwen3-Embedding)
    → PGVector入库
```

#### 4. 会话与记忆管理

- **滑动窗口记忆**：仅保留最近40条消息（20轮对话），避免上下文溢出
- **CheckPointer持久化**：LangGraph会话状态存储，支持断点续传
- **角色系统提示词**：首次对话注入SystemMessage，定制化回答风格

---

## 3. 关键配置与环境变量

### 必需环境变量 (.env)

| 变量名 | 用途 | 示例值 |
|--------|-----|--------|
| `SILICONFLOW_API_KEY` | LLM/Embedding API密钥 | `sk-xxx` |
| `PGDATABASE_URL` | PostgreSQL连接串 | `postgresql://user:pass@host:5432/db` |
| `JWT_SECRET_KEY` | JWT令牌签名密钥 | `your-secret-key` |
| `CORS_ORIGINS` | 允许的CORS源（逗号分隔） | `http://localhost:3000,https://app.com` |

### 核心配置文件

- **config/app_config.json**：数据库、向量存储、RAG策略配置
- **config/agent_llm_config.json**：LLM模型、温度、超时、系统提示词

---

## 4. Manus AI 技术调研与对比

### 4.1 Manus AI 核心架构

根据最新调研（2026年），Manus AI的架构包含以下关键组件：

#### 1) 三大核心组件

```mermaid
graph LR
    A[Planner 规划器] --> B[Memory 记忆系统]
    B --> C[Tool Execution 工具执行]
    C --> A

    D[Foundation Models] --> A
    D --> B
    D --> C

    E[Sandbox VM] --> C

    style A fill:#ffeb3b
    style B fill:#4caf50
    style C fill:#2196f3
    style D fill:#9c27b0
    style E fill:#ff5722
```

- **Planner**：任务规划器，负责将用户请求分解为可执行步骤
- **Memory**：记忆系统，保存上下文和中间状态
- **Tool Execution Loop**：工具执行循环，调用各类工具完成任务

#### 2) 沙盒基础设施

- **独立云VM**：每个用户任务分配独立的虚拟机
- **完整环境**：包含网络、文件系统、浏览器、开发工具
- **Zero Trust架构**：用户和AI拥有root权限，沙盒内完全自治
- **隔离执行**：不同任务间完全隔离，确保安全性

#### 3) 多模态能力

- 支持输入/输出：文本、图像、音频、代码
- 跨模态任务处理能力
- 上下文理解和跨格式转换

#### 4) 最新版本特性 (Manus 1.6, 2026)

- **Max Performance**：核心Agent架构升级，处理复杂任务需更少监督
- **高级规划能力**：显著提升的规划和问题解决能力
- **Meta收购整合**：2025年底Meta收购，技术深度整合

### 4.2 Manus vs JinRongAgents 对比分析

| 维度 | Manus AI | JinRongAgents |
|------|----------|--------------|
| **架构模式** | Planner + Memory + Tool Loop | LangGraph ReAct Agent |
| **运行环境** | 独立云VM沙盒（完整OS环境） | Python进程（FastAPI服务） |
| **隔离级别** | VM级隔离，root权限 | 进程级隔离，受限环境 |
| **工具系统** | 通用工具集（浏览器、终端、代码执行） | 领域专用工具（17个金融业务工具） |
| **记忆系统** | 长期记忆 + 短期记忆 | 滑动窗口（40条消息） + CheckPointer |
| **多模态** | ✅ 文本/图像/音频/代码全支持 | ⚠️ 主要支持文本，文件上传限PDF/DOCX/TXT |
| **任务类型** | 通用自主任务（编程、研究、设计） | 垂直领域任务（金融建账规则处理） |
| **交互方式** | 异步任务执行，长时间运行 | 同步/流式聊天，快速响应 |
| **代码执行** | ✅ 完整代码执行环境 | ❌ 无代码执行能力 |
| **安全模型** | Zero Trust（沙盒内完全自治） | ACL访问控制（基于角色权限） |
| **可扩展性** | 插件式工具扩展 | 装饰器式工具注册 (@tool) |
| **部署模式** | 云端SaaS（Meta基础设施） | 私有化部署（Docker/本地） |

### 4.3 架构差异深度分析

#### 执行模式对比

**Manus执行流**：
```
用户请求
    → Planner分解任务
    → 分配独立VM
    → 串行执行子任务（可包含代码运行、Web交互）
    → Memory记录中间状态
    → 聚合结果返回
```

**JinRongAgents执行流**：
```
用户请求
    → Agent识别意图
    → 调用工具（smart_retrieve/qa_agent/document_processor）
    → PGVector检索/LLM生成
    → 流式返回结果
```

#### 设计哲学差异

| 设计维度 | Manus | JinRongAgents |
|---------|-------|--------------|
| **目标定位** | 通用自主Agent平台 | 垂直领域专家系统 |
| **复杂度** | 高（需管理VM生命周期） | 中（标准Web应用） |
| **响应速度** | 慢（VM启动 + 任务执行） | 快（毫秒级API响应） |
| **资源消耗** | 高（每任务一个VM） | 低（共享进程资源） |
| **适用场景** | 复杂、长时间、需代码执行的任务 | 快速查询、知识问答、文档处理 |

### 4.4 可借鉴的Manus设计思想

#### 1. 增强的规划能力

**当前局限**：JinRongAgents的Agent是ReAct模式，单步推理 + 工具调用，缺乏长期任务规划。

**改进方向**：引入Plan-Execute范式
```python
# 伪代码示例
def enhanced_agent():
    plan = planner.decompose_task(user_query)  # 任务分解
    for step in plan.steps:
        result = executor.execute(step)
        memory.save(step, result)
    return aggregator.combine(memory.get_all())
```

#### 2. 更灵活的记忆系统

**当前局限**：滑动窗口简单粗暴，可能丢失关键上下文。

**改进方向**：分层记忆架构
- **工作记忆**（短期）：当前对话的最近N轮
- **情景记忆**（中期）：当前会话的关键信息摘要
- **语义记忆**（长期）：跨会话的领域知识图谱

#### 3. 沙盒化工具执行

**当前局限**：工具直接访问文件系统和数据库，存在安全风险。

**改进方向**：轻量级沙盒隔离
- 使用Docker容器隔离工具执行环境
- 限制文件系统访问范围（chroot）
- 网络访问白名单机制

---

## 5. 技术债务与优化建议

### 5.1 当前系统的优势

✅ **分层清晰**：Web → Biz → Agent → Tools → Storage，职责分明
✅ **RAG智能**：7种问题类型 + 3种检索策略 + Rerank优化
✅ **流式响应**：SSE流式输出，用户体验好
✅ **工具丰富**：17个专用工具覆盖核心业务场景
✅ **配置驱动**：角色/模型/策略均可配置，灵活度高

### 5.2 待优化方向

⚠️ **记忆管理**：滑动窗口可能丢失关键信息，建议引入摘要机制
⚠️ **并发处理**：单worker模式，高并发场景需多进程部署
⚠️ **错误恢复**：缺少断点续传和任务重试机制
⚠️ **可观测性**：缺少链路追踪（Trace）和性能指标（Metrics）
⚠️ **测试覆盖**：单元测试和集成测试覆盖不足

### 5.3 Manus启发的未来演进路线

#### Phase 1: 增强规划能力 (近期)
- 实现Plan-Execute模式的Agent变体
- 支持多步骤任务的自动分解和执行

#### Phase 2: 记忆系统升级 (中期)
- 引入分层记忆（工作/情景/语义）
- 支持跨会话的知识图谱构建

#### Phase 3: 沙盒化执行 (远期)
- 基于Docker的轻量级沙盒
- 支持安全的代码执行工具

---

## 6. 数据流示例

### 6.1 完整QA流程追踪

```
[用户] 提问："辅助建账的首笔划款规则是什么？"
    ↓
[FastAPI] POST /api/chat
    ↓
[AgentService] stream_chat(message, conversation_id, role="product_manager")
    ↓
[LangGraph Agent]
    - 加载历史：CheckPointer.get(thread_id)
    - 注入SystemPrompt（首次对话）
    - 调用Agent.astream()
    ↓
[Agent推理]
    - 识别意图：需要查询知识库
    - 选择工具：smart_retrieve
    ↓
[smart_retrieve工具]
    - 问题分类：classify_question_type() → "rule"
    - 策略选择：get_retrieval_strategy("rule") → "hybrid"
    - 执行检索：hybrid_retrieve(query, top_k=15)
    ↓
[HybridRetriever]
    - Vector检索：PGVector.similarity_search(query)
    - BM25检索：BM25Retriever.retrieve(query)
    - RRF融合：reciprocal_rank_fusion(vector_results, bm25_results)
    ↓
[Reranker]
    - 调用Qwen3-Reranker重排序
    - 返回Top-5最相关结果
    ↓
[Agent推理]
    - 基于检索结果生成回答
    - 调用DeepSeek-V3.2生成
    ↓
[AgentService]
    - 流式yield每个chunk
    - 保存消息到CheckPointer
    ↓
[FastAPI]
    - SSE流式响应：data: {"content": "根据规则...", "done": false}
    - 最终消息：data: {"content": "", "done": true}
    ↓
[用户] 收到完整回答
```

### 6.2 文档处理流程追踪

```
[用户] 上传：building_rules_v3.pdf (5MB)
    ↓
[FastAPI] POST /api/knowledge/upload (multipart/form-data)
    ↓
[知识库路由] knowledge.py::upload_document()
    - 文件验证：validate_upload(filename, content)
    - 临时存储：tempfile.NamedTemporaryFile()
    ↓
[RAGService] ingest_file(tmp_path, metadata, use_hierarchical=False)
    ↓
[文档加载] load_document.invoke(file_path)
    - 识别文件类型：.pdf
    - 调用PyPDFLoader解析
    - 返回原始文本
    ↓
[文本分割] split_text_recursive.invoke(text)
    - RecursiveCharacterTextSplitter
    - chunk_size=1000, chunk_overlap=200
    - 返回：150个文本块
    ↓
[原始文件存储] provider.ingest_document()
    - S3上传：s3://bucket/docs/building_rules_v3.pdf
    - 返回object_key
    ↓
[向量化] get_vector_store().add_documents()
    - 批量调用Qwen3-Embedding
    - 生成1536维向量
    - PGVector批量插入：langchain_pg_embedding表
    - 关联metadata：{source, object_key, chunk_index}
    ↓
[缓存失效] cache.delete("kb_stats:*")
    ↓
[响应] {"status": "success", "chunks_count": 150}
    ↓
[用户] 看到上传成功提示
```

---

## 7. 参考资料

### JinRongAgents相关

- **代码仓库**：本地项目 `agents_final_tech/`
- **文档**：
  - `docs/API_REFERENCE.md` - API参考文档
  - `docs/DEVELOPER_GUIDE.md` - 开发者指南
  - `docs/TOOLS_USAGE.md` - 工具使用说明
  - `CLAUDE.md` - 项目概览与约定

### Manus AI相关

- [From Mind to Machine: The Rise of Manus AI as a Fully Autonomous Digital Agent (arXiv)](https://arxiv.org/html/2505.02024v1)
- [In-depth technical investigation into the Manus AI agent (GitHub Gist)](https://gist.github.com/renschni/4fbc70b31bad8dd57f3370239dccd58f)
- [Manus (AI agent) - Wikipedia](https://en.wikipedia.org/wiki/Manus_(AI_agent))
- [Meta's Manus AI Reveals Sandbox Architecture (Bitcoin Ethereum News)](https://bitcoinethereumnews.com/tech/metas-manus-ai-reveals-sandbox-architecture-behind-autonomous-agent-tasks/)
- [Manus Official Website](https://manus.im/)
- [Context Engineering for AI Agents: Lessons from Building Manus](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)
- [Introducing Manus 1.6: Max Performance, Mobile Dev, and Design View](https://manus.im/blog/manus-max-release)
- [OpenManus - Open-source Framework](https://openmanus.github.io/)

### 技术框架参考

- **LangChain**: [Python文档](https://python.langchain.com/)
- **LangGraph**: [官方文档](https://langchain-ai.github.io/langgraph/)
- **FastAPI**: [官方文档](https://fastapi.tiangolo.com/)
- **PGVector**: [GitHub仓库](https://github.com/pgvector/pgvector)

---

**文档版本**：v1.0
**创建日期**：2026-01-19
**作者**：Claude Sonnet 4.5
**最后更新**：2026-01-19

## 8. 学硕算法创新方案：基于推荐算法思想的深度演进

针对垂直领域金融 Agent 的业务特性，结合推荐系统（RecSys）的前沿算法思想，提出以下三个深度创新方向：

### 8.1 层次化长期记忆管理 (HMM)
- **RecSys 类比**：类比 DIN/DIEN 中的用户长短期兴趣序列建模。
- **核心逻辑**：将记忆分为 **Working Memory** (滑动窗口)、**Episodic Memory** (向量化检索) 和 **Profile Memory** (语义压缩)。
- **算法创新**：引入 **Target Attention** 机制。当新 Query 进入时，利用 Attention 计算 Query 与历史记忆碎片的相似度权重，动态聚合生成背景上下文向量，而非简单的最近对话拼接。
- **论文切入点**：*“基于兴趣演化建模的金融 Agent 长对话记忆增强机制研究”*。

### 8.2 自适应检索与负采样策略
- **RecSys 类比**：类比推荐系统中的 **多阶段排序 (Recall -> Ranking)** 与 **硬负样本采样 (Hard Negative Mining)**。
- **核心逻辑**：将 RAG 过程建模为“召回-粗排-精排”链路。引入“难负样本发现”机制，通过判别器识别“语义相关但事实错误”的干扰项。
- **算法创新**：自适应检索深度。根据问题复杂度自动调节检索范围和推理步数（Adaptive Step），实现计算代价与准确率的平衡。
- **论文切入点**：*“面向复杂金融规则的自适应检索与鲁棒重排序算法优化”*。

### 8.3 多 Agent 协作博弈架构
- **RecSys 类比**：类比 **Multi-task Learning (MMoE)** 或 **Actor-Critic** 机制。
- **核心逻辑**：构建两个对立角色：**Proposer (回答生成者)** 和 **Reviewer (合规审计者)**。
- **算法创新**：引入 **博弈论下的共识机制**。通过两个 Agent 针对 RAG 检索到的内容进行“辩论 (Debate)”，消除单一模型产生的幻觉。
- **论文切入点**：*“基于博弈论的多智能体金融合规性生成与自动化审校框架”*。



金融大模型助手：基于推荐算法思想的深度创新方案
1. 层次化长期记忆管理 (Analogy: DIN/DIEN 序列建模)
核心思路：将 Agent 的记忆管理看作推荐系统中的用户兴趣演化。

RecSys 类比：
短期记忆：Session-based 行为（最近 20 轮对话），类似当前点击流。
长期记忆：用户长期画像（历史 Session 的摘要），类似 User Profile。
Attention 机制：模拟 DIN (Deep Interest Network) 的 Target Attention。当新问题（Query）进来时，不只是看最近几句话，而是通过 Attention 计算 Query 与历史所有“记忆碎片”的相关性权重，聚合生成“背景向量”。
研究价值：解决长对话下的“信息遗忘”和“干扰噪声”问题。
代码切入点：
修改 src/storage/memory/memory_saver.py，增加一个 MemorySummarizer 模块。
在 src/agents/agent.py 的 AgentState 中，除了 messages，引入一个 long_term_context 字段，通过语义相似度（Attention）从历史数据库中召回。
2. 自适应检索与负采样 (Analogy: Multi-stage Ranking & Hard Negative)
核心思路：将 RAG 的检索过程看作推荐系统的 召回(Recall) -> 粗排(Pre-ranking) -> 精排(Ranking) 链路。

RecSys 类比：
负采样优化：在 RAG 中，很多检索结果是“看起来相关但事实错误”的噪声。这对应推荐中的 Hard Negative。可以引入一个“难负样本发现”机制，训练或 Prompt 指导模型识别那些极具误导性的金融条目。
自适应分级检索：类似推荐中的 多阶段策略。简单问题直接向量检索（类比快路排序）；复杂问题触发混合检索+多步推理（类比全精排）。
研究价值：通过“计算代价”与“回答质量”的权衡（Adaptive Retrieval），提升系统的灵效性。
代码切入点：
深挖 src/tools/question_classifier.py，将其从简单的分类器升级为“决策引擎”。
在 src/biz/rag_service.py 中引入类似 Rerank (精排) 的逻辑，并根据阈值决定是否需要“扩召回”。
3. 多 Agent 对抗与共识机制 (Analogy: Actor-Critic / Ensemble)
核心思路：将复杂决策任务看作多个弱分类器的 Ensemble 或 博弈论下的纳什均衡。

RecSys 类比：
类似 Multi-task Learning (MMoE) 或 Actor-Critic。一个智能体负责“回答”（Actor），另一个智能体负责“合规性审计/挑错”（Critic）。
通过两个 Persona 对立的 Agent 针对 RAG 检索到的内容进行“辩论”，消除单一模型产生的幻觉。
研究价值：在金融、法律等高严肃领域，这种“审校”机制是论文的巨大加分项。
代码切入点：
在 src/agents/agent.py 中，使用 LangGraph 重新定义拓扑结构：从 User -> Agent -> Tool 变为 User -> Proposer Agent -> Reviewer Agent -> Consensus Logic -> User。
---
**最后更新**：2026-01-26
**更新内容**：新增学硕算法创新路径规划
