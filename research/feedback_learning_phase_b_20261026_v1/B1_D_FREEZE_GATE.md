# B1 Qualification and B2 Decision Gate

Goal ID: `FEEDBACK_LEARNING_PHASE_B_20261026`

Authority commit: `caa18102bdbbcfe99a889bcf82a125dcc20fdcca`

## Deployment Contracts

- O: frozen ordinary direct solver.
- N: one neutral retry from the same model and visible input.
- R: full-program revision trained from the ordinary checkpoint.
- E: restricted local-edit revision trained from the same ordinary checkpoint and
  applied by a deterministic editor.

R/E must share source tasks, visible inputs, label quality, rehearsal mixture,
optimizer budget and evaluation prompts as far as the representation allows.
Target-length and compute differences must be recorded, not declared matched.

## Supervision Gate

Qualification requires:

1. At least two naturally occurring eligible error types with visible evidence.
2. Correct and no-op trajectories, not only error cases.
3. Every correction has source identity, O output, visible error evidence,
   correction target/action, patch applicability and independent execution.
4. Unobservable unit/period requirements are `UNRESOLVED`, never guessed.
5. Training reference, teacher reference, deployment feedback and confirmation
   gold are separate fields.

If these conditions cannot be met, B2 training is not launched and the budget
remains unused.

## Frozen Primary Estimands

- Final semantic correctness: correct program/evidence/unit/role/period on the
  full eligible evaluation population.
- Error repair: O wrong to final correct.
- Correct preservation: O correct to final correct; O correct to wrong is
  separately counted.
- Delivery: correct, wrong, reasonable UNKNOWN/abstention and coverage.
- Cost: input/output/training tokens, GPU time, tool calls, wall time and
  adapter/application cost.

Variants from one source family are repeated measures, not independent samples.

## Minimum Useful Effect

For E to survive development and confirmation:

- E - R must be at least +5 percentage points in paired final semantic
  correctness.
- E - N must be at least +3 percentage points.
- E must cover at least two eligible natural error types without reversing the
  direction in either.
- E may damage at most one additional originally-correct family per 24-family
  panel relative to R.

If the point estimate is below the threshold or the source-cluster interval
crosses zero with a wide range, the result is `INCONCLUSIVE`, not success. If
the advantage disappears after matched supervision/compute or exists only in
JSON format/length, stop the local-edit candidate.

## C3 Separation

C3 remains a fixed-model delivery question. It survives only if transparent
checks or a bounded action improve correct delivery and error risk at an
explainable cost over always-accept and neutral retry. Abstention alone is not
an improvement, and the same E repairer is not counted as a second innovation.
