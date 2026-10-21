# Independent Review: Adaptive Revalidation V2

Date: 2026-10-21
Reviewer identity: independent AI software/scientific review; not human blind
review or domain certification.

Verdicts:

- `SPEC_COMPLIANT = NO`
- `TASK_QUALITY = BLOCK`
- Evidence boundary remains `DEV_ONLY_AUTHORED_MECHANISM_FIXTURES`.

## Critical findings

1. Actor capability isolation is not enforced. `runner.py` passes the full
   `ThinEnvironment` object to policies. Python underscore names do not hide
   `_fixture`, `_graph`, or `_trace`; direct inspection recovered Gold outputs,
   source values and the hidden graph. The package also exports
   `CHECKER_GRAPH`. This invalidates policy comparisons as actor-view
   noninterference evidence.
2. Actor-visible identifiers encode outcome classes. Scenario IDs such as
   `breaking_change`, `benign_change`, `inactive_branch_change` and
   `missing_edge_breaking`, plus `chg_<scenario_id>_<node>` change IDs, expose
   the Gold/family distinction. Random policy seeding also consumes these IDs.

## Important and minor findings

3. Receipt verification checks source hashes and selected fields but does not
   recompute policy results or fully validate the caller-supplied test summary
   and zero-call accounting. The current receipt is reproducible, but the
   verifier is weaker than its evidence claim.
4. Tests do not cover semantic ID opacity or capability isolation.

## Verified positives

- Focused tests pass 17/17 under Python 3.9 and Python 3.11.
- Two policy replays are byte-identical.
- The receipt is reproducible and source hashes verify.
- The 12-node/3-output environment, nine scenario families, five policies,
  metrics, fixed repairer and oracle upper-bound separation are present.

## Required correction before comparison

- Run actor policies in a separate capability boundary with a public
  three-tool RPC/facade; do not hand evaluator objects to policy code.
- Replace scenario/change identifiers with opaque IDs and decouple policy
  randomness from semantic labels.
- Recompute and verify policy aggregates, test summary and accounting fields.
- Add adversarial introspection tests for both critical boundaries.
