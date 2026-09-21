# Paper draft v0 - mature sections S1 / S2 / S6 (AAAI 7-page target)

> Status: draft v0.3 (2026-09-20, main thread; T7 backfill per user ruling 2026-09-20) | Scope: S1-S7 assembled from existing artefacts | S3 was landed 2026-09-10 (ruling 10=c); S4 and S5 body assembled in T7; S6 unchanged; S7 assembled in T7 with the D4-deferral correction note preserved verbatim | every number carries an artefact path; numbers with no artefact remain explicit [TODO-*] with the blocker named
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
perturbations, six defect types), a frozen checkpoint-level discrimination pass
renders 96/118 injections visible (checkpoint-level visibility), while at the
protocol level the same corpus yields 85/118 under flat aggregation and 13/118
under hierarchical expert-weight aggregation. These three figures are three
distinct calibers and are defined once here: checkpoint-level visibility counts an
injection as visible when a checkpoint moves at all; protocol-level detection
counts it as detected when the aggregated score crosses the protocol threshold.
Visibility is therefore not detection, and the two are never interchanged below.
At the table level the same split holds: flat scoring discriminates 75/95 tables
(78.9%), hierarchical expert scoring 20/95. Across all calibers the OCR-similar
class is absorbed silently in all 13/13 cases (visibility 0.0): the text matching
layer maps the corrupted header back to the original field within its
edit-distance tolerance, and no downstream check moves
[logs/graph/eval/checkpoint_discrimination_tables_v2.json;
logs/graph/eval/t1_eval_baseline_comparison.json, arm_b.protocols
.E1.2_flat / .E1.3_hier_expert]. The same pass sees other defect types at 81-100%
visibility. End-to-end correctness alone cannot distinguish "defect detected" from
"defect silently absorbed", and a single score hides the type-structured visibility
spectrum.

Evaluation of long-horizon systems must therefore (i) report a defect visibility
profile per defect type and intensity rather than one aggregate score, and
(ii) treat the evaluation protocol itself as an object of measurement: does it
have the discriminability to separate normal from defective systems, and where is
it structurally blind? On the same frozen corpus, four evaluation protocols order the
same system very differently: an end-to-end protocol detects 112/118 injections, a flat
single-score protocol 85/118, and the hierarchical expert-weight protocol as instantiated
13/118, so the detected-defect count is a property of the scoring protocol rather than of
the tested system [logs/graph/eval/t1_eval_baseline_comparison.json, arm_b.protocols].
The visibility spectrum is also stable in ordering but not in absolute range across the
scoring threshold gamma in {0.2, 0.3, 0.5, 0.7, 0.9}: the OCR-similar class is blind at
every point (0/13) and the type ordering stays non-degenerate (type range 1.0, 0.6471,
0.5882, 0.3, 0.3), while the literal absolute-range criterion fails at gamma 0.7 and 0.9
and is reported as failing rather than relabeled
[logs/graph/eval/t2_visibility_sensitivity.json, prereg_predicates
.E2_1_ocr_similar_blind_all_gamma / .E2_1_type_range_ge_0p5_all_gamma_injection_level /
.E2_1_ranking_non_degenerate_all_gamma].
(Ruling 2a, frozen 2026-08-30: the ranking of the visibility spectrum is stable
across the full threshold grid gamma in {0.2, 0.3, 0.5, 0.7, 0.9}; the absolute range
decays at high gamma by a quantization mechanism - one injection on a table
with n canonical headers moves the score by at most 1/n_canonical, and only
narrow tables remain at high gamma. The mechanism explanation belongs in the
main text; the literal-range criterion failing at gamma 0.7/0.9 is reported as
such, not relabeled. [logs/graph/eval/t2_visibility_sensitivity.json])

## S2 Hierarchical checkpoint evaluation framework (1.25p)

We represent a document pipeline as a forest of checkpoint trees: a parsing tree
(document read-in, table structure, field mapping, arithmetic reconciliation) and
a QA tree (retrieval grounding, faithfulness, numeric correctness, citation,
refusal) - two roots with 12 scored leaves, expert weights in {1,2,3} (chosen by hand
from the importance of each checkpoint, the design point the searched-weight arm later
replaces with an automatic search),
sibling-normalized bottom-up aggregation, hard-gate (hinge) leaves that must clear
the stability threshold (Algorithm 1), and an explicit missing-score policy configured per
tree: the parsing tree assigns 0 to absent evidence, the QA tree assigns a neutral 5
[config/eval_checkpoint_trees.json]. Each leaf is scored either by a
deterministic contract (16/16 contracts pass on the frozen regression set) or,
for open-semantic dimensions, by a leakage-protected judge whose prompt never
sees the injected ground truth (four dimensions, 4.94-5.0 on the baseline set)
[docs/experiments/2026-08-08_eval_baseline.md]; every check retains its evidence
chain, so a root score always decomposes into per-checkpoint findings. The
framework records latency and scores model-call and check-count cost as its cost axis
(scored units: 2 root units for the end-to-end arm versus 12 leaf units for the
checkpoint-level arms), giving the cost axis used later for
cost-discriminability trade-offs.

Algorithm 1 states the aggregation exactly as implemented, so that the framework can be
reproduced from the paper alone. It differs from the deliverable-only original in two
places, both forced by our setting and both marked: leaves are scored by deterministic
contracts wherever a contract exists, and absent evidence is handled by an explicit
policy rather than by omission.

```
Algorithm 1  Recursive checkpoint aggregation (as implemented)
Require: checkpoint tree T with root r; leaf-to-evidence routing R; per-leaf weight w(n)
         in {1,2,3}; per-leaf missing score m(n); hinge-leaf set H = {n : mapping(n) in
         {overall_status_binary, pass_rate_contract, nf_pass_rate}}; threshold set K
Ensure:  per-tree root score S(r) in [0,10]; per-threshold success rates; stability flag

 1: function SCORENODE(n)
 2:     if n has no children then                       # leaf
 3:         v, c, note <- EVIDENCE(n)                    # v: raw rate in [0,1] or judge 0-5
 4:         if v is undefined then                       # missing artefact / unusable judge dim
 5:             return (m(n), degraded <- true, note)     # m(n) = per-tree missing score (parse 0 / QA 5)
 6:         end if
 7:         if mapping(n) = judge_dim_0_5 then return (10 * v / 5, false, note)
 8:         else return (10 * v, false, note)            # rates and binaries map onto 0-10
 9:         end if
10:     end if
11:     C <- children(n)
12:     W <- sum over c in C of w(c)                       # sibling normalisation
13:     S <- 0
14:     for all c in C do
15:         S <- S + (w(c) / W) * SCORENODE(c)             # bottom-up weighted mean
16:     end for
17:     return (S, any child degraded, children aggregated)
18: end function

19: function EVALUATETREE(T, K)
20:     (S(r), degraded, _) <- SCORENODE(r)
21:     L <- leaf scores collected during the traversal
22:     for all k in K do
23:         root_sr(k) <- |{c in children(r) : score(c) > k}| / |children(r)|
24:         leaf_sr(k) <- |{n in L : score(n) > k}| / |L|
25:     end for
26:     k_last <- last element of K                        # as implemented: stability uses the final k
27:     stable <- (|{n in L : score(n) > k_last}| >= 0.9 * |L|) and (for all h in H : score(h) >= 7)
28:     return (S(r), root_sr, leaf_sr, stable, degraded)
29: end function EVALUATETREE
```

Three properties of Algorithm 1 are load-bearing for the rest of the paper. First, the
aggregation is a sibling-normalised weighted mean at every internal node, so the root is a
convex combination of leaf scores and no internal node can exceed its highest-scoring child
[scripts/eval_checkpoint_aggregate.py, aggregate_tree: w_sum and agg]. Second, the hinge
set is a hard gate on the stability flag, not a silent zeroing: a hinge leaf below the
threshold blocks the stable verdict, while a non-hinge leaf does not. The hinge set does not
determine the missing score - absent evidence is scored per tree (0 on the parsing tree, 5 on
the QA tree), so of the five hinge leaves only the parsing-tree one is scored 0. The hinge
set is defined by the mapping, three types hitting five leaves
[config/eval_checkpoint_trees.json, leaves of mapping overall_status_binary /
pass_rate_contract / nf_pass_rate; scripts/eval_checkpoint_aggregate.py, HINGE_ROUTES]. Third, degradation is explicit and reported: an absent
artefact or an unusable judge dimension (average null or n = 0) returns the configured
missing score together with a reason string, and the reason is carried into the report, so
a degraded root score is never indistinguishable from a genuinely low one
[scripts/eval_checkpoint_aggregate.py, _mapped_leaf_score and _judge_avg]. The missing
score is a per-tree configuration, not a property of the hinge set: absent evidence scores 0
on the parsing tree and a neutral 5 on the QA tree. What makes the hinge set load-bearing is
the stability gate, not the missing score: a hinge leaf below the threshold blocks the
stable verdict while non-hinge leaves do not [config/eval_checkpoint_trees.json, the five
leaves whose mapping is one of overall_status_binary / pass_rate_contract /
nf_pass_rate; scripts/eval_checkpoint_aggregate.py, HINGE_ROUTES and the stability
expression]. The whole
procedure is deterministic given the artefacts: no leaf score depends on a live model call,
which is what allows every number in this paper to be recomputed offline
[logs/graph/eval/t1_eval_baseline_comparison.json, aggregation_isomorphism.max_abs_err = 0.0].
Two implementation details are stated because a reader reproducing Algorithm 1 would
otherwise get different numbers from ours. The stability flag is evaluated at the last
threshold passed on the command line, not at a fixed k: the report's stable field therefore
belongs to the k = 8 row under the default threshold list, while the hinge sub-check is
hard-coded at 7 [scripts/eval_checkpoint_aggregate.py, the stable assignment inside the
per-threshold loop]. And the leaf counts are 5 (parse) and 7 (qa), 12 in total, not the 20
implied by an earlier twenty-leaf draft of the tree; the 0.9 fraction is a fraction of the
current leaf count [ibid., result['n_leaves'] per tree; the run above reports parse 5 and
qa 7]. On the live artefacts both thresholds give the same flag, so this
distinction does not change any reported number; it is recorded so the definition is
unambiguous.

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

Missing evidence is a first-class caliber choice rather than a formatting detail: the
hierarchical expert arm scores 20/95 (table level) when its two not-applicable leaves are
excluded from the aggregate instead of filled with a neutral score, and both the exclusion
caliber and the dropped leaf identifiers are recorded with the arm
[docs/experiments/2026-08-30_t1_eval_baseline_comparison_design.md, section 7 supersede
note; logs/graph/eval/t1_eval_baseline_comparison.json, arm_b.armB_tree.dropped_na_leaves].
The four-protocol comparison is reported in S4 and S5; the matching-competition validity
threat and its oracle ceiling are reported in the validity-threats section
[logs/graph/eval/t6_matching_competition.json].
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

Applicability note (ruling 2026-09-04, frozen criteria unchanged): on the
current corpus and frozen checkpoint tree, the hierarchical and flat
protocols are affinely identical on the matched false-positive axis - the
single input-varying leaf makes the layered score exactly 3/8 of the flat
score up to a strict positive affine map, and a 2000-replicate recalibrated
bootstrap gives a protocol-difference CI of [0,0] (same ROC) - so the
0.7895 vs 0.2105 detection gap reported by the W2 window is a
threshold-placement artifact, not protocol discriminability
[logs/graph/eval/d3_matched_fpr_stage_a.json]. Any localization or
diagnostic value of layering on this corpus must come from a second
input-varying leaf (candidate parse.reconcile, folded into Phase D4 under
the unfreeze clause: validation split only, test split untouched, freeze
restored on completion) or from the judge arm, and is reported as such when
available; if the identity null persists it is reported as-is.
Caliber note (ruling F-1, frozen 2026-08-30): the frozen M2 evaluation fixture
used for calibration arms is an **internal calibration arm** (de-identified,
frozen-hash registered); numbers cited in the body come only from public bases
(TAT-QA / TAT-DQA).

## S3 Defect visibility diagnostics (1.5p)

> Namespace note (2026-09-10, append-only): "S3" here is the conference short-paper section
> defined in docs/experiments/2026-08-29_long_horizon_eval_paper_blueprint.md :34. It is
> homonymous with, and unrelated to, "## S3 注入分类学与 crosswalk" in
> docs/experiments/2026-08-27_blind_cone_chapter_skeleton.md :18 (that file numbers the
> dissertation blind-cone chapter). Any citation of "S3" must carry the document name.

Under the frozen evaluator configuration, character-level header perturbations form a
perturbation family with a recomputable definition: every instance touches exactly one
token, has lowercase Levenshtein distance exactly 1, preserves token count, and leaves the
perturbed column's values unchanged in all 13 cases
[logs/graph/eval/d3_autopsy_recompute.json, payload.recomputed_summary.ocr_max_levenshtein_lower
/ .ocr_single_token_touched / .ocr_token_count_preserved / .ocr_c2_value_invariance_holds].
The evaluator is blind to this family across the entire strength grid
gamma in {0.2, 0.3, 0.5, 0.7, 0.9}
(0/13 visible; the grid is the five discrete points {0.2, 0.3, 0.5, 0.7, 0.9}, not a
continuous sweep) [logs/graph/eval/d1_mutant_validity_audit.json,
payload.injections[].visible_by_gamma], and the anchor-stage detection count for the family
is 0 [logs/graph/eval/d1_mutant_validity_audit.json,
payload.counts.anchor_detected_by_type.ocr_similar]. This total blindness is the strongest
endpoint of the visibility spectrum observed in this study. Whether the blind spot
constitutes a missed detection depends on the definition of the equivalence class; we treat
that question as a boundary condition in S7 and claim here only the directly observable
evaluator property.

Beyond this family, the window identifies criterion-relativity of instance-level harmfulness
labels. All 7 type-level equivalence-class members survive 0/7 under an instance-level
oracle [logs/graph/eval/d3_autopsy_recompute.json, payload.recomputed_summary.d1_E_total /
.d1_E_surviving_oracle]; 5 of the 8 cross-criterion comparison rows disagree, and every
disagreement falls on the criterion-kind axis - canonical form / canonical truth
preservation versus reader referent recoverability - rather than splitting along defect type
[ibid., .dr4_agree / .dr4_disagree / .dr4_rows_miss_side / .dr4_rows_false_alarm_side;
stratification A-07]; and identical input strings receive consistent verdicts in 3/3
repeated groups, ruling out sampling noise as an alternative explanation [ibid.,
.identical_input_groups / .identical_input_groups_verdict_consistent]. We therefore claim
that instance-level harmfulness labels are criterion-relative, that the disagreement
structure of the visibility spectrum is characterized by two orthogonal axes (a granularity
axis and a criterion-kind axis), and that disagreement appears block-wise along the
criterion-kind axis rather than case-by-case at random. When citing that 14 of 21
zero-signal injections were judged equivalent, the family stratification must be reported
alongside (13/13 within ocr_similar; 1/8 in the non-ocr_similar subset), and it must not be
stated as a global claim that most of the zero-signal harmful set was judged harmless
[ibid., .jn1_n / .jn1_equivalent / .ocr_similar_equivalent / .non_ocr_n /
.non_ocr_equivalent].

Relation to mutation testing. A reader from the mutation-testing literature will
recognise the injection setup: a synthetic defect is introduced, and the question is
whether the evaluator notices. The difference is what gets reported. Mutation testing
reduces to a binary kill/no-kill per mutant and summarises with a mutation score; silent
absorption is simply an unkilled mutant. We keep the absorbed case as a first-class,
separately named outcome and report it per defect family rather than collapsing it into the
kill count, because an absorbed defect and an untested defect call for different responses
in this domain. The family-level visibility rates in S3 are the corresponding statistic.

## S4 Protocol rigor: what the score actually measures (1.0p)

The evaluation protocol is itself measured before its numbers are used. On the frozen
selection corpus the four-protocol comparison separates two effects that a single score
confounds. Detection counts are protocol-dependent: end-to-end detects 112/118
injections, flat 85/118, and the hierarchical expert arm as instantiated 13/118, so the
protocol difference is not a noise-level detail but a reordering of what counts as
detected [logs/graph/eval/t1_eval_baseline_comparison.json, arm_b.protocols
.E1.1_end_to_end / .E1.2_flat / .E1.3_hier_expert]. The checkpoint-level arms separate the
same mutants further: per-protocol tree-root mean separation is 2.5053 (end-to-end), 2.5072
(flat), 2.5053 (hierarchical, expert weights) and 2.8563 (hierarchical, searched weights),
against blended separations of 1.2526-1.4282 [ibid., arm_a.protocols, fields
.mean_separation_tree_root / .mean_separation_blended]. The apparent gain comes with a cost:
the checkpoint-level arms report 12 per-leaf decomposition dimensions where the end-to-end
arm reports only 2 aggregated root scores, and the two calibers are not commensurable, so
both are reported and never averaged.

We make the protocol-dependence explicit on the matched false-positive axis, where a
single aggregate number would mislead. Holding the false-positive rate fixed by
recalibrating each protocol on clean tables, the hierarchical and flat protocols are
affinely identical on the current corpus: the input-varying part of the score reduces to a
single leaf, so the layered score is a strict positive affine image of the flat score, and
the 2000-replicate table-cluster bootstrap gives a protocol-difference confidence interval
of [0, 0] [logs/graph/eval/d3_matched_fpr_stage_a.json, payload.a4_matched_fpr]. The
0.7895 versus 0.2105 gap visible in the raw counts is therefore a threshold-placement
artifact rather than protocol discriminability, and we report it as such. Clean controls
are enumerable as a structural fact - 2384 clean tables, of which 2382 are usable, the two
exclusions lacking a self-derived canonical header - and on those tables any within-table
contrastive score is identically 0 under the frozen definition, which is why the matched
comparison yields a null rather than a power problem [ibid., payload.preflight.P1 /
payload.a2_clean_controls_fpr.enumeration].

Weight search is reported for what it buys, not as a contribution. A particle-swarm search
over the same weight space reproduces the greedy result exactly (mean separation 1.432574
on 5 seeds, identical to greedy, at 7650 evaluations versus 67) and beats the equal, expert
and random-30 controls while not improving the worst-case mutant
[logs/graph/eval/t4_pso_fair_comparison.json, payload.t4.primary_separation_table;
payload.prereg_predicates.C3_pso_beats_four_controls = PARTIAL, degradation clause
triggered]. A minimax variant trades mean separation for worst-case separation (1.25605
mean versus 0.35714 worst) [ibid., .pso_minimax_5seeds]. We therefore keep expert and
greedy calibers throughout and present automated search as a way to avoid expert
weight-tuning cost, stating the worst-dimension regression alongside.

A cross-matcher check bounds how far the blindness result travels. Re-running the same
spectrum under four matchers - production greedy, normalized-distance greedy, and the
Hungarian global assignment under both score calibers - leaves the blind set identical to
[ocr_similar] in all four: the spectral structure, meaning the existence of a fully blind
type, is matcher-independent within the edit-distance family
[logs/graph/eval/d2_cross_matcher_det.json, payload.r3_assessment
.blind_set_identical_across_prereg_family]. What does move is the ranking: 0 assignment
flips under the assignment axis but 5 class flips under the scoring axis, all on
date_variant, so rank changes are driven by scoring caliber rather than by the allocation
algorithm. The position of the blind class is preserved; the relative order of the visible
classes is not, and both facts are reported rather than the flattering one.

Finally, the judge dimension of the framework is calibrated against a deterministic
reference. The pre-registered consistency bound is per judge dimension on the 0-5 judge scale
(|delta| <= 0.5); scoring all 120 leaf-state cells with a judge instead of the
deterministic mapping meets it (max observed 0.5). Derived to the 0-10 tree-root scale, the
control tree roots differ by at most 0.22, while individual leaves move by up to 7.0: the
control holds at the aggregate level, not per cell [logs/graph/eval/t4_pso_fair_comparison.json,
payload.e1_5.endpoint_consistency_note / .judged_vs_mapped_max_abs_delta]. One mutant is
invisible to the judge for a fidelity reason rather than a judge-capability reason: the
zero-signal injection lands only on aggregate counters while the affected items carry no
numeric claim, so its separation is 0.0000 and it is excluded from judge-side claims
[ibid., payload.findings.F_W2_1_m7_item_level_invisible].

## S5 Experiments (1.5p)

**Main comparison.** Table 1 reports the four protocols on one frozen corpus of 95 tables
carrying 118 injections, with table-level and injection-level detection and bootstrap
confidence intervals. The protocols are ordered by how much structure they score:
end-to-end evaluates only the final artefact, flat averages every leaf, and the hierarchical
arms aggregate leaves bottom-up under sibling-normalized expert weights. Detection falls
monotonically as the protocol scores more structure rather than the artifact alone, from
112/118 injections under end-to-end to 13/118 under the expert hierarchy; the hierarchical
arms are not a more sensitive detector on this corpus at this threshold, and the per-type
breakdown shows where the loss concentrates (alias_variant 41/47 end-to-end versus 2/47
hierarchical) [logs/graph/eval/t1_eval_baseline_comparison.json, arm_b.protocols].

| protocol | scored units | tables detected | injections detected |
|---|---|---|---|
| E1.1 end-to-end | 2 (root scores) | 95/95 (1.0) | 112/118 (0.9492) |
| E1.2 flat | 12 (leaves) | 75/95 (0.7895, CI95 [0.6947, 0.8737]) | 85/118 (0.7203) |
| E1.3 hierarchical, expert weights | 12 (leaves) | 20/95 (0.2105, CI95 [0.1263, 0.2947]) | 13/118 (0.1102) |
| E1.4 hierarchical, searched weights | 12 (leaves) | not transferable (see below) | not transferable |

Table 1. Four-protocol detection comparison on the frozen corpus. Counts and intervals are
read from the artefact; the searched-weight row is marked not transferable because the
search space is defined over an 11-dimensional internal-node space that is not isomorphic
to the instantiated tree used in the table-level arm, so transferring it would compare two
different objects [logs/graph/eval/t1_eval_baseline_comparison.json, arm_b.protocols
.E1.4_hier_pso].

**Sensitivity.** The visibility spectrum is probed over a five-point threshold grid. The
blind class is blind at every point and the type ordering stays non-degenerate, while the
absolute range contracts as the threshold rises, because a single injection on a table with
n canonical headers can move the score by at most 1/n and only narrow tables remain at high
gamma [logs/graph/eval/t2_visibility_sensitivity.json, prereg_predicates]. Injector-seed
sensitivity is bounded separately: re-running the flat protocol under three seeds with
everything else held fixed gives table-detection rates of 0.7895, 0.7835 and 0.7556, a
spread of 0.0339, pooled 0.7766 with CI95 [0.727, 0.8227], and the seed-42 run reproduces
the frozen artifact byte-for-byte
[logs/graph/eval/t4_pso_fair_comparison.json, payload.e1_6.seed_distribution_E1_2_flat /
.pooled_across_seeds / .gate_seed42_byte_identity].

**Ablation.** Two ablations isolate the aggregation machinery from the scoring content.
Weights: equal, expert, random-30 and searched settings land within 1.2560-1.4326 mean
separation, with the searched setting matching greedy exactly and the worst-case mutant
unchanged at 0.0926, so the weight axis moves the headroom but not the weakest case
[logs/graph/eval/t4_pso_fair_comparison.json, payload.t4.primary_separation_table].
Allocation: replacing greedy assignment with Hungarian global assignment changes 0
assignments and 0 flips, and a positive control confirms the solver does detect
improvements when they exist (403.0 versus 806.0 on the control instance), so the null is a
property of the corpus rather than a degenerate solver
[logs/graph/eval/t6_matching_competition.json, prereg_predicates.P1_branch /
solver_validation].

**External validity.** The spectrum is re-run under four matchers and the blind set is
identical across all four, while 5 class flips appear on the scoring axis alone; the
structure is stable and the ranking is not [logs/graph/eval/d2_cross_matcher_det.json,
payload.r3_assessment.axis_attribution]. Two external-validity probes are **not** reported
as results. A second dataflow was pre-registered but deferred, because the family-level
constructible-n table is undefined on the frozen contract (the corpus carries no table
layer), so no number from it exists and none is cited. The judge arm covers 28 cases at the
injection level and 120 leaf-state cells at the aggregate level; both are reported with
their counts so their scope is readable, and neither is extrapolated to families that
received zero calls [logs/graph/eval/t4_pso_fair_comparison.json, payload.e1_5.cells_total /
.cells_ok; logs/graph/eval/d3_matched_fpr_stage_b.json, call_counter_breakdown;
logs/graph/eval/d1_mutant_validity_audit.json, payload.injections[] type counts].

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
docs/experiments/2026-08-29_collision_expansion_experiment.md]. Which dimension fires is
part of the mechanism and we report it as such: in the adversarial arm all seven
rejections fired on the gain dimension (collateral was exactly 0.0, so the
collateral-side path never activated), whereas the collateral dimension became routinely
active only once the collision regime was expanded [docs/experiments/
2026-08-28_adversarial_arm_experiment.md, mechanism-correction note (2026-08-29);
docs/experiments/2026-08-29_collision_expansion_experiment.md, collateral dimension
fully activated].

We present this strictly as a mechanism case, not an efficacy claim: the main
effect of gating on downstream correctness is not significant at current corpus
size (table-level delta V(ACC) = 0.05 with CI containing 0; column-level 7/40 vs
4/40, exact McNemar p = 0.375)
[docs/experiments/2026-08-29_column_sensitivity_analysis.md]. The case
instantiates evaluation-driven safe self-learning without reinforcement-learning
or preference-optimization machinery, and its honest null motivates the larger
thesis question of when collision exposure, suggestion reliability and per-collision
harm jointly determine gating value.


## Threats to validity

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

## S7 Discussion, limitations, conclusion (0.5p)

> Landing note (2026-09-10, append-only, ruling 10=c): this boundary paragraph is
> provisional with respect to exactly one input - the second-scorer arm pre-registered for
> D4. If that arm reports, this paragraph is revised by an appended correction note, not by
> rewriting (decision 4A discipline). No scenario / counterfactual figure from receipt
> A-16 appears in S3 or S7 (retroactive=false, non-paper numbers).

The harmfulness judgements in this study depend on the frozen scorer/matcher
equivalence-class definition, and we make none of the following four claims. First, we do
not adjudicate which of the two criteria is correct: under the frozen judge protocol, 14 of
21 zero-signal injections were judged equivalent, so the implicit assumption that zero
signal implies harmful cannot be sustained at the instance level, and that judgement depends
on the scorer/matcher equivalence-class definition; this window shows only that the judge so
decided, not that the decision is true. Second, we do not claim that referent recoverability
is the correct equivalence-class definition; it was observed under a single judge, a single
frozen protocol, and n = 28 [logs/graph/eval/d3_autopsy_recompute.json,
payload.recomputed_summary.n_judge_cases]. Third, a single judge at n = 28 does not support
extrapolation to untested perturbation families: mixed_lang (20 instances) and unit_suffix
(5 instances) received zero calls in this window, so we draw no conclusion about them
[logs/graph/eval/d1_mutant_validity_audit.json, payload.injections[] type counts;
logs/graph/eval/d3_matched_fpr_stage_b.json - absence of verdict rows for these two
families]. Fourth, we write neither the judge verdict nor the DR4 oracle as ground truth;
their disagreement is itself a result of this study rather than evidence that either side
failed, and the 8 comparison rows must be reported split by direction (7 miss-side rows,
1 false-alarm-side row), with any direction of n < 5 reported as counts only, never as rates
[logs/graph/eval/d3_autopsy_recompute.json, payload.recomputed_summary.dr4_rows_miss_side /
.dr4_rows_false_alarm_side].

Accordingly, the total blindness reported in S3 should be read as an observation about the
evaluator, while whether that blind spot constitutes a missed detection remains an open,
definition-dependent question; the 13 instances remain in the harmful injection set, and
neither the detection denominator nor the primary TPR was changed by this window's
judgements [ibid., .s2_denominator_frozen / .s2_tpr_frozen]. The pre-registered next window
stratifies by perturbation family x criterion kind and adds a second-scorer arm, to test
whether criterion-relativity is a property of the criterion kind or of a single scorer;
until that arm reports, the claim is not upgraded.

> Correction note (2026-09-12, append-only; supersedes the forward-looking sentence above,
> which is preserved verbatim as trajectory per the decision-4A discipline):
> the pre-registered next window described in that sentence **is no longer scheduled**.
> The D4 transfer experiment was deferred by ruling 21=D (2026-09-11) because the
> family-level constructible-n table is undefined on the frozen TAT-DQA joint-v1 contract
> (the corpus carries no table layer, so per-family n has no definition); the deferral was
> for that reason only, not for budget, endpoint or scheduling reasons. Consequently the
> second-scorer arm has **not reported and is not pending**: it is deferred. Two consequences
> for this section, both of which tighten rather than loosen the claim boundary:
> (1) the criterion-relativity claim **remains at its D3 evidence level and is not upgraded**
>     - the sentence above said the claim would not be upgraded until the arm reports, and
>     that still holds, now for a stronger reason (the arm is deferred, not merely awaited);
> (2) nothing in S3 or S7 may cite a family x criterion-kind stratification, a second-scorer
>     result, or any D4 number, because none exists. Any such citation would be a reference to
>     an experiment that was never run.
> The four claim-boundary items stated earlier in this section are unchanged, and the study
> still adjudicates nothing about which criterion is correct: judge and DR4 oracle remain
> non-ground-truth, and the disagreement between them remains a result rather than a defect.
> Assembly note (2026-09-20, append-only, T7): S7 is now assembled. The closing paragraph above
> was written before assembly and is preserved verbatim as trajectory; the assembled prose below
> adds the algorithmic contribution to the discussion and states the limits that remain.

Our contribution is not a new detector and we do not present one. What the study
contributes is a way to measure an evaluation protocol itself: a checkpoint forest that
turns a single end-to-end score into a decomposable one, a visibility profile that reports
per-type rather than aggregate detectability, and an explicit account of where the protocol
is blind. The finding that most changes how such protocols should be reported is negative
in form and therefore worth stating plainly: on this corpus, adding structure to the score
does not buy additional discriminability at a matched false-positive rate, because the
input-varying part of the layered score collapses onto a single leaf and the two protocols
end up related by a positive affine map [logs/graph/eval/d3_matched_fpr_stage_a.json,
payload.a4_matched_fpr]. Structure buys localization and evidence decomposition, not
sensitivity, and the paper claims exactly that and no more
[logs/graph/eval/t1_eval_baseline_comparison.json, arm_a.protocols.localization_rate].

Three limits bound the claims and are stated rather than deferred. First, the visibility
spectrum is measured on a single corpus of synthetic perturbations over a public tabular
base; the blind class is stable across four matchers and across injector seeds, but a
different corpus could move it, and no cross-domain transfer is claimed
[logs/graph/eval/d2_cross_matcher_det.json, payload.r3_assessment;
logs/graph/eval/t4_pso_fair_comparison.json, payload.e1_6.seed_distribution_E1_2_flat].
Second, the harmfulness of an injection is criterion-relative, and we adjudicate neither of
the two criteria; the second-scorer arm that would have separated criterion-kind from
scorer effects was pre-registered and is now deferred, so the claim stays at its current
evidence level rather than being upgraded. Third, the matching-competition ceiling is a
property of the scoring layer rather than of the assignment algorithm: greedy is already
globally optimal here (0 flips against Hungarian) while the oracle correctness ceiling drops
from 0.952381 to 0.597015 under overlay sharing, so no post-hoc assignment fix is proposed
[logs/graph/eval/t6_matching_competition.json, gates.g4_oracle_plain /
.g4_oracle_overlay].

Two directions follow and are deliberately left open. The layer-level localization that the
hierarchy provides is only observable when more than one leaf varies with the input; the
current frozen tree has exactly one, which is why the matched comparison is an identity, and
a second varying leaf is the minimal change that would make localization measurable
[logs/graph/eval/d3_matched_fpr_stage_a.json, payload.a4_matched_fpr]. And because
Algorithm 1 is deterministic given artefacts, the same instrument that evaluates the system
can be reused as the objective of a weight search, which is where the searched-weight arm
already operates; whether that search is worth its cost is answered negatively on this
corpus and is left as a question for larger ones
[logs/graph/eval/t4_pso_fair_comparison.json, payload.t4.primary_separation_table].

We close on the observation that motivated the study. A system can be correct at the end and
unreliable in the middle, and an evaluation protocol can be sensitive to one defect family
and blind to another; a single number cannot express either distinction. Reporting
decomposable scores with an explicit visibility profile, and measuring the protocol
alongside the system, costs little and makes those distinctions visible - which is the whole
of the claim we make.

## 审稿人视角五问注记（paper-review-check 一轮, 2026-08-30 夜, Loop D 自审; 结论权在 Loop C/用户）

五问 = skill 五焦点: 核心主张 / 方法 / 实验 / 写作 / 风险。blocking 与 polish 分列。

### S1
- [polish] 与变异测试谱系（簇一）的对位句缺失: 静默吸收 ≈ "mutant 未杀死测试", 但本文按层报告可见性而非二元 kill——reviewer 首问必是"与 mutation testing 何异"。修: S1 末或 S3 加一句对位（相关工作 v3 簇一已备素材）。
- [已处理 2026-09-20 T7] 78.9%/81.4% 单匹配器外部效度: 原占位 [TODO-T6-crossref] 已由 S4 末段承接——四匹配器下盲集恒为 [ocr_similar]（结构稳、名次不稳），且 T6 分支 a 记录分配层不可消解 [logs/graph/eval/d2_cross_matcher_det.json, payload.r3_assessment; logs/graph/eval/t6_matching_competition.json, prereg_predicates.P1_branch]。
- 主张清晰/新颖/有据: 无 blocking。

### S2
- [已处理 2026-09-20 T7] Algorithm 1 伪代码已入 S2（含输入/输出/聚合规则/缺失值处理/hinge gate 行为），逐行对位表落 docs/experiments/2026-09-20_algorithm1_lines_vs_impl.md [scripts/eval_checkpoint_aggregate.py]。
- [已处理 2026-09-20 T7; **2026-09-21 批 #8-C 更正口径**] missing-score 政策敏感性已披露: S2 新段落写明 E1.3 的 20/95 来自「排除」口径, 并给出 dropped_na_leaves 与设计稿 §7 supersede 注记指针。**原句「S4 另记判定级 missing 政策（hinge 用 0、其余用中性 5）」口径有误已删**——实测 missing score 是**按树配置**（parse 树全 0 / qa 树全 5）, 与 hinge 集合不重合（5 个 hinge 叶中仅 1 个为 0）; hinge 的作用是 stability 判据（详见 S2 正文与对位表 §2）[config/eval_checkpoint_trees.json].
- [已处理 2026-09-20 T7] 专家权重 1-3 手工设定: S2 保留手工权重表述, S4 给出搜索臂的回答（同值 1.432574、7650 vs 67 次评估、最坏维未改善）[logs/graph/eval/t4_pso_fair_comparison.json, payload.t4.primary_separation_table]。
- 术语/记号一致: visibility profile / silent absorption 与蓝图命名裁定一致, 无 blocking。

### S6
- [已处理 2026-09-20 T7] gain/collateral 门已在 S6 正文形式化（accept iff expected gain >= tau and collateral >= -epsilon），并保留「机制案例非功效主张」定位；tau/epsilon 的具体取值属 T5/门控章, 不在本文档范围。
- [polish] 非显著案例的入选理由应前置一句（对抗臂 100% 门拒是机制信号, 非功效主张）——现有文本已含但位置靠后, 提前。
- 语料体制标注: 对抗臂/碰撞体制分列 ✓ 无 blocking。
