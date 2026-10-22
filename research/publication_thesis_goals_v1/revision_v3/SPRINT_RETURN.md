# Loop D Publication And Thesis Sprint Return v3

Date: 2026-10-23, Asia/Shanghai

Status: `EVIDENCE_EXIT_WITH_BOUNDED_STATE_CARD_SIGNAL`

## 1. Decisions

### Paper E

`NARROW_AND_CONTINUE / READY_FOR_OWNER_SUBMISSION_ACTION`

The unique manuscript remains a bounded two-case measurement audit. A targeted
author review found one submission blocker: the ICAART AI disclosure did not
identify the affected manuscript parts and code uses precisely enough for the
official venue rule. The canonical Markdown, ICAART TeX/PDF, disclosure draft
and package audit were synchronized without changing the scientific claims or
frozen values.

Fresh verification re-ran the wide evidence gate and private artifact
reproduction. The review PDF remains 11 A4 pages; claim bindings are 25/25,
figure bindings 23/23 and citations 21/21. The live venue was rechecked through
2026-10-23. Submission, authorship, payment, disclosure approval and public
artifact release remain Owner actions.

### G2

`STOP_CURRENT_MECHANISM_UNCHANGED`

No new G2 model experiment was run. The previous actual-module and paired
consumption repair still has no increment over strong simple baselines on its
six-object panel. This is not reopened by the new work.

### G3 And Third Contribution

`TRANSPARENT_REUSE_RULE_QUALIFIED / COMPLEX_PLANNER_PAUSED`

The policy probe now enforces per-input evidence granularity and implements
`REUSE`, `PARTIAL_CHECK`, `FULL_CHECK` and `DEFER`. On 5 candidate modules x 4
development scenarios, scope policy and always-full both yield 15 CORRECT and
5 ABSTAIN; scope uses 30 probes versus 35. The 20 transitions are not natural
families, and the probe does not show downstream repair or outcome benefit.

### Open Exploration

The Valentine risk-constrained mapping route is stopped before LoRA. Visible
confidence thresholds and a nested pair-OOF lightweight selector cannot jointly
meet the frozen harmful-map risk and target-exact constraints. This is a
bounded negative qualification, not evidence that selective mapping is
generally impossible.

STALE is retained as the strongest new mechanism source. Public-data retrieval
shows real headroom: query-only and recent top-2 have zero relevant recall,
lexical top-2 mean recall is 0.347 and oracle relevant top-2 is 1.0.

## 2. STALE Mechanism Evidence

All model calls used `Qwen3.6-35B-A3B-Q4_K_M.gguf` on GB10, temperature 0,
`max_tokens=256`, `enable_thinking=false`, sequential calls and zero retries.
The actor never received `M_old`, `M_new`, `explanation` or
`relevant_session_index` in the main or two-stage prompts.

| Condition | Cases | Result | Evidence identity |
|---|---:|---:|---|
| One-shot with oracle raw sessions | 4 development | 1/4 stale-state success | DEV_ONLY real model |
| Explicit `M_old/M_new` | 4 development | 4/4 | ORACLE_DIAGNOSTIC_NOT_DEPLOYABLE |
| Explicit values plus explanation | 4 development | 4/4 | ORACLE_DIAGNOSTIC_NOT_DEPLOYABLE |
| Raw sessions -> model state card -> answer | 4 development | 3/4 | DEV_ONLY mechanism |
| Frozen new-UID one-shot | 8 unused UIDs | 0/8 | bounded within-source confirmation |
| Frozen new-UID two-stage | 8 unused UIDs | 4/8 | bounded within-source confirmation |

The new-UID paired difference is `+0.50`: T1 improves from 0/4 to 2/4 and T2
from 0/4 to 2/4. There are no one-shot-only successes. The mechanism judgment
is narrow:

> Under oracle retrieval on unused UIDs from the same public STALE release, a
> compact state-card intermediate representation improves paired stale-state
> handling over one-shot prompting for the fixed model and budget.

The result supports state extraction/representation as the next development
question. It does not establish a full memory method, realistic retrieval
performance, independent external validity or official STALE judge accuracy.
State cards are model outputs, answer polarity is a lexical proxy, and the
oracle relevant session selection is hidden post-input information.

## 3. Evidence Identity

- Engineering validation: strict JSON/schema tests, actor-visibility tests,
  request/response preservation and deterministic replay.
- Real model observation: 76 GB10 generation calls across the main STALE
  probe, oracle diagnostic, two-stage probe and new-UID check.
- Oracle-aided diagnostic: explicit hidden state values and explanation arms.
- Bounded confirmation: eight unused UIDs from the same STALE release; not an
  independent external benchmark or human gold.
- No official LLM judge, training, paid API or production Memory write occurred.

One post-generation bookkeeping defect is preserved: the oracle diagnostic
raised `NameError` because `sha256_bytes` was omitted while assembling results
after all eight raw responses were already stored. Recovery reconstructed the
result from raw evidence, reissued no request, and verified identical pre/post
manifests. This was not a model or API failure.

## 4. Resources

- Current Goal total including the earlier Partridge probe: 77 accounting
  attempts, 77 physical HTTP calls and 218,945 accounting tokens.
- Revision v3 alone: 76 attempts and 217,096 tokens.
- Retries, official judge calls, training runs and production Memory writes: 0.
- STALE download: 305,908,212 bytes on GB10, SHA-256
  `5f3ec375179e20e2e94469e018189188f34e2e7e5f21cbecbd99fcfa648c1876`.
- Paid API spend: 0.

The authoritative settlement is
`research/publication_thesis_goals_v1/RESOURCE_LEDGER.json`. Historical ledgers
remain separate.

## 5. Next Scientific Gate

The highest-value next test is a frozen matched comparison of one-shot versus
two-stage state cards under non-oracle retrieval, preferably on a new source or
release. It must hold retrieval, prompt, model and token limits fixed and score
state handling independently of the model-produced card text.

Continue only if the state-card gain survives realistic retrieval and a simple
extraction baseline does not explain it. If the gain disappears after retrieval
errors, report a retrieval bottleneck and stop the method claim. If a simple
extractor matches the model card, retain the measurement boundary and stop the
learned-mechanism direction.

This is a development gate, not authorization for a new unbounded run.
