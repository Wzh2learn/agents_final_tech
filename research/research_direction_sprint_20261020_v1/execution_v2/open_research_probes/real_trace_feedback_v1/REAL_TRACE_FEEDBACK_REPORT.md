# Real-Trace Feedback Contract Analysis

Status: `POSTHOC_DEV_ONLY_COMPLETED`
Date: 2026-10-20, Asia/Shanghai

## Evidence Identity

- Real model traces: seven B0 V2 `plan -> evidence_lookup -> consume` outputs
  from run `FINRANK_C1_B0_V2_ENGINEERING_FIX_20261020T031024.100294Z`.
  The source records 14 real generation requests, one success and six
  non-successes.
- AI development reference: `REFERENCES_V1.json`, `human_confirmed=false`.
  It is not human gold, blind review or independent validation.
- Post-hoc intervention: the feedback contracts and update dispositions below
  were computed after observing B0 and were not available to the actor.

No new model, judge, training, service or network request was made. The shared
generation ledger was not modified.

## Contract Comparison

| Contract | Accepted | Main limitation on these traces |
|---|---:|---|
| exact-match | 0/7 | Rejects the successful ESD_010 set because `cand_003+cand_007` is a valid sufficient set with optional redundant support |
| minimal sufficient set | 3/7 | Retains ESD_001 and ESD_006 despite incomplete V1 answer atoms |
| fact coverage V1 | 1/7 | Ignores evidence precision; ESD_006 is also penalized by over-required operands |
| set-valued sufficiency + scope precision | 3/7 | Correct for evidence, but still retains traces with incomplete answers when used alone |
| composite trace V1 | 1/7 | Correctly separates evidence and answer gates, but preserves the ESD_006 reference defect |
| composite trace + C2 sensitivity | 2/7 | Most explanatory: accepts ESD_010 and ESD_006 while separating the four actionable trace revisions |

The C2 sensitivity only changes ESD_006 required answer atoms to
`derived_gross_profit` and `derived_gross_margin`. It does not rewrite
`REFERENCES_V1.json`.

## Six Non-Successes

| Task | What is retained | What is revised or rejected | Cause |
|---|---|---|---|
| ESD_001 | Real trace and sufficient `cand_001` consume action | Revise answer facts | Evidence is correct; 12,471 and 5,050 values are absent |
| ESD_002 | Real failure record only | Reject current evidence and answer claims | `cand_005` is unsupported and no answer atom is produced |
| ESD_003 | Real trace and partial support from `cand_006` | Revise selection and answer facts | Add `cand_007`, remove unsupported `cand_001`, then answer both atoms |
| ESD_004 | Real trace and supported `cand_003` | Revise selection and answer facts | Add `cand_005`; current consume omits ROE |
| ESD_006 | Real trace and requested 20,541 / 11.97% output | Revise the reference scope, not the model trace | C1/C2 identify the V1 revenue/cost operands as over-required |
| ESD_012 | Real trace and supported method evidence from `cand_005` | Revise selection and answer facts | Add `cand_001`; replace unsupported trend interpretation with 2.42/3.33/4.12 |

ESD_010 remains the positive control. Its evidence is sufficient and precise,
and both answer atoms match. Exact-match nevertheless rejects it because the
valid optional redundant candidate changes the set identity.

## Interpretation

The composite contract with the labeled ESD_006 sensitivity is the most
explanatory. It avoids three distinct errors:

1. exact-match penalizes valid alternative sufficient sets;
2. minimal-set-only retains correct evidence traces whose answers are incomplete;
3. fact-coverage-only ignores whether the evidence action is supported.

This is evidence that feedback semantics can change which real trajectories
would be retained or repaired. It is not evidence that experience learning
improves model behavior.

## H Decision

The current traces do **not** yet support a small real-history H comparison.
The six non-successes mix answer-fact omission, partial evidence selection,
one unsupported selection and one reference defect. They do not define a
homogeneous residual decision, and no complete task-matched correction
histories have been established.

Stop H unless both conditions hold after corrected/equal-visibility baseline
qualification:

1. at least two comparable residual evidence-selection failures remain; and
2. at least two complete task-matched real histories can change that same
   decision through an executed feedback/correction chain.

If residual errors are mainly answer or reference defects, or eligible
correction histories cannot be formed, stop this H candidate and preserve the
boundary result.

## Artifacts

- Frozen fixture: `fixture/real_trace_feedback_fixture.json`
- Freeze receipt: `fixture/FREEZE_RECEIPT.json`
- Machine-readable analysis: `REAL_TRACE_FEEDBACK_ANALYSIS.json`
- Deterministic analyzer: `real_trace_feedback.py`
- Contract tests: `test_real_trace_feedback.py`

All five regression tests pass with `python -B -m unittest -v
test_real_trace_feedback.py`.
