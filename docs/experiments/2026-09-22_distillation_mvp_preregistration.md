# Evaluate–Distill–Evolve 小论文实验预注册合同 v1

> 状态：`DRAFT_NOT_FROZEN`（待用户/导师确认数值门限后才能执行） | 更新：2026-09-23
> Claim：当前三阶段叙事 RQ2 / RQ3 / RQ4，兼为大论文 TH-I3 提供证据；**不属于评估子稿 SP-RQ2**
> 边界：本文件只规定待冻结的实验问题、比较、统计口径与停止条件；不启动模型、训练、端点、数据库或生产服务。

本合同不是第二份执行计划。执行顺序、授权门和 GB10 命令仍以 `docs/handoff/2026-09-22-paper-research-next-phase.md` 为唯一权威；数据质量/角色以 `paper/dataset_protocol_v1.md` 为准，方法记号以 `paper/method_theory_materials_v1.md` 为准。

## 1. 一页决策

- 主学生只用 Qwen3-8B；Qwen3-4B 只做训练链 smoke，不做参数量消融。
- 主对比是 A2 checkpoint-filtered SFT 对 A1 unfiltered SFT；A0 是同任务 zero-shot，A3 仅在双向 DPO 数据门通过后开启。
- A1/A2 同时报告 natural-volume 和 size/token/group-matched 两种口径；后者是识别 checkpoint 过滤增量价值的主口径。
- 主统计单位是 source-table UID，不是 mutant、动作事件、偏好对或 token。
- 当前数据仍为 `DATA_NO_GO`；本合同不能将软件 PASS、`LEARNABILITY_SIGNAL` 或合成 fixture 升级为训练许可/论文结果。
- 数值容差、实际模型 revision、训练预算和数据来源批准仍是 `UNSET`；在它们被人工签字与 hash 绑定前，本文件不是“已冻结预注册”。

## 2. 研究问题与可证伪假设

### RQ2：过程证据过滤是否改善动作策略蒸馏？

- H2a（质量）：在 size/token/group-matched 口径下，A2 的 action macro-F1 相对 A1 不劣于预注册容差 $\delta_q$。
- H2b（安全）：在冻结的有效动作覆盖下，A2 的 harmful-action rate 不高于 A1 加预注册容差 $\delta_h$。
- H2c（选择性）：A2 的 risk–coverage 曲线在预注册风险上限 $\alpha$ 下提供更高覆盖；零覆盖的 always-skip 单列，不把未定义风险记为 0。

### RQ3：独立验证与版本回滚是否能安全累积规则？

- H3a：independent-gate 相对 fixed-dual gate 降低 harmful accept rate，同时 valid-rule retention 不劣于 $\delta_r$。
- H3b：rollback-versioning 在预注册预算 $B$ 内恢复最佳 gate-validation 快照，不把开发侧不变量写成 sealed-test 泛化保证。
- H3c：动态 leave-one-source-out collateral 只支持累计局部界。若要检验全局 telescoping 推论，必须先冻结同一 $\mathcal D_{\mathrm{reg}}$ 并单独扩展合同/测试。

### RQ4：完整闭环是否改善质量—风险—成本权衡？

- H4：在质量和安全非劣门均通过时，学生预筛 + 独立固化门相比教师全量验证降低预注册的实测成本至少 $\rho_c$。
- RQ4 只在 RQ2/RQ3 各自通过且 sealed test 未被开发污染时执行；不把 E、D、R 分别有结果拼成“闭环有效”。

## 3. 前置门与数据冻结

必须按顺序通过，不可跳门：

1. `SOURCE_GO`：公开来源 URL、license 适用范围、commit/release、字节 hash 和零甲方数据证明已核。
2. `LABEL_GO`：Q3 双审/裁决、action/target 正确性、冲突隔离通过。
3. `SPLIT_GO`：先按 group UID 分 proposal/train、gate-validation、sealed test、future replay；同母表 clean/mutant/轨迹/规则事件不跨层。
4. `POWER_GO`：用开发侧方差假设做 UID 聚类 MDE/功效分析；不用 sealed 结果反推参数。
5. `BASELINE_GO`：五类简单基线仍留有可学残差；`SIMPLE_SUFFICIENT`、`NO_CLEAR_SIGNAL`、`PILOT_ONLY` 或 `DATA_NO_GO` 都停止主训练。
6. `MODEL_GO`：用户批准模型、权重许可、GB10 窗口、预算、输出目录和恢复策略。

标签质量 Q0–Q3 与上述四个 role layer 是两个正交维度。P0 新来源分为 FinQA process/checkpoint preflight 与 Valentine NYC schema-action preflight，两者不按行混合；随后才考虑 MultiHiertt 条件外部验证。ConvFinQA 与 FinQA 同 independence cluster；旧 TAT-QA train+dev 池在完成 UID 曝光反查前继续 `HISTORICAL_ONLY`，TAT-DQA 继续冻结。

## 4. 实验臂与唯一职责

### 4.1 零模型可学性门（Phase 1a）

| 臂 | 用途 |
|---|---|
| B0 always-skip | 暴露零覆盖/类别失衡退化 |
| B1 deterministic exact | 检验精确规则是否已足够 |
| B2 lexical/fuzzy | 检验字面相似是否已解释残差 |
| B3 confidence-only | 检验教师自报置信是否已足够 |
| B4 simple classifier | 检验冻结便宜特征是否已足够 |

输出只能是 `SIMPLE_SUFFICIENT` / `LEARNABILITY_SIGNAL` / `NO_CLEAR_SIGNAL` / `PILOT_ONLY`，不输出 `DATA_GO`。

### 4.2 学生训练（Phase 3/4）

| 臂 | 配置 | 边界 |
|---|---|---|
| smoke | Qwen3-4B LoRA/QLoRA，极少步 | 只验训练/保存/恢复链，不进表 1 |
| A0 | Qwen3-8B 同任务 zero-shot | 训练前基线；不用旧 16 题 QA 替代 |
| A1 | Qwen3-8B unfiltered SFT | 只纳入来源/标签合法的未过滤教师动作 |
| A2 | 同底座/训练配置的 checkpoint-filtered SFT | 主实验臂 |
| A3 | A2 + DPO | 只有双向、独立、足量的偏好对通过独立门才运行 |

经典 KD KL 项只在教师 logits/概率真实存在并绑定来源时启用；当前主实验是两头 action/target SFT，不伪造软标签。

### 4.3 规则演化（Phase 2/5）

七臂固定为 no-gate、gain-only、collateral-only、confidence-only、fixed-dual、independent-gate-validation、rollback-versioning。所有臂消费同一候选顺序，维护独立规则状态，并在本臂当前状态上重算 source gain、proposal collateral 和 gate delta。任何报告在独立 GB10 验收前必须保持 `paper_result=false`。

## 5. 数据量与训练公平性

1. **natural-volume**：A1/A2 各用真实可用数据量，报告 UID、样本、token、update 和成本；用于实用效果，不作过滤质量的单独因果证据。
2. **size/token/group-matched（主口径）**：只在 proposal/train 内用预注册算法匹配独立 UID、家族分布、有效 token 与 update 预算。不复制样本充数，不看 gate/sealed 结果选子集。
3. A1/A2 同一底座、revision、tokenizer/template、精度/量化、LoRA、optimizer、scheduler、effective batch、停止规则、seed 列表和解码配置。
4. 主臂至少 3 seeds；单 seed 只标 `PILOT_ONLY`。不把同一模型的多次解码当成独立训练 seed。

## 6. 指标与统计口径

### 6.1 RQ2 主指标

- action macro-F1；`map_to / hold / skip` 逐类 precision/recall/F1。
- `map_to` 条件下 target exact accuracy。
- harmful-action rate，必须在 Q3 正确性标签上计算，不用 gate 接受标签代替。
- valid-action coverage 与 risk–coverage 曲线；零覆盖时 risk 记 `undefined`。
- 最坏家族表现及每家族有效 UID 数。

### 6.2 RQ3/RQ4 主指标

- harmful accept rate、valid-rule retention、gate coverage/accuracy、最坏家族。
- validation queries、rollbacks、主动规则数、实测端到端延迟、生成/验证 token、峰值显存。
- 仓内 `cost_proxy` 只作软件对账，不得写成真实延迟或 GPU 成本。

### 6.3 推断

- 点估计与 95% CI 按 source-table UID 成组；同表 mutant/事件不当 iid。
- A1/A2 使用同 seed 配对；主报告先计算每 seed 的 UID 聚类差值，再汇总 seed 间变异。层级 bootstrap 只作敏感性分析。
- RQ2 的共同主门和 RQ3 的共同主门各自使用 Holm 校正；次指标标为 exploratory，不用未校正 p-value 翻转主结论。
- 统计不可用来弥补功效不足；未达预注册有效 UID 下限时只报告 pilot/不确定区间。

## 7. 待人工确认的冻结收据

执行者必须生成一份 Git 外 JSON 收据，并在仓内只记字段齐全性、hash 与批准人，不提交私有内容。以下任一值为 `UNSET`即禁止正式实验：

```json
{
  "status": "FROZEN_BY_HUMAN",
  "approved_by": "UNSET",
  "approved_at": "UNSET",
  "source_manifest_sha256": "UNSET",
  "historical_exposure_manifest_sha256": "UNSET",
  "role_split_manifest_sha256": "UNSET",
  "q3_adjudication_receipt_sha256": "UNSET",
  "model_id_revision_hash": "UNSET",
  "tokenizer_template_hash": "UNSET",
  "training_config_hash": "UNSET",
  "seed_list": "UNSET",
  "delta_quality": "UNSET",
  "delta_harm": "UNSET",
  "delta_retention": "UNSET",
  "minimum_cost_reduction": "UNSET",
  "minimum_uid_by_role_family": "UNSET",
  "multiplicity_policy": "holm_for_confirmatory_families",
  "sealed_test_open_once": true
}
```

`delta_quality=0.02` 只能作讨论起点，尚未批准；不能原样复制后声称已预注册。

## 8. 判定与停止规则

| 情形 | 结论/动作 |
|---|---|
| 任一 source/label/split 门失败 | `DATA_NO_GO`；不训练 |
| 功效不足或只有单 seed | `PILOT_ONLY`；不写论文级蒸馏结论 |
| 简单基线已达冻结质量/风险/覆盖门 | `SIMPLE_SUFFICIENT`；取消 8B 主训练，保留评估稿 |
| 简单基线没有稳定可学残差 | `NO_CLEAR_SIGNAL`；先查标签/功效，不启动 8B 主训练 |
| A2 质量或安全非劣失败 | RQ2 不支持，保留 null/adverse；不改 split/容差救结论 |
| DPO 偏好仍单向或不足 | 删除 A3 正式臂，不扩写偏好学习贡献 |
| Phase 2 源状态不可重建 | `REPLAY_BLOCKED`；不用旧分数拼反事实 |
| independent gate 或 rollback 安全门失败 | RQ3/RQ4 不支持，小论文回退 Stage E 评估保底稿 |
| 发现泄漏、未冻结改参或 sealed 多次揭封 | 本次确认性实验 `INVALID`，不进论文 |

## 9. 论文结果槽位（当前均为空）

- Table 1：B0–B4 与 A0–A3 的 action/target、harm、coverage、最坏家族、不确定性和成本。
- Table 2：七类规则门的 harmful accept、valid retention、gate 指标、查询/回滚与成本。
- Figure 3：学生 risk–coverage 与 quality–cost Pareto。
- Figure 4：共享候选流上的 retained-valid、retained-harmful、rollback 与累计成本。
- Appendix：数据卡、曝光审计、训练配置、家族全表、null/adverse 与排除清单。

在独立验收前，这些槽位只能消费 `paper_result=false` 的水印预览，不能填写正式数字。

## 10. 执行与验收顺序

1. GB10 恢复后先只读核现状，在干净隔离 worktree 里执行。
2. 完成历史 TAT-QA UID 曝光审计、FinQA 过程来源 preflight 与 Valentine NYC 动作来源 preflight，再由用户批准具体来源；ConvFinQA/FinQA 先做同源去重。
3. 按 Phase 1 数据合同双跑、零 `connect` 并取得独立人工验收；再运行 Phase 1a 五基线。
4. Phase 1a 留有可学残差后，依次执行 Phase 2 正式 replay、4B smoke、8B A0–A2；A3 仍单独判门。
5. 各阶段均需用户对应授权；详细命令、输出位置和回滚规则只维护在 handoff 计划及 Phase 1a data-gate 报告，本文件不复制。

## 11. 冻结前人工检查表

- [ ] 数据来源、许可、版本、hash 和历史曝光清单已签字。
- [ ] Q3 双审/裁决和四层 UID 零交叉已独立验收。
- [ ] 五基线结论为 `LEARNABILITY_SIGNAL`，不是其他停止状态。
- [ ] 模型/revision/template、训练超参、seed、预算和输出位置已冻结。
- [ ] $\delta_q$、$\delta_h$、$\delta_r$、$\alpha$、$\rho_c$、最低 UID/家族覆盖和 Holm 检验族已确认。
- [ ] 三类实验输出均带证据级别和 `paper_result` 标记，sealed test 只允许揭封一次。
- [ ] 专利公开门已由用户确认；未确认时不投稿、不上传预印本、不公开核心代码。
