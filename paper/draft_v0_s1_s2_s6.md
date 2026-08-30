# Paper draft v0 - mature sections S1 / S2 / S6 (AAAI 7-page target)

> Status: draft v0 (2026-08-30, main thread) | Scope: mature sections only; S3-S5, S7 await T1-T6 artifacts
> Discipline: every number below is a traceable value from an existing repo artifact (path in brackets);
> numbers not yet produced are explicit [TODO-*] placeholders - no fabrication, no extrapolation.
> Blueprint: docs/experiments/2026-08-29_long_horizon_eval_paper_blueprint.md (S1-S7 skeleton).
> Boundary: internal draft; no public disclosure (arXiv/submission/preprint) before patent filing status confirmed (docs/34 section 6).

## S1 Problem: final correctness is not step reliability, and evaluation itself can be blind (0.75p)

Long-horizon document intelligence systems chain parsing, schema/semantic mapping,
retrieval and reasoning, and output generation. Practice evaluates them end to end:
if the final answer is right, the pipeline passes. We argue this conflates two
distinct failure modes and can certify systems whose intermediate steps are
unreliable, or worse, certify evaluation protocols that cannot see their own blind
regions.

We make the blindness concrete with controlled defect injection. On 95 tables and
118 header-drift injections built from a public tabular base (fully synthetic
perturbations, six defect types), a frozen hierarchical evaluation discriminates
75/95 tables (78.9%) and renders 96/118 injections visible (81.4%) - yet the
OCR-similar class is absorbed silently in all 13/13 cases (visibility 0.0): the
text matching layer maps the corrupted header back to the original field within
its edit-distance tolerance, and no downstream check moves
[logs/graph/eval/checkpoint_discrimination_tables_v2.json]. The same protocol sees
other defect types at 81-100% visibility. End-to-end correctness alone cannot
distinguish "defect detected" from "defect silently absorbed", and a single score
hides the type-structured visibility spectrum.

Evaluation of long-horizon systems must therefore (i) report a defect visibility
profile per defect type and intensity rather than one aggregate score, and
(ii) treat the evaluation protocol itself as an object of measurement: does it
have the discriminability to separate normal from defective systems, and where is
it structurally blind? [TODO-T1: four-protocol baseline comparison table]
[TODO-T2: threshold-grid sensitivity of the spectrum]
(Ruling 2a, frozen 2026-08-30: the ranking of the visibility spectrum is stable
across the full threshold grid gamma in {0.2, ..., 0.9}; the absolute range
decays at high gamma by a quantization mechanism - one injection on a table
with n canonical headers moves the score by at most 1/n_canonical, and only
narrow tables remain at high gamma. The mechanism explanation belongs in the
main text; the literal-range criterion failing at gamma 0.7/0.9 is reported as
such, not relabeled. [logs/graph/eval/t2_visibility_sensitivity.json])

## S2 Hierarchical checkpoint evaluation framework (1.25p)

We represent a document pipeline as a forest of checkpoint trees: a parsing tree
(document read-in, table structure, field mapping, arithmetic reconciliation) and
a QA tree (retrieval grounding, faithfulness, numeric correctness, citation,
refusal) - two roots with 12 scored leaves, expert weights in {1,2,3},
sibling-normalized bottom-up aggregation, hard hinge gates that zero a subtree on
gate failure, and explicit missing-score degradation when evidence is absent
[config/eval_checkpoint_trees.json]. Each leaf is scored either by a
deterministic contract (16/16 contracts pass on the frozen regression set) or,
for open-semantic dimensions, by a leakage-protected judge whose prompt never
sees the injected ground truth (four dimensions, 4.94-5.0 on the baseline set)
[docs/experiments/2026-08-08_eval_baseline.md]; every check retains its evidence
chain, so a root score always decomposes into per-checkpoint findings. The
framework scores latency and model-call cost as first-class dimensions, giving
the cost axis used later for cost-discriminability trade-offs.

Defect injection turns the framework into a meta-evaluation instrument. We inject
controlled mutants at two granularities - nine checkpoint-level mutants spanning
contract failures, judge degradation, grounding loss and catastrophic parse
states [logs/graph/eval/checkpoint_discrimination_report.json], and 118
header-drift injections across six types (alias, mixed-language, unit-suffix,
date, OCR-similar, prefix noise) [logs/graph/eval/checkpoint_discrimination_tables_v2.json] -
and record, per injection, whether the defect is (a) detected at a checkpoint,
(b) silently absorbed by an intermediate layer, or (c) manifested downstream.
The resulting visibility profile is the paper's core diagnostic: it locates which
defect families the protocol cannot see and which layer absorbs them.

[TODO-T1: end-to-end-only / flat-weighted / hierarchical-expert baselines on the
same corpus; [TODO-T6: matching-competition validity threat and oracle ceiling].]
Weight-search note (J3 ruling, frozen 2026-08-30; PSO removed from
contributions): a particle-swarm weight search reproduced the same mean
separation (1.4326) as greedy coordinate ascent at 114x the evaluation cost
(7650 vs 67 evaluations, 5 seeds identical), so all reported weights use
greedy/equal calibers [logs/graph/eval/t4_pso_fair_comparison.json].

Pre-registered positioning (ruling 1a, frozen 2026-08-30; wording superseded
the same day per adopted expert review - the paper may state less than the
preregistered degradation ceiling, and it does; frozen criteria unchanged):
"Hierarchical checkpoints provide layer-level localization and decomposable
evidence under a lower evaluation budget, but do not improve raw
defect-detection sensitivity in the current setting."
(Both arms detect below flat: arm A 3/9 vs 4/9, arm B 20/95 vs 75/95;
cost axis 2 vs 12 units.)
Caliber note (ruling F-1, frozen 2026-08-30): the frozen M2 evaluation fixture
used for calibration arms is an **internal calibration arm** (de-identified,
frozen-hash registered); numbers cited in the body come only from public bases
(TAT-QA / TAT-DQA).

## S6 Closed-loop case: evaluation findings into gated rule consolidation (0.5p)

We close the loop with a compact case study of how evaluation findings feed back
into the system under test. Findings of unmapped or mis-mapped headers generate
candidate rule fixes; each candidate passes a gain-collateral double gate (accept
iff expected gain >= tau and collateral damage >= -epsilon), is consolidated as a
deterministic rule artifact, and must clear a regression verification gate before
re-entering evaluation. In the adversarial-suggester arm, the gate rejects 7/7
(100%) high-confidence wrong mappings, and 5/5 in the expanded-collision regime -
with a complete audit chain of proposals, gate decisions and consolidated rules
[docs/experiments/2026-08-28_adversarial_arm_experiment.md;
docs/experiments/2026-08-29_collision_expansion_experiment.md].

We present this strictly as a mechanism case, not an efficacy claim: the main
effect of gating on downstream correctness is not significant at current corpus
size (table-level delta V(ACC) = 0.05 with CI containing 0; column-level 7/40 vs
4/40, exact McNemar p = 0.375)
[docs/experiments/2026-08-29_column_sensitivity_analysis.md]. The case
instantiates evaluation-driven safe self-learning without reinforcement-learning
or preference-optimization machinery, and its honest null motivates the larger
thesis question of when collision exposure, suggestion reliability and per-collision
harm jointly determine gating value.


## Threats to validity (stub; ruling 3 landed 2026-08-30, formal assembly in T7)

Matching competition. Under overlay shared headers, multiple canonical
variants of the same column compete for a single slot; even when every
ground-truth rule is present, inter-column competition compresses the
correctness ceiling (oracle: plain 0.952381 vs collision 0.597015). Gating
blocks incremental harm only, not the stock competition
[logs/graph/eval/t6_matching_competition.json].

Branch-a verdict (T6, pre-registered): Hungarian global assignment vs greedy
differs by 0 assignments and 0 flips on the frozen corpus - greedy is already
globally near-optimal at this scoring layer. Matching competition is therefore
**not resolvable at the allocation layer; the root cause is scoring-layer
pollution**: near-identical strings receive the same score band as ground
truth. Reported as a validity threat to the single-matcher visibility
spectrum, not as an efficacy claim.

## 审稿人视角五问注记（paper-review-check 一轮, 2026-08-30 夜, Loop D 自审; 结论权在 Loop C/用户）

五问 = skill 五焦点: 核心主张 / 方法 / 实验 / 写作 / 风险。blocking 与 polish 分列。

### S1
- [polish] 与变异测试谱系（簇一）的对位句缺失: 静默吸收 ≈ "mutant 未杀死测试", 但本文按层报告可见性而非二元 kill——reviewer 首问必是"与 mutation testing 何异"。修: S1 末或 S3 加一句对位（相关工作 v3 簇一已备素材）。
- [polish] 78.9%/81.4% 单匹配器外部效度: reviewer 会问盲区是匹配器属性还是协议属性。缓解证据在 T6 分支 a（分配层不可消解）——S1 加交叉引用占位 [TODO-T6-crossref]。
- 主张清晰/新颖/有据: 无 blocking。

### S2
- [blocking-占位] Algorithm 1 伪代码未入稿（方法完整性）。修: [TODO: algorithm-description 产伪代码, 与 eval_checkpoint_aggregate.py 逐行对位]。
- [blocking-披露] missing-score 政策敏感性: E1.3=20/95 对 missing 处理（排除 vs 补 0）敏感, 草稿未披露。修: S2 加 missing-score 政策句 + 指向 T1 设计稿 §7 supersede 注记。
- [polish] 专家权重 1-3 手工设定: 加前向引用 S4（PSO 搜索即该问题的回答）。
- 术语/记号一致: visibility profile / silent absorption 与蓝图命名裁定一致, 无 blocking。

### S6
- [polish] gain/collateral 门未形式化（τ/ε 取值未给）。修: 加一行门定义或指向方法章占位。
- [polish] 非显著案例的入选理由应前置一句（对抗臂 100% 门拒是机制信号, 非功效主张）——现有文本已含但位置靠后, 提前。
- 语料体制标注: 对抗臂/碰撞体制分列 ✓ 无 blocking。
