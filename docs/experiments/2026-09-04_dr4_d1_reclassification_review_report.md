---
status: DR-4 复核收口（改期 #1 收口重派, 零端点 / 只读 / 不溯及）
date: 2026-09-04
card: docs/experiments/2026-09-01_dr4_d1_reclassification_review_card.md
card_id: TASK-20260901-DR4
artifact: logs/graph/eval/dr4_d1_reclassification_review.json
script: research/paper_dr4_d1_reclassification_review.py
endpoint_calls: 0
reviewed_instances: 118
diff_changed: 8
---

# DR-4 复核：D1 现行分类按 Step 1 独立 oracle 的逐实例结果

> 派发: Loop A 收口重派（改期 #1, 范围严格限定 = 报告 + 收据 + 记账 + 提交, 禁重跑分析 / 禁改工件 / 禁开端点 / 禁改判据）
> 数字来源: **只从冻结工件取**（`payload_sha256` `47adbe66…`, 文件 sha256 `7806b77b…`）; 本报告不新增任何分析或判据。
> 依据: DR-4 重写（`docs/experiments/2026-08-31_d1_autopsy_decision_record.md`）+ 专家第 2 轮 §5（独立 oracle / instance-level）

## 0 一页结论

1. **复核覆盖 = 118/118 注入实例逐实例判定**, 三项判据（C1 算子资格 / C2 规范真值映射不变 /
   C3 下游目标语义不变）逐条证据入工件; 判定路径两阶段冻结（oracle 判定与落盘**先于**读取任何
   `class`/检测/吸收字段）, 禁读字段在阶段 1 产物中零出现。
2. **现行分类被完整复现**（G1）: H 85 / E 7 / HI 26, 逐条 118/118 与 D1 存储标签一致,
   E 集 7 uid 与 T2 冻结集集合相等（alias 4 + prefix 3）。复现门过 → diff 的分母可信。
3. **实例级 oracle 口径 = E 1 / H 117**, 与现行分类的 diff = **8 例**（稳定 110 例）。
   交叉表（oracle | 现行）: `E|H = 1`、`H|E = 7`、`H|H = 84`、`H|HI = 26`。
   ⇒ **现行 7 条等价注入在独立 oracle 下全部不成立**（无一例两侧同时为 E）, 且 26 条 HI 中
   **实例级应判等价者为 0**（卡 §3 步骤 3 专项问句的答案是零）。
4. **翻转的失败判据只有两类**（工件 `correction_record.mechanism_summary`, 7 例 E→H）: `C1_operator` 3 例 +
   `C2_canonical_truth` 4 例; 第 8 例 = `none_failed`（三条全过 ⇒ 新增等价）。前者 = 前缀噪声装饰化过程**删除**了原内容原子
   （单位符号 `US$`/`£` 丢失）, 后者 = 别名替换**丢失限定语**（ACCUMULATED / PAID / FREE / PRE_SPECTRUM）。
   唯一新增等价 = `Revenues → sales`（现行判 H, oracle 判 E）。
5. **对 D3 的敏感性**（不溯及）: D3 有害分母按现行分类冻结 = 111（85 H + 26 HI）; oracle 口径有害集
   = 117 ⇒ **delta = +6**, 等价集 1。D3 已冻结产物不重算, 下一轮 FPR/召回分母须**显式声明口径**。
6. **口径敏感性披露**: 主口径（严格 C2, 限定语属标准字段集）E = 1; 宽松口径（限定语差异移出 C2、
   后果并入 C3 唯一指称检验）E = 15, 两口径逐实例一致 104/118。宽松口径只作披露, 不改主判定、不入分母。
7. **字节级确定性已证**（本次收口重派的唯一执行动作）: 脚本在镜像目录双跑, 两次输出 sha256 全等
   且**与首跑冻结工件逐字节相同**（`7806b77b…`）; 仓库内工件与全部输入 sha 前后未变。

**元结论（给 Loop D, 本窗只登记不判定）**: 「等价注入」作为正例的证据基础在本语料上几乎不存在——
现行 7 条 E 全部因**限定语丢失**或**内容原子被删除**而失败, 唯一成立者是纯同义别名 1 例。
这直接影响 D1「E 集」口径与任何以 E 集为分子的鲁棒性表述; 判据冻结不溯及, 更正只作为
**未来口径与下一轮实验的输入**（工件 `correction_record.statement`）。

## 1 首跑事实与本次收口范围

| 项 | 事实 |
|---|---|
| 首跑（09-02 00:2x） | 分析段全部完成并落工件（441 KB, 四门 + 五预注册全 PASS, exit 0） |
| 中断点 | 写报告正文前令牌耗尽（1,281,246 tokens）→ 报告/收据/提交未落, 属改期纪律内（≤2） |
| 中间产物处置 | 完整工件 + 脚本**保留不清除**（与 D2 首跑零产出不同, 本次执行段绿态） |
| 本次收口动作 | 只读工件 + 复跑脚本验确定性 + 依工件数字写报告 + 收据 + 记账 + 逐路径提交 |
| 本次未做 | 未重跑分析、未改工件、未开端点、未改判据（上下文纪律: 按键段读, 不全量复读 `oracle_items`） |

## 2 前提证伪（P1–P3, 工件 `prereg_predicates`）

| 前提 | 结论 | 证据（取自工件） |
|---|---|---|
| P1 D1 工件冻结在位且含 item 级证据 | holds = true | `d1_gates_all_pass=true`, `n_items=118`, item 字段 20 项含 `type` / `class` / `canonical_keyset_identical` / `invisibility_mechanism` |
| P2 逐实例 mutation 定义可取覆盖 118 | holds = true | `n_map=118` `n_d1=118`, 注入器词库成员核对 `n_checked=118` / `n_miss=0`, 枚举 5 例入工件 |
| P3 零端点 | holds = true | `ports_touched=[]` / `model_calls=0` / 主动试连 3 项全被拦 / AST 检索 clean |

预注册经验项: E1 = true（`n_changed=8`, 全部变更带 `evidence_criterion_first_fail` + `mechanism`）;
E2 = true（`e_membership_changed=true`, 移出 7 / 加入 1 ⇒ 更正记录 + D3 敏感性注记均产出）。

## 3 Step 1 oracle 判据与独立性自证（判据冻结, 零改动）

`E(m)=1` 当且仅当三条全真, 任一不真即判有害:

- **C1 算子资格** — mutation 属预定义语义等价算子。`ocr_similar` / `date_variant` / `unit_suffix`
  按设计意图即非等价算子; `prefix_noise` 逐实例判「只加装饰而未删内容」（删除 ⇒ 该实例不算等价算子）。
- **C2 规范真值映射不变** — 独立冻结词表把表头切成 (concepts, restrictors, units) 三集合 +
  未登录原子逐字保留, 变换前后四元组逐等; 取值不变由「数据行零改动」的机器事实独立承担。
- **C3 下游目标语义不变** — 逐实例隔离（只替换本列）后该列在表内仍唯一指称同一目标,
  无同表原子序列重复、无邻列共享标准概念、取值/目标列不变。

独立性（反循环论证）: 判定路径不 import 生产匹配器 `scripts/m1_statement_parser.py`,
禁读输入 = `absorbed` / `detected_at_anchor` / `visible_by_gamma` / `absorption_tier` / `class` /
`canonical_keyset_identical` / `h_*` / `marginal_dH` / `invisibility_mechanism` / `gamma` 等
（absorption 是 outcome 不是 criterion）。自证三件: 阶段 1 产物键名扫描 `forbidden_keys_in_oracle=[]`;
运行期模块复核 `forbidden_modules_loaded=[]`; 两阶段 sha 冻结链（阶段 1 冻结
`oracle_rows_sha256 = 4b3025ef…` 先于阶段 2 读现行标签）。

词表与完整性口径: 230 表面式 / 82 概念 / 44 限定语 / 15 单位, 118 对表头扫 824 原子,
未登录 residue 27 种 75 次; 未登录原子逐字参与相等判定 ⇒ 覆盖缺口只会把实例推向 H, 不会凭空造 E。
完整性（G4）: 2479 表, keyset 与 D1 全等（118/118）, 原文/注入文本对账零失配, 非表头行改动 0 表
⇒ 取值不变是机器事实。

## 4 复核结果

### 4.1 现行分类复现（G1 PASS）

- 复现计数 H 85 / E 7 / HI 26（和 118）= D1 存储计数; 逐条比对 118/118 一致。
- 现行 E 按类型: `alias_variant 4` + `prefix_noise 3`（= 预注册）。
- 现行 E 集 7 uid 与 T2 冻结 7 uid **集合相等**（`e_equal_t2 = true`）。
- 现行分类按类型分布: H = {alias 36, date 12, mixed_lang 19, prefix 13, unit_suffix 5};
  E = {alias 4, prefix 3}; HI = {alias 7, date 5, mixed_lang 1, ocr_similar 13},
  HI 机制构成（D1 存储）= silent 15 / dilution 11。

### 4.2 实例级 oracle 判定

| 类型 | n | oracle E | oracle H |
|---|---|---|---|
| alias_variant | 47 | 1 | 46 |
| mixed_lang | 20 | 0 | 20 |
| prefix_noise | 16 | 0 | 16 |
| date_variant | 17 | 0 | 17 |
| ocr_similar | 13 | 0 | 13 |
| unit_suffix | 5 | 0 | 5 |
| **合计** | **118** | **1** | **117** |

逐类型标签一致（date_variant / mixed_lang / ocr_similar / prefix_noise / unit_suffix 五族 oracle 内一致）
是判据的**结果**而非按类型一刀切的**输入**——每条实例的三项判据证据独立入工件
（`every_row_has_three_criteria_evidence = true`, `no_type_level_blanket = true`）。

## 5 diff 全表（8 例变更, 稳定 110 例）

交叉表 oracle|现行: `E|H 1` / `H|E 7` / `H|H 84` / `H|HI 26`。**`E|E` 格为空**——
现行 7 条等价无一被 oracle 同时认可。

| # | uid8#col | 类型 | 原文 → 注入 | 现行 | oracle | 首失判据 | 机制（工件取证） |
|---|---|---|---|---|---|---|---|
| 1 | `3789d7da#1` | alias_variant | `Revenues` → `sales` | H | E | 无（三条全过） | 两侧四元组逐等, 表内唯一指称不变 ⇒ 真同义别名 |
| 2 | `50e78448#2` | prefix_noise | `US$` → `US [1]` | E | H | C1 | 序号前缀装饰化删除内容原子 `$` ⇒ 单位 USD 丢失, 该实例非等价算子 |
| 3 | `5e60c056#0` | prefix_noise | `£m` → `m【】` | E | H | C1 | 全角方括号装饰删除 `£` ⇒ 单位 GBP 丢失 |
| 4 | `b5aae4e9#0` | prefix_noise | `£m` → `m【】` | E | H | C1 | 同上（同算子同型第二实例） |
| 5 | `54c494f7#2` | alias_variant | `Accumulated Amortization` → `amort` | E | H | C2 | 限定语 ACCUMULATED 丢失, 四元组不等 |
| 6 | `e9730ea3#2` | alias_variant | `Accumulated Amortization` → `amort` | E | H | C2 | 同上 |
| 7 | `73a817fc#1` | alias_variant | `Dividends Paid(1)` → `dividend` | E | H | C2 | 限定语 PAID 丢失 |
| 8 | `e67f7bf2#4` | alias_variant | `Free cash flow (pre-spectrum)` → `cashflow` | E | H | C2 | 限定语 FREE + PRE_SPECTRUM 丢失 |

机制计数: `C1_operator` 3 / `C2_canonical_truth` 4 / `none_failed` 1。
方向计数: E→H 7 例（现行等价集全部失守）/ H→E 1 例; **HI→E 0 例**（26 条盲区注入无一在实例级应判等价）。
diff 8 例的 C3（下游唯一指称）**全部通过**（`exact_duplicate_headers=[]` / `concept_collisions=[]`）
⇒ 本批复判的危害机制集中于 C1/C2 两关, 即**字段集内容本身变化**（单位符号或限定语丢失）,
而非「注入后表头歧义」。

## 6 更正记录（不溯及）

工件 `correction_record`: `e_membership_changed = true`, `non_retroactive = true`。
原文（逐字）: 本记录是对 D1/T2 现行分类的**更正记录**, 不溯及——D1 报告与工件
（`d1_mutant_validity_audit.json` / `t2_visibility_sensitivity.json`）保持只读原文,
现行口径的计数不改写; 更正只作为未来口径与下一轮实验的输入。

- 从现行 E 集移出: 7 条（明细见 §5 第 2–8 行）。
- 加入 oracle E 集: 1 条（`3789d7da#1`）。
- 边界裁定已在判据侧冻结并披露（`criterion_provenance.boundary_rulings`）: net/gross/total/accumulated
  一律限定语不得吞进单一概念——正是 amort / dividend / cashflow 三案由 E 判 H 的机制来源;
  mixed_lang 双语复写采集合去重口径, 该族仍因限定语缺失全判 H。

## 7 D3 检出分母敏感性注记（不溯及）

工件 `d3_sensitivity_note`: D3 匹配 FPR 的有害分母按**现行分类**冻结 = 111（85 H + 26 HI）;
oracle 口径有害集 = 117、等价集 = 1 ⇒ **delta = +6**。
处置 = D3 已冻结产物不重算（`retroactive = false`）, 本注记只提供敏感性:
下一轮 FPR/召回分母须**显式声明口径**（现行 vs oracle）。

## 8 口径敏感性（严格 vs 宽松）

`tier_sensitivity`: 主口径严格（限定语属标准字段集）E = 1 / H = 117;
宽松口径 C2'（仅比概念/单位/未登录原子, 限定语缺失后果并入 C3）E = 15 / H = 103;
逐实例一致 104/118, 14 例分歧（实例清单见工件）。宽松口径**只作敏感性披露**,
不改写主判定、不用于任何下游分母。

## 9 字节级确定性复跑（本次收口的唯一执行动作）

脚本 `meta.determinism` 口径: 不落墙钟时间戳, 判据与词表全部内置冻结 ⇒ 两次实跑文件 sha256 全等。

- **为何在镜像目录跑**: 任务卡自身是脚本 sha 快照的输入之一（`SNAPSHOT_FILES` 含 card 与 D1 报告）,
  而卡片在 09-04 被加编（4170 B `85155fc7…` → 5407 B `22b78646…`）。在仓库内原地重跑会把新卡片摘要
  写进工件 ⇒ 改写首跑冻结工件, 违反「禁止改工件 / 不溯及」。故在临时镜像
  `/tmp/dr4_verify.*` 内复现: 输入全部按首跑摘要同版本布放（卡片取加编前 `790f67f` 版本, 校验 sha
  = `85155fc7…`; D1/T2 工件与 drift 三件同 sha; 脚本同 sha `dbf3ae0e…`; Python 3.12.3 = 工件 `meta.python`）。
- **结果**: 双跑 `cmp` 逐字节相同, 且两次的 sha256 = 仓库内首跑工件 sha256 =
  `7806b77b5ad46add9f0461f12c82c54b7f0328f5e3cf66ac6b8aaceefc52d6ca`（441,072 B）,
  `payload_sha256 = 47adbe6649666f864693daead98cb857ff1189545b7e28b0ba126f7cc8beb126`,
  四门全 PASS、五预注册全 holds、`recompute_ok=True`、client hits `[]`、exit 0。
- 仓库内工件与输入 sha 复核（收口前后全等）:
  `dr4_d1_reclassification_review.json` `7806b77b…` / `d1_mutant_validity_audit.json` `ef1d46ed…` /
  `t2_visibility_sensitivity.json` `eff82b0b…` / `injection_map.json` `d7612405…` /
  `tatqa_tables.json` `3e7e0568…`。

## 10 红线自查

- 零端点 ✓（`ports_touched=[]` / `model_calls=0` / budget 0 / socket 出站在导入期封死 +
  主动试连 3 项全拦 / AST 作用域检索 clean; 未启动未连接 :8004 :8006 :8008 :5050 :15432）
- D1/T2 工件与报告只读 ✓（脚本自身快照 before/after 全等 + 本次收口镜像外零写入, 仓库工件 sha 未变）
- 不溯及 ✓（只出更正记录, 未改写 D1 报告/工件计数）
- 判据冻结零改动 ✓（脚本 sha `dbf3ae0e…` 与首跑同; 未新增分析）
- 甲方标识零进入 ✓（工件 `client_identifier_zero_entered=true`, 证据只用 uid/列号与位置别名）
- 与 D3 工件域不相交 ✓（`d3_artifact_write_attempts=0`, `written_paths` 仅工件 + /tmp 阶段 1 冻结件）
- 逐路径 `git add`, 无 `-A`、无 amend ✓
- 冻结节点零触碰 ✓（`tests/test_m1_service.py` / `~/wzh/m1_samples/` / `scripts/graph/frozen_hashes.txt` 未进入本卡读写集）
- TAT-DQA 代码零修改 ✓（drift 语料与 TAT-DQA 表数据为**只读输入**, 未改任何 tat_dqa 测试/脚本）

## 11 复算命令

```bash
R=~/wzh/projects/agents_final_tech
M=$(mktemp -d /tmp/dr4_verify.XXXX)          # 镜像 = 唯一不改写冻结工件的复算路径
mkdir -p $M/research $M/logs/graph/eval $M/scripts/research $M/docs/experiments \
         $M/data/research/drift_v0/input $M/data/research/drift_v0/output
cp $R/research/paper_dr4_d1_reclassification_review.py $M/research/
cp $R/logs/graph/eval/d1_mutant_validity_audit.json $R/logs/graph/eval/t2_visibility_sensitivity.json $M/logs/graph/eval/
cp $R/scripts/research/drift_inject.py $M/scripts/research/
cp $R/data/research/drift_v0/input/tatqa_tables.json $M/data/research/drift_v0/input/
cp $R/data/research/drift_v0/output/injection_map.json $R/data/research/drift_v0/output/injected_tables.json $M/data/research/drift_v0/output/
cp $R/docs/experiments/2026-08-31_d1_audit_report.md $M/docs/experiments/
# 卡片必须取加编前版本（它是脚本 sha 快照的输入, 卡片版本决定工件字节）
git -C $R show 790f67f:docs/experiments/2026-09-01_dr4_d1_reclassification_review_card.md \
  > $M/docs/experiments/2026-09-01_dr4_d1_reclassification_review_card.md
cd $M
python3 research/paper_dr4_d1_reclassification_review.py; echo exit=$?      # run 1
sha256sum logs/graph/eval/dr4_d1_reclassification_review.json
python3 research/paper_dr4_d1_reclassification_review.py; echo exit=$?      # run 2
sha256sum logs/graph/eval/dr4_d1_reclassification_review.json               # 两次全等 = 7806b77b...
```

```bash
# 收据复算（本仓库路径）
venv/bin/python scripts/graph/hooks/summary_recompute_guard.py check \
  docs/experiments/2026-09-04_dr4_d1_reclassification_review_report.md
```

<!-- SUMMARY-GUARD
artifact: logs/graph/eval/dr4_d1_reclassification_review.json
sha256: 7806b77b5ad46add9f0461f12c82c54b7f0328f5e3cf66ac6b8aaceefc52d6ca
claims:
  meta.reviewed_instances = 118
  payload_sha256 = 47adbe6649666f864693daead98cb857ff1189545b7e28b0ba126f7cc8beb126
  gates.all_pass = true
  prereg_predicates.P1 = true
  prereg_predicates.P3 = true
  prereg_predicates.E2 = true
  payload.oracle_counts.total = 118
  payload.oracle_counts.E = 1
  payload.oracle_counts.H = 117
  payload.oracle_counts.by_type.alias_variant.E = 1
  payload.oracle_counts.by_type.ocr_similar.H = 13
  payload.oracle_counts.by_type.prefix_noise.E = 0
  payload.gates.G1_reproduce_current.counts_reproduced.H = 85
  payload.gates.G1_reproduce_current.counts_reproduced.E = 7
  payload.gates.G1_reproduce_current.counts_reproduced.HI = 26
  payload.gates.G1_reproduce_current.per_item_reproduction_matches_stored_class = 118
  payload.gates.G1_reproduce_current.cross_tab_oracle_vs_current["H|E"] = 7
  payload.gates.G1_reproduce_current.cross_tab_oracle_vs_current["E|H"] = 1
  payload.gates.G1_reproduce_current.cross_tab_oracle_vs_current["H|H"] = 84
  payload.gates.G1_reproduce_current.cross_tab_oracle_vs_current["H|HI"] = 26
  payload.current_classification.e_equal_t2 = true
  payload.diff.n_changed = 8
  payload.diff.n_stable = 110
  payload.diff.current_e_to_oracle_h[0].uid8 = "50e78448"
  payload.diff.current_harmful_to_oracle_e[0].uid8 = "3789d7da"
  payload.diff.current_harmful_to_oracle_e[0].current_class = "H"
  payload.correction_record.e_membership_changed = true
  payload.correction_record.non_retroactive = true
  payload.correction_record.mechanism_summary["C1_operator"] = 3
  payload.correction_record.mechanism_summary["C2_canonical_truth"] = 4
  payload.correction_record.mechanism_summary["none_failed"] = 1
  payload.d3_sensitivity_note.d3_frozen_harmful_denominator = 111
  payload.d3_sensitivity_note.oracle_harmful_denominator = 117
  payload.d3_sensitivity_note.delta = 6
  payload.d3_sensitivity_note.retroactive = false
  payload.tier_sensitivity.primary_strict.E = 1
  payload.tier_sensitivity.sensitivity_lenient.E = 15
  payload.tier_sensitivity.agreement_with_primary = 104
  payload.gates.G4_input_integrity.alignment_118 = true
  payload.integrity.n_tables = 2479
  payload.integrity.value_invariance_is_machine_fact = true
  payload.integrity.mutation_definitions.n_miss = 0
  payload.gates.G3_independence_and_evidence.oracle_rows_sha256 = 4b3025efd7138c2ab36c7b4c9fbab72bd178e41fd36964e8ea13ad6533ce9304
  payload.gates.G3_independence_and_evidence.oracle_independence.forbidden_keys_in_oracle = []
  payload.gates.G3_independence_and_evidence.oracle_independence.forbidden_modules_loaded = []
  payload.lexicon.n_surfaces = 230
  payload.lexicon.n_atoms_scanned_118_pairs = 824
  payload.lexicon.n_distinct_residue_atoms = 27
  payload.zero_endpoint.ports_touched = []
  payload.zero_endpoint.model_calls = 0
  payload.redline_self_check.client_identifier_zero_entered = true
  payload.redline_self_check.d3_artifact_write_attempts = 0
  payload.redline_self_check.frozen_artifacts_readonly_sha_equal_before_after = true
END-SUMMARY-GUARD -->
