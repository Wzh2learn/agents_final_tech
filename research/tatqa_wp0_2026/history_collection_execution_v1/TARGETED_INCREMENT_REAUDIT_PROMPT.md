# Loop C Targeted Review: Authorized Execution Increments

Task id: `authorized-collection-increment-review-20261018-r1`
Role: Loop C independent reviewer.
Mode: read-only review of exactly two authorized increments.

Use direct execution and mechanical comparison first. Do not review unrelated package areas or old materials. Do not issue online requests, start/restart services, collect data, pilot, train, or authorize the run. This is not human semantic gold.

## Checks

1. Simulate window crossing. Verify the check occurs before every request, a request is not sent unless the full timeout fits before expiry, expiry stops new requests, and partial request/result evidence is saved.
2. Fail a fixture qualification case. Verify exactly six fixture requests occur and history request count is zero.
3. Pass fixtures. Verify fixture requests are first, history follows, total request cap remains 54, and token/retry/concurrency limits remain 600000/0/1.
4. Compare `baseline_0d13f556/artifacts/TASK_REFERENCE_MANIFEST.json` with `TASK_REFERENCE_MANIFEST.json` and `MANIFEST_COMPARISON.json`; verify tasks, references, model, generation parameters including `max_tokens=256`, prompts, source split, and sample counts are unchanged.

## Output

Write one report if permitted:
`research/tatqa_wp0_2026/history_collection_execution_v1/LOOP_C_AUTHORIZED_INCREMENT_REAUDIT.md`

Return `ACCEPTED`, `CONDITIONAL`, or `REJECTED`, with blocker count. Check only these increments. Explicitly state that online collection remains unauthorized until a separately bound authorization file is used.
