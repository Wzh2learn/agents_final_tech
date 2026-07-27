# 开发机 Codex CLI 交接说明

## 入口

先阅读 [M1/M2 联合数据闭环计划](13_M1_M2联合数据闭环计划.md)、[阶段收尾与对外汇报](12_阶段收尾与对外汇报.md)、根目录
[HANDOFF.md](../HANDOFF.md) 和 `AGENTS.md`。代码与文档通过 Git 同步；模型
权重、环境、来源映射、运行日志和私有样本不进入 Git。

**2026-07-27 提醒：** 本机存在未验证的 M1 页面草稿，尚未提交或同步到 GB10。不要在
开发机上重建、运行或声称验证该功能；应先等待本机完成静态交互、测试和浏览器检查并提交，
再按 Git 同步后进行集成验证。

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
接手 JinRongAgents 的 M1 -> M2 联合数据闭环。先阅读 AGENTS.md、HANDOFF.md、
docs/13_M1_M2联合数据闭环计划.md、docs/12_阶段收尾与对外汇报.md、
docs/AGENTS.md 和 docs/05_开发任务清单.md，
然后只读检查 Git 与 tmux 状态。不要假定任何模型或数据库服务仍在运行，也不要
输出或提交凭据、地址、私有来源、原始模型/工具输出。

已完成：只读 OpenCode/MCP 正式稳定性为 20/20 通过，生命周期问题已修复。
当前批准的下一步：以 CC BY 4.0 的 TAT-DQA 为主数据集，建立文档级 60/20/20、
100 文档、最多 500 问题的 joint-v1 固定小样本。先完成 DATA-1 和 DATA-2：检查
磁盘/网络，编写可测试的下载校验与确定性抽样脚本，再下载到
~/wzh/datasets/tat-dqa/ 并生成不含正文的 manifest。不要先启动模型，不要下载
PubTables-1M、FinTabNet、FinQA 等候选，也不要开始 SFT/DPO 或多 Agent 编排。

执行完成后运行相关 pytest，记录文件大小、样本/问题/答案类型/split 数量、泄漏检查、
命令和阻塞。原始 PDF、解析 JSON、渲染图片、索引、日志和模型输出不得进入 Git。
若 Google Drive 配额、网络或空间阻塞，停止重复尝试，保留脱敏错误并报告下一条可行命令。
```

## 每次续接

```bash
cd ~/wzh/projects/agents_final_tech
git pull --ff-only origin main
codex
```

每次交付应列出变更文件、验证命令、结果和未决依赖。涉及服务、GPU、网络、驱动、
权限或真实业务数据前，先取得相应授权。
