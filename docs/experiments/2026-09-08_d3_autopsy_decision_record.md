---
status: 活跃（autopsy 决策记录; 判定请求 ×2 已裁定 09-09 = ① c / ② c, 裁定注记见 §5; D4 拟卡另批）
date: 2026-09-08
card: docs/experiments/2026-09-01_d3_matched_specificity_card.md
card_id: TASK-20260901-D3
window: D3 阶段 B judge 重打分窗（2026-09-06, Loop A@GB10, 仅 :8004, 28 冻结调用）
target_report: docs/experiments/2026-09-06_d3_matched_fpr_stage_b.md
target_artifact: logs/graph/eval/d3_matched_fpr_stage_b.json
closeout_record: docs/experiments/2026-09-07_d3_stage_b_closeout.md
recompute_artifact: logs/graph/eval/d3_autopsy_recompute.json
recompute_script: research/paper_d3_autopsy_recompute.py
phase: autopsy
endpoint_calls: 0
precedent: docs/experiments/2026-09-01_d2_autopsy_decision_record.md
---

# D3 Autopsy 决策记录

> 执行: Loop D 2026-09-08（本地, **零端点 / 零重跑 / 零新增 judge 调用**）
> 依据: 用户裁定 09-07——决策 6=A（一次到底, 单轮交付分析 + 判定请求）/ 7=B（A4/A5 只排期不动手）/ 8=A（硬规则 3 口径澄清）
> 治理: `docs/governance/2026-09-07_execution_plane_boundary.md`——autopsy 属本地控制/审计面, EFT 三问全落本地侧（输入 = 已落盘既有事实; 输出 = 既有事实的确定性函数; 标签 = `phase: autopsy` + `endpoint_calls: 0`）
> 纪律: 判据 / oracle / 阈值 / 协议 / H·E·HI 底表 / S-2 分母 111 **零改动且不溯及**; 边界例一个不删; **不选 judge 或 DR4 任一方为胜者**; 判定请求 ≤2 件, 只呈交不裁定

## 0 一页结论

三条证据线（D1 类型级标签 / DR4 实例级 oracle / 阶段 B judge）的分歧**不是测量噪声, 而是判据差异**, 且该差异可分解为两条正交轴:

- **粒度轴（类型级 → 实例级）**: D1 的 7 例 E 在 DR4 实例级 oracle 下 **0 例存续**（7/7 全翻转）; oracle 唯一的 E 例（`3789d7da#1`）此前标签是 H ⇒ 等价类**整体换血**（收据 A-18, L3）。
- **判据种类轴（规范形式 → 读者指代）**: DR4 的 C1/C2 问「规范形式与规范真值是否存续」, judge 问「读者能否恢复同一指代」。8 行对照里 5 例 disagree 全部落在这条轴上（A-07 / A-10, L3）。

方向性触发 ②（14/21 equivalent ≥ 11）**完全由 ocr_similar 一族承载**: 14 例 equivalent 中 13 例是 ocr_similar（该族 13/13 全判 equivalent）, 非 ocr_similar 子集 8 例中仅 1 例 equivalent（A-05, L3）。该 13 例的编辑形态学首次被量化: **lowercase Levenshtein 距离恒为 1**, token 数 13/13 保持, 受影响 token 恰为 1 个（A-06, L3）。

**方向性新发现（§7 即时上报）**: 这 13 例的「有害」归属在三条线上**都不是实例级经验发现**——D1 侧唯一不满足的 E 条件是**类型白名单**（其余实例级条件 13/13 满足, A-14）; DR4 侧 C1 的 `check` 字段 13/13 = `family_design_intent`（族级规定）, C2 13/13 fail 但其中 **4 例无任何概念丢失**、仅因新增未登录 residue 原子而 fail, 且 13/13 `value_invariance.holds = true`（A-12 / A-13）。DR4 自己在 `payload.lexicon.residue_note` 已披露该偏置是**单向**的: 「词表覆盖缺口只会把实例推向 H, 不会凭空造 E」。

因此本记录对三个核心问题的回答是**分层的**（§2）: 标签确为判据相对（可写成机制主张）, 但「哪条判据正确」不可裁（必须写成 claim boundary）。判定请求 2 件见 §4。

## 1 证据基线与复算收据

| 项 | 值 |
|---|---|
| 复算脚本 | `research/paper_d3_autopsy_recompute.py`（零 HTTP 客户端 import / 无 subprocess / 无 ssh / socket 层封死守卫） |
| 收据 | `logs/graph/eval/d3_autopsy_recompute.json`——`meta.phase = autopsy`, `meta.endpoint_calls = 0`, `meta.socket_attempts = []`（治理件硬规则 1 + 2 自证） |
| 收据 sha256 | `2b62bf317635a91b6ad113d0d3024aa8652bc444eff42d569222c891ae0c522f`（纯 LF 件, raw == lf, 23 881 B） |
| payload_sha256 | `d9827807f2d29e728a011099e47442796d7ca35a200967fc2a17b58c0a16f4aa` |
| 检查项 | **18/18 全 PASS**（证据级别: 独立复算 17 / 字段存在 1） |
| 输入四件 | `d3_matched_fpr_stage_b.json` / `d1_mutant_validity_audit.json` / `dr4_d1_reclassification_review.json` / `d3_stage_b_call_ledger.jsonl`（62 行）; 双口径 sha 已入 `meta.reproduce.expected_input_sha256{,_lf}`（F-0907-2 对策） |
| 复现命令 | Windows `python research/paper_d3_autopsy_recompute.py`; GB10 `cd ~/wzh/projects/agents_final_tech && venv/bin/python research/paper_d3_autopsy_recompute.py`——**已内置于收据 `meta.reproduce`**（硬规则 3 落地首例, 见 §5 决策 8A） |

证据级别口径沿用收口报告: **L1 字段存在 / L2 存值一致 / L3 独立复算 / L4 运行证据**。本记录所有论文级数字均为 **L3**（收据可离线复算）或 **L4**（阶段 B 窗运行态工件）。

## 2 七层分层分析

> 写法约束（用户 09-07 强制）: 逐层标注, **不得把 Observation 直接写成 Mechanism conclusion**; 明确区分客观事实与解释; judge 不是 ground truth, DR4 oracle 也不自动是 ground truth; disagreement 本身可以是研究结果。

### FA-1 触发 ② 的 14/21 完全由 ocr_similar 一族承载

- **Observation**: J-N1 的 21 例中 14 例判 equivalent; 这 14 例里 13 例属 ocr_similar 族（该族 13/13 全判 equivalent）, 余下 8 例（date_variant 2 + threshold_dilution 6）中只有 1 例判 equivalent。
- **Evidence**（L3）: 收据 A-03 / A-04 / A-05。字段路径 = 阶段 B `payload.per_case[].verdict` × D1 `payload.injections[].type` 与 `.invisibility_mechanism`（28 例按 `(uid8, col)` 1:1 join, original/injected 逐字节相等, A-02）。分层构成 = absorption_silent 15（ocr_similar 13 + date_variant 2）+ threshold_dilution 6; 交叉表 = ocr_similar 13 eq / 0 mc、date_variant 1 eq / 1 mc、dilution 0 eq / 6 mc。
- **Interpretation**: 预注册阈值「≥11/21 equivalent」的命中, 不是「零信号有害集多数无害」的均匀现象, 而是**单一扰动族的整族行为**跨过了为全集设定的阈值。族内一致（13/13）+ 族外几乎全反（1/8）⇒ 该触发携带的信息量集中在族身份上, 不在比例上。
- **Mechanism hypothesis**: judge 对「词形被扰动但指代完全可恢复」的输入系统性判 equivalent; 该族在 21 例中占 13/21 = 61.9%, 因此**仅凭族内一致性即可单独越过 11/21 阈值**, 无需其他族配合。
- **Paper claim（最多能写到）**: 触发 ② 的命中具有**族条件性（family-conditional）**。论文引用 14/21 时必须同时给出 13/13（ocr_similar）与 1/8（非 ocr_similar）的分层, **不得**把它写成「零信号有害集多数被判无害」的总体陈述。
- **Boundary（不能推出）**: 不能推出「零信号有害集整体无害」; 不能推出 judge 对其他族同样宽松（dilution 6/6 判有害, 方向相反）; 不能据此改 S-2 分母 111（本轮冻结, 归 §4 判定请求 ①）; 不能推出阈值 11/21 设错了——它是预注册值, 判据冻结不溯及。
- **Next experiment（如何验证机制）**: D4 把**扰动族**写成预注册分层变量, 触发判据改为族级（每族独立阈值 + 族内 n 下限）, 并对非 ocr_similar 族扩样, 检验「族内一致 / 族外相反」的结构是否稳定复现。

### FA-2 「纯字符级拼写扰动」首次获得量化定义: 编辑距离恒为 1

- **Observation**: 13 例 ocr_similar 的 lowercase Levenshtein 距离**全部 = 1**; 长度变化 = 0（8 例, 单字符替换）或 −1（5 例, 单字符删除）; token 数 13/13 保持不变; 受影响 token 13/13 恰为 1 个。
- **Evidence**（L3）: 收据 A-06, `lev_distribution = {1: 13}`, `len_delta_distribution = {-1: 5, 0: 8}`, `ocr_token_count_preserved = 13`, `ocr_single_token_touched = 13`。扰动原子实测 9 种（A-13）: `equty` `divdend` `capitai` `capitaiized` `liabilitie` `operat` `ng` `1` `5`。
- **Interpretation**: 此前「纯字符级拼写扰动」只是散文描述（收口报告 §3 / THREADS #D3-STAGE-B-CLOSEOUT）, 现在有可复算的形态学定义 = **单 token · 编辑距离 1 · token 数不变**。这把该族从「看起来像错字」升级为「有量化边界的扰动族」。
- **Mechanism hypothesis**: 编辑距离 1 的词形扰动在人类读者处指代完全可恢复（judge rationale 13/13 为「拼写错误, 语义不变 / 语义指向相同」, L1）, 但在**有限词表**处必然失配——失配与语义无关, 只与词表覆盖有关。
- **Paper claim（最多能写到）**: 可以把「字符级扰动」作为一个**有量化定义的扰动族**写进论文（单 token、编辑距离 1、token 数守恒）, 并陈述: 该族在 reader 判据与 lexicon 判据下结论相反, 且两侧各自的判据都是明确、可复现的。
- **Boundary（不能推出）**: 编辑距离 1 **不是**语义等价的充分条件——本窗未测「编辑距离 1 但改变语义」的反例（如 `m` → `km`、`2019` → `2018`）, 故不得推广为「所有编辑距离 1 的扰动都无害」; 也不得反向推广为「编辑距离大即有害」。
- **Next experiment**: D4 增设**编辑距离 1 但语义改变**的对照族（单位 / 年份 / 正负号类单字符替换）, 检验 judge 与 lexicon 两条判据是否在该对照族上分离。若分离, FA-2 的机制解释获得证伪性支持; 若 judge 也判 equivalent, 则暴露 judge 自身的宽松偏置。**此对照族是 FA-2 从解释升为机制主张的唯一路径。**

### FA-3 13 例 ocr_similar 的「有害」归属在三条线上都不是实例级经验发现

- **Observation**: ① D1 侧——13/13 满足 E 定义的**全部实例级条件**（`absorbed = true`、`mapping_target == original`、`marginal_dH = 0.0`、`detected_at_anchor = false`、`canonical_keyset_identical` 12/13）, 唯一不满足的是**类型白名单**（`ocr_similar ∉ {alias_variant, mixed_lang, prefix_noise}`）⇒ class = HI。② DR4 侧——C1 的 `check` 字段 13/13 = `family_design_intent` 且 `pass = false`（族级规定, 非实例观测）; C2 13/13 fail, 但其中 **4 例 `truth_lost.concepts` 为空**, 仅因 `truth_added.residue` 非空而 fail; 13/13 `value_invariance.holds = true` 且 `data_rows_identical = true`; C3 8 pass / 5 fail, 5 例 fail 全部归因「邻列共享概念」（如共享泛概念 `COUNT`）。③ judge 侧——13/13 equivalent。
- **Evidence**（L3 + L1）: 收据 A-12 / A-13 / A-14 / A-15。字段路径 = D1 `payload.equivalence.definition`（E 定义原文含类型白名单）、`payload.injections[].{absorbed, mapping_target, marginal_dH, detected_at_anchor, canonical_keyset_identical, class}`; DR4 `payload.criterion_provenance.c1_families.non_equivalent_by_design.ocr_similar`（原文: 「误读产物（形近错认）, 设计意图即破坏词形」）、`payload.oracle_items[].C1_operator.check`、`.C2_canonical_truth.{truth_lost, truth_added, value_invariance}`、`.C3_downstream.concept_collisions`、`payload.lexicon.residue_note`。
- **Interpretation**: 两条判「有害」的线, 其决定性理由分别是**规定性的**（类型白名单 / 族设计意图）与**方法学的**（未登录原子逐字纳入相等性判定）, 都**不是**「这一列的所指发生了变化」的实例级观测。唯一逐例审视所指的一条线（judge）给出相反结论。DR4 的 `residue_note` 已自我披露该偏置的方向性: 「词表覆盖缺口只会把实例推向 H, 不会凭空造 E」——即词表方法在形近误读上**结构性地不可能**产出 E。
- **Mechanism hypothesis**: 「有害」在本族上是**定义与词表覆盖的函数**, 不是实例语义的函数。因此「评估器对该族全盲」与「该族有害」是两个独立命题: 前者是可直接观测的评估器属性, 后者依赖等价类定义。
- **Paper claim（最多能写到）**: 在冻结判据下, ocr_similar 族的有害归属由**类型白名单 + 词表覆盖**决定, 而非由实例级语义证据决定。据此论文必须把两件事分写: **(a) 经验事实**——评估器对字符级表头扰动在 γ ∈ [0.2, 0.9] 全域零可见（0/13, `visible_by_gamma` 全 false, L3）、`anchor_detected_by_type.ocr_similar = 0`（L2）; **(b) 依赖定义的解释**——该盲区是否构成「漏检」取决于等价类定义。**只有 (a) 可写成主张, (b) 必须写成边界。**
- **Boundary（不能推出）**: 不能推出 judge 正确、DR4 错误（DR4 已披露自身偏置方向, 属诚实入账, 不是缺陷隐瞒）; 不能推出 13 例应从有害集移出（归 §4 判定请求 ①, 由用户裁定）; 不能推出词表方法整体无效——它对 alias_variant / unit_suffix 族仍给出实例级区分（DR4 diff 中 3×C1 + 4×C2 的逐例理由即为其区分力证据）; 不能推出 C3 的 5 例 fail 无意义（邻列概念冲突是独立的下游风险, 与词表覆盖无关）。
- **Next experiment**: D4 预注册一条**词表覆盖敏感性次级臂**——把 9 个 residue 原子登记入词表后重算 C2, 报告 13 例中有多少在覆盖修复后仍判 H。该臂结果**只用于边界披露, 不回改 D1/DR4 任何标签**（判据冻结不溯及）, 且必须与主判据分列呈现。零端点, 可在 D4 执行前作为本地旁证先行。

### FA-4 J-N2 的分歧不沿 D1 类型切, 而沿「指代可恢复性」切

- **Observation**: J-N2 的 7 例中, `alias_variant` 4 例 = 3 equivalent / 1 meaning_changed, `prefix_noise` 3 例 = 1 equivalent / 2 meaning_changed——**两个 D1 类型都不是判定同质的**。逐例: `Accumulated Amortization`→`amort` ×2 = equivalent; `Dividends Paid(1)`→`dividend` = equivalent; `Free cash flow (pre-spectrum)`→`cashflow` = meaning_changed; `US$`→`US [1]` = equivalent; `£m`→`m【】` ×2 = meaning_changed。
- **Evidence**（L3 + L1）: 收据 A-07（`by_type`）; judge rationale 原文（`payload.per_case[].rationale`, L1）: 「amort 是 Accumulated Amortization 的常见缩写, 语义一致」/「删除货币单位 £, 语义改变」/「US$ 与 US 均为美元符号或缩写变体, 指代相同币种字段」/「修改后列名删除了关键限定语(pre-spectrum), 导致字段范围扩大」。
- **Interpretation**: judge 的实际判别变量既不是「类型」也不是「编辑距离」（`Accumulated Amortization`→`amort` 编辑距离极大却判 equivalent）, 而是**改后标签能否恢复原指代**: 缩写保留指代 → equivalent; 删除的是**范围限定语**（pre-spectrum）→ 指代变宽 → meaning_changed; 货币符号删除后 `US` 仍可恢复币种 → equivalent, 而 `m【】` 完全丢失币种标识 → meaning_changed。
- **Mechanism hypothesis**: judge 实现的是**指代可恢复性**判据; DR4 的 C1/C2 实现的是**规范形式 / 规范真值存续**判据。两者在「缩写保留指代但破坏规范形式」这一区域**必然分离**——这正是 5/8 disagree 的来源, 也是 DR4 把 7 例 E 全数翻为 H 的来源。两条判据不是同一量的两次测量, 而是两个不同的量。
- **Paper claim（最多能写到）**: 可写成**机制主张**——「实例级危害性标签是**判据相对的（criterion-relative）**; 本窗识别出两条正交轴: 粒度轴（类型级 vs 实例级）与判据种类轴（规范形式 vs 读者指代）; 分歧沿判据种类轴**成块**出现, 不是逐例随机噪声」。支撑该主张的四条 L3 证据: (i) 类型级 E 集 0/7 存续（A-18）; (ii) J-N2 分歧不沿类型切（A-07）; (iii) 相同输入串判定 3/3 组自洽（A-08）⇒ 排除采样噪声; (iv) 分歧按扰动族成块（收口报告 §3 已记, 本次 A-07 独立复算）。
- **Boundary（不能推出）**: 不能选任一方为胜者; 不能把「指代可恢复性」写成**正确的**等价类定义（它只在单一 judge、单一冻结协议、n = 28 下被测到）; 不能推广到本窗零调用的族（`mixed_lang` 20 例、`unit_suffix` 5 例, J-N3 = 0 调用）; 不能推出该机制在第二个 scorer 上同样成立——**在拿到第二 scorer 臂之前, 「判据相对性」是机制主张, 「指代可恢复性是正确的判据」只能是 claim boundary**。
- **Next experiment**: D4 加入**第二 scorer 臂**（不同模型, 或同模型不同协议措辞）, 检验「指代可恢复性」是 judge 个体属性还是判据种类属性。这是把 FA-4 的解释层升为机制主张、并把 §4 判定请求 ② 从 boundary 松绑的唯一路径。

### FA-5 边界对 `567a03c7#1` / `68b8d514#1` 是「同模板、异内容」, 反判有据

- **Observation**: 两例同属 `date_variant` / `absorption_silent`; 改后标签都匹配模板 `<Lead> <YYYY>-<CJK 短语>` 且 Lead 与原名仅大小写差异; 但追加的 CJK 短语不同（`期末日期` vs `报表明细日期`）, verdict 相反（meaning_changed vs equivalent）。
- **Evidence**（L3 + L1）: 收据 A-09（模板正则匹配、`lead_case_folded` 双双为真、`appended_cjk` 不等、verdict 不等）。rationale 原文: `567a03c7#1`「修改后列名包含'期末日期', 与原始'行权日期'语义不同」; `68b8d514#1`「仅增加年份标注, 核心语义仍为授予日期」。
- **Interpretation**: 此前记账把这对写作「同形态反判」, 暗示 judge 不稳定。实测**不成立**: `期末日期`（period-end date）与 `行权日期`（exercise date）是**不同概念**, 而 `报表明细日期` 是对 `授予日期` 的**兼容描述**。judge 做的是内容判别, 不是随机波动——这与 A-08（相同输入串 3/3 组同判）互相印证。
- **Mechanism hypothesis**: **追加型扰动（append）在形态上同质、在语义上异质**。因此「形态族」不是判定预测变量, FA-4 的指代可恢复性才是。这也解释了为什么按扰动族分层比按编辑形态分层更有解释力。
- **Paper claim（最多能写到）**: 可把这对作为「**形态同质 ≠ 语义同质**」的示例写进边界节, 用来支撑「扰动族标签不能替代实例级判据」这一条, 与 FA-3 / FA-4 同向。
- **Boundary（不能推出）**: 不能推出 judge 的内容判别在所有追加型扰动上都正确（n = 2）; 不能推出 `date_variant` 族的总体行为（该族 17 例中本窗只测 2 例）; 不能把这条当作 judge 优于 DR4 的证据——DR4 对这 2 例未单独出对照行。
- **Next experiment**: D4 扩样追加型扰动, 把「追加短语与原名的**概念相容性**」作为预注册分层变量（相容 / 冲突 / 无关三档）, 检验 verdict 是否沿该变量分离。
- **更正注记（只增不改, 承决策 4A 口径）**: THREADS `#D3-STAGE-B-CLOSEOUT` 与收口报告 §3 中「同形对（`amort` ×2、`£m`→`m【】` ×2）判定自洽一致 ⇒ temp=0 稳定」**仍然成立**（收据 A-08 实测 3 组重复输入全部同判, 并新识别出第 3 组 `Operating Leases`→`operat1ng Leases` ×2 = equivalent）; 但把 `567a03c7#1` / `68b8d514#1` 称为「同形态反判」应收紧为「**同模板、异内容、反判有据**」。原文不回改, 以本注记为准。

### FA-6 DR4 8 行的单一 tally 混了两个误差方向

- **Observation**: 8 行中 7 行 `direction = E->H`（漏检侧）, 1 行 `direction = H->E`（误报侧, `3789d7da#1` `Revenues`→`sales`: oracle = E, 而确定性通道 `visible = true ∧ absorbed = false ∧ match_tier = 0`）。分层后 = 漏检侧 3 agree / 4 disagree, 误报侧 0 agree / 1 disagree, 合并 3 agree / 5 disagree。
- **Evidence**（L3）: 收据 A-10（谓词独立重建, 8/8 与交付 `agreement` 字段逐行相同, tally 与 `payload.dr4_agreement_tally` 全等）、A-11（`directions = {E->H: 7, H->E: 1}`）。
- **Interpretation**: `3 agree / 5 disagree` 把「该不该漏检」与「该不该报警」两个不同问题合成一个数。误报侧只有 1 行, 任何比例都不具统计意义; 漏检侧 7 行的 3/4 也不能当作率来推断, 因为 DR4 oracle 与 judge 不是同一判据的两次独立测量（FA-4）。
- **Mechanism hypothesis**: **agreement 谓词本身没有问题**（A-10 用散文谓词独立重建, 结果逐行相同）, 问题在**汇总口径**: 该谓词定义的是**方向一致性**, 不是**判据一致性**。当两行使用不同判据时, disagree 是判据差异的合法产物。
- **Paper claim（最多能写到）**: 报告 8 行对照时**必须按方向分层**（漏检侧 7 行 = 3 agree / 4 disagree; 误报侧 1 行 = 0 agree / 1 disagree）, 不得只报合并 tally; 并须附谓词的性质注记（方向一致性 ≠ 判据一致性）。
- **Boundary（不能推出）**: 不能把 5/8 disagree 写成「DR4 与 judge 有 62.5% 的不一致率」; 不能把误报侧的 1 行推广为 specificity 结论（n = 1）; 不能据此判定 `3789d7da#1` 的 oracle 或确定性通道任一方有误——该行是**过度检出（false alarm）候选**, 属 D3 matched-specificity 的正题, 不是矛盾。
- **Next experiment**: D4 卡冻结节写入**分层 agreement 口径**（§3 措辞草案）+ 每方向的最小样本量要求（n < 5 只报计数不报率）。
- **更正注记（F-S1 连带, 09-09 侧线抽验 + 主线程自查, 只增不改, 承决策 4A 口径）**: 上一行「分层 agreement 口径（**§3** 措辞草案）」的指向**有误**, 正确落点 = 本记录 **§4**「agreement 谓词入 D4 卡冻结节的确切措辞草案（承 F-0907-3, 派发硬前置）」（内含可**逐字**并入 D4 卡冻结节的 `A-D4-1` 文本 + 强制分层汇总三条 + 「方向一致性 ≠ 判据一致性」性质注记 + 以本窗 8 行为回归夹具的验收）; 本记录 **§3** = 「对三个核心问题的回答」, **不含**措辞草案。同批 §6 落地指针行写的即为「**§4** 措辞草案」⇒ 本记录**内部自指此前亦不一致**（FA-6 行指 §3、§6 行指 §4）, 且与 `docs/experiments/2026-09-06_harness_audit_response.md` §2.1 第 1 项（原 :39, 同指 §3）为**同型错指**。侧线 F-S1 只列出跨文档那一处, 本处为主线程落地时自查新增的连带发现。按只增不改口径: 上一行原文**保留作轨迹**, 指向以本注记为准 = **§4**; 该审计响应文档侧的更正注记与两份文档的**双向复验结果**见其 §2.1 与 THREADS `#D3-RULINGS-9C-10C-11B`。本条为**指针更正, 不改任何数字、不改判据、不改 §4 草案文本、不动 SUMMARY-GUARD 块与收据 sha**。

## 3 对三个核心问题的回答（用户已定死, 不改写不窄化）

**Q1: 为什么 matcher / oracle 的等价类定义扩张后, 部分原本 harmful / equivalent 标签发生系统性变化?**

因为「扩张」实际发生在**粒度轴**上, 而 D1 的 E 定义是三条件合取——「被吸收 ∧ 类型属 {alias_variant, mixed_lang, prefix_noise} ∧ 映射标准字段集与原表一致」——其中**只有第三条件是实例级的**, 前两条分别靠匹配器行为与类型身份通过。DR4 把判定下沉到实例级, 并在 `forbidden_oracle_inputs` 中**显式屏蔽全部匹配器行为字段**（`absorbed` / `detected_at_anchor` / `visible_by_gamma` / `marginal_dH` / `canonical_keyset_identical` / `mapping_target` / `absorption_tier` / `class` / `equivalent`, A-15, L1）⇒ 原本靠「类型属白名单 + 被吸收」两条通过的 7 例 E **同时失去支撑**, 于是 7/7 全翻转而非部分翻转（A-18, L3）。变化的系统性来自**定义结构**, 不来自实例内容差异。

**Q2: 当前所谓 harmful / equivalent 是否依赖于 scorer / matcher 的等价类定义?**

**是**, 且依赖方式可识别、可分解。四条 L3 证据: (i) 类型级 E 集在实例级 oracle 下 0/7 存续（A-18）; (ii) ocr_similar 13 例的有害归属由类型白名单 + 词表覆盖决定, 无实例级语义证据支撑, 且 13/13 取值不变（A-12 / A-13 / A-14）; (iii) J-N2 分歧不沿 D1 类型切而沿指代可恢复性切（A-07）; (iv) 相同输入串判定 3/3 组自洽（A-08）⇒ 分歧不是测量噪声, 排除「随机不一致」这一替代解释。

**Q3: 这种 scorer dependence 应成为论文机制主张, 还是 claim boundary?**

**分层处置, 不是二选一。**

- 可写成**机制主张**的部分: 「实例级危害性标签是判据相对的」+「存在两条正交轴（粒度 / 判据种类）」+「分歧沿判据种类轴成块出现、非噪声」。这一层有四条 L3 独立复算支撑（FA-4 Paper claim 行）, 且**不需要**裁定哪条判据正确。
- 必须写成 **claim boundary** 的部分: 「哪条判据正确」、「13 例是否应移出有害集」、「指代可恢复性是否为正确的等价类定义」、「5/8 disagree 是否代表某一方失效」。这一层缺第三方裁定者与第二 scorer 臂, n = 28, 单一 judge, 单一冻结协议。
- 与已锁定的 §15 更正 2 口径同构（收口报告 :215-243）: 「在冻结 judge 协议下, 21 例零信号注入中 14 例被判 equivalent ⇒『零信号即有害』的**隐含假设在实例级不可维持**, 且该判定依赖 scorer/matcher 的等价类定义」——本记录把「依赖性」从一句归因展开为**两轴 + 六项 FA**, 并给出可证伪的下一步。

## 4 agreement 谓词入 D4 卡冻结节的确切措辞草案（承 F-0907-3, 派发硬前置）

下列文本可**逐字**并入 D4 卡冻结节:

```text
A-D4-1 agreement 谓词（冻结; 派发硬前置, 承 F-0907-3）

对每一行对照 (case, oracle, evidence_kind), agreement 按下列两式之一机械判定,
零现场解释空间; 两式互斥, 由 evidence_kind 唯一决定:

  judge 行（evidence_kind == "judge_verdict"）:
    agree  <=>  (verdict == "meaning_changed") == (dr4_oracle == "HARMFUL")

  确定性行（evidence_kind == "deterministic_evidence", 零 judge 调用）:
    detected := visible AND (NOT absorbed) AND (match_tier == 0)
    agree  <=>  detected == (dr4_oracle == "HARMFUL")

汇总口径（强制分层, 承 FA-6）:
  1. 必须按 direction 分列报告: 漏检侧（E->H）与误报侧（H->E）各出
     agree / disagree 计数, 不得只报合并 tally。
  2. 每方向须标注 n; n < 5 的方向只报计数, 不报率、不报百分比。
  3. unresolved_invalid_final 单列, 不并入 disagree。

谓词性质注记（写入卡, 防误读）:
  本谓词定义的是【方向一致性】, 不是【判据一致性】。当对照两侧使用不同判据
  （oracle = 规范形式/规范真值存续; judge = 读者指代可恢复性）时, disagree 是
  判据差异的合法产物, 不构成任一方失效的证据。禁止把 disagree 计数写成
  「不一致率」或与任一方错误率等同。

验收（本地可先行, 零端点）:
  以 D3 阶段 B 8 行为回归夹具, 用本谓词独立重建, 必须逐行复现
  3 agree / 5 disagree / 0 unresolved（收据
  logs/graph/eval/d3_autopsy_recompute.json 检查项 A-10 已实证）。
```

## 5 判定请求（2 件, 待用户圈选; 本记录不裁定、不选边）

### 为什么是这两件（候选 ③ 已被吸收）

用户给的三个候选中, **③「缩写 / 单位变化算不算改口径」在 FA-4 里已经被分解完毕**: 它就是「指代可恢复性 vs 规范形式存续」两条判据在具体族上的分歧实例, 其答案**完全由 ② 决定**——② 选分层（推荐 c）则 ③ 自动落为「两种口径都合法, 按判据种类分层报告」; ② 选 a 或 b 则 ③ 随之确定。且 ③ 没有任何下游阻塞项: D4 oracle 等的是 ①（有害集成员与分母）, 论文措辞等的是 ②（R3 与 S3/S7 写到哪一步）, 没有环节在等 ③。单独提 ③ 等于要求用户在 ② 之前先给 ② 的一个特例裁定, 违反「≤2 件」的意图。故选 **① + ②**。

### 判定请求 ① 纯字符级拼写扰动是否计入「有害注入集」

**问题一句话**: FA-2/FA-3 量化出的 13 例（单 token · 编辑距离 1 · token 数守恒 · 取值 13/13 不变 · 有害归属由类型白名单 + 词表覆盖决定）是否仍计入 S-2 有害注入集（现行分母 111）?

| 选项 | 具体后果 |
|---|---|
| **a) 计入, 表述照旧** | S-2 分母保持 111, TPR 主口径保持 0.810811。C1/R1 的「ocr_similar 0/13 全盲」继续作为**漏检**证据。风险: 把定义性标签写成经验发现, 审稿人用本窗 13/13 equivalent 即可质疑分母合法性, 而论文里没有披露该 13 例的归属来源。 |
| **b) 移出有害集** | 分母 111 → 98, TPR 0.810811 → **0.918367**（Δ +0.107556, 收据 A-16 情景算术, L3）。后果: 论文最强的可见性谱证据（ocr_similar 13/13 恒零可见）从「漏检」降级为「正确的无害吸收」, **C1 主张失去主要支撑**; 且违反「判据冻结不溯及」, 需显式解冻裁定 + 全套下游数字重算（STATE / INDEX / T7 / Claim Set）+ 更正注记。 |
| **c) 计入但改述（推荐）** | 分母与 TPR **零改动**（111 / 0.810811 原样）。把该 13 例的表述从「13 例有害缺陷被漏检」改为: 「评估器对字符级表头扰动在 γ ∈ [0.2, 0.9] 全域零可见（0/13）; 该盲区是否构成漏检取决于等价类定义（见边界节）」。C1/R1 的经验内核（评估器盲区）**完整保留**, 定义依赖性如实披露, 与收口报告 §15 更正 2 已锁定的口径同构, 不新增主张风险。连带要求: D4 oracle 把「扰动族 × 判据种类」写成预注册分层变量。 |

**推荐 c**, 理由: a 把一个定义性标签写成经验发现, 审稿面完全暴露; b 需要溯及解冻, 并会拆掉论文的主证据链; c 在不改任何数字与判据的前提下, 把主张收紧到证据真正能支撑的那一步——即 FA-3 的 (a)/(b) 分离。

> **裁定注记（09-09 落地批, 决策 9 = c, 只增不改）**: 用户已圈选 **c「计入但改述」**, a / b 两支不采, 上表原文逐字保留作轨迹。**裁定后果** = S-2 分母 **111** 与 TPR 主口径 **0.810811** 零改动、H·E·HI 底表 **85/7/26** 零改动、J-N3 维持 **0 调用**; 13 例 ocr_similar（单 token · lowercase Levenshtein 恒为 1 · token 数守恒 · 取值 13/13 不变）**继续计入 S-2 有害注入集**。表述按 c 支改述为: 「评估器对字符级表头扰动在 γ ∈ [0.2, 0.9] 全域零可见（0/13）; 该盲区是否构成漏检取决于等价类定义（见边界节）」。**C1/R1 的经验内核（评估器盲区）完整保留, 不得因改述而弱化「0/13 全盲」这一观测**; 措辞与收口报告 §15.2 已锁定口径**同构一致, 不另立第三种说法**。**红线** = 不得移出有害集、不得改分母、不得溯及解冻; b 支原文所列分母 / TPR 情景数字属收据 **A-16 内部情景算术**（`retroactive = false`, 仅供裁定用、非论文数字）, **只存在于收据与本节 b 支原文内**, 不得进入论文、STATE、INDEX、汇报正文的任何主张位置, 本批之后不再引用。**连带要求（已持久化）** = D4 oracle 把「扰动族 × 判据种类」写成**预注册分层变量**, 落点 = `docs/experiments/2026-09-06_harness_audit_response.md` §2.1 第 **4** 项; 记账 = THREADS `#D3-RULINGS-9C-10C-11B`。

### 判定请求 ② scorer dependence 写成机制主张还是 claim boundary

**问题一句话**: FA-4 识别出的「判据相对性 + 两条正交轴 + 分歧成块非噪声」, 在论文里写成机制主张（R3 / S3）还是只写成局限节的 claim boundary（S7）?

| 选项 | 具体后果 |
|---|---|
| **a) 全写机制主张** | 可写「实例级危害性标签由等价类定义决定」。后果: 需要第三方裁定者或第二 scorer 臂来排除「judge 个体宽松」这一替代解释, **本窗没有**; 审稿人会要求证明这不是单一模型偏好。影响 R3 与 S3 全节。 |
| **b) 全写 claim boundary** | 只在 S7 写一句「标签依赖判据」。后果: 浪费本窗最强的结构发现（两轴 + 族级成块 + 相同输入自洽 + E 类 0/7 存续）, R3 降级为免责声明, 与 D2 已裁的「盲区范围移动」表述层级不匹配。 |
| **c) 分层写（推荐）** | **机制主张**写到: 判据相对性 + 两条正交轴（粒度 / 判据种类）+ 分歧沿判据种类轴成块、非噪声（四条 L3 证据, FA-4）。**claim boundary** 写明: 不裁定哪条判据正确、不主张指代可恢复性为正确定义、单一 judge n = 28 不外推、mixed_lang 与 unit_suffix 两族本窗零调用故无结论。落点 = R3（承接 D2「盲区范围移动」表述）+ S3 一段 + S7 一段。连带硬要求: **D4 必须预注册第二 scorer 臂**, 否则该机制主张永久停在 D3 证据面。 |

**推荐 c**, 理由: FA-4 的四条证据足以支撑「相对性」这一层, 但不足以支撑「哪一侧正确」; 分层写法让能写的写足、不能写的守住, 且把缺口转成 D4 的一条明确预注册要求, 而不是留成一句免责。

> **裁定注记（09-09 落地批, 决策 10 = c, 只增不改）**: 用户已圈选 **c「分层写」**, a / b 两支不采, 上表原文逐字保留作轨迹。**可写成机制主张（三条）**——四条 L3 支撑 = E 集 0/7 存续（A-18）/ 分歧不沿 D1 类型切（A-07）/ 相同输入 3 组 3/3 自洽（A-08）/ 分歧按族成块: ①「实例级危害性标签是**判据相对的**」②「存在**两条正交轴**（粒度轴 / 判据种类轴）」③「分歧沿判据种类轴**成块出现、非噪声**」。**必须写成 claim boundary（四条）**——不裁定哪条判据正确 / 不主张「指代可恢复性」为正确的等价类定义 / 单一 judge、n = 28 不外推 / `mixed_lang`（20 例）与 `unit_suffix`（5 例）本窗零调用故无结论。**落点** = **R3**（承接 D2「盲区范围移动」表述层级, 本批已落注记于 Claim Set v2）+ **S3 一段** + **S7 一段**; S3 / S7 属侧线叙事骨架资产（`docs/experiments/2026-08-29_long_horizon_eval_paper_blueprint.md` :34 / :38 与 `paper/draft_v0_s1_s2_s6.md`）, **主线程只读、本批不改骨架正文**, 确切可粘贴措辞包以汇报正文交付、不落盘, 交侧线复核后由用户决定是否落骨架。**红线** = judge 与 DR4 oracle **均非 ground truth, 不得选边**; **边界例零删除**（`567a03c7#1`、`68b8d514#1`、`3789d7da#1`、同形对三组全保留）。**连带硬要求（已持久化）** = **D4 必须预注册第二 scorer 臂**; 缺此臂则「判据相对性」永久停在 D3 证据面, **不得升级为「哪条判据正确」**, 落点 = `docs/experiments/2026-09-06_harness_audit_response.md` §2.1 第 **5** 项。

## 6 决策 8A / 7B 落地指针

**决策 8A（硬规则 3 口径澄清, 已落地本批）**

- 治理件 `docs/governance/2026-09-07_execution_plane_boundary.md`: 硬规则 3 正文加一句「复现路径以收据或其绑定文档记载为准」（**:59**）; §五 追裁定注记两项均已裁定（**:72-74**）; §六 状态改为「**已澄清（09-08, 决策 8A）**」（**:80**）+ 澄清注记（**:82**）+ 规则 3 的正确用法三步（**:86**）。
- THREADS 新增 `#EXEC-PLANE-RULE3-CLARIFIED`。
- **未做（按 8A 明令）**: 不重跑审计脚本、不生成 v2 收据、不改收据任何字段与 sha、不改 SUMMARY-GUARD 块。
- 首例按澄清口径的合格件 = 本轮 `logs/graph/eval/d3_autopsy_recompute.json`（`meta.reproduce` 内置于收据本体）。

**决策 7B（A4/A5 只排期, 本轮不动手修, 已落地本批）**

- 落点 = `docs/experiments/2026-09-06_harness_audit_response.md` §2 A4 / A5 行「时点」与「状态」列已更新为**排期钉死**（**:28-29**）, 新增 A4w 行承载 watcher 机制修复（**:30**）, 新增 §2.1「D4 拟卡输入清单: 三项派发硬前置」（**:35**）+ 编号命名空间注记（**:43**）。
- THREADS 新增 `#A4A5-WATCHER-SCHEDULED-7B`。
- 三项派发硬前置 = ① agreement 谓词入卡（§4 措辞草案）② watcher 执行位实证 + 首次 tick 实证 ③ A4/A5 验收通过。**修者不自验**已写进排期注记（验收方 = 侧线或 Loop A）。
- **编号命名空间冲突（如实上报, 未擅自处置）**: 用户指令写「docs/29 A 表既有 A4/A5 行」, 但 docs/29 的 A4 = 「Route S 对照臂 serving (SGLang+NVFP4+RadixArk)」（**:103**）、A5 = 「L3 DFlash2 :8007 探针」（**:104**）, 与审计 A4/A5（守卫修复包 / 定标契约版本化）**同名不同物**; 审计派生的治理条目在 docs/29 中另占 A19-A23。按「不新开编号」与「不改写无关台账」两条约束, 本轮**未改动 docs/29 的 A4/A5 行**, 只在审计响应文档内落地并加消歧注记。若用户本意确为 docs/29, 请指明应改哪一行, 另批处置。

## 7 即时上报（方向性新发现, 按开工卡 §五.2 不等排期）

1. **FA-3 与既有 claim 存在张力（需与判定请求 ① 一并裁）**: ocr_similar 13 例的有害归属在三条线上均非实例级经验发现, 而 DR4 已自证其词表偏置是单向的（「只会把实例推向 H, 不会凭空造 E」）。这**不推翻**任何既有数字（0/13 全盲、111 分母、0.810811 全部照旧）, 但**改变这些数字可以被用来主张什么**。已按 FA-3 的 (a)/(b) 分离给出可写与不可写的边界。
2. **FA-6 是汇总口径缺陷, 不是数字错误**: 8 行对照的合并 tally 混了漏检侧与误报侧。既有 `3 agree / 5 disagree` 数值本身经 A-10 独立重建**逐行相符**, 不需更正; 需更正的是**引用方式**（必须分层）。D4 卡冻结节措辞已备（§4）。
3. **FA-5 需一条措辞更正注记**: 「同形态反判」应收紧为「同模板、异内容、反判有据」。按决策 4A 口径只追加、不回改原文、不动收据。已在 FA-5 末行落注记, 同批 THREADS 记账。

> **§7 第 1 条注记（FA-3 张力; 09-09 落地批, 决策 9 = c, 只增不改）**: 本条上报的张力**已随判定请求 ① = c 处置完毕**——13 例继续计入有害集, **不推翻任何既有数字**（0/13 全盲、S-2 分母 111、TPR 主口径 0.810811、H·E·HI 85/7/26 全部照旧）, **只改变这些数字可以被用来主张的范围**: 可写成主张的只有 FA-3 的 **(a) 经验事实**（评估器对字符级表头扰动在 γ ∈ [0.2, 0.9] 全域零可见 0/13）, **(b)「该盲区是否构成漏检」永久留在边界节**, 且该判定依赖 scorer / matcher 的等价类定义（依赖性归本记录 FA-3 / FA-4 + F-0907-3）。DR4 `payload.lexicon.residue_note` 的单向偏置自证（「词表覆盖缺口只会把实例推向 H, 不会凭空造 E」）按裁定**继续作为「定义依赖性」的证据披露**, 不作为「13 例应移出有害集」的依据, 亦不得写成任一方 ground truth。第 2、3 条（FA-6 汇总口径 / FA-5 措辞更正）**状态不变**: 前者为引用方式约束、已入 §4 冻结措辞草案与 §2.1 硬前置 ①, 后者已在 FA-5 末行落注记, 两条均无待裁项。

## 8 红线自查（本轮）

- **零端点**: 收据 `meta.endpoint_calls = 0`、`meta.socket_attempts = []`、`payload.zero_endpoint = true`; 脚本无 HTTP 客户端 import、无 subprocess、无 ssh, socket 层 `connect` / `connect_ex` 双双封死（A-01 / A-17, L3）。无 canary、无 judge、无模型调用。
- **零重跑**: 阶段 B 与 closeout 收据均未重跑; `d3_stage_b_closeout_spotcheck.json` 的 sha 与 SUMMARY-GUARD 块零改动; 未生成任何 v2 收据。
- **判据 / oracle / 阈值 / 底表零改动**: E-1..E-4、S-1..S-8、R1-R4、D1-D2、加编 1/2/3、C3-1..C3-6 全部未触; H/E/HI = 85/7/26 未动; S-2 分母 111 未动（A-16 只做情景算术, `retroactive = false`）; J-N3 维持 0 调用。
- **边界例零删除**: `567a03c7#1`、`68b8d514#1`、`3789d7da#1`、同形对（`amort` ×2、`£m`→`m【】` ×2、`operat1ng Leases` ×2）全部保留并逐例分析。
- **不选边**: 未把 judge verdict 或 DR4 oracle 任一方写成 ground truth; 判定请求 2 件只呈交选项与后果, 推荐仅为建议权。
- **未进 D4 拟卡**: 本轮只产出「入卡措辞草案」与「三项派发硬前置」, 未起草 D4 卡本体。
- **未做 A4/A5 修复**: 只更新排期列与验收方注记, 钩链与定标代码零改动。
- **未碰侧线资产**: 两份 `side_handoff_*.md` 未读未改未提交。
- **未 commit 残件**: `IMPLEMENTATION_PLAN.md` / `PROMPT.md` / `_d3b_dispatch.sh` / `logs/graph/docs_lint_report.json` 保持原状。
- **治理件硬规则 2**: 新收据文件名含 `recompute` 与 `autopsy`（`d3_autopsy_recompute.json`）, `meta` 含 `phase: autopsy` 与 `endpoint_calls: 0`; 未生成任何 `*_stage_x.json` / `*_window.json` 形似原始实验件的产物。
- **检查点持久化（A22 对策）**: 分析全程以收据 + 本记录分段写盘, 中断只需重做报告不需重跑分析。

## 9 停等点

1. **本记录 + §5 判定请求 2 件交付后停下**, 等用户圈选; **不自行进入 D4 拟卡**。
2. §6 的编号命名空间冲突（docs/29 A4/A5 vs 审计 A4/A5）等用户确认落点。
3. 圈选后的既定序列: D4 transfer 预注册卡（本地只拟不执行, 含 §4 谓词 + 三项派发硬前置 + 第二 scorer 臂 + 扰动族分层）→ A4/A5/A4w 合并批（D4 拟卡后、执行前）→ D4 执行（GB10）→ T7 数字合流 → neat 收口 → T5 视觉（P2）。

> **§9 停等点状态注记（09-09 裁定落地批, 只增不改）**:
> - **第 1 项 = 已裁定销账**: 判定请求 ×2 已由用户圈选（① = **c** / ② = **c**）, 裁定注记见 §5 两表下各一条。本批 = 裁定落地批, **仍未进入 D4 拟卡**。
> - **第 2 项 = 已裁定销账（决策 11 = B）**: 编号命名空间冲突的落点已定 = 在 `docs/29_graph_engineering_roadmap.md` 的 **A 表下方新增一行脚注**做「同名不同物」消歧（docs/29 A4 = Route S 对照臂 serving、A5 = L3 DFlash2 :8007 探针; 审计 A4 / A5 = 守卫修复包 / 定标契约版本化, 另有 A4w; 审计派生治理条目在 docs/29 另占 **A19-A23**）, 引用须带文档名消歧。**A4(:103) / A5(:104) 既有单元格逐字未动、未新开任何 A 编号、未把审计 A4/A5/A4w 迁入 A 表**, A 表原有各行逐字不动。
> - **第 3 项 = 部分销账, 既定序列不变**: 圈选已完成, 但 **D4 拟卡为下一批（另批另派）, 本批不进**。本批只把两条连带要求持久化到 `docs/experiments/2026-09-06_harness_audit_response.md` §2.1 第 **4 / 5** 项（扰动族 × 判据种类预注册分层 + 第二 scorer 臂）, 连同 §4 的 A-D4-1 谓词草案一并作为 D4 拟卡输入, 防下一批丢失。序列其余环节（A4/A5/A4w 合并批 = D4 拟卡之后、执行之前 → D4 执行 GB10 → T7 数字合流 → neat 收口 → T5 视觉 P2）**时点与顺序均不变**。

<!-- SUMMARY-GUARD
artifact: logs/graph/eval/d3_autopsy_recompute.json
sha256: 2b62bf317635a91b6ad113d0d3024aa8652bc444eff42d569222c891ae0c522f
claims:
  payload.all_pass = true
  payload.n_checks = 18
  payload.n_pass = 18
  payload.zero_endpoint = true
  meta.endpoint_calls = 0
  meta.phase = autopsy
  payload.recomputed_summary.jn1_equivalent = 14
  payload.recomputed_summary.jn1_meaning_changed = 7
  payload.recomputed_summary.jn2_equivalent = 4
  payload.recomputed_summary.jn2_meaning_changed = 3
  payload.recomputed_summary.ocr_similar_n = 13
  payload.recomputed_summary.ocr_similar_equivalent = 13
  payload.recomputed_summary.non_ocr_n = 8
  payload.recomputed_summary.non_ocr_equivalent = 1
  payload.recomputed_summary.ocr_max_levenshtein_lower = 1
  payload.recomputed_summary.dr4_agree = 3
  payload.recomputed_summary.dr4_disagree = 5
  payload.recomputed_summary.dr4_rows_miss_side = 7
  payload.recomputed_summary.dr4_rows_false_alarm_side = 1
  payload.recomputed_summary.d1_E_total = 7
  payload.recomputed_summary.d1_E_surviving_oracle = 0
  payload.recomputed_summary.identical_input_groups = 3
  payload.recomputed_summary.identical_input_groups_verdict_consistent = 3
  payload.recomputed_summary.s2_denominator_frozen = 111
  payload.recomputed_summary.s2_tpr_frozen = 0.810811
  payload.recomputed_summary.s2_denominator_scenario = 98
  payload.recomputed_summary.s2_tpr_scenario = 0.918367
  payload.recomputed_summary.endpoint_calls = 0
END-SUMMARY-GUARD -->
