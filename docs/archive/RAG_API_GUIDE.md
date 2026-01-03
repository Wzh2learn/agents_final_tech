# RAG系统API方案使用指南

## 概述

本RAG系统现已完全使用API调用方案，不再需要本地下载和运行大模型，解决了以下问题：
- ❌ 不需要下载BGE embedding模型（约400MB）
- ❌ 不需要下载BGE Reranker模型（约1.1GB）
- ❌ 不需要本地GPU资源
- ❌ 避免了LSP静态类型检查错误

## 架构变更

### 1. Embedding API（豆包）

**旧方案**：使用本地BGE模型
```python
from sentence_transformers import SentenceTransformer
embeddings = SentenceTransformer("BAAI/bge-small-zh-v1.5")
```

**新方案**：使用豆包Embedding API
```python
from tools.vector_store import get_embeddings
embeddings = get_embeddings(
    model="doubao-embedding-large-text-250515"
)
```

**特点**：
- ✅ 使用OpenAI兼容API格式
- ✅ 自动从环境变量获取配置
- ✅ 无需本地模型文件
- ✅ 按需付费，资源弹性

### 2. Rerank API（大语言模型）

**旧方案**：使用本地BGE Reranker模型
```python
from sentence_transformers import CrossEncoder
reranker = CrossEncoder("BAAI/bge-reranker-large")
```

**新方案**：使用大语言模型智能评分
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
- ✅ 无需本地Reranker模型

## 环境变量配置

确保以下环境变量已正确设置：

```bash
# 豆包API配置（系统自动配置）
COZE_WORKLOAD_IDENTITY_API_KEY=your_api_key
COZE_INTEGRATION_MODEL_BASE_URL=your_base_url

# PostgreSQL数据库配置
PGDATABASE_URL=postgresql://user:password@host:port/database
# 或者单独配置
POSTGRES_HOST=your_host
POSTGRES_PORT=5432
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database
```

## 核心功能使用

### 1. 文档加载

```python
from tools.document_loader import load_document

# 加载Markdown文档
content = load_document.invoke({"file_path": "document.md"})

# 加载Word文档
content = load_document.invoke({"file_path": "document.docx"})
```

### 2. 文本分割

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

### 3. 添加文档到知识库

```python
from tools.knowledge_base import add_document_to_knowledge_base

# 添加文档
result = add_document_to_knowledge_base.invoke({
    "file_path": "knowledge.md",
    "collection_name": "knowledge_base",
    "batch_size": 10
})
```

### 4. RAG检索

```python
from tools.rag_retriever import rag_retrieve_with_rerank

# 执行RAG检索
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

## LangGraph工作流

完整RAG工作流仍可正常使用，底层自动切换为API方案：

```python
from tools.rag_graph import create_rag_graph

app = create_rag_graph()
result = app.invoke({
    "question": "建账的流程是什么？",
    "context": {},
    "max_round": 3
})
```

## 性能对比

| 指标 | 本地模型方案 | API方案 |
|------|-------------|---------|
| 首次初始化时间 | 5-10分钟（下载模型） | <1秒 |
| Embedding延迟 | 50-100ms | 200-500ms（网络） |
| Rerank延迟 | 100-200ms | 1-3s（LLM推理） |
| 本地存储 | ~1.5GB | 0MB |
| GPU需求 | 是（可选） | 否 |
| 准确率 | 高 | 高 |

**说明**：
- API方案的Rerank延迟较高，但准确率可能更好（LLM理解语义更强）
- 可以根据需要关闭Rerank（use_rerank=False）以提升速度

## 常见问题

### Q1: LSP提示无法识别某些包（langchain_postgres, langchain_text_splitters等）

**A**: 这些是误报，不影响实际运行。这些包已在requirements.txt中声明并正确安装。

### Q2: 是否需要保留sentence-transformers依赖？

**A**: 理论上可以移除，但建议保留，因为：
- 可能被其他包依赖
- 如果将来需要切换回本地模型，可以快速切换

### Q3: 如何切换回本地模型？

**A**: 修改以下文件：
1. `vector_store.py`: 恢复使用HuggingFaceEmbeddings
2. `reranker_tool.py`: 恢复使用CrossEncoder

### Q4: API调用的成本如何？

**A**: 豆包Embedding和LLM通常按token计费。建议：
- 控制initial_k参数（如10-20）
- 合理使用Rerank（对简单查询可关闭）
- 利用知识库的缓存能力

## 最佳实践

1. **初始化知识库**：
   ```python
   # 批量添加文档
   for file_path in doc_files:
       add_document_to_knowledge_base.invoke({
           "file_path": file_path,
           "collection_name": "knowledge_base"
       })
   ```

2. **调整检索参数**：
   - 简单查询：`use_rerank=False`, `top_n=3`
   - 复杂查询：`use_rerank=True`, `initial_k=20`, `top_n=5`

3. **监控API使用**：
   ```python
   from tools.vector_store import check_vector_store_setup
   status = check_vector_store_setup.invoke()
   print(status)
   ```

## 依赖包

**必需**：
- `langchain-postgres`: PostgreSQL向量存储
- `openai`: OpenAI兼容API客户端
- `unstructured`: 文档解析
- `python-docx`: Word文档处理

**可选**（本地模型方案需要）：
- `sentence-transformers`: 本地embedding模型
- `torch`: PyTorch深度学习框架

## 总结

API方案的主要优势：
- ✅ **零配置**：无需下载模型、无需GPU
- ✅ **快速启动**：开箱即用，几分钟内完成部署
- ✅ **弹性扩展**：按需付费，自动扩容
- ✅ **准确率高**：使用最新的豆包模型
- ✅ **易于维护**：无需管理模型文件和版本

适合以下场景：
- 快速原型开发
- 云端部署环境
- 无GPU资源的环境
- 需要高准确率的场景

如需本地部署或离线使用，可参考旧版本的实现切换回本地模型方案。
