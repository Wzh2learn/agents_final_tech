# docs/INDEX.md — 文档目录（唯一入口）

**甲方入口：[`docs/23_甲方阶段汇报.md`](23_甲方阶段汇报.md)** — 自包含发送版（图片全部内嵌，单文件可直接发）：`23_甲方阶段汇报_发送版.docx`

> 状态: 活跃 | 更新: 2026-08-05（全量文档普查 + 目录表格化；本轮归档 26 件） | 取代/被取代: 无
> 维护: Loop D 每次 neat/收尾时同步本文件。新会话阅读顺序: 根 `AGENTS.md` → `memory/STATE.md` → 本文件。现状以 memory/ 为准，不要到历史文档里找现状。

## 活文档（持续维护；内容冲突时以这些为准）

| 文件 | 状态 | 一句话摘要 | 最后更新 |
|---|---|---|---|
| `INDEX.md` | 活跃 | 本目录表 | 2026-08-05 |
| `README.md` | 活跃 | docs 入口指针 | 2026-08-05 |
| `CLAUDE.md` | 活跃 | Claude Code (Loop C) 阅读指引（薄指针，以根 AGENTS.md 为准） | 2026-08-05 |
| `17_Graph_Engineering_多层Loop设计.md` | 活跃 | 四层 Loop（A 执行 / B 验证 / C 审计 / D 战略）设计与安全机制 | 2026-08-04 |
| `18_多Agent编排工具演进计划.md` | 活跃 | 编排工具选型 + §10 记忆系统排期（mem0 L2） | 2026-08-04 |
| `m1_coldstart_candidates.md` | 活跃 | 冻结 schema 之外的候选列台账，随甲方样本扩充更新 | 2026-07-30 |
| `RECSYS_MEMORY_DESIGN.md` | 设计依据 | 层次化记忆设计 v1.8；L2 情景记忆已实现并在用；§8/§9 为研究议程 | 2026-02-20 |
| 根 `AGENTS.md` / `memory/` / `logs/graph/dispatch_log.md` | 活跃 | agent 约束 / 蒸馏记忆 / 事件流（docs 外，列此备查） | 随时 |

## 交付材料（对甲方）

| 文件 | 状态 | 一句话摘要 | 最后更新 |
|---|---|---|---|
| `23_甲方阶段汇报.md` | 待发送（等人审阅） | 甲方阶段汇报包：定位 / 能力 / 战绩 / 限制 / 路线图 + 7 张彩排截图 | 2026-08-05 |
| `23_甲方阶段汇报_发送版.docx` | 待发送（等人审阅） | 自包含发送版，图片全部内嵌，单文件可直接发 | 2026-08-05 |
| `24_交付决策菜单.md` | 活跃 | 开口清单（样本请求）+ 反馈→行动路由 + 彩排记录 | 2026-08-04 |
| `19_系统能力说明书.md` | 活跃 | 面向甲方的业务视角能力说明 v1.0 | 2026-08-01 |

## 当前阶段（事实 / 配置 / 依据）

| 文件 | 状态 | 一句话摘要 | 最后更新 |
|---|---|---|---|
| `20_部署指南.md` | 活跃 | 部署方式、环境要求、Docker Compose | 2026-08-01 |
| `21_基础设施盘点与gap解决规划.md` | 活跃（规划已全部执行） | 资源盘点 + 3 个 gap 解决路径（NCAMC/华泰/email 均已 CLOSED） | 2026-08-02 |
| `25_交付架构决策.md` | 活跃（决策已拍板，待执行） | 页面后端切 OpenCode 链：路线 A 保底 + B 目标 + 本地 embedding 前置梳理 | 2026-08-05 |
| `15_远程开发机_Codex_CLI_与_OpenCode_配置.md` | 活跃 | GB10 开发机配置与模型切换指南（Loop A/C 均 qwen3.8-max） | 2026-08-03 |
| `13_M1_M2联合数据闭环计划.md` | 历史-政策依据 | 公开数据集 / split 政策唯一依据（研究线冻结配套，根 AGENTS.md 指定必读） | 2026-07-22 |
| `architecture/codebase_map.md` | 活跃 | 代码库结构 + 依赖图 + 端口拓扑（普查抽查与实况一致） | 2026-08-04 |
| `architecture/skill_system_health.md` | 历史-参考 | Skill 体检报告（头部补注：第 11 个 skill 未经该轮扫描） | 2026-08-04 |
| `architecture/phase2_docs_inventory.md` | 历史-参考 | docs 00-16 盘点过程记录（2026-08-03） | 2026-08-03 |
| `architecture/phase2_root_md_conflicts.md` | 历史-参考 | 根目录 MD 一致性审查与修复记录 | 2026-08-03 |
| `architecture/phase2_docs_inventory_2026-08-05.md` | 历史-参考 | 本轮全量普查三张表（顶层 / architecture+datasets / experiments） | 2026-08-05 |
| `datasets/tat-dqa-joint-v1-data-card.md` | 活跃（冻结契约） | TAT-DQA 数据卡，研究线规范性冻结起点 | 2026-07-23 |

## 实验记录（experiments/，只追加不重写；日期前缀即时戳）

| 文件/目录 | 状态 | 一句话摘要 |
|---|---|---|
| `2026-08-06_tmux_inventory.md` | 存活-当前 | tmux 会话盘点: 6 pane 处置 + skill 分发漂移修复 + 安全台账 | 2026-08-06 |
| `SUMMARY_audit_loop_c.md` | 活跃 | 9 轮 Loop C 审计汇总（审计历史先读这个） |
| `2026-08-05_opencode_e2e.md` | 活跃 | 交付链 S1-S5 端到端验证证据（OpenCode+MCP+多 agent，含检索降级根因） |
| `2026-08-04_rehearsal/` | 活跃 | 彩排截图 7 张 + demo 日志（docs/23 引用，勿动） |
| `2026-08-01_demo_sequence/` | 活跃 | 演示截图序列 11 张（AGENTS.md、docs/19 引用） |
| `2026-07-31_ui_screenshots/` | 活跃 | UI 截图 6 张（docs/19 引用） |
| `2026-07-31_e2e_benchmark.md` | 活跃 | 唯一 e2e 性能基线 |
| `2026-07-31_m2_rag_integration.md` | 活跃 | M2 RAG 闭环记录 |
| `2026-08-01_field_accuracy.json` | 活跃 | 字段级准确率评测产物（21 checks / 100%） |
| `2026-07-31_paddleocr_arm64_investigation.md` | 活跃 | PaddleOCR ARM64 永久不可用结论的依据（fast-fail 门控） |
| `2026-07-31_paddleocr_vl_transformers_compat.md` | 活跃 | PaddleOCR-VL transformers 兼容性调查 |
| `2026-07-23_tat_dqa_m2_upper_bound.md` | 活跃（研究线冻结） | TAT-DQA M2 上限基线 |
| `2026-07-29_qoder_recon.md` | 活跃 | Qoder 迁移侦察（决策 pending，等 PAT） |
| `2026-07-14_vision_smoke_test.md` | 历史-参考 | PaddleOCR-VL 不兼容根因的环境依据 |
| `2026-07-28_m1_baseline.md` | 历史-参考 | M1 parser 基线 |
| `2026-07-28_chunking_and_integration.md` | 历史-参考 | chunking 与集成实验 |
| `2026-07-28_rerank_experiment.md` | 历史-参考 | rerank 实验 |
| `2026-07-28_retrieval_ablation.md` | 历史-参考 | 检索消融实验 |
| `2026-07-29_m1_schema_reconcile.md` | 历史-参考 | schema 与勾稽实验 |
| `2026-07-29_m1_verify_and_mcp.md` | 历史-参考 | 验证与 MCP 实验 |
| `2026-08-03_code_review_dedup.md` | 完成-证据链 | Phase 3 审查总报告（7 份分报告 + 分诊） |
| `phase3_loop_c_differential.md` / `phase3_loop_c_review_codebase.md` / `phase3_loop_c_spec_compliance.md` / `phase3_review_config_tests.md` / `phase3_review_deadcode.md` / `phase3_review_scripts.md` / `phase3_review_src.md` | 完成-证据链 | Phase 3 各分报告 |

## 归档（archive/，只读历史，不得作为现状依据）

| 条目 | 归档日期 | 说明 |
|---|---|---|
| `archive/09_OpenCode与现有RAG_MCP实施方案.md` | 2026-08-05 | ⚠️ OpenCode+MCP 交付路线图（交付物，永不删除；交付链路启动时仍是依据，从 archive 读取） |
| `archive/10_OpenCode开发机运行说明.md` | 2026-08-05 | ⚠️ OpenCode 开发机运行说明（交付物，永不删除） |
| `archive/2026-07-19_m2_mcp_verification.md` | 2026-08-05 | ⚠️ MCP 20/20 验收证据（交付物，永不删除） |
| `archive/22_overnight_loopD_neat_closeout.md` | 2026-08-05 | 过夜 8h 自主循环收尾记录（现状记录职能由 memory/ 接管） |
| `archive/experiments/`（22 件） | 2026-08-05 | 见下方清单 |
| 既有归档（34 件） | 2026-08-03 | 见下方清单 |

<details>
<summary>archive/experiments/ 22 件清单（2026-08-05 归档；审计分轮报告内容已归并入 SUMMARY_audit_loop_c.md）</summary>

2026-07-10_model_services.md / 2026-07-10_tabular_smoke_test.md / 2026-07-28_m1_llm_batch.md / 2026-07-28_m1_llm_extraction.md / 2026-07-28_m1_statement_parser.md / 2026-07-29_m1_compact_and_patch.md / 2026-07-29_m1_header_mapping_llm.md / 2026-07-29_m1_multiagent_delegation.md / 2026-07-29_m1_next_iteration.md / 2026-07-29_m1_ocr_fallback.md / 2026-07-30_72b_vs_35b_summary.md / 2026-07-31_72b_reevaluation.md / 2026-07-31_zhikuncode_ui_screenshot.png / 2026-07-31_audit_loop_c.md / 2026-07-31_audit_loop_c_2.md / 2026-07-31_audit_loop_c_3.md / 2026-07-31_audit_loop_c_4.md / 2026-07-31_audit_loop_c_5.md / 2026-07-31_audit_loop_c_6.md / 2026-07-31_audit_loop_c_r7.md / 2026-08-02_audit_loop_c_deepseek.md / 2026-08-02_audit_loop_c_qwen38.md
</details>

<details>
<summary>既有归档 34 件清单（2026-08-03 归档）</summary>

00_Codex_启动提示词.md / 01_项目背景与目标.md / 02_阶段计划与分工.md / 03_技术架构与模块设计.md / 04_服务器与模型部署计划.md / 05_开发任务清单.md / 06_Remote_SSH_开发流程.md / 07_角色B_模型调研与研究方向.md / 08_GB10模型服务两阶段计划_老师汇报版.md / 11_开发机_Codex_CLI_交接.md / 12_阶段收尾与对外汇报.md / 14_角色B_开发日志_老师汇报版.md / 16_Qoder_CLI迁移评估与计划.md / AGENTS.md / API_REFERENCE.md / ARCHITECTURAL_REVIEW_REPORT.md / CLAUDE_PLUGIN_SETUP.md / CODE_REVIEW_COMPREHENSIVE_20260118.md / code_review_prompt.md / codex_migration_pack_all_in_one.md / DEPLOYMENT.md / DEVELOPER_GUIDE.md / DIFY_VS_TOOLS_COMPARISON.md / Explore.md / implementation_guide.md / KB_UI_REDESIGN_SPEC.md / OPTIMIZATION_IMPLEMENTATION_REPORT.md / PROJECT_BUSINESS_FLOW_WORKLOAD_REPORT.md / PROJECT_REVIEW_REPORT.md / README_legacy_1115lines.md / README_scripts_2026-07-21.md / REVIEW_REPORT_20260118.md / TOOLS_USAGE.md / VibeCoding_Migration_Kit_Merged.md
</details>

## 治理规则

1. 新增文档: 当前事实 → docs/ 顶层编号；实验记录 → experiments/；废弃 → `git mv` 进 archive/（禁止 rm）。任何归档/新增必须同步更新本文件，同一 commit。
2. 存活文档（本目录顶层 + architecture/ + datasets/）头部必须有状态标记行 `状态: … | 更新: … | 取代/被取代: …`；experiments/ 只追加不重写，以日期前缀为时效标记。
3. OpenCode/MCP 交付物三件（09 / 10 / 2026-07-19_m2_mcp_verification）：**永不删除**；2026-08-05 起归档于 archive/，本文件归档组保留条目。
4. HANDOFF.md 冻结为 2026-08-04 快照，不再更新；现状快照一律写 memory/STATE.md。
5. gap/遗留项台账唯一存放于 memory/THREADS.md，其他文档只引用不复述。
6. 盘点依据与矛盾修复记录: `architecture/phase2_docs_inventory.md`、`architecture/phase2_root_md_conflicts.md`、`architecture/phase2_docs_inventory_2026-08-05.md`（本轮）。
