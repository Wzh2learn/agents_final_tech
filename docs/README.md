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
- [阶段收尾与对外汇报（2026-07-23）](12_阶段收尾与对外汇报.md)
- [角色 B 开发日志（老师汇报版）](14_角色B_开发日志_老师汇报版.md)
- [开发机 Codex CLI 交接](11_开发机_Codex_CLI_交接.md)
- [本机 M1 展示草稿状态](../HANDOFF.md#local-m1-display-draft-not-yet-verified)

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
- [M1/M2 联合数据闭环计划](13_M1_M2联合数据闭环计划.md)

## 当前实现状态

截至 2026-07-22，只读 OpenCode/MCP 正式稳定性验收已 **20/20 通过**，且
进程生命周期问题已修复；Qwen3-14B 是已验证的本地生成服务路径，但不表示
当前正在运行。M1/M2 已明确为“文档解析 -> 建库 -> 带证据问答”的联合任务，
并选定 CC BY 4.0 的 TAT-DQA 固定小样本作为首个公共基线；公开 ID 子集已保留
官方 split 完成冻结，7/7 官方数据文件已通过大小、JSON 和 ZIP CRC 校验。独立 Vision/Tabular MCP 已实现，且
TabPFN v2、TabFM 脱敏合成链路已通过；这些不是业务质量指标。M1 数值基线和完整
多 Agent 编排尚未完成。TAT-DQA 官方解析 JSON 的首个 validation M2 上限已经完成：
文档 Recall@5 0.81、证据块 Recall@5 0.50、答案 EM 0.24；它不包含 OCR/PDF 误差。
面向老师或协作同学请优先阅读[阶段收尾与对外汇报](12_阶段收尾与对外汇报.md)。

2026-07-27 在本机工作区开始起草确定性文本规则基线的 M1 展示页；该草稿未完成静态
交互、测试、浏览器验证或 GB10 同步，因此不是新的模型实验结论。其精确状态以根目录
`HANDOFF.md` 为准。

模型下载、环境和冒烟测试记录位于 [`experiments/`](experiments/)，模型目录约定见 [`../models/README.md`](../models/README.md)，脚本说明见 [`../scripts/README_scripts.md`](../scripts/README_scripts.md)。
首个公共 validation 指标见 [TAT-DQA M2 解析上限](experiments/2026-07-23_tat_dqa_m2_upper_bound.md)。

## 归档

`archive/` 保存迁移包、旧设计和历史审查报告，仅用于追溯。若归档内容与当前代码、根目录 `AGENTS.md` 或编号计划文档冲突，以当前代码和现行指南为准。
