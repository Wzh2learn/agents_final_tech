# 开发机 Codex CLI 交接说明

## 入口

先阅读 [阶段收尾与对外汇报](12_阶段收尾与对外汇报.md)、根目录
[HANDOFF.md](../HANDOFF.md) 和 `AGENTS.md`。代码与文档通过 Git 同步；模型
权重、环境、来源映射、运行日志和私有样本不进入 Git。

## 第一次续接

在开发机终端执行：

```bash
cd ~/wzh/projects/agents_final_tech
git status --short
git stash list
git pull --ff-only origin main
tmux list-windows -t coding-jinrong
codex
```

若 `git status --short` 或 stash 有输出，不覆盖、清理、应用或删除；先确认归属。
需要查看现有会话时使用 `tmux attach -t coding-jinrong`，退出查看用 `Ctrl-b d`。

进入 Codex CLI 后可粘贴：

```text
接手 JinRongAgents 的文档所述 M1/M2 工作。先阅读 AGENTS.md、HANDOFF.md、
docs/12_阶段收尾与对外汇报.md、docs/AGENTS.md 和 docs/05_开发任务清单.md，
然后只读检查 Git 与 tmux 状态。不要假定任何模型或数据库服务仍在运行，也不要
输出或提交凭据、地址、私有来源、原始模型/工具输出。

已完成：只读 OpenCode/MCP 正式稳定性为 20/20 通过，生命周期问题已修复。
未完成：M2 正式业务指标（缺批准的标签—来源映射和人工标注）、M1 数值基线、
完整多 Agent 编排。按批准的数据和责任边界继续，不启动无关实验、下载或服务。
```

## 每次续接

```bash
cd ~/wzh/projects/agents_final_tech
git pull --ff-only origin main
codex
```

每次交付应列出变更文件、验证命令、结果和未决依赖。涉及服务、GPU、网络、驱动、
权限或真实业务数据前，先取得相应授权。
