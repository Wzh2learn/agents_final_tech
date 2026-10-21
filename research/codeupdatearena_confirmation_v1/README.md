# CodeUpdateArena Confirmation Adapter V1

This directory contains the independent new-family confirmation adapter. The
frozen family set is
`../research_portfolio_v2/CODEUPDATEARENA_CONFIRMATION_FAMILIES.json`.

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
py -3.11 -m unittest -v research.codeupdatearena_confirmation_v1.test_revalidate
```

Prepare and execute the bounded study with:

```powershell
py -3.11 research/codeupdatearena_confirmation_v1/run_adapter.py prepare
py -3.11 research/codeupdatearena_confirmation_v1/run_adapter.py run
```

`prepare` makes no model calls. `run` has zero retries and single concurrency.
Generated syntax, runtime, timeout, and test failures are recorded as model
results. Model identity, malformed response envelopes, missing usage, and
infrastructure failures stop the batch and remain in the ledger.

`revalidate_v1.py` and `REVALIDATION_LEDGER.json` are retained copies from the
prior V2 revalidation package and are not used by this confirmation run.
`run_frozen/` preserves the exact spec and runner bytes used for the model
batch; top-level spec/report metadata was corrected only after execution.
