# RAG 检索系统完整指南

## 目录
- [概述](#概述)
- [架构说明](#架构说明)
- [功能概览](#功能概览)
- [快速上手](#快速上手)
- [API 文档](#api-文档)
- [使用示例](#使用示例)
- [高级配置](#高级配置)
- [性能优化](#性能优化)
- [常见问题](#常见问题)

---

## 概述

本系统实现了完整的 RAG（检索增强生成）能力，支持多种检索策略和智能路由。系统现已完全使用 API 调用方案，不再需要本地下载和运行大模型。

### 核心优势

- ✅ **无需本地模型**：不再需要下载 BGE embedding（400MB）和 Reranker（1.1GB）模型
- ✅ **即开即用**：无需等待模型下载和初始化
- ✅ **资源弹性**：按需调用 API，无需 GPU
- ✅ **避免 LSP 错误**：解决本地模型依赖包的类型检查问题
- ✅ **智能路由**：根据问题类型自动选择最优检索策略
- ✅ **混合检索**：融合向量检索和 BM25 全文检索

### 系统架构

```
用户问题
    ↓
问题类型分类器（7种类型）
    ↓
智能路由
    ↓
┌─────────────────────────────────────┐
│  检索策略选择                        │
│  - 向量检索（语义匹配）              │
│  - BM25检索（关键词匹配）            │
│  - 混合检索（向量+BM25）             │
│  - 混合检索+Rerank                  │
└─────────────────────────────────────┘
    ↓
向量数据库（PostgreSQL + PGVector）
    ↓
Rerank重排序（LLM智能评分）
    ↓
生成回答
```

---

## 架构说明

### 1. Embedding API（豆包）

**方案说明**：使用豆包 Embedding API 进行文本向量化

```python
from tools.vector_store import get_embeddings

embeddings = get_embeddings(
    model="doubao-embedding-large-text-250515"
)
```

**特点**：
- ✅ 使用 OpenAI 兼容 API 格式
- ✅ 自动从环境变量获取配置
- ✅ 无需本地模型文件
- ✅ 按需付费，资源弹性

### 2. Rerank API（大语言模型）

**方案说明**：使用大语言模型进行智能重排序

```python
from tools.reranker_tool import rerank_documents

result = rerank_documents.func(
    query="用户问题",
    documents='[{"content": "文档1"}, {"content": "文档2"}]',
    top_n=5
)
```

**特点**：
- ✅ 使用豆包大语言模型（doubao-seed-1-6-251015）
- ✅ 智能理解语义相关性
- ✅ 返回相关性评分和原因
- ✅ 无需本地 Reranker 模型

### 3. 向量数据库

**技术栈**：PostgreSQL + PGVector

**优势**：
- ✅ 成熟的 PostgreSQL 数据库
- ✅ 强大的向量相似度搜索
- ✅ 支持 JSONB 元数据
- ✅ 支持关系查询和向量查询

---

## 功能概览

### 核心功能

1. **文档加载**
   - 支持 Markdown (.md)、Word (.docx)、PDF (.pdf)、TXT (.txt)、CSV (.csv)、JSON (.json)
   - 自动识别文件格式
   - 保留文档元数据

2. **文本分割**
   - 递归字符分割
   - Markdown 结构分割
   - 自动选择最优策略

3. **向量存储**
   - PostgreSQL + PGVector
   - 支持 JSONB 元数据
   - 自动索引

4. **Rerank 重排**
   - LLM 智能评分
   - 语义理解
   - 相关性排序

5. **问题类型分类**（7种类型）
   - concept（概念型）：什么是 XXX
   - process（流程型）：如何做 XXX
   - compare（对比型）：XXX 和 YYY 的区别
   - factual（事实型）：XXX 的数据、日期
   - rule（规则型）：XXX 的规则、规定
   - troubleshooting（故障排查）：XXX 出现错误
   - general（通用型）：其他问题

6. **智能检索策略**
   - 向量检索（语义匹配）
   - BM25 检索（关键词匹配）
   - 混合检索（向量 + BM25）
   - 混合检索 + Rerank
   - 自动路由（根据问题类型）

7. **知识库管理**
   - 添加/删除文档
   - 搜索文档
   - 获取统计信息
   - 文档下载

8. **高级功能**
   - 知识热力图
   - 文档分层结构
   - 答案溯源
   - 检索方法对比
   - 批量检索

---

## 快速上手

### 环境配置

#### 1. 安装依赖

```bash
pip install -qU langchain-postgres
pip install -qU docx2txt
pip install -qU 'unstructured[md]'
pip install -qU python-docx
pip install -qU pypdf
pip install -qU langchain-text-splitters
pip install -qU rank-bm25
```

#### 2. 配置环境变量

```bash
# 豆包 API 配置（系统自动配置）
COZE_WORKLOAD_IDENTITY_API_KEY=your_api_key
COZE_INTEGRATION_MODEL_BASE_URL=your_base_url

# PostgreSQL 数据库配置
PGDATABASE_URL=postgresql://user:password@host:port/database
# 或分别配置
POSTGRES_HOST=your_host
POSTGRES_PORT=5432
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database
```

#### 3. 初始化数据库

```bash
python scripts/init_pgvector_db.py
```

#### 4. 配置 Embedding

**选项 A：使用模拟 Embedding（测试环境）**

编辑 `config/app_config.json`：

```json
{
  "embedding": {
    "use_mock": true,
    "mock_dimension": 1536
  }
}
```

**选项 B：使用真实 Embedding API（生产环境）**

编辑 `config/app_config.json`：

```json
{
  "embedding": {
    "use_mock": false,
    "provider": "doubao",
    "model": "doubao-embedding-large-text-250515"
  }
}
```

### 基本使用

#### 1. 加载文档

```python
from tools.document_loader import load_document

# 加载 Markdown 文档
content = load_document.invoke({"file_path": "assets/document.md"})

# 加载 Word 文档
content = load_document.invoke({"file_path": "assets/document.docx"})
```

#### 2. 分割文本

```python
from tools.text_splitter import split_text_recursive

# 分割文本
result = split_text_recursive.invoke({
    "text": "长文本内容...",
    "chunk_size": 1000,
    "chunk_overlap": 200
})
chunks = json.loads(result)
```

#### 3. 添加文档到知识库

```python
from tools.knowledge_base import add_document_to_knowledge_base

# 添加文档
result = add_document_to_knowledge_base.invoke({
    "file_path": "assets/knowledge.md",
    "collection_name": "knowledge_base",
    "batch_size": 10
})
```

#### 4. RAG 检索

```python
from tools.rag_retriever import rag_retrieve_with_rerank

# 执行 RAG 检索
result = rag_retrieve_with_rerank.invoke({
    "query": "建账的基本原则是什么？",
    "collection_name": "knowledge_base",
    "initial_k": 20,
    "top_n": 5,
    "use_rerank": True
})
```

**返回示例**：
```
🔍 RAG 检索结果
查询: 建账的基本原则是什么？
使用 Rerank: 是
初始检索: 20 文档
返回结果: 5 文档
==================================================

【结果 1】
向量相似度: 0.7823
Rerank 分数: 0.95
相关原因: 完全相关，直接回答了建账的基本原则
内容: 建账是企业财务管理的基础工作，需要遵循以下原则：
- 真实性原则：确保所有数据真实准确
- 完整性原则：确保账目完整无遗漏
- 及时性原则：及时记录和更新账目
...
```

---

## API 文档

### 文档加载工具

#### load_document

加载单个文档内容（Markdown/Word/PDF/TXT/CSV/JSON）

**参数**：
- `file_path` (str): 文档文件路径

**返回**：
- 文档内容字符串

**示例**：
```python
load_document.invoke({"file_path": "assets/document.md"})
```

#### load_documents_with_metadata

加载文档并保留元数据

**参数**：
- `file_path` (str): 文档文件路径
- `mode` (str): 加载模式（"elements" 保留文档元素元数据）

**返回**：
- 文档内容和元数据的 JSON 字符串

**示例**：
```python
load_documents_with_metadata.invoke({
    "file_path": "assets/document.md",
    "mode": "elements"
})
```

#### get_document_info

获取文档基本信息

**参数**：
- `file_path` (str): 文档文件路径

**返回**：
- 文档信息 JSON（文件名、大小、类型、行数等）

**示例**：
```python
get_document_info.invoke({"file_path": "assets/document.md"})
```

---

### 文本分割工具

#### split_text_recursive

使用递归字符分割器分割文本

**参数**：
- `text` (str): 要分割的文本
- `chunk_size` (int): 分块大小（默认 1000）
- `chunk_overlap` (int): 分块重叠大小（默认 200）

**返回**：
- 分割后的文本块 JSON 字符串

**示例**：
```python
split_text_recursive.invoke({
    "text": "长文档内容...",
    "chunk_size": 1000,
    "chunk_overlap": 200
})
```

#### split_text_by_markdown_structure

基于 Markdown 标题结构分割

**参数**：
- `text` (str): Markdown 文本

**返回**：
- 按标题结构分割的文本块 JSON 字符串

**示例**：
```python
split_text_by_markdown_structure.invoke({
    "text": "# 标题1\n内容...\n## 标题2\n内容..."
})
```

#### split_document_optimized

根据文件类型自动选择最优分割策略

**参数**：
- `text` (str): 文档内容
- `file_type` (str): 文件类型（"text", "markdown", "code"）

**返回**：
- 优化分割后的文本块 JSON 字符串

**示例**：
```python
split_document_optimized.invoke({
    "text": "文档内容",
    "file_type": "markdown"
})
```

---

### Rerank 工具

#### rerank_documents

使用 LLM 对检索结果进行重排序

**参数**：
- `query` (str): 用户查询
- `documents` (str): 文档列表 JSON 字符串
- `top_n` (int): 返回结果数量（默认 5）

**返回**：
- 重排序后的文档和评分 JSON 字符串

**示例**：
```python
rerank_documents.invoke({
    "query": "建账规则是什么？",
    "documents": '[{"content": "文档1"}, {"content": "文档2"}]',
    "top_n": 5
})
```

---

### 知识库管理工具

#### add_document_to_knowledge_base

添加文档到知识库（自动处理：加载、分割、向量化、存储）

**参数**：
- `file_path` (str): 文档文件路径
- `chunk_size` (int): 分块大小（默认 1000）
- `chunk_overlap` (int): 分块重叠大小（默认 200）
- `collection_name` (str): 集合名称（默认 "knowledge_base"）
- `metadata` (str): 元数据 JSON 字符串（可选）

**返回**：
- 添加结果信息

**示例**：
```python
add_document_to_knowledge_base.invoke({
    "file_path": "assets/建账规则.md",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "collection_name": "knowledge_base",
    "metadata": '{"category": "建账规则", "version": "1.0"}'
})
```

#### search_knowledge_base

从知识库搜索相关文档

**参数**：
- `query` (str): 查询内容
- `k` (int): 返回结果数量（默认 5）
- `score_threshold` (float): 相似度阈值（默认 0.7）
- `collection_name` (str): 集合名称（默认 "knowledge_base"）

**返回**：
- 搜索结果 JSON 字符串

**示例**：
```python
search_knowledge_base.invoke({
    "query": "什么是建账规则？",
    "k": 5,
    "score_threshold": 0.7
})
```

#### delete_documents_from_knowledge_base

从知识库删除文档

**参数**：
- `source` (str): 文档来源（文件名）
- `metadata_filter` (str): 元数据过滤条件 JSON 字符串（可选）
- `collection_name` (str): 集合名称（默认 "knowledge_base"）

**返回**：
- 删除结果信息

**示例**：
```python
delete_documents_from_knowledge_base.invoke({
    "source": "建账规则.md",
    "metadata_filter": '{"category": "建账规则"}'
})
```

#### get_knowledge_base_stats

获取知识库统计信息

**参数**：
- `collection_name` (str): 集合名称（默认 "knowledge_base"）

**返回**：
- 统计信息 JSON（文档数、分块数、向量维度等）

**示例**：
```python
get_knowledge_base_stats.invoke({
    "collection_name": "knowledge_base"
})
```

---

### RAG 检索工具

#### rag_retrieve_with_rerank

RAG 检索（向量检索 + Rerank 重排）

**参数**：
- `query` (str): 用户查询
- `collection_name` (str): 集合名称（默认 "knowledge_base"）
- `initial_k` (int): 初始检索文档数（默认 20）
- `top_n` (int): 最终返回文档数（默认 5）
- `use_rerank` (bool): 是否使用 Rerank（默认 True）

**返回**：
- RAG 检索结果（包含相似度、Rerank 分数、内容）

**示例**：
```python
rag_retrieve_with_rerank.invoke({
    "query": "建账的基本原则是什么？",
    "collection_name": "knowledge_base",
    "initial_k": 20,
    "top_n": 5,
    "use_rerank": True
})
```

---

### BM25 检索工具

#### bm25_retrieve

BM25 全文检索

**参数**：
- `query` (str): 查询内容
- `top_k` (int): 返回结果数量（默认 5）
- `collection_name` (str): 集合名称（默认 "knowledge_base"）

**返回**：
- BM25 检索结果 JSON 字符串

**示例**：
```python
bm25_retrieve.invoke({
    "query": "建账规则",
    "top_k": 5,
    "collection_name": "knowledge_base"
})
```

---

### 混合检索工具

#### hybrid_retrieve

混合检索（向量 + BM25）

**参数**：
- `query` (str): 查询内容
- `top_k` (int): 返回结果数量（默认 5）
- `vector_weight` (float): 向量检索权重（默认 0.5）
- `bm25_weight` (float): BM25 检索权重（默认 0.5）
- `collection_name` (str): 集合名称（默认 "knowledge_base"）
- `use_rerank` (bool): 是否使用 Rerank（默认 False）

**返回**：
- 混合检索结果 JSON 字符串

**示例**：
```python
hybrid_retrieve.invoke({
    "query": "建账规则是什么？",
    "top_k": 5,
    "vector_weight": 0.5,
    "bm25_weight": 0.5,
    "use_rerank": True
})
```

---

### 智能路由工具

#### smart_retrieve

智能检索路由（自动选择最优策略）

**参数**：
- `query` (str): 查询内容
- `top_k` (int): 返回结果数量（默认 5）
- `collection_name` (str): 集合名称（默认 "knowledge_base"）
- `strategy` (str): 指定策略（可选，默认自动选择）
  - "vector" - 向量检索
  - "bm25" - BM25 检索
  - "hybrid" - 混合检索
  - "hybrid_rerank" - 混合检索 + Rerank

**返回**：
- 智能检索结果 JSON 字符串

**示例**：
```python
# 自动选择策略
smart_retrieve.invoke({
    "query": "什么是建账规则？",
    "top_k": 5
})

# 指定策略
smart_retrieve.invoke({
    "query": "什么是建账规则？",
    "top_k": 5,
    "strategy": "hybrid_rerank"
})
```

---

### 问题分类工具

#### classify_question_type

问题类型分类

**参数**：
- `query` (str): 用户查询

**返回**：
- 问题类型 JSON 字符串
  - type: 问题类型（concept/process/compare/factual/rule/troubleshooting/general）
  - confidence: 置信度（0-1）
  - recommended_strategy: 推荐检索策略

**示例**：
```python
classify_question_type.invoke({
    "query": "什么是建账规则？"
})
```

**返回示例**：
```json
{
  "type": "concept",
  "confidence": 0.95,
  "recommended_strategy": "hybrid_rerank"
}
```

---

### 高级功能工具

#### generate_knowledge_heatmap

生成知识热力图数据

**参数**：
- `collection_name` (str): 集合名称（默认 "knowledge_base"）
- `max_topics` (int): 最大主题数（默认 10）
- `days` (int): 统计天数（默认 7）

**返回**：
- 热力图数据 JSON 字符串

**示例**：
```python
generate_knowledge_heatmap.invoke({
    "collection_name": "knowledge_base",
    "max_topics": 10,
    "days": 7
})
```

#### build_document_hierarchy

构建文档分层结构

**参数**：
- `collection_name` (str): 集合名称（默认 "knowledge_base"）
- `document_id` (str): 文档 ID（可选）

**返回**：
- 分层结构 JSON 字符串

**示例**：
```python
build_document_hierarchy.invoke({
    "collection_name": "knowledge_base"
})
```

#### compare_retrieval_methods

对比不同检索方法

**参数**：
- `query` (str): 查询内容
- `collection_name` (str): 集合名称（默认 "knowledge_base"）
- `top_k` (int): 返回结果数量（默认 5）

**返回**：
- 对比结果 JSON 字符串

**示例**：
```python
compare_retrieval_methods.invoke({
    "query": "什么是建账规则？",
    "top_k": 5
})
```

---

## 使用示例

### 示例 1：完整的 RAG 流程

```python
# 1. 加载文档
from tools.document_loader import load_document
content = load_document.invoke({"file_path": "assets/knowledge.md"})

# 2. 分割文本
from tools.text_splitter import split_text_recursive
chunks_json = split_text_recursive.invoke({
    "text": content,
    "chunk_size": 1000,
    "chunk_overlap": 200
})
chunks = json.loads(chunks_json)

# 3. 添加到知识库
from tools.knowledge_base import add_document_to_knowledge_base
result = add_document_to_knowledge_base.invoke({
    "file_path": "assets/knowledge.md",
    "collection_name": "knowledge_base"
})

# 4. RAG 检索
from tools.rag_retriever import rag_retrieve_with_rerank
result = rag_retrieve_with_rerank.invoke({
    "query": "建账的基本原则是什么？",
    "collection_name": "knowledge_base",
    "use_rerank": True
})
```

### 示例 2：问题分类 + 智能路由

```python
from tools.rag_router import classify_question_type, smart_retrieve

# 1. 分类问题
classification = json.loads(classify_question_type.invoke({
    "query": "什么是建账规则？"
}))

print(f"问题类型: {classification['type']}")
print(f"推荐策略: {classification['recommended_strategy']}")

# 2. 智能检索（自动使用推荐策略）
result = smart_retrieve.invoke({
    "query": "什么是建账规则？",
    "top_k": 5
})
```

### 示例 3：混合检索对比

```python
from tools.rag_retriever import rag_retrieve_with_rerank
from tools.bm25_retriever import bm25_retrieve
from tools.hybrid_retriever import hybrid_retrieve

query = "什么是建账规则？"

# 向量检索
vector_result = rag_retrieve_with_rerank.invoke({
    "query": query,
    "use_rerank": False
})

# BM25 检索
bm25_result = bm25_retrieve.invoke({
    "query": query
})

# 混合检索
hybrid_result = hybrid_retrieve.invoke({
    "query": query,
    "vector_weight": 0.5,
    "bm25_weight": 0.5
})

# 对比结果
print("=== 向量检索 ===")
print(vector_result)

print("\n=== BM25 检索 ===")
print(bm25_result)

print("\n=== 混合检索 ===")
print(hybrid_result)
```

### 示例 4：知识热力图分析

```python
from tools.knowledge_heatmap import generate_knowledge_heatmap

# 生成热力图
heatmap_data = json.loads(generate_knowledge_heatmap.invoke({
    "collection_name": "knowledge_base",
    "max_topics": 10,
    "days": 7
}))

# 分析热门主题
print("=== 知识热力图 ===")
for topic in heatmap_data['topics']:
    print(f"主题: {topic['name']}")
    print(f"热度: {topic['heat_level']}/5")
    print(f"检索次数: {topic['retrieval_count']}")
    print(f"平均准确率: {topic['avg_accuracy']:.2%}")
    print()
```

---

## 高级配置

### 检索策略选择指南

| 问题类型 | 推荐策略 | 说明 |
|---------|---------|------|
| concept（概念型） | hybrid_rerank | 需要语义理解，混合检索 + Rerank 效果最好 |
| process（流程型） | hybrid_rerank | 流程说明需要准确理解 |
| compare（对比型） | hybrid_rerank | 对比分析需要深入理解 |
| factual（事实型） | bm25 | 事实查询关键词匹配即可 |
| rule（规则型） | hybrid_rerank | 规则解释需要语义理解 |
| troubleshooting（故障排查） | hybrid_rerank | 故障排查需要综合理解 |
| general（通用型） | vector | 通用问题向量检索即可 |

### 参数调优建议

#### 向量检索

```json
{
  "vector_store": {
    "initial_k": 20,      // 初始检索数量，越大召回率越高
    "score_threshold": 0.7 // 相似度阈值，越高过滤越严格
  }
}
```

#### BM25 检索

```json
{
  "bm25": {
    "k1": 1.2,           // 控制词频饱和度（通常 1.2-2.0）
    "b": 0.75,           // 控制文档长度归一化（通常 0.75）
    "top_k": 5           // 返回结果数量
  }
}
```

#### 混合检索

```json
{
  "rag": {
    "vector_weight": 0.5,  // 向量检索权重
    "bm25_weight": 0.5,    // BM25 检索权重
    "use_rerank": true     // 是否使用 Rerank
  }
}
```

**调优建议**：
- 语义理解为主：`vector_weight: 0.7, bm25_weight: 0.3`
- 关键词匹配为主：`vector_weight: 0.3, bm25_weight: 0.7`
- 平衡策略：`vector_weight: 0.5, bm25_weight: 0.5`

#### Rerank

```json
{
  "rerank": {
    "enabled": true,
    "top_n": 5,        // 返回结果数量
    "model": "doubao-seed-1-6-251015"
  }
}
```

---

## 性能优化

### 缓存机制

系统实现了内存缓存，显著提升性能：

```python
from src.utils.cache import cached, SimpleCache

# 使用缓存装饰器
@cached(ttl=300, key_prefix="kb_stats")
def get_knowledge_base_stats(collection_name):
    # 函数实现
    pass
```

**缓存效果**：
- 知识库统计 API：
  - 首次调用：约 100-200ms
  - 缓存调用：约 0.3-0.5ms
  - **性能提升：200-400倍**

### 数据库优化

- 使用索引（PostgreSQL）
- 避免N+1查询
- 分页减少数据传输
- 使用连接池

### 检索优化建议

1. **合理设置初始检索数量**（initial_k）
   - 太小：召回率低
   - 太大：性能差
   - 推荐：20-50

2. **使用 Rerank 提升准确性**
   - 适合对准确性要求高的场景
   - 会增加延迟（1-3秒）
   - 可以关闭 Rerank 提升速度

3. **选择合适的检索策略**
   - 事实查询：BM25（快速）
   - 语义理解：向量检索（中等）
   - 高准确性：混合检索 + Rerank（慢但准确）

---

## 常见问题

### Q1: LSP 提示无法识别某些包（langchain_postgres, langchain_text_splitters等）

**A**: 这些是误报，不影响实际运行。这些包已在 requirements.txt 中声明并正确安装。

### Q2: 是否需要保留 sentence-transformers 依赖？

**A**: 理论上可以移除，但建议保留，因为：
- 可能被其他包依赖
- 如果将来需要切换回本地模型，可以快速切换

### Q3: 如何切换回本地模型？

**A**: 修改以下文件：
1. `vector_store.py`: 恢复使用 HuggingFaceEmbeddings
2. `reranker_tool.py`: 恢复使用 CrossEncoder

### Q4: Embedding API 调用失败怎么办？

**A**:
1. 检查环境变量是否正确设置
2. 检查 API Key 是否有效
3. 测试时可以使用模拟 Embedding：设置 `"use_mock": true`
4. 检查网络连接

### Q5: Rerank 延迟太高怎么办？

**A**:
1. 关闭 Rerank：`use_rerank: false`
2. 减少初始检索数量：`initial_k: 10`
3. 减少最终返回数量：`top_n: 3`

### Q6: 如何提高检索准确率？

**A**:
1. 使用混合检索 + Rerank
2. 调整 vector_weight 和 bm25_weight
3. 增加 initial_k 提高召回率
4. 优化文档质量（结构化、清晰）

### Q7: 如何测试 RAG 功能？

**A**:
```bash
# RAG 完整测试
python tests/test_rag_complete.py

# BM25 检索测试
python tests/test_bm25_simple.py

# RAG 策略测试
python tests/test_rag_strategy.py
```

### Q8: 支持哪些文档格式？

**A**: 支持：
- Markdown (.md)
- Word (.docx)
- PDF (.pdf)
- TXT (.txt)
- CSV (.csv)
- JSON (.json)

### Q9: 如何添加自定义文档格式？

**A**:
1. 在 `src/tools/document_loader.py` 中添加加载逻辑
2. 安装相应的解析库（如 pypdf、python-docx）
3. 更新 `config/app_config.json` 中的支持格式列表

### Q10: 性能对比（本地模型 vs API）

| 指标 | 本地模型方案 | API 方案 |
|------|-------------|---------|
| 首次初始化时间 | 5-10分钟（下载模型） | <1秒 |
| Embedding 延迟 | 50-100ms | 200-500ms（网络） |
| Rerank 延迟 | 100-200ms | 1-3s（LLM推理） |
| 本地存储 | ~1.5GB | 0MB |
| GPU 需求 | 是（可选） | 否 |
| 准确率 | 高 | 高 |

---

## 相关文档

- [配置说明文档](CONFIGURATION.md) - 详细的配置项说明
- [项目 README](../README.md) - 项目概览和快速开始
