# V3 Implementation Report

Status: `DEV_ONLY_AUTHORED_MECHANISM_FIXTURES`

## Boundary

V3 preserves V2 source/results and changes only this package. Policies execute
in a spawned process over canonical JSON RPC. The actor receives serialized
`ActorInput`, returned evidence, and exactly `inspect_dependency`,
`inspect_change`, and `run_target_test`. `actor.py` and `policy_rpc.py` contain
no evaluator imports; graph, fixture, trace, source-value, and Gold state stays
in evaluator-only modules.

Actor-visible scenario/change/node/output IDs are stable opaque IDs derived
from frozen ordinal positions. `fixtures.ActorIdentityMap` retains semantic
graph names for evaluator metrics and upper bounds. Hidden-label/Gold mutation
tests confirm serialized actor input and random ordering remain unchanged.

## Replay

The frozen nine-family fixture set and five policies are unchanged:
`no_check`, `random_check_seed_20261021`, `unit_cost_greedy`,
`two_step_lookahead`, and `full_recompute`. The fixed repairer remains
evidence-only. Budgets 0-9 produce 450 policy episodes.

| Policy | action loss | repair loss | query | recompute | missed | over | regression | completion | abstention |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `no_check` | 0.50 | 0.01 | 0 | 0 | 130 | 0 | 0.48 | 0.00 | 1.00 |
| `random_check_seed_20261021` | 0.42 | 0.00 | 405 | 587 | 75 | 25 | 0.28 | 0.39 | 0.61 |
| `unit_cost_greedy` | 0.10 | 0.00 | 405 | 756 | 27 | 0 | 0.10 | 0.80 | 0.20 |
| `two_step_lookahead` | 0.12 | 0.00 | 405 | 780 | 28 | 4 | 0.10 | 0.79 | 0.21 |
| `full_recompute` | 0.52 | 0.00 | 0 | 1980 | 0 | 140 | 0.00 | 1.00 | 0.00 |

The 90 matched greedy/two-step pairs have zero query-cost mismatches. Greedy is
sufficient on these fixtures: two-step has zero positive pairs, seven negative
pairs, and mean final-action-loss benefit `-0.02037037037` when defined as
`greedy_loss - two_step_loss`.

## Receipt

`receipt.py` schema v2 replays all budgets and compares canonical policy
results, per-budget aggregates, evaluator upper bounds, frontier, and paired
comparison. It validates opaque ID patterns, test summary consistency, exact
zero-call accounting, evidence boundary fields, source hashes, and replay
hashes. Result, aggregate, replay-hash, result-hash, source-hash, test-summary,
and zero-call tampering all fail closed.

## Verification

Commands:

```text
python -m pytest research/adaptive_revalidation_v3/tests -q
.\venv\Scripts\python.exe -m pytest research/adaptive_revalidation_v3/tests -q
python -m compileall -q research/adaptive_revalidation_v3
.\venv\Scripts\python.exe -m compileall -q research/adaptive_revalidation_v3
python -m research.adaptive_revalidation_v3 run --output <py39.json>
.\venv\Scripts\python.exe -m research.adaptive_revalidation_v3 run --output <py311.json>
python -m research.adaptive_revalidation_v3 receipt --output research/adaptive_revalidation_v3/result_receipt.json --test-command "python -m pytest research/adaptive_revalidation_v3/tests -q" --test-exit-code 0 --test-passed 24 --test-failed 0 --test-skipped 0
python -m research.adaptive_revalidation_v3 verify-receipt --input research/adaptive_revalidation_v3/result_receipt.json
```

Observed: Python 3.9 `24 passed` with one existing unknown `asyncio_mode`
warning; Python 3.11.9 `24 passed`; both compile checks exit 0. The independent
3.9/3.11 replay files are byte-identical at SHA-256
`7CC907097F3619E4323D6D67987A69DD3F82936F29E2C3BFD991CCD7AC5DF3BF`, which is
also bound and verified by the receipt.

Receipt test counts are self-attested inputs with field and arithmetic
consistency checks; they are not independent instrumentation of the pytest
process. The RPC is a capability/object boundary, not an OS security sandbox.

No model, network, judge, database, or training call was made. The shared dirty
worktree was not committed.
