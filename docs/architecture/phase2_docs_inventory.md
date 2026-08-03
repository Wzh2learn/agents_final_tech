# Phase 2 文档盘点：docs/ 顶层 00-16 编号文档与无编号 md

**盘点日期**: 2026-08-03
**范围**: `docs/` 顶层编号 00-16 的 md 文档与无编号 md（不含 `experiments/`、`architecture/` 子目录；17-21 不在本次范围）。共 32 个文件。
**判定依据（当前系统实况）**: M1 甲方对账单解析 100%（5/5 真实样本，勾稽全 PASS）；M2 RAG QA 14/15=93%（collection `m1_parsed_statements`，137 embeddings）；模型路由 Loop A（Codex CLI）与 Loop C（Claude Code）均为 qwen3.8-max（Loop C 走 Anthropic 兼容端点，2026-08-03 tool_use 已验证）；ZhikunCode v1.2.1+7 docker 部署；VLM 线（:8007/Triton）已关闭，OCR 由 vision-8004 承担；Graph 四层 Loop 运行中（A 待命/B 30min/C 12h/D 指挥）；TAT-DQA 研究线冻结，主线为客户甲方对账单 M1。

**状态定义**: 存活 = 仍是当前事实；已被替代 = 内容被更新的文档取代（注明取代者）；历史 = 仅存档价值。

## 一、编号文档（00-16）

| 文件 | 状态 | 一句话理由 | 建议去向 |
|---|---|---|---|
| docs/00_Codex_启动提示词.md | 已被替代 | 初期会话引导提示词，其任务清单（M2 标签映射审批、第一阶段优先项）早已由当前主线取代 | 移入 docs/archive/；现会话交接以 docs/15 + HANDOFF.md 为准 |
| docs/01_项目背景与目标.md | 已被替代 | 原始“业务规则文档”M1/M2 定位已被客户甲方对账单 M1 主线与能力说明书取代 | 移入 docs/archive/；现目标定位见根 AGENTS.md 主线声明与 docs/19 |
| docs/02_阶段计划与分工.md | 已被替代 | 两阶段计划与角色 B/协作同学分工已被 Graph 四层 Loop 运行模型取代 | 移入 docs/archive/；现计划与分工见 docs/17、docs/21、HANDOFF.md |
| docs/03_技术架构与模块设计.md | 已被替代 | 模块与接口设计（/api/rules/* 等）与现行 M1/M2 端点集和 loop 架构不符 | 移入 docs/archive/；现架构见根 AGENTS.md、docs/17、docs/20 |
| docs/04_服务器与模型部署计划.md | 已被替代 | vLLM 为主的部署路线与候选模型池已让位于 llama-server + 云端 qwen3.8-max 路由现状 | 移入 docs/archive/；现模型路由与部署见根 AGENTS.md 与 docs/21 |
| docs/05_开发任务清单.md | 已被替代 | 任务状态止于 2026-07-24/27，MCP/DATA 各任务已完成或被客户 M1 主线取代 | 移入 docs/archive/；现任务队列见 HANDOFF.md 与 docs/21 |
| docs/06_Remote_SSH_开发流程.md | 已被替代 | 开发方式已转为 Codex CLI + tmux loop 模式，文中 vLLM/conda/前端示例与现状不符 | 移入 docs/archive/；现开发流程见 docs/15 与 docs/17 |
| docs/07_角色B_模型调研与研究方向.md | 历史 | 研究议程基线（TabFM/OCR 对比/微调方向），TAT-DQA 已冻结、VLM 线关闭，研究线暂停 | 留档；冻结边界见根 AGENTS.md“Frozen Items” |
| docs/08_GB10模型服务两阶段计划_老师汇报版.md | 已被替代 | 两阶段计划的汇报版快照，对外口径已由后续开发日志与能力说明书承接 | 移入 docs/archive/；对外说明以 docs/19 为准 |
| docs/09_OpenCode与现有RAG_MCP实施方案.md | 已被替代 | 实现状态止于 2026-07-27，多 Agent 编排主体已转向 Codex/Qoder/ZhikunCode harness + Graph loop | 移入 docs/archive/；薄适配原则由根 AGENTS.md 架构边界继续承载 |
| docs/10_OpenCode开发机运行说明.md | 已被替代 | “当前优先事项”与 Vision MCP 描述（paddleocr 默认）均已过时，M1/M2 已转入客户主线 | 移入 docs/archive/；现状态见 HANDOFF.md 与根 AGENTS.md |
| docs/11_开发机_Codex_CLI_交接.md | 已被替代 | 交接提示词停留在 TAT-DQA joint-v1 阶段，已被 docs/15 的完整配置与模型切换说明取代 | 移入 docs/archive/；交接以 docs/15 为准 |
| docs/12_阶段收尾与对外汇报.md | 已被替代 | 2026-07-27 时点的对外汇报基准，未覆盖其后解析 100%、生产冲刺与 Scenario 1 进展 | 移入 docs/archive/；对外汇报见 docs/14、docs/19、HANDOFF.md |
| docs/13_M1_M2联合数据闭环计划.md | 存活 | 仍是已批准公开数据集（TAT-DQA joint-v1）与 split 政策的规范依据（根 AGENTS.md 规定会话必读），惟该研究线已冻结 | 原地保留；执行主线已转客户 M1，须与根 AGENTS.md 冻结声明配套阅读 |
| docs/14_角色B_开发日志_老师汇报版.md | 历史 | 截至 2026-07-28 的阶段性日志汇报，属存档记录，其后进展另见 HANDOFF 与收尾文档 | 留档；后续进展见 HANDOFF.md、docs/18_overnight_loopD_neat_closeout.md |
| docs/15_远程开发机_Codex_CLI_与_OpenCode_配置.md | 存活（部分） | 仍是 GB10 开发机 Codex CLI 配置的现行依据，但“Loop C 用 glm-5.2”一行已过时（现为 qwen3.8-max 经 Anthropic 兼容端点） | 原地保留；建议将模型分配段与根 AGENTS.md“Model Routing（2026-08-03）”同步 |
| docs/16_Qoder_CLI迁移评估与计划.md | 已被替代 | 侦察阶段已完成且结论已回写根 AGENTS.md 与实验报告，本文仅剩决策留痕价值 | 移入 docs/archive/；现结论见根 AGENTS.md“Qoder CLI Recon”与 docs/experiments/2026-07-29_qoder_recon.md |

## 二、无编号文档

| 文件 | 状态 | 一句话理由 | 建议去向 |
|---|---|---|---|
| docs/AGENTS.md | 已被替代 | Implemented/Planned 状态段停留在 2026-07-22，与现状（M1 100%、M2 14/15、Loop 体系）矛盾 | 移入 docs/archive/ 或重写；权威状态以根 AGENTS.md 与 HANDOFF.md 为准 |
| docs/README.md | 已被替代 | “当前实现状态”段止于 2026-07-22，导航缺 15-21 及新文档入口 | 建议重写为覆盖 00-21 与 experiments 的纯导航页；状态以 HANDOFF.md 为准 |
| docs/CLAUDE.md | 存活（部分） | 指向根 AGENTS.md 的规则与编码约束仍有效，但必读清单（02/05/09）已过时 | 原地保留；建议必读清单更新为 HANDOFF.md + docs/17/21 |
| docs/CLAUDE_PLUGIN_SETUP.md | 历史 | Windows VS Code Anthropic 插件环境变量注入的初期记录，Loop C 现行配置方式已变 | 移入 docs/archive/；现 Claude Code 配置见根 AGENTS.md 模型路由与 docs/15 |
| docs/API_REFERENCE.md | 已被替代 | 原系统 v1.0 API（chat/知识库/协作），缺全部现行 /api/m1/*、/api/m2/*、schema、metrics 端点 | 移入 docs/archive/ 或按现行代码重写；端点摘要见根 AGENTS.md |
| docs/DEPLOYMENT.md | 已被替代 | 初期部署指南（run.bat/gunicorn 单机流程），已被 Docker Compose 生产部署指南取代 | 移入 docs/archive/；部署以 docs/20_部署指南.md 为准 |
| docs/DEVELOPER_GUIDE.md | 已被替代 | M1/M2 之前的模块地图，ACL 分层概述已由根 AGENTS.md 更准确、更新的项目结构段承接 | 移入 docs/archive/；架构概览见根 AGENTS.md |
| docs/DIFY_VS_TOOLS_COMPARISON.md | 历史 | 2026-01 Dify→LangGraph 迁移的对比考古，与当前 M1/M2 主线无关 | 留档 |
| docs/Explore.md | 历史 | 原 JinRongAgents 系统的架构探索与技术调研记录 | 留档 |
| docs/KB_UI_REDESIGN_SPEC.md | 历史 | 原知识库页面 Dify 风格重构设计稿，现行 UI（含 m1 工作台）已另行演进 | 留档 |
| docs/PROJECT_BUSINESS_FLOW_WORKLOAD_REPORT.md | 历史 | 2026-03-04 原系统业务流程与工作量汇报快照 | 留档 |
| docs/RECSYS_MEMORY_DESIGN.md | 存活（部分） | 其 L2 情景记忆已按本设计实现并在用（src/storage/memory/episodic_memory.py），惟非当前 M1/M2 主线焦点 | 原地保留，作为 memory 子系统设计依据 |
| docs/TOOLS_USAGE.md | 历史 | 2026-01-04 原系统 agent 工具清单（23 个），先于 M1/M2 工具与 MCP 体系 | 留档；现工具面见根 AGENTS.md |
| docs/m1_coldstart_candidates.md | 存活 | Loop D 的 schema 候选列治理记录（2026-07-30），自述可随样本扩充更新且流程仍在生效 | 原地保留 |
| docs/2026-07-19_m2_mcp_verification.md | 历史 | 2026-07-19 只读 MCP 20/20 稳定性验收的事件性验证记录，结论已成历史基线 | 留档 |

## 三、统计与建议

- **存活 5**（含 3 个“存活（部分）”）：docs/13、docs/15、docs/CLAUDE.md、docs/RECSYS_MEMORY_DESIGN.md、docs/m1_coldstart_candidates.md。
- **已被替代 19**：编号 00-06、08-12、16 及 docs/AGENTS.md、docs/README.md、docs/API_REFERENCE.md、docs/DEPLOYMENT.md、docs/DEVELOPER_GUIDE.md、docs/CLAUDE_PLUGIN_SETUP.md。多数建议移入既有 `docs/archive/`。
- **历史 8**：docs/07、docs/14、docs/DIFY_VS_TOOLS_COMPARISON.md、docs/Explore.md、docs/KB_UI_REDESIGN_SPEC.md、docs/PROJECT_BUSINESS_FLOW_WORKLOAD_REPORT.md、docs/TOOLS_USAGE.md、docs/2026-07-19_m2_mcp_verification.md。
- 三个“存活（部分）”文件各带一处需与根 AGENTS.md 同步的过时点（docs/15 的 Loop C 模型行、docs/CLAUDE.md 的必读清单、RECSYS 设计仅 L2 落地），本次盘点为只读任务，未做任何修改。
- docs/17-21、experiments/、archive/ 不在本次盘点范围（其中 17-21 为当前事实的主要承载文档，作为上表“取代者”引用）。

END-OF-REPORT
