# MA-CERD Interpretation Corrections

Date: 2026-10-21, Asia/Shanghai
Status: `DATED_CORRECTION_APPLIED_TO_CURRENT_INTERPRETATION`

This note supersedes the current explanatory wording only. The original
reports, prompts, predictions, Gold labels and scores remain unchanged.

## 1. Resource membership is not dependency propagation

`run_adjudicator_oracle.py` selects nodes by membership in
`candidate_features.resource_ids`; it does not traverse dependency edges.
The result supports resource-membership localization and calibrated public
rules. It does not establish that graph propagation works or that dependency
structure is the unique bottleneck. Fresh and staged probes also omit plan
edges, so their score differences do not isolate one common information set.

## 2. Handling `0.012` is exact full-set matching

The uncertainty prompt permits subsets of `execute`, `repair`, and `defer`,
while scoring requires exact equality with the complete Gold allowed set.
Post-hoc recomputation on the existing 250 predictions found:

- 241 predictions are `{defer}`; all 241 are admissible.
- 245 predictions are non-empty subsets of Gold.
- 250 predictions intersect Gold.
- Exact complete-set matching is `3/250 = 0.012`.
- Macro set precision is `0.990`; recall is `0.4173`.

These facts separate enumerating all allowed actions from selecting the
action to execute. Admissibility is not completion, utility, risk control, or
task success. Any new study must report always-defer, coverage, completion,
risk and cost as separate outcomes.

## 3. The transparent baseline is a full-release summary

The reported relation `0.881`, handling `0.839`, impact F1 `0.676`, and
preserved F1 `0.648` summarize all 1,000 release records after train-family
calibration. They are not pure held-out metrics.

For the original test partition, relation is `0.830`, handling `0.835`,
impact F1 `0.5856`, and preserved F1 `0.5280`. The original test has been
used repeatedly for development. Future claims require paired family
differences and genuinely new families.

## 4. The uncertainty queue uses oracle-assisted diagnostics

The model input includes `o3_relation`. This is useful for diagnosing the
queue but is oracle-assisted relative to a deployment setting. In this
release, the 250-record queue is equivalent to selecting the public
`blocking_requirements` signature. That equivalence does not establish that
the same selector will work on a new distribution.

Directly supplied O1 output and independently computed O1 evidence must be
reported separately.

## 5. Simulator and trace replay status

The MA-CERD simulator/trace has not been independently replayed in this
project. Gold labels must not be used to reconstruct a trace. Simulation
execution, adjudication policy and the complete allowed-action set are
different targets and cannot be collapsed into one success metric.

## 6. Fixture boundary

The 10 `DEV_ONLY_AUTHORED_MECHANISM_FIXTURES` checks show that selected
mechanisms can be expressed and negative cases detected under authored
inputs. They do not establish external-task validity, model capability,
learning guards, or method superiority.
