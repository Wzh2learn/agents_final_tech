# 预注册门词表的可追溯性：六个 `*_GO` 门与 `REPLAY_BLOCKED` 在代码里**零落地**，附七门全量失败码清单

> 状态: 活跃 | 更新: 2026-09-24 | 取代/被取代: 不取代任何既有报告；为「预注册门逐门通过」这一验收口径补上**此前不存在的映射表**
> 用途: 目标句与预注册件都以 `SOURCE_GO / LABEL_GO / SPLIT_GO / POWER_GO / BASELINE_GO / MODEL_GO` 六个门为验收单位，要求「必须按顺序通过，不可跳门」（预注册件 §3 :39）。本件机械核实这六个门**在代码里是否存在对应物**，并给出七个机器门的全量失败码清单，使「某门通过」这类主张首次可追溯。
> 边界: 全程只读静态检索与源码解析。未改任何代码、文档或判据一个字节；未改冻结判据；未解 `DATA_NO_GO`；未启动 Phase 1a/2；未运行任何测试或实验；零端点、零模型调用。

## 1 结论摘要

1. **六个 `*_GO` 门名在任何 `.py` 文件里出现 0 次**（`git grep -E 'SOURCE_GO|LABEL_GO|SPLIT_GO|POWER_GO|BASELINE_GO|MODEL_GO' HEAD -- '*.py'` = 0 命中）。它们只作为**散文**存在于两个文档：`docs/experiments/2026-09-22_distillation_mvp_preregistration.md` §3 `:41-46`（各 1 次）与 `paper/dataset_protocol_v1.md`（各 1 次）。
2. 机器侧另有一套**完全不同的词表**：合同 `phase1a_data_contract.py` 的 7 个门名为 `artifact_integrity / layer_isolation / independent_correctness / licence_permission / confidence_provenance / analysis_plan / parser_contract`，终态只有 `DATA_NO_GO` 与 `READY_FOR_INDEPENDENT_ACCEPTANCE`；可学性 runner 另出 4 个决策 `PILOT_ONLY / LEARNABILITY_SIGNAL / SIMPLE_SUFFICIENT / NO_CLEAR_SIGNAL`。**两套词表无一字重合。**
3. 映射是**双向非满射**：6 个散文门中 **3 个有强机械对应**（`LABEL_GO`、`SPLIT_GO`，以及 `SOURCE_GO` 的许可与哈希部分）、**1 个仅部分对应**（`POWER_GO`）、**1 个在另一个脚本里**（`BASELINE_GO`）、**1 个完全无对应**（`MODEL_GO`）；反向看，7 个机器门中 **2 个不对应任何散文门**（`confidence_provenance`、`parser_contract`）。
4. **`REPLAY_BLOCKED` 同样是「文档有、代码无」**：4 处文档要求它，`.py` 命中 **0**；Phase 2 runner 实际以 `raise ValueError` 处置，故该状态**永不会出现在任何报告里**。
5. ⇒ **「逐门通过」目前不可机械判定**。任何「X_GO 已通过」的说法都只能是人工解读，而该解读所依据的映射**此前无任何文档记载**（本件 §3 首次给出）。

## 2 方法

- 门名与状态名：`git grep -n -E` 全仓（HEAD），并**分别统计全仓命中与仅 `.py` 命中**，两者之差即「只在散文里存在」的部分。
- 机器门语义：**不靠门名猜**，而是用正则从源码抽取**每一处** `_fail(gates, "<gate>", "<code>")` 调用并按门分组（合同内共 **99** 处调用、**98** 个不同码字面量，其中 3 个是 f-string 模板，展开后更多）。
- 计数时剔除本会话自产引用（`docs/experiments/2026-09-24_*.md`、`logs/graph/dispatch_log.md`、`memory/THREADS.md`），避免自证。

## 3 映射表（本件的核心产出；此前不存在）

| 散文门（预注册件 §3 :41-46 原文要旨） | 机器对应 | 失败码数 | 覆盖评估 | **无机械检查的部分** |
|---|---|---|---|---|
| **`SOURCE_GO`** :41 — 公开来源 URL、license 适用范围、commit/release、字节 hash、零甲方数据证明已核 | `licence_permission` + `artifact_integrity` | 5 + 27 | **部分** | 「公开来源 URL」「commit/release」「**零甲方数据证明**」三项**无任何机器检查**；`artifact_integrity` 只核字节数与 sha256 自洽，不核来源合法性 |
| **`LABEL_GO`** :42 — Q3 双审/裁决、action/target 正确性、冲突隔离 | `independent_correctness` | 17 | **强** | 该门含 `label_not_q3`、`insufficient_independent_reviewers`、`missing_adjudication`、`invalid_adjudication`、`gold_review_mismatch`、`gold_adjudication_mismatch`、`invalid_gold_action`、`duplicate_label`、`extra_label`、`label_identity_mismatch` 等，与散文逐项对应 |
| **`SPLIT_GO`** :43 — 按 namespaced lineage UID 与 independence cluster 分层；同母表 clean/mutant/轨迹/规则事件不跨层；future replay 需哈希绑定协议，否则标 `LONGITUDINAL_EVIDENCE_UNAVAILABLE` | `layer_isolation` | 22 | **强** | 含 `independence_cluster_cross_role_layer`、`uid_cross_partition`、`lineage_root_cross_partition`、`lineage_uid_mismatch`、`transformation_parent_cross_lineage`、`transformation_parent_cycle`、`future_acquisition_not_after_freeze`、`future_protocol_not_approved` 等；`LONGITUDINAL_EVIDENCE_UNAVAILABLE` 亦已在代码中实现（`.py` 命中 3） |
| **`POWER_GO`** :44 — 用**开发侧方差假设**做 UID 聚类 MDE/功效分析；**不用 sealed 结果反推参数** | `analysis_plan` | 17 | **弱（仅字段形状）** | 该门**只做字段存在性与取值域校验**（`invalid_target_power`、`invalid_mde_by_confirmatory_contrast`、`invalid_minimum_uid_by_*`、`invalid_cluster_unit` 等），**不做任何功效计算**；且「不用 sealed 反推参数」**无任何机器检查**。⇒ **不得把「`analysis_plan` 门 PASS」读作「`POWER_GO` 通过」** |
| **`BASELINE_GO`** :45 — 五类简单基线仍留有可学残差；`SIMPLE_SUFFICIENT`/`NO_CLEAR_SIGNAL`/`PILOT_ONLY`/`DATA_NO_GO` 都停止主训练 | **不在数据合同内**；在 `phase1a_learnability_baselines.py` 的决策输出 | 4 决策 + 5 臂 | **在另一脚本、另一词表** | 决策产于 `:980 PILOT_ONLY` / `:1003 LEARNABILITY_SIGNAL` / `:1010 SIMPLE_SUFFICIENT` / `:1019 NO_CLEAR_SIGNAL`；五臂 = `always_skip`/`deterministic_matcher`/`lexical_fuzzy`/`confidence_only`/`simple_classifier`。⇒ 该门证据**不出现在数据合同报告里**，须另取 runner 报告 |
| **`MODEL_GO`** :46 — 用户批准模型、权重许可、GB10 窗口、预算、输出目录和恢复策略 | **无** | 0 | **完全无机械对应** | 纯用户授权；其记录只会是 C 类三个 hash 字段（`model_id_revision_hash`/`tokenizer_template_hash`/`training_config_hash`），但**无任何代码发出或校验 `MODEL_GO`** |

**反向：7 个机器门中有 2 个不对应任何散文门**

| 机器门 | 失败码数 | 说明 |
|---|---|---|
| `confidence_provenance` | 5 | `gain_collateral_substitution_forbidden`、`invalid_confidence_vocabulary`、`invalid_missing_policy`、`missing_confidence_field`、`missing_confidence_source`。六个散文门**均未提及 confidence**（仅 `DATA_NO_GO` 报告的补充合同表提到该角色）⇒ 这是一道**有实现但无散文门归属**的检查 |
| `parser_contract` | 5 | `parser_contract_not_passed`、`missing_parser_checker`、`invalid_parser_commit`、`invalid_parser_execution_time`、`parser_input_hash_mismatch`。同样**无散文门归属** |

⇒ 六个散文门**不是**七个机器门的划分：既非满射（2 个机器门无人认领），也非单射（`SOURCE_GO` 跨 2 个机器门），且 `BASELINE_GO` 根本不在这套门里、`MODEL_GO` 无任何实现。

## 4 `REPLAY_BLOCKED`：文档要求 4 处，代码实现 0 处

| 出处 | 原文要旨 |
|---|---|
| 预注册件 `:166` | 「Phase 2 源状态不可重建 → `REPLAY_BLOCKED`；不用旧分数拼反事实」 |
| `DATA_NO_GO` 报告 `:47` | 「Phase 2 remains `REPLAY_BLOCKED`; no empty baseline, placeholder result, or speculative paper number is valid」 |
| 计划件 `:283` | 「源表/状态缺失则标 `REPLAY_BLOCKED`，不能伪造闭环或用在线建议器补齐」 |
| 计划件 `:311` | 「任何源表/状态缺失均记 `REPLAY_BLOCKED`」 |

`git grep -n "REPLAY_BLOCKED" -- "*.py"` = **0 命中**。Phase 2 runner 内与状态相关的只有 `REPORT_VERSION = "phase2-rule-gate-report-v2"`（`:22`）与报告里的 `contract_version` 字段（`:565`）；对源表/状态缺失的实际处置是 `_validate_dataset()` 内**抛 `ValueError`**（如 `:149` “forbidden or unknown data layer”、`:169` 候选列表为空、`:191` `source_uid` 不属 `proposal_train` 等）。

**后果（如实界定，不夸大）**：两者**都是 fail-closed**——缺料时不会产出结果，所以**不存在「伪造闭环」的风险**。差异只在**可观测性**：文档承诺的状态字**永不出现在任何报告里**，审计者按 `REPLAY_BLOCKED` 检索产物会一无所获，且一个 `ValueError` traceback 容易被误读为「代码 bug」而非「门判定结果」。⇒ 建议二择一（均需授权）：① 在 runner 里把该类输入缺失收敛为显式 `REPLAY_BLOCKED` 状态并写入报告（改代码，须补正反例）；② 在四处文档追加 append-only 注记，写明「该门的实际实现形态是 `ValueError` fail-closed，报告内无 `REPLAY_BLOCKED` 字面状态」（零代码改动）。**本件不选、不实施。**

## 5 由此必须避免的三类错误主张

1. **不得**把「`analysis_plan` 门 PASS」说成「`POWER_GO` 通过」——前者只校验字段形状，**不做功效计算**，也不检查「未用 sealed 反推」（§3 第 4 行）。
2. **不得**把「合同报告 `READY_FOR_INDEPENDENT_ACCEPTANCE`」说成「六个门全部通过」——它只覆盖 `SOURCE_GO` 的一部分、`LABEL_GO`、`SPLIT_GO` 与 `POWER_GO` 的字段形状；`BASELINE_GO` 在另一脚本，`MODEL_GO` 无实现。
3. **不得**把「`SOURCE_GO` 通过」说成「零甲方数据已证明」——该条**无任何机器检查**，只能由人工/独立审计认定。

## 6 建议（均需授权，本件未实施任何一项）

1. **零代码改动、最低成本**：把 §3 的映射表作为 append-only 注记追加到预注册件 §3 之后（或 `docs/research/README.md` 的冲突裁定层），使「某门通过」的主张从此有唯一映射依据。本件已把表写全，可直接落。
2. **中等成本**：在合同报告里为 7 个机器门各加一个 `maps_to_prereg_gate` 别名字段（纯输出层，不改任何判定逻辑与失败码），使报告自带映射。属代码改动 ⇒ 须授权 + 修者不自验 + 补正反例。
3. **须单独裁定**：`MODEL_GO` 与「零甲方数据证明」两条**本质上不可机械化**（前者是用户授权，后者是来源合法性判断）。建议在文档里明确标为「人工门，不由代码发出」，以免后续再有人找它们的机器对应物。
4. `confidence_provenance` 与 `parser_contract` **有实现但无散文门归属**：建议明确它们归属哪个散文门（或新增第 7、8 个散文门），否则这两道检查在「逐门通过」口径下**无处记账**。

## 7 附录：七门全量失败码清单（机械抽取，共 99 处 `_fail` 调用 / 98 个不同码字面量）

```text
[analysis_plan] 17 处 / 17 码
  ambiguous_legacy_statistical_field, analysis_plan_not_approved, f"invalid_{key}"(模板,
  展开为 invalid_significance_level / invalid_target_power / invalid_risk_limit),
  invalid_analysis_approval_time, invalid_cluster_unit, invalid_holm_adjustment,
  invalid_holm_families, invalid_mde_by_confirmatory_contrast, invalid_minimum_uid_by_action,
  invalid_minimum_uid_by_role_family, invalid_noninferiority_margins,
  invalid_one_sided_p_value_methods, invalid_seed_uid_aggregation, invalid_threshold_selection,
  layer_manifest_hash_mismatch, missing_analysis_owner, missing_primary_metric

[artifact_integrity] 28 处 / 27 码
  artifact_list_required, byte_count_mismatch, duplicate_artifact_id, duplicate_role_artifact,
  empty_artifact, feature_ledger_identity_mismatch, feature_ledger_proposal_coverage_mismatch,
  feature_ledger_source_hash_mismatch, invalid_artifact_entry, invalid_artifact_id,
  invalid_artifact_role, invalid_feature_ledger_fields, invalid_feature_ledger_row,
  invalid_feature_ledger_rows, invalid_feature_ledger_version, invalid_manifest_json,
  invalid_sha256, manifest_object_required, missing_artifact, missing_package_id,
  missing_package_or_manifest, missing_required_role, sha256_mismatch, unreadable_artifact,
  unsafe_artifact_path, unsafe_manifest_path, unsupported_contract_version

[confidence_provenance] 5 处 / 5 码
  gain_collateral_substitution_forbidden, invalid_confidence_vocabulary,
  invalid_missing_policy, missing_confidence_field, missing_confidence_source

[independent_correctness] 17 处 / 17 码
  bound_artifact_unavailable, duplicate_label, extra_label, gold_adjudication_mismatch,
  gold_review_mismatch, insufficient_independent_reviewers, invalid_adjudication,
  invalid_gold_action, invalid_label_fields, invalid_label_json, invalid_label_sample_id,
  invalid_reviewer_label, label_identity_mismatch, label_not_q3, label_object_required,
  missing_adjudication, missing_label

[layer_isolation] 22 处 / 22 码
  duplicate_sample_id, f"invalid_future_protocol_{field}"(模板), f"missing_future_protocol_{field}"(模板),
  future_acquisition_not_after_freeze, future_protocol_not_approved,
  independence_cluster_cross_role_layer, invalid_future_contamination_policy,
  invalid_future_protocol_fields, invalid_future_protocol_freeze_receipt,
  invalid_future_protocol_version, invalid_lineage_entry, invalid_partition,
  lineage_root_cross_partition, lineage_uid_mismatch, missing_future_protocol_cycle_id,
  missing_future_protocol_owner, missing_or_empty_partition, missing_transformation_parent,
  self_referential_transformation_parent, transformation_parent_cross_lineage,
  transformation_parent_cycle, uid_cross_partition

[licence_permission] 5 处 / 5 码
  invalid_acceptance_time, licence_artifact_hash_mismatch, licence_not_accepted,
  missing_acceptance_owner, missing_permitted_use

[parser_contract] 5 处 / 5 码
  invalid_parser_commit, invalid_parser_execution_time, missing_parser_checker,
  parser_contract_not_passed, parser_input_hash_mismatch
```

可学性 runner（`BASELINE_GO` 的实际载体）：4 个决策 `PILOT_ONLY:980` / `LEARNABILITY_SIGNAL:1003` / `SIMPLE_SUFFICIENT:1010` / `NO_CLEAR_SIGNAL:1019`；5 臂 `always_skip` / `deterministic_matcher` / `lexical_fuzzy` / `confidence_only` / `simple_classifier`；`training_authorized` 出现 5 次且恒为 `false`，`paper_result` 出现 1 次。

## 8 复现与取证

```bash
# 六个门名与 REPLAY_BLOCKED 的代码落地情况（关键：分全仓与仅 .py 两次）
git grep -n -E 'SOURCE_GO|LABEL_GO|SPLIT_GO|POWER_GO|BASELINE_GO|MODEL_GO' HEAD
git grep -n -E 'SOURCE_GO|LABEL_GO|SPLIT_GO|POWER_GO|BASELINE_GO|MODEL_GO' HEAD -- '*.py'   # 期望 0
git grep -n 'REPLAY_BLOCKED' HEAD
git grep -n 'REPLAY_BLOCKED' HEAD -- '*.py'                                                  # 期望 0
# 七门失败码分组
~/wzh/projects/agents_final_tech/venv/bin/python /tmp/gate_map.py <worktree>
```

| 文件（GB10 `/tmp`，仓外，不 commit） | sha256 |
|---|---|
| `gate_map.py` | `8cdb19e335cb0a4a4099156436f8509f7a16fde6a29d06f7454a49037f94f7fa` |
| `gate_map.json` | `fe5369ef0340578b43fac60a66dc92da0e767854e8b384123c57fe14110cfa0b` |

纯静态检索与源码正则解析：**零端点、零模型调用、零 canary、零 judge、零起 run；未运行任何测试或实验**（本件不含任何测试结果，故亦无 health 探测计数需申报）。`/tmp` 非持久，故七门清单已全量抄入 §7。

## 9 红线自查

- 未改任何代码、文档或判据一个字节；§6 的四条建议**一律未实施**。
- 未改冻结判据/阈值/oracle/冻结 hash；**未解 `DATA_NO_GO`**；未启动 Phase 1a/2；未批准任何数值、未填任何 `UNSET`；未授权训练或端点。
- 零端点、零模型调用、零 canary、零 judge、零起 run；未运行任何测试；未派发任何 Loop A/B/C 卡。
- 未动 `docs/33`、`docs/34`；未 pull production（仍 `e5ab809` + 5 脏件）；未重启 daemon `1816933` 与 `:5050` `1868428`；未改 crontab；未重置 Loop B；四件用户资产零触碰；逐路径 add、无 `-A`/`--amend`/`--no-verify`。
