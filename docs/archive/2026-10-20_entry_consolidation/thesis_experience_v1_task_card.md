# TH3-RQ2 最小科学验证与 WP-0/WP-1 任务卡：设计稿

> 2026-10-12｜`DESIGN_COMPLETE / QUALIFICATION_PENDING / EXPERIMENT_NOT_RUN`
> 本轮只完成研究资格核验设计；没有核验实际服务器数据、采集经验、实现代码或执行实验。`G-RQ=PENDING / G-M=PENDING / METHOD_NOVELTY=NOT_IDENTIFIED`；不把本设计当作 WP-0 资格验收完成或任何运行许可。
> 科学裁决以 [治理基线 v1](THESIS_RESEARCH_GOVERNANCE_BASELINE_v1.md) 为准；范围以 [架构 v3](THESIS_RESEARCH_ARCHITECTURE_v3.md) 为准；四臂、首验数值和资源门沿用 [执行蓝图 §2](THESIS_EXECUTION_BLUEPRINT_v1.md#2-首个最小验证实验给定经验的跨任务效应)。本卡细化既定 WP-0/WP-1，不另建路线、工作包编号或平行实验计划。

**Goal：** 判断指定任务中是否有值得继续研究的经验复用机会，而不是证明 Memory/SFT 有效或提出完整方法。

**Architecture：** 一个冻结工具型 Agent、一个固定历史经验池、来自新来源的受限任务、既定四臂；先裁决资格和最小验证必要性，未来获准后才实现薄执行器与申请 WP-2。

**Tech stack：** 后续拟用独立研究 Python 入口及真实计算工具，不接生产服务/PG。模型 revision、数据许可、确切来源与执行环境尚未核验，不从现有部署或旧许可推定可用。

## 1. RQ2 的最小可验证问题

**在固定模型、工具和调用预算下，提供来自其他来源的相关真实执行经验，是否提高新来源同类表格计算任务的答案正确率，并伴随相符的实际执行行为？**

这是“给定经验包的跨任务效应”。第一步不回答反馈构造算法、记忆更新算法、参数学习、持续适应或一般知识分工。这里的复用允许发生在上下文中；普通 few-shot 也是可能解释，不能通过重新命名排除它。

待检验假设仅为：指定相关经验池可能有净收益。反例包括无收益、产生回归、只有静态规则收益、只有不相关示例干扰造成的相对优势。Paper E 只提醒目标与测量对象必须一致，不认证新任务答案、反馈资格或效用。

**当前投入判断：值得完成一次受限的只读资格核验设计与材料核验；尚无依据投入候选新算法、Memory 系统或 SFT。** 能否申请最小运行，取决于 WP-0 真实材料与两门裁决。

## 2. 什么证据支持“经验复用值得继续研究”

必须同时有以下证据，而不是只看总分上涨：

1. **有效对象：** 任务目标、字段、时期、单位和数值关系可独立复核；工具消费 Agent 实际选择的参数，回答消费真实结果。经验反馈来自获准、可复核的历史后果，不是反思自评分；修正轨迹确实执行过。
2. **未来任务增量：** E 相对 B 与 C 均有答案净收益；列出纠正、回归、拒答和 UNKNOWN，不能只报挑出的成功案例。
3. **执行相符：** 收益伴随字段、时期或量纲等相关行动的合理改变。行为改变不等于结果改善；二者一致也不单独证明行动的因果贡献。
4. **替代解释可审查：** 来源/近重复隔离，测试答案不进入经验，控制相关/不相关经验的数量、格式与长度，保持任务证据及调用上限一致，完整记验证与推理成本。等 token 不等于等语义信息。
5. **范围与精度诚实：** 收益不能集中在一个来源；报告来源级差异和不确定性。小 pilot 只决定是否值得进一步验证，不证明总体稳定收益。

独立测试单位是 **8 个 origin**，不是 16 题、32 次重复或 128 episodes。两次重复不增加独立来源。结论还条件于一个固定历史经验池，不能外推为跨经验池、反馈来源或任务家族的稳定效应；公开材料也不能保证模型预训练从未见过。

## 3. 最小任务、Agent、经验与 baseline

### 3.1 任务与目标

沿用蓝图任务：**从同一表格的两期数据计算增减额，并按要求统一单位**。不加入增长率、复杂财务推理、新领域或长程任务。

WP-0 必须把每题的指标、两期、目标单位及“有符号变化/增减额”的读取规则写清，参考目标从源材料独立复核；不能凭模型输出倒定答案。模型需要选择字段、时期、单位关系和计算参数，工具不得用 gold 自动替它纠正。

来源必须在获准范围内、原文可复核、origin 谱系可分组。本轮没有选定或核验确切数据 revision、文件与题目 IDs；这些是未核验依赖，不是假定已具备的样本。旧 E/FinQA/PR-03/TAT-DQA 材料不通过重新切分成为新确认面板，旧闭线与许可不解除。

### 3.2 Agent 与经验

- 一个冻结模型与固定工具接口；第一次请求产生实际工具操作/参数，真实执行；第二次消费结果并回答。每 episode 最多两次模型调用，无第三轮自动 repair。
- 这是受限工具型 Agent，不声称通用规划或长程能力。每题重置状态，测试反馈不回写，不训练、不自动更新记忆。
- E/C 均展示 1–2 条历史经验，保留：历史问题、实际字段/时期/单位与工具参数、实际结果、独立反馈及确实执行的修正。历史任务答案可按获准反馈权限使用；未来测试答案不能进入。
- 相关性按开发阶段锁定的任务结构规则分配，不看测试输出/gold 选经验。若所谓修正从未执行，则不能把它补写成真实经验；本轮不采集或编造轨迹。

### 3.3 沿用四臂及其识别边界

| 臂 | 固定内容 | 能回答什么 |
|---|---|---|
| **B：无经验** | 基础提示、任务原文与工具 | 原始能力与所选任务的增量空间。 |
| **E：相关原始经验** | 其他 origin 的相关真实经验；不先归纳新规则 | 该经验包相对 B 的效应，包含示例、执行和反馈的共同影响。 |
| **C：不相关经验** | 正确、真实、同格式；数量一致，E/C token 差异不超过 5% | E−C 检查所选相关经验的优势；C−B 检查不相关示例是否帮助或干扰。 |
| **S：静态规则** | 开发阶段锁定的单位/时期检查步骤，不含测试答案 | 检查是否已有低成本简单解释；不是全部静态规则的上界。 |

S 只覆盖一般的字段/时期核对、单位统一与目标计算检查，不能针对 pilot 逐题加规则。四臂获得相同且完整的任务证据；不能因经验占空间而逐臂删表格字段。

**四臂没有分离同一相关轨迹中的反馈、修正与示例内容，因此不能直接检验 v3 的“执行支持/适用条件带来额外学习价值”完整假设。** 不在本轮加臂补齐；只有复用机会和必要性成立后，才按既有 WP-3 判断是否值得进行机制比较。E−S 也不证明 Memory 必需或成本更优。

### 3.4 规模与预算：原蓝图摘录，未授权运行

经验池 8 episodes/至少 4 origins；开发 4 题/至少 2 origins；pilot 16 题/8 origins，每 origin 2 题。三组按报告、来源谱系和近重复整体隔离。数量是资格建议，不代表来源已经存在或功效充分。

沿用 4 臂 × 16 题 × 2 重复，128 episodes、最多 256 次评估请求；采集/开发最多 40 次，transport 重试最多 4 次，总计最多 **300 次 actor 请求尝试，judge 0 次**。输入 4096、单次输出 512、经验块 600 tokens 的建议上限和超限处理完全继承蓝图。独立审查若调用项目模型须另列预算。WP-0/1 本身不使用这些模型预算，采集/运行属于后续获准 WP-2。

## 4. STOP、未定与进入方法研究的条件

以下沿用蓝图资源门，不新增显著性标准。方法研究没有自动 GO。

| 结果/材料状态 | 裁决与允许动作 |
|---|---|
| 无确切许可/独立来源/参考目标；泄漏或执行对象错配 | 不进入 pilot；分别报来源不足、资格未定或无效。不能据此宣布经验学习无效。 |
| B 两次均无错误、没有增量空间 | `STOP_THIS_PANEL / CEILING`，不人为加难追效果。 |
| 行为变化但答案没有净改善，来源集中或不确定性过大 | `UNDETERMINED`，不进入复杂方法/训练；不得把未显著写成无效或等价。 |
| 有效资格与实际能力对照成立，但 E 两次无收益 | 可暂停当前呈现形式；科学判断仍可未定。两次 E−B 均不高于 −12.5 个百分点时沿用明确负向暂停建议；零星回归不等于整体有害。 |
| E−B 与 E−C 的平均增量均至少 12.5 个百分点，分别有至少 3 个净正向 origins，单 origin 不超过相应全部纠正案例的 50%，两次重复均不反向，执行解释一致 | 只可记 `CONTINUE_EXPLORATORY` 并申请既有基线/必要性比较。保守 UNKNOWN 解释须仍过门；区间可跨零，不能作为确认性结论。 |
| E 有收益但不胜 S；或简单规则/合适已有方法已经足够 | 复用机会可能成立；新方法必要性未成立。S 解决全部任务则停止本面板新算法，不否认已观察到的复用效应。 |
| 有有效复用机会、强简单与适配已有方法未解释的残差，并有具体最近邻差异和否证条件 | 才可提交 G-M 对候选方法研究范围的裁决，并申请相应实现/运行；不等于优势或创新已成立。 |

E−C 不能单独支持有用结论，尤其当 C−B 为负时。四臂没有完成 ACE/MemRL 等合适已有方法比较；不能把未运行的基线当作已失败。需要时先在既定 WP-3 范围申请基线诊断，不直接写新算法。

最多一次有证据的任务/呈现修正及新确认材料，遵守蓝图全局上限和单独许可；不能每个模型/提示各重试一次。来源不足、无效或精度不足不成为整个 RQ2 的永久否定，也不自动获得补样预算。

## 5. 与已有工作的关系及唯一潜在空间

[ACE](https://arxiv.org/abs/2510.04618) 已用生成、反思与整理更新经验手册，并利用自然执行反馈；[MemRL](https://arxiv.org/abs/2601.03192) 已研究环境反馈驱动的记忆效用与检索。因此经验包有用、反思有用或检索经验有用，都不能直接认领为新方法。

[TRUSTMEM](https://arxiv.org/abs/2606.25161) 验证记忆转换的覆盖、保留与忠实性；[PMD](https://arxiv.org/abs/2607.01480) 将跨任务程序经验形成记忆并蒸馏到参数。“可靠反馈再学习”或“Memory→SFT”也不是已认证空白。这里是机制覆盖核对，不认证这些工作的结论普遍成立。

**只保留一项 `H / NOT_IDENTIFIED`：在指定任务中，过去执行有事实支持的反馈，与未来任务效用之间，是否存在最近邻尚未解释的具体分离或适用边界？** 若存在，保留/使用适用条件是否有超出静态规则、朴素经验和合适已有方法的增量，才值得进一步判断。

这最多是潜在的经验发现或方法差异入口，不是当前创新。四臂不能将差异归因于反馈资格本身；需要什么机制比较由后续必要性裁决决定，本卡不设计它。若已有方法已解释全部结果，就没有必须开发新算法的理由。

## 6. GB10 Loop A 工作包：规划定义，不执行

### WP-0：只读研究问题、来源与最小验证必要性核验

**责任：** 后续指定的一名 Loop A 执行者负责材料核验和本卡资格附录；导师/owner 裁决 G-RQ/G-M。执行者不是唯一协作者，不得覆盖其他人的改动或回改旧证据。

**按需读取：** 仓库 `AGENTS.md`、`memory/CORE.md`、`STATE.md` 和 `THREADS.md` 的近期相关条目；治理基线 §2–§4；本卡；蓝图 §2 与 WP-0。只为具体来源读对应许可/源文件，为具体方法差异读近邻原论文；不全量加载历史实验。

**允许写入：** 仅本卡的资格核验附录及现有规定的简短状态/派活回执；原始来源内容不提交 Git。数据只读路径须由具体任务授权绑定，不能搜索整个服务器或读取凭证。

- [ ] 列出确切来源/revision/许可/文件范围、经验/开发/pilot IDs 和 origin/近重复分组；无可访问材料则报依赖未核验，不自动下载或复制私有数据。
- [ ] 核验参考目标与真实执行的设计链；区分读代码/契约可支持的对象一致性与尚未发生的运行行为，不伪造轨迹或软件 PASS。
- [ ] 核验经验可合法获得、反馈权限与结构相关性，记录静态规则/普通 few-shot 等替代解释；新经验的实际采集留待获准 WP-2。
- [ ] 精读最相关已有机制，记录本任务仍未知的问题、为何值得做最小验证，以及何种结果使新算法无必要；不宣称文献空白。
- [ ] 在本卡附录记录 G-RQ 和 G-M 对最小验证/必要实现的裁决建议、证据位置及未核验依赖，交导师/owner 决定。

**交付与停止：** 一份可追溯的资格附录，不另建 registry。没有完整材料或两门仍未定，就停在 WP-0；不创建 runner、不模型采样、不连生产服务/数据库、不部署 GB10。任何远端读取先遵守对应具体访问范围；本轮没有 SSH 或远端核验。

### WP-1：有条件的薄执行器与软件资格

**前置：** WP-0 的 `G-RQ=PASS`、G-M 明确允许最小验证及必要实现，且已有独立 checkout、可写路径与软件检查许可。**本轮未满足也未执行。**

**责任与拟建范围：** 一名后续 Loop A 执行者负责 `research/thesis_experience_v1/task_adapter.py`、`run_probe.py`、`analyze.py` 及必要的聚焦软件验证；不改其他协作者文件。一个 runner 共用四臂，不建设 Memory 管理器、SFT 管线或服务。

- [ ] 适配器隔离 actor 可见输入与只供评分的参考目标；核验字段/时期/单位及等价计算的消费路径。
- [ ] runner 固定臂/经验/重复分配、状态重置和计数，实际调用工具并让后续回答消费其结果；禁止预填 gold、静默补样、按臂截断或额外 repair。
- [ ] 分析器按 origin 汇总四项配对差值、执行行为、纠正/回归/UNKNOWN 与成本；没有真实结果时不生成效果结论。
- [ ] 仅用获准的合成 fixture 检查参数消费、gold 隔离、状态重置、预算及缺失/超限停止；fixture 不是研究结果，不调用模型/生产端点或导入有副作用的生产反思/PG 组件。

**验收与停止：** 能复现合同指定的软件行为和记账，方可报限定范围 `SOFTWARE_PASS`；失败就修软件或停止，不借真实模型“试一下”。本包不采集历史经验、不运行四臂、不训练。实际模型 pilot 仍是 **WP-2**，须另有数据/模型/预算/窗口许可。

## 7. 当前资格记录

| 项目 | 本轮状态 |
|---|---|
| 最小问题、证据需求、四臂解释、工作包边界 | 设计已记录；沿用原蓝图，不是实验结论 |
| 来源/文件/IDs、许可适配、谱系、真实经验轨迹、模型 revision、GB10执行环境与窗口 | 未核验；未绑定运行合同 |
| G-RQ / G-M / 新方法 | PENDING / PENDING / NOT_IDENTIFIED |
| 实施与运行 | WP-1 未实施；WP-2 未运行；代码、稿件与旧闭线不变 |

本卡完成的是 **WP-0 设计子任务**，下一步仍为本包只读材料资格核验。不得把文档完整、文献相关、历史工件校验或本轮用户的设计授权，改写成 `TASK_QUALIFIED`、方法 GO 或运行窗口。

## 8. WP-0 read-only experience-pool qualification addendum (2026-10-17)

> Scope: follow the existing architecture and this card; no new panel, model call, runner, training, or budget use.
> Status: `WP0_READONLY_AUDIT_RECORDED / HISTORY_POOL_NOT_ESTABLISHED / EXPERIMENT_NOT_AUTHORIZED`.

### Evidence boundary

- Source/material qualification is inherited from `WP0_TATQA_QUALIFICATION_APPENDIX_v1.md`: TAT-QA licence and raw hashes are recorded, origin grouping is instantiated, and the item/checker contracts exist.
- The stopped WP-2 artifacts were read only to test whether they contain usable history episodes. No stopped panel was reopened.
- No external download, service call, model call, judge call, training, or production access was performed.

### Findings

| object | status | evidence |
|---|---|---|
| TAT-QA source / revision / licence | `QUALIFIED_CONDITIONAL` | `WP0_TATQA_QUALIFICATION_APPENDIX_v1.md` §2-§4; raw fetch and licence receipts recorded there |
| origin and near-duplicate grouping | `DESIGN_AND_CANDIDATE_POOL_ONLY` | 182 origins / 176 with usable rows; WP-2 item receipt reports 352 draft items from 176 origins, `DRAFT_NOT_FROZEN` |
| reference target and tool-consumption chain | `CONTRACTED_NOT_EXECUTED_FOR_NEW_HISTORY` | `WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1.md`; WP-1 software PASS is contract-scoped only |
| historical experience pool | `NOT_ESTABLISHED` | `S4B_STOP_RECEIPT.json` reports `s4_completed_episodes=0`; `S4_HISTORY_FAILURE_FINAL_RECEIPT.json` and `S4_HISTORY_FAILURE_RERUN_RECEIPT.json` report `completed_episodes=0`; no canonical episode objects with executed feedback/corrections were found |
| feedback rights | `RULE_AVAILABLE / POOL_EMPTY` | `WP0_TATQA_FEEDBACK_RIGHT_CONTRACT_v1.md` defines allow-list and hard-forbidden fields, but no qualifying episode payload is available to which it can be applied |
| actor revision | `ARTIFACT_VERIFIED / MODEL_GO_NOT_A_NEW_PHASE` | `ACTOR_ARTIFACT_VERIFICATION_RECEIPT.json` verifies the pinned Qwen3-8B artifact; this is not a new MODEL_GO or actor freeze for the next phase |
| provenance completeness | `PENDING` | S4 stop receipt records a raw-response overwrite incident; the lost response is disclosed and not reconstructed |

### Interpretation

The existing S4/S4B attempts are preserved engineering traces, not a historical experience pool. They cannot be promoted into E/C context because the panel completed zero episodes, the required correction/feedback objects are absent, and one raw attempt was overwritten. The next question therefore remains a **design question**, not a result:

> After evidence-qualification filtering, does real historical experience improve future independent-task performance relative to general rules, generic extra context, and unfiltered experience?

The current record does not answer that question. It also does not support `METHOD_NOVELTY`, `G-M=PASS`, or any experience-learning effectiveness claim.

### Gate recommendation

- `G-RQ`: keep the existing recommendation `QUALIFIED_CONDITIONAL` for the bounded task question; owner/advisor still must approve the exact experience-pool source and future collection scope.
- `G-M`: `HOLD / NOT_IDENTIFIED`.
- `WP-2`/pilot: `NOT_AUTHORIZED`; no continuation of the stopped S4 panel.
- First allowed future step: a separately authorized history-collection design with frozen feedback rights, actor revision, source/origin IDs, and budget/window. Until then, stop at WP-0.
