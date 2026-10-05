# Documentation Index

> 状态: 活跃 | 更新: 2026-09-23 | 取代/被取代: 取代原逐实验历史台账式索引

本文件只回答“去哪里找”。当前状态以 [`../memory/STATE.md`](../memory/STATE.md) 为准，未决事项以 [`../memory/THREADS.md`](../memory/THREADS.md) 为准，历史过程进入 Git、`experiments/` 或 `archive/`。

## 从这里开始

| 需要 | 权威入口 |
|---|---|
| 使用与本地启动 | [`../README.md`](../README.md) |
| Agent 规则与边界 | [`../AGENTS.md`](../AGENTS.md) |
| 当前状态 | [`../memory/STATE.md`](../memory/STATE.md) |
| 长期架构/运行基线 | [`../memory/CORE.md`](../memory/CORE.md) |
| 未决事项 | [`../memory/THREADS.md`](../memory/THREADS.md) |
| 已确认决策 | [`../memory/DECISIONS.md`](../memory/DECISIONS.md) |
| Skill 路由 | [`SKILL_ROUTING.md`](SKILL_ROUTING.md) |
| 科研主线与论文验收 | [`research/README.md`](research/README.md) |

## 产品与交付

| 文件 | 状态 | 用途 |
|---|---|---|
| [`23_甲方阶段汇报.md`](23_甲方阶段汇报.md) | 已发送快照 | 对甲方阶段汇报源文 |
| `23_甲方阶段汇报_发送版.docx` | 已发送冻结件 | 对外发送版 |
| [`19_系统能力说明书.md`](19_系统能力说明书.md) | 历史快照 | 2026-08-05 能力口径，不代表当前实现 |
| [`24_交付决策菜单.md`](24_交付决策菜单.md) | 历史快照 | 已消费的反馈与决策菜单 |
| [`25_交付架构决策.md`](25_交付架构决策.md) | 历史快照 | OpenCode 交付链决策过程 |
| [`26_选择题体验设计.md`](26_选择题体验设计.md) | 历史快照 | 体验方案 |
| [`27_M1M2页面改版_两个设计方向.md`](27_M1M2页面改版_两个设计方向.md) | 已实施 | 页面方向 A 的设计依据 |
| [`31_导师进展汇报.md`](31_导师进展汇报.md) | 已取代 | 旧导师汇报 |
| [`31_导师进展汇报_v2_20260825.md`](31_导师进展汇报_v2_20260825.md) | 冻结快照 | 导师汇报 v2 |

## 工程、运行与架构

| 文件 | 状态 | 用途 |
|---|---|---|
| [`datasets/2026-10-04_rq2_identification_and_acquisition_card.md`](datasets/2026-10-04_rq2_identification_and_acquisition_card.md) | 决策申请 | RQ2 identification、Route V/F、数据/许可/split/power 申报；不授权下载 |
| [`experiments/2026-10-04_q3_b0_b4_execution_plan.md`](experiments/2026-10-04_q3_b0_b4_execution_plan.md) | 计划 | Q3 R1/R2/ADJ 与 B0-B4 执行前置、可见性、预算、go/no-go；当前未运行 |
| [`experiments/2026-10-04_rq2_valentine_bridge_structure_audit.md`](experiments/2026-10-04_rq2_valentine_bridge_structure_audit.md) | 实证审计 | 10 pair trajectory/audit 结构、146 源列覆盖、gold 隔离与 RQ2 bridge 边界 |
| [`experiments/2026-10-04_q3_adjudicated_labels_and_b5_candidate.md`](experiments/2026-10-04_q3_adjudicated_labels_and_b5_candidate.md) | 用户确认摘要 | Q3 R1/R2/ADJ exploratory 汇总与 B5 候选边界；raw/hash 待封存 |
| [`datasets/phase1a_q3_seal_receipt_v1.json`](datasets/phase1a_q3_seal_receipt_v1.json) | Pre-seal 收据 | 五个必需 raw 工件当前 MISSING；输入模板/哈希与误认候选已登记 |
| [`experiments/2026-10-04_q3_boundary_blocker_audit.md`](experiments/2026-10-04_q3_boundary_blocker_audit.md) | 边界审计 | raw MISSING、三条异常引用 A/B 处置、B5 offline audit |
| [`experiments/2026-10-04_q3_full_delivery_seal_validation.md`](experiments/2026-10-04_q3_full_delivery_seal_validation.md) | Seal validation | 10-file raw package, 9/9 hashes, corrected ledger and visibility exceptions |
| [`experiments/2026-10-04_q3_partial_delivery_validation.md`](experiments/2026-10-04_q3_partial_delivery_validation.md) | Superseded snapshot | Partial-delivery state before full raw package arrived |
| [`datasets/2026-10-04_b0_b4_exploratory_split_protocol_v1.md`](datasets/2026-10-04_b0_b4_exploratory_split_protocol_v1.md) | Draft protocol | leave-one-pair-out / group-aware exploratory split；NOT_RUN |
| [`datasets/2026-10-04_b0_b4_exploratory_freeze_v1.json`](datasets/2026-10-04_b0_b4_exploratory_freeze_v1.json) | Superseded freeze | first run invalidated by salted B4 alignment bug |
| [`datasets/2026-10-04_b0_b4_exploratory_config_v1.json`](datasets/2026-10-04_b0_b4_exploratory_config_v1.json) | Frozen config | LOO / salted sensitivity / bootstrap 2000 configuration |
| [`datasets/2026-10-04_b0_b4_exploratory_freeze_v2.json`](datasets/2026-10-04_b0_b4_exploratory_freeze_v2.json) | Valid freeze | v2 runner/input bindings before validated rerun |
| [`datasets/2026-10-04_b0_b4_exploratory_results_v2.json`](datasets/2026-10-04_b0_b4_exploratory_results_v2.json) | Machine result | primary and mandatory sensitivity metrics, hashes |
| [`experiments/2026-10-04_b0_b4_exploratory_probe_results_v2.md`](experiments/2026-10-04_b0_b4_exploratory_probe_results_v2.md) | Exploratory result | B0-B4 v2 interpretation and evidence boundary |
| [`datasets/2026-10-05_stage_d_necessity_gate_v1.json`](datasets/2026-10-05_stage_d_necessity_gate_v1.json) | Machine gate | risk_limit=0.10 necessity verdict |
| [`experiments/2026-10-05_stage_d_necessity_gate.md`](experiments/2026-10-05_stage_d_necessity_gate.md) | Gate report | PILOT_ONLY risk-constrained coverage judgment |
| [`experiments/2026-10-05_internal_deliverable_completion_audit.md`](experiments/2026-10-05_internal_deliverable_completion_audit.md) | Completion audit | internal paper/thesis deliverables complete; research goal remains open |
| [`experiments/2026-10-05_stage_d_data_no_go_boundary_and_requirements.md`](experiments/2026-10-05_stage_d_data_no_go_boundary_and_requirements.md) | Formal boundary | DATA_NO_GO / RQ2 NOT_IDENTIFIED with exact future requirements |
| [`datasets/2026-10-05_stage_d_training_readiness_config_v1.json`](datasets/2026-10-05_stage_d_training_readiness_config_v1.json) | Readiness config | A0-A3 / 4B smoke dry-run configuration and resource gates |
| [`datasets/2026-10-05_stage_d_training_readiness_validation_v1.json`](datasets/2026-10-05_stage_d_training_readiness_validation_v1.json) | Dry-run validation | PASS_DRY_RUN_ONLY, training execution blocked |
| [`experiments/2026-10-05_stage_d_training_readiness_report.md`](experiments/2026-10-05_stage_d_training_readiness_report.md) | Readiness report | resource/monitor/estimate summary; no training execution |
| [`experiments/2026-10-05_training_dependency_audit.md`](experiments/2026-10-05_training_dependency_audit.md) | Dependency audit | peft/trl installed; deepspeed replaced by single-device accelerate |
| [`experiments/2026-10-05_qwen_model_candidate_metadata_audit.md`](experiments/2026-10-05_qwen_model_candidate_metadata_audit.md) | Model metadata | immutable HF revisions and licence; weight sync blocked |
| [`experiments/2026-10-05_model_sync_blocked.md`](experiments/2026-10-05_model_sync_blocked.md) | Sync status | MODEL_SYNC_BLOCKED; network/token status without secret |
| [`datasets/2026-10-05_model_training_go_application_v1.md`](datasets/2026-10-05_model_training_go_application_v1.md) | Pending application | MODEL_GO / TRAINING_GO fields and blockers; not authorization |
| [`experiments/2026-10-05_stage_d_necessity_residual_memo.md`](experiments/2026-10-05_stage_d_necessity_residual_memo.md) | Necessity memo | risk-constrained coverage and A2 residual criteria |
| [`experiments/2026-10-05_stage_r_rq4_static_protocol.md`](experiments/2026-10-05_stage_r_rq4_static_protocol.md) | Static protocol | seven-arm order/state/rollback and C0-C3 analysis |
| [`datasets/2026-10-05_rq2_source_label_split_power_application_v1.md`](datasets/2026-10-05_rq2_source_label_split_power_application_v1.md) | Application | SOURCE/LABEL/SPLIT/POWER exact request, no download |
| [`datasets/2026-10-05_valentine_route_v_exact_annex_v1.json`](datasets/2026-10-05_valentine_route_v_exact_annex_v1.json) | Exact annex | approved revision has 10 clusters, 0 eligible new, 30-cluster gap |
| [`17_Graph_Engineering_多层Loop设计.md`](17_Graph_Engineering_多层Loop设计.md) | 设计依据 | 现役协作边界与历史架构；不提供任务授权或实时状态 |
| [`18_多Agent编排工具演进计划.md`](18_多Agent编排工具演进计划.md) | 历史快照 | 已执行的多 Agent 演进计划 |
| [`20_部署指南.md`](20_部署指南.md) | 历史快照 | 旧部署拓扑；当前启动以根 `serve.sh`/README 为准 |
| [`21_基础设施盘点与gap解决规划.md`](21_基础设施盘点与gap解决规划.md) | 历史参考 | 已执行的基础设施规划 |
| [`28_业界对标与优化菜单.md`](28_业界对标与优化菜单.md) | 历史快照 | 已消费的优化菜单 |
| [`29_graph_engineering_roadmap.md`](29_graph_engineering_roadmap.md) | 活跃路线入口 | 工程职责与历史 backlog 索引；当前未决只在 THREADS |
| [`32_模型升级与多agent再思考.md`](32_模型升级与多agent再思考.md) | 活跃 | 模型升级与多 Agent 专项 |
| [`15_远程开发机_Codex_CLI_与_OpenCode_配置.md`](15_远程开发机_Codex_CLI_与_OpenCode_配置.md) | 历史快照 | GB10 配置过程 |
| [`architecture/codebase_map.md`](architecture/codebase_map.md) | 活跃 | 生产/科研代码依赖、验证入口与执行边界；不声明实时健康 |
| [`architecture/gb10_vllm_startup_sop.md`](architecture/gb10_vllm_startup_sop.md) | 活跃 | GB10 vLLM 启动 SOP |
| [`architecture/skill_system_health.md`](architecture/skill_system_health.md) | 审计快照 | Skill 历史体检结果 |
| [`architecture/phase2_docs_inventory.md`](architecture/phase2_docs_inventory.md) | 历史参考 | 早期文档盘点 |
| [`architecture/phase2_docs_inventory_2026-08-05.md`](architecture/phase2_docs_inventory_2026-08-05.md) | 历史参考 | 2026-08-05 文档盘点 |
| [`architecture/phase2_root_md_conflicts.md`](architecture/phase2_root_md_conflicts.md) | 历史参考 | 根文档冲突处理记录 |

## 研究

| 文件 | 状态 | 用途 |
|---|---|---|
| [`research/README.md`](research/README.md) | 活跃 | 小论文、大论文、证据边界与论文导向验收的统一执行入口 |
| [`handoff/2026-09-22-paper-research-next-phase.md`](handoff/2026-09-22-paper-research-next-phase.md) | 活跃执行计划 | 后续 Agent 的论文科研优先级、阶段任务卡、验收门与止损路线 |
| [`handoff/2026-09-24_user_decision_packet.md`](handoff/2026-09-24_user_decision_packet.md) | 活跃决策请求 | 解锁实验线最小决策集：label 复核 canonical 参考、licence 签署、P1 下载范围、Loop A 沙箱口径、MIMO 批排期、专利确认 |
| [`13_M1_M2联合数据闭环计划.md`](13_M1_M2联合数据闭环计划.md) | 冻结政策依据 | 数据集与 split 政策 |
| [`30_科研线规划.md`](30_科研线规划.md) | 已被取代 | 旧科研路线 |
| [`33_导师指导吸收_科研三线升级.md`](33_导师指导吸收_科研三线升级.md) | 战略依据、受保护只读 | 导师政策来源；旧范围/排期不覆盖 research/README 的现役裁定 |
| [`34_专利_小论文_大论文协同研究路线.md`](34_专利_小论文_大论文协同研究路线.md) | 政策依据、受保护只读 | 专利公开边界继续有效；评估单线范围已被用户校准 |
| [`RECSYS_MEMORY_DESIGN.md`](RECSYS_MEMORY_DESIGN.md) | 设计依据 | 层次化记忆设计 |
| [`datasets/tat-dqa-joint-v1-data-card.md`](datasets/tat-dqa-joint-v1-data-card.md) | 冻结契约 | TAT-DQA 数据卡 |
| [`datasets/paper-public-source-registry-v1.json`](datasets/paper-public-source-registry-v1.json) | 活跃元数据合同 | 小论文 10 个公开来源的核验 commit、许可缺口、独立性簇命名空间与下载禁门；不含数据正文 |
| [`datasets/2026-09-24_phase1a_role_protocols_and_templates.md`](datasets/2026-09-24_phase1a_role_protocols_and_templates.md) | 活跃协议 | 七角色协议与模板：label_ledger 独立复核协议、licence_record / schema / analysis_plan 模板、receipt 与 ledger 运行器规格、装配日检查单；含零模型探针与 PENDING 口径 |
| [`datasets/2026-09-24_dA_canonical_reference_evidence.md`](datasets/2026-09-24_dA_canonical_reference_evidence.md) | 决策支持 | D-A 裁定证据：管线配置与当前 corpus 表头交集 0（选项 2 不可行），可行路径仅剩官方摘录或延后 P1 |
| [`datasets/2026-09-24_label_review_protocol_templates.md`](datasets/2026-09-24_label_review_protocol_templates.md) | 流程模板 | label 独立复核的载体可见性边界、R1/R2 判定提示与裁决记录模板、启动检查单 |
| [`datasets/2026-09-24_dC_download_scope_evidence.md`](datasets/2026-09-24_dC_download_scope_evidence.md) | 决策支持 | D-C 精确下载范围：FinQA train/dev（test 预留、private 排除）+ Valentine 10 个 NYC 目录；零下载实测 |
| [`datasets/2026-09-24_dB_licence_evidence.md`](datasets/2026-09-24_dB_licence_evidence.md) | 决策支持 | D-B 签署证据：FinQA README 零许可提及（registry 行被证伪）、Valentine Apache-2.0 + NYC 上游条款；签署范围确认四条 |
| [`datasets/phase1a_licence_record_v1.json`](datasets/phase1a_licence_record_v1.json) | 正式记录 | D-B licence_record：accepted_by=Wzh、现场 accepted_at、四项 permitted_uses；covered hashes 仅限 D-B annex 三件，不授权再分发/公开/商业/其他源或口径 |
| [`datasets/2026-09-25_phase1a_split_design_and_layer_capacity.md`](datasets/2026-09-25_phase1a_split_design_and_layer_capacity.md) | 活跃设计+实测 | SPLIT 预注册规则（双盐簇级分桶、标签盲、注册表驱动的角色门）与双命名空间层容量实测：FinQA M 扫描（M=8 → 286 UID）、Valentine 10 簇/146 列/K=10 且 dev 层为 0；四堵墙 W1-W4 与 G-A..G-E 裁定结果 |
| [`datasets/2026-09-25_finqa_process_structure_and_checkpoint_semantics.md`](datasets/2026-09-25_finqa_process_structure_and_checkpoint_semantics.md) | 活跃实测+设计约束 | FinQA 过程结构实测（7 134 例 / 10 960 gold 中间步 / 步键集统一 (op,arg1,arg2,res) / 21 个 op 根 / 多步例占 40.6%）与两种 checkpoint 语义的区分：冻结 Stage E = 表头注入族判别，FinQA = 推理步检查点；adapter 须为新命名空间新仪器，冻结数字零改动不溯及 |
| [`experiments/`](experiments/) | 只追加证据集 | 实验、审计、任务卡与结果；按文件名日期检索 |
| [`superpowers/`](superpowers/) | 计划快照 | 历史实施计划 |

## 治理

| 文件/目录 | 状态 | 用途 |
|---|---|---|
| [`README.md`](README.md) | 活跃 | docs 入口说明 |
| [`CLAUDE.md`](CLAUDE.md) | 活跃 | Claude Code 薄指针 |
| [`m1_coldstart_candidates.md`](m1_coldstart_candidates.md) | 活跃 | M1 冷启动候选列台账 |
| [`SKILL_ROUTING.md`](SKILL_ROUTING.md) | 活跃 | Skill 选择与组合规则 |
| [`governance/SKILL_REGISTRY.md`](governance/SKILL_REGISTRY.md) | 活跃 | Loop A/C 分发注册表 |
| [`governance/2026-09-07_execution_plane_boundary.md`](governance/2026-09-07_execution_plane_boundary.md) | 活跃 | 本地与 GB10 执行边界 |
| [`governance/2026-09-10_backlog_ledger_and_loop_restart_proposal.md`](governance/2026-09-10_backlog_ledger_and_loop_restart_proposal.md) | 提案快照 | backlog 与 Loop 重启提案 |
| [`governance/2026-09-11_serving_stack_provenance.md`](governance/2026-09-11_serving_stack_provenance.md) | 取证快照 | GB10 serving 栈来源证据 |
| [`governance/2026-09-24_gb10_experiment_safety_gates.md`](governance/2026-09-24_gb10_experiment_safety_gates.md) | 活跃 | GB10 实验安全与资源门：开工/停止阈值、并发与预算、进程回收、隔离纪律；含两处不可直接测量项（内存 free vs available、GB10 统一内存无独立 VRAM） |
| [`governance/audit/`](governance/audit/) | 只读证据集 | Harness 审计工件 |
| [`governance/reference/`](governance/reference/) | 参考资料 | 外部治理模板，不描述项目现状 |
| [`governance/2026-09-25_loop_a_sandbox_scoping_design.md`](governance/2026-09-25_loop_a_sandbox_scoping_design.md) | 活跃设计 | Loop A 沙箱分级（R 类 read-only / W 类 workspace-write / 禁 bypass）与派发核对清单（D-D 授权范围设计） |
| [`archive/`](archive/) | 只读历史 | 已归档文档；不得作为当前状态依据 |

## 维护规则

1. 顶层、`architecture/`、`datasets/` 和 `governance/` 的现役文件逐项登记。
2. `experiments/`、`governance/audit/`、`governance/reference/`、`superpowers/` 按目录登记，不维护逐文件流水账。
3. 新文档或归档操作必须与本索引同一提交；归档使用 `git mv`，禁止直接删除。
4. 顶层存活文档必须包含“状态 / 更新 / 取代或被取代”头部。
5. 当前状态只写 `memory/STATE.md`；未决事项只写 `memory/THREADS.md`；已结案历史保存在 Git、`memory/archive/` 或 `docs/archive/`。
6. `HANDOFF.md` 是冻结历史快照，不再作为当前入口。
