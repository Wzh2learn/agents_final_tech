# B2B Output-Budget and Analysis Repair Decision

Goal ID: `FEEDBACK_LEARNING_PHASE_B_20261026`
Date: 2026-10-26, Asia/Shanghai

## Identity Of The First B2 Run

The first B2 run is retained as
`EXPOSED_DEVELOPMENT_INTERFACE_TRUNCATION_RUN`, not as a final method negative.

- The same-start R/E training itself completed two authorized runs.
- The 108-row generative run used the frozen 192-token output cap.
- R and E each produced exactly `36 * 192 = 6,912` completion tokens.
- R had 24 `SYNTAX_ADAPTER_FAILURE` rows and E had 24; E had zero legal
  patches. This is consistent with systematic truncation/representation
  overflow, not evidence that local editing lacks useful information.
- The first analysis also used all-three-variants-correct family identity as
  the primary paired score. That is a valid paired-completion diagnostic, but
  it is not the frozen overall `SET_BINDING_SET_ACCURACY` estimand and hides
  row-level harm. The primary development contrast must be the mean row-level
  paired difference, aggregated within source family and then across families.

No confirmation source was generated or inspected.

## Bounded Repair

Run a second development generation on the same frozen 12-family panel using
the same already-trained R/E adapters, visible task content, seeds, decoding
and information contract. Only the output-format instruction may be tightened
to request the contracted object without prose. Do not retrain and do not
change the supervision, checkpoint, panel, target, patch applier or
confirmation data.

Only these deployment-output repairs are allowed:

1. Raise `max_new_tokens` from 192 to 384.
2. Require the model to return only its contracted JSON/patch object, with no
   explanatory prose.
3. Keep strict-whole-JSON, embedded-JSON and syntax-adapter outcomes separate.
4. Preserve raw text and truncation/finish reasons.

Primary analysis:

- Unit row: each trajectory variant.
- `SET_BINDING_SET_ACCURACY` only; no answer-correctness score.
- Paired E-R and E-N row differences averaged within each of the 12 source
  families, then averaged across families.
- Bootstrap or exact paired intervals resample source families, not 36 rows.
- Report all-three-variants-correct paired completion separately.
- Report O-error repair, O-correct damage, wrong delivery, reasonable
  UNKNOWN/abstention, coverage, syntax, patch legality, contract preservation,
  target-token length and end-to-end cost.

## Accounting

- New generation attempts: 72 maximum, R and E only, 36 each.
- New generation tokens: conservative cap 180,000.
- Training runs: 0.
- Training tokens: 0.
- Reallocate 36 attempts from `failure_interface_reserve` and 36 attempts from
  the still-unreleased `exposure_clean_confirmation` allocation. Do not exceed
  the global Phase B cap and do not call this confirmation.
- Preserve the first run raw, logs and partial-failure record.

## Exit Rule

If the repaired run still has pervasive syntax/interface failures, stop the R/E
candidate as an interface/representation failure and do not launch confirmation
or second seed. If outputs become valid but E remains below the frozen effect
threshold or damages originally-correct families, stop the local-edit candidate
on a method-level development negative. If E passes the development gate, freeze
the repaired contract and request a separately exposure-clean confirmation
panel before any new-source generation.
