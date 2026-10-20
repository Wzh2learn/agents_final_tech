# MA-CERD Independent Research Return

Status: `INDEPENDENT_TASK_AUDIT_AND_PROBE_COMPLETE`

## Dataset Audit

- Source: MA-CERD Gold Public v1, Zenodo DOI `10.5281/zenodo.21946188`.
- License: CC BY 4.0 for data/docs; Apache-2.0 for release scripts.
- Release validation: PASS for 1,000 Gold records, privacy boundaries,
  family splits and SHA-256 manifest.
- Composition: 100 families, 685 change, 315 invariant; 600/200/200
  train/development/test; interventions cover requirement, authority,
  evidence, state and expression changes.

## Offline Baselines

| Baseline | Relation accuracy | Handling exact | Impact F1 | Preserved F1 |
|---|---:|---:|---:|---:|
| Base copy | 0.315 | 0.000 | 0.315 | 0.724 |
| All change | 0.685 | 0.813 | 0.445 | 0.104 |
| Oracle | 1.000 | 1.000 | 1.000 | 1.000 |

The independent task has substantial deterministic headroom.

## Model Probe

8 selected test contracts x 3 feedback arms x 2 controls = 48 requests. All
48 outputs were schema-valid and raw-complete.

Matched `REVISE` control produced identical scores for all three contracts:
relation `3/8`, handling `0/8`, impact F1 `0.375`, preserved F1 `0.756`.

Natural feedback produced the same relation `3/8` and handling `0/8` for all
arms. Exact-match and composite were identical; sufficiency-only differed only
slightly in impact F1 (`0.425` versus `0.375`) and preserved F1
(`0.649` versus `0.756`).

## Interpretation

The independent MA-CERD probe does not support superiority for exact-match,
sufficiency-only or composite feedback. When revision state is matched, the
arms are identical. Natural feedback differences are small and unstable and
are confounded by the prior no-change submission.

The result strengthens the earlier conclusion: current evidence supports a
feedback-contract *failure-mode taxonomy*, not a ranking of feedback methods.
A valid next study must independently vary feedback semantics while matching
revision intensity, prompt length and prior quality, with repeated decoding or
family-cluster uncertainty estimates.

## Accounting

- MA-CERD model requests: 48.
- MA-CERD run tokens: 76,994.
- Shared ledger after all approved exploration: `228/228` requests and
  `730,260/2,000,000` tokens.
- Raw pairs: 48/48; crashes and retries: 0.
- Judge, training, paid research API and production Memory writes: 0.

## Ruling

`STOP_FEEDBACK_RANKING_CLAIMS`.

Keep MA-CERD as the independent task source for a future preregistered
comparison. Do not claim that any feedback contract is currently superior or
that experience learning has been demonstrated.
