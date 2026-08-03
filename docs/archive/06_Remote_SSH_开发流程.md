# 06 Remote SSH 开发流程

## 1. 目标

使用 VS Code Remote SSH 连接 Linux 开发机，在远程环境中进行项目开发、模型部署、后端服务运行和实验测试。

## 2. 安全原则

1. 不要把服务器密码写入仓库；
2. 不要把服务器 IP 写入仓库；
3. 不要提交 `.env`；
4. 不要提交 API key；
5. 不要在文档中记录真实 token；
6. 不要让 Codex 执行破坏性系统命令，除非人工确认；
7. 所有服务器环境修改先记录，再执行。

## 3. 推荐目录

远程开发机建议目录：

```bash
mkdir -p ~/wzh/projects
cd ~/wzh/projects
git clone <REPO_URL> agents_final_tech
cd agents_final_tech
```

## 4. Python 环境

开发机优先复用已经验证的 Conda 环境，不重新创建通用环境：

- `wzh_vllm`：项目服务、llama.cpp 与 MCP；
- `wzh_retrieval`：Embedding/Reranker；
- `wzh_vision`：OCR/VLM；
- `wzh_tabular`：TabFM/TabPFN。

只有依赖确实冲突时才创建新环境，且不得原地升级上述共享环境的 CUDA/Torch。
以下命令仅供新机器从零搭建时参考。

venv 示例：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

conda 示例：

```bash
conda create -n <new_environment_name> python=3.11 -y
conda activate <new_environment_name>
pip install -U pip
pip install -r requirements.txt
```

## 5. 环境变量

创建 `.env`：

```bash
cp .env.example .env
```

`.env` 仅保存在服务器本地，不提交 Git。

## 6. 服务器摸底命令

```bash
nvidia-smi
uname -a
df -h
free -h
python3 --version
nvcc --version || true
docker --version || true
```

建议把输出保存到：

```text
experiments/results/server_env_check.md
```

注意：不要把敏感 IP、用户名、内网路径写入公开仓库。

## 7. 本地模型服务启动方式

### vLLM 示例

```bash
export MODEL_NAME=<model_name_or_path>
python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL_NAME" \
  --host 0.0.0.0 \
  --port 8000
```

### llama.cpp 示例

```bash
export GGUF_MODEL_PATH=<path_to_model.gguf>
./llama-server \
  -m "$GGUF_MODEL_PATH" \
  --host 0.0.0.0 \
  --port 8001
```

具体命令需要根据服务器实际环境调整。

## 8. 后端启动

示例：

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## 9. 前端启动

示例：

```bash
cd frontend
npm install
npm run dev
```

## 10. Codex 使用方式

### 方式一：在本地 VS Code 使用 Codex

适合：

1. 改代码；
2. 生成文档；
3. 生成接口；
4. 写测试；
5. 写脚本。

### 方式二：Remote SSH 后在远程终端使用 Codex CLI

适合：

1. 检查服务器环境；
2. 调试 Python 依赖；
3. 运行模型服务；
4. 执行 benchmark；
5. 修复远程环境相关问题。

当前后续开发采用方式二。第一次续接先执行：

```bash
cd ~/wzh/projects/agents_final_tech
git status --short
git stash list
git fetch origin
git pull --ff-only origin main
codex
```

进入 Codex CLI 后按 `docs/11_开发机_Codex_CLI_交接.md` 的提示词续接。

使用原则：

1. 先让 Codex 读 `AGENTS.md`；
2. 每次只给一个明确任务；
3. 执行系统级命令前人工确认；
4. 不要让 Codex 自动修改 CUDA、驱动或系统包；
5. 对每次改动要求说明 changed files、run commands、test results。

## 11. Git 工作流

建议：

```bash
git checkout -b feat/backend-scaffold
# 修改代码
git add .
git commit -m "feat: add backend scaffold"
git push origin feat/backend-scaffold
```

每个任务尽量一个小分支。

## 12. 调试记录

建议把实验结果放到：

```text
experiments/results/
```

文件命名：

```text
YYYYMMDD_model_benchmark.md
YYYYMMDD_rag_eval.md
YYYYMMDD_rule_extraction_eval.md
```
