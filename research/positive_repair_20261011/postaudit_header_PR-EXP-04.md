# Loop C Post-Result Independent Audit — PR-EXP-04 (GENERALIZATION_TEST)

You are the independent Loop C auditor. POST-RESULT audit of one completed Track P experiment. Read-only, packet-only, report-only: no tools, no file reads, no network, no edits. Judge strictly from this packet; missing evidence -> UNVERIFIED. Do not modify, re-run, or rescue the result. Labels: FACT / INFERENCE / UNVERIFIED.

## Round context (disclosed facts)
- Track P first wave: PR-EXP-03/01 INTERVENTION_REPAIR, PR-EXP-04 GENERALIZATION_TEST (supporting-only; never counts toward the repair count), PR-EXP-07 ROBUSTNESS_ANTI_TAUTOLOGY.
- Registered class for PR-EXP-04: INVALID.
- Disclosed incidents, NOT scientific record: two engineering dispatch layers (a1 INPUT_MISSING x4; a2 HASH_MISMATCH x4) were fail-closed infrastructure failures with zero scientific side effects.
- SPECIAL: Registered INVALID came from a FROZEN_IMPLEMENTATION_FAILURE - KeyError: 'group_uid' at run_pr_exp_04.py:690 in build_scientific_result, raised AFTER generation and gates (preflight END_TO_END_PREFLIGHT_PASS; row/group gates PASS; harness equivalence 72/72 response vectors identical) and BEFORE metric evaluation; the agent refused post-generation source edits per freeze discipline; no rescue attempted (recorded). Judge whether INVALID is the correct class (vs MECHANISM_NOT_EVALUABLE), attribute the root cause (Loop A implementation bug vs Loop D contract), and state the minimal correct future action.
- Note: the descriptive machinery claims N1/N2 mechanisms were generated, gates passed, and the N1 harness-equivalence control passed; cross-mechanism metrics are NOT_COMPUTED. Do not treat anything as transfer evidence.

## Checklist (answer every item; cite packet fields)
1. Was the frozen prereg followed (population/intervention/baselines/metrics/taxonomy/stop rules; no threshold/rule hunting)?
2. Held-out independence (mechanism-disjoint + group-disjoint; UID overlap; freeze order)?
3. Any metric defined/modified after seeing results?
4. Measurement object consistent before/after?
5. Any source-local tautology in anything REPORTABLE from this packet?
6. Any label / stage / outcome leakage (incl. provenance fields, pairing, generation rules)?
7. Cost fairness (same-budget; zero model calls verified by packet)?
8. Are effect sizes / CIs recomputable from the packet as given? (state what you could and could not recompute)
9. Is the registered result classification reasonable and complete per the prereg taxonomy (POSITIVE / NULL / NEGATIVE / INVALID / NOT_EVALUABLE; NOT_EVALUABLE never merged into NULL)?
10. Manuscript role: should the SANER manuscript cite, bound, or decline this; any claim beyond evidence?

## Required output format
## INDEPENDENCE DECLARATION
## CHECKLIST
- C1..C10: one line each (FACT/INFERENCE/UNVERIFIED)
## FINDINGS (ordered by severity; cite packet fields)
## STRONGEST OBJECTION
## VERDICT: ENDORSE_CLASS | ENDORSE_WITH_NOTES | CHALLENGE_CLASS
## RECOMMENDED REGISTRY CLASS: (one of POSITIVE / NULL / NEGATIVE / INVALID / NOT_EVALUABLE)
## ROOT CAUSE ATTRIBUTION: (LOOP_A_IMPLEMENTATION_DEFECT | LOOP_D_CONTRACT_DEFECT | SCIENTIFIC_GATE | UNKNOWN) + one line
## RECOMMENDED MANUSCRIPT ROLE: (cite / bound / decline-cite / future-work) + one line
## RESIDUAL RISKS / NEXT ACTION
End with the literal line: POSTAUDIT_COMPLETE