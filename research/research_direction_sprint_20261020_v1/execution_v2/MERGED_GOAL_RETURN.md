# Merged Goal Return

Goals:

- `FINRANK_DEV_HEADROOM_AND_SCOPE_TRANSFER_V1`
- `OPEN_RESEARCH_DISCOVERY_AND_MECHANISM_PROBES_V1`

Status: `COMPLETED_WITH_STOP_AND_CONTINUE_RECOMMENDATIONS`
Date: 2026-10-20, Asia/Shanghai

## Independent Rulings

**Paper E: NARROW_AND_CONTINUE.**

Keep Paper E as a bounded two-case measurement-audit paper. The new evidence
strengthens the motivation that score, observation, and claim contracts control
interpretation. It does not replace the missing prospective independent
application or support a universal audit-method claim.

**Experience reuse: STOP_H_ON_FINRANK_PANEL; CONTINUE_FEEDBACK_CONTRACT_RESEARCH.**

Do not collect task-matched history or run H on the current seven-task panel.
After the corrected full-visibility baseline, the preregistered H gate fails:
there are no comparable residual evidence-selection failures and no complete
task-matched correction histories. Continue with feedback-contract semantics
and move the next empirical question to a task population where applicability
conditions can naturally change.

## What Changed

1. B0 V2's `1/7` was a frozen score, not six clean semantic failures. At least
   one failure was a scorer false negative and one had a reference-scope
   ambiguity.
2. The B0/strong-rule comparison was not same-information. The corrected
   `FULL_VISIBLE_CANDIDATES_AT_PLAN` estimand measures complete-candidate
   selection and consumption, not active evidence acquisition or B0 V2
   reproduction.
3. Literal `%` versus `percent` and arbitrary-pair derivation support were
   deterministic scorer defects. Both are closed with red/green evidence.
4. The corrected baseline makes acquisition headroom unmeasurable in this
   full-candidate estimand. Outcome recall is high, but plan precision remains
   `5/7`; the remaining outcome failures are one sufficient-evidence
   abstention and one structured-output truncation at the unchanged output
   budget.
5. Real-trace feedback analysis shows that exact-match rejects a valid
   alternative sufficient set, while sufficient-set or fact-coverage feedback
   alone can retain answer-invalid or out-of-scope traces. A composite contract
   needs set-valued sufficiency, scope precision, and answer-fact coverage.

## FinRank Evidence

The final development observation is B0 V4:

| Layer | Result |
|---|---:|
| Plan contains a minimal sufficient set (derived set containment) | 7/7 |
| Consume cites a sufficient set | 6/7 |
| Answer/reference match | 5/7 |
| HTTP/raw/tool-chain failures | 0 |
| Plan precision against minimal/optional evidence | 5/7 |

- `ESD_006` selected sufficient evidence but returned `UNKNOWN`. This is a real
  abstention non-success.
- `ESD_012` selected the planned IDs, but consume still hit
  `finish_reason=length` at `completion_tokens=256` and emitted invalid
  truncated JSON after the minified-output instruction.
- The deterministic strong rule is a same-information selection control, not a
  compute-equivalent upper bound.
- B0 V3 and B0 V4 selected identical evidence IDs. The visibility-driven
  selection change occurred in V2 -> V3; V4 is confirmatory, not a second
  independent selection measurement.
- Plan minimal-sufficiency `7/7` is derived by set containment against
  `REFERENCES_V3.json`; the runner does not machine-attest that metric. Plan
  precision `5/7` shows residual over-selection on ESD_002 and ESD_010.

Version separation is preserved:

- B0 V3 frozen score: `4/7`.
- B0 V3 post-hoc unit correction: `5/7`.
- B0 V3 post-hoc full checker V3: `5/7`.
- B0 V4 formal development observation: `5/7`.

## Open Research Evidence

- Lexical lookup was the best realizable acquisition policy at budgets 1/2/3.
- The tested score-disagreement policy is stopped.
- Exact-match-only feedback is stopped.
- Unqualified minimal-set or fact-coverage retention is stopped.
- Continue studying composite feedback semantics, especially alternate
  sufficient sets plus scope precision.

These are controlled finite-panel or post-hoc mechanism results. They do not
establish experience-learning benefit.

## Strongest Paper E Claim

> A reproducible measurement audit can separate score-contract sensitivity from
> decision stability in a real evidence-ranking benchmark, while exposing a
> residual reproduction gap without overstating its cause or the generality of
> the review procedure.

## Next Research Action

Build one small, natural condition-change task population in which:

- the same local experience is valid before a rule/scope change and must be
  revised after it;
- alternate sufficient evidence sets occur naturally;
- out-of-scope additions can be distinguished from valid redundancy;
- the primary comparison is composite feedback versus exact-match and
  sufficient-set-only feedback.

The first gate is task/reference feasibility and a frozen development protocol,
not another FinRank history run. Stop if the task cannot establish independent
references or if ordinary examples/rules explain all behavior changes.

The protocol must score sufficiency and scope precision separately at both
plan and consume time, so recall and over-selection are not collapsed.

## Accounting

- New generation: `56/192` requests.
- Accounting tokens: `458,650/2,000,000`.
- Retries: `0`.
- Judge, training, paid research API, history, pilot, and production Memory
  writes: `0`.
- Old ledger remains unchanged at `313/316` requests and
  `324,086/2,750,000` tokens.

## Verification

GB10 is authoritative:

- Loop A: `PASS`; bundle `14/14`, C3 `13/13`, C2 historical `5/5`,
  open-probe `4/4`, real-trace feedback `5/5`, direct recomputation `23/23`.
- Loop C: `ADOPT_MERGED_RETURN_WITH_TWO_CORRECTIONS`; no data/hash/ledger
  blocker.
- GB10 files: `GB10_LOOP_A_RETURN.md`, `GB10_LOOP_A_VERIFICATION.json`,
  `GB10_LOOP_C_REVIEW.md`.

Local supporting checks:

- C3 verification: `13/13 PASS` under project Python 3.11.
- C2 historical verification: `5/5`, with source-snapshot limitation.
- Open probe regression: `4/4 PASS`.
- Real-trace feedback regression: `5/5 PASS`.
- Frozen C3 FIX1 bundle:
  `7bb3564cc8a30bac8d81f158232d68c8e3fbdf59247edbc5cd963c47deb893e7`.

Independent review:
`INDEPENDENT_SCIENCE_REVIEW.md` and `GB10_LOOP_C_REVIEW.md`.

## Remaining Limits

- `ESD_001` has a question/reference ambiguity over whether numeric values are
  required.
- Literal numeric support still binds values more strongly than complete source
  label/unit/period provenance.
- Plan minimal-sufficiency `7/7` is derived rather than runner-attested, and
  plan precision is `5/7`.
- Derivation-check closure is fixture-level because ESD_006 returned
  `UNKNOWN`.
- C2 cannot be reproduced exactly from the current source after C3 drift.
- The panel has seven development tasks, one source component, and AI-assisted
  references with `human_confirmed=false`.

## Owner Decision

None is required for the next design and offline feasibility work. A later
confirmatory run that changes the model, task population, or request budget
requires a separate decision.
