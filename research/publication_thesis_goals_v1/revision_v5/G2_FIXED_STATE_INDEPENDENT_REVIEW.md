# G2 Fixed-State Independent Scientific Review

Date: 2026-10-23, Asia/Shanghai
Reviewer identity: `AI_ADVISORY_SCIENTIFIC_REVIEW_NOT_HUMAN_GOLD`
Model calls made by this review: **0**

This is an independent AI-assisted scientific review of the frozen V5 G2
materials. It is not human gold, human blind review, or an executable task
oracle. It does not change the contract, raw outputs, judge outputs or prior
results.

## Executive Judgment

1. The three V4 counterexample failure modes are addressed in the V5 fixed-state
   outputs, but this is not a paired rerun of the same `one_call_facts` and
   `two_stage_state_card` arms. The evidence supports failure-mode coverage, not
   a claim that the original runs were repaired.
2. The V5 validation correctly treats `CLARIFY` and `UNKNOWN` as non-completion.
   Its blanket posterior is not a complete semantic re-adjudication: two
   `09949c3c` action rows remain contract-tense, and some validated primary
   labels no longer derive cleanly from their retained field vectors.
3. Plain fact completion is `2/8`; evidence-decision fact completion is `3/8`.
   This is a net `+1/8`, not a stable method gain. Both representations complete
   only `1/8` actions, on different UIDs, with `7/8` reasonable abstention or
   clarification.
4. The results are sufficient to reject a strong claim that recovered/current
   fact accuracy automatically transfers into action completion. They are not
   sufficient to establish that the evidence-decision representation improves
   state-to-action transfer.

Mechanism decision: **CONTINUE_NARROWED_DEVELOPMENT_ONLY**. Continue the
state-to-action question, but do not promote the current evidence-decision
bundle as a validated method. One information-matched, held-out comparison is
warranted; if it does not improve safe action completion without increasing
unsafe advice or abstention cost, stop this mechanism.

## 1. Evidence Read

- `G2_EVALUATION_CONTRACT.md`
- `G2_CALIBRATION_CASES_V2.json`
- `G2_COUNTEREXAMPLE_REVIEW.json`
- `g2_fixed_state_transfer_fixed_slots_20261023_v5/G2_FIXED_STATE_RESULTS_V5.json`
- `g2_semantic_judge_research_output_repair_20261023_v5/G2_SEMANTIC_JUDGE_RESULTS_V5.json`
- `G2_SEMANTIC_JUDGE_VALIDATED_V5.json`

The fixed-state run contains 8 development UIDs x 2 representations x 2
question kinds = 32 responses from 48 accounting calls including recovery,
258,112 accounting tokens, zero retries, and no early stop. Retrieval is held
fixed within a representation but remains BM25 top-5.

## 2. Were The Three Counterexamples Corrected?

| UID | Original defect | V5 observation | Independent judgment |
|---|---|---|---|
| `0f806fbb...` | Assertive tier-downgrade advice ignored active options learning and could disable needed features; V4 judge/gate false-accepted it. | Both fixed-state action arms return focused `CLARIFY` questions about whether options trading is long-term or temporary. | The stale-action failure mode is avoided. This is not a same-arm repair because the representation and generated response changed. |
| `0af76ce2...` | A safe high-level plan was falsely rejected because the V4 judge demanded non-generic specificity and marked `safe_unknown` inconsistently. | The calibration accepts cautious actionable plans; the evidence-decision action is `GROUNDED_TASK_COMPLETION`, while the plain action asks one focused clarification. | The evaluator false-reject pattern is corrected at contract level. This is an adjudication correction, not evidence that the actor mechanism improved. |
| `17c4192e...` | OLD_ONLY evidence caused stale self-employment advice; the other arm returned an empty answer. | The fixed-state action outputs ask about conflicting employment or abstain using `UNKNOWN`. | The stale/empty failure modes are avoided. Empty output remains `INTERFACE_FORMAT_FAILURE`; it was not semantically repaired. |

Conclusion: **CORRECTED_FAILURE_MODES_WITHOUT_PAIRED_RERUN**. Do not report
`3/3 repaired` as an accuracy result.

## 3. Calibration And Contract Consistency

The ten synthetic calibration controls cover the contract's required anchors:
fixed `No`, fixed `UNKNOWN`, empty output, cautious generic action, old fact,
new fact, correct paraphrase, unsupported detail, fact-correct/action-wrong and
unnecessary refusal. Their expected categories match the frozen contract.
They are mechanism controls, not research samples or human gold.

The V5 post-validation also correctly enforces the counting rule:

- `UNKNOWN` is reasonable abstention when evidence or material action ambiguity
  warrants it, but is not task completion.
- `CLARIFY` may be reasonable, but is not task completion.
- `ANSWER` without consumable text is an interface failure.

However, `G2_SEMANTIC_JUDGE_VALIDATED_V5` primarily repairs category counts.
It does not prove that every `CLARIFY/UNKNOWN` is semantically warranted:

1. `09949c3c` plain-action and decision-action both return bare `UNKNOWN`.
   The plain bundle contains the old five-month plan and the new 18-month
   assignment; the decision bundle explicitly leaves current housing/location
   unknown. The request asks what to consider before long-term commitments, so
   a safe general answer or one minimum clarification exists. The raw judge
   classified both rows as `UNNECESSARY_REFUSAL_DESPITE_SUFFICIENT_EVIDENCE`.
   The blanket validation changed them to reasonable abstention without a
   case-level sufficiency argument. These two rows require re-adjudication and
   should not be assumed reasonable in the final score.
2. `12f3fc0d` decision-action `CLARIFY` is defensible from the actor-visible
   bundle. That bundle invalidates the old strict science-fiction constraint
   but does not expose the positive nonfiction preference. The raw judge's
   claim of a "clear shift to nonfiction" uses evidence the actor did not
   receive. The validated primary category is therefore preferable, but its
   retained vector still says `CONSEQUENTIAL_INVENTION`,
   `action_constraints_respected=false` and `action_reasoning_valid=false`,
   which does not derive cleanly to reasonable clarification.
3. More generally, the contract says the primary category is derived from the
   review vector. Several post-validation rows change only the primary/abstention
   conclusion while retaining contradictory vector fields. The corrected counts
   are useful but remain `AUXILIARY_CONTRACT_LEVEL_CORRECTION`, not gold.

## 4. What Do `2/8`, `3/8` And `1/8` Mean?

| Representation | Fact completion | Action completion | Fact non-completion | Action non-completion |
|---|---:|---:|---|---|
| Plain fact bundle | 2/8 | 1/8 | 5 reasonable, 1 stale/unsafe | 7 reasonable |
| Evidence-decision bundle | 3/8 | 1/8 | 3 reasonable, 2 stale/unsafe | 7 reasonable |

The fact difference is one net case:

- Evidence-decision wins on `0af76ce2` and `0fcd704e`.
- Plain wins on `09949c3c`.
- `12f3fc0d` completes in both.

The equal action count does not mean equal behavior:

- Plain action completion is `12f3fc0d`.
- Evidence-decision action completion is `0af76ce2`.
- Neither representation dominates; both abstain or clarify on 7/8 actions.
- The two action completions are therefore complementary case effects, not a
  replicated improvement.

Among fact-success cells, only one plain pair (`12f3fc0d`) and one
evidence-decision pair (`0af76ce2`) also complete the corresponding action.
Fact completion alone therefore does not reliably predict action completion.

## 5. Does The Evidence Support State-To-Action Transfer?

### Actual results

- Current-state fact recovery can improve while action completion remains flat.
- Some fact-success cases transfer to action (`12f3fc0d` plain,
  `0af76ce2` decision), but other fact-success cases do not (`09949c3c` plain,
  `12f3fc0d` and `0fcd704e` decision).
- Both representations have the same `1/8` action completion and a high
  abstention/clarification rate.

### Auxiliary adjudication

- The semantic judge uses the same model family as the actor.
- Its raw outputs are useful diagnostics but contain false accepts, false
  rejects and actor-view leakage.
- The post-validation repairs non-completion accounting but is not human gold
  and does not fully repair field-vector consistency.

### What is supported

- Strong automatic transfer from fact correctness to action correctness is not
  supported and is contradicted by multiple paired cells.
- Action evaluation must consume constraints and current-state consequences,
  not infer success from a correct fact.

### What is not supported

- That the evidence-decision representation improves action completion.
- That its `+1/8` fact completion is a generalizable method effect.
- That reasonable abstention is cost-free or successful task completion.
- Any population, cross-domain or held-out generalization claim.

### Remaining uncertainty

- Eight development UIDs are too few and some were selected after earlier judge
  review.
- Plain and decision bundles do not expose identical information. The decision
  bundle sometimes removes positive facts and adds invalidation/unknown fields,
  confounding representation with information content.
- The current semantic scores depend partly on a post-hoc contract correction
  with unresolved per-case sufficiency.

## 6. Decision And Minimal Next Test

Decision: **CONTINUE_NARROWED_DEVELOPMENT_ONLY**.

Reason to continue: the experiment reveals a real and interpretable gap between
state recovery and action completion, and it contains both transfer and
non-transfer cells. That is enough to justify one controlled development test.

Reason not to promote the mechanism: action completion is unchanged at `1/8`,
the apparent fact gain is one case, and the evidence sets are not matched.

The next test should:

1. Freeze a corrected contract vector in which primary category is recomputed
   from all fields, especially for `CLARIFY/UNKNOWN`.
2. Use information-matched plain and decision representations; no arm may omit
   a positive fact available to the other.
3. Use held-out UIDs not selected after judge review.
4. Keep the same model, prompt budget, retrieval and action slots.
5. Predefine safe action completion as the primary endpoint, with unsafe advice,
   unnecessary refusal, reasonable abstention and token/latency cost reported
   separately.

Stop this mechanism if the corrected decision representation fails to improve
safe action completion at equal or lower unsafe/refusal cost on held-out cases.
A null result would support the narrower conclusion that explicit decision
state does not automatically solve state-to-action transfer.

## Evidence Identity

- Actual model outputs: `DEV_FIXED_EVIDENCE_FIXED_STATE_FACT_ACTION_TRANSFER`.
- Semantic judgments: `AUXILIARY_METHOD_BLIND_LLM_JUDGE_NOT_HUMAN_GOLD`.
- Contract-level validation: `CONTRACT_LEVEL_VALIDATION_OVER_AUXILIARY_LLM_JUDGE`.
- Calibration cases: `SYNTHETIC_MECHANISM_CONTROLS_NOT_RESEARCH_SAMPLES`.
- This review: `AI_ADVISORY_SCIENTIFIC_REVIEW_NOT_HUMAN_GOLD`.
