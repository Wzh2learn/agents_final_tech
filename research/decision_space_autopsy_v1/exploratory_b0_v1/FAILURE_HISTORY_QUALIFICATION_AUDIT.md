# Failure History Qualification Audit

Status: `COMPLETE_READ_ONLY / MODEL_REQUESTS_0`

Audit time: `2026-10-19T21:52:44+08:00`

## Scope and decision rule

This audit separates four things that must not be conflated:

1. `COMPLETE_FAILURE`: the actor produced an attempt, the tool path produced a
   result or deterministic error, the consume response exists, and the attempt
   was classified. Correctness is not part of record completeness.
2. `MISSING_RECORD`: a required attempt, plan status, tool result, consume
   result, or attempt identity is absent.
3. `VISIBLE_DECIDABLE_WRONG_ROLE`: the expected decision is `WRONG_ROLE`, and
   the actor-visible `requested_role` and `candidate_citation` differ in their
   row or period labels. Hidden row or period indices cannot make a role
   decidable.
4. `ROLE_CORRECTION`: a completed role decision was wrong, deterministic role
   feedback was issued, and a later completed attempt changed that role
   decision to the reference decision. A plan/tool recovery is not a role
   correction.

The original 12-item real-history pool and the six-item same-number role
history collection are evaluated separately. No B0 result is treated as
historical experience.

## Primary conclusion

There are **zero true role-correction trajectories**.

There is **one** actor-visible, decidable wrong-role task with a complete failed
attempt: `NR_development_0402_N2`. Its failure is a plan/tool failure
(`PLAN_OR_TOOL_ERROR`, first decision `UNKNOWN`), not a wrong-role decision
being corrected. It is therefore suitable only as a negative interface/tool
recovery signature, not as evidence of role-error correction.

There are **not at least two** actor-visible, decidable wrong-role failed
histories. The proposed H-negative/random mechanism is not sufficiently
supported by the current history material:

- required minimum: 2 qualified visible/decidable wrong-role failed histories;
- observed count: 1;
- observed true role-decision failures with feedback and follow-up: 0.

This is `INSUFFICIENT_FOR_H_NEGATIVE_RANDOM`, not a claim that negative
experience can never help.

## Original 12 real-history experiences

Source: `history_collection_execution_v1/pilot_prep_v1/EXPERIENCE_POOL.json`
(`H01`-`H12`).

All 24 attempts have the result-level shape
`plan -> tool_result -> consume -> feedback_category`. Every attempt has a
valid `calc` plan, tool status `OK`, consume status `ANSWER`, matching
`calc_value/delta_target`, and matching recomputed reference. The associated
`COLLECTION_RETURN.md` reports both attempts successful for all 12.

| class | count | IDs | permitted mechanism use |
|---|---:|---|---|
| stable successful trajectories | 12 | H01-H12 | positive solved-example or positive behavior references |
| failed trajectories | 0 | none | none |
| correction trajectories | 0 | none | none |
| missing result-level records | 0 | none | none |

The `context.lesson` field is identical hard-coded prose on all 12 items. It
was not derived from an observed correction and must not be represented as
empirical feedback or a learned lesson. The attempts themselves may be retained
as real positive execution traces; the `lesson` text is not qualified evidence.

These 12 items cannot populate a negative-only or correction-based H arm.

## Same-number role history collection

Source: `exploratory_b0_v1/HISTORY_COLLECTION_RESULT.json`, task definitions in
`decision_space_autopsy_v1/SAME_NUMBER_ROLE_TASKS_DRAFT.json`, and the frozen
history protocol.

The run contains 6 trajectories and 12 attempts. All 12 attempts have result
records containing plan status or plan payload, deterministic tool result,
consume payload, classification fields, and attempt number. Five first
attempts and one second attempt are non-success. None is a missing record at
this result level.

| task ID | actor-visible role relation | attempt 1 | feedback | attempt 2 | qualification |
|---|---|---|---|---|---|
| `NR_development_0402_N2` | different row, same period | complete plan/tool failure; `UNKNOWN`; `NON_SUCCESS` | `PLAN_OR_TOOL_ERROR` | valid `calc`; `WRONG_ROLE`; `SUCCESS` | one qualified visible/decidable wrong-role failed task; interface recovery only |
| `NR_development_0402_P1` | same row and period | complete plan/tool failure; `UNKNOWN`; `NON_SUCCESS` | `PLAN_OR_TOOL_ERROR` | valid `calc`; `SUPPORTED`; `SUCCESS` | positive task recovered from interface failure; not role-negative |
| `NR_development_1582_N2` | identical visible row and period | complete plan/tool failure; `UNKNOWN`; `NON_SUCCESS` | `PLAN_OR_TOOL_ERROR` | valid `calc`; `SUPPORTED`; `NON_SUCCESS` | complete failure record, but reference is unscorable from visible evidence |
| `NR_development_1582_P1` | same row and period | complete plan/tool failure; `UNKNOWN`; `NON_SUCCESS` | `PLAN_OR_TOOL_ERROR` | valid `calc`; `SUPPORTED`; `SUCCESS` | positive task recovered from interface failure; not role-negative |
| `NR_development_2174_N2` | same row, different period | valid `calc`; `WRONG_ROLE`; `SUCCESS` | `SUCCESS` | valid `calc`; `WRONG_ROLE`; `SUCCESS` | visible/decidable wrong-role solve, but no failure or correction |
| `NR_development_2174_P1` | same row and period | complete plan/tool failure; `UNKNOWN`; `NON_SUCCESS` | `PLAN_OR_TOOL_ERROR` | valid `calc`; `SUPPORTED`; `SUCCESS` | positive task recovered from interface failure; not role-negative |

The `feedback` column is the stored feedback after attempt 1. The result file
does not store a separate feedback object after attempt 2; later success is
evidenced by the attempt-2 plan/tool/consume classification, not by an invented
second feedback record.

### Exact evidence fields

`NR_development_0402_N2`:

- visible requested role: `Cash and cash equivalents @ Group 2019`;
- visible candidate citation: `Cash including Group’s share of joint ventures
  @ Group 2019`;
- hidden target/candidate row indices: `2/8`; this difference is not needed to
  decide the task;
- expected decision: `WRONG_ROLE`;
- first plan/tool/consume: `INVALID_PLAN/TOOL_ERROR -> UNKNOWN`;
- feedback category: `PLAN_OR_TOOL_ERROR`;
- second plan/tool/consume: `calc("-223.0")/OK -> WRONG_ROLE`;
- second outcome: `SUCCESS`.

`NR_development_1582_N2`:

- visible requested and candidate role both: `Adjusted operating costs1 @
  2019`;
- hidden target/candidate row indices: `4/9`;
- expected decision: `WRONG_ROLE`;
- first plan/tool/consume: `INVALID_PLAN/TOOL_ERROR -> UNKNOWN`;
- feedback category: `PLAN_OR_TOOL_ERROR`;
- second plan/tool/consume: `calc("275.7")/OK -> SUPPORTED`;
- second outcome: `NON_SUCCESS`.

The expected `WRONG_ROLE` cannot be inferred from the actor-visible evidence.
The differing hidden `row_index` is hidden reference leakage into task
construction. Classify this item as `UNSCORABLE_FOR_REFERENCE` or
`REQUIRES_HUMAN_SEMANTIC_ADJUDICATION`; do not use it as a wrong-role
negative, do not call `SUPPORTED` a model role failure, and do not use it to
construct a correction story.

`NR_development_2174_N2`:

- visible requested role: `Non-deductible and other items @ 2019`;
- visible candidate citation: `Non-deductible and other items @ 2018`;
- hidden target/candidate period indices: `1/2`;
- expected decision: `WRONG_ROLE`;
- both attempts: valid `calc("3.4 - 3.4")`, tool `OK`, consume `WRONG_ROLE`,
  outcome `SUCCESS`.

This is actor-visible and decidable, but both attempts were correct. It can be
a solved wrong-role example or control, not a failure or correction history.

## Counts and H-negative/random eligibility

| qualification question | result |
|---|---:|
| original pool negative/correction trajectories | 0 / 12 |
| same-number result-level missing records | 0 / 6 |
| same-number trajectories with a complete non-success attempt | 5 / 6 |
| same-number `ROLE_DECISION_ERROR` feedback records | 0 / 6 |
| visible/decidable wrong-role tasks | 2 / 6 (`0402_N2`, `2174_N2`) |
| visible/decidable wrong-role tasks with a failed attempt | 1 / 6 (`0402_N2`) |
| visible/decidable wrong-role decision failures with feedback and follow-up | 0 / 6 |
| minimum required for H-negative/random | 2 |

### Use boundary

- `NR_development_0402_N2` may be used only as a negative **interface/tool
  recovery** history if the hypothesis is explicitly about plan validity and
  tool consumption.
- `NR_development_2174_N2` may be used as a positive solved-role example or
  matched control.
- `NR_development_1582_N2` may be used only as a task-construction/reference
  failure fixture.
- `NR_development_0402_P1`, `NR_development_1582_P1`, and
  `NR_development_2174_P1` may be used as positive recovery examples, not
  wrong-role negatives.
- H-negative/random must not run from this pool if it requires at least two
  visible/decidable wrong-role failure histories. Do not relabel the
  `1582_N2` ambiguity or the `2174_N2` success to meet the count.

## Raw-chain limitation

The runner records request payloads and responses through
`ImmutableRawStore.begin_request` and `persist_response`, and the result budget
reports 24 requests with no stop reason. The raw root recorded in the
authorization is not accessible from this Windows audit environment, so this
audit verifies result-level completeness and the runner's identity-preserving
write path, but does not independently re-read the request/response directories.

Before using any selected negative in a future online arm, raw request/response
identity should be checked on the host that owns the raw root. This limitation
does not turn a present failure record into a missing record, but it prevents
claiming a newly reverified raw chain from this read-only pass.

## Final disposition

`NOT_ENOUGH_QUALIFIED_WRONG_ROLE_FAILURE_HISTORIES_FOR_H_NEGATIVE_RANDOM`

Do not run H-negative/random from the current material under a two-history
minimum. Preserve the valid boundary result: the existing collection contains
real complete failures and interface recoveries, but no observed role-error
feedback correction and only one visible/decidable wrong-role failed task.
