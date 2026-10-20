# Condition Change Real Model Tier 1 Return

Status: `COMPLETE_TIER1_WITH_INTERFACE_FAILURES`
Run ID: `CONDITION_CHANGE_TIER1_20261020`

| Quantity | Result |
|---|---:|
| Requests | 26/26 |
| Run tokens | 46,051 |
| Raw pairs | 26/26 |
| Invalid submissions | 8/26 |
| Answer coverage | 17/26 |
| Plan sufficiency | 18/26 |
| Composite acceptance | 16/26 |

The eight invalid outputs used
`{"submit_reimbursement_decision":{...}}`. Under the frozen direct-object
contract they are hard failures and were not repaired or re-run.

## Valid-Only Diagnostic

This is post-hoc, not the primary estimand. Primary pair rates are `2/3` flip
revision and `4/10` invariant preservation. Valid-only rates are `2/2` and
`4/4`, but they do not independently prove condition sensitivity.

## Interpretation

Compliant outputs often follow the stated policy delta, but pair rates do not
independently establish condition sensitivity. The dominant issue is
submission-representation ambiguity between tool call and bare object.

## Accounting

- Shared ledger: `82/192` requests and `504,701/2,000,000` tokens.
- Retries, judge, training, paid API, and production Memory writes: `0`.
- Verification: `11/11 PASS`.

## Ruling

`KEEP_TIER1_AS_INTERFACE_LIMITED_DEVELOPMENT_OBSERVATION`.

Do not claim an experience or condition-sensitivity effect. Before Tier 2,
freeze interface contract v3, run a form-only canary, and obtain one scoped
independent review.
