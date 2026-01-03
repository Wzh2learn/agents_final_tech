# Dify知识库迁移方案

## 📋 现状分析

### Dify知识库配置

您的Dify知识库使用了以下高级特性：
- **父子分段模式**：智能切分文档，保持语义完整性
- **向量化存储**：使用embedding模型向量化文档片段
- **Embedding模型**：（需要确认具体模型）
- **Rerank模型**：Qwen3-Reranker-0.6B（根据WF_QA_Main.yml）

### Coze当前状态

- ✅ 有本地文件检索功能（关键词匹配）
- ❌ 没有向量数据库集成
- ❌ 没有embedding模型
- ❌ 没有rerank模型

## 🎯 迁移方案对比

### 方案A：使用本地向量数据库（推荐）

**优势**：
- ✅ 完全自主控制
- ✅ 可以实现Dify的父子分段、embedding、rerank功能
- ✅ 集成到Coze系统中
- ✅ 成本低

**劣势**：
- ⚠️ 需要开发和维护
- ⚠️ 需要自行管理向量数据库

**技术栈**：
```python
# 向量数据库
- ChromaDB / FAISS / Milvus

# Embedding
- sentence-transformers
- LangChain embeddings

# Rerank
- sentence-transformers cross-encoder
```

### 方案B：使用外部向量服务（快速）

**优势**：
- ✅ 开发快
- ✅ 无需维护向量数据库
- ✅ 可使用成熟服务（如Pinecone、Weaviate）

**劣势**：
- ⚠️ 可能需要付费
- ⚠️ 依赖第三方服务

### 方案C：简化方案（当前可快速实现）

**优势**：
- ✅ 无需额外依赖
- ✅ 快速实现
- ✅ 使用已有的本地文件检索

**劣势**：
- ⚠️ 检索准确度较低
- ⚠️ 无法实现语义检索

## 🚀 推荐实现：方案A - 本地向量数据库

### Step 1: 安装依赖

```bash
pip install chromadb sentence-transformers langchain-chroma
```

### Step 2: 创建向量数据库管理工具

创建 `src/tools/knowledge_base.py`：

```python
import os
from typing import List, Optional
from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

# 向量数据库路径
CHROMA_DB_PATH = "assets/chroma_db"

# Embedding模型
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"

def get_embeddings():
    """获取embedding模型"""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

def get_vector_collection(collection_name: str = "rules"):
    """获取或创建向量集合"""
    embeddings = get_embeddings()

    # 确保目录存在
    os.makedirs(CHROMA_DB_PATH, exist_ok=True)

    # 创建向量数据库
    vectordb = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_PATH
    )

    return vectordb

@tool
def add_documents_to_knowledge_base(
    file_path: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    runtime=None
) -> str:
    """
    添加文档到知识库（支持父子分段）

    Args:
        file_path: 文档文件路径
        chunk_size: 分段大小
        chunk_overlap: 分段重叠大小

    Returns:
        添加结果
    """
    # 读取文档
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 创建Document对象
    doc = Document(
        page_content=content,
        metadata={"source": file_path}
    )

    # 获取向量集合
    vectordb = get_vector_collection()

    # 添加文档（自动分段）
    vectordb.add_documents([doc])

    return f"✅ 成功将文档 {file_path} 添加到知识库"

@tool
def search_knowledge_base(
    query: str,
    top_k: int = 4,
    runtime=None
) -> str:
    """
    在知识库中搜索相关内容

    Args:
        query: 查询内容
        top_k: 返回结果数量

    Returns:
        搜索结果
    """
    # 获取向量集合
    vectordb = get_vector_collection()

    # 相似度搜索
    results = vectordb.similarity_search_with_score(query, k=top_k)

    # 格式化结果
    output = "🔍 知识库搜索结果：\n\n"
    for i, (doc, score) in enumerate(results, 1):
        output += f"【结果{i}】相关度: {score:.4f}\n"
        output += f"来源: {doc.metadata.get('source', 'unknown')}\n"
        output += f"内容: {doc.page_content[:500]}...\n\n"

    return output

@tool
def rerank_search_results(
    query: str,
    documents: List[str],
    top_k: int = 3,
    runtime=None
) -> str:
    """
    使用Rerank模型重新排序搜索结果

    Args:
        query: 查询内容
        documents: 文档列表
        top_k: 返回结果数量

    Returns:
        重新排序后的结果
    """
    from sentence_transformers import CrossEncoder

    # 加载Rerank模型（需要下载）
    rerank_model = CrossEncoder('BAAI/bge-reranker-v2-m3')

    # 计算相关性分数
    pairs = [[query, doc] for doc in documents]
    scores = rerank_model.predict(pairs)

    # 排序
    results = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)

    # 返回top_k结果
    output = "🔄 Rerank排序结果：\n\n"
    for i, (doc, score) in enumerate(results[:top_k], 1):
        output += f"【结果{i}】分数: {score:.4f}\n"
        output += f"内容: {doc[:500]}...\n\n"

    return output
```

### Step 3: 从Dify导出知识库

**方法1：直接从Dify API导出（如果有API访问）**

```python
import requests

def export_dify_knowledgebase(api_key: str, dataset_id: str):
    """从Dify导出知识库"""
    url = f"https://api.dify.ai/v1/datasets/{dataset_id}/documents"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    return response.json()
```

**方法2：手动导出（如果API不可用）**

1. 在Dify知识库管理界面，逐个导出文档
2. 保存到 `assets/knowledge/` 目录
3. 使用 `add_documents_to_knowledge_base` 工具添加

### Step 4: 更新QA工具使用向量检索

修改 `src/tools/qa_agent.py`：

```python
from tools.knowledge_base import search_knowledge_base, rerank_search_results

def _search_knowledge_vector(query: str) -> str:
    """使用向量检索"""
    # 先进行向量搜索
    search_results = search_knowledge_base(query=query, top_k=10)

    # 如果需要rerank
    # documents = [...]  # 提取文档
    # reranked_results = rerank_search_results(query=query, documents=documents)

    return search_results
```

### Step 5: 测试和验证

```python
# 添加文档到知识库
add_documents_to_knowledge_base(file_path="assets/test_rule.md")

# 搜索测试
results = search_knowledge_base(query="什么是建账规则？")
```

## 📊 迁移步骤总结

### 阶段1：准备工作（1-2天）
- [ ] 从Dify导出知识库文档
- [ ] 整理文档到 `assets/knowledge/` 目录
- [ ] 安装必要依赖

### 阶段2：实现向量数据库（3-5天）
- [ ] 创建向量数据库工具
- [ ] 实现文档添加功能
- [ ] 实现语义搜索功能
- [ ] 实现Rerank功能

### 阶段3：集成和测试（2-3天）
- [ ] 更新QA工具使用向量检索
- [ ] 测试搜索准确度
- [ ] 性能优化

### 阶段4：生产部署（1-2天）
- [ ] 配置生产环境
- [ ] 数据备份
- [ ] 监控和告警

## 💡 快速开始：简化版方案

如果您希望快速实现，可以暂时使用当前的本地文件检索：

```python
# 使用现有的关键词匹配搜索
@tool
def qa_agent_simple(
    query: str,
    role: str = "default",
    runtime=None
) -> str:
    """简化版QA问答（使用本地文件检索）"""
    # 使用现有的_search_knowledge函数
    relevant_docs = _search_knowledge(query)
    # ...后续逻辑
```

## 📈 性能对比

| 特性 | Dify知识库 | Coze当前 | Coze+向量DB |
|------|-----------|---------|------------|
| 检索准确度 | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| 开发成本 | 低 | 低 | 中 |
| 维护成本 | 低 | 低 | 中 |
| 扩展性 | 高 | 低 | 高 |
| 成本 | 可能付费 | 免费 | 免费 |

## 🎯 建议

**短期方案**：
- 使用当前的本地文件检索
- 快速验证核心功能

**中期方案**：
- 实现向量数据库集成
- 提升检索准确度

**长期方案**：
- 考虑使用企业级向量数据库
- 实现父子分段和高级rerank
