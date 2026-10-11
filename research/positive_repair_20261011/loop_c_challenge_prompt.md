# Loop C Fresh-Context Scientific Challenge — Positive Repair Candidate Set (draft)

You are the independent Loop C auditor. This is a DESIGN-STAGE, read-only challenge of 8 draft repair candidates, produced before any first-round experiment is selected or run.

Scope and rules:
- You receive this packet only. No tools, no file reads, no network, no model calls, no edits. Do not attempt to modify anything. Report only.
- Authorized purpose: challenge the draft candidates and return verdicts. This is NOT an experiment, NOT a result, and NOT an execution authorization.
- Judge only from this packet. If the packet lacks evidence you need, say so explicitly as `UNVERIFIED`; do not assume missing facts.
- Separate `FACT` / `INFERENCE` / `UNVERIFIED` in your answers. Zero findings is allowed if supported.

## Context (compressed evidence base; all from frozen project artifacts)

- Program: measurement-validity research ("Visibility Is Not Detection"). Current paper route is SANER Route A. Track P is a bottom-up repair portfolio: audit finding -> minimal repair -> held-out evidence -> replication -> shared principle. No top-down method is required or pre-assumed.
- A "positive repair" here must be: scientifically clean, low cost, reproducible, held-out evaluable, one main design factor changed per experiment, NULL informative, and free of measurement-object cheating (no changing the metric/threshold/object to manufacture gain; no direct-codebook gain; no outcome-selected samples; no oracle-target edits for gain).
- Frozen evidence fragments used below:
  - E1: 95 tables / 118 header-drift injections; 96/118 visible; OCR-like 0/13 across 11 clusters; families alias(43/47), date(15/17), mixed(20/20), ocr(0/13), prefix(13/16), unit(5/5).
  - E2: clean-only matched-FPR operating point `NOT_IDENTIFIABLE`; 2,382 clean rows have contrastive support exactly {0}; equality claim degraded; the frozen doc names the remedy as "a revised score definition with nonzero clean support or a separately preregistered pseudo-injection/null-mutation panel".
  - E3: multi-leaf M/R/N: 72 clusters / 216 injections; LOCO macro-F1/top-1 = 1.0; post-hoc ablation: full vector 1.0, direct 3-leaf codebook 1.0, non-direct-only 0.3333 (tie 0.6667), any-response scalar 0.0. 8 of 12 checkpoint columns are identically zero; `parse.table.regression` and `parse.field.hit_rate` are byte-identical aliases (same predicate written twice); an MVP design audit filed this as a HIGH incident and single blocker.
  - E4: mechanism generalization audit: every stage has exactly 1 frozen mechanism; `train_on_one_mechanism_test_on_another = NOT_IDENTIFIED`; minimum required per stage = 2.
  - E5: OCR strength gradient (post-hoc): edit-distance-2 duplication visible 8/8; distance-1 absorbed 5/5.
  - E6: multi-leaf harness reruns in ~53 s end-to-end on GB10, zero endpoints; any config change requires a new namespace + fresh freeze/audit. Ancestor-node scores for the frozen 12-leaf tree can be derived from frozen leaf scores by the frozen aggregation code (no new runs).
  - E7: missing evidence is currently encoded as 0 and counted separately; `missing_score` is 0 for parse leaves and 5 for qa leaves; a design audit filed this asymmetry as a MED incident ("non-identifiable would score perfect marks").
  - E8: QA-layer silent normalization (n=12 record): the model can rewrite a mutated token back to canonical at the QA layer, making the defect invisible at that layer.

## Draft candidates (8)

### PR-01 Clean-support null-mutation panel
- Problem (FACT): clean-only matched-FPR blocked by zero clean support; equality not identifiable.
- Repair: preregistered null-mutation panel (semantics-preserving edits the canonicalizer maps to identity); re-run the same identifiability analysis with nonzero clean support.
- Causal rationale: null edits give clean-side score variation, making clean FPR observable across thresholds, so the matched operating point becomes decidable (or provably still not).
- Held-out: calibrate on one table-cluster half; re-test identifiability on held-out clusters; families separate.
- Primary metric: clean-side positive support > 0 + identifiability decision; paired TPR difference at matched FPR with CI where identifiable.
- Cost: LOW (deterministic, zero model). Duration: ~1 day.
- Tautology concern: must ensure null edits are semantics-preserving and frozen before harmful-side inspection; support may legitimately stay 0 (NULL publishable).

### PR-02 Observation placement / alignment re-observation
- Problem (FACT): localization exists only at directly instrumented leaves; non-direct collapses to chance; propagation depth / first-visible distance unexecuted.
- Repair: freeze placement rule set (parent / grandparent / sibling sets / non-direct subset of each responsive leaf); derive node scores via frozen aggregation from the frozen 216x12 carriers; re-run frozen nearest-centroid discrimination per placement under LOCO.
- Causal rationale: signal persists while the responsive leaf's weighted fraction keeps class separation; the curve quantifies decay of diagnosability with source->observation distance.
- Held-out: LOCO clusters; rules frozen before results.
- Primary metric: macro-F1 / top-1 vs placement; decay curve; ties.
- Cost: LOW (hours; seconds compute). Duration: ~1 day.
- Tautology concern: decay is expected; require pre-declared falsification thresholds; probe "definitional dilution".

### PR-03 M-stage oracle de-alias
- Problem (FACT): two M-stage leaves are byte-identical aliases; the source-local/downstream partition is undefined; HIGH incident + single blocker in the MVP design audit.
- Repair: implement a genuine table-shape/header-order structural oracle for `parse.table.regression`, frozen before association tests; re-run frozen evaluation + ablation; report changed conclusions (expect M1 downstream remains non-estimable, correctly).
- Causal rationale: authentic structural measurement removes contamination; source/downstream partition becomes well-defined for future mechanisms.
- Held-out: LOCO + ablation codebook control.
- Primary metric: leaf independence (identical-column check -> 0), stage signature re-derivation, ablation status; explicit non-estimability accounting.
- Cost: LOW-MED. Duration: ~1 day.
- Tautology concern: LOW; oracle must be structural and frozen first.

### PR-04 Cross-mechanism transfer (one new mechanism)
- Problem (FACT): one mechanism per stage; cross-mechanism generalization NOT_IDENTIFIED; perfect result may be mechanism-bound.
- Repair: implement ONE additional deterministic mechanism for ONE stage (first choice N2: operator/coefficient perturbation; zero model); evaluate A->B and B->A transfer under frozen nearest-centroid with direct-codebook controls. If M, PR-03 is a prerequisite.
- Causal rationale: if a stage signature fit on mechanism-A rows predicts mechanism-B rows without directly targeting B, alignment is mechanism-general; otherwise fingerprint-bound.
- Held-out: mechanism-level split + cluster LOCO, both frozen.
- Primary metric: cross-mechanism macro-F1 / top-1 per direction vs chance/majority/direct baselines.
- Cost: MED. Duration: 1-2 days.
- Tautology concern: extraction frozen before B rows observed; direct-codebook control mandatory; probe "trivially shared leaf".

### PR-05 Blind-family boundary replication
- Problem (FACT): OCR 0/13 blind at all thresholds; strength gradient post-hoc (distance-2 visible 8/8; distance-1 absorbed 5/5); only one blind family.
- Repair: freeze a 3-bin OCR-adjacent strength ladder + one additional expected-blind control family (e.g., internal-whitespace OOV); generate on fresh held-out clusters; preregister per-bin visibility predictions; run frozen quantify pipeline.
- Causal rationale: absorption boundary = mapping-loss boundary (generic effect), not family-specific; currently untested out-of-sample.
- Held-out: new clusters; predictions frozen before outcomes.
- Primary metric: monotonicity across strength bins; control-family rate.
- Cost: LOW-MED (generator reuse; zero model). Duration: ~1 day.
- Tautology concern: "monotone by construction" must be falsifiable; bins and failure conditions preregistered.

### PR-06 Minimal-leaf pruning at equal diagnosability (cost axis)
- Problem (FACT): 8/12 leaves never respond; direct 3-leaf codebook already 1.0; cost axis unquantified.
- Repair: freeze label-blind pruning rule (train-split variance > 0 AND MI > epsilon; stage-aligned manual baseline as control); evaluate preserved diagnosability on LOCO held-out; report cost ledger (leaf checks / judge calls saved).
- Causal rationale: zero-information observations cannot reduce held-out decision power if the rule is honest; claim is cost-side.
- Held-out: LOCO; prune rule frozen on train folds only.
- Primary metric: non-inferiority of macro-F1 / top-1; cost delta.
- Cost: LOW. Duration: ~0.5-1 day.
- Tautology concern: close to the existing ablation; must stay strictly cost-side.

### PR-07 Label-blind re-extraction bridge
- Problem (FACT): v1 features are contract-derived; the surviving reviewer attack is exactly this; v2 delta requires label-blind extraction and sets a NULL rule (report NULL if full vector <= direct codebook).
- Repair: new namespace; extractor reads only paired raw outputs (no stage/mutation labels); rerun discrimination + ablation on the 216 carriers; explicitly non-confirmatory sensitivity run.
- Causal rationale: removing label leakage from feature construction measures actual observation dynamics rather than injection labels.
- Held-out: LOCO; delta requirement.
- Primary metric: label-blind macro-F1 vs strongest codebook baseline; NULL rule per delta.
- Cost: MED-LOW. Duration: 1-2 days.
- Tautology concern: same corpus; non-confirmatory by design; extractor must be provably label-blind.

### PR-08 Tri-state missing-evidence cells
- Problem (FACT): missing evidence encoded as 0 + counted; not exercised by fixtures; `missing_score` asymmetry (parse 0 / qa 5) inverts non-identifiability; MED incident filed.
- Repair: recompute a bounded outcome table in tri-state {response / no-response / no-evidence} from frozen inputs + build no-evidence fixtures; contract tests; report decision flips vs current policy.
- Causal rationale: zero-conflation vs unknown is a policy choice with measurable consequences; repair makes it explicit.
- Held-out: contract fixtures + cluster-split sensitivity.
- Primary metric: flip rate of visibility/detection cells under policy; identification status.
- Cost: LOW-MED. Duration: ~1 day.
- Tautology concern: LOW.

## Challenge questions — answer ALL 8 for EACH candidate (verbatim from the owner, with English digest)

1. 这个 repair 的 improvement 是否由定义保证？ / Is the improvement guaranteed by definition?
2. 是否真正改变了 observability，而非标签？ / Does it change observability rather than labels?
3. held-out 是否独立？ / Is the held-out evaluation independent?
4. baseline 是否公平？ / Is the baseline fair?
5. cost 是否公平？ / Is the cost accounted fairly?
6. 是否是 source-local direct response？ / Is it merely a source-local direct response?
7. measurement object 前后是否可比较？ / Are the before/after measurement objects comparable?
8. NULL 是否仍有解释价值？ / Does NULL remain informative?

## Required output format (machine-parseable)

For each candidate, exactly:

## CANDIDATE PR-0X
- Q1: <one line>
- Q2: <one line>
- Q3: <one line>
- Q4: <one line>
- Q5: <one line>
- Q6: <one line>
- Q7: <one line>
- Q8: <one line>
- VERDICT: KEEP | REVISE | FAIL
- MINIMAL_MODIFICATION: <required only if REVISE; else "none">
- BLOCKING_REASON: <required only if FAIL; else "none">

Then:

## RANKING
1) PR-0X ... 5) PR-0X (recommended first-round top 5, with one-line reasons)

## STRONGEST_OBJECTION
<the single most dangerous cross-candidate objection, and which candidate it most threatens>

## NOTES
<any UNVERIFIED items, packet gaps, or replacement suggestions>

End with the literal line: `CHALLENGE_COMPLETE`