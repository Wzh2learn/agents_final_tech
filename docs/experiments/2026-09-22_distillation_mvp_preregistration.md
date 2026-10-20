# Evaluate–Distill–Evolve 小论文实验预注册合同 v1

> 状态：`DRAFT_NOT_FROZEN`（待用户/导师确认数值门限后才能执行） | 更新：2026-09-23
> Claim：当前三阶段叙事 RQ2 / RQ3 / RQ4，兼为大论文 TH-I3 提供证据；**不属于评估子稿 SP-RQ2**
> 边界：本文件只规定待冻结的实验问题、比较、统计口径与停止条件；不启动模型、训练、端点、数据库或生产服务。

本合同不是第二份执行计划。执行顺序、授权门和 GB10 命令仍以 `docs/archive/2026-10-20_entry_consolidation/2026-09-22-paper-research-next-phase.md` 为唯一权威；数据质量/角色以 `paper/dataset_protocol_v1.md` 为准，方法记号以 `paper/method_theory_materials_v1.md` 为准。

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
- H2c（预筛）：A2 在预注册候选风险上限 $\rho_{\max}$ 下提供更高送检覆盖，同时报告有效候选召回、漏失有效规则率和验证成本；所有候选仍经过确定性 gate。零送检的 always-skip 单列，不把未定义风险记为 0。统计显著性水平另记 $\alpha_{\mathrm{sig}}$。

### RQ3：独立验证与版本回滚是否能安全累积规则？

- H3a：independent-gate 相对 fixed-dual gate 降低 UID-any-harm rate 的单侧上界，同时 valid-rule retention 不劣于 $\delta_r$；rule-level harmful-accept rate 仅作描述。
- H3b：rollback-versioning 在预注册预算 $B$ 内恢复最佳 gate-validation 快照，不把开发侧不变量写成 sealed-test 泛化保证。
- H3c：动态 leave-one-source-out collateral 只支持累计局部界。若要检验全局 telescoping 推论，必须先冻结同一 $\mathcal D_{\mathrm{reg}}$ 并单独扩展合同/测试。

### RQ4：完整闭环是否改善质量—风险—成本权衡？

- H4：在质量和安全非劣门均通过时，学生预筛 + 独立固化门相比教师全量验证降低预注册的实测成本至少 $\rho_c$。
- RQ4 只在 RQ2/RQ3 各自通过且 sealed test 未被开发污染时执行；不把 E、D、R 分别有结果拼成“闭环有效”。

## 3. 前置门与数据冻结

必须按顺序通过，不可跳门：

1. `SOURCE_GO`：公开来源 URL、license 适用范围、commit/release、字节 hash 和零甲方数据证明已核。
2. `LABEL_GO`：Q3 双审/裁决、action/target 正确性、冲突隔离通过。
3. `SPLIT_GO`：先按 namespaced lineage UID 与 independence cluster 分 proposal/train、gate-validation、sealed test；同母表 clean/mutant/轨迹/规则事件不跨层。future replay 尚未到来时允许为空，但必须有哈希绑定的获取时间、来源约束、分层规则与“不回流本轮”协议，并标 `LONGITUDINAL_EVIDENCE_UNAVAILABLE`。
4. `POWER_GO`：用开发侧方差假设做 UID 聚类 MDE/功效分析；不用 sealed 结果反推参数。
5. `BASELINE_GO`：五类简单基线仍留有可学残差；`SIMPLE_SUFFICIENT`、`NO_CLEAR_SIGNAL`、`PILOT_ONLY` 或 `DATA_NO_GO` 都停止主训练。
6. `MODEL_GO`：用户批准模型、权重许可、GB10 窗口、预算、输出目录和恢复策略。

标签质量 Q0–Q3 与上述四个 role layer 是两个正交维度。P0 新来源分为 FinQA process/checkpoint preflight 与 Valentine NYC schema-action preflight，两者不按行混合；随后才考虑 MultiHiertt 条件外部验证。ConvFinQA 与 FinQA 同 independence cluster；旧 TAT-QA train+dev 池在完成 UID 曝光反查前继续 `HISTORICAL_ONLY`，TAT-DQA 继续冻结。

### 3.1 RQ2 同样本桥接门

FinQA 只提供 process/program gold，Valentine NYC 只提供 schema correspondence；二者是互补预研来源，**不能相互拼接成 RQ2 主实验**。进入 A1/A2 的每个样本必须来自同一已验收母池，并同时具备：

1. 运行时可得、且在 teacher action 产生前冻结的 checkpoint evidence；
2. 同一 sample/lineage UID 上的 Q3 teacher action 与条件 target；
3. 可用于 sealed 评分的 Q3 outcome/correctness 标签。

A1 与 A2 共享 provenance、licence、Q3 和 proposal-role 资格门 $u_i$；A1 使用全部 $u_i=1$ 样本，A2 仅增加 checkpoint filter $z_i$。若只能取得 FinQA 或 Valentine 的单侧标签，最多分别报告 Stage E/Stage D 外部效度或 pilot，RQ2 保持 `NOT_IDENTIFIED`。

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
- harmful-map rate（错误 `map_to` / 全部可测样本）与 map-to risk（错误 `map_to` / 所有 `map_to` 预测），必须在 Q3 正确性标签上计算，不用 gate 接受标签代替。
- correct-map coverage（正确 `map_to` / 全部可测样本）与候选风险—送检覆盖曲线；另报有效候选召回、漏失有效规则率和验证成本。学生输出不能绕过确定性 gate；零送检时 risk 记 `undefined`。
- 最坏家族表现及每家族有效 UID 数。

### 6.2 RQ3/RQ4 主指标

- rule-level harmful-accept rate（有害接受事件/全部接受事件，描述量）、回滚后的 rule-level harmful-retained rate、UID-any-harm rate（任一有害接受事件）及其单侧 Clopper–Pearson 上界、valid-rule retention、gate coverage/accuracy、最坏家族。分母和“曾接受/最终保留”状态不得混名或共用区间。
- validation queries、rollbacks、主动规则数、实测端到端延迟、生成/验证 token、峰值显存。
- 仓内 `cost_proxy` 只作软件对账，不得写成真实延迟或 GPU 成本。

### 6.3 推断

- 点估计与区间按 namespaced lineage UID 成组；同表 mutant/事件不当 iid。A1/A2 使用同 seed、同 UID 配对，点估计对 seed×UID 单元等权，主区间按“成对重采样 seed，再在 seed 内成对重采样 UID”的两阶段 bootstrap；不得平铺所有行。
- 质量非劣用 A2−A1 的单侧下置信界对 $-\delta_q$；安全非劣用单侧上置信界对 $\delta_h$；retention 非劣用单侧下置信界对 $-\delta_r$。“不显著”不等于非劣。
- RQ2 确认性 Holm family 固定为 H2a 质量非劣、H2b 安全非劣、H2c 风险约束下覆盖；RQ3 family 固定为 UID-any-harm 与 valid-rule retention。逐家族与其他次指标为 exploratory。
- 阈值只在 proposal/train 内部 dev 上按“风险不高于 $\rho_{\max}$ 时覆盖最大”选；并列时先选 action macro-F1 高者，再选更保守阈值。gate/sealed 不参与阈值选择。
- 统计不可用来弥补功效不足；`minimum_uid_by_role_family` 与 MDE 必须在揭封前由人批准并绑定 hash，未达下限时只报告 pilot/不确定区间。

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
  "risk_limit": "UNSET",
  "significance_level": "UNSET",
  "one_sided_interval_method": "paired_two_stage_seed_uid_bootstrap",
  "threshold_selection": "proposal_dev_max_coverage_under_risk_then_macro_f1_then_conservative",
  "minimum_cost_reduction": "UNSET",
  "minimum_uid_by_role_family": "UNSET",
  "mde_by_confirmatory_contrast": "UNSET",
  "rq2_holm_family": ["H2a_quality_noninferiority", "H2b_safety_noninferiority", "H2c_risk_constrained_coverage"],
  "rq3_holm_family": ["H3a_uid_any_harm", "H3a_valid_rule_retention"],
  "sealed_test_open_once": true
}
```

`delta_quality=0.02` 只能作讨论起点，尚未批准；不能原样复制后声称已预注册。

### 7.1 追加注记（2026-09-24，用户裁定 D7/D8/D9/D10/D12；append-only，上文一字未改）

本节为用户裁定后的 append-only 注记。**上文 §7 正文与 JSON 块保持原样作为轨迹**；若本节与上文冲突，**以本节为准**。

**(1) D7：§7 与 `analysis_plan.json` 是两份不同工件。** §7 是**人工冻结收据**（记批准人、批准时间、各类 hash、各 δ 与家族），`analysis_plan.json` 是**包内机器合同角色件**（`research/phase1a_data_contract.py` 的 `analysis_plan` 角色）。二者**不是一份**：实测 §7 的 24 键与合同 18 个必需键在 **10 个键上完全不相交**，且把 §7 的 18 个 `UNSET` 全部填入合成值、键集保持不变后，真实校验器仍报 **14 个 schema 级错误**（`overall = DATA_NO_GO`）。⇒ **不得照 §7 的字段集构造 `analysis_plan.json`。** 证据见 `2026-09-24_phase1a_s7_receipt_contract_gap.md`。

**(2) `analysis_plan.json` 的 18 个必需键**（机械导出于合同 `:909-977`；另有 3 个「出现即失败」的遗留歧义键 `alpha` / `power` / 单数 `noninferiority_margin`，`:910`，**不得出现**）：

`status` · `approved_by` · `approved_at` · `cluster_unit` · `significance_level` · `target_power` · `risk_limit` · `noninferiority_margins`（嵌套，键集恰为 `delta_quality`/`delta_harm`/`delta_retention`）· `primary_metrics`（须含 `action_macro_f1` 与 `harmful_map_rate`）· `threshold_selection` · `seed_uid_aggregation` · `holm_families`（嵌套）· `one_sided_p_value_methods`（恰 5 键）· `holm_adjustment` · `minimum_uid_by_role_family` · `minimum_uid_by_action`（键集恰为 `map_to`/`skip`/`hold`）· `mde_by_confirmatory_contrast`（键集恰为 `REQUIRED_MDE_CONTRASTS`）· `layer_manifest_sha256`

**(3) D8：以下为用户批准的设计起点值，不再是合成 fixture 值。**

| 键 | 批准值 |
|---|---|
| `approved_by` | 用户（Wzh） |
| `approved_at` | 实际写入时的 ISO 8601 时间 |
| `significance_level` | `0.05` |
| `risk_limit` | `0.10` |
| `delta_quality` | `0.02` |
| `delta_harm` | `0.02` |
| `delta_retention` | `0.02` |
| `minimum_cost_reduction` | `0.10` |
| `seed_list` | `[42, 43, 44]` |
| `target_power` | `0.80` |

⇒ 上文「`delta_quality=0.02` 只能作讨论起点，尚未批准」一句**就 `delta_quality` 而言已被 D8 取代**（原文按 append-only 纪律保留作轨迹，不回改）。其余各值同批生效。**注意**：`minimum_uid_by_role_family`、`minimum_uid_by_action` 与 `mde_by_confirmatory_contrast` **不在本批批准范围内**——它们需真实开发侧方差做功效分析（见 `2026-09-24_phase1a_power_mde_sensitivity_grid.md`：同一 δ 下所需独立 UID 数跨一个数量级，主导项是 σ²），在数据补充交付开发侧样本前**不可定值**。

**(4) D9：`H3a` 命名统一为 `H3a_uid_any_harm`。** §7 `:149` 的写法即权威。合同侧 `REQUIRED_HOLM_FAMILIES`（`:99-108`）与 `one_sided_p_value_methods`（`:946-953`）原用 `H3a_cluster_any_harm`，经全仓证据权重核实为**孤立离群值**（仅 4 处 / 2 文件，其中 2 处是夹具回声），而科学层（本件 §2 `:28`、§6.2 `:109`、§6.3 `:117`、§7 `:149`）与已落地的 Phase 2 实现（`phase2_rule_gate_replay.py:392-399` 产出 `uid_any_harm_*` 指标、`paper_result_views.py:76-81` 消费、`test_phase2_rule_gate_replay.py:214-236` 断言）统一用 `uid_any_harm`。因合同强制 `cluster_unit == lineage_uid`，两名**语义相同**，故这是**纯命名对齐**，不改统计量、阈值、家族结构或判定逻辑。`REQUIRED_MDE_CONTRASTS`（`:110-114`）由家族派生，会联动。证据见 `2026-09-24_spec_conflict_weight_of_evidence.md`。

**(5) D10：`threshold_selection` 采「范围 token + 规则字段」双记录，暂不实现完整选阈算法。** 机器合同保留范围 token **`proposal_dev_only`**（`:940`）；完整规则 **`proposal_dev_max_coverage_under_risk_then_macro_f1_then_conservative`**（与 §6.3 `:118` 逐段对应）另作**规则字段/注记**记录。由**独立 Loop C 或独立 agent 做机器审计**，核三件事：范围确为 proposal/dev、不含 gate/sealed、规则文本与预注册一致。**本批不实现完整选阈算法**（实测该规则此前在所有 `.py` 中零实现）。

**(6) D12：`H3a` 欠功效的处置目标。** `H3a_uid_any_harm` 被合同钉为 `exact_mcnemar`（`:950`），d 个不一致对可达到的最小单侧 p 为 `0.5^d`，故 α=0.05 下 **d ≥ 5** 才可能显著；而合同对 `minimum_uid_by_action` 只要求 `>= 2`（`:962-968`），那是健全性下限而非功效下限。处置目标 = **数据补充 250–500 个有效 UID**（期望 5 个不一致对需 `N ≈ 5/p_d`，`p_d`=1%→500、2%→250）。**若补充达不到，`H3a` 降为 exploratory，不改检验方法，不用功效不足冒充显著结论。** 证据见 `2026-09-24_phase1a_power_mde_sensitivity_grid.md` §4。

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

- Appendix Table A1：B0–B4 的开发侧可学性门，不与论文主学生结果混表。
- Table 1：A0–A3 的 action/target、harm、coverage、最坏家族、不确定性和成本。
- Table 2：七类规则门的 harmful accept、valid retention、gate 指标、查询/回滚与成本。
- Figure 3：学生候选风险—送检覆盖与 quality–verification-cost Pareto。
- Figure 4：共享候选流上的 retained-valid、retained-harmful、rollback 与累计成本。
- Appendix：数据卡、曝光审计、训练配置、家族全表、null/adverse 与排除清单。

在独立验收前，这些槽位只能消费 `paper_result=false` 的水印预览，不能填写正式数字。

## 10. 执行与验收顺序

1. GB10 恢复后先只读核现状，在干净隔离 worktree 里执行。
2. 完成历史 TAT-QA UID 曝光审计、FinQA 过程来源 preflight 与 Valentine NYC 动作来源 preflight，再由用户批准具体来源；ConvFinQA/FinQA 先做同源去重。
3. 按 Phase 1 数据合同双跑、零 `connect` 并取得独立人工验收。此后 Phase 1a 与 Phase 2 分别申请授权：Phase 1a 回答可学性，Phase 2 回答规则门；两者可顺序执行，但 Phase 2 不以 `LEARNABILITY_SIGNAL` 为前置。
4. 只有 Phase 1a 留有可学残差，才继续 4B smoke、8B A0–A2；A3 仍单独判门。Phase 2 的正式 replay 只依赖已接收数据、可重建状态与其单独授权。
5. 各阶段均需用户对应授权；详细命令、输出位置和回滚规则只维护在 handoff 计划及 Phase 1a data-gate 报告，本文件不复制。

## 11. 冻结前人工检查表

- [ ] 数据来源、许可、版本、hash 和历史曝光清单已签字。
- [ ] Q3 双审/裁决和四层 UID 零交叉已独立验收。
- [ ] 若申请 4B/8B 训练，五基线结论为 `LEARNABILITY_SIGNAL`；若只申请 Phase 2 replay，本项不构成前置。
- [ ] 模型/revision/template、训练超参、seed、预算和输出位置已冻结。
- [ ] $\delta_q$、$\delta_h$、$\delta_r$、$\rho_{\max}$、$\alpha_{\mathrm{sig}}$、$\rho_c$、最低 UID/家族覆盖、MDE 和两组 Holm family 已确认。
- [ ] 三类实验输出均带证据级别和 `paper_result` 标记，sealed test 只允许揭封一次。
- [ ] 专利公开门已由用户确认；未确认时不投稿、不上传预印本、不公开核心代码。
