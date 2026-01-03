# 🚀 建账规则助手系统 (Rules Agent)

基于 **LangChain + LangGraph** 架构的智能建账规则助手。本项目将非结构化的金融业务文档自动化解析为结构化规则，并提供多策略 RAG 知识检索能力。

---

## 🛠️ 核心架构
本项目采用模块化设计，确保高扩展性与鲁棒性：
- **Agent 层**：利用 LangGraph 驱动多角色（PM/Dev/Sales）对话流。
- **检索层**：支持向量检索 (BGE-M3) + 全文检索 (BM25) + LLM Rerank。
- **存储层**：PostgreSQL (PGVector) 存储向量，S3 存储原始文档。
- **ACL 防腐层**：`StorageProvider` 统一封装数据 I/O，内置 Pydantic 校验。

## 📖 快速索引

*   **[🏗️ 技术规格与架构 (docs/TECHNICAL_SPECS.md)](docs/TECHNICAL_SPECS.md)** - 系统模块划分、Dify 迁移对照及数据流。
*   **[⚙️ 配置与 RAG 指南 (docs/CONFIGURATION_RAG.md)](docs/CONFIGURATION_RAG.md)** - 环境变量、模型参数及深度检索策略。
*   **[🚀 部署与操作 SOP (docs/DEPLOYMENT_SOP.md)](docs/DEPLOYMENT_SOP.md)** - 环境安装、数据库初始化及运行指引。

## 🚀 5 分钟启动
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境
cp .env.example .env  # 填写 SiliconFlow API Key

# 3. 验证并启动
python scripts/verify_config.py
python src/main.py -m http -p 5000
```

## ✨ 关键特性
- **真实 API 驱动**：全面对接硅基流动 (SiliconFlow) API，使用 DeepSeek-V3 核心。
- **智能路由**：自动分类问题类型并选择最优检索路径。
- **极致性能**：内存缓存机制使热点查询提速 200 倍以上。

---

## 🎯 核心功能使用

### 使用 Web 界面

#### 1. 聊天界面

访问 `http://localhost:5000` 进入聊天界面：

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

访问 `http://localhost:5000/knowledge` 进入知识库管理界面：

- **概览**：查看知识库统计和最近上传的文档
- **文档管理**：查看文档列表，支持搜索和分页
- **上传文档**：支持拖拽上传和文件选择
- **知识热力图**：可视化展示主题热度
- **答案溯源**：查看 AI 回答的溯源信息
- **智能对比**：对比不同检索策略的结果

#### 3. 协作会话

访问 `http://localhost:5000/collaboration` 进入协作界面：

1. 输入昵称
2. 创建或加入会话
3. 实时协作，查看在线用户

---

## ⚙️ 配置说明

详细的配置说明请参考：[docs/CONFIGURATION_RAG.md](docs/CONFIGURATION_RAG.md)

### 配置文件位置

- `config/app_config.json` - 应用配置（数据库、模型、RAG策略等）
- `config/agent_llm_config.json` - Agent LLM 配置

### 主要配置项

| 配置块 | 说明 | 必须性 |
|--------|------|--------|
| `database` | PostgreSQL 数据库连接 | 🔴 必须 |
| `vector_store` | 向量数据库（PGVector）配置 | 🔴 必须 |
| `embedding` | Embedding 模型配置 | 🔴 必须 |
| `llm` | 主 LLM 模型配置 | 🔴 必须 |
| `rerank` | Rerank 重排序配置 | 🟡 可选 |
| `rag` | RAG 检索策略配置 | 🟡 可选 |
| `bm25` | BM25 全文检索配置 | 🟡 可选 |
| `web` | Web 服务配置 | 🟡 可选 |
| `storage` | 文件存储配置 | 🟡 可选 |

### 环境变量

```bash
# 豆包 API 配置
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

---

## 🔍 RAG 功能使用

详细的 RAG 功能使用指南请参考：[docs/CONFIGURATION_RAG.md](docs/CONFIGURATION_RAG.md)

### RAG 核心功能

1. **问题类型分类**（7种类型）
   - concept（概念型）
   - process（流程型）
   - compare（对比型）
   - factual（事实型）
   - rule（规则型）
   - troubleshooting（故障排查）
   - general（通用型）

2. **检索策略**
   - 向量检索（语义匹配）
   - BM25 检索（关键词匹配）
   - 混合检索（向量 + BM25）
   - Rerank 重排序（LLM智能评分）

3. **智能路由**
   - 自动分类问题类型
   - 自动选择最优检索策略
   - 支持手动指定策略

---

## 🛠️ 开发指南

### 添加新工具

1. 在 `src/tools/` 目录下创建工具文件
2. 使用 `@tool` 装饰器定义工具函数
3. 在 `src/agents/agent.py` 中注册工具
4. 更新 `config/app_config.json` 中的工具列表

### 测试

```bash
# RAG 完整测试
python tests/test_rag_complete.py

# BM25 检索测试
python tests/test_bm25_simple.py

# RAG 策略测试
python tests/test_rag_strategy.py

# 优化功能测试
python tests/test_optimizations.py
```

### 常用命令

```bash
# 配置验证
python scripts/verify_config.py

# 初始化数据库
python scripts/init_pgvector_db.py

# 填充知识库
python scripts/populate_knowledge_base.py

# 启动服务
python src/main.py

# 停止服务
pkill -f "python src/main.py"
```

---

## ❓ 常见问题

### 问题 1: 数据库连接失败

**错误信息**：
```
connection to server at "localhost" (::1), port 5432 failed
```

**解决方法**：
1. 检查 PostgreSQL 服务是否启动
2. 检查 `config/app_config.json` 中的连接信息
3. 确认数据库已创建：`CREATE DATABASE vector_db;`
4. 安装 PGVector 扩展：`CREATE EXTENSION vector;`

### 问题 2: Embedding API 调用失败

**错误信息**：
```
RuntimeError: 调用 Embedding API 失败: <html><head><title>404 Not Found</title></head>
```

**解决方法**：
1. 检查环境变量是否正确设置
2. 检查 API Key 是否有效
3. 测试时可以使用模拟 Embedding：设置 `"use_mock": true`

### 问题 3: LSP 提示无法识别某些包

**错误信息**：
```
Import "langchain_postgres" could not be resolved
```

**说明**：这是误报，不影响实际运行。这些包已在 requirements.txt 中声明并正确安装。

### 问题 4: 性能优化

**缓存机制**：
- 知识库统计 API 使用 60 秒缓存
- 性能提升 200-400 倍

**数据库优化**：
- 使用索引（PostgreSQL）
- 避免N+1查询
- 分页减少数据传输

---

## 📊 项目完成度

| 模块 | 完成度 | 说明 |
|------|--------|------|
| Dify 工作流迁移 | 100% | 5个工作流全部迁移完成 |
| 核心工具开发 | 100% | 34个工具全部实现 |
| RAG 检索功能 | 100% | 向量/BM25/混合检索/Rerank |
| Web 可视化界面 | 100% | 聊天/协作/RAG配置/知识库管理 |
| 知识库管理 | 100% | 文档CRUD/统计/搜索/分页 |
| 实时协作 | 100% | WebSocket/会话管理 |
| 文档处理 | 100% | 支持多种格式解析 |
| 配置管理 | 100% | 集中化配置系统 |
| 缓存优化 | 100% | 内存缓存，性能提升200-400倍 |

**总完成度：100%** ✅

---

## 📄 相关文档

- [部署与操作 SOP](docs/DEPLOYMENT_SOP.md) - 快速启动与环境部署
- [技术规格与架构](docs/TECHNICAL_SPECS.md) - 系统原理与迁移对照
- [配置与 RAG 指南](docs/CONFIGURATION_RAG.md) - 模型与检索策略深度调优
- [归档文档](docs/archive/) - 历史开发记录

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📜 许可证

本项目基于 MIT 许可证开源。
