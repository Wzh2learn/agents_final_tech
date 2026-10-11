# Prereg — PR-EXP-03: M-stage structural-oracle coverage repair (de-alias)

> version: v2 (revision 1; closes audit-v1 conditions a-e) | experiment_id: PR-EXP-03 | candidate: PR-03 | role: INTERVENTION_REPAIR
> frozen: 2026-10-11 | authority: Human decision 2026-10-11 (first wave); execution requires Loop C pre-result verdict PASS
> shared artifacts pinned in research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json

## 1. Hypothesis
A table-structure oracle defined from table/schema semantics and frozen before any topology-outcome observation recovers held-out structural failures that the existing field-hit-derived oracle misses, at comparable measurement cost, without constant-1-style or duplicate-catch artifacts.

## 2. Owner-fixed criteria (2026-10-11 human decision, section 3)
Primary question: held-out structural failures recovered where the existing oracle misses, comparable cost. Oracle from table/schema/execution semantics; no mutation labels; no held-out outcome; frozen before any M2-type result observation; held-out topology failures independent; old vs repaired oracle on the same population. Primary metrics: (1) held-out failure coverage delta; (2) stage/family diagnosability delta. Improvement only from SOURCE_LOCAL_RESPONSE -> not a repair positive. Merely-different oracle with no held-out diagnostic gain -> NULL.

## 3. Population
- P1 held-out topology failure set: deterministic adjacent-column transposition failures over held-out table UIDs. Selection rule (verbatim; pinned in the implementation contract): UIDs = ascending SHA-256(seed=20261011:namespace="pr03-topology":uid) over the frozen drift corpus table set (membership pinned by source-file hash + UID list hash); EXCLUSION REGISTRY = M-stage UIDs and N-stage UIDs extracted from research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json (extraction command recorded verbatim); exactly one adjacent column pair transposed per selected table, pair index by frozen per-table hash rule; values and row counts preserved; generator double-run byte-identical required.
- Ground truth for P1: stage_label="M", family_label="topology_transposition".
- P2 control: frozen 216-row carriers — untouched; only for the regression check; never for primary metrics.
- P3 M1 regression set: held-out M1-style cases (frozen selection rule).

## 4. Intervention and arms (frozen before P1 generation)
Structural oracle v2 at parse.table.regression: response = int(structural_signature(baseline) != structural_signature(injected)); structural_signature = (column_count, ordered positional header-token sequence under the pinned canonicalizer, row_count). No mutation labels; no held-out outcomes; fail-closed: undefined artifacts -> NOT_EVALUABLE cell.
Freeze order: (1) oracle implementation hash + verbatim rules; (2) P1 generation; (3) evaluation. No edits after P1 observation.
Arms (same frozen response rule): A0 no-op/identity (structural oracle must return 0 on every case); A1 value-only specificity (cell-value changes, structure preserved; must return 0); A2 P1 (expected 1); A3 frozen-carrier regression (M1 subset; expected 0).
Baseline oracles on the same population: (a) v1 aliased implementation (verbatim two-line extract from run_multileaf_formal.py:256-258 + file hash), (b) standalone field-hit oracle; unchanged.
Constant-1 control: documented that a constant-1 rule attains coverage=1 on P1 but fails A0/A1; POSITIVE therefore requires A0/A1 pass.

## 5. Metrics
Primary: (1) held-out failure coverage delta = coverage(new) − coverage(old) on P1 (raw numerators/denominators; cluster bootstrap CI over table UIDs, frozen seed); (2) stage/family diagnosability delta on the mixed held-out population = P1 ∪ frozen-rule subsample of carriers; macro-F1 via frozen nearest-centroid, LOCO over groups (table/document clusters, no source overlap); conclusion-level deltas only.
Secondary: disagreement rate; incremental unique catches; check-cost (§6); M1 regression; A0/A1 false-positive counts.
Attribution audit (operational; per contracts/SOURCE_LOCAL_RESPONSE_v1.md): pass = unique new catches AND A0/A1 clean AND constant-1 documented failure.

## 6. Cost and cost tolerance (defined)
Zero model/judge calls. Both oracles produce exactly 1 leaf response per case: check-count equality is the frozen cost tolerance (exact equality; no runtime-based claim). Freeze/audit overhead recorded in the cost ledger.

## 7. Outcome taxonomy (complete)
- POSITIVE: Δcov > 0 with CI lower > 0 AND Δdiag >= −0.02 (frozen materiality margin) AND A0/A1 pass AND no M1 regression AND attribution pass.
- DIAG_ONLY: Δcov <= 0 or CI includes 0, but Δdiag > +0.02 -> recorded as NULL with diag gain noted; NOT a repair positive.
- NULL: no material gain and no material loss (coverage nonpositive or CI includes 0; |Δdiag| <= 0.02).
- NEGATIVE: Δdiag < −0.02 (regardless of coverage).
- INVALID: sanity-gate failure, label access, post-freeze edits, UID overlap, cost inequivalence.
- NOT_EVALUABLE: P1 not executable/visible, or oracle semantics undefined on held-out artifacts. Never merged into NULL.
Sanity gate (defined): the structural column must differ from the field-hit column on >=1 held-out P1 case AND must not be a monotone function of field-hit on the frozen 216 rows; failure = INVALID (implementation defect), not a scientific outcome.

## 8. Implementation contract requirement
Before execution, Loop A materializes runs/PR-EXP-03/implementation_contract.md containing verbatim: drift-corpus membership rule (source path + sha256 + UID list hash), UID exclusion registry (extracted list + extraction command), pair-selection hash rule, oracle v2 source hash, baseline extract hashes, arm definitions, bootstrap seed, shared-surface hash check results. Missing items -> INPUT_MISSING stop.

## 9. Stop conditions
Any requirement violation; no threshold/oracle hunting; any scope change -> new prereg + re-audit. If any audit-v1 condition cannot be satisfied within this revision -> STOP_BRANCH.