# Adaptive Revalidation V3 Implementation Report

Date: 2026-10-21
Status: `IMPLEMENTATION_COMPLETE_DEV_ONLY`
Evidence boundary: `DEV_ONLY_AUTHORED_MECHANISM_FIXTURES`

## Scope

Completed `research/adaptive_revalidation_v3/` without modifying V2 source or
results. V3 preserves the nine fixture families, five policies, fixed repairer,
and all V2 metrics while correcting the independent-review blockers.

Policy batches now execute in a spawned process over canonical JSON RPC. The
policy receives only serialized `ActorInput`, returned evidence, and a client
with exactly `inspect_dependency`, `inspect_change`, and `run_target_test`.
Actor-side modules contain no evaluator imports. Returned evidence must match
the actual RPC calls, and only `full_recompute` may override the fixed repairer.

Actor scenario/change/node/output IDs are stable opaque IDs derived from frozen
ordinal positions. Semantic names remain in an evaluator-only identity map for
metrics and upper bounds. Hidden-label/Gold mutation tests leave serialized
actor input and random ordering unchanged.

Receipt verification independently replays the full budget sweep and compares
canonical result sections, aggregates, frontier, and paired comparison. It also
checks source hashes, opaque-ID patterns, test-summary consistency, exact
zero-call accounting, evidence-boundary fields, and replay hashes.

## Files

- `research/adaptive_revalidation_v3/actor.py`: actor-safe DTOs and JSON codec.
- `research/adaptive_revalidation_v3/policy_rpc.py`: spawned worker and
  three-call RPC client.
- `research/adaptive_revalidation_v3/policies.py`: actor-only five-policy code.
- `research/adaptive_revalidation_v3/repairer.py`: evidence-only fixed repairer.
- `research/adaptive_revalidation_v3/environment.py`: evaluator-side tools.
- `research/adaptive_revalidation_v3/fixtures.py`: frozen fixtures and
  evaluator-only opaque identity map.
- `research/adaptive_revalidation_v3/model.py`: evaluator graph/trace/results.
- `research/adaptive_revalidation_v3/metrics.py`: preserved metrics.
- `research/adaptive_revalidation_v3/runner.py`: RPC orchestration, budgets,
  frontier, and paired comparison.
- `research/adaptive_revalidation_v3/receipt.py`: replay-bound receipt builder
  and fail-closed verifier.
- `research/adaptive_revalidation_v3/tests/test_adaptive_revalidation.py`:
  capability, opacity, replay, metric, and tamper tests.
- `research/adaptive_revalidation_v3/{TASK_SPEC.md,README.md,RESULT_NOTE.md,IMPLEMENTATION_REPORT.md}`.
- `research/adaptive_revalidation_v3/result_receipt.json`: regenerated receipt.
- `docs/superpowers/plans/2026-10-21-adaptive-revalidation-v3.md`: execution
  plan required by repository workflow.

## Commands And Results

```text
python -m pytest research/adaptive_revalidation_v3/tests -q
```

Result: `24 passed`, one existing warning for unknown pytest option
`asyncio_mode`.

```text
.\venv\Scripts\python.exe -m pytest research/adaptive_revalidation_v3/tests -q
```

Result: Python 3.11.9, `24 passed`.

```text
python -m compileall -q research/adaptive_revalidation_v3
.\venv\Scripts\python.exe -m compileall -q research/adaptive_revalidation_v3
```

Result: both exit code 0.

```text
python -m research.adaptive_revalidation_v3 run --output <py39.json>
.\venv\Scripts\python.exe -m research.adaptive_revalidation_v3 run --output <py311.json>
```

Result: both exit code 0 and are byte-identical at SHA-256
`7CC907097F3619E4323D6D67987A69DD3F82936F29E2C3BFD991CCD7AC5DF3BF`.
The replay contains 450 episodes, nine families, five policies, and budgets
0-9. The receipt binds and verifies this exact serialized replay hash.

```text
python -m research.adaptive_revalidation_v3 receipt --output research/adaptive_revalidation_v3/result_receipt.json --test-command "python -m pytest research/adaptive_revalidation_v3/tests -q" --test-exit-code 0 --test-passed 24 --test-failed 0 --test-skipped 0
python -m research.adaptive_revalidation_v3 verify-receipt --input research/adaptive_revalidation_v3/result_receipt.json
```

Result: `PASS`; 450 policy episodes, 9 families, budgets 0-9, 19 source files.
Receipt SHA-256:
`7BE5255FA76BDAA8D4F33FC86E8071B263D6878C6F0439F2894E39821ACCF4F7`.

## Scientific Comparison

Across all 90 matched-budget/scenario greedy versus two-step pairs:

- query-cost mismatches: 0;
- positive two-step pairs: 0;
- negative two-step pairs: 7;
- mean `greedy_loss - two_step_loss`: `-0.02037037037`;
- `greedy_sufficient`: true;
- `two_step_adds_paired_benefit`: false.

The numeric cost/action-loss Pareto frontier is recorded in the replay and
receipt. Semantic family labels are used only for evaluator reporting, not
policy input, sampling, or scoring.

## Concerns

- These are authored development fixtures, not external-task or model evidence.
- The spawned RPC boundary is a capability/object boundary, not an OS security
  sandbox; policy code can still import files from the shared filesystem.
- Receipt test counts are self-attested and checked for field/arithmetic
  consistency; they are not independent pytest instrumentation.
- The system Python 3.11 launcher had no pytest, so the required 3.11 test run
  used the repository virtual environment's Python 3.11.9 and pytest 9.0.1.
- The repository's existing pytest `asyncio_mode` warning remains unchanged.
- The shared worktree was already dirty and was not committed.

No model, network, judge, database, or training call was made.
