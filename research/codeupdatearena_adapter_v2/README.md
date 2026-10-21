# CodeUpdateArena Adapter V1

This directory contains the bounded external adapter specified by
`../research_portfolio_v2/CODEUPDATEARENA_ADAPTER_TASK.md`.

The runner has two explicit phases:

1. `prepare` verifies the pinned CodeUpdateArena source, builds the exact
   eight-family snapshot, executes every reference solution and hidden test in
   `python-sandbox:latest`, and freezes `TASK_SNAPSHOT.json` plus
   `PRE_MODEL_REPORT.md`.
2. `run` refuses to call the model unless the freeze receipt validates, then
   performs exactly 16 single-turn generations and preserves raw requests,
   responses, programs, Docker commands, stdout, and stderr.

Run focused contract tests with:

```powershell
py -3.11 -m unittest -v research.codeupdatearena_adapter_v1.test_run_adapter
```

Prepare and execute the bounded study with:

```powershell
py -3.11 research/codeupdatearena_adapter_v1/run_adapter.py prepare
py -3.11 research/codeupdatearena_adapter_v1/run_adapter.py run
```

`prepare` makes no model calls. `run` has zero retries and single concurrency.
Generated syntax, runtime, timeout, and test failures are recorded as model
results. Model identity, malformed response envelopes, missing usage, and
infrastructure failures stop the batch and remain in the ledger.
