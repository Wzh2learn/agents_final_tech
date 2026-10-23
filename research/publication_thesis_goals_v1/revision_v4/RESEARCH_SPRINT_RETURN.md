# Loop D Research Sprint Return v4

Date: 2026-10-23, Asia/Shanghai

Status: `EVIDENCE_EXIT_STATE_CARD_NOT_CONFIRMED_ACTION_GAIN_ABSENT`

## 1. Hypotheses And Falsifiers

### H1: The old state-card improvement was semantic, not a scoring artifact.

Falsifier: a constant `No + STALE_DETECTED` strategy passes the old metric, or a
method-blind semantic judge removes most of the `0/8 -> 4/8` difference.

Result: falsified as originally stated. The old proxy is degenerate. It remains a
record of answer-behavior change, not semantic accuracy.

### H2: A compact state-card representation improves stale-state resolution beyond
generic fact extraction at comparable budget.

Falsifier: one-call facts matches state card on paired cases, or the difference is
only one or two cases.

Result: not confirmed. Under BM25 top-5, strict dim1 judge results are 4/16 for
one-call facts, 3/16 for generic timeline and 5/16 for state card. On the eight
retrieval-covered cases: 4/8, 3/8 and 5/8. State card versus one-call has 2
state-only wins, 1 one-call-only win, 3 shared wins and 10 shared failures.

### H3: Dim1 state representation transfers to better downstream actions.

Falsifier: validated dim3 actions do not improve over one-call facts.

Result: falsified for the current method. After deterministic non-degeneracy
gating, one-call facts is 3/16 and state card 2/16. On the six retrieval-covered
cases: 2/6 versus 0/6. State-card expansion is stopped for action claims.

### H4: The scope policy's 30-versus-35 probe saving is unique to scope reasoning.

Falsifier: exact cache plus miss revalidation reaches the same decisions and probe
count.

Result: falsified. The exact-cache baseline is 15 CORRECT, 5 ABSTAIN, 30 probes,
with all 20 decisions identical to scope. The saving is exact-input cache reuse.

## 2. Measurement Repair

The v3 `pair_success` required only self-reported `STALE_DETECTED` and a negative
answer prefix. A fixed object satisfying both passed 8/8 without seeing evidence.
The prefix rule also classified uncertainty as negative and missed explicit current
facts.

This round preserves all v3 outputs and proxy counts but does not use them as
semantic accuracy. New evaluation separates:

- specific current-fact support;
- rejection of the stale state;
- evidence consistency;
- safe UNKNOWN under missing evidence;
- concrete action alignment;
- empty/contradictory judge outputs.

The deterministic overlap scorer produced known false positives and is diagnostic
only. The final semantic evidence uses a method-blind auxiliary LLM judge with
hidden `M_old/M_new/explanation`, retrieved source sessions and anonymized answers.
Strict validation rejects string booleans and inconsistent `pass` fields. A second
deterministic action gate rejects empty answers and `safe_unknown=true` successes.
Neither judge nor hidden explanations are human gold.

## 3. Retrieval And State Processing

### Non-oracle retrieval

Zero-model policy comparison over 400 dim1 items:

| Policy | New recall | Both old/new | Mean context chars |
|---|---:|---:|---:|
| BM25 top-3 | 0.370 | 0.360 | 34,444 |
| BM25 top-5 | 0.473 | 0.468 | 63,870 |
| latest-3 | 0.000 | 0.000 | 44,138 |
| latest-1 + BM25-2 | 0.275 | 0.270 | 34,844 |

On the frozen 16 UIDs, top-5 raises coverage from 3/16 to 8/16. Relevant STALE
evidence is not simply the final sessions, so recency-only fails.

### Matched model arms

All arms receive the same official-style role/order/timestamp session rendering.
Direct and one-call arms have 512 max output tokens. Two-call arms have a total
512 cap split between intermediate and answer stages.

| Condition | Calls | Strict dim1 pass | Retrieval-covered pass | Validated dim3 action |
|---|---:|---:|---:|---:|
| Direct answer, top-3 | 1 per case | 0/16 | 0/3 | not run |
| One-call facts, top-5 | 1 per case | 4/16 | 4/8 | 3/16 |
| Generic two-stage timeline, top-5 | 2 per case | 3/16 | 3/8 | not run |
| Two-stage state card, top-5 | 2 per case | 5/16 | 5/8 | 2/16 |

The development-only four-arm probe also favored state card on four objects, but
that set is too small and the scorer was repaired after inspecting failures. The
top-5 comparison is the stronger current evidence and still does not establish a
stable method advantage.

## 4. Error Decomposition

- Retrieval miss: 8/16 top-5 cases still retrieve old evidence without the new
  evidence. This is now the largest end-to-end limitation.
- Stale acceptance: common in one-call and timeline outputs when old evidence is
  visible but new evidence is missing.
- State extraction: state cards can state the current fact when both relevant
  sessions are retrieved, but they also produce unsupported specificity and empty
  answers.
- Propagation: Type II cases remain harder; explicit `M_old/M_new` diagnostics
  help, but generated state cards do not consistently recover the dependency.
- Action: dim1 success does not transfer. State card is lower than one-call after
  empty-answer and safe-unknown contradictions are removed.
- Judge/measurement: lexical overlap and unvalidated LLM judge fields can create
  false positives; every final metric now has a non-degeneracy gate.

## 5. CUPMem Boundary

STALE/CUPMem already covers:

- user-only structured state extraction;
- explicit versus inferred update separation;
- write-time stale/unknown-current adjudication;
- propagation-aware candidate search;
- `SUPPORTED/OUTDATED/UNRESOLVED` premise verdicts;
- constrained current-basis readout and action grounding.

Our state card is therefore not a new memory architecture. The remaining candidate
contribution is narrower: a stage-separated evaluation that measures retrieval
coverage, current-fact recovery, stale-state handling and action transfer under
matched budgets, with constant-answer and empty-answer controls. Even that requires
independent action references and more natural families before contribution status.

Deep-reading note: `reading_notes/2026_STALE_2605.06527.md`.

## 6. Scope Panel Closeout

`REUSE_EXACT_CACHE_BASELINE_V2.json` replays frozen action receipts without new
module execution:

- scope: 15 CORRECT, 5 ABSTAIN, 30 probes;
- exact cache + miss revalidation: 15 CORRECT, 5 ABSTAIN, 30 probes;
- always-full: 15 CORRECT, 5 ABSTAIN, 35 probes.

The exact-cache decisions match scope for all 20 transitions. The panel is closed
for further method expansion. It remains development material for evidence lifetime
and cache semantics.

## 7. Paper E And Thesis

Paper E remains `NARROW_AND_CONTINUE / READY_FOR_OWNER_SUBMISSION_ACTION`. The
two-case boundary is unchanged. The ICAART AI disclosure was corrected to name the
tools, affected manuscript parts and code uses. Fresh verification confirms:

- 11 A4 review pages;
- 25 claim bindings;
- 23 figure bindings;
- 21/21 citations;
- deterministic artifact reproduction;
- live venue deadline 2026-10-29 AoE.

The Chinese advisor page and thesis scaffold now combine scope reuse and STALE
state/action transfer into one third research point. They do not count scope and
state card as separate innovations.

## 8. Resource Accounting

Revision v4 model and judge execution:

- 349 accounting/physical HTTP calls;
- 2,831,240 accounting tokens;
- zero retries in every completed receipt;
- zero paid API, training or production Memory writes.

This includes preserved engineering overhead from truncated JSON, strict-judge
schema failures and repaired action prompts. Including the prior 77 calls and
218,945 tokens in the current publication/thesis Goal, the aggregate is:

- 426 calls;
- 3,050,185 accounting tokens.

The authoritative settlement is `RESOURCE_LEDGER.json`. Historical ledgers remain
separate.

## 9. Scientific Decision

### State card

`STOP_CURRENT_ACTION_METHOD / KEEP_DIM1_REPRESENTATION_CANDIDATE`.

Do not run more state-card arms on the same STALE panel. The dim1 difference is
small and paired evidence is inconsistent; dim3 action behavior is not better.

### Retrieval

`CONTINUE_AS_SEPARATE_BOTTLENECK`.

BM25 top-5 is a real, cheap improvement over top-3 and exposes more state-processing
cases. Future work should improve new-evidence retrieval or add explicit uncertainty,
not compensate for retrieval failure with more state-card computation.

### Third thesis point

`NARROW_TO_STAGE_SEPARATED_EVIDENCE_RELIABILITY`.

The defensible question is how to separate evidence retrieval, current-state
recovery and action transfer, and how to score them without degenerate proxies.
This is not yet a method contribution.

## 10. Next Single Experiment

Build or obtain an independent action reference that admits multiple valid actions
and distinguishes safe UNKNOWN, then compare one-call fact extraction against the
best simple retrieval/uncertainty policy on new natural families. Include:

- old-only retrieval;
- new-only retrieval;
- both retrieved;
- conflicting or ambiguous evidence;
- unchanged-state controls.

Primary metric: validated action success under fixed retrieval and matched total
budget. Stop the third contribution if one-call facts or a transparent uncertainty
rule remains equal or better.

## 11. Owner Actions

Only Paper E external actions require Owner input: authors/affiliation, AI disclosure
wording, patent status, artifact release/license/DOI, submission/payment, presentation
and school recognition. No experimental or writing work is blocked on these items.
