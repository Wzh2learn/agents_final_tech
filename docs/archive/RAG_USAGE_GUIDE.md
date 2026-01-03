# RAG 功能使用指南

本文档介绍了如何使用 Agent 中新增的 RAG 功能。

## 📚 功能概览

本次更新为 Agent 添加了完整的 RAG（检索增强生成）能力，包括：

1. **文档加载**：支持 Markdown (.md) 和 Word (.docx) 格式
2. **文本分割**：支持递归分割和 Markdown 结构分割
3. **向量存储**：使用 PostgreSQL + PGVector 进行向量存储
4. **Rerank 重排**：使用 BGE reranker 模型对检索结果进行重排序
5. **知识库管理**：文档上传、删除、查询
6. **RAG 检索**：集成向量检索和 Rerank 的智能检索
7. **LangGraph 工作流**：完整的 RAG Agent 工作流实现

## 🛠️ 工具列表

### 1. 文档加载工具

#### `load_document`
加载单个文档内容（Markdown/Word）

```python
load_document(file_path="assets/example.md")
```

#### `load_documents_with_metadata`
加载文档并保留元数据

```python
load_documents_with_metadata(
    file_path="assets/example.md",
    mode="elements"  # 保留文档元素元数据
)
```

#### `get_document_info`
获取文档基本信息

```python
get_document_info(file_path="assets/example.md")
```

### 2. 文本分割工具

#### `split_text_recursive`
使用递归字符分割器分割文本

```python
split_text_recursive(
    text="长文档内容...",
    chunk_size=1000,
    chunk_overlap=200
)
```

#### `split_text_by_markdown_structure`
基于 Markdown 标题结构分割

```python
split_text_by_markdown_structure(
    text="# 标题1\n内容...\n## 标题2\n内容..."
)
```

#### `split_document_optimized`
根据文件类型自动选择最优分割策略

```python
split_document_optimized(
    text="文档内容",
    file_type="markdown"  # "text", "markdown", "code"
)
```

### 3. Rerank 工具

#### `rerank_documents`
使用 BGE reranker 对检索结果进行重排序

```python
rerank_documents(
    query="用户查询",
    documents='[{"content": "文档1"}, {"content": "文档2"}]',
    model_name="BAAI/bge-reranker-large",
    top_n=5
)
```

#### `get_rerank_info`
获取 reranker 模型信息

```python
get_rerank_info()
```

### 4. 知识库管理工具

#### `add_document_to_knowledge_base`
添加文档到知识库（自动处理：加载、分割、向量化、存储）

```python
add_document_to_knowledge_base(
    file_path="assets/建账规则.md",
    chunk_size=1000,
    chunk_overlap=200,
    collection_name="knowledge_base",
    metadata='{"category": "建账规则", "version": "1.0"}'
)
```

#### `search_knowledge_base`
从知识库搜索相关文档

```python
search_knowledge_base(
    query="什么是建账规则？",
    k=5,
    score_threshold=0.7
)
```

#### `delete_documents_from_knowledge_base`
从知识库删除文档

```python
delete_documents_from_knowledge_base(
    source="建账规则.md",
    metadata_filter='{"category": "建账规则"}'
)
```

#### `get_knowledge_base_stats`
获取知识库统计信息

```python
get_knowledge_base_stats(collection_name="knowledge_base")
```

### 5. RAG 检索工具

#### `rag_retrieve_with_rerank`
RAG 检索（向量检索 + Rerank 重排）

```python
rag_retrieve_with_rerank(
    query="用户查询",
    collection_name="knowledge_base",
    initial_k=20,    # 初始检索文档数
    top_n=5,         # 最终返回文档数
    use_rerank=True,
    rerank_model="BAAI/bge-reranker-large"
)
```

#### `hybrid_search`
混合搜索（对比向量检索和 Rerank 结果）

```python
hybrid_search(
    query="用户查询",
    collection_name="knowledge_base",
    k=5
)
```

#### `format_docs_for_rag`
格式化检索到的文档用于 RAG 生成

```python
format_docs_for_rag(
    docs='[{"content": "文档1"}, {"content": "文档2"}]',
    max_length=2000
)
```

## 📖 环境配置

### 依赖包安装

```bash
pip install -qU langchain-postgres
pip install -qU docx2txt
pip install -qU 'unstructured[md]'
pip install -qU python-docx
pip install -qU langchain-text-splitters
pip install -qU sentence-transformers
```

### 环境变量配置

需要配置以下环境变量（可选）：

```bash
# PostgreSQL 配置
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=your_password
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=vector_db
```

如果未配置，系统将使用默认值。

## 🎯 使用示例

### 示例 1：添加文档到知识库

1. 准备 Markdown 或 Word 文档
2. 调用工具添加到知识库：

```python
# 添加文档
result = add_document_to_knowledge_base(
    file_path="assets/建账规则.md",
    chunk_size=1000,
    chunk_overlap=200,
    metadata='{"category": "建账规则", "department": "财务"}'
)
print(result)
```

### 示例 2：RAG 问答

```python
# RAG 检索
result = rag_retrieve_with_rerank(
    query="建账规则中如何处理逾期账单？",
    initial_k=20,
    top_n=5,
    use_rerank=True
)

print(result)
```

输出将包含：
- 检索到的文档
- 向量相似度分数
- Rerank 分数
- 文档元数据（来源等）

### 示例 3：完整 RAG 流程

Agent 会自动执行完整的 RAG 流程：

1. **检索决策**：判断是否需要检索
2. **文档检索**：从知识库检索相关文档
3. **相关性评估**：评估文档是否相关
4. **问题重写**（如需要）：优化查询并重新检索
5. **答案生成**：基于文档生成答案并提供引用
6. **后续建议**：生成 3 个相关的后续问题

## 🏗️ LangGraph 工作流

系统实现了完整的 LangGraph RAG 工作流（在 `src/tools/rag_graph.py` 中）：

### 工作流节点

1. **retrieve_decision**：检索决策节点
   - 决定是否需要检索文档
   - 判断标准：查询是否涉及具体业务规则、技术细节等

2. **retrieve_docs**：文档检索节点
   - 执行向量检索
   - 应用 Rerank 重排

3. **grade_documents**：文档相关性评估节点
   - 评估检索到的文档是否真正相关
   - 如果不相关，进入问题重写

4. **rewrite_query**：问题重写节点
   - 优化用户查询
   - 重新执行检索

5. **generate_answer**：答案生成节点
   - 基于相关文档生成答案
   - 提供引用来源

6. **suggest_questions**：后续问题建议节点
   - 基于问题和答案生成后续问题
   - 添加到答案末尾

### 工作流图

```
START
  ↓
retrieve_decision (检索决策)
  ├─ retrieve_docs → 需要检索
  └─ direct_answer → 直接回答
  ↓
retrieve_docs (文档检索)
  ↓
grade_documents (相关性评估)
  ├─ generate_answer → 文档相关
  └─ rewrite_query → 文档不相关
  ↓
rewrite_query (问题重写) ←──┘
  ↓
generate_answer (答案生成)
  ↓
suggest_questions (后续建议)
  ↓
END
```

## 📝 输出示例

### RAG 问答输出示例

```
根据建账规则文档，逾期账单的处理方式如下：

### 处理流程

1. **自动标记**
   - 系统自动识别逾期账单（超过账期 30 天）
   - 在账单上标记"逾期"状态

2. **催款通知**
   - 系统自动发送催款通知
   - 通知间隔：逾期后 7 天、15 天、30 天

3. **罚息计算**
   - 按日利率 0.05% 计算罚息
   - 罚息金额 = 逾期金额 × 0.05% × 逾期天数

### 特殊情况处理

- **客户协商**：可申请延长账期或分期付款
- **坏账处理**：逾期超过 180 天自动转为坏账

---
引用来源:
[建账规则_v1.0.md - 第四章 逾期账单处理]
[建账规则_v1.0.md - 第五章 罚息计算]

---

💡 后续问题建议：
1. 如何申请延长账期？
2. 坏账处理的流程是什么？
3. 罚息计算的公式是什么？
```

## 🚀 最佳实践

### 1. 文档准备

- 使用 Markdown 或 Word 格式
- 文档结构清晰，使用标题、列表等
- 避免过多格式化，保持内容简洁

### 2. 分割策略

- **Markdown 文档**：使用 `split_text_by_markdown_structure`
- **其他文档**：使用 `split_text_recursive`
- 推荐参数：
  - `chunk_size`: 1000-2000 字符
  - `chunk_overlap`: 200-300 字符（保持语义连贯性）

### 3. Rerank 使用

- 大模型（`BAAI/bge-reranker-large`）：效果更好，但速度较慢
- 基础模型（`BAAI/bge-reranker-base`）：速度快，适合实时应用
- 推荐参数：
  - `initial_k`: 20（为 Rerank 提供足够候选）
  - `top_n`: 5（返回最终结果数）

### 4. 知识库管理

- 定期更新知识库内容
- 删除过时文档
- 使用元数据分类文档（如 `category`, `department`）

## 🔧 故障排查

### 问题 1：依赖包未安装

**错误**：`ModuleNotFoundError`

**解决**：
```bash
pip install -qU langchain-postgres docx2txt 'unstructured[md]' python-docx langchain-text-splitters sentence-transformers
```

### 问题 2：向量存储连接失败

**错误**：`RuntimeError: 创建向量存储失败`

**解决**：
1. 检查 PostgreSQL 服务是否运行
2. 检查环境变量配置
3. 运行 `check_vector_store_setup()` 查看详细状态

### 问题 3：Rerank 模型加载失败

**错误**：`RuntimeError: 初始化 reranker 模型失败`

**解决**：
1. 检查网络连接（首次加载需要从 HuggingFace 下载模型）
2. 确保有足够的内存
3. 使用 `get_rerank_info()` 查看模型状态

### 问题 4：检索结果为空

**可能原因**：
- 知识库中没有相关文档
- `score_threshold` 设置过高

**解决**：
1. 降低 `score_threshold`（如从 0.7 降到 0.5）
2. 检查知识库内容：`get_knowledge_base_stats()`
3. 添加更多相关文档到知识库

## 📚 更多资源

- [LangChain RAG 文档](https://python.langchain.com/docs/tutorials/rag/)
- [BGE Reranker 模型](https://huggingface.co/BAAI/bge-reranker-large)
- [PGVector 文档](https://python.langchain.com/docs/integrations/vectorstores/pgvector/)

## 💡 总结

本 RAG 系统提供了：

1. ✅ 完整的文档加载和分割能力
2. ✅ 基于 PostgreSQL + PGVector 的向量存储
3. ✅ BGE Reranker 智能重排序
4. ✅ 知识库管理（上传、删除、查询）
5. ✅ 完整的 LangGraph RAG 工作流
6. ✅ 自动引用和后续问题建议

通过合理配置和使用，可以构建高效、准确的 RAG 应用！
