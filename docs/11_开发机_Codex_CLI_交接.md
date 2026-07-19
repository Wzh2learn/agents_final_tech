# 开发机 Codex CLI 交接说明

## 目标

后续以开发机上的 Codex CLI 为主要执行入口。代码和文档通过 GitHub 同步，
模型权重、Conda 环境、数据库、Token 和运行日志保留在开发机，不进入 Git。

## 第一次续接

在 VS Code Remote-SSH 的开发机终端执行：

```bash
cd ~/wzh/projects/agents_final_tech
git status --short
git stash list
git fetch origin
git pull --ff-only origin main
codex
```

如果 `git status --short` 有输出，不要直接覆盖或清理。先让 Codex 判断这些改动
来自谁、是否与当前任务相关。远端已有 stash 也不能自动应用或删除。

进入 Codex CLI 后粘贴：

```text
你现在接手 JinRongAgents 的 GB10 本地模型、OpenCode、RAG MCP 和 M1/M2
实验工作。请先完整阅读 AGENTS.md、HANDOFF.md、docs/AGENTS.md、
docs/05_开发任务清单.md、docs/09_OpenCode与现有RAG_MCP实施方案.md、
docs/10_OpenCode开发机运行说明.md，不要先改代码。

然后检查当前 Git 状态、开发机已有 Conda 环境、PostgreSQL/PGVector、
8004 端口的 Qwen3-14B 服务、OpenCode 和 jinrong-rag MCP。不要输出或提交
密码、Token、IP、模型权重和私有数据，不要修改 CUDA、驱动或系统网络。

根据 HANDOFF.md 从当前进度继续：先完成 20 次只读 MCP/OpenCode 稳定性验收
并保存脱敏结果，然后建立第一版 20 条 M2 标注集和可重复评测脚本，输出
Recall@5、来源命中率、拒答率、回答质量和延迟。先阅读和核验，再给出简短
执行计划并直接完成可以安全完成的部分。
```

## 每次继续工作

以后重新进入开发机时执行：

```bash
cd ~/wzh/projects/agents_final_tech
git pull --ff-only origin main
codex
```

对 Codex 说：

```text
读取 AGENTS.md 和 HANDOFF.md，检查 git status 与当前服务状态，继续
HANDOFF.md 的 Immediate Work。先告诉我已完成、待完成和本轮要做的第一项。
```

## 推荐协作方式

- 一次给 Codex 一个可验收任务，例如“完成 20 次 MCP 稳定性脚本和结果记录”。
- 要求每次交付包含 changed files、运行命令、测试结果和剩余风险。
- 代码变更先在开发机测试，再提交并推送；本机以后只需 `git pull` 查看。
- 实验原始数据如含业务内容，留在开发机；Git 只保存脱敏样例、脚本和汇总。
