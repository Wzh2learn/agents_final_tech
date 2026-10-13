# 大论文文档结构与状态分类 v1

> 2026-10-13 | 依据：jinrong-docs-sync 四层结构 + neat-freak 状态口径 | 只做分类与入口整理，不改任何研究边界，不授权执行。

## 1. 四层映射（大论文线）

| 层 | 本线对应物 | 写入规则 |
|---|---|---|
| 活口径（先读） | MASTER_RESEARCH_EXECUTION_ENTRY_v1、THESIS_RESEARCH_GOVERNANCE_BASELINE_v1、THESIS_RESEARCH_ARCHITECTURE_v3、THESIS_EXECUTION_BLUEPRINT_v1、thesis_experience_v1_task_card | 事实/边界变化即更新；冲突时以此层为准（次序：入口→基线→架构→蓝图→卡） |
| 当前·凭证 | WP0_* 系列（资格/包/附录/协议/合约草案/冻结方案/执行包）、WP1_COMPLETION_RECORD_v1、THESIS_DIRECTIONS_AND_DECISIONS_MAP_v1、THESIS_DOCS_STRUCTURE_v1（本文）、WP2_EXECUTION_RUNBOOK_v1 | 只追加/修订事实；不重写历史结论 |
| 实验·收据 | research/tatqa_wp0_2026/**（代码+收据）、data/research/**（GB10 运行时）、各 run_logs | 只追加；收据绑定哈希；不提交数据体 |
| 归档·历史 | docs/research/history/2026-10-12_pre_governance/**；v1/v2 架构与旧蓝图快照；C 组冻结线文档（Stage D/R、FinQA、TAT-DQA、PR、Route B、EDR） | 只读；禁止作为现状依据；归档用 git mv 不用 rm |

## 2. 状态分类（每份文档一句话现状）

- 活口径五件：verified-current（2026-10-13 复核，无矛盾）。
- WP0 资格线：CLOSED（A1–A6 收据齐）；G-RQ 建议 QUALIFIED_CONDITIONAL、G-M 仍 HOLD。
- WP1 工具线：DELIVERED（run3 PASS，spec rev1.2；复审计 items/scope PASS）。
- 评测协议：SPEC_ONLY（WP-2 用；未冻结）。
- feedback-right 合约：DRAFT（5 个空待导师）。
- actor 冻结方案：PLAN（F1–F5；MODEL_GO 未批）。
- Loop A 执行包：dispatch log 至 run3 + 审计（历史+复用）。
- 负结果核查：CLOSED（复算 11/11 + 字节级重跑 + bug-lens PASS）。
- 历史冻结组：只读（详见 directions map §3C），不进现状链。
- Paper E 资产：跨线引用（paper/ 与 docs/research 双域；以 handoff/gate 为准）。

## 3. 阅读顺序（唯一链）

1. MASTER_RESEARCH_EXECUTION_ENTRY_v1
2. THESIS_RESEARCH_GOVERNANCE_BASELINE_v1（边界与两门）
3. THESIS_RESEARCH_ARCHITECTURE_v3（范围与 RQ）
4. THESIS_EXECUTION_BLUEPRINT_v1（工作包与参数）
5. thesis_experience_v1_task_card（当前最小问题）
6. THESIS_DIRECTIONS_AND_DECISIONS_MAP_v1（方向菜单与拍板点）
7. THESIS_DOCS_STRUCTURE_v1（本文，目录与状态）
按需凭证：WP0/WP1 系列、WP2_EXECUTION_RUNBOOK_v1、ADVISOR brief。

## 4. 更新职责与红线

- 谁更新什么：Loop D 维护活口径与凭证；Loop A/C 只写各自执行/审计产物。
- 不新增平行 registry；docs/INDEX.md 保持单入口；历史只读。
- 不重开 C 组冻结线；不把历史快照当现状依据。
- WP-2 开跑前必读：蓝皮书 §2 + 评测协议 + runbook。

## 5. 本轮一致性检查

- INDEX 单入口：今天新增文档（map/结构/runbook/核查）均已登记（见 INDEX 对应行）。
- 无死引用：活口径五件互引完整；凭证引用均指向存在文件。
- 状态无越级：无文档声称未发生的执行结果（G-RQ/G-M 仍为建议态；WP-2 未运行）。
