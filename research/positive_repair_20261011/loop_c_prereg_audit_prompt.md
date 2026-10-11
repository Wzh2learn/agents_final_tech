# Loop C Pre-Result Design Audit — Track P First-Wave Preregs (PR-EXP-03 / PR-EXP-01 / PR-EXP-04 / PR-EXP-07)

You are the independent Loop C auditor. This is a DESIGN-STAGE, read-only pre-result audit of four frozen experiment preregs, BEFORE any Loop A execution.

Scope and rules:
- You receive this packet only. No tools, no file reads, no network, no model calls, no edits. Report only.
- Authorized purpose: per-experiment verdicts that gate execution. This is NOT an experiment and NOT a result.
- Judge only from this packet; missing evidence -> UNVERIFIED.
- Labels: FACT / INFERENCE / UNVERIFIED where useful.

## Context: the decision this audit gates (from the 2026-10-11 human decision)
- Track P roles: INTERVENTION_REPAIR (counts toward the >=3 synthesis gate) / GENERALIZATION_TEST / ROBUSTNESS_ANTI_TAUTOLOGY / BOUNDARY_REPLICATION (all supporting-only).
- First wave (this audit): PR-EXP-03 (INTERVENTION_REPAIR), PR-EXP-01 (INTERVENTION_REPAIR), PR-EXP-04 (GENERALIZATION_TEST), PR-EXP-07 (ROBUSTNESS_ANTI_TAUTOLOGY).
- Decision function: For each experiment, return exactly PASS | CONDITIONAL | FAIL.
  - PASS: Loop D may dispatch Loop A execution WITHOUT further user approval, provided the scientific scope is unchanged.
  - CONDITIONAL: Loop D may revise ONLY the prereg / implementation contract (one revision), then at most ONE re-audit. If still not PASS -> STOP_BRANCH for that experiment.
  - FAIL: STOP_BRANCH for that experiment.
- If the only path to PASS would change the scientific scope of the human-approved prompt, mark FAIL with SCOPE_CHANGE: YES; Loop D must NOT auto-apply scope changes.
- Anti-cherry-picking: failures are kept in the registry; NOT_EVALUABLE must never be merged into NULL.

## Preregs under audit (verbatim; frozen 2026-10-11)

### Prefix note (metadata; not part of prereg text)
- PR-EXP-03 prereg sha256: 4430f2db951b73453dee6f64ea8edbee25f0cf2b3b8d676d019539f2edc1ea51
- PR-EXP-01 prereg sha256: 5685794fe0253bc559e97f189ab722c365d81aa1a906a507b83f7b541bf8e371
- PR-EXP-04 prereg sha256: f387877654e0e045df1c1a4d440121f231ade49e6c1324787a1e77ac068eae3b
- PR-EXP-07 prereg sha256: 70eaa6d9515a85d2c1d3869434d6d838fdb467cc540f8d73d0da60d25691568e

--- BEGIN PR-EXP-03 ---

# Prereg — PR-EXP-03: M-stage structural-oracle coverage repair (de-alias)

> experiment_id: PR-EXP-03 | candidate: PR-03 | role: INTERVENTION_REPAIR
> frozen: 2026-10-11 (Loop D) | authority: Human decision 2026-10-11 (first wave); execution requires Loop C pre-result verdict PASS
> scope: repair the filed HIGH incident `aliased-checkpoint-pair-labelled-as-distinct-oracles` by replacing the field-hit copy at `parse.table.regression` with a genuine structural oracle, and test it on held-out structural (topology) failures.

## 1. Hypothesis
A table-structure oracle defined from table/schema semantics and frozen before any topology-outcome observation recovers held-out structural failures that the existing field-hit-derived oracle misses, at comparable measurement cost, and does not owe any gain to SOURCE_LOCAL_RESPONSE.

## 2. Owner-fixed criteria (2026-10-11 human decision, section 3)
- Primary question: held-out structural failures recovered where the existing oracle misses, with comparable cost.
- Oracle defined from table/schema/execution semantics; must NOT read mutation labels; must NOT read held-out outcome; frozen before any M2-type result observation; held-out topology failures independent; old and repaired oracle compared on the same population.
- Primary metrics: (1) held-out failure coverage delta; (2) stage/family diagnosability delta.
- Improvement only from SOURCE_LOCAL_RESPONSE -> not a repair positive. Oracle merely different but no held-out diagnostic gain -> NULL.

## 3. Population
- P1 held-out topology failure set: deterministic adjacent-column transposition failures over held-out table UIDs. Selection rule (frozen): UIDs = ascending SHA-256(seed=20261011:namespace="pr03-topology":uid) over candidate tables in the frozen drift corpus; exclusion = UIDs used by any prior Stage E/M-stage experiment (disjointness recorded); exactly one adjacent column pair transposed per table, pair chosen by frozen per-table hash rule; values and row counts preserved; generator double-run byte-identical required.
- P2 control: existing frozen 216-row M/R/N carriers — untouched; used only for the M1-regression secondary check; never for primary metrics.
- P3 M1 regression set: held-out subset of existing M1-style failure cases (frozen selection rule) for no-regression.

## 4. Intervention (frozen before P1 generation)
Structural oracle v2 at `parse.table.regression`: response = int(structural_signature(baseline) != structural_signature(injected)), where structural_signature = (column_count, ordered positional header-token sequence under frozen canonicalization, row_count). Defined from schema/table semantics; no mutation labels; no held-out outcomes; fail-closed: undefined artifacts -> NOT_EVALUABLE cell (never guessed).
- Freeze order: oracle definition + implementation hash first; then P1 generated; then evaluated. No edits after P1 observation.
- Baseline oracles on the same population: (a) existing aliased implementation (v1 copy), (b) standalone field-hit oracle; both unchanged.

## 5. Metrics
Primary:
1. held-out failure coverage delta = coverage(new) − coverage(old) on P1; coverage = fraction of transposition cases with response=1 under the frozen response rule; raw numerators/denominators; cluster-level bootstrap CI over table UIDs (frozen seed).
2. stage/family diagnosability delta: macro-F1 (frozen nearest-centroid, LOCO over held-out groups) with corrected vs aliased configuration on P1; conclusion-level deltas only (before/after F1 never reported as one combined number).
Secondary: disagreement rate; incremental unique catches; observation/check-cost delta (same check-count budget class); M1 regression check (response preserved on P3).
Attribution audit (mandatory): any gain must be shown not to be attributable to SOURCE_LOCAL_RESPONSE only.

## 6. Cost
Zero model/judge calls; deterministic; expected GB10 minutes; freeze/audit overhead included in the cost ledger.

## 7. Success / NULL / INVALID / NOT_EVALUABLE / Stop
- POSITIVE: coverage delta > 0 (bootstrap lower bound > 0) AND diagnosability delta >= 0 AND no M1 regression AND not source-local-only.
- NULL: oracle differs (sanity gate passes) but no held-out coverage gain and no diagnosability gain.
- INVALID: label access; outcome-peeking; post-freeze edits; UID overlap with prior populations; cost inequivalence.
- NOT_EVALUABLE: P1 not executable/visible on the frozen surface, or oracle semantics undefined on held-out artifacts. Never merged into NULL.
- STOP: any requirement violation; no threshold/oracle hunting; any scope change -> new prereg + re-audit.

--- END PR-EXP-03 ---

--- BEGIN PR-EXP-01 ---

# Prereg — PR-EXP-01: SYNTHETIC_NULL_SUPPORT_REPAIR

> experiment_id: PR-EXP-01 | candidate: PR-01 | role: INTERVENTION_REPAIR
> claim object: SYNTHETIC_NULL_SUPPORT_REPAIR — never "empirical clean-only matched-FPR repair"
> frozen: 2026-10-11 (Loop D) | authority: Human decision 2026-10-11; execution requires Loop C pre-result PASS and the null-semantics qualification below

## 1. Background (facts)
- Clean-only matched-FPR operating point is NOT_IDENTIFIABLE; 2,382 clean rows carry contrastive support exactly {0}; the frozen reanalysis doc names the remedy: nonzero clean support via a preregistered null-mutation panel.

## 2. Null-semantics qualification (fail-closed precondition)
- Null-mutation class (deterministic candidates): cell-text edge whitespace; internal single-space normalization; case/format variants ONLY if the frozen canonicalizer is verifiably identity on them. Generator emits edits + claimed identity mapping; generated without reading harmful outcomes.
- Independent verification: a checker implemented independently of the generator re-runs frozen canonicalization + downstream pipeline and requires bit-identical downstream artifacts (hash equality) vs original; only admitted edits enter the panel. Admission list + edit DSL + generator/checker hashes frozen BEFORE scoring.
- If the admission set is empty or identity cannot be independently verified -> STOP; report NOT_EVALUABLE; no scoring, no claim.

## 3. Populations and split
- Calibration nulls: admitted edits on calibration folds (frozen 5-fold table-UID rule inherited from the matched-FPR reanalysis namespace).
- Held-out nulls: disjoint folds.
- Harmful pairs: frozen 111 harmful pairs; NEVER used for threshold selection; may be read only AFTER the operating point is frozen.

## 4. Threshold selection (owner-fixed)
- Threshold selected SOLELY from calibration null scores (frozen rule, alpha=0.05); frozen by hash before any harmful-side read.

## 5. Primary qualification and positive rule
- calibration null support > single point;
- threshold solely from calibration nulls;
- held-out null FPR <= alpha;
- THEN held-out harmful TPR at the frozen operating point (+ paired cluster bootstrap CI).
- POSITIVE = operating point becomes identifiable AND held-out null FPR contract satisfied.

## 6. NULL / NOT_IDENTIFIABLE
- If the synthetic-null distribution cannot support held-out calibration (support remains single-point, or the FPR contract is unmeetable) -> NULL / NOT_IDENTIFIABLE.

## 7. Reporting boundary
- Report the original 2,382-row identifiability result separately; never silently replace E2's population. All conclusions phrased as SYNTHETIC_NULL_SUPPORT_REPAIR.

## 8. Cost / INVALID / Stop
- Zero model calls; deterministic; calibration + held-out runs in minutes.
- INVALID: harmful-side involvement in selection; any post-freeze edit; relabeling as empirical clean-only repair.
- STOP: qualification failure or unverifiable identity; else proceed.

--- END PR-EXP-01 ---

--- BEGIN PR-EXP-04 ---

# Prereg — PR-EXP-04: Cross-mechanism generalization (N1 vs N2)

> experiment_id: PR-EXP-04 | candidate: PR-04 | role: GENERALIZATION_TEST (supporting evidence only; does NOT count toward the repair count)
> frozen: 2026-10-11 (Loop D) | authority: Human decision 2026-10-11 (first wave); execution requires Loop C pre-result verdict PASS

## 1. Hypothesis
The frozen stage-aligned signature for stage N generalizes across genuine mutation mechanisms: N1 operand-value perturbation vs N2 operator/coefficient perturbation. This tests whether instrumentation captures stage information beyond a single mutation fingerprint.

## 2. N2 requirements (all mandatory; else MECHANISM_NOT_EVALUABLE)
- genuine different mechanism (operator/coefficient/sign semantics change; not a string/parameter variant);
- deterministic;
- executor-owned downstream consequence (relation recomputed through the frozen reconciliation path);
- preregistered before any N2 result (this file);
- visibility/evaluability minimum gate: >= 2/3 of generated N2 injections produce >= 1 measurable response on the frozen 12-leaf surface under the frozen response rule, AND >= 6 distinct held-out groups show response. Otherwise: MECHANISM_NOT_EVALUABLE (never counted as a generalization failure).
- N2 selection rationale (owner + Loop C condition): chosen for determinism and executor ownership, NOT for expected performance.

## 3. Population and split
- N1 rows: existing frozen N-stage carriers (unchanged).
- N2 rows: new deterministic N2 injections on held-out groups; generation rule frozen; UIDs disjoint from N1 groups; double-run byte-identical required.
- mechanism-disjoint + group-disjoint; directions N1->N2 and N2->N1 (fit on one mechanism's groups; evaluate on the other's).

## 4. Design
Frozen nearest-centroid (tie=failure), LOCO on held-out groups; direct-codebook control mandatory; responsive-leaf-set overlap report A vs B mandatory; extraction frozen before N2 rows observed; no feature edits after observation.

## 5. Primary metric
macro-F1 / stage identification per direction vs frozen chance/majority/direct baselines; cluster bootstrap CIs.

## 6. Success / NULL / NOT_EVALUABLE / INVALID / Stop
- POSITIVE (supporting): both directions non-negative vs chance, at least one direction strictly above chance/majority with CI excluding chance; direct-codebook control reported; overlap report attached.
- NULL: collapse toward chance -> fingerprint-bound result; documented; bounds the flagship claim. Never merged with NOT_EVALUABLE.
- NOT_EVALUABLE: N2 fails the visibility/evaluability gate -> MECHANISM_NOT_EVALUABLE.
- INVALID: leakage between mechanism sets; post-hoc tuning; prereg deviations.
- STOP: any requirement violation; no tuning to recover transfer.

--- END PR-EXP-04 ---

--- BEGIN PR-EXP-07 ---

# Prereg — PR-EXP-07: Label-blind re-extraction (anti-tautology robustness)

> experiment_id: PR-EXP-07 | candidate: PR-07 | role: ROBUSTNESS_ANTI_TAUTOLOGY (supporting evidence only; NOT a repair count)
> frozen: 2026-10-11 (Loop D) | authority: Human decision 2026-10-11 (first wave); execution requires Loop C pre-result verdict PASS
> Objective: re-test the multi-leaf result after removing every possible label / contract-construction information channel. NOT a new positive method.

## 1. Extractor blindness contract (must be provably enforced)
Extractor inputs ONLY: the unordered pair {A,B} of paired raw observation states. Blind pairing: pair order randomized by frozen seed; features computed as order-invariant (symmetric) functions; swap-invariance test required across all rows (feature(P) == feature(swap(P))).
Forbidden knowledge (structurally impossible to access): mutation family label; stage label; expected first stage; target checkpoint identity; gold outcome; sample namespace; generation code.

## 2. Frozen feature sets
- full label-blind feature set;
- direct-codebook subset (control);
- non-direct subset;
- NULL rule: full <= direct -> NULL.

## 3. Primary
macro-F1 / top-1 of stage decoding under frozen nearest-centroid + LOCO vs direct-codebook baseline vs chance.

## 4. Interpretation (owner-fixed)
- If label-blind full remains clearly above non-direct/chance -> robust supporting evidence.
- If it degrades -> retain the NULL/negative result AND correspondingly lower the original multi-leaf claim (recorded explicitly, never silent).

## 5. No-rescue rule
Extractor frozen by hash before evaluation; no post-hoc tuning; any edit -> new prereg.

## 6. Cost / INVALID / Stop
Zero model calls; deterministic; minutes of GB10 compute.
INVALID: any leakage channel found usable; swap-invariance or blind-pairing proof fails.
STOP: proof failure; else proceed.

--- END PR-EXP-07 ---

## Audit questions (answer ALL 10 for EACH experiment, one line each)
1. Is any improvement guaranteed by definition (or achievable only via definitional construction)?
2. Does the design change observability rather than labels / task truth?
3. Is the held-out set independent and correctly partitioned (leakage, UID overlap, freeze order)?
4. Are baselines fair and complete for this experiment type?
5. Is cost accounted fairly; is a same-budget comparison possible?
6. Can a source-local-only gain be ruled out (or, for PR-04/07, is source-locality handled in the right direction)?
7. Are before/after measurement objects comparable, with non-comparabilities correctly declared?
8. Is NULL / NOT_EVALUABLE informative and correctly separated?
9. Does anything change the scientific scope relative to the human-approved prompt? (also set SCOPE_CHANGE)
10. Are any mandatory conditions missing from the prereg? (list precisely)

## Required output format (machine-parseable)

## PR-EXP-03
- Q1: ...
- Q2: ...
- Q3: ...
- Q4: ...
- Q5: ...
- Q6: ...
- Q7: ...
- Q8: ...
- Q9: ...
- Q10: ...
- VERDICT: PASS | CONDITIONAL | FAIL
- CONDITIONS: <only if CONDITIONAL; must be limited to prereg/implementation-contract revisions>
- SCOPE_CHANGE: NO | YES (<one-line description>)

(repeat identically for PR-EXP-01, PR-EXP-04, PR-EXP-07)

## GLOBAL
- <cross-experiment notes: contradictions, circularity, ordering constraints, any UNVERIFIED items>

End with the literal line: `PREREG_AUDIT_COMPLETE`