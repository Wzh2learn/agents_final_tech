# Loop C Post-Result Independent Audit — PR-EXP-07 (ROBUSTNESS_ANTI_TAUTOLOGY)

You are the independent Loop C auditor. This is a POST-RESULT audit of one completed Track P experiment. Read-only, packet-only, report-only: no tools, no file reads, no network, no edits. Judge strictly from this packet; missing evidence -> UNVERIFIED. Do not modify, re-run, or rescue the result. Labels: FACT / INFERENCE / UNVERIFIED.

## Round context (disclosed facts)
- Track P first wave: PR-EXP-03 INTERVENTION_REPAIR / PR-EXP-01 INTERVENTION_REPAIR / PR-EXP-04 GENERALIZATION_TEST / PR-EXP-07 ROBUSTNESS_ANTI_TAUTOLOGY. Only INTERVENTION_REPAIR positives may ever count toward the synthesis gate.
- Registered class for PR-EXP-07: NOT_EVALUABLE.
- Disclosed incidents, NOT part of this experiment's scientific record: (i) two engineering dispatch layers (a1 INPUT_MISSING x4; a2 HASH_MISMATCH x4) were fail-closed infrastructure failures, zero scientific side effects, excluded from scientific classes; (ii) the prereg re-audit log lost its leading sections in capture (verdicts recovered from GLOBAL); (iii) the Loop D prereg/sanity-gate definitions may contain defects - examine critically.
- Registered NOT_EVALUABLE came from a contract pin defect: the frozen implementation contract required the paired-carrier field expected_first_affected_stage, but the frozen carrier schema exposes expected_first_stage; no unauthorized fallback was applied; 216/216 rows excluded and no scoring occurred. Blindness proofs PASS (swap-invariance 216/216, pairing PASS, leakage PASS, forbidden fields never accessed). Judge whether NOT_EVALUABLE is correct, attribute the root cause (Loop D contract pin), and state the minimal correct future action WITHOUT tuning the extractor to rescue results.

## Your checklist (answer every item; cite packet fields)
1. Was the frozen prereg followed (population/intervention/baselines/metrics/taxonomy/stop rules; no threshold or rule hunting)?
2. Was the held-out set kept independent (UID overlap, freeze order, split integrity)?
3. Was any metric defined or modified after seeing results (post-hoc)?
4. Is the measurement object consistent before/after (same construct, correctly declared non-comparabilities)?
5. Any source-local tautology in the reported effect (per contracts/SOURCE_LOCAL_RESPONSE semantics)?
6. Any label / stage / outcome leakage (incl. provenance fields, pairing order, generation rules)?
7. Is cost accounted fairly (same-budget comparison; zero model calls verified by packet)?
8. Are effect sizes / CIs recomputable from the packet as given? (state what you could and could not recompute; that is expected for a packet-only audit)
9. Is the registered result classification reasonable and complete per the prereg taxonomy (POSITIVE / NULL / NEGATIVE / INVALID / NOT_EVALUABLE; NOT_EVALUABLE never merged into NULL)?
10. Does the packet suggest any manuscript claim beyond the evidence (should the SANER Route A manuscript cite, declining-cite, or bound this)?

## Required output format
## INDEPENDENCE DECLARATION
## CHECKLIST
- C1..C10: one line each (FACT/INFERENCE/UNVERIFIED)
## FINDINGS (ordered by severity; cite packet fields)
## STRONGEST OBJECTION
## VERDICT: ENDORSE_CLASS | ENDORSE_WITH_NOTES | CHALLENGE_CLASS
## RECOMMENDED REGISTRY CLASS: (one of POSITIVE / NULL / NEGATIVE / INVALID / NOT_EVALUABLE)
## RECOMMENDED MANUSCRIPT ROLE: (cite / bound / decline-cite / future-work) + one-line reason
## RESIDUAL RISKS / NEXT ACTION
End with the literal line: POSTAUDIT_COMPLETE