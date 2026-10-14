# T3 policy-level runner

This directory contains a Python 3.12, standard-library-only mock runner for T3.
It implements deterministic request recording, monotonic counting, explicit
fail-closed budget handling, and policy denial evidence. The mock transport
reads only the local fixtures in `fixtures/`; it never opens a socket, invokes a
model, contacts a production service, or connects to a database.

## Usage

Run one fixture into a disposable workspace:

```bash
python3 runner/runner.py execute \
  --workspace /absolute/path/to/scratch \
  --run-id 20261014T161814Z_0123abcd \
  --fixture runner/fixtures/success.json
```

Run the local qualification suite:

```bash
python3 runner/run_qualification.py \
  --pass-id PASS_1 \
  --output qualification_pass_1.json \
  --scratch-root qualification_work/PASS_1
```

The run ID must match `YYYYMMDDTHHMMSSZ_uuid8`. Existing run directories are
rejected before any write. Existing attempt directories are rejected before
`request.json`; `overwrite_rejection.json` records the refusal while preserving
the existing evidence.

## Accounting model

- `model_extra_requests` counts every mock transport attempt, including
  simulated failure, timeout, manual retry, and crash.
- `transport_calls` counts actual mock transport invocations.
- `budget_rejections` counts attempts stopped before transport because the cap
  was already reached.
- `execution_chat_usage` remains `UNRESOLVED`; it is never reported as zero.
- `count_history.jsonl` stores before/after values and is checked for monotonic
  progression.

## Boundary and unverified surface

The runner is policy-level, not an OS sandbox. The allowlist and rejection
logic are tested locally, but kernel isolation, network namespaces, filesystem
capabilities, containers, seccomp, and cross-user enforcement are not
implemented or claimed. Qualification is `LOCAL_DEV_HOST`; it does not bind
GB10 runtime behavior and does not qualify production, training, database, or
real model endpoints.
