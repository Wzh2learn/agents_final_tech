# OpenCode 开发机运行说明

当前进度和下一任务以根目录 `HANDOFF.md` 为准。

## 当前已验证链路

OpenCode 运行在开发机，使用 GB10 上的本地 Qwen3-14B OpenAI-compatible 服务；
知识检索通过项目内的只读 `jinrong-rag` MCP 接入现有 RAG/PGVector。

已验证：

- 14B 服务：`http://127.0.0.1:8004/v1`
- MCP：`knowledge_search`、`knowledge_list_collections`、`knowledge_get_source`
- OpenCode：`gb10/qwen3-14b` 能返回模型结果
- 14B 上下文窗口：`16384`；8K 会导致项目默认提示词超出限制

## 启动方式

如果模型服务未运行，先启动 14B 服务：

```bash
bash scripts/start_llamacpp_model.sh \
  ~/wzh/models/gguf/qwen3-14b/Qwen3-14B-Q4_K_M.gguf \
  8004 /tmp/qwen3-14b-8004.log 16384
```

在 VS Code Remote-SSH 连接开发机后的交互式终端执行：

```bash
cd ~/wzh/projects/agents_final_tech
export PGDATABASE_URL='postgresql://USER:PASSWORD@127.0.0.1:15432/vector_db'
bash scripts/run_opencode_gb10.sh
```

一次性验证模型：

```bash
bash scripts/run_opencode_gb10.sh run --pure --auto \
  --model gb10/qwen3-14b 'Reply with exactly OK.'
```

脚本默认设置 `OPENCODE_DISABLE_MODELS_FETCH=1`，防止 OpenCode 启动时访问
`models.dev` 更新远程模型目录。开发机当前网络条件下，这一步可能长时间等待。
脚本还会复用 `wzh_vllm` 环境中的 Python 作为 MCP 运行时。

## 注意事项

- OpenCode 应在 VS Code Remote-SSH 的终端中运行；非交互 SSH 命令需要额外分配 TTY。
- 一次只启动一个大模型服务，避免 GB10 显存和内存竞争。
- 数据库密码、模型 Token 和代理配置只放在开发机环境变量或用户配置中，不提交 Git。
- 先执行 `opencode mcp list`，确认 `jinrong-rag` 为 `connected`，再开始 M1/M2 测试。
