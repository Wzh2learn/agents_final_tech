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