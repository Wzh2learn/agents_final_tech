# Prereg — PR-EXP-04: Cross-mechanism generalization (N1 vs N2)

> version: v2 (revision 1; closes audit-v1 conditions a-e) | experiment_id: PR-EXP-04 | candidate: PR-04 | role: GENERALIZATION_TEST (supporting evidence only; does NOT count toward the repair count)
> frozen: 2026-10-11 | authority: Human decision 2026-10-11 (first wave); execution requires Loop C pre-result verdict PASS

## 1. Hypothesis
The frozen stage-aligned signature for stage N generalizes across genuine mutation mechanisms: N1 operand-value perturbation vs N2 operator/coefficient perturbation. Tests whether instrumentation captures stage information beyond a single mutation fingerprint.

## 2. N2 requirements (all mandatory; else MECHANISM_NOT_EVALUABLE)
- genuine different mechanism (operator/coefficient/sign semantics change; not a string/parameter variant);
- deterministic;
- executor-owned downstream consequence (relation recomputed through the frozen reconciliation path);
- preregistered before any N2 result (this file);
- visibility/evaluability minimum gate: >= 2/3 of generated N2 injections produce >= 1 measurable response on the frozen 12-leaf surface under the frozen response rule AND >= 6 distinct held-out groups show response. Otherwise: MECHANISM_NOT_EVALUABLE (never a generalization failure);
- N2 selection rationale: determinism and executor ownership, NOT expected performance.

## 3. Population, groups, and split
- N1 rows: existing frozen N-stage carriers (unchanged; descriptive gate attrition reported).
- N2 rows: new deterministic N2 injections on held-out groups; generation rule frozen; UIDs disjoint from N1 groups; double-run byte-identical.
- "Group" (defined): stage-namespaced cluster as in the frozen freeze receipt (N:<uid>); for N2, groups = held-out table UIDs.
- mechanism-disjoint + group-disjoint; directions N1->N2 and N2->N1 (fit on one mechanism's groups; evaluate on the other's).
- Declarations: N1 and N2 are different populations by design; the visibility gate conditions N2 (N1 is frozen with its own observed 72/72 visibility; attrition reported for both); method-development history on N1 carriers is recorded as making the N2->N1 direction potentially optimistic.

## 4. Design and controls
Frozen nearest-centroid (tie=failure), LOCO on held-out groups; direct-codebook control mandatory; responsive-leaf-set overlap report mandatory; extraction frozen before N2 rows observed; no feature edits after observation.
- Feature surface ban: features may only use the frozen 12-leaf response surface + frozen contract-check outputs; provenance/mechanism-identifier features are forbidden (pinned in the implementation contract).
- Harness-equivalence control (mandatory): regenerate N1 rows through the N2 harness code path; require byte-identical response vectors vs frozen N1 rows; failure -> INVALID (harness confound not separable).

## 5. Primary metric and frozen baselines
macro-F1 / stage identification per direction; frozen baselines (numeric): chance top-1 = 1/3; uniform-class macro-F1 = 1/3; majority macro-F1 = 1/6; direct-codebook references from the frozen ablation (full 1.0 / direct 1.0 / non-direct 0.3333). Cluster bootstrap CIs.

## 6. Cost (added)
Zero model/judge calls; GB10 minutes; same-budget comparison = identical procedure both directions; freeze/audit overhead in the cost ledger.

## 7. Outcome taxonomy (complete, numeric)
Materiality margin m=0.05.
- SUPPORTED (supporting): both directions point >= 1/3 AND >= 1 direction CI-low > 1/3 AND direct-codebook control reported AND overlap report attached.
- NULL (fingerprint-bound): all directions |point − 1/3| <= m, or CI includes 1/3 without meeting SUPPORTED criteria. Documented; bounds the flagship claim.
- NEGATIVE: any direction point < 1/3 − m.
- NOT_EVALUABLE: N2 fails the visibility/evaluability gate (MECHANISM_NOT_EVALUABLE), or insufficient groups for a CI. Never merged into NULL.
- INVALID: leakage between mechanism sets; harness-equivalence failure; post-hoc tuning; prereg deviations.

## 8. Stop conditions
Any requirement violation; no tuning to recover transfer. This experiment never counts toward the repair count.