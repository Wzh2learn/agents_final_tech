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