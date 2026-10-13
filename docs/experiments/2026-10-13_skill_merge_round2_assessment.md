# Skill 库第二轮合并评估（2026-10-13，只读评估 + 建议）

> 状态: 评估稿（未修改任何 skill、未运行 sync、未改分发表） | 范围: 仓库 `skills/`（source of truth，93 个目录）+ `scripts/graph/sync_skills.sh` 分发表
> 工具: skill-merger 扫描口径 + 人工 front matter / 分发表双向核对 | 基线对比: 09-21 批 #8-A（`docs/experiments/2026-09-21_skill_merge_proposal.md`）

## 0 结论先行

**本轮建议：不做任何新的 skill 合并。**

理由：高价值合并簇已由 09-21 批清空（10 簇已执行，目录 108→92）；剩余候选逐一复核后（C9/C10 延后簇 + C11/C15 已裁定簇 + 本轮新检查的疑似簇）均不建议执行；库规模已处于"触发边界清晰"的合理水位，继续合并的边际收益小于触发面损失。

唯一发现的注册表现象（非问题）：`verification-before-completion` 是"在盘未登记"的孤儿目录，但它已于 2026-08-26 标 DEPRECATED（SKILL.md 头部注明 + `SKILL_ROUTING.md` 第 30 行登记），不再分发，符合治理规则 4"只标记不删除"——**无需动作**。

## 1 扫描概况

| 项目 | 值 | 说明 |
|---|---|---|
| 仓库 `skills/` 目录数 | **93** | 09-21 批合并后为 92；期间净 +1（`inquiry-methods` 路由件，吸收 `portfolio-triage`） |
| `A_SKILLS` 项数 | **77** | 与 09-21 批合并后一致 |
| `C_SKILLS` 项数 | **22** | 同上 |
| 登记未在盘 | **0** | 分发表与磁盘双向核对 |
| 在盘未登记 | **1** | `verification-before-completion`（已废保留，见 §0 说明） |

与 09-21 裁定对照（裁定原文见 `docs/SKILL_ROUTING.md` §3 裁定表）：

- 已执行：C1–C8、C12、C13 共 10 簇合并（目录 108→92）。
- 已裁定保持独立：C11（paper-audit 分工并存）、C15（dispatching-parallel-agents 不合并）。
- 当时延后：C9（web-deploy）、C10（codebase-review）——本轮复核，见 §2。

## 2 候选逐项复核

| 候选 | 来源 | 本轮结论 | 理由 |
|---|---|---|---|
| **C9** web-deploy = `cloudflare-deploy` + `vercel-deploy` | 09-21 延后 | **建议保持独立** | 平台名即触发器（cloudflare / vercel），互不误触发；合并需迁移 309 个资源文件，收益仅目录 −1，成本收益不成比例 |
| **C10** codebase-review = `codebase-map` + `review-codebase` | 09-21 延后 | **建议保持独立** | 跨 A/C 双 Loop，合并后安装项不降（A+C 仍各装一份）；合计 694 行需下沉 references；输出物（结构图 vs 架构健康评审）使用时机不同 |
| **C11** paper-audit = `paper-polish-and-audit` + `paper-review-check` | 09-21 裁定保持 | **维持保持** | 过程审查（draft 期逻辑检查）vs 投稿终审（submission gate，含项目定制规则）；触发边界清晰，合并反而混淆 |
| **C15** = `dispatching-parallel-agents` + `subagent-fanout` | 09-21 裁定保持 | **维持保持** | 通用概览（167L）vs 精确 fanout 实践（13L）；粒度不同，且 fanout 单独服务 C 线 |

本轮新检查的疑似簇（全部建议保持独立，理由一行一条）：

- {`requesting-code-review`, `receiving-code-review`}：请求方 / 接收方两个视角，触发词不冲突。
- {`pdf`, `pdf-ingestion`}：工具操作 vs 上下文装载；"pdf 双份"另有 08-29 裁定（仓库版为准），不在合并范围。
- {`writing-plans`, `executing-plans`, `spec-first`, `sprint-contract`, `subagent-driven-development`}：计划族五层次（规格 / 计划 / 执行 / 契约 / 子代理内核），09-21 已核。
- {`experiment-analysis`, `experiment-autopsy`, `offline-eval-playbook`}：归因框架 / 尸检方法论（受保护，入向引用 12）/ 离线评测专项；阶段不同。
- {`jinrong-docs-sync`, `neat-freak`, `organize-logs`}：本仓文档治理 / 通用知识收尾 / 实验日志专项；各自唯一职责。
- {`skill-doctor`, `skill-map`, `skill-merger`, `skill-hook-trigger`, `skills-best-practices`}：meta 五件分工明确（体检 / 引用图 / 合并 / 触发 / 规范）。
- {`code-cleanup-helper`, `code-simplification`}：找债（扫描 + audit）vs 改债（重构动作），动词不同。
- {`agent-rules`, `agent-prompt-contracts`, `graph-loop-rules`}：规则文件生成 / prompt 契约库 / 本仓红线；均为受保护或高引用件。

## 3 可选轻整理（1 行级，如点头可执行；零科学风险）

1. `SKILL_ROUTING.md` §3 裁定表：把 C9/C10 的"延后"更新为"保持独立（2026-10-13 复核）"——纯状态对齐，不改裁定内容。（注：SKILL_ROUTING 为立法件，修改需用户批。）
2. `subagent-fanout` 与 `dispatching-parallel-agents` 各加一行交叉指引（DPA → fanout 是它的精确并行实践；fanout → 报告是声明不是证据，编排者需验证后再合成）。—— 可选
3. 无其他：注册表已 100% 对齐；deprecated 件已合规标注。

## 4 待用户确认

1. 是否接受"本轮零合并"结论？
2. 是否执行轻整理 #1 / #2？
3. C9 / C10 是否正式定性为"保持独立"（写入 `SKILL_ROUTING.md`）？

## 5 本批做了什么 / 没做什么

- 做了：仓库 `skills/` 93 目录与分发表双向核对；09-21 裁定逐条复核；本轮新疑似簇扫描；评估报告（本文件）。
- 没做：未修改任何 skill；未改 `sync_skills.sh` / `SKILL_ROUTING.md` / `SKILL_REGISTRY.md`；未运行 sync；未删除任何目录。
