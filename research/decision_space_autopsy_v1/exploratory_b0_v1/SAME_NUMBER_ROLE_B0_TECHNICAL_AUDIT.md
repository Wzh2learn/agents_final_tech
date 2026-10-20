# Same-Number Role B0 Technical Audit

Status: `RESCORE_ACCEPTED_EXPLORATORY_HEADROOM`

## Run identity

- Authorization: `SAME-NUMBER-B0-20261019-1035-48REQ-R2`
- Requests: 48/48, no retry, single concurrency.
- Tasks: 24, including 9 development and 3 exploratory future clusters, two matched tasks per cluster.
- Actual tokens: 29,207.
- Raw: 48 request/response pairs, 0 crash.

The first launch at 10:34 UTC stopped before the window with 0 requests. It is preserved as a pre-window incident and is not part of the scientific run.

## Original contract defect

The original runner reported `11/24` success. Eight consume responses were marked `FORMAT_INVALID` because the validator required null numeric/unit fields for `WRONG_ROLE`. The raw model outputs carried the actual calculator value and unit while declaring `WRONG_ROLE`, which is semantically necessary to distinguish role failure from numeric failure.

This was a scoring contract defect. The model outputs themselves were parseable JSON.

## Versioned rescore

The corrected contract requires numeric `calc_value` and `unit` for both `SUPPORTED` and `WRONG_ROLE`; only `UNKNOWN/REFUSE` require nulls. The rescore reparsed immutable raw responses and changed no task, reference, prompt or request.

Corrected result:

- success: 18/24;
- non-success: 6/24;
- non-success clusters: 6;
- decision: `CONTINUE_TO_ARM_DESIGN`.

Failure decomposition:

- 5 false accepts: expected `WRONG_ROLE`, returned `SUPPORTED`, numeric result matched;
- 1 false reject: expected `SUPPORTED`, returned `WRONG_ROLE`, numeric result matched;
- development: 13/18 success;
- exploratory future: 5/6 success;
- same-number: 13/18 success;
- same-delta: 5/6 success.

The failures are role-decision failures while the tool/numeric path remains correct.

## Interpretation

This is the first panel with observable headroom for experience reuse: the disputed action is evidence-role acceptance, not arithmetic. The result remains exploratory because the unit comparator and consume contract required technical correction after the first B0 and the future holdout has only three clusters.

## Required caveat

Always report the immutable original `11/24` result together with the versioned `18/24` rescore. Do not describe the corrected result as a pre-registered confirmatory estimate. No R/C/H was run in this B0.
