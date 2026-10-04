# RQ2 Valentine same-sample bridge structure audit（2026-10-04）

> 状态：实证结构审计（Loop D，零模型/零下载） | 运行：GB10 唯一权威
> 输入：D-C 已批准暂存 `~/wzh/phase1a_staging_20260925/valentine/experiments/data`
> 边界：未打开 `ground_truth.json` 内容；`_full.json` 含内嵌 gold，原文件不得进入任何 R1/R2/ADJ 或学习特征。

## 1. 审计问题

RQ2 需要同一 `lineage_uid` 同时具备 checkpoint evidence、action/target、correctness。本件只回答 Valentine 现有 10 个 pair 是否具备可机械抽取的前两项，以及 raw 文件是否能安全交给复核载体。

## 2. 工件与完整性

GB10 `/tmp` 只读审计产物：

| 产物 | 字节 | sha256 |
|---|---:|---|
| `rq2_valentine_trajectory_inventory.json` | 83,280 | `5df515ff69a4838cd498d988ad540ff05482b612827a8790c35d029e89191998` |
| `rq2_valentine_bridge_structure.json` | 42,145 | `74ea5c9e09319f9850260a603827e0f6c45bba9224ba472553eaad4badab3aaf` |
| `rq2_valentine_toolcall_string_audit.json` | 3,255 | `5ffc1317ab2e1661176d89b057e16bf0577eb97a04974b91778d293b3582e266` |
| `rq2_valentine_toolcall_dict_audit.json` | 13,742 | `76f902ae2521429ae8fd5a405dc839cce4cff0f5acd51edea887c1f6c81fb3c8` |
| `rq2_valentine_bridge_feasibility.json` | 16,104 | `ddb01138c5fcbe5aa742fe832600f9192b6c33ca0c5dec0cb2c9b156d6948c09` |

## 3. 结构实测

| 项目 | 实测 |
|---|---:|
| pair clusters | 10 |
| source headers / target headers | 146 / 160 |
| audit turns | 359 |
| trajectory-log turns | 349 |
| trajectory messages | 739 |
| final tool calls | 360 |
| raw/final tool-call identical turns | 324 |
| raw/final different turns | 35 |
| `was_rewritten=true` | 37 |
| action events | `batch_record_match=23`, `record_match=6`, `revoke_match=1`, `finalize_all_matches=10` |
| final source-header coverage | 146 / 146 |
| final target-header coverage | 119 / 160 |
| action-event source coverage | 146 / 146 |
| trajectory forbidden-marker count | 0 |
| audit-with-gold-fields-removed marker count | 0 |

工具参数包含 `source_column(s)`、`target_column`、`confidence`、`reasoning`、`transformation_code` 以及 `mappings/matches/pairs`。工具名包含 `record_match`、`batch_record_match`、`revoke_match`、`finalize_all_matches`、`retrieve_candidates*`、`test_transformation`。这证明动作生成不是只存在于最终汇总，而是有 turn-level 候选、接受/撤销和 finalization 过程。

## 4. Gold 隔离边界

1. `ground_truth.json` 本身未 open/read。
2. `<pair>_full.json` **内嵌** `ground_truth` 与 `final_evaluation`；即便本审计只打印结构签名和计数，raw `_full.json` 仍不得交给 R1/R2/ADJ、不得进入 feature ledger。
3. `<pair>_trajectory.json` 未检出 `ground_truth`、`final_evaluation`、`ambiguous_scenarios`、`false_positive_scenarios` 标记。
4. `<pair>_result.json` 是 post-hoc evaluation，不能作为 correctness，也不能给生成/复核载体。
5. 后续 adapter 必须只导出 `audit_trail` 的 turn/tool-call/state 事件，显式删除 gold/evaluation 字段，并对输出做 forbidden-key fail-closed 检查。

## 5. 对 RQ2 identification 的判定

### 5.1 已获得

- checkpoint evidence：`trajectory`、`trajectory_log`、`audit_trail` 的 turn、accepted/rejected、raw→final rewrite、工具调用序列。
- action/target 候选：工具调用参数和最终 record/revoke/finalize 事件可回指 source column；146/146 源列被 final 动作流覆盖，119/160 target header 被最终动作流引用。
- 同样本连接可行性：source header、稳定 pair/lineage root、过程 turn 和 action event 可在同一 pair/column 身份上派生。

### 5.2 仍缺

- correctness：Q3 R1/R2/ADJ 尚未运行，source-side gold 不能替代独立 correctness。
- B0–B4：Valentine `proposal_train.dev=0`，不满足 runner 的非空 dev/UID support；不能用 10 pair 强跑。
- confirmatory power：10 clusters、K=10、dev 为空，不足以形成 `POWER_GO` 或 gate/sealed。
- 轨迹语义清洗：当前 `_full.json` 的 audit trail 是可抽取过程证据，但尚未形成带 hash 的去 gold checkpoint adapter/receipt。

### 5.3 当前边界

- 现有 10 pair 可以支撑 **exploratory Q3 + checkpoint extraction feasibility**，不能支撑 Stage D、RQ2 confirmation、DATA_GO 或训练。
- Route V 的扩源目标仍是至少 40 个独立 pair clusters，但优先级现在明确为：先做 Q3 correctness 和去 gold adapter，再按 split/power 证据决定新增目录范围。
- Route F 仍受 D-A/V2-3 阻塞，不构造替代 action ontology。

## 6. 下一步执行合同

1. 实现并测试去 gold 的 Valentine process-checkpoint adapter；输出必须 `paper_result=false`、`ground_truth_read=false`、`correctness_status=NOT_RUN`。
2. Q3 R1/R2/ADJ 在独立授权后运行，任何载体不得见 `_full.json` 原文、`ground_truth.json`、`_result.json`。
3. Q3 锁定后才把 correctness join 到 checkpoint/action 事件；再决定 Route V 精确扩源和 B0–B4 的 split/power 申报。
4. 任何 raw `_full.json`、source gold 或 `_result.json` 进入 reviewer/feature 都判 `INVALID`，不得用事后 gold 补 Q3。

## 7. Adapter preflight addendum (2026-10-04)

The gold-free adapter and Q3 package focused suite passed on GB10 before the real-staging preflight: 24 passed. Real D-C staging then failed closed at 	ool_call_source_not_in_header. In one pair (City_Government__DSNY_Districts_With_Disposal_Vendor_Assignments), three final action events (ecord_match, evoke_match, atch_record_match) reference mgp_curb_pri_boro, which is in neither the 16-column source header nor the 17-column target header. The 146/146 valid source coverage remains true, but the full process view is not safely bindable until those three invalid action references are quarantined or explained. The adapter intentionally does not emit a partial checkpoint package. A positive-control strace observed 1 synthetic ground_truth.json open; the real adapter trace observed 0.
