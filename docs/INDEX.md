# docs/INDEX.md — 文档目录（唯一入口）

**甲方入口：[`docs/23_甲方阶段汇报.md`](23_甲方阶段汇报.md)** — 自包含发送版（图片全部内嵌，单文件可直接发）：`23_甲方阶段汇报_发送版.docx`

> 状态: 活跃 | 更新: 2026-08-13（S3 队列实验登记: dify 术语挖掘 + Docling 探针） | 取代/被取代: 无
> 维护: Loop D 每次 neat/收尾时同步本文件。新会话阅读顺序: 根 `AGENTS.md` → `memory/STATE.md` → 本文件。现状以 memory/ 为准，不要到历史文档里找现状。

## 活文档（持续维护；内容冲突时以这些为准）

| 文件 | 状态 | 一句话摘要 | 最后更新 |
|---|---|---|---|
| `INDEX.md` | 活跃 | 本目录表 | 2026-08-05 |
| `README.md` | 活跃 | docs 入口指针 | 2026-08-05 |
| `CLAUDE.md` | 活跃 | Claude Code (Loop C) 阅读指引（薄指针，以根 AGENTS.md 为准） | 2026-08-05 |
| `17_Graph_Engineering_多层Loop设计.md` | 活跃 | 四层 Loop（A 执行 / B 验证 / C 审计 / D 战略）设计与安全机制 | 2026-08-08 |
| `18_多Agent编排工具演进计划.md` | 活跃 | 编排工具选型 + §10 记忆系统 + §12 沉淀专项记录 | 2026-08-09 |
| `m1_coldstart_candidates.md` | 活跃 | 冻结 schema 之外的候选列台账，随甲方样本扩充更新 | 2026-07-30 |
| `RECSYS_MEMORY_DESIGN.md` | 设计依据 | 层次化记忆设计 v1.8；L2 情景记忆已实现并在用；§8/§9 为研究议程 | 2026-02-20 |
| 根 `AGENTS.md` / `memory/` / `logs/graph/dispatch_log.md` | 活跃 | agent 约束 / 蒸馏记忆 / 事件流（docs 外，列此备查） | 随时 |

## 交付材料（对甲方）

| 文件 | 状态 | 一句话摘要 | 最后更新 |
|---|---|---|---|
| `23_甲方阶段汇报.md` | 待发送（重写版等用户终审） | 重写版: 30s 执行摘要(4 关键数字) / 场景化能力 / 递进故事 / 诚实限制 / 需要您支持清单 + 10 张 08-12 实拍图; 口径演化移脚注; 话术拆内部文档 | 2026-08-12 |
| `23_甲方阶段汇报_发送版.docx` | 待发送（等用户终审） | 重写版发送包: 封面 + 10 图内嵌 + 4 关键数字; md5 bc3785cb4237dcda316120251fab8472 冻结待终审 | 2026-08-12 |
| `24_交付决策菜单.md` | 活跃 | 开口清单（样本请求）+ 反馈→行动路由 + 彩排记录 | 2026-08-04 |
| `19_系统能力说明书.md` | 活跃 | 面向甲方的业务视角能力说明 v1.1（+建议沉淀/对比分析/双链路） | 2026-08-09 |

## 当前阶段（事实 / 配置 / 依据）

| 文件 | 状态 | 一句话摘要 | 最后更新 |
|---|---|---|---|
| `20_部署指南.md` | 活跃 | 部署方式、环境要求、Docker Compose | 2026-08-01 |
| `21_基础设施盘点与gap解决规划.md` | 历史-参考（规划已全部执行） | 资源盘点 + 3 个 gap 解决路径（NCAMC/华泰/email 均已 CLOSED） | 2026-08-02 |
| `25_交付架构决策.md` | 活跃（决策已拍板，待执行） | 页面后端切 OpenCode 链：路线 A 保底 + B 目标 + 本地 embedding 前置梳理 | 2026-08-05 |
| `26_选择题体验设计.md` | 活跃（场景 A 已 walkthrough 验收 08-11; 场景 B 待触发） | 映射候选选择题面板设计 + 场景 B 设计 + 能力暴露度清单 + 甲方问答对账表附录 | 2026-08-10 |
| `27_M1M2页面改版_两个设计方向.md` | 方向已批（先 B 后 A, 代码等发送后） | M1/M2 页面改版两方向：A 三栏任务工作台 vs B 流水线画布控制台 + 公共规范（模式切换诚实设计/选择器保留表）+ 红线合规迁移预案 + 两个 HTML 草图 | 2026-08-11 |
| `28_业界对标与优化菜单.md` | 活跃（顺序已批 #2→#1→#4, 其余待拍板） | 四类对标(WorkBuddy/Manus/Devin/Cursor, Perplexity/NotebookLM/Dify, Docling/MinerU/LlamaParse/TextIn, RAGAS/DeepEval/TruLens) + Top5 优化菜单 + 四维审计清单附录 | 2026-08-11 |
| `29_graph_engineering_roadmap.md` | 活跃（菜单待拍板） | 人肉环节盘点 + 分级菜单 L1 status.sh / L2 任务卡模板 / L3 自动编排前提（暂缓） | 2026-08-12 |
| `30_科研线规划.md` | 活跃 | 科研线规划: VGMC 验证门控记忆固化 (三条素材线 / M0-M4 路线图 / 甲方数据零进入; 文末附 M0 文献调研任务卡) | 2026-08-13 |
| `31_导师进展汇报.md` | 活跃 | 导师预审包: 定位+架构/功能清单/前端重点节(12 图配看点)/战绩表/限制与下一步/请导师把关清单; 附录取回命令 | 2026-08-13 |
| `32_模型升级与多agent再思考.md` | 活跃（S4 双模型接线完成; 路线 B 权重未发布挂 watch） | 模型升级专项: 旧栈约束盘点 / Qwen3.8-27B+vLLM 探针事实 / P2 基准(矩阵+并发+judge+视觉) / 闸门判定与切换菜单 / 多 agent 再思考菜单 | 2026-08-16 |
| `33_导师指导吸收_科研三线升级.md` | 活跃 | 08-18 演示后导师三层指导吸收: hbkeyan 材料索引(GTA-2/Judge 实证/PSO 测评专利/指标手册) / 评估+改进+自学习三线框架 / 大论文四点+小论文 AB / 数据集策略 / 小模型矩阵 / §9 graph loop 精读与实验探索任务卡 | 2026-08-18 |
| `15_远程开发机_Codex_CLI_与_OpenCode_配置.md` | 活跃 | GB10 开发机配置与模型切换指南（Loop A flash / Loop C qwen3.8-max） | 2026-08-08 |
| `13_M1_M2联合数据闭环计划.md` | 历史-政策依据 | 公开数据集 / split 政策唯一依据（研究线冻结配套，根 AGENTS.md 指定必读） | 2026-07-22 |
| `architecture/codebase_map.md` | 活跃 | 代码库结构 + 依赖图 + 端口拓扑（含 :4096 sidecar） | 2026-08-08 |
| `architecture/gb10_vllm_startup_sop.md` | 活跃 | GB10 vLLM 启动 SOP: page cache 回收→GMEM=0.30→Mamba 并发上限→编译缓存; FM1-FM4 失败模式对策 + 基建通道台账 + 多实例内存算术 | 2026-08-16 |
| `architecture/skill_system_health.md` | 历史-参考 | Skill 体检报告（头部补注：第 11 个 skill 未经该轮扫描） | 2026-08-04 |
| `architecture/phase2_docs_inventory.md` | 历史-参考 | docs 00-16 盘点过程记录（2026-08-03） | 2026-08-03 |
| `architecture/phase2_root_md_conflicts.md` | 历史-参考 | 根目录 MD 一致性审查与修复记录 | 2026-08-03 |
| `architecture/phase2_docs_inventory_2026-08-05.md` | 历史-参考 | 本轮全量普查三张表（顶层 / architecture+datasets / experiments） | 2026-08-05 |
| `datasets/tat-dqa-joint-v1-data-card.md` | 活跃（冻结契约） | TAT-DQA 数据卡，研究线规范性冻结起点 | 2026-07-23 |

## 实验记录（experiments/，只追加不重写；日期前缀即时戳）

| 文件/目录 | 状态 | 一句话摘要 |
|---|---|---|
| `2026-08-06_tmux_inventory.md` | 存活-当前 | tmux 会话盘点: 6 pane 处置 + skill 分发漂移修复 + 安全台账 | 2026-08-06 |
| `2026-08-06_audit_loop_c_flash_fixes.md` | 活跃 | Loop C 审计: flash 首任务+三修复+A2 灰度 CONDITIONAL（后转 ACCEPTED） | 2026-08-06 |
| `2026-08-06_differential_phase3_to_head.md` | 活跃 | Loop C differential 4a151dd..HEAD: ACCEPTED, 33 findings (0C/1H/8M) | 2026-08-07 |
| `2026-08-07_full_system_inventory.md` | 活跃 | 全系统工具盘点: skills 三端 diff + doctor 实跑 + MCP/CLI/harness 证据与建议 | 2026-08-07 |
| `2026-08-08_eval_baseline.md` | 活跃 | eval 首份基线: M1 门禁 15/15 + M2 确定性 16/16 + judge 四维（含两次复测演化） | 2026-08-09 |
| `2026-08-09_demo_script.md` | 活跃 | 演示脚本 9 步（双链路快与准叙事） | 2026-08-09 |
| `2026-08-09_demo_video/steps.md` | 活跃 | 演示视频（5:10）步骤清单；视频文件不入 git（scp 取回，路径见 steps.md） | 2026-08-10 |
| `2026-08-10_audit_loop_c_differential.md` | 活跃 | Loop C differential a7f8282..HEAD: CONDITIONAL, 20 findings (0C/1H/6M)，T4 端点/门禁/RAG/docs/23 数字 | 2026-08-10 |
| `2026-08-11_low_hit_attribution.md` | 活跃 | 低分归因三类（规则覆盖/OCR 识别/统计口径）——甲方问答依据 | 2026-08-11 |
| `2026-08-11_m1m2_redesign/` | 待决策 | 页面改版两方向 HTML 草图（direction_a/b.html，静态可直接浏览器打开，配套 docs/27） | 2026-08-11 |
| `2026-08-11_agent_latency_diagnosis.md` | 活跃 | agent 路延迟根因诊断(冷 prefill 37s + 输出 reasoning) + 修复方案菜单(待拍板) | 2026-08-11 |
| `2026-08-12_client_experience_audit.md` | 活跃 | 甲方发送前自体验审计(15 步/0 错误/无必修项, 口头解释×4) + docs/23 声明复测表(漂移×2 入账, 其一当晚 T4① 修复) | 2026-08-12 |
| `2026-08-12_client_experience_audit/` | 活跃 | T1 原始数据 audit_raw.json + 截图 6 张（配套上条） | 2026-08-12 |
| `2026-08-12_audit_loop_c_differential.md` | 活跃 | Loop C differential 5535bdf..504810c: CONDITIONAL, FC-1 已修/FC-4 FC-5 复评 HIGH 存量/FC-7 8 9 合规 | 2026-08-12 |
| `2026-08-12_asset_activation_sweep.md` | 活跃 | Q1 休眠资产摸排: 8 资产探针证据 + Top3 激活建议(:8005 judge 分流/vision MCP 接样本目录/status.sh) | 2026-08-12 |
| `2026-08-12_mapping_table_reuse.md` | 活跃 | Q2 甲方映射表再挖掘: 别名表 56 产品/234 证券/61 机构 + compare 三级解析链(45 tests) + schema 差集=0 | 2026-08-12 |
| `2026-08-12_docs23_screenshots/` | 活跃 | docs/23 重写版 10 张实拍截图（含建议映射选择题面板 6 候选）+ shots_meta.json | 2026-08-12 |
| `2026-08-13_advisor_package/` | 活跃 | 导师包新拍 8 张（检索透明面板 top_k/score/路由 meta + sources 特写 + 建议面板）+ shots_meta.json | 2026-08-13 |
| `2026-08-18_demo_rehearsal/demo_script.md` | 活跃 | 明日导师演示脚本（双链路三段切换/逐步话术/预案/GO-NO-GO 判据） | 2026-08-18 |
| `2026-08-18_demo_rehearsal/rehearsal_results.md` | 活跃 | 彩排耗时表 + agent 路条件 GO 判定（warm-up 协议） | 2026-08-18 |
| `2026-08-18_demo_rehearsal/advisor_glossary_card.md` | 活跃 | 导师演示名词速查卡（10 条白话+技术底, 内部） | 2026-08-18 |
| `2026-08-18_claim_reality_audit.md` | 活跃 | 声明-实况对账审计（进程普查 0 倒挂/口径决议/新鲜度注） | 2026-08-18 |
| `2026-08-15_demo_video_v2/steps.md` | 活跃 | 演示视频 v2（3:48）分段清单；视频文件不入 git（scp 取回，路径见台账） | 2026-08-16 |
| `2026-08-12_dify_rule_terms_mining.md` | 活跃 | S3② dify 甲方规则 docx 术语挖掘: 确定性脚本 + 3 synonyms 补词(证券持仓明细), 诚实 delta=0 | 2026-08-13 |
| `2026-08-13_docling_probe.md` | 活跃 | S3④ Docling ARM64 探针: CPU 路可用, NCAMC 垂直行提取优于坐标重建, 定位离线 second-opinion | 2026-08-13 |
| `2026-08-12_demo_talk_track.md` | 活跃（内部, 不进发送版） | 演示话术清单（取代 docs/23 旧附录 C）: 双链路/递进故事/7 条口头解释 | 2026-08-12 |
| `2026-08-13_m0_literature_survey.md` | 历史-参考（结论活跃） | M0 文献调研: VGMC 差异化成立(附条件); CAIS/STATE-Bench 锚点未核验入台账; 可吸收清单 |
| `SUMMARY_audit_loop_c.md` | 活跃 | 9 轮 Loop C 审计汇总（审计历史先读这个） |
| `2026-08-05_opencode_e2e.md` | 活跃 | 交付链 S1-S5 端到端验证证据（OpenCode+MCP+多 agent，含检索降级根因） |
| `2026-08-04_rehearsal/` | 历史-参考 | 彩排截图 7 张（发送版已改用 08-12 重拍，本目录留档；demo 日志实测缺失，见 2026-08-10 审计 F19） |
| `2026-08-13_advisor_package_review.md` | 历史-参考 | 导师包发送前终审报告（Loop C 初审/复验/三验 + 受众分离轮，三轮达标） | 2026-08-16 |
| `2026-08-01_demo_sequence/` | 活跃 | 演示截图序列 11 张（AGENTS.md、docs/19 引用） |
| `2026-07-31_ui_screenshots/` | 活跃 | UI 截图 6 张（docs/19 引用） |
| `2026-08-01_field_accuracy.json` | 活跃 | 字段级准确率评测产物（21 checks / 100%） |
| `2026-07-31_paddleocr_arm64_investigation.md` | 活跃 | PaddleOCR ARM64 永久不可用结论的依据（fast-fail 门控） |
| `2026-07-23_tat_dqa_m2_upper_bound.md` | 活跃（研究线冻结） | TAT-DQA M2 上限基线 |
| `2026-07-29_qoder_recon.md` | 活跃 | Qoder 迁移侦察（决策 pending，等 PAT） |
| `2026-07-29_m1_verify_and_mcp.md` | 历史-参考 | 验证与 MCP 实验 |

## 归档（archive/，只读历史，不得作为现状依据）

| 条目 | 归档日期 | 说明 |
|---|---|---|
| `archive/09_OpenCode与现有RAG_MCP实施方案.md` | 2026-08-05 | ⚠️ OpenCode+MCP 交付路线图（交付物，永不删除；交付链路启动时仍是依据，从 archive 读取） |
| `archive/10_OpenCode开发机运行说明.md` | 2026-08-05 | ⚠️ OpenCode 开发机运行说明（交付物，永不删除） |
| `archive/2026-07-19_m2_mcp_verification.md` | 2026-08-05 | ⚠️ MCP 20/20 验收证据（交付物，永不删除） |
| `archive/22_overnight_loopD_neat_closeout.md` | 2026-08-05 | 过夜 8h 自主循环收尾记录（现状记录职能由 memory/ 接管） |
| `archive/experiments/`（22 件） | 2026-08-05 | 见下方清单 |
| 既有归档（34 件） | 2026-08-03 | 见下方清单 |
| `archive/experiments/`（2026-08-12 批，18 件） | 2026-08-12 | 七月实验 + Phase 3 审查集群 + embedding 审计；现状性能/eval 基线以 2026-08-08_eval_baseline.md 为准 |
| `archive/README_Codex_使用说明.md` | 2026-08-12 | 历史快照（文内自声明），现行以根 AGENTS.md / HANDOFF.md 为准 |

<details>
<summary>archive/experiments/ 22 件清单（2026-08-05 归档；审计分轮报告内容已归并入 SUMMARY_audit_loop_c.md）</summary>

2026-07-10_model_services.md / 2026-07-10_tabular_smoke_test.md / 2026-07-28_m1_llm_batch.md / 2026-07-28_m1_llm_extraction.md / 2026-07-28_m1_statement_parser.md / 2026-07-29_m1_compact_and_patch.md / 2026-07-29_m1_header_mapping_llm.md / 2026-07-29_m1_multiagent_delegation.md / 2026-07-29_m1_next_iteration.md / 2026-07-29_m1_ocr_fallback.md / 2026-07-30_72b_vs_35b_summary.md / 2026-07-31_72b_reevaluation.md / 2026-07-31_zhikuncode_ui_screenshot.png / 2026-07-31_audit_loop_c.md / 2026-07-31_audit_loop_c_2.md / 2026-07-31_audit_loop_c_3.md / 2026-07-31_audit_loop_c_4.md / 2026-07-31_audit_loop_c_5.md / 2026-07-31_audit_loop_c_6.md / 2026-07-31_audit_loop_c_r7.md / 2026-08-02_audit_loop_c_deepseek.md / 2026-08-02_audit_loop_c_qwen38.md
</details>

<details>
<summary>archive/experiments/ 18 件清单（2026-08-12 归档；性能/检索基线已由 eval 基线取代，Phase 3 审查集群结论已闭环）</summary>

2026-07-14_vision_smoke_test.md / 2026-07-28_chunking_and_integration.md / 2026-07-28_m1_baseline.md / 2026-07-28_rerank_experiment.md / 2026-07-28_retrieval_ablation.md / 2026-07-29_m1_schema_reconcile.md / 2026-07-31_e2e_benchmark.md / 2026-07-31_m2_rag_integration.md / 2026-07-31_paddleocr_vl_transformers_compat.md / 2026-08-03_code_review_dedup.md / 2026-08-05_audit_embedding_skill.md / phase3_loop_c_differential.md / phase3_loop_c_review_codebase.md / phase3_loop_c_spec_compliance.md / phase3_review_config_tests.md / phase3_review_deadcode.md / phase3_review_scripts.md / phase3_review_src.md
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
