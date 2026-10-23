# Loop D Research Sprint Return V5

Date: 2026-10-23, Asia/Shanghai

Status: `EVIDENCE_EXIT_TWO_G3_CANDIDATES_WITH_DISTINCT_MEASUREMENTS`

## 1. Starting Point And Plan

This sprint continued from `df58512a7a84251446d7377eee5f71a405aa6544` without
resetting prior work. The execution plan is in `EXECUTION_PLAN.md`. V4's
426 calls / 3,050,185 tokens are the starting ledger; no historical ledger was
reset.

## 2. Paper E

`READY_FOR_OWNER_SUBMISSION_HANDOFF`.

The two-case manuscript remains unchanged. The live ICAART 2027 check records
Regular Paper as the intended route, second-stage deadline 2026-10-29 AoE
(extended), notification 2026-12-04, and camera-ready/registration 2026-12-18.
The submission link reaches PRIMORIS while the CFP body still says submission
will be available soon; this conflict is explicitly marked for a live login
recheck immediately before upload.

The handoff contains the final PDF identity, submission-field draft, author and
BUPT placeholders, AI disclosure wording, artifact plan, fee/presentation
scenarios and patent/school-recognition questions. No submission, payment,
signature, author email or public release was performed.

## 3. G2 Measurement Repair

The three V4 counterexamples were reviewed against raw answers, selected
evidence and hidden references:

- `0f806fbb`: the answer incorrectly said derivatives were not being practiced
  while the evidence showed active options learning. The old judge accepted it.
- `0af76ce2`: a concrete low-effort social plan was reasonable; the old gate
  rejected it only because `safe_unknown` was mixed with cautious qualification.
- `17c4192e`: the answer continued to treat self-employment as current. The old
  judge accepted it; the gate rejected it for the wrong reason.

The V5 contract separates grounded completion, stale/unsafe advice, reasonable
UNKNOWN/clarification, unnecessary refusal and interface failure. It explicitly
allows multiple valid actions, distinguishes historical facts from suggestions,
and does not make UNKNOWN automatically successful or failing.

Calibration evidence:

- Initial calibration with incomplete evidence excerpts: 6/10, `STOP`.
- Evidence-complete V2 calibration: 9/10, `FLAG_AND_CONTINUE`.
- The one remaining error is fixed `No.` under an action prompt being classified
  as unnecessary refusal rather than interface failure. It is recorded as a
  judge boundary error and does not silently alter the research labels.

## 4. G2 Mechanism Experiment

Retrieval intervention:

- Original BM25 top-5 is the strongest transparent baseline over 400 dim1 and
  dim3 items. `BOTH` coverage is 0.430/0.435 respectively.
- User-only change expansion, attribute-recency and two-pass change retrieval
  all reduce coverage and do not save context. The simple query expansions are
  stopped.

Fixed evidence and fixed recovered state:

- Eight development UIDs used one BM25 top-5 evidence package, one recovered
  bundle, then separate fact and action answers from the same bundle.
- Plain fact bundle: fact completion 2/8, action completion 1/8.
- Evidence-decision bundle: fact completion 3/8, action completion 1/8.
- After contract validation, both action arms have 7/8 reasonable
  UNKNOWN/clarification or refusal/unsafe outcomes. The fact gain is one case,
  not a stable method effect.
- Independent review therefore rejects automatic state-to-action transfer and
  does not establish a decision-bundle advantage.

End-to-end top-5 action review:

- Independent review covers all 32 outputs from 16 UIDs and two representations.
- The aggregate categories are `one-call 2 grounded / 9 stale-unsafe / 4
  reasonable / 1 unnecessary refusal / 0 interface` and `two-stage 3 grounded /
  0 stale-unsafe / 9 reasonable / 3 unnecessary refusal / 1 interface`.
- The two-stage form reduces unsafe/stale answers but moves more cases into
  abstention or unnecessary refusal. This is a safety/coverage tradeoff, not an
  action accuracy win.

The mechanism decision is `CONTINUE_NARROWED_DEVELOPMENT_ONLY`: one
information-matched held-out test is justified only if it improves safe action
completion at equal or lower unsafe/refusal cost. Otherwise stop this mechanism.

## 5. G3 Independent Candidate

The separate problem is incremental evidence acquisition after top-3:

- 43/400 UID expansions add a relevant old/new session.
- Always expanding to top-5 reaches 187/400 BOTH but performs 357 no-gain
  expansions and costs 64,338 mean context chars.
- Oracle-selective reaches the same 187/400 with 43 expansions and 37,292 mean
  context chars. This is a real cost headroom, but oracle is not deployable.
- The visible cue rule finds only 1/43 useful expansions and is stopped.
- A depth-2 visible-feature tree finds 5/43 at a 10% expansion budget, precision
  0.125, versus the visible rule's 1/43 and 0.111. Its cost is about 4.6x the
  rule; this is a weak learnability signal, not a learned policy.
- The model KEEP/EXPAND interface produced no valid decision after two calls:
  one thinking-parameter error and one output truncation. This is
  `UNEVALUATED_NO_VALID_DECISION`, not a negative accuracy result.

G3 remains `KEEP_WITH_HEADROOM`, separate from G2. The next G3 gate is a frozen
held-out, cost-aware evaluation of visible features and a simplified KEEP/EXPAND
interface. No learning claim is made.

## 6. Evidence Classification

Actual results:

- Paper E live venue and submission handoff.
- G2 V5 counterexample review and evaluation contract.
- G2 retrieval-policy negative comparison.
- G2 fixed-state model experiment and end-to-end independent review.
- G3 deterministic 400-UID replay and visible-feature cross-validation.

Auxiliary or diagnostic evidence:

- V4 judge/gate labels, old proxy scores and judge calibration outputs.
- Hidden `M_old/M_new/explanation` and relevant session indices used only for
  researcher-side evaluation.
- G3 oracle-selective policy and the fixed-state oracle references.

Not established:

- A new memory architecture.
- A stable state-to-action transfer gain.
- A deployable selective evidence-expansion policy.
- A learned G3 selector or any SFT/LoRA result.
- Human gold, blind review or financial expert certification.

## 7. Resource Accounting

V5 authoritative execution is 110 accounting/physical calls and 663,178
accounting tokens:

- G2 fixed-state actor: 62 calls, 355,719 tokens, including 14 preserved
  truncation/repair attempts.
- G2 judge/calibration: 46 calls, 283,220 tokens, including failed judge
  formatting attempts.
- G3 model interface: 2 calls, 24,239 tokens; call 2 raw is preserved and call
  1 usage is recovered from the server task because its raw response was lost
  during parsing.

Cumulative current Goal accounting is 536 calls and 3,713,363 tokens. Training,
paid API and production Memory writes remain zero. All historical ledgers are
separate. See `RESOURCE_LEDGER.json`.

## 8. Portfolio Decision

- Paper E: continue and prepare for owner submission action.
- G2: keep only a narrowed state-to-action development test; stop the old
  consumption/scope mechanisms and do not claim a representation gain.
- G3: keep selective incremental evidence acquisition as a distinct candidate;
  stop the visible rule and defer any model policy claim.

The two remaining candidates are not certified thesis contributions. They are
now measurably different questions with separate failure modes and cost models.

## 9. Next Single Experiments

1. G2: one information-matched, held-out fact/action test with corrected
   vectors and independent action reference. Stop if safe action completion does
   not improve at equal or lower unsafe/refusal cost.
2. G3: frozen UID-grouped visible-feature evaluation and a compact KEEP/EXPAND
   interface with sufficient output budget. Stop if it cannot beat the transparent
   rule at matched expansion cost.

## 10. Owner Actions

The only external actions left are Paper E identity/affiliation, AI disclosure
approval, patent status, artifact release/license/DOI, submission/payment,
presentation/travel and school recognition. No research work is blocked on
those decisions.
