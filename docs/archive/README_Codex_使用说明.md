# Codex 使用说明

> **历史快照 (2026-07-19)**: 本文的 MCP/进度描述停留在 7 月中旬。现行实况以 `AGENTS.md` (Model Routing / Skill 武库) 与 `HANDOFF.md` 顶部快照为准；MCP 现为 5 工具，M1 解析已达成 scenario1 100%。

## 启动方式

Codex 在本仓库开始工作前，应依次阅读：

1. `AGENTS.md`
2. `HANDOFF.md`
3. `docs/AGENTS.md`
4. `docs/02_阶段计划与分工.md`
5. `docs/05_开发任务清单.md`
6. `docs/09_OpenCode与现有RAG_MCP实施方案.md`

`docs/00_Codex_启动提示词.md` 可用于新任务的上下文初始化，但代码状态仍以仓库实现和上述现行指南为准。

## 当前工作主线

本仓库已有 FastAPI、LangGraph、RAGService、PostgreSQL/PGVector 和知识库页面。新增工作是在不复制知识库的前提下，通过只读 MCP 将现有检索能力提供给 OpenCode，并通过 GB10 上的 OpenAI-compatible 模型服务推进 M1/M2 实验。

当前已实现三个 MCP 工具：`knowledge_search`、`knowledge_list_collections`、`knowledge_get_source`。M1 OCR/规则抽取、正式评测和完整多 Agent 工作流仍是后续任务。

## 开发机协作

后续以 GB10 开发机上的 Codex CLI 为主要执行入口，通过 Git 与本机同步代码。
模型权重、Conda 环境、模型服务和 GPU 实验保留在开发机，不提交服务器地址、
密码、Token、模型权重或实验产生的大文件。完整续接步骤见
`docs/11_开发机_Codex_CLI_交接.md`。

开发机 MCP 验证入口：

```bash
export PGDATABASE_URL='postgresql://USER:PASSWORD@127.0.0.1:15432/vector_db'
export JINRONG_MCP_PYTHON="$HOME/miniconda3/envs/wzh_vllm/bin/python"
python scripts/smoke_test_mcp_server.py
opencode mcp list
```

任何 CUDA、驱动、系统网络、共享环境或正在运行的模型服务变更，都应先确认影响范围。
