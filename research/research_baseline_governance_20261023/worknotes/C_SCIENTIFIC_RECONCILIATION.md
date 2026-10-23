# C: Scientific Reconciliation And Experiment-Card Pre-Review

Date: 2026-10-23, Asia/Shanghai

Status: `INDEPENDENT_AI_SCI_REVIEW / NOT_HUMAN_GOLD / NOT_AN_EXPERIMENT`

## Mode

Primary mode: `fact-check`; secondary mode: `portfolio-triage` and
`minimal-experiment`. This note checks whether the current claims follow from the
existing artifacts and whether the three proposed cards can identify their
stated mechanisms. It does not authorize or run a model experiment, judge call,
training run, submission, or public release.

## Boundary

Read or mechanically checked:

- `D:/Documents/Loop_D_前置科研治理与资产接续Prompt_20261023.md`
- `D:/Documents/Loop_D_V5科研复核与下一阶段建议_20261023.md`
- `research/publication_thesis_goals_v1/revision_v5/G3_REPORT_V1.md`
- `research/publication_thesis_goals_v1/revision_v5/G3_OFFLINE_RESULTS_V1.json`
- `research/publication_thesis_goals_v1/revision_v5/G3_VISIBLE_FEATURE_PREDICTION_V5.py`
- `research/publication_thesis_goals_v1/revision_v5/G3_VISIBLE_FEATURE_PREDICTION_PROTOCOL_V5.json`
- `research/publication_thesis_goals_v1/revision_v5/G3_VISIBLE_FEATURE_PREDICTION_RESULTS_V5.json`
- `research/publication_thesis_goals_v1/revision_v5/G3_VISIBLE_FEATURE_PREDICTION_REPORT_V5.md`
- `research/publication_thesis_goals_v1/revision_v5/G2_EVALUATION_CONTRACT.md`
- `research/publication_thesis_goals_v1/revision_v5/G2_FIXED_STATE_PROTOCOL_V5.json`
- `research/publication_thesis_goals_v1/revision_v5/g2_fixed_state_transfer_fixed_slots_20261023_v5/G2_FIXED_STATE_RESULTS_V5.json`
- `research/publication_thesis_goals_v1/revision_v5/G2_SEMANTIC_JUDGE_VALIDATED_V5.json`
- `research/publication_thesis_goals_v1/revision_v5/G2_FIXED_STATE_INDEPENDENT_REVIEW.md`
- `paper/saner_rene_claim_matrix_v1.json`
- `paper/overleaf_bundle/saner_rene_manuscript_v1.tex`
- `research/publication_thesis_goals_v1/revision_v5/PAPER_E_SUBMISSION_HANDOFF.md`
- selected training-readiness and PRM smoke records named below

Fresh deterministic checks in this review:

- Hypergeometric `N=400, K=43, n=40`: `E[X]=4.3`,
  `P(X>=5)=0.434752093806`, exact 2.5%-97.5% quantiles `1..8`.
- Sum of rank-4/5 incremental context in the 400-row prediction input:
  `11,850,080` chars; expected cost of 40 uniform draws:
  `1,185,008` chars.

Not checked: literature novelty, external venue state, GB10 runtime, model
quality, semantic truth of generated answers, or a new independent sample.

## Evidence Labels

- `FACT`: directly present in a cited artifact or recomputed here.
- `INFERENCE`: derived from facts; the chain is stated.
- `VALUE`: research-priority judgment.
- `UNVERIFIED`: plausible but not established by current evidence.

## 1. Three Lines Must Remain Separate

| Line | Measurement object | Current defensible conclusion | What it cannot support |
|---|---|---|---|
| Paper E | validity of evaluation measurements | A bounded two-case audit separates visibility, detection, contract-relative harmfulness, score sensitivity, decision stability and reproduction gap; FinQA is a nested measurement-object boundary inside Case 1 | a general validity theory, validated universal checklist, detector ranking, or a third case |
| Evidence sufficiency and reliable use (old G2/state card) | after legal evidence is fixed, whether sufficient current facts/constraints are recovered and then used | Actual generated bundles are often incomplete and current action completion is low; correct automatic state-to-action transfer is not established | that a correct sufficient state is ignored, that one representation is better, or that retrieval is the unique bottleneck |
| Evidence acquisition utility and cost (old G3) | before reading rank 4/5, whether to KEEP or EXPAND and at what full cost | Current labels show 43 measured useful expansions and an oracle coverage/cost headroom; the visible rule is inadequate and the model policy is unevaluated | learned signal beyond random, downstream task benefit, total-cost saving, or a general acquisition method |

These lines are scientifically separable only through interventions. G2 must fix
the evidence package and vary state recovery/representation/use. G3 must fix the
reader and vary evidence acquisition. If both are evaluated by re-retrieving and
regenerating for every question, the resulting comparison does not isolate
either mechanism and should be merged or redesigned.

## 2. Corrections Required In Current Synthesis

### 2.1 G3 depth-2 is compatible with same-budget random

`FACT`: 43/400 rows are useful under the hidden expansion label. The depth-2
tree selects 40 and finds 5, while the same action count has random expectation
4.3 and exact `P(X>=5)=0.434752`; the central exact range is 1-8.

`INFERENCE`: `5/43` is not evidence of a learnable selector signal beyond
random variation. It also does not prove that the task is unlearnable. The
correct status is `NO_IDENTIFIED_INCREMENT_OVER_RANDOM_ON_THIS_DEVELOPMENT_SET`.

Required wording repair:

- Replace `weak learnability signal`, `some visible signal may exist`, or
  `depth-2 weak signal` in
  `RESEARCH_SPRINT_RETURN_V5.md:101-103`, `memory/STATE.md:27`,
  `memory/THREADS.md:15`, and the equivalent synthesis with
  `post-hoc development ranking diagnostic compatible with random variation`.
- Preserve the historical report at
  `G3_VISIBLE_FEATURE_PREDICTION_REPORT_V5.md:34-46`; add a dated correction in
  current synthesis rather than rewriting frozen output.

The action-count comparison is not cost matched. Tree expansion cost is
`1,194,603` chars versus random expectation `1,185,008`; the 10% action cap is
not a token/tool/latency budget.

### 2.2 The G3 predictor protocol description does not match execution

`FACT`: inner thresholds are computed and recorded at
`G3_VISIBLE_FEATURE_PREDICTION_V5.py:135-146`, but outer predictions are not
thresholded with them. Test scores are averaged across repeated folds
(`:124-150`) and thresholded once over all 400 rows (`:175-176`).

`INFERENCE`: this is an OOF batch-ranking diagnostic. It is not nested
threshold execution and cannot be described as an online policy with a frozen
per-training-fold operating point. Repeated folds do not create five
independent replications; the 400 rows remain one development panel.

Required design repair: choose one identity explicitly:

1. rewrite the protocol as `GLOBAL_OOF_RANKING_DIAGNOSTIC`, or
2. implement genuinely frozen per-outer-fold thresholds and report the
   per-fold decisions without selecting the final operating point on all rows.

### 2.3 G3 oracle proves coverage/cost headroom, not task utility

`FACT`: always top-5 reaches `187/400` measured BOTH coverage at
`64,338.07` mean context chars; oracle-selective reaches the same coverage with
43 expansions and `37,292.01` mean chars.

`INFERENCE`: the oracle establishes room to avoid 357 measured no-gain
expansions under the current label. It does not establish that:

- the 357 expansions contain no useful information beyond the label;
- the 43 label-positive expansions improve facts, actions, or task completion;
- selector inference, retrieval, indexing and preprocessing save total cost;
- rank 4/5 selection solves evidence missing from the entire candidate pool.

Use `no measured gain under the current reference`, not `no information value`.
The downstream gain and complete cost are missing measurements.

### 2.4 G2 conditions on fact success that is not sufficient-state recovery

`FACT`: `G2_FIXED_STATE_PROTOCOL_V5.json:40` defines
`paired action success conditional on fact success from the same recovered
bundle`. But the bundle is generated by the method and may omit facts needed for
the action.

Concrete case `12f3fc0d`:

- plain bundle retains the positive current preference of nonfiction,
  biographies/history and supports both fact and action completion;
- evidence-decision bundle retains only the invalidation of strict sci-fi and
  loses the positive current preference; its action asks for genre and is an
  unnecessary refusal/clarification under the current judge.

Concrete case `09949c3c`:

- plain bundle contains the old five-month plan and new 18-month assignment;
  binary answer `No` can correctly reject the old state, but the action remains
  `UNKNOWN`;
- evidence-decision bundle omits `confirmed_fact_1/2` and treats the current
  housing state as unknown.

`INFERENCE`: a correct answer to `is the old state still valid?` is not proof
that the new state is sufficient for action. Action failure in these cases can
be caused by recovery information loss. Current evidence does not identify
downstream use of a correct, sufficient, equal-information state.

The primary metric must be decomposed into:

1. old-state invalidation correctness;
2. recovery of sufficient positive facts, constraints and unknowns with source
   references;
3. downstream use of a fixed sufficient state for fact and action.

Only comparison 3 isolates state-to-action use. Researchers composing
sufficient facts is a diagnostic reference and must not be called normal
method performance or human gold.

### 2.5 Independent-review count summaries are not authoritative

`FACT`: `G2_SEMANTIC_JUDGE_VALIDATED_V5.json` gives:

- plain action: 1 grounded completion, 6 reasonable unknown/clarification,
  1 unnecessary refusal;
- evidence-decision action: 1 grounded completion, 5 reasonable
  unknown/clarification, 2 unnecessary refusals.

`FACT`: both `09949c3c` action rows remain unnecessary refusal before and after
the local validator; there was no validator relabel to reasonable.

`INFERENCE`: the independent-review statement of `1 completion + 7 reasonable`
for both arms is wrong and must not enter the baseline. Preserve the review as
historical/auxiliary evidence, and derive current counts from case-level
artifacts. The underlying `1/8` action completion remains unchanged.

### 2.6 G2 and G3 BM25 results are not direct method comparisons

`FACT`: G2 strips stop words and short tokens; G3 keeps them and adds session/
time prefixes. The observed dim1 BOTH coverage differs (`0.430` versus
`0.4675`).

`INFERENCE`: these are different retrieval implementations. Their difference
cannot be attributed to state handling or acquisition policy. Every result
must bind retrieval version, tokenizer, query field and candidate ordering.

## 3. Paper E Boundary

`FACT`: the claim matrix status is
`AMENDED_2026_10_21_NARROW_AND_CONTINUE`. The manuscript explicitly counts
exactly two cases: Case 1 staged document evaluator with FinQA as a nested
boundary probe, and Case 2 FinRank. It excludes MA-CERD, adaptive revalidation
and later AI-assisted task review from the case count and contribution.

Strongest defensible contribution:

> Across exactly two bounded evaluation audits, the work separates measurement
> objects that final scores conflate and demonstrates concrete reporting
> consequences: visibility is not detection, harmfulness is
> equivalence-contract-relative, score sensitivity need not reverse a
> qualitative decision, and some released values retain an unresolved
> reproduction gap. The six-step sequence is a proposed checklist, not a
> validated universal method.

External use is concrete but narrow: evaluator authors can bind perturbation,
observation, scoring, identity and reported decision to the same measurement
object before interpreting cross-system comparisons. The audit helps decide
what to report and what comparison is interpretable; it does not rank detectors
or certify any benchmark.

Paper E should continue independently. G2/G3 findings are motivation or later
work only and must not become a third confirmation. The submission handoff is
administrative evidence, not additional scientific evidence.

Remaining non-scientific risk: live venue/form details and Owner-only external
actions may change. That does not narrow the scientific claim.

## 4. Experiment-Card Pre-Review

### Card 1: State Information-Loss Localization

Status: `READY_FOR_BOUNDED_DEVELOPMENT / CONFIRMATION_INPUT_MISSING`.

What it can identify:

- `actual bundle -> sufficient-fact/constraint completeness` identifies
  recovery loss;
- `researcher-sufficient state -> fact/action` diagnoses downstream use;
- `plain vs structured with identical semantic content` identifies
  representation effects;
- actual bundle vs sufficient state estimates the combined recovery/use gap.

Required comparisons:

1. Fixed legal evidence and fixed actor.
2. Sufficient-fact diagnostic state and actual generated bundle.
3. Equal-information plain and structured renderings.
4. One-call raw-evidence baseline and a predeclared reasonable-abstention
   baseline.

Primary endpoint: safe grounded action completion under a multi-valid-action
reference. Secondary: stale/unsafe action, reasonable clarification, unnecessary
refusal, interface failure, fact/constraint recall, unsupported additions and
cost. UNKNOWN is neither success nor failure by default.

Current assets:

- 8 exposed development UIDs in `G2_FIXED_STATE_PROTOCOL_V5.json`;
- same top-5 evidence and same generated bundle for fact/action;
- raw bundle/answer records and V5 semantic-judge outputs;
- calibration contract and counterexamples.

Blockers before confirmation:

- sufficient facts/constraints and acceptable action sets must be independently
  specified and versioned, without exposing them to the actor;
- semantic judging needs calibrated disagreement and error rates; current AI
  judge is auxiliary;
- all current UIDs are development-exposed. A later freeze requires new
  UID/user/task groups or a new source, not a reshuffle of these 8.

First executable work: deterministic bundle-completeness audit over the existing
8 UIDs, followed by an information-matched fixture dry-run. This is engineering
and diagnostic evidence only.

### Card 2: Effective Evidence Expansion And Total Cost

Status: `READY_FOR_OFFLINE_DEVELOPMENT / MODEL_LEG_BLOCKED_BY_INTERFACE`.

What it can identify:

- fixed reader + acquisition policy isolates evidence acquisition;
- always top-5, same-budget random and a strong cheap baseline distinguish
  policy from extra evidence/compute;
- end-to-end fact/action change distinguishes relevant-hit gain from task gain;
- total accounting distinguishes saved reader context from selector overhead.

Required comparison:

- KEEP all;
- always top-5;
- uniform random at matched expansion count and, separately, matched character/
  token cost;
- one strong cheap transparent selector fixed on development data;
- candidate selector;
- hidden oracle only as a separately reported diagnostic ceiling.

Fixed reader must consume the same final evidence format. Report retrieval,
index/preprocessing, selector input/output, reader input/output, tool calls,
latency and cache effects. Relevant-session hit is not the primary scientific
endpoint; downstream safe completion or reliable fact recovery is.

Current assets:

- 400-row `T1_T2_400_FULL.json` development replay;
- reproducible offline policy results and model-visible/hidden field contract;
- G3 model receipts and preserved interface failures.

Blockers:

- current model policy has no valid KEEP/EXPAND decision after two calls;
  this is `UNEVALUATED`, not zero accuracy;
- the next interface must be a single action field with sufficient predeclared
  output budget and raw-first receipt preservation;
- the depth-2 result must be reclassified as compatible with random before it
  justifies any learning investment;
- the 400 rows and hidden labels are development material. Confirmation needs
  new UIDs/source clusters and a frozen selector.

First executable work: rerun only deterministic offline baselines with a new
receipt that adds matched-count and matched-cost random controls. Do not spend
model calls until a one-field contract passes a small deterministic fixture.

### Card 3: Small-Model Learning Alternative

Status: `NOT_READY_FOR_SCIENTIFIC_TRAINING / READY_ONLY_FOR_TASK_AND_LABEL_QUALIFICATION`.

The training chain exists, but the scientific task does not yet satisfy the
three-part gate: new task, verifiable supervision, and an executable train/test
contract.

Reusable engineering evidence:

- `docs/research/prm_reference_training_smoke_v1.md` shows Qwen3-4B LoRA,
  checkpoint save and held-out evaluation on GB10;
- `docs/research/prm_reference_training_smoke_audit_addendum_v1.md` shows why
  8 train/4 held-out rows, two steps and overlapping arms cannot establish an
  effect;
- `research/validate_stage_d_training_readiness.py` and
  `docs/datasets/2026-10-05_stage_d_training_readiness_config_v1.json` define
  a dry-run QLoRA configuration and resource gates.

Why old labels cannot be reused directly:

- VGMC checkpoint/action material has conflicts, multiple targets and no
  same-sample bridge sufficient for a clean student target;
- Q3 has 146 columns but only 10 lineage/table-pair clusters, visibility
  exceptions and exploratory adjudication; it is not independent human gold;
- the 60 DPO pairs are single-direction toward skip and fail balanced
  preference requirements;
- PRM smoke labels belong to another task and its license/split/power gates
  remain open. Its runner can be reused, not its tiny comparison as a result.

Preferred fallback candidate: a new CodeUpdateArena-style API-change adaptation
task whose labels are produced by executable tests/checkers, with source/task
groups separated before any teacher generation. This fits the project's
change-and-evidence theme and avoids relabeling old Memory/Valentine panels.
It is only a candidate until the actual train/dev/test examples, license,
student checkpoint and non-training baseline are materialized.

Required arms:

1. no-training/base student;
2. generic supervised examples without the proposed selection signal;
3. simple deterministic filtering;
4. candidate supervision.

All arms must share model, tokenizer, token budget and splits. Primary metric
must be independently executable task correctness, not label fit or loss.
Teacher/generated labels are training inputs, not semantic gold.

First executable work: produce a source-qualified task annex and a deterministic
train/dev/test manifest, then run the existing training-readiness validator.
No GPU training is justified by the present card.

## 5. Required Interpretation Boundaries

- `FACT`: scope `30 versus 35` probes is fully explained by exact cache plus
  miss revalidation; stop extending that panel as a novel scope method.
- `FACT`: state-card end-to-end results trade fewer stale/unsafe outputs for
  more reasonable/unnecessary abstention; this is not action-accuracy victory.
- `INFERENCE`: G2 and G3 remain useful candidate problems because they target
  different interventions, but neither is yet a thesis contribution.
- `VALUE`: prioritize Card 1, retain Card 2 as the independent candidate, and
  hold Card 3 as a learning fallback only after its new task passes supervision
  qualification.
- `UNVERIFIED`: whether any candidate will outperform its strongest simple
  baseline on new source/task groups.

## 6. Recommendation, Risks, Exit And First Action

Recommendation:

1. Main attack: Card 1, because it closes the highest-impact interpretation
   failure and already has concrete counterexamples.
2. Independent candidate: Card 2, after a deterministic matched-random replay
   and a minimal interface repair.
3. Learning fallback: CodeUpdateArena-style task qualification in parallel at
   low cost; defer training until executable labels and a clean split exist.

Conditions:

- Card 1 continues only if sufficient-state action performance exceeds the
  one-call/selective-abstention baseline at matched risk and lower unnecessary
  refusal on new groups.
- Card 2 continues only if a non-oracle policy beats matched random and a
  strong cheap rule on downstream value at matched total cost.
- Card 3 enters training only if the new task has independent executable
  correctness, source-group isolation and a residual after strong simple
  baselines.

Largest risks:

- confusing a diagnostic reference with deployable input;
- letting AI judge errors become method effects;
- treating exposed 400/8-item panels as confirmation;
- spending compute on representation before information sufficiency is fixed.

Exit conditions:

- stop Card 1 if the sufficient-state arm still fails primarily for reasons
  outside state use, or if reference action ambiguity dominates;
- stop Card 2 if matched random/cheap policy explains all measured gain or total
  cost is not lower;
- stop Card 3 before training if executable supervision and independent split
  cannot be formed.

First action: implement the Card 1 deterministic completeness matrix over the
existing eight development UIDs, explicitly marking sufficient-fact references
as diagnostic and deriving counts from case-level JSON.

## Completion Boundary

- Inquiry/review judgment: completed.
- Human decision: not recorded.
- Experiment execution: not performed in this subtask.
- Result acceptance: not applicable.
- No model, judge, training or external call was made.

