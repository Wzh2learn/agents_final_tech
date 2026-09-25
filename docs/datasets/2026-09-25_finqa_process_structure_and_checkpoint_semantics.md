# FinQA 过程结构实测与两种 checkpoint 语义的区分（2026-09-25）

> 状态: 实测 + 设计约束件（Loop D）| 零模型调用、零端点、零下载 | 数据体不入 Git
> 取证: GB10 只读探针 over D-C 批准暂存 `~/wzh/phase1a_staging_20260925/`，两文件 sha256 运行时断言等于 SOURCE_GO 在案值
> 关系: 上游 `docs/experiments/2026-09-25_source_go_p1p2_staging.md`；姊妹件 `docs/datasets/2026-09-25_phase1a_split_design_and_layer_capacity.md`（其 W4 判定 FinQA 不承担动作标签）

## 1 实测过程结构（7 134 例，逐文件断言哈希后统计）

| 量 | 实测值 |
|---|---|
| 例数 | 7 134（train 6 251 / dev 883） |
| gold 中间步总数 | 10 960 |
| 每例步数分布 | 1 步 4 240 · 2 步 2 300 · 3 步 374 · 4 步 108 · 5 步 106 · 6 步 6 |
| 步记录键集 | 全 10 960 步恰为 `(op, arg1, arg2, res)`，零例外、零缺键 |
| op 词表规模 | 21 个 op 根；`divide1` 2 618 · `divide2` 2 348 · `minus1` 1 600 · `minus2` 1 555 · `add1` 923 · `add2` 769 · `multiply2` 321 · `multiply1` 310 · `compare` 134 · `divide0` 115 · `average1` 62 · `average2` 52 · `max2` 34 · `sum2` 25 · 余 7 类合计 94（14 类小计 10 866 + 94 = 10 960，与步总数逐条对账） |
| gold 证据条数/例 | 1 条 3 266 · 2 条 3 076 · 3 条 533 · 4 条 177 · 5 条 41 · 6 条 25 · 7 条 9 · 8 条 1 · 9 条 6 |
| 证据落点类型 | `table_*` 8 583 · `text_*` 3 622 |
| `exe_ans` 类型 | float 7 000 · `"yes"` 80 · `"no"` 54 |

三点直接可用的结论：

1. 步级 oracle 是官方自带且结构统一的。每一步都带 `res`（该步的 gold 中间结果），因此步级故障注入与步级
   定位判定都有官方 oracle，无需人工标注、无需模型判定，也不触碰 D-A 对官方 schema 的限制。
2. 多步例占 2 894 / 7 134 = 40.6%。单步例（4 240）没有「中间」可言，步级分层评测只在多步子集上有意义；
   任何 adapter 必须先声明这一分母，否则会把单步例算作步级判别的成功样本。
3. op 词表只有 21 个根且高度偏斜（前四类 divide1 / divide2 / minus1 / minus2 占 8 121 / 10 960 = 74.1%）。
   按 op 根分层报告是必须的，否则总量指标由 divide 与 minus 主导，稀有 op（`sum2` 25、`max2` 34）上的行为不可见。

## 2 关键设计约束：仓内存在两种不同的 checkpoint 语义，不可混用

冻结 Stage E 口径（`logs/graph/eval/checkpoint_discrimination_tables_v2.json`）的顶层结构实测为
`meta`（含 `caliber`、`drop_threshold`、`runtime_s`）· `properties`（`discrimination`、`locality`、
`zero_drift`、`crosscheck_mismatch`）· `by_type`（`alias_variant`、`date_variant`、`mixed_lang`、
`ocr_similar`、`prefix_noise`、`unit_suffix` 六个注入族）· `patent_crosswalk` · `tables` · `qa_arm`。
它测量的对象是表头在确定性注入下的可判别性与定位性，其 checkpoint 是「表 / 表头检查点」，分层维度是注入族。

FinQA 提供的是推理步检查点：一次数值推理过程中的每一步及其 gold 中间结果，分层维度是 op 根。

二者不是同一测量对象的两个数据源，而是两种不同的检查点语义。因此：

- FinQA adapter 必须是新命名空间下的新仪器，产出独立 artifact；
- 不得被描述为对冻结 Stage E 结果的「复现」「重算」或「替代」，也不得复用其口径字段名去承载不同语义；
- 冻结判据与冻结数字（`85 / 7 / 26`、`drop_threshold = 2.0`、`τ_min`、分母 `111`、`TPR`、六族计数）
  零改动、不溯及；本件不产生任何可与之比较的数字，也不主张任何跨口径可比性。

## 3 该 adapter 能与不能支持的主张

能支持（在独立验收通过后）：

- 过程级 / 步级错误定位与分层评测在第二个独立金融来源上的外部效度，即评估轨已知的
  `supported_with_external_validity_gap` 缺口可被一个真实第二数据流部分收窄；
- 步级 oracle 来自官方标注而非模型判定，故不引入裁判偏置，也不消耗模型预算。

不能支持（写死，防越界）：

- 任何动作标签或可学性结论（姊妹件 W4：`action_label_fit = PROGRAMS_ARE_NOT_MAP_HOLD_SKIP_LABELS`）；
- Stage D 蒸馏、学生模型、RQ2 的确认性证据（同样本桥不存在，RQ2 维持 `NOT_IDENTIFIED`）；
- 对甲方业务口径或冻结 Stage E 结论的任何修改或加强。

## 4 下一步 runner 规格草案（未来批实现，本批不实现、不运行）

- 拟名 `research/finqa_step_checkpoint_adapter.py`：零模型、零连接（沿用 socket 守卫模式）、双跑 byte-identical。
- 输入：暂存内 FinQA 两文件（sha256 运行时断言）+ 由 `research/phase1a_split_assign.py` 在选定 M 下产出的
  权威 layers（直接消费其 `layers_manifest_sha256`，不另立一套划分）。
- 步级故障注入：只在多步子集（步数 ≥ 2）上，对单步的 `arg1` / `arg2` / `res` 做确定性扰动；seed 与
  generator commit 写入 artifact；clean 与 mutant 继承同一 lineage root 与同一 role layer，不跨层。
- 报告维度：步级检出与定位、按 op 根分层（21 根全列，稀有根单列不并入 other）、按步数分层（2..6）、
  按 role layer 分层；分母显式声明为多步例数，单步例单独计数且不计入步级判别分母。
- 验收门：fail-closed 编码 + 双跑一致 + 零连接自证 + 独立 Loop C 审计；实现批须带正反例
  （篡改输入哈希必须失败、注入步必须可被定位、未注入的 clean 必须零误报）。
- M 的选定：本件不定稿。姊妹件 §4.1 已给「M → 规模」实测映射（M=8 → 856 样本 / 286 UID / 88 簇，
  M=12 → 709 / 228 / 63），adapter 批按算力预算在该表上选点，并复跑分层仪器产出权威 layers。

## 5 红线自查

- 零模型、零端点、零下载：本件全部数字来自 GB10 只读探针，运行时断言两文件 sha256 等于 SOURCE_GO 在案值。
- 数据体不入 Git：探针输出在 GB10 `/tmp`，本件只记聚合计数，不记任何样本正文、问题文本或表格内容。
- 未改冻结判据 / 冻结 hash / 冻结口径字段；未改 TAT-DQA 边界；旧 TAT-QA 池仍 HISTORICAL_ONLY。
- 未改 `paper/dataset_protocol_v1.md`、注册表、合同与任何守卫逻辑；未覆盖 production 脏件。
- 不外发、不上 arXiv、不公开代码（专利状态仍由用户确认）。
