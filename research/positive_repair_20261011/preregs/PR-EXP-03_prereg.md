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