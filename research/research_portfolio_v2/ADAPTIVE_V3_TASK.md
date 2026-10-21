# Adaptive Revalidation V3 Task

Status: `IMPLEMENTATION_SPEC`
Date: 2026-10-21

Create `research/adaptive_revalidation_v3/`. Preserve all V2 source and
results. V3 must correct the independent review blockers before any policy
comparison is considered valid.

## Required fixes

1. Capability isolation:
   - Policy code must run outside the evaluator process or behind a strict
     process/RPC boundary.
   - The policy receives only serialized `ActorInput`, returned evidence and a
     three-call public tool client.
   - It must not receive `ThinEnvironment`, `ScenarioFixture`,
     `ExecutionGraph`, traces, source values, Gold objects or package exports
     containing them.
   - Add adversarial introspection tests proving policy code cannot reach
     evaluator internals through the client object.

2. Opaque identifiers:
   - Actor-visible scenario, change, node and output identifiers must be
     stable opaque IDs with no family/answer semantics.
   - Keep an evaluator-only mapping back to semantic graph names.
   - Policy randomness must be seeded independently of semantic labels.
   - Add tests that mutation of hidden labels/Gold does not change serialized
     actor input.

3. Receipt integrity:
   - Recompute policy aggregates and replay results from source/frozen inputs.
   - Verify zero-call accounting, test summary and evidence boundary fields.
   - Fail receipt verification on result payload tampering.

## Scientific comparison

- Preserve the nine scenario families, five required policies, metrics and
  fixed repairer.
- Run budgets 0-9 and identify the cost/action-loss frontier.
- Report whether greedy remains sufficient and whether two-step adds any
  paired benefit at matched query cost.
- Do not use semantic scenario labels in scoring or sampling.
- All initial results remain `DEV_ONLY_AUTHORED_MECHANISM_FIXTURES`.

## Verification

- Python 3.9 and 3.11 focused tests.
- Deterministic replay hashes.
- Independent actor-boundary and identifier-opacity tests.
- No model, network, judge, database or training calls.
- Do not commit the shared dirty worktree.
