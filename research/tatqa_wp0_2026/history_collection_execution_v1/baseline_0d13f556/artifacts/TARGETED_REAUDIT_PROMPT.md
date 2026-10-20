# Loop C Targeted Re-audit: BLOCKER-1 and BLOCKER-2 closure

Task id: `collection-execution-readiness-reaudit-20261018-r1`
Role: Loop C independent reviewer.
Mode: focused read-only re-check of two repaired blockers only.

Do not re-review the entire package or old materials. Use bash and direct execution first. Do not modify files, start services, issue requests, collect data, pilot, train, or authorize collection. This is not human semantic gold.

## Prior report

`LOOP_C_INCREMENTAL_REVIEW.md` is `CONDITIONAL` with exactly two blockers:

- BLOCKER-1: `1/0` raised an uncaught `ZeroDivisionError` and aborted a single-shot run.
- BLOCKER-2: H03/H07/H08/H12 actor projections included source `Change`/`$ CHANGE` columns equal to gold.

## Targeted checks

1. `evaluate_expression("1/0")` and `validate_plan_response` now raise controlled `ValueError`, not `ZeroDivisionError`.
2. A stub adapter emitting `1/0` for every plan completes all 54 request slots; every result records `TOOL_ERROR/INVALID_PLAN`, the consume stage still runs, and no raw directory is orphaned without a result path.
3. Every research task and fixture actor projection is exactly `[row_label, period_early_value, period_late_value]` under headers `[row, period_early_label, period_late_label]`.
4. No actor projection contains `Change`, `$ CHANGE`, `%Change`, a non-target column, gold field, hidden reference, UID, cluster ID, source item ID, or rank.
5. H03/H07/H08/H12 no longer expose their source change cells, while hidden independent references remain unchanged and correct.
6. Re-run the affected tests, verify local and GB10 receipts, and recompute bundle hashes.

## Output

Write one report if permitted:
`research/tatqa_wp0_2026/history_collection_execution_v1/LOOP_C_INCREMENTAL_REAUDIT.md`

Return `ACCEPTED` only if both blockers are closed and no new blocker is found; otherwise return `CONDITIONAL` or `REJECTED`.

State the final blocker count. Non-blocking observations may be recorded separately and must not be inflated into blockers. Explicitly state that online collection remains unauthorized.
