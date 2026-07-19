# 项目文档导航

本目录同时记录现有 JinRongAgents 系统、GB10 模型实验和 OpenCode/MCP 接入方案。代码现状以仓库实现为准，计划文档中的候选接口不等于已经完成。

## 开发入口

- [仓库贡献指南](../AGENTS.md)
- [Agent 开发指南](AGENTS.md)
- [开发者指南](DEVELOPER_GUIDE.md)
- [部署指南](DEPLOYMENT.md)
- [API 参考](API_REFERENCE.md)
- [工具使用说明](TOOLS_USAGE.md)
- [当前开发交接](../HANDOFF.md)
- [开发机 Codex CLI 交接](11_开发机_Codex_CLI_交接.md)

## M1/M2 与 GB10 主线

- [项目背景与目标](01_项目背景与目标.md)
- [两阶段计划与分工](02_阶段计划与分工.md)
- [技术架构与模块设计](03_技术架构与模块设计.md)
- [服务器与模型部署计划](04_服务器与模型部署计划.md)
- [开发任务清单](05_开发任务清单.md)
- [Remote SSH 开发流程](06_Remote_SSH_开发流程.md)
- [角色 B 模型调研与研究方向](07_角色B_模型调研与研究方向.md)
- [老师汇报版两阶段计划](08_GB10模型服务两阶段计划_老师汇报版.md)
- [OpenCode 与现有 RAG MCP 实施方案](09_OpenCode与现有RAG_MCP实施方案.md)
- [OpenCode 开发机运行说明](10_OpenCode开发机运行说明.md)

## 当前实现状态

截至 2026-07-19，GB10 Qwen3-14B 16K 服务、OpenCode Provider、只读
`jinrong-rag` MCP Adapter 和一次真实工具调用已验证。下一步是 20 次连续调用
稳定性验收和 M2 正式数据集/数字基线。M1 OCR/规则抽取工具与完整多 Agent
编排仍在任务清单中。

模型下载、环境和冒烟测试记录位于 [`experiments/`](experiments/)，模型目录约定见 [`../models/README.md`](../models/README.md)，脚本说明见 [`../scripts/README_scripts.md`](../scripts/README_scripts.md)。

## 归档

`archive/` 保存迁移包、旧设计和历史审查报告，仅用于追溯。若归档内容与当前代码、根目录 `AGENTS.md` 或编号计划文档冲突，以当前代码和现行指南为准。
