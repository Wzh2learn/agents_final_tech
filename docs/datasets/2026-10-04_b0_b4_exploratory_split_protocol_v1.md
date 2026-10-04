# B0-B4 exploratory split protocol v1

> 状态：`USER_SELECTED_NOT_FROZEN / NOT_RUN` | Goal：`ACTIVE`
> 运行边界：只准备协议；不运行 B0-B4/B5、不启动模型/Phase 2/训练、不新增下载
> 关联：[`docs/experiments/2026-10-04_q3_boundary_blocker_audit.md`](../experiments/2026-10-04_q3_boundary_blocker_audit.md)

## 1. Purpose and evidence level

本协议只回答一个 exploratory go/no-go 问题：在 Q3 三类动作和 canonical target 上，简单 typed-decision 基线是否已经覆盖大部分可学结构，从而降低训练专门 checkpoint-filtered student 的必要性。

它不是 frozen `phase1a_learnability_baselines.py` 的替代实现，不产生 Stage D、DATA_GO、RQ2 confirmation 或训练授权。当前 Valentine `proposal_train.dev=0`，所以 frozen runner 不能直接运行。

执行硬前置：

1. Q3 raw R1/R2/ADJ、final ledger、visibility receipt 和 manifest/hash 已封存；
2. 三个 `mgp_curb_pri_boro` 异常引用已由用户裁定为 reference quarantine 或 whole-pair INVALID；
3. 分析分母、split 选项、超参和停止条件已冻结；
4. 任何运行仍带 `paper_result=false`，只在 GB10 隔离 worktree/独立输出目录执行。

## 2. Analysis unit and labels

- 独立单元：Valentine table-pair / lineage UID，不是 146 个 source columns。
- 当前总体：10 clusters / 146 source columns。
- 若采用 whole-pair INVALID：9 clusters / 130 source columns；若采用 reference quarantine：10 clusters / 146 columns，但须标 3 个 quarantine references。
- gold action/target 只能来自封存后的 Q3 final label ledger。不得读取 `ground_truth.json`、source gold、pipeline mapping、injection map、checkpoint score、gain/collateral 或 reviewer raw outputs作为特征。
- `confidence` 缺失记 `unmeasurable`，不得填 0。

## 3. Split options

### P1 - Leave-one-pair-out（推荐用于 exploratory）

- 外层 10 folds（或 whole-pair INVALID 时 9 folds）：每次留出 1 个 pair 作 test，其余 pairs 作 train/calibration。
- 所有外层 test pair 在该 fold 中只评估一次；不得用它选 threshold、feature、超参或 stopping。
- B0/B1/B3 不拟合阈值；B2 的 lexical threshold 和 B4 的 classifier hyperparameters 必须在外层开始前冻结。
- 若必须调 threshold，只能在每个外层 train 集内做 group-aware inner leave-one-pair-out；inner validation 也不得跨 pair 泄漏。
- 合并外层 out-of-fold prediction 后再计算总体指标；不能把每个 fold 的样本平铺当 iid。
- 主区间：按 pair cluster bootstrap，保留 seed `[42,43,44]` 的独立重复；seed dispersion 单报。建议 2,000 次 bootstrap，但次数需在冻结收据中确认。

### P2 - Salted group-aware exploratory split（备选）

- 新建独立 exploratory salt，不修改 frozen split 或 G-B。
- 建议规则：`sha256("b0b4-explore-v1:layer\n" + pair_id) mod 100`，train `[0,60)`、dev `[60,80)`、test `[80,100)`。
- 每个 pair 整组进入一层；禁止 source columns、Q3 rows、trajectory events 跨层。
- 若任一层为空，协议即 `BLOCKED_EMPTY_LAYER`，不得换 salt、不得手工补齐。
- 该 split 只能做 exploratory sensitivity，不能写成 gate/sealed 或正式 split。

**建议**：P1 作为主 exploratory 协议，P2 作为 split-sensitivity；最终选择需用户批准，不能两者挑更好的结果报告。

## 4. Frozen baseline mapping

| ID | runner role | 拟合/调参边界 |
|---|---|---|
| B0 | `always_skip` | 无拟合 |
| B1 | `deterministic_matcher` | 无拟合 |
| B2 | `lexical_fuzzy` | threshold 必须预冻结；若调参仅在 inner group folds |
| B3 | `confidence_only` | 无拟合；missing 置信度子集单列 |
| B4 | `simple_classifier` | 仅在外层 train pairs 拟合；超参预冻结；不是学生模型 |

B5 不属于 B0-B4，不进入本协议的排名、调参或 go/no-go。

## 5. Metrics and denominators

以封存后的 Q3 ledger 为唯一 correctness 来源。摘要中的 `map_to=52 / skip=58 / hold=36` 只作预期校验，不替代 ledger 计数。

| 指标 | 分母/定义 |
|---|---|
| action macro-F1 | 所有评估 source columns 的三类 action；固定类别集合 `map_to/hold/skip`，缺类按 0 并报 support |
| per-action P/R/F1 | 各 action 的 gold support；不因某 fold 缺类而删除该类 |
| target exact | 主分母 = gold `map_to`；错误 action 或 missing target 记错误 |
| predicted-map target exact | 次分母 = predicted `map_to`；与主分母分开报告 |
| harmful-map rate | incorrect `map_to` / all evaluated columns |
| map-to risk | incorrect `map_to` / predicted `map_to`；预测数为 0 时记 `undefined` |
| correct-map coverage | correct `map_to` / all evaluated columns |
| hold/skip recall | 各类 gold support |
| worst pair/family | 每个 pair 的指标与 support；不把 pair 内 columns 当独立样本 |
| cost/latency | 可记录，不进入本 exploratory 的科学结论 |

不确定性：

- pooled out-of-fold point estimate；
- pair-cluster bootstrap 95% interval；
- 每 pair 单独指标和 support；
- `[42,43,44]` 的 seed dispersion 单列；
- 10 clusters 很少，任何区间都标 exploratory，不作确认性显著性声明。

## 6. Stopping and invalidation

以下任一发生即停止，不继续 B0-B4/B5：

1. raw seal 缺任一必需工件；
2. 三个异常引用未获用户处置；
3. Q3 ledger、input manifest、split manifest hash 不一致；
4. 任何 reviewer/gold/pipeline 字段进入 feature；
5. 在外层 test 或全体 146 rows 上调参后再报同集结果；
6. split 空层、pair/UID 跨层或 cluster 数与分母不一致；
7. 输出出现 NaN/Inf、未定义风险被写成 0、或 `paper_result=true`；
8. 计划要求的 reviewer/label/visibility receipt 无法独立复核。

本协议只允许输出 `SIMPLE_SUFFICIENT / LEARNABILITY_SIGNAL / NO_CLEAR_SIGNAL / PILOT_ONLY` 一类 exploratory disposition；其具体阈值必须另行冻结，不能使用测试 fixture 的阈值冒充批准值。

## 7. Current status

- 协议已写，不执行；
- `proposal_train.dev=0` 仍然成立；
- B0-B4 runner 仍 `NOT_RUN`；
- B5 仍 `PROPOSED_EXPLORATORY / NOT_RUN`；
- `DATA_NO_GO`、`RQ2 NOT_IDENTIFIED`、Stage D/RQ4/训练/外发边界全部不变。

## 8. User ruling applied (2026-10-04)

- P1 leave-one-pair-out is selected as the primary exploratory protocol.
- P2 salted group-aware split is selected only as split sensitivity.
- Pair-cluster bootstrap `n=2000` and seeds `[42,43,44]` are accepted for exploratory uncertainty only; they do not prove power.
- Thresholds, classifier hyperparameters, exact candidate grids, output hashes, and freeze receipt are still pending. Therefore this is `USER_SELECTED_NOT_FROZEN`, not an execution authorization.
- The same data may not be used for tuning and then reported as the evaluation set.