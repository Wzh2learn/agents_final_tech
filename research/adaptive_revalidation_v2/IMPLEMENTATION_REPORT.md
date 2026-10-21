# Implementation Report

Status: `DEV_ONLY_AUTHORED_MECHANISM_FIXTURES`

## Scope and boundary

This package implements the bounded adaptive-revalidation thin environment in
`TASK_SPEC.md`. It is intentionally isolated under
`research/adaptive_revalidation_v2/` and makes no model, judge, network,
database, or training calls. Every result is development mechanism evidence
from authored fixtures, not external-task performance.

## Environment contract

`CHECKER_GRAPH` has 12 executable nodes and 3 outputs:

| Node | Operation | Dependencies |
|---|---|---|
| `price`, `rate`, `fee`, `branch_flag`, `bonus`, `unused` | source | none |
| `base` | add | `price`, `fee` |
| `scaled` | multiply | `base`, `rate` |
| `taxed` | copy | `base` |
| `total` | add | `scaled`, `taxed` |
| `margin` | subtract | `scaled`, `taxed` |
| `audit` | select | `branch_flag`, `bonus`, `scaled` |

The output set is `total`, `margin`, `audit`. Every fixture validates that its
before-source state reproduces an explicit success snapshot and that its
post-source state contains at least one source change.

The exact public query surface is:

1. `inspect_dependency(node_id)`
2. `inspect_change(change_id)`
3. `run_target_test(output_id)`

`ActorInput` contains only scenario ID, node/output identifiers, opaque change
summaries, and the query budget. It does not contain Gold, the hidden checker
graph, the hidden active trace, before/post values, or values derived from those
objects. Query evidence is returned by the three tools and is the only input
consumed by `FixedRepairer`; its method signature is `repair(bundle)`. The
full-recompute baseline is a separately labeled direct override
(`full_recompute_override`) and is not represented as fixed-repairer evidence.

## Scenario matrix

`fixtures/scenarios.json` freezes nine deterministic families. Each row has a
before-success snapshot and a post-change source state.

| Family | Change | Value-level Gold outputs | Visible-graph condition |
|---|---|---|---|
| `breaking` | price 100 to 110 | `total`, `margin`, `audit` | complete |
| `benign` | unused 0 to 7 | none | complete |
| `inactive_branch` | bonus 20 to 30 while guard is zero | none | static `bonus -> audit`, inactive in trace |
| `multiple_evidence` | fee 5 to 7 | `total`, `margin`, `audit` | complete |
| `value_cancellation` | price 100 to 110 and fee 5 to -5 | none | complete, source changes cancel in `base` |
| `near_additive` | price 100 to 110 and fee 5 to -3 | `total`, `margin`, `audit` | complete, small residual |
| `partial_breaking` | bonus 20 to 30 with guard one | `audit` | complete |
| `missing_edge` | price 100 to 110 | `total`, `margin`, `audit` | visible `price -> base` edge omitted |
| `noisy_edge` | unused 0 to 7 | none | visible unused -> total edge added |

The value-level Gold set is the evaluator-only set of outputs whose computed
before and post values differ. Structural graph reachability and active-trace
reachability are reported separately as upper bounds.

## Policies

All policy replays use a fixed query budget of 9 on these fixtures and unit
query cost.

| Policy | Selection rule | Final action source |
|---|---|---|
| `no_check` | no queries | fixed repairer over empty evidence |
| `random_check_seed_20261021` | seeded LCG shuffle without replacement | fixed repairer |
| `unit_cost_greedy` | maximum expected one-query entropy reduction per unit cost | fixed repairer |
| `two_step_lookahead` | one-step gain plus expected best second-query gain | fixed repairer |
| `full_recompute` | recompute every output, no queries | direct baseline override |

The information-gain policies maintain a binary impact hypothesis over the
three visible outputs. Query likelihoods are deterministic, actor-visible
heuristics; they do not inspect the hidden graph, Gold, or hidden trace. The
query trace records the selected query and score, but that trace is not passed
to the repairer.

## Fixed repairer replay

For each output, `FixedRepairer` applies these ordered rules using only the
returned `EvidenceBundle`:

1. A failing `run_target_test` forces `recompute`.
2. A passing `run_target_test` commits `keep`.
3. All inspected source deltas zero commits `keep`.
4. Any visible dependency path from an actor change commits `recompute`.
5. Complete dependency evidence against all changes commits `keep`.
6. Anything unresolved is an explicit `abstain`.

This supports multiple valid evidence sets: dependency/change evidence and
target-test evidence can independently produce the same action.

## Metrics

Let `G` be evaluator-only outputs whose values change, `R` be outputs marked
`recompute`, and `n` be three outputs. The metrics are deliberately partial and
not collapsed into one score:

- `final_action_loss`: mean per-output decision loss, 0 for the minimal
  value-preserving committed action, 1 for a wrong committed action, and 0.5
  for an abstention.
- `repair_loss`: mean squared normalized final error,
  `((final - post) / max(1, abs(before), abs(post)))^2`.
- `query_cost`: public query count, one per tool call.
- `recomputation_cost`: sum of static dependency-closure node counts for outputs
  in `R`.
- `missed_invalidation`: `|G - R|`.
- `over_invalidation`: `|R - G|`.
- `regression_rate`: fraction of outputs whose final value differs from post.
- `completion`: fraction of outputs with a committed keep/recompute decision.
- `abstention`: fraction of outputs with an explicit abstain decision.

Exact cancellation and inactive branches remain zero-repair cases; a near-
additive residual remains a graded repair error. Oracle graph and full-trace
calculations occur only in the separate `evaluator_only_upper_bounds` record,
with `policy_eligible: false`.

## Deterministic aggregate results

These are nine-fixture replay totals from the final mechanism run:

| Policy | action loss | repair loss | query | recompute | missed | over | regression | completion | abstention |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `no_check` | 0.500000 | 0.005873 | 0 | 0 | 13 | 0 | 0.481481 | 0.000000 | 1.000000 |
| `random_check_seed_20261021` | 0.148148 | 0.000853 | 81 | 73 | 4 | 1 | 0.148148 | 0.777778 | 0.222222 |
| `unit_cost_greedy` | 0.000000 | 0.000000 | 81 | 96 | 0 | 0 | 0.000000 | 1.000000 | 0.000000 |
| `two_step_lookahead` | 0.000000 | 0.000000 | 81 | 96 | 0 | 0 | 0.000000 | 1.000000 | 0.000000 |
| `full_recompute` | 0.518519 | 0.000000 | 0 | 198 | 0 | 14 | 0.000000 | 1.000000 | 0.000000 |

The table is descriptive fixture evidence only; it is not a claim about
external task performance or model quality.

## Tests and verification

The focused suite covers the graph/fixture contract, actor boundary, exact
public-tool payload shapes, query-budget enforcement, invalid targets and
evidence ordering, graph fail-closed validation, multiple evidence sets,
missing/noisy edge behavior, cancellation, inactive branches, partial impact,
near-additive errors, policy determinism, information-gain budgets, metric
partiality, oracle separation, receipt determinism, and receipt tampering.

Development test iterations were:

| Run | Result | Cause of any red |
|---|---|---|
| initial focused run | 14 passed, 1 failed | test expected an empty full trace while source nodes correctly remained changed |
| boundary-test run | 15 passed, 2 failed | test setup hit sequential-index and node-count guards before duplicate/cycle guards |
| final focused run | 17 passed, 1 warning | warning is the repository's existing unknown `asyncio_mode` pytest option |

Fresh commands used for the final claim:

```text
python -m pytest research/adaptive_revalidation_v2/tests -q
python -m compileall -q research/adaptive_revalidation_v2
python -m research.adaptive_revalidation_v2 receipt --output research/adaptive_revalidation_v2/result_receipt.json --test-command "python -m pytest research/adaptive_revalidation_v2/tests -q" --test-exit-code 0 --test-passed 17 --test-failed 0 --test-skipped 0
python -m research.adaptive_revalidation_v2 verify-receipt --input research/adaptive_revalidation_v2/result_receipt.json
```

The repository requests Python 3.12, but this local Windows environment has no
3.12 interpreter. The final source compiles and the focused suite passes under
the available Python 3.9.10 interpreter; the available repository virtual
environment reports Python 3.11.9 and is used as an additional compatibility
check. No model or network call was made.

## Files

- `model.py`, `environment.py`, `repairer.py`, `metrics.py`, `policies.py`,
  `runner.py`, `receipt.py`, `__main__.py`, `__init__.py`
- `fixtures.py`, `fixtures/scenarios.json`, `py.typed`
- `tests/test_adaptive_revalidation.py`
- `TASK_SPEC.md`, `README.md`, `RESULT_NOTE.md`, this report
