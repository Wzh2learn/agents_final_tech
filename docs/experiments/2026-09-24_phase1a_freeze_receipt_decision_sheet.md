# Phase 1a 冻结收据裁定清单（Loop D 产出，18 个 UNSET 字段逐项归因）

> 状态: 活跃 | 更新: 2026-09-24 | 取代/被取代: 不取代 DATA_NO_GO 报告，也不改动预注册合同
> 用途: 把 `docs/experiments/2026-09-22_distillation_mvp_preregistration.md` §7 冻结收据里的 18 个 `UNSET` 字段，按「谁能填、卡在哪、填了能解哪道门」拆开，供用户逐项裁定。
> 边界: 本件**不批准任何数值**、不产生任何实验数字、不改判据/阈值/oracle、不解 `DATA_NO_GO`。所有候选值一律标注为**未批准的讨论起点**。

## 1 现状（机械提取，非人工誊写）

§7 收据共 **24 个字段**，其中 **18 个为 `UNSET`**、6 个已定。

已定 6 项 = `status=FROZEN_BY_HUMAN`、`one_sided_interval_method=paired_two_stage_seed_uid_bootstrap`、`threshold_selection=proposal_dev_max_coverage_under_risk_then_macro_f1_then_conservative`、`rq2_holm_family`（H2a/H2b/H2c）、`rq3_holm_family`（H3a_uid_any_harm / H3a_valid_rule_retention）、`sealed_test_open_once=true`。

## 2 18 个 UNSET 按可裁定性分四类

### A 类：只需用户/导师拍板，不依赖任何尚未存在的数据（9 项）

| 字段 | 含义 | 仓内可见的候选值与其身份 | 解开哪道门 |
|---|---|---|---|
| `approved_by` | 批准人 | 无候选，只能由用户填 | 全部（收据生效前提） |
| `approved_at` | 批准时间 | 无候选 | 全部 |
| `significance_level` | 确认性检验 α | **0.05 仅出现在合成测试 fixture**（`tests/test_phase1a_data_contract.py`、`tests/test_phase2_rule_gate_replay.py`），属测试数据，非批准值 | POWER_GO / 推断门 |
| `risk_limit` | 候选风险上限 ρ_max | **0.1 同上，仅合成 fixture** | RQ2 H2c 风险约束覆盖 |
| `delta_quality` | 质量非劣容差 δ_q | 预注册件 §7 自己写明「`delta_quality=0.02` 只能作讨论起点，**尚未批准**」 | RQ2 H2a |
| `delta_harm` | 安全非劣容差 δ_h | 仓内无任何具体数值 | RQ2 H2b |
| `delta_retention` | 规则保留非劣容差 δ_r | 仓内无任何具体数值 | RQ3 H3a retention |
| `minimum_cost_reduction` | 成本下降下限 ρ_c | 仓内无任何具体数值 | RQ4 |
| `seed_list` | 主臂随机种子列表 | §5.4 只规定「主臂至少 3 seeds；单 seed 只标 PILOT_ONLY」，未给具体值 | 训练公平性门 |

**A 类是本轮唯一能靠裁定推进的部分**：9 项全部不需要新数据，用户给出数值即可写入收据。

### B 类：卡在数据补充，值必须从尚不存在的工件算出（4 项）

| 字段 | 依赖 | 对应 DATA_NO_GO 的缺失门 |
|---|---|---|
| `source_manifest_sha256` | 完整源表/schema/`injection_map` 的不可变清单 | Source/schema completeness |
| `historical_exposure_manifest_sha256` | 历史 TAT-QA UID 曝光审计产物 | Independent layers |
| `role_split_manifest_sha256` | 四层（proposal train/dev、gate-validation、sealed-test）disjoint 清单 | Independent layers |
| `q3_adjudication_receipt_sha256` | Q3 双审 + 独立裁决记录（≥2 个不同 reviewer 身份） | Independent correctness |

这四项**不能由任何人先填**：它们是哈希，必须等数据 owner 交付工件后才能计算。

### C 类：卡在模型与训练决策（3 项）

`model_id_revision_hash`、`tokenizer_template_hash`、`training_config_hash` —— 需先由用户批准具体模型与 revision、tokenizer/template、训练超参（对应 `MODEL_GO`），再对冻结配置取哈希。预注册件 §4.2 已把主学生限定为 Qwen3-8B、4B 只做 smoke，但 revision 与配置未定。

### D 类：卡在功效分析，需真实方差（2 项）

`minimum_uid_by_role_family`、`mde_by_confirmatory_contrast` —— 预注册件 §6.3 明令「用开发侧方差假设做 UID 聚类 MDE/功效分析；**不用 sealed 结果反推参数**」，故必须先有 A 类的 α 与 B 类的真实数据，才能算出这两个值。**顺序上 D 类最后。**

## 3 一处必须先澄清的 schema 不对齐（临界路径陷阱）

机器合同 `research/phase1a_data_contract.py` 对 `analysis_plan` 角色硬要求三个键，而 §7 收据里**一个都没有**：

1. `target_power`：合同 `:920` 要求 `("significance_level","target_power","risk_limit")` 三键均为 (0,1) 内有限数值；§7 收据无 `target_power` 字段。**合成 fixture 里的 0.8 同样只是测试数据。**
2. `cluster_unit`：合同 `:918` 要求严格等于 `"lineage_uid"`；§7 收据无此字段。
3. `noninferiority_margins`：合同 `:924` 起要求它是一个**嵌套对象**且键集恰为 `{delta_quality, delta_harm, delta_retention}`（`REQUIRED_NONINFERIORITY_MARGINS`，`:94-98`）；而 §7 收据把这三项写成**顶层平铺字段**。

**两种解释，需用户/导师定夺，本件不代判**：

- (a) §7 收据与 `analysis_plan` 是两个不同工件（收据记批准、analysis_plan 是私有包内的角色件）。若如此，应在预注册件里明写二者关系与各自字段集，否则执行者会照 §7 填错对象。
- (b) 二者本应是同一份。若如此，§7 缺 3 个键且 margins 结构不符，**照 §7 原样填满仍会被合同判 `invalid_target_power` / `invalid_cluster_unit` 而 fail-closed**，白跑一轮。

## 4 建议的裁定顺序（不含任何数值主张）

1. 先裁 §3：明确 §7 收据与 `analysis_plan` 是一份还是两份。这决定后面填表的字段集。
2. 再裁 A 类 9 项（纯决策，零数据依赖）。α、ρ_max、δ_q 三项仓内有可讨论起点；δ_h、δ_r、ρ_c、seed_list 四项仓内无任何依据，需从头给。
3. B 类 4 项转给数据 owner，按 DATA_NO_GO 的「Executable supplement contract」八个角色交付。
4. C 类 3 项等 `MODEL_GO` 决策。
5. D 类 2 项在 A 类的 α 与 B 类真实数据到位后由功效分析算出，不得用 sealed 结果反推。

## 5 与 Loop C 队列的关系（避免重复劳动）

GB10 上 Loop C Lead 控制面（`~/.jinrong-loop-c`）实测：无 `STOP`、`ACTIVE.json={}`、state `IDLE`，队列 6 项 = 2 READY / 4 BLOCKED。其中 `LC-RESEARCH-001`（离线证据图 + 数据补充设计）为 READY 但从未被认领；`LC-DATA-SUPPLEMENT`、`LC-PHASE1A`、`LC-PHASE2` 均 BLOCKED。

`LC-RESEARCH-001` 卡片的 owned paths 是 `docs/experiments/2026-09-23_phase1a_data_no_go.md` 与 `docs/archive/2026-10-20_entry_consolidation/2026-09-22-paper-research-next-phase.md`，**forbidden 含 `paper/*` 与 `research/*`**，故它按现有范围**无法**产出本件（冻结收据在预注册件内、合同在 `research/` 下）。本件与该卡互补，不重复。

该卡另有一处自身矛盾需先解，才可派发：`Owner: Loop A (mimo-v2.6-flash)`，但 forbidden 写「no model or endpoints」、acceptance 写 `calls=0`。派发前需明确它究竟走不走模型端点，并按安全门 §4 设定调用预算与 canary。

## 6 本件不做的事

不批准任何数值、不填任何 `UNSET`、不改预注册合同、不改 `phase1a_data_contract.py`、不解除 `DATA_NO_GO`、不启动 Phase 1a 或 Phase 2、不授权训练或模型端点、不把合成 fixture 值当作候选批准值、不产生任何论文数字。