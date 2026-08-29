# Paper draft v0 - mature sections S1 / S2 / S6 (AAAI 7-page target)

> Status: draft v0 (2026-08-30, main thread) | Scope: mature sections only; S3-S5, S7 await T1-T6 artifacts
> Discipline: every number below is a traceable value from an existing repo artifact (path in brackets);
> numbers not yet produced are explicit [TODO-*] placeholders - no fabrication, no extrapolation.
> Blueprint: docs/experiments/2026-08-29_long_horizon_eval_paper_blueprint.md (S1-S7 skeleton).

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
same corpus; [TODO-T4: PSO-optimized weights and cost-discriminability Pareto
curve]; [TODO-T6: matching-competition validity threat and oracle ceiling].]

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
