# 建账规则助手系统 - 配置说明文档

## 目录
- [概述](#概述)
- [快速开始](#快速开始)
- [配置文件说明](#配置文件说明)
- [详细配置项](#详细配置项)
- [环境变量配置](#环境变量配置)
- [常见问题](#常见问题)

---

## 概述

本系统使用集中化配置管理，所有配置项统一在 `config/app_config.json` 文件中管理。通过修改此配置文件，可以快速调整系统的行为和参数，无需修改代码。

### 配置文件位置
```
config/app_config.json
```

### 配置版本
当前版本: `1.0.0`

---

## 快速开始

### 1. 首次配置（5分钟）

#### 步骤1: 配置数据库连接
编辑 `config/app_config.json`，修改 `database` 部分：

```json
{
  "database": {
    "host": "your-db-host",
    "port": 5432,
    "database": "vector_db",
    "user": "postgres",
    "password": "your-password"
  }
}
```

#### 步骤2: 配置Embedding模型
如果使用真实Embedding API：

```json
{
  "embedding": {
    "enabled": true,
    "provider": "doubao",
    "use_mock": false,
    "model": "doubao-embedding-large-text-250515"
  }
}
```

如果仅用于测试，可以使用模拟Embedding：

```json
{
  "embedding": {
    "use_mock": true,
    "mock_dimension": 1536
  }
}
```

#### 步骤3: 配置LLM模型
```json
{
  "llm": {
    "model": "doubao-seed-1-6-251015",
    "temperature": 0.7,
    "max_tokens": 10000
  }
}
```

#### 步骤4: 初始化数据库
```bash
cd /workspace/projects
python scripts/init_pgvector_db.py
```

#### 步骤5: 加载示例文档
```bash
python scripts/populate_knowledge_base.py
```

#### 步骤6: 启动Web服务
```bash
python src/main.py
```

访问 `http://localhost:5000` 开始使用。

---

## 配置文件说明

### 配置文件结构

配置文件分为以下几个主要部分：

| 配置块 | 说明 | 优先级 |
|--------|------|--------|
| `database` | PostgreSQL数据库连接配置 | 🔴 必须 |
| `vector_store` | 向量数据库（PGVector）配置 | 🔴 必须 |
| `embedding` | Embedding模型配置 | 🔴 必须 |
| `llm` | 主LLM模型配置 | 🔴 必须 |
| `rerank` | Rerank重排序配置 | 🟡 可选 |
| `rag` | RAG检索策略配置 | 🟡 可选 |
| `bm25` | BM25全文检索配置 | 🟡 可选 |
| `document_processing` | 文档处理配置 | 🟡 可选 |
| `web` | Web服务配置 | 🟡 可选 |
| `websocket` | WebSocket服务配置 | 🟡 可选 |
| `collaboration` | 协作会话配置 | 🟡 可选 |
| `storage` | 文件存储配置 | 🟡 可选 |
| `memory` | 对话记忆配置 | 🟡 可选 |
| `logging` | 日志配置 | 🟡 可选 |
| `features` | 功能开关配置 | 🟡 可选 |

---

## 详细配置项

### 1. 数据库配置 (database)

配置PostgreSQL数据库连接，用于存储向量数据和协作会话数据。

```json
{
  "database": {
    "enabled": true,                          // 是否启用数据库
    "type": "postgresql",                     // 数据库类型
    "host": "localhost",                      // 数据库主机地址
    "port": 5432,                             // 数据库端口
    "database": "vector_db",                  // 数据库名称
    "user": "postgres",                       // 数据库用户名
    "password": "",                           // 数据库密码（建议使用环境变量）
    "connection_pool_size": 10,               // 连接池大小
    "connection_timeout": 30,                 // 连接超时（秒）
    "notes": "数据库连接配置"
  }
}
```

**注意事项:**
- 生产环境建议使用环境变量 `PGDATABASE_URL` 或单独的环境变量来存储密码
- 需要安装PostgreSQL扩展: `CREATE EXTENSION vector;`

---

### 2. 向量存储配置 (vector_store)

配置PGVector向量数据库。

```json
{
  "vector_store": {
    "enabled": true,                          // 是否启用向量存储
    "type": "pgvector",                       // 向量存储类型
    "collection_name": "knowledge_base",      // 集合名称（表名）
    "embedding_dimension": 1024,              // 向量维度（根据Embedding模型调整）
    "use_jsonb": true,                        // 使用JSONB提升性能
    "notes": "向量存储配置"
  }
}
```

**注意事项:**
- `embedding_dimension` 必须与Embedding模型的输出维度匹配
- 豆包Embedding模型维度为 1024
- OpenAI Embedding模型维度为 1536

---

### 3. Embedding模型配置 (embedding)

配置文本向量化模型。

```json
{
  "embedding": {
    "enabled": true,                          // 是否启用Embedding
    "provider": "doubao",                     // 提供商：doubao/openai/mock
    "model": "doubao-embedding-large-text-250515",  // 模型名称
    "use_mock": false,                        // 是否使用模拟Embedding（测试用）
    "mock_dimension": 1536,                   // 模拟向量维度
    "api_key_env": "COZE_WORKLOAD_IDENTITY_API_KEY", // API Key环境变量名
    "base_url_env": "COZE_INTEGRATION_MODEL_BASE_URL",  // Base URL环境变量名
    "batch_size": 100,                        // 批处理大小
    "timeout": 60,                            // 超时时间（秒）
    "notes": "Embedding模型配置"
  }
}
```

**支持的Provider:**

| Provider | 说明 | 使用场景 |
|----------|------|----------|
| `doubao` | 豆包Embedding API | 生产环境推荐 |
| `openai` | OpenAI Embedding API | 国际化场景 |
| `mock` | 模拟Embedding（基于哈希） | 测试和开发环境 |

**测试环境快速配置:**
```json
{
  "embedding": {
    "use_mock": true,
    "mock_dimension": 1024
  }
}
```

**生产环境配置:**
```json
{
  "embedding": {
    "use_mock": false,
    "provider": "doubao",
    "model": "doubao-embedding-large-text-250515"
  }
}
```

**注意事项:**
- 使用真实API时，需要配置环境变量（见[环境变量配置](#环境变量配置)）
- 模拟Embedding仅用于测试，不具备语义理解能力

---

### 4. LLM模型配置 (llm)

配置主LLM模型，用于Agent对话和Rerank。

```json
{
  "llm": {
    "model": "doubao-seed-1-6-251015",        // 模型名称
    "api_key_env": "COZE_WORKLOAD_IDENTITY_API_KEY",  // API Key环境变量名
    "base_url_env": "COZE_INTEGRATION_MODEL_BASE_URL",  // Base URL环境变量名
    "temperature": 0.7,                      // 温度参数（0-1）
    "top_p": 0.9,                            // Top P参数（0-1）
    "max_tokens": 10000,                     // 最大输出token数
    "timeout": 600,                          // 超时时间（秒）
    "thinking": "disabled",                   // 思维模式：enabled/disabled
    "notes": "主LLM模型配置"
  }
}
```

**参数说明:**

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `temperature` | 控制输出的随机性 | 0.3-0.7（创造性任务用较高值，精确任务用较低值） |
| `top_p` | 核采样参数 | 0.9-1.0 |
| `max_tokens` | 最大输出长度 | 根据需求调整 |
| `thinking` | 是否启用思维模式 | 生产环境建议 `disabled` |

---

### 5. Rerank配置 (rerank)

配置检索结果重排序功能。

```json
{
  "rerank": {
    "enabled": true,                          // 是否启用Rerank
    "method": "llm",                          // Rerank方法：llm/api
    "llm_model": "doubao-seed-1-6-251015",   // LLM模型名称
    "temperature": 0.1,                       // 低温度保证稳定性
    "max_tokens": 1000,                      // 最大输出token数
    "top_n": 5,                              // 返回的top-k结果数
    "notes": "Rerank重排序配置"
  }
}
```

**Rerank方法:**

- `llm`: 使用大语言模型进行重排序（准确性高，速度较慢）
- `api`: 使用专门的Rerank API（速度快，需要配置专门的Rerank模型）

**使用建议:**
- 对准确性要求高的场景：使用 `llm` 方法
- 需要快速响应的场景：关闭Rerank或使用专门的Rerank API

---

### 6. RAG检索配置 (rag)

配置RAG检索的各种策略和参数。

```json
{
  "rag": {
    "enabled": true,                          // 是否启用RAG
    "default_top_k": 5,                       // 默认检索文档数
    "default_top_n": 5,                       // 默认返回文档数（Rerank后）
    "use_rerank_by_default": false,           // 默认是否使用Rerank
    "question_classification": {
      "enabled": true,                        // 是否启用问题分类
      "types": ["concept", "process", "compare", "factual", "rule", "troubleshooting", "general"]
    },
    "retrieval_strategies": {
      // 问题类型对应的检索策略
      "concept": {
        "method": "vector",                   // 检索方法：vector/bm25/hybrid/hybrid_rerank
        "use_rerank": true,
        "vector_weight": 0.6,                 // 向量检索权重
        "bm25_weight": 0.4,                  // BM25检索权重
        "reason": "概念解释类问题适合语义匹配"
      },
      // ... 其他策略
    },
    "notes": "RAG检索配置"
  }
}
```

**检索方法说明:**

| 方法 | 说明 | 适用场景 | 速度 | 准确性 |
|------|------|----------|------|--------|
| `vector` | 向量检索 | 语义理解、概念解释 | 快 | 中高 |
| `bm25` | BM25全文检索 | 精确关键词、事实查询 | 最快 | 中 |
| `hybrid` | 混合检索（向量+BM25） | 综合场景 | 中 | 高 |
| `hybrid_rerank` | 混合检索+Rerank | 高精度需求 | 慢 | 最高 |

**问题类型与推荐策略:**

| 问题类型 | 说明 | 推荐策略 |
|----------|------|----------|
| `concept` | 概念解释 | `vector` + Rerank |
| `process` | 流程说明 | `hybrid` + Rerank |
| `compare` | 对比分析 | `hybrid` + Rerank |
| `factual` | 事实查询 | `bm25` |
| `rule` | 规则解释 | `vector` + Rerank |
| `troubleshooting` | 故障排查 | `hybrid_rerank` |
| `general` | 通用问题 | `vector` |

**自定义检索策略:**

如需自定义策略，可以修改 `retrieval_strategies` 部分：

```json
{
  "custom_question_type": {
    "method": "hybrid",
    "use_rerank": true,
    "vector_weight": 0.7,
    "bm25_weight": 0.3,
    "reason": "自定义问题类型的说明"
  }
}
```

---

### 7. BM25配置 (bm25)

配置BM25全文检索参数。

```json
{
  "bm25": {
    "enabled": true,                          // 是否启用BM25
    "k1": 1.5,                                // 词频饱和度参数
    "b": 0.75,                                // 文档长度归一化参数
    "cache_dir": "/tmp/bm25_cache",           // BM25索引缓存目录
    "language": "zh",                        // 语言：zh/en
    "notes": "BM25全文检索配置"
  }
}
```

**参数说明:**

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `k1` | 控制词频饱和度 | 1.2-2.0（默认1.5） |
| `b` | 控制文档长度归一化 | 0.75（标准值） |

**调整建议:**
- `k1` 增大：提高高频词的重要性
- `k1` 减小：降低高频词的重要性
- `b` 增大：减弱文档长度的影响
- `b` 减小：增强文档长度的影响

---

### 8. 文档处理配置 (document_processing)

配置文档解析和分块参数。

```json
{
  "document_processing": {
    "chunk_size": 500,                       // 文本块大小（字符数）
    "chunk_overlap": 50,                     // 文本块重叠大小
    "supported_formats": [".md", ".txt", ".pdf", ".docx", ".doc"],  // 支持的文件格式
    "max_file_size_mb": 10,                  // 最大文件大小（MB）
    "max_documents": 50,                     // 最大文档数量
    "notes": "文档处理配置"
  }
}
```

**分块建议:**

| 文档类型 | chunk_size | chunk_overlap |
|----------|------------|---------------|
| 短文档（<1000字） | 300-500 | 30-50 |
| 中等文档（1000-5000字） | 500-800 | 50-100 |
| 长文档（>5000字） | 800-1000 | 100-150 |

---

### 9. Web服务配置 (web)

配置Flask Web服务。

```json
{
  "web": {
    "enabled": true,                          // 是否启用Web服务
    "host": "0.0.0.0",                       // 监听地址
    "port": 5000,                            // 监听端口
    "debug": false,                          // 调试模式
    "notes": "Web服务配置"
  }
}
```

**注意事项:**
- 生产环境务必设置 `debug: false`
- `host: "0.0.0.0"` 允许外部访问
- 如果使用防火墙，请确保端口开放

---

### 10. WebSocket配置 (websocket)

配置WebSocket实时通信服务。

```json
{
  "websocket": {
    "enabled": true,                          // 是否启用WebSocket
    "host": "0.0.0.0",                       // 监听地址
    "port": 5001,                            // 监听端口
    "notes": "WebSocket服务配置"
  }
}
```

---

### 11. 协作会话配置 (collaboration)

配置多人实时协作功能。

```json
{
  "collaboration": {
    "enabled": true,                          // 是否启用协作功能
    "max_sessions": 100,                      // 最大会话数
    "max_messages_per_session": 1000,         // 每个会话最大消息数
    "max_participants_per_session": 10,       // 每个会话最大参与者数
    "nickname_length_min": 1,                 // 昵称最小长度
    "nickname_length_max": 20,                // 昵称最大长度
    "notes": "协作会话配置"
  }
}
```

---

### 12. 文件存储配置 (storage)

配置文件存储方式。

```json
{
  "storage": {
    "type": "local",                          // 存储类型：local/oss/s3
    "local_path": "/workspace/projects/assets",  // 本地存储路径
    "notes": "文件存储配置"
  }
}
```

**支持的存储类型:**

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| `local` | 本地文件系统 | 开发和测试 |
| `oss` | 对象存储（阿里云） | 生产环境 |
| `s3` | 对象存储（AWS） | 国际化场景 |

**对象存储配置（示例）:**

```json
{
  "storage": {
    "type": "oss",
    "bucket": "your-bucket-name",
    "access_key_id": "your-access-key-id",
    "access_key_secret": "your-access-key-secret",
    "endpoint": "https://oss-cn-hangzhou.aliyuncs.com"
  }
}
```

---

### 13. 对话记忆配置 (memory)

配置对话历史记忆功能。

```json
{
  "memory": {
    "enabled": true,                          // 是否启用记忆
    "max_messages": 40,                       // 最大消息数（20轮对话）
    "notes": "对话记忆配置"
  }
}
```

**注意事项:**
- `max_messages` 越大，消耗的token越多
- 推荐设置为 40（20轮对话）
- 过大可能导致响应变慢或成本增加

---

### 14. 日志配置 (logging)

配置日志输出。

```json
{
  "logging": {
    "level": "INFO",                         // 日志级别：DEBUG/INFO/WARNING/ERROR
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "notes": "日志配置"
  }
}
```

---

### 15. 功能开关配置 (features)

配置各功能的启用状态。

```json
{
  "features": {
    "role_selection": true,                  // 角色选择功能
    "smart_routing": true,                   // 智能路由功能
    "hybrid_retrieval": true,                 // 混合检索功能
    "realtime_collaboration": true,           // 实时协作功能
    "rerank": true,                           // Rerank功能
    "follow_up_questions": true,              // 后续问题建议功能
    "notes": "功能开关配置"
  }
}
```

---

## 环境变量配置

部分敏感配置（如API Key、密码）建议使用环境变量配置，而非直接写在配置文件中。

### 必需的环境变量

| 环境变量 | 说明 | 示例值 |
|----------|------|--------|
| `COZE_WORKLOAD_IDENTITY_API_KEY` | 模型API密钥 | `your-api-key` |
| `COZE_INTEGRATION_MODEL_BASE_URL` | 模型服务Base URL | `https://api.example.com/v1` |

### 可选的环境变量

| 环境变量 | 说明 | 示例值 |
|----------|------|--------|
| `PGDATABASE_URL` | PostgreSQL连接字符串 | `postgresql://user:pass@host:port/db` |
| `POSTGRES_USER` | PostgreSQL用户名 | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL密码 | `your-password` |
| `POSTGRES_HOST` | PostgreSQL主机地址 | `localhost` |
| `POSTGRES_PORT` | PostgreSQL端口 | `5432` |
| `POSTGRES_DB` | PostgreSQL数据库名 | `vector_db` |

### 设置环境变量的方法

#### 方法1: 在终端中设置（临时）
```bash
export COZE_WORKLOAD_IDENTITY_API_KEY="your-api-key"
export COZE_INTEGRATION_MODEL_BASE_URL="https://api.example.com/v1"
```

#### 方法2: 在 `.env` 文件中设置（推荐）
创建 `config/.env` 文件：
```bash
COZE_WORKLOAD_IDENTITY_API_KEY=your-api-key
COZE_INTEGRATION_MODEL_BASE_URL=https://api.example.com/v1
```

然后加载环境变量：
```bash
cd /workspace/projects
python scripts/load_env.py
```

#### 方法3: 在启动脚本中设置
修改 `src/main.py`，在文件开头添加：
```python
import os
os.environ["COZE_WORKLOAD_IDENTITY_API_KEY"] = "your-api-key"
os.environ["COZE_INTEGRATION_MODEL_BASE_URL"] = "https://api.example.com/v1"
```

---

## 常见问题

### Q1: 如何切换到真实的Embedding API？

**A:** 修改 `config/app_config.json`：

```json
{
  "embedding": {
    "use_mock": false,
    "provider": "doubao",
    "model": "doubao-embedding-large-text-250515"
  }
}
```

确保配置了环境变量：
```bash
export COZE_WORKLOAD_IDENTITY_API_KEY="your-api-key"
export COZE_INTEGRATION_MODEL_BASE_URL="https://api.example.com/v1"
```

---

### Q2: 如何调整RAG检索策略？

**A:** 修改 `config/app_config.json` 中的 `rag.retrieval_strategies` 部分。

例如，将所有问题的检索策略改为混合检索：

```json
{
  "rag": {
    "retrieval_strategies": {
      "default": {
        "method": "hybrid",
        "use_rerank": true,
        "vector_weight": 0.5,
        "bm25_weight": 0.5
      }
    }
  }
}
```

---

### Q3: 如何调整文档分块大小？

**A:** 修改 `config/app_config.json`：

```json
{
  "document_processing": {
    "chunk_size": 800,        // 增大文本块
    "chunk_overlap": 100     // 增大重叠部分
  }
}
```

**注意:** 修改后需要重新导入文档：
```bash
python scripts/populate_knowledge_base.py --rebuild
```

---

### Q4: 如何提高检索准确性？

**A:** 可以尝试以下方法：

1. **启用Rerank:**
```json
{
  "rag": {
    "use_rerank_by_default": true
  }
}
```

2. **调整混合检索权重:**
```json
{
  "rag": {
    "retrieval_strategies": {
      "hybrid": {
        "vector_weight": 0.7,
        "bm25_weight": 0.3
      }
    }
  }
}
```

3. **增大检索文档数:**
```json
{
  "rag": {
    "default_top_k": 10,
    "default_top_n": 5
  }
}
```

---

### Q5: 如何提高响应速度？

**A:** 可以尝试以下方法：

1. **关闭Rerank:**
```json
{
  "rag": {
    "use_rerank_by_default": false
  }
}
```

2. **减少检索文档数:**
```json
{
  "rag": {
    "default_top_k": 3,
    "default_top_n": 3
  }
}
```

3. **使用BM25检索:**
```json
{
  "rag": {
    "retrieval_strategies": {
      "default": {
        "method": "bm25",
        "use_rerank": false
      }
    }
  }
}
```

---

### Q6: 如何添加新的文档类型支持？

**A:** 修改 `config/app_config.json`，添加新的文件格式：

```json
{
  "document_processing": {
    "supported_formats": [".md", ".txt", ".pdf", ".docx", ".doc", ".rtf", ".xlsx"]
  }
}
```

然后在 `src/tools/document_loader.py` 中添加对应的加载器。

---

### Q7: 如何配置多个LLM模型？

**A:** 当前配置文件仅支持配置一个主LLM模型。如需使用多个模型，可以在代码中动态创建多个ChatOpenAI实例。

示例：
```python
from langchain_openai import ChatOpenAI

# 主模型
main_llm = ChatOpenAI(model="doubao-seed-1-6-251015")

# Rerank专用模型（使用更小更快的模型）
rerank_llm = ChatOpenAI(model="doubao-lite-1-6-251015")
```

---

### Q8: 数据库连接失败怎么办？

**A:** 检查以下几点：

1. **确认PostgreSQL服务已启动:**
```bash
sudo systemctl status postgresql
```

2. **确认PGVector扩展已安装:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

3. **检查连接字符串:**
```bash
# 测试连接
psql -h localhost -p 5432 -U postgres -d vector_db
```

4. **检查配置文件:**
```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "database": "vector_db",
    "user": "postgres",
    "password": "your-password"
  }
}
```

---

### Q9: 如何备份数据库？

**A:** 使用 `pg_dump` 命令备份：

```bash
# 备份数据库
pg_dump -h localhost -U postgres vector_db > backup.sql

# 恢复数据库
psql -h localhost -U postgres vector_db < backup.sql
```

---

### Q10: 如何监控系统的运行状态？

**A:** 系统提供健康检查接口：

```bash
curl http://localhost:5000/health
```

返回示例：
```json
{
  "status": "healthy"
}
```

也可以查看日志文件：
```bash
tail -f logs/app.log
```

---

## 配置最佳实践

### 1. 开发环境配置

```json
{
  "embedding": {
    "use_mock": true
  },
  "web": {
    "debug": true
  },
  "logging": {
    "level": "DEBUG"
  }
}
```

### 2. 测试环境配置

```json
{
  "embedding": {
    "use_mock": false,
    "provider": "doubao"
  },
  "web": {
    "debug": false
  },
  "logging": {
    "level": "INFO"
  }
}
```

### 3. 生产环境配置

```json
{
  "embedding": {
    "use_mock": false,
    "provider": "doubao"
  },
  "web": {
    "debug": false,
    "host": "0.0.0.0"
  },
  "logging": {
    "level": "WARNING"
  },
  "database": {
    "connection_pool_size": 20,
    "connection_timeout": 30
  }
}
```

**额外注意事项:**
- 使用环境变量存储敏感信息
- 配置反向代理（如Nginx）
- 启用HTTPS
- 配置日志轮转
- 设置监控和告警

---

## 配置模板

### 完整的配置模板

详见 `config/app_config.json` 文件。

### 最小化配置模板

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "database": "vector_db",
    "user": "postgres",
    "password": ""
  },
  "embedding": {
    "use_mock": true,
    "mock_dimension": 1024
  },
  "llm": {
    "model": "doubao-seed-1-6-251015",
    "temperature": 0.7
  },
  "vector_store": {
    "collection_name": "knowledge_base"
  }
}
```

---

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本
- 支持基本的RAG检索配置
- 支持多策略路由
- 支持协作会话配置

---

## 联系与支持

如有问题或建议，请联系项目维护者。
