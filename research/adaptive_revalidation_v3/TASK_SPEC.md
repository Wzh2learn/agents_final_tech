# Adaptive Revalidation V3 Task Contract

Status: `IMPLEMENTATION_SPEC`
Evidence boundary: `DEV_ONLY_AUTHORED_MECHANISM_FIXTURES`

V3 preserves the nine authored scenario families, five required policies,
fixed repairer, and all V2 partial-success metrics. Policy code executes in a
spawned process and receives only canonical serialized `ActorInput`, returned
evidence, and a client exposing exactly `inspect_dependency`, `inspect_change`,
and `run_target_test`. No fixture, graph, trace, source value, Gold object, or
evaluator export crosses that boundary.

Actor-visible scenario, change, node, and output IDs are stable opaque IDs
derived from frozen ordinal positions. Semantic graph names remain in an
evaluator-only identity map for scoring and upper-bound reporting. Policy
randomness is seeded from opaque actor identity, never semantic labels.

Replay query budgets 0 through 9, compute the cost/action-loss frontier, and
compare greedy with two-step lookahead at matched query cost. Receipt
verification recomputes all result sections and aggregates from source and
frozen inputs, validates test-summary and zero-call accounting fields, and
fails closed on result payload tampering.

No model, network, judge, database, or training calls are permitted. V2 source
and results remain unchanged.
