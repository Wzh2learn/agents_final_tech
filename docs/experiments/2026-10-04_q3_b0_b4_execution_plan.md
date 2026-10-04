# Q3 独立复核与 B0–B4 执行卡（2026-10-04）

> 状态：`PLANNED_NOT_RUN` | 模型调用：0 | 下载：0 | Phase 1a/2/训练：未启动
> 授权边界：本件只定义可审计执行面。三位专家的 Q3 exploratory 摘要已由用户确认，但 raw R1/R2/ADJ、final ledger 与 receipt/hash 尚未封存；B0–B4 没有 GB10 开发结果。
> 关联：`docs/experiments/2026-10-03_ruling_gd_q3_package_and_goal_refresh.md`、`docs/datasets/2026-10-04_rq2_identification_and_acquisition_card.md`

## 1. 当前可复用输入

- 已装配的 Valentine Q3 输入包：10 pair、146 source columns、160 target headers，历史包在 GB10 `/tmp/valentine_q3_20261003_jeDV/package_a/`。
- 输入包已有稳定 `sample_id`、`uid`、canonical target header、R1/R2 prompt、裁决空模板和 manifest。
- 历史包是 hardening 前的不可变证据，不覆盖、不改写。若 `/tmp` 包不可用，只能从严格三文件 allowlist 重建，且 `ground_truth.json` 只做存在性校验，禁止 open/read。
- 当前 Q3 可见性边界：R1/R2 只见 source header、canonical reference 和 label semantics；ADJ 只见分歧、source header、canonical reference；三者均不得见 `ground_truth.json`、pipeline mapping、injection map 或他载体判定。

## 2. R1/R2/ADJ 派发合同

### 2.1 身份和隔离

| 载体 | 既有路由 | 会话/模型要求 | 可见面 |
|---|---|---|---|
| R1 | `qwen3.8-max` | 独立会话、独立模型身份，不是生成器 | source header、canonical reference、LABEL_FIELDS |
| R2 | `deepseek-v4-pro` | 与 R1 互异的独立会话/模型身份，不是生成器 | 同 R1，但不得见 R1 判定 |
| ADJ | 独立第三身份，待派发前明确 | 与 R1/R2/生成器均互异，不得复用生成器上下文 | R1/R2 分歧行、source header、canonical reference |

任何身份不互异、上下文共享、生成者兼任或复用输入包生成器上下文的运行直接判 `INVALID`。MIMO Token Plan 当前仅 `READY_FOR_CONFIG_ONLY`；没有明确派发授权前不调用模型、不运行 R1/R2/ADJ。

### 2.2 调用预算和监控

- 硬预算 `<200`，包含 canary、失败重试和任何 MCP 模型调用；不因长任务使用短 timeout。
- 长任务后台运行，monitor 记录 PID、开始时间、heartbeat、日志、调用计数、资源占用和退出码。
- canary 失败、身份/可见性审计失败、JSON 重复键、超预算或任一安全门触发即停，不无限重试。
- 任何载体输出必须是严格 JSON；重复 key 用 `object_pairs_hook` 拒绝；禁止把 token、env 值、prompt 私密字段写入日志或 Git。

### 2.3 标签与裁决

1. R1/R2 对每个 `(sample_id, uid, col)` 给唯一 `action`（`map_to/hold/skip`）和 `target`。
2. 只有 R1/R2 完成且身份/可见性审计通过，才生成分歧集。
3. ADJ 只裁决分歧，不重写一致行；裁决记录包含 `adjudicator_id`、template version、action/target、rationale ref。
4. 生成者、输入包 builder 和任一 reviewer 不得自审；缺裁决、缺 reviewer、身份重合或无 hash 绑定均 `LABEL_GO=FAIL`。
5. 只有最终 label ledger 锁定后，才允许做 source 自带 `ground_truth.json` 的收敛效度统计；该统计是事后元数据对照，不是 reviewer 输入，也不替代 correctness。

## 3. B0–B4 简单基线

本卡不新增 runner。沿用 `research/phase1a_learnability_baselines.py` 的五个固定基线：

| 编号 | runner 名称 | 作用 |
|---|---|---|
| B0 | `always_skip` | 零送检/全跳过下界；risk 不定义时不记 0 |
| B1 | `deterministic_matcher` | 规范化后唯一精确 canonical match，否则 skip |
| B2 | `lexical_fuzzy` | lexical/SequenceMatcher 相似度阈值；代表 exact/fuzzy 与 classical matcher 的轻量对照 |
| B3 | `confidence_only` | 只用真实 confidence 字段；missing 记 `unmeasurable`，不填 0 |
| B4 | `simple_classifier` | 特征绑定的廉价 CPU softmax 分类器；只是可学性探针，不是学生模型 |

`deterministic_matcher + lexical_fuzzy` 覆盖 exact/fuzzy/classical matcher 角色；本批不额外引入 COMA/Cupid/外部 matcher，也不把它们当新实验。B0–B4 全部只消费 proposal/train train/dev，输出 aggregate-only 指标和 UID-cluster 区间。

## 4. 前置与运行顺序

只有以下输入全部具备，才允许在 GB10 隔离 worktree 运行：

1. `SOURCE_GO`：来源、revision、字节、sha256、许可和零私有数据证明；
2. `LABEL_GO`：Q3 label ledger、R1/R2/ADJ 三身份审计、裁决和冲突隔离；
3. `SPLIT_GO`：四层 UID 零交叉、cluster-level 分桶和 `layer_manifest_sha256`；
4. `POWER_GO`：真实开发侧方差、MDE/power receipt、最低 UID/action/family 覆盖；
5. `BASELINE_GO`：B0–B4 runner 的 hash-bound feature ledger、precheck、独立 acceptance receipt 和 analysis_plan；
6. `MODEL_GO`：用户批准模型/revision/tokenizer/template、预算、输出目录、恢复策略和 seed `[42,43,44]`；
7. `SAFETY_GO`：磁盘/inode/available memory/GPU utilization/并发/产物/日志/进程回收全部通过。

运行顺序固定为：输入包完整性与可见性审计 → R1/R2 双审 → ADJ 分歧裁决 → label ledger 锁定 → source gold 事后收敛统计（若有）→ Q3 质量报告 → B0–B4。Q3 和 B0–B4 都只标 `paper_result=false`。

## 5. 指标和判定

### 5.1 Q3 复核报告

必须逐项给原始计数、分母、缺失/冲突数和 hash：

- R1/R2 action agreement、target agreement、分歧数；
- ADJ 裁决数、未裁决数、身份/可见性违规数；
- `map_to / hold / skip` 的每类计数与 reviewer 独立性；
- source gold 收敛统计（若运行）明确标 `SOURCE自带元数据`，不与 Q3 correctness 混名。

### 5.2 B0–B4 报告

沿用 runner 的 `action_macro_f1`、`harmful_map_rate`、`map_to_risk`、`correct_map_coverage`、worst-family、UID support、成本和 bootstrap 区间。confidence-only 的 missing 子集单列，不能与 full partition 直接比较。

### 5.3 Go / no-go

| 结果 | 含义 | 后续 |
|---|---|---|
| `SIMPLE_SUFFICIENT` | 非学习简单基线已满足预注册开发策略 | 停止升级到 8B 训练，保留简单方法结果 |
| `LEARNABILITY_SIGNAL` | 廉价分类器在开发侧相对最强非学习基线有预注册残余增益 | 只允许申请单独 MODEL_GO/训练窗口，不等于 DATA_GO |
| `NO_CLEAR_SIGNAL` | 没有基线满足开发策略 | 不训练，报告 null/adverse |
| `PILOT_ONLY` | UID/family/action 覆盖不足或输入质量不足 | 只报 pilot，不冒充确认性结论 |

Q3 raw 未封存、身份不独立、ground_truth 泄漏或 label ledger 未锁定时，所有 B0–B4 结果无效，不进入 Stage D。

## 6. Stage D 门序

只有 `SOURCE/LABEL/SPLIT/POWER/BASELINE/MODEL/SAFETY` 全部通过，才按：

`B0–B4 → A0 zero-shot → A1 unfiltered SFT → A2 checkpoint-filtered SFT → A3 DPO（条件实验）`

推进。A2 才是 checkpoint filtering 的主对比；A3 不是默认步骤。任何阶段接近 OOM、磁盘爆满、GPU 争用或预算上限即停，产物写隔离 worktree/独立 run-id 目录，不覆盖 production。

## 7. 明确未完成

- Q3 R1/R2/ADJ：用户确认的 exploratory 摘要已形成；raw 输出、final ledger、visibility receipt 与 manifest/hash 仍 `MISSING`，不是 artifact closure；
- B0–B4：`NOT_RUN`，没有 GB10 development 数字；
- RQ2：`NOT_IDENTIFIED`，不因 Q3 或简单基线自动升级；
- Stage D/Phase 2/训练：未启动；
- MIMO：`READY_FOR_CONFIG_ONLY`，本件不派发模型、不记录 token；
- 任何结果不得写成 Stage D、DATA_GO、RQ2 确认或 safe continual improvement。

## 8. Status addendum (2026-10-04)

The user subsequently confirmed that three independent experts completed R1/R2/ADJ Q3 review. The reported exploratory summary is 146/146 adjudicated labels, 119/146 action exact agreement (81.51%), action Cohen's kappa approximately 0.727, 41/41 target exact agreement on shared `map_to` decisions, and a pre-correction distribution of `map_to=52 / skip=58 / hold=36`. The authoritative corrected distribution is `map_to=51 / skip=58 / hold=37` after the single line-61 correction.

Raw expert outputs, adjudication ledger, final label ledger, visibility receipt, and hashes are still pending seal. B0-B4 remain `NOT_RUN`. A B5 Jev-like typed-decision baseline is registered only as `PROPOSED_EXPLORATORY / NOT_RUN`; it does not replace the frozen B0-B4 set and does not change `DATA_NO_GO`, `RQ2 NOT_IDENTIFIED`, or training authorization.

## 9. Boundary closure addendum (2026-10-04)

The raw seal is not complete. See [docs/experiments/2026-10-04_q3_boundary_blocker_audit.md](2026-10-04_q3_boundary_blocker_audit.md) and [docs/datasets/2026-10-04_b0_b4_exploratory_split_protocol_v1.md](../datasets/2026-10-04_b0_b4_exploratory_split_protocol_v1.md). Three invalid action references are pending user choice between reference quarantine and whole-pair INVALID. B0-B4 remain NOT_RUN; B5 remains PROPOSED_EXPLORATORY / NOT_RUN. No model, Phase 2, training, or download was started.

## 10. Ruling status (2026-10-04)

Raw originals must be delivered to exact GB10 paths or /home/testuser/wzh/q3_raw_seal_20261004/inbox/. Invalid references use Option A as primary and Option B as mandatory sensitivity. B0-B4 uses LOO primary and salted split sensitivity; bootstrap 2000 / seeds [42,43,44] are exploratory only. B5 remains dormant. No run is authorized.

## 11. Sealed Q3 correction (2026-10-04)

Raw seal is complete with visibility exceptions. Use corrected ledger SHA256 cf339cef8b7065dad05f574a1400415a7bff64b78b66e1db38f74143cc49ccb6 and corrected counts 51/58/37; 52/58/36 is superseded for analysis. B0-B4 remain NOT_RUN.
