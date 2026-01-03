# 建账规则助手 - 快速开始指南

## 前置要求

- Python 3.8+
- PostgreSQL 12+ (已安装 PGVector 扩展)
- 豆包 API Key (可选，测试环境可使用模拟 Embedding)

## 5 分钟快速启动

### 步骤 1: 克隆项目（已完成）

项目已在 `/workspace/projects` 目录中。

### 步骤 2: 安装依赖（已完成）

```bash
cd /workspace/projects
pip install -r requirements.txt
```

### 步骤 3: 配置数据库

编辑 `config/app_config.json`，修改数据库连接信息：

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

### 步骤 4: 初始化数据库

```bash
cd /workspace/projects
python scripts/init_pgvector_db.py
```

### 步骤 5: 验证配置

```bash
python scripts/verify_config.py
```

### 步骤 6: 启动服务

```bash
python src/main.py
```

### 步骤 7: 访问界面

打开浏览器，访问 `http://localhost:5000`

## 测试系统

### 测试 1: 配置验证

```bash
python scripts/verify_config.py
```

预期输出：
```
✓ 配置验证全部通过！可以开始使用系统。
```

### 测试 2: 健康检查

```bash
curl http://localhost:5000/health
```

预期输出：
```json
{
  "status": "healthy"
}
```

### 测试 3: RAG 功能测试

```bash
python tests/test_rag_complete.py
```

## 配置 Embedding

### 选项 A: 使用模拟 Embedding（测试环境）

编辑 `config/app_config.json`：

```json
{
  "embedding": {
    "use_mock": true,
    "mock_dimension": 1536
  }
}
```

### 选项 B: 使用真实 Embedding API（生产环境）

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

设置环境变量：

```bash
export COZE_WORKLOAD_IDENTITY_API_KEY="your-api-key"
export COZE_INTEGRATION_MODEL_BASE_URL="https://api.example.com/v1"
```

## 使用 Web 界面

### 1. 选择角色

进入聊天界面后，选择你的角色：

- **a** - 产品经理
- **b** - 技术开发
- **c** - 销售运营
- **d** - 默认工程师

### 2. 提问

在输入框中输入问题，例如：

- "什么是建账规则？"
- "如何进行科目设置？"
- "财务凭证和业务凭证有什么区别？"

### 3. 查看回答

系统会自动：
1. 识别问题类型
2. 选择最优检索策略
3. 检索相关知识
4. 生成回答

### 4. 查看协作

访问 `http://localhost:5000/collaboration` 进入协作界面：

1. 输入昵称
2. 创建或加入会话
3. 实时协作

## 常用命令

### 配置验证

```bash
python scripts/verify_config.py
```

### 初始化数据库

```bash
python scripts/init_pgvector_db.py
```

### 填充知识库

```bash
python scripts/populate_knowledge_base.py
```

### 启动服务

```bash
python src/main.py
```

### 停止服务

```bash
# 按 Ctrl+C 或
pkill -f "python src/main.py"
```

## 故障排除

### 问题 1: 数据库连接失败

**解决方案：**
```bash
# 检查 PostgreSQL 服务
sudo systemctl status postgresql

# 测试连接
psql -h localhost -p 5432 -U postgres -d vector_db

# 安装 PGVector 扩展
psql -U postgres -d vector_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 问题 2: 端口被占用

**解决方案：**
```bash
# 查找占用端口的进程
lsof -ti:5000

# 杀死进程
kill -9 $(lsof -ti:5000)

# 或修改配置文件中的端口
# 编辑 config/app_config.json
```

### 问题 3: 配置验证失败

**解决方案：**
```bash
# 查看详细错误
python scripts/verify_config.py

# 检查配置文件
cat config/app_config.json

# 查看配置说明
cat docs/CONFIGURATION.md
```

### 问题 4: 缺少依赖包

**解决方案：**
```bash
# 重新安装依赖
pip install -r requirements.txt

# 检查特定包
pip list | grep package-name

# 安装缺失的包
pip install package-name
```

## 下一步

- 查看 [配置说明文档](CONFIGURATION.md)
- 查看 [项目总结](../PROJECT_SUMMARY.md)
- 添加文档到知识库
- 自定义 RAG 检索策略
- 实现高级 RAG 功能

## 获取帮助

- 查看配置文档：`docs/CONFIGURATION.md`
- 查看项目总结：`PROJECT_SUMMARY.md`
- 运行测试脚本：`tests/`
- 查看日志：`logs/app.log`

---

**祝使用愉快！**
