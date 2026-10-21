# Adaptive Revalidation V3

This directory contains a deterministic development-only mechanism fixture.
It is evidence for bounded adaptive revalidation, not an external-task
benchmark. Every result is labeled `DEV_ONLY_AUTHORED_MECHANISM_FIXTURES`.

Policy batches run in a spawned process over canonical JSON RPC. The policy
receives serialized actor input and a client with exactly these calls:

```text
inspect_dependency
inspect_change
run_target_test
```

Actor-visible scenario, change, node, and output IDs are stable opaque IDs.
Evaluator-only identity maps retain semantic graph names for metrics and upper
bounds. The fixed repairer receives only serialized evidence bundles.

Run focused tests from `agents_final_tech`:

```text
python -m pytest research/adaptive_revalidation_v3/tests -q
.\venv\Scripts\python.exe -m pytest research/adaptive_revalidation_v3/tests -q
```

Run the deterministic budget sweep and receipt checks:

```text
python -m research.adaptive_revalidation_v3 run --output result.json
python -m research.adaptive_revalidation_v3 receipt --output research/adaptive_revalidation_v3/result_receipt.json --test-command "python -m pytest research/adaptive_revalidation_v3/tests -q" --test-exit-code 0 --test-passed 22 --test-failed 0 --test-skipped 0
python -m research.adaptive_revalidation_v3 verify-receipt --input research/adaptive_revalidation_v3/result_receipt.json
```

The `run` command covers query budgets 0 through 9 and reports the
cost/action-loss frontier plus matched-cost greedy/two-step comparison.
