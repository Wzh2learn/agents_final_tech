# Track P Round 1 Closeout v1 (first-wave Positive Repair Sprint)

> date: 2026-10-11 | status: CLOSED_NO_GENUINE_REPAIR_POSITIVE | no synthesis triggered | no new experiments
> pipeline: r3 collected -> 4 independent Loop C post-result audits bound -> unified report

## 1. Experiment roles
PR-EXP-03 / PR-EXP-01 = INTERVENTION_REPAIR; PR-EXP-04 = GENERALIZATION_TEST (supporting-only); PR-EXP-07 = ROBUSTNESS_ANTI_TAUTOLOGY (supporting-only).

## 2. Prereg hashes (v2, frozen)
PR-EXP-03 f3398a329a12ef23e528eb41d0bd90c8b4c5cee807c3d2c76c5afd0ac753f250 | PR-EXP-01 41c6c3cd14b5d0dd1e00abef9bd15953ba9bf1cb1d8463910270f67b94af0cd3 | PR-EXP-04 c28574b19748ff6cb626cd484af4c08256aa6b449fe9f8a8d1db6aa89a76b038 | PR-EXP-07 4724e53ebaf86633384f1955e5182bd7c5b886994603b59a6146c45ce6426d5f

## 3. Loop A results
- PR-EXP-01: NOT_EVALUABLE (Phase 0 fail-closed; independent checker returned unverifiable_identity; harmful side never read; 9,566 admitted / 37,900 candidate applications; zero model calls).
- PR-EXP-03: INVALID (frozen sanity gate: carrier non-monotonicity clause failed + 2 undefined baseline field-hit cells on all-empty-header tables; complete-case descriptive 1973/2431 new vs 0/2429 baseline; zero model calls).
- PR-EXP-04: INVALID (frozen-implementation KeyError 'group_uid' after generation + gates, before metric evaluation; no post-generation edits; zero model calls).
- PR-EXP-07: NOT_EVALUABLE (contract-pinned label-provenance field expected_first_affected_stage absent; carrier exposes expected_first_stage; 216/216 excluded; blindness proofs PASS; zero model calls).
- All four: zero frozen-artifact edits; all fail-closed correctly. a1 (INPUT_MISSING x4) and a2 (HASH_MISMATCH x4) remain ENGINEERING_DISPATCH_FAILURE, excluded from scientific classes.

## 4. Loop C independent verdicts (fresh context, packet-only)
- PR-EXP-01: ENDORSE_WITH_NOTES (NOT_EVALUABLE correct; Phase 0 FAIL trigger contradicted by all reported passing sub-checks -> suspected checker/contract defect; scientifically empty; no gate credit).
- PR-EXP-03: CHALLENGE_CLASS -> recommended registry class NOT_EVALUABLE (registered INVALID kept as gate-provenance annotation; the sanity-gate clause is unsatisfiable-by-construction on structurally-null carriers and contradicts the A3 expected-0 arm; the 2 undefined cells independently block primary metrics; complete-case contrast NON-ADMISSIBLE).
- PR-EXP-04: ENDORSE_WITH_NOTES (INVALID correct; MECHANISM_NOT_EVALUABLE wrong; HIGH provenance finding: delivered result/receipt not attributable to the frozen runner; degenerate one-hot measurement surface; estimand insensitive to the hypothesis under shared M/R anchors).
- PR-EXP-07: ENDORSE_WITH_NOTES (NOT_EVALUABLE correct; root cause = Loop D contract pin; proof-PASS is not ROBUST; claim neither raised nor lowered).

## 5. Effect size / CI
None computed anywhere (no scored effect). Only descriptive complete-case numbers exist (PR-EXP-03) and are quarantined. Audit recomputation: PR-EXP-01 partition arithmetic closed exactly; PR-EXP-03 rates and Wilson intervals reproduced (bootstrap not recomputable packet-only); PR-EXP-04 control values reproduced but are definitionally true; PR-EXP-07 nothing to recompute.

## 6. Result classes
NOT_EVALUABLE x2 (01, 07) + NOT_EVALUABLE recommended (03; registered INVALID) + INVALID x1 (04). Zero POSITIVE / NULL / NEGATIVE. Engineering failures excluded.

## 7. Genuine repair positive?
None. genuine_repair_positive=false for all four; counted_toward_synthesis_gate=0.

## 8. Support for existing multi-leaf / observation claims?
No change. PR-EXP-07 robustness remains UNTESTED (correctly no claim-lowering note). PR-EXP-03 supplies no admissible support. The flagship multi-leaf claim is neither strengthened nor weakened by this wave.

## 9. Shared-principle hypothesis?
Neither supported nor refuted: no positive repair exists to test it. INFERENCE seed ("the object was never made well-defined; results inherit the object defect") was instantiated by the wave itself: all four stops trace to definition/provenance defects, not to scientific findings.

## 10. Replication needed?
For outcomes, N/A (no effect measured). Recovery = corrected re-runs (v3), each under a NEW prereg + pre-result audit; not authorized in this round.

## 11. Include in SANER Route A?
No. 01/03/04 = decline-cite; 07 = bound (at most a one-line preregistration-accounting sentence).

## 12. Evidence ladder (current highest)
LEVEL_0 (audit findings only). No LEVEL_1+ claim is supported.

## 13. Track A progress
- Item 1 (Figure 1/2/3 source binding): COMPLETE. docs/research/figures_saner/ (fig1 svg; fig2 svg+png+csv; fig3 svg+png; figure_source_binding_manifest.json; receipt): 10 verification checks PASS, 30 Fig-2 cells recomputed from t2, 98 numeric bindings, captions exact, forbidden phrases absent, no clipping; frozen sources/manuscript untouched.
- Item 2 (reviewer-attack claim audit): COMPLETE. Loop C verdict CHALLENGE_CLAIM_SET. Critical: F1 claim matrix not parseable JSON + incomplete hash coverage (autopsy unhashed); F2 contribution-3 wording above evidence and contradicting the draft body; F3 FinQA causal "because" + undefined vocabulary; F4 machine-readable forbidden list weaker than human list; F5 "blindness" deficit framing; F6 statistical reporting arithmetic issues; 14-item forbidden-language scan + TOP-5 reviewer attacks with pre-prepared responses; all fixes are wording/governance-only, no new experiments.
- Items 3-6: queued (title/abstract/contribution freeze awaits user review; related-work gap check; official NIST citation or drop; submission package checks).

## 14. Next-round highest ROI
1) Fix the four defect classes first (Loop D contract pins + gate definitions; Loop A schema assertion + writer provenance/attribution) - harness/contract quality is the bottleneck, not science.
2) Execute the reviewer-attack audit repairs in Track A before the 2026-10-20 freeze (claim-matrix JSON repair + hash coverage; contribution-3 rewording; one title; forbidden-list restoration; number-reporting detail).
3) Only then decide corrected re-runs (PR-EXP-03 v3 / PR-EXP-01 v3 / PR-EXP-04-R / PR-EXP-07 v3), each with new prereg + pre-result audit. No easy-experiment padding; no synthesis until the gate is actually met.