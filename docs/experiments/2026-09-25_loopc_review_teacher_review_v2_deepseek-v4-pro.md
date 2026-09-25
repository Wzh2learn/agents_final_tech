# Loop C independent review of the evaluation-track manuscript, round v2 (model deepseek-v4-pro)

> Dispatched by Loop D on 2026-09-25 under the goal completion criterion (independent dual-model review),
> because the §6 external-validity paragraph and claim SP-C5 were added after the previous ACCEPT chain.
> Mode: evidence packet inline (manuscript + claim manifest + step-checkpoint v2 results + split design/capacity),
> no tools, 1 turn, cost not reported by bare mode. Packet sha256
> `ef6ddc7ac80b865d5441993b6187a2cd2db1789428c925fb36d2be39cf56fb78` (61 097 bytes).
> Session PID 3812665 on GB10; ran concurrently with the qwen3.8-max session, no shared context, no resume.
> Limitation carried over from round v1: this is a text-level review; the underlying JSON artifacts were not recomputed.
> Body below is the session final message verbatim; assembled by Loop D without edits.
# Loop C 审稿报告：§6 末段 + SP-C5 新增内容

---

## 1. 总体判定：**REVISE**

一条 Blocking issue（"any proportional assignment" 过度主张）必须修正。其余问题均为 Major 或 Minor，可在同轮修订中解决。

---

## 2. Blocking Issues

### B1. "any proportional assignment" 是对证据的过度推广

- **位置**：§6 末段，第六句。"…contains only ten origin clusters, which leaves one role layer empty under **any proportional assignment** and caps independent units at ten."
- **证据指针**：附录 D（`phase1a_split_design_and_layer_capacity.md`）§4.2 仅证明在 _当前这一种_ 分桶方案（hash mod 100 → train [0,50) / dev [50,70) / gate [70,85) / sealed [85,100)，即 50:20:15:15 固定 band + hash 随机放置）下，dev 层恰好分到 0 个簇。附录 D §8 G-B 明确讨论了**替代分配规则**（「按簇哈希排序后的秩分位」），并指出该替代规则「可保证簇数 ≥4 时四层非空」。因此"under any proportional assignment"是已证伪的陈述 —— 证据只支撑"under the fixed band assignment used here"，而不是"any"。
- **稿件原文**：`which leaves one role layer empty under any proportional assignment`
- **artifact 原文**（附录 D §4.2）：`dev = 0（0 簇）`（当前 run 结果）；§5 W1：`阈值分桶在 10 个簇上把 dev band（20%）分到 0 个簇`；§8 G-B：`「按簇哈希排序后的秩分位」（可保证簇数 ≥4 时四层非空）`
- **两侧不一致**。
- **建议修法**：改为 `which, under the fixed band assignment, leaves the dev layer empty` 或 `which leaves one role layer unfilled under the current split rule`。
- **风险等级**：高。若保留，等于宣称一个 10 簇语料在任何比例分配下都必然有一层为空，而附录 D 的 G-B 裁定项已经给出了反例构造。

---

## 3. Major Issues

### M1. "Detection figures…" 一句构成不必要的狗哨风险

- **位置**：§6 末段，最后一句。"Detection figures from that run are conditional on a faithful subset of 16% to 24% and are deliberately not claimed as evidence here; what is claimed is the boundary itself."
- **证据指针**：附录 C §7 明确禁止：「不得把 detection 0.99068 / 0.99358 或 localization 1.0 说成『步级 checkpoint 检测在 FinQA 上成立』」。稿件确实没有"说成成立"，且写了"not claimed as evidence"。但"Detection figures from that run are conditional on…"的写法本身**暗示存在一个高检测率**（否则没有提及的必要），而该高检测率（0.99）正是附录 C §7 禁止引用的数字。提及存在而不报数字，在同行评审中属于典型狗哨：知情的审稿人会推知 0.99 存在，不知情的读者会被暗示"有检测能力"。
- **建议修法**：整句删去"Detection figures from that run are conditional on a faithful subset of 16% to 24% and are deliberately not claimed as evidence here;"，直接以"what is claimed is the boundary itself — the scorer cannot reproduce the leaf-state cells and the route was stopped rather than re-parameterized."结尾。若必须交代分母比例，改为"…the scorer's step semantics are reconstructible on only 16%-24% of records, which is insufficient for cell-level reproduction under the pre-set 0.5 threshold; the stop condition therefore fired."
- **风险等级**：中高。不修正可能导致审稿人认为作者在以"不报数字"的方式规避附录 C §7 禁令。

### M2. Criterion (i) "partially met" 的定性需要更精确

- **位置**：§6 末段，第二句。"Criterion (i) is partially met."
- **证据指针**：附录 D §6 合同逐门对位表明确记载 FinQA 命名空间的 `layer_isolation` 失败码为 `missing_or_empty_partition`（gate/sealed 因注册表 `role_fit` 未含而空），且 §5.2 的更正写明 FinQA「**不能**过 LABEL_GO」。而 reinstatement criterion (i) 的原文是"passes SOURCE_GO **and** SPLIT_GO with UID-disjoint layers"。当前进展是：SOURCE_GO ✓、split 仪器就绪且几何可填 ✓、LABEL_GO ✗（不可逾越）、SPLIT_GO 因标签缺失而无法正式通过。"Partially met"正确但过于模糊 —— 读者可能误以为只剩小缺口，而实际 LABEL_GO 是不可逾越的结构性障碍（W4 + 附录 D §5.1）。
- **建议修法**：在"partially met"后补充一句定性，例如："SOURCE_GO passed and the split instrument is geometrically ready, but the label layer cannot be satisfied because this corpus lacks an externally defined canonical vocabulary for table columns (Appendix D, W4); SPLIT_GO therefore remains blocked pending a label source."
- **风险等级**：中。不修正可能导致读者低估缺口严重性。

### M3. SP-C5 的 status 分类与其证据体量不匹配

- **位置**：`claim_manifest_v1.json` SP-C5 条目。
- **证据指针**：SP-C5 引用三份证据文件（SOURCE_GO staging、split 设计与层容量实测、步级 checkpoint v2 结果），覆盖两个独立工作线。其内容体量（三个完整实测件、四个数字、一个 stop condition、一个边界结论）超过 SP-C4（mechanism_case_only，一个探索性案例）和 SP-C1（单家族盲区观察）。但 SP-C5 的 status 值 `attempted_stopped_by_preregistration` 是 manifest 中唯一既不含"supported"也不含"as_"前缀的状态，不便于与 SP-C1..SP-C4 横向比较。
- **建议修法**：将 status 改为 `supported_as_preregistered_boundary_only` 或 `boundary_observed_not_result_claimed`，以明确：该条目报告的是**被正确触发的预注册边界**，不是被驳回的主张。同时建议在 scope_limit 中显式增加"this entry reports a boundary finding, not a substantive result"，与当前 scope_limit 最后一句的"not a performance result"形成补充。
- **风险等级**：低中。不影响稿件正文，但 manifest 是 Loop C 判定的正式记录，status 分类应自洽。

---

## 4. Minor Issues

### m1. "16% to 24%" 是四舍五入，与 artifact 精确值有偏差

- **位置**：§6 末段，最后一句。"…conditional on a faithful subset of 16% to 24%…"
- **两侧数字**：
  - 稿件：16% to 24%
  - artifact（附录 C §7）：`322 / 467，占 1 970 的 16.3% / 23.7%`
- **判定**：一致（取整后），但精度低于 artifact。在涉及分母含义的关键句中，建议保留一位小数（"16.3% to 23.7%"）以减少审稿人质疑空间。
- **风险等级**：低。

### m2. 段落信息密度过高，第二数据流与第二 scorer 两条线交错

- **位置**：§6 末段全文。
- **描述**：一段内同时覆盖：(a) SOURCE_GO 通过 + split 几何可填，(b) label 层缺失原因（FinQA 无 canonical vocabulary + Valentine 10 簇不足），(c) step checkpoint scorer 的两种百分号读法、保真度、停止条件触发，(d) 16%-24% faithful subset、(e) 边界结论。两条线（数据流 / scorer）在同一个长句中交汇（"on that corpus the four role layers are geometrically fillable…"），读者需反复回溯才能解耦。
- **建议修法**：将段落拆为两段：(i) 第二数据流：进展与 label 层缺口；(ii) 第二 scorer：步级重执行、两种读法、停止条件与边界结论。不改内容，只改结构。
- **风险等级**：低。

### m3. "ten origin clusters" 与 "caps independent units at ten" 表述可更精确

- **位置**：§6 末段，第六句。
- **描述**：Valentine 的实际独立单元是 lineage UID（即源表），不是 cluster。10 个簇 = 10 个 UID，故"caps independent units at ten"正确，但"ten origin clusters"中的"origin"一词可能与 `independence_cluster` 的命名空间前缀概念混淆 —— artifact 中 Valentine 的 cluster 是 NYC 表对目录名，不是"origin cluster"这个正式术语。建议统一为"ten independence clusters"或直接说"ten table-pair clusters, yielding ten independent units."
- **风险等级**：低。

---

## 5. 数字逐项核对表

| 数字 | 稿件原文（§6 末段） | artifact 原文 | 是否一致 |
|---|---|---|---|
| 2409 | "2409 lineage UIDs" | 附录 D §4.1 M=1 行：`UID = 2 409` | ✅ 一致 |
| 768 | "768 report clusters at full population" | 附录 D §4.1 M=1 行：`入选簇/总簇 = 768/768` | ✅ 一致 |
| 1970 | "1970 frozen step-level records" | 附录 C §2 标题：`M=1 主语料（1 970 条记录）` | ✅ 一致 |
| 0.0298 | "0.0298 under one percent convention" | 附录 C §1 表格：`mantissa_direct` pct 保真度 = `0.0298` | ✅ 一致 |
| 0.2233 | "0.2233 under the other" | 附录 C §1 表格：`mantissa_scaled` pct 保真度 = `0.2233` | ✅ 一致 |
| 0.5 | "the pre-set 0.5 threshold" | 附录 C §1：`『若 v2 在两种读法下的 pct 形态保真度均仍低于 0.5…』` | ✅ 一致 |
| ten | "ten origin clusters" | 附录 D §4.2：`入选簇/总簇 = 10/10` | ✅ 一致（表述建议统一，见 m3） |
| one role layer empty | "leaves one role layer empty" | 附录 D §4.2：`dev = 0（0 簇）` | ✅ 一致（但"any proportional assignment"限定语过度推广，见 B1） |
| 16% to 24% | "faithful subset of 16% to 24%" | 附录 C §7：`322 / 467，占 1 970 的 16.3% / 23.7%` | ✅ 一致（四舍五入，见 m1） |

**结论**：所有裸数字与 artifact 一致。唯一的不一致不在数字本身，而在限定语"any proportional assignment"（见 B1）。

---

## 6. SP-C5 条目评估

| 维度 | 评估 |
|---|---|
| **status** | `attempted_stopped_by_preregistration` — 语义准确（attempted + stopped），但与 manifest 中 SP-C1..SP-C4 的 status 分类体系不统一。建议改为 `boundary_observed_not_result_claimed` 或等效分类值（见 M3） |
| **claim 文本** | 准确概括了三条结论：SOURCE_GO + UID-disjoint ✓、action-label ✗、step re-execution ✗、deferred arms unreported。与 §6 末段一致。未发现过度主张或不足。 |
| **manuscript_tokens** | 四个 token（0.0298 / 0.2233 / 1970 / 2409）均来自稿件 §6 末段且均可在附录 C/D 中逐字定位。缺少对"ten origin clusters"和"0.5 threshold"的 token 级引用，但这不削弱证据链 —— 两者在 claim 文本中未作为数字主张出现。 |
| **evidence** | 三份证据文件覆盖充分：(1) SOURCE_GO staging 支撑 SOURCE_GO 通过；(2) split design 支撑 UID-disjoint 层分配与 2409 UID；(3) step checkpoint v2 结果支撑 0.0298/0.2233/1970/stop condition。 |
| **scope_limit** | "No second-dataflow result and no second-scorer result are claimed; the reported quantity is the measured boundary and the fired stop condition, not a performance result." — 范围限定正确，与稿件"what is claimed is the boundary itself"对齐。建议补充"this entry reports a boundary finding"以区分于 SP-C1..SP-C4 的 substantive claim 性质。 |
| **与 SP-C1..SP-C4 的冲突检查** | 无冲突。SP-C3 scope_limit 写"No second-dataflow result and no second-scorer result are claimed"，SP-C5 在 claim 文本和 scope_limit 中均遵守此限制。SP-C5 不与任何既有 claim 重复或越界。 |
| **forbidden marker 检查** | 无。SP-C5 的 claim 文本、manuscript_tokens、evidence、scope_limit 中均不含 manifest 所列 forbidden markers。 |
| **建议** | **保留 SP-C5，但修改 status 值**（见 M3）。不降级、不需改写 claim 文本。 |

---

## 7. 下一步 3 项建议

1. **立即修正 B1**（最高优先级）：将"under any proportional assignment"替换为"under the fixed band assignment"或"under the current split rule"。这是整篇稿件中唯一一个与 artifact 证据产生实质性偏差的断言。附录 D §8 G-B 已给出反例构造，不可保留。

2. **处理 M1 狗哨风险**（与 B1 同轮）：删除或改写"Detection figures from that run are conditional on…"一句。如确需交代分母信息以说明"为什么不能用于 reproduced leaf-state cells"，改为不含"detection"一词的中性表述（见 M1 建议修法）。此举同时消除附录 C §7 禁令的任何灰色地带解读。

3. **结构优化 + status 统一**（可与上两项同轮，也可单独一版）：(a) 将 §6 末段拆为两段以解耦数据流与 scorer 叙事（见 m2）；(b) 将 SP-C5 status 改为 `boundary_observed_not_result_claimed` 或 Loop C 与作者协商确定的新值（见 M3）；(c) 将"16% to 24%"改为"16.3% to 23.7%"（见 m1）。

---

**审稿人签署**：Loop C（独立审稿人），2026-09-25。本报告仅基于所附附录 A–D 的文本证据，未调用任何外部工具、未修改任何文件、未引入外部文献。
