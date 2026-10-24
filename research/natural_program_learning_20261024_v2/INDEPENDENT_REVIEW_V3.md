# Independent AI Review V3

Date: 2026-10-24, Asia/Shanghai

Identity: `INDEPENDENT_AI_SCIENTIFIC_REVIEW`, not human gold, blind review, or
financial professional certification.

## Review Verdict

- The old claim that relevant-change adaptation was zero should be withdrawn.
  Ninety-five frozen outputs were mis-scored against stale task tables.
- Ordinary answer/execution SFT is a strong baseline only on the bounded
  TAT-QA same-source panels. It is not a cross-dataset or general SOTA claim.
- Visible-program filtering and paired-variant stability supervision should
  both stop under their frozen rules.
- C3 has no delivery-policy increment: all-applicable and always-accept make
  the same decisions on the confirmation outputs.

## Findings And Responses

1. **Metric denominators.** The reviewer correctly noted that the report mixed
   task-level paired intersections with raw per-instance delivery counts.
   `METHOD_RESEARCH_RETURN_V3.md` and `V3_RESOURCE_RECEIPT.json` now define
   both explicitly. The ordinary confirmation counts 68/72 raw correct are
   consistent with 23/24 original, 22/24 original-and-relevant and 22/24
   original-and-irrelevant intersections; these quantities are not additive.
2. **Stability counts.** The 61/72, 62/72 and 63/72 raw delivery counts are
   consistent with task-level intersections in the summary. They are now
   reported as raw output counts and no longer interpreted as policy gains.
3. **Relevant-change percentage.** Test raw relevant-change correctness is
   20/24 = 83.3%; the previously reported 75.0% is the paired
   `original AND relevant` intersection. Both are now labelled.
4. **Historical logistic comparison.** The evidence is in
   `C3_DELIVERY_ANALYSIS_CORRECTED_V3.json`, which was outside the reviewer's
   narrow file list. The method return now links it directly.
5. **Resource ledger path.** The reviewer prompt omitted the repository
   segment `agents_final_tech`; the actual ledger exists at
   `research/publication_thesis_goals_v1/RESOURCE_LEDGER.json` and its V3
   delta arithmetic was independently checked.
6. **Reference terminology.** `executable gold derivations` was corrected to
   `executable reference derivations`.
7. **Single next step.** The next step is now only a frozen deterministic
   row/period binding checker on a disjoint new-family panel. A new natural
   source is deferred to a later transfer question.

## Residual Risk

The confirmation families are same-source TAT-QA table families, not an
independent benchmark. The sample is small, and the binding checker is not yet
implemented. The review therefore supports the stop decisions and measurement
correction, but not a general claim that evidence-binding supervision is
unnecessary.
