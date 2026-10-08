# Spend Budget Pattern

> Status: active governance reference | Adapted for JinRongAgents from `skills-loop-engineering`.
> A budget is a hard ceiling with escalation, not a target or a substitute for convergence.

## Purpose

Long agent loops, retries, and fan-out can consume unbounded tokens, money, wall-clock time, or
tool calls. The budget unit must be chosen before execution and shared across every participant.

## Required Budget Record

| Field | Requirement |
|---|---|
| Scope | Session, run, dispatch, or fan-out family |
| Unit | Calls, tokens, cost, wall-clock, GPU-hours, output bytes, or log bytes |
| Ceiling | Exact approved value; no implicit default |
| Shared pool | Main loop and every sub-agent draw from one counter |
| Warning point | Frozen pre-run threshold for graceful wrap-up |
| Stop | Exact condition that aborts further work |
| Recovery | Resume marker, retained partial artifacts, and escalation owner |

## Rules

1. Count actual usage, not only planned upper bounds.
2. Shared fan-out uses one pool. Per-agent copies of the same budget multiply spend silently.
3. Retries and failed calls count against the same pool.
4. Exhaustion is a hard stop followed by human escalation; do not quietly degrade or retry forever.
5. Preserve partial results and disclose work that was dropped or not run.
6. The ceiling is a backstop. Do not spend to the cap because capacity remains.
7. Threshold changes require a new frozen config before execution, not after observing results.

## Reporting Contract

Every run reports `planned ceiling`, `actual usage`, `remaining`, `stopped/not stopped`, and
`coverage dropped`. A partial run is not reported as complete.

## Related

- [`EXTERNAL_CALL_RELIABILITY_PATTERN.md`](EXTERNAL_CALL_RELIABILITY_PATTERN.md) - retries consume the shared budget
- [`FOUR_CONCEPT_SEPARATION_PATTERN.md`](FOUR_CONCEPT_SEPARATION_PATTERN.md) - execution does not prove completion
- [`TIERED_EVAL_PATTERN.md`](TIERED_EVAL_PATTERN.md) - disclose verification scope and cost tier
- [`../../../skills/context-budget/`](../../../skills/context-budget/) - context-window budget
