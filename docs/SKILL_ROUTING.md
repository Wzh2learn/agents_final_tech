# SKILL_ROUTING.md — skill 路由法（治理线立法, 2026-08-29）

> 状态: 活跃（立法件, 修改需用户批） | 更新: 2026-10-29 | 取代/被取代: 无 | 依据: 侧线设计稿转述（用户卡 08-29）+ 注册表↔分发漂移事故（30 件, 08-29 修复）+ skill 库扩容精简化（09-18 批 #6-S: 49 件新 skill 入库、12 件旧件删除）+ **skill 语义合并（09-21 批 #8-A: 10 簇合并, 目录 108→92; 五线主装按合并后名重列, §3 裁定表逐字保留不回改）+ **第二轮复核（2026-10-14 用户批准: C9/C10 保持独立、零新合并；见 experiments/2026-10-13_skill_merge_round2_assessment.md）**
> 范围: 六线任务的 skill 装载决策; 与根 AGENTS.md 配属注册表互为表里（注册表 = 有什么, 本法 = 何时用）

## 2026-10-29 复核记录

本次核对 §1 列出的技能均在仓库 `skills/` 中有 `SKILL.md`；主装为候选路由，按任务选用，不表示每次全部装载。实际分发以 `scripts/graph/sync_skills.sh` 的 A/C 数组为准，历史表中的数量是当时快照。论文线继续使用写作、文献精读和审稿技能；外部写作资源先核查来源和许可，再决定是否纳入，不因声明“顶会”就视为录用保障。本次未更改路由裁定。

## 1 六线总表（任务线 → 主装 skill）

| 线 | 主装（按需, 单任务 ≤5） | 常备背景（不占配额） |
|---|---|---|
| 论文线 | research-writing-skill / paper-deep-reading / algorithm-description / paper-review-check / paper-polish-and-audit / scientific-toolkit-skill | graph-loop-rules |
| 治理线 | neat-freak / jinrong-docs-sync / code-cleanup-helper / skill-doctor / skill-map / repo-audit / readme-audit | graph-loop-rules |
| 运维线 | systematic-debugging / m1-gap-triage / m2-rag-playbook / graph-loop-rules / experiment-autopsy / shift-notes / experiment-analysis / train-monitor / gpu-env | graph-loop-rules |
| 前端线 | playwright / frontend-quality / verify-before-done | graph-loop-rules |
| 工程线 | testing-practices / git-history-ops / code-simplification / commit-and-pr-hygiene / db-schema-change / systematic-debugging / secret-scan / input-validation / dependency-audit / eval-harness / progress-reading-protocol | graph-loop-rules |
| 交付线 | office-academic-skill / pdf / verify-before-done | graph-loop-rules |
| 调研/决策线 | inquiry-methods / socrates / paper-review-check / research-driven-design / decision-record | graph-loop-rules |

## 2 仲裁规则（冲突时依次适用）

1. **红线永载**: 涉及冻结节点/生产后端/甲方数据/对外发送的任务, `graph-loop-rules` 无条件装载, 不占配额。
2. **领域优先**: 任务领域词命中某线 → 该线主装优先于通用件（如"论文草稿"→ 论文线, 不装通用 review-codebase）。
3. **单任务 ≤5**: 装载清单超过 5 件 = 过装备（认知负载 > 收益, 见 tool-restraint 主张）; 超出者移入"可选"注记不装载。
4. **新旧降级**: 同职能新旧两件并存时, 新版装载、旧版标 DEPRECATED 不删（治理规则 4 先例）; 引用旧版的历史工件不改。
5. **显式优于推断**: 卡片装载清单 > 触发词推断; 推断装载必须在开工注记里写明理由。

## 3 冗余裁决表（点名裁定, 2026-08-29）

| 件 | 裁定 | 理由 |
|---|---|---|
| verification-before-completion | **已废（DEPRECATED 标记）** | 已并入 verify-before-done（对抗式审查 + 完成门两段式, 2026-07-28 合并）; 新任务一律装后者 |
| paper-review-check vs paper-polish-and-audit | **分工并存**: 过程审查用前者, 投稿终审用后者 | review-check = 草稿期逻辑/一致性/审稿风险（每章过一遍）; polish-audit = 定稿期术语锁定/主张核验/编译检查（投稿前一次） |
| pdf 双份（仓库版 + 个人版） | **合一: 仓库版为准** | 仓库 skills/ = source of truth（三层分发架构）; 个人版仅作未同步兜底, 不得反向回灌覆盖 |
| figma × 6 / cloudflare-deploy / vercel-deploy | **标个人通用, 不主动装载** | 本项目无 Figma/部署工作流; 仅用户显式要求时装载; 注册表保留（分发实况对齐）但路由表不列 |
| recsys-toolkit | 个人职业工具, 不入项目路由 | 触发词 /recsys, 与五线无关 |
| vibe-coding × 6（context-manager / planner / principles / prompt-engineer / quality-gate / refinement） | **已删（09-18 批 #6-S, 用户裁定）** | 旧世代自洽管线, 职责已被 spec-first + sprint-contract + executing-plans 覆盖; 互引随删消失 |
| code-review / generate-commit / memory-systems / multi-agent-patterns / tool-design / webapp-testing | **已删（09-18 批 #6-S, 用户裁定）** | 与 C 侧现役件职责重叠; 删前实测前 5 件零入向引用, code-review 仅被 code-pathology 的 tags 引用 |
| subagent-fanout vs dispatching-parallel-agents vs subagent-driven-development | **分工并存**: 通用概览 / 计划内多步执行 / 新件=精确并行 fanout | 三者粒度不同, 暂不合并（skill-merger 可后续评估） |
| owasp-review / sql-review / authz-check / input-validation / secret-scan | **分工并存（新件, 09-18 入库）** | 分别覆盖安全 diff 审查 / SQL 正确性 / 授权越权 / 边界输入 / 密钥扫描, 互不替代 |
| 09-21 批 #8-A 的 10 簇合并 | **10 簇合并已执行（用户 09-21 裁定）** | C1 research-writing-skill(合 paper-writing-zh) / C2 experiment-analysis(合 experiment-observer) / C3 commit-and-pr-hygiene(3) / C4 code-simplification(3) / C5 git-history-ops(3) / C6 db-schema-change(2) / C7 frontend-quality(3) / C8 testing-practices(4) / C12 progress-reading-protocol(合 broken-window-check) / C13 eval-harness(合 evaluator-calibration); 目录 108→92, A 93→77, C 21→21 |
| 09-21 批 #8-A 的四个「保持现状」 | **不合并（用户 09-21 裁定）** | C9 web-deploy 保持独立（2026-10-14 复核） / C10 codebase-review 保持独立（2026-10-14 复核） / C11 paper-audit 保持分工并存（§3 原裁定有效） / C15 dispatching-parallel-agents 保持不合并（§3 原裁定有效） |
| verification-before-completion 摘除 | **已执行（09-21 批 #9-B, 三步同一 commit）** | C14+A19 落地: (i) `docs_lint [5]` 跳过用途列含 DEPRECATED 的注册表行 + 输出一条 INFO 行; (ii) 从 `A_SKILLS` 摘除该件（A 77→76, 总数 98→97）; (iii) prune 安装区残留（实测仅 `~/.codex/skills` 一端有副本）。注册表行按治理规则 4 保留 |

## 4 钩链矩阵（机械强制层 × 自动装载）

| 钩/环 | 自动关联 | 说明 |
|---|---|---|
| pre-commit index-guard | jinrong-docs-sync（事后） | 新文档未登记被拦 → 收口时装载补登记 |
| pre-commit large-file-guard | 无 skill | 纯机械 |
| Loop B 验证 | 无（纯 bash） | 不装 AI |
| Loop C 审计派单 | differential-review / paper-review-check（论文件, 08-29 扩围） | 审计对象决定 |
| 收口清单漂移扫描 | neat-freak（命中多时装载清场） | governance_drift_scan 命中 ≥10 触发 |
| 实验窗开/收 | sprint-contract + verify-before-done | 窗口卡标配两件 |

## 5 装载纪律（卡片义务）

1. 任务卡必须含"**skill 装载清单**"行: 列出本任务实际装载件（≤5 + 红线常备）, 空 = 声明"无需装载"。
2. 推断装载需一句话理由; 显式装载照录卡文。
3. 收口汇报附装载清单执行情况（装了没用 / 没用装 = 浪费信号, 记台账供路由表迭代）。
4. 路由表每季度（或漂移事故后）复审一次, 修订需用户批（立法件纪律）。
| formal experiment preflight | verify-before-done + audit-cycle + self-eval-bias | `FORMAL_EXPERIMENT_PREFLIGHT_V1.md`; END_TO_END_PREFLIGHT_PASS 前禁止 scientific output |
| authority/handoff closure | neat-freak + jinrong-docs-sync | `GRAPH_LOOP_AUTHORITY_MAP_V1.md`; A/C/D handoff 必须带 authority paths + hashes + PASS level |
