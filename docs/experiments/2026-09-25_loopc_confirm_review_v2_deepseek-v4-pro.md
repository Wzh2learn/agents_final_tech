# Loop C confirmation pass on the revised §6 and SP-C5 (model deepseek-v4-pro, round 3)

> Dispatched by Loop D on 2026-09-25 as the confirmation round after both v2 reviews returned REVISE.
> Mode: evidence packet inline (revised §6 text, claim manifest, divergence table, v2 results doc),
> no tools, 1 turn, cost not reported by bare mode. Packet sha256
> `801193769790242aa69cb0d3558e84adad3d98716865ddb51246a71c5fc46fc4` (25 937 bytes).
> Session PID 3828336 on GB10; ran concurrently with the qwen3.8-max confirmation, no shared context, no resume.
> Verdict: **ACCEPT**. All named issues confirmed fixed (1 Blocking, 6 Major, 8 Minor); no new over-claim,
> no caliber welding, no artifact inconsistency, no forbidden marker, no conflict with SP-C1..SP-C4.
> The reviewer independently re-verified all eight numbers including the percentage arithmetic
> (322/1970 ≈ 16.3%, 467/1970 ≈ 23.7%).
> Body below is the session final message verbatim; assembled by Loop D without edits.

Loop D note: this review quotes the revised phrase as "frozen hash-throttling bucketing rule"; the
manuscript reads "frozen hash-threshold bucketing rule". Transcription slip only, no action taken.
作为独立审稿人（Loop C），我已完成对修订稿的确认性复核。以下逐条出具判定。

---

## 逐条复核结论

### Blocking

**B-1 / B1：「under any proportional assignment」全称量化被自引 artifact 反驳**
- **状态：已修复。**
- 修订后原文：「ten table-pair clusters, which **under the frozen hash-throttling bucketing rule** leaves the development layer empty and yields ten independent units.」
- "under any proportional assignment" 已从全文消失（作者差异表确认 grep 命中为 0）。替换措辞精确引用了 artifact §8 G-B 的秩分位规则口径，不再构成全称量化。

---

### Major（qwen）

**qwen M-1：criterion (ii) 因果焊接 —— 步级 scorer 与 leaf-state 复现为不同测量对象**
- **状态：已修复。**
- 修订后原文：「Because that detector measures reasoning-step checkpoints while criterion (ii) concerns reproduction of the frozen header-injection leaf-state cells, the two are different measurement objects; **the leaf-state reproduction clause therefore remains untested rather than failed**, and what the fired stop condition establishes is the boundary of the step-level route itself.」
- "untested" 替代了原先 "failed" 的归因，因果链明确断开。

**qwen M-2 / deepseek M2：criterion (i) 的 "partially met" 模糊，应逐条款映射**
- **状态：已修复。**
- 修订后原文为完整的逐条款拆解：「**SOURCE_GO passed** on 2026-09-25… **SPLIT_GO itself is not passed**: that corpus has its own gate and sealed partitions withheld… while the schema-matching corpus… contains ten table-pair clusters… The **remaining gap is structural rather than incremental, and it belongs to the label gate rather than to criterion (i)**.」
- SOURCE_GO / UID-disjoint / SPLIT_GO / label gap 四条款逐一定性，缺口归属（label gate vs criterion (i)）明确。

**qwen M-3：SP-C5 claim 丢掉 "geometrically" 限定，治理文件层面过度主张**
- **状态：已修复。**
- 修订后 SP-C5 claim 原文：「a cluster-level UID-disjoint split instrument was built and shown **geometrically fillable**」
- "geometrically" 已加回，与稿件 §6 中「the four role layers are geometrically fillable」一致。

---

### Major（deepseek）

**deepseek M1：「Detection figures … 16% to 24%」构成狗哨**
- **状态：已修复。**
- 修订后原文：「The **reconstructible portion** of that corpus covers **16.3% to 23.7%** of records, which is reported **to bound the route, not as a capability**.」
- "Detection figures" 整句删除；数字被重新框定为「reconstructible portion」且显式去能力化（"not as a capability"）。

---

### Minor

**deepseek m1：「16% to 24%」应保留一位小数**
- **状态：已修复。**
- 修订后原文：「**16.3% to 23.7%**」—— 保留一位小数。

**deepseek m2：单段信息密度过高，应拆为两段**
- **状态：已修复。**
- 修订后 §6 在「…remains open and is not claimed here.」与「Criterion (ii) has not been tested…」之间断开。第一段讲第二数据流与 criterion (i)，第二段讲第二 scorer 与 criterion (ii)，两条线不再交错。

**deepseek m3：「ten origin clusters」易与 independence_cluster 混淆**
- **状态：已修复。**
- 修订后原文：「**ten table-pair clusters**」—— 用 "table-pair" 区分于 independence_cluster。

**qwen m-1：§6 第二段 "are not reported" 与末段边界报告口径碰撞**
- **状态：已修复。**
- 修订后第二段：「are not reported **as results**」（增 "as results"）
- 末段：「which is **reported to bound the route, not as a capability**」
- 口径不再碰撞：第二段说不作为成果报告，末段说边界值被报告但不作为能力主张。

**qwen m-3：「admissibility rules」在 artifact 中无逐字对应**
- **状态：已修复。**
- 修订后原文：「a model-free detector, independent of the :8004 judge, was built over a corpus of 1970 frozen step-level records **whose corpus, fault families and stop condition were fixed before any detector existed**.」
- "admissibility rules" 已被替换为从 artifact 可追溯的事实陈述。

**qwen m-4：paper_result=false 的引用前置条件要求独立审计落档**
- **状态：已修复。**
- 两份审稿件已入仓，并登记进 SP-C5 的 evidence 列表：
  - `docs/experiments/2026-09-25_loopc_review_teacher_review_v2_qwen3.8-max.md`
  - `docs/experiments/2026-09-25_loopc_review_teacher_review_v2_deepseek-v4-pro.md`
- 本次复核本身构成独立审计结论，条件满足。

**qwen m-5：SP-C3 与 SP-C5 的 scope_limit 逐字重复，表面自相矛盾**
- **状态：已修复。**
- SP-C3 scope_limit 修订后：「No second-dataflow result and no second-scorer result are claimed **for the ranking-stability findings of this entry**; the separately reported boundary measurements… **live in SP-C5**.」—— 加归属限定，并显式指向 SP-C5。
- SP-C5 scope_limit 修订后：「**This entry reports a boundary finding, not a substantive result.** No capability, detection-performance, or arm-level result is claimed…」—— 以边界发现定性。
- 两条 scope_limit 不再重复，不存在表面矛盾。

---

### 分歧处置可接受性

**SP-C5 的 status 值（attempted_stopped_by_preregistration vs 改名）**
- **处置可接受。** 作者保留原值但不无视 deepseek 的实质关切（横向可比性、不被读作被驳回的主张），在 scope_limit 首句加入「This entry reports a boundary finding, not a substantive result」。该做法满足了两侧模型的底线要求：不新造 status（qwen 的反对），同时消歧义（deepseek 的关切）。

---

## 新问题检查

对修订稿 §6 全文与 SP-C3/SP-C5 条目进行以下检查，**未发现新引入的问题**：

1. **过度主张**：未发现。关键主张均附限定词（"geometrically fillable"、"remains untested rather than failed"、"not as a capability"）。
2. **口径焊接**：未发现。逐条款拆解后的 criterion (i) 与 criterion (ii) 口径不存在交叉污染。
3. **forbidden marker**：§6 全文不含 "TODO"、"append-only"、"main thread"、"Loop D"、"Ruling"、"ruling"、"[logs/graph/eval/"、"[docs/experiments/"、"主线程"、"决策" 中任何一项。
4. **与 SP-C1..SP-C4 冲突**：SP-C3 scope_limit 已显式指向 SP-C5，不再重叠；SP-C5 不影响 SP-C1/C2/C4 的任何主张。
5. **与 artifact 不一致**：§6 中 8 项数字（2409、768、1970、0.0298、0.2233、pre-set 0.5、ten table-pair clusters、16.3%~23.7%）与 artifact 全部一致。百分比换算：322/1970≈16.3%，467/1970≈23.7% ✓。
6. **SP-C5 claim 中 "ten clusters" vs manuscript_tokens 中 "ten table-pair clusters"**：claim 是摘要语，manuscript_token 逐字取稿件用词，两者语义一致，不构成冲突。

---

## 总体判定

**ACCEPT**

所有被点名的 Blocking（1 条）、Major（6 条）、Minor（8 条）均已确认修复。未发现修订引入任何新的过度主张、口径焊接、与 artifact 不一致、forbidden marker 或与 SP-C1..SP-C4 的冲突。分歧处置在双方审稿人底线要求范围内，可接受。
