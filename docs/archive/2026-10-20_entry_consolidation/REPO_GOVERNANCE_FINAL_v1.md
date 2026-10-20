# Repo / Harness 研究治理收尾 v1

> 2026-10-12｜`LOCAL_RESEARCH_HANDOFF_CLOSED / SCIENCE_AND_RUNTIME_GATES_PENDING`
> “FINAL”仅指本轮研究交接入口收敛，不代表全库无债务、跨主机同步、科学资格、投稿或清场完成。本轮只新增三份用户要求的治理文档并对齐必要导航/状态；不实验、不改稿、不改代码、不部署、不提交/推送、不删除/移动资产。

## 1. 唯一现役答案与职责

| 要回答什么 | 唯一维护位置 |
|---|---|
| Paper E 当前能否投、如何收尾 | [投稿门禁](PAPER_E_SUBMISSION_READINESS_GATE_v1.md)；claim 的科学判断来自 [作者级裁决](SANER_SCIENTIFIC_ADJUDICATION_v1.md)。当前 BLOCKED，纠偏未落实。 |
| 硕士研究从哪里接手、资产怎样继承 | [执行入口](MASTER_RESEARCH_EXECUTION_ENTRY_v1.md)；只路由，不增加路线。 |
| 科学推进约束与创新状态 | [治理基线](THESIS_RESEARCH_GOVERNANCE_BASELINE_v1.md)；G-RQ/G-M 均 PENDING，具体方法未识别。 |
| RQ/范围、包序/参数、当前最小问题 | [架构 v3](THESIS_RESEARCH_ARCHITECTURE_v3.md) / [蓝图 v1](THESIS_EXECUTION_BLUEPRINT_v1.md) / [WP-0 task card](thesis_experience_v1_task_card.md)；不在三份新入口复制一套排期或改门槛。 |
| 当前状态、未决项、决策、导航 | [STATE](../../memory/STATE.md) / [THREADS](../../memory/THREADS.md) / [DECISIONS](../../memory/DECISIONS.md) / [INDEX](../INDEX.md)。开放缺口只在 THREADS 维护；本文件记录本次边界与快照。 |

canonical manuscript、matrix、scope lock 仍是现有投稿工件，但其中尚未落实裁决的解释不能覆盖科学裁决。旧
[`PROJECT_CLOSEOUT_AND_HANDOFF_v1.md`](../archive/2026-10-19_PROJECT_CLOSEOUT_AND_HANDOFF_v1.md)
与 `side_handoff.md` 的机械完成、human-only blockers、matched-FPR 简写和 PR
恢复建议已加取代提示；历史正文保留，不再签发当前许可。

## 2. 保留资产与冻结路线

| 资产/路线 | 本轮治理处置 |
|---|---|
| Paper E 原始数据、协议、正式结果、post-hoc 身份、autopsy、图/引用/哈希链与投稿包 | 全部保留。后续 WP-E 只纠正当前表述和必要派生件；不改历史证据或用新结果补旧 claim。 |
| v1/v2、owner memo、独立战略审查、v3/蓝图治理前历史快照 | 保留决策来源；旧建议不控制现役排期。历史快照原始字节不动。 |
| TH3-RQ1/2/3 与 WP-0 设计 | 冻结为当前受限规划；本轮不新增模型/领域/候选机制/治理系统。设计完成，任务资格与执行仍未通过。 |
| 原 EDR、Stage D/R、旧来源筛选/adapter、模型权重与软件验收记录 | 作为历史、机制或工程资产保留；不自动搬入新任务，不把旧 PASS 当新 MODEL_GO/训练许可。 |
| Route B、PR-03、旧 causal MVP、FinQA 失配载体、TAT-DQA；冻结 PR-01/04/07 | 本主线不调参、续跑、换名恢复或作新训练来源；历史状态/证据保留。旧交接中的 PR 恢复建议不再控制当前路线。 |
| 生产 FastAPI/RAG/PG、业务 Agent 与外部模型/数据 | 维持既有工程边界；不是 thesis 端到端能力证据。此次无服务/端点核验或机器安装操作。 |

不做物理瘦身来证明治理完成。不删除代码/旧报告、不移动 worktree、不安装/同步 skill、不新建 daemon、registry、审批器或单独 Memory/SFT harness。未来若确有实现必要，沿用既定一个 runner、四臂和隔离研究目录。

## 3. Loop D 派活、Loop A 执行与证据级别

Loop D 下一步只应按 [硕士执行入口 §4](MASTER_RESEARCH_EXECUTION_ENTRY_v1.md#4-loop-ad-从哪里开始) 准备 **WP-0 只读资格核验**；Paper E 的未来改稿任务另按投稿门禁，经明确范围授权后派发。两者可独立推进，不相互借用许可。

沿用 [Loop A constraints](../../scripts/graph/loop_a_exec_constraints.md) 与 [Loop C audit prompt](../../scripts/graph/loop_c_audit_prompt.md)。派活要指明当前包、确切路径、责任、允许动作、停止条件、授权范围与证据身份；不把全文历史塞进 prompt。执行者不是唯一协作者，不覆盖其他人的脏件。

现有 launcher 的 bypass 配置仅作静态记录，未运行或修改；它不实现本研究的授权裁决。能启动进程不等于两门通过或运行获准，不能把文档门禁描述成已经部署的机器强制门禁。

必须区分：本地文档检查、只读材料资格、软件检查、探索性效果、确认性结论、作者签署及外部提交。任何低级别 PASS 均不能替代上一级。B 默认可能访问真实服务，本轮不启动；内部独立文本复核不等于已完成 GB10/投稿包的独立 Loop C 运行验收。

技能按当前任务选择，不超过五项加红线背景。仓库 `skills/` 是源，实际安装与分发另需许可；旧 profile/skill 路由不自动授予模型调用。skill metadata/引用的本地静态检查只反映目录卫生，不能认证机器安装或 harness 运行。

## 4. 本轮事实面与未完成边界

| 事实面 | 收尾状态 | 已核验范围与限制 |
|---|---|---|
| 代码/冻结证据 | `verified-current`，仅指本轮未改 | 本地 HEAD 与脏件范围、受保护文件哈希；未执行代码/测试，不认证运行行为。 |
| 运行态/远端/生产 | `out-of-scope` | 无 SSH、模型/judge/canary/API/PG、GB10测试或部署；旧三端对齐/PASS不是本轮实测。 |
| 文档 | `changed-and-verified` | 三份入口及必要导航/取代关系；本地 UTF-8、链接、差异和静态一致性检查。 |
| Agent 规则/skills | 规则只读；静态检查完成，目录债务保留 | 不改 AGENTS/SKILL_ROUTING/安装区/hooks；检查快照见下，不将旧测试数当现状或警告为零。 |
| 项目记忆 | `changed-and-verified` | 仅维护仓库允许的 STATE/THREADS/DECISIONS 短指针；不修改宿主生成记忆或个人配置。 |
| 工作区/Git | `pending` | 开始时 main@`bb9392518791f0c9fcced3eb81002814e1d1941f` 已有本轮之前的文档脏件与未跟踪研究文件；不是干净 checkout。未 commit/push，也未验证 origin/GB10 当前等价。 |

只读 worktree 清点另见现有 Git 元数据：主 checkout、临时 detached 验证 checkout、同级 test checkout 均保留；未检查后两者的未合并内容或所有权，不作为删除候选。无自动清场清单或删除动作。本轮没有需要用户确认的物理清理请求。

**技能静态体检快照（本地，唯一 root=`skills/`）：** doctor 为 0 errors、139 warnings、0 fixes；其中 73 项 completion-evidence 提示、66 项 frontmatter 字段顺序提示；退出码为 1（脚本对 findings 非空的审阅状态），不是全绿。map 成功退出 0，为 114 skills、51 edges、1 个同名簇、27 项 `unresolved-like-reference`。同名簇是两份 `pdf`；27 项是启发式候选，含 15 个 Cloudflare URL/路由示例、3 个占位/金额示例、9 个外部可选参考里的旧 `/paper-writing` 调用，不等于 27 条已证断链。此快照不认证机器安装或全库零债务；不设为投稿/研究的新增阻断，也不自动修目录。map 首次受 Windows GBK 解码影响，改用进程级 UTF-8 后只读重试成功，未改全局环境。

## 5. 交接完成条件与后续入口

本轮的 done 仅为：三个用户要求的文件存在，结论与四份科学基线一致；旧入口不能绕过投稿/研究门；索引与项目状态可找到新入口；受保护文件不变；本地文档检查及独立范围复核有记录。检查回执写既有 dispatch log，不新建治理数据库。

仍待后续动作的状态保留在 THREADS：Paper E 作者级纠偏与最终版本验收；WP-0 确切材料及两门裁决；必要实现/运行/资源许可；署名/venue/公开/投稿的 owner 决定；Git 集成与远端实况另行核验。**交接可用，不等于实验可开跑、论文可投或整个 repo 已清理。**
