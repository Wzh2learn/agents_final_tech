# Prereg — PR-EXP-01: SYNTHETIC_NULL_SUPPORT_REPAIR

> version: v2 (revision 1; closes audit-v1 conditions a-e) | experiment_id: PR-EXP-01 | candidate: PR-01 | role: INTERVENTION_REPAIR
> claim object: SYNTHETIC_NULL_SUPPORT_REPAIR — never "empirical clean-only matched-FPR repair"
> frozen: 2026-10-11 | authority: Human decision 2026-10-11; execution requires Loop C pre-result PASS and the null-semantics qualification below

## 1. Background (facts)
Clean-only matched-FPR operating point NOT_IDENTIFIABLE; 2,382 clean rows carry contrastive support exactly {0}; the frozen reanalysis doc names the remedy: nonzero clean support via a preregistered null-mutation panel.

## 2. Null-semantics qualification (fail-closed; surfaces defined)
- Scored surface: the exact raw observation surface consumed by the frozen contrastive score computation — pinned verbatim in the implementation contract by reading the frozen scorer implementation (path + hash + exact input expression).
- Task-truth surface: downstream canonical artifacts (post-canonicalization pipeline outputs) — identity (hash equality) required.
- Admitted edits must be NON-identity on the scored surface AND hash-identical on the task-truth surface. If no edits satisfy both under the frozen edit DSL -> NOT_EVALUABLE (panel empty), never NULL.
- Generator/checker independence: checker must not import the generator module (AST import check); separate file-hash lineage recorded; checker re-runs canonicalization + downstream pipeline and requires downstream hash equality.
- Panel completeness: panel = the complete admitted set under the frozen rule; no sampling, no outcome-based selection.

## 3. Populations and split
- Calibration nulls: admitted edits on calibration folds (frozen 5-fold table-UID rule inherited from the matched-FPR reanalysis namespace; rule text pinned verbatim in the implementation contract).
- Held-out nulls: disjoint folds.
- Harmful pairs: frozen 111 harmful pairs; NEVER used for threshold selection; read only after the operating point is frozen.

## 4. Threshold rule (frozen, incl. ties)
Threshold = the smallest t such that fraction(calibration-null scores > t) <= alpha, alpha=0.05; strict greater-than comparison; ties handled by the frozen "smallest t" rule (all candidate t drawn from the calibration-null score support). Rule hash-frozen before any harmful-side read.

## 5. Primary qualification and positive rule
- calibration null support > single point;
- threshold solely from calibration nulls;
- held-out null FPR <= alpha;
- THEN held-out harmful TPR at the frozen operating point (+ paired cluster bootstrap CI).
- POSITIVE = operating point becomes identifiable AND held-out null FPR contract satisfied. Identifiability status recorded as a result ATTRIBUTE, not a label.

## 6. Outcome labels (canonical, single string per run)
- POSITIVE / NULL / NEGATIVE / INVALID / NOT_EVALUABLE (exactly one).
- NULL: substantive run failing support or FPR contract (informative: bounds the remedy). 
- NOT_EVALUABLE: empty admission set, unverifiable identity, or unpinnable scored surface; never merged into NULL.
- INVALID: harmful-side involvement in selection; any post-freeze edit; relabeling as empirical clean-only repair.

## 7. Reporting boundary and bridge report
- Report the original 2,382-row identifiability result separately; never silently replace E2's population. All conclusions phrased as SYNTHETIC_NULL_SUPPORT_REPAIR.
- Bridge report (required): empirical clean-row score distribution + their FPR at the frozen threshold, labeled explicitly as a non-comparable empirical-vs-synthetic read.

## 8. Cost
Zero model calls; deterministic; calibration + held-out runs in minutes; same-budget comparison = same procedure on both null partitions.

## 9. Stop conditions
Qualification failure or unverifiable identity -> STOP (NOT_EVALUABLE). If the scored surface cannot be pinned without changing the claim object -> STOP_BRANCH. No threshold hunting; any scope change -> new prereg + re-audit.