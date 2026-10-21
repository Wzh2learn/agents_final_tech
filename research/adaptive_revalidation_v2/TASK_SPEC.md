# Adaptive Revalidation Thin Environment Task

Status: `IMPLEMENTATION_SPEC`
Evidence boundary: all initial outputs are
`DEV_ONLY_AUTHORED_MECHANISM_FIXTURES`.

Implement a small deterministic environment shared by candidates A and B.
Do not make model calls and do not claim external-task performance.

## Required environment

- 8 to 12 executable nodes and 2 to 4 outputs.
- At least one change-before success snapshot and one post-change state.
- Public tools:
  `inspect_dependency`, `inspect_change`, and `run_target_test`.
- Actor-visible input must exclude Gold, hidden checker graph, hidden trace,
  and values derived from them.
- A fixed repairer consumes only the evidence returned by a query policy.

## Required scenario families

- breaking and benign changes;
- inactive branch changes;
- multiple valid supporting evidence sets;
- source changes with value cancellation;
- missing or noisy dependency edges.

## Required policies

- no checking;
- random checking;
- unit-cost greedy information gain;
- two-step lookahead;
- full recomputation.

Oracle graph and full trace may be reported only as separate upper bounds.

## Required metrics

- final action loss;
- repair loss;
- query cost;
- recomputation cost;
- missed invalidation;
- over-invalidation;
- regression rate;
- completion and abstention.

Do not create an all-or-nothing score unless the environment naturally
requires it. Preserve partial success and near-additive cases.

## Deliverables

- typed Python implementation under `research/adaptive_revalidation_v2/`;
- deterministic tests;
- frozen development fixtures;
- JSON result receipt with source hashes;
- concise result note that clearly states DEV_ONLY status.
