# Q3 boundary and blocker closure audit（2026-10-04）

> 状态：只读边界审计 | Goal：`ACTIVE`，不申报完成
> 运行边界：零模型、零 B0-B4/B5、零 Phase 2、零训练、零新下载
> 证据等级：Q3 仅为 user-confirmed exploratory summary；raw artifact closure 未完成

## 1. Q3 raw artifact inventory

| 必需工件 | 准确状态 | 路径/证据 | 判定 |
|---|---|---|---|
| R1 output | `MISSING_ARTIFACT` | 本地仓库、`D:\AIRcommend\JinRongAgents`、GB10 `~/wzh` 与 `/tmp` 未找到结果件 | 不得由摘要反推 |
| R2 output | `MISSING_ARTIFACT` | 同上 | 不得由摘要反推 |
| ADJ output | `MISSING_ARTIFACT` | 同上 | 不得由摘要反推 |
| final label ledger | `MISSING_ARTIFACT` | 仅有 `research/phase1a_label_ledger_assemble.py` 及测试，不是 ledger 产物 | 146 行最终标签尚无 raw ledger |
| visibility / gold-isolation receipt | `MISSING_ARTIFACT` for expert run | 输入构建 receipt 存在，但不能替代专家运行可见性 receipt | 需独立封存 |
| output manifest/hash | `MISSING_ARTIFACT` | 输入包 manifest 存在；专家输出 manifest 不存在 | 不能以输入 manifest 顶替 |

已确认的输入包位置：GB10 `/tmp/valentine_q3_20261003_jeDV/package_a`。

| 输入件 | sha256 | 解释 |
|---|---|---|
| `manifest.json` | `d91fd7d46a8c02c7ef4432d3fa1f38d8b5b42956746723d33244bd9dbcb94b5c` | 输入包 manifest |
| `samples.jsonl` | `6843f4c500a90335f5b66f48e130565bb3887407aa1ad8971a99385e9ea28c6d` | 146 个输入样本 |
| `canonical_reference.json` | `241ca7ed1ef30c4531cd9d6c7dc03652c00142eb7a0d622c637489b57bede377` | canonical target headers |
| `../build.strace` | `b588bf9a966d07eb0bfa06dfa2760fa179d84fea081904b18bfa3cfc15c54258` | 输入构建的 gold 隔离证据 |

模板状态实测：

- `r1_block_001/002/003.json`：`judgments=[0,0,0]`
- `r2_block_001/002/003.json`：`judgments=[0,0,0]`
- `adjudication_block_001/002/003.json`：nonnull action/target `[0,0,0]`

因此这些文件是输入空模板，不是 raw 专家结果。

误封候选已排除：

- `/tmp/r1.json`：历史 audit report schema，不是 Q3 reviewer output。
- `/tmp/r2.json`：历史 preregistration payload schema，不是 Q3 reviewer output。
- 机器收据：[`docs/datasets/phase1a_q3_seal_receipt_v1.json`](../datasets/phase1a_q3_seal_receipt_v1.json)。

用户确认摘要仍只可写为：146/146 adjudicated；119/146 exact agreement；action κ≈0.727；shared `map_to` target 41/41；27 个 action-boundary disagreement；最终 `map_to=52 / skip=58 / hold=36`。`seal_complete=false`。

## 2. Three invalid action references

来源：GB10 D-C staging 的 `<pair>_full.json`，只读递归检查 `source_column/source_columns`。

pair = `City_Government__DSNY_Districts_With_Disposal_Vendor_Assignments`；source headers=16，target headers=17。`mgp_curb_pri_boro` 不在 source headers，也不在 target headers。

| turn | location | tool | call id | invalid source ref | rewrite / verdict |
|---:|---|---|---|---|---|
| 12 | `final` | `record_match` | `call_c4f11200e31c4c269217b8dc` | `mgp_curb_pri_boro` | `was_rewritten=true`; `REJECT` |
| 13 | `final` | `revoke_match` | `call_59ac6c3556084cfea42c037f` | `mgp_curb_pri_boro` | `was_rewritten=true`; `REJECT` |
| 31 | `final` | `batch_record_match` | `call_5e32f59bddca46e18a95c413` | `mgp_curb_pri_boro` | `was_rewritten=true`; `REJECT` |

共同特征：三条均位于 rewritten/rejected 过程；该引用既非当前 source header，也非 target header。不得改名、猜 alias、改 gold 或静默丢弃。

### 2.1 Option A: reference-level quarantine

**处置**

- 对每个非法 source reference 建独立 `invalid_action_reference` 记录，计数固定为 3。
- `batch_record_match` 中的合法 source-column 子事件仍可导出；非法子事件隔离。
- `record_match` / `revoke_match` 若只含非法引用，则该事件不进入 checkpoint/action-state 序列。
- adapter 输出必须带 `invalid_action_reference_count=3`、事件 hash、pair、turn、tool 和 quarantine reason。

**影响范围**

- 保留其余合法 source-column 事件；不直接删除整个 pair。
- 146 个合法 source-column coverage 事实仍成立，但该 pair 的动作状态时间线不完整。
- `record -> revoke -> batch` 中涉及该非法名的状态迁移无法解释；checkpoint-filter 指标须排除这些 quarantine 子事件。
- 需要做 pair-level sensitivity：主分析按 quarantine，敏感性分析按整 pair 剔除。

**风险**

- 若该名本应映射到某个合法列，丢弃 record/revoke 可能让合法列的状态历史错误。
- 若 batch 中混有合法映射，整事件删除会损失合法信息；只隔离非法子事件则必须保证输出解析严格。

**需要批准**

1. 是否允许 reference-level quarantine 而不是整事件删除；
2. 是否要求主分析 + pair-exclusion 敏感性双报；
3. adapter 是否允许输出 partial process view，同时保持 `correctness_status=NOT_RUN`。

### 2.2 Option B: whole pair INVALID

**处置**

- 将该 pair 标记 `INVALID_ACTION_REFERENCE_UNRESOLVED`。
- 不生成该 pair 的 checkpoint/action view；不改 raw、gold 或列名。

**影响范围**

- 去除 1 个 lineage/table-pair cluster 和 16 个 source columns。
- 可分析范围从 10 clusters / 146 columns 变为 9 clusters / 130 columns。
- 由于 final label ledger 尚未封存，不能给出剩余 130 列的 `map_to/skip/hold` 子分布。
- K=10 已不足，剔除后 exploratory 不确定性进一步上升。

**风险**

- 最保守，不会让未知 alias 污染状态序列。
- 可能不必要地丢掉一个仍有 15 个合法 source columns 的 cluster。
- Q3 总摘要 146/146 与 B0 分析分母将不同，必须显式区分。

**需要批准**

1. 是否直接判整 pair INVALID；
2. B0-B4 是否固定使用 9 clusters / 130 columns；
3. Q3 总摘要是否仍保留 146 口径，同时另报分析子集。

**建议处置但不代选**：先按 Option A 生成隔离清单，并把 Option B 作为预注册敏感性分析；主分析采用哪种方案由用户裁定。

## 3. B0-B4 exploratory split

协议已单独落盘：[`docs/datasets/2026-10-04_b0_b4_exploratory_split_protocol_v1.md`](../datasets/2026-10-04_b0_b4_exploratory_split_protocol_v1.md)。

状态：`DRAFT_NOT_FROZEN / NOT_RUN`。当前 `proposal_train.dev=0`，不得直接运行 frozen runner。执行前必须先关闭 raw seal 和异常引用处置。

## 4. B5 offline audit

| 审计面 | `open-alternative-jev` | `jevos-v2` | 证据 |
|---|---|---|---|
| local source checkout | `MISSING` | `MISSING` | 本地/GB10 文件名搜索无实现 |
| licence file | `MISSING` | `MISSING` | 未发现候选源目录或 LICENSE |
| provenance / owner | `UNVERIFIED` | `UNVERIFIED` | 仓内仅有候选名 |
| version / commit | `MISSING` | `MISSING` | 无 lockfile、package metadata 或 tag |
| dependency surface | `UNVERIFIED` | `UNVERIFIED` | GB10 `pip list` 无 jev*；import graph 无候选模块 |
| typed output capability | `UNVERIFIED` | `UNVERIFIED` | 无源码/接口证据；yes/no 限制不能替代三类 action + target |

B5 输入合同保持 `source_header + canonical headers + LABEL semantics`；先判 `map_to/hold/skip`，仅 `map_to` 再选 canonical target。B5 只回答通用 typed-decision baseline 是否覆盖问题、是否仍有训练专门学生的必要性；不解除 `DATA_NO_GO`。

在用户提供准确 source URL/commit/license/dependency manifest，或另行批准 metadata-only 核验前，B5 保持 `PROPOSED_EXPLORATORY / NOT_RUN`，不安装、不运行。

## 5. Boundary status

- Goal 仍 `ACTIVE`。
- Stage E 保底稿有效。
- `RQ2 NOT_IDENTIFIED / DATA_NO_GO` 保持。
- Q3 仅为 exploratory learnability evidence。
- Stage R、RQ4、训练、正式投稿和外部发布均未完成。
- 专利未确认前不上 arXiv、不公开代码、不外发。

## 6. User ruling applied (2026-10-04)

- Raw delivery: use exact GB10 paths when available; otherwise deliver originals to `/home/testuser/wzh/q3_raw_seal_20261004/inbox/`. The directory was created empty with mode 700. Only original outputs/ledgers/receipts are accepted; reconstruction from the summary is prohibited.
- Invalid action references: Option A reference-level quarantine is the primary analysis. Isolate turn 12 `record_match`, turn 13 `revoke_match`, and turn 31 `batch_record_match`; record `invalid_action_reference_count=3`. Option B whole-pair INVALID is mandatory sensitivity. Keep the 146-column Q3 summary and separately report the 9-cluster / 130-column sensitivity subset. No renaming, alias guessing, or gold edits.
- B0-B4: leave-one-pair-out is the primary exploratory protocol; the salted group-aware split is sensitivity only. Pair-cluster bootstrap `n=2000` with seeds `[42,43,44]` is accepted for exploratory uncertainty, not power proof. Same-data tuning followed by same-data reporting is prohibited.
- B5: remains dormant / `PROPOSED_EXPLORATORY / NOT_RUN`. At most a metadata-only audit may be prepared later; installation or execution requires separate authorization.
- Execution gates remain closed until raw seal, invalid-reference implementation, label-ledger lock, split freeze, and B5 boundary closure.