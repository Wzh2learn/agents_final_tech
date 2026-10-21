# Current State

> Updated: 2026-10-21 | Scope: research portfolio, Paper E, adaptive
> revalidation, and external-change sources | Runtime: bounded probes complete

## Current Rulings

- Paper E: `NARROW_AND_CONTINUE` as a bounded two-case measurement audit.
- FinRank history/H: `STOP_ON_CURRENT_PANEL`; the corrected full-visibility
  baseline has no comparable residual evidence-selection population and no
  task-matched correction histories.
- MA-CERD correction dated 2026-10-21: the reported resource baseline uses
  `resource_ids` membership, not dependency-edge propagation. The full-release
  transparent summary is `0.881/0.839/0.676/0.648`; the original test summary
  is `0.830/0.835/0.5856/0.5280`. Handling `0.012` is complete allowed-set
  exact matching, while 241/250 predictions are admissible `{defer}` subsets.
  `TOOL_FIRST_WITH_SELECTIVE_ESCALATION` remains a development hypothesis,
  not a verified unique-bottleneck result. See
  [`CORRECTIONS_20261021.md`](../research/ma_cerd_independent_v1/CORRECTIONS_20261021.md).
- Adaptive revalidation V3: spawned-process RPC plus opaque IDs passed 24 tests
  on Python 3.9/3.11 and a 450-episode receipt replay. Unit-cost greedy is
  sufficient at three queries per fixture; two-step lookahead has zero positive
  matched pairs and mean benefit `-0.02037`. Stop further complexity on these
  authored fixtures.
- CodeUpdateArena: the V1 executor is preserved as `INVALID_HARNESS_REPLAY`.
  The zero-request V2 revalidation blocks marker/exit aliases, validates trusted
  test lifecycles, pins the Docker image ID and classifies assertion failures.
  Valid result: base `3/8`, update-info `2/8`, paired difference `-1`; ruling
  `BOUNDED_NEGATIVE_STOP_V2_VALIDATED`.
- Independent new-family confirmation: base `7/8`, update-info `4/8`, paired
  difference `-3`, with 1 versus 4 `test_failure`;
  `BOUNDED_NEGATIVE_REPLICATED_NEW_FAMILIES`.
- External-source review: PyMigBench is the stronger real-commit behavioral
  source; VersiCode is limited to version-change observability because its
  editing rows are highly duplicated and have no behavioral oracle.
- VersiCode observability pilot: BASE `0/8`, prose mapping `8/8`, the same
  mapping as structured fields `7/8`, and target-package probes `5/8` at
  roughly `4x` BASE tokens. This is syntax/name evidence only; one
  prose/structured discordance does not establish representation superiority.
- PyMigBench curation attempted 36 commits and a single dependency-aware
  `thombashi/datetimerange` revival with zero model calls and zero retries.
  No gold behavioral oracle passed: the revival reached `160 passed / 8 failed`
  and exposed missing tzdata/timezone and transitive-version contracts.
- New Goal accounting: `98/2048` attempts and `44,610/10,000,000` tokens.
  Physical HTTP calls are 98; judge, training, paid API and production Memory
  writes are zero.
- Final FinRank development observation: B0 V4 `5/7`; derived plan
  minimal-sufficiency `7/7`, plan precision `5/7`, consume sufficiency `6/7`.
  `ESD_006` is a real sufficient-evidence abstention; `ESD_012` is a
  fixed-budget serialization failure.
- Shared ledger: `747/747` requests and `1,564,176/2,000,000` accounting
  tokens, recomputed from 747 request records. There are 746 `OK` records and
  one retained `FAILED/request_already_exists` event with conservative
  10,240-token accounting. Judge, training, paid API and production Memory
  writes are zero.
- Old ledger remains isolated at `313/316` requests and
  `324,086/2,750,000` tokens.

## Authority

Current research routing is
[`docs/research/README.md`](../docs/research/README.md). The merged return is
[`research/research_direction_sprint_20261020_v1/execution_v2/MERGED_GOAL_RETURN.md`](../research/research_direction_sprint_20261020_v1/execution_v2/MERGED_GOAL_RETURN.md).
Independent scientific review is
[`INDEPENDENT_SCIENCE_REVIEW.md`](../research/research_direction_sprint_20261020_v1/execution_v2/INDEPENDENT_SCIENCE_REVIEW.md).
GB10 authoritative review is
[`GB10_LOOP_C_REVIEW.md`](../research/research_direction_sprint_20261020_v1/execution_v2/GB10_LOOP_C_REVIEW.md).

## Next Execution Step

Use `research/portfolio-integration-v2` as the reviewable integration branch.
Do not rerun VersiCode, CodeUpdateArena or the same authored fixtures. A
behavioral external-change run requires one PyMigBench task with frozen Python,
package locks, tzdata, timezone and tests, plus a gold all-tests-pass result
before model calls. Keep Paper E at `NARROW_AND_CONTINUE`, FinRank at
`STOP_ON_CURRENT_PANEL`, and do not convert bounded observability findings
into general method claims.

Historical state before the 2026-10-19 closeout is preserved in
[`docs/archive/2026-10-19_memory_state_history.md`](../docs/archive/2026-10-19_memory_state_history.md).
The earlier pre-governance snapshot remains at
`memory/archive/STATE_2026-09-22_pre_governance.md`.
