# D1 突变体有效性审计报告（零端点）

> 卡号: TASK-20260831-01 | 执行者: Loop A（GB10）| 执行日期: 2026-08-31
> 判据冻结: `docs/experiments/2026-08-31_d1_mutant_validity_audit_design.md`（§2 三分类定义 / §3 预注册 P1-P6 / §5 OCR 论证骨架）
> 任务卡: `docs/experiments/2026-08-31_d1_task_card.md` | 风险: 低（零端点, 冻结工件只读）
> 工件: `logs/graph/eval/d1_mutant_validity_audit.json` | 脚本: `research/paper_d1_mutant_validity_audit.py`
> 本报告只收集与判定工件内门; 主张层（论文含义）判定归主线程后续 autopsy（收集与判定分离）。

## 1. 执行结果

前置证伪四件全过（注入件 sha 与 W2 登记逐字一致 / T2 `n_equivalent == 7` / 突变体证据源在位 / 护栏无 http 客户端导入）; 审计脚本实跑 **exit 0**, **G1-G7 全 PASS**, `all_pass = true`; 预注册 **P1-P6 逐条为真, 零改判、零 BLOCKED**。118 注入三分类 = **85/7/26**（H/E/HI, 合计 118, 覆盖 95 张表）; 9 检查点突变体 = **MO 8 / MU 1**（MU 唯一成员 `M7_nf_fail_3`, 原样保留）。全部数字可从工件复算（§10）。

工件 `payload_sha256 = d7d0e0e0a34370b513655c6c65996332a7ec4c3828854886f94b4b776b7f28b3`（跨两次实跑逐字节稳定; 摘要在 payload 收口后计算, 承 W2 f1bf00b 教训）。

## 2. 三分类底表（118 注入, 每注入恰好一类）

判据（设计稿 §2, 冻结不溯及）: **H** = 锚点 γ=0.2 检出; **E** = 被吸收 且 类型 ∈ {alias_variant, mixed_lang, prefix_noise} 且 映射标准字段集与原表一致; **HI** = 其余锚点未检出者。

| 类型 | 注入数 | H 有害-可见 | E 等价 | HI 有害-不可见 |
|---|---|---|---|---|
| alias_variant | 47 | 36 | 4 | 7 |
| date_variant | 17 | 12 | 0 | 5 |
| mixed_lang | 20 | 19 | 0 | 1 |
| ocr_similar | 13 | 0 | 0 | 13 |
| prefix_noise | 16 | 13 | 3 | 0 |
| unit_suffix | 5 | 5 | 0 | 0 |
| **合计** | **118** | **85** | **7** | **26** |

互斥性与完备性实检: H ∪ E ∪ HI = 118 且两两不相交; E 的 7 条 **absorbed 全为 true 且 keyset 全一致**（即 §2 三条件逐条成立, 非仅取 keyset 代理）。

### 2.1 「被吸收」两口径同时入账（无静默取舍）

设计稿 §2 的 HI 用词「被吸收」按任务卡 P2 的冻结推导口径执行 = **锚点未检出**（118−85=33, 33−7=26）。严格映射吸收口径并行登记:

- `absorbed_strict_total` = **22**（注入表头被匹配接回原标准字段）= E 7 + HI 吸收子集 15; 恒有 `absorbed_and_detected_at_anchor` = 0（吸收 ⇒ 字段集不变 ⇒ 无失配信号）。
- HI 的 26 条按机制分层:

| 类型 | 机制 | 条数 |
|---|---|---|
| alias_variant | threshold_dilution | 7 |
| date_variant | absorption_silent | 2 |
| date_variant | threshold_dilution | 3 |
| mixed_lang | threshold_dilution | 1 |
| ocr_similar | absorption_silent | 13 |
| **合计** | — | **26** |

（余 11 条非吸收, 而是宽表单注入边际降幅 dH 低于锚点阈值的**阈值稀释**——同样属「协议无信号」, 但机制不同, 故分列不入吸收叙事。）

## 3. 等价集复现（P1 / G1）

D1 从冻结原始件独立重推的等价集与 T2 冻结 `e2_2_equivalence_correction.equivalent_list` **集合差 = ∅**（7 uid: alias_variant 4 + prefix_noise 3 + mixed_lang 0, 与预注册构成一致）。

| # | uid(前8) | col | 类型 | 原表头 → 注入表头 |
|---|---|---|---|---|---|
| 1 | 50e78448 | 2 | prefix_noise | `US$` → `US [1]` |
| 2 | 54c494f7 | 2 | alias_variant | `Accumulated Amortization` → `amort` |
| 3 | 5e60c056 | 0 | prefix_noise | `£m` → `m【】` |
| 4 | 73a817fc | 1 | alias_variant | `Dividends Paid(1)` → `dividend` |
| 5 | b5aae4e9 | 0 | prefix_noise | `£m` → `m【】` |
| 6 | e67f7bf2 | 4 | alias_variant | `Free cash flow (pre-spectrum)` → `cashflow` |
| 7 | e9730ea3 | 2 | alias_variant | `Accumulated Amortization` → `amort` |

`keyset_identical_total` = 19（字段集一致的注入总数）, 其中仅 7 条落在三个合法写法类型内 → 另 12 条按 §2 判 HI（类型不属合法写法集, 不因字段集巧合一致而升格为等价）。

## 4. 等价注入的全网格不可见性（P3 / G3）

| 类别 | n | γ=0.2 可见 | γ=0.3 可见 | γ=0.5 可见 | γ=0.7 可见 | γ=0.9 可见 |
|---|---|---|---|---|---|---|
| H | 85 | 85 | 45 | 29 | 13 | 13 |
| E | 7 | 0 | 0 | 0 | 0 | 0 |
| HI | 26 | 0 | 0 | 0 | 0 | 0 |

E 行在 {0.2, 0.3, 0.5, 0.7, 0.9} 全部 **0 可见**（违例列表空）; 同时 HI 行亦为全 0——即「锚点未检出」在本网格上是 γ-不变的, 等价类的不可见性不是阈值调出来的产物。H 行随 γ 单调收缩（85→45→29→13→13）属预期的边际降幅量化地板效应, 与 C1 主张无关。

## 5. OCR 形近: 有害且不可见（P5 / G5）

13 条 `ocr_similar` 注入 **13/13 全属 HI**, 且映射目标 100% 不变（`all_mapping_targets_unchanged = true`）, 吸收档位全为 tier 1（编辑距离 ≤1）——即设计稿 §5 论证骨架的三前提（形近串破坏字面 / 匹配层静默接回原字段 / 协议零信号）逐条有数据承载。工件内存全部 13 条三元组, 报告引用前 5 条:

| 原表头 (original) | 注入表头 (injected) | 映射目标 | 目标不变 | 吸收档位 |
|---|---|---|---|---|
| `Number of equity shares` | `Number of equty shares` | `Number of equity shares` | True | tier 1 |
| `Dividend per Share` | `divdend per Share` | `Dividend per Share` | True | tier 1 |
| `Vessels and capitalized dry-docking` | `Vessels and capitaiized dry-docking` | `Vessels and capitalized dry-docking` | True | tier 1 |
| `Other plant and operating equipment` | `Other plant and operat1ng equipment` | `Other plant and operating equipment` | True | tier 1 |
| `Operating Leases` | `operat1ng Leases` | `Operating Leases` | True | tier 1 |

与等价类的边界（§5 冻结判据）: alias/prefix_noise 被吸收 = **归一化**（合法写法, 系统行为不变 → 鲁棒, 7 例）; ocr_similar 被吸收 = **把误读静默合法化**（破坏语义而无信号 → 有害-不可见, 13 例）。判据 = 该类型被注入的设计意图, 重分类须用户裁定, 本卡未动。

## 6. 检查点突变体 MO/MU（P4 / G4）

判据（§2）: **MO** = 缺陷在该叶 item 级证据的承载字段上有移动（契约叶可读字段 / judge 叶可见证据片段）, 判别协议原则上可检出; **MU** = 缺陷只落在派生标签 / 预聚合量, item 级承载字段零移动 → 对 item 级判分结构性不可见。突变体在 /tmp 副本上由冻结 mutator 重建（活工件零改动）, 逐叶对照 control 与 mutant 的 item 级证据视图差分。

| 突变体 | 树 | 目标叶 | 分类 | item 级承载字段（证据路径） | 承载字段移动 item 数 | 仅派生标签移动 item 数 | 判分分离度 | 映射分离度 |
|---|---|---|---|---|---|---|---|
| M1_m1_rows_fail | parse | parse.doc.ok, parse.field.hit_rate, parse.reconcile.equations, parse.table.regression | **MO** | `parse.doc.ok`→`status`; `parse.field.hit_rate`→`values_checked`,`values_mismatched`; `parse.reconcile.equations`→`status`; `parse.table.regression`→`status` | 8 | 0 | 1.8523 | 2.6428 |
| M2_exact_numeric_fail | qa | qa.numeric.exact | **MO** | `qa.numeric.exact`→`contract_verdict` | 7 | 0 | 0.6250 | 0.6250 |
| M3_source_required_fail | qa | qa.retrieval.source_required | **MO** | `qa.retrieval.source_required`→`contract_verdict` | 15 | 0 | 0.8333 | 0.8333 |
| M4_refusal_expected_fail | qa | qa.refusal.deterministic | **MO** | `qa.refusal.deterministic`→`contract_verdict` | 1 | 0 | 0.5556 | 0.5556 |
| M5_judge_faithfulness_degrade | qa | qa.faithfulness.judge | **MO** | `qa.faithfulness.judge`→`verdict_on_0_5` | 16 | 0 | 0.6250 | 0.7350 |
| M6_judge_citation_degrade | qa | qa.citation.judge | **MO** | `qa.citation.judge`→`verdict_on_0_5` | 16 | 0 | 0.5000 | 0.5833 |
| M7_nf_fail_3 | qa | qa.numeric.number_grounding | **MU** | —（无承载字段） | 0 | 3 | 0.0000 | 0.2083 |
| M8_judge_artifact_missing | qa | qa.citation.judge, qa.faithfulness.judge, qa.refusal.judge | **MO** | `qa.citation.judge`→`verdict_on_0_5`; `qa.faithfulness.judge`→`verdict_on_0_5`; `qa.refusal.judge`→`verdict_on_0_5` | 48 | 0 | 2.0972 | 1.1656 |
| M9_m1_all_rows_fail | parse | parse.doc.ok, parse.field.hit_rate, parse.reconcile.equations, parse.table.regression | **MO** | `parse.doc.ok`→`status`; `parse.field.hit_rate`→`values_checked`,`values_mismatched`; `parse.reconcile.equations`→`status`; `parse.table.regression`→`status` | 48 | 0 | 4.6591 | 3.9248 |

- **MU = {M7_nf_fail_3}（1 个, 与预注册完全一致）**: 原子路径差分显示 4 处变化全在 `number_faithfulness_report.json` 的 `n_fail`（聚合计数）与 `results[*].pass`（派生布尔标签）; 目标叶 `qa.numeric.number_grounding` 的承载字段 `number_claims` / `ungrounded` **9 个 item 零移动**, 仅 `grounding_verdict` 派生标签移动 3 个 → 判分分离度 **0.0000** 而确定性映射分离度 0.2083（有信号但被派生层吞掉, 未达 item 级证据层）。
- **MO 8 个**: 每个都给出逐叶 `leaf → carrier_fields` 证据路径（G4 的 `mo_missing_evidence_path` = 空列表）, 无批量改判。
- 计数口径: 「承载字段移动 item 数」= 各目标叶 `n_primary_items_moved` 之和（跨叶求和, 故 M1/M9 的 parse 树可为 4 叶合计）; `M8_judge_artifact_missing` 因工件被删（control 16 item → mutant 0 item）按整叶证据缺失计入移动, 与 M5/M6 的逐 item 改分不同, 引用时注意区分。
- 三个数据源方向一致: item 级证据视图（本卡重推）/ E1.5 判分矩阵（`t4_pso_fair_comparison.json:payload.e1_5`）/ 确定性映射矩阵（`checkpoint_discrimination_report.json:mutants`）。
- **M7 保留声明（J2 附加条件）**: 原样保留 `logs/graph/eval/number_faithfulness_report.json`, 不重设计、不替换、不改判其既有结论; D1 仅登记其不可观测性归因于「缺陷落在预聚合量」。工件 `m7_retention.preserved_verbatim = true`, `redesigned_or_replaced = false`。

## 7. 门判定

| 门 | 判据 | 判定 |
|---|---|---|
| G1 | 等价集 == T2 冻结 7 uid（P1） | **PASS** |
| G2 | γ=0.2 三分类计数 85/7/26（P2） | **PASS** |
| G3 | 等价注入全 γ 网格不可见（P3） | **PASS** |
| G4 | 突变体分类 == 预注册 + 证据路径全在（P4） | **PASS** |
| G5 | OCR 13 全 HI + 示例三元组在位（P5） | **PASS** |
| G6 | 零端点 + 只读自证（P6） | **PASS** |
| G7 | 工件回读复算摘要一致 | **PASS** |

`gates.all_pass = true`。

## 8. 预注册预测逐条判定（对照设计稿 §3, 不溯及）

| 预测 | 冻结预期 | 实测 | 判定 |
|---|---|---|---|
| P1 等价集复现 | == T2 冻结 7 uid, 集合差 ∅ | 7 = 7, 差集双向空 | **成立** |
| P2 γ=0.2 计数 | H 85 / E 7 / HI 26, 总 118 | 85 / 7 / 26 / 118; 逐类 36/12/19/0/13/5 同 T2 冻结 | **成立** |
| P3 等价 ⇒ 全网格不可见 | 7 条 × 5 γ 全不可见 | 0 违例 | **成立** |
| P4 突变体分类 | MU = {M7_nf_fail_3}, MO = 其余 8, 证据路径全在 | MU 1 / MO 8, 缺路径列表空 | **成立** |
| P5 OCR 有害论证 | 13 全 ∈ HI + ≥3 条三元组 | 13/13 HI, 13 条三元组, 目标全不变 | **成立** |
| P6 零端点自证 | ports_touched = [], model_calls = 0, 预算计数器 0 | [] / 0 / 0, 试连三探针全拦 | **成立** |

零项改判、零项溯及修订; 无 BLOCKED 条目。

## 9. 红线自查

- **零端点**: `ports_touched = []`, `model_calls = 0`, 预算计数器恒 0; socket 层封死出站并**主动试连自证**（create_connection / getaddrinfo / socket.connect 三探针全 `blocked:RuntimeError`）——护栏非空转。
- **扫描作用域分层（本卡唯一方法学偏离, 如实入账）**: G6 硬门按任务卡 P4 的证伪口径改为 **AST 级 import/call 检索**（http 客户端根模块 + subprocess）, 作用域 = 本窗 research 脚本 + D1 导入的聚合脚本, 与 T2 冻结 `SCAN_MANIFEST` 同构; 逐行字面量扫描降为**披露层**（命中全是中文注释/文档字符串里「不调用 :8004/:5050/:8006」的否定式声明）。生产匹配器 `scripts/m1_statement_parser.py` 自带 OCR/VLM helper, 列作用域外并逐条披露其 AST 命中; D1「只调用其纯文本匹配 API」由三重自证: socket 封死 + 试连全拦 + `MATCHER_APIS_CALLED` 五项 `hasattr` 断言全 true。检索器另做正/负控: 三个 D1 作用域件零命中, 已知含 `urlopen`/`subprocess` 的生产件与造假的违规样例均命中（不放水）。
- **冻结工件只读**: 6 件输入摘要与 W2 登记逐字一致; 活工件与冻结注入件**前后 sha256 全等**（`live_and_frozen_artifacts_untouched = true`）; 突变体副本全落 `/tmp/d1_mutant_scratch`（仓库外）。
- **M7 原样保留零替代**（J2）: 见 §6 声明。
- **甲方标识零进入**: 工件全文经禁用词扫荡（CLIENT_TOKENS + 问题 id 前缀）零命中, 报告同口径; 突变体证据只用位置别名 `row_NN` / `item_NN`, 名称字段永不读取; 注入 uid 为 UUID。
- **判据冻结不溯及**: §2/§3 原样执行, 未因结果调整任何阈值或类型集。
- git 纪律: 逐路径 add, 无 `-A`、无 `--amend`。

## 10. 复算

```bash
python3 research/paper_d1_mutant_validity_audit.py   # exit 0 = G1-G7 全过; 重写工件
```

<!-- SUMMARY-GUARD
artifact: logs/graph/eval/d1_mutant_validity_audit.json
sha256: ef1d46ed9ca1ae3832f35d2796b3a51be34c912897d68b40d73c9413d8651a2b
claims:
  payload.counts.H = 85
  payload.counts.E = 7
  payload.counts.HI = 26
  payload.counts.total = 118
  payload.counts.n_tables = 95
  payload.counts.absorbed_strict_total = 22
  payload.counts.undetected_at_anchor_total = 33
  payload.counts.hi_by_mechanism.absorption_silent = 15
  payload.counts.hi_by_mechanism.threshold_dilution = 11
  payload.counts.keyset_identical_total = 19
  payload.counts.absorbed_and_detected_at_anchor = 0
  payload.equivalence.n_equivalent = 7
  payload.ocr_absorption_examples.n_ocr = 13
  payload.ocr_absorption_examples.n_ocr_HI = 13
  payload.ocr_absorption_examples.all_targets_unchanged = true
  payload.mutant_counts.MO = 8
  payload.mutant_counts.MU = 1
  payload.mutant_counts.mu_ids[0] = M7_nf_fail_3
  payload.m7_retention.preserved_verbatim = true
  payload.m7_retention.redesigned_or_replaced = false
  payload.redline_self_check.live_and_frozen_artifacts_untouched = true
  payload.redline_self_check.client_identifier_zero_entered = true
  payload.zero_endpoint.model_calls = 0
  payload.zero_endpoint.budget_counter = 0
  payload.gate_details.G6_zero_endpoint_and_readonly_self_proof.pass = true
  gates.all_pass = true
  payload_sha256 = d7d0e0e0a34370b513655c6c65996332a7ec4c3828854886f94b4b776b7f28b3
END-SUMMARY-GUARD -->
