# Loop C Incremental Review: COLLECTION_EXECUTION_READINESS

Task id: `collection-execution-readiness-review-20261018-r1`
Role: Loop C independent reviewer.
Mode: bounded read-only incremental review of the new execution chain only.

Use bash and mechanical recomputation first. Do not modify reviewed files. Do not start services, issue requests, collect data, run pilots, train, or authorize collection. This review is not human semantic gold.

## Scope

Review only `history_collection_execution_v1/` and its pinned input identities:

1. `TASK_REFERENCE_MANIFEST.json`: 12 history, 16 future, 4 development, 3 fixture items; deterministic selection; independent references; actor/hidden isolation.
2. `EXECUTION_PLAN.json`: 54 request slots, 48 history + 6 fixture, fixed 54/600000 budget, retry 0, concurrency 1.
3. `RUNTIME_IDENTITY_SNAPSHOT.json`: model, embedded tokenizer, chat template, server binary, generation policy, and all hash checks.
4. `collection_runner.py` and `execution_core.py`: authorization gate before adapter, strict JSON, safe calculator, budget -> immutable raw -> plan/tool/consume integration.
5. `tests/test_execution_v1.py` and receipts: local/GB10 zero external-call tests.
6. `PRE_COLLECTION_EXECUTION_BUNDLE.json` if present: every hash and blocker status.

## Required checks

- No actor-visible task contains UID, cluster ID, source item ID, gold, rank, or hidden reference.
- Every selected reference is independently recomputed and candidate gold agreement is recorded without using gold for ordering.
- The runner cannot create an adapter or issue a request without a valid authorization file whose bundle hash and Beijing window match.
- Raw response overwrite, crash terminal state, request identity, budget caps, and invalid output paths are enforced.
- The fixture adapter is clearly non-generative and is not presented as a scientific result.
- The proposed window is only a proposal; no request or service start occurred.

## Output

Write one report if permitted:
`research/tatqa_wp0_2026/history_collection_execution_v1/LOOP_C_INCREMENTAL_REVIEW.md`

Return `ACCEPTED`, `CONDITIONAL`, or `REJECTED`.

Report each blocker as `BLOCKER` or `NON_BLOCKING_NOTE`, state whether blocker count is zero, and explicitly state that online collection remains unauthorized. If write access is denied, return the complete report in the task output for Loop D to transcribe.
