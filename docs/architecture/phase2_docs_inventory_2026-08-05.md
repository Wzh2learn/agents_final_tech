# 全量文档普查报告（2026-08-05）

> 状态: 历史-参考（一次性普查过程记录） | 更新: 2026-08-05 | 取代/被取代: 无
> 基线: 根 AGENTS.md + memory/CORE.md/STATE.md/THREADS.md（2026-08-04 快照）。方式: 3 个并行只读子代理分区普查 + 主线程引用反查。执行结果: 顶层归档 4 件、experiments 归档 22 件、INDEX 目录表格化、存活文档全部加状态标记。

## 1. docs/ 顶层（普查时 18 件）

| 文件 | 摘要 | 判定 | 处置 |
|---|---|---|---|
| 09_OpenCode与现有RAG_MCP实施方案.md | OpenCode+RAG MCP 交付路线图（阶段 A-D） | 存活（交付物） | 按新保护规则归档至 archive/，永不删除，交付链路启动时仍是依据 |
| 10_OpenCode开发机运行说明.md | GB10 OpenCode/三个只读 MCP 运行说明（20/20） | 存活（交付物） | 同上 |
| 2026-07-19_m2_mcp_verification.md | 只读 MCP 20/20 稳定性验收事件记录 | 历史（交付物证据） | 同上 |
| 22_overnight_loopD_neat_closeout.md | 过夜 8h Loop D neat 收尾记录 | 完成-可归档 | 归档；现状记录职能由 memory/ 接管；内部标题 #18→#22 撞车已修 |
| 13_M1_M2联合数据闭环计划.md | TAT-DQA joint-v1 数据/评测主线计划 | 历史-政策依据 | 留顶层（公开数据集与 split 政策唯一依据，根 AGENTS.md 指定必读，研究线冻结配套） |
| 15_远程开发机_Codex_CLI_与_OpenCode_配置.md | GB10 配置 + 模型切换指南 | 存活-活跃 | 留顶层；"Loop C 用 glm-5.2" 过时行已改 qwen3.8-max |
| 17_Graph_Engineering_多层Loop设计.md | 四层 Loop 设计与安全机制 | 存活-活跃 | 留顶层 |
| 18_多Agent编排工具演进计划.md | 编排工具选型 + §10 记忆系统排期 | 存活-活跃 | 留顶层 |
| 19_系统能力说明书.md | 面向甲方能力说明 v1.0 | 存活-活跃 | 留顶层；"详见 docs/22" 引用改指 memory/THREADS.md |
| 20_部署指南.md | 部署方式与环境要求 | 存活-活跃 | 留顶层 |
| 21_基础设施盘点与gap解决规划.md | 资源盘点 + 3 gap 路径 | 存活-活跃 | 留顶层；头部"规划(未执行)"已改"已执行（3 gap CLOSED）" |
| 23_甲方阶段汇报.md | 甲方阶段汇报包 | 存活-待发送 | 留顶层（甲方入口；7 张截图已真实嵌入；发送版 docx 同目录） |
| 24_交付决策菜单.md | 开口清单 + 反馈→行动路由 | 存活-活跃 | 留顶层；docs/09 引用改指 archive 路径 |
| CLAUDE.md | Loop C 阅读指引（薄指针） | 存活-活跃 | 留顶层不合并；两处漂移已修（AGENTS.md 相对链、HANDOFF 已冻结） |
| INDEX.md | 文档导航唯一入口 | 存活-活跃 | 重写为目录表格（本文件配套） |
| m1_coldstart_candidates.md | 冻结 schema 候选列台账 | 存活-活跃 | 留顶层 |
| README.md | 入口指针 | 存活-活跃 | 留顶层 |
| RECSYS_MEMORY_DESIGN.md | 层次化记忆设计 v1.8 | 存活-设计依据 | 留顶层（L2 情景记忆已按设计落地并在用；与 memory/ 四层是不同系统，L1/L2 术语撞名需注意） |

## 2. architecture/ + datasets/（5 件）

| 文件 | 判定 | 处置 |
|---|---|---|
| architecture/codebase_map.md | 存活-活跃（抽查与实况一致；个别数字噪音不影响结论） | 保留 |
| architecture/skill_system_health.md | 与现状不符（报告称 skills/=10，实际 11，jinrong-docs-sync 未经扫描） | 头部加补注；下轮体检覆盖 11 个 |
| architecture/phase2_docs_inventory.md | 历史-参考（建议已基本执行；其"09/10 已被替代"判断被 2026-08-04 INDEX 规则覆盖，本轮按新保护规则归档） | 保留 |
| architecture/phase2_root_md_conflicts.md | 历史-参考（修复项抽查已落实） | 保留 |
| datasets/tat-dqa-joint-v1-data-card.md | 存活-活跃（规范性冻结契约，配套 manifest/checks/脚本/测试齐全） | 保留 |

## 3. docs/experiments/（普查时 45 文件 + 3 目录）

| 组 | 判定 | 处置 |
|---|---|---|
| 初始模型服务与冒烟（07-10~07-14，3 件） | 历史-参考 | model_services + tabular_smoke 归档；vision_smoke 保留（PaddleOCR-VL 不兼容根因依据） |
| TAT-DQA 研究基线（07-23，1 件） | 存活（研究线冻结非删除） | 保留 |
| M1 parser 迭代周（07-28~07-29，14 件） | 混合 | 5 件保留（baseline/chunking/rerank/retrieval_ablation/verify_and_mcp + schema_reconcile 保守保留）；8 件过期归档 |
| Qoder 迁移侦察（07-29，1 件） | 存活（决策 pending 等 PAT） | 保留 |
| 72B 模型对比（07-30~07-31，2 件） | 完成（结论已固化进 docs/18 §16 与 AGENTS.md） | 归档 |
| Loop C 审计系列（07-31~08-02，10 件） | SUMMARY 存活；9 份分轮历史 | SUMMARY 保留；分轮 9 件归档（内容已归并入 SUMMARY） |
| M2 RAG 闭环与 E2E 基准（07-31~08-01，3 件） | 存活 | 保留 |
| PaddleOCR 调查（07-31，2 件） | 存活（永久不可用结论依据） | 保留 |
| UI 截图/演示物料（3 目录 + 顶层 1 png） | 存活（docs/19、23、AGENTS.md 活链） | 保留；顶层 zhikuncode png 近重复件归档 |
| Phase 3 代码审查（08-03~08-04，8 件） | 完成-证据链（STATE 仍引用） | 暂整组保留，待下轮审查覆盖后再归档 |

## 4. 漂移与修复记录（本轮）

1. 顶层 4 件 + experiments 22 件 git mv 归档；INDEX 重写为目录表格并登记全部归档条目。
2. 存活文档头部统一加状态标记行（15 份，含 architecture/datasets 2 份）。
3. docs/19 → memory/THREADS.md 引用修正；docs/24 → archive/09 路径修正；HANDOFF 冻结标注 + archive/22 链接修正；AGENTS.md 开头阅读指引从 HANDOFF 改指 memory/STATE.md。
4. docs/15 模型路由行（glm-5.2 → qwen3.8-max）、docs/21 头部状态行、docs/22 标题撞车、skill_system_health 补注、CLAUDE.md 两处漂移均修复。
5. 治理规则变更: OpenCode/MCP 交付物三件从"永不归档/删除"改为"可归档、永不删除"（甲方 2026-08-05 指令），INDEX/CORE/jinrong-docs-sync skill 三处同步。
6. SUMMARY_audit_loop_c.md 处置表引用的 results/ 目录全历史不存在（从未入库），不构成死链风险，记录在案。
