# Experiment A Independent Review

Date: 2026-10-25

Identity: AI-assisted independent technical and scientific review. This is not
human gold, blind review, financial-expert certification, or an independent
model-family evaluation.

## Verdict

The frozen-candidate transition results are reproducible and support a bounded
negative conclusion for this Qwen3-4B ordinary checkpoint and these visible
feedback representations:

- Correct neutral revision, execution feedback, and localization feedback all
  leave all 16 initially wrong candidates wrong.
- Correct neutral revision preserves all 56 initially correct candidates.
- Execution feedback changes 16 initially correct candidates to wrong.
- Localization feedback changes 7 initially correct candidates to wrong.
- No tested intervention improves numeric correctness over the frozen 56/72.

This is enough to reject the immediate hypothesis that appending these
execution or localization diagnoses enables one-shot correction by the current
model. It is not evidence that verified feedback learning is generally
ineffective.

The current Experiment A feedback-quality fields are not valid measurements of
the feedback sent to the model and must be corrected before being cited.

## Read-Only Recomputation

Inputs and preserved results:

- Frozen V5 results SHA-256:
  `456aa2a67a629260177642aabf0c4bf4d3ed3fd89ce7b61d67c7b3e62335e0f6`.
- First three-condition raw result SHA-256:
  `f05b0dbc73de14270f8385b4861fdd5897422ec60adfee552a8de9550b3c336d`.
- Preserved failed neutral interface result SHA-256:
  `2df56f87ed7caed2a13f8de061dd6fc866ef7e8ce898f5d74770904339c68ced`.
- Corrected neutral revision result SHA-256:
  `e40f38f30ddd5e1fa59c01dc3836c02a7013f60fa4b8531a8c143d8755dc498e`.
- Enriched V3 result SHA-256:
  `2e4b43067372f1866f6939be4a081e70b96ffc71b6425e9675acff5a2c05fc11`.

The V3 result has 360 rows. Independent counts:

| Condition | Attempts | Numerically correct | Prompt + completion tokens | Main output state |
|---|---:|---:|---:|---|
| deterministic rerun control | 72 | 56 | 32,435 | 72 complete |
| failed neutral interface v2 | 72 | 0 | 35,903 | 71 empty/parse failures |
| corrected neutral revision | 72 | 56 | 43,039 | 72 complete |
| execution feedback | 72 | 40 | 65,769 | 12 parse failures |
| localization feedback | 72 | 49 | 58,217 | 72 complete |

Total is 360 accounting attempts and 235,363 accounting tokens. The summary
and row-level recomputation agree exactly.

Transitions from the same frozen candidates:

| Condition | wrong to correct | correct to wrong | correct retained | wrong retained |
|---|---:|---:|---:|---:|
| deterministic rerun | 0 | 0 | 56 | 16 |
| corrected neutral revision | 0 | 0 | 56 | 16 |
| execution feedback | 0 | 16 | 40 | 16 |
| localization feedback | 0 | 7 | 49 | 16 |

Task-level paired results across original/relevant/irrelevant variants:

| Condition | all three correct | original correct | relevant correct given original | irrelevant correct given original |
|---|---:|---:|---:|---:|
| frozen/deterministic/neutral | 17/24 | 19/24 | 18/24 | 18/24 |
| execution feedback | 7/24 | 14/24 | 9/24 | 11/24 |
| localization feedback | 13/24 | 18/24 | 17/24 | 13/24 |

Variants are repeated measures within 24 task families and must not be treated
as 72 independent task samples. The small panel supports direction and failure
mechanism analysis, not a population effect size.

## Required Metric Correction

`same_candidate_feedback_a_v1.py:319-325` computes localization feedback
quality from the revised output rather than the feedback originally supplied:

1. `semantic_check` is run on `target`, which is parsed from the revised
   `generated_text`.
2. `expected_discrepancies` is also called with the revised `generated_text`.
3. `initial_correct` is set from the revised `result["program_correct"]`,
   not the frozen original candidate.

Consequently, the reported `feedback_error_rate=0` and
`feedback_insufficient_rate=15/72` describe the post-revision output's
discrepancy/semantic relation. They do not measure whether the original
localization feedback was false, supported, or sufficient for the original
candidate. These two fields must be recomputed from:

- the frozen initial candidate;
- the exact localization feedback text sent in the prompt;
- a separately frozen mapping from visible findings to post-hoc discrepancy
  categories;
- initial correctness, not revised correctness.

Until then, do not use those two rates in a scientific claim.

## Other Measurement Boundaries

- `exact_reference_set` is an expected-reference-set diagnostic. It is not a
  complete semantic gold and does not establish that non-exact legal evidence
  bindings are wrong.
- The ordinary correction changes two initially wrong outputs from disjoint to
  exact reference sets while leaving their numeric results wrong. This shows
  that reference-set recovery and task correctness are distinct.
- `execution_feedback.feedback_error=false` is asserted by construction for a
  deterministic trace; the analysis does not independently validate every
  displayed trace cell. The raw trace was generated only from visible table,
  candidate, and deterministic execution.
- Hidden expected answers/programs are not used in `revision_prompt`,
  `execution_feedback`, or `localization_feedback`. They enter post-hoc
  evaluation only. A naive text scan is not sufficient because expected values
  can naturally occur in tables or the previous candidate.
- The first neutral-revision implementation put the instruction before the
  previous JSON and produced 71 empty completions. It is correctly retained as
  an interface failure, not a model-quality result. The corrected condition
  places the standard revision instruction after the candidate and matches the
  feedback arms' continuation structure.

## Strongest Alternative Explanations

1. **The model lacks a learned revision operator.** It can produce a structured
   program once, but the ordinary SFT format does not teach it to interpret a
   diagnosis and modify only the faulty dependency. The zero wrong-to-correct
   transitions and correct-to-wrong damage are consistent with this.
2. **The feedback is too weak or incorrectly scoped.** Localization reports
   row/period/program conflicts but does not provide a verified edit or state
   which legal binding should change. The current feedback-quality analysis
   cannot yet quantify this limitation.
3. **Prompt-length/continuation interference differs by arm.** Execution
   feedback is longest and has 12 parse failures plus the most damage.
   Localization is shorter and less destructive but still below the original.
   This argues against a simple “more information is better” explanation.
4. **The panel is saturated for one-shot self-revision under this decoder.**
   Neutral revision preserves the original distribution exactly and finds no
   new correct answers, despite some reference-set cleanup.

The present evidence cannot distinguish explanations 1 and 2 without a
high-quality localization upper bound or verified correction supervision.

## O/R/E Recommendation

Do not launch the planned E arm from the current Experiment A trajectories.
There are no observed successful natural correction trajectories to supervise,
and training on the hidden corrected target would reproduce the already audited
“failed item answer repetition/weighting” identity rather than verified
feedback learning.

Before O/R/E, execute one bounded mechanism diagnostic:

- derive an explicitly `ORACLE_ASSISTED_DEVELOPMENT_ONLY` localization category
  from the hidden reference;
- reveal only the discrepancy type, never the correct program, evidence IDs, or
  answer;
- run the same one-shot revision on all 72 candidates;
- if wrong-to-correct remains zero, attribute the immediate bottleneck to
  feedback execution/revision capability and stop this inference-time repair
  representation;
- if wrong-to-correct becomes non-zero, use only independently verified natural
  corrections to construct E, with R matched for extra tokens, update count,
  task coverage, and training cost.

Thus O/R/E remains a possible learning experiment only after qualified
correction supervision exists. The current A result alone does not justify
training, and it does not justify a general claim that feedback learning is
ineffective.
