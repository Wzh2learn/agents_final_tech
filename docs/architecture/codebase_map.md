# 代码资产与执行边界地图

> 状态: 活跃 | 更新: 2026-09-23 | 取代/被取代: 取代本文件旧规模统计与服务健康快照；历史见 Git

本文件说明仓内代码在哪里、怎样关联、验证需要什么，不是服务器存活报告。科研证据成熟度见 `paper/research_asset_map_v2.md`；当前状态见 `memory/STATE.md`；运行基线见 `memory/CORE.md`。

## 三个不同的系统

| 系统 | 入口与职责 | 不应混淆的边界 |
|---|---|---|
| 业务产品 | `serve.sh` → `src/main.py` → `src/web/` → `src/biz/` | M1 解析与 M2 问答，不等于研究实验 |
| 业务内 Agent | `src/agents/agent.py`、`src/biz/agent_service.py`：LangGraph ReAct、工具调用与会话记忆 | 面向用户请求，不是研发 Loop A/B/C/D |
| 研发治理 harness | `scripts/graph/`：派发、验证、审计、记录 | 面向代码/实验交付，不自动证明业务或研究成功 |

## 产品代码与依赖

| 资产 | 实现与调用关系 | 验证边界 |
|---|---|---|
| 启动 | 根 `serve.sh`；`scripts/run.sh` 为安全启动包装 | 默认 5050、`PGDATABASE_URL`、`vector_db` 是契约，不是当前健康结论 |
| M1 解析 | `src/biz/m1_statement_parser.py`、`src/biz/m1_service.py` | OCR/模型回退依赖运行环境；纯函数测试不证明真实样本效果 |
| M1 入库 | `src/biz/m1_rag_ingest.py` → RAG/storage | 写数据库；未经授权不执行 |
| M2/RAG | `src/biz/m2_service.py`、`src/biz/rag_service.py` | 依赖数据库、检索与生成服务 |
| Agent/适配 | `src/agents/`、`src/biz/agent_service.py` 与 OpenCode 适配代码 | 与研发 CLI、模型部署分别管理 |
| 存储与工具 | `src/storage/`、`src/tools/` | PostgreSQL/PGVector、文件和文档工具 |
| MCP | `src/mcp_server/`、`src/vision_mcp_server/`、`src/tabular_mcp_server/` | 默认只读；进程是否安装、运行需执行面另行核验 |
| 表格推理子进程 | `src/tabular_mcp_server/service.py` → `scripts/run_tabular_inference.py` | 生产运行时依赖，不是可随意归档的孤立实验 |
| 兼容 CLI | `scripts/m1_statement_parser.py`、`scripts/m1_rag_ingest.py` | 委托 `src/biz/`，不能反向成为业务实现入口 |

`scripts/catalog.toml` 只分类 `scripts/`；其中 research 分类包含 `scripts/research/`，不覆盖仓库根 `research/`。根科研脚本以以下分组和资产账本为入口，不把整个目录当作执行白名单。

## 科研代码、输入与产出

| 资产组 | 输入 → 产出 | 当前可用性与执行面 |
|---|---|---|
| `scripts/research/drift_inject.py` | 原表/注入配置 → 漂移语料与注入映射 | 合成 fixture 可离线验证；正式语料生成须按既有计划授权 |
| 评估聚合、K2 与 `research/paper_d*` / `paper_t*` / `paper_w2*` | 已有 checkpoint/逐样本工件 → 汇总、稳健性与审稿证据 | 先查具体入口；有的仅聚合，有的会请求模型，不能按文件前缀推断零调用 |
| `research/vgmc_exp1.py` 与其他 VGMC 脚本 | drift_v0 语料、候选动作、规则状态 → 门控/拒绝/污染曲线 | `fewshot_pool` 等纯函数可用 fixture；完整回放/新数字归正式执行面 |
| `research/dpo_pairs_v0.py` | 旧生成入口：checkpoint → 偏好对；`--audit`：已有37件工件 → 来源/标签/历史划分审计 | 审计不加载语料/模型、不导出训练样本；结果见资产账本 §3.1；回归 `tests/test_distillation_data_audit.py` |
| `research/phase1a_data_contract.py` | v2 私有补充包 manifest + hash 绑定工件 → 七门聚合预检收据 | 校验 namespaced lineage UID/root/independence cluster 三层隔离、canonical Q3 ledger 和冻结统计合同；当前四层必有数据，future 可空但须 acquisition protocol 并标长期证据不可用。通过只到 `READY_FOR_INDEPENDENT_ACCEPTANCE`；回归 `tests/test_phase1a_data_contract.py` |
| `research/phase1a_learnability_baselines.py` | 已独立接收的 proposal train/dev 派生视图 + canonical ledger + 预注册配置 → 五类简单基线聚合开发报告 | 逐条核对 Q3 ledger，拒绝 gate/sealed/future 样本与事后特征；明确 `harmful_map_rate` / `map_to_risk` / `correct_map_coverage`，只给四种开发决策，不能放行训练；回归 `tests/test_phase1a_learnability_baselines.py` |
| `research/phase2_rule_gate_replay.py` | proposal/train 共享候选流 + 独立 gate-validation + 各臂规则状态 → 七类门 replay 聚合报告 | 每臂按自身状态重算 gain/collateral/gate delta，拒绝 sealed/future 和事后分数字段；分列 rule-level harm 与 UID-any-harm/Clopper–Pearson 上界；本地仅验证合成状态机；回归 `tests/test_phase2_rule_gate_replay.py` |
| `research/paper_result_views.py` | Phase 2 聚合报告 → Table 2 / Figure 4 稳定数据接口 | 只转换聚合字段并保留两种 harm 分母，强制 `paper_result=false` 和未验收水印；不能自行把 GB10 工件提升为论文证据 |
| bandit / PSO / 视觉探索脚本 | 各自实验输入 → 探索工件 | 历史/候选资产，不是本轮自动重开项目 |
| `research/validate_paper_claims.py` | 主张 manifest、正文、工件路径 → 静态验收 | 本地离线；路径/标记通过不等于复算数字或证明贡献 |
| `research/build_teacher_review_docx.py` | Markdown + 图表模板 → DOCX | 本地离线派生；结构测试不等于 Office 视觉验收 |

已有 JSON 位于 `logs/graph/eval/`，是对应已记录实验的数字依据；不能从聚合文件反推所有原始语料已在本机。用户说明执行环境、语料与模型资产在另一台服务器，本轮未核验，不下载、不搬运、不重建；本地缺件标为依赖待执行面核验，而非资产丢失或实验失败。

## 研发协作与自动化程度

- 设计依据：`docs/17_Graph_Engineering_多层Loop设计.md`；工程路线：`docs/29_graph_engineering_roadmap.md`。
- 执行面权威：`docs/governance/2026-09-07_execution_plane_boundary.md`。本地做控制、分析和审计；GB10 承载获批正式实验事实。
- D 给有界任务和授权；A 执行；B 独立验证；C 独立审计；D 验收。科研阶段顺序只来自 `docs/handoff/2026-09-22-paper-research-next-phase.md`。
- `graph_orchestrator.sh` 有 B 启动逻辑，A/C 分支主要给派发说明；不是完整 A→B→C 自动流水线。
- `loop_b_verify.sh` 的判分逻辑是确定性的，但默认 canary、API、QA/PG 检查会访问真实服务，不能当零调用单测执行。
- `dispatch_precheck.sh` 校验 watcher 与运行收据合同，不执行 watcher；合成收据只用于测试，不能作为真实开窗凭证。
- hooks、skills 分发、daemon 与调度都是机器安装状态；Git 中存在脚本不代表已接线或生效。本轮不修改全局安装。

## 定点验证地图

- 启动/分层/分类：`tests/test_runtime_contract.py`、`tests/test_production_module_boundaries.py`、`tests/test_script_catalog.py`。
- 科研纯逻辑：评估聚合测试、drift 合成用例、`tests/test_vgmc_baseline.py`、`tests/test_phase1a_data_contract.py`、`tests/test_phase1a_learnability_baselines.py`、`tests/test_phase2_rule_gate_replay.py`；逐项确认不加载真实语料或访问服务。
- 治理合同：`tests/test_document_governance.py`、`tests/test_dispatch_precheck.py`。
- 主张与派生件：`tests/test_paper_claim_acceptance.py`、`tests/test_research_story_assets.py`。

以上不是全仓运行健康证明。正式服务、模型、数据库和真实语料效果需单独授权、在指定执行面取证；冻结边界仍以 `AGENTS.md` 为准。
