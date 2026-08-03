# 部署指南

## 系统要求

- Python 3.11+
- Docker Desktop（推荐）
- 8GB+ RAM
- 20GB 存储空间

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository_url>
cd agents_final_tech

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate.bat  # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 到 `.env`:

```env
SILICONFLOW_API_KEY=your_api_key_here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_TRUST_ENV=false
PGDATABASE_URL=postgresql://postgres:your_password_here@localhost:15432/vector_db
```

### 4. 启动 PGVector 容器

```bash
docker run -d --name pgvector_15432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=vector_db \
  -p 15432:5432 \
  ankane/pgvector:latest
```

容器已存在时直接执行：

```bash
docker start pgvector_15432
```

### 5. 初始化数据库

```bash
python scripts/init_pgvector_db.py
python scripts/init_collaboration_db.py
```

### 6. 启动服务

```bash
# Windows
run.bat

# Linux/macOS
python src/web/app.py
```

访问: http://localhost:5000

## 生产部署

### 使用 Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 src.web.app:app
```

### 使用 Docker

```bash
docker-compose up -d
```

### 使用 Nginx

配置反向代理：
- Flask: http://localhost:5000
- WebSocket: ws://localhost:5001

详细配置参考项目 wiki。

## 常见问题

### 端口被占用
```bash
# 查找占用进程
lsof -i :5000  # Linux/macOS
netstat -ano | findstr :5000  # Windows
```

### 数据库连接失败
1. 确认 `pgvector_15432` 容器正在运行
2. 使用 `docker logs pgvector_15432` 检查数据库是否 ready
3. 检查 `.env` 的 `PGDATABASE_URL` 是否为 `localhost:15432/vector_db`
4. 重新执行初始化脚本

### 依赖安装失败
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 更多信息

参考 README.md 和项目文档。
