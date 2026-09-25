# Loop C narrow release confirmation, round 5 (model deepseek-v4-pro) - ACCEPT

> Dispatched by Loop D on 2026-09-25 to convert round 4's conditional REVISE into a verdict,
> per the round-4 reviewer's own release conditions. Scope: the four release conditions plus a
> check that F5-F9 were not botched; C3-N3 / C3-N4 were explicitly not reopened.
> Mode: evidence packet inline (SP-C5 entry, revised §6 paragraphs, the pre-existing deferral
> sentence, the verbatim diff, and the v2 results section that anchors 322 / 467), no tools,
> 1 turn, cost not reported by bare mode. Packet sha256
> `bf086dff371053e8a207f08d1db9fd62678d4d0630c54c353622cf2a6cc5783d` (20 014 bytes).
> Audited head = `12e5e398ff8e8602a09dee78a9619eb6d0466ff2`. GB10 PID 3890703, clean exit, empty stderr.
> Verdict: **ACCEPT**. All four release conditions satisfied; no new finding.
> Body below is the session final message verbatim; assembled by Loop D without edits.
---

## Loop C 第 5 轮窄范围放行确认（只读，逐条核四条放行条件）

### 判定结果（逐条）

---

#### F1：322 / 467 —— **已满足**

作者选择「登记 + 锚点」路径，`manuscript_tokens` 新增两条：

- `"322 records of 1970"`
- `"467 under the one yielding 0.2233"`

**逐字一致性核验：**

| token | 修订后 §6 正文对应片段 | 匹配 |
|---|---|---|
| `322 records of 1970` | 「covers **322 records of 1970** under the convention yielding 0.0298」 | ✅ 逐字一致 |
| `467 under the one yielding 0.2233` | 「and **467 under the one yielding 0.2233**」 | ✅ 逐字一致 |

**锚点（evidence）核验：** SP-C5 的 evidence 第三条为 `step_checkpoint_score_v2_results.md`，即附录 E。该件 §2 表明确出现：

- `mantissa_direct` 下 `fault_detection_rate` 分母 **322**（解释为 interpretation_fidelity 分子：1970 × 0.16345178 ≈ 322）
- `mantissa_scaled` 下 `fault_detection_rate` 分母 **467**（解释为 interpretation_fidelity 分子：1970 × 0.23705584 ≈ 467）

两数均在出处件中有明确行，锚点成立。**放行条件满足。**

---

#### F2：「whose absence」→「whose missing table layer」—— **已满足**

修订为：

> the transfer corpus **whose missing table layer** triggered the original deferral

且该句末尾从 `does not apply to it` → `does not apply to the acquisition corpus`（消除了代词歧义）。

**一致性核验（与附录 C 既有的递延理由原句）：**

附录 C：
> The transfer corpus **lacks the table layer** required to define per-family constructible sample counts, so the transfer arm was deferred

修订后的 F2 表述（「whose missing table layer triggered the original deferral」）与上述既存理由完全一致：递延原因均归为 transfer corpus 的 **table layer 缺失**，未引入新归因、未与他处矛盾。

此外，修订后段落在紧接处写明：
> the clause that deferred the transfer corpus, the absence of a table layer, does not apply to the acquisition corpus

这里 `the absence of a table layer` 修饰的是「致递延的那个 clause」的主语（即 transfer corpus），与附录 C 的逻辑链首尾相接。**放行条件满足。**

---

#### F3：「two to eleven columns」增入 manuscript_tokens —— **已满足**

`claim_manifest_v1.json` 的 SP-C5 `manuscript_tokens` 数组已含 `"two to eleven columns"`。正文 §6 修订段中对应 token 为「with **two to eleven columns**」，逐字一致。**放行条件满足。**

---

#### F4：附录侧列数分布千位分隔排版修正 —— **已满足**

修订前（歧义态）：`2:1 586`、`4:2 422` 等（空格既是分隔符又是千位符）

修订后：`2: 1586`、`3: 1452`、`4: 2422` … `11: 4`，所有数字去除千位分隔空格，并追加校验句 `（求和 = 7134，与例数对账）`。

手工对账：1586 + 1452 + 2422 + 530 + 541 + 483 + 102 + 12 + 2 + 4 = **7134** ✅。**放行条件满足。**

---

#### F5–F9：顺带检查，未发现改错

diff 中涉及的纯措辞改动包括：

1. `named separately here, so that no finding is bound to the wrong one` → `named separately`（精简，含义不受损）
2. `frozen bucketing rule` → `frozen hash-threshold bucketing rule`（与 §6 正文措辞对齐，更精确）
3. `A table layer makes samples definable` → `Here, a table layer makes samples definable`（加 `Here,` 改善段落衔接流）
4. `322 and 467 records of 1970 under the two conventions` → `322 records of 1970 under the convention yielding 0.0298, and 467 under the one yielding 0.2233`（消除歧义，同时承载 F1 登记）
5. 行数分布 `4:1 141` → `4: 1141` 等千位分隔去除（随 F4 同批修正）

以上五项均未引入事实错误或逻辑断裂。

---

### 总体判定：**ACCEPT**

四条放行条件全部满足，F5–F9 措辞改动未检出错误。本轮不重开 C3-N3 / C3-N4。
