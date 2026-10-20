# GB10 Loop A Bounded Real Model Task

Task ID: `gb10-condition-change-real-model-tier1-a`

Read and obey:
`condition_change_feedback_v1/BOUNDED_REAL_MODEL_V1_PREREGISTRATION.md`.

Implement a focused runner in `condition_change_feedback_v1/` and execute Tier
1 exactly once. Do not run Tier 2, feedback-revision arms, judge, training,
network calls other than the 26 model requests, or production Memory writes.

Requirements:

1. Verify the pinned model/server/template and GB10 endpoint before the first
   request.
2. Freeze the runner, prompt, schema, task order, and run ID before execution.
3. Record one immutable request/response pair per task in a unique raw root.
4. Settle every request in the shared generation ledger before moving on.
5. Validate submission JSON strictly; never repair or coerce output.
6. Score all three feedback contracts deterministically from
   `REFERENCE_TASKS_V2.json`.
7. Execute the frozen CC013 clean/alternate probe offline before the model run.
8. Preserve V1/V2 inputs and all previous results.

Write only inside `condition_change_feedback_v1/` plus:

- `execution_v2/CONDITION_CHANGE_REAL_MODEL_RETURN.md`
- `execution_v2/CONDITION_CHANGE_REAL_MODEL_VERIFICATION.json`

Do not overwrite `GB10_LOOP_A_*` or `CONDITION_CHANGE_LOOP_A_*`. Report exact
requests, tokens, results, failures, hashes, and stop state.
