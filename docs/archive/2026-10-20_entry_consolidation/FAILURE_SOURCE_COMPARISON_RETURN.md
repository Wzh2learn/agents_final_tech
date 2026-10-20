# Failure-Source Comparison Return

Status: `HISTORICAL_ATTEMPT / REQUESTS_0 / SUPERSEDED_BY_COLLECTION_RETURN`

This file preserves the earlier window-stop snapshot. After the owner allowed
execution to continue, the separate role-history collection ran and became the
current result. See `ROLE_HISTORY_COLLECTION_RETURN.md` and
`ROLE_HISTORY_COLLECTION_LEDGER_V1.json` for current accounting and status.

## Outcome

The bounded H-negative versus random-failure run did not issue a model request.
The runner stopped before the first request because less than the frozen
120-second per-request timeout remained before the 2026-10-19 22:00
Asia/Shanghai deadline. This is `STOP_REQUEST`, not a model result.

The unused request-budget increase is recorded as 24 additional requests, from
a cumulative cap of 292 to 316. Actual cumulative use remains 292 requests and
310,144 accounting tokens. No retry, fixture, judge, training or
production-memory write was issued.

## Why the planned comparison was not scientifically sufficient

The independent history qualification found:

- The original H01-H12 calculation histories contain no negative or corrective
  trajectories.
- Five same-number history records contain a failed attempt, but no record shows
  a wrong-role decision corrected by role-specific feedback.
- `NR_development_0402_N2` is the only actor-visible, determinable wrong-role
  failed history. Its first failure is `PLAN_OR_TOOL_ERROR / UNKNOWN`; the
  second attempt recovers the interface and role decision. It is not evidence
  of wrong-role correction.
- `NR_development_1582_N2` is `UNSCORABLE_FOR_REFERENCE`: the requested and
  candidate visible roles are identical and differ only by hidden `row_index`.
- `NR_development_2174_N2` is visible and determinable, but both attempts were
  correct and cannot be used as a failed history.

Therefore the available pool cannot establish that negative episodic memory
contains role-correction information absent from ordinary solved examples.
Running the frozen H-negative/random contexts would at most probe interface
recovery from generic calculator failures.

## Offline corrections completed

- The role-task generator now distinguishes visible row/period/unit differences
  from hidden-coordinate-only differences.
- Row-index-only wrong-role cases are marked `UNSCORABLE_FOR_REFERENCE` and are
  excluded from model tasks.
- Six qualification regression tests pass, including row, period and unit
  visible-difference cases and the row-index-only exclusion case.
- The old frozen task package, raw responses, results and ledgers were not
  overwritten.

## Scientific decision

Do not spend the 24-request increase on H-negative/random under the current
history pool. The next bounded collection must be selected for an actual
decision position and must preserve:

1. a first actor role decision before a tool-interface failure can erase it;
2. deterministic role-specific feedback generated independently of actor
   output;
3. a subsequent real attempt whose action change is recorded;
4. visible, reference-determinable requested/candidate role differences.

If that collection produces fewer than two visible wrong-role failures with
role-specific feedback and changed follow-up actions, stop the
negative-episodic-memory mechanism as `NOT_IDENTIFIABLE_WITH_REAL_HISTORY`.

## Frozen comparison bundle

- `freeze_hneg_random_contexts_v2.py`:
  `5ef4236a6557973ed0346605974ce55e9c476f1ae798bc446025baad4de53988`
- `H_NEG_CONTEXTS_V2.json`:
  `f5f5a291228c84c0ae5b2887f2fbe2697a8349375d689db577cd3d1fb791cf33`
- `RANDOM_FAILURE_CONTEXTS_V2.json`:
  `1976274d741a33ce222161172d8e31de44c084a35d8f8fb7326d491cd05f8ffd`
- `SAME_NUMBER_ROLE_H_NEG_PROTOCOL_V2.json`:
  `0f7fc3653bfa3cbaf3958cb7372022126e37c14542d366401f01655ede265690`
- `SAME_NUMBER_ROLE_RANDOM_PROTOCOL_V2.json`:
  `2d9da8a818065564d73111dd1b65a54844de6bbdd925790e758ee1b79cd5ad8`
- `EXPLORATORY_BUDGET_EXPANSION_V1.json`:
  `8e5d279fe69ba661aac3521ac086678a3a3675e6a79e6070d722ef4f187bf16a`

These artifacts document the attempted bounded comparison and its unused
budget. They are not experimental evidence for a historical-memory effect.
