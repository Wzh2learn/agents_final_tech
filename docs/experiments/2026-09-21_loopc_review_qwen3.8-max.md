# 独立审稿报告

**审稿依据**：paper-review-check（五焦点+blocking/polish 分列）、experiment-autopsy（先裁决后尸检、预注册判据纪律）、eval-harness（冻结输入/判定分布/评分者校准视角）、algorithm-description（先读代码再核描述、不确定处显式标注）。
**审稿方式**：只读。所有引用数字均已对照仓内工件逐一复核（复核范围：`scripts/eval_checkpoint_aggregate.py` 全文、`config/eval_checkpoint_trees.json` 全文、t1/t2/t4/t6/d1/d2/d3a/d3b/d3_recompute/tables_v2/discrimination_report/aggregate_report/m2_judge_report 共 13 个 JSON 工件、4 份实验源文档、W1 窗口报告）。未联网，未引用任何未核实外部文献。

---

## 1. 总体判定：**REVISE**

证据链闭合度显著高于常规草稿（抽查的 ~60 个数字中仅 2 处指针错挂、0 处数值捏造），预注册判据、降级条款、"失败判据如实报失败"的纪律执行到位。但存在 **2 个 Blocking 级内部矛盾**（均出在"论文自述 vs 被引证据"层面，恰好违反论文自己立下的 "exactly as implemented / every number carries an artefact path" 纪律），修复成本低、必须修复后方可进入投稿流程。另有一条论文之外的外部门（专利申请状态，advisor 文档 §2.3）不在本审稿可解范围。

---

## 2. Blocking issues

### B1. hinge 叶"缺失证据给 0 分"的方法描述与冻结配置直接矛盾（三处同源错误）

- **文件+行号**：
  - `paper/draft_v0_s1_s2_s6.md:62-63`（"hard-gate leaves whose absent evidence contributes zero instead of the neutral default"）
  - `paper/draft_v0_s1_s2_s6.md:122-127`（"a hinge leaf with absent evidence is scored 0 by its configured missing score rather than the neutral default, which is why the missing caliber is defensive at exactly the leaves that guard the outcome"，指针指向 config）
  - `paper/draft_v0_s1_s2_s6.md:533`（自审注记"hinge 用 0、其余用中性 5"）
  - `docs/experiments/2026-09-20_algorithm1_lines_vs_impl.md:30`（§2 特化①"缺失分数为 0（树配置逐叶 missing_score: 0）而非其余叶的中性 5"）
- **证据指针**：`HINGE_ROUTES`（`scripts/eval_checkpoint_aggregate.py:149`）= {overall_status_binary, pass_rate_contract, nf_pass_rate}，对应 5 个 hinge 叶。`config/eval_checkpoint_trees.json` 实测：
  - `parse.doc.ok`（:38，hinge）missing_score **0** ✓
  - `qa.retrieval.source_required`（:83，hinge）missing_score **5** ✗
  - `qa.numeric.exact`（:101，hinge）missing_score **5** ✗
  - `qa.numeric.number_grounding`（:102，hinge）missing_score **5** ✗
  - `qa.refusal.deterministic`（:121，hinge）missing_score **5** ✗
  - 反向也不成立："其余用中性 5"错——4 个**非** hinge 的 parse 叶（:39 run_completed、:48 row_pass_rate、:57 hit_rate_achievement、:66 reconcile_derived）全部 missing_score **0**。
  - 实际策略是**按树分**（parse 树全 0 / qa 树全 5），不是按 hinge 分。5 个 hinge 叶中仅 1 个满足论文声称的"defensive zero"。
- **影响边界**：活工件跑批 `degraded = []`（`logs/graph/eval/checkpoint_aggregate_report.json`），缺失路径从未触发，**所有实测数字不受影响**；受影响的是方法学设计主张本身。
- **建议修法**：二选一。(a) 改写描述为真实策略："missing score 按树配置（parse 树防御性 0、qa 树中性 5）；hinge 的硬门作用仅经由 stability 判据（Algorithm 1 line 27），不改变缺失分数"——同步修 :62-63、:122-127、:533 与对位表 §2①；(b) 若坚持"hinge=0"是设计意图，需另开授权批次改 config 并重跑 W1 复现门（会动冻结口径，不推荐在投稿前做）。
- **风险等级**：**高**。论文卖点是"可从论文单独复现 + 每个数字有指针"，而此处顺着论文给的指针（config）第一步就能证伪正文；对位表作为"逐行复核保证件"携带同一错误，审计层失效。

### B2. S1 第二段把 flat/判别臂口径的头条数字冠以 "hierarchical"，与同节第四段及 Table 1 直接冲突

- **文件+行号**：`paper/draft_v0_s1_s2_s6.md:20-25`（"a frozen **hierarchical** evaluation discriminates 75/95 tables (78.9%) and renders 96/118 injections visible (81.4%)"）vs 同文件 `:36-37`（"the hierarchical expert-weight protocol as instantiated **13/118**"）与 `:328`（Table 1：E1.3 hierarchical 20/95、13/118；E1.2 **flat 75/95**）。
- **证据指针**：75/95 与 96/118 出自 `logs/graph/eval/checkpoint_discrimination_tables_v2.json`（meta.caliber：判据 = 命中率叶 drop=(H_orig−H_inj)×10 ≥ 2；properties.discrimination 75/95=0.7895；by_type n_visible 合计 43+15+20+0+13+5=96）。同一判据在 `t1_eval_baseline_comparison.json` 中被标为 **E1.2_flat**（e1_6.protocol_reuse："run_arm_b 逐字复用; TAU=2.0 / FLAT_TAU_H=0.2"），E1.3_hier_expert 是 20/95。另："visible 96/118"（未被静默吸收）与"detected 85/118"（过协议阈值）是两个口径（d1_mutant_validity_audit.json counts：anchor_detected_total=85、absorbed_strict_total=22、hi_by_mechanism.threshold_dilution=11），S1 未区分，读者无法调和 96 vs 85 vs 13。
- **建议修法**：S1 ¶2 将 "frozen hierarchical evaluation" 改为准确名称，如 "the frozen checkpoint-discrimination arm (hit-rate leaf, ΔH·10 ≥ 2 criterion)"；并加半句口径注记："visible（未被吸收）≠ detected（过阈值），96/118 为前者，85/118 为后者"。
- **风险等级**：**高**。引言头条数字与 Table 1 同词不同值，是审稿人第一轮就会抓住的内部矛盾，且会让"hierarchical 检出更低"这一核心诚实定位反被质疑为数据混乱。

---

## 3. Major issues

### M1. S2 "latency 是一等计分维度"无工件支撑

- **文件+行号**：`paper/draft_v0_s1_s2_s6.md:70-71`（"The framework scores **latency** and model-call cost as first-class dimensions, giving the cost axis…"）。
- **证据指针**：`config/eval_checkpoint_trees.json` 全文 0 处 latency（12 叶无任何延迟叶）；`t1_eval_baseline_comparison.json` 的 cost_proxy 仅含 model_calls / deterministic_checks / scored_units；蓝图与 t1 中亦无 latency 计分字段。latency 仅在 `docs/experiments/2026-08-08_eval_baseline.md`（m2_eval_deterministic "route/latency 记录"）中作为**记录项**存在。S4/S5 实际使用的成本轴 = scored_units（2 vs 12）。
- **建议修法**：改为 "the framework records latency and scores model-call/check-count cost as the cost axis (scored units: 2 root vs 12 leaf)"，或删去 latency。
- **风险等级**：中。方法节过度声称，顺指针即穿帮；一句话可修。

### M2. S4 judge 校准段：预注册判据口径错位 + E1.5 关键局限未在正文披露

- **文件+行号**：`paper/draft_v0_s1_s2_s6.md:300-304`（"leaves the control tree roots within 0.5 of the mapped caliber, **the pre-registered consistency bound**"）。
- **证据指针**：`t4_pso_fair_comparison.json` payload.e1_5.endpoint_consistency_note：预注册判据是 `prediction_abs_delta_per_dim_le: 0.5`——**逐 judge 维、0-5 量表**（max_observed 0.5，holds true）；论文把它挪用于**树根、0-10 量表**。根级 Δ 事实上成立（judged qa root 9.75 vs mapped 9.97 → 0.22；parse 10.0 vs 10.0），但它是派生量，不是预注册量。另两处未披露的局限（同工件）：design_note——"3 个 judge 叶为『裁判评判定』而非『裁判评原始答案』"；caveat——"本注记度量的是【:8004 聚合器能否复现历史四维均分】，不等于…逐条判定一致率"。
- **建议修法**：正文改写为"预注册界 = 逐维 |Δ|≤0.5（0-5 量表），实测 max 0.5，成立；派生地，控制态树根在 0-10 量表上相差 ≤0.22"；并加一句 design_note/caveat 局限（judge 重评的是逐条判定的再聚合，非原始答案）。
- **风险等级**：中。数值都真，但"预注册判据"归属写错——按 experiment-autopsy 纪律这正是"结果反定义判据"的口径滑移，审稿人对照工件可指出。

### M3. S6 双门案例未披露源文档明确标注的"机制更正"（7/7 全由 gain 维拦截，ε 维零点火）

- **文件+行号**：`paper/draft_v0_s1_s2_s6.md:379-385`（"each candidate passes a gain-collateral double gate … the gate rejects 7/7 (100%)"）。
- **证据指针**：`docs/experiments/2026-08-28_adversarial_arm_experiment.md:23`——"**机制更正（08-29 全盘复审, Loop C F1）**：7 条对抗事件全部 gain=0.0(<τ) 且 collateral=0.0(≥−ε)，拦截发生在 **gain 维**…设计稿 §0 预期的 collateral<−ε 路径未出现"。扩容臂 ε 维确有激活（`2026-08-29_collision_expansion_experiment.md` §4.2 "ε 维完全激活"；EXP_g10 行 5/0、门拒率 1.00）。
- **建议修法**：S6 加一句："in the adversarial arm all seven rejections fired on the gain dimension (Σε = 0, collateral path never activated); the collateral dimension became routinely active only in the expanded-collision regime"。
- **风险等级**：中。S6 自我定位是"机制案例"，而哪个门点火恰恰是机制本身；论文跳过了自家复审明确记录的更正，读引用源的审稿人会视为选择性披露。

### M4. advisor 盘点件相对当前草稿整体过期，若据其决策将误报就绪度

- **文件+行号**：`docs/experiments/2026-09-20_advisor_package_and_paper_readiness.md:26`（#6 记录 draft = 19,788 B，sha256(16) `89f46d5017eab273`）；`:60-70`（§2.1 列 7 处 [TODO]）；`:72-75`（§2.2 两条硬阻塞：T7 回填、Algorithm 1 入稿）。
- **证据指针**：当前 `paper/draft_v0_s1_s2_s6.md` 实测 39,528 B，sha256(16) `01e2c7d1388b39f4`；draft:3 自证 "T7 backfill per user ruling 2026-09-20"；正文 grep 已无任何未闭合 `[TODO-*]`（仅纪律声明与"已处理"注记）；Algorithm 1 已入稿（draft:79-116）且对位表已落盘（draft:532 指向被审文档本身）。即 §2.2 两条"硬阻塞"在盘点当晚已被关闭，盘点件未追记。
- **建议修法**：按该项目 append-only 纪律，在盘点件追加 status addendum：新 sha/字节数、TODO 清零、两阻塞关闭证据指针（draft:3、:79-116、:532），并注明"§2.1/§2.2 为 18:31 快照，已被 23:33 的 T7 回填取代"。§2.3 专利门保持 open。
- **风险等级**：中。文档自身声明了取值时间，不算失实；但它是"发不发导师包"的决策输入，过期状态会误导下一步裁定。

---

## 4. Minor issues

| # | 位置 | 问题 | 证据指针 | 建议修法 | 风险 |
|---|---|---|---|---|---|
| m1 | draft:114-115 | Algorithm 1 行号重复：两行均为 "28:" | 伪代码块目视可证 | 第二行改 29 | 低 |
| m2 | draft:73（"exactly as implemented"） | 伪代码省略了三处实现细节：`w_sum or 1.0` 全零权重保护（script:229）、`round(…,4)` 舍入（script:205,231）、binary 叶内部口径（router 先返回 0-10，再 `*unit/10`，script:201，非伪代码的 `10*v`） | `d3_matched_fpr_stage_a.json:1194-1198` 恰把 9e-08 斜率偏差归因于 round 量化——舍入对"byte 级复现"并非可忽略 | 措辞降为 "as implemented (guards and rounding documented in the line-alignment table)"，或伪代码加两条注 | 低 |
| m3 | 对位表:22 | root_sr 备注"分母 = 子树数（本树 2）"错误：实现分母 = 本树根的直接子节点数 | `checkpoint_aggregate_report.json` results.parse.sr."5".n_sr_subtrees = **4**（qa 为 5）；"2"是森林树数（旧 docstring :15 n_subtrees=2 的口径） | 备注改"分母 = 本树根直接子节点数（parse 4 / qa 5）"；论文 Algorithm 1 line 23 本身正确，无需动 | 低 |
| m4 | 对位表:33 | "docstring 第 16 行仍写 18/20"——实际在 script:17（:16 是"全部 20 叶子"句）；且 docstring:17 判据"无 hinge 叶子 **<= 7**"与代码 `all(hinge >= 7)`（script:257-259）在 =7 边界相反，对位表只标了 18/20 与 k=7 两处过时，漏了这条边界差异 | script:14-17 原文 | 更正行号；把 <=7 vs >=7 边界差异补入"留待授权批次"清单 | 低 |
| m5 | 对位表:38-39（§3 复算记录） | "qa root 9.97"按当前工件态可复现（`m2_judge_report.json` faithfulness avg=4.94 → qa 9.97 ✓），但仓内存档 `checkpoint_aggregate_report.json`（generated 2026-08-18）qa=10.0——存档报告早于当前 judge 工件，读者对不上 | 两工件字段对照 | §3 注明"仓内 report 为 08-18 旧档；本复算以当前 m2_judge_report 为准"，或授权批次重跑刷新存档 | 低 |
| m6 | draft:370-372 | "120 leaf-state cells"指针错挂：所引 `d3_matched_fpr_stage_b.json, call_counter_breakdown` 无 120（total 31 / formal 28）；120 在 `t4_pso_fair_comparison.json` payload.e1_5.cells_total（=120 ✓，cells_ok 120） | 两工件实测 | 指针补 t4 e1_5 | 低 |
| m7 | draft:533 | 自审注记"S4 另记判定级 missing 政策（hinge 用 0、其余用中性 5）"：S4 正文（:246-309）无此内容（grep 证实），且该句口径本身与 config 矛盾（并入 B1） | grep "missing" 全稿仅命中 S2/伪代码/注记 | 随 B1 一并改写或删除该注记 | 低 |
| m8 | draft:66-68 | "four dimensions, 4.94-5.0 on the baseline set"：基线文档含中间复测 citation **4.69**（:50，后被 rubric 拒答豁免修复覆盖为 5.0，:58-60）；4.94-5.0 对"当前正式基线"+ t4 live_8004 冻结值成立，但未注明取哪个时点 | `2026-08-08_eval_baseline.md:50,58-60`；t4 e1_5 note live_8004 dims | 加注"当前正式基线（rubric 修复后）口径" | 低 |
| m9 | draft:74-77 | "the deliverable-only original"未具名未引用：Algorithm 1 的原始出处（GTA-2）只存在于仓外 hbkeyan 材料（advisor 文档 :17-18，仓内不可核验）与 script:2 的 docstring；草稿正文读者无法定位"original" | advisor 文档 §1.1 #4/#5（仓外路径 D:\…\hbkeyan\）；related_work_v4 在仓内 | 正文具名并引 related_work_v4 中已核验的条目；仓外材料不可作为唯一出处 | 低-中（涉及溯源，投稿前必须补引用） |
| m10 | 自审注记 draft:527 | mutation-testing 对位句仍为未关闭 [polish]（"reviewer 首问必是'与 mutation testing 何异'"——自评已预言攻击点，素材在 related_work v3/v4 已备） | draft:527 | 投稿前落一句对位 | 低 |

---

## 5. Algorithm 1 与实现一致性（algorithm-description 视角专项）

**总评：核心聚合逻辑逐行一致，一致性水平高；3 处偏差（1 处 Blocking、2 处 Minor），且对位表本身诚实记录了大部分已知差异。**

已复核一致的关键点（论文行号 → 代码行号）：
- 叶判定/证据路由/显式降级：draft:87-95 → script:219-223、:175-188（`missing_score` 默认 5.0、degraded+reason、"不静默给 0" ✓）
- judge 0-5 → 0-10：draft:92 → script:193-195（`val*unit/5.0`）✓
- 兄弟归一化加权平均：draft:97-100 → script:228-230 ✓；凸组合性质（draft:119-121）由 `w/w_sum` 结构成立 ✓
- H 集合定义：draft:82-83 → script:149 `HINGE_ROUTES` 逐字对应 ✓
- 稳定性判据：draft:112-113 → script:245-260（叶侧 `>`、hinge 侧硬编码 `>= 7`、末次 k 生效、默认 [5,7,8] ⇒ k=8）✓；"两个阈值口径在活工件上同旗"经 parse stable（5/5 过）与 qa stable（7/7 过）证实 ✓
- 叶数 5/7/12（非旧稿 20）：draft:141-143 → aggregate_report n_leaves、对位表 §3 ✓；0.9×12=10.8 的口径说明 ✓
- 确定性/同构复现：draft:131-134 → t1 `aggregation_isomorphism.max_abs_err = 0.0`（parse 10.0 / qa 9.97）✓
- 旧措辞"zero a subtree"已修正为"not a silent zeroing"（draft:122），与对位表 §2 的修正记录互证 ✓

不一致点：
1. **B1**（hinge 缺失分数=0 的声称 vs config 实测 4/5 为 5）——唯一的实质性方法描述错误。
2. **m2**（"exactly as implemented" vs 保护/舍入/binary 内部口径三处省略）。
3. **m3/m4**（对位表 root_sr 分母备注错、docstring 行号偏一、<=7 vs >=7 边界漏记）——论文伪代码本身在这三处均正确，错在审计附表。

另记：script docstring 的 "18/20 叶子"与 config meta 的 "STABLE = 0.9 (18/20 leaves pass)"（config:16）均为二十叶旧口径残留，论文 draft:141-143 已如实披露、对位表"只记不改"处理合规——此点无责，但授权批次应一并清理（含 config meta，对位表 §4 目前只列了 docstring）。

---

## 6. 实验证据链是否闭合（experiment-autopsy + eval-harness 视角）

**总评：主张→工件→数值三级链条经抽查全部可对上，闭合度 ~95%；未闭合部分均已显式声明为未闭合（合格），仅 2 处指针错挂。**

逐段核验结果（全部实测比对）：

| 主张 | 工件 | 结果 |
|---|---|---|
| S1/Table 1 四协议：95/95·112/118(0.9492)、75/95(0.7895, CI[0.6947,0.8737])·85/118(0.7203)、20/95(0.2105, CI[0.1263,0.2947])·13/118(0.1102)、E1.4 不迁移(11 维不同构) | t1 arm_b.protocols | **全对** |
| S1 判别 75/95(78.9%)、可见 96/118(81.4%)、ocr_similar 13/13 吸收(vis 0.0)、他类 81-100% | tables_v2 properties/by_type | **全对**（96 为 by_type 求和；命名问题见 B2） |
| S1/S3 γ 网格 {0.2,0.3,0.5,0.7,0.9}、0/13 全盲、type range 1.0/0.6471/0.5882/0.3/0.3、字面判据 0.7/0.9 失败如实报 | t2 prereg_predicates + d1 injections[].visible_by_gamma | **全对**（holds=false 原样呈现，未重贴标签 ✓） |
| S2 九 mutant、16/16 契约、judge 4.94-5.0、isomorphism 0.0、dropped_na_leaves=2 | discrimination_report(n_mutants=9)、eval_baseline:15、t1 | **全对**（m8 时点注记除外） |
| S2/S4 PSO：1.432574×5 seeds、7650 vs 67(≈114x)、C3=PARTIAL 降级、minimax 1.25605/0.35714、m7 保真度排除(0.0000) | t4 payload.t4 / e1_5 / findings | **全对**（降级条款如实触发 ✓） |
| S2/S4 matched-FPR：单变叶、3/8 仿射、2000 次表簇(88)bootstrap CI[0,0]、2384/2382/2、0.7895vs0.2105=阈值摆放伪影 | d3_stage_a a4/preflight/a2 | **全对** |
| S4 跨匹配器：盲集恒 [ocr_similar]、分配轴 0 翻转、打分轴 5 翻转全在 date_variant | d2 r3_assessment + matcher_class_transitions.flip_types={date_variant:5} | **全对** |
| S5 种子敏感性：0.7895/0.7835/0.7556、spread 0.0339、pooled 0.7766 CI[0.727,0.8227]、seed42 byte-identical | t4 e1_6 | **全对** |
| S5 消融：权重族 1.2560-1.4326、worst 0.0926 不变；Hungarian 0/0、正对照 403 vs 806 | t4 + t6 | **全对** |
| S3/S7：E 集 0/7、DR4 8 行 3/5 分歧(7 miss+1 FA)、同输入 3/3、21 中 14 等价(13/13 ocr + 1/8 非 ocr)、n=28、分母 111/TPR 0.810811 冻结 | d3_autopsy_recompute recomputed_summary | **全对**（分层报告纪律执行到位 ✓） |
| S6：7/7、5/5、ΔV(ACC)=0.05 CI 含 0、7/40 vs 4/40、McNemar p=0.375 | 两份实验文档 + column_sensitivity:10,24-28 | **数字全对**；机制披露缺 M3 |
| Threats：oracle 0.952381→0.597015、分支 a | t6 gates/P1_branch | **全对** |
| 复现门：W1 G1-G4 零误差、payload_sha256 双跑一致 | w1_window_report.md | **在案** ✓ |

eval-harness 视角的结构性评价：冻结输入（seed42 byte-identity gate）、判定分布留痕（prereg_predicates 带 verdict）、评分者局限披露（judge 单模型 :8004、无第二 scorer）该项目均已自建——超出多数投稿的实际水平。**唯一未闭合的证据缺口是第二 scorer 臂（D4 deferred）**：criterion-relativity 主张因此停在 D3 证据级，S7 更正注记（draft:453-470）对此的处理（"deferred 而非 awaited，主张不升级"）是正确的收紧而非放松 ✓。S7 家族×判据分层、任何 D4 数字均未被引用 ✓（grep 证实）。

未闭合项清单（均非隐瞒）：① latency 维度声称无指针（M1）；② 120-cells 指针错挂（m6）；③ 单变叶 ⇒ localization 价值不可测（S7:504-508 已留口）；④ 第二 scorer（deferred，已披露）。

---

## 7. 论文写作与审稿风险（paper-review-check 五焦点）

- **核心主张**：清晰且自我克制——"structure buys localization and evidence decomposition, not sensitivity"（draft:484-486）与预注册定位（:173-180）一致，negative result 的正面化叙述成立。风险：主张的新颖性高度依赖"协议依赖性/matched-FPR 恒等"这一发现，而相关工作节尚未入稿（仓内有 related_work_v4，正文无 References）——**投稿版缺 related work 与引用体系是当前最大的结构性缺口**（含 m9 的 Algorithm 1 原始出处引用）。
- **审稿人第一攻击点排序**：① B2 的 S1 术语冲突（引言即矛盾，最致命且最易修）；② "与 mutation testing 何异"（自审 :527 已预言，对位句仍未落）；③ 单语料+全合成扰动（S7:488-493 已披露，跨匹配器/跨种子稳定性是有效防线）；④ judge 单模型且 E1.5 是"裁判评判定"（M2 披露后风险可控）；⑤ hierarchical 检出低于 flat 会不会说明框架无用——现有"定位/证据分解 vs 灵敏度"的切割是诚实的，但 B2 不修会把这个防御打穿。
- **写作/排版风险**：7.0p 预算（0.75+1.25+1.5+1.0+1.5+0.5+0.5）与蓝图吻合，但当前稿正文内嵌大量方括号指针与 append-only 注记（S3 命名注、S7 更正注、五问注记），投稿排版时必须迁移到附录/脚注，否则 7 页装不下；"decision-4A 保留原文+追加更正"的纪律适合内部台账，不适合会议终稿形态——需要一次"注记→终稿"的编译步骤。
- **外部硬门**：专利申请状态未确认前不外发（advisor 文档 §2.3、draft:7）——非本审稿可解，但它是唯一真正卡投稿时点的事项，其余都是文本工作。
- **advisor 文档自身风险**：18 件材料清单中 5 件为仓外路径（D:\…\hbkeyan\），单独 clone 不可解析（文档 :20 已自标脆弱点 ✓）；#18 INDEX 过期项已自标待主线程更正 ✓。

---

## 8. 下一步 3 项建议（按优先级）

1. **【P0，一个授权批次】修 B1+B2 四处同源文本**：S1:20-25 协议改名+visible/detected 口径注记；S2:62-63、:122-127 hinge 缺失分数改为按树分口径（或明写"设计意图 vs 现配置差异"）；对位表 §2①、draft:533 注记同步改。全部为措辞级修改，零数字变动、零工件重跑。预期：引言矛盾消除，"exactly as implemented"声明恢复可辩护；若不改，这两处是拒稿级攻击面。
2. **【P1，同批或次批】补齐三处披露 + 两处指针**：M1 latency 句改写；M2 judge 校准预注册口径如实表述并补 design_note/caveat 一句；M3 S6 加 gain/ε 点火维一句；m6 补 t4 e1_5 指针；m9 在正文具名 Algorithm 1 原始出处并挂 related_work_v4 引用。预期：论文自设的"每数字有指针、每判据有预注册"纪律实现零例外。
3. **【P1，流程件】advisor 盘点件追加 status addendum + 落 mutation-testing 对位句**：addendum 记新 sha（`01e2c7d1388b39f4`/39,528 B）、TODO 清零、§2.2 两阻塞关闭证据（draft:3、:79-116、:532），使导师包决策基于当前态；同时把自审 :527 预留的"静默吸收 ≈ mutant 未杀死、但按层报可见性而非二元 kill"对位句落入 S1 末或 S3——这是自审已识别、素材已备、仍未关闭的唯一 polish 项，也是审稿人首问的预制答案。（专利申请状态确认继续留作用户专属门，本三项不与其互锁。）

---

**审稿人结语**：这份草稿最罕见的品质是对自己不利的数字全部原样在案（C3 PARTIAL、t2 字面判据 holds=false、matched-FPR CI[0,0]、S6 McNemar p=0.375、E1.4 不迁移），尸检与预注册纪律执行到位。当前的问题不是证据不足，而是**两处自述文字跟不上自家工件**（B1、B2）——修文字即可，不需要动任何冻结数字。
