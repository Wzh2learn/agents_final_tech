# Loop C narrow release confirmation, round 5 (model qwen3.8-max) - ACCEPT

> Dispatched by Loop D on 2026-09-25 to convert round 4's conditional REVISE into a verdict,
> per the round-4 reviewer's own release conditions. Scope: the four release conditions plus a
> check that F5-F9 were not botched; C3-N3 / C3-N4 were explicitly not reopened.
> Mode: evidence packet inline (SP-C5 entry, revised §6 paragraphs, the pre-existing deferral
> sentence, the verbatim diff, and the v2 results section that anchors 322 / 467), no tools,
> 1 turn, cost not reported by bare mode. Packet sha256
> `bf086dff371053e8a207f08d1db9fd62678d4d0630c54c353622cf2a6cc5783d` (20 014 bytes).
> Audited head = `12e5e398ff8e8602a09dee78a9619eb6d0466ff2`. GB10 PID 3890701, clean exit, empty stderr.
> Verdict: **ACCEPT**. All four release conditions satisfied. One bookkeeping note (N-1): the
> `audit_status` field still read round3 and should be advanced to round5 - actioned by Loop D
> in the same wave.
> Body below is the session final message verbatim; assembled by Loop D without edits.
# Loop C 第 5 轮 · 窄范围放行确认报告

**审稿对象**：head `12e5e398ff8e8602a09dee78a9619eb6d0466ff2`，SP-C5 条目、§6 两段修订、附录侧排版 diff、v2 结果件（附录 E）。
**范围**：仅核第 4 轮四条放行条件 + F5–F9 是否改错。不重开 C3-N3 / C3-N4。未调用工具，未修改任何文件。

---

## 逐条判定

### 条件 1（F1：322 / 467 二选一处理）——**已满足**（走「登记 + 锚点」路径）

**(a) 正文改写正确。** §6 第二段末句由旧版含混的 "covers 322 and 467 records of 1970 under the two conventions" 改为显式绑定：

> "…covers **322 records of 1970 under the convention yielding 0.0298**, and **467 under the one yielding 0.2233**, i.e. 16.3% to 23.7%…"

绑定方向核对（对照附录 E §1/§2）：`mantissa_direct` → pct 保真度 0.0298 → 分母 322；`mantissa_scaled` → 0.2233 → 分母 467。**322↔0.0298、467↔0.2233 的配对与出处件完全一致，无错绑。** 且 322/1970 = 16.345% → 16.3%，467/1970 = 23.706% → 23.7%，与 "16.3% to 23.7%"（升序、direct→scaled）自洽；附录 E §2 中 interpretation_fidelity 0.16345178 × 1970 ≈ 322、0.23705584 × 1970 ≈ 467，交叉印证这两个数即「忠实重构的记录数」，正文措辞 "the portion … with faithful reconstruction" 语义准确。

**(b) token 登记与正文逐字一致。** manuscript_tokens 新增：
- `"322 records of 1970"` —— 正文含逐字子串 "322 records of 1970" ✓
- `"467 under the one yielding 0.2233"` —— 正文含逐字子串 "467 under the one yielding 0.2233" ✓

**(c) 锚点真实含 322 / 467。** SP-C5 evidence 第三项 `docs/experiments/2026-09-25_step_checkpoint_score_v2_results.md` 即附录 E 出处件，其 §2 表格中 322 与 467 作为 `fault_detection_rate` / `clean_false_flag_rate` 的分母明确在案（M=1 主语料，1970 条）。**锚点成立。**

**(d) 不越 scope_limit。** 句末 "is reported to bound the route, not as a capability" 保留，与条目 scope_limit（"the measured boundary, and the fired stop condition"）一致，未构成能力声明。✓

### 条件 2（F3：manuscript_tokens 增 "two to eleven columns"）——**已满足**

- token `"two to eleven columns"` 已加入 ✓；正文逐字含 "with two to eleven columns" ✓。
- 与既有条目内部一致：claim 未变，该 token 支撑的是 SOURCE_GO 的表层均匀性陈述，与早已登记的 `"7134 examples"` 同句同源。
- 非阻断建议（不影响判定）：列数分布的最详载处是 `docs/datasets/2026-09-25_finqa_process_structure_and_checkpoint_semantics.md`，该件不在 SP-C5 evidence 列表内；若 staging 件（evidence 第一项）已含列宽范围则无须动作，否则可考虑补列。此点第 4 轮未设为条件，仅作记录。

### 条件 3（F2：改掉 "whose absence"）——**已满足**

- 旧："the transfer corpus **whose absence** triggered the original deferral" → 新："the transfer corpus **whose missing table layer** triggered the original deferral"。递延原因现正确归到「缺 table layer」。
- **与 §6 既有段落（附录 C，第 157 行）一致性核对**：既有原句为 "The transfer corpus **lacks the table layer** required to define per-family constructible sample counts, so the transfer arm was deferred…"。改后措辞（missing table layer / 同段后文 "the absence of a table layer"）与既有归因**同指同一缺陷，无冲突、无第二套理由**。✓
- 同句第二处消歧也已改好："does not apply to **it**" → "does not apply to **the acquisition corpus**"，指代不再可能被误读为 action corpus。✓

### 条件 4（F4：附录侧列数分布千位分隔排版）——**已满足**

- 旧版混排 "2:1 586 · 3:1 452 · 4:2 422 · 5:530…"（前三项用空格千分位、后七项不用，且 "2:1 586" 有被误读为比值 2:1 的风险）→ 新版统一为无分隔连写 "2: 1586 · 3: 1452 · 4: 2422 · 5: 530 · 6: 541 · 7: 483 · 8: 102 · 9: 12 · 10: 2 · 11: 4"。
- **数值核对**：1586+1452+2422+530+541+483+102+12+2+4 = **7134**，与新增的对账注 "（求和 = 7134，与例数对账）" 及同表 "带非空 table_ori 的例 7 134" 吻合。数值未被排版修改改动，仅格式统一。✓
- 行数分布行同步统一格式（1: 1 · 2: 77 · 3: 597 · 4: 1141 · 5: 1316 · 6: 1044），标注为「分布头部」，不要求和，无问题。✓

---

## F5–F9（纯措辞）抽查：**未发现改错**

- claim 字段 "frozen bucketing rule" → "frozen **hash-threshold** bucketing rule"：与正文 §6 逐字一致，属收紧而非漂移。✓
- "named separately here, so that no finding is bound to the wrong one" → "named separately"：删冗余，三语料点名结构未动。✓
- "A table layer makes samples definable" → "**Here,** a table layer makes samples definable"：加限定词，缩小断言作用域，方向正确。✓
- 全部 13 个 manuscript_tokens 与当前正文逐字复核一遍（2409 lineage UIDs / 768 report clusters / 1970 frozen step-level records / 0.0298 / 0.2233 / pre-set 0.5 / ten table-pair clusters / 16.3% to 23.7% / four role layers / 7134 examples / two to eleven columns / 322 records of 1970 / 467 under the one yielding 0.2233）：**均为正文逐字子串，无失配。**✓

## 非阻断记录（不影响本轮判定）

- N-1：`audit_status` 仍为 `dual_model_ACCEPT_2026-09-25_round3`，未反映第 4 轮（REVISE 附条件）与本轮结果；建议作者按流程惯例更新为 round5 字样。属簿记项。
- N-2：见条件 2 下关于列宽锚点件的建议。

---

## 总体判定：**ACCEPT**

四条放行条件全部满足：F1 走「登记 + 锚点」路径且 token 逐字一致、锚点件真实含 322/467 并与正文绑定方向正确；F3 token 已补；F2 递延归因已正确落到「缺 table layer」且与 §6 既有段落一致；F4 排版统一且求和对账 = 7134。F5–F9 措辞改动无引入错误。N-1、N-2 为非阻断项，可随下次提交顺带处理，无需再审。
