# 🚀 项目部署与协作指南

## 📖 目录

- [方案一：推送到 GitHub](#方案一推送到-github-推荐)
- [方案二：下载到本地修改](#方案二下载到本地修改)
- [常见问题](#常见问题)

---

## 方案一：推送到 GitHub（推荐）

### 步骤 1：创建 GitHub 仓库

1. 访问 [GitHub](https://github.com) 并登录
2. 点击右上角 "+" → "New repository"
3. 填写仓库名称（建议：`accounting-rules-assistant`）
4. 选择仓库类型：
   - **Public**：公开可见，适合开源项目
   - **Private**：仅自己可见，适合私有项目
5. **重要**：不要勾选 "Initialize this repository with README"
6. 点击 "Create repository"

### 步骤 2：配置 Git 身份（首次使用）

```bash
# 设置你的用户名
git config --global user.name "Your Name"

# 设置你的邮箱
git config --global user.email "your.email@example.com"
```

### 步骤 3：添加远程仓库并推送

```bash
# 进入项目目录
cd /workspace/projects

# 添加远程仓库（替换 YOUR_USERNAME 和 REPO_NAME）
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# 推送代码到 GitHub
git push -u origin main

# 如果使用 SSH（推荐）
git remote set-url origin git@github.com:YOUR_USERNAME/REPO_NAME.git
git push -u origin main
```

### 步骤 4：验证推送成功

1. 访问你的 GitHub 仓库页面
2. 查看代码是否已经同步
3. 确认 README.md、requirements.txt 等文件已上传

### 步骤 5：后续更新代码

```bash
# 查看修改状态
git status

# 添加修改的文件
git add .

# 提交修改（写清楚修改内容）
git commit -m "fix: 修复了xxx问题"

# 推送到 GitHub
git push
```

---

## 方案二：下载到本地修改

### 步骤 1：克隆项目到本地

#### 如果已推送到 GitHub

```bash
# 在本地终端执行
git clone https://github.com/YOUR_USERNAME/REPO_NAME.git

# 或使用 SSH
git clone git@github.com:YOUR_USERNAME/REPO_NAME.git

# 进入项目目录
cd REPO_NAME
```

#### 如果未推送到 GitHub（直接导出）

```bash
# 在远程服务器上打包项目
cd /workspace/projects
tar -czf accounting-rules-assistant.tar.gz \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='*.pyc' \
    .

# 下载到本地（使用 scp 或 sftp）
# scp username@remote:/workspace/projects/accounting-rules-assistant.tar.gz .

# 在本地解压
tar -xzf accounting-rules-assistant.tar.gz
```

### 步骤 2：本地环境配置

#### 安装 Python 依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 配置数据库

1. 安装 PostgreSQL 12+ 并添加 PGVector 扩展
2. 创建数据库：
```sql
CREATE DATABASE accounting_rules;
\c accounting_rules
CREATE EXTENSION IF NOT EXISTS vector;
```

3. 修改配置文件 `config/app_config.json`：
```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "dbname": "accounting_rules",
    "user": "your_username",
    "password": "your_password"
  }
}
```

#### 配置环境变量

创建 `.env` 文件：
```bash
# 豆包 API Key（可选）
COZE_WORKLOAD_IDENTITY_API_KEY=your_api_key_here
COZE_INTEGRATION_MODEL_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# 数据库连接
DB_HOST=localhost
DB_PORT=5432
DB_NAME=accounting_rules
DB_USER=your_username
DB_PASSWORD=your_password
```

### 步骤 3：初始化数据库

```bash
# 运行数据库迁移
python -m storage.database.shared.model

# 或使用 flask 命令
flask db upgrade
```

### 步骤 4：启动服务

```bash
# 启动 Web 服务
python src/main.py

# 或使用提供的脚本
./scripts/start.sh
```

### 步骤 5：访问应用

打开浏览器访问：`http://localhost:5000`

---

## 🔄 日常开发流程

### 1. 拉取最新代码

```bash
# 从 GitHub 拉取最新代码
git pull origin main
```

### 2. 创建新分支（开发新功能）

```bash
# 创建并切换到新分支
git checkout -b feature/new-feature

# 或修复 bug
git checkout -b fix/bug-description
```

### 3. 提交修改

```bash
# 查看修改
git status

# 添加修改的文件
git add src/agents/agent.py

# 提交修改
git commit -m "feat: 添加了新功能"

# 推送到 GitHub
git push origin feature/new-feature
```

### 4. 合并分支

```bash
# 切换到主分支
git checkout main

# 合并功能分支
git merge feature/new-feature

# 推送到 GitHub
git push origin main
```

---

## 🛠️ 常见问题

### Q1: 推送时提示 "Authentication Failed"

**解决方案**：
1. 使用 Personal Access Token：
   - GitHub → Settings → Developer settings → Personal access tokens
   - 生成新 token，选择 `repo` 权限
   - 使用 token 替代密码

2. 或使用 SSH 密钥：
```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 查看公钥
cat ~/.ssh/id_ed25519.pub

# 添加到 GitHub：Settings → SSH and GPG keys → New SSH key
```

### Q2: 本地启动时报错 "ModuleNotFoundError"

**解决方案**：
```bash
# 确保已安装所有依赖
pip install -r requirements.txt

# 如果使用虚拟环境，确保已激活
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### Q3: 数据库连接失败

**解决方案**：
1. 检查 PostgreSQL 是否运行：
```bash
# Linux/macOS
sudo service postgresql status

# Windows
# 在服务管理器中查看 PostgreSQL 服务
```

2. 检查 PGVector 扩展：
```sql
\c accounting_rules
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Q4: 如何备份数据库

```bash
# 备份数据库
pg_dump -U username -d accounting_rules > backup.sql

# 恢复数据库
psql -U username -d accounting_rules < backup.sql
```

### Q5: 如何重启服务

```bash
# 停止服务
pkill -f "python src/main.py"

# 重新启动
python src/main.py
```

---

## 📝 Git 最佳实践

### 提交信息规范

使用 Conventional Commits 格式：

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式修改
refactor: 重构代码
test: 测试相关
chore: 构建/工具链相关
```

示例：
```bash
git commit -m "feat: 添加了角色识别功能"
git commit -m "fix: 修复了文档上传的 bug"
git commit -m "docs: 更新了部署文档"
```

### 忽略文件

确保 `.gitignore` 文件包含：
```
__pycache__/
*.pyc
.env
venv/
*.log
.pytest_cache/
*.egg-info/
```

### 分支管理

- `main`：主分支，保持稳定
- `feature/*`：功能开发分支
- `fix/*`：Bug 修复分支
- `hotfix/*`：紧急修复分支

---

## 🎯 下一步建议

1. **推送到 GitHub**：方便代码管理和协作
2. **配置 CI/CD**：自动化测试和部署
3. **添加监控**：跟踪服务状态和性能
4. **编写单元测试**：保证代码质量
5. **优化文档**：提升用户体验

---

## 📚 更多资源

- [Git 官方文档](https://git-scm.com/doc)
- [GitHub 学习指南](https://docs.github.com/en/get-started)
- [LangChain 文档](https://python.langchain.com/)
- [Flask 文档](https://flask.palletsprojects.com/)

---

**祝您使用愉快！如有问题，请查看项目 README.md 或提交 Issue。**
