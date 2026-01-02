# 建账规则助手系统

基于 LangChain + LangGraph 架构的智能建账规则助手，完整迁移自 Dify 工作流，新增 RAG 知识检索能力，现已全面切换为 API 方案。

## 📋 目录

- [功能特性](#功能特性)
- [技术架构](#技术架构)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [核心功能使用](#核心功能使用)
- [配置说明](#配置说明)
- [开发指南](#开发指南)
- [常见问题](#常见问题)

---

## ✨ 功能特性

### 核心能力

1. **角色识别与路由**
   - 支持 4 种角色：产品经理、技术开发、销售运营、默认工程师
   - 根据角色自动调整回答重点和语气
   - 提供开场白引导用户选择角色

2. **文档处理**
   - 支持 Markdown 和 Word 文档加载
   - 智能文本分割（递归分割、Markdown 结构分割）
   - 提取结构化规则表格
   - 规则校验功能

3. **RAG 知识检索**
   - 基于向量数据库的语义搜索
   - LLM 智能重排序（Rerank）
   - 支持混合检索（向量 + 关键词）
   - 自动引用来源

4. **智能问答**
   - 基于知识库回答用户问题
   - 查询分类和路由
   - 后续问题建议

5. **反馈处理**
   - 接收并分类用户反馈
   - 反馈汇总报告
   - 自动通知关键问题

6. **知识库管理**
   - 添加/删除文档
   - 查询知识库统计
   - 支持多种元数据过滤

### API 方案优势

✅ **无需本地模型**：不再需要下载 BGE embedding（400MB）和 Reranker（1.1GB）模型
✅ **即开即用**：无需等待模型下载和初始化
✅ **资源弹性**：按需调用 API，无需 GPU
✅ **避免 LSP 错误**：解决本地模型依赖包的类型检查问题

---

## 🏗️ 技术架构

### 技术栈

- **框架**: LangChain 1.0 + LangGraph
- **大模型**: deepseek-v3-2-251201（可通过配置切换）
- **Embedding**: 豆包 Embedding API（doubao-embedding-large-text-250515）
- **Rerank**: 豆包大语言模型（doubao-seed-1-6-251015）
- **向量数据库**: PostgreSQL + PGVector
- **对象存储**: 集成对象存储 API
- **语言**: Python 3.9+

### 架构图

```
用户输入
    ↓
主 Agent（角色识别 + 路由）
    ↓
┌─────────────┬─────────────┬─────────────┐
│ 文档处理     │ RAG 检索    │ 反馈处理     │
│ 工具组      │ 工具组      │ 工具组      │
└─────────────┴─────────────┴─────────────┘
    ↓              ↓              ↓
文档解析      向量搜索 + Rerank  反馈记录
规则提取      知识库查询        报告生成
    ↓              ↓              ↓
┌───────────────────────────────────┐
│         PostgreSQL + PGVector     │
│         (向量数据库 + 知识库)      │
└───────────────────────────────────┘
    ↓
角色化回答 + 后续建议
```

---

## 📁 项目结构

```
.
├── config/                          # 配置目录
│   └── agent_llm_config.json       # Agent 和模型配置
├── docs/                           # 文档
│   └── RAG_API_GUIDE.md           # RAG API 方案详细指南
├── scripts/                        # 脚本（内置，无需修改）
│   ├── local_run.sh               # 本地运行脚本
│   └── http_run.sh                # HTTP 服务启动脚本
├── assets/                         # 资源与数据中心
│   ├── data/                      # 测试数据文件
│   ├── docs/                      # 文档资源
│   └── knowledge/                 # 知识库文档
├── src/
│   ├── agents/                    # Agent 代码
│   │   └── agent.py               # 主 Agent（建账规则助手）
│   ├── tools/                     # 工具定义
│   │   ├── document_loader.py     # 文档加载工具
│   │   ├── text_splitter.py       # 文本分割工具
│   │   ├── vector_store.py        # 向量存储（Embedding API）
│   │   ├── reranker_tool.py       # Rerank 工具（LLM API）
│   │   ├── knowledge_base.py      # 知识库管理工具
│   │   ├── rag_retriever.py       # RAG 检索工具
│   │   ├── document_processor.py  # 文档处理工具
│   │   ├── qa_agent.py            # QA 问答工具
│   │   ├── feedback_handler.py    # 反馈处理工具
│   │   ├── file_writer.py         # 文件写入工具
│   │   └── __init__.py            # 工具导出
│   ├── storage/                   # 存储初始化
│   │   └── memory/
│   │       └── memory_saver.py    # 短期记忆（对话历史）
│   ├── biz/                       # 业务封装（内置）
│   └── main.py                    # 运行主入口（内置）
├── tests/                         # 单元测试目录
├── requirements.txt               # Python 依赖
├── AGENT.md                       # 模型规范
└── README.md                      # 本文档
```

---

## 🚀 快速开始

### 1. 环境准备

确保已安装 Python 3.9+，然后安装依赖：

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件或设置以下环境变量：

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

### 3. 准备测试数据

将文档放入 `assets/` 目录：

```bash
# 示例文档结构
assets/
├── docs/
│   ├── 建账规则.md
│   └── 财务流程.docx
├── knowledge/
│   └── 知识库文档.md
└── data/
    └── 测试数据.json
```

### 4. 运行方式

#### 本地运行

```bash
# 运行完整工作流
bash scripts/local_run.sh -m flow

# 运行单个节点
bash scripts/local_run.sh -m node -n node_name
```

#### 启动 HTTP 服务

```bash
# 启动 HTTP 服务（端口 5000）
bash scripts/http_run.sh -m http -p 5000
```

#### Python 直接运行

```bash
# 运行主程序
python src/main.py
```

---

## 🔧 核心功能使用

### 1. 首次交互：角色选择

系统会自动显示开场白引导用户选择角色：

```
欢迎使用建账规则助手！请选择你的角色：

【a】产品经理 - 关注业务流程和用户体验
【b】技术开发 - 关注技术实现和系统架构  
【c】销售运营 - 关注客户价值和市场竞争
【d】默认工程师视角 - 标准技术解释

请回复 a/b/c/d 选择你的角色，这将影响回答的重点和详细程度。
```

### 2. 文档处理

**场景**：当用户提到任何文档、文件处理、提取规则、生成表格等需求时

**使用工具**：`document_processor`

```python
from tools.document_processor import document_processor

# 解析文档并提取规则表格
result = document_processor.invoke({
    "file_path": "assets/docs/建账规则.md",
    "role": "product_manager"  # 根据用户角色选择
})
```

### 3. RAG 知识检索

**场景**：当用户询问关于建账规则的问题时

**使用工具**：`rag_retrieve_with_rerank`

```python
from tools.rag_retriever import rag_retrieve_with_rerank

# 执行 RAG 检索（向量搜索 + Rerank）
result = rag_retrieve_with_rerank.invoke({
    "query": "建账的基本原则是什么？",
    "collection_name": "knowledge_base",
    "initial_k": 20,
    "top_n": 5,
    "use_rerank": True  # 启用 LLM 智能重排序
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

### 4. 知识库管理

#### 添加文档

```python
from tools.knowledge_base import add_document_to_knowledge_base

# 添加文档到知识库
result = add_document_to_knowledge_base.invoke({
    "file_path": "assets/knowledge/建账规则.md",
    "collection_name": "knowledge_base",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "metadata": '{"category": "建账规则", "version": "1.0"}'
})
```

#### 搜索知识库

```python
from tools.knowledge_base import search_knowledge_base

# 搜索知识库
result = search_knowledge_base.invoke({
    "query": "建账流程",
    "collection_name": "knowledge_base",
    "k": 5,
    "score_threshold": 0.7,
    "filter": '{"category": "建账规则"}'
})
```

#### 获取统计信息

```python
from tools.knowledge_base import get_knowledge_base_stats

# 获取知识库统计
result = get_knowledge_base_stats.invoke({
    "collection_name": "knowledge_base"
})
```

### 5. 文档加载和分割

#### 加载文档

```python
from tools.document_loader import load_document

# 加载 Markdown 文档
content = load_document.invoke({"file_path": "assets/docs/建账规则.md"})

# 加载 Word 文档
content = load_document.invoke({"file_path": "assets/docs/财务流程.docx"})
```

#### 分割文本

```python
from tools.text_splitter import split_text_recursive
import json

# 递归文本分割
result = split_text_recursive.invoke({
    "text": "长文本内容...",
    "chunk_size": 1000,
    "chunk_overlap": 200
})
chunks = json.loads(result)

# Markdown 结构分割
from tools.text_splitter import split_text_by_markdown_structure
result = split_text_by_markdown_structure.invoke({
    "text": "# 标题\n内容...",
    "max_chunk_size": 1000
})
```

### 6. 反馈处理

```python
from tools.feedback_handler import feedback_handler

# 处理用户反馈
result = feedback_handler.invoke({
    "user_feedback": "回答不够详细，希望补充更多示例",
    "last_answer": "AI 上次回答",
    "conversation_id": "会话 ID",
    "auto_notify": False  # 是否自动通知关键问题
})
```

### 7. 文件写入

```python
from tools.file_writer import write_to_storage

# 写入对象存储
result = write_to_storage.invoke({
    "content": "文件内容",
    "filename": "result.md",
    "metadata": '{"type": "report", "date": "2025-01-01"}'
})
```

---

## ⚙️ 配置说明

### Agent 配置（config/agent_llm_config.json）

```json
{
  "config": {
    "temperature": 0.7,
    "frequency_penalty": 0,
    "top_p": 0.9,
    "max_tokens": 4096,
    "max_completion_tokens": 10000,
    "thinking_type": "enabled",
    "reasoning_effort": "medium",
    "response_format": "text",
    "model": "deepseek-v3-2-251201"
  },
  "sp": "# 系统提示词...",
  "tools": [
    "document_processor",
    "validate_rules",
    "rag_retrieve_with_rerank",
    "add_document_to_knowledge_base",
    ...
  ]
}
```

**配置项说明**：

- `temperature`: 控制回答随机性（0-1，越高越随机）
- `top_p`: 核采样参数（0-1）
- `max_tokens`: 最大输出 token 数
- `thinking_type`: 是否启用思考模式（enabled/disabled）
- `model`: 使用的模型名称

### 模型切换

系统支持通过修改配置文件切换模型：

1. 查询可用模型（通过 `integration_search` 工具）
2. 修改 `config/agent_llm_config.json` 中的 `model` 字段
3. 重启服务生效

### RAG 参数调优

在 `config/agent_llm_config.json` 的系统提示词中，可以调整 RAG 参数：

```python
# 默认 RAG 参数
rag_retrieve_with_rerank(
  initial_k=20,      # 初始向量检索数量
  top_n=5,           # 最终返回数量
  use_rerank=True    # 是否启用 Rerank
)
```

**建议**：
- 提升准确率：增加 `initial_k`，启用 `use_rerank`
- 提升速度：减少 `initial_k`，禁用 `use_rerank`

---

## 📚 工具列表

### 文档处理工具

| 工具名称 | 功能 | 使用场景 |
|---------|------|---------|
| `document_processor` | 解析文档并提取规则表格 | 文档处理、规则提取 |
| `validate_rules` | 校验规则合理性 | 规则验证 |

### RAG 检索工具

| 工具名称 | 功能 | 使用场景 |
|---------|------|---------|
| `rag_retrieve_with_rerank` | RAG 检索（向量+Rerank） | 智能问答、知识检索 |
| `search_knowledge_base` | 向量搜索 | 知识库查询 |
| `format_docs_for_rag` | 格式化文档用于生成 | 文档格式化 |

### 知识库管理工具

| 工具名称 | 功能 | 使用场景 |
|---------|------|---------|
| `add_document_to_knowledge_base` | 添加文档到知识库 | 知识库构建 |
| `delete_documents_from_knowledge_base` | 删除文档 | 知识库维护 |
| `get_knowledge_base_stats` | 获取统计信息 | 知识库监控 |

### 文档加载和分割工具

| 工具名称 | 功能 | 使用场景 |
|---------|------|---------|
| `load_document` | 加载文档（Markdown/Word） | 文档导入 |
| `split_text_recursive` | 递归文本分割 | 文本预处理 |
| `split_text_by_markdown_structure` | Markdown 结构分割 | Markdown 文档 |
| `split_document_optimized` | 优化文档分割 | 高级分割需求 |
| `split_text_with_summary` | 文本分割并统计 | 数据分析 |

### Rerank 工具

| 工具名称 | 功能 | 使用场景 |
|---------|------|---------|
| `rerank_documents` | 文档重排序（LLM API） | 检索结果优化 |

### QA 工具

| 工具名称 | 功能 | 使用场景 |
|---------|------|---------|
| `qa_agent` | QA 问答 | 智能问答 |
| `classify_query` | 查询分类 | 意图识别 |

### 反馈处理工具

| 工具名称 | 功能 | 使用场景 |
|---------|------|---------|
| `feedback_handler` | 分类并处理反馈 | 用户反馈处理 |
| `generate_summary_report` | 生成反馈汇总报告 | 管理员报告 |

### 文件写入工具

| 工具名称 | 功能 | 使用场景 |
|---------|------|---------|
| `write_to_file` | 写入本地文件 | 本地存储 |
| `write_to_storage` | 写入对象存储 | 云端存储 |
| `save_rule_to_knowledge` | 保存规则到知识库 | 规则归档 |
| `save_qa_answer` | 保存问答对到知识库 | 知识积累 |
| `read_from_storage` | 从对象存储读取 | 数据读取 |
| `list_storage_files` | 列出对象存储文件 | 文件管理 |

### 辅助工具

| 工具名称 | 功能 | 使用场景 |
|---------|------|---------|
| `check_vector_store_setup` | 检查向量存储设置 | 环境检查 |

---

## 🛠️ 开发指南

### 添加新工具

1. 在 `src/tools/` 目录创建新文件，例如 `new_tool.py`：

```python
from langchain.tools import tool
from langchain.agents import ToolRuntime

@tool
def my_new_tool(
    param1: str,
    param2: int,
    runtime: ToolRuntime
) -> str:
    """工具描述
    
    Args:
        param1: 参数1说明
        param2: 参数2说明
    
    Returns:
        工具执行结果
    """
    # 工具逻辑
    result = f"执行结果：{param1}, {param2}"
    return result
```

2. 在 `src/tools/__init__.py` 中导入：

```python
from tools.new_tool import my_new_tool

ALL_TOOLS = [
    # ... 其他工具
    my_new_tool,
]
```

3. 在 `src/agents/agent.py` 中注册：

```python
from tools.new_tool import my_new_tool

def build_agent(ctx=None):
    tools = [
        # ... 其他工具
        my_new_tool,
    ]
    # ...
```

4. 在 `config/agent_llm_config.json` 中添加工具名称

### 测试工具

```python
from tools.my_new_tool import my_new_tool

# 直接调用工具
result = my_new_tool.invoke({
    "param1": "测试",
    "param2": 42
})
print(result)
```

### 调试技巧

1. **启用详细日志**：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **查看向量数据库状态**：

```python
from tools.vector_store import check_vector_store_setup
print(check_vector_store_setup.invoke({}))
```

3. **测试 RAG 流程**：

```python
from tools.rag_retriever import rag_retrieve_with_rerank
result = rag_retrieve_with_rerank.invoke({
    "query": "测试问题",
    "collection_name": "knowledge_base",
    "initial_k": 5,
    "top_n": 3,
    "use_rerank": True
})
print(result)
```

---

## ❓ 常见问题

### Q1: LSP 提示无法识别某些包（langchain_postgres, langchain_text_splitters 等）

**A**: 这些是误报，不影响实际运行。这些包已在 `requirements.txt` 中声明并正确安装。原因是 LSP 静态类型检查工具可能无法识别动态导入的包。

**解决方法**：
- 如果不影响实际运行，可以忽略这些警告
- 或者在 IDE 中配置 `PYTHONPATH` 包含项目根目录

### Q2: 是否需要保留 sentence-transformers 依赖？

**A**: 理论上可以移除，但建议保留，因为：
- 可能被其他包间接依赖
- 如果将来需要切换回本地模型，可以快速切换

如需移除，编辑 `requirements.txt`，删除相关行后重新安装：

```bash
pip install -r requirements.txt
```

### Q3: 如何切换回本地模型？

**A**: 修改以下文件：

1. **vector_store.py**: 恢复使用 HuggingFaceEmbeddings
   ```python
   from langchain_community.embeddings import HuggingFaceEmbeddings
   embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
   ```

2. **reranker_tool.py**: 恢复使用 CrossEncoder
   ```python
   from sentence_transformers import CrossEncoder
   reranker = CrossEncoder("BAAI/bge-reranker-large")
   ```

### Q4: Rerank 延迟较高，如何优化？

**A**: 有以下几种优化方案：

1. **禁用 Rerank**：在调用时设置 `use_rerank=False`
   ```python
   rag_retrieve_with_rerank.invoke({
       "query": "问题",
       "use_rerank": False
   })
   ```

2. **减少初始检索数量**：减少 `initial_k` 参数
   ```python
   rag_retrieve_with_rerank.invoke({
       "query": "问题",
       "initial_k": 10,  # 从 20 减少到 10
       "top_n": 5
   })
   ```

3. **使用更快的模型**：切换到推理速度更快的模型（需在配置中修改）

### Q5: 如何批量添加文档到知识库？

**A**: 可以编写脚本批量处理：

```python
import os
from tools.knowledge_base import add_document_to_knowledge_base

# 批量添加文档
docs_dir = "assets/knowledge/"
for filename in os.listdir(docs_dir):
    if filename.endswith(('.md', '.docx')):
        result = add_document_to_knowledge_base.invoke({
            "file_path": os.path.join(docs_dir, filename),
            "collection_name": "knowledge_base",
            "batch_size": 10
        })
        print(f"已添加: {filename}")
```

### Q6: 数据库连接失败怎么办？

**A**: 检查以下几点：

1. 确认 PostgreSQL 数据库已启动
2. 检查环境变量配置是否正确
3. 确认数据库已创建 PGVector 扩展：
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. 测试数据库连接：
   ```python
   import psycopg2
   conn = psycopg2.connect(os.getenv("PGDATABASE_URL"))
   print("连接成功")
   ```

### Q7: 如何导出知识库数据？

**A**: 使用 `search_knowledge_base` 工具获取所有数据：

```python
from tools.knowledge_base import search_knowledge_base
import json

# 获取所有文档（设置较低的 score_threshold）
result = search_knowledge_base.invoke({
    "query": "",  # 空查询返回所有结果
    "collection_name": "knowledge_base",
    "k": 1000,
    "score_threshold": 0.0
})

# 保存到文件
with open("knowledge_backup.json", "w", encoding="utf-8") as f:
    f.write(result)
```

---

## 📖 更多文档

- [RAG API 方案详细指南](docs/RAG_API_GUIDE.md)
- [AGENT.md](AGENT.md) - Agent 规范文档

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证。

---

## 📮 联系方式

如有问题或建议，请提交 Issue。
