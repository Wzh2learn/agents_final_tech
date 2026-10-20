# 执行侧交接状态 v1

> 2026-10-12｜`HANDOFF_READY / WP_E_REVISION_PENDING / WP0_QUALIFICATION_PENDING`
> 战略治理阶段结束；本轮只审查与交接，完成后停止，等待下一阶段任务。本文是执行摘要，不替代既有 gate、科学基线或蓝图，不增设研究路线、方法或审批门。

## 1. 当前唯一执行优先级

| 工作面 | 下一阶段限定任务 | 当前实际状态 |
|---|---|---|
| **Paper E：投稿修订** | 进入既有 **WP-E**，严格按 [投稿 gate](../research/PAPER_E_SUBMISSION_READINESS_GATE_v1.md) 落实作者级裁决；先处理 C2 核心逻辑，随后完成其余必改项与传播检查。 | 纠偏未执行，`SUBMISSION_BLOCKED_SCIENCE`；“进入修订流程”不等于现稿可以注册/投稿。 |
| **硕士大论文：WP-0** | 只核验研究问题、来源/许可、独立目标、经验可得性及最小验证必要性，在现有任务卡写资格附录。 | 设计完成、材料资格未核验；`G-RQ=PENDING / G-M=PENDING / METHOD_NOVELTY=NOT_IDENTIFIED`。 |

两项分别推进；Paper E 不等待 pilot 正向，WP-0 不依赖 Paper E 已证明学习资格。有限资源优先保障 Paper E 修订；大论文不跳过 WP-0。Agent/Memory/SFT/DPO/Adaptation 的未来空间保留，当前不提前实现或训练。

## 2. 下一阶段允许事项

- **Loop D：** 按以上两个既定包组织任务，绑定责任人、读写路径、产物与停止条件；不重新设计路线或批量派发后续包。用户已确认优先级，无须再次询问路线选择。
- **Loop A / WP-E：** 下一阶段任务明确改稿范围后，按 gate 同步 manuscript、claim matrix、scope lock 和必要派生/注册材料；记录裁决落实位置，保留原始数字与证据身份。最终版本再做必要文本、编译、引用和匿名检查。本轮尚未修改这些工件。
- **Loop A / WP-0：** 按 task card 对获准材料做只读核验并记录建议；无访问范围的远端/私有材料报未核验依赖，不自动下载或扩大搜索。产物写回同一卡片，不重建卡片或另开 registry。

以上是后续任务边界，不是在本轮启动执行。已有明确授权持续有效；缺少的具体范围由下一阶段任务补齐，不反复请求已授事项。

## 3. 当前禁止事项

- 提前进入 WP-1 runner 实现、WP-2 模型 pilot、经验采样、Memory 管理器、SFT/DPO/reward-model 训练或 Adaptation 更新；不因文档齐备自动升级两门状态。
- 新实验、模型/judge/canary/生产 API/PG 调用、服务变更、模型加载、自动下载或外发；具体后续动作按对应范围许可处理。
- 改原始数据、评分、阈值、tie、split、样本或历史审计记录；以新结果维持旧 claim，或将 Paper E 迁移为学习有效性证据。
- 重开 Route B、PR-03、旧 causal MVP、FinQA 失配载体、TAT-DQA 或被冻结 PR 路线；恢复强制 EDR、扩展新领域/平台。
- 自动注册摘要、投稿、发布 artifact、提交/推送、删除/归档资产或清理他人脏件。

## 4. Loop A 最短阅读入口

共同先读 [AGENTS](../../AGENTS.md)、[CORE](../../memory/CORE.md)、[STATE](../../memory/STATE.md) 与 [THREADS](../../memory/THREADS.md) 的当前相关条目，再读本状态卡。

| 任务 | 按需继续读取 |
|---|---|
| WP-E | [投稿 gate](../research/PAPER_E_SUBMISSION_READINESS_GATE_v1.md) → [科学裁决](../research/SANER_SCIENTIFIC_ADJUDICATION_v1.md) → [蓝图 WP-E](../research/THESIS_EXECUTION_BLUEPRINT_v1.md) → gate 指向的 canonical 稿/matrix/scope；只为具体 claim 追溯证据。 |
| WP-0 | [硕士执行入口](../research/MASTER_RESEARCH_EXECUTION_ENTRY_v1.md) → [治理基线](../research/THESIS_RESEARCH_GOVERNANCE_BASELINE_v1.md) → [现有 task card](../research/thesis_experience_v1_task_card.md) → 蓝图 WP-0 与确切来源/许可。 |
| 权限/资产边界 | [repo 治理收尾](../research/REPO_GOVERNANCE_FINAL_v1.md)、[Loop A constraints](../../scripts/graph/loop_a_exec_constraints.md)；全局导航见 [INDEX](../INDEX.md)。 |

## 5. 需要导师 / owner 决策的事项

1. **Paper E：** 尚未明确的具体改稿/派生件写入范围、作者最终 claim 签署、venue 与署名、artifact 公开方式、摘要注册及正式提交。方向已确定，不再重审路线；外发不由执行 Agent 自动决定。
2. **WP-0：** 具体材料访问/记录范围；收到资格附录后，对 G-RQ、G-M 的限定范围作裁决，决定是否值得投入必要实现或最小验证。资格核验不能由 Agent 自行升级为方法 GO。
3. **后续阶段：** 资源/数据/模型/预算/运行窗口、候选方法必要性、参数或适应研究及学位范围。当前不提前申请或执行。

## 6. 执行阻碍检查结论

| 检查面 | 结论与处理 |
|---|---|
| 入口缺失 | 四份主入口、科学基线与 task card 均存在；链接本地核验，不代表远端已同步。 |
| 状态/路线冲突 | 当前主入口一致：WP-E 待修、WP-0 待核验，未授权实验/实现。STATE 旧目标段已标为历史，不覆盖当前优先级。 |
| 重复/废弃入口 | 按职责分工，不是平行方案。旧 closeout/side_handoff 已有取代提示；v1/v2、旧 EDR 与冻结路线仅作历史，不删除、不复活。 |
| 旧设计时态 | 蓝图的 task card“拟建”为历史设计用语；实际文件已存在，只有设计完成，不代表资格通过，不要再次创建。 |
| Git / 运行 / 目录债务 | 已有脏件、远端实况及 skill 警告仍按既有记录保留；不阻碍本地只读交接，但不得假设 GB10 已有本轮文档或授权窗口。真正派活前绑定实际执行面版本与所需文件。 |

**结论：未发现阻碍上述两项准备工作的未解决治理冲突。** 科学修订、材料资格和 owner 决策仍是实际待办，不用新一轮战略治理替代执行。本轮到此停止；不派发 WP-E/WP-0，不修改论文/代码，不运行实验。
