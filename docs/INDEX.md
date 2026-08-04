# docs/INDEX.md — 文档导航唯一入口

- 更新: 2026-08-04 (验收审计补登记 README/data-card) | 维护: Loop D 每次 neat/收尾时同步本文件
- 新会话阅读顺序: 根 AGENTS.md → memory/STATE.md → 本文件。现状以 memory/ 为准，不要到历史文档里找现状。

## 活文档（持续维护；内容冲突时以这些为准）

| 文档 | 用途 |
|---|---|
| 根 `AGENTS.md` | agent 约束、架构边界、模型路由、Skill 武库注册表 |
| `17_Graph_Engineering_多层Loop设计.md` | 四层 Loop 设计与运行机制 |
| `18_多Agent编排工具演进计划.md` | 工具演进计划 + 记忆系统排期 |
| `CLAUDE.md` | Claude Code (Loop C) 阅读指引 |
| `m1_coldstart_candidates.md` | schema 候选列治理记录 |
| 根 `logs/graph/dispatch_log.md` | 原始事件流（与 memory/ 蒸馏层两轨并行） |
| 根 `memory/` | 蒸馏记忆层: CORE / DECISIONS / STATE / THREADS |

## 当前（当前事实与交付面）

- `19_系统能力说明书.md` — 面向甲方的业务视角能力说明（交付面）
- `20_部署指南.md` — 部署方式与环境要求
- `21_基础设施盘点与gap解决规划.md` — 资源盘点 + 3 个 known gap 解决路径
- `15_远程开发机_Codex_CLI_与_OpenCode_配置.md` — GB10 开发机配置与模型切换指南
- `09_OpenCode与现有RAG_MCP实施方案.md` — OpenCode 交付链路路线图 ⚠️ 交付物，禁止归档/删除
- `10_OpenCode开发机运行说明.md` — OpenCode 开发机运行 ⚠️ 交付物，禁止归档/删除
- `2026-07-19_m2_mcp_verification.md` — MCP 20/20 验收基线 ⚠️ 交付物证据，禁止归档/删除
- `13_M1_M2联合数据闭环计划.md` — 公开数据集政策依据（研究线已冻结，与 AGENTS.md 冻结声明配套阅读）
- `RECSYS_MEMORY_DESIGN.md` — 记忆子系统设计依据（L2 情景记忆已实现并在用）
- `22_overnight_loopD_neat_closeout.md` — 8 小时自主循环收尾记录
- `architecture/` — codebase map、skill 体检报告、Phase 2 盘点报告
- `README.md` — docs 目录指针文件（导航以本 INDEX.md 为准）
- `datasets/tat-dqa-joint-v1-data-card.md` — TAT-DQA 公开数据集 data card（研究线冻结起点）

## 实验（experiments/，只追加不重写）

- `SUMMARY_audit_loop_c.md` — 9 轮 Loop C 审计汇总（审计历史先读这个；更正 docs/22 §12 旧口径）
- scenario1 解析、UI 截图序列、性能基准、模型对比、各实验与审计报告（按日期命名）

## 归档（archive/，只读历史，不得作为现状依据）

- 已被替代的编号文档: 00-08、11、12、14、16
- 初期杂项: API_REFERENCE / DEPLOYMENT / DEVELOPER_GUIDE / TOOLS_USAGE / Explore / KB_UI_REDESIGN_SPEC / DIFY_VS_TOOLS_COMPARISON 等
- 根目录历史快照: PROJECT_REVIEW_REPORT / code_review_prompt / implementation_guide / README_legacy_1115lines

## 治理规则

1. 新增文档: 当前事实 → docs/ 顶层编号；实验记录 → experiments/；废弃 → `git mv` 进 archive/（禁止 rm）。任何归档/新增必须同步更新本文件。
2. HANDOFF.md 冻结于 2026-08-03 快照，不再更新；现状快照一律写 memory/STATE.md。
3. OpenCode/MCP 交付物三件（09 / 10 / 2026-07-19_m2_mcp_verification）永不归档或删除。
4. 盘点依据与矛盾修复记录: `architecture/phase2_docs_inventory.md`、`architecture/phase2_root_md_conflicts.md`。