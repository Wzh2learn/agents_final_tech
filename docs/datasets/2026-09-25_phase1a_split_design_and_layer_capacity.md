# Phase 1a SPLIT 设计与层容量实测（双命名空间，2026-09-25）

> 状态: 设计 + 实测件（Loop D）| 裁定依据: D-A=3 / D-C 最小下载范围 / D12 UID 目标 | 零模型调用、零端点、零下载
> 仪器: `research/phase1a_split_assign.py`（15 例合同测试，GB10 全绿）| 暂存: GB10 `~/wzh/phase1a_staging_20260925/`（仓外，数据体永不入 Git）
> 上游: `docs/experiments/2026-09-25_source_go_p1p2_staging.md`（SOURCE_GO）· 协议: `docs/datasets/2026-09-24_phase1a_role_protocols_and_templates.md` · 词表: `paper/dataset_protocol_v1.md`

## 1 结论摘要

1. **SPLIT 仪器与规则已就绪**：确定性、标签盲、零连接、哈希绑定 fail-closed 的分层运行器已落地并通过 15 例合同测试；
   两次运行产物逐字节相同（产物内不含任何墙钟字段）。
2. **动作包的 SPLIT_GO = BLOCKED**，且不是「差一步」而是四堵可实测的墙（§5）。在 D-C 批准范围内，
   任何命名空间都无法产出可通过 `research/phase1a_data_contract.py` 的 phase1a 包。
3. **RQ2 所需的「同样本桥」在批准范围内不存在**：FinQA 有过程/checkpoint 证据但无动作标签语义，
   Valentine 有动作标签材料但无过程/checkpoint。按 `paper/dataset_protocol_v1.md` §4.1 的既有规则，
   缺桥时 RQ2 记 `NOT_IDENTIFIED`，两路只算互补预研。
4. **决策前识别出两项不受当时待裁定项阻塞的工作**（§7；2026-10-03 裁定后仅 Valentine Q3 仍在途，FinQA 步级线由 V2-3 关闭）：Valentine 146 列的 Q3 独立复核，
   以及 FinQA checkpoint adapter 设计。二者都不依赖 §8 的裁定结果。
5. 本件不改任何冻结判据、不改 `paper/dataset_protocol_v1.md` §4.1 的 PILOT_ONLY 裁定、不改注册表；
   需要改的地方全部作为 §8 的裁定项上交。

## 2 预注册规则（先于任何标注固定，且不可由参数绕过）

| 项 | 规则 | 出处/理由 |
|---|---|---|
| 聚类单元 | `independence_cluster` = 命名空间前缀 + 共享来源组 id；FinQA = 年报filing `TICKER/YEAR`，Valentine = NYC 表对目录名 | `paper/dataset_protocol_v1.md` §6.1（簇粒度为 report/document/table family，不得把整个数据集写成一个簇） |
| lineage root | FinQA = `TICKER/YEAR/page_N.pdf`（例 id 去掉尾部 `-K`）；Valentine = `<pair>/source_table.csv` | §6.1「stable report/document/table root」 |
| uid | `lineage_uid(dataset_id, dataset_revision, lineage_root_id)`，直接复用合同函数，不另实现 | `research/phase1a_data_contract.py:137` |
| dataset_revision | 取注册表 `checked_default_head`，代码内不写死 | 单一信源；漂移即 fail |
| 宇宙有界化 | `sha256("phase1a-split-v1:universe\n" + cluster) mod M == 0` 者入选；`M` 为必填显式参数，无默认值 | 防止静默调参；M 的选择只影响规模，不接触标签或结果 |
| 层分配 | `sha256("phase1a-split-v1:layer\n" + cluster) mod 100` → train [0,50) / dev [50,70) / gate [70,85) / sealed [85,100) | 两个盐互相独立；簇级分配 ⇒ root 与 uid 天然不跨 partition |
| sample_id | `sha256` 规范化对象（salt + dataset_id + revision + natural_key）；FinQA natural_key = 例 id，Valentine = `pair#col_index#col_name` | §6.1「stable sample hash」 |
| 标签盲 | Valentine 侧只读 `source_table.csv` 的表头行；`ground_truth.json`、`target_table.csv`、全部数据行、扰动轨迹一律不读，且这些文件被刻意排除在 sha256 manifest 之外 ⇒ 一旦读取即 `input_not_in_sha256_manifest` 失败 | 把「不看答案」变成机械强制，而非口头承诺 |
| 治理编码 | 注册表 `role_fit` 未字面含 `gate_validation` / `sealed_test` 时，该两层输出为空、受影响行转入 `pending_ruling_rows` 并给出 `LAYER_CAPACITY_BLOCKED_PILOT_ONLY`；只有显式传入裁定 id（`--pilot-override-ruling`）才可填层 | 规则 4 类治理冲突不再靠人记；裁定 id 会写进产物，可追溯 |
| future_replay | 恒为空数组 + `LONGITUDINAL_EVIDENCE_UNAVAILABLE` 注记 | 前瞻批次尚未到来，不得伪造长期证据 |

## 3 仪器与自证

- 运行器：`research/phase1a_split_assign.py`（491 行）；测试：`tests/test_phase1a_split_assign.py`（15 例，GB10 `venv/bin/python -m pytest` 全绿）。
- 覆盖的正反例：pilot 命名空间扣住 gate/sealed · 传入裁定 id 后四层齐备 · 行满足合同 8 字段与 uid 重算 ·
  ground_truth/target_table 从不被读 · `layers_manifest_sha256` 与合同 `_digest_object` 口径逐位相同 ·
  两次 compute 逐字相同 · CLI 产物逐字节相同 · 篡改一字节即 `input_sha256_mismatch` ·
  manifest 缺项即 `input_not_in_sha256_manifest` · 例 id 不可解析即 `unparsable_example_id` ·
  命名空间不在注册表即 `namespace_not_in_registry` · `commit` 非 40-hex 与 `M<1` 均 fail 且不写文件 · 零连接守卫。
- 产物不含墙钟字段（`executed_at` 只打印到 stdout），因此「双跑 byte-identical」是构造性质而非运气。
- 产物直接给出 `layers_manifest_sha256`，即 `analysis_plan.layer_manifest_sha256` 必须等于的那个摘要（合同 :977）。

## 4 实测层容量（GB10，暂存只读；产物写 /tmp/split_probe_20260925/，不入 Git）

运行时刻 repo HEAD = `236cda99162954a16d057e8187581507f420f25b`；运行器字节与落库字节一致（§10 给复核命令）。
UID 列 = 宇宙内不同 lineage root 数（含被扣住的行）；train/dev 为已分配样本数，pending 为按规则本应进入
gate/sealed 但因注册表 `role_fit` 未授权而被扣住的样本数。四项相加恒等于宇宙内样本数（逐行核过）。

### 4.1 FinQA 命名空间（cluster = 年报 filing，root = 报告页）

| M | 入选簇/总簇 | 宇宙内样本 | UID | train | dev | pending gate | pending sealed | 产物 sha256（前16） |
|---|---|---|---|---|---|---|---|---|
| 1 | 768/768 | 7 134 | 2 409 | 3 409 | 1 472 | 930 | 1 323 | `bdab21afd9f0e94e` |
| 4 | 194/768 | 1 875 | 619 | 780 | 315 | 304 | 476 | `930b4fb2b2c8c502` |
| 8 | 88/768 | 856 | 286 | 376 | 180 | 182 | 118 | `aed1bf22e20bc936` |
| 12 | 63/768 | 709 | 228 | 259 | 146 | 167 | 137 | `8224442358c3bf63` |
| 16 | 41/768 | 389 | 124 | 182 | 83 | 78 | 46 | `3537b28c9574c63f` |
| 20 | 39/768 | 378 | 124 | 138 | 98 | 104 | 38 | `cbaf147d95c5fa47` |
| 24 | 31/768 | 340 | 109 | 151 | 68 | 76 | 45 | `47f25a52fad67c05` |

读数：四层在 M ≤ 12 时全部非空（含被扣住的两层），几何上完全可填；M=8 的 UID = 286 落在 D12 的
250-500 目标带内，M=4 为 619（超出上界）。M 不在本件定稿：FinQA 走过程/checkpoint 流，无需人工或载体标注，
其规模应由 checkpoint adapter 的算力预算决定，而非由标注预算决定；本表只给出「M → 规模」的实测映射供裁定。

### 4.2 Valentine NYC 命名空间（cluster = 表对，root = source_table.csv，sample = 一个源列）

| M | 入选簇/总簇 | 宇宙内样本 | UID | train | dev | pending gate | pending sealed | 产物 sha256（前16） |
|---|---|---|---|---|---|---|---|---|
| 1 | 10/10 | 146 | 10 | 99（7 簇） | 0（0 簇） | 23（2 簇） | 24（1 簇） | `8ff657cb4fb4369d` |

`layers_manifest_sha256` = `3651cd32883c599bf32fa9728ab7af28d7c13409caed950f695e9dab289c22b6`；
产物 reasons 逐字为 `LAYER_CAPACITY_BLOCKED_PILOT_ONLY:gate_validation,sealed_test`、
`ROWS_WITHHELD_PENDING_RULING:47`、`EMPTY_REQUIRED_PARTITION:proposal_train.dev`、
`EMPTY_REQUIRED_PARTITION:gate_validation`、`EMPTY_REQUIRED_PARTITION:sealed_test`。

源侧标注材料实测（只读 `ground_truth.json`，仅用于容量核算，不进入分层输入）：
10 个表对共 146 个源列 / 160 个目标列；`matches` = 77（覆盖 146 源列中的 77 列）、
`ambiguous_scenarios` = 10、`false_positive_scenarios` = 0。
按 §4.2 口径：`map_to` 有 77 个机械候选（Q1，须经 Q3 方可用），`hold` 有 10 个天然歧义候选，
而 `skip` 的源侧机械种子为 0 —— 69 个未被 matches 覆盖的源列只是候选负例，按协议必须经 Q3 才可标 `skip`。

## 5 四堵墙（每条给实测或条文出处，不靠主观判断）

W1 — 10 个簇填不满四层（最硬的一堵）。阈值分桶在 10 个簇上把 dev band（20%）分到 0 个簇，
实测 `EMPTY_REQUIRED_PARTITION:proposal_train.dev`。合同 `REQUIRED_PARTITIONS` 要求四个 partition 全部非空，
空即 `layer_isolation: missing_or_empty_partition`。这堵墙与 PILOT_ONLY 裁定无关：即使授权 gate/sealed，
dev 仍为空。簇数 10 是批准范围的上限（D-C 只批了这 10 个 NYC 目录）。

W2 — 注册表与协议都不给 Valentine gate/sealed 角色。`paper-public-source-registry-v1.json` 中
`valentine_nyc.role_fit = [schema_action_pilot, simple_baselines, proposal_train]`；
`paper/dataset_protocol_v1.md` §4.1 明写「当前 Valentine NYC 10 个表对只登记为 PILOT_ONLY proposal/dev 候选，
不同时承担 gate；后续新增且按完整 origin cluster 隔离的独立批次才可申请 gate 角色」。运行器按注册表字面执行，
未授权即扣行并报 `LAYER_CAPACITY_BLOCKED_PILOT_ONLY`。

W3 — 动作流的 UID 功效结构性不足。Valentine 的 lineage root 就是源表，一表对 = 1 root = 1 UID，实测 K = 10。
D12 的目标是补充 250-500 个有效 UID；`docs/experiments/2026-09-24_phase1a_power_mde_sensitivity_grid.md`
表 A 给的所需 K 在 delta=0.02 时为 45、delta=0.01 时为 178（且那是下界，未计 Holm）。
K=10 与目标带差 25-50 倍，且这不是「多标注就能补」的量：它受表对数量约束，而表对数量受下载范围约束。
按 D12 既定处置，动作流上的 UID 聚类确认性推断只能记 exploratory。

W4 — FinQA 不能承担动作标签。注册表 `finqa.action_label_fit = PROGRAMS_ARE_NOT_MAP_HOLD_SKIP_LABELS`；
§4.1 亦写「用 gold program/supporting evidence 设计 checkpoint adapter；不直接转成动作标签」。
其已审计的 schema 角色（`docs/datasets/phase1a_schema_draft_v1.json`，取 README 第 31-47 行）描述的是
条目级字段（pre_text/post_text/table/id/qa.*），不是金融表列的 canonical 字段表；
D-A=3 明确禁止自行构造或替代官方 schema。故 FinQA 虽能几何上填满四层（§4.1），
却无法提供合同要求的 `label_ledger`（`gold_action` 属 {map_to, skip, hold} 且带 `col`）。

合成结论：批准范围内，动作流有标签语义但填不满层且 K=10；过程流填得满层但没有动作标签语义。
§4.1 要求的「同样本桥」（同一母池同时具备 checkpoint evidence + Q3 teacher action/target + Q3 outcome）
在两个命名空间中都不存在，故 RQ2 记 `NOT_IDENTIFIED`，Phase 1a 动作包的 DATA_NO_GO 不能凭本批解除。

### 5.1 W4 补充：闭合两条显然的绕法（append-only）

绕法一，把 schema 草案的九个**条目级**字段（pre_text / post_text / table / id / qa.*）直接当作
`canonical_fields` 去标 FinQA 的表列：任何真实表头（如 `Net Sales`、`2009`、`% of Net Sales`）都不属于该字段集，
故 `gold_action` 只能恒为 `skip`；此时「恒预测 skip」的规则即可取得 `action_macro_f1 = 1.0` 与
`harmful_map_rate = 0` 的双满分，可学性结论退化为恒真命题，`minimum_uid_by_action` 也无法满足
（合同要求键集恰为 {map_to, skip, hold}，而 map_to / hold 两类为空）。

绕法二，改用「自 canonical」（把归一化后的原表头自身当参考词汇，即
`research/phase1a_parser_contract_receipt.py` 的冻结口径）：这与 `docs/datasets/2026-09-24_dA_canonical_reference_evidence.md`
§2 第 2 条已判定的情形同构 —— map_to 判定退化为对表头归一化的确认，与可见性口径同义反复，不满足独立性。

⇒ W4 的实质不是「缺一份 schema 文件」，而是**该来源在本任务定义下无判别力**：
非退化的动作标签需要一个外部 canonical 词汇，而 Valentine 天然自带一个（同一官方来源的目标表列名，见 G-D），
FinQA 不自带。这也解释了注册表为何把两者的 `action_label_fit` 写成两种相反结论。

### 5.2 对「P1-future 包逐门推进」这一路径的更正

既定推进路径写作 SOURCE_GO → LABEL_GO → SPLIT_GO → … 且以 P1-future（FinQA）包为载体。按本件实测应更正为：

1. P1-future（FinQA）**能**过 SOURCE_GO（已在案）与 SPLIT 的几何门（四层可填，§4.1），
   但**不能**过 LABEL_GO —— 见 W4 与 §5.1，除非任务定义改变（属判据面，须显式授权）。
2. 动作标签链（LABEL_GO 及其后的可学性/功效门）的天然载体是 Valentine 命名空间，
   而它被 W1（十簇填不满四层）与 W3（K=10）挡住，且 W2 是治理裁定而非技术限制。
3. 因此「逐门推进」在批准范围内没有单一载体可走通；可行的是两条并行支路：
   FinQA 走 checkpoint adapter（过程流外部效度，不需动作标签），
   Valentine 走 proposal_train 内的 exploratory 可学性（146 列 Q3 复核，见 §7.1），
   两者都不构成 RQ2 的确认性证据。是否接受这一更正即 G-E。

## 6 与合同的逐门对位（哪一门、以哪个码失败）

| 合同门 | 失败码 | 触发条件 | 本批状态 |
|---|---|---|---|
| `layer_isolation` | `missing_or_empty_partition` | `proposal_train.dev` / `gate_validation` / `sealed_test` 任一为空 | Valentine 三者全空（W1+W2）；FinQA 仅后两者空（W2 同理，注册表 `role_fit` 未含） |
| `independent_correctness` | `missing_label` | 任一 partition 内任一样本无 Q3 标签行 | 合同要求**全 partition 全覆盖**，故 gate/sealed 也须标注；这决定了复核工作量按宇宙内全部样本计，而非只按 proposal |
| `independent_correctness` | `label_not_q3` / `insufficient_independent_reviewers` / `missing_adjudication` | 单审、载体不足 2、分歧无裁决 | 由 §7.1 的三载体流程覆盖 |
| `analysis_plan` | `layer_manifest_sha256` 不等 | 与 `_digest_object(manifest["layers"])` 不一致 | 本件产物已直接给出该摘要（§4.2 全值；§4.1 各 M 的产物内含），装配时逐字引用即可 |
| `artifact_integrity` | `feature_ledger_proposal_coverage_mismatch` | 特征账本行集不等于 proposal_train 样本集 | 派生运行器已落地，等标签就位后即可跑 |

判定：**SPLIT 仪器 = READY；动作包 SPLIT_GO = BLOCKED（W1-W4）**。本件不宣称任何门通过。

## 7 决策前识别的两项与裁定后状态

1. **Valentine 146 源列的 Q3 独立复核**。三载体（R1 = qwen3.8-max，R2 = deepseek-v4-pro，裁决载体独立且不得由
   生成者担任），按 `docs/datasets/2026-09-24_label_review_protocol_templates.md` 的可见性边界执行；
   另加一条本批新增的边界：**任何载体都不得看到 `ground_truth.json`**（含 `matches` / `ambiguous_scenarios`），
   否则判定退化为对源侧既有答案的确认，与 D-A 证据件 §2 第 2 条同构。源侧 ground truth 只在复核完成后
   用于事后一致性统计（Q3 gold 对源侧 gold 的收敛效度），并须披露其为来源自带元数据。
   工作量：146 样本 × 2 载体，按每块约 50 样本切分 ⇒ 约 6 次判定派发 + 分歧裁决，落在既有模型预算内。
   合同要求全 partition 覆盖标签，故这 146 列在 G-A/G-C 任一结果下都需要标注，先做不产生返工。
2. **FinQA checkpoint adapter 设计**（过程/checkpoint 流）。不需要动作标签，因此不受 W4 约束；
   四层几何可填（§4.1），M 由 adapter 的算力预算定稿后再跑一次本仪器即可产出权威 layers。

仪器可复用：若将来获批新的独立批次，只需在注册表加行（含 `independence_cluster_namespace` 与
`checked_default_head`）、下载进仓外暂存、生成 sha256 manifest，即可用同一运行器分层，无需改代码。

## 8 需用户裁定项（本批不代判、不自行改协议）

- **G-A**：是否允许 `valentine_nyc` 承担 gate/sealed（= 同时修 `paper/dataset_protocol_v1.md` §4.1 的 PILOT_ONLY
  与注册表 `role_fit`）。实测前提：即使批准，W1 仍使 dev 为空，故 G-A 单独批准无效，必须与 G-B 或 G-C 同时裁。
  建议：**不批**（10 簇 / K=10，统计上不足以承担接受-回滚门）。
- **G-B**：小簇数下的层分配规则是否由「阈值分桶」改为「按簇哈希排序后的秩分位」（可保证簇数 ≥4 时四层非空）。
  代价：层归属不再对新增簇稳定，`future_replay` 的「新增独立批次」语义会被削弱。
  建议：**保持阈值分桶**，不为凑非空而改规则（改规则去适应数据正是本门要防的事）。
- **G-C**：是否批准一次新的最小下载增量，以取得 ≥40 个 origin cluster 的独立批次（真正填满四层并把 K 抬到
  可讨论的量级）。本批不下载、不选源；若批准，范围须另行精确申报。
- **G-D**：Valentine 的 canonical 参考是否可用 `target_table.csv` 的表头（同一官方来源自带的目标表列名，
  非我们构造的字段表）。建议：**可用**，但需确认，因为它是对 D-A=3「不得自行构造或替代官方 schema」的延伸适用；
  确认前 §7.1 的复核输入包不装配。
- **G-E**：在 W1-W4 未解除前，是否接受「Phase 1a 动作包维持 DATA_NO_GO、RQ2 记 `NOT_IDENTIFIED`、
  小论文继续按已落地的评估保底口径推进、Valentine 146 列的 Q3 复核作为 exploratory 可学性证据」这一组合。
  建议：**接受**（与目标中「不允许无限等待」一致，且不动任何冻结判据）。

## 9 红线自查

- 零模型调用、零端点：本批全部实测为只读脚本；运行器内置 connect 守卫，产物 `observed_ports` = `[]`。
- 零下载：未获取任何新文件，只使用 D-C 已批准并已在案的暂存。
- 数据体不入 Git：分层产物写 GB10 `/tmp/split_probe_20260925/`；本件只记哈希、字节数与计数。
- 未改冻结判据 / 冻结 hash / TAT-DQA 边界；未改 §4.1、未改注册表、未改合同、未改任何钩子或守卫逻辑。
- 未覆盖 production 脏件：GB10 侧只新增两个未跟踪文件，`git pull --ff-only` 前先删除同名未跟踪副本。
- git 纪律：逐路径 add，无 `-A`、无 `--amend`、无 `--no-verify`、无破坏性命令。
- 专利未确认：不外发、不上 arXiv、不公开代码。

## 10 复现

```bash
# GB10，仓库根；STAGE=~/wzh/phase1a_staging_20260925
venv/bin/python -m pytest tests/test_phase1a_split_assign.py -q          # 15 passed
venv/bin/python research/phase1a_split_assign.py --namespace valentine_nyc \
  --staging-root "$STAGE" --sha256-manifest "$STAGE/sha256_manifest.txt" \
  --m-universe 1 --commit 236cda99162954a16d057e8187581507f420f25b --out /tmp/v.json
# 再跑一次到 /tmp/v2.json：cmp 应无差异（产物无墙钟字段）
```

探针产物 sha256（GB10 `/tmp/split_probe_20260925/`，非 Git 资产，仅作本件数字的取证锚）：
`finqa_m1` `bdab21afd9f0e94e8ad5b65db47cb82d82cd37b8bc00c68e0d827044651f2ed6` ·
`finqa_m4` `930b4fb2b2c8c5029d47ec65a68a4115cb27ca1b8be64e0997ee6f27e84e1644` ·
`finqa_m8` `aed1bf22e20bc936de506bfcd93ca55ed518ffb0c8625b355f230212eeb0a5ad` ·
`finqa_m12` `8224442358c3bf633242c25b6f21df9c713db44495d14dc701ee3f6329ef0d6c` ·
`finqa_m16` `3537b28c9574c63f08f498daeab715790ec697f34fcaa9b9244fee7571cb9484` ·
`finqa_m20` `cbaf147d95c5fa477f1a3ced5f3144e5ef25fbb037c4cc8d638952941af0ac43` ·
`finqa_m24` `47f25a52fad67c055afe619f984757bc1eca9a41993c73345c3a48d05927461a` ·
`valentine_m1` `8ff657cb4fb4369d2250454c26410e8b9649b2b1a3c10c7cf9b8de33e734b544`。

## 11 跨 head 复现记录（append-only，2026-09-25 补记）

本件 §4 的层容量数字在两个不同 repo head 上各跑一次，`layers_manifest_sha256` 逐位相同：

| head | 命名空间 / M | layers_manifest_sha256 | 产物差异 |
|---|---|---|---|
| `236cda99162954a16d057e8187581507f420f25b` | valentine_nyc / M=1 | `3651cd32883c599bf32fa9728ab7af28d7c13409caed950f695e9dab289c22b6` | 基准 |
| `d079c055fd014f05a647f124edcceec365fe3967` | valentine_nyc / M=1 | 同上（逐位相同） | 除 `commit` 字段外逐字节相同（过滤该字段后 `diff` 输出为空） |

层分配按构造与 commit 无关：层盐 `phase1a-split-v1:layer` 的输入只有 cluster 字符串，不含 commit。
上表是该构造性质的实测复核，不是巧合，也不是对某一 head 的调参结果。
本记录用于支撑 `paper/thesis_proposal_v1.md` §7.3 取证链 bullet 与
`paper/thesis_ch1_ch2_draft_v1.md` §2.10 的对应陈述（独立审计 Finding F1 的落点补全）。

## 12 用户裁定结果（2026-10-03，append-only）

§8 的建议项已由用户逐条裁定；该节保留为决策前记录，当前口径以本节为准：

| 项 | 裁定 | 当前约束 |
|---|---|---|
| G-A | 不批 | Valentine 不承担 gate/sealed，维持注册表 `role_fit` |
| G-B | 不批 | 保持 frozen hash-threshold bucketing，不为四层非空改分配规则 |
| G-C | 本批不批 | 不选源、不下载；≥40 origin cluster 的扩源另开精确申报卡 |
| G-D | 批准 | `target_table.csv` 表头可作 canonical 参考；只开 146 列 Q3 exploratory 复核 |
| G-E | 接受 | 动作包维持 `DATA_NO_GO`，RQ2 记 `NOT_IDENTIFIED`，小论文按评估保底口径 |

V2-3 同日关闭：FinQA 步级重执行线按预注册停止条件归档，不开 v3、不申报官方算子代码/文档。146 列 Q3 输入包已装配但 review 未运行，不能据此改变任何正式门。
