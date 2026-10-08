# External Call Reliability Pattern

> Status: active governance reference | Adapted for JinRongAgents from `skills-loop-engineering`.
> Transport failures, logic failures, and side effects require different retry policies.

## Failure Classes

| Class | Examples | Policy |
|---|---|---|
| Transport | timeout, connection reset, 429, transient 5xx | bounded exponential backoff with jitter |
| Logic | malformed or unparseable response | one controlled parse retry where the contract permits |
| Client error | ordinary 4xx | do not retry; fix request or stop |
| Sustained outage | repeated transport failures | open circuit breaker and escalate |
| Side-effect timeout | write may have succeeded upstream | retry only with idempotency key or local dedup ledger |

## Required Design

1. Pre-register maximum attempts, backoff base, jitter, total wall-clock, and spend budget.
2. Separate transport retries from structured-output or schema retries.
3. Use a shared circuit breaker per endpoint or provider.
4. Give side-effecting requests a client-generated idempotency key. If the provider cannot dedupe,
   keep a local request ledger or make the consumer idempotent.
5. Count every retry against [`SPEND_BUDGET_PATTERN.md`](SPEND_BUDGET_PATTERN.md).
6. Preserve failed responses and null results; do not synthesize a success after retry exhaustion.

## Stop Conditions

Stop and escalate when the breaker opens, the retry/spend ceiling is reached, the response changes
contract shape, authentication is ambiguous, or retry should repeat the failure with increasing
impact.

## Reporting Contract

Record endpoint class, request purpose, attempt count, final status, breaker state, idempotency
method, time, and spend. Do not log authorization values or full private payloads.

## Related

- [`SPEND_BUDGET_PATTERN.md`](SPEND_BUDGET_PATTERN.md) - shared hard ceiling
- [`RUNTIME_REDACTION_PATTERN.md`](RUNTIME_REDACTION_PATTERN.md) - redact before external egress
- [`../../../skills/structured-output/`](../../../skills/structured-output/) - bounded parse retry
- [`../../../skills/data-sync/`](../../../skills/data-sync/) - resumable transfer discipline
