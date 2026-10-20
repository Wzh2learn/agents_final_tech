# GB10 Loop C Incremental Science Review

Task ID: `gb10-finrank-c3-review-20261020-c`

Materialization note: GB10 Loop C produced this review and `rc=0`. Its direct
file write was blocked by the Claude tool permission gate, so Loop D copied the
completed review from the immutable launcher log without changing its ruling.

Evidence discipline: `0` model requests, `0` judge/training/network calls, `0`
service probes. All verification was deterministic recomputation from stored
artifacts. No existing report, raw result, or frozen reference was modified.

## Executive Ruling

`ADOPT_MERGED_RETURN_WITH_TWO_CORRECTIONS`

The merged return's conclusions hold. Two claims need correction before this
package is quoted again.

## 1. Literal-Percent And Explicit-Derivation Blockers

Status: `CLOSED_WITH_ONE_QUALIFICATION`.

`FACT`: `C3_UNIT_RED.json` records the original false negative and
`C3_UNIT_GREEN.json` records the corrected match. `FACT`: B0 V4 ESD_004 stores
`unit: "%"` with values `8.7` and `20.8`, and both atoms match. `FACT`:
ESD_004 is the sole V3-to-post-hoc outcome change, from `4/7` to `5/7`.

`FACT`: `C3_DERIVATION_RED.json` records the arbitrary-pair false support.
`C3_DERIVATION_GREEN.json` rejects that pair because an operand is absent and
accepts the explicit revenue/cost formula. `FACT`: both derivation receipts
record zero generation requests.

`FACT`: the only derivation-requiring live task, ESD_006, returned `UNKNOWN`
with no facts or derivation checks. The derivation path was not exercised on a
live model output in B0 V4. The red fixture is one-sided.

`UNVERIFIED`: checker behavior on a live task that emits derived facts.

`FACT`: literal numeric support is value-based rather than fully bound to the
source label, unit, and period. This residual limitation is non-blocking for
the arbitrary-pair defect but blocks stronger provenance claims.

## 2. Do The B0 V4 Counts Support The Root Causes?

Status: `PARTIALLY`.

`FACT`: the counts are accurate and independently reproduced:

| Run | Score | Plan sufficiency | Consume sufficiency | Plan precision |
|---|---:|---:|---:|---:|
| B0 V2 | 1/7 | 3/7 | 3/7 | 0/7 |
| B0 V3 equal visibility | 4/7 | 7/7 | 6/7 | 5/7 |
| B0 V3 post-hoc V3 | 5/7 | 7/7 | 6/7 | 5/7 |
| B0 V4 formal | 5/7 | 7/7 | 6/7 | 5/7 |

`FACT`: B0 V3 and B0 V4 have identical plan ID sets and identical consume
`used_candidate_ids` for all seven tasks.

`INFERENCE`:

1. The visibility confound is supported by B0 V2 -> V3, not by V4. Plan
   sufficiency rises from `3/7` to `7/7` when candidate text becomes visible.
2. The literal-percent defect is supported by the ESD_004-only `4/7 -> 5/7`
   post-hoc correction.
3. The minified-output defect is diagnosed but not remediated. ESD_012 fails
   consume in both V3 and V4.
4. The ESD_006 V1 reference over-constraint is validated, but correcting it
   does not make ESD_006 successful; the live failure is abstention.

`FACT`: ESD_012's truncated payload is semantically complete: it contains the
used IDs and all four requested facts. It nevertheless fails strict JSON and
ends at `completion_tokens=256`. `INFERENCE`: this is a serialization-budget
failure, not a selection or knowledge failure. The frozen contract forbids a
token-budget change, so this blocker cannot be closed inside C3.

`FACT`: plan precision is `5/7`. ESD_002 includes wrong-period `cand_004`;
ESD_010 includes unsupported `cand_005`. Both succeed only because consume
drops those extras.

`INFERENCE`: "evidence selection is no longer the main gap" overstates the
evidence. The defensible statement is that plan recall is saturated at `7/7`
while precision remains `5/7`; this panel cannot separate deliberate broad
selection from genuine selection skill.

## 3. FULL_VISIBLE Estimand

Status: `CORRECTLY_LIMITED_WITH_TWO_WORDING_CAUTIONS`.

`FACT`: the actor and run cards name
`COMPLETE_CANDIDATE_SELECTION_AND_CONSUMPTION` and explicitly exclude active
acquisition and B0 V2 reproduction. The strong rule is a same-information
control, not a compute-equivalent bound.

`INFERENCE`: the corrected baseline makes acquisition headroom unmeasurable in
this design; it does not show that acquisition headroom is absent. The separate
open-probe study retains an oracle gap. V4 replicates V3 selection and is not
an independent selection measurement.

## 4. H Gate

Status: `CORRECTLY_FAILED`.

`FACT`: H requires at least two comparable residual selection failures and at
least two complete task-matched histories with executed correction chains.
`FACT`: the outcome residuals are ESD_006 abstention and ESD_012 serialization.
`FACT`: no executed correction histories exist; real-trace feedback is post-hoc
and unavailable to the actor.

`INFERENCE`: the history condition fails independently, and the stop clause
also triggers. H must remain stopped. Do not convert ESD_006 or ESD_012 into
history-learning cases.

`INFERENCE`: plan-level over-selection remains real, but it does not rescue H.
It instead strengthens the redirect to feedback contracts that score both
sufficiency and scope precision.

## 5. Paper E

Status: `NARROW_AND_CONTINUE_CONFIRMED`.

`FACT`: the external audit retains a bounded two-case measurement-audit claim
and the need for a prospectively frozen independent application. All new
evidence is development-only, post-hoc, or finite-panel, with
`human_confirmed=false`.

`INFERENCE`: the new evidence reinforces score, claim, and observation contract
boundaries. It does not supply the missing prospective application or justify
stronger benchmark/model claims.

## 6. GB10 Loop A

Status: `NO_BLOCKER_WITH_ONE_METRIC_LABEL_CORRECTION`.

`FACT`: Loop A passed 14/14 bundle hashes, 13/13 C3 checks, 5/5 C2 historical
checks, 4/4 and 5/5 unit tests, and 23/23 direct recomputation checks. Its
artifact hashes and ledger totals match independent recomputation.

`FACT`: `GB10_LOOP_A_VERIFICATION.json` labels plan-contract and tool validity
as `plan_sufficient`. The runner does not machine-attest minimal-set
sufficiency at plan time. Direct set containment against `REFERENCES_V3.json`
does establish the substantive `7/7`, but it is derived rather than attested.

`INFERENCE`: no data, hash, count, or ledger discrepancy exists. Report plan
minimal-sufficiency `7/7` as derived and report plan precision `5/7`.

## Real Blockers

1. Clean structured-output baseline: ESD_012 remains truncated under the fixed
   token budget.
2. H preconditions: no qualifying residual population and no executed
   task-matched correction histories.
3. Stronger Paper E validation: no prospectively frozen independent
   application.

## Non-Blocking Limits

1. ESD_001 question/reference numeric ambiguity.
2. Value-based rather than provenance-bound literal support.
3. Derivation closure is fixture-level only.
4. The derivation red fixture tests one direction.
5. Plan sufficiency is derived; plan precision is `5/7`.
6. V3 and V4 selections are identical.
7. C2 lacks an exact source snapshot.
8. Seven development tasks, one source component, and
   `human_confirmed=false`.

## Final Ruling

`ADOPT_MERGED_RETURN_WITH_TWO_CORRECTIONS`

Close the literal-percent and arbitrary-derivation blockers. Keep serialization,
H-collection, and Paper-E-validation blockers open. Stop H on this panel,
preserve the FULL_VISIBLE limit, and continue Paper E under its bounded
two-case ruling. Attribute the plan-sufficiency gain to B0 V2 -> V3, and record
plan minimal-sufficiency `7/7` as derived alongside plan precision `5/7`.

## Single Next Research Action

Build the small natural condition-change task population specified in the
merged return. Its frozen protocol must score sufficiency and scope precision
at both plan and consume time, so recall and over-selection become separately
measurable. The first gate is task/reference feasibility and protocol
freeze, not another FinRank history run. Stop if independent references cannot
be established or ordinary examples/rules explain all behavior changes.
