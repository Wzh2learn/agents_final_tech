# Loop C confirmation pass on the revised §6 and SP-C5 (model qwen3.8-max, round 3)

> Dispatched by Loop D on 2026-09-25 as the confirmation round after both v2 reviews returned REVISE.
> Mode: evidence packet inline (revised §6 text, claim manifest, divergence table, v2 results doc),
> no tools, 1 turn, cost not reported by bare mode. Packet sha256
> `801193769790242aa69cb0d3558e84adad3d98716865ddb51246a71c5fc46fc4` (25 937 bytes).
> Session PID 3828335 on GB10; ran concurrently with the deepseek-v4-pro confirmation, no shared context, no resume.
> Verdict: **ACCEPT** (10 of 11 named issues fixed, qwen m-4 partially fixed with the remainder temporally
> posterior; 0 new Blocking, 0 new Major, 6 non-blocking editorial items; 2 post-obligations recorded below).
> Body below is the session final message verbatim; assembled by Loop D without edits.

Post-obligations carried into the ledger by Loop D (not part of the verbatim body):
1. record this confirmation and register it against SP-C5, annotating that review records are audit
   records rather than measurement evidence;
2. the next review packet must attach the SOURCE_GO staging doc and the split design/capacity doc.
Loop D note: the reviewer's quotation of the revised text as "hash-throttling bucketing rule" is a
transcription slip; the manuscript reads "hash-threshold bucketing rule" (grep: 1 hit for threshold,
0 for throttling). The manuscript was not changed to match the misquote.
# Loop C 确认性复核（confirmation pass，第 3 轮）

**范围**：仅核对被点名的 11 条问题 + 1 项分歧处置；检查修订是否引入新问题。**方式**：只读，未修改任何文件，未联网，未调用工具。
**依赖声明**：本轮审阅包只含附录 D（步级 v2 结果件）。语料侧数字（2409 / 768 / ten clusters / SOURCE_GO 日期与 digests）的原始件不在本包内，我沿用上一轮两份审稿已落档的核验结论（附录 C §1：「9 项全部与 artifact 一致」），并对这些项标注为「已登记、本包不可复核」。

## 判定摘要

| 类别 | 结果 |
|---|---|
| 11 条点名问题 | 10 条**已修复**，1 条（qwen m-4）**部分修复**（剩余动作在时间上必然后置） |
| 分歧处置（SP-C5 status） | **可接受** |
| 新引入问题 | Blocking 0 · Major 0 · Minor 6 · Advisory 4 |
| forbidden marker | 0 命中（含一处近似项已排除） |
| 与 SP-C1..SP-C4 冲突 | 无 |
| 与附录 D §7 四条禁令 | 无违反 |
| **总体判定** | **ACCEPT**（附 2 项后置义务 + 6 项非阻断编辑项） |

---

## 1 逐条核对

**B-1 / B1（Blocking，全称量化）——已修复。**
修订后原文：「while the schema-matching corpus that does carry an action vocabulary contains ten table-pair clusters, **which under the frozen hash-threshold bucketing rule** leaves the development layer empty and yields ten independent units」。全称量化短语已消失，量词被收敛到「当前在 force 的那一条冻结规则」，与 G-B 条目（秩分位规则在簇数 ≥4 时可保四层非空）不再冲突：稿件现在只主张 hash-threshold 规则下 dev 层为空，而 G-B 恰好说明换个规则结论会不同，两者相容。同时保留「ten independent units」——该结论只依赖簇数、不依赖分桶规则，未受收窄影响，处理正确。
*残留*：限定语只落在稿件，未同步到 SP-C5 claim 文本（见 C3-N4）。

**qwen M-1（criterion (ii) 因果焊接）——已修复。**
原文：「Because that detector measures reasoning-step checkpoints while criterion (ii) concerns reproduction of the frozen header-injection leaf-state cells, **the two are different measurement objects**; the leaf-state reproduction clause therefore remains **untested rather than failed**, and what the fired stop condition establishes is the boundary of the step-level route itself。」
与附录 D §7 第 2 条禁令逐字对齐（「表头注入族判别 vs 推理步检查点，不同测量对象」），且 SP-C5 的 claim 与 scope_limit 两处同步了同一表述，未出现「稿件弱、治理件强」的反向失配。停止条件的证明力被限定为「the boundary of the step-level route itself」，未外溢到 criterion (ii)。

**qwen M-2 / deepseek M2（"partially met" 模糊）——已修复。**
「partially met」已删除，改为「Progress against criterion (i) is now measurable, **clause by clause**」，并逐项落地：SOURCE_GO 通过（含日期与 per-file digests）／UID-disjoint 簇级分配就绪（report-level 而非 dataset-level）／**SPLIT_GO 未通过**（含被扣层事实与成因）／table-layer（ten table-pair clusters → dev 层为空）／label 缺口显式改判归属（「it belongs to the **label gate** rather than to criterion (i)」）／原递延理由显式记为开放（「remains open and is not claimed here」）。缺口不再被低报，且未把 label 缺口冒充为 criterion (i) 的进展。
*残留*：三条语料的身份绑定不清（见 C3-N3）。

**qwen M-3（claim 丢掉 "geometrically"）——已修复。**
SP-C5 claim 现为「a cluster-level UID-disjoint split instrument was built and **shown geometrically fillable**, but SPLIT_GO itself remains blocked」，与稿件强度一致，并补齐了 blocked 的两条成因。采纳保守一侧、且不使 deepseek 的「准确」判断失效，处置逻辑成立。
*nit*：「shown geometrically fillable」省略了宾语（fillable 的对象是 four role layers），建议补全。

**deepseek M1（"Detection figures" 狗哨）——已修复。**
含 "Detection figures" 的整句已删；§6 全文不出现 detection 0.99068 / 0.99358、localization 1.0、root_cause 1.0 中任何一个；分母改以中性表述给出，并自带反能力化声明：「which is reported **to bound the route, not as a capability**」。附录 D §4 关于 root_cause=1.0「是健全性检查、不是性能结果」的警告因此无从被误引。
*残留*：新的中性措辞本身缺 artifact 锚（见 C3-N2）。

**deepseek m1（一位小数）——已修复。** 「16.3% to 23.7%」，与附录 D §7 的 322/467 ÷ 1970 逐位一致；manuscript_tokens 同步为 "16.3% to 23.7%"，token 与最终措辞逐字取值。

**deepseek m2（拆段）——已修复。** criterion (i) 与 criterion (ii) 各自独立成段，段首分别为「Progress against criterion (i)…」与「Criterion (ii) has not been tested…」，两条线不再交错；这一拆分同时降低了「label 缺口 ↔ 步级停止」被读者焊接的风险。

**deepseek m3（术语混淆）——已修复（附核验项）。** 「ten origin clusters」→「ten table-pair clusters」，与 independence_cluster / report cluster 不再同形。*核验项*：新术语是否为语料件自有措辞，本包无法确认（见 C3-V1）。

**qwen m-1（口径碰撞）——已修复。** 「are not reported **as results**; the two paragraphs that follow report the measured boundaries and the fired stop condition from those attempts」，与末段「报告边界量」不再互斥，且与「preregistered-but-unreported」形成一致口径。
*残留*：前向引用计数不准（见 C3-N1）。

**qwen m-3（"admissibility rules" 无逐字对应）——已修复。** 改为「whose corpus, fault families and stop condition were fixed before any detector existed」，与附录 D §6「一套在检测器存在之前就已冻结的步级故障注入语料（1 970 条…双跑逐字节相同）」及 V2-3 对族语义/故障定义不得改动的禁令相容，描述性替代了自造术语。
*残留*：改写造成 "corpus…whose corpus" 重复（见 C3-N5）。

**qwen m-4（paper_result=false 的引用前置条件）——部分修复。**
已完成：两份独立审稿件入仓并登记进 SP-C5 evidence（`...loopc_review_teacher_review_v2_qwen3.8-max.md` / `...deepseek-v4-pro.md`），附录 C 作为处置件落档。
未完成：这两份是 **REVISE 轮**的审计结论，不是终局结论；本确认件的结论尚不存在于仓内，因而也尚未登记。此外 SP-C5 未记录「引用许可指向哪一份审计件」的指针，evidence 数组里测量件与审计件混列（见 C3-N6）。
**本轮我作为独立审计人对被引数字的结论**：0.0298、0.2233、pre-set 0.5、1970、16.3%、23.7% 六项与附录 D 完全一致（复算见 §3）。**但 `paper_result` 的翻转是治理动作，不由审稿人作出**，本件不视为已翻转；稿件目前仅以边界量引用，符合该标记的意图。

**qwen m-5（SP-C3 / SP-C5 scope_limit 逐字重复）——已修复。**
SP-C3 加了归属限定「No second-dataflow result and no second-scorer result are claimed **for the ranking-stability findings of this entry**; the separately reported boundary measurements … **live in SP-C5**」；SP-C5 改为「This entry reports a boundary finding, not a substantive result」。重复消除，且建立了单向指针，表面自相矛盾解除。

**分歧处置（SP-C5 status 保留原值 + scope_limit 首句）——可接受。**
理由独立成立，不需同意任一方：(1) 现有 status 集合本就不是单族（SP-C4 = `mechanism_case_only` 已在 `supported_*` 之外），"不统一" 不构成硬伤；(2) deepseek 的实质关切是「不被读作被驳回的主张、横向可比」，scope_limit 首句已直接满足；(3) 改名会损失 "attempted + stopped" 这一事实陈述，属净损失。分歧未合并、理由显式记录，符合处置纪律。
*建议（非阻断）*：若 status 将来被程序消费，加一个伴生字段（如 `result_class: "boundary_finding"`）而不是改 status。

---

## 2 修订引入的新问题（全部 Minor / Advisory，无一阻断）

**Minor**
- **C3-N1** 前向引用计数错误（m-1 修订引入）：该句之后依次是「Reinstatement criteria…」段、criterion (i) 段、criterion (ii) 段，共三段；「the two paragraphs that follow」字面指向的是「递延判据段 + criterion (i) 段」。建议改为 "the final two paragraphs of this section"。
- **C3-N2** 新中性措辞缺 artifact 锚（M1 修订引入）：「The **reconstructible portion** of that corpus」——附录 D 对该分母的自有 gloss 是 clean_faithful（322 / 467）。数值上二者同量（interpretation_fidelity 0.16345178 × 1970 = 322），但用词属解释性引入，与 qwen m-3 同类。建议：「the portion of records with faithful reconstruction (clean-faithful denominators 322 and 467 of 1970, i.e. 16.3% to 23.7%)」。
- **C3-N3** criterion (i) 的候选语料身份未绑定（M-2 拆条款后显影）：SOURCE_GO 通过的语料是否**具备 table layer**，稿件未交代；三条语料（acquisition / schema-matching / transfer）分属不同条款，易被读成同一条语料的四个条款。结论方向不受影响（SPLIT_GO 未通过 + dev 层为空 ⇒ (i) 不成立），但建议加一句绑定候选语料身份。
- **C3-N4** B-1 的限定语未同步到治理层：SP-C5 claim 写「leaves the development layer empty **at ten clusters**」，缺 "under the frozen bucketing rule"。这正是 G-B 反驳的推理形式（把规则依赖读成语料内禀属性）。**误差方向保守**（夸大的是阻塞项、不是能力），故列 Minor 而非 Major；建议下次治理触碰时补限定。
- **C3-N5** 语法冗余（m-3 修订引入）：「a corpus of 1970 frozen step-level records **whose corpus**, fault families and stop condition were fixed」。建议 "whose contents, fault families and stop condition"。
- **C3-N6** 新写的 SP-C5 scope_limit 第二句枚举不全：「the reported quantities are **the measured boundary and the fired stop condition**」，但 claim 还包含 SOURCE_GO 通过与 2409/768 的分层容量算术。免责句窄于 claim 内容。建议扩为「procedural gate status, split-capacity arithmetic, the measured boundary, and the fired stop condition」。

**Advisory（多为既存项，不计入本轮门槛）**
- **C3-A1** 指代复用：「that corpus」在三句内先后指 acquisition 语料与 schema-matching 语料；label 缺口的归属对象可被误绑。建议给两条语料各起短名。
- **C3-A2** 附录 C §3 称 token 集「覆盖段落全部数字」，但 "four role layers" 与日期 2026-09-25 未入 token（SP-C1 有 "five thresholds" 先例）。补 token 或改软措辞，二者择一。
- **C3-A3** limitation 1「the evidence comes from **one public tabular corpus**」与其后两段引入的第二数据流语料、步级（非表格）语料相邻；建议限定为「the evidence supporting the reported results」。
- **C3-A4** 基础设施标识入稿：「the :8004 judge」（既存措辞，本轮重复一次）。外发前建议去端口化为 "the frozen reference judge of Section 5.3"。
- **C3-A5** manifest 排版：evidence 数组中有一处逗号独行（`…step_checkpoint_score_v2_results.md"` 换行 `,`）。JSON 合法但显手工追加痕迹，建议格式化并跑一次解析校验。

---

## 3 全局一致性检查

**数字复算（本轮我独立核对附录 D）**

| 稿件/claim 字符串 | 附录 D 来源 | 复算 | 结论 |
|---|---|---|---|
| 0.0298 | §1 表，44 / 1478 | 0.029770 | ✓ |
| 0.2233 | §1 表，330 / 1478 | 0.223275 | ✓ |
| pre-set 0.5 | §1 预注册阈值 | — | ✓ |
| 1970 frozen step-level records | §2 / §6 | — | ✓ |
| 16.3% / 23.7% | §7，322 / 467 ÷ 1970 | 0.163452 / 0.237056 | ✓ |
| 两种读法并列 | §7 第 4 条禁令 | 0.0298 与 0.2233 同时出现 | ✓ |

**forbidden marker**：对 §6 全文逐项扫描 10 个 marker，**0 命中**。近似项已排除：「The **main finding** is methodological」不构成 "main thread"；无 "Ruling "、无 "TODO"、无 "append-only"、无 `[logs/graph/eval/`、无 `[docs/experiments/`、无中文 marker。稿件亦未出现 "Loop C/D" 或任何仓内路径（路径只存在于 manifest，属允许位置）。

**与 SP-C1..SP-C4**：无冲突。特别核过两处易撞点——(a) SP-C2 的 scope_limit「Localization value cannot be established…」：稿件未报告任何 localization / root_cause 数字，无碰撞；(b) SP-C3 的 ranking-stability 与 SP-C5 的边界量已通过归属限定分工，无重复计数。SP-C1、SP-C4 未被本轮修订触及。

**与附录 D §7 四条禁令**：逐条通过（不称能力／不称复现或替代冻结 Stage E／不反推动作标签与可学性／不只引 scaled 一路）。另：§4「root_cause=1.0 不是性能结果」与 §5「518/3096 未解释残余」均未被稿件引用，前者安全，后者建议在该路线若被重提时补披露（当前不要求）。

**新的过度主张 / 口径焊接**：未发现。两条线现已物理分段，且 criterion (ii) 段自带「different measurement objects」隔离句；未出现把 SOURCE_GO 通过读作 arm 复活、或把停止条件读作 Stage E 结论的路径。

---

## 4 总体判定：**ACCEPT**

11 条点名问题中 10 条已修复、1 条（qwen m-4）的剩余部分在时间上只能后置于本件；Blocking 与 Major 均已清空；新引入的 6 条 Minor 全为措辞/枚举/指代级，无一改变数字、量词方向或结论强度。分歧处置可接受。

**放行后置义务（必须做，不需再审）**
1. 将本确认件结论落档，并在 SP-C5 evidence（或新增的审计指针位置）登记；同时标注 evidence 中两条 loopc 条目为「审计记录」而非「测量证据」，以保住 evidence 字段语义。`paper_result` 是否翻转由治理方决定，本件不代为翻转。
2. 下一轮审阅包补附 `2026-09-25_source_go_p1p2_staging.md` 与 `2026-09-25_phase1a_split_design_and_layer_capacity.md`（承接 qwen m-2）。

**编辑项处置规则**：C3-N1/N2/N5/N6 与 A1/A2/A5 属纯措辞，可直接改；**凡触及数字、量词、规则限定或语料归属的改动（C3-N3/N4）须回到 diff 级确认**，不需重审全文。

**本包不可复核项（C3-V1）**：「ten table-pair clusters」「frozen hash-threshold bucketing rule」「2409 lineage UIDs / 768 report clusters」「SOURCE_GO 通过日期与 per-file digests」——已登记于 SP-C5 evidence，但原件不在本轮包内；本轮沿用上一轮两份独立审稿的核验结论，未自行确认。
