# Evidence Feedback and Reliable Delivery Continuation Return

Date: 2026-10-25, Asia/Shanghai

Status: `COMPLETED_STAGE_WITH_BOUNDED_NEGATIVE_AND_CONTINUE_DIRECTIONS`

## Scientific Judgment

The main judgment changed in three ways.

1. P0 shows that multi-row period evidence loss, not only model reasoning,
   caused many checker rejections. Restoring visible headers raises ordinary
   `VALID` from 31/72 to 48/72 and correct accepted coverage from 21/72 to
   36/72. It does not make the checker safe: 12 accepted outputs remain
   numerically wrong and the accepted-wrong rate is 25.0%.
2. The current one-shot visible-feedback repair hypothesis is falsified on the
   development panel. Correct neutral revision is 56/72 and repairs 0/16
   initial errors; localization is 49/72 with 0 repairs and 7 correct-to-wrong;
   execution feedback is 40/72 with 0 repairs and 16 correct-to-wrong. The
   strongest simple baseline is therefore the unchanged or neutrally revised
   ordinary output, not the diagnostic feedback.
3. A 24-family untouched bounded confirmation keeps the same ordering.
   Ordinary neutral revision reaches 62/72 versus original 60/72 and
   localization 59/72. Neutral revision repairs 2 errors without damaging a
   correct output; localization repairs 3 but damages 4. This supports a
   modest retry baseline, not a localization-repair contribution.

The oracle-assisted development diagnostic narrows the mechanism. Discrepancy
classes alone repair 3/16 initial errors, so the model can sometimes execute a
correct error class. The same prompt format destroys 54 initially correct
outputs and completes only 13/72 structured outputs, so it is not a deployable
upper bound for delivery. Combined with 0 visible-feedback repairs, the current
limit is both visible localization insufficiency and prompt/revision stability.

## P0 Scope

See `P0_IMPACT_RETURN.md`. Historical numeric scores and checkpoint identities
are unchanged. The corrected replay is `POST_HOC_DEVELOPMENT_REPLAY`. The
bounded denominator repair triggers 0/72 times, so its policy has no observed
repair increment.

## Experiment A: Same-Candidate Feedback Intervention

Identity: frozen ordinary Qwen3-4B candidates, one additional generation,
256-token cap, no hidden answer/program/reference in prompts.

| Condition | Correct | Wrong-to-correct | Correct-to-wrong | All 3 variants |
|---|---:|---:|---:|---:|
| Frozen original | 56/72 | - | - | 17/24 |
| Correct neutral revision | 56/72 | 0 | 0 | 17/24 |
| Execution feedback | 40/72 | 0 | 16 | 7/24 |
| Visible localization | 49/72 | 0 | 7 | 13/24 |

The first neutral-revision implementation placed the instruction before the
candidate JSON and produced 71 empty completions. Those 72 attempts are
preserved as an interface failure, not a model-quality observation. The
corrected neutral revision places the instruction after the candidate and
matches the feedback arms' continuation structure.

The independent review correctly rejected the first feedback-quality metric.
The corrected post-hoc mapping uses the frozen initial candidate and the
actual visible feedback. It reports 3/72 false-alarm cases and 12/72
insufficient diagnoses. These remain development diagnostics; algebraically
equivalent programs can be misclassified.

## Experiment B: O/R/E Continuation

`E` was not trained. There is no independently verified natural correction
trajectory to supervise: visible feedback repaired 0 errors, and the three
oracle-assisted corrections are not deployable feedback evidence. Training on
their hidden corrected targets would reproduce failed-item answer repetition
or weighting, not verified feedback learning.

This is a supervision-eligibility stop, not evidence that feedback learning in
general is ineffective. The executed substitute is the oracle mechanism
diagnostic plus the fixed-model delivery confirmation below. A future E arm is
qualified only after a teacher or toolchain produces independently verified
visible corrections without using hidden answers as a selection shortcut.

## Experiment C: Fixed-Model Delivery Confirmation

Identity: 24 untouched source-disjoint families, three variants each, frozen
ordinary checkpoint. This is a bounded confirmation, not cross-report or
cross-benchmark generalization.

| Policy | Correct delivery | Wrong delivery | Abstain | Conditional wrong |
|---|---:|---:|---:|---:|
| Always accept original | 60 | 12 | 0 | 16.7% |
| Always accept neutral retry | 62 | 10 | 0 | 13.9% |
| Always accept localization | 59 | 13 | 0 | 18.1% |
| Semantic gate original | 32 | 6 | 34 | 15.8% |
| Bounded repair + verified fallback | 33 | 6 | 33 | 15.4% |

The transparent gate and bounded repair reduce accepted wrong answers only by
discarding 33-34 tasks. They do not improve correct delivery over the strong
retry baseline. The current localization-repair policy is stopped. Neutral
revision remains a simple costed baseline and produced one improved family
with no degraded family on this panel.

## Paper E

The two-case measurement-audit boundary is unchanged. The current decision is:

- Primary: ICAART 2027 Regular, only if Owner can authorize before the
  2026-10-29 AoE deadline, accept presentation/travel exposure, and confirm
  SCITEPRESS proceedings recognition.
- Sequential backup: Computer Science subscription route, without simultaneous
  submission.

The manuscript now includes the ICAART data-quality/synthetic-bias comparison,
a bounded agent-evaluator relevance statement, the `AI Evaluation` keyword,
and a verified no-version OpenAI Codex software citation. The 12-page ICAART
PDF and package pass evidence, citation, anonymization, format, hash and
private-artifact checks. No submission, payment, signature or public release
was performed.

## Evidence Identity

- P0 replay: post-hoc development replay.
- Experiment A: development mechanism experiment on frozen natural outputs.
- Oracle condition: `ORACLE_ASSISTED_DEVELOPMENT_ONLY`, not deployable.
- Experiment C: bounded confirmation on 24 new families.
- All numeric references remain numeric/program identities unless explicitly
  separated as semantic or delivery measures.

## Next Execution

The next high-value work is not another O/R/E reweighting run. It is to collect
a small, source-isolated set of natural errors and independently verified
visible correction trajectories using a stronger teacher or deterministic
edit verifier, then freeze one correction representation and compare O/R/E
from the same ordinary checkpoint. The first stop rule is simple: if verified
corrections cannot beat neutral retry at inference or cannot be learned beyond
R, stop the feedback-learning candidate and retain the measurement and
delivery findings as negative/methodological material.

## Owner Decisions

Only external or identity actions remain: Paper E route approval, author and
affiliation fields, AI disclosure wording, artifact release/license, patent
status, submission/payment, and presentation/travel. The exact 2027 thesis
review date is still unknown and must not be assumed to be October 31.
