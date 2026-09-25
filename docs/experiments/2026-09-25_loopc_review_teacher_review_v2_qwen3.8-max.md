# Loop C independent review of the evaluation-track manuscript, round v2 (model qwen3.8-max)

> Dispatched by Loop D on 2026-09-25 under the goal completion criterion (independent dual-model review),
> because the §6 external-validity paragraph and claim SP-C5 were added after the previous ACCEPT chain.
> Mode: evidence packet inline (manuscript + claim manifest + step-checkpoint v2 results + split design/capacity),
> no tools, 1 turn, cost not reported by bare mode. Packet sha256
> `ef6ddc7ac80b865d5441993b6187a2cd2db1789428c925fb36d2be39cf56fb78` (61 097 bytes).
> Session PID 3812664 on GB10; ran concurrently with the deepseek-v4-pro session, no shared context, no resume.
> Limitation carried over from round v1: this is a text-level review; the underlying JSON artifacts were not recomputed.
> Body below is the session final message verbatim; assembled by Loop D without edits.
# Loop C 独立审稿意见

审查对象：`paper/teacher_review_draft_v1.md` §6 末段（"Progress against those criteria…"）+ `paper/claim_manifest_v1.json` SP-C5 条目。只读审查，未修改任何文件，未联网。

---

## 1. 总体判定：**REVISE**

新段落的核心动作是正确的：只报边界、不报性能，双读法并列，显式拒绝引用检出率数字，与附录 C §7 的"不得主张"清单基本吻合。全部 9 个受查数字中 8 个与 artifact 逐字一致。但存在 1 处对 artifact 的过度概括（Blocking）和 3 处框架性失准（Major），修掉即可回到 ACCEPT 轨道。

---

## 2. Blocking issues

**B-1. "under any proportional assignment" 是被其自引 artifact 直接反驳的全称量化**
- 位置：§6 末段第 4 句（"…contains only ten origin clusters, which leaves one role layer empty **under any proportional assignment**…"）
- 证据指针：附录 D §5 W1 只证明**冻结的哈希阈值分桶规则**下 dev 得 0 簇（`EMPTY_REQUIRED_PARTITION:proposal_train.dev`，且"即使授权 gate/sealed，dev 仍为空"）；但附录 D §8 G-B 明文写道，改用"按簇哈希排序后的秩分位"规则"**可保证簇数 ≥4 时四层非空**"。10 ≥ 4，即存在一种（秩分位意义上的）比例分配使四层全非空。稿件的"any"与所引 artifact 的 G-B 条目直接矛盾。
- 建议修法：改为 "…leaves one role layer (dev) empty **under the frozen hash-threshold bucketing rule, independent of the governance ruling**, and caps independent units at ten"。一句话可修，不需要动结论（W3 的 K=10 上限不依赖该量词）。
- 风险等级：**高**（对 artifact 的失实概括，且发生在承载数字的句子中；敌意审稿人可据此质疑整段的可信度）。

---

## 3. Major issues

**M-1. Criterion (ii) 的失败被错误归因：附录 C 明令该 scorer 与 leaf-state cells 是"不同测量对象"**
- 位置：§6 末段第 5–7 句（"Criterion (ii) was attempted and failed… so the scorer **cannot reproduce the leaf-state cells**…"）
- 证据指针：§6 既有 reinstatement 段把 criterion (ii) 定义为"a second scorer independent of the :8004 judge **reproduces the leaf-state cells**"（即 §5.3 的 120 个 leaf-state 校准格，TAT-QA 表头注入测量对象）。而附录 C §7 第二条明文："**不得称本件复现、重算或替代冻结 Stage E 口径（表头注入族判别 vs 推理步检查点，不同测量对象）**"。即：这个 1970 条 FinQA 步级重执行 scorer 从一开始就不是 criterion (ii) 的合格实例化——它的停止条件触发于**其自身**预注册（pct 保真度 < 0.5），而非"复现 leaf-state cells 失败"这一实测。稿件的因果句 "fidelity… below 0.5, **so** the scorer cannot reproduce the leaf-state cells" 把两条不同口径的失败焊接成一条，暗示 criterion (ii) 被"直接测试并证伪"，实际上 leaf-state cells 复现条款是**未被测试**（untested），不是**测试后失败**（failed）。
- 建议修法：拆开因果，例如："A candidate route toward an independent second scorer — a model-free step-level re-execution detector over a second corpus — was stopped by its own pre-registered stop condition (…). Because that detector measures reasoning-step checkpoints rather than the frozen header-injection leaf states, the leaf-state-cell reproduction clause of criterion (ii) remains **untested**; what the fired stop condition establishes is the boundary of the step-level route itself."
- 风险等级：**高**（触碰 artifact 明写的引用禁令的边界；混淆两个测量口径正是本论文方法论立场所反对的事）。

**M-2. "The label layer is what remains unmet" 低报了 criterion (i) 的实际缺口**
- 位置：§6 末段第 2–4 句
- 证据指针：reinstatement criterion (i) 的条款是 "**with a table layer**" + "passes SOURCE_GO **and SPLIT_GO** with UID-disjoint layers"。对照附录 D：(a) SPLIT_GO 并未通过——§6 判定行明文 "动作包 SPLIT_GO = BLOCKED（W1–W4）"，且 §6 对位表写明 **FinQA 自身 gate/sealed 两个 partition 也为空**（注册表 `role_fit` 未含，"FinQA 仅后两者空"），稿件只以 "geometrically fillable" 暗示、未披露治理扣层这一事实；(b) criterion (i) 原文里根本没有"label layer"条款——标签语义是 Phase 1a 的 LABEL_GO 门（附录 D §5.2），稿件把它安到 criterion (i) 头上，属于条款错位；(c) 原递延理由（transfer corpus 缺 table layer，无法定义 per-family constructible sample counts）在新段落中既未确认解决也未确认仍开放。
- 建议修法：逐条款映射一句话：SOURCE_GO ✓（2026-09-25，per-file digests）；UID-disjoint 簇级分配 ✓（构造性质，附录 D §2）；SPLIT_GO ✗（FinQA gate/sealed 因注册表 role_fit 被扣，Valentine dev 因 W1 结构性为空）；table-layer 条款状态显式写明（仍未确立/由何 artifact 回答）。把 label 缺口明确标注为"Phase 1a LABEL_GO（criterion (i) 之外的门）"。
- 风险等级：**中高**（不是数字错误，但"criterion (i) is partially met + 唯余 label"的表述会让读者高估距 reinstatement 的距离之近）。

**M-3. SP-C5 的 claim 文本丢掉了 "geometrically" 限定词，与 manuscript 和 artifact 双双不一致**
- 位置：`claim_manifest_v1.json` SP-C5 `claim` 字段："SOURCE_GO and **UID-disjoint layer assignment were achieved**"
- 证据指针：manuscript 自己写的是 "the four role layers are **geometrically** fillable"；附录 D §4.1 读数原文 "四层在 M ≤ 12 时全部非空（**含被扣住的两层**），几何上完全可填"，§6 判定 "SPLIT 仪器 = READY；动作包 SPLIT_GO = BLOCKED"。manifest 把"几何可填 + 仪器就绪"升格为"layer assignment achieved"，是治理文件层面的过度主张。
- 建议修法：claim 改为 "…SOURCE_GO was passed and a cluster-level UID-disjoint split instrument was built and shown **geometrically** fillable (SPLIT_GO itself remains blocked: gate/sealed withheld by registry role_fit; the action-flow dev partition is structurally empty at K=10), while action-label semantics and step-level re-execution fidelity were not achieved…"
- 风险等级：**中**（manifest 是对外问责面，措辞必须不弱于 manuscript 的限定强度）。

---

## 4. Minor issues

**m-1. §6 内部时态/口径碰撞："are not reported" vs 第三段的详细报告**
- 位置：§6 第二段 "A second dataflow and a second scorer were preregistered but **are not reported**" 与末段并存。
- 证据指针：末段实际上**报告了**第二次 scorer 尝试的边界量（0.0298/0.2233/停止条件）。两段并不矛盾（arms 的结果未报 ≠ 边界未报），但未点破。
- 建议修法：第二段末尾加半句 "…are not reported **as results**; the final paragraph of this section reports the measured boundaries and the fired stop condition from those attempts."
- 风险等级：低。

**m-2. SOURCE_GO 细节无法在所提供的附录内核验**
- 位置：§6 末段第 3 句 "passed SOURCE_GO on 2026-09-25 under an approved minimal acquisition scope **with per-file digests recorded**"。
- 证据指针：SP-C5 evidence 列有 `docs/experiments/2026-09-25_source_go_p1p2_staging.md`，但本次审稿附录只含 C、D 两件；附录 D 头部仅交叉引用 "（SOURCE_GO）" 与 sha256 manifest 机制。日期与"最小下载范围（D-C）"可由附录 D 头部佐证，"per-file digests" 只能间接推定。
- 建议修法：无需改稿件；在下轮审阅包中附 SOURCE_GO 件，或在该句后加 evidence ledger 指针。
- 风险等级：低（非不一致，仅未核验）。

**m-3. "admissibility rules were fixed before any detector existed" 的措辞在附录 C 中无逐字对应**
- 位置：§6 末段第 6 句。
- 证据指针：附录 C §6 逐字为"一套**在检测器存在之前就已冻结**的步级故障注入语料（1 970 条…）"；故障族与判据冻结可由 V2-3 禁令（"不得改族语义、改故障定义"）与预注册 sha `6ee1d06b…` 推出，但 "admissibility rules" 一词未出现（最接近的是 unevaluable 分类与 clean_faithful 分母定义）。
- 建议修法：改为 "…whose corpus, fault families, and stop condition were frozen before any detector existed"，或保留原词但在 evidence ledger 中给出 admissibility 规则的出处指针。
- 风险等级：低。

**m-4. `paper_result = false` 引用门的程序闭环**
- 位置：附录 C 头部 "未经独立 Loop C 审计前不得被论文引用"；稿件已引用。
- 证据指针：本审稿即该审计。判定：所引数字（0.0298/0.2233/0.5/1970/16–24%/停止条件触发）均为边界量而非性能量，符合附录 C §7 全部四项禁令（含"两读法必须同时出现"——稿件双列 ✓；未引 detection 0.99068/0.99358 与 localization 1.0 ✓）。但引用合法性以本审计结论落档 + B-1/M-1/M-2 修复为前提。
- 建议修法：将本次 Loop C 结论写入 evidence ledger，并在 manifest SP-C5 evidence 中登记审计件路径。
- 风险等级：低（程序性）。

**m-5. SP-C3 与 SP-C5 的 scope_limit 逐字重复，产生表面自相矛盾**
- 位置：manifest SP-C3 与 SP-C5 的 `scope_limit` 均以 "No second-dataflow result and no second-scorer result are claimed" 开头。
- 证据指针：SP-C5 的 claim 同时报告了第二次 scorer 的实测保真度。两条并存时，SP-C3 的旧措辞（写于 SP-C5 之前）会被读成"manifest 整体否认存在任何 second-scorer 数字"。
- 建议修法：SP-C3 scope_limit 加限定 "…are claimed **for the ranking-stability results of SP-C3**"；SP-C5 scope_limit 首句改为 "No capability, detection-performance, or arm-level result is claimed; the reported quantities are the measured boundary and the fired stop condition."
- 风险等级：低。

---

## 5. 数字逐项核对表

| # | 数字 | 稿件原文（§6 末段） | artifact 原文 | 一致性 |
|---|---|---|---|---|
| 1 | 2409 | "2409 lineage UIDs over 768 report clusters at full population" | 附录 D §4.1，M=1 行：UID = 2 409；"UID 列 = 宇宙内不同 lineage root 数（含被扣住的行）" | ✅ 一致 |
| 2 | 768 | 同上 | 附录 D §4.1，M=1 行：入选簇/总簇 = 768/768（cluster = 年报 filing） | ✅ 一致 |
| 3 | 1970 | "a corpus of 1970 frozen step-level records" | 附录 C §2 "M=1 主语料（1 970 条记录）"；§6 "步级故障注入语料（1 970 条，sha `03cf47c3…`，双跑逐字节相同）" | ✅ 一致 |
| 4 | 0.0298 | "fidelity … was 0.0298 under one percent convention" | 附录 C §1 表：`mantissa_direct`，44 / 1 478，pct 保真度 **0.0298**，"是否 ≥0.5：否" | ✅ 一致（且稿件正确限定为 percent-form，未与全量 interpretation_fidelity 0.163 混用） |
| 5 | 0.2233 | "0.2233 under the other" | 附录 C §1 表：`mantissa_scaled`，330 / 1 478，**0.2233**，"否" | ✅ 一致（两读法并列，符合附录 C §7 第四条禁令） |
| 6 | 0.5 阈值 | "both below the pre-set 0.5 threshold" | 附录 C §1 预注册原文："若 v2 在两种读法下的 pct 形态保真度均仍低于 0.5，则…本线停止" | ✅ 一致 |
| 7 | ten origin clusters | "contains only ten origin clusters" | 附录 D §4.2：Valentine M=1 入选簇 10/10；W3 "实测 K = 10"；"簇数 10 是批准范围的上限" | ✅ 一致 |
| 8 | one role layer empty | "leaves one role layer empty **under any proportional assignment**" | 附录 D W1：阈值分桶下 dev band 分到 0 个簇（`EMPTY_REQUIRED_PARTITION:proposal_train.dev`），"即使授权 gate/sealed，dev 仍为空"；**但** §8 G-B：秩分位规则"可保证簇数 ≥4 时四层非空" | ⚠️ **数字内核一致**（冻结规则下恰好一层结构性为空），**量词不一致**（"any proportional assignment" 被 G-B 反驳）→ 见 B-1 |
| 9 | 16%–24% | "conditional on a faithful subset of 16% to 24%" | 附录 C §7："分母是 clean_faithful（322 / 467，占 1 970 的 **16.3% / 23.7%**）"；§2 interpretation_fidelity 0.16345 / 0.23706 | ✅ 一致（合理取整） |

**结论：无数字级不一致（第 8 项为量词级失准，非计数错误），故无因数字触发的强制 Blocking；B-1 以失实概括立案。**

---

## 6. SP-C5 条目评估

- **status（`attempted_stopped_by_preregistration`）**：对 scorer 一半准确；对 dataflow 一半偏悲观——dataflow 是"部分推进"（SOURCE_GO ✓、几何门 ✓、SPLIT_GO ✗）而非"stopped"。可接受，但 claim 文本应像 manuscript 一样用 "partially met / stopped" 双轨措辞。不建议降级，不需要新造 status。
- **manuscript_tokens**：四个 token（"0.0298"、"0.2233"、"1970 frozen step-level records"、"2409 lineage UIDs"）均在 manuscript 中逐字命中 ✅。但漏掉了同样承载主张的 "768 report clusters"、"ten origin clusters"、"0.5"、"16% to 24%"——建议补齐，使 token 集覆盖段落全部数字（对齐 SP-C1/C2 的密度）。
- **evidence**：三件中两件（附录 C、D）已核验且支撑充分；`2026-09-25_source_go_p1p2_staging.md` 未随审阅包提供（见 m-2）。evidence 链**基本足以支撑**其主张。
- **scope_limit**：方向正确（"the reported quantity is the measured boundary and the fired stop condition, not a performance result"），但与 SP-C3 逐字重复造成表面矛盾（m-5），且未覆盖 M-1 揭示的"leaf-state cells 条款实为 untested 而非 failed"这一边界。
- **总评**：**改写，不降级、不加强**。claim 按 M-3 加 "geometrically / SPLIT_GO remains blocked" 限定；scope_limit 补一句 "the leaf-state-cell reproduction clause of reinstatement criterion (ii) remains untested; the stopped route measured a different object (reasoning-step checkpoints)"。

**方法论风险专项（审查任务 5）**：新段落在"报告边界 vs 报告性能"上的处理是**合格的**——只引用触发停止条件的保真度数字，显式声明 "Detection figures … are deliberately not claimed as evidence here; what is claimed is the boundary itself"，未出现 0.99068/0.99358/1.0 中任何一个被禁数字，未把 16%–24% 子集分母的检出率暗示为整体能力（该子集仅作为"为何不引用检出数字"的限定条件出现）。唯一残留风险即 M-1 的口径焊接，修复后该段可作为"负结果如实上报"的正面示范。

**Forbidden markers（审查任务 4）**：对新增文本逐项扫描 "TODO / append-only / main thread / Loop D / Ruling / ruling / [logs/graph/eval/ / [docs/experiments/ / 主线程 / 决策"——**均未出现** ✅。与 SP-C1..C4 无主张冲突；与 SP-C2（matched-FPR 无增益）、SP-C4（机制案例不作贡献）口径一致；Abstract 与 §7 无需改动（二者均未涉及递延 arms，新段落未引入任何需要上提至 Abstract 的主张）。

---

## 7. 下一步 3 项建议

1. **修 B-1 + M-2（一句话级改动）**：将 "under any proportional assignment" 收窄为 "under the frozen hash-threshold bucketing rule, independent of the governance ruling"；并在 criterion (i) 进度句后补一个显式逐条款清单（SOURCE_GO ✓ / UID-disjoint ✓ / SPLIT_GO ✗——含 FinQA gate/sealed 被注册表 role_fit 扣住这一事实 / table-layer 条款状态 / label 缺口归属 LABEL_GO 而非 criterion (i)）。
2. **修 M-1**：按第 3 节给出的措辞把 criterion (ii) 的因果链拆为"候选路线被自身预注册停止条件终止"+"leaf-state-cell 复现条款因测量对象不同而保持 untested"，使段落与附录 C §7 第二条禁令完全对齐；同句顺带处理 m-3 的 "admissibility rules" 措辞。
3. **修 manifest（M-3 + m-5 + token 补齐）并闭环引用门（m-4）**：SP-C5 claim 加 "geometrically fillable / SPLIT_GO remains blocked" 限定；SP-C3 与 SP-C5 的 scope_limit 去重并各自加归属限定；manuscript_tokens 补 "768 report clusters"、"ten origin clusters"、"0.5"、"16% to 24%"；将本次 Loop C 审计结论登记入 evidence ledger，以满足附录 C `paper_result = false` 的引用前置条件。

完成上述三项后，本审稿人预期可转 ACCEPT，无需重审全文（仅需复核 §6 末段与 SP-C5 条目的 diff）。
