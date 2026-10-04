# RQ2 identification 与数据获取申报卡（2026-10-04）

> 状态：`DECISION_APPLICATION / NO_EXECUTION` | 授权：本件不下载、不扩源、不派模型、不启动 Phase 1a/2 或训练
> 基线：批准起点 `f2adaf1be13cd641ca0993c8e2d20a16ad717cfc`；本件起草时 local = origin = `e44c3c3d3922bc8b3c6f11d6a7cd50526ad6ebc0`
> 目的：把 RQ2 缺少的同样本桥、候选数据路线、许可、split 和 power 申报做成一次精确决策面；不自行选择或获取新数据。

## 1. identification 结论

RQ2 的可识别对象必须在**同一个 namespaced lineage UID 内**同时具备三类证据：

1. `checkpoint evidence`：动作生成前可获得、可追溯到来源与生成状态的过程检查点；
2. `action / target`：`map_to / hold / skip` 动作及 `map_to` 的 canonical target；
3. `correctness`：独立 Q3 标签与裁决结果，能够定义正确动作、错误动作和 harmful action。

当前批准范围内没有单一母池满足这三项：

| 来源 | 已有 | 缺失 | 当前可写边界 |
|---|---|---|---|
| FinQA `train/dev` | gold program / reasoning steps，可形成 process/checkpoint 证据 | 当前任务定义下没有独立 action/target 语义；D-A 选项 3 不提供官方 schema excerpt，V2-3 又关闭了算子材料路线 | 互补过程证据，不是 RQ2 同样本桥 |
| Valentine NYC 10 pairs | source/target header、动作/correspondence 材料、146 个 Q3 待复核源列 | 没有已审计的同一样本 checkpoint evidence；`proposal_train.dev=0`、K=10，不能承担 gate/sealed | exploratory action learnability，不是 Stage D 或 RQ2 证据 |
| 历史 TAT-QA / TAT-DQA | 历史评估材料 | TAT-QA 未完成曝光审计；TAT-DQA 冻结 | 不进入本轮 RQ2 母池 |

因此当前状态继续为 `RQ2 = NOT_IDENTIFIED`、`DATA_NO_GO`。146 列 Q3 即使完成，也只能说明 Valentine 子集的标签可学性，不会自动补出 checkpoint bridge。

## 2. 两条候选路线比较

### 2.1 Route V：Valentine 独立 cluster 扩源（优先候选，待批准）

**优点**

- 保留现成的 action/target 与 Q3 复核语义；
- 10 个已有 pair 的输入包、稳定 sample_id、可见性边界和 allowlist runner 可以复用；
- 以 pair 为 independence cluster，符合现有 `lineage_uid` 与 split 规则；
- 后续若获得可审计的状态轨迹，可在同一 source column 上连接 checkpoint、action/target 和 correctness。

**关键缺口**

- 当前 10 个 pair 只有 10 个独立 cluster，且冻结 hash-threshold bucketing 下 dev 为空；
- `_full/_result/_trajectory` 文件不能未经语义审计就当 checkpoint evidence；
- 扩源到至少 40 个独立 origin clusters 仍受 G-C 不批准边界约束，必须先批准精确目录清单；
- Valentine 的 source `ground_truth.json` 只能在标签锁定后做来源自带 gold 的收敛效度统计，不能给任何 R1/R2/ADJ 看。

**推荐**

Route V 是当前最短的 identification 路线，但只是**申报候选**。本卡不下载新目录、不改 G-A/G-B/G-C、不改变现有 10-pair 输入包状态。

### 2.2 Route F：FinQA action/schema 元数据补全（当前不推荐）

**优点**

- 已有成熟 process/checkpoint 语义和相对大的报告级 lineage universe；
- 可作为未来独立过程效度或外部验证命名空间。

**阻塞**

- D-A 裁定为选项 3，用户未提供官方 TAT-QA schema excerpt，主线程不得构造替代 schema；
- V2-3 已关闭 FinQA 步级重执行，不开 v3、不申报官方算子代码/文档；
- FinQA program 不等于本任务的 action/target 标签，必须另立任务定义、canonical 动作 ontology、独立 reviewer 和 licence annex；
- 不能与 Valentine 按行拼成同分布主实验。

Route F 只有在用户另行批准新的任务定义和精确来源/许可附件后才可进入识别；本卡不代为选择该路线。

## 3. Route V 精确获取申报（待用户批准后才执行）

### 3.1 来源身份

| 字段 | 申报值 |
|---|---|
| official repo | `https://github.com/delftdata/valentine` |
| source revision | `5d5163f04da304985bd51a476ccf7653de3979c3` |
| cluster unit | 一个独立 NYC table-pair 目录；namespace 仍为 `valentine_nyc` |
| target size | 目标是累计至少 40 个独立 pair clusters；不是 40 个源列，也不是 40 个事件 |
| current batch | 已批准的 10 个 NYC 目录不重复下载，不覆盖、不重写 |
| execution place | GB10 仓外 staging；数据体不进 Git |

### 3.2 新增文件范围（任何清单外文件均需重新申报）

对每个**经批准**的新增 pair 目录，最小范围只允许：

```text
valentine/experiments/data/<approved_pair>/source_table.csv
valentine/experiments/data/<approved_pair>/target_table.csv
valentine/experiments/data/<approved_pair>/ground_truth.json
```

`ground_truth.json` 只做输入完整性与最终收敛统计，生成输入包时不得读取内容。若后续需要把 `_full.json`、`_result.json` 或 `_trajectory.json` 作为 checkpoint evidence，必须：

1. 先提交这些文件的精确路径、字节、sha256、字段语义和读取权限；
2. 证明它们的 checkpoint 语义不是由 `ground_truth.json` 或注入结果反推；
3. 取得单独批准后才可加入获取范围。

**明确排除**：FinQA test/private、全文 PDF、其他数据集、其他 Valentine 目录、任何私有数据、任何未列文件或派生缓存。

### 3.3 Licence 申报

| 来源 | 当前证据 | 申报边界 |
|---|---|---|
| Valentine repo | Apache-2.0，`LICENSE` sha256 = `f4960433bd98568685898d782e724fc28b5481be2a4b57b6280bf6e8c262e99d` | 仅 training / tuning / evaluation / rule_acceptance |
| NYC 目录数据 | NYC Open Data 上游条款 govern | 不得扩展 redistribution、public_release、commercial_use、其他数据源或其他许可解释 |
| D-B licence_record | `docs/datasets/phase1a_licence_record_v1.json`，accepted_by=Wzh | 只覆盖 FinQA LICENSE、FinQA README、Valentine LICENSE 三件；不等于新增目录已获授权 |

新增 pair 的许可核验必须在获取前逐目录记录 owner、许可文本/URL、covered artifact hashes 和 permitted uses；不得用现有 D-B 记录替代新目录确认。

### 3.4 split 申报

- 继续使用 `research/phase1a_split_assign.py` 的双盐规则：cluster-level universe bound + frozen layer hash bucketing。
- 四层仍为 `proposal_train`、`dev`、`gate_validation`、`sealed_test`；`future_replay` 可空但必须标 `LONGITUDINAL_EVIDENCE_UNAVAILABLE`。
- G-A/G-B 不变：不把 Valentine 提升为 gate/sealed，不为凑四层非空改分配规则。
- 若新增 cluster 后仍有空层或不满足最低 UID 覆盖，结果是 `SPLIT_GO = BLOCKED` 或 `PILOT_ONLY`，不是重新分桶。
- Q3 标签必须覆盖进入任何正式层的样本；proposal/train 内部 dev 只用于阈值选择，gate/sealed 不参与选择。
- 同一 pair 的 source/target/trajectory/Q3 行、clean/mutant 和后续规则事件必须共享同一 lineage UID，禁止跨层。

### 3.5 power 申报

沿用已批准的设计起点，不新增数字：

| 项目 | 值/规则 |
|---|---|
| `significance_level` | `0.05` |
| `target_power` | `0.80` |
| `risk_limit` | `0.10` |
| `delta_quality / delta_harm / delta_retention` | `0.02 / 0.02 / 0.02` |
| `minimum_cost_reduction` | `0.10` |
| `seed_list` | `[42, 43, 44]` |
| 聚类单元 | namespaced lineage UID / independence cluster |
| 区间 | 成对 seed×UID 两阶段 cluster bootstrap；seed dispersion 单报 |
| threshold | `proposal_dev_only`；完整规则记为 `proposal_dev_max_coverage_under_risk_then_macro_f1_then_conservative` |

`minimum_uid_by_action`、`minimum_uid_by_role_family` 和 `mde_by_confirmatory_contrast` 仍需真实 proposal/train 开发侧方差后形成 power receipt；不能从 10 pairs、146 columns 或任何 source gold 直接推导。D12 的 250–500 有效 UID 目标是 H3a 欠功效的处置目标，不是 RQ2 的自动样本量承诺。未达功效时只报 pilot/不确定区间，不改检验方法。

### 3.6 RQ2 母池角色合同

每个进入 RQ2 的样本必须能由同一 UID 重算并绑定以下角色：

1. `checkpoint evidence`：状态/检查点来源、生成器身份、时间/step、输入输出 hash；
2. `action/target`：Q3 标签、reviewer identities、adjudication、canonical target；
3. `correctness`：独立裁决后的正确性标签，harmful action 定义冻结；
4. `source/schema`：官方来源、schema/metadata、revision 和 source hash；
5. `licence_record`：owner/time、covered hashes、permitted uses；
6. `confidence_manifest`：只记录真实来源字段，缺失写 `unmeasurable`；
7. `analysis_plan`：18 键机器合同，绑定 manifest hash；
8. `parser_contract_receipt` / `learnability_feature_ledger` / `phase1a_manifest.json`：按现有 Phase 1a 合同生成并独立复核。

若 checkpoint evidence 不能在同一 UID 上重算，或 correctness 只能由生成器自审，RQ2 继续 `NOT_IDENTIFIED`，不进入 B0–B4 或 A0–A3。

## 4. 当前门状态与决策请求

| 门 | 当前状态 | 通过所需 |
|---|---|---|
| SOURCE_GO | 部分证据已有，新增 cluster 未批准 | 用户批准 Route V 精确目录/文件范围、来源 revision、许可 annex |
| LABEL_GO | 未通过 | Q3 R1/R2/ADJ 独立身份、双审/裁决和冲突处理完成 |
| SPLIT_GO | BLOCKED | 新 cluster 后四层/UID 覆盖和冻结分桶通过；不改 G-A/G-B |
| POWER_GO | 未通过 | 真实开发侧方差、MDE/power receipt、最低 UID/family 覆盖人工批准 |
| BASELINE_GO | 未运行 | Q3 + B0–B4 在 GB10 独立验收 |
| MODEL_GO | 未授权 | 用户批准模型/revision/预算/窗口/输出目录/恢复策略 |
| SAFETY_GO | 设计已定义，未运行 | 磁盘/内存/GPU/并发/产物/调用/进程回收监控实际通过 |

**请求用户裁定的最小项**

1. 是否批准 Route V 作为 RQ2 identification 候选，并批准“至少 40 个独立 pair clusters”的目标；
2. 是否批准新增 pair 的精确目录清单获取申请（本卡不自行列名、不下载）；
3. 是否批准每个新增 pair 仅取 `source_table.csv / target_table.csv / ground_truth.json`，其他轨迹文件另卡；
4. 是否接受上述 licence、split、power 申报作为后续 acquisition/precheck 的边界；
5. Q3/B0–B4 是否在新 key、模型派发授权和 SAFETY_GO 后执行。

在用户明确批准前，所有状态保持 pending，不创建第二份 licence_record，不新增下载，不动 TAT-DQA/TAT-QA 边界，不把 exploratory 证据升级为 Stage D。
