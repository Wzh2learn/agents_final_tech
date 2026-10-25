# Final Stage Independent Review

Date: 2026-10-25, Asia/Shanghai

Identity: AI-assisted independent scientific review of the completed stage.
This is not human gold, blind review, financial-expert certification, or an
independent model-family evaluation.

## Verdict

The P0 and Experiment A arithmetic is reproducible, and the Paper E package is
mechanically ready. One blocking evidence-identity error must be corrected:
Experiment C is not an untouched new-family confirmation. Its 24 task IDs are
exactly the second half of the V4/V5 natural-error pool.

After that identity downgrade, the stage still supports a bounded negative for
the current one-shot repair representations and retains neutral revision as a
strong simple baseline. It does not support a confirmed generalization claim.

## Blocking Finding: Experiment C Reuses the Prior Error Pool

The protocol and return call the C panel 24 "untouched" or "new" families and
label the run `BOUNDED_CONFIRMATION_24_NEW_FAMILIES`. The raw task identity
does not support that label.

- C contains 24 unique `source_task_id` values.
- `natural_error_repair_v4/error_pool_instances_v4.jsonl` contains 48 task IDs.
- The intersection is 24/24, not a subset sampled from unseen tasks.
- Four of these tasks were already ordinary-model errors in
  `error_pool_baseline_v4.jsonl`.
- `run_natural_error_repair_v4.py` and `run_weighted_error_repair_v5.py` use
  the first 48 source-disjoint tasks as the natural-error pool and derive
  error-targeted training from its failed outputs. Thus at least part of the C
  panel participated in error collection and training selection.

This violates the prompt's rule that panels already inspected during method
development are development/history replay, not new confirmation.

Required correction:

1. Relabel Experiment C as `PRIOR_ERROR_POOL_DEVELOPMENT_REPLAY` or
   `SOURCE_DISJOINT_REPLAY_ON_V4_V5_ERROR_POOL`.
2. Replace every `new families`, `untouched`, `bounded confirmation`, and
   `confirmation` claim in `RESEARCH_RETURN_20261025.md`,
   `CONFIRMATION_C_PROTOCOL_V1.json`, `DELIVERY_CONFIRMATION_C_V1.json`,
   state/threads/thesis summaries, and the resource receipt status.
3. Keep the actual counts and transitions unchanged. They remain useful
   paired development evidence.
4. Do not use C as independent evidence of generalization. The stop decision
   for the current repair representation remains reasonable, but its strongest
   support is Experiment A plus this reused-panel replay, not a new-family
   confirmation.

## High-Priority Wording Corrections

### O/R/E supervision statement is too absolute

`RESEARCH_RETURN_20261025.md` says there is "no independently verified natural
correct correction trajectory." C did produce two neutral-retry
wrong-to-correct transitions, and the oracle diagnostic produced three.

The defensible statement is narrower: there is no **feedback-derived,
training-qualified, source-isolated correction trajectory** suitable for E.
The two neutral corrections came from the reused C panel and do not contain a
verified feedback mechanism. The three oracle corrections use hidden
correctness/discrepancy status and are explicitly non-deployable.

The decision not to train E is still justified under that narrower statement.

### Mechanism attribution is not fully identified

The return says the current limit "is both visible localization insufficiency
and prompt/revision stability." The results are consistent with both, but do
not causally separate them:

- visible localization repairs 0 errors;
- the oracle condition repairs 3 errors;
- the oracle prompt also has severe output-format/revision instability;
- feedback quality is a post-hoc expected-program mapping and can mislabel
  algebraic equivalents.

Use "consistent with a combination of..." rather than "is both". The strongest
remaining alternative is that the ordinary SFT output contract lacks a stable
revision operator, so even useful diagnostic text is poorly consumed.

### "Falsified" is stronger than the evidence

Replace "the hypothesis is falsified" with "the hypothesis is not supported on
this checkpoint, decoder, prompt family and development panel" or "bounded
negative". This preserves the actual result without implying a population-level
refutation.

## Paper E Consistency

The current package evidence is internally sound:

- PDF: 12 pages, SHA-256
  `30aa05af73e05c5e64f324014f982547b46f7166448f256425b5de0ca990b013`.
- Package audit: `PASS`.
- Evidence/citations: 24 cited, 24 bibliography entries, zero missing/unused.
- PDF extraction: zero unresolved references; `AI Evaluation` present and
  unqualified `Agent Evaluation` keyword absent.
- No submission, payment, signature, external contact or public release.

One stale derived record remains. `PAPER_E_ROUTE_ADAPTATION_RESULT_20261025.json`
still reports `current_review_pdf_pages: 11`,
`current_markdown_non_whitespace_chars: 40284`, and lists required adaptations
as future actions. The current audit reports 12 pages and 41,515 non-whitespace
Markdown characters, and those adaptations are implemented.

Either mark that JSON explicitly as `PRE_MANUSCRIPT_ADAPTATION_SNAPSHOT`, or
update its current-state fields while preserving the original route analysis.
The package audit and manifest should remain the submission-state authority.

## Supported Results

- P0's 31/48 `VALID`, 36/19 `UNRESOLVED`, and 5/5 `INVALID` before/after
  counts are supported by the replay summaries.
- P0 correctly separates changed visible checker decisions from unchanged
  numeric scores and checkpoint identities.
- Experiment A transitions are supported: neutral 56/72 with 0/0 transitions,
  localization 49/72 with 0 wrong-to-correct and 7 correct-to-wrong, and
  execution 40/72 with 0 wrong-to-correct and 16 correct-to-wrong.
- The corrected feedback-quality diagnostic is properly sourced from the
  frozen initial candidate and actual visible feedback; its 3/72 false-alarm
  and 12/72 insufficient counts remain post-hoc diagnostics.
- The oracle condition is correctly marked `ORACLE_ASSISTED_DEVELOPMENT_ONLY`
  and discloses hidden initial-correctness/discrepancy-class features.
- Resource arithmetic is consistent: 648 new attempts, 453,307 generation
  tokens, 45 local batched generate calls, zero new training/judge/HTTP/paid
  API/production Memory activity, and 52 attempts remaining.
- The Paper E two-case boundary and Owner-only external actions are correct.

## Strongest Alternative Explanation

The current evidence does not distinguish "the localizer is insufficient" from
"the base model cannot reliably execute any one-shot textual revision under
this output contract." The oracle result shows some correction capacity but
also severe format instability. A future experiment should first make the
revision operator stable under neutral and oracle controls, then vary feedback
quality while holding the output contract fixed.

## Required Fixes Before Final Handoff

1. Downgrade all Experiment C confirmation/new-family labels as specified
   above; preserve raw results and hashes.
2. Narrow the O/R/E absence statement to feedback-derived training-qualified
   corrections.
3. Change causal wording and "falsified" to bounded interpretation.
4. Mark or refresh the stale Paper E route result snapshot.
5. Re-run JSON parsing, docs lint, package audit and claim/evidence after the
   wording/identity changes. No model calls are required.
