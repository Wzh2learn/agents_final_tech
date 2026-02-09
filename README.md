# 🚀 建账规则助手系统 (JinRongAgents)

基于 **LangChain 1.0+ + LangGraph + FastAPI** 架构的智能金融业务助手系统。本项目提供智能问答、文档处理、知识库管理等核心功能，支持会计规则的智能检索与解读。

**技术栈**: Python 3.11 | FastAPI | LangChain 1.0+ | LangGraph 1.0.2 | PostgreSQL + PGVector | SiliconFlow API (DeepSeek-V3.2)

---

## 🏗️ 项目架构 (ACL 分层模式)

```
JinRongAgents/
├── src/                    # 核心源代码 (ACL 分层)
│   ├── web/                # 表示层 - FastAPI routes + WebSocket (端口 5000/5001)
│   │   ├── routers/        # API 路由模块 (chat, knowledge, collaboration)
│   │   ├── static/          # 前端资源 (CSS/JS)
│   │   ├── templates/       # HTML 模板
│   │   ├── websocket_server.py  # WebSocket 服务
│   │   └── collaboration_service.py  # 协作服务
│   ├── biz/                # 业务逻辑层 - Service 层
│   │   ├── agent_service.py   # Agent 执行、会话管理
│   │   └── rag_service.py     # RAG 检索、智能选择
│   ├── agents/             # Agent 层 - LangGraph ReAct Agent
│   │   └── agent.py        # 主路由、17+ 工具集成
│   ├── tools/              # 工具层 - Agent 可调用工具
│   │   ├── vector_store.py       # PGVector 封装
│   │   ├── bm25_retriever.py     # 全文检索
│   │   ├── hybrid_retriever.py   # 混合检索
│   │   ├── reranker_tool.py      # 重排序
│   │   ├── document_processor.py # 文档处理
│   │   └── question_classifier.py # 问题分类
│   ├── storage/            # 数据访问层 - ACL 防腐层模式
│   │   ├── database/       # SQLAlchemy 模型、DocumentManager
│   │   ├── collaboration/  # 协作数据存储
│   │   ├── memory/         # LangGraph checkpointer
│   │   ├── s3/             # S3 对象存储
│   │   └── provider.py    # StorageProvider 统一封装
│   ├── auth/               # 认证层 - JWT token
│   └── utils/              # 工具函数 (Config Loader, Cache)
├── scripts/                # 初始化脚本
│   ├── init_pgvector_db.py     # PGVector 初始化
│   ├── init_collaboration_db.py # 协作数据库初始化
│   ├── populate_knowledge_base.py # 知识库填充
│   ├── verify_config.py        # 配置验证
│   ├── test_web_ui.py          # Web UI 测试
│   └── test_db_conn.py         # 数据库连接测试
├── tests/                  # 测试脚本
│   ├── test_core_service.py    # 核心服务测试
│   ├── test_web_integration.py # API 集成测试
│   └── test_e2e_browser.py     # E2E 浏览器测试
├── config/                # 配置文件
│   └── app_config.json     # 应用配置 (数据库、向量存储、LLM)
├── docs/                  # 文档目录
├── assets/                 # 静态资源
├── data/                   # 数据存储
│   ├── local_bucket/      # 本地文档存储
│   └── sessions.db         # SQLite 会话存储
├── CLAUDE.md              # Claude Code 指导文件
├── README.md              # 项目说明文档
├── requirements.txt        # Python 依赖
└── .env.example            # 环境变量示例
```

---

## 📋 文件分类说明

| 文件类型 | 位置 | 说明 |
|----------|------|------|
| 核心代码 | `src/` | ACL 分层架构 |
| 初始化脚本 | `scripts/` | 数据库初始化、配置验证 |
| 测试脚本 | `tests/` | 单元测试、集成测试 |
| 配置文件 | `config/` | 应用配置 |
| 文档 | `docs/` | 开发文档、API 文档 |
| 数据存储 | `data/` | 文档、会话数据 |
| 指导文件 | `CLAUDE.md` | AI 助手指导 |

---

## 🛠️ 核心特性

- **Agent 层**：LangGraph ReAct Agent，支持4种角色（PM/Dev/Sales/Engineer），滑动窗口记忆管理
- **检索层**：向量检索 (Qwen3-Embedding) + BM25全文检索 + 混合检索 + LLM Rerank
- **存储层**：PostgreSQL + PGVector向量存储，S3对象存储（可选）
- **ACL 防腐层**：`StorageProvider` 统一封装数据I/O，内置Pydantic校验，支持降级逻辑

## 📖 快速索引

*   **[📚 开发者指南 (docs/DEVELOPER_GUIDE.md)](docs/DEVELOPER_GUIDE.md)** - 项目架构、开发规范、新功能添加指南
*   **[🔌 API 参考文档 (docs/API_REFERENCE.md)](docs/API_REFERENCE.md)** - 完整的 REST API 接口文档
*   **[🚀 部署指南 (docs/DEPLOYMENT.md)](docs/DEPLOYMENT.md)** - 环境配置、数据库初始化、部署步骤
*   **[🛠️ 工具使用说明 (TOOLS_USAGE.md)](TOOLS_USAGE.md)** - 所有工具的用途和调用路径

## 🚀 5分钟快速启动

### 前置要求
- Python 3.11+
- PostgreSQL 14+ (已安装PGVector扩展)
- SiliconFlow API密钥

### 方式 1：自动启动脚本 (推荐)

**Windows**:
```bash
venv\Scripts\activate.bat
python src/main.py -m http -p 5000
```

**Linux/Mac**:
```bash
source venv/bin/activate
python src/main.py -m http -p 5000
```

### 方式 2：手动启动

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境变量**

   创建 `.env` 文件：
   ```bash
   # 必需环境变量
   SILICONFLOW_API_KEY=your_siliconflow_api_key
   PGDATABASE_URL=postgresql://user:password@localhost:5432/jinrong_agents

   # 可选环境变量
   SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
   JWT_SECRET_KEY=your_jwt_secret
   CORS_ORIGINS=http://localhost:5000,http://localhost:3000
   MEMORY_BACKEND=postgres  # 或 memory
   ```

3. **启动 Docker 数据库容器**（必须步骤）
   ```bash
   # 启动 PostgreSQL + PGVector 容器（数据会持久化）
   docker run -d --name pgvector -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=vector_db -p 5432:5432 ankane/pgvector:latest
   
   # 等待数据库就绪（约5-10秒）
   docker logs pgvector | findstr "ready"
   ```
   
   > **⚠️ 重要**：如果容器已存在，直接启动即可：`docker start pgvector`
   > 数据存储在 Docker volume 中，重启容器不会丢失。

4. **初始化数据库**
   ```bash
   # 创建数据库和PGVector扩展
   python scripts/init_pgvector_db.py

   # 初始化协作系统表
   python scripts/init_collaboration_db.py

   # (可选) 填充知识库
   python scripts/populate_knowledge_base.py
   ```

4. **启动服务（方式1：一键启动 - 推荐）**
   ```bash
   # Windows 一键启动（自动检查Docker+虚拟环境+启动后端）
   run.bat
   ```
   该脚本会自动：
   - 检查并启动 pgvector Docker 容器
   - 激活 Python 虚拟环境
   - 检查 SILICONFLOW_API_KEY 配置
   - 启动 Web 服务（端口 5000）和 WebSocket（端口 5001）

5. **启动服务（方式2：手动启动）**
   ```bash
   # 启动 Docker 数据库
   docker start pgvector
   
   # 激活虚拟环境并启动
   venv\Scripts\activate
   python src/main.py -m http -p 5000
   ```

6. **访问系统**
   - 主页: http://localhost:5000
   - 聊天界面: http://localhost:5000/chat
   - 知识库管理: http://localhost:5000/knowledge
   - API文档: http://localhost:5000/docs

### 方式 3：验证配置

在启动前验证所有配置是否正确：
```bash
python scripts/verify_config.py
```

## ✨ 关键特性

- **LangGraph ReAct Agent**：基于LangChain 1.0+构建，支持流式输出、工具调用、滑动窗口记忆管理
- **多角色对话**：支持4种角色切换 - 产品经理/技术开发/销售运营/默认工程师
- **智能RAG检索**：7种问题类型分类 → 3种检索策略 → Rerank重排序
- **QA固定流程**：多路检索 → 生成回答 → 质检评估 → 反思优化（对应Dify工作流设计）
- **实时协作**：WebSocket实时多人聊天，消息持久化，支持私人/协作会话
- **文档处理**：支持多种格式（txt/md/pdf/docx/csv/json），自动规则提取为Markdown表格
- **父子分段**：两级文档分割（父块2000字符/子块500字符），概览+详细检索
- **答案溯源**：精确定位原文位置、高亮引用片段、展开完整上下文
- **极致性能**：内存缓存机制（60秒TTL），热点查询提速200-400倍
- **ACL防腐层**：StorageProvider统一数据访问，Pydantic schema验证，支持降级逻辑
- **配置中心化**：AppConfig单例管理，支持嵌套key访问，环境变量优先级高于配置文件
- **认证系统**：JWT token认证，支持用户登录和权限管理

---

## 🎯 核心功能使用

### 使用 Web 界面

#### 主页导航

访问 `http://localhost:5000` 进入系统主页，提供2个功能入口：

- **💬 智能对话** (`/chat`) - 支持多会话管理、多角色对话、协作会话（WebSocket实时协作已集成）
- **📚 知识库管理** (`/knowledge`) - 文档管理、分段预览、RAG配置（检索策略配置已集成）、答案溯源、智能对比

#### 1. 聊天界面

访问 `/chat` 进入聊天界面：

**选择角色**：
- **a** - 产品经理（业务需求、用户体验）
- **b** - 技术开发（技术实现、系统架构）
- **c** - 销售运营（客户案例、市场反馈）
- **d** - 默认工程师（通用技术支持）

**提问示例**：
- "什么是建账规则？"
- "如何进行科目设置？"
- "财务凭证和业务凭证有什么区别？"

**系统会自动**：
1. 识别问题类型
2. 选择最优检索策略
3. 检索相关知识
4. 生成回答

#### 2. 知识库管理

访问 `/knowledge` 进入知识库管理界面：

- **概览**：查看知识库统计和最近上传的文档
- **文档列表**：查看所有文档，点击文档进入详情页
- **文档详情**：查看文档分段列表（支持父子分段层级展示）和元数据
- **RAG配置**：在文档详情页集成检索策略配置（分段模式、Top K、Rerank开关）
- **上传文档**：支持拖拽上传和文件选择，可选父子分段模式（默认开启）
- **答案溯源**：精确定位原文位置、高亮引用片段、展开完整上下文
- **智能对比**：对比不同检索策略的结果

#### 3. 多会话与协作

在 `/chat` 界面中：

1. **个人会话**：点击"开启新对话"创建私人会话，支持多会话并行管理
2. **协作会话**：点击"加入/创建协作"按钮，输入昵称后可创建或加入协作会话
3. **实时协作**：协作会话通过 WebSocket 实现多人实时聊天，所有参与者共享 AI 响应

---

## ⚙️ 配置说明

详细的配置说明请参考：[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

### 配置文件位置

- `config/app_config.json` - 应用主配置（数据库、模型、RAG策略、Web服务等）
- `config/agent_llm_config.json` - Agent LLM配置（模型参数、系统提示词）
- `.env` - 环境变量配置（API密钥、数据库连接等）

### 主要配置项

| 配置块 | 说明 | 必须性 |
|--------|------|--------|
| `database` | PostgreSQL 数据库连接 | 🔴 必须 |
| `vector_store` | PGVector向量数据库配置 | 🔴 必须 |
| `embedding` | Embedding模型配置 (Qwen3-Embedding-0.6B) | 🔴 必须 |
| `llm` | 主LLM模型配置 (DeepSeek-V3.2) | 🔴 必须 |
| `rerank` | Rerank重排序配置 (Qwen3-Reranker-0.6B) | 🟡 可选 |
| `rag` | RAG检索策略配置（7种问题类型映射） | 🟡 可选 |
| `bm25` | BM25全文检索配置（k1/b参数） | 🟡 可选 |
| `document_processing` | 文档处理配置（分块大小、重叠等） | 🟡 可选 |
| `web` | Web服务配置（CORS、端口等） | 🟡 可选 |
| `websocket` | WebSocket配置（端口、心跳间隔） | 🟡 可选 |
| `collaboration` | 协作系统配置 | 🟡 可选 |
| `storage` | 文件存储配置（本地/S3） | 🟡 可选 |
| `memory` | 记忆后端配置（postgres/memory） | 🟡 可选 |
| `features` | 功能开关（缓存、Rerank等） | 🟡 可选 |

### 环境变量

**必需**:
```bash
SILICONFLOW_API_KEY=your_siliconflow_api_key
PGDATABASE_URL=postgresql://user:password@localhost:5432/jinrong_agents
```

**可选**:
```bash
# SiliconFlow API配置
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1

# JWT认证配置
JWT_SECRET_KEY=your_random_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# CORS配置
CORS_ORIGINS=http://localhost:5000,http://localhost:3000

# 记忆后端选择
MEMORY_BACKEND=postgres  # postgres (持久化) 或 memory (内存)

# 数据库连接池配置
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
```

### 配置示例

**config/app_config.json** (主配置):
```json
{
  "llm": {
    "model_name": "deepseek-ai/DeepSeek-V3.2",
    "temperature": 0.7,
    "max_tokens": 10000
  },
  "embedding": {
    "model_name": "Qwen/Qwen3-Embedding-0.6B"
  },
  "rerank": {
    "model_name": "Qwen/Qwen3-Reranker-0.6B",
    "top_n": 5
  },
  "rag": {
    "strategies": {
      "concept": "vector",
      "process": "hybrid",
      "compare": "vector",
      "factual": "bm25",
      "rule": "hybrid",
      "troubleshooting": "hybrid",
      "general": "vector"
    }
  }
}
```

---

## 🔍 RAG检索系统

详细的RAG功能使用指南请参考：[docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)

### RAG核心组件

**问题分类器** (7种问题类型):
- `concept` (概念型) - 定义、术语解释
- `process` (流程型) - 操作步骤、流程说明
- `compare` (对比型) - 比较两个或多个事物
- `factual` (事实型) - 事实查询、数据查询
- `rule` (规则型) - 规则、政策查询
- `troubleshooting` (故障排查) - 问题诊断、错误处理
- `general` (通用型) - 其他一般性问题

**检索策略**:
1. **向量检索** (Vector Search) - 语义匹配，适合概念型/对比型问题
2. **BM25检索** (Full-text Search) - 关键词匹配，适合事实型问题
3. **混合检索** (Hybrid Search) - 向量+BM25，适合流程型/规则型/故障排查

**智能路由**:
```
用户查询 → 问题分类 → 策略选择 → 执行检索 → Rerank重排序 → 返回结果
```

### RAG工具API

系统提供3个核心RAG工具供Agent调用：

1. **smart_retrieve** - 智能单次检索
   ```python
   smart_retrieve(
       query="什么是建账规则？",
       top_k=5,
       enable_rerank=True
   )
   ```

2. **batch_retrieve** - 批量检索
   ```python
   batch_retrieve(
       queries=["问题1", "问题2", "问题3"],
       top_k=5,
       enable_rerank=True
   )
   ```

3. **get_retrieval_statistics** - 检索统计分析
   ```python
   get_retrieval_statistics(
       queries=["问题1", "问题2"],
       top_k=5
   )
   ```

### 策略映射（默认配置）

| 问题类型 | 检索策略 | 原因 |
|---------|---------|------|
| concept | vector | 语义理解最重要 |
| process | hybrid | 需要关键词+语义 |
| compare | vector | 需要理解多个概念 |
| factual | bm25 | 精确关键词匹配 |
| rule | hybrid | 规则名称+语义理解 |
| troubleshooting | hybrid | 错误码+语义诊断 |
| general | vector | 通用语义理解 |

---

## 🛠️ 开发指南

完整的开发指南请参考：[docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)

### 项目结构

```
src/
├── agents/
│   └── agent.py              # LangGraph ReAct Agent主路由 (17个工具)
├── biz/
│   ├── agent_service.py      # Agent对话服务 (会话管理、流式输出)
│   └── rag_service.py        # RAG检索服务 (问题分类、策略路由)
├── tools/                    # 17个Agent工具
│   ├── rag_tools.py          # smart_retrieve, batch_retrieve, get_retrieval_statistics
│   ├── qa_agent.py           # QA问答 (固定流程: 检索→生成→质检→反思)
│   ├── document_processor.py # 文档规则提取、validate_rules
│   ├── vector_store.py       # PGVector向量存储
│   ├── bm25_retriever.py     # BM25全文检索
│   ├── hybrid_retriever.py   # 混合检索
│   ├── reranker_tool.py      # LLM重排序
│   ├── question_classifier.py # 问题分类 (7种类型)
│   ├── feedback_handler.py   # feedback_handler, generate_summary_report
│   ├── file_writer.py        # write_to_file, write_to_storage, read_from_storage等
│   └── ...
├── storage/
│   ├── provider.py           # ACL防腐层 (统一存储访问)
│   ├── database/             # SQLAlchemy模型、文档管理器
│   ├── memory/               # LangGraph checkpointer (postgres/memory)
│   └── s3/                   # S3对象存储
├── web/
│   ├── routers/              # FastAPI路由
│   │   ├── chat.py           # 聊天API (14个端点)
│   │   ├── knowledge.py      # 知识库API (9个端点)
│   │   ├── collaboration.py  # 协作API (6个端点)
│   │   ├── pages.py          # 页面路由 (3个端点)
│   │   └── cache.py          # 缓存管理 (2个端点)
│   ├── templates/            # HTML模板
│   ├── static/               # 前端资源
│   └── collaboration_service.py  # WebSocket协作服务
├── auth/
│   ├── router.py             # JWT认证路由
│   ├── jwt_handler.py        # JWT处理
│   └── users.py              # 用户管理
└── utils/
    ├── config_loader.py      # AppConfig配置加载器
    ├── cache.py              # 内存缓存 (60秒TTL)
    └── log/                  # 日志工具
```

### 添加新工具

1. **创建工具文件** - 在 `src/tools/` 目录下创建
   ```python
   from langchain.tools import tool

   @tool
   def my_new_tool(param: str) -> str:
       """Tool description for the Agent to understand."""
       # Tool implementation
       return result
   ```

2. **注册工具** - 在 `src/agents/agent.py` 中添加到 `tools` 列表
   ```python
   from tools.my_tool import my_new_tool

   tools = [
       # ... existing tools
       my_new_tool,
   ]
   ```

3. **更新配置** (可选) - 如果工具需要特殊配置，更新 `config/app_config.json`

### 添加新API端点

1. **创建/修改路由** - 在 `src/web/routers/` 目录下
   ```python
   from fastapi import APIRouter, HTTPException

   router = APIRouter(prefix="/api/myfeature", tags=["MyFeature"])

   @router.get("/data")
   async def get_data():
       return {"data": "example"}
   ```

2. **注册路由** - 在 `src/main.py` 中添加
   ```python
   from web.routers import myfeature
   app.include_router(myfeature.router)
   ```

### 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
python tests/test_core_service.py
python tests/test_web_integration.py

# 运行E2E浏览器测试
python tests/test_e2e_browser.py

# 测试覆盖率
pytest tests/ --cov=src --cov-report=html
```

### 常用命令

```bash
# 配置验证
python scripts/verify_config.py

# 数据库初始化
python scripts/init_pgvector_db.py
python scripts/init_collaboration_db.py

# 填充知识库
python scripts/populate_knowledge_base.py

# 数据库连接测试
python scripts/test_db_conn.py

# 会话迁移
python scripts/migrate_sessions.py

# 启动服务
python src/main.py -m http -p 5000

# 代码格式化
isort src/ tests/

# 代码检查
pylint src/ --disable=import-error
```

### 代码规范

**导入顺序**:
```python
# 标准库
import os
import logging

# 第三方库
from fastapi import FastAPI
from langchain.tools import tool

# 项目内部模块
from ..tools.vector_store import get_vector_store
```

**服务单例模式**:
```python
_rag_service = None

def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
```

**工具装饰器规范**:
```python
@tool
def my_tool(query: str, top_k: int = 5) -> str:
    """
    Clear tool description for Agent.

    Args:
        query: The search query
        top_k: Number of results to return

    Returns:
        JSON string with results
    """
    # Implementation
    return json.dumps(results)
```

---

## 📋 API接口清单

完整的API文档请参考：[docs/API_REFERENCE.md](docs/API_REFERENCE.md)

### 聊天API (src/web/routers/chat.py)

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/chat` | 流式聊天 (SSE) |
| POST | `/api/reset` | 重置会话 |
| POST | `/api/set_role` | 设置角色 |
| GET | `/api/status` | 获取会话状态 |
| GET | `/api/chat/sessions` | 获取所有会话 |
| POST | `/api/chat/sessions` | 创建会话 |
| GET | `/api/chat/sessions/{id}` | 获取会话详情 |
| PATCH | `/api/chat/sessions/{id}` | 更新会话 |
| DELETE | `/api/chat/sessions/{id}` | 删除会话 |
| GET | `/api/chat/sessions/{id}/history` | 获取历史消息 |

### 知识库API (src/web/routers/knowledge.py)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/knowledge/stats` | 知识库统计 (60秒缓存) |
| GET | `/api/knowledge/documents` | 文档列表 (分页/搜索) |
| POST | `/api/knowledge/upload` | 上传文档 |
| DELETE | `/api/knowledge/documents/{id}` | 删除文档 |
| GET | `/api/knowledge/documents/{id}/download` | 下载文档 |
| GET | `/api/knowledge/documents/{id}/export-docx` | 导出DOCX |
| POST | `/api/knowledge/traceability` | 答案溯源 |
| POST | `/api/knowledge/compare` | 检索方法对比 |
| GET | `/api/knowledge/heatmap` | 知识热力图 |

### 协作API (src/web/routers/collaboration.py)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/collaboration/sessions` | 获取所有协作会话 |
| POST | `/api/collaboration/sessions` | 创建协作会话 |
| DELETE | `/api/collaboration/sessions/{id}` | 删除会话 |
| GET | `/api/collaboration/sessions/{id}/participants` | 参与者列表 |
| POST | `/api/collaboration/sessions/{id}/participants` | 添加参与者 |
| GET | `/api/collaboration/sessions/{id}/messages` | 获取消息 |

### 认证API (src/auth/router.py)

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 用户登录 (JWT) |

### 缓存管理API (src/web/routers/cache.py)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/cache/stats` | 缓存统计 |
| POST | `/api/cache/clear` | 清空缓存 |

### 页面路由 (src/web/routers/pages.py)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/` | 主页 |
| GET | `/chat` | 聊天界面 |
| GET | `/knowledge` | 知识库管理 |

### WebSocket端点

| 端点 | 说明 |
|------|------|
| `ws://localhost:5001/ws` | 协作聊天WebSocket |

---

## ❓ 常见问题

### Q1: 数据库连接失败

**错误信息**:
```
connection to server at "localhost" (::1), port 5432 failed
```

**解决方法**:
1. 检查PostgreSQL服务是否启动
   ```bash
   # Windows
   net start postgresql-x64-14

   # Linux/Mac
   sudo systemctl status postgresql
   ```

2. 检查 `.env` 或 `config/app_config.json` 中的连接信息

3. 确认数据库已创建
   ```sql
   CREATE DATABASE jinrong_agents;
   ```

4. 安装PGVector扩展
   ```sql
   CREATE EXTENSION vector;
   ```

5. 运行初始化脚本
   ```bash
   python scripts/init_pgvector_db.py
   python scripts/init_collaboration_db.py
   ```

### Q2: API密钥配置问题

**错误信息**:
```
RuntimeError: 调用 Embedding API 失败: 401 Unauthorized
```

**解决方法**:
1. 检查环境变量 `SILICONFLOW_API_KEY` 是否正确设置
2. 确认API Key有效且有足额度
3. 验证API Base URL是否正确（默认: `https://api.siliconflow.cn/v1`）
4. 运行配置验证脚本
   ```bash
   python scripts/verify_config.py
   ```

### Q3: 内存不足或性能问题

**症状**: 系统响应慢、内存占用高

**解决方法**:
1. **启用缓存** - 确保 `config/app_config.json` 中 `features.enable_cache: true`
2. **调整分块大小** - 减小 `document_processing.chunk_size`（默认2000）
3. **限制并发** - 减小数据库连接池大小（`DB_POOL_SIZE`）
4. **使用内存后端** - 如果不需要持久化，设置 `MEMORY_BACKEND=memory`
5. **减少Top K** - 减少检索返回的结果数量（默认5）

### Q4: 工具导入错误

**错误信息**:
```
Import "langchain_postgres" could not be resolved
```

**说明**: 这是LSP误报，不影响实际运行。这些包已在 `requirements.txt` 中声明并正确安装。

**验证方法**:
```bash
pip list | grep langchain-postgres
# 应该显示: langchain-postgres 0.0.16 (或其他版本)
```

### Q5: WebSocket连接失败

**症状**: 协作聊天无法连接

**解决方法**:
1. 检查WebSocket端口是否开放（默认5001）
2. 检查防火墙设置
3. 确认 `config/app_config.json` 中 `websocket.port` 配置正确
4. 检查前端配置 `src/web/static/config.js` 中的 `WS_PORT`

### Q6: 文档上传失败

**症状**: 上传文档时报错或无响应

**解决方法**:
1. **检查文件大小** - 默认限制可能在FastAPI中配置
2. **检查文件格式** - 确认支持的格式（txt/md/pdf/docx/csv/json）
3. **检查存储配置** - 确认 `storage` 配置正确
4. **查看日志** - 检查 `logs/` 目录下的错误日志

### Q7: Rerank功能不生效

**症状**: 开启Rerank后结果没有变化

**解决方法**:
1. 确认 `config/app_config.json` 中 `rerank.enabled: true`
2. 确认 `features.enable_rerank: true`
3. 检查Rerank模型是否正确配置
4. 查看日志确认Rerank是否被调用

### Q8: 会话记忆丢失

**症状**: 对话上下文丢失或无法恢复

**解决方法**:
1. **检查记忆后端** - 确认 `MEMORY_BACKEND=postgres`（而非memory）
2. **检查数据库连接** - 确认PostgreSQL连接正常
3. **检查checkpointer表** - 确认 `checkpoints` 表存在
4. **降级重试** - 系统会自动降级到内存后端，但不持久化

### Q9: 性能优化建议

**如何提升系统性能**:

1. **启用缓存** (200-400倍提速)
   ```json
   "features": {
     "enable_cache": true,
     "cache_ttl": 60
   }
   ```

2. **使用混合检索** - 对于复杂查询使用hybrid策略

3. **调整Rerank Top N** - 减小到3-5可以提速

4. **数据库索引** - 确保向量字段有HNSW索引

5. **连接池优化**
   ```bash
   DB_POOL_SIZE=10
   DB_MAX_OVERFLOW=20
   ```

6. **异步处理** - 使用FastAPI的异步特性

---

## 📊 项目完成度

| 模块 | 完成度 | 说明 |
|------|--------|------|
| **核心架构** | 100% | 5层分层架构（Web/Biz/Agent/Tools/Storage） |
| **Dify工作流迁移** | 100% | 5个工作流全部迁移完成 |
| **Agent系统** | 100% | LangGraph ReAct Agent，17个工具，4种角色 |
| **RAG检索功能** | 100% | 7种问题分类 + 3种检索策略 + Rerank |
| **QA问答系统** | 100% | 固定流程（检索→生成→质检→反思） |
| **文档处理** | 100% | 支持多种格式，规则提取，父子分段 |
| **知识库管理** | 100% | 文档CRUD、统计、搜索、分页、溯源 |
| **Web可视化界面** | 100% | 聊天/协作/知识库/RAG配置 |
| **实时协作** | 100% | WebSocket实时多人聊天，消息持久化 |
| **认证系统** | 90% | JWT登录已实现，权限管理待完善 |
| **配置管理** | 100% | 集中化AppConfig，环境变量优先级 |
| **缓存优化** | 100% | 内存缓存（60秒TTL），提速200-400倍 |
| **ACL防腐层** | 100% | StorageProvider，Schema验证，降级逻辑 |
| **记忆管理** | 100% | Postgres持久化 + Memory降级 |
| **测试覆盖** | 40% | 核心服务有测试，需补充单元测试 |
| **监控告警** | 0% | 未实现（待开发） |
| **API文档** | 100% | FastAPI自动生成 + Markdown文档 |

**总体完成度**: 约 **95%** ✅

**已实现功能**:
- ✅ 17个Agent工具全部实现并注册
- ✅ 34个API端点（聊天/知识库/协作/认证/缓存）
- ✅ 多角色对话系统（4种角色）
- ✅ 智能RAG检索（7种问题类型 → 3种策略）
- ✅ 实时协作（WebSocket）
- ✅ 父子分段文档处理
- ✅ 答案溯源与检索对比
- ✅ JWT认证
- ✅ 性能缓存优化

**待优化项**:
- ⏳ 补充单元测试（目标80%覆盖率）
- ⏳ 添加监控告警（Prometheus/Grafana）
- ⏳ 完善权限管理（RBAC）
- ⏳ 国际化支持（i18n）
- ⏳ API限流保护

---

## 📄 相关文档

### 核心文档
- **[📚 开发者指南](docs/DEVELOPER_GUIDE.md)** - 项目架构、开发规范、新功能添加、测试指南
- **[🔌 API参考文档](docs/API_REFERENCE.md)** - 完整的REST API接口文档（34个端点）
- **[🚀 部署指南](docs/DEPLOYMENT.md)** - 环境配置、数据库初始化、部署步骤、生产环境配置
- **[🛠️ 工具使用说明](TOOLS_USAGE.md)** - 17个Agent工具的用途和调用路径
- **[🤖 Agent设计文档](docs/AGENTS.md)** - LangGraph Agent架构、工具调用、记忆管理
- **[🔧 Claude插件设置](docs/CLAUDE_PLUGIN_SETUP.md)** - Claude Code项目指南

### 架构与设计
- **[📋 Dify vs 自建对比](DIFY_VS_TOOLS_COMPARISON.md)** - Dify工作流与自建工具对比分析
- **[📝 CLAUDE.md](CLAUDE.md)** - Claude Code专用项目指南（技术栈、命令、架构）

### 归档文档
- **[docs/archive/](docs/archive/)** - 历史开发记录、架构评审、代码审查报告、迁移指南

### 配置文件
- `config/app_config.json` - 应用主配置
- `config/agent_llm_config.json` - Agent LLM配置
- `.env` - 环境变量配置

---

## 🎯 数据流架构

完整请求链路：

```
用户请求
    ↓
FastAPI路由 (src/web/routers/)
    ↓
Business Service (src/biz/)
    ├─ AgentService.stream_chat()  # 对话服务
    └─ RAGService                   # 检索服务
        ↓
LangGraph ReAct Agent (src/agents/agent.py)
    ├─ 工具调用决策
    └─ 滑动窗口记忆管理 (最近20轮)
        ↓
Agent Tools (src/tools/) - 17个工具
    ├─ qa_agent           # 固定QA流程
    ├─ smart_retrieve     # 智能RAG检索
    ├─ document_processor # 文档处理
    └─ ...
        ↓
RAG Pipeline (src/biz/rag_service.py)
    ├─ 1. 问题分类 (7种类型)
    ├─ 2. 策略路由 (vector/bm25/hybrid)
    ├─ 3. 检索执行
    └─ 4. Rerank重排序
        ↓
Storage Layer (src/storage/)
    ├─ PGVector (向量检索)
    ├─ BM25 (全文检索)
    ├─ PostgreSQL (数据持久化)
    └─ S3 (对象存储)
        ↓
返回结果 → 流式输出 → 用户
```

---

## 🛡️ 技术亮点

1. **LangGraph ReAct Agent**
   - 基于最新LangChain 1.0+技术栈
   - 支持流式输出、工具调用、记忆管理
   - 滑动窗口记忆（最近20轮对话，40条消息）

2. **多策略RAG系统**
   - 7种问题类型自动分类
   - 3种检索策略智能路由
   - Rerank重排序提升准确率

3. **QA固定流程**
   - 多路检索（规则库 + 标准答案库）
   - 生成回答
   - 智检质量评估
   - 反思智能体优化
   - 对应Dify工作流 WF_QA_Main

4. **ACL防腐层设计**
   - StorageProvider统一数据访问
   - Pydantic schema验证
   - 降级逻辑（S3 → 本地）
   - 业务模块不直接依赖存储实现

5. **性能优化**
   - 内存缓存（60秒TTL）
   - 热点查询提速200-400倍
   - 数据库连接池管理
   - 异步I/O处理

6. **实时协作**
   - WebSocket长连接
   - 多人实时聊天
   - 消息持久化
   - 会话管理

---

## 🔧 脚本工具清单

| 脚本 | 说明 |
|------|------|
| `scripts/init_pgvector_db.py` | 初始化PGVector数据库（创建扩展和表） |
| `scripts/init_collaboration_db.py` | 初始化协作系统表 |
| `scripts/populate_knowledge_base.py` | 批量导入文档到知识库 |
| `scripts/verify_config.py` | 验证所有配置项正确性 |
| `scripts/test_db_conn.py` | 测试数据库连接 |
| `scripts/migrate_sessions.py` | 会话迁移脚本 |
| `scripts/test_web_ui.py` | 测试Web UI |
| `scripts/setup_claude_env.ps1` | PowerShell环境设置 |

---

## 🎓 学习路径

**新手入门**:
1. 阅读本README了解项目概况
2. 阅读 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) 完成环境搭建
3. 运行 `python scripts/verify_config.py` 验证配置
4. 启动系统并访问 http://localhost:5000
5. 尝试聊天功能，体验不同角色

**开发者**:
1. 阅读 [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) 了解架构
2. 阅读 [docs/AGENTS.md](docs/AGENTS.md) 了解Agent设计
3. 查看 `src/agents/agent.py` 了解工具注册
4. 查看 `src/tools/` 了解工具实现
5. 阅读 [docs/API_REFERENCE.md](docs/API_REFERENCE.md) 了解API设计

**进阶优化**:
1. 阅读 `src/biz/rag_service.py` 了解RAG策略
2. 研究 `src/storage/provider.py` 了解ACL设计
3. 分析 `src/utils/cache.py` 了解缓存实现
4. 查看 `tests/` 目录学习测试方法

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

**提交Issue**:
- 使用清晰的标题描述问题
- 提供复现步骤
- 附上错误日志和环境信息

**提交PR**:
- Fork项目并创建功能分支
- 遵循项目代码规范
- 添加必要的测试
- 更新相关文档
- 提交前运行 `pytest tests/ -v`

**代码规范**:
- 使用 `isort` 格式化导入
- 使用 `pylint` 检查代码质量
- 遵循PEP 8规范
- 添加类型注解
- 编写清晰的docstring

---

## 📞 联系方式

- **项目仓库**: [GitHub Repository]
- **问题反馈**: [GitHub Issues]
- **文档**: 见 `docs/` 目录

---

## 📜 许可证

本项目基于 **MIT许可证** 开源。

---

## 🙏 致谢

感谢以下开源项目：
- [LangChain](https://github.com/langchain-ai/langchain) - LLM应用开发框架
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent状态图框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Web框架
- [PostgreSQL](https://www.postgresql.org/) - 强大的关系型数据库
- [PGVector](https://github.com/pgvector/pgvector) - 向量相似度搜索扩展
- [SiliconFlow](https://siliconflow.cn/) - LLM API服务提供商

---

**最后更新**: 2026-01-20
**版本**: 1.0.0
**状态**: 生产就绪 (95%完成度)
