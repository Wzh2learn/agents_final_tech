Now I have all the evidence needed. Let me construct the complete review.

---

# 独立审稿报告

**审查对象：**
1. `paper/draft_v0_s1_s2_s6.md` (主稿)
2. `docs/experiments/2026-09-20_algorithm1_lines_vs_impl.md` (算法-实现对位表)
3. `docs/experiments/2026-09-20_advisor_package_and_paper_readiness.md` (盘点件)

**审查框架：** paper-review-check / experiment-autopsy / eval-harness / algorithm-description

---

## 1. 总体判定：**REVISE**（修改后可达 ACCEPT）

理由：证据链闭合、算法实现一致性高、核心发现诚实且新颖。但存在一处**可导致 desk-reject 的术语漂移**（S1→S4 同名异义）和三处**审稿人必会攻击的措辞歧义**。这些问题均可通过纯文本修订解决，无需新实验。

---

## 2. Blocking Issues

### B1. S1 "hierarchical evaluation" 与 S4 同名异义——引发数字矛盾

- **文件**: `paper/draft_v0_s1_s2_s6.md`
- **行号**: :21–24 (S1) vs :253–256 (S4)
- **证据**: 
  - S1 声称 "a frozen hierarchical evaluation discriminates 75/95 tables (78.9%) and renders 96/118 injections visible (81.4%)"，引用 `checkpoint_discrimination_tables_v2.json`
  - S4 Table 1 报告：flat 协议 75/95 tables / 85/118 injections；hierarchical expert 协议 20/95 tables / 13/118 injections
  - 两处引用不同工件（`checkpoint_discrimination_tables_v2.json` vs `t1_eval_baseline_comparison.json`），但使用相同术语 "hierarchical evaluation"
  - 经核查：S1 的 75/95 匹配 flat 协议，96/118 不匹配任何协议层数字（flat=85/118, hierarchical=13/118），96/118 实际来自 checkpoint-level 逐检查点判别（任一检查点可见即算可见）——这是第三种测量口径
- **建议修法**: S1 将 "hierarchical evaluation" 改为 "checkpoint-level discrimination" 或 "a frozen evaluation at the checkpoint level"，并明确标注这是 "per-checkpoint visibility (any checkpoint flags the defect)"，与 S4–S5 的 "protocol-level detection (aggregated root score crosses threshold)" 做显式区分。三个测量口径（checkpoint-level visibility / protocol-level flat / protocol-level hierarchical）必须在首次出现时以表格或短句并列定义。
- **风险等级**: **desk-reject risk**——审稿人会在 5 分钟内发现 S1 数字与 S5 表格不一致，直接判定数据不可信。

### B2. S1 引入框架时使用较优数字（75/95, 96/118），S4 才揭示本文主张的层级协议仅检出 13/118——构成选择性呈现印象

- **文件**: `paper/draft_v0_s1_s2_s6.md`
- **行号**: :21–28 (S1) vs :253–256 (S4)
- **证据**: S1 以 75/95 和 96/118 开篇，呈现框架"能看见"多数缺陷；S4 才揭示层级化框架检出率最低（13/118）。这种"先亮优点再亮缺点"的叙事顺序，在 S1 未区分测量口径的前提下，给审稿人的第一印象是**框架有效**——但实际框架在 protocol-level 的检出是最弱的。作者在 S7 诚实承认这是负面发现（:479–486），但 S1→S4 的叙事弧线会令审稿人怀疑故意隐瞒。
- **建议修法**: S1 开篇同时给出三种测量口径的概览数字，或至少用一句如 "At the protocol level, the hierarchical framework detects fewer injections than a flat baseline, which we report candidly in S4" 引导预期。S1 的定位应是"我们测量了什么"而非"框架查出了多少"。
- **风险等级**: **强 reject 触发点**——审稿人如感到被误导，再无翻身机会。

---

## 3. Major Issues

### M1. Algorithm 1 伪代码有重复行号（28 号出现两次）

- **文件**: `paper/draft_v0_s1_s2_s6.md`
- **行号**: :114（`28: end function`）和 :115（`28: end function`）
- **证据**: 伪代码块最后两行均为 `28: end function`。第一行对应 `EVALUATETREE` 的结束，第二行无对应。
- **建议修法**: 第二行删除，或改为 `29: end function`（如果两个 function 需要分别标注结束）。推荐使用 `end function EVALUATETREE` 显式命名。
- **风险等级**: 版面级但审稿人会认为不专业。

### M2. S3 内部注记与论文正文混杂

- **文件**: `paper/draft_v0_s1_s2_s6.md`
- **行号**: :203–207 (Namespace note); :417–421 (Landing note); :453–473 (Correction note)
- **证据**: 多处 append-only 内部注记直接嵌入正文，含 "本批未改"、"决策 10=c"、"decision-4A discipline" 等项目管理语言。审稿人读到这些会认为稿件未完成。
- **建议修法**: 全部移入独立的 "退火注记.md" 或置于 `<!-- -->` HTML 注释中。正文只保留最终学术文本。
- **风险等级**: 审稿人直接扣分（写作质量）。

### M3. "审稿人视角五问注记"整段（:522–539）内嵌中文任务管理笔记

- **文件**: `paper/draft_v0_s1_s2_s6.md`
- **行号**: :522–539
- **证据**: 整节是中文内部审稿笔记，列出 "blocking / polish" 分类和已处理/未处理状态。对 AAAI 审稿人完全不可读且会暴露内部过程。
- **建议修法**: 整节移除出论文文件，放入独立审稿准备笔记。该节内容已大部分在 T7 中处理，可归档。
- **风险等级**: 强——审稿人看到内部笔记 = 稿件未完成 = 直接拒。

### M4. S7 的前瞻句 + 更正注记构成读者迷宫

- **文件**: `paper/draft_v0_s1_s2_s6.md`
- **行号**: :449–473
- **证据**: 正文说 "until that arm reports, the claim is not upgraded"（:451），紧接着更正注记说该 arm "is no longer scheduled"（:455）。读者必须同时理解正文 + 注记才能知道最终状态。且叙事从 "未升级" → "不再安排" 的跳跃对不熟悉内部决策的审稿人是不可追踪的。
- **建议修法**: 将两段合并为单一最终表述："A confirmatory second-scorer arm was pre-registered but is now deferred because the required per-family constructible-n table is undefined on the frozen corpus. Therefore the criterion-relativity claim remains at its current evidence level and is not upgraded." 不需要保留"原句 + 注记"的结构——那是内部轨迹，不是论文。
- **风险等级**: 审稿人会被叙事复杂度绕晕，放弃理解 → 判为不清晰。

### M5. gamma 网格符号不当

- **文件**: `paper/draft_v0_s1_s2_s6.md`
- **行号**: :39–43, :215–217
- **证据**: 正文写 "gamma in {0.2, 0.3, 0.5, 0.7, 0.9}"（集合记号）和 "gamma in [0.2, 0.9]"（区间记号）混用。:216 有澄清括号 "(the grid is the five discrete points...not a continuous sweep)"——这恰恰证明记号不当，每个看到 "gamma in [0.2, 0.9]" 的读者都会被误导。
- **建议修法**: 全文统一使用 γ ∈ {0.2, 0.3, 0.5, 0.7, 0.9} 或定义一个符号 G = {...}。删除括号澄清，因为它暴露了写作过程。
- **风险等级**: Method 章的基本严谨性被质疑。

---

## 4. Minor Issues

### m1. S2 专家权重缺乏引入理由

- **文件**: `paper/draft_v0_s1_s2_s6.md`
- **行号**: :63
- **证据**: "expert weights in {1,2,3}" 直接陈述，没有任何理由。S4 后用 PSO 对比证明 greedy/expert 同值——但这只是证明了权重不敏感，不是证明了专家权重的合理性。
- **建议修法**: 在 S2 加一句："weights are manually assigned by domain experts on the development split (1 = informational, 2 = actionable, 3 = gate-level); Section 4 shows they are not worse than any automated search on this corpus."
- **风险等级**: 低——但审稿人会问。

### m2. S4 "12 leaf units" vs "2 root units" 的可比性声明不足

- **文件**: `paper/draft_v0_s1_s2_s6.md`
- **行号**: :259–260
- **证据**: "the checkpoint-level arms score 12 leaf units where the end-to-end arm scores 2 root units, and the two calibers are not commensurable"——这是什么意思？它们是不同粒度的测量，不是不同单位的测量。如果不可通约，为什么放在同一个 cost axis 上？
- **建议修法**: 改为 "the checkpoint-level arms decompose the score into 12 leaf-level dimensions while end-to-end reports only 2 root-level aggregates; this decomposition carries an evaluation budget cost (6× the artifact space) but provides per-layer diagnostic signals unavailable to the end-to-end protocol."
- **风险等级**: 低——Method 细节但若审稿人是测评背景会追问。

### m3. S6 门控案例的定位摇摆

- **文件**: `paper/draft_v0_s1_s2_s6.md`
- **行号**: :387–395
- **证据**: "We present this strictly as a mechanism case, not an efficacy claim" 与后续 "main effect...not significant" 互相抵消。读者读完 S6 会问"那这段存在的理由是什么？"——门拒 7/7 是机制信号，但 p=0.375 是非显著，N=40 太小。两段分开写可能更好：① 机制演示（7/7 门拒）② 诚实 null（功效不足以支撑主张）。
- **建议修法**: 将门拒 7/7 作为主叙述，非显著作为局限直接跟进。当前先讲 "not significant" 再讲 "honest null motivates..." 的次序弱化了机制演示。
- **风险等级**: 低——Section 6 已是全稿最短章，审稿人不会攻击太猛。

### m4. 蓝图与盘点件中 [TODO] 与已解决状态的漂移

- **文件**: `docs/experiments/2026-09-20_advisor_package_and_paper_readiness.md`
- **行号**: :62–71（7 处 TODO 表）; :74–75（"Algorithm 1 伪代码未入稿"）
- **证据**: 盘点件称 "Algorithm 1 伪代码未入稿" 是硬阻塞——但当前论文草稿（:80–116）已经包含 Algorithm 1 伪代码。盘点件取值时间 2026-09-20，论文草稿也是 2026-09-20（T7），盘点件可能写于 T7 组装之前。7 处 TODO 中 [TODO-T1/T2/T6-crossref] 等也在 T7 中部分解决（S4 末段有 T6 交叉引用）。
- **建议修法**: 盘点件头部加注 "取值时间早于 T7 组装完成"，或更新 TODO 表。
- **风险等级**: 内部文档的低优先级漂移，不直接影响论文。

### m5. 算法-实现对位表缺少 hinge 叶子数为 3 但 config 中为 5 的明确说明

- **文件**: `docs/experiments/2026-09-20_algorithm1_lines_vs_impl.md`
- **行号**: :29（`HINGE_ROUTES = {"overall_status_binary", "pass_rate_contract", "nf_pass_rate"}`）
- **证据**: 对位表列 hinge 路由为 3 种 mapping 类型。但 `config/eval_checkpoint_trees.json` 中带 `missing_score: 0` 的叶子有 5 个（parse.doc.ok, parse.doc.throughput, parse.table.regression, parse.field.hit_rate, parse.reconcile.equations），其中只有 `overall_status_binary` 是 hinge 路由。`run_completed`, `row_pass_rate`, `hit_rate_achievement`, `reconcile_derived` 的 missing_score 也是 0 但不在 HINGE_ROUTES 中。这意味着 missing_score=0 和 hinge 是两个独立概念——但论文 S2 :64–65 将它们合并为 "hard-gate leaves whose absent evidence contributes zero"。
- **建议修法**: 在论文和/或对位表中澄清两组概念：① missing_score=0 的叶子（5 个 parse 叶，防止工件缺失时给出假阳性默许分）② hinge 路由的叶子（3 个 mapping 类型，参与稳定性硬检查）。 它们是正交的：parse 树叶子 missing_score=0 是工件缺失的防御性设计，hinge 参与 stable 判据。
- **风险等级**: 低——审稿人不会对照 config 文件，但如有可复现性要求，这会暴露。

---

## 5. Algorithm 1 与实现一致性

**总体：高度一致，仅有文档级差异。** Algorithm 1 伪代码与 `scripts/eval_checkpoint_aggregate.py` 在逻辑层面完全同构。已逐行核实：

| 维度 | 判定 | 证据 |
|---|---|---|
| 叶子判定（DFS 底） | ✅ 一致 | 伪代码 L2 vs 实现 L218 `if not children:` |
| 缺失证据降级 | ✅ 一致 | 伪代码 L4-5 vs 实现 L178-180（`__missing__`→`missing_score`+degraded） |
| judge 0→5 映射 | ✅ 一致 | 伪代码 L7 vs 实现 L193-194 `val * unit / 5.0` |
| 兄弟归一化加权平均 | ✅ 一致 | 伪代码 L15 vs 实现 L230 `agg = sum(s * (w/w_sum)...)` |
| 稳定性判据 | ✅ 一致 | 伪代码 L27 vs 实现 L258-260：`>` 阈值 + `>= 7` hinge + `>= 0.9` 比例 |
| k_last 使用末次阈值 | ✅ 一致 | 伪代码 L26 vs 实现 L245-260 循环内最后赋值 |
| root_sr 子树数 | ✅ 一致 | 伪代码 L23 vs 实现 L246-248（n_subtrees=2） |
| leaf_sr 叶子计数 | ✅ 一致 | 伪代码 L24 vs 实现 L249-250 |

**已知差异（已记录，非缺陷）**：
1. 实现 docstring（L17 "18/20 >= 7"）仍引用旧 20 叶草案，实际 12 叶。该处已在对位表 :33-34 和论文 S2 :141-142 注明。属于可修复的文档过时问题。
2. 伪代码 duplicate line 28（见 B1 之上）——这是 LaTeX 排版错误，非逻辑错误。
3. 伪代码 L21-22 的 `L`（收集叶子分数）在实现中通过 `_iter_nodes` + post-hoc 收集（L236-238），而非遍历时实时收集。这等价但不严格对应——如果阅读伪代码后复现时试图在 DFS 中实时收集，会得到略不同的代码结构。这是一个可忽略的风格差异。

**结论**：Algorithm 1 可被独立复现。两个注明差异不会产生不同数字。

---

## 6. 实验证据链是否闭合

**判定：闭合且路径可溯，但 S1→S4 的两层口径跳跃是链上最弱的连接点。**

证据链逐段检验：

| 链段 | 闭合？ | 证据路径 | 问题 |
|---|---|---|---|
| S1 开篇缺陷注入统计 | ⚠️ 部分 | `checkpoint_discrimination_tables_v2.json` | S1 引用 checkpoint-level 口径（96/118），S4-S5 引用 protocol-level 口径（85/118 flat, 13/118 hier）。两个口径在正文中未被显式区分。 |
| S2 框架树结构与聚合 | ✅ | `config/eval_checkpoint_trees.json` → `eval_checkpoint_aggregate.py` | 叶子 12、权重、missing_score、hinge 链逐级可查 |
| S2 聚合同构验证 | ✅ | `t1_eval_baseline_comparison.json` → `aggregation_isomorphism.max_abs_err = 0.0` | 论文中指明 0.0，工件中确为 0.0 |
| S3 OCR 盲点 | ✅ | `d3_autopsy_recompute.json` → `ocr_max_levenshtein_lower = 1` → `visible_by_gamma = 0/13 all points` → `t2_visibility_sensitivity.json` → `E2_1_ocr_similar_blind_all_gamma = true` | 两端验证，自上而下无断点 |
| S3 判据相对性 | ✅ | `d3_autopsy_recompute.json` → `dr4_agree=3, dr4_disagree=5, n_judge_cases=28` | 28 例小样本，诚实标注 |
| S4 四协议比较 | ✅ | `t1_eval_baseline_comparison.json` → `arm_b.protocols` → E1.1=112/118, E1.2=85/118, E1.3=13/118 | 全部溯及工件 |
| S4 matched-FPR 仿射恒等 | ✅ | `d3_matched_fpr_stage_a.json` → `a4_matched_fpr` → `difference_CI95 = [0,0]`, `slope = 3/8`, `spearman_rho = 1.0` | 最强链段：0 争议 |
| S4 跨匹配器盲集 | ✅ | `d2_cross_matcher_det.json` → `r3_assessment.blind_set_identical_across_prereg_family = true` | 四匹配器下盲集恒为 [ocr_similar] |
| S4 PSO vs greedy | ✅ | `t4_pso_fair_comparison.json` → 5 seeds identical at 1.432574 | 7650 vs 67 评估次数，可查 |
| S5 T2 灵敏度网格 | ✅ | `t2_visibility_sensitivity.json` → prereg_predicates 三谓词 | 全部 5 点 0.2–0.9 已覆盖 |
| S5 T6 匹配竞争 | ✅ | `t6_matching_competition.json` → `g4_oracle_plain=0.952381, g4_oracle_overlay=0.597015, P1_branch 0 flips` | 分配层不可消解结论成立 |
| S6 闭环门控 | ✅ | `2026-08-28_adversarial_arm_experiment.md` + `2026-08-29_collision_expansion_experiment.md` → 7/7 门拒 | 对抗臂审计链完整，N=40 列灵敏度 p=0.375 诚实 |
| S7 局限与边界 | ⚠️ 偏弱 | D4 推迟导致判据相对性主张停留在 D3 水平 | 这本身不是链断裂——是已知的未闭合开口，已诚实报告 |

**链上唯一结构性弱点**：S1 的 checkpoint-level visibility（96/118）与 S4–S5 的 protocol-level detection（85/118 flat, 13/118 hier）之间的度量口径跃迁未在正文中正式定义。读者会以为 S1 的 96/118 是 "hierarchical evaluation" 的检出——然后到 S4 看到 13/118，产生认知失调。这不是数据造假，而是**术语歧义导致证据链看起来断裂**。

---

## 7. 论文写作与审稿风险

### 7.1 结构性风险

| # | 风险 | 攻击面 | 严重度 |
|---|---|---|---|
| R1 | S1→S4 同名异义（见 B1） | 审稿人最直接的攻击点："S1 says your method detects 96/118, then in S4 Table 1 it detects 13/118. Which is it?" | **critical** |
| R2 | "先亮好数字、后露差数字" 的叙事弧线 | 审稿人怀疑选择性报告 → 全稿信任崩塌 | **critical** |
| R3 | 核心发现是负面的（层级化不提升判别力）——论文需要比正面结果更强的说服力 | 审稿人："what is the contribution if the method doesn't improve detection?" | **high** |
| R4 | 解决 R3 的论据分散在多处：matched-FPR 在 S2 applicability note + S4，localization 在 S7 | 核心 rebuttal 点不集中，审稿人可能漏过 | **high** |
| R5 | 判据相对性主张因 D4 推迟而停留在 N=28 的水平 | 审稿人："you claim criterion-relativity as a finding but it's based on 28 judge cases with no confirmatory experiment" | **moderate** |

### 7.2 写作质量

**优点**：
- 诚实性突出——每一个 null result 都明确报告，matched-FPR CI=[0,0] 不美化
- 证据链的可追溯性可能是审稿人至今见过最强的——每个数字跟一个文件路径
- Algorithm 1 + 对位表 提供了可复现性保障
- 预注册判据（prereg_predicates）的使用在测评论文中罕见且加分

**问题**：
- 大量内部注记混入正文（见 M2, M3）
- 术语定义在正文中分散（"visibility profile" 在 S1→S3 之间，正式定义在 S4 才出现）
- S3 "Namespace note" 和 S7 "Correction note" 的 append-only + 轨迹保留结构对非合作者完全不可读
- 正文中多处括号里包含"ruling X, frozen YYYY-MM-DD"格式的决策元数据——审稿人没有决策编号的解码器

### 7.3 审稿人最可能攻击的 5 个问题（按其出现概率排序）

1. **"Your S1 claims 96/118 detected by hierarchical evaluation, but S5 Table 1 shows 13/118. Explain."** → 术语漂移。修法见 B1。
2. **"If your framework detects fewer defects than a flat baseline, what exactly is the contribution?"** → 回答在 matched-FPR 仿射恒等 + 层次化提供 localization 而非 sensitivity。需在 S2 和 S4 各一句集中陈述，而非分散在 applicability note + S4 + S7 三处。
3. **"You claim criterion-relativity, but you only have 28 judge cases and the confirmatory experiment was never run. Isn't this premature?"** → 在 S7 诚实报告 D4 推迟、降低主张强度即可——目前的措辞已经在做这件事，只是被注记格式掩盖。
4. **"Expert weights in {1,2,3} are arbitrary. How were they chosen?"** → S4 的 PSO 对比可回答"任意但 not worse than any search"，需在 S2 加一句引入。
5. **"Your gamma notation [0.2, 0.9] implies a continuous sweep; the parenthetical clarification shows you know it's discrete. Why not use set notation?"** → 修法见 M5。

---

## 8. 下一步 3 项建议

### 建议 1（P0，blocking）：修复 S1→S4 术语漂移和口径定义

**行动**：在 S1 末尾增加一个小节 "Measurement modes" 或直接在第一段末尾定义三个口径：
- **Checkpoint-level visibility**（任一叶子看见即算）→ S1 数字（96/118）
- **Protocol-level flat detection**（扁平均分越阈值）→ S4 E1.2（85/118）
- **Protocol-level hierarchical detection**（层级聚合越阈值）→ S4 E1.3（13/118）

将 S1 的 "hierarchical evaluation" 改为 "checkpoint-level discrimination"。S4 开始的 "hierarchical protocol" 保留。三个术语区分后，S1 和 S4 之间的数字差异就不再是矛盾，而是具有解释力的结构特征（层级聚合信息丢失）。

**不改实验，只改文字。**

### 建议 2（P0，blocking）：移除所有内部注记，重写 S3/S7 为纯学术文本

**行动**：
1. 删除或注释化 :203–207 (Namespace note), :417–421 (Landing note), :453–473 (Correction note), :522–539 (审稿人视角五问)
2. 将 S7 的 "表述 + 注记" 结构融合为单一最终表述
3. 将 gamma 区间记法全局改为 γ ∈ G = {0.2, 0.3, 0.5, 0.7, 0.9}
4. 修复 Algorithm 1 duplicate line 28

### 建议 3（P1）：集中 rebuttal 核心论点至一个段落

**行动**：在 S2 末尾或 S4 开头增加一个 "What the framework does and does not provide" 的集中声明（2-3 句），明确：
- ✅ Provides: per-layer visibility profile, evidence decomposition, matched-FPR identity proof, evaluator blind-spot diagnostics
- ❌ Does not: improve raw defect-detection sensitivity on this corpus (matched-FPR identity), replace flat protocol for detection tasks

这直接预回答审稿人最可能的 "what is the contribution" 攻击。目前这个论点分散在 :181-194（applicability note）、:479-486（S7）、:262-275（S4）三处。

---

**审稿人签名**：独立审稿（只读，未修改任何文件，未联网）  
**审查日期**：2026-09-21  
**证据基准**：18 处 JSON 工件逐件核验（存在性 + 关键值采样） + 实现件完整阅读 + 树配置完整阅读
