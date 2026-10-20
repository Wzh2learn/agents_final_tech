# COLLECTION_EXECUTION_READINESS Goal

Build one offline, hash-frozen execution package for a future single 54-request TAT-QA history collection run without issuing any model request or starting any service.

## Done when

1. `TASK_REFERENCE_MANIFEST.json` deterministically contains 12 history tasks (one per history cluster), 16 future tasks (two per future cluster), and 4 development tasks (two per development cluster), with independently recomputed contract-scoped references and explicit visibility fields.
2. A fixed plan and consume prompt pair, JSON schemas, and strict parser reject malformed or unknown-field model/tool outputs without silent coercion.
3. A non-generative runtime identity snapshot binds every available model, tokenizer, chat template, service binary, generation parameter, calculator, checker, runner, adapter, schema, and prompt hash; unavailable identities are `UNRESOLVED` blockers rather than guesses.
4. `collection_runner.py` integrates hard request/token budget, unique request IDs, immutable raw capture, crash state, plan -> real tool -> consume flow, and an execution authorization gate that cannot issue requests during this task.
5. Local and GB10 tests pass with zero model, endpoint, judge, training, collection, pilot, service-start, or online-write calls.
6. One Loop C incremental review covers only the new execution chain and manifest; every real blocker is fixed and receives a targeted re-check.
7. `PRE_COLLECTION_EXECUTION_BUNDLE.json` has reproducible hashes for every execution artifact and input identity.
8. `EXECUTION_READINESS_RETURN.md` briefly reports bundle hashes, task/reference qualification, incremental review verdict, 54-request budget, one recommended Beijing-time 90-minute window, and exact blocker count.

## Never touch

- Existing `history_collection_offline_v1`, `history_collection_design_v1`, TQ-4/TQ-5, WP-2, frozen papers, raw data, scores, references, old audits, skills, memory, or unrelated dirty workspace files.
- No generated request, service start/restart, pilot, training, online memory write-back, source switch, public release, or commit/push/reset/clean.

## Stop if

- Any file outside `history_collection_execution_v1/` changes.
- An existing test becomes failing.
- Request/token caps, raw overwrite refusal, request-response correspondence, or authorization gating cannot be enforced.
- Runtime identity cannot be established without starting a service or issuing a probe.
- A task/reference requires unapproved semantic adjudication or uses future gold for selection.
- The four-hour execution budget is reached; return actual state and blockers instead of extending.
