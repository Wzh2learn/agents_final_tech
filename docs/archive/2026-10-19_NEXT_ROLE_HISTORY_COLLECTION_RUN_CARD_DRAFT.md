# Next Role-History Collection Run Card

Status: `SUPERSEDED / PARTIALLY_EXECUTED / NO_FURTHER_RUN_AUTHORIZED`

This draft was partially executed after the owner allowed immediate execution.
The final result is `ROLE_HISTORY_COLLECTION_RETURN.md`. It is retained for the
frozen design and budget-formula correction, not as an active run request.

## Decision to support

Can real history teach a role-binding correction that is not already supplied by
ordinary solved examples or a static rule?

The current evidence cannot answer this question because the only visible
wrong-role failure history failed before role consumption and therefore has no
role-specific correction.

## Bounded collection

- Source: fixed-revision TAT-QA raw files already bound by the accepted source
  qualification; no new dataset or download.
- Eligible tasks: visible row/period/unit/scale differences only. Exclude
  `UNSCORABLE_FOR_REFERENCE`, including hidden-coordinate-only role differences.
- Select six source clusters and two tasks per cluster using a frozen structural
  order before any request. Keep source clusters disjoint from the exploratory
  future panel used for the final comparison.
- Use the qualified `calc` contract and the existing model/runtime identity.
- Maximum 6 history tasks, two attempts per task, with each attempt consisting
  of one plan request and one consume request: 24 requests, 0 retries, single
  concurrency. Use the formula `requests = tasks * attempts * 2`.
- Keep the first attempt's role decision and the first tool result separately.
  If plan/tool failure prevents role consumption, mark
  `ROLE_FEEDBACK_UNAVAILABLE`; do not turn it into a role-correction example.
- Deterministic feedback must state the role mismatch only when the first
  consumed role decision is wrong and the reference is independently
  determinable. The second attempt must be a real request and its action change
  must be recorded.
- A usable negative history requires all of: visible determinable role
  difference, first wrong role decision, successful plan/tool trace, independent
  role-specific feedback, and a later real attempt.

## Frozen gate before H-negative

Run H-negative/random only if the collection yields at least two usable
negative histories across at least two source clusters, with matched and
mismatched role-state controls. Otherwise stop as
`NOT_IDENTIFIABLE_WITH_REAL_HISTORY`; do not use generic plan/tool failures to
fill the role-correction pool.

The H-negative context contains the failed role attempt and deterministic
feedback but no final corrected answer. The random-failure control uses a
length- and schema-matched failure from the opposite role state. Ordinary
solved-example K remains the necessary few-shot control if the gate passes.

## Metrics

Primary: cluster-equal role decision accuracy.

Also record plan validity, tool execution, answer/reference match,
answer/tool-return consistency, `UNKNOWN`/`REFUSE`, false accepts/rejects,
action change after feedback, context length, and accounting cost.

## Budget and authorization boundary

The prior exploratory increase is recorded as 24 requests and 300,000
accounting tokens, taking the cumulative cap from 292/2.45M to 316/2.75M. It
was not consumed by the stopped H-negative/random attempt. The next run must
freeze a new window, run identity, raw root and hash bundle before its first
request. No request is authorized by this draft.

## Stop conditions

- Ambiguous visible role or reference: exclude before model access.
- Fewer than two usable wrong-role corrected histories: stop the mechanism
  candidate.
- Interface/raw/identity failure: technical stop, not an experience result.
- H-negative does not beat K or the matched random-failure control: stop the
  historical-memory claim.
- H-negative improves only plan/format reliability: report interface effect
  only.
