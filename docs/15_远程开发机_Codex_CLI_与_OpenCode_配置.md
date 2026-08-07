# 远程开发机配置：Codex CLI + OpenCode

> 状态: 活跃 | 更新: 2026-08-07（Loop A 模型分工更新） | 取代/被取代: 无

**日期：2026-07-27。** 本文覆盖 GB10 开发机上两套工具的安装与验证。

## 1. 两套工具的定位

| 工具 | 用途 | 模型来源 |
|------|------|----------|
| **Codex CLI** | 开发助手：写代码、跑命令、调试环境、Git 操作 | OpenAI API（云端） |
| **OpenCode** | M1/M2 实验执行：通过 MCP 调用本地模型和知识库 | GB10 本地 Qwen3-14B（`127.0.0.1:8004`） |

两者互不干扰。Codex CLI 不接入 MCP，OpenCode 不调用 OpenAI API。

---

## 2. Codex CLI 安装

### 前置要求

- Node.js **22+**（推荐 22 LTS）
- 一个有效的 OpenAI API Key（需要 Codex 访问权限）

### 安装步骤

```bash
# 检查 Node 版本（需要 >= 22）
node --version

# 如果没有 Node 22，用 nvm 安装
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
source ~/.bashrc
nvm install 22
nvm use 22

# 全局安装 Codex CLI
npm install -g @openai/codex

# 验证
codex --version
```

### 配置 API Key

```bash
# 写入 shell 配置（不要提交到 Git）
echo 'export OPENAI_API_KEY="sk-..."' >> ~/.bashrc
source ~/.bashrc
```

或者每次会话临时设置：

```bash
export OPENAI_API_KEY="sk-..."
```

### 首次使用

```bash
cd ~/wzh/projects/agents_final_tech
codex
```

进入后粘贴 `docs/11_开发机_Codex_CLI_交接.md` 中的启动提示词即可续接。

### 常用参数

```bash
# 指定模型（默认 o4-mini）
codex --model o3

# 全自动模式（不逐步确认）
codex --approval-mode full-auto

# 直接给任务
codex "检查 git status 并报告未提交变更"
```

### 注意事项

- Codex CLI 会在项目目录下创建 `.codex/` 配置目录，已加入 `.gitignore`
- 不要在 Codex CLI 中执行破坏性系统命令（CUDA、驱动、网络）
- 涉及 GPU、模型服务、数据库的操作先人工确认
- 网络需要能访问 `api.openai.com`；如果开发机有代理，确保 `HTTPS_PROXY` 正确

---

## 3. OpenCode 配置（已有，验证即可）

OpenCode 接入 GB10 本地 Qwen3-14B 模型，通过 MCP 调用知识库、Vision 和 Tabular 工具。
配置文件为仓库根目录的 `opencode.json`，已提交到 Git。

### 前置条件

```bash
# 确认 OpenCode 已安装
opencode --version

# 确认本地模型服务在运行（端口 8004）
curl -s http://127.0.0.1:8004/v1/models | head -20

# 如果模型未启动，用 llama.cpp 启动（根据实际模型路径）
bash scripts/start_llamacpp_model.sh
```

### MCP 服务验证

```bash
cd ~/wzh/projects/agents_final_tech

# 设置环境变量（值不记录到文档）
export PGDATABASE_URL='postgresql://USER:PASSWORD@127.0.0.1:15432/vector_db'
export JINRONG_MCP_PYTHON="$HOME/miniconda3/envs/wzh_vllm/bin/python"

# 知识库 MCP smoke test
python scripts/smoke_test_mcp_server.py

# 查看 OpenCode 连接的 MCP
opencode mcp list
```

预期输出：`jinrong-rag`、`jinrong-vision`、`jinrong-tabular` 三个 MCP 均显示 connected。

### OpenCode 使用

```bash
# 交互模式
opencode

# 指定 agent 运行任务
bash scripts/run_opencode_gb10.sh run \
  --agent m2-qa --title m2-test \
  '检索"企业开户资料核验"相关规则并引用来源'

# Tabular 专用 runner
bash scripts/run_opencode_tabular.sh run \
  --agent tabular-runner --title tabular-demo \
  'Call tabular_classify once with the supplied numeric training and prediction rows.'
```

### 已验证状态（2026-07-21）

- 只读 MCP 稳定性：**20/20 通过**
- Qwen3-14B 本地生成服务路径：已验证
- Vision MCP 协议发现：通过（真实 OCR 调用待补）
- Tabular MCP 合成链路：TabPFN v2 + TabFM 均通过
- `tabular-runner` 端到端：约 26 秒完成

### 注意

- OpenCode 的模型服务、MCP 进程和 Conda 环境都在开发机本地，不进 Git
- 不要通过 OpenCode 修改数据库、创建向量库或绕过 `RAGService`
- 一次只启动一个大模型，避免显存冲突
- 历史验证结论不代表当前服务仍在运行，每次续接先检查

---

## 4. 续接检查清单

每次 SSH 到开发机后：

```bash
# 1. 代码同步
cd ~/wzh/projects/agents_final_tech
git status --short
git stash list
git pull --ff-only origin main

# 2. 检查 tmux 会话
tmux list-windows -t coding-jinrong 2>/dev/null || echo "no tmux session"

# 3. 检查模型服务（OpenCode 需要）
curl -s http://127.0.0.1:8004/v1/models | python3 -m json.tool | head -5

# 4. 检查数据库（MCP 需要）
docker ps --filter "name=pgvector" --format "{{.Names}} {{.Status}}"

# 5. 启动 Codex CLI（开发助手）
codex

# 或启动 OpenCode（M1/M2 实验）
opencode
```

---

## 5. 故障排查

| 问题 | 排查 |
|------|------|
| `codex: command not found` | 检查 `node --version` >= 22，`npm list -g @openai/codex` |
| Codex CLI 连接超时 | 检查 `HTTPS_PROXY`、`curl https://api.openai.com/v1/models` |
| OpenCode 报 model unavailable | `curl http://127.0.0.1:8004/v1/models`，确认 llama.cpp 在运行 |
| MCP 连接失败 | 检查 `PGDATABASE_URL`、`JINRONG_MCP_PYTHON`、Docker 容器状态 |
| 显存不足 | `nvidia-smi`，关闭不需要的模型进程 |
| SSH 断开后进程丢失 | 使用 `tmux` 或 `nohup`，不要直接在前台跑长任务 |


## 模型切换 (2026-07-31 更新)

Codex CLI 支持三个模型通道，通过 `scripts/switch_codex_model.sh` 一键切换：

```bash
# 切换到 qwen3.8-max-preview (默认，直连千问 Responses API)
bash scripts/switch_codex_model.sh qwen

# 切换到 glm-5.2 (经 :8100 代理，Responses→Chat 转换)
bash scripts/switch_codex_model.sh glm

# 切换到 deepseek-v4-pro (经 :8100 代理)
bash scripts/switch_codex_model.sh deepseek
```

切换逻辑：
- `qwen` → `model_provider = "Token_Plan"` (直连千问 Responses API)
- `glm` / `deepseek` → `model_provider = "Token_Plan_Chat"` (经 :8100 代理)
- glm/deepseek 切换时自动确保 :8100 代理在跑

Claude Code 默认模型为 qwen3.8-max（千问 Anthropic 兼容端点，2026-08-03 切换并验证 tool_use），配置在 `~/.claude/settings.json`。glm-5.2 / deepseek-v4-flash-0731 为可选回退。
其他工具默认 qwen3.8-max-preview。

模型分配原则：
- **日常执行层** (Loop A / Codex CLI): deepseek-v4-flash-0731（2026-08-06 起, 经 :8100 代理; 分工边界见 memory/DECISIONS.md——flash 只做代码执行/有界任务）
- **审计层** (Loop C / Claude Code): qwen3.8-max（2026-08-03 定版切换，tool_use 已验证）
- **硬骨头手动升级**: glm-5.2 或 deepseek-v4-pro，遇到 qwen 搞不定的任务时切
